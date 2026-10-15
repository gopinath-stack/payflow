"""PayFlow - Payments Service
Moves money between accounts by calling the Accounts Service,
records each payment, and publishes an event to Redis for the Notifier.
"""
import json
import logging
import os
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Integer, Numeric, String, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./payments.db")
ACCOUNTS_URL = os.getenv("ACCOUNTS_URL", "http://localhost:8001")
REDIS_URL = os.getenv("REDIS_URL", "")          # empty = events only logged
EVENT_QUEUE = os.getenv("EVENT_QUEUE", "payment-events")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s payments %(message)s")
log = logging.getLogger("payments")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    from_account = Column(Integer, nullable=False)
    to_account = Column(Integer, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


Base.metadata.create_all(engine)

_redis = None
if REDIS_URL:
    import redis
    _redis = redis.Redis.from_url(REDIS_URL)

app = FastAPI(title="PayFlow Payments", version=APP_VERSION)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class PaymentIn(BaseModel):
    from_account: int
    to_account: int
    amount: float = Field(gt=0)


def to_dict(p: Payment) -> dict:
    return {
        "id": p.id, "from_account": p.from_account, "to_account": p.to_account,
        "amount": float(p.amount), "status": p.status,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


def publish(event: dict) -> None:
    if _redis is None:
        log.info("event (no redis): %s", event)
        return
    try:
        _redis.rpush(EVENT_QUEUE, json.dumps(event))
    except Exception as exc:  # payment already done; never fail it for a notification
        log.error("could not publish event: %s", exc)


def call_accounts(path: str, amount: float) -> None:
    resp = httpx.post(f"{ACCOUNTS_URL}{path}", json={"amount": amount}, timeout=5)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.json().get("detail", "accounts error"))


@app.get("/health")
def health():
    return {"status": "ok", "service": "payments", "version": APP_VERSION}


@app.get("/ready")
def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        httpx.get(f"{ACCOUNTS_URL}/health", timeout=2).raise_for_status()
        return {"status": "ready"}
    except Exception as exc:
        log.error("readiness failed: %s", exc)
        raise HTTPException(503, "dependency not reachable")


@app.post("/payments", status_code=201)
def create_payment(body: PaymentIn):
    if body.from_account == body.to_account:
        raise HTTPException(400, "cannot pay the same account")

    try:
        call_accounts(f"/accounts/{body.from_account}/debit", body.amount)
        try:
            call_accounts(f"/accounts/{body.to_account}/credit", body.amount)
        except HTTPException:
            call_accounts(f"/accounts/{body.from_account}/credit", body.amount)  # refund
            raise
        status = "COMPLETED"
    except httpx.HTTPError as exc:
        log.error("accounts service unreachable: %s", exc)
        raise HTTPException(503, "accounts service unavailable")
    except HTTPException as exc:
        status = "FAILED"
        with Session() as s:
            p = Payment(from_account=body.from_account, to_account=body.to_account,
                        amount=body.amount, status=status)
            s.add(p)
            s.commit()
        log.warning("payment failed: %s", exc.detail)
        raise

    with Session() as s:
        p = Payment(from_account=body.from_account, to_account=body.to_account,
                    amount=body.amount, status=status)
        s.add(p)
        s.commit()
        result = to_dict(p)

    log.info("payment completed id=%s amount=%s", result["id"], body.amount)
    publish({"type": "PAYMENT_COMPLETED", **result})
    return result


@app.get("/payments")
def list_payments():
    with Session() as s:
        return [to_dict(p) for p in s.query(Payment).order_by(Payment.id.desc()).all()]

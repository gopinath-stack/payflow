"""PayFlow - Accounts Service
Owns customer accounts and balances.
Config comes ONLY from environment variables (12-factor).
"""
import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, Numeric, String, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./accounts.db")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s accounts %(message)s")
log = logging.getLogger("accounts")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    owner = Column(String(100), nullable=False)
    balance = Column(Numeric(12, 2), nullable=False, default=0)


Base.metadata.create_all(engine)

app = FastAPI(title="PayFlow Accounts", version=APP_VERSION)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class AccountIn(BaseModel):
    owner: str = Field(min_length=1, max_length=100)
    initial_balance: float = Field(ge=0, default=0)


class AmountIn(BaseModel):
    amount: float = Field(gt=0)


def to_dict(a: Account) -> dict:
    return {"id": a.id, "owner": a.owner, "balance": float(a.balance)}


@app.get("/health")
def health():
    """Liveness: is the process alive?"""
    return {"status": "ok", "service": "accounts", "version": APP_VERSION}


@app.get("/ready")
def ready():
    """Readiness: can we reach the database?"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:
        log.error("readiness failed: %s", exc)
        raise HTTPException(503, "database not reachable")


@app.post("/accounts", status_code=201)
def create_account(body: AccountIn):
    with Session() as s:
        acc = Account(owner=body.owner, balance=body.initial_balance)
        s.add(acc)
        s.commit()
        log.info("account created id=%s owner=%s", acc.id, acc.owner)
        return to_dict(acc)


@app.get("/accounts")
def list_accounts():
    with Session() as s:
        return [to_dict(a) for a in s.query(Account).order_by(Account.id).all()]


@app.get("/accounts/{account_id}")
def get_account(account_id: int):
    with Session() as s:
        acc = s.get(Account, account_id)
        if not acc:
            raise HTTPException(404, "account not found")
        return to_dict(acc)


@app.post("/accounts/{account_id}/debit")
def debit(account_id: int, body: AmountIn):
    with Session() as s:
        acc = s.get(Account, account_id)
        if not acc:
            raise HTTPException(404, "account not found")
        if float(acc.balance) < body.amount:
            log.warning("insufficient funds id=%s", account_id)
            raise HTTPException(409, "insufficient funds")
        acc.balance = float(acc.balance) - body.amount
        s.commit()
        return to_dict(acc)


@app.post("/accounts/{account_id}/credit")
def credit(account_id: int, body: AmountIn):
    with Session() as s:
        acc = s.get(Account, account_id)
        if not acc:
            raise HTTPException(404, "account not found")
        acc.balance = float(acc.balance) + body.amount
        s.commit()
        return to_dict(acc)

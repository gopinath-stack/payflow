import os

os.environ["DATABASE_URL"] = "sqlite:///./test_payments.db"

from fastapi.testclient import TestClient  # noqa: E402

import app as payments  # noqa: E402

client = TestClient(payments.app)


def test_health():
    assert client.get("/health").json()["service"] == "payments"


def test_same_account_rejected():
    r = client.post("/payments", json={"from_account": 1, "to_account": 1, "amount": 10})
    assert r.status_code == 400


def test_payment_completed(monkeypatch):
    monkeypatch.setattr(payments, "call_accounts", lambda path, amount: None)
    r = client.post("/payments", json={"from_account": 1, "to_account": 2, "amount": 250})
    assert r.status_code == 201
    assert r.json()["status"] == "COMPLETED"

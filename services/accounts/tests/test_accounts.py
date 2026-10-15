import os

os.environ["DATABASE_URL"] = "sqlite:///./test_accounts.db"

from fastapi.testclient import TestClient  # noqa: E402

import app as accounts  # noqa: E402

client = TestClient(accounts.app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_create_and_debit():
    acc = client.post("/accounts", json={"owner": "Ravi", "initial_balance": 1000}).json()
    r = client.post(f"/accounts/{acc['id']}/debit", json={"amount": 300})
    assert r.status_code == 200
    assert r.json()["balance"] == 700


def test_insufficient_funds():
    acc = client.post("/accounts", json={"owner": "Meena", "initial_balance": 50}).json()
    r = client.post(f"/accounts/{acc['id']}/debit", json={"amount": 100})
    assert r.status_code == 409

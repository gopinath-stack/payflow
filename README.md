# PayFlow: digital payments platform (raw code)

You are the **DevOps / OpenShift engineer**. The dev team gave you this **raw application code**.
There is **no** Containerfile, YAML, Helm, pipeline or monitoring yet. Building all of that is **your job**.

## Architecture
```
[Frontend (HTML)] ──► [Accounts API :8001] ──► [PostgreSQL]
        │                    ▲
        └──────────► [Payments API :8002] ──► [PostgreSQL]
                             │
                             └──► [Redis queue] ──► [Notifier worker]
```

| Service | Folder | Tech | Port |
|---|---|---|---|
| Accounts API | `services/accounts` | Python FastAPI | 8001 |
| Payments API | `services/payments` | Python FastAPI | 8002 |
| Notifier worker | `services/notifier` | Python (no port) | - |
| Frontend | `frontend` | Static HTML/JS | 8080 |
| Database | - | PostgreSQL (SQLite locally) | 5432 |
| Queue | - | Redis | 6379 |

## Configuration (environment variables only)
| Variable | Used by | Default (local) |
|---|---|---|
| `DATABASE_URL` | accounts, payments | `sqlite:///./<name>.db` |
| `ACCOUNTS_URL` | payments | `http://localhost:8001` |
| `REDIS_URL` | payments, notifier | empty (payments) / `redis://localhost:6379/0` |
| `EVENT_QUEUE` | payments, notifier | `payment-events` |
| `APP_VERSION`, `LOG_LEVEL` | all | `0.1.0`, `INFO` |

Postgres example: `postgresql://payflow:secret@postgres:5432/accounts`

## Health endpoints
- `GET /health`: liveness (process alive)
- `GET /ready`: readiness (dependencies reachable)

## Run locally (Git Bash on your laptop)
```bash
cd services/accounts && pip install -r requirements.txt && uvicorn app:app --port 8001
# new terminal
cd services/payments && pip install -r requirements.txt && uvicorn app:app --port 8002
# open frontend/index.html in your browser
```
Tests: `cd services/accounts && pip install -r requirements-dev.txt && python -m pytest -q` (same for payments)

## Work tracking
Backlog with acceptance criteria: `docs/backlog.md` · Working rules: `CONTRIBUTING.md`

Environments: **dev** = laptop Kubernetes · **prod** = AWS EKS (Mumbai)

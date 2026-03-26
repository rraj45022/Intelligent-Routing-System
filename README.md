# Smart Ticket Router

This project routes incoming support tickets using a production-shaped pipeline:

1. embedding-based similarity retrieval against resolved ticket history
2. business rules
3. skills and workload scoring
4. LLM review only for low-confidence cases

## Setup

```bash
/Users/rahulraj/python/agent-recommender-system/venv/bin/python -m alembic upgrade head
/Users/rahulraj/python/agent-recommender-system/venv/bin/python -m backend.scripts.seed_sample_data
/Users/rahulraj/python/agent-recommender-system/venv/bin/python -m backend.scripts.train_routing_models
```

## Batch Routing

Route a batch from a JSON array or JSONL file:

```bash
/Users/rahulraj/python/agent-recommender-system/venv/bin/python -m backend.scripts.route_ticket_batch sample_tickets.json --chunk-size 25
```

Persist routed tickets:

```bash
/Users/rahulraj/python/agent-recommender-system/venv/bin/python -m backend.scripts.route_ticket_batch sample_tickets.json --chunk-size 25 --persist
```

Track a named ingestion job:

```bash
/Users/rahulraj/python/agent-recommender-system/venv/bin/python -m backend.scripts.route_ticket_batch sample_tickets.json --chunk-size 25 --persist --job-name morning-load
```

## Running 10k Tickets

Generate a 10k synthetic intake file:

```bash
/Users/rahulraj/python/agent-recommender-system/venv/bin/python -m backend.scripts.generate_ticket_batch massive_tickets.json --count 10000
```

Refresh the embedding artifact and trained skill profiles before the morning load:

```bash
/Users/rahulraj/python/agent-recommender-system/venv/bin/python -m backend.scripts.train_routing_models
```

Process the file in persisted chunks and create a tracked batch job:

```bash
/Users/rahulraj/python/agent-recommender-system/venv/bin/python -m backend.scripts.route_ticket_batch massive_tickets.json --chunk-size 25 --persist --job-name morning-load-10k
```

After the run, inspect the operations dashboard in the admin UI or query the Postgres tables:

- `batch_ingestion_jobs`
- `batch_ingestion_items`
- `routing_decision_audit`

## Notes

- similarity artifacts are stored under `backend/artifacts/`
- the similarity artifact now contains sentence-transformer embeddings plus a nearest-neighbor vector index
- skill profiles are trained from `ticket_history` and saved into associate routing profiles
- `batch_ingestion_jobs`, `batch_ingestion_items`, and `routing_decision_audit` provide orchestration and observability tables in Postgres
- batch routing reuses shared state so large morning loads can be handled in chunks instead of rebuilding retrieval features per ticket

---

**Quick Start (local dev)**

1. Create a Python virtualenv and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Create a `.env` with a `DATABASE_URL` (Postgres) and `SECRET_KEY`. Example:

```
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/str_db
SECRET_KEY=change-me
ENV=local
```

3. Run the app (dev):

```bash
# start backend
uvicorn backend.main:app --reload

# in separate terminal - frontend
cd frontend
npm install
npm run dev
```

4. Seed sample data (creates admin & agent users and some associates/tickets):

```bash
python -m backend.scripts.seed_sample_data
```

Default seeded credentials:
- admin@example.com / admin123 (admin)
- agent@example.com / agent123 (agent)

**Frontend**
- Dev server proxies `/api` to the backend and `/ws` to the backend websocket. Login at `/login` or signup at `/signup`.

**Demo feeder**
- A background feeder is enabled by default in `ENV=local` and creates demo tickets every 10s. Configure with `.env`:

```
DEMO_TICKET_FEED_ENABLED=true
DEMO_TICKET_FEED_INTERVAL_SECONDS=10.0
```

**Testing & Dev tools**
- `requirements-dev.txt` includes lint/test tools such as `pytest`, `black`, and `pre-commit` for CI.

**Troubleshooting**
- If the frontend reports a missing `react-router-dom`, run `npm install` from the `frontend` directory.
- If DB migrations are needed later, add Alembic revisions and run `alembic upgrade head`.

---

If you'd like, I can also add a Docker Compose file to simplify local runs (Postgres + backend + frontend).
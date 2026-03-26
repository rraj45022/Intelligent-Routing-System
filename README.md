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
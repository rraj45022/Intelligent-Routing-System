from fastapi import FastAPI

from backend.core.config import settings
from backend.core.db import Base, engine
from backend.models import associate, batch_ingestion, routing_audit, ticket_history, tickets, user  # noqa: F401
from backend.routers import associates, routing, tickets
from backend.routers import auth as auth_router
from backend.services.ticket_feeder import ticket_feeder
from backend.ws import ticket_stream

app = FastAPI(title="Smart Ticket Router")

@app.on_event("startup")
async def on_startup():
    # for early dev only; later use Alembic
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if settings.env == "local" and settings.demo_ticket_feed_enabled:
        ticket_feeder.interval_seconds = settings.demo_ticket_feed_interval_seconds
        await ticket_feeder.start()


@app.on_event("shutdown")
async def on_shutdown():
    if settings.demo_ticket_feed_enabled:
        await ticket_feeder.stop()

app.include_router(tickets.router)
app.include_router(associates.router)
app.include_router(routing.router)
app.include_router(auth_router.router)
app.include_router(ticket_stream.router)

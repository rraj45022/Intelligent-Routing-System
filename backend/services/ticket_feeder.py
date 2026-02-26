import asyncio
import itertools
import logging
import random
from datetime import datetime

from fastapi import HTTPException

from backend.core.db import AsyncSessionLocal
from backend.models.tickets import PriorityEnum, StatusEnum, Ticket
from backend.schemas.ticket import TicketCreate, TicketOut
from backend.services.routing_services import pick_associate_for_ticket
from backend.ws.ticket_stream import broadcast_ticket_event

logger = logging.getLogger(__name__)

# Simple pools of demo values to create variety.
MODULES = ["billing", "auth", "search", "shipping", "catalog", "analytics"]
CUSTOMER_SEGMENTS = ["retail", "enterprise", "partner"]
CHANNELS = ["web", "mobile", "support", "chat"]
PRIORITIES = [PriorityEnum.Low, PriorityEnum.Medium, PriorityEnum.High, PriorityEnum.Critical]


class TicketFeeder:
    """Fire-and-forget background loop that emits demo tickets on a cadence."""

    def __init__(self, interval_seconds: float = 10.0) -> None:
        self.interval_seconds = interval_seconds
        self._task: asyncio.Task | None = None
        self._running = False
        self._counter = itertools.count(1)

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Ticket feeder started with %.1f second interval", self.interval_seconds)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Ticket feeder stopped")

    async def _run(self) -> None:
        while self._running:
            try:
                await self._emit_one()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Ticket feeder encountered an error")
            await asyncio.sleep(self.interval_seconds)

    async def _emit_one(self) -> None:
        seq = next(self._counter)
        ticket_in = self._build_ticket(seq)

        async with AsyncSessionLocal() as db:
            try:
                decision = await pick_associate_for_ticket(db, ticket_in)
            except HTTPException as exc:
                logger.warning("Ticket feeder skipped ticket %s: %s", seq, exc.detail)
                return

            ticket = Ticket(
                title=ticket_in.title,
                description=ticket_in.description,
                module=ticket_in.module,
                priority=ticket_in.priority,
                customer_segment=ticket_in.customer_segment,
                channel=ticket_in.channel,
                status=StatusEnum.Open,
                assigned_associate_id=decision.chosen_associate_id,
                created_at=datetime.utcnow(),
            )

            db.add(ticket)
            await db.commit()
            await db.refresh(ticket)

        await broadcast_ticket_event(
            {
                "type": "ticket.created",
                "payload": TicketOut.from_orm(ticket).model_dump(),
            }
        )
        logger.debug("Ticket feeder created ticket id=%s", ticket.id)

    def _build_ticket(self, seq: int) -> TicketCreate:
        module = random.choice(MODULES)
        priority = random.choice(PRIORITIES)
        segment = random.choice(CUSTOMER_SEGMENTS)
        channel = random.choice(CHANNELS)
        title = f"[Auto #{seq}] {module.capitalize()} incident"
        description = (
            f"Auto-generated ticket {seq} for module {module} with priority {priority.value}."
        )
        return TicketCreate(
            title=title,
            description=description,
            module=module,
            priority=priority,
            customer_segment=segment,
            channel=channel,
        )


# Shared singleton used by application lifecycle hooks
# Interval is injected via settings at startup to keep config in one place.
ticket_feeder = TicketFeeder()

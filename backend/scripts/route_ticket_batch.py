"""Route a batch of tickets from a JSON array or JSONL file.

Run with:
./venv/bin/python -m backend.scripts.route_ticket_batch sample_tickets.json --chunk-size 25
"""

import argparse
import asyncio
import json
from pathlib import Path

from backend.core.config import settings
from backend.core.db import AsyncSessionLocal
from backend.models.batch_ingestion import BatchIngestionJob
from backend.models.tickets import StatusEnum, Ticket
from backend.schemas.ticket import TicketCreate
from backend.services.audit_service import log_routing_decision
from backend.services.ingestion_service import (
    create_batch_job,
    finalize_job,
    get_job_items,
    mark_item_failure,
    mark_item_success,
    mark_job_running,
)
from backend.services.routing_services import route_tickets_batch


def _load_tickets(input_path: Path) -> list[TicketCreate]:
    raw = input_path.read_text(encoding="utf-8").strip()
    if not raw:
        return []

    if raw.startswith("["):
        payload = json.loads(raw)
    else:
        payload = [json.loads(line) for line in raw.splitlines() if line.strip()]
    return [TicketCreate.model_validate(item) for item in payload]


async def _persist_tickets(session, tickets: list[TicketCreate], decisions) -> None:
    created_tickets: list[Ticket] = []
    for ticket_in, decision in zip(tickets, decisions):
        ticket = Ticket(
            title=ticket_in.title,
            description=ticket_in.description,
            module=ticket_in.module,
            priority=ticket_in.priority,
            customer_segment=ticket_in.customer_segment,
            channel=ticket_in.channel,
            status=StatusEnum.Open,
            assigned_associate_id=decision.chosen_associate_id,
        )
        session.add(ticket)
        created_tickets.append(ticket)
    await session.flush()
    return created_tickets


async def route_batch(input_path: Path, chunk_size: int, persist: bool, job_name: str | None) -> None:
    tickets = _load_tickets(input_path)
    if not tickets:
        print("No tickets found in input file.")
        return

    async with AsyncSessionLocal() as session:
        batch_job = await create_batch_job(
            session,
            job_name=job_name or input_path.stem,
            source_name=str(input_path),
            chunk_size=chunk_size,
            tickets=tickets,
        )
        await mark_job_running(session, batch_job)
        items = await get_job_items(session, batch_job.id)
        total = 0
        for start in range(0, len(tickets), chunk_size):
            chunk = tickets[start : start + chunk_size]
            chunk_items = items[start : start + chunk_size]
            created_tickets = []
            try:
                decisions = await route_tickets_batch(session, chunk)
                if persist:
                    created_tickets = await _persist_tickets(session, chunk, decisions)

                for index, (ticket_in, decision, item) in enumerate(zip(chunk, decisions, chunk_items)):
                    created_ticket = created_tickets[index] if created_tickets else None
                    mark_item_success(
                        item,
                        associate_id=decision.chosen_associate_id,
                        strategy=decision.strategy,
                        confidence=decision.confidence,
                        ticket_id=created_ticket.id if created_ticket else None,
                    )
                    await log_routing_decision(
                        session,
                        decision,
                        ticket_id=created_ticket.id if created_ticket else None,
                        ingestion_job_id=batch_job.id,
                        ingestion_item_id=item.id,
                    )
                await session.commit()
            except Exception as exc:
                for item in chunk_items:
                    mark_item_failure(item, error_message=str(exc))
                await session.commit()
                raise

            total += len(chunk)
            print(f"Processed chunk {start // chunk_size + 1}: tickets={len(chunk)} total={total}")
            for ticket_in, decision in zip(chunk[:3], decisions[:3]):
                print(
                    json.dumps(
                        {
                            "ticket_title": ticket_in.title,
                            "chosen_associate": decision.chosen_associate_name,
                            "strategy": decision.strategy,
                            "confidence": decision.confidence,
                        }
                    )
                )
        await finalize_job(session, batch_job)
        print(json.dumps({"job_id": batch_job.id, "job_name": batch_job.job_name, "status": batch_job.status.value}))


def main() -> None:
    parser = argparse.ArgumentParser(description="Route a batch of tickets from a JSON file.")
    parser.add_argument("input_path", type=Path)
    parser.add_argument("--chunk-size", type=int, default=settings.routing_batch_size)
    parser.add_argument("--persist", action="store_true")
    parser.add_argument("--job-name", type=str, default=None)
    args = parser.parse_args()
    asyncio.run(route_batch(args.input_path, args.chunk_size, args.persist, args.job_name))


if __name__ == "__main__":
    main()
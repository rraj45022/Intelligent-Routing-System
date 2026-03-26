from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.batch_ingestion import (
    BatchIngestionItem,
    BatchIngestionJob,
    BatchItemStatus,
    BatchJobStatus,
)
from backend.schemas.ticket import TicketCreate


async def create_batch_job(
    db: AsyncSession,
    *,
    job_name: str,
    source_name: str,
    chunk_size: int,
    tickets: list[TicketCreate],
) -> BatchIngestionJob:
    job = BatchIngestionJob(
        job_name=job_name,
        source_name=source_name,
        status=BatchJobStatus.pending,
        total_tickets=len(tickets),
        chunk_size=chunk_size,
    )
    db.add(job)
    await db.flush()

    for index, ticket in enumerate(tickets, start=1):
        db.add(
            BatchIngestionItem(
                job_id=job.id,
                external_ticket_ref=f"{job_name}-{index}",
                ticket_payload=ticket.model_dump(mode="json"),
                status=BatchItemStatus.pending,
            )
        )

    await db.commit()
    await db.refresh(job)
    return job


async def mark_job_running(db: AsyncSession, job: BatchIngestionJob) -> None:
    job.status = BatchJobStatus.running
    job.started_at = datetime.utcnow()
    await db.commit()


async def get_job_items(db: AsyncSession, job_id: int) -> list[BatchIngestionItem]:
    result = await db.execute(
        select(BatchIngestionItem).where(BatchIngestionItem.job_id == job_id).order_by(BatchIngestionItem.id)
    )
    return result.scalars().all()


def mark_item_success(
    item: BatchIngestionItem,
    *,
    associate_id: int,
    strategy: str,
    confidence: float,
    ticket_id: int | None,
) -> None:
    item.status = BatchItemStatus.persisted if ticket_id is not None else BatchItemStatus.routed
    item.chosen_associate_id = associate_id
    item.routing_strategy = strategy
    item.confidence = confidence
    item.ticket_id = ticket_id
    item.processed_at = datetime.utcnow()
    item.error_message = None


def mark_item_failure(item: BatchIngestionItem, *, error_message: str) -> None:
    item.status = BatchItemStatus.failed
    item.error_message = error_message
    item.processed_at = datetime.utcnow()


async def finalize_job(db: AsyncSession, job: BatchIngestionJob) -> None:
    items = await get_job_items(db, job.id)
    processed = sum(1 for item in items if item.status != BatchItemStatus.pending)
    succeeded = sum(1 for item in items if item.status in (BatchItemStatus.routed, BatchItemStatus.persisted))
    failed = sum(1 for item in items if item.status == BatchItemStatus.failed)

    job.processed_tickets = processed
    job.succeeded_tickets = succeeded
    job.failed_tickets = failed
    job.completed_at = datetime.utcnow()
    if failed and succeeded:
        job.status = BatchJobStatus.partial
    elif failed:
        job.status = BatchJobStatus.failed
    else:
        job.status = BatchJobStatus.completed

    await db.commit()
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.ticket_history import TicketHistory
from backend.models.tickets import Ticket


async def sync_resolved_ticket_to_history(db: AsyncSession, ticket: Ticket) -> None:
    if ticket.status.value != "Resolved":
        return
    if ticket.assigned_associate_id is None or ticket.resolved_at is None:
        return

    result = await db.execute(
        select(TicketHistory).where(TicketHistory.source_ticket_id == ticket.id)
    )
    history = result.scalar_one_or_none()

    if history is None:
        history = TicketHistory(source_ticket_id=ticket.id)
        db.add(history)

    history.title = ticket.title
    history.description = ticket.description
    history.module = ticket.module
    history.priority = ticket.priority
    history.customer_segment = ticket.customer_segment
    history.channel = ticket.channel
    history.created_at = ticket.created_at
    history.resolved_at = ticket.resolved_at
    history.resolved_by_associate_id = ticket.assigned_associate_id
    history.resolution_hours = ticket.resolution_hours
    history.csat_score = ticket.csat_score
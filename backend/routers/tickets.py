from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.db import get_db
from backend.models.tickets import StatusEnum, Ticket
from backend.schemas.ticket import TicketCreate, TicketOut, TicketUpdate
from backend.services.auth import get_current_active_user
from backend.services.routing_services import pick_associate_for_ticket
from backend.ws.ticket_stream import broadcast_ticket_event

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
    dependencies=[Depends(get_current_active_user)],
)

@router.post("/", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_in: TicketCreate,
    db: AsyncSession = Depends(get_db),
):
    # call routing logic
    decision = await pick_associate_for_ticket(db, ticket_in)

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

    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)

    await broadcast_ticket_event(
        {
            "type": "ticket.created",
            "payload": TicketOut.from_orm(ticket).model_dump(),
        }
    )

    return ticket

@router.get("/", response_model=list[TicketOut])
async def list_tickets(
    db: AsyncSession = Depends(get_db),
    status_filter: StatusEnum | None = None,
):
    stmt = select(Ticket)
    if status_filter:
        stmt = stmt.where(Ticket.status == status_filter)

    result = await db.execute(stmt.order_by(Ticket.created_at.desc()))
    tickets = result.scalars().all()
    return tickets

@router.patch("/{ticket_id}", response_model=TicketOut)
async def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    original_status = ticket.status
    if ticket_update.status is not None:
        ticket.status = ticket_update.status
    if ticket_update.assigned_associate_id is not None:
        ticket.assigned_associate_id = ticket_update.assigned_associate_id

        if (
            ticket_update.status == StatusEnum.Resolved
            and original_status != StatusEnum.Resolved
            and ticket.resolved_at is None
        ):
            ticket.resolved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(ticket)

    await broadcast_ticket_event(
        {
            "type": "ticket.updated",
            "payload": TicketOut.from_orm(ticket).model_dump(),
        }
    )
    return ticket

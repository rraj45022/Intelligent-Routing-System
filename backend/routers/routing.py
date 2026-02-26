from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.db import get_db
from backend.models.user import UserRole
from backend.schemas.routing import RoutingDecision
from backend.schemas.ticket import TicketCreate
from backend.services.auth import require_role
from backend.services.routing_services import pick_associate_for_ticket

router = APIRouter(
	prefix="/routing",
	tags=["routing"],
	dependencies=[Depends(require_role(UserRole.admin))],
)


@router.post("/preview", response_model=RoutingDecision)
async def preview_routing(
	ticket_in: TicketCreate,
	db: AsyncSession = Depends(get_db),
):
	decision = await pick_associate_for_ticket(db, ticket_in)
	return decision

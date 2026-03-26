from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.db import get_db
from backend.models.associate import Associate
from backend.models.user import UserRole
from backend.schemas.associate import AssociateCreate, AssociateOut
from backend.services.auth import get_current_active_user, require_role

router = APIRouter(
	prefix="/associates",
	tags=["associates"],
	dependencies=[Depends(get_current_active_user)],
)


@router.post("/", response_model=AssociateOut, status_code=status.HTTP_201_CREATED)
async def create_associate(
	associate_in: AssociateCreate,
	db: AsyncSession = Depends(get_db),
	_: None = Depends(require_role(UserRole.admin)),
):
	associate = Associate(
		name=associate_in.name,
		skills=associate_in.skills,
		skill_levels=associate_in.skill_levels,
		active=associate_in.active,
		availability_status=associate_in.availability_status,
		daily_capacity=associate_in.daily_capacity,
		max_concurrent_tickets=associate_in.max_concurrent_tickets,
	)
	db.add(associate)
	await db.commit()
	await db.refresh(associate)
	return associate


@router.get("/", response_model=list[AssociateOut])
async def list_associates(
	active_only: bool | None = None,
	db: AsyncSession = Depends(get_db),
):
	stmt = select(Associate)
	if active_only is True:
		stmt = stmt.where(Associate.active.is_(True))
	if active_only is False:
		stmt = stmt.where(Associate.active.is_(False))

	result = await db.execute(stmt.order_by(Associate.name))
	return result.scalars().all()


@router.get("/{associate_id}", response_model=AssociateOut)
async def get_associate(
	associate_id: int,
	db: AsyncSession = Depends(get_db),
):
	result = await db.execute(select(Associate).where(Associate.id == associate_id))
	associate = result.scalar_one_or_none()
	if not associate:
		raise HTTPException(status_code=404, detail="Associate not found")
	return associate

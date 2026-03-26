from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.db import get_db
from backend.models.associate import Associate
from backend.models.batch_ingestion import BatchIngestionJob
from backend.models.routing_audit import RoutingDecisionAudit
from backend.models.ticket_history import TicketHistory
from backend.models.tickets import StatusEnum, Ticket
from backend.models.user import UserRole
from backend.schemas.ops_dashboard import (
	AssociateLoadSnapshot,
	OpsMetric,
	RecentAuditDecision,
	RecentBatchJob,
	RoutingOpsDashboard,
	StrategyStat,
)
from backend.schemas.routing import RoutingDecision
from backend.schemas.ticket import TicketCreate
from backend.services.auth import require_role
from backend.services.routing_services import pick_associate_for_ticket, route_tickets_batch

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


@router.post("/batch-preview", response_model=list[RoutingDecision])
async def preview_batch_routing(
	tickets_in: list[TicketCreate],
	db: AsyncSession = Depends(get_db),
):
	return await route_tickets_batch(db, tickets_in)


@router.get("/ops/dashboard", response_model=RoutingOpsDashboard)
async def routing_ops_dashboard(
	db: AsyncSession = Depends(get_db),
):
	open_counts_result = await db.execute(
		select(Ticket.assigned_associate_id, func.count(Ticket.id))
		.where(
			Ticket.assigned_associate_id.is_not(None),
			Ticket.status.in_([StatusEnum.Open, StatusEnum.InProgress]),
		)
		.group_by(Ticket.assigned_associate_id)
	)
	open_counts = {associate_id: count for associate_id, count in open_counts_result.all()}

	total_tickets = await db.scalar(select(func.count(Ticket.id))) or 0
	open_tickets = await db.scalar(
		select(func.count(Ticket.id)).where(Ticket.status.in_([StatusEnum.Open, StatusEnum.InProgress]))
	) or 0
	history_count = await db.scalar(select(func.count(TicketHistory.id))) or 0
	active_associates = await db.scalar(select(func.count(Associate.id)).where(Associate.active.is_(True))) or 0
	total_jobs = await db.scalar(select(func.count(BatchIngestionJob.id))) or 0
	total_audits = await db.scalar(select(func.count(RoutingDecisionAudit.id))) or 0

	strategy_rows = (
		await db.execute(
			select(RoutingDecisionAudit.strategy, func.count(RoutingDecisionAudit.id))
			.group_by(RoutingDecisionAudit.strategy)
			.order_by(func.count(RoutingDecisionAudit.id).desc())
		)
	).all()
	strategy_total = sum(count for _, count in strategy_rows) or 1

	associate_rows = (
		await db.execute(select(Associate).order_by(Associate.name))
	).scalars().all()
	daily_counts_result = await db.execute(
		select(Ticket.assigned_associate_id, func.count(Ticket.id))
		.where(
			Ticket.assigned_associate_id.is_not(None),
			func.date(Ticket.created_at) == func.current_date(),
		)
		.group_by(Ticket.assigned_associate_id)
	)
	daily_counts = {associate_id: count for associate_id, count in daily_counts_result.all()}

	recent_jobs = (
		await db.execute(
			select(BatchIngestionJob)
			.order_by(BatchIngestionJob.id.desc())
			.limit(6)
		)
	).scalars().all()

	audit_rows = (
		await db.execute(
			select(RoutingDecisionAudit, Associate.name)
			.join(Associate, Associate.id == RoutingDecisionAudit.chosen_associate_id)
			.order_by(RoutingDecisionAudit.id.desc())
			.limit(8)
		)
	).all()

	artifact_path = str(Path(settings.routing_artifact_dir) / settings.routing_similarity_artifact_name)

	return RoutingOpsDashboard(
		metrics=[
			OpsMetric(label="Live tickets", value=int(open_tickets), detail=f"{int(total_tickets)} total tickets"),
			OpsMetric(label="History corpus", value=int(history_count), detail="Resolved tickets available for retrieval"),
			OpsMetric(label="Active associates", value=int(active_associates), detail="Agents considered for routing"),
			OpsMetric(label="Batch jobs", value=int(total_jobs), detail=f"{int(total_audits)} routing audit rows"),
		],
		strategy_breakdown=[
			StrategyStat(strategy=strategy, count=int(count), share=round(count / strategy_total, 4))
			for strategy, count in strategy_rows
		],
		associate_load=[
			AssociateLoadSnapshot(
				associate_id=associate.id,
				associate_name=associate.name,
				availability_status=associate.availability_status.value,
				open_tickets=int(open_counts.get(associate.id, 0)),
				daily_assigned=int(daily_counts.get(associate.id, 0)),
				daily_capacity=associate.daily_capacity,
				max_concurrent_tickets=associate.max_concurrent_tickets,
				top_skills=list((associate.skill_levels or {}).keys())[:3] or list((associate.skills or [])[:3]),
			)
			for associate in associate_rows
		],
		recent_jobs=[
			RecentBatchJob(
				id=job.id,
				job_name=job.job_name,
				source_name=job.source_name,
				status=job.status.value,
				total_tickets=job.total_tickets,
				processed_tickets=job.processed_tickets,
				succeeded_tickets=job.succeeded_tickets,
				failed_tickets=job.failed_tickets,
				chunk_size=job.chunk_size,
				requested_at=job.requested_at.isoformat(),
				completed_at=job.completed_at.isoformat() if job.completed_at else None,
			)
			for job in recent_jobs
		],
		recent_audits=[
			RecentAuditDecision(
				id=audit.id,
				ticket_id=audit.ticket_id,
				strategy=audit.strategy,
				confidence=audit.confidence,
				chosen_associate_id=audit.chosen_associate_id,
				chosen_associate_name=associate_name,
				llm_used=audit.llm_used,
				matched_history_similarity=audit.matched_history_similarity,
				reason=audit.reason,
				created_at=audit.created_at.isoformat(),
			)
			for audit, associate_name in audit_rows
		],
		artifact_path=artifact_path,
		embedding_model_name=settings.routing_embedding_model_name,
	)

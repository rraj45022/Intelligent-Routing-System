from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.routing_audit import RoutingDecisionAudit
from backend.schemas.routing import RoutingDecision


async def log_routing_decision(
    db: AsyncSession,
    decision: RoutingDecision,
    *,
    ticket_id: int | None = None,
    ingestion_job_id: int | None = None,
    ingestion_item_id: int | None = None,
) -> RoutingDecisionAudit:
    audit = RoutingDecisionAudit(
        ticket_id=ticket_id,
        ingestion_job_id=ingestion_job_id,
        ingestion_item_id=ingestion_item_id,
        chosen_associate_id=decision.chosen_associate_id,
        strategy=decision.strategy,
        confidence=decision.confidence,
        llm_used=decision.llm_used,
        matched_history_id=decision.matched_history_id,
        matched_history_similarity=decision.matched_history_similarity,
        reason=decision.reason,
        candidate_snapshot=[candidate.model_dump() for candidate in decision.candidates],
    )
    db.add(audit)
    await db.flush()
    return audit
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.models.associate import Associate, AvailabilityStatus
from backend.models.ticket_history import TicketHistory
from backend.models.tickets import StatusEnum, Ticket
from backend.schemas.routing import RoutingCandidate, RoutingDecision
from backend.schemas.ticket import TicketCreate
from backend.services import llm_router, model_registry


def _utc_day_start() -> datetime:
    now = datetime.utcnow()
    return datetime(now.year, now.month, now.day)


async def _load_routing_state(
    db: AsyncSession,
) -> tuple[list[Associate], list[TicketHistory], dict[int, int], dict[int, int]]:
    associates_result = await db.execute(select(Associate).where(Associate.active.is_(True)))
    associates = associates_result.scalars().all()

    history_result = await db.execute(
        select(TicketHistory).order_by(TicketHistory.resolved_at.desc())
    )
    history_rows = history_result.scalars().all()

    open_counts_result = await db.execute(
        select(Ticket.assigned_associate_id, func.count(Ticket.id))
        .where(
            Ticket.assigned_associate_id.is_not(None),
            Ticket.status.in_([StatusEnum.Open, StatusEnum.InProgress]),
        )
        .group_by(Ticket.assigned_associate_id)
    )
    open_ticket_counts = {associate_id: count for associate_id, count in open_counts_result.all()}

    day_start = _utc_day_start()
    daily_counts_result = await db.execute(
        select(Ticket.assigned_associate_id, func.count(Ticket.id))
        .where(
            Ticket.assigned_associate_id.is_not(None),
            Ticket.created_at >= day_start,
        )
        .group_by(Ticket.assigned_associate_id)
    )
    daily_assigned_counts = {associate_id: count for associate_id, count in daily_counts_result.all()}

    return associates, history_rows, open_ticket_counts, daily_assigned_counts


def _candidate_from_score(
    associate: Associate,
    score: model_registry.AssociateRoutingScore,
    llm_score: float | None = None,
    source: str | None = None,
) -> RoutingCandidate:
    return RoutingCandidate(
        associate_id=associate.id,
        associate_name=associate.name,
        score=round(score.final_score if llm_score is None else ((1 - settings.llm_weight) * score.final_score + settings.llm_weight * llm_score), 4),
        skill_score=score.skill_score,
        workload_score=score.workload_score,
        llm_score=llm_score,
        source=source,
    )


def _is_assignable(
    associate: Associate,
    score: model_registry.AssociateRoutingScore | None,
) -> bool:
    if associate.availability_status == AvailabilityStatus.offline:
        return False
    if score is None:
        return True
    return score.capacity_remaining > 0


async def _route_ticket_with_state(
    ticket_in: TicketCreate,
    associates: list[Associate],
    history_rows: list[TicketHistory],
    open_ticket_counts: dict[int, int],
    daily_assigned_counts: dict[int, int],
) -> RoutingDecision:
    if not associates:
        raise HTTPException(status_code=400, detail="No active associates available for routing")

    associate_lookup = {associate.id: associate for associate in associates}
    scored_candidates = model_registry.score_candidates(
        ticket_in,
        associates,
        open_ticket_counts=open_ticket_counts,
        daily_assigned_counts=daily_assigned_counts,
    )
    score_lookup = {item.associate_id: item for item in scored_candidates}
    assignable_scores = [
        item for item in scored_candidates if _is_assignable(associate_lookup[item.associate_id], item)
    ]
    ranked_scores = assignable_scores or scored_candidates

    history_matches = model_registry.find_history_matches(
        ticket_in,
        history_rows,
        top_k=settings.history_top_k,
    )
    best_match = history_matches[0] if history_matches else None
    if (
        best_match is not None
        and best_match.similarity >= settings.history_similarity_threshold
        and best_match.resolved_by_associate_id in associate_lookup
    ):
        matched_associate = associate_lookup[best_match.resolved_by_associate_id]
        matched_score = score_lookup.get(matched_associate.id)
        if _is_assignable(matched_associate, matched_score):
            fallback_candidates = [
                _candidate_from_score(associate_lookup[item.associate_id], item, source="skills_workload")
                for item in ranked_scores
                if item.associate_id != matched_associate.id
            ]
            matched_candidate = RoutingCandidate(
                associate_id=matched_associate.id,
                associate_name=matched_associate.name,
                score=round(best_match.similarity, 4),
                skill_score=matched_score.skill_score if matched_score else None,
                workload_score=matched_score.workload_score if matched_score else None,
                source="historical_resolver",
            )
            return RoutingDecision(
                chosen_associate_id=matched_associate.id,
                chosen_associate_name=matched_associate.name,
                confidence=round(best_match.similarity, 4),
                candidates=[matched_candidate, *fallback_candidates[: settings.history_top_k - 1]],
                reason=(
                    f"Assigned to previous resolver from similar history ticket #{best_match.history_id}"
                    f" ('{best_match.title}')"
                ),
                strategy="historical_resolver",
                matched_history_id=best_match.history_id,
                matched_history_similarity=round(best_match.similarity, 4),
            )

    shortlist_scores = ranked_scores[:3]
    llm_used = False
    llm_score_lookup: dict[int, float] = {}
    if shortlist_scores:
        top_score = shortlist_scores[0].final_score
        runner_up = shortlist_scores[1].final_score if len(shortlist_scores) > 1 else 0.0
        low_confidence = top_score < settings.llm_low_confidence_threshold
        narrow_gap = (top_score - runner_up) < settings.llm_candidate_gap_threshold
        if low_confidence or narrow_gap:
            shortlist_associates = [associate_lookup[item.associate_id] for item in shortlist_scores]
            llm_score_lookup = await llm_router.score_with_llm(
                ticket_in,
                shortlist_associates,
                top_k=len(shortlist_associates),
            )
            llm_used = bool(llm_score_lookup)

    candidates: list[RoutingCandidate] = []
    for item in ranked_scores:
        associate = associate_lookup[item.associate_id]
        llm_score = llm_score_lookup.get(item.associate_id)
        candidates.append(
            _candidate_from_score(
                associate,
                item,
                llm_score=llm_score,
                source="llm_reviewed" if llm_score is not None else "skills_workload",
            )
        )

    candidates.sort(key=lambda candidate: candidate.score, reverse=True)
    top_candidate = candidates[0]
    reason = "Skills and workload routing"
    strategy = "skills_workload"
    if llm_used:
        reason = "LLM reviewed top low-confidence candidates after skills/workload scoring"
        strategy = "llm_reviewed"

    return RoutingDecision(
        chosen_associate_id=top_candidate.associate_id,
        chosen_associate_name=top_candidate.associate_name,
        confidence=top_candidate.score,
        candidates=candidates[: settings.history_top_k],
        reason=reason,
        strategy=strategy,
        llm_used=llm_used,
    )

async def pick_associate_for_ticket(
    db: AsyncSession, ticket_in: TicketCreate
) -> RoutingDecision:
    decisions = await route_tickets_batch(db, [ticket_in])
    return decisions[0]


async def route_tickets_batch(
    db: AsyncSession, tickets_in: list[TicketCreate]
) -> list[RoutingDecision]:
    associates, history_rows, open_ticket_counts, daily_assigned_counts = await _load_routing_state(db)
    decisions: list[RoutingDecision] = []
    for ticket_in in tickets_in:
        decision = await _route_ticket_with_state(
            ticket_in,
            associates,
            history_rows,
            open_ticket_counts,
            daily_assigned_counts,
        )
        decisions.append(decision)
        open_ticket_counts[decision.chosen_associate_id] = open_ticket_counts.get(decision.chosen_associate_id, 0) + 1
        daily_assigned_counts[decision.chosen_associate_id] = daily_assigned_counts.get(decision.chosen_associate_id, 0) + 1
    return decisions

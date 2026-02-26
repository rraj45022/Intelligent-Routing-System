from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.models.associate import Associate
from backend.schemas.routing import RoutingCandidate, RoutingDecision
from backend.schemas.ticket import TicketCreate
from backend.services import llm_router, model_registry

async def pick_associate_for_ticket(
    db: AsyncSession, ticket_in: TicketCreate
) -> RoutingDecision:
    result = await db.execute(select(Associate).where(Associate.active == True))
    associates = result.scalars().all()

    if not associates:
        raise HTTPException(status_code=400, detail="No active associates available for routing")

    ml_scored = model_registry.score_candidates(ticket_in, associates)
    ml_lookup = {aid: score for aid, score in ml_scored}

    llm_scores = await llm_router.score_with_llm(ticket_in, associates, top_k=5)
    use_llm = bool(llm_scores)
    llm_weight = settings.llm_weight if use_llm else 0.0

    candidates: list[RoutingCandidate] = []
    for associate in associates:
        ml_score = ml_lookup.get(associate.id, 0.0)
        llm_score = llm_scores.get(associate.id, ml_score)
        blended = (1 - llm_weight) * ml_score + llm_weight * llm_score
        candidates.append(
            RoutingCandidate(
                associate_id=associate.id,
                associate_name=associate.name,
                score=blended,
            )
        )

    candidates.sort(key=lambda c: c.score, reverse=True)
    top = candidates[0]

    return RoutingDecision(
        chosen_associate_id=top.associate_id,
        chosen_associate_name=top.associate_name,
        confidence=top.score,
        candidates=candidates[:5],
        reason=(
            "Blended ML/LLM scoring" if use_llm else "ML scoring (synthetic-trained baseline)"
        ),
    )

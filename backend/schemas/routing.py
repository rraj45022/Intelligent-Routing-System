from pydantic import BaseModel
from typing import List

class RoutingCandidate(BaseModel):
    associate_id: int
    associate_name: str
    score: float
    skill_score: float | None = None
    workload_score: float | None = None
    llm_score: float | None = None
    source: str | None = None

class RoutingDecision(BaseModel):
    chosen_associate_id: int
    chosen_associate_name: str
    confidence: float
    candidates: List[RoutingCandidate]
    reason: str
    strategy: str = "skills_workload"
    matched_history_id: int | None = None
    matched_history_similarity: float | None = None
    llm_used: bool = False

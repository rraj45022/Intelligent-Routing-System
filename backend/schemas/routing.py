from pydantic import BaseModel
from typing import List

class RoutingCandidate(BaseModel):
    associate_id: int
    associate_name: str
    score: float

class RoutingDecision(BaseModel):
    chosen_associate_id: int
    chosen_associate_name: str
    confidence: float
    candidates: List[RoutingCandidate]
    reason: str

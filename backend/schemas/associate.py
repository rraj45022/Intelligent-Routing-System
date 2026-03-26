from typing import Dict, List

from pydantic import BaseModel, Field

from backend.models.associate import AvailabilityStatus

class AssociateBase(BaseModel):
    name: str
    skills: List[str] = Field(default_factory=list)
    skill_levels: Dict[str, float] = Field(default_factory=dict)
    active: bool = True
    availability_status: AvailabilityStatus = AvailabilityStatus.available
    daily_capacity: int = 250
    max_concurrent_tickets: int = 40

class AssociateCreate(AssociateBase):
    pass

class AssociateOut(AssociateBase):
    id: int

    class Config:
        from_attributes = True

from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from backend.models.tickets import PriorityEnum, StatusEnum

class TicketBase(BaseModel):
    title: str
    description: str
    module: str
    priority: PriorityEnum
    customer_segment: str
    channel: str

class TicketCreate(TicketBase):
    pass

class TicketUpdate(BaseModel):
    status: Optional[StatusEnum] = None
    assigned_associate_id: Optional[int] = None

class TicketOut(TicketBase):
    id: int
    status: StatusEnum
    created_at: datetime
    resolved_at: Optional[datetime] = None
    assigned_associate_id: Optional[int] = None
    reopened_flag: bool
    escalated_flag: bool
    resolution_hours: Optional[float] = None
    csat_score: Optional[float] = None

    class Config:
        from_attributes = True
        json_encoders = {StatusEnum: lambda v: v.label}

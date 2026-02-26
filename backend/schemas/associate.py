from pydantic import BaseModel
from typing import List

class AssociateBase(BaseModel):
    name: str
    skills: List[str] = []
    active: bool = True

class AssociateCreate(AssociateBase):
    pass

class AssociateOut(AssociateBase):
    id: int

    class Config:
        from_attributes = True

import enum

from sqlalchemy import Boolean, Enum, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.db import Base


class AvailabilityStatus(str, enum.Enum):
    available = "available"
    busy = "busy"
    offline = "offline"

class Associate(Base):
    __tablename__ = "associates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)  # list of modules
    skill_levels: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    availability_status: Mapped[AvailabilityStatus] = mapped_column(
        Enum(AvailabilityStatus), default=AvailabilityStatus.available, index=True
    )
    daily_capacity: Mapped[int] = mapped_column(Integer, default=250)
    max_concurrent_tickets: Mapped[int] = mapped_column(Integer, default=40)

    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="assigned_associate")

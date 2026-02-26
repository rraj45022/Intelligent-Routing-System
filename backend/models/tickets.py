from datetime import datetime
import enum

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.db import Base
from backend.models.associate import Associate


class EnumWithValue(Enum):
    """Enum type that always binds the Enum member value (not the name)."""

    cache_ok = True

    def bind_processor(self, dialect):
        super_proc = super().bind_processor(dialect)

        def process(value):
            if value is None:
                return None
            if isinstance(value, enum.Enum):
                value = value.value
            return super_proc(value) if super_proc else value

        return process

class PriorityEnum(str, enum.Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"
    Critical = "Critical"


class StatusEnum(str, enum.Enum):
    Open = "Open"
    InProgress = "InProgress"
    Resolved = "Resolved"
    Closed = "Closed"

    @property
    def label(self) -> str:
        if self is StatusEnum.InProgress:
            return "In Progress"
        return self.value


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    module: Mapped[str] = mapped_column(String(50), index=True)
    priority: Mapped[PriorityEnum] = mapped_column(EnumWithValue(PriorityEnum), index=True)
    status: Mapped[StatusEnum] = mapped_column(
        EnumWithValue(StatusEnum), default=StatusEnum.Open, index=True
    )
    customer_segment: Mapped[str] = mapped_column(String(50))
    channel: Mapped[str] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    assigned_associate_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("associates.id"), nullable=True, index=True
    )
    assigned_associate: Mapped[Associate] = relationship("Associate", back_populates="tickets")

    reopened_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    escalated_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    csat_score: Mapped[float | None] = mapped_column(Float, nullable=True)

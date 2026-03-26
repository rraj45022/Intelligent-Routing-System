from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.db import Base
from backend.models.associate import Associate
from backend.models.tickets import EnumWithValue, PriorityEnum


class TicketHistory(Base):
    __tablename__ = "ticket_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_ticket_id: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    priority: Mapped[PriorityEnum] = mapped_column(EnumWithValue(PriorityEnum), nullable=False, index=True)
    customer_segment: Mapped[str] = mapped_column(String(50), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    resolved_by_associate_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("associates.id"), nullable=False, index=True
    )
    resolution_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    csat_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    resolved_by_associate: Mapped[Associate] = relationship("Associate")
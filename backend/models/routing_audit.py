from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.db import Base


class RoutingDecisionAudit(Base):
    __tablename__ = "routing_decision_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("tickets.id"), nullable=True, index=True)
    ingestion_job_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("batch_ingestion_jobs.id"), nullable=True, index=True
    )
    ingestion_item_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("batch_ingestion_items.id"), nullable=True, index=True
    )
    chosen_associate_id: Mapped[int] = mapped_column(Integer, ForeignKey("associates.id"), nullable=False, index=True)
    strategy: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    llm_used: Mapped[bool] = mapped_column(Boolean, default=False)
    matched_history_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("ticket_history.id"), nullable=True, index=True
    )
    matched_history_similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    candidate_snapshot: Mapped[list[dict]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
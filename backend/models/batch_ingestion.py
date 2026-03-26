from datetime import datetime
import enum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.db import Base


class BatchJobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    partial = "partial"


class BatchItemStatus(str, enum.Enum):
    pending = "pending"
    routed = "routed"
    persisted = "persisted"
    failed = "failed"


class BatchIngestionJob(Base):
    __tablename__ = "batch_ingestion_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[BatchJobStatus] = mapped_column(Enum(BatchJobStatus), default=BatchJobStatus.pending, index=True)
    total_tickets: Mapped[int] = mapped_column(Integer, default=0)
    processed_tickets: Mapped[int] = mapped_column(Integer, default=0)
    succeeded_tickets: Mapped[int] = mapped_column(Integer, default=0)
    failed_tickets: Mapped[int] = mapped_column(Integer, default=0)
    chunk_size: Mapped[int] = mapped_column(Integer, default=25)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    items: Mapped[list["BatchIngestionItem"]] = relationship(
        "BatchIngestionItem",
        back_populates="job",
        cascade="all, delete-orphan",
    )


class BatchIngestionItem(Base):
    __tablename__ = "batch_ingestion_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("batch_ingestion_jobs.id"), index=True)
    external_ticket_ref: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    ticket_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[BatchItemStatus] = mapped_column(Enum(BatchItemStatus), default=BatchItemStatus.pending, index=True)
    chosen_associate_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("associates.id"), nullable=True, index=True)
    ticket_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("tickets.id"), nullable=True, index=True)
    routing_strategy: Mapped[str | None] = mapped_column(String(80), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    job: Mapped[BatchIngestionJob] = relationship("BatchIngestionJob", back_populates="items")
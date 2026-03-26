"""Add ticket history table for history-based routing."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


revision: str = "20260326_0002"
down_revision: Union[str, None] = "20260223_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    priority_enum = pg.ENUM(
        "Low", "Medium", "High", "Critical", name="priorityenum", schema="public", create_type=False
    )

    op.create_table(
        "ticket_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_ticket_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("module", sa.String(length=50), nullable=False),
        sa.Column("priority", priority_enum, nullable=False),
        sa.Column("customer_segment", sa.String(length=50), nullable=False),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_by_associate_id", sa.Integer(), sa.ForeignKey("associates.id"), nullable=False),
        sa.Column("resolution_hours", sa.Float(), nullable=True),
        sa.Column("csat_score", sa.Float(), nullable=True),
        sa.UniqueConstraint("source_ticket_id", name="uq_ticket_history_source_ticket_id"),
    )
    op.create_index(op.f("ix_ticket_history_id"), "ticket_history", ["id"], unique=False)
    op.create_index(op.f("ix_ticket_history_source_ticket_id"), "ticket_history", ["source_ticket_id"], unique=False)
    op.create_index(op.f("ix_ticket_history_module"), "ticket_history", ["module"], unique=False)
    op.create_index(op.f("ix_ticket_history_priority"), "ticket_history", ["priority"], unique=False)
    op.create_index(op.f("ix_ticket_history_resolved_at"), "ticket_history", ["resolved_at"], unique=False)
    op.create_index(
        op.f("ix_ticket_history_resolved_by_associate_id"),
        "ticket_history",
        ["resolved_by_associate_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ticket_history_resolved_by_associate_id"), table_name="ticket_history")
    op.drop_index(op.f("ix_ticket_history_resolved_at"), table_name="ticket_history")
    op.drop_index(op.f("ix_ticket_history_priority"), table_name="ticket_history")
    op.drop_index(op.f("ix_ticket_history_module"), table_name="ticket_history")
    op.drop_index(op.f("ix_ticket_history_source_ticket_id"), table_name="ticket_history")
    op.drop_index(op.f("ix_ticket_history_id"), table_name="ticket_history")
    op.drop_table("ticket_history")
"""Initial schema for users, associates, and tickets."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision: str = "20260223_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Clean slate: drop types and tables if they exist, then recreate types
    op.execute("DROP TABLE IF EXISTS tickets CASCADE")
    op.execute("DROP TABLE IF EXISTS associates CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TYPE IF EXISTS public.statusenum CASCADE")
    op.execute("DROP TYPE IF EXISTS public.priorityenum CASCADE")
    op.execute("DROP TYPE IF EXISTS public.userrole CASCADE")

    op.execute("CREATE TYPE public.userrole AS ENUM ('admin', 'agent')")
    op.execute("CREATE TYPE public.priorityenum AS ENUM ('Low', 'Medium', 'High', 'Critical')")
    op.execute("CREATE TYPE public.statusenum AS ENUM ('Open', 'InProgress', 'Resolved', 'Closed')")

    user_role_enum = pg.ENUM("admin", "agent", name="userrole", schema="public", create_type=False)
    priority_enum = pg.ENUM("Low", "Medium", "High", "Critical", name="priorityenum", schema="public", create_type=False)
    status_enum = pg.ENUM(
        "Open", "InProgress", "Resolved", "Closed", name="statusenum", schema="public", create_type=False
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(op.f("uq_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "associates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index(op.f("ix_associates_id"), "associates", ["id"], unique=False)

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("module", sa.String(length=50), nullable=False),
        sa.Column("priority", priority_enum, nullable=False),
        sa.Column(
            "status",
            status_enum,
            nullable=False,
            server_default=sa.text("'Open'"),
        ),
        sa.Column("customer_segment", sa.String(length=50), nullable=False),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_associate_id", sa.Integer(), sa.ForeignKey("associates.id"), nullable=True),
        sa.Column("reopened_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("escalated_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("resolution_hours", sa.Float(), nullable=True),
        sa.Column("csat_score", sa.Float(), nullable=True),
    )
    op.create_index(op.f("ix_tickets_id"), "tickets", ["id"], unique=False)
    op.create_index(op.f("ix_tickets_module"), "tickets", ["module"], unique=False)
    op.create_index(op.f("ix_tickets_priority"), "tickets", ["priority"], unique=False)
    op.create_index(op.f("ix_tickets_status"), "tickets", ["status"], unique=False)
    op.create_index(
        op.f("ix_tickets_assigned_associate_id"),
        "tickets",
        ["assigned_associate_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_tickets_assigned_associate_id"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_status"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_priority"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_module"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_id"), table_name="tickets")
    op.drop_table("tickets")

    op.drop_index(op.f("ix_associates_id"), table_name="associates")
    op.drop_table("associates")

    op.drop_index(op.f("uq_users_email"), table_name="users")
    op.drop_table("users")
    # Leave enums in place to avoid interfering with existing DB types

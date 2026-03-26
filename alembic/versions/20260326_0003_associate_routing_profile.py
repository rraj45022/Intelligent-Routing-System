"""Add associate routing profile fields."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


revision: str = "20260326_0003"
down_revision: Union[str, None] = "20260326_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE public.availabilitystatus AS ENUM ('available', 'busy', 'offline')")
    availability_enum = pg.ENUM(
        "available",
        "busy",
        "offline",
        name="availabilitystatus",
        schema="public",
        create_type=False,
    )

    op.add_column(
        "associates",
        sa.Column("skill_levels", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )
    op.add_column(
        "associates",
        sa.Column(
            "availability_status",
            availability_enum,
            nullable=False,
            server_default=sa.text("'available'"),
        ),
    )
    op.add_column(
        "associates",
        sa.Column("daily_capacity", sa.Integer(), nullable=False, server_default=sa.text("250")),
    )
    op.add_column(
        "associates",
        sa.Column(
            "max_concurrent_tickets",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("40"),
        ),
    )
    op.create_index(op.f("ix_associates_availability_status"), "associates", ["availability_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_associates_availability_status"), table_name="associates")
    op.drop_column("associates", "max_concurrent_tickets")
    op.drop_column("associates", "daily_capacity")
    op.drop_column("associates", "availability_status")
    op.drop_column("associates", "skill_levels")
    op.execute("DROP TYPE IF EXISTS public.availabilitystatus")
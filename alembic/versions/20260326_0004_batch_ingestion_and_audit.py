"""Add batch ingestion and routing audit tables."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


revision: str = "20260326_0004"
down_revision: Union[str, None] = "20260326_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE public.batchjobstatus AS ENUM ('pending', 'running', 'completed', 'failed', 'partial')")
    op.execute("CREATE TYPE public.batchitemstatus AS ENUM ('pending', 'routed', 'persisted', 'failed')")

    batch_job_status = pg.ENUM(
        'pending', 'running', 'completed', 'failed', 'partial',
        name='batchjobstatus', schema='public', create_type=False,
    )
    batch_item_status = pg.ENUM(
        'pending', 'routed', 'persisted', 'failed',
        name='batchitemstatus', schema='public', create_type=False,
    )

    op.create_table(
        'batch_ingestion_jobs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('job_name', sa.String(length=120), nullable=False),
        sa.Column('source_name', sa.String(length=255), nullable=False),
        sa.Column('status', batch_job_status, nullable=False, server_default=sa.text("'pending'")),
        sa.Column('total_tickets', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('processed_tickets', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('succeeded_tickets', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('failed_tickets', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('chunk_size', sa.Integer(), nullable=False, server_default=sa.text('25')),
        sa.Column('requested_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )
    op.create_index(op.f('ix_batch_ingestion_jobs_id'), 'batch_ingestion_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_batch_ingestion_jobs_status'), 'batch_ingestion_jobs', ['status'], unique=False)

    op.create_table(
        'batch_ingestion_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('job_id', sa.Integer(), sa.ForeignKey('batch_ingestion_jobs.id'), nullable=False),
        sa.Column('external_ticket_ref', sa.String(length=120), nullable=True),
        sa.Column('ticket_payload', sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('status', batch_item_status, nullable=False, server_default=sa.text("'pending'")),
        sa.Column('chosen_associate_id', sa.Integer(), sa.ForeignKey('associates.id'), nullable=True),
        sa.Column('ticket_id', sa.Integer(), sa.ForeignKey('tickets.id'), nullable=True),
        sa.Column('routing_strategy', sa.String(length=80), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_batch_ingestion_items_id'), 'batch_ingestion_items', ['id'], unique=False)
    op.create_index(op.f('ix_batch_ingestion_items_job_id'), 'batch_ingestion_items', ['job_id'], unique=False)
    op.create_index(op.f('ix_batch_ingestion_items_external_ticket_ref'), 'batch_ingestion_items', ['external_ticket_ref'], unique=False)
    op.create_index(op.f('ix_batch_ingestion_items_status'), 'batch_ingestion_items', ['status'], unique=False)
    op.create_index(op.f('ix_batch_ingestion_items_chosen_associate_id'), 'batch_ingestion_items', ['chosen_associate_id'], unique=False)
    op.create_index(op.f('ix_batch_ingestion_items_ticket_id'), 'batch_ingestion_items', ['ticket_id'], unique=False)

    op.create_table(
        'routing_decision_audit',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ticket_id', sa.Integer(), sa.ForeignKey('tickets.id'), nullable=True),
        sa.Column('ingestion_job_id', sa.Integer(), sa.ForeignKey('batch_ingestion_jobs.id'), nullable=True),
        sa.Column('ingestion_item_id', sa.Integer(), sa.ForeignKey('batch_ingestion_items.id'), nullable=True),
        sa.Column('chosen_associate_id', sa.Integer(), sa.ForeignKey('associates.id'), nullable=False),
        sa.Column('strategy', sa.String(length=80), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('llm_used', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('matched_history_id', sa.Integer(), sa.ForeignKey('ticket_history.id'), nullable=True),
        sa.Column('matched_history_similarity', sa.Float(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('candidate_snapshot', sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index(op.f('ix_routing_decision_audit_id'), 'routing_decision_audit', ['id'], unique=False)
    op.create_index(op.f('ix_routing_decision_audit_ticket_id'), 'routing_decision_audit', ['ticket_id'], unique=False)
    op.create_index(op.f('ix_routing_decision_audit_ingestion_job_id'), 'routing_decision_audit', ['ingestion_job_id'], unique=False)
    op.create_index(op.f('ix_routing_decision_audit_ingestion_item_id'), 'routing_decision_audit', ['ingestion_item_id'], unique=False)
    op.create_index(op.f('ix_routing_decision_audit_chosen_associate_id'), 'routing_decision_audit', ['chosen_associate_id'], unique=False)
    op.create_index(op.f('ix_routing_decision_audit_strategy'), 'routing_decision_audit', ['strategy'], unique=False)
    op.create_index(op.f('ix_routing_decision_audit_matched_history_id'), 'routing_decision_audit', ['matched_history_id'], unique=False)
    op.create_index(op.f('ix_routing_decision_audit_created_at'), 'routing_decision_audit', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_routing_decision_audit_created_at'), table_name='routing_decision_audit')
    op.drop_index(op.f('ix_routing_decision_audit_matched_history_id'), table_name='routing_decision_audit')
    op.drop_index(op.f('ix_routing_decision_audit_strategy'), table_name='routing_decision_audit')
    op.drop_index(op.f('ix_routing_decision_audit_chosen_associate_id'), table_name='routing_decision_audit')
    op.drop_index(op.f('ix_routing_decision_audit_ingestion_item_id'), table_name='routing_decision_audit')
    op.drop_index(op.f('ix_routing_decision_audit_ingestion_job_id'), table_name='routing_decision_audit')
    op.drop_index(op.f('ix_routing_decision_audit_ticket_id'), table_name='routing_decision_audit')
    op.drop_index(op.f('ix_routing_decision_audit_id'), table_name='routing_decision_audit')
    op.drop_table('routing_decision_audit')

    op.drop_index(op.f('ix_batch_ingestion_items_ticket_id'), table_name='batch_ingestion_items')
    op.drop_index(op.f('ix_batch_ingestion_items_chosen_associate_id'), table_name='batch_ingestion_items')
    op.drop_index(op.f('ix_batch_ingestion_items_status'), table_name='batch_ingestion_items')
    op.drop_index(op.f('ix_batch_ingestion_items_external_ticket_ref'), table_name='batch_ingestion_items')
    op.drop_index(op.f('ix_batch_ingestion_items_job_id'), table_name='batch_ingestion_items')
    op.drop_index(op.f('ix_batch_ingestion_items_id'), table_name='batch_ingestion_items')
    op.drop_table('batch_ingestion_items')

    op.drop_index(op.f('ix_batch_ingestion_jobs_status'), table_name='batch_ingestion_jobs')
    op.drop_index(op.f('ix_batch_ingestion_jobs_id'), table_name='batch_ingestion_jobs')
    op.drop_table('batch_ingestion_jobs')

    op.execute('DROP TYPE IF EXISTS public.batchitemstatus')
    op.execute('DROP TYPE IF EXISTS public.batchjobstatus')
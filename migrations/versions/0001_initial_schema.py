"""Initial Schema Creation

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-08 23:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. data_sources
    op.create_table(
        'data_sources',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('source_type', sa.Enum('OFFICIAL', 'MARKET_DATA', 'UNOFFICIAL_GMP', 'REGISTRAR', name='source_type_enum'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('priority', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('config_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_sources_code'), 'data_sources', ['code'], unique=True)
    op.create_index(op.f('ix_data_sources_id'), 'data_sources', ['id'], unique=False)
    op.create_index(op.f('ix_data_sources_source_type'), 'data_sources', ['source_type'], unique=False)

    # 2. ipos
    op.create_table(
        'ipos',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('bse_code', sa.String(length=20), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('issue_type', sa.Enum('MAINBOARD', 'SME', name='issue_type_enum'), nullable=False),
        sa.Column('status', sa.Enum('UPCOMING', 'OPEN', 'CLOSED', 'ALLOTTED', 'LISTED', 'WITHDRAWN', name='ipo_status_enum'), nullable=False),
        sa.Column('min_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('max_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('issue_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('lot_size', sa.Integer(), nullable=True),
        sa.Column('total_issue_size_cr', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('fresh_issue_cr', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('offer_for_sale_cr', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('open_date', sa.Date(), nullable=True),
        sa.Column('close_date', sa.Date(), nullable=True),
        sa.Column('allotment_date', sa.Date(), nullable=True),
        sa.Column('listing_date', sa.Date(), nullable=True),
        sa.Column('registrar_name', sa.String(length=150), nullable=True),
        sa.Column('registrar_url', sa.String(length=500), nullable=True),
        sa.Column('rhp_url', sa.String(length=500), nullable=True),
        sa.Column('primary_source_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['primary_source_id'], ['data_sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ipos_symbol'), 'ipos', ['symbol'], unique=True)
    op.create_index(op.f('ix_ipos_bse_code'), 'ipos', ['bse_code'], unique=False)
    op.create_index(op.f('ix_ipos_issue_type'), 'ipos', ['issue_type'], unique=False)
    op.create_index(op.f('ix_ipos_status'), 'ipos', ['status'], unique=False)

    # 3. gmp_history
    op.create_table(
        'gmp_history',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('ipo_id', sa.UUID(), nullable=False),
        sa.Column('source_id', sa.UUID(), nullable=False),
        sa.Column('gmp_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('gmp_percent', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('estimated_listing_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('subject_to_sauda', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('observation_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['ipo_id'], ['ipos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ipo_id', 'source_id', 'observation_time', name='uq_gmp_ipo_source_obs_time')
    )
    op.create_index('idx_gmp_ipo_time', 'gmp_history', ['ipo_id', sa.text('observation_time DESC')], unique=False)
    op.create_index('idx_gmp_source_time', 'gmp_history', ['source_id', sa.text('observation_time DESC')], unique=False)

    # 4. subscription_history
    op.create_table(
        'subscription_history',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('ipo_id', sa.UUID(), nullable=False),
        sa.Column('source_id', sa.UUID(), nullable=False),
        sa.Column('qib_x', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('nii_x', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('b_nii_x', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('s_nii_x', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('retail_x', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('employee_x', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('overall_x', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('observation_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['ipo_id'], ['ipos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ipo_id', 'source_id', 'observation_time', name='uq_sub_ipo_source_obs_time')
    )
    op.create_index('idx_sub_ipo_time', 'subscription_history', ['ipo_id', sa.text('observation_time DESC')], unique=False)
    op.create_index('idx_sub_source_time', 'subscription_history', ['source_id', sa.text('observation_time DESC')], unique=False)

    # 5. notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('ipo_id', sa.UUID(), nullable=True),
        sa.Column('telegram_chat_id', sa.String(length=100), nullable=False),
        sa.Column('notification_type', sa.Enum('GMP_SPIKE', 'SUBSCRIPTION_HIGH', 'ALLOTMENT_OUT', 'DAILY_DIGEST', 'IPO_OPENING', name='notification_type_enum'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'SENT', 'FAILED', name='notification_status_enum'), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('source_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['ipo_id'], ['ipos.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_notif_status_type', 'notifications', ['status', 'notification_type'], unique=False)
    op.create_index('idx_notif_chat_created', 'notifications', ['telegram_chat_id', 'created_at'], unique=False)

    # 6. api_requests
    op.create_table(
        'api_requests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('source_id', sa.UUID(), nullable=False),
        sa.Column('endpoint', sa.String(length=500), nullable=False),
        sa.Column('http_method', sa.String(length=10), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('request_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_api_req_source_status', 'api_requests', ['source_id', 'status_code'], unique=False)
    op.create_index('idx_api_req_timestamp', 'api_requests', [sa.text('request_timestamp DESC')], unique=False)

    # 7. workflow_health
    op.create_table(
        'workflow_health',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workflow_name', sa.String(length=100), nullable=False),
        sa.Column('n8n_execution_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('SUCCESS', 'WARNING', 'FAILURE', 'RUNNING', name='health_status_enum'), nullable=False),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('error_log', sa.Text(), nullable=True),
        sa.Column('last_heartbeat', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_wf_name_status', 'workflow_health', ['workflow_name', 'status'], unique=False)
    op.create_index('idx_wf_heartbeat', 'workflow_health', [sa.text('last_heartbeat DESC')], unique=False)

def downgrade() -> None:
    op.drop_table('workflow_health')
    op.drop_table('api_requests')
    op.drop_table('notifications')
    op.drop_table('subscription_history')
    op.drop_table('gmp_history')
    op.drop_table('ipos')
    op.drop_table('data_sources')

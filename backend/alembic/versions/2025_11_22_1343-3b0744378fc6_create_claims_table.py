"""create_claims_table

Revision ID: 3b0744378fc6
Revises: 002
Create Date: 2025-11-22 13:43:14.401131+03:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b0744378fc6'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create claims table
    op.create_table(
        'claims',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('farm_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        
        # Ground Truth fields
        sa.Column('image_url', sa.Text(), nullable=False),
        sa.Column('ml_class', sa.String(50), nullable=False),
        sa.Column('ml_confidence', sa.Float(), nullable=False),
        sa.Column('top_three_classes', sa.JSON(), nullable=True),
        sa.Column('device_tilt', sa.Float(), nullable=True),
        sa.Column('device_azimuth', sa.Float(), nullable=True),
        sa.Column('capture_gps_lat', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('capture_gps_lng', sa.Numeric(precision=11, scale=8), nullable=True),
        
        # Space Truth fields
        sa.Column('ndmi_value', sa.Float(), nullable=True),
        sa.Column('ndmi_14day_avg', sa.Float(), nullable=True),
        sa.Column('satellite_verdict', sa.String(50), nullable=True),
        sa.Column('observation_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cloud_cover_pct', sa.Float(), nullable=True),
        
        # Final Verdict fields
        sa.Column('weighted_score', sa.Float(), nullable=True),
        sa.Column('verdict_explanation', sa.Text(), nullable=True),
        sa.Column('ground_truth_confidence', sa.Float(), nullable=True),
        sa.Column('space_truth_confidence', sa.Float(), nullable=True),
        
        # Payment fields
        sa.Column('payout_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('payout_status', sa.String(50), nullable=True),
        sa.Column('payout_reference', sa.String(255), nullable=True),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='SET NULL'),
    )
    
    # Create indexes
    op.create_index('ix_claims_agent_id', 'claims', ['agent_id'])
    op.create_index('ix_claims_farm_id', 'claims', ['farm_id'])
    op.create_index('ix_claims_status', 'claims', ['status'])
    op.create_index('ix_claims_created_at', 'claims', ['created_at'], postgresql_using='btree', postgresql_ops={'created_at': 'DESC'})


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_claims_created_at', table_name='claims')
    op.drop_index('ix_claims_status', table_name='claims')
    op.drop_index('ix_claims_farm_id', table_name='claims')
    op.drop_index('ix_claims_agent_id', table_name='claims')
    
    # Drop table
    op.drop_table('claims')

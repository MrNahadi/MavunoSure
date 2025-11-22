"""create farms table

Revision ID: 002
Revises: 001
Create Date: 2024-11-22 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create farms table"""
    op.create_table(
        'farms',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('farmer_name', sa.String(length=255), nullable=False),
        sa.Column('farmer_id', sa.String(length=50), nullable=False),
        sa.Column('phone_number', sa.String(length=15), nullable=False),
        sa.Column('crop_type', sa.String(length=50), nullable=False),
        sa.Column('gps_lat', sa.Numeric(precision=10, scale=8), nullable=False),
        sa.Column('gps_lng', sa.Numeric(precision=11, scale=8), nullable=False),
        sa.Column('gps_accuracy', sa.Float, nullable=True),
        sa.Column('registered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('registered_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    
    # Create foreign key to agents table
    op.create_foreign_key(
        'fk_farms_registered_by_agents',
        'farms',
        'agents',
        ['registered_by'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Create indexes for common queries
    op.create_index('ix_farms_farmer_id', 'farms', ['farmer_id'])
    op.create_index('ix_farms_registered_by', 'farms', ['registered_by'])
    
    # Create spatial index for GPS coordinates (for future spatial queries)
    # Note: For production, consider using PostGIS extension for better spatial support
    op.create_index('ix_farms_gps_lat_lng', 'farms', ['gps_lat', 'gps_lng'])


def downgrade() -> None:
    """Drop farms table"""
    op.drop_index('ix_farms_gps_lat_lng', table_name='farms')
    op.drop_index('ix_farms_registered_by', table_name='farms')
    op.drop_index('ix_farms_farmer_id', table_name='farms')
    op.drop_constraint('fk_farms_registered_by_agents', 'farms', type_='foreignkey')
    op.drop_table('farms')

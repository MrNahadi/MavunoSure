"""create agents table

Revision ID: 001
Revises: 
Create Date: 2024-11-21 23:38:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create agents table"""
    op.create_table(
        'agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('phone_number', sa.String(length=15), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create unique constraint on phone_number
    op.create_unique_constraint('uq_agents_phone_number', 'agents', ['phone_number'])
    
    # Create index on phone_number for faster lookups
    op.create_index('ix_agents_phone_number', 'agents', ['phone_number'])


def downgrade() -> None:
    """Drop agents table"""
    op.drop_index('ix_agents_phone_number', table_name='agents')
    op.drop_constraint('uq_agents_phone_number', 'agents', type_='unique')
    op.drop_table('agents')

"""add_payment_transactions_table

Revision ID: b665c3b83713
Revises: 3b0744378fc6
Create Date: 2025-11-22 14:07:05.628487+03:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b665c3b83713'
down_revision = '3b0744378fc6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'payment_transactions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('transaction_id', sa.String(length=50), nullable=False),
        sa.Column('claim_id', sa.UUID(), nullable=False),
        sa.Column('phone_number', sa.String(length=15), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_transactions_transaction_id'), 'payment_transactions', ['transaction_id'], unique=True)
    op.create_index(op.f('ix_payment_transactions_claim_id'), 'payment_transactions', ['claim_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_payment_transactions_claim_id'), table_name='payment_transactions')
    op.drop_index(op.f('ix_payment_transactions_transaction_id'), table_name='payment_transactions')
    op.drop_table('payment_transactions')

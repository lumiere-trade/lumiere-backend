"""
Add last_blockchain_check column to users table.

Revision ID: add_last_blockchain_check
Revises: previous_revision
Create Date: 2025-10-31
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251031_blockchain_check'
down_revision = 'd0c93926b370'  # Update this to last migration ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add last_blockchain_check column."""
    op.add_column(
        'users',
        sa.Column('last_blockchain_check', sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    """Remove last_blockchain_check column."""
    op.drop_column('users', 'last_blockchain_check')

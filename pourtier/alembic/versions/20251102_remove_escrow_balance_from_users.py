"""
Remove escrow balance cache from users table.

Architecture decision: User entity is minimal immutable identity.
- Blockchain is source of truth for balances
- Query real-time instead of caching
- Nothing in User updates after creation

Revision ID: remove_escrow_balance
Revises: remove_escrow_columns
Create Date: 2025-11-02
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "remove_escrow_balance"
down_revision = "remove_escrow_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove cached blockchain data from users table."""
    op.drop_column("users", "escrow_balance")
    op.drop_column("users", "last_blockchain_check")
    op.drop_column("users", "updated_at")


def downgrade() -> None:
    """Restore columns (data will be lost)."""
    op.add_column(
        "users",
        sa.Column(
            "escrow_balance",
            sa.DECIMAL(precision=18, scale=6),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "last_blockchain_check",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

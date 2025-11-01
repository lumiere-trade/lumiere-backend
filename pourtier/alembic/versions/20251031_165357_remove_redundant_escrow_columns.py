"""
Remove redundant escrow columns from users table.

Architecture decision: escrow_account is derived from wallet_address,
not stored. Only cache volatile blockchain data (balance).

Revision ID: remove_escrow_columns
Revises: 20251031_blockchain_check
Create Date: 2025-10-31
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "remove_escrow_columns"
down_revision = "20251031_blockchain_check"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove redundant escrow columns."""
    # Drop index FIRST (before dropping column)
    op.drop_index("ix_users_escrow_account", table_name="users", if_exists=True)

    # Then drop columns
    op.drop_column("users", "escrow_account")
    op.drop_column("users", "escrow_token_mint")
    op.drop_column("users", "escrow_initialized_at")


def downgrade() -> None:
    """Restore removed columns (for rollback)."""
    # Restore columns first
    op.add_column("users", sa.Column("escrow_account", sa.String(44), nullable=True))
    op.add_column("users", sa.Column("escrow_token_mint", sa.String(44), nullable=True))
    op.add_column(
        "users", sa.Column("escrow_initialized_at", sa.DateTime(), nullable=True)
    )

    # Then restore index
    op.create_index(
        "ix_users_escrow_account",
        "users",
        ["escrow_account"],
        unique=False,
        postgresql_where=sa.text("escrow_account IS NOT NULL"),
    )

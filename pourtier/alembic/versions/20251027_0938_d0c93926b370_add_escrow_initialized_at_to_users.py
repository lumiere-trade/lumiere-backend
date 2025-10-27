"""add_escrow_initialized_at_to_users

Revision ID: d0c93926b370
Revises: 6f6dcb3513f2
Create Date: 2025-10-27 09:38:04.168251+00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d0c93926b370"
down_revision: Union[str, Sequence[str], None] = "6f6dcb3513f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add escrow_initialized_at column to users table.

    Backfills existing users who have escrow accounts with their created_at
    timestamp as a reasonable approximation.
    """
    # Add column as nullable
    op.add_column(
        "users",
        sa.Column(
            "escrow_initialized_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    # Backfill for existing users with escrow accounts
    # Use created_at as approximation since we don't have exact initialization time
    op.execute(
        """
        UPDATE users
        SET escrow_initialized_at = created_at
        WHERE escrow_account IS NOT NULL
        AND escrow_initialized_at IS NULL
    """
    )


def downgrade() -> None:
    """
    Remove escrow_initialized_at column from users table.

    WARNING: This will permanently delete initialization timestamps.
    """
    op.drop_column("users", "escrow_initialized_at")

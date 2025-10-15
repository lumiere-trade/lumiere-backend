"""
Add subscription_id to escrow_transactions table.

For tracking which subscription a SUBSCRIPTION_FEE transaction belongs to.
"""

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from pourtier.config.settings import settings


async def migrate():
    """Add subscription_id column to escrow_transactions."""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        # Add subscription_id column (nullable)
        await conn.execute(
            text(
                """
            ALTER TABLE escrow_transactions
            ADD COLUMN IF NOT EXISTS subscription_id UUID;
        """
            )
        )

        print("Added subscription_id to escrow_transactions")

    await engine.dispose()


if __name__ == "__main__":
    print("Adding subscription_id to escrow_transactions...")
    asyncio.run(migrate())

"""
Recreate database tables from SQLAlchemy models.

DANGER: This drops ALL tables and recreates them!
Use only for development/testing.
"""

import asyncio
import sys
from pathlib import Path

from pourtier.config.settings import settings
from pourtier.infrastructure.persistence.database import Database
from pourtier.infrastructure.persistence.models import Base

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def recreate_tables():
    """Drop and recreate all tables."""
    print("RECREATING DATABASE TABLES")
    print("=" * 50)
    print(f"Database: {settings.DATABASE_URL.split('@')[1]}")
    print("WARNING: This will DELETE all data!")
    print("=" * 50)

    # Confirm
    response = input("\nType 'YES' to continue: ")
    if response != "YES":
        print("Aborted")
        return

    print("\n🗑️  Dropping all tables...")
    db = Database(settings.DATABASE_URL)
    await db.connect()

    async with db._engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    print("Tables dropped")

    print("\nCreating new tables from models...")
    async with db._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Tables created")

    await db.disconnect()

    print("\n" + "=" * 50)
    print("Database recreated successfully!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(recreate_tables())

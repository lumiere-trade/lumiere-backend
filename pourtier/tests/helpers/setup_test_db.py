"""
Setup test database script.

Creates pourtier_test_db database and applies schema.

Usage:
    cd ~/lumiere
    python -m pourtier.tests.setup_test_db
"""

import asyncio
import subprocess
import sys
from pathlib import Path

# CRITICAL: Add lumiere root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent  # tests/
POURTIER_DIR = SCRIPT_DIR.parent  # pourtier/
LUMIERE_ROOT = POURTIER_DIR.parent  # lumiere/

# Add lumiere root FIRST
if str(LUMIERE_ROOT) not in sys.path:
    sys.path.insert(0, str(LUMIERE_ROOT))

print(f"📂 Script directory: {SCRIPT_DIR}")
print(f"📂 Pourtier directory: {POURTIER_DIR}")
print(f"📂 Lumiere root: {LUMIERE_ROOT}")
print()

try:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    from pourtier.infrastructure.persistence.models import Base

    print("Successfully imported pourtier modules")
    print()
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Database configuration
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "pourtier_user"
DB_PASSWORD = "pourtier_pass"
DB_NAME = "pourtier_test_db"

# Connection URL
TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@" f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def create_database_with_psql():
    """
    Create test database using psql command as postgres user.

    Uses subprocess to run psql commands with sudo -u postgres.
    """
    print(f"🔍 Creating database '{DB_NAME}' using psql...")

    try:
        # Step 1: Drop database if exists
        print("🗑️  Dropping existing database (if any)...")
        drop_cmd = [
            "sudo",
            "-u",
            "postgres",
            "psql",
            "-c",
            f"DROP DATABASE IF EXISTS {DB_NAME};",
        ]

        result = subprocess.run(
            drop_cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0 and "does not exist" not in result.stderr:
            print(f"Drop warning: {result.stderr}")

        # Step 2: Create database
        print(f"🔨 Creating database '{DB_NAME}'...")
        create_cmd = [
            "sudo",
            "-u",
            "postgres",
            "psql",
            "-c",
            f"CREATE DATABASE {DB_NAME} OWNER {DB_USER};",
        ]

        result = subprocess.run(
            create_cmd,
            capture_output=True,
            text=True,
            check=True,
        )

        if "CREATE DATABASE" in result.stdout:
            print(f"Database '{DB_NAME}' created")
        else:
            print(f"Unexpected output: {result.stdout}")

        # Step 3: Grant privileges
        print(f"🔑 Granting privileges to '{DB_USER}'...")
        grant_cmd = [
            "sudo",
            "-u",
            "postgres",
            "psql",
            "-c",
            f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};",
        ]

        subprocess.run(grant_cmd, capture_output=True, text=True, check=True)
        print("Privileges granted")

        return True

    except subprocess.CalledProcessError as e:
        print(f"Error executing psql command: {e}")
        print(f"   stdout: {e.stdout}")
        print(f"   stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("psql command not found. Is PostgreSQL installed?")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


async def create_tables():
    """Create all tables using SQLAlchemy models."""
    print(f"🔨 Creating tables in '{DB_NAME}'...")

    try:
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await engine.dispose()

        print("All tables created successfully")
        return True

    except Exception as e:
        print(f"Error creating tables: {e}")
        import traceback

        traceback.print_exc()
        return False


async def verify_tables():
    """Verify that all expected tables exist."""
    print(f"🔍 Verifying tables in '{DB_NAME}'...")

    expected_tables = [
        "users",
        "subscriptions",
        "payments",
        "deposits",
        "deployed_strategies",
    ]

    try:
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)

        async with engine.begin() as conn:
            result = await conn.execute(
                text(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                    """
                )
            )
            tables = [row[0] for row in result]

        await engine.dispose()

        print(f"Found {len(tables)} tables:")
        for table in tables:
            status = "[OK]" if table in expected_tables else "[WARN]"
            print(f"  {status} {table}")

        missing_tables = set(expected_tables) - set(tables)
        if missing_tables:
            print(f"Missing tables: {', '.join(missing_tables)}")
            return False

        print("All expected tables exist")
        return True

    except Exception as e:
        print(f"Error verifying tables: {e}")
        return False


async def seed_test_data():
    """Seed database with test data."""
    print("🌱 Seeding test data...")

    try:
        from datetime import datetime, timedelta, timezone
        from uuid import uuid4

        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from pourtier.infrastructure.persistence.models import (
            SubscriptionModel,
            UserModel,
        )

        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            now = datetime.now(timezone.utc)

            test_users = [
                UserModel(
                    id=uuid4(),
                    wallet_address="TestWallet1234567890123456789012345",
                    email="test1@example.com",
                    display_name="Test User 1",
                    created_at=now,
                    updated_at=now,
                ),
                UserModel(
                    id=uuid4(),
                    wallet_address="TestWallet9876543210987654321098765",
                    email="test2@example.com",
                    display_name="Test User 2",
                    created_at=now,
                    updated_at=now,
                ),
            ]

            session.add_all(test_users)
            await session.flush()

            subscription = SubscriptionModel(
                id=uuid4(),
                user_id=test_users[0].id,
                plan_type="basic",
                status="active",
                started_at=now,
                expires_at=now + timedelta(days=30),
                created_at=now,
                updated_at=now,
            )

            session.add(subscription)
            await session.commit()

        await engine.dispose()

        print(f"Seeded {len(test_users)} test users")
        print("Seeded 1 test subscription")
        return True

    except Exception as e:
        print(f"Error seeding test data: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main setup function."""
    print("=" * 60)
    print("POURTIER TEST DATABASE SETUP")
    print("=" * 60)
    print()

    # Create database using psql
    if not create_database_with_psql():
        print("\nSetup failed at database creation")
        print("\n💡 Make sure you can run: sudo -u postgres psql")
        sys.exit(1)

    print()

    # Create tables
    if not await create_tables():
        print("\nSetup failed at table creation")
        sys.exit(1)

    print()

    # Verify tables
    if not await verify_tables():
        print("\nSetup failed at table verification")
        sys.exit(1)

    print()

    # Seed test data
    seed_data = input("🌱 Seed test data? (y/n): ").lower().strip()
    if seed_data == "y":
        print()
        if not await seed_test_data():
            print("\nWarning: Test data seeding failed")
        print()

    print("=" * 60)
    print("TEST DATABASE SETUP COMPLETE")
    print("=" * 60)
    print()
    print(f"Database: {DB_NAME}")
    print(f"Connection: {TEST_DATABASE_URL}")
    print()
    print("Ready to run tests:")
    print("   cd ~/lumiere")
    print("   pytest pourtier/tests/ -v")
    print()


if __name__ == "__main__":
    asyncio.run(main())

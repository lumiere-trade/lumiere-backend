"""
Database initialization script.

Creates pourtier_db database and runs schema.sql migration.
"""

import asyncio
import re
import sys
from pathlib import Path

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pourtier.config.settings import settings  # noqa: E402


def parse_database_url(url: str) -> dict:
    """
    Parse PostgreSQL URL into components.

    Args:
        url: Database URL (postgresql+asyncpg://user:pass@host:port/db)

    Returns:
        Dict with host, port, user, password, database
    """
    # Remove driver prefix
    url = url.replace("postgresql+asyncpg://", "")
    url = url.replace("postgresql://", "")

    # Split credentials and location
    if "@" not in url:
        raise ValueError("Invalid database URL format")

    credentials, location = url.split("@")
    user, password = credentials.split(":")

    # Split host/port and database
    if "/" not in location:
        raise ValueError("Invalid database URL format")

    host_port, database = location.split("/")

    if ":" in host_port:
        host, port = host_port.split(":")
    else:
        host = host_port
        port = "5432"

    return {
        "host": host,
        "port": int(port),
        "user": user,
        "password": password,
        "database": database,
    }


def split_sql_statements(sql: str) -> list:
    """
    Split SQL file into individual statements.

    Args:
        sql: SQL content

    Returns:
        List of SQL statements
    """
    # Remove comments
    sql = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)

    # Split by semicolon (but not inside $$ blocks for functions)
    statements = []
    current = []
    in_function = False

    for line in sql.split("\n"):
        if "$$" in line:
            in_function = not in_function

        current.append(line)

        if ";" in line and not in_function:
            stmt = "\n".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []

    # Add any remaining content
    if current:
        stmt = "\n".join(current).strip()
        if stmt:
            statements.append(stmt)

    return [s for s in statements if s and not s.isspace()]


async def create_database_if_not_exists():
    """Create pourtier_db database if it doesn't exist."""
    print("🔍 Checking if database exists...")

    # Parse database URL
    db_config = parse_database_url(settings.DATABASE_URL)

    try:
        # Connect to postgres default database
        conn = await asyncpg.connect(
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["user"],
            password=db_config["password"],
            database="postgres",
        )

        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            db_config["database"],
        )

        if exists:
            print(f"Database '{db_config['database']}' already exists")
        else:
            print(f"Creating database '{db_config['database']}'...")
            await conn.execute(f'CREATE DATABASE {db_config["database"]}')
            print("Database created successfully")

        await conn.close()

    except Exception as e:
        print(f"Error creating database: {e}")
        raise


async def run_schema_migration():
    """Run schema.sql file to create tables."""
    print("\nRunning schema migration...")

    # Read schema file
    schema_path = (
        Path(__file__).parent.parent / "infrastructure" / "persistence" / "schema.sql"
    )

    if not schema_path.exists():
        print(f"Schema file not found: {schema_path}")
        sys.exit(1)

    with open(schema_path, "r") as f:
        schema_sql = f.read()

    # Split SQL into individual statements
    statements = split_sql_statements(schema_sql)
    print(f"Executing {len(statements)} SQL statements...")

    # Connect to pourtier_db and execute schema
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    success_count = 0
    warning_count = 0

    try:
        # Execute each statement in SEPARATE transaction
        for i, statement in enumerate(statements, 1):
            try:
                async with engine.begin() as conn:
                    await conn.execute(text(statement))
                success_count += 1
            except Exception as e:
                warning_count += 1
                # Only show actual errors (not "already exists")
                error_msg = str(e).lower()
                if "does not exist" in error_msg:
                    print(f"Statement {i} failed: {e}")
                # Silently skip "already exists" warnings
                continue

        print(
            f"Schema migration completed: "
            f"{success_count} success, {warning_count} skipped"
        )

    except Exception as e:
        print(f"Error running schema migration: {e}")
        raise
    finally:
        await engine.dispose()


async def verify_tables():
    """Verify all tables were created."""
    print("\n🔍 Verifying tables...")

    expected_tables = [
        "users",
        "subscriptions",
        "payments",
        "escrow_transactions",
        "legal_documents",
        "user_legal_acceptances",
    ]

    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                    """
                )
            )
            tables = [row[0] for row in result]

        print(f"📋 Found tables: {', '.join(tables)}")

        # Check if all expected tables exist
        missing = set(expected_tables) - set(tables)
        if missing:
            print(f"Missing tables: {', '.join(missing)}")
            return False

        print("All tables created successfully")
        return True

    except Exception as e:
        print(f"Error verifying tables: {e}")
        return False
    finally:
        await engine.dispose()


async def main():
    """Run database initialization."""
    print("Pourtier Database Initialization")
    print("=" * 50)

    # Mask password in URL for display
    display_url = settings.DATABASE_URL
    if "@" in display_url:
        parts = display_url.split("@")
        credentials = parts[0].split("//")[1]
        if ":" in credentials:
            user = credentials.split(":")[0]
            display_url = display_url.replace(credentials, f"{user}:***")

    print(f"Database URL: {display_url}")
    print("=" * 50)
    print()

    try:
        # Step 1: Create database
        await create_database_if_not_exists()

        # Step 2: Run schema migration
        await run_schema_migration()

        # Step 3: Verify tables
        success = await verify_tables()

        if success:
            print("\n" + "=" * 50)
            print("Database initialization completed successfully!")
            print("=" * 50)
        else:
            print("\n" + "=" * 50)
            print("Database initialization completed with warnings")
            print("=" * 50)
            sys.exit(1)

    except Exception as e:
        print("\n" + "=" * 50)
        print(f"Database initialization failed: {e}")
        print("=" * 50)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

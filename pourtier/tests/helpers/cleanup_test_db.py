"""
Cleanup test database script.

Drops pourtier_test_db database.

Usage:
    python tests/cleanup_test_db.py
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database configuration
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "pourtier_user"
DB_PASSWORD = "pourtier_pass"
DB_NAME = "pourtier_test_db"


def cleanup_database():
    """Drop test database."""
    print(f"🗑️  Cleaning up test database '{DB_NAME}'...")

    try:
        # Connect to postgres database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres",
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        exists = cursor.fetchone()

        if not exists:
            print(f"Database '{DB_NAME}' does not exist")
            cursor.close()
            conn.close()
            return True

        # Terminate existing connections
        print("🔌 Terminating active connections...")
        cursor.execute(
            """
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = %s
              AND pid <> pg_backend_pid();
            """,
            (DB_NAME,),
        )

        # Drop database
        print(f"🗑️  Dropping database '{DB_NAME}'...")
        cursor.execute(f'DROP DATABASE "{DB_NAME}"')

        cursor.close()
        conn.close()

        print(f"Database '{DB_NAME}' dropped successfully")
        return True

    except psycopg2.Error as e:
        print(f"Error cleaning up database: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("POURTIER TEST DATABASE CLEANUP")
    print("=" * 60)
    print()

    if cleanup_database():
        print()
        print("Cleanup complete")
    else:
        print()
        print("Cleanup failed")

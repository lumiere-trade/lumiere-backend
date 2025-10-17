"""
Test fixtures and configuration.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from pourtier.infrastructure.persistence.database import Database
from pourtier.infrastructure.persistence.models import Base

# Test database URL (separate from production)
TEST_DATABASE_URL = (
    "postgresql+asyncpg://pourtier_user:pourtier_pass@localhost:5432/"
    "pourtier_test_db"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[Database, None]:
    """
    Create test database and tables.

    Each test gets a clean database.
    """
    # Create engine
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create Database instance
    db = Database(database_url=TEST_DATABASE_URL, echo=False)
    await db.connect()

    yield db

    # Cleanup
    await db.disconnect()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_db: Database) -> AsyncGenerator[AsyncSession, None]:
    """Provide database session for tests."""
    async with test_db.session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_db: Database) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide HTTP client for API testing.

    Override database dependency to use test database.
    """
    from pourtier.di.dependencies import get_db_session

    # Override database dependency
    async def override_get_db_session():
        async with test_db.session() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_wallet_address() -> str:
    """Provide test wallet address."""
    return "FakeWalletAddress1234567890123456789012"


@pytest.fixture
def another_wallet_address() -> str:
    """Provide another test wallet address."""
    return "AnotherWalletAddr9876543210987654321098"

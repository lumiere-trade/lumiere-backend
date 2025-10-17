"""
Database connection and session management.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class Database:
    """
    Async database connection manager using SQLAlchemy.

    Provides session factory and connection pooling.
    Clean architecture - no global state, managed through DI container.
    """

    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
    ):
        """
        Initialize database connection.

        Args:
            database_url: PostgreSQL connection string
            echo: Enable SQL query logging
            pool_size: Number of connections to maintain in pool
            max_overflow: Max connections beyond pool_size
            pool_timeout: Seconds to wait for connection
            pool_recycle: Recycle connections after N seconds
        """
        self.database_url = database_url
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker | None = None

    async def connect(self) -> None:
        """Establish database connection and create session factory."""
        if self._engine is not None:
            return

        self._engine = create_async_engine(
            self.database_url,
            echo=self.echo,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=True,
            connect_args={
                "server_settings": {
                    "application_name": "pourtier",
                }
            },
        )

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def disconnect(self) -> None:
        """Close database connection and cleanup resources."""
        if self._engine is None:
            return

        await self._engine.dispose()
        self._engine = None
        self._session_factory = None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Provide async database session context manager.

        Automatically commits on success, rolls back on exception.

        Usage:
            async with database.session() as session:
                result = await session.execute(query)

        Yields:
            AsyncSession: Database session with transaction management
        """
        if self._session_factory is None:
            raise RuntimeError("Database not connected. Call connect() first.")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def health_check(self) -> bool:
        """
        Check database connectivity.

        Returns:
            True if connection is healthy, False otherwise
        """
        if self._engine is None:
            return False

        try:
            async with self.session() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

"""Redis cache client implementation."""

from typing import Optional

import redis.asyncio as aioredis

from pourtier.infrastructure.cache.i_cache_client import ICacheClient


class RedisCacheClient(ICacheClient):
    """
    Redis cache client using async redis library.

    Provides key-value storage with automatic expiration.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
    ):
        """
        Initialize Redis client configuration.

        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number (0-15)
            password: Redis password (None if no auth)
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password if password else None
        self._client: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        """Establish connection to Redis server."""
        if self._client is not None:
            return

        self._client = await aioredis.from_url(
            f"redis://{self.host}:{self.port}/{self.db}",
            password=self.password,
            encoding="utf-8",
            decode_responses=True,
        )

    async def disconnect(self) -> None:
        """Close connection to Redis server."""
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def set(
        self,
        key: str,
        value: str,
        expire_seconds: Optional[int] = None,
    ) -> bool:
        """
        Store value with optional expiration.

        Args:
            key: Cache key
            value: Value to store
            expire_seconds: TTL in seconds (None = no expiration)

        Returns:
            True if stored successfully
        """
        if self._client is None:
            await self.connect()

        if expire_seconds:
            await self._client.setex(key, expire_seconds, value)
        else:
            await self._client.set(key, value)

        return True

    async def get(self, key: str) -> Optional[str]:
        """
        Retrieve value by key.

        Args:
            key: Cache key

        Returns:
            Value if exists, None otherwise
        """
        if self._client is None:
            await self.connect()

        value = await self._client.get(key)
        return value

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted
        """
        if self._client is None:
            await self.connect()

        result = await self._client.delete(key)
        return result > 0

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        if self._client is None:
            await self.connect()

        result = await self._client.exists(key)
        return result > 0

    async def ping(self) -> bool:
        """
        Check if Redis server is reachable.

        Returns:
            True if server responds
        """
        if self._client is None:
            await self.connect()

        try:
            await self._client.ping()
            return True
        except Exception:
            return False

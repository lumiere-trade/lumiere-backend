"""
Redis-based idempotency store for Passeur.

Implements IdempotencyStore protocol from shared package.
"""

import json
from typing import Any, Optional

import redis.asyncio as aioredis
from shared.resilience import IdempotencyStore

from passeur.config.settings import get_settings


class RedisIdempotencyStore(IdempotencyStore):
    """
    Redis implementation of idempotency store.
    
    Used for financial and security operations to ensure exactly-once semantics.
    Critical for:
    - Escrow withdrawals (prevent double withdrawal)
    - Authority delegation (prevent duplicate delegation)
    - Deposit operations (prevent double deposit)
    """

    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        """
        Initialize Redis idempotency store.

        Args:
            redis_client: Optional Redis client. If None, creates from settings.
        """
        self.redis = redis_client
        self._settings = get_settings()

    async def _ensure_connection(self) -> None:
        """Ensure Redis connection is established."""
        if self.redis is None:
            self.redis = await aioredis.from_url(
                f"redis://{self._settings.redis.host}:{self._settings.redis.port}",
                db=self._settings.redis.db,
                password=self._settings.redis.password,
                socket_timeout=self._settings.redis.socket_timeout,
                socket_connect_timeout=self._settings.redis.socket_connect_timeout,
                decode_responses=False,
            )

    async def get_async(self, key: str) -> Optional[Any]:
        """
        Get value by idempotency key.

        Args:
            key: Idempotency key

        Returns:
            Stored value or None if not found
        """
        await self._ensure_connection()
        
        value = await self.redis.get(f"idempotency:{key}")
        if value:
            return json.loads(value)
        return None

    async def set_async(self, key: str, value: Any, ttl: int) -> None:
        """
        Set value with TTL.

        Args:
            key: Idempotency key
            value: Value to store
            ttl: Time to live in seconds
        """
        await self._ensure_connection()
        
        serialized = json.dumps(value, default=str)
        await self.redis.setex(
            f"idempotency:{key}",
            ttl,
            serialized,
        )

    async def exists_async(self, key: str) -> bool:
        """
        Check if key exists.

        Args:
            key: Idempotency key

        Returns:
            True if key exists
        """
        await self._ensure_connection()
        
        exists = await self.redis.exists(f"idempotency:{key}")
        return bool(exists)

    async def delete_async(self, key: str) -> None:
        """
        Delete key.

        Args:
            key: Idempotency key
        """
        await self._ensure_connection()
        
        await self.redis.delete(f"idempotency:{key}")

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()

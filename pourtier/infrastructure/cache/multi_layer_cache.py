"""
Multi-layer caching strategy.

L1: In-memory cache (cachetools TTLCache) - fastest, local
L2: Redis cache - fast, distributed
L3: Database - slowest, source of truth
"""

import asyncio
import pickle
from typing import Any, Callable, Optional

from cachetools import TTLCache

from pourtier.infrastructure.monitoring import metrics


class MultiLayerCache:
    """
    Multi-layer cache with L1 (memory) and L2 (Redis) tiers.

    Performance:
    - L1 hit: 1-5ms (in-memory)
    - L2 hit: 5-20ms (Redis)
    - L3 miss: 50-200ms (Database)
    """

    def __init__(
        self,
        redis_client: Any,
        l1_maxsize: int = 1000,
        l1_ttl: int = 300,
        l2_ttl: int = 3600,
    ):
        """
        Initialize multi-layer cache.

        Args:
            redis_client: Redis client instance
            l1_maxsize: Max items in L1 cache (default: 1000)
            l1_ttl: L1 TTL in seconds (default: 300s = 5min)
            l2_ttl: L2 TTL in seconds (default: 3600s = 1hour)
        """
        self.redis = redis_client
        self.l1_ttl = l1_ttl
        self.l2_ttl = l2_ttl

        # L1: In-memory TTL cache with LRU eviction
        self.l1_cache = TTLCache(maxsize=l1_maxsize, ttl=l1_ttl)
        self.l1_lock = asyncio.Lock()

    async def get(
        self,
        key: str,
        fetch_func: Optional[Callable] = None,
        key_prefix: str = "cache",
    ) -> Optional[Any]:
        """
        Get value from cache (L1 → L2 → fetch_func).

        Args:
            key: Cache key
            fetch_func: Optional async function to fetch on miss
            key_prefix: Key prefix for namespacing

        Returns:
            Cached value or None
        """
        full_key = f"{key_prefix}:{key}"

        # Try L1 (memory)
        async with self.l1_lock:
            if full_key in self.l1_cache:
                metrics.cache_hits_total.labels(cache_type="L1").inc()
                return self.l1_cache[full_key]

        # Try L2 (Redis)
        try:
            redis_value = await self.redis.get(full_key)
            if redis_value:
                metrics.cache_hits_total.labels(cache_type="L2").inc()

                # Deserialize
                value = pickle.loads(redis_value)

                # Warm L1
                async with self.l1_lock:
                    self.l1_cache[full_key] = value

                return value
        except Exception:
            # Redis error - continue without L2
            pass

        # Cache miss
        metrics.cache_misses_total.labels(cache_type="multi").inc()

        # Fetch from source if function provided
        if fetch_func:
            value = await fetch_func()
            if value is not None:
                await self.set(key, value, key_prefix=key_prefix)
            return value

        return None

    async def set(
        self,
        key: str,
        value: Any,
        key_prefix: str = "cache",
        l1_ttl: Optional[int] = None,
        l2_ttl: Optional[int] = None,
    ) -> None:
        """
        Set value in both L1 and L2 caches.

        Args:
            key: Cache key
            value: Value to cache
            key_prefix: Key prefix for namespacing
            l1_ttl: Override L1 TTL (optional)
            l2_ttl: Override L2 TTL (optional)
        """
        full_key = f"{key_prefix}:{key}"

        # Set in L1 (memory)
        async with self.l1_lock:
            self.l1_cache[full_key] = value

        # Set in L2 (Redis)
        try:
            serialized = pickle.dumps(value)
            ttl = l2_ttl or self.l2_ttl
            await self.redis.setex(full_key, ttl, serialized)
            metrics.cache_operations_total.labels(
                operation="set", cache_type="multi"
            ).inc()
        except Exception:
            # Redis error - continue with L1 only
            pass

    async def delete(self, key: str, key_prefix: str = "cache") -> None:
        """
        Delete from both L1 and L2 caches.

        Args:
            key: Cache key
            key_prefix: Key prefix for namespacing
        """
        full_key = f"{key_prefix}:{key}"

        # Delete from L1
        async with self.l1_lock:
            self.l1_cache.pop(full_key, None)

        # Delete from L2
        try:
            await self.redis.delete(full_key)
            metrics.cache_operations_total.labels(
                operation="delete", cache_type="multi"
            ).inc()
        except Exception:
            pass

    async def invalidate_pattern(self, pattern: str) -> None:
        """
        Invalidate all keys matching pattern in L2 (Redis).

        L1 will expire naturally via TTL.

        Args:
            pattern: Redis key pattern (e.g., "cache:user:*")
        """
        try:
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)

                    # Also remove from L1 if present
                    async with self.l1_lock:
                        for key in keys:
                            self.l1_cache.pop(key.decode("utf-8"), None)

                if cursor == 0:
                    break

            metrics.cache_operations_total.labels(
                operation="invalidate", cache_type="multi"
            ).inc()
        except Exception:
            pass

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with L1 stats
        """
        return {
            "l1_size": len(self.l1_cache),
            "l1_maxsize": self.l1_cache.maxsize,
            "l1_ttl": self.l1_ttl,
            "l2_ttl": self.l2_ttl,
        }

"""
HTTP response caching with Redis.
"""

import hashlib
import json
from functools import wraps
from typing import Any, Callable, Optional

from fastapi import Request


class ResponseCache:
    """Cache HTTP responses in Redis."""

    def __init__(self, redis_client, default_ttl: int = 300):
        """
        Initialize response cache.

        Args:
            redis_client: Redis client instance
            default_ttl: Default TTL in seconds (5 minutes)
        """
        self.redis = redis_client
        self.default_ttl = default_ttl

    def _generate_cache_key(
        self, request: Request, key_prefix: str = "response"
    ) -> str:
        """
        Generate cache key from request.

        Args:
            request: FastAPI request
            key_prefix: Key prefix for namespacing

        Returns:
            Cache key string
        """
        # Include path, query params, and user in key
        path = request.url.path
        query = str(sorted(request.query_params.items()))

        # Include user from auth header if present
        auth_header = request.headers.get("authorization", "")
        user_hash = hashlib.md5(auth_header.encode()).hexdigest()[:8]

        # Generate key
        key_data = f"{path}:{query}:{user_hash}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()

        return f"{key_prefix}:{key_hash}"

    async def get_cached_response(self, cache_key: str) -> Optional[dict]:
        """
        Get cached response from Redis.

        Args:
            cache_key: Cache key

        Returns:
            Cached response dict or None
        """
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            # If cache fails, continue without cache
            pass
        return None

    async def set_cached_response(
        self, cache_key: str, response_data: dict, ttl: Optional[int] = None
    ) -> None:
        """
        Store response in Redis cache.

        Args:
            cache_key: Cache key
            response_data: Response data to cache
            ttl: TTL in seconds (uses default if None)
        """
        try:
            ttl = ttl or self.default_ttl
            await self.redis.setex(cache_key, ttl, json.dumps(response_data))
        except Exception:
            # If cache fails, continue without cache
            pass

    async def invalidate_pattern(self, pattern: str) -> None:
        """
        Invalidate all cache keys matching pattern.

        Args:
            pattern: Redis key pattern (e.g., "response:user:*")
        """
        try:
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception:
            pass


def cache_response(ttl: int = 300, key_prefix: str = "response"):
    """
    Decorator to cache endpoint responses.

    Usage:
        @router.get("/users")
        @cache_response(ttl=3600)
        async def list_users():
            ...

    Args:
        ttl: Cache TTL in seconds
        key_prefix: Cache key prefix
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Extract request from kwargs
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get("request")

            if not request:
                # No request found, execute without cache
                return await func(*args, **kwargs)

            # Get cache instance from app state
            cache: Optional[ResponseCache] = getattr(
                request.app.state, "response_cache", None
            )

            if not cache:
                # Cache not configured, execute without cache
                return await func(*args, **kwargs)

            # Generate cache key
            cache_key = cache._generate_cache_key(request, key_prefix)

            # Try to get from cache
            cached_response = await cache.get_cached_response(cache_key)
            if cached_response:
                return cached_response

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result (only for successful responses)
            if result:
                await cache.set_cached_response(cache_key, result, ttl)

            return result

        return wrapper

    return decorator

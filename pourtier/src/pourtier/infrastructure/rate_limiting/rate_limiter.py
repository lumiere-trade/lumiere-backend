"""
Rate Limiter implementation.

Uses Redis for distributed rate limiting across multiple instances.
Implements sliding window algorithm for accurate rate limiting.
"""

import time
from typing import Optional, Tuple

from pourtier.infrastructure.cache.i_cache_client import ICacheClient


class RateLimiter:
    """
    Distributed rate limiter using Redis sliding window.

    Features:
    - Per-user rate limiting
    - Sliding window algorithm (more accurate than fixed window)
    - Distributed across multiple instances
    - Configurable limits per endpoint
    """

    def __init__(
        self,
        cache_client: ICacheClient,
        default_requests_per_minute: int = 60,
        default_burst_size: int = 10,
    ):
        """
        Initialize rate limiter.

        Args:
            cache_client: Redis cache client for distributed storage
            default_requests_per_minute: Default rate limit (60 req/min)
            default_burst_size: Burst allowance (10 extra requests)
        """
        self.cache = cache_client
        self.default_rpm = default_requests_per_minute
        self.default_burst = default_burst_size

    def _make_key(self, identifier: str, endpoint: str) -> str:
        """
        Make Redis key for rate limit tracking.

        Args:
            identifier: User ID or IP address
            endpoint: API endpoint path

        Returns:
            Redis key string
        """
        return f"ratelimit:{identifier}:{endpoint}"

    async def check_rate_limit(
        self,
        identifier: str,
        endpoint: str,
        requests_per_minute: Optional[int] = None,
        burst_size: Optional[int] = None,
    ) -> Tuple[bool, dict]:
        """
        Check if request is within rate limit.

        Uses sliding window algorithm:
        1. Get current timestamp
        2. Remove requests older than 1 minute
        3. Count remaining requests
        4. Check if under limit (RPM + burst)
        5. Add current request if allowed

        Args:
            identifier: User ID or IP address
            endpoint: API endpoint path
            requests_per_minute: Custom RPM (uses default if None)
            burst_size: Custom burst (uses default if None)

        Returns:
            Tuple of (allowed: bool, info: dict with limit details)
        """
        rpm = requests_per_minute or self.default_rpm
        burst = burst_size or self.default_burst
        max_requests = rpm + burst

        key = self._make_key(identifier, endpoint)
        now = time.time()
        window_start = now - 60  # 1 minute window

        # Use Redis pipeline for atomic operations
        pipe = self.cache._client.pipeline()

        # Remove old requests (outside 1-minute window)
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current requests in window
        pipe.zcard(key)

        # Execute pipeline
        _, current_count = await pipe.execute()

        # Check if under limit
        allowed = current_count < max_requests

        if allowed:
            # Add current request with timestamp as score
            await self.cache._client.zadd(key, {str(now): now})

            # Set expiry (2 minutes to be safe)
            await self.cache._client.expire(key, 120)

        # Calculate reset time (when oldest request expires)
        reset_time = int(now + 60)

        # Remaining requests
        remaining = max(0, max_requests - current_count - (1 if allowed else 0))

        info = {
            "limit": max_requests,
            "remaining": remaining,
            "reset": reset_time,
            "retry_after": 60 if not allowed else None,
        }

        return allowed, info

    async def reset_limit(self, identifier: str, endpoint: str) -> None:
        """
        Reset rate limit for user/endpoint.

        Args:
            identifier: User ID or IP address
            endpoint: API endpoint path
        """
        key = self._make_key(identifier, endpoint)
        await self.cache._client.delete(key)

    async def get_limit_info(
        self,
        identifier: str,
        endpoint: str,
        requests_per_minute: Optional[int] = None,
        burst_size: Optional[int] = None,
    ) -> dict:
        """
        Get current rate limit info without consuming a request.

        Args:
            identifier: User ID or IP address
            endpoint: API endpoint path
            requests_per_minute: Custom RPM
            burst_size: Custom burst

        Returns:
            Dict with limit info
        """
        rpm = requests_per_minute or self.default_rpm
        burst = burst_size or self.default_burst
        max_requests = rpm + burst

        key = self._make_key(identifier, endpoint)
        now = time.time()
        window_start = now - 60

        # Remove old and count current
        pipe = self.cache._client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        _, current_count = await pipe.execute()

        remaining = max(0, max_requests - current_count)
        reset_time = int(now + 60)

        return {
            "limit": max_requests,
            "remaining": remaining,
            "reset": reset_time,
            "current": current_count,
        }

"""
Unit tests for RateLimiter.

Tests sliding window rate limiting algorithm.

Usage:
    python tests/unit/infrastructure/test_rate_limiter.py
    laborant pourtier --unit
"""

import time
from unittest.mock import AsyncMock, MagicMock

from pourtier.infrastructure.rate_limiting.rate_limiter import RateLimiter
from shared.tests import LaborantTest


class TestRateLimiter(LaborantTest):
    """Unit tests for RateLimiter."""

    component_name = "pourtier"
    test_category = "unit"

    # ================================================================
    # Helper Methods
    # ================================================================

    def _create_mock_cache(self) -> AsyncMock:
        """Create mock Redis cache client."""
        mock_cache = AsyncMock()
        mock_cache._client = AsyncMock()
        return mock_cache

    def _setup_pipeline_mock(self, mock_cache: AsyncMock, execute_result: list):
        """Setup pipeline mock with correct sync/async mix."""
        # Create sync pipeline object
        mock_pipeline = MagicMock()
        mock_pipeline.zremrangebyscore = MagicMock()
        mock_pipeline.zcard = MagicMock()
        mock_pipeline.execute = AsyncMock(return_value=execute_result)

        # Make pipeline() return sync object (NOT async)
        mock_cache._client.pipeline = MagicMock(return_value=mock_pipeline)

        return mock_pipeline

    def _create_rate_limiter(
        self, cache: AsyncMock, rpm: int = 60, burst: int = 10
    ) -> RateLimiter:
        """Create rate limiter with mock cache."""
        return RateLimiter(
            cache_client=cache,
            default_requests_per_minute=rpm,
            default_burst_size=burst,
        )

    # ================================================================
    # Test Methods
    # ================================================================

    async def test_rate_limiter_allows_first_request(self):
        """Test rate limiter allows first request."""
        self.reporter.info(
            "Testing rate limiter allows first request",
            context="Test",
        )

        mock_cache = self._create_mock_cache()
        self._setup_pipeline_mock(mock_cache, execute_result=[None, 0])
        rate_limiter = self._create_rate_limiter(mock_cache, rpm=60, burst=10)

        # Execute
        allowed, info = await rate_limiter.check_rate_limit(
            identifier="user:123",
            endpoint="/api/users",
        )

        # Verify
        assert allowed is True
        assert info["limit"] == 70  # 60 + 10 burst
        assert info["remaining"] == 69  # 70 - 1
        assert "reset" in info

        self.reporter.info("First request allowed", context="Test")

    async def test_rate_limiter_blocks_after_limit(self):
        """Test rate limiter blocks after reaching limit."""
        self.reporter.info(
            "Testing rate limiter blocks after limit",
            context="Test",
        )

        mock_cache = self._create_mock_cache()
        self._setup_pipeline_mock(mock_cache, execute_result=[None, 70])
        rate_limiter = self._create_rate_limiter(mock_cache, rpm=60, burst=10)

        # Execute
        allowed, info = await rate_limiter.check_rate_limit(
            identifier="user:123",
            endpoint="/api/users",
        )

        # Verify
        assert allowed is False
        assert info["limit"] == 70
        assert info["remaining"] == 0
        assert info["retry_after"] == 60

        # Verify zadd was NOT called (request not added)
        mock_cache._client.zadd.assert_not_called()

        self.reporter.info("Request blocked after limit", context="Test")

    async def test_rate_limiter_uses_sliding_window(self):
        """Test rate limiter uses sliding window algorithm."""
        self.reporter.info(
            "Testing sliding window algorithm",
            context="Test",
        )

        mock_cache = self._create_mock_cache()
        mock_pipeline = self._setup_pipeline_mock(mock_cache, execute_result=[None, 50])
        rate_limiter = self._create_rate_limiter(mock_cache, rpm=60, burst=10)

        # Execute
        await rate_limiter.check_rate_limit(
            identifier="user:123",
            endpoint="/api/users",
        )

        # Verify zremrangebyscore was called (removes old requests)
        mock_pipeline.zremrangebyscore.assert_called_once()

        # Get the call args to verify window calculation
        call_args = mock_pipeline.zremrangebyscore.call_args[0]
        key = call_args[0]
        min_score = call_args[1]
        max_score = call_args[2]

        assert "ratelimit:user:123:/api/users" in key
        assert min_score == 0
        # max_score should be (now - 60 seconds)
        assert max_score < time.time()

        self.reporter.info("Sliding window verified", context="Test")

    async def test_rate_limiter_resets_limit(self):
        """Test rate limiter can reset limit for user."""
        self.reporter.info(
            "Testing rate limit reset",
            context="Test",
        )

        mock_cache = self._create_mock_cache()
        rate_limiter = self._create_rate_limiter(mock_cache)

        # Execute
        await rate_limiter.reset_limit(
            identifier="user:123",
            endpoint="/api/users",
        )

        # Verify delete was called with correct key
        mock_cache._client.delete.assert_called_once()
        call_args = mock_cache._client.delete.call_args[0]
        key = call_args[0]

        assert "ratelimit:user:123:/api/users" in key

        self.reporter.info("Rate limit reset successfully", context="Test")

    async def test_rate_limiter_get_limit_info(self):
        """Test getting rate limit info without consuming request."""
        self.reporter.info(
            "Testing get limit info",
            context="Test",
        )

        mock_cache = self._create_mock_cache()
        self._setup_pipeline_mock(mock_cache, execute_result=[None, 30])
        rate_limiter = self._create_rate_limiter(mock_cache, rpm=60, burst=10)

        # Execute
        info = await rate_limiter.get_limit_info(
            identifier="user:123",
            endpoint="/api/users",
        )

        # Verify
        assert info["limit"] == 70
        assert info["remaining"] == 40  # 70 - 30
        assert info["current"] == 30
        assert "reset" in info

        # Verify zadd was NOT called (info only, no request added)
        mock_cache._client.zadd.assert_not_called()

        self.reporter.info("Limit info retrieved without consuming", context="Test")

    async def test_rate_limiter_custom_limits(self):
        """Test rate limiter with custom per-endpoint limits."""
        self.reporter.info(
            "Testing custom per-endpoint limits",
            context="Test",
        )

        mock_cache = self._create_mock_cache()
        self._setup_pipeline_mock(mock_cache, execute_result=[None, 0])
        rate_limiter = self._create_rate_limiter(mock_cache, rpm=60, burst=10)

        # Execute with custom limits (lower for sensitive endpoint)
        allowed, info = await rate_limiter.check_rate_limit(
            identifier="user:123",
            endpoint="/api/deposit",
            requests_per_minute=10,  # Custom lower limit
            burst_size=2,
        )

        # Verify custom limits applied
        assert info["limit"] == 12  # 10 + 2 burst (not 70)
        assert allowed is True

        self.reporter.info("Custom limits applied correctly", context="Test")

    async def test_rate_limiter_key_generation(self):
        """Test rate limiter generates correct Redis keys."""
        self.reporter.info(
            "Testing rate limiter key generation",
            context="Test",
        )

        mock_cache = self._create_mock_cache()
        rate_limiter = self._create_rate_limiter(mock_cache)

        # Test key generation
        key1 = rate_limiter._make_key("user:123", "/api/users")
        key2 = rate_limiter._make_key("ip:1.2.3.4", "/api/deposit")
        key3 = rate_limiter._make_key("user:456", "/api/users")

        # Verify keys are unique per user/endpoint combination
        assert key1 == "ratelimit:user:123:/api/users"
        assert key2 == "ratelimit:ip:1.2.3.4:/api/deposit"
        assert key3 == "ratelimit:user:456:/api/users"

        # Verify different users/endpoints get different keys
        assert key1 != key2
        assert key1 != key3

        self.reporter.info("Rate limiter keys generated correctly", context="Test")


if __name__ == "__main__":
    TestRateLimiter.run_as_main()

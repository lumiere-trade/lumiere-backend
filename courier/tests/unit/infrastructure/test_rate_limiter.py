"""
Unit tests for RateLimiter.

Tests token bucket rate limiting algorithm.

Usage:
    python -m courier.tests.unit.infrastructure.test_rate_limiter
    laborant courier --unit
"""

import asyncio
from datetime import datetime, timedelta

from shared.tests import LaborantTest

from courier.infrastructure.rate_limiting import RateLimiter


class TestRateLimiter(LaborantTest):
    """Unit tests for RateLimiter."""

    component_name = "courier"
    test_category = "unit"

    # ================================================================
    # Basic rate limiting tests
    # ================================================================

    async def test_allows_requests_within_limit(self):
        """Test allows requests within rate limit."""
        self.reporter.info("Testing requests within limit", context="Test")

        limiter = RateLimiter(limit=5, window_seconds=60)

        # Should allow 5 requests
        for i in range(5):
            result = await limiter.check_rate_limit("service_a")
            assert result is True, f"Request {i+1} should be allowed"

        self.reporter.info("All 5 requests allowed", context="Test")

    async def test_blocks_requests_exceeding_limit(self):
        """Test blocks requests exceeding rate limit."""
        self.reporter.info("Testing requests exceeding limit", context="Test")

        limiter = RateLimiter(limit=3, window_seconds=60)

        # Allow 3 requests
        for i in range(3):
            result = await limiter.check_rate_limit("service_b")
            assert result is True

        # 4th request should be blocked
        result = await limiter.check_rate_limit("service_b")
        assert result is False

        self.reporter.info("4th request blocked as expected", context="Test")

    async def test_different_identifiers_independent(self):
        """Test different identifiers have independent limits."""
        self.reporter.info("Testing independent identifiers", context="Test")

        limiter = RateLimiter(limit=2, window_seconds=60)

        # Service A: 2 requests
        assert await limiter.check_rate_limit("service_a") is True
        assert await limiter.check_rate_limit("service_a") is True

        # Service B: Should still have full limit
        assert await limiter.check_rate_limit("service_b") is True
        assert await limiter.check_rate_limit("service_b") is True

        # Both at limit now
        assert await limiter.check_rate_limit("service_a") is False
        assert await limiter.check_rate_limit("service_b") is False

        self.reporter.info("Identifiers tracked independently", context="Test")

    async def test_sliding_window_allows_new_requests(self):
        """Test sliding window allows requests after old ones expire."""
        self.reporter.info("Testing sliding window", context="Test")

        limiter = RateLimiter(limit=2, window_seconds=1)  # 1 second window

        # Fill limit
        assert await limiter.check_rate_limit("service_c") is True
        assert await limiter.check_rate_limit("service_c") is True
        assert await limiter.check_rate_limit("service_c") is False

        # Wait for window to pass
        await asyncio.sleep(1.1)

        # Should allow new requests
        assert await limiter.check_rate_limit("service_c") is True
        assert await limiter.check_rate_limit("service_c") is True

        self.reporter.info("New requests allowed after window", context="Test")

    # ================================================================
    # Stats and info tests
    # ================================================================

    async def test_get_remaining_returns_correct_count(self):
        """Test get_remaining returns correct remaining count."""
        self.reporter.info("Testing get_remaining", context="Test")

        limiter = RateLimiter(limit=5, window_seconds=60)

        # Initially full limit
        assert limiter.get_remaining("service_d") == 5

        # After 2 requests
        await limiter.check_rate_limit("service_d")
        await limiter.check_rate_limit("service_d")
        assert limiter.get_remaining("service_d") == 3

        # After 3 more (at limit)
        await limiter.check_rate_limit("service_d")
        await limiter.check_rate_limit("service_d")
        await limiter.check_rate_limit("service_d")
        assert limiter.get_remaining("service_d") == 0

        self.reporter.info("Remaining count accurate", context="Test")

    async def test_get_reset_time_returns_correct_time(self):
        """Test get_reset_time returns when limit resets."""
        self.reporter.info("Testing get_reset_time", context="Test")

        limiter = RateLimiter(limit=3, window_seconds=60)

        # No requests yet
        assert limiter.get_reset_time("service_e") is None

        # Make request
        before = datetime.utcnow()
        await limiter.check_rate_limit("service_e")
        datetime.utcnow()

        reset_time = limiter.get_reset_time("service_e")
        assert reset_time is not None

        # Reset should be ~60 seconds from now
        expected_reset = before + timedelta(seconds=60)
        time_diff = abs((reset_time - expected_reset).total_seconds())
        assert time_diff < 2  # Allow 2 second tolerance

        self.reporter.info("Reset time calculated correctly", context="Test")

    async def test_get_retry_after_seconds(self):
        """Test get_retry_after_seconds returns correct wait time."""
        self.reporter.info("Testing get_retry_after_seconds", context="Test")

        limiter = RateLimiter(limit=1, window_seconds=10)

        # Fill limit
        await limiter.check_rate_limit("service_f")

        # Get retry after
        retry_after = limiter.get_retry_after_seconds("service_f")

        # Should be ~10 seconds
        assert 8 <= retry_after <= 11

        self.reporter.info(f"Retry after: {retry_after} seconds", context="Test")

    async def test_get_stats_returns_complete_info(self):
        """Test get_stats returns all rate limit info."""
        self.reporter.info("Testing get_stats", context="Test")

        limiter = RateLimiter(limit=5, window_seconds=60)

        # Make 3 requests
        for _ in range(3):
            await limiter.check_rate_limit("service_g")

        stats = limiter.get_stats("service_g")

        assert stats["identifier"] == "service_g"
        assert stats["limit"] == 5
        assert stats["window_seconds"] == 60
        assert stats["current_count"] == 3
        assert stats["remaining"] == 2
        assert stats["reset_at"] is not None
        assert stats["retry_after_seconds"] > 0

        self.reporter.info("Stats complete and accurate", context="Test")

    # ================================================================
    # Clear and management tests
    # ================================================================

    async def test_clear_specific_identifier(self):
        """Test clearing specific identifier."""
        self.reporter.info("Testing clear specific identifier", context="Test")

        limiter = RateLimiter(limit=2, window_seconds=60)

        # Fill limits for two services
        await limiter.check_rate_limit("service_h")
        await limiter.check_rate_limit("service_h")
        await limiter.check_rate_limit("service_i")

        # Clear service_h
        limiter.clear("service_h")

        # service_h should have full limit again
        assert await limiter.check_rate_limit("service_h") is True
        assert await limiter.check_rate_limit("service_h") is True

        # service_i still at limit
        assert await limiter.check_rate_limit("service_i") is True
        assert await limiter.check_rate_limit("service_i") is False

        self.reporter.info("Specific identifier cleared", context="Test")

    async def test_clear_all_identifiers(self):
        """Test clearing all identifiers."""
        self.reporter.info("Testing clear all identifiers", context="Test")

        limiter = RateLimiter(limit=1, window_seconds=60)

        # Fill limits
        await limiter.check_rate_limit("service_j")
        await limiter.check_rate_limit("service_k")

        # Clear all
        limiter.clear()

        # Both should have full limit
        assert await limiter.check_rate_limit("service_j") is True
        assert await limiter.check_rate_limit("service_k") is True

        self.reporter.info("All identifiers cleared", context="Test")

    async def test_get_all_stats(self):
        """Test getting stats for all identifiers."""
        self.reporter.info("Testing get_all_stats", context="Test")

        limiter = RateLimiter(limit=5, window_seconds=60)

        # Make requests from multiple services
        await limiter.check_rate_limit("service_l")
        await limiter.check_rate_limit("service_m")
        await limiter.check_rate_limit("service_m")

        all_stats = limiter.get_all_stats()

        assert "service_l" in all_stats
        assert "service_m" in all_stats
        assert all_stats["service_l"]["current_count"] == 1
        assert all_stats["service_m"]["current_count"] == 2

        self.reporter.info("All stats retrieved", context="Test")


if __name__ == "__main__":
    TestRateLimiter.run_as_main()

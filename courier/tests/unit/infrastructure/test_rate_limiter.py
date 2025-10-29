"""
Unit tests for RateLimiter.

Tests token bucket rate limiting algorithm including per-message-type limits.

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
    # Per-message-type rate limiting tests (NEW - Phase 2.3)
    # ================================================================

    async def test_per_type_limits_enforced(self):
        """Test per-message-type limits are enforced."""
        self.reporter.info("Testing per-type rate limits", context="Test")

        per_type_limits = {
            "trade": 2,
            "candles": 5,
            "strategy": 1,
        }
        limiter = RateLimiter(
            limit=10,
            window_seconds=60,
            per_type_limits=per_type_limits,
        )

        # Trade messages: 2 allowed
        assert await limiter.check_rate_limit("user_1", "trade") is True
        assert await limiter.check_rate_limit("user_1", "trade") is True
        assert await limiter.check_rate_limit("user_1", "trade") is False

        # Candles messages: 5 allowed
        for i in range(5):
            result = await limiter.check_rate_limit("user_1", "candles")
            assert result is True, f"Candle {i+1} should be allowed"
        assert await limiter.check_rate_limit("user_1", "candles") is False

        # Strategy messages: 1 allowed
        assert await limiter.check_rate_limit("user_1", "strategy") is True
        assert await limiter.check_rate_limit("user_1", "strategy") is False

        self.reporter.info("Per-type limits enforced correctly", context="Test")

    async def test_per_type_fallback_to_global_limit(self):
        """Test fallback to global limit for unconfigured types."""
        self.reporter.info("Testing fallback to global limit", context="Test")

        per_type_limits = {"trade": 2}
        limiter = RateLimiter(
            limit=5,
            window_seconds=60,
            per_type_limits=per_type_limits,
        )

        # Trade: Uses per-type limit (2)
        assert await limiter.check_rate_limit("user_2", "trade") is True
        assert await limiter.check_rate_limit("user_2", "trade") is True
        assert await limiter.check_rate_limit("user_2", "trade") is False

        # Unknown type: Uses global limit (5)
        for i in range(5):
            result = await limiter.check_rate_limit("user_2", "unknown")
            assert result is True, f"Unknown {i+1} should use global limit"
        assert await limiter.check_rate_limit("user_2", "unknown") is False

        self.reporter.info("Fallback to global limit works", context="Test")

    async def test_per_type_independent_per_user(self):
        """Test per-type limits are independent per user."""
        self.reporter.info("Testing per-type limits per user", context="Test")

        per_type_limits = {"trade": 2}
        limiter = RateLimiter(
            limit=10,
            window_seconds=60,
            per_type_limits=per_type_limits,
        )

        # User 1: Fill trade limit
        assert await limiter.check_rate_limit("user_1", "trade") is True
        assert await limiter.check_rate_limit("user_1", "trade") is True
        assert await limiter.check_rate_limit("user_1", "trade") is False

        # User 2: Should have full trade limit
        assert await limiter.check_rate_limit("user_2", "trade") is True
        assert await limiter.check_rate_limit("user_2", "trade") is True
        assert await limiter.check_rate_limit("user_2", "trade") is False

        self.reporter.info("Per-type limits independent per user", context="Test")

    async def test_per_type_get_remaining(self):
        """Test get_remaining with message_type."""
        self.reporter.info("Testing get_remaining with type", context="Test")

        per_type_limits = {"trade": 3, "candles": 5}
        limiter = RateLimiter(
            limit=10,
            window_seconds=60,
            per_type_limits=per_type_limits,
        )

        # Initially full
        assert limiter.get_remaining("user_3", "trade") == 3
        assert limiter.get_remaining("user_3", "candles") == 5

        # After requests
        await limiter.check_rate_limit("user_3", "trade")
        await limiter.check_rate_limit("user_3", "candles")
        await limiter.check_rate_limit("user_3", "candles")

        assert limiter.get_remaining("user_3", "trade") == 2
        assert limiter.get_remaining("user_3", "candles") == 3

        self.reporter.info("get_remaining works with types", context="Test")

    async def test_per_type_get_stats(self):
        """Test get_stats returns per-type information."""
        self.reporter.info("Testing get_stats with type", context="Test")

        per_type_limits = {"trade": 5}
        limiter = RateLimiter(
            limit=10,
            window_seconds=60,
            per_type_limits=per_type_limits,
        )

        # Make requests
        await limiter.check_rate_limit("user_4", "trade")
        await limiter.check_rate_limit("user_4", "trade")

        stats = limiter.get_stats("user_4", "trade")

        assert stats["identifier"] == "user_4"
        assert stats["message_type"] == "trade"
        assert stats["limit"] == 5
        assert stats["current_count"] == 2
        assert stats["remaining"] == 3
        assert stats["window_seconds"] == 60

        self.reporter.info("get_stats includes type info", context="Test")

    async def test_per_type_clear_specific_type(self):
        """Test clearing specific message type for identifier."""
        self.reporter.info("Testing clear specific type", context="Test")

        per_type_limits = {"trade": 2, "candles": 2}
        limiter = RateLimiter(
            limit=10,
            window_seconds=60,
            per_type_limits=per_type_limits,
        )

        # Fill both types
        await limiter.check_rate_limit("user_5", "trade")
        await limiter.check_rate_limit("user_5", "trade")
        await limiter.check_rate_limit("user_5", "candles")
        await limiter.check_rate_limit("user_5", "candles")

        # Both at limit
        assert await limiter.check_rate_limit("user_5", "trade") is False
        assert await limiter.check_rate_limit("user_5", "candles") is False

        # Clear only trade
        limiter.clear("user_5", "trade")

        # Trade should be reset, candles still at limit
        assert await limiter.check_rate_limit("user_5", "trade") is True
        assert await limiter.check_rate_limit("user_5", "candles") is False

        self.reporter.info("Specific type cleared successfully", context="Test")

    async def test_per_type_clear_all_types_for_identifier(self):
        """Test clearing all types for specific identifier."""
        self.reporter.info("Testing clear all types for identifier", context="Test")

        per_type_limits = {"trade": 1, "candles": 1}
        limiter = RateLimiter(
            limit=10,
            window_seconds=60,
            per_type_limits=per_type_limits,
        )

        # Fill both types for user_6
        await limiter.check_rate_limit("user_6", "trade")
        await limiter.check_rate_limit("user_6", "candles")

        # Clear all types for user_6
        limiter.clear("user_6")

        # Both should be reset
        assert await limiter.check_rate_limit("user_6", "trade") is True
        assert await limiter.check_rate_limit("user_6", "candles") is True

        self.reporter.info("All types cleared for identifier", context="Test")

    async def test_per_type_get_all_stats(self):
        """Test get_all_stats includes per-type stats."""
        self.reporter.info("Testing get_all_stats with types", context="Test")

        per_type_limits = {"trade": 5, "candles": 3}
        limiter = RateLimiter(
            limit=10,
            window_seconds=60,
            per_type_limits=per_type_limits,
        )

        # Make requests
        await limiter.check_rate_limit("user_7", "trade")
        await limiter.check_rate_limit("user_7", "candles")
        await limiter.check_rate_limit("user_8", "trade")

        all_stats = limiter.get_all_stats()

        # Check per-type entries
        assert "user_7:trade" in all_stats
        assert "user_7:candles" in all_stats
        assert "user_8:trade" in all_stats

        assert all_stats["user_7:trade"]["current_count"] == 1
        assert all_stats["user_7:candles"]["current_count"] == 1
        assert all_stats["user_8:trade"]["current_count"] == 1

        self.reporter.info("get_all_stats includes per-type data", context="Test")

    async def test_get_configured_types(self):
        """Test get_configured_types returns configured message types."""
        self.reporter.info("Testing get_configured_types", context="Test")

        per_type_limits = {
            "trade": 50,
            "candles": 100,
            "strategy": 10,
        }
        limiter = RateLimiter(
            limit=30,
            window_seconds=60,
            per_type_limits=per_type_limits,
        )

        configured = limiter.get_configured_types()

        assert len(configured) == 3
        assert "trade" in configured
        assert "candles" in configured
        assert "strategy" in configured

        self.reporter.info("Configured types retrieved", context="Test")

    async def test_per_type_sliding_window(self):
        """Test per-type limits respect sliding window."""
        self.reporter.info("Testing per-type sliding window", context="Test")

        per_type_limits = {"trade": 2}
        limiter = RateLimiter(
            limit=10,
            window_seconds=1,
            per_type_limits=per_type_limits,
        )

        # Fill trade limit
        assert await limiter.check_rate_limit("user_9", "trade") is True
        assert await limiter.check_rate_limit("user_9", "trade") is True
        assert await limiter.check_rate_limit("user_9", "trade") is False

        # Wait for window
        await asyncio.sleep(1.1)

        # Should allow new requests
        assert await limiter.check_rate_limit("user_9", "trade") is True
        assert await limiter.check_rate_limit("user_9", "trade") is True

        self.reporter.info("Per-type sliding window works", context="Test")

    # ================================================================
    # Stats and info tests (original)
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
    # Clear and management tests (original)
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

"""
Unit tests for Rate Limiter (Token Bucket).

Tests rate limiting logic, token refill, burst capacity, and registry.

Usage:
    python tests/unit/resilience/test_rate_limiter.py
    laborant test shared --unit
"""

import time
import asyncio
from shared.tests import LaborantTest
from shared.resilience.rate_limiter import (
    TokenBucket,
    RateLimitConfig,
    RateLimitExceeded,
    RateLimiterRegistry,
)


class TestRateLimiter(LaborantTest):
    """Unit tests for Rate Limiter."""

    component_name = "shared"
    test_category = "unit"

    # ================================================================
    # Configuration tests
    # ================================================================

    def test_rate_limit_config_defaults(self):
        """Test RateLimitConfig default values."""
        self.reporter.info("Testing RateLimitConfig defaults", context="Test")

        config = RateLimitConfig()

        assert config.tokens_per_second == 10.0
        assert config.burst_size == 20
        assert config.initial_tokens is None

        self.reporter.info("Default config values correct", context="Test")

    def test_rate_limit_config_custom_values(self):
        """Test RateLimitConfig with custom values."""
        self.reporter.info("Testing custom RateLimitConfig", context="Test")

        config = RateLimitConfig(
            tokens_per_second=5.0,
            burst_size=10,
            initial_tokens=5,
        )

        assert config.tokens_per_second == 5.0
        assert config.burst_size == 10
        assert config.initial_tokens == 5

        self.reporter.info("Custom config values correct", context="Test")

    # ================================================================
    # Token bucket basic tests (isolated instances)
    # ================================================================

    def test_token_bucket_initialization(self):
        """Test TokenBucket initialization."""
        self.reporter.info("Testing initialization", context="Test")

        bucket = TokenBucket(
            RateLimitConfig(tokens_per_second=5.0, burst_size=10)
        )

        assert bucket.tokens_per_second == 5.0
        assert bucket.burst_size == 10
        # Should start with burst_size tokens
        assert 9.9 <= bucket.available_tokens <= 10.0

        self.reporter.info("Initialization correct", context="Test")

    def test_try_acquire_basic(self):
        """Test basic try_acquire functionality."""
        self.reporter.info("Testing try_acquire", context="Test")

        # Fresh bucket with exactly 10 tokens
        bucket = TokenBucket(
            RateLimitConfig(
                tokens_per_second=1.0,  # Slow refill
                burst_size=10,
                initial_tokens=10,
            )
        )

        # First acquire should succeed
        result1 = bucket.try_acquire(3.0)
        assert result1 is True

        # Second acquire should succeed
        result2 = bucket.try_acquire(3.0)
        assert result2 is True

        # Third should fail (only 4 left, need 5)
        result3 = bucket.try_acquire(5.0)
        assert result3 is False

        self.reporter.info("try_acquire working", context="Test")


    def test_burst_size_cap(self):
        """Test tokens don't exceed burst_size."""
        self.reporter.info("Testing burst cap", context="Test")

        # Fast refill but small burst
        bucket = TokenBucket(
            RateLimitConfig(
                tokens_per_second=1000.0,
                burst_size=5,
            )
        )

        # Wait to overfill
        time.sleep(0.1)

        # Should be capped at burst_size
        tokens = bucket.available_tokens
        assert tokens == 5.0

        self.reporter.info("Burst cap working", context="Test")

    def test_blocking_acquire(self):
        """Test blocking acquire waits for tokens."""
        self.reporter.info("Testing blocking acquire", context="Test")

        bucket = TokenBucket(
            RateLimitConfig(
                tokens_per_second=10.0,
                burst_size=100,
                initial_tokens=0,
            )
        )

        start = time.time()
        bucket.acquire(5.0)
        elapsed = time.time() - start

        # Should take ~0.5 seconds
        assert 0.45 <= elapsed <= 0.6

        self.reporter.info(f"Blocked {elapsed:.2f}s", context="Test")

    def test_acquire_timeout(self):
        """Test acquire with timeout."""
        self.reporter.info("Testing timeout", context="Test")

        bucket = TokenBucket(
            RateLimitConfig(
                tokens_per_second=10.0,
                burst_size=100,
                initial_tokens=0,
            )
        )

        try:
            # Need 10 tokens at 10/sec = 1s, but timeout at 0.3s
            bucket.acquire(10.0, timeout=0.3)
            assert False, "Should have timed out"
        except RateLimitExceeded as e:
            assert e.tokens_required == 10.0
            self.reporter.info("Timeout raised correctly", context="Test")

    def test_async_acquire(self):
        """Test async acquire."""
        self.reporter.info("Testing async acquire", context="Test")

        bucket = TokenBucket(
            RateLimitConfig(
                tokens_per_second=10.0,
                burst_size=100,
                initial_tokens=0,
            )
        )

        async def test():
            start = time.time()
            await bucket.acquire_async(5.0)
            return time.time() - start

        elapsed = asyncio.run(test())

        assert 0.45 <= elapsed <= 0.6

        self.reporter.info(f"Async acquired in {elapsed:.2f}s", context="Test")

    def test_reset_functionality(self):
        """Test reset restores tokens."""
        self.reporter.info("Testing reset", context="Test")

        bucket = TokenBucket(
            RateLimitConfig(
                tokens_per_second=1.0,
                burst_size=20,
                initial_tokens=20,
            )
        )

        # Consume tokens
        bucket.try_acquire(15.0)

        # Reset should restore
        bucket.reset()

        # Should have initial_tokens back
        assert 19.9 <= bucket.available_tokens <= 20.0

        self.reporter.info("Reset working", context="Test")

    # ================================================================
    # Registry tests
    # ================================================================

    def test_registry_basic(self):
        """Test registry creates and returns limiters."""
        self.reporter.info("Testing registry", context="Test")

        registry = RateLimiterRegistry(
            default_config=RateLimitConfig(tokens_per_second=5.0)
        )

        # Get limiter
        limiter = registry.get_limiter("user_1")
        assert limiter.tokens_per_second == 5.0

        # Get again - should be same instance
        same = registry.get_limiter("user_1")
        assert limiter is same

        self.reporter.info("Registry working", context="Test")

    def test_registry_custom_config(self):
        """Test registry with custom config per key."""
        self.reporter.info("Testing custom config", context="Test")

        registry = RateLimiterRegistry()

        custom = RateLimitConfig(tokens_per_second=50.0, burst_size=100)
        limiter = registry.set_limiter("premium", custom)

        assert limiter.tokens_per_second == 50.0
        assert limiter.burst_size == 100

        self.reporter.info("Custom config working", context="Test")

    def test_registry_remove(self):
        """Test removing limiter from registry."""
        self.reporter.info("Testing remove", context="Test")

        registry = RateLimiterRegistry()

        limiter1 = registry.get_limiter("user_x")
        registry.remove_limiter("user_x")
        limiter2 = registry.get_limiter("user_x")

        # Should be different instances
        assert limiter1 is not limiter2

        self.reporter.info("Remove working", context="Test")

    def test_registry_clear(self):
        """Test clearing all limiters."""
        self.reporter.info("Testing clear", context="Test")

        registry = RateLimiterRegistry()

        limiter1 = registry.get_limiter("user_a")
        registry.clear()
        limiter2 = registry.get_limiter("user_a")

        assert limiter1 is not limiter2

        self.reporter.info("Clear working", context="Test")


if __name__ == "__main__":
    TestRateLimiter.run_as_main()

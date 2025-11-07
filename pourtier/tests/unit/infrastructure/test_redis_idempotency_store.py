"""
Unit tests for RedisIdempotencyStore.

Tests Redis-based idempotency key storage and retrieval.

Usage:
    python tests/unit/infrastructure/test_redis_idempotency_store.py
    laborant pourtier --unit
"""

import json
from unittest.mock import AsyncMock

from pourtier.infrastructure.cache.redis_idempotency_store import (
    RedisIdempotencyStore,
)
from shared.tests import LaborantTest


class TestRedisIdempotencyStore(LaborantTest):
    """Unit tests for RedisIdempotencyStore."""

    component_name = "pourtier"
    test_category = "unit"

    # ================================================================
    # Helper Methods
    # ================================================================

    def _create_mock_redis(self) -> AsyncMock:
        """Create mock Redis client."""
        return AsyncMock()

    # ================================================================
    # Test Methods
    # ================================================================

    async def test_get_async_returns_cached_value(self):
        """Test get_async returns cached value if exists."""
        self.reporter.info(
            "Testing get_async returns cached value",
            context="Test",
        )

        mock_redis = self._create_mock_redis()
        store = RedisIdempotencyStore(mock_redis, key_prefix="test:")

        # Mock Redis to return cached value
        cached_data = {"transaction_id": "abc123", "amount": 100}
        mock_redis.get.return_value = json.dumps(cached_data).encode()

        # Execute
        result = await store.get_async("test_key")

        # Verify
        assert result == cached_data
        mock_redis.get.assert_called_once_with("test:test_key")

        self.reporter.info("Cached value returned correctly", context="Test")

    async def test_get_async_returns_none_if_not_exists(self):
        """Test get_async returns None if key doesn't exist."""
        self.reporter.info(
            "Testing get_async returns None if not exists",
            context="Test",
        )

        mock_redis = self._create_mock_redis()
        store = RedisIdempotencyStore(mock_redis, key_prefix="test:")

        # Mock Redis to return None
        mock_redis.get.return_value = None

        # Execute
        result = await store.get_async("nonexistent_key")

        # Verify
        assert result is None
        mock_redis.get.assert_called_once_with("test:nonexistent_key")

        self.reporter.info("None returned for nonexistent key", context="Test")

    async def test_set_async_stores_value_with_ttl(self):
        """Test set_async stores value with TTL."""
        self.reporter.info(
            "Testing set_async stores value with TTL",
            context="Test",
        )

        mock_redis = self._create_mock_redis()
        store = RedisIdempotencyStore(mock_redis, key_prefix="test:")

        # Test data
        test_value = {"transaction_id": "xyz789", "amount": 250}
        test_key = "deposit_key"
        test_ttl = 3600

        # Execute
        await store.set_async(test_key, test_value, ttl=test_ttl)

        # Verify
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args[0]
        assert call_args[0] == "test:deposit_key"  # Full key with prefix
        assert call_args[1] == test_ttl  # TTL
        assert json.loads(call_args[2]) == test_value  # Serialized value

        self.reporter.info("Value stored with TTL correctly", context="Test")

    async def test_exists_async_returns_true_if_exists(self):
        """Test exists_async returns True if key exists."""
        self.reporter.info(
            "Testing exists_async returns True if exists",
            context="Test",
        )

        mock_redis = self._create_mock_redis()
        store = RedisIdempotencyStore(mock_redis, key_prefix="test:")

        # Mock Redis to return 1 (exists)
        mock_redis.exists.return_value = 1

        # Execute
        result = await store.exists_async("existing_key")

        # Verify
        assert result is True
        mock_redis.exists.assert_called_once_with("test:existing_key")

        self.reporter.info("exists_async returned True correctly", context="Test")

    async def test_exists_async_returns_false_if_not_exists(self):
        """Test exists_async returns False if key doesn't exist."""
        self.reporter.info(
            "Testing exists_async returns False if not exists",
            context="Test",
        )

        mock_redis = self._create_mock_redis()
        store = RedisIdempotencyStore(mock_redis, key_prefix="test:")

        # Mock Redis to return 0 (doesn't exist)
        mock_redis.exists.return_value = 0

        # Execute
        result = await store.exists_async("nonexistent_key")

        # Verify
        assert result is False
        mock_redis.exists.assert_called_once_with("test:nonexistent_key")

        self.reporter.info("exists_async returned False correctly", context="Test")

    async def test_delete_async_removes_key(self):
        """Test delete_async removes key from Redis."""
        self.reporter.info(
            "Testing delete_async removes key",
            context="Test",
        )

        mock_redis = self._create_mock_redis()
        store = RedisIdempotencyStore(mock_redis, key_prefix="test:")

        # Execute
        await store.delete_async("key_to_delete")

        # Verify
        mock_redis.delete.assert_called_once_with("test:key_to_delete")

        self.reporter.info("Key deleted correctly", context="Test")

    async def test_key_prefix_applied_correctly(self):
        """Test that key prefix is applied to all operations."""
        self.reporter.info(
            "Testing key prefix applied to all operations",
            context="Test",
        )

        mock_redis = self._create_mock_redis()
        custom_prefix = "pourtier:idempotency:"
        store = RedisIdempotencyStore(mock_redis, key_prefix=custom_prefix)

        test_key = "my_operation_123"

        # Test get (mock return value properly)
        mock_redis.get.return_value = json.dumps({"test": "data"}).encode()
        await store.get_async(test_key)
        assert mock_redis.get.call_args[0][0] == f"{custom_prefix}{test_key}"

        # Test exists
        mock_redis.exists.return_value = 1
        await store.exists_async(test_key)
        assert mock_redis.exists.call_args[0][0] == f"{custom_prefix}{test_key}"

        # Test delete
        await store.delete_async(test_key)
        assert mock_redis.delete.call_args[0][0] == f"{custom_prefix}{test_key}"

        self.reporter.info("Key prefix applied correctly", context="Test")


if __name__ == "__main__":
    TestRedisIdempotencyStore.run_as_main()

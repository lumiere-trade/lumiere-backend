"""
Unit tests for Idempotency pattern.

Tests idempotency key generation, storage, and decorator functionality.

Usage:
    python tests/unit/resilience/test_idempotency.py
    laborant test shared --unit
"""

import time
import asyncio
from shared.tests import LaborantTest
from shared.resilience.idempotency import (
    IdempotencyKey,
    IdempotencyStore,
    InMemoryIdempotencyStore,
    idempotent,
    DuplicateRequestError,
)


class TestIdempotencyKey(LaborantTest):
    """Unit tests for IdempotencyKey generation."""

    component_name = "shared"
    test_category = "unit"

    def test_from_user_request(self):
        """Test key generation from user request."""
        self.reporter.info("Testing user request key", context="Test")

        key1 = IdempotencyKey.from_user_request(
            user_id="user123",
            operation="deposit",
            amount=1000,
            token="USDC"
        )

        # Same params should give same key
        key2 = IdempotencyKey.from_user_request(
            user_id="user123",
            operation="deposit",
            amount=1000,
            token="USDC"
        )

        assert key1 == key2
        assert len(key1) == 64  # SHA256 hash

        # Different params should give different key
        key3 = IdempotencyKey.from_user_request(
            user_id="user123",
            operation="deposit",
            amount=2000,  # Different amount
            token="USDC"
        )

        assert key1 != key3

        self.reporter.info("User request keys working", context="Test")

    def test_from_trade(self):
        """Test key generation from trade."""
        self.reporter.info("Testing trade key", context="Test")

        key = IdempotencyKey.from_trade(
            strategy_id="strat_456",
            signal_hash="abc123",
            timestamp=1730500000
        )

        assert key == "trade_strat_456_1730500000_abc123"
        assert key.startswith("trade_")

        self.reporter.info("Trade key working", context="Test")

    def test_from_blockchain_tx(self):
        """Test key generation from blockchain transaction."""
        self.reporter.info("Testing blockchain tx key", context="Test")

        key = IdempotencyKey.from_blockchain_tx(
            operation="bridge",
            chain="solana",
            params_hash="def789"
        )

        assert key == "blockchain_bridge_solana_def789"
        assert key.startswith("blockchain_")

        self.reporter.info("Blockchain tx key working", context="Test")

    def test_from_event(self):
        """Test key generation from event."""
        self.reporter.info("Testing event key", context="Test")

        key = IdempotencyKey.from_event("evt_12345")

        assert key == "event_evt_12345"
        assert key.startswith("event_")

        self.reporter.info("Event key working", context="Test")

    def test_hash_params(self):
        """Test parameter hashing."""
        self.reporter.info("Testing parameter hashing", context="Test")

        hash1 = IdempotencyKey.hash_params(
            amount=1000,
            token="USDC",
            user="user123"
        )

        # Same params, same hash
        hash2 = IdempotencyKey.hash_params(
            user="user123",  # Different order
            amount=1000,
            token="USDC"
        )

        assert hash1 == hash2
        assert len(hash1) == 64

        # Different params, different hash
        hash3 = IdempotencyKey.hash_params(
            amount=2000,
            token="USDC",
            user="user123"
        )

        assert hash1 != hash3

        self.reporter.info("Parameter hashing working", context="Test")


class TestInMemoryIdempotencyStore(LaborantTest):
    """Unit tests for InMemoryIdempotencyStore."""

    component_name = "shared"
    test_category = "unit"

    def test_store_basic_operations(self):
        """Test basic store operations."""
        self.reporter.info("Testing store operations", context="Test")

        store = InMemoryIdempotencyStore()

        # Initially empty
        assert not store.exists("key1")
        assert store.get("key1") is None

        # Set value
        store.set("key1", {"result": "success"})

        # Should exist now
        assert store.exists("key1")
        assert store.get("key1") == {"result": "success"}

        self.reporter.info("Store operations working", context="Test")

    def test_store_expiry(self):
        """Test store TTL expiry."""
        self.reporter.info("Testing store expiry", context="Test")

        store = InMemoryIdempotencyStore()

        # Set with 1 second TTL
        store.set("key1", "value1", ttl=1)

        # Should exist immediately
        assert store.exists("key1")

        # Wait for expiry
        time.sleep(1.1)

        # Should be gone
        assert not store.exists("key1")
        assert store.get("key1") is None

        self.reporter.info("Store expiry working", context="Test")

    def test_store_async_operations(self):
        """Test async store operations."""
        self.reporter.info("Testing async store", context="Test")

        store = InMemoryIdempotencyStore()

        async def test_async():
            # Set async
            await store.set_async("key1", "value1")

            # Get async
            value = await store.get_async("key1")
            assert value == "value1"

            # Exists async
            exists = await store.exists_async("key1")
            assert exists is True

        asyncio.run(test_async())

        self.reporter.info("Async store working", context="Test")


class TestIdempotentDecorator(LaborantTest):
    """Unit tests for @idempotent decorator."""

    component_name = "shared"
    test_category = "unit"

    def test_idempotent_sync_function(self):
        """Test idempotent decorator with sync function."""
        self.reporter.info("Testing sync idempotent", context="Test")

        store = InMemoryIdempotencyStore()
        call_count = [0]

        @idempotent(key_param="request_id", store=store)
        def execute_operation(user_id: str, amount: float, request_id: str):
            call_count[0] += 1
            return {"user": user_id, "amount": amount, "count": call_count[0]}

        # First call - should execute
        result1 = execute_operation("user123", 1000, request_id="req_001")
        assert result1["count"] == 1
        assert call_count[0] == 1

        # Second call with same key - should return cached
        result2 = execute_operation("user123", 1000, request_id="req_001")
        assert result2["count"] == 1  # Same as first call
        assert call_count[0] == 1  # Function not called again

        # Third call with different key - should execute
        result3 = execute_operation("user123", 2000, request_id="req_002")
        assert result3["count"] == 2
        assert call_count[0] == 2

        self.reporter.info("Sync idempotent working", context="Test")

    def test_idempotent_async_function(self):
        """Test idempotent decorator with async function."""
        self.reporter.info("Testing async idempotent", context="Test")

        store = InMemoryIdempotencyStore()
        call_count = [0]

        @idempotent(key_param="request_id", store=store)
        async def execute_async_operation(user_id: str, request_id: str):
            call_count[0] += 1
            await asyncio.sleep(0.1)
            return {"user": user_id, "count": call_count[0]}

        async def test():
            # First call
            result1 = await execute_async_operation(
                "user123", request_id="req_001"
            )
            assert result1["count"] == 1

            # Second call - cached
            result2 = await execute_async_operation(
                "user123", request_id="req_001"
            )
            assert result2["count"] == 1
            assert call_count[0] == 1

        asyncio.run(test())

        self.reporter.info("Async idempotent working", context="Test")

    def test_idempotent_missing_key(self):
        """Test idempotent decorator raises on missing key."""
        self.reporter.info("Testing missing key error", context="Test")

        store = InMemoryIdempotencyStore()

        @idempotent(key_param="request_id", store=store)
        def execute_operation(user_id: str, request_id: str):
            return {"user": user_id}

        # Should raise ValueError if key missing
        try:
            execute_operation("user123")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "request_id" in str(e)

        self.reporter.info("Missing key error raised", context="Test")

    def test_idempotent_with_ttl(self):
        """Test idempotent decorator with custom TTL."""
        self.reporter.info("Testing custom TTL", context="Test")

        store = InMemoryIdempotencyStore()
        call_count = [0]

        @idempotent(key_param="request_id", store=store, ttl=1)
        def execute_operation(request_id: str):
            call_count[0] += 1
            return call_count[0]

        # First call
        result1 = execute_operation(request_id="req_001")
        assert result1 == 1

        # Second call - cached
        result2 = execute_operation(request_id="req_001")
        assert result2 == 1

        # Wait for expiry
        time.sleep(1.1)

        # Third call - expired, should execute again
        result3 = execute_operation(request_id="req_001")
        assert result3 == 2

        self.reporter.info("Custom TTL working", context="Test")

    def test_idempotent_raise_on_duplicate(self):
        """Test idempotent with raise_on_duplicate flag."""
        self.reporter.info("Testing raise on duplicate", context="Test")

        store = InMemoryIdempotencyStore()

        @idempotent(
            key_param="request_id",
            store=store,
            raise_on_duplicate=True
        )
        def execute_operation(request_id: str):
            return {"status": "success"}

        # First call - should succeed
        result1 = execute_operation(request_id="req_001")
        assert result1["status"] == "success"

        # Second call - should raise
        try:
            execute_operation(request_id="req_001")
            assert False, "Should have raised DuplicateRequestError"
        except DuplicateRequestError as e:
            assert e.key == "req_001"
            assert e.cached_result["status"] == "success"

        self.reporter.info("Raise on duplicate working", context="Test")


class TestIdempotencyIntegration(LaborantTest):
    """Integration tests for idempotency patterns."""

    component_name = "shared"
    test_category = "unit"

    def test_trade_execution_scenario(self):
        """Test idempotency in trade execution scenario."""
        self.reporter.info("Testing trade execution", context="Test")

        store = InMemoryIdempotencyStore()
        executed_trades = []

        def execute_trade_internal(strategy_id: str, signal_hash: str):
            # Generate idempotency key
            trade_id = IdempotencyKey.from_trade(
                strategy_id=strategy_id,
                signal_hash=signal_hash,
                timestamp=int(time.time())
            )

            # Check if already executed
            if store.exists(trade_id):
                return store.get(trade_id)

            # Execute trade
            trade_result = {
                "trade_id": trade_id,
                "strategy": strategy_id,
                "status": "executed"
            }
            executed_trades.append(trade_id)

            # Store result
            store.set(trade_id, trade_result)

            return trade_result

        # First execution
        result1 = execute_trade_internal("strat_123", "signal_abc")
        assert result1["status"] == "executed"
        assert len(executed_trades) == 1

        # Retry with same params - should return cached
        result2 = execute_trade_internal("strat_123", "signal_abc")
        assert result2["status"] == "executed"
        assert result1["trade_id"] == result2["trade_id"]
        assert len(executed_trades) == 1  # Not executed again

        self.reporter.info("Trade execution idempotency working", context="Test")

    def test_event_processing_scenario(self):
        """Test idempotency in event processing."""
        self.reporter.info("Testing event processing", context="Test")

        store = InMemoryIdempotencyStore()
        processed_events = []

        def handle_event(event: dict):
            event_id = event["event_id"]

            # Generate key
            key = IdempotencyKey.from_event(event_id)

            # Check if processed
            if store.exists(key):
                return  # Already processed

            # Process event
            processed_events.append(event_id)

            # Mark as processed
            store.set(key, {"processed": True})

        event = {"event_id": "evt_123", "data": "test"}

        # First processing
        handle_event(event)
        assert len(processed_events) == 1

        # Duplicate event
        handle_event(event)
        assert len(processed_events) == 1  # Not processed again

        self.reporter.info("Event processing idempotency working", context="Test")


if __name__ == "__main__":
    TestIdempotencyKey.run_as_main()
    TestInMemoryIdempotencyStore.run_as_main()
    TestIdempotentDecorator.run_as_main()
    TestIdempotencyIntegration.run_as_main()

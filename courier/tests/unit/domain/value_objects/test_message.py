"""
Unit tests for Message value object.

Tests message validation and immutability.

Usage:
    python -m courier.tests.unit.domain.value_objects.test_message
    laborant courier --unit
"""

from datetime import datetime

from courier.domain.value_objects.message import Message
from shared.tests import LaborantTest


class TestMessage(LaborantTest):
    """Unit tests for Message value object."""

    component_name = "courier"
    test_category = "unit"

    # ================================================================
    # Creation & Validation tests
    # ================================================================

    def test_create_message_with_data(self):
        """Test creating Message with valid data."""
        self.reporter.info("Testing message creation", context="Test")

        data = {"type": "test.event", "value": 123}
        message = Message(data=data)

        assert message.data == data
        assert isinstance(message.timestamp, datetime)
        self.reporter.info("Message created successfully", context="Test")

    def test_message_auto_generates_timestamp(self):
        """Test Message auto-generates timestamp."""
        self.reporter.info("Testing auto-generated timestamp", context="Test")

        data = {"type": "test"}
        message = Message(data=data)

        assert isinstance(message.timestamp, datetime)
        assert message.timestamp is not None
        self.reporter.info("Timestamp auto-generated", context="Test")

    def test_create_message_with_custom_timestamp(self):
        """Test creating Message with custom timestamp."""
        self.reporter.info("Testing custom timestamp", context="Test")

        data = {"type": "test"}
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        message = Message(data=data, timestamp=custom_time)

        assert message.timestamp == custom_time
        self.reporter.info("Custom timestamp accepted", context="Test")

    def test_reject_non_dict_data(self):
        """Test Message rejects non-dict data."""
        self.reporter.info("Testing rejection of non-dict data", context="Test")

        invalid_data = [
            "string",
            123,
            ["list"],
            None,
            True,
        ]

        for invalid in invalid_data:
            try:
                Message(data=invalid)
                assert False, f"Should have rejected: {type(invalid)}"
            except ValueError as e:
                assert "must be a dictionary" in str(e)
                self.reporter.info(
                    f"Non-dict data rejected: {type(invalid)}",
                    context="Test"
                )

    def test_reject_empty_data(self):
        """Test Message rejects empty dict."""
        self.reporter.info("Testing rejection of empty data", context="Test")

        try:
            Message(data={})
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "cannot be empty" in str(e)
            self.reporter.info("Empty data correctly rejected", context="Test")

    # ================================================================
    # Data access tests
    # ================================================================

    def test_data_property_returns_copy(self):
        """Test data property returns copy (immutable)."""
        self.reporter.info("Testing data property returns copy", context="Test")

        original_data = {"type": "test", "value": 123}
        message = Message(data=original_data)

        # Get data
        retrieved_data = message.data

        # Modify retrieved data
        retrieved_data["value"] = 999

        # Original message data should be unchanged
        assert message.data["value"] == 123
        self.reporter.info("Message data is immutable", context="Test")

    def test_get_type_returns_message_type(self):
        """Test get_type() returns message type."""
        self.reporter.info("Testing get_type() method", context="Test")

        data = {"type": "subscription.created", "plan": "pro"}
        message = Message(data=data)

        assert message.get_type() == "subscription.created"
        self.reporter.info("Message type retrieved correctly", context="Test")

    def test_get_type_returns_unknown_if_missing(self):
        """Test get_type() returns 'unknown' if type not in data."""
        self.reporter.info("Testing get_type() with missing type", context="Test")

        data = {"value": 123}
        message = Message(data=data)

        assert message.get_type() == "unknown"
        self.reporter.info("Default type 'unknown' returned", context="Test")

    # ================================================================
    # Timestamp tests
    # ================================================================

    def test_timestamp_property_immutable(self):
        """Test timestamp property is immutable."""
        self.reporter.info("Testing timestamp immutability", context="Test")

        data = {"type": "test"}
        message = Message(data=data)
        original_timestamp = message.timestamp

        # Timestamp should be the same on repeated access
        assert message.timestamp == original_timestamp
        self.reporter.info("Timestamp is immutable", context="Test")

    # ================================================================
    # String representation tests
    # ================================================================

    def test_message_repr(self):
        """Test Message string representation."""
        self.reporter.info("Testing message repr", context="Test")

        data = {"type": "test.event"}
        message = Message(data=data)
        repr_str = repr(message)

        assert "Message" in repr_str
        assert "test.event" in repr_str
        assert "timestamp" in repr_str.lower()
        self.reporter.info(f"Message repr: {repr_str}", context="Test")

    # ================================================================
    # Complex data tests
    # ================================================================

    def test_message_with_nested_data(self):
        """Test Message with nested dictionary data."""
        self.reporter.info("Testing message with nested data", context="Test")

        data = {
            "type": "position.opened",
            "position": {
                "symbol": "SOL/USDT",
                "side": "long",
                "size": 100,
                "metadata": {
                    "strategy_id": "abc123",
                    "risk_level": "medium"
                }
            }
        }

        message = Message(data=data)

        assert message.data["type"] == "position.opened"
        assert message.data["position"]["symbol"] == "SOL/USDT"
        assert message.data["position"]["metadata"]["strategy_id"] == "abc123"
        self.reporter.info("Nested data preserved correctly", context="Test")

    def test_message_with_list_in_data(self):
        """Test Message with list values in data."""
        self.reporter.info("Testing message with list values", context="Test")

        data = {
            "type": "batch.update",
            "items": [1, 2, 3, 4, 5],
            "symbols": ["SOL", "BTC", "ETH"]
        }

        message = Message(data=data)

        assert message.data["items"] == [1, 2, 3, 4, 5]
        assert message.data["symbols"] == ["SOL", "BTC", "ETH"]
        self.reporter.info("List values preserved correctly", context="Test")

    def test_message_data_deep_copy(self):
        """Test Message data is deep copied."""
        self.reporter.info("Testing data deep copy", context="Test")

        original_data = {
            "type": "test",
            "nested": {"value": 123}
        }

        message = Message(data=original_data)

        # Modify original data
        original_data["nested"]["value"] = 999

        # Message data should be unchanged
        assert message.data["nested"]["value"] == 123
        self.reporter.info("Data is deep copied", context="Test")

    # ================================================================
    # Various message types tests
    # ================================================================

    def test_subscription_event_message(self):
        """Test subscription event message."""
        self.reporter.info("Testing subscription event message", context="Test")

        data = {
            "type": "subscription.created",
            "user_id": "user-123",
            "plan": "pro",
            "expires_at": "2025-12-31T23:59:59Z"
        }

        message = Message(data=data)

        assert message.get_type() == "subscription.created"
        assert message.data["plan"] == "pro"
        self.reporter.info("Subscription event message correct", context="Test")

    def test_trade_event_message(self):
        """Test trade event message."""
        self.reporter.info("Testing trade event message", context="Test")

        data = {
            "type": "trade.executed",
            "symbol": "SOL/USDT",
            "side": "buy",
            "amount": 100.5,
            "price": 45.25
        }

        message = Message(data=data)

        assert message.get_type() == "trade.executed"
        assert message.data["symbol"] == "SOL/USDT"
        self.reporter.info("Trade event message correct", context="Test")

    def test_forge_job_message(self):
        """Test forge job event message."""
        self.reporter.info("Testing forge job message", context="Test")

        data = {
            "type": "forge.job.completed",
            "job_id": "job-xyz-789",
            "result": {
                "extrema_found": 15,
                "duration_ms": 2500
            }
        }

        message = Message(data=data)

        assert message.get_type() == "forge.job.completed"
        assert message.data["result"]["extrema_found"] == 15
        self.reporter.info("Forge job message correct", context="Test")


if __name__ == "__main__":
    TestMessage.run_as_main()

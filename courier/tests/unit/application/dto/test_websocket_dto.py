"""
Unit tests for WebSocket DTOs.

Tests WebSocketConnectionInfo validation and properties.

Usage:
    python -m courier.tests.unit.application.dto.test_websocket_dto
    laborant courier --unit
"""

from datetime import datetime

from pydantic import ValidationError
from shared.tests import LaborantTest

from courier.application.dto.websocket_dto import WebSocketConnectionInfo


class TestWebSocketConnectionInfo(LaborantTest):
    """Unit tests for WebSocketConnectionInfo DTO."""

    component_name = "courier"
    test_category = "unit"

    # ================================================================
    # Creation tests
    # ================================================================

    def test_create_connection_info_unauthenticated(self):
        """Test creating connection info without authentication."""
        self.reporter.info("Testing unauthenticated connection", context="Test")

        info = WebSocketConnectionInfo(channel="global")

        assert info.channel == "global"
        assert info.user_id is None
        assert info.wallet_address is None
        assert isinstance(info.connected_at, str)
        self.reporter.info("Unauthenticated connection info created", context="Test")

    def test_create_connection_info_authenticated(self):
        """Test creating connection info with full authentication."""
        self.reporter.info("Testing authenticated connection", context="Test")

        info = WebSocketConnectionInfo(
            channel="user.123",
            user_id="123",
            wallet_address="9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin",
        )

        assert info.channel == "user.123"
        assert info.user_id == "123"
        assert info.wallet_address == "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"
        self.reporter.info("Authenticated connection info created", context="Test")

    def test_create_connection_info_with_user_id_only(self):
        """Test creating connection info with only user_id."""
        self.reporter.info("Testing partial authentication (user_id)", context="Test")

        info = WebSocketConnectionInfo(channel="strategy.abc", user_id="456")

        assert info.user_id == "456"
        assert info.wallet_address is None
        self.reporter.info("Partial auth (user_id only) accepted", context="Test")

    def test_create_connection_info_with_wallet_only(self):
        """Test creating connection info with only wallet_address."""
        self.reporter.info("Testing partial authentication (wallet)", context="Test")

        wallet = "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"
        info = WebSocketConnectionInfo(channel="global", wallet_address=wallet)

        assert info.user_id is None
        assert info.wallet_address == wallet
        self.reporter.info("Partial auth (wallet only) accepted", context="Test")

    def test_connection_info_auto_generates_timestamp(self):
        """Test connection info auto-generates ISO timestamp."""
        self.reporter.info("Testing auto-generated timestamp", context="Test")

        info = WebSocketConnectionInfo(channel="test")

        assert isinstance(info.connected_at, str)
        datetime.fromisoformat(info.connected_at)
        self.reporter.info(f"Generated timestamp: {info.connected_at}", context="Test")

    def test_create_connection_info_with_custom_timestamp(self):
        """Test creating connection info with custom timestamp."""
        self.reporter.info("Testing custom timestamp", context="Test")

        custom_time = "2024-01-01T12:00:00"
        info = WebSocketConnectionInfo(channel="test", connected_at=custom_time)

        assert info.connected_at == custom_time
        self.reporter.info("Custom timestamp accepted", context="Test")

    # ================================================================
    # Validation tests
    # ================================================================

    def test_connection_info_requires_channel(self):
        """Test connection info validation fails without channel."""
        self.reporter.info("Testing missing channel validation", context="Test")

        try:
            WebSocketConnectionInfo(user_id="123")
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "channel" in str(e)
            self.reporter.info(
                "Validation correctly rejected missing channel", context="Test"
            )

    def test_connection_info_rejects_empty_channel(self):
        """Test connection info validation fails with empty channel."""
        self.reporter.info("Testing empty channel validation", context="Test")

        try:
            WebSocketConnectionInfo(channel="")
            assert False, "Should have raised ValidationError"
        except ValidationError:
            self.reporter.info(
                "Validation correctly rejected empty channel", context="Test"
            )

    def test_connection_info_accepts_empty_user_id(self):
        """Test connection info accepts empty user_id string."""
        self.reporter.info("Testing empty user_id", context="Test")

        info = WebSocketConnectionInfo(channel="test", user_id="")

        assert info.user_id == ""
        self.reporter.info("Empty user_id accepted", context="Test")

    def test_connection_info_accepts_empty_wallet(self):
        """Test connection info accepts empty wallet_address string."""
        self.reporter.info("Testing empty wallet_address", context="Test")

        info = WebSocketConnectionInfo(channel="test", wallet_address="")

        assert info.wallet_address == ""
        self.reporter.info("Empty wallet_address accepted", context="Test")

    # ================================================================
    # Serialization tests
    # ================================================================

    def test_connection_info_to_dict_full(self):
        """Test connection info serialization with all fields."""
        self.reporter.info("Testing full serialization", context="Test")

        info = WebSocketConnectionInfo(
            channel="user.123",
            user_id="123",
            wallet_address="9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin",
            connected_at="2024-01-01T12:00:00",
        )
        info_dict = info.model_dump()

        assert info_dict["channel"] == "user.123"
        assert info_dict["user_id"] == "123"
        assert (
            info_dict["wallet_address"]
            == "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"
        )
        assert info_dict["connected_at"] == "2024-01-01T12:00:00"
        self.reporter.info("Full serialization correct", context="Test")

    def test_connection_info_to_dict_minimal(self):
        """Test connection info serialization with minimal fields."""
        self.reporter.info("Testing minimal serialization", context="Test")

        info = WebSocketConnectionInfo(channel="global")
        info_dict = info.model_dump()

        assert info_dict["channel"] == "global"
        assert info_dict["user_id"] is None
        assert info_dict["wallet_address"] is None
        assert "connected_at" in info_dict
        self.reporter.info("Minimal serialization correct", context="Test")

    def test_connection_info_from_dict(self):
        """Test connection info deserialization from dict."""
        self.reporter.info("Testing deserialization", context="Test")

        data = {
            "channel": "strategy.abc",
            "user_id": "789",
            "wallet_address": "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin",
            "connected_at": "2024-01-01T12:00:00",
        }
        info = WebSocketConnectionInfo(**data)

        assert info.channel == "strategy.abc"
        assert info.user_id == "789"
        assert info.wallet_address == "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"
        assert info.connected_at == "2024-01-01T12:00:00"
        self.reporter.info("Deserialization correct", context="Test")

    def test_connection_info_from_dict_partial(self):
        """Test connection info deserialization with optional fields omitted."""
        self.reporter.info("Testing partial deserialization", context="Test")

        data = {"channel": "global"}
        info = WebSocketConnectionInfo(**data)

        assert info.channel == "global"
        assert info.user_id is None
        assert info.wallet_address is None
        self.reporter.info("Partial deserialization correct", context="Test")

    # ================================================================
    # Channel pattern tests
    # ================================================================

    def test_connection_info_with_user_channel(self):
        """Test connection info with user-specific channel."""
        self.reporter.info("Testing user channel pattern", context="Test")

        info = WebSocketConnectionInfo(
            channel="user.123", user_id="123", wallet_address="test_wallet"
        )

        assert info.channel == "user.123"
        assert "user." in info.channel
        self.reporter.info("User channel pattern accepted", context="Test")

    def test_connection_info_with_strategy_channel(self):
        """Test connection info with strategy-specific channel."""
        self.reporter.info("Testing strategy channel pattern", context="Test")

        info = WebSocketConnectionInfo(channel="strategy.abc-def-123")

        assert info.channel == "strategy.abc-def-123"
        assert "strategy." in info.channel
        self.reporter.info("Strategy channel pattern accepted", context="Test")

    def test_connection_info_with_global_channel(self):
        """Test connection info with global channel."""
        self.reporter.info("Testing global channel", context="Test")

        info = WebSocketConnectionInfo(channel="global")

        assert info.channel == "global"
        self.reporter.info("Global channel accepted", context="Test")

    def test_connection_info_with_ephemeral_channel(self):
        """Test connection info with ephemeral channel pattern."""
        self.reporter.info("Testing ephemeral channel pattern", context="Test")

        info = WebSocketConnectionInfo(channel="forge.job.xyz")

        assert info.channel == "forge.job.xyz"
        assert "forge.job." in info.channel
        self.reporter.info("Ephemeral channel pattern accepted", context="Test")

    # ================================================================
    # Edge cases
    # ================================================================

    def test_connection_info_with_very_long_channel(self):
        """Test connection info with very long channel name."""
        self.reporter.info("Testing very long channel name", context="Test")

        long_channel = "strategy." + "a" * 200
        info = WebSocketConnectionInfo(channel=long_channel)

        assert info.channel == long_channel
        self.reporter.info("Long channel name accepted", context="Test")

    def test_connection_info_with_special_chars_in_channel(self):
        """Test connection info with special characters in channel."""
        self.reporter.info("Testing special chars in channel", context="Test")

        info = WebSocketConnectionInfo(channel="user.test-123.channel")

        assert info.channel == "user.test-123.channel"
        self.reporter.info("Special chars in channel accepted", context="Test")

    def test_timestamp_is_valid_iso_format(self):
        """Test auto-generated timestamp is valid ISO format."""
        self.reporter.info("Testing ISO timestamp format", context="Test")

        info = WebSocketConnectionInfo(channel="test")

        try:
            parsed = datetime.fromisoformat(info.connected_at)
            assert isinstance(parsed, datetime)
            self.reporter.info("Timestamp is valid ISO format", context="Test")
        except ValueError:
            assert False, "Timestamp should be valid ISO format"

    def test_multiple_connections_different_timestamps(self):
        """Test multiple connections have different timestamps."""
        self.reporter.info("Testing unique timestamps", context="Test")

        import time

        info1 = WebSocketConnectionInfo(channel="test")
        time.sleep(0.001)
        info2 = WebSocketConnectionInfo(channel="test")

        assert info1.connected_at != info2.connected_at
        self.reporter.info("Timestamps are unique", context="Test")

    def test_connection_info_field_types(self):
        """Test connection info field types are correct."""
        self.reporter.info("Testing field types", context="Test")

        info = WebSocketConnectionInfo(
            channel="user.123",
            user_id="123",
            wallet_address="test_wallet",
        )

        assert isinstance(info.channel, str)
        assert isinstance(info.user_id, str) or info.user_id is None
        assert isinstance(info.wallet_address, str) or info.wallet_address is None
        assert isinstance(info.connected_at, str)
        self.reporter.info("All field types correct", context="Test")


if __name__ == "__main__":
    TestWebSocketConnectionInfo.run_as_main()

"""
Unit tests for Client entity.

Tests client creation, authentication, and properties.

Usage:
    python -m courier.tests.unit.domain.entities.test_client
    laborant courier --unit
"""

from datetime import datetime
from uuid import UUID

from shared.tests import LaborantTest

from courier.domain.entities.client import Client


class TestClient(LaborantTest):
    """Unit tests for Client entity."""

    component_name = "courier"
    test_category = "unit"

    # ================================================================
    # Creation tests
    # ================================================================

    def test_create_unauthenticated_client(self):
        """Test creating Client without authentication."""
        self.reporter.info("Testing unauthenticated client creation", context="Test")

        client = Client(channel_name="global")

        assert client.channel_name == "global"
        assert isinstance(client.id, UUID)
        assert isinstance(client.connected_at, datetime)
        assert client.user_id is None
        assert client.wallet_address is None
        assert client.is_authenticated() is False
        self.reporter.info("Unauthenticated client created", context="Test")

    def test_create_authenticated_client(self):
        """Test creating Client with authentication."""
        self.reporter.info("Testing authenticated client creation", context="Test")

        client = Client(
            channel_name="user.123",
            user_id="user-abc",
            wallet_address="DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK",
        )

        assert client.channel_name == "user.123"
        assert client.user_id == "user-abc"
        assert client.wallet_address == "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK"
        assert client.is_authenticated() is True
        self.reporter.info("Authenticated client created", context="Test")

    def test_client_auto_generates_id(self):
        """Test Client auto-generates UUID."""
        self.reporter.info("Testing auto-generated UUID", context="Test")

        client = Client(channel_name="global")

        assert isinstance(client.id, UUID)
        assert client.id is not None
        self.reporter.info(f"Generated UUID: {client.id}", context="Test")

    def test_client_auto_generates_timestamp(self):
        """Test Client auto-generates connected_at timestamp."""
        self.reporter.info("Testing auto-generated timestamp", context="Test")

        client = Client(channel_name="global")

        assert isinstance(client.connected_at, datetime)
        self.reporter.info("Timestamp auto-generated", context="Test")

    def test_create_client_with_custom_id(self):
        """Test creating Client with custom UUID."""
        self.reporter.info("Testing client with custom ID", context="Test")

        from uuid import uuid4

        custom_id = uuid4()
        client = Client(channel_name="test", client_id=custom_id)

        assert client.id == custom_id
        self.reporter.info("Client created with custom ID", context="Test")

    def test_create_client_with_custom_timestamp(self):
        """Test creating Client with custom timestamp."""
        self.reporter.info("Testing client with custom timestamp", context="Test")

        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        client = Client(channel_name="test", connected_at=custom_time)

        assert client.connected_at == custom_time
        self.reporter.info("Client created with custom timestamp", context="Test")

    # ================================================================
    # Authentication tests
    # ================================================================

    def test_is_authenticated_true_with_user_id(self):
        """Test is_authenticated() returns True when user_id present."""
        self.reporter.info("Testing is_authenticated() with user_id", context="Test")

        client = Client(channel_name="user.123", user_id="user-abc")

        assert client.is_authenticated() is True
        self.reporter.info("Client is authenticated", context="Test")

    def test_is_authenticated_false_without_user_id(self):
        """Test is_authenticated() returns False when user_id absent."""
        self.reporter.info("Testing is_authenticated() without user_id", context="Test")

        client = Client(channel_name="global")

        assert client.is_authenticated() is False
        self.reporter.info("Client is not authenticated", context="Test")

    def test_is_authenticated_with_wallet_but_no_user_id(self):
        """Test is_authenticated() False with wallet but no user_id."""
        self.reporter.info(
            "Testing is_authenticated() with wallet only", context="Test"
        )

        client = Client(
            channel_name="global",
            wallet_address="DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK",
        )

        assert client.is_authenticated() is False
        self.reporter.info("Client not authenticated without user_id", context="Test")

    # ================================================================
    # Equality tests
    # ================================================================

    def test_clients_with_same_id_are_equal(self):
        """Test two Clients with same ID are equal."""
        self.reporter.info("Testing client equality", context="Test")

        from uuid import uuid4

        client_id = uuid4()
        client1 = Client(channel_name="user.123", client_id=client_id)
        client2 = Client(channel_name="user.456", client_id=client_id)

        assert client1 == client2
        self.reporter.info("Clients with same ID are equal", context="Test")

    def test_clients_with_different_ids_not_equal(self):
        """Test two Clients with different IDs are not equal."""
        self.reporter.info("Testing client inequality", context="Test")

        client1 = Client(channel_name="user.123")
        client2 = Client(channel_name="user.123")

        assert client1 != client2
        self.reporter.info("Clients with different IDs not equal", context="Test")

    def test_client_not_equal_to_non_client(self):
        """Test Client not equal to non-Client object."""
        self.reporter.info("Testing inequality with non-Client", context="Test")

        client = Client(channel_name="global")

        assert client != "client"
        assert client != 123
        assert client is not None
        self.reporter.info("Client not equal to non-Client", context="Test")

    # ================================================================
    # Hashing tests
    # ================================================================

    def test_client_hashable(self):
        """Test Client can be used in sets and dicts."""
        self.reporter.info("Testing client hashability", context="Test")

        client1 = Client(channel_name="user.123")
        client2 = Client(channel_name="user.456")
        client3 = Client(channel_name="user.789", client_id=client1.id)

        # Test in set
        client_set = {client1, client2, client3}
        assert len(client_set) == 2
        self.reporter.info("Client works in set", context="Test")

        # Test as dict key
        client_dict = {client1: "value1", client2: "value2"}
        assert client_dict[client3] == "value1"
        self.reporter.info("Client works as dict key", context="Test")

    # ================================================================
    # String representation tests
    # ================================================================

    def test_client_repr_unauthenticated(self):
        """Test Client repr for unauthenticated client."""
        self.reporter.info("Testing unauthenticated client repr", context="Test")

        client = Client(channel_name="global")
        repr_str = repr(client)

        assert "Client" in repr_str
        assert "global" in repr_str
        assert "unauthenticated" in repr_str
        assert str(client.id) in repr_str
        self.reporter.info(f"Client repr: {repr_str}", context="Test")

    def test_client_repr_authenticated(self):
        """Test Client repr for authenticated client."""
        self.reporter.info("Testing authenticated client repr", context="Test")

        client = Client(channel_name="user.123", user_id="user-abc")
        repr_str = repr(client)

        assert "Client" in repr_str
        assert "user.123" in repr_str
        assert "user_id=user-abc" in repr_str
        assert str(client.id) in repr_str
        self.reporter.info(f"Client repr: {repr_str}", context="Test")

    # ================================================================
    # Channel assignment tests
    # ================================================================

    def test_client_assigned_to_channel(self):
        """Test Client is assigned to correct channel."""
        self.reporter.info("Testing channel assignment", context="Test")

        channel_name = "strategy.abc-123"
        client = Client(channel_name=channel_name)

        assert client.channel_name == channel_name
        self.reporter.info("Client assigned to channel", context="Test")

    def test_multiple_clients_different_channels(self):
        """Test multiple clients can be on different channels."""
        self.reporter.info(
            "Testing multiple clients on different channels", context="Test"
        )

        client1 = Client(channel_name="user.123")
        client2 = Client(channel_name="user.456")
        client3 = Client(channel_name="global")

        assert client1.channel_name == "user.123"
        assert client2.channel_name == "user.456"
        assert client3.channel_name == "global"
        self.reporter.info("Multiple clients on different channels", context="Test")

    # ================================================================
    # Edge cases
    # ================================================================

    def test_two_clients_different_ids(self):
        """Test two clients have different IDs."""
        self.reporter.info("Testing two clients have different IDs", context="Test")

        client1 = Client(channel_name="global")
        client2 = Client(channel_name="global")

        assert client1.id != client2.id
        self.reporter.info("Different clients have different IDs", context="Test")

    def test_client_attributes_mutable(self):
        """Test Client attributes are mutable."""
        self.reporter.info("Testing client mutability", context="Test")

        client = Client(channel_name="user.123")

        # Attributes are mutable
        client.user_id = "user-abc"
        assert client.user_id == "user-abc"

        client.wallet_address = "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK"
        assert client.wallet_address == "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK"

        client.channel_name = "user.456"
        assert client.channel_name == "user.456"

        self.reporter.info("Client attributes are mutable", context="Test")

    def test_partial_authentication_data(self):
        """Test Client with only user_id or only wallet_address."""
        self.reporter.info("Testing partial authentication data", context="Test")

        # Only user_id
        client1 = Client(channel_name="user.123", user_id="user-abc")
        assert client1.is_authenticated() is True
        assert client1.wallet_address is None

        # Only wallet_address
        client2 = Client(
            channel_name="user.456",
            wallet_address="DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK",
        )
        assert client2.is_authenticated() is False
        assert client2.user_id is None

        self.reporter.info("Partial authentication data handled", context="Test")


if __name__ == "__main__":
    TestClient.run_as_main()

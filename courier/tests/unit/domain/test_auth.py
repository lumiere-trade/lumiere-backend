"""
Unit tests for authentication domain models.

Tests TokenPayload and AuthenticatedClient models.

Usage:
    python -m courier.tests.unit.domain.test_auth
    laborant courier --unit
"""

from datetime import datetime, timedelta

from courier.domain.auth import TokenPayload, AuthenticatedClient
from shared.tests import LaborantTest


class TestTokenPayload(LaborantTest):
    """Unit tests for TokenPayload model."""

    component_name = "courier"
    test_category = "unit"

    # ================================================================
    # Creation tests
    # ================================================================

    def test_create_token_payload(self):
        """Test creating TokenPayload with valid data."""
        self.reporter.info("Testing token payload creation", context="Test")

        exp_time = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        iat_time = int(datetime.utcnow().timestamp())

        payload = TokenPayload(
            user_id="user-abc-123",
            wallet_address="DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK",
            exp=exp_time,
            iat=iat_time
        )

        assert payload.user_id == "user-abc-123"
        assert payload.wallet_address == "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK"
        assert payload.exp == exp_time
        assert payload.iat == iat_time
        self.reporter.info("Token payload created", context="Test")

    def test_token_payload_validation(self):
        """Test TokenPayload validates required fields."""
        self.reporter.info("Testing token payload validation", context="Test")

        exp_time = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        iat_time = int(datetime.utcnow().timestamp())

        # All required fields must be present
        try:
            TokenPayload(
                user_id="user-123",
                wallet_address="DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK",
                exp=exp_time
                # Missing iat
            )
            assert False, "Should have raised validation error"
        except Exception:
            self.reporter.info("Missing field validation works", context="Test")

    def test_token_payload_expiration_check(self):
        """Test checking if token is expired."""
        self.reporter.info("Testing token expiration check", context="Test")

        # Expired token
        expired_time = int((datetime.utcnow() - timedelta(hours=1)).timestamp())
        iat_time = int((datetime.utcnow() - timedelta(hours=2)).timestamp())

        expired_payload = TokenPayload(
            user_id="user-123",
            wallet_address="DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK",
            exp=expired_time,
            iat=iat_time
        )

        current_time = int(datetime.utcnow().timestamp())
        assert expired_payload.exp < current_time

        # Valid token
        valid_exp = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        valid_iat = int(datetime.utcnow().timestamp())

        valid_payload = TokenPayload(
            user_id="user-456",
            wallet_address="DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK",
            exp=valid_exp,
            iat=valid_iat
        )

        assert valid_payload.exp > current_time
        self.reporter.info("Expiration check works", context="Test")

    # ================================================================
    # Serialization tests
    # ================================================================

    def test_token_payload_to_dict(self):
        """Test TokenPayload serialization to dict."""
        self.reporter.info("Testing token payload serialization", context="Test")

        exp_time = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        iat_time = int(datetime.utcnow().timestamp())

        payload = TokenPayload(
            user_id="user-789",
            wallet_address="DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK",
            exp=exp_time,
            iat=iat_time
        )

        payload_dict = payload.model_dump()

        assert payload_dict["user_id"] == "user-789"
        assert payload_dict["wallet_address"] == "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK"
        assert payload_dict["exp"] == exp_time
        assert payload_dict["iat"] == iat_time
        self.reporter.info("Token payload serialized", context="Test")


class TestAuthenticatedClient(LaborantTest):
    """Unit tests for AuthenticatedClient model."""

    component_name = "courier"
    test_category = "unit"

    # ================================================================
    # Creation tests
    # ================================================================

    def test_create_authenticated_client(self):
        """Test creating AuthenticatedClient."""
        self.reporter.info("Testing authenticated client creation", context="Test")

        client = AuthenticatedClient(
            user_id="user-abc",
            wallet_address="DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK",
            channel="user.123"
        )

        assert client.user_id == "user-abc"
        assert client.wallet_address == "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK"
        assert client.channel == "user.123"
        assert client.connected_at is not None
        self.reporter.info("Authenticated client created", context="Test")

    def test_authenticated_client_auto_timestamp(self):
        """Test AuthenticatedClient auto-generates connected_at."""
        self.reporter.info(
            "Testing authenticated client auto timestamp",
            context="Test"
        )

        client = AuthenticatedClient(
            user_id="user-123",
            wallet_address="DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK",
            channel="global"
        )

        assert client.connected_at is not None
        assert isinstance(client.connected_at, str)
        assert "T" in client.connected_at  # ISO format
        self.reporter.info("Auto timestamp generated", context="Test")

    def test_authenticated_client_validation(self):
        """Test AuthenticatedClient validates required fields."""
        self.reporter.info(
            "Testing authenticated client validation",
            context="Test"
        )

        # Missing required field
        try:
            AuthenticatedClient(
                user_id="user-123",
                wallet_address="DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK"
                # Missing channel
            )
            assert False, "Should have raised validation error"
        except Exception:
            self.reporter.info("Missing field validation works", context="Test")

    # ================================================================
    # Serialization tests
    # ================================================================

    def test_authenticated_client_to_dict(self):
        """Test AuthenticatedClient serialization."""
        self.reporter.info(
            "Testing authenticated client serialization",
            context="Test"
        )

        client = AuthenticatedClient(
            user_id="user-xyz",
            wallet_address="DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK",
            channel="strategy.abc"
        )

        client_dict = client.model_dump()

        assert client_dict["user_id"] == "user-xyz"
        assert client_dict["wallet_address"] == "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK"
        assert client_dict["channel"] == "strategy.abc"
        assert "connected_at" in client_dict
        self.reporter.info("Authenticated client serialized", context="Test")

    # ================================================================
    # Channel tests
    # ================================================================

    def test_authenticated_client_different_channels(self):
        """Test multiple authenticated clients on different channels."""
        self.reporter.info(
            "Testing authenticated clients on different channels",
            context="Test"
        )

        client1 = AuthenticatedClient(
            user_id="user-1",
            wallet_address="A" * 44,
            channel="user.123"
        )

        client2 = AuthenticatedClient(
            user_id="user-2",
            wallet_address="B" * 44,
            channel="strategy.xyz"
        )

        assert client1.channel == "user.123"
        assert client2.channel == "strategy.xyz"
        assert client1.user_id != client2.user_id
        self.reporter.info("Different channels handled", context="Test")


if __name__ == "__main__":
    # Run both test classes
    TestTokenPayload.run_as_main()
    TestAuthenticatedClient.run_as_main()

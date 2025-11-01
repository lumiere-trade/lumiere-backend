"""
Unit tests for User entity.

Tests user creation, validation, and balance operations.

Usage:
    python tests/unit/domain/entities/test_user.py
    laborant pourtier --unit
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pourtier.domain.entities.user import User
from shared.tests import LaborantTest


class TestUser(LaborantTest):
    """Unit tests for User entity."""

    component_name = "pourtier"
    test_category = "unit"

    # ================================================================
    # Creation tests
    # ================================================================

    def test_create_user_with_wallet(self):
        """Test creating User with valid wallet address."""
        self.reporter.info("Testing user creation with wallet", context="Test")

        wallet = "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK"
        user = User(wallet_address=wallet)

        assert user.wallet_address == wallet
        assert isinstance(user.id, UUID)
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        self.reporter.info("User created with wallet", context="Test")

    def test_user_auto_generates_id(self):
        """Test User auto-generates UUID."""
        self.reporter.info("Testing auto-generated UUID", context="Test")

        user = User(wallet_address="A" * 44)

        assert isinstance(user.id, UUID)
        assert user.id is not None
        self.reporter.info(f"Generated UUID: {user.id}", context="Test")

    def test_user_auto_generates_timestamps(self):
        """Test User auto-generates created_at and updated_at."""
        self.reporter.info("Testing auto-generated timestamps", context="Test")

        user = User(wallet_address="A" * 44)

        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        assert user.created_at <= user.updated_at
        self.reporter.info("Timestamps auto-generated", context="Test")

    # ================================================================
    # Validation tests
    # ================================================================

    def test_reject_empty_wallet(self):
        """Test User rejects empty wallet address."""
        self.reporter.info("Testing rejection of empty wallet", context="Test")

        try:
            User(wallet_address="")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Wallet address is required" in str(e)
            self.reporter.info("Empty wallet correctly rejected", context="Test")

    def test_reject_short_wallet(self):
        """Test User rejects wallet shorter than 32 chars."""
        self.reporter.info("Testing rejection of short wallet", context="Test")

        try:
            User(wallet_address="ShortWallet123")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid wallet address length" in str(e)
            self.reporter.info("Short wallet correctly rejected", context="Test")

    def test_accept_32_char_wallet(self):
        """Test User accepts 32 character wallet (minimum)."""
        self.reporter.info("Testing 32-char wallet (minimum)", context="Test")

        wallet = "A" * 32
        user = User(wallet_address=wallet)

        assert user.wallet_address == wallet
        self.reporter.info("32-char wallet accepted", context="Test")

    def test_accept_44_char_wallet(self):
        """Test User accepts 44 character wallet (standard)."""
        self.reporter.info("Testing 44-char wallet (standard)", context="Test")

        wallet = "B" * 44
        user = User(wallet_address=wallet)

        assert user.wallet_address == wallet
        self.reporter.info("44-char wallet accepted", context="Test")

    # ================================================================
    # Balance tests (escrow balance cached in DB)
    # ================================================================

    def test_user_default_escrow_fields(self):
        """Test User has default balance field."""
        self.reporter.info("Testing default balance field", context="Test")

        user = User(wallet_address="A" * 44)

        assert user.escrow_balance == Decimal("0")
        assert user.last_blockchain_check is None
        self.reporter.info("Default balance field correct", context="Test")

    def test_update_escrow_balance(self):
        """Test update_escrow_balance() updates balance."""
        self.reporter.info("Testing update_escrow_balance()", context="Test")

        user = User(wallet_address="A" * 44)

        user.update_escrow_balance(Decimal("100.50"))

        assert user.escrow_balance == Decimal("100.50")
        self.reporter.info("Escrow balance updated", context="Test")

    def test_reject_negative_escrow_balance(self):
        """Test update_escrow_balance() rejects negative balance."""
        self.reporter.info("Testing rejection of negative balance", context="Test")

        user = User(wallet_address="A" * 44)

        try:
            user.update_escrow_balance(Decimal("-10.0"))
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Balance cannot be negative" in str(e)
            self.reporter.info("Negative balance correctly rejected", context="Test")

    def test_has_sufficient_balance(self):
        """Test has_sufficient_balance() checks balance."""
        self.reporter.info("Testing has_sufficient_balance()", context="Test")

        user = User(wallet_address="A" * 44)
        user.update_escrow_balance(Decimal("100.0"))

        assert user.has_sufficient_balance(Decimal("50.0")) is True
        assert user.has_sufficient_balance(Decimal("100.0")) is True
        assert user.has_sufficient_balance(Decimal("150.0")) is False
        self.reporter.info("Balance check working correctly", context="Test")

    def test_update_blockchain_check_timestamp(self):
        """Test update_blockchain_check_timestamp() sets timestamp."""
        self.reporter.info(
            "Testing update_blockchain_check_timestamp()", context="Test"
        )

        user = User(wallet_address="A" * 44)

        assert user.last_blockchain_check is None

        user.update_blockchain_check_timestamp()

        assert user.last_blockchain_check is not None
        assert isinstance(user.last_blockchain_check, datetime)
        self.reporter.info("Blockchain check timestamp updated", context="Test")

    # ================================================================
    # Serialization tests
    # ================================================================

    def test_to_dict_serialization(self):
        """Test to_dict() returns correct dictionary."""
        self.reporter.info("Testing to_dict() serialization", context="Test")

        wallet = "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK"
        user = User(wallet_address=wallet)

        result = user.to_dict()

        assert result["id"] == str(user.id)
        assert result["wallet_address"] == wallet
        assert "created_at" in result
        assert "updated_at" in result
        assert result["escrow_balance"] == "0"
        assert result["last_blockchain_check"] is None
        self.reporter.info("to_dict() serialization correct", context="Test")

    def test_to_dict_timestamps_iso_format(self):
        """Test to_dict() timestamps are ISO format strings."""
        self.reporter.info("Testing to_dict() timestamp format", context="Test")

        user = User(wallet_address="A" * 44)

        result = user.to_dict()

        assert isinstance(result["created_at"], str)
        assert isinstance(result["updated_at"], str)
        assert "T" in result["created_at"]
        assert "T" in result["updated_at"]
        self.reporter.info("Timestamps in ISO format", context="Test")

    def test_to_dict_with_balance(self):
        """Test to_dict() includes balance data."""
        self.reporter.info("Testing to_dict() with balance", context="Test")

        user = User(wallet_address="A" * 44)
        user.update_escrow_balance(Decimal("250.75"))
        user.update_blockchain_check_timestamp()

        result = user.to_dict()

        assert result["escrow_balance"] == "250.75"
        assert result["last_blockchain_check"] is not None
        assert isinstance(result["last_blockchain_check"], str)
        assert "T" in result["last_blockchain_check"]
        self.reporter.info("to_dict() includes balance data", context="Test")

    # ================================================================
    # Misc tests
    # ================================================================

    def test_two_users_different_ids(self):
        """Test two users have different IDs."""
        self.reporter.info("Testing two users have different IDs", context="Test")

        user1 = User(wallet_address="A" * 44)
        user2 = User(wallet_address="B" * 44)

        assert user1.id != user2.id
        self.reporter.info("Different users have different IDs", context="Test")

    def test_user_mutable(self):
        """Test User entity is mutable (not frozen)."""
        self.reporter.info("Testing User is mutable", context="Test")

        user = User(wallet_address="A" * 44)

        user.escrow_balance = Decimal("999.99")

        assert user.escrow_balance == Decimal("999.99")
        self.reporter.info("User is mutable (as expected)", context="Test")


if __name__ == "__main__":
    TestUser.run_as_main()

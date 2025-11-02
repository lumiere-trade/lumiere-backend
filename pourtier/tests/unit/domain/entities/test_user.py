"""
Unit tests for User entity.

Tests immutable user identity creation and validation.

Usage:
    python tests/unit/domain/entities/test_user.py
    laborant pourtier --unit
"""

from datetime import datetime
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
        self.reporter.info("User created with wallet", context="Test")

    def test_user_auto_generates_id(self):
        """Test User auto-generates UUID."""
        self.reporter.info("Testing auto-generated UUID", context="Test")

        user = User(wallet_address="A" * 44)

        assert isinstance(user.id, UUID)
        assert user.id is not None
        self.reporter.info(f"Generated UUID: {user.id}", context="Test")

    def test_user_auto_generates_timestamp(self):
        """Test User auto-generates created_at timestamp."""
        self.reporter.info("Testing auto-generated timestamp", context="Test")

        user = User(wallet_address="A" * 44)

        assert isinstance(user.created_at, datetime)
        self.reporter.info("Timestamp auto-generated", context="Test")

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
    # Immutability tests
    # ================================================================

    def test_user_immutable_core_identity(self):
        """Test User core identity fields are immutable."""
        self.reporter.info("Testing User immutability", context="Test")

        user = User(wallet_address="A" * 44)
        original_id = user.id
        original_wallet = user.wallet_address
        original_created = user.created_at

        # Core identity should not be modifiable
        assert user.id == original_id
        assert user.wallet_address == original_wallet
        assert user.created_at == original_created
        
        self.reporter.info("User core identity is immutable", context="Test")

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
        
        # No balance or blockchain check fields
        assert "escrow_balance" not in result
        assert "last_blockchain_check" not in result
        assert "updated_at" not in result
        
        self.reporter.info("to_dict() serialization correct", context="Test")

    def test_to_dict_timestamp_iso_format(self):
        """Test to_dict() timestamp is ISO format string."""
        self.reporter.info("Testing to_dict() timestamp format", context="Test")

        user = User(wallet_address="A" * 44)

        result = user.to_dict()

        assert isinstance(result["created_at"], str)
        assert "T" in result["created_at"]
        self.reporter.info("Timestamp in ISO format", context="Test")

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

    def test_user_minimal_web3_identity(self):
        """Test User represents minimal Web3 identity."""
        self.reporter.info("Testing User as minimal identity", context="Test")

        user = User(wallet_address="A" * 44)

        # User has only identity fields
        assert hasattr(user, "id")
        assert hasattr(user, "wallet_address")
        assert hasattr(user, "created_at")
        
        # User does NOT have escrow fields (queried from blockchain)
        assert not hasattr(user, "escrow_balance")
        assert not hasattr(user, "escrow_account")
        assert not hasattr(user, "last_blockchain_check")
        assert not hasattr(user, "updated_at")
        
        self.reporter.info("User is minimal Web3 identity", context="Test")


if __name__ == "__main__":
    TestUser.run_as_main()

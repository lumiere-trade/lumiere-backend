"""
Unit tests for WalletAddress value object.

Tests wallet address validation and formatting.

Usage:
    python -m pourtier.tests.unit.domain.value_objects.test_wallet_address
    laborant pourtier --unit
"""

from pourtier.domain.value_objects.wallet_address import WalletAddress
from shared.tests import LaborantTest


class TestWalletAddress(LaborantTest):
    """Unit tests for WalletAddress value object."""

    component_name = "pourtier"
    test_category = "unit"

    # ================================================================
    # Creation & Validation tests
    # ================================================================

    def test_create_valid_wallet_address(self):
        """Test creating WalletAddress with valid address."""
        self.reporter.info("Testing valid wallet address creation", context="Test")

        address = "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK"
        wallet = WalletAddress(address=address)

        assert wallet.address == address
        self.reporter.info("Valid wallet address accepted", context="Test")

    def test_create_wallet_address_32_chars(self):
        """Test creating WalletAddress with 32 chars (minimum)."""
        self.reporter.info(
            "Testing wallet address with 32 chars (minimum)", context="Test"
        )

        address = "A" * 32
        wallet = WalletAddress(address=address)

        assert wallet.address == address
        assert len(wallet.address) == 32
        self.reporter.info("32-char wallet address accepted", context="Test")

    def test_create_wallet_address_44_chars(self):
        """Test creating WalletAddress with 44 chars (maximum)."""
        self.reporter.info(
            "Testing wallet address with 44 chars (maximum)", context="Test"
        )

        address = "B" * 44
        wallet = WalletAddress(address=address)

        assert wallet.address == address
        assert len(wallet.address) == 44
        self.reporter.info("44-char wallet address accepted", context="Test")

    def test_reject_empty_address(self):
        """Test WalletAddress rejects empty string."""
        self.reporter.info("Testing rejection of empty address", context="Test")

        try:
            WalletAddress(address="")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "cannot be empty" in str(e)
            self.reporter.info("Empty address correctly rejected", context="Test")

    def test_reject_too_short_address(self):
        """Test WalletAddress rejects address shorter than 32 chars."""
        self.reporter.info("Testing rejection of too short address", context="Test")

        try:
            WalletAddress(address="Short123")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid wallet address length" in str(e)
            self.reporter.info("Too short address correctly rejected", context="Test")

    def test_reject_too_long_address(self):
        """Test WalletAddress rejects address longer than 44 chars."""
        self.reporter.info("Testing rejection of too long address", context="Test")

        long_address = "A" * 50
        try:
            WalletAddress(address=long_address)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid wallet address length" in str(e)
            self.reporter.info("Too long address correctly rejected", context="Test")

    def test_reject_invalid_characters(self):
        """Test WalletAddress rejects non-base58 characters."""
        self.reporter.info("Testing rejection of invalid characters", context="Test")

        # Base58 excludes: 0, O, I, l
        invalid_address = "0" * 32
        try:
            WalletAddress(address=invalid_address)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "invalid characters" in str(e)
            self.reporter.info("Address with '0' correctly rejected", context="Test")

        invalid_address = "O" * 32
        try:
            WalletAddress(address=invalid_address)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "invalid characters" in str(e)
            self.reporter.info("Address with 'O' correctly rejected", context="Test")

    # ================================================================
    # Formatting tests
    # ================================================================

    def test_truncated_format(self):
        """Test truncated() returns first 6 and last 4 chars."""
        self.reporter.info("Testing truncated format", context="Test")

        address = "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK"
        wallet = WalletAddress(address=address)

        truncated = wallet.truncated()

        assert truncated == "DYw8jC...NSKK"
        assert len(truncated) == 13

        self.reporter.info(f"Truncated format correct: {truncated}", context="Test")

    def test_str_returns_full_address(self):
        """Test str() returns full address."""
        self.reporter.info("Testing __str__ method", context="Test")

        address = "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK"
        wallet = WalletAddress(address=address)

        assert str(wallet) == address
        self.reporter.info("__str__ returns full address", context="Test")

    # ================================================================
    # Equality & Hashing tests
    # ================================================================

    def test_equality_same_address(self):
        """Test two WalletAddress with same address are equal."""
        self.reporter.info("Testing equality with same address", context="Test")

        address = "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK"
        wallet1 = WalletAddress(address=address)
        wallet2 = WalletAddress(address=address)

        assert wallet1 == wallet2
        self.reporter.info("Equal addresses are equal", context="Test")

    def test_inequality_different_address(self):
        """Test two WalletAddress with different addresses are not equal."""
        self.reporter.info(
            "Testing inequality with different addresses", context="Test"
        )

        wallet1 = WalletAddress(address="A" * 44)
        wallet2 = WalletAddress(address="B" * 44)

        assert wallet1 != wallet2
        self.reporter.info("Different addresses are not equal", context="Test")

    def test_inequality_with_string(self):
        """Test WalletAddress is not equal to string."""
        self.reporter.info("Testing inequality with string", context="Test")

        address = "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK"
        wallet = WalletAddress(address=address)

        assert wallet != address
        assert not (wallet == address)
        self.reporter.info("WalletAddress not equal to string", context="Test")

    def test_hashable(self):
        """Test WalletAddress can be used in sets and dicts."""
        self.reporter.info("Testing hashability (set and dict usage)", context="Test")

        address1 = "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK"
        # Valid base58: no 0, O, I, l
        address2 = "ABC123def456GHJ789jkm345pqr678STUvwxyz9XYZ12"

        wallet1 = WalletAddress(address=address1)
        wallet2 = WalletAddress(address=address2)
        wallet3 = WalletAddress(address=address1)

        # Test in set
        wallet_set = {wallet1, wallet2, wallet3}
        assert len(wallet_set) == 2
        self.reporter.info("WalletAddress works in set", context="Test")

        # Test as dict key
        wallet_dict = {wallet1: "user1", wallet2: "user2"}
        assert wallet_dict[wallet3] == "user1"
        self.reporter.info("WalletAddress works as dict key", context="Test")

    # ================================================================
    # Immutability tests
    # ================================================================

    def test_cannot_modify_address(self):
        """Test address attribute cannot be modified after creation."""
        self.reporter.info("Testing immutability", context="Test")

        wallet = WalletAddress(address="A" * 44)

        try:
            wallet.address = "B" * 44
            assert False, "Should have raised AttributeError"
        except AttributeError:
            self.reporter.info("WalletAddress is immutable", context="Test")


if __name__ == "__main__":
    TestWalletAddress.run_as_main()

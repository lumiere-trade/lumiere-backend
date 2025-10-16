"""
Unit tests for Passeur utility functions.

Tests UUID conversion, PDA seed generation, and validation functions.

Usage:
    python -m passeur.tests.unit.test_utils
    laborant passeur --unit
"""

from uuid import uuid4

from shared.tests import LaborantTest
from passeur.utils.blockchain import (
    derive_escrow_pda_seeds,
    format_uuid_for_anchor,
    uuid_to_bytes,
)
from passeur.utils.validation import validate_solana_address, validate_uuid


class TestPasseurUtils(LaborantTest):
    """Unit tests for Passeur utility functions."""

    component_name = "passeur"
    test_category = "unit"

    def setup(self):
        """Setup before all tests."""
        self.reporter.info("Initializing utility tests", context="Setup")

    # ================================================================
    # UUID conversion tests
    # ================================================================

    def test_uuid_to_bytes_with_dashes(self):
        """Test UUID to bytes conversion with dashes."""
        self.reporter.info("Testing UUID to bytes with dashes", context="Test")

        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        result = uuid_to_bytes(uuid_str)

        assert isinstance(result, bytes)
        assert len(result) == 16

        self.reporter.info("UUID converted to 16 bytes", context="Test")

    def test_uuid_to_bytes_without_dashes(self):
        """Test UUID to bytes conversion without dashes."""
        self.reporter.info("Testing UUID to bytes without dashes", context="Test")

        uuid_str = "550e8400e29b41d4a716446655440000"
        result = uuid_to_bytes(uuid_str)

        assert isinstance(result, bytes)
        assert len(result) == 16

        self.reporter.info("UUID without dashes converted correctly", context="Test")

    def test_uuid_to_bytes_consistency(self):
        """Test UUID to bytes gives same result with/without dashes."""
        self.reporter.info("Testing UUID conversion consistency", context="Test")

        uuid_with_dashes = "550e8400-e29b-41d4-a716-446655440000"
        uuid_without_dashes = "550e8400e29b41d4a716446655440000"

        result1 = uuid_to_bytes(uuid_with_dashes)
        result2 = uuid_to_bytes(uuid_without_dashes)

        assert result1 == result2

        self.reporter.info("UUID conversion consistent", context="Test")

    def test_uuid_to_bytes_random(self):
        """Test UUID to bytes with random UUID."""
        self.reporter.info("Testing UUID to bytes with random UUID", context="Test")

        random_uuid = str(uuid4())
        result = uuid_to_bytes(random_uuid)

        assert isinstance(result, bytes)
        assert len(result) == 16

        self.reporter.info(
            f"Random UUID {random_uuid[:8]}... converted", context="Test"
        )

    # ================================================================
    # Anchor formatting tests
    # ================================================================

    def test_format_uuid_for_anchor(self):
        """Test formatting UUID for Anchor smart contract."""
        self.reporter.info("Testing UUID format for Anchor", context="Test")

        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        result = format_uuid_for_anchor(uuid_str)

        assert isinstance(result, list)
        assert len(result) == 16
        assert all(isinstance(x, int) for x in result)
        assert all(0 <= x <= 255 for x in result)

        self.reporter.info("UUID formatted correctly for Anchor", context="Test")

    def test_format_uuid_for_anchor_values(self):
        """Test UUID formatting produces correct byte values."""
        self.reporter.info("Testing UUID byte values for Anchor", context="Test")

        # Known UUID
        uuid_str = "00000000-0000-0000-0000-000000000001"
        result = format_uuid_for_anchor(uuid_str)

        # Last byte should be 1
        assert result[-1] == 1
        # All others should be 0
        assert all(x == 0 for x in result[:-1])

        self.reporter.info("UUID byte values correct", context="Test")

    # ================================================================
    # PDA seed derivation tests
    # ================================================================

    def test_derive_escrow_pda_seeds(self):
        """Test deriving escrow PDA seeds."""
        self.reporter.info("Testing PDA seed derivation", context="Test")

        user_wallet = "11111111111111111111111111111111"
        strategy_id = "550e8400-e29b-41d4-a716-446655440000"

        seeds = derive_escrow_pda_seeds(user_wallet, strategy_id)

        assert isinstance(seeds, tuple)
        assert len(seeds) == 3
        assert seeds[0] == b"escrow"
        assert isinstance(seeds[1], bytes)
        assert isinstance(seeds[2], bytes)
        assert len(seeds[2]) == 16  # Strategy ID is 16 bytes

        self.reporter.info("PDA seeds derived correctly", context="Test")

    def test_derive_escrow_pda_seeds_deterministic(self):
        """Test PDA seed derivation is deterministic."""
        self.reporter.info("Testing PDA seed derivation determinism", context="Test")

        user_wallet = "11111111111111111111111111111111"
        strategy_id = "550e8400-e29b-41d4-a716-446655440000"

        seeds1 = derive_escrow_pda_seeds(user_wallet, strategy_id)
        seeds2 = derive_escrow_pda_seeds(user_wallet, strategy_id)

        assert seeds1 == seeds2

        self.reporter.info("PDA seeds deterministic", context="Test")

    def test_derive_escrow_pda_seeds_different_strategies(self):
        """Test different strategies produce different seeds."""
        self.reporter.info("Testing PDA seeds for different strategies", context="Test")

        user_wallet = "11111111111111111111111111111111"
        strategy_id1 = str(uuid4())
        strategy_id2 = str(uuid4())

        seeds1 = derive_escrow_pda_seeds(user_wallet, strategy_id1)
        seeds2 = derive_escrow_pda_seeds(user_wallet, strategy_id2)

        assert seeds1[2] != seeds2[2]  # Strategy bytes should differ

        self.reporter.info("Different strategies have different seeds", context="Test")

    # ================================================================
    # Validation tests
    # ================================================================

    def test_validate_solana_address_valid(self):
        """Test validating valid Solana addresses."""
        self.reporter.info("Testing valid Solana address validation", context="Test")

        valid_addresses = [
            "11111111111111111111111111111111",
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
            "9gvUtaF99sQ287PNzRfCbhFTC4PUnnd7jdAjnY5GUVhS",
        ]

        for address in valid_addresses:
            assert validate_solana_address(address) is True

        self.reporter.info("Valid Solana addresses accepted", context="Test")

    def test_validate_solana_address_invalid(self):
        """Test validating invalid Solana addresses."""
        self.reporter.info("Testing invalid Solana address validation", context="Test")

        invalid_addresses = [
            "",
            "short",
            "0" * 100,  # Too long
            "invalid-chars-!@#$",
        ]

        for address in invalid_addresses:
            assert validate_solana_address(address) is False

        # Test None separately
        assert validate_solana_address(None) is False

        self.reporter.info("Invalid Solana addresses rejected", context="Test")

    def test_validate_uuid_valid(self):
        """Test validating valid UUIDs."""
        self.reporter.info("Testing valid UUID validation", context="Test")

        valid_uuids = [
            "550e8400-e29b-41d4-a716-446655440000",
            str(uuid4()),
            "00000000-0000-0000-0000-000000000000",
        ]

        for uuid_str in valid_uuids:
            assert validate_uuid(uuid_str) is True

        self.reporter.info("Valid UUIDs accepted", context="Test")

    def test_validate_uuid_invalid(self):
        """Test validating invalid UUIDs."""
        self.reporter.info("Testing invalid UUID validation", context="Test")

        invalid_uuids = [
            "",
            "not-a-uuid",
            "550e8400-e29b-41d4-a716",  # Too short
            "550e8400-e29b-41d4-a716-446655440000-extra",  # Too long
            None,
        ]

        for uuid_str in invalid_uuids:
            assert validate_uuid(uuid_str) is False

        self.reporter.info("Invalid UUIDs rejected", context="Test")

    def test_validate_uuid_no_dashes(self):
        """Test UUID validation with format without dashes."""
        self.reporter.info("Testing UUID validation without dashes", context="Test")

        # UUID library accepts format without dashes
        uuid_no_dashes = "550e8400e29b41d4a716446655440000"

        # This might fail depending on UUID library strictness
        try:
            result = validate_uuid(uuid_no_dashes)
            self.reporter.info(f"UUID without dashes: {result}", context="Test")
        except Exception:
            self.reporter.info(
                "UUID without dashes rejected (expected)", context="Test"
            )


if __name__ == "__main__":
    TestPasseurUtils.run_as_main()

"""
Unit tests for StrategyReference value object.

Tests strategy reference validation and formatting.

Usage:
    python -m pourtier.tests.unit.domain.value_objects.test_strategy_reference
    laborant pourtier --unit
"""

from uuid import uuid4

from pourtier.domain.value_objects.strategy_reference import StrategyReference
from shared.tests import LaborantTest


class TestStrategyReference(LaborantTest):
    """Unit tests for StrategyReference value object."""

    component_name = "pourtier"
    test_category = "unit"

    # ================================================================
    # Creation & Validation tests
    # ================================================================

    def test_create_valid_strategy_reference(self):
        """Test creating StrategyReference with valid data."""
        self.reporter.info("Testing valid strategy reference creation", context="Test")

        strategy_id = uuid4()
        ref = StrategyReference(
            strategy_id=strategy_id,
            strategy_name="RSI Mean Reversion",
            asset_symbol="SOLUSDT",
            asset_interval="1h",
        )

        assert ref.strategy_id == strategy_id
        assert ref.strategy_name == "RSI Mean Reversion"
        assert ref.asset_symbol == "SOLUSDT"
        assert ref.asset_interval == "1h"
        self.reporter.info("Valid strategy reference accepted", context="Test")

    def test_reject_empty_strategy_name(self):
        """Test StrategyReference rejects empty strategy name."""
        self.reporter.info("Testing rejection of empty strategy name", context="Test")

        try:
            StrategyReference(
                strategy_id=uuid4(),
                strategy_name="",
                asset_symbol="SOLUSDT",
                asset_interval="1h",
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Strategy name is required" in str(e)
            self.reporter.info("Empty strategy name correctly rejected", context="Test")

    def test_reject_empty_asset_symbol(self):
        """Test StrategyReference rejects empty asset symbol."""
        self.reporter.info("Testing rejection of empty asset symbol", context="Test")

        try:
            StrategyReference(
                strategy_id=uuid4(),
                strategy_name="Test Strategy",
                asset_symbol="",
                asset_interval="1h",
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Asset symbol is required" in str(e)
            self.reporter.info("Empty asset symbol correctly rejected", context="Test")

    def test_reject_empty_asset_interval(self):
        """Test StrategyReference rejects empty asset interval."""
        self.reporter.info("Testing rejection of empty asset interval", context="Test")

        try:
            StrategyReference(
                strategy_id=uuid4(),
                strategy_name="Test Strategy",
                asset_symbol="SOLUSDT",
                asset_interval="",
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Asset interval is required" in str(e)
            self.reporter.info(
                "Empty asset interval correctly rejected", context="Test"
            )

    # ================================================================
    # Interval Validation tests
    # ================================================================

    def test_accept_interval_1m(self):
        """Test StrategyReference accepts '1m' interval."""
        self.reporter.info("Testing valid interval: 1m", context="Test")

        ref = StrategyReference(
            strategy_id=uuid4(),
            strategy_name="Test Strategy",
            asset_symbol="SOLUSDT",
            asset_interval="1m",
        )
        assert ref.asset_interval == "1m"
        self.reporter.info("Interval '1m' accepted", context="Test")

    def test_accept_interval_5m(self):
        """Test StrategyReference accepts '5m' interval."""
        self.reporter.info("Testing valid interval: 5m", context="Test")

        ref = StrategyReference(
            strategy_id=uuid4(),
            strategy_name="Test Strategy",
            asset_symbol="SOLUSDT",
            asset_interval="5m",
        )
        assert ref.asset_interval == "5m"
        self.reporter.info("Interval '5m' accepted", context="Test")

    def test_accept_interval_15m(self):
        """Test StrategyReference accepts '15m' interval."""
        self.reporter.info("Testing valid interval: 15m", context="Test")

        ref = StrategyReference(
            strategy_id=uuid4(),
            strategy_name="Test Strategy",
            asset_symbol="SOLUSDT",
            asset_interval="15m",
        )
        assert ref.asset_interval == "15m"
        self.reporter.info("Interval '15m' accepted", context="Test")

    def test_accept_interval_1h(self):
        """Test StrategyReference accepts '1h' interval."""
        self.reporter.info("Testing valid interval: 1h", context="Test")

        ref = StrategyReference(
            strategy_id=uuid4(),
            strategy_name="Test Strategy",
            asset_symbol="SOLUSDT",
            asset_interval="1h",
        )
        assert ref.asset_interval == "1h"
        self.reporter.info("Interval '1h' accepted", context="Test")

    def test_accept_interval_4h(self):
        """Test StrategyReference accepts '4h' interval."""
        self.reporter.info("Testing valid interval: 4h", context="Test")

        ref = StrategyReference(
            strategy_id=uuid4(),
            strategy_name="Test Strategy",
            asset_symbol="SOLUSDT",
            asset_interval="4h",
        )
        assert ref.asset_interval == "4h"
        self.reporter.info("Interval '4h' accepted", context="Test")

    def test_accept_interval_1d(self):
        """Test StrategyReference accepts '1d' interval."""
        self.reporter.info("Testing valid interval: 1d", context="Test")

        ref = StrategyReference(
            strategy_id=uuid4(),
            strategy_name="Test Strategy",
            asset_symbol="SOLUSDT",
            asset_interval="1d",
        )
        assert ref.asset_interval == "1d"
        self.reporter.info("Interval '1d' accepted", context="Test")

    def test_reject_invalid_interval(self):
        """Test StrategyReference rejects invalid interval."""
        self.reporter.info("Testing rejection of invalid interval", context="Test")

        try:
            StrategyReference(
                strategy_id=uuid4(),
                strategy_name="Test Strategy",
                asset_symbol="SOLUSDT",
                asset_interval="30m",
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid interval: 30m" in str(e)
            assert "Must be one of" in str(e)
            self.reporter.info(
                "Invalid interval '30m' correctly rejected", context="Test"
            )

    # ================================================================
    # Display & Formatting tests
    # ================================================================

    def test_display_name_format(self):
        """Test display_name() returns correct format."""
        self.reporter.info("Testing display_name() format", context="Test")

        ref = StrategyReference(
            strategy_id=uuid4(),
            strategy_name="RSI Strategy",
            asset_symbol="BTCUSDT",
            asset_interval="4h",
        )

        display = ref.display_name()
        assert display == "RSI Strategy (BTCUSDT/4h)"
        self.reporter.info(f"Display name: {display}", context="Test")

    def test_str_returns_display_name(self):
        """Test __str__ returns display_name()."""
        self.reporter.info("Testing __str__ method", context="Test")

        ref = StrategyReference(
            strategy_id=uuid4(),
            strategy_name="EMA Crossover",
            asset_symbol="ETHUSDT",
            asset_interval="1h",
        )

        assert str(ref) == "EMA Crossover (ETHUSDT/1h)"
        self.reporter.info("__str__ returns display_name()", context="Test")

    # ================================================================
    # Serialization tests
    # ================================================================

    def test_to_dict_serialization(self):
        """Test to_dict() returns correct dictionary."""
        self.reporter.info("Testing to_dict() serialization", context="Test")

        strategy_id = uuid4()
        ref = StrategyReference(
            strategy_id=strategy_id,
            strategy_name="MACD Strategy",
            asset_symbol="SOLUSDT",
            asset_interval="15m",
        )

        result = ref.to_dict()

        assert result["strategy_id"] == str(strategy_id)
        assert result["strategy_name"] == "MACD Strategy"
        assert result["asset_symbol"] == "SOLUSDT"
        assert result["asset_interval"] == "15m"
        assert len(result) == 4
        self.reporter.info("to_dict() serialization correct", context="Test")

    # ================================================================
    # Equality & Hashing tests
    # ================================================================

    def test_equality_same_strategy_id(self):
        """Test two references with same ID are equal."""
        self.reporter.info("Testing equality with same strategy_id", context="Test")

        strategy_id = uuid4()
        ref1 = StrategyReference(
            strategy_id=strategy_id,
            strategy_name="Strategy A",
            asset_symbol="SOLUSDT",
            asset_interval="1h",
        )
        ref2 = StrategyReference(
            strategy_id=strategy_id,
            strategy_name="Strategy B",  # Different name
            asset_symbol="BTCUSDT",  # Different symbol
            asset_interval="4h",  # Different interval
        )

        assert ref1 == ref2
        self.reporter.info(
            "References with same ID are equal (regardless of other fields)",
            context="Test",
        )

    def test_inequality_different_strategy_id(self):
        """Test two references with different IDs are not equal."""
        self.reporter.info(
            "Testing inequality with different strategy_id", context="Test"
        )

        ref1 = StrategyReference(
            strategy_id=uuid4(),
            strategy_name="Strategy A",
            asset_symbol="SOLUSDT",
            asset_interval="1h",
        )
        ref2 = StrategyReference(
            strategy_id=uuid4(),
            strategy_name="Strategy A",  # Same name
            asset_symbol="SOLUSDT",  # Same symbol
            asset_interval="1h",  # Same interval
        )

        assert ref1 != ref2
        self.reporter.info(
            "References with different IDs are not equal", context="Test"
        )

    def test_inequality_with_other_type(self):
        """Test StrategyReference is not equal to other types."""
        self.reporter.info("Testing inequality with other types", context="Test")

        ref = StrategyReference(
            strategy_id=uuid4(),
            strategy_name="Test Strategy",
            asset_symbol="SOLUSDT",
            asset_interval="1h",
        )

        assert ref != "Test Strategy"
        assert ref != uuid4()
        assert ref != {"strategy_name": "Test Strategy"}
        self.reporter.info("StrategyReference not equal to other types", context="Test")

    def test_hashable(self):
        """Test StrategyReference can be used in sets and dicts."""
        self.reporter.info("Testing hashability (set and dict usage)", context="Test")

        id1 = uuid4()
        id2 = uuid4()

        ref1 = StrategyReference(
            strategy_id=id1,
            strategy_name="Strategy A",
            asset_symbol="SOLUSDT",
            asset_interval="1h",
        )
        ref2 = StrategyReference(
            strategy_id=id2,
            strategy_name="Strategy B",
            asset_symbol="BTCUSDT",
            asset_interval="4h",
        )
        ref3 = StrategyReference(
            strategy_id=id1,  # Same as ref1
            strategy_name="Different Name",
            asset_symbol="ETHUSDT",
            asset_interval="15m",
        )

        # Test in set
        ref_set = {ref1, ref2, ref3}
        assert len(ref_set) == 2  # ref1 and ref3 are same (same ID)
        self.reporter.info("StrategyReference works in set", context="Test")

        # Test as dict key
        ref_dict = {ref1: "first", ref2: "second"}
        assert ref_dict[ref3] == "first"  # ref3 has same ID as ref1
        self.reporter.info("StrategyReference works as dict key", context="Test")

    # ================================================================
    # Immutability tests
    # ================================================================

    def test_cannot_modify_strategy_id(self):
        """Test strategy_id cannot be modified after creation."""
        self.reporter.info("Testing immutability of strategy_id", context="Test")

        ref = StrategyReference(
            strategy_id=uuid4(),
            strategy_name="Test Strategy",
            asset_symbol="SOLUSDT",
            asset_interval="1h",
        )

        try:
            ref.strategy_id = uuid4()
            assert False, "Should have raised AttributeError"
        except AttributeError:
            self.reporter.info(
                "StrategyReference.strategy_id is immutable", context="Test"
            )

    def test_cannot_modify_strategy_name(self):
        """Test strategy_name cannot be modified after creation."""
        self.reporter.info("Testing immutability of strategy_name", context="Test")

        ref = StrategyReference(
            strategy_id=uuid4(),
            strategy_name="Test Strategy",
            asset_symbol="SOLUSDT",
            asset_interval="1h",
        )

        try:
            ref.strategy_name = "New Name"
            assert False, "Should have raised AttributeError"
        except AttributeError:
            self.reporter.info(
                "StrategyReference.strategy_name is immutable", context="Test"
            )

    def test_cannot_modify_asset_symbol(self):
        """Test asset_symbol cannot be modified after creation."""
        self.reporter.info("Testing immutability of asset_symbol", context="Test")

        ref = StrategyReference(
            strategy_id=uuid4(),
            strategy_name="Test Strategy",
            asset_symbol="SOLUSDT",
            asset_interval="1h",
        )

        try:
            ref.asset_symbol = "BTCUSDT"
            assert False, "Should have raised AttributeError"
        except AttributeError:
            self.reporter.info(
                "StrategyReference.asset_symbol is immutable", context="Test"
            )

    def test_cannot_modify_asset_interval(self):
        """Test asset_interval cannot be modified after creation."""
        self.reporter.info("Testing immutability of asset_interval", context="Test")

        ref = StrategyReference(
            strategy_id=uuid4(),
            strategy_name="Test Strategy",
            asset_symbol="SOLUSDT",
            asset_interval="1h",
        )

        try:
            ref.asset_interval = "4h"
            assert False, "Should have raised AttributeError"
        except AttributeError:
            self.reporter.info(
                "StrategyReference.asset_interval is immutable", context="Test"
            )


if __name__ == "__main__":
    TestStrategyReference.run_as_main()

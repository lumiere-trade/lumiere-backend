"""
Unit tests for SubscriptionPlanDetails value object.

Tests subscription plan configuration and validation.

Usage:
    python -m pourtier.tests.unit.domain.value_objects.test_subscription_plan
    laborant pourtier --unit
"""

from decimal import Decimal

from pourtier.domain.value_objects.subscription_plan import (
    BASIC_PLAN,
    FREE_PLAN,
    PRO_PLAN,
    SubscriptionPlanDetails,
    get_plan_details,
)
from shared.tests import LaborantTest


class TestSubscriptionPlan(LaborantTest):
    """Unit tests for SubscriptionPlanDetails value object."""

    component_name = "pourtier"
    test_category = "unit"

    # ================================================================
    # Creation & Validation tests
    # ================================================================

    def test_create_valid_plan(self):
        """Test creating SubscriptionPlanDetails with valid data."""
        self.reporter.info("Testing valid plan creation", context="Test")

        plan = SubscriptionPlanDetails(
            plan_type="custom",
            price=Decimal("49.99"),
            duration_days=30,
            max_active_strategies=5,
            features=("Feature 1", "Feature 2"),
        )

        assert plan.plan_type == "custom"
        assert plan.price == Decimal("49.99")
        assert plan.duration_days == 30
        assert plan.max_active_strategies == 5
        assert len(plan.features) == 2
        self.reporter.info("Valid plan accepted", context="Test")

    def test_reject_empty_plan_type(self):
        """Test SubscriptionPlanDetails rejects empty plan type."""
        self.reporter.info("Testing rejection of empty plan type", context="Test")

        try:
            SubscriptionPlanDetails(
                plan_type="",
                price=Decimal("10.0"),
                duration_days=30,
                max_active_strategies=1,
                features=("Feature",),
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Plan type is required" in str(e)
            self.reporter.info("Empty plan type correctly rejected", context="Test")

    def test_reject_negative_price(self):
        """Test SubscriptionPlanDetails rejects negative price."""
        self.reporter.info("Testing rejection of negative price", context="Test")

        try:
            SubscriptionPlanDetails(
                plan_type="test",
                price=Decimal("-10.0"),
                duration_days=30,
                max_active_strategies=1,
                features=("Feature",),
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Price cannot be negative" in str(e)
            self.reporter.info("Negative price correctly rejected", context="Test")

    def test_reject_zero_duration(self):
        """Test SubscriptionPlanDetails rejects zero duration."""
        self.reporter.info("Testing rejection of zero duration", context="Test")

        try:
            SubscriptionPlanDetails(
                plan_type="test",
                price=Decimal("10.0"),
                duration_days=0,
                max_active_strategies=1,
                features=("Feature",),
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Duration must be positive" in str(e)
            self.reporter.info("Zero duration correctly rejected", context="Test")

    def test_reject_negative_duration(self):
        """Test SubscriptionPlanDetails rejects negative duration."""
        self.reporter.info("Testing rejection of negative duration", context="Test")

        try:
            SubscriptionPlanDetails(
                plan_type="test",
                price=Decimal("10.0"),
                duration_days=-30,
                max_active_strategies=1,
                features=("Feature",),
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Duration must be positive" in str(e)
            self.reporter.info("Negative duration correctly rejected", context="Test")

    def test_accept_none_duration(self):
        """Test SubscriptionPlanDetails accepts None duration."""
        self.reporter.info("Testing acceptance of None duration", context="Test")

        plan = SubscriptionPlanDetails(
            plan_type="unlimited",
            price=Decimal("0"),
            duration_days=None,
            max_active_strategies=1,
            features=("Feature",),
        )

        assert plan.duration_days is None
        self.reporter.info("None duration accepted (unlimited)", context="Test")

    def test_reject_zero_max_strategies(self):
        """Test SubscriptionPlanDetails rejects zero max strategies."""
        self.reporter.info("Testing rejection of zero max strategies", context="Test")

        try:
            SubscriptionPlanDetails(
                plan_type="test",
                price=Decimal("10.0"),
                duration_days=30,
                max_active_strategies=0,
                features=("Feature",),
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Max strategies must be positive" in str(e)
            self.reporter.info("Zero max strategies correctly rejected", context="Test")

    def test_reject_negative_max_strategies(self):
        """Test SubscriptionPlanDetails rejects negative max strategies."""
        self.reporter.info(
            "Testing rejection of negative max strategies", context="Test"
        )

        try:
            SubscriptionPlanDetails(
                plan_type="test",
                price=Decimal("10.0"),
                duration_days=30,
                max_active_strategies=-5,
                features=("Feature",),
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Max strategies must be positive" in str(e)
            self.reporter.info(
                "Negative max strategies correctly rejected", context="Test"
            )

    # ================================================================
    # Price Calculation tests
    # ================================================================

    def test_is_free_zero_price(self):
        """Test is_free() returns True for zero price."""
        self.reporter.info("Testing is_free() with zero price", context="Test")

        plan = SubscriptionPlanDetails(
            plan_type="free",
            price=Decimal("0"),
            duration_days=None,
            max_active_strategies=1,
            features=("Feature",),
        )

        assert plan.is_free() is True
        self.reporter.info("is_free() correctly returns True", context="Test")

    def test_is_free_non_zero_price(self):
        """Test is_free() returns False for non-zero price."""
        self.reporter.info("Testing is_free() with non-zero price", context="Test")

        plan = SubscriptionPlanDetails(
            plan_type="paid",
            price=Decimal("29.99"),
            duration_days=30,
            max_active_strategies=3,
            features=("Feature",),
        )

        assert plan.is_free() is False
        self.reporter.info("is_free() correctly returns False", context="Test")

    def test_monthly_price_free_plan(self):
        """Test monthly_price() returns 0 for free plan."""
        self.reporter.info("Testing monthly_price() for free plan", context="Test")

        plan = SubscriptionPlanDetails(
            plan_type="free",
            price=Decimal("0"),
            duration_days=None,
            max_active_strategies=1,
            features=("Feature",),
        )

        assert plan.monthly_price() == Decimal("0")
        self.reporter.info("Free plan monthly_price is 0", context="Test")

    def test_monthly_price_30_day_plan(self):
        """Test monthly_price() for 30-day plan."""
        self.reporter.info("Testing monthly_price() for 30-day plan", context="Test")

        plan = SubscriptionPlanDetails(
            plan_type="monthly",
            price=Decimal("29.99"),
            duration_days=30,
            max_active_strategies=3,
            features=("Feature",),
        )

        monthly = plan.monthly_price()
        assert monthly == Decimal("29.99")
        self.reporter.info(f"30-day plan monthly_price: {monthly}", context="Test")

    def test_monthly_price_yearly_plan(self):
        """Test monthly_price() for yearly plan (365 days)."""
        self.reporter.info("Testing monthly_price() for yearly plan", context="Test")

        plan = SubscriptionPlanDetails(
            plan_type="yearly",
            price=Decimal("299.99"),
            duration_days=365,
            max_active_strategies=10,
            features=("Feature",),
        )

        monthly = plan.monthly_price()
        # 299.99 / (365/30) ≈ 24.65
        expected = Decimal("299.99") / (Decimal("365") / Decimal("30"))
        assert abs(monthly - expected) < Decimal("0.01")
        self.reporter.info(f"Yearly plan monthly_price: {monthly:.2f}", context="Test")

    def test_monthly_price_none_duration(self):
        """Test monthly_price() returns 0 for None duration."""
        self.reporter.info("Testing monthly_price() for None duration", context="Test")

        plan = SubscriptionPlanDetails(
            plan_type="unlimited",
            price=Decimal("999.99"),
            duration_days=None,
            max_active_strategies=100,
            features=("Feature",),
        )

        assert plan.monthly_price() == Decimal("0")
        self.reporter.info("None duration monthly_price is 0", context="Test")

    # ================================================================
    # Serialization tests
    # ================================================================

    def test_to_dict_serialization(self):
        """Test to_dict() returns correct dictionary."""
        self.reporter.info("Testing to_dict() serialization", context="Test")

        plan = SubscriptionPlanDetails(
            plan_type="test",
            price=Decimal("49.99"),
            duration_days=30,
            max_active_strategies=5,
            features=("Feature 1", "Feature 2", "Feature 3"),
        )

        result = plan.to_dict()

        assert result["plan_type"] == "test"
        assert result["price"] == "49.99"
        assert result["duration_days"] == 30
        assert result["max_active_strategies"] == 5
        assert result["features"] == ["Feature 1", "Feature 2", "Feature 3"]
        assert len(result) == 5
        self.reporter.info("to_dict() serialization correct", context="Test")

    # ================================================================
    # Predefined Plans tests
    # ================================================================

    def test_free_plan_configuration(self):
        """Test FREE_PLAN predefined configuration."""
        self.reporter.info("Testing FREE_PLAN configuration", context="Test")

        assert FREE_PLAN.plan_type == "free"
        assert FREE_PLAN.price == Decimal("0")
        assert FREE_PLAN.duration_days is None
        assert FREE_PLAN.max_active_strategies == 1
        assert len(FREE_PLAN.features) == 3
        assert "1 active strategy" in FREE_PLAN.features
        assert FREE_PLAN.is_free() is True
        self.reporter.info("FREE_PLAN configuration correct", context="Test")

    def test_basic_plan_configuration(self):
        """Test BASIC_PLAN predefined configuration."""
        self.reporter.info("Testing BASIC_PLAN configuration", context="Test")

        assert BASIC_PLAN.plan_type == "basic"
        assert BASIC_PLAN.price == Decimal("29.99")
        assert BASIC_PLAN.duration_days == 30
        assert BASIC_PLAN.max_active_strategies == 3
        assert len(BASIC_PLAN.features) == 4
        assert "3 active strategies" in BASIC_PLAN.features
        assert BASIC_PLAN.is_free() is False
        self.reporter.info("BASIC_PLAN configuration correct", context="Test")

    def test_pro_plan_configuration(self):
        """Test PRO_PLAN predefined configuration."""
        self.reporter.info("Testing PRO_PLAN configuration", context="Test")

        assert PRO_PLAN.plan_type == "pro"
        assert PRO_PLAN.price == Decimal("99.99")
        assert PRO_PLAN.duration_days == 30
        assert PRO_PLAN.max_active_strategies == 10
        assert len(PRO_PLAN.features) == 5
        assert "10 active strategies" in PRO_PLAN.features
        assert PRO_PLAN.is_free() is False
        self.reporter.info("PRO_PLAN configuration correct", context="Test")

    # ================================================================
    # Factory Function tests
    # ================================================================

    def test_get_plan_details_free(self):
        """Test get_plan_details() returns FREE_PLAN for 'free'."""
        self.reporter.info("Testing get_plan_details('free')", context="Test")

        plan = get_plan_details("free")
        assert plan is FREE_PLAN
        self.reporter.info("get_plan_details('free') returns FREE_PLAN", context="Test")

    def test_get_plan_details_basic(self):
        """Test get_plan_details() returns BASIC_PLAN for 'basic'."""
        self.reporter.info("Testing get_plan_details('basic')", context="Test")

        plan = get_plan_details("basic")
        assert plan is BASIC_PLAN
        self.reporter.info(
            "get_plan_details('basic') returns BASIC_PLAN", context="Test"
        )

    def test_get_plan_details_pro(self):
        """Test get_plan_details() returns PRO_PLAN for 'pro'."""
        self.reporter.info("Testing get_plan_details('pro')", context="Test")

        plan = get_plan_details("pro")
        assert plan is PRO_PLAN
        self.reporter.info("get_plan_details('pro') returns PRO_PLAN", context="Test")

    def test_get_plan_details_case_insensitive(self):
        """Test get_plan_details() is case-insensitive."""
        self.reporter.info(
            "Testing get_plan_details() case insensitivity", context="Test"
        )

        assert get_plan_details("FREE") is FREE_PLAN
        assert get_plan_details("Basic") is BASIC_PLAN
        assert get_plan_details("PRO") is PRO_PLAN
        self.reporter.info("get_plan_details() is case-insensitive", context="Test")

    def test_get_plan_details_unknown_raises(self):
        """Test get_plan_details() raises for unknown plan."""
        self.reporter.info(
            "Testing get_plan_details() with unknown plan", context="Test"
        )

        try:
            get_plan_details("unknown")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown plan type: unknown" in str(e)
            self.reporter.info(
                "Unknown plan type correctly raises ValueError", context="Test"
            )

    # ================================================================
    # Immutability tests
    # ================================================================

    def test_cannot_modify_plan_type(self):
        """Test plan_type cannot be modified after creation."""
        self.reporter.info("Testing immutability of plan_type", context="Test")

        plan = SubscriptionPlanDetails(
            plan_type="test",
            price=Decimal("10.0"),
            duration_days=30,
            max_active_strategies=1,
            features=("Feature",),
        )

        try:
            plan.plan_type = "modified"
            assert False, "Should have raised AttributeError"
        except AttributeError:
            self.reporter.info(
                "SubscriptionPlanDetails.plan_type is immutable", context="Test"
            )

    def test_cannot_modify_price(self):
        """Test price cannot be modified after creation."""
        self.reporter.info("Testing immutability of price", context="Test")

        plan = SubscriptionPlanDetails(
            plan_type="test",
            price=Decimal("10.0"),
            duration_days=30,
            max_active_strategies=1,
            features=("Feature",),
        )

        try:
            plan.price = Decimal("20.0")
            assert False, "Should have raised AttributeError"
        except AttributeError:
            self.reporter.info(
                "SubscriptionPlanDetails.price is immutable", context="Test"
            )

    def test_cannot_modify_features(self):
        """Test features cannot be modified after creation."""
        self.reporter.info("Testing immutability of features", context="Test")

        plan = SubscriptionPlanDetails(
            plan_type="test",
            price=Decimal("10.0"),
            duration_days=30,
            max_active_strategies=1,
            features=("Feature 1", "Feature 2"),
        )

        try:
            plan.features = ("New Feature",)
            assert False, "Should have raised AttributeError"
        except AttributeError:
            self.reporter.info(
                "SubscriptionPlanDetails.features is immutable", context="Test"
            )


if __name__ == "__main__":
    TestSubscriptionPlan.run_as_main()

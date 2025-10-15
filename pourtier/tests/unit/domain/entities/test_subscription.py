"""
Unit tests for Subscription entity.

Tests subscription lifecycle, status management, and renewals.

Usage:
    python -m pourtier.tests.unit.domain.entities.test_subscription
    laborant pourtier --unit
"""

import time
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from pourtier.domain.entities.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)
from shared.tests import LaborantTest


class TestSubscription(LaborantTest):
    """Unit tests for Subscription entity."""

    component_name = "pourtier"
    test_category = "unit"

    # ================================================================
    # Creation tests
    # ================================================================

    def test_create_free_subscription(self):
        """Test creating free subscription."""
        self.reporter.info("Testing free subscription creation", context="Test")

        user_id = uuid4()
        sub = Subscription(user_id=user_id, plan_type=SubscriptionPlan.FREE)

        assert sub.plan_type == SubscriptionPlan.FREE
        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.expires_at is None
        assert sub.user_id == user_id
        self.reporter.info("Free subscription created", context="Test")

    def test_create_basic_subscription(self):
        """Test creating basic subscription with expiration."""
        self.reporter.info("Testing basic subscription creation", context="Test")

        expires = datetime.now() + timedelta(days=30)
        sub = Subscription(
            user_id=uuid4(), plan_type=SubscriptionPlan.BASIC, expires_at=expires
        )

        assert sub.plan_type == SubscriptionPlan.BASIC
        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.expires_at == expires
        self.reporter.info("Basic subscription created", context="Test")

    def test_create_pro_subscription(self):
        """Test creating pro subscription with expiration."""
        self.reporter.info("Testing pro subscription creation", context="Test")

        expires = datetime.now() + timedelta(days=365)
        sub = Subscription(
            user_id=uuid4(), plan_type=SubscriptionPlan.PRO, expires_at=expires
        )

        assert sub.plan_type == SubscriptionPlan.PRO
        assert sub.expires_at == expires
        self.reporter.info("Pro subscription created", context="Test")

    def test_subscription_auto_generates_id(self):
        """Test Subscription auto-generates UUID."""
        self.reporter.info("Testing auto-generated UUID", context="Test")

        sub = Subscription(user_id=uuid4(), plan_type=SubscriptionPlan.FREE)

        assert isinstance(sub.id, UUID)
        self.reporter.info(f"Generated UUID: {sub.id}", context="Test")

    def test_subscription_auto_generates_timestamps(self):
        """Test Subscription auto-generates timestamps."""
        self.reporter.info("Testing auto-generated timestamps", context="Test")

        sub = Subscription(user_id=uuid4(), plan_type=SubscriptionPlan.FREE)

        assert isinstance(sub.created_at, datetime)
        assert isinstance(sub.updated_at, datetime)
        assert isinstance(sub.started_at, datetime)
        self.reporter.info("Timestamps auto-generated", context="Test")

    def test_reject_paid_plan_without_expiration(self):
        """Test paid plan requires expiration date."""
        self.reporter.info("Testing paid plan without expiration", context="Test")

        try:
            Subscription(
                user_id=uuid4(), plan_type=SubscriptionPlan.BASIC, expires_at=None
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Paid plans must have expiration date" in str(e)
            self.reporter.info(
                "Paid plan without expiration correctly rejected", context="Test"
            )

    # ================================================================
    # is_active() tests
    # ================================================================

    def test_is_active_free_plan(self):
        """Test is_active() for free plan (always active)."""
        self.reporter.info("Testing is_active() for free plan", context="Test")

        sub = Subscription(user_id=uuid4(), plan_type=SubscriptionPlan.FREE)

        assert sub.is_active() is True
        self.reporter.info("Free plan is_active() returns True", context="Test")

    def test_is_active_paid_plan_not_expired(self):
        """Test is_active() for paid plan not expired."""
        self.reporter.info(
            "Testing is_active() for non-expired paid plan", context="Test"
        )

        expires = datetime.now() + timedelta(days=30)
        sub = Subscription(
            user_id=uuid4(), plan_type=SubscriptionPlan.BASIC, expires_at=expires
        )

        assert sub.is_active() is True
        self.reporter.info("Non-expired paid plan is active", context="Test")

    def test_is_active_paid_plan_expired(self):
        """Test is_active() for paid plan that expired."""
        self.reporter.info("Testing is_active() for expired paid plan", context="Test")

        expires = datetime.now() - timedelta(days=1)
        sub = Subscription(
            user_id=uuid4(), plan_type=SubscriptionPlan.BASIC, expires_at=expires
        )

        assert sub.is_active() is False
        self.reporter.info("Expired paid plan is not active", context="Test")

    def test_is_active_cancelled_subscription(self):
        """Test is_active() for cancelled subscription."""
        self.reporter.info(
            "Testing is_active() for cancelled subscription", context="Test"
        )

        sub = Subscription(
            user_id=uuid4(),
            plan_type=SubscriptionPlan.FREE,
            status=SubscriptionStatus.CANCELLED,
        )

        assert sub.is_active() is False
        self.reporter.info("Cancelled subscription is not active", context="Test")

    def test_is_active_expired_subscription(self):
        """Test is_active() for expired subscription."""
        self.reporter.info(
            "Testing is_active() for expired subscription", context="Test"
        )

        expires = datetime.now() + timedelta(days=30)
        sub = Subscription(
            user_id=uuid4(),
            plan_type=SubscriptionPlan.BASIC,
            expires_at=expires,
            status=SubscriptionStatus.EXPIRED,
        )

        assert sub.is_active() is False
        self.reporter.info("Expired subscription is not active", context="Test")

    # ================================================================
    # Lifecycle methods tests
    # ================================================================

    def test_cancel_subscription(self):
        """Test cancel() marks subscription as cancelled."""
        self.reporter.info("Testing cancel() method", context="Test")

        sub = Subscription(
            user_id=uuid4(),
            plan_type=SubscriptionPlan.BASIC,
            expires_at=datetime.now() + timedelta(days=30),
        )

        original_updated_at = sub.updated_at
        time.sleep(0.01)

        sub.cancel()

        assert sub.status == SubscriptionStatus.CANCELLED
        assert sub.updated_at > original_updated_at
        self.reporter.info("Subscription cancelled successfully", context="Test")

    def test_expire_subscription(self):
        """Test expire() marks subscription as expired."""
        self.reporter.info("Testing expire() method", context="Test")

        sub = Subscription(
            user_id=uuid4(),
            plan_type=SubscriptionPlan.BASIC,
            expires_at=datetime.now() + timedelta(days=30),
        )

        original_updated_at = sub.updated_at
        time.sleep(0.01)

        sub.expire()

        assert sub.status == SubscriptionStatus.EXPIRED
        assert sub.updated_at > original_updated_at
        self.reporter.info("Subscription expired successfully", context="Test")

    def test_renew_subscription_not_expired(self):
        """Test renew() extends non-expired subscription."""
        self.reporter.info(
            "Testing renew() for non-expired subscription", context="Test"
        )

        original_expires = datetime.now() + timedelta(days=5)
        sub = Subscription(
            user_id=uuid4(),
            plan_type=SubscriptionPlan.BASIC,
            expires_at=original_expires,
        )

        sub.renew(duration_days=30)

        # Should extend from original expiration
        expected = original_expires + timedelta(days=30)
        assert sub.status == SubscriptionStatus.ACTIVE
        assert abs((sub.expires_at - expected).total_seconds()) < 1
        self.reporter.info(
            "Subscription renewed from original expiration", context="Test"
        )

    def test_renew_subscription_already_expired(self):
        """Test renew() extends from now if already expired."""
        self.reporter.info(
            "Testing renew() for already expired subscription", context="Test"
        )

        original_expires = datetime.now() - timedelta(days=5)
        sub = Subscription(
            user_id=uuid4(),
            plan_type=SubscriptionPlan.BASIC,
            expires_at=original_expires,
        )

        sub.renew(duration_days=30)

        # Should extend from now
        expected = datetime.now() + timedelta(days=30)
        assert sub.status == SubscriptionStatus.ACTIVE
        assert abs((sub.expires_at - expected).total_seconds()) < 2
        self.reporter.info(
            "Subscription renewed from now (was expired)", context="Test"
        )

    def test_renew_cancelled_subscription(self):
        """Test renew() reactivates cancelled subscription."""
        self.reporter.info("Testing renew() for cancelled subscription", context="Test")

        sub = Subscription(
            user_id=uuid4(),
            plan_type=SubscriptionPlan.BASIC,
            expires_at=datetime.now() + timedelta(days=30),
            status=SubscriptionStatus.CANCELLED,
        )

        sub.renew(duration_days=30)

        assert sub.status == SubscriptionStatus.ACTIVE
        self.reporter.info("Cancelled subscription reactivated", context="Test")

    def test_renew_updates_timestamp(self):
        """Test renew() updates updated_at timestamp."""
        self.reporter.info("Testing renew() updates timestamp", context="Test")

        sub = Subscription(
            user_id=uuid4(),
            plan_type=SubscriptionPlan.BASIC,
            expires_at=datetime.now() + timedelta(days=30),
        )

        original_updated_at = sub.updated_at
        time.sleep(0.01)

        sub.renew(duration_days=30)

        assert sub.updated_at > original_updated_at
        self.reporter.info("Timestamp updated correctly", context="Test")

    def test_reject_renew_free_plan(self):
        """Test renew() rejects free plan."""
        self.reporter.info("Testing renew() rejection for free plan", context="Test")

        sub = Subscription(user_id=uuid4(), plan_type=SubscriptionPlan.FREE)

        try:
            sub.renew(duration_days=30)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Cannot renew free plan" in str(e)
            self.reporter.info("Free plan renewal correctly rejected", context="Test")

    # ================================================================
    # Serialization tests
    # ================================================================

    def test_to_dict_serialization(self):
        """Test to_dict() returns correct dictionary."""
        self.reporter.info("Testing to_dict() serialization", context="Test")

        user_id = uuid4()
        expires = datetime.now() + timedelta(days=30)
        sub = Subscription(
            user_id=user_id, plan_type=SubscriptionPlan.BASIC, expires_at=expires
        )

        result = sub.to_dict()

        assert result["id"] == str(sub.id)
        assert result["user_id"] == str(user_id)
        assert result["plan_type"] == "basic"
        assert result["status"] == "active"
        assert "started_at" in result
        assert "expires_at" in result
        assert "created_at" in result
        assert "updated_at" in result
        assert len(result) == 8
        self.reporter.info("to_dict() serialization correct", context="Test")

    def test_to_dict_with_none_expires_at(self):
        """Test to_dict() handles None expires_at (free plan)."""
        self.reporter.info("Testing to_dict() with None expires_at", context="Test")

        sub = Subscription(user_id=uuid4(), plan_type=SubscriptionPlan.FREE)

        result = sub.to_dict()

        assert result["expires_at"] is None
        self.reporter.info("to_dict() handles None expires_at", context="Test")

    def test_to_dict_timestamps_iso_format(self):
        """Test to_dict() timestamps are ISO format strings."""
        self.reporter.info("Testing to_dict() timestamp format", context="Test")

        sub = Subscription(user_id=uuid4(), plan_type=SubscriptionPlan.FREE)

        result = sub.to_dict()

        assert isinstance(result["started_at"], str)
        assert isinstance(result["created_at"], str)
        assert isinstance(result["updated_at"], str)
        assert "T" in result["started_at"]
        self.reporter.info("Timestamps in ISO format", context="Test")

    # ================================================================
    # Enum tests
    # ================================================================

    def test_subscription_plan_enum_values(self):
        """Test SubscriptionPlan enum has correct values."""
        self.reporter.info("Testing SubscriptionPlan enum", context="Test")

        assert SubscriptionPlan.FREE.value == "free"
        assert SubscriptionPlan.BASIC.value == "basic"
        assert SubscriptionPlan.PRO.value == "pro"
        self.reporter.info("SubscriptionPlan enum correct", context="Test")

    def test_subscription_status_enum_values(self):
        """Test SubscriptionStatus enum has correct values."""
        self.reporter.info("Testing SubscriptionStatus enum", context="Test")

        assert SubscriptionStatus.ACTIVE.value == "active"
        assert SubscriptionStatus.CANCELLED.value == "cancelled"
        assert SubscriptionStatus.EXPIRED.value == "expired"
        self.reporter.info("SubscriptionStatus enum correct", context="Test")

    # ================================================================
    # Misc tests
    # ================================================================

    def test_subscription_mutable(self):
        """Test Subscription entity is mutable (not frozen)."""
        self.reporter.info("Testing Subscription is mutable", context="Test")

        sub = Subscription(user_id=uuid4(), plan_type=SubscriptionPlan.FREE)

        # Should be able to modify
        sub.status = SubscriptionStatus.CANCELLED
        assert sub.status == SubscriptionStatus.CANCELLED
        self.reporter.info("Subscription is mutable (as expected)", context="Test")


if __name__ == "__main__":
    TestSubscription.run_as_main()

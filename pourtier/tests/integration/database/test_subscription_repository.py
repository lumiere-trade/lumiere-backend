"""
Integration tests for SubscriptionRepository with real PostgreSQL.

Tests subscription CRUD operations on test database.

Usage:
    python -m pourtier.tests.integration.database.test_subscription_repository
    laborant pourtier --integration
"""

from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine

from pourtier.config.settings import load_config
from pourtier.domain.entities.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)
from pourtier.domain.entities.user import User
from pourtier.domain.exceptions import EntityNotFoundError
from pourtier.infrastructure.persistence.database import Database
from pourtier.infrastructure.persistence.models import Base
from pourtier.infrastructure.persistence.repositories.subscription_repository import (
    SubscriptionRepository,
)
from pourtier.infrastructure.persistence.repositories.user_repository import (
    UserRepository,
)
from shared.tests import LaborantTest

# Load test configuration
test_settings = load_config("development.yaml", env="development")
TEST_DATABASE_URL = test_settings.DATABASE_URL


class TestSubscriptionRepository(LaborantTest):
    """Integration tests for SubscriptionRepository."""

    component_name = "pourtier"
    test_category = "integration"

    # Class-level shared resources
    db: Database = None

    # ================================================================
    # Async Lifecycle Hooks
    # ================================================================

    async def async_setup(self):
        """Setup test database (runs once before all tests)."""
        self.reporter.info("Setting up test database...", context="Setup")
        self.reporter.info(f"Database: {TEST_DATABASE_URL}", context="Setup")

        # Drop and recreate tables
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

        # Connect database
        TestSubscriptionRepository.db = Database(
            database_url=TEST_DATABASE_URL, echo=False
        )
        await TestSubscriptionRepository.db.connect()

        self.reporter.info("Test database ready", context="Setup")

    async def async_teardown(self):
        """Cleanup test database (runs once after all tests)."""
        self.reporter.info("Cleaning up test database...", context="Teardown")

        if TestSubscriptionRepository.db:
            await TestSubscriptionRepository.db.disconnect()

        # Drop all tables
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

        self.reporter.info("Cleanup complete", context="Teardown")

    # ================================================================
    # Helper Methods
    # ================================================================

    def _generate_unique_wallet(self) -> str:
        """Generate unique 44-character wallet address."""
        unique_id = str(uuid4()).replace("-", "")
        return unique_id.ljust(44, "0")

    async def _create_test_user(self) -> User:
        """Create a test user with unique wallet."""
        async with self.db.session() as session:
            user_repo = UserRepository(session)
            user = User(wallet_address=self._generate_unique_wallet())
            return await user_repo.create(user)

    # ================================================================
    # Test Methods
    # ================================================================

    async def test_create_subscription(self):
        """Test creating a subscription."""
        self.reporter.info("Testing subscription creation", context="Test")

        user = await self._create_test_user()

        async with self.db.session() as session:
            repo = SubscriptionRepository(session)

            subscription = Subscription(
                user_id=user.id,
                plan_type=SubscriptionPlan.PRO,
                status=SubscriptionStatus.ACTIVE,
                started_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=30),
            )

            created = await repo.create(subscription)

            assert created.id is not None
            assert created.user_id == user.id
            assert created.plan_type == SubscriptionPlan.PRO
            assert created.status == SubscriptionStatus.ACTIVE

            self.reporter.info(f"Subscription created: {created.id}", context="Test")

    async def test_get_subscription_by_id(self):
        """Test retrieving subscription by ID."""
        self.reporter.info("Testing get subscription by ID", context="Test")

        user = await self._create_test_user()

        # Create subscription
        async with self.db.session() as session:
            repo = SubscriptionRepository(session)
            subscription = Subscription(
                user_id=user.id,
                plan_type=SubscriptionPlan.BASIC,
                status=SubscriptionStatus.ACTIVE,
                started_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=30),
            )
            created = await repo.create(subscription)

        # Retrieve by ID
        async with self.db.session() as session:
            repo = SubscriptionRepository(session)
            retrieved = await repo.get_by_id(created.id)

            assert retrieved is not None
            assert retrieved.id == created.id
            assert retrieved.user_id == user.id
            assert retrieved.plan_type == SubscriptionPlan.BASIC

            self.reporter.info("Subscription retrieved", context="Test")

    async def test_get_active_subscription(self):
        """Test getting active subscription for user."""
        self.reporter.info("Testing get active subscription", context="Test")

        user = await self._create_test_user()

        # Create active subscription
        async with self.db.session() as session:
            repo = SubscriptionRepository(session)
            subscription = Subscription(
                user_id=user.id,
                plan_type=SubscriptionPlan.PRO,
                status=SubscriptionStatus.ACTIVE,
                started_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=30),
            )
            await repo.create(subscription)

        # Get active subscription
        async with self.db.session() as session:
            repo = SubscriptionRepository(session)
            active = await repo.get_active_by_user(user.id)

            assert active is not None
            assert active.user_id == user.id
            assert active.status == SubscriptionStatus.ACTIVE

            self.reporter.info("Active subscription found", context="Test")

    async def test_get_active_subscription_none(self):
        """Test getting active subscription when none exists."""
        self.reporter.info("Testing get active subscription (none)", context="Test")

        user = await self._create_test_user()

        # Create expired subscription
        async with self.db.session() as session:
            repo = SubscriptionRepository(session)
            subscription = Subscription(
                user_id=user.id,
                plan_type=SubscriptionPlan.BASIC,
                status=SubscriptionStatus.EXPIRED,
                started_at=datetime.now() - timedelta(days=60),
                expires_at=datetime.now() - timedelta(days=30),
            )
            await repo.create(subscription)

        # Try to get active (should be None)
        async with self.db.session() as session:
            repo = SubscriptionRepository(session)
            active = await repo.get_active_by_user(user.id)

            assert active is None, "Should return None for expired subscription"

            self.reporter.info(
                "No active subscription correctly returned", context="Test"
            )

    async def test_update_subscription(self):
        """Test updating subscription."""
        self.reporter.info("Testing subscription update", context="Test")

        user = await self._create_test_user()

        # Create subscription
        async with self.db.session() as session:
            repo = SubscriptionRepository(session)
            subscription = Subscription(
                user_id=user.id,
                plan_type=SubscriptionPlan.BASIC,
                status=SubscriptionStatus.ACTIVE,
                started_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=30),
            )
            created = await repo.create(subscription)

        # Update subscription
        async with self.db.session() as session:
            repo = SubscriptionRepository(session)
            created.status = SubscriptionStatus.CANCELLED
            updated = await repo.update(created)

            assert updated.status == SubscriptionStatus.CANCELLED

            self.reporter.info("Subscription updated", context="Test")

    async def test_list_subscriptions_by_user(self):
        """Test listing all subscriptions for user."""
        self.reporter.info("Testing list subscriptions by user", context="Test")

        user = await self._create_test_user()

        # Create multiple subscriptions
        async with self.db.session() as session:
            repo = SubscriptionRepository(session)

            # Active subscription
            sub1 = Subscription(
                user_id=user.id,
                plan_type=SubscriptionPlan.PRO,
                status=SubscriptionStatus.ACTIVE,
                started_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=30),
            )
            await repo.create(sub1)

            # Expired subscription
            sub2 = Subscription(
                user_id=user.id,
                plan_type=SubscriptionPlan.BASIC,
                status=SubscriptionStatus.EXPIRED,
                started_at=datetime.now() - timedelta(days=60),
                expires_at=datetime.now() - timedelta(days=30),
            )
            await repo.create(sub2)

        # List all subscriptions
        async with self.db.session() as session:
            repo = SubscriptionRepository(session)
            subscriptions = await repo.list_by_user(user.id)

            assert len(subscriptions) == 2
            assert any(s.status == SubscriptionStatus.ACTIVE for s in subscriptions)
            assert any(s.status == SubscriptionStatus.EXPIRED for s in subscriptions)

            self.reporter.info(
                f"Found {len(subscriptions)} subscriptions", context="Test"
            )

    async def test_update_nonexistent_subscription(self):
        """Test updating non-existent subscription raises error."""
        self.reporter.info("Testing update non-existent subscription", context="Test")

        async with self.db.session() as session:
            repo = SubscriptionRepository(session)

            # Create subscription that doesn't exist in DB
            subscription = Subscription(
                id=uuid4(),
                user_id=uuid4(),
                plan_type=SubscriptionPlan.BASIC,
                status=SubscriptionStatus.ACTIVE,
                started_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=30),
            )

            try:
                await repo.update(subscription)
                assert False, "Should raise EntityNotFoundError"
            except EntityNotFoundError:
                self.reporter.info("Update non-existent error raised", context="Test")

    async def test_subscription_with_no_expiration(self):
        """Test subscription with no expiration (free plan)."""
        self.reporter.info("Testing subscription without expiration", context="Test")

        user = await self._create_test_user()

        async with self.db.session() as session:
            repo = SubscriptionRepository(session)

            # Free plan has no expiration
            subscription = Subscription(
                user_id=user.id,
                plan_type=SubscriptionPlan.FREE,
                status=SubscriptionStatus.ACTIVE,
                started_at=datetime.now(),
                expires_at=None,  # No expiration
            )

            created = await repo.create(subscription)

            assert created.expires_at is None
            assert created.plan_type == SubscriptionPlan.FREE

            self.reporter.info("Free subscription created", context="Test")


if __name__ == "__main__":
    TestSubscriptionRepository.run_as_main()

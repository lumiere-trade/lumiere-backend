"""
Integration tests for Subscription API routes.

Tests subscription endpoints with httpx.AsyncClient and real test database.
All tests are ASYNC, following the same pattern as other integration tests.

Usage:
    ENV=test python -m pourtier.tests.integration.api.test_subscription_routes
    laborant pourtier --integration
"""

from decimal import Decimal
from uuid import uuid4

import httpx
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine

from pourtier.config.settings import load_config, override_settings
from pourtier.di.container import get_container
from pourtier.di.dependencies import get_db_session
from pourtier.domain.entities.user import User
from pourtier.infrastructure.persistence.database import Database
from pourtier.infrastructure.persistence.models import (
    Base,
    SubscriptionModel,
)
from pourtier.main import create_app
from shared.tests import LaborantTest


class TestSubscriptionRoutes(LaborantTest):
    """Integration tests for Subscription API routes."""

    component_name = "pourtier"
    test_category = "integration"

    # Class-level shared resources
    db: Database = None
    client: httpx.AsyncClient = None
    test_user: User = None
    test_token: str = None
    test_settings = None

    async def async_setup(self):
        """Setup test database and API client (runs once before all tests)."""
        self.reporter.info("Setting up subscription API tests...", context="Setup")

        # Load test configuration
        TestSubscriptionRoutes.test_settings = load_config(
            "development.yaml", env="development"
        )
        app = create_app(TestSubscriptionRoutes.test_settings)

        TEST_DATABASE_URL = TestSubscriptionRoutes.test_settings.DATABASE_URL
        self.reporter.info(f"Database: {TEST_DATABASE_URL}", context="Setup")

        # Apply test settings globally
        override_settings(TestSubscriptionRoutes.test_settings)

        # Drop and recreate tables
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

        # Connect database
        TestSubscriptionRoutes.db = Database(
            database_url=TEST_DATABASE_URL, echo=False
        )
        await TestSubscriptionRoutes.db.connect()

        # Override container's database with test database
        container = get_container()
        container._database = TestSubscriptionRoutes.db

        # Initialize cache if enabled
        if TestSubscriptionRoutes.test_settings.REDIS_ENABLED:
            await container.cache_client.connect()
            self.reporter.info("Redis cache connected", context="Setup")

        # Override FastAPI dependency to use test DB
        async def override_get_db_session():
            """Provide test database session."""
            async with TestSubscriptionRoutes.db.session() as session:
                yield session

        app.dependency_overrides[get_db_session] = override_get_db_session

        # Create AsyncClient with ASGI transport
        TestSubscriptionRoutes.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        )

        # Create test user with escrow
        await self._create_test_user_with_escrow()

        # Generate test JWT token
        TestSubscriptionRoutes.test_token = self._generate_test_token()

        self.reporter.info("Subscription API tests ready", context="Setup")

    async def async_teardown(self):
        """Cleanup test database (runs once after all tests)."""
        self.reporter.info(
            "Cleaning up subscription API tests...", context="Teardown"
        )

        # Close AsyncClient
        if TestSubscriptionRoutes.client:
            await TestSubscriptionRoutes.client.aclose()

        # Disconnect cache
        container = get_container()
        if (
            TestSubscriptionRoutes.test_settings.REDIS_ENABLED
            and container._cache_client
        ):
            await container.cache_client.disconnect()

        # Disconnect database
        if TestSubscriptionRoutes.db:
            await TestSubscriptionRoutes.db.disconnect()

        # Drop all tables
        TEST_DATABASE_URL = TestSubscriptionRoutes.test_settings.DATABASE_URL
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

        self.reporter.info("Cleanup complete", context="Teardown")

    async def async_setup_test(self):
        """Setup before each test - ensure clean state."""
        self.reporter.info("Cleaning test state...", context="Test")

        # Delete all subscriptions for test user
        async with self.db.session() as session:
            await session.execute(
                delete(SubscriptionModel).where(
                    SubscriptionModel.user_id == self.test_user.id
                )
            )
            await session.commit()

        # Restore user balance to $500 using container
        container = get_container()
        async with self.db.session() as session:
            user_repo = container.get_user_repository(session)
            user = await user_repo.get_by_id(self.test_user.id)
            user.escrow_balance = Decimal("500.0")
            await user_repo.update(user)

        # Clear cache
        if (
            TestSubscriptionRoutes.test_settings.REDIS_ENABLED
            and container._multi_layer_cache
        ):
            cache = container.multi_layer_cache
            async with cache.l1_lock:
                cache.l1_cache.clear()

        self.reporter.info("Clean state ready", context="Test")

    async def async_teardown_test(self):
        """Cleanup after each test."""
        pass

    def _generate_unique_wallet(self) -> str:
        """Generate unique 44-character wallet address."""
        unique_id = str(uuid4()).replace("-", "")
        return unique_id.ljust(44, "0")

    async def _create_test_user_with_escrow(self):
        """Create test user with initialized escrow and sufficient balance."""
        container = get_container()
        async with self.db.session() as session:
            user_repo = container.get_user_repository(session)
            user = User(wallet_address=self._generate_unique_wallet())
            user.initialize_escrow(
                escrow_account="3aV1Pbb5bT4x7dPdKj2fhgrXM2kPGMsTs4zB7CMkKfki",
                token_mint="USDC",
            )
            user.update_escrow_balance(Decimal("500.0"))
            TestSubscriptionRoutes.test_user = await user_repo.create(user)

    def _generate_test_token(self) -> str:
        """Generate test JWT token using test settings."""
        from pourtier.infrastructure.auth.jwt_handler import create_access_token

        return create_access_token(
            user_id=self.test_user.id,
            wallet_address=self.test_user.wallet_address,
        )

    def _auth_headers(self) -> dict:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.test_token}"}

    async def test_create_subscription_success(self):
        """Test successful subscription creation."""
        self.reporter.info("Testing create subscription (success)", context="Test")

        response = await self.client.post(
            "/api/subscriptions/",
            json={"plan_type": "basic"},
            headers=self._auth_headers(),
        )

        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert data["user_id"] == str(self.test_user.id)
        assert data["plan_type"] == "basic"
        assert data["status"] == "active"
        assert "started_at" in data
        assert "expires_at" in data

        self.reporter.info("Subscription created successfully", context="Test")

    async def test_create_subscription_insufficient_balance(self):
        """Test subscription creation with insufficient balance."""
        self.reporter.info(
            "Testing create subscription (insufficient balance)", context="Test"
        )

        container = get_container()
        async with self.db.session() as session:
            user_repo = container.get_user_repository(session)
            user = await user_repo.get_by_id(self.test_user.id)
            user.escrow_balance = Decimal("5.0")
            await user_repo.update(user)

        response = await self.client.post(
            "/api/subscriptions/",
            json={"plan_type": "basic"},
            headers=self._auth_headers(),
        )

        assert response.status_code == 400
        assert "insufficient" in response.json()["detail"].lower()

        self.reporter.info("Insufficient balance error returned", context="Test")

    async def test_create_subscription_unauthorized(self):
        """Test subscription creation without authentication."""
        self.reporter.info(
            "Testing create subscription (unauthorized)", context="Test"
        )

        response = await self.client.post(
            "/api/subscriptions/",
            json={"plan_type": "basic"},
        )

        assert response.status_code == 403

        self.reporter.info("Unauthorized error returned", context="Test")

    async def test_create_subscription_pro_plan(self):
        """Test creating PRO subscription."""
        self.reporter.info("Testing create PRO subscription", context="Test")

        response = await self.client.post(
            "/api/subscriptions/",
            json={"plan_type": "pro"},
            headers=self._auth_headers(),
        )

        assert response.status_code == 201

        data = response.json()
        assert data["plan_type"] == "pro"
        assert data["status"] == "active"

        self.reporter.info("PRO subscription created successfully", context="Test")

    async def test_list_subscriptions_empty(self):
        """Test listing subscriptions when user has none."""
        self.reporter.info("Testing list subscriptions (empty)", context="Test")

        response = await self.client.get(
            "/api/subscriptions/",
            headers=self._auth_headers(),
        )

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

        self.reporter.info("Empty subscription list returned", context="Test")

    async def test_list_subscriptions_with_data(self):
        """Test listing subscriptions when user has subscriptions."""
        self.reporter.info("Testing list subscriptions (with data)", context="Test")

        create_response = await self.client.post(
            "/api/subscriptions/",
            json={"plan_type": "basic"},
            headers=self._auth_headers(),
        )
        assert create_response.status_code == 201

        response = await self.client.get(
            "/api/subscriptions/",
            headers=self._auth_headers(),
        )

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["plan_type"] == "basic"

        self.reporter.info("Subscription list retrieved", context="Test")

    async def test_check_status_no_subscription(self):
        """Test checking subscription status with no active subscription."""
        self.reporter.info("Testing check status (no subscription)", context="Test")

        response = await self.client.get(
            "/api/subscriptions/check",
            headers=self._auth_headers(),
        )

        assert response.status_code == 200

        data = response.json()
        assert data["has_active_subscription"] is False
        assert data["current_plan"] is None

        self.reporter.info("No subscription status returned", context="Test")

    async def test_check_status_with_active_subscription(self):
        """Test checking subscription status with active subscription."""
        self.reporter.info(
            "Testing check status (active subscription)", context="Test"
        )

        create_response = await self.client.post(
            "/api/subscriptions/",
            json={"plan_type": "pro"},
            headers=self._auth_headers(),
        )
        assert create_response.status_code == 201

        response = await self.client.get(
            "/api/subscriptions/check",
            headers=self._auth_headers(),
        )

        assert response.status_code == 200

        data = response.json()
        assert data["has_active_subscription"] is True
        assert data["current_plan"] == "pro"

        self.reporter.info("Active subscription status returned", context="Test")

    async def test_get_subscription_by_id_success(self):
        """Test getting subscription by ID."""
        self.reporter.info(
            "Testing get subscription by ID (success)", context="Test"
        )

        create_response = await self.client.post(
            "/api/subscriptions/",
            json={"plan_type": "basic"},
            headers=self._auth_headers(),
        )
        subscription_id = create_response.json()["id"]

        response = await self.client.get(
            f"/api/subscriptions/{subscription_id}",
            headers=self._auth_headers(),
        )

        assert response.status_code == 200

        data = response.json()
        assert data["id"] == subscription_id
        assert data["plan_type"] == "basic"

        self.reporter.info("Subscription retrieved by ID", context="Test")

    async def test_get_subscription_by_id_not_found(self):
        """Test getting non-existent subscription."""
        self.reporter.info(
            "Testing get subscription by ID (not found)", context="Test"
        )

        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await self.client.get(
            f"/api/subscriptions/{fake_id}",
            headers=self._auth_headers(),
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        self.reporter.info("Not found error returned", context="Test")

    async def test_get_subscription_by_id_forbidden(self):
        """Test getting another user's subscription."""
        self.reporter.info(
            "Testing get subscription by ID (forbidden)", context="Test"
        )

        create_response = await self.client.post(
            "/api/subscriptions/",
            json={"plan_type": "basic"},
            headers=self._auth_headers(),
        )
        subscription_id = create_response.json()["id"]

        container = get_container()
        async with self.db.session() as session:
            user_repo = container.get_user_repository(session)
            other_user = User(wallet_address=self._generate_unique_wallet())
            other_user.initialize_escrow(
                escrow_account="4bW2Qcc6cU5y8sT3nZ4yK8pL9rN6mO8hP7qR5sT4uV3w",
                token_mint="USDC",
            )
            other_user = await user_repo.create(other_user)

        from pourtier.infrastructure.auth.jwt_handler import create_access_token

        other_token = create_access_token(
            user_id=other_user.id,
            wallet_address=other_user.wallet_address,
        )

        response = await self.client.get(
            f"/api/subscriptions/{subscription_id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )

        assert response.status_code == 403
        assert "not authorized" in response.json()["detail"].lower()

        self.reporter.info("Forbidden error returned", context="Test")

    async def test_update_subscription_cancel(self):
        """Test cancelling subscription."""
        self.reporter.info("Testing update subscription (cancel)", context="Test")

        create_response = await self.client.post(
            "/api/subscriptions/",
            json={"plan_type": "basic"},
            headers=self._auth_headers(),
        )
        subscription_id = create_response.json()["id"]

        response = await self.client.patch(
            f"/api/subscriptions/{subscription_id}",
            json={"status": "cancelled"},
            headers=self._auth_headers(),
        )

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "cancelled"

        self.reporter.info("Subscription cancelled successfully", context="Test")

    async def test_update_subscription_expire(self):
        """Test expiring subscription."""
        self.reporter.info("Testing update subscription (expire)", context="Test")

        create_response = await self.client.post(
            "/api/subscriptions/",
            json={"plan_type": "basic"},
            headers=self._auth_headers(),
        )
        subscription_id = create_response.json()["id"]

        response = await self.client.patch(
            f"/api/subscriptions/{subscription_id}",
            json={"status": "expired"},
            headers=self._auth_headers(),
        )

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "expired"

        self.reporter.info("Subscription expired successfully", context="Test")

    async def test_update_subscription_invalid_status(self):
        """Test updating subscription with invalid status."""
        self.reporter.info(
            "Testing update subscription (invalid status)", context="Test"
        )

        create_response = await self.client.post(
            "/api/subscriptions/",
            json={"plan_type": "basic"},
            headers=self._auth_headers(),
        )
        subscription_id = create_response.json()["id"]

        response = await self.client.patch(
            f"/api/subscriptions/{subscription_id}",
            json={"status": "invalid_status"},
            headers=self._auth_headers(),
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

        self.reporter.info("Invalid status error returned", context="Test")

    async def test_update_subscription_not_found(self):
        """Test updating non-existent subscription."""
        self.reporter.info("Testing update subscription (not found)", context="Test")

        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await self.client.patch(
            f"/api/subscriptions/{fake_id}",
            json={"status": "cancelled"},
            headers=self._auth_headers(),
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        self.reporter.info("Not found error returned", context="Test")


if __name__ == "__main__":
    TestSubscriptionRoutes.run_as_main()

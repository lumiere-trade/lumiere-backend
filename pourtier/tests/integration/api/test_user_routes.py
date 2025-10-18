"""
Integration tests for User API routes.

Tests user endpoints with httpx.AsyncClient and real test database.

Usage:
    laborant test pourtier --integration
"""

from decimal import Decimal
from uuid import uuid4

import httpx

from pourtier.config.settings import get_settings
from pourtier.di.dependencies import get_db_session
from pourtier.domain.entities.user import User
from pourtier.infrastructure.persistence.database import Database
from pourtier.infrastructure.persistence.models import Base
from pourtier.infrastructure.persistence.repositories.user_repository import (
    UserRepository,
)
from pourtier.main import create_app
from shared.tests import LaborantTest


class TestUserRoutes(LaborantTest):
    """Integration tests for User API routes."""

    component_name = "pourtier"
    test_category = "integration"

    db: Database = None
    client: httpx.AsyncClient = None

    async def async_setup(self):
        """Setup test database and API client."""
        self.reporter.info("Setting up user API tests...", context="Setup")

        # Load settings
        settings = get_settings()
        self.reporter.info(f"Loaded ENV={settings.ENV}", context="Setup")

        # Create test database instance
        TestUserRoutes.db = Database(database_url=settings.DATABASE_URL, echo=False)
        await TestUserRoutes.db.connect()
        self.reporter.info("Connected to test database", context="Setup")

        # Reset database schema using public method
        await TestUserRoutes.db.reset_schema_for_testing(Base.metadata)
        self.reporter.info("Database schema reset", context="Setup")

        # Create test app
        app = create_app(settings)

        # Override FastAPI dependency
        async def override_get_db_session():
            """Provide test database session."""
            async with TestUserRoutes.db.session() as session:
                yield session

        app.dependency_overrides[get_db_session] = override_get_db_session
        self.reporter.info("Database dependency overridden", context="Setup")

        # Create async client
        TestUserRoutes.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        )

        self.reporter.info("User API tests ready", context="Setup")

    async def async_teardown(self):
        """Cleanup test database."""
        self.reporter.info("Cleaning up user API tests...", context="Teardown")

        if TestUserRoutes.client:
            await TestUserRoutes.client.aclose()

        if TestUserRoutes.db:
            await TestUserRoutes.db.disconnect()

        self.reporter.info("Cleanup complete", context="Teardown")

    def _generate_unique_wallet(self) -> str:
        """Generate unique 44-character wallet address."""
        unique_id = str(uuid4()).replace("-", "")
        return unique_id.ljust(44, "0")

    async def _create_test_user(self, with_escrow: bool = False) -> User:
        """Create test user in database."""
        async with self.db.session() as session:
            user_repo = UserRepository(session)
            user = User(wallet_address=self._generate_unique_wallet())

            if with_escrow:
                user.initialize_escrow(
                    escrow_account="3aV1Pbb5bT4x7dPdKj2fhgrXM2kPGMsTs4zB7CMkKfki",
                    token_mint="USDC",
                )
                user.update_escrow_balance(Decimal("100.0"))

            return await user_repo.create(user)

    def _generate_test_token(self, user: User) -> str:
        """Generate test JWT token for user."""
        from pourtier.infrastructure.auth.jwt_handler import create_access_token

        return create_access_token(
            user_id=user.id,
            wallet_address=user.wallet_address,
        )

    def _auth_headers(self, token: str) -> dict:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {token}"}

    async def test_create_user_success(self):
        """Test successful user creation."""
        self.reporter.info("Testing create user (success)", context="Test")

        wallet = self._generate_unique_wallet()

        response = await self.client.post(
            "/api/users/",
            json={"wallet_address": wallet},
        )

        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert data["wallet_address"] == wallet
        assert data["escrow_account"] is None
        assert Decimal(data["escrow_balance"]) == Decimal("0")
        assert "created_at" in data
        assert "updated_at" in data

        self.reporter.info("User created successfully", context="Test")

    async def test_create_user_duplicate_wallet(self):
        """Test creating user with duplicate wallet address."""
        self.reporter.info("Testing create user (duplicate wallet)", context="Test")

        wallet = self._generate_unique_wallet()
        response1 = await self.client.post(
            "/api/users/",
            json={"wallet_address": wallet},
        )
        assert response1.status_code == 201

        response2 = await self.client.post(
            "/api/users/",
            json={"wallet_address": wallet},
        )

        assert response2.status_code == 400
        detail = response2.json()["detail"].lower()
        assert any(
            keyword in detail
            for keyword in ["already registered", "already exists", "duplicate"]
        )

        self.reporter.info("Duplicate wallet error returned", context="Test")

    async def test_create_user_invalid_wallet(self):
        """Test creating user with invalid wallet address."""
        self.reporter.info("Testing create user (invalid wallet)", context="Test")

        response = await self.client.post(
            "/api/users/",
            json={"wallet_address": "short"},
        )

        assert response.status_code in [400, 422]

        self.reporter.info("Invalid wallet error returned", context="Test")

    async def test_get_current_user_success(self):
        """Test getting current authenticated user profile."""
        self.reporter.info("Testing get current user (success)", context="Test")

        user = await self._create_test_user(with_escrow=True)
        token = self._generate_test_token(user)

        response = await self.client.get(
            "/api/users/me",
            headers=self._auth_headers(token),
        )

        assert response.status_code == 200

        data = response.json()
        assert data["id"] == str(user.id)
        assert data["wallet_address"] == user.wallet_address
        assert data["escrow_account"] == user.escrow_account
        assert Decimal(data["escrow_balance"]) == Decimal("100.0")

        self.reporter.info("Current user retrieved successfully", context="Test")

    async def test_get_current_user_unauthorized(self):
        """Test getting current user without authentication."""
        self.reporter.info("Testing get current user (unauthorized)", context="Test")

        response = await self.client.get("/api/users/me")

        assert response.status_code == 403

        self.reporter.info("Unauthorized error returned", context="Test")

    async def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        self.reporter.info("Testing get current user (invalid token)", context="Test")

        response = await self.client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer invalid_token_here"},
        )

        assert response.status_code in [401, 403]

        self.reporter.info("Invalid token error returned", context="Test")

    async def test_get_user_by_id_success(self):
        """Test getting user by ID."""
        self.reporter.info("Testing get user by ID (success)", context="Test")

        user = await self._create_test_user(with_escrow=True)

        response = await self.client.get(f"/api/users/{user.id}")

        assert response.status_code == 200

        data = response.json()
        assert data["id"] == str(user.id)
        assert data["wallet_address"] == user.wallet_address
        assert data["escrow_account"] == user.escrow_account

        self.reporter.info("User retrieved by ID successfully", context="Test")

    async def test_get_user_by_id_not_found(self):
        """Test getting non-existent user by ID."""
        self.reporter.info("Testing get user by ID (not found)", context="Test")

        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await self.client.get(f"/api/users/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        self.reporter.info("Not found error returned", context="Test")

    async def test_get_user_by_id_invalid_uuid(self):
        """Test getting user with invalid UUID format."""
        self.reporter.info("Testing get user by ID (invalid UUID)", context="Test")

        response = await self.client.get("/api/users/invalid-uuid-format")

        assert response.status_code == 422

        self.reporter.info("Invalid UUID error returned", context="Test")

    async def test_get_user_by_wallet_success(self):
        """Test getting user by wallet address."""
        self.reporter.info("Testing get user by wallet (success)", context="Test")

        user = await self._create_test_user(with_escrow=True)

        response = await self.client.get(f"/api/users/wallet/{user.wallet_address}")

        assert response.status_code == 200

        data = response.json()
        assert data["id"] == str(user.id)
        assert data["wallet_address"] == user.wallet_address
        assert data["escrow_account"] == user.escrow_account

        self.reporter.info("User retrieved by wallet successfully", context="Test")

    async def test_get_user_by_wallet_not_found(self):
        """Test getting non-existent user by wallet."""
        self.reporter.info("Testing get user by wallet (not found)", context="Test")

        fake_wallet = self._generate_unique_wallet()

        response = await self.client.get(f"/api/users/wallet/{fake_wallet}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        self.reporter.info("Not found error returned", context="Test")

    async def test_create_user_without_escrow(self):
        """Test that newly created user has no escrow initialized."""
        self.reporter.info("Testing user creation without escrow", context="Test")

        wallet = self._generate_unique_wallet()

        response = await self.client.post(
            "/api/users/",
            json={"wallet_address": wallet},
        )

        assert response.status_code == 201

        data = response.json()
        assert data["escrow_account"] is None
        assert Decimal(data["escrow_balance"]) == Decimal("0")
        assert data["escrow_token_mint"] is None

        self.reporter.info("User created without escrow", context="Test")

    async def test_get_user_profile_complete_flow(self):
        """Test complete flow: create user, authenticate, get profile."""
        self.reporter.info("Testing complete user flow", context="Test")

        wallet = self._generate_unique_wallet()
        create_response = await self.client.post(
            "/api/users/",
            json={"wallet_address": wallet},
        )
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]

        get_response = await self.client.get(f"/api/users/{user_id}")
        assert get_response.status_code == 200
        assert get_response.json()["wallet_address"] == wallet

        wallet_response = await self.client.get(f"/api/users/wallet/{wallet}")
        assert wallet_response.status_code == 200
        assert wallet_response.json()["id"] == user_id

        self.reporter.info("Complete user flow successful", context="Test")


if __name__ == "__main__":
    TestUserRoutes.run_as_main()

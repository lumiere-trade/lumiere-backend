"""
Integration tests for Authentication API routes.

Tests the new auth flow:
- POST /api/auth/verify
- POST /api/auth/create-account
- POST /api/auth/login

Execution:
    laborant test pourtier --integration
    laborant test pourtier --file test_auth_routes.py
"""

import json

import httpx
from base58 import b58encode
from solders.keypair import Keypair
from sqlalchemy import delete, select, text

from pourtier.config.settings import get_settings
from pourtier.di.container import get_container
from pourtier.di.dependencies import get_db_session
from pourtier.domain.entities.user import User
from pourtier.infrastructure.persistence.database import Database
from pourtier.infrastructure.persistence.models import (
    Base,
    UserLegalAcceptanceModel,
    UserModel,
)
from pourtier.main import create_app
from shared.blockchain.wallets import PlatformWallets
from shared.tests import LaborantTest


class TestAuthRoutes(LaborantTest):
    """Integration tests for Authentication API routes."""

    component_name = "pourtier"
    test_category = "integration"

    db: Database = None
    client: httpx.AsyncClient = None
    alice_keypair: Keypair = None
    alice_wallet: str = None
    bob_keypair: Keypair = None
    bob_wallet: str = None

    async def async_setup(self):
        """Setup test database and client."""
        self.reporter.info(
            "Setting up auth API integration tests...", context="Setup"
        )

        # Load settings (DATABASE_URL from environment)
        settings = get_settings()
        self.reporter.info(f"Loaded ENV={settings.ENV}", context="Setup")

        # Create test database instance
        TestAuthRoutes.db = Database(database_url=settings.DATABASE_URL, echo=False)
        await TestAuthRoutes.db.connect()
        self.reporter.info("Connected to test database", context="Setup")

        # Drop and recreate tables
        async with TestAuthRoutes.db._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        self.reporter.info("Database schema created", context="Setup")

        # Seed legal documents
        await self._seed_legal_documents()

        # Override container's database with test database
        container = get_container()
        container._database = TestAuthRoutes.db

        # Initialize cache if enabled
        if settings.REDIS_ENABLED:
            await container.cache_client.connect()
            self.reporter.info("Redis cache connected", context="Setup")

        # Create test app with overridden dependencies
        app = create_app(settings)

        async def override_get_db_session():
            """Provide test database session."""
            async with TestAuthRoutes.db.session() as session:
                yield session

        app.dependency_overrides[get_db_session] = override_get_db_session
        self.reporter.info("Database dependency overridden", context="Setup")

        # Create async client
        TestAuthRoutes.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        )

        # Load test wallets
        TestAuthRoutes.alice_wallet = PlatformWallets.get_test_alice_address()
        TestAuthRoutes.alice_keypair = self._load_keypair(
            PlatformWallets.get_test_alice_keypair()
        )

        TestAuthRoutes.bob_wallet = PlatformWallets.get_test_bob_address()
        TestAuthRoutes.bob_keypair = self._load_keypair(
            PlatformWallets.get_test_bob_keypair()
        )

        self.reporter.info("Test wallets loaded", context="Setup")
        self.reporter.info("Auth API integration tests ready", context="Setup")

    async def async_teardown(self):
        """Cleanup test database and connections."""
        self.reporter.info(
            "Cleaning up auth API integration tests...", context="Teardown"
        )

        # Close AsyncClient
        if TestAuthRoutes.client:
            await TestAuthRoutes.client.aclose()

        # Disconnect cache
        settings = get_settings()
        container = get_container()
        if settings.REDIS_ENABLED and container._cache_client:
            await container.cache_client.disconnect()

        # Disconnect database
        if TestAuthRoutes.db:
            await TestAuthRoutes.db.disconnect()

        self.reporter.info("Cleanup complete", context="Teardown")

    async def async_setup_test(self):
        """Setup before each test - ensure clean state."""
        self.reporter.info("Verifying clean state...", context="Test")

        async with self.db.session() as session:
            await session.execute(
                delete(UserModel).where(
                    UserModel.wallet_address.in_(
                        [self.alice_wallet, self.bob_wallet]
                    )
                )
            )
            await session.commit()

        settings = get_settings()
        container = get_container()
        if settings.REDIS_ENABLED and container._multi_layer_cache:
            cache = container.multi_layer_cache
            async with cache.l1_lock:
                cache.l1_cache.clear()
            await cache.invalidate_pattern("user:*")

        self.reporter.info("Clean state verified", context="Test")

    async def async_teardown_test(self):
        """Cleanup after each test."""
        self.reporter.info("Cleaning up test traces...", context="Test")

        async with self.db.session() as session:
            result = await session.execute(
                select(UserModel.id).where(
                    UserModel.wallet_address.in_(
                        [self.alice_wallet, self.bob_wallet]
                    )
                )
            )
            user_ids = [row[0] for row in result]

            if user_ids:
                await session.execute(
                    delete(UserLegalAcceptanceModel).where(
                        UserLegalAcceptanceModel.user_id.in_(user_ids)
                    )
                )

            await session.execute(
                delete(UserModel).where(
                    UserModel.wallet_address.in_(
                        [self.alice_wallet, self.bob_wallet]
                    )
                )
            )
            await session.commit()

        settings = get_settings()
        container = get_container()
        if settings.REDIS_ENABLED and container._multi_layer_cache:
            cache = container.multi_layer_cache
            async with cache.l1_lock:
                cache.l1_cache.clear()
            await cache.invalidate_pattern("user:*")

        self.reporter.info("Test cleanup complete", context="Test")

    async def _seed_legal_documents(self):
        """Seed legal documents for testing."""
        self.reporter.info("Seeding legal documents...", context="Setup")

        async with self.db.session() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO legal_documents (
                        id, document_type, version, title, content,
                        status, effective_date, created_at, updated_at
                    ) VALUES (
                        gen_random_uuid(),
                        'terms_of_service',
                        '1.0.0',
                        'Terms of Service',
                        'Test Terms of Service Content',
                        'active',
                        NOW(),
                        NOW(),
                        NOW()
                    )
                """
                )
            )
            await session.commit()

        self.reporter.info("Legal documents seeded", context="Setup")

    def _load_keypair(self, path: str) -> Keypair:
        """Load Solana keypair from JSON file."""
        with open(path, "r") as f:
            secret = json.load(f)
        return Keypair.from_bytes(bytes(secret))

    def _sign_message(self, keypair: Keypair, message: str) -> str:
        """Sign a message with keypair."""
        message_bytes = message.encode("utf-8")
        signature = keypair.sign_message(message_bytes)
        return b58encode(bytes(signature)).decode("utf-8")

    async def _get_legal_document_ids(self) -> list[str]:
        """Get all active legal document IDs."""
        response = await self.client.get("/api/legal/documents")
        assert response.status_code == 200
        return [doc["id"] for doc in response.json()]

    async def _create_alice_account(self) -> dict:
        """Create Alice's account and return response data."""
        message = "Sign in to Lumiere"
        signature = self._sign_message(self.alice_keypair, message)
        document_ids = await self._get_legal_document_ids()

        response = await self.client.post(
            "/api/auth/create-account",
            json={
                "wallet_address": self.alice_wallet,
                "message": message,
                "signature": signature,
                "accepted_documents": document_ids,
                "ip_address": "127.0.0.1",
                "user_agent": "Test Client",
            },
        )

        assert response.status_code == 201
        return response.json()

    async def test_verify_wallet_new_user_valid_signature(self):
        """Test verifying wallet with valid signature for new user."""
        self.reporter.info(
            "Testing verify wallet (new user, valid signature)", context="Test"
        )

        message = "Sign in to Lumiere"
        signature = self._sign_message(self.alice_keypair, message)

        response = await self.client.post(
            "/api/auth/verify",
            json={
                "wallet_address": self.alice_wallet,
                "message": message,
                "signature": signature,
            },
        )

        assert response.status_code == 200

        data = response.json()
        assert data["signature_valid"] is True
        assert data["user_exists"] is False
        assert data["wallet_address"] == self.alice_wallet
        assert data["user_id"] is None

        self.reporter.info("Verify wallet successful (new user)", context="Test")

    async def test_verify_wallet_existing_user(self):
        """Test verifying wallet for existing user."""
        self.reporter.info("Testing verify wallet (existing user)", context="Test")

        account_data = await self._create_alice_account()
        user_id = account_data["user_id"]

        message = "Sign in to Lumiere"
        signature = self._sign_message(self.alice_keypair, message)

        response = await self.client.post(
            "/api/auth/verify",
            json={
                "wallet_address": self.alice_wallet,
                "message": message,
                "signature": signature,
            },
        )

        assert response.status_code == 200

        data = response.json()
        assert data["signature_valid"] is True
        assert data["user_exists"] is True
        assert data["user_id"] == user_id
        assert data["wallet_address"] == self.alice_wallet

        self.reporter.info("Verify wallet successful (existing user)", context="Test")

    async def test_verify_wallet_invalid_signature(self):
        """Test verifying wallet with invalid signature."""
        self.reporter.info("Testing verify wallet (invalid signature)", context="Test")

        message = "Sign in to Lumiere"
        fake_signature = "1" * 88

        response = await self.client.post(
            "/api/auth/verify",
            json={
                "wallet_address": self.alice_wallet,
                "message": message,
                "signature": fake_signature,
            },
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

        self.reporter.info("Invalid signature rejected", context="Test")

    async def test_verify_wallet_wrong_message(self):
        """Test verifying wallet with wrong message."""
        self.reporter.info("Testing verify wallet (wrong message)", context="Test")

        correct_message = "Sign in to Lumiere"
        signature = self._sign_message(self.alice_keypair, correct_message)

        wrong_message = "Different message"

        response = await self.client.post(
            "/api/auth/verify",
            json={
                "wallet_address": self.alice_wallet,
                "message": wrong_message,
                "signature": signature,
            },
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

        self.reporter.info("Wrong message rejected", context="Test")

    async def test_verify_wallet_invalid_address(self):
        """Test verifying wallet with invalid address format."""
        self.reporter.info("Testing verify wallet (invalid address)", context="Test")

        message = "Sign in to Lumiere"
        signature = self._sign_message(self.alice_keypair, message)

        response = await self.client.post(
            "/api/auth/verify",
            json={
                "wallet_address": "invalid_wallet",
                "message": message,
                "signature": signature,
            },
        )

        assert response.status_code == 422

        self.reporter.info("Invalid wallet address rejected", context="Test")

    async def test_create_account_success(self):
        """Test creating account with legal acceptance."""
        self.reporter.info("Testing create account (success)", context="Test")

        message = "Sign in to Lumiere"
        signature = self._sign_message(self.bob_keypair, message)
        document_ids = await self._get_legal_document_ids()

        response = await self.client.post(
            "/api/auth/create-account",
            json={
                "wallet_address": self.bob_wallet,
                "message": message,
                "signature": signature,
                "accepted_documents": document_ids,
                "ip_address": "127.0.0.1",
                "user_agent": "Test Client",
            },
        )

        assert response.status_code == 201

        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert "user_id" in data
        assert "wallet_address" in data

        assert data["token_type"] == "bearer"
        assert data["wallet_address"] == self.bob_wallet
        assert data["access_token"].count(".") == 2

        self.reporter.info("Account created successfully", context="Test")

    async def test_create_account_already_exists(self):
        """Test creating account that already exists."""
        self.reporter.info("Testing create account (already exists)", context="Test")

        await self._create_alice_account()

        message = "Sign in to Lumiere"
        signature = self._sign_message(self.alice_keypair, message)
        document_ids = await self._get_legal_document_ids()

        response = await self.client.post(
            "/api/auth/create-account",
            json={
                "wallet_address": self.alice_wallet,
                "message": message,
                "signature": signature,
                "accepted_documents": document_ids,
                "ip_address": "127.0.0.1",
                "user_agent": "Test Client",
            },
        )

        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

        self.reporter.info("Duplicate account rejected", context="Test")

    async def test_create_account_invalid_signature(self):
        """Test creating account with invalid signature."""
        self.reporter.info("Testing create account (invalid signature)", context="Test")

        message = "Sign in to Lumiere"
        fake_signature = "1" * 88
        document_ids = await self._get_legal_document_ids()

        response = await self.client.post(
            "/api/auth/create-account",
            json={
                "wallet_address": self.bob_wallet,
                "message": message,
                "signature": fake_signature,
                "accepted_documents": document_ids,
                "ip_address": "127.0.0.1",
                "user_agent": "Test Client",
            },
        )

        assert response.status_code == 400

        self.reporter.info("Invalid signature rejected", context="Test")

    async def test_create_account_missing_documents(self):
        """Test creating account without accepting documents."""
        self.reporter.info("Testing create account (missing documents)", context="Test")

        message = "Sign in to Lumiere"
        signature = self._sign_message(self.bob_keypair, message)

        response = await self.client.post(
            "/api/auth/create-account",
            json={
                "wallet_address": self.bob_wallet,
                "message": message,
                "signature": signature,
                "accepted_documents": [],
                "ip_address": "127.0.0.1",
                "user_agent": "Test Client",
            },
        )

        assert response.status_code == 422

        self.reporter.info("Missing documents rejected", context="Test")

    async def test_create_account_invalid_document_id(self):
        """Test creating account with invalid document ID."""
        self.reporter.info(
            "Testing create account (invalid document ID)", context="Test"
        )

        message = "Sign in to Lumiere"
        signature = self._sign_message(self.bob_keypair, message)

        response = await self.client.post(
            "/api/auth/create-account",
            json={
                "wallet_address": self.bob_wallet,
                "message": message,
                "signature": signature,
                "accepted_documents": ["00000000-0000-0000-0000-000000000000"],
                "ip_address": "127.0.0.1",
                "user_agent": "Test Client",
            },
        )

        assert response.status_code == 400

        self.reporter.info("Invalid document ID rejected", context="Test")

    async def test_login_success_compliant_user(self):
        """Test logging in compliant user."""
        self.reporter.info("Testing login (success, compliant)", context="Test")

        await self._create_alice_account()

        message = "Sign in to Lumiere"
        signature = self._sign_message(self.alice_keypair, message)

        response = await self.client.post(
            "/api/auth/login",
            json={
                "wallet_address": self.alice_wallet,
                "message": message,
                "signature": signature,
            },
        )

        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["wallet_address"] == self.alice_wallet
        assert data["is_compliant"] is True
        assert len(data["pending_documents"]) == 0

        self.reporter.info("Login successful (compliant user)", context="Test")

    async def test_login_user_not_found(self):
        """Test logging in non-existent user."""
        self.reporter.info("Testing login (user not found)", context="Test")

        message = "Sign in to Lumiere"
        signature = self._sign_message(self.bob_keypair, message)

        response = await self.client.post(
            "/api/auth/login",
            json={
                "wallet_address": self.bob_wallet,
                "message": message,
                "signature": signature,
            },
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        self.reporter.info("User not found error returned", context="Test")

    async def test_login_invalid_signature(self):
        """Test logging in with invalid signature."""
        self.reporter.info("Testing login (invalid signature)", context="Test")

        await self._create_alice_account()

        message = "Sign in to Lumiere"
        fake_signature = "1" * 88

        response = await self.client.post(
            "/api/auth/login",
            json={
                "wallet_address": self.alice_wallet,
                "message": message,
                "signature": fake_signature,
            },
        )

        assert response.status_code == 401

        self.reporter.info("Invalid signature rejected", context="Test")

    async def test_login_non_compliant_user(self):
        """Test logging in user with pending legal documents."""
        self.reporter.info("Testing login (non-compliant user)", context="Test")

        container = get_container()
        async with self.db.session() as session:
            user_repo = container.get_user_repository(session)
            user = User(wallet_address=self.bob_wallet)
            await user_repo.create(user)

        message = "Sign in to Lumiere"
        signature = self._sign_message(self.bob_keypair, message)

        response = await self.client.post(
            "/api/auth/login",
            json={
                "wallet_address": self.bob_wallet,
                "message": message,
                "signature": signature,
            },
        )

        assert response.status_code == 200

        data = response.json()
        assert data["is_compliant"] is False
        assert len(data["pending_documents"]) > 0

        self.reporter.info("Login successful (non-compliant user)", context="Test")


if __name__ == "__main__":
    TestAuthRoutes.run_as_main()

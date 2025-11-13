"""
End-to-end authentication flow test with legal compliance.

Tests new auth flow:
1. Verify wallet signature
2. Get legal documents
3. Create account with legal acceptance
import asyncio
4. Login existing user

Uses Alice test wallet for authentication.
import asyncio

Usage:
    laborant pourtier --e2e
"""

import json

import httpx
from base58 import b58encode
from solders.keypair import Keypair
from sqlalchemy import text

from pourtier.config.settings import get_settings
from pourtier.infrastructure.persistence.database import Database
from pourtier.infrastructure.persistence.models import Base
from shared.blockchain.wallets import PlatformWallets
from shared.tests import LaborantTest

AUTH_MESSAGE = "Sign this message to authenticate with Lumiere"


def load_keypair(path: str) -> Keypair:
    """Load Solana keypair from JSON file."""
    with open(path, "r") as f:
        secret = json.load(f)
    return Keypair.from_bytes(bytes(secret))


def sign_message_with_alice(message: str) -> str:
    """Sign message with Alice's keypair."""
    keypair = load_keypair(PlatformWallets.get_test_alice_keypair())
    message_bytes = message.encode("utf-8")
    signature = keypair.sign_message(message_bytes)
    return b58encode(bytes(signature)).decode("utf-8")


class TestAuthFlow(LaborantTest):
    """End-to-end authentication flow test."""

    component_name = "pourtier"
    test_category = "e2e"

    db: Database = None
    api_base_url: str = None
    alice_wallet: str = None
    token: str = None
    user_id: str = None
    document_ids: list = []

    async def async_setup(self):
        """Setup test environment."""
        self.reporter.info("Setting up E2E test environment...", context="Setup")

        settings = get_settings()
        TestAuthFlow.api_base_url = f"http://localhost:{settings.API_PORT}"
        TestAuthFlow.alice_wallet = PlatformWallets.get_test_alice_address()

        self.reporter.info(f"API URL: {self.api_base_url}", context="Setup")
        self.reporter.info(f"Alice wallet: {self.alice_wallet}", context="Setup")

        TestAuthFlow.db = Database(database_url=settings.DATABASE_URL, echo=False)
        await TestAuthFlow.db.connect()

        await TestAuthFlow.db.reset_schema_for_testing(Base.metadata)

        await self._seed_legal_documents()

        await self._wait_for_api()

        self.reporter.info("E2E environment ready", context="Setup")

    async def async_teardown(self):
        """Cleanup test environment."""
        self.reporter.info("Cleaning up E2E environment...", context="Teardown")

        if TestAuthFlow.db:
            await TestAuthFlow.db.disconnect()

        self.reporter.info("Cleanup complete", context="Teardown")

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

    async def _wait_for_api(self):
        """Wait for API to be ready."""
        self.reporter.info("Waiting for API...", context="Setup")

        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.api_base_url}/health", timeout=2.0
                    )
                    if response.status_code == 200:
                        self.reporter.info(
                            f"API ready (attempt {attempt + 1})", context="Setup"
                        )
                        return
            except Exception:
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1)

        raise RuntimeError("API not accessible")

    async def test_01_health_check(self):
        """Test health check endpoint."""
        self.reporter.info("Testing health endpoint...", context="Test")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base_url}/health")

            assert response.status_code == 200

            data = response.json()
            assert data["status"] in ["healthy", "degraded"]

            self.reporter.info("Health check passed", context="Test")

    async def test_02_get_legal_documents(self):
        """Test getting active legal documents."""
        self.reporter.info("Getting legal documents...", context="Test")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base_url}/api/legal/documents")

            assert response.status_code == 200

            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0

            TestAuthFlow.document_ids = [doc["id"] for doc in data]

            self.reporter.info(f"Found {len(data)} legal documents", context="Test")

    async def test_03_verify_wallet_new_user(self):
        """Test verifying wallet for new user."""
        self.reporter.info("Verifying wallet (new user)...", context="Test")

        signature = sign_message_with_alice(AUTH_MESSAGE)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base_url}/api/auth/verify",
                json={
                    "wallet_address": self.alice_wallet,
                    "message": AUTH_MESSAGE,
                    "signature": signature,
                },
            )

            assert response.status_code == 200

            data = response.json()
            assert data["signature_valid"] is True
            assert data["user_exists"] is False

            self.reporter.info("Wallet verified - user does not exist", context="Test")

    async def test_04_create_account_with_legal(self):
        """Test creating account with legal acceptance."""
        self.reporter.info("Creating account with legal acceptance...", context="Test")

        signature = sign_message_with_alice(AUTH_MESSAGE)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base_url}/api/auth/create-account",
                json={
                    "wallet_address": self.alice_wallet,
                    "message": AUTH_MESSAGE,
                    "signature": signature,
                    "wallet_type": "Phantom",
                    "accepted_documents": self.document_ids,
                    "ip_address": "127.0.0.1",
                    "user_agent": "E2E Test Client",
                },
            )

            assert response.status_code == 201

            data = response.json()
            assert "access_token" in data
            assert data["wallet_address"] == self.alice_wallet

            TestAuthFlow.token = data["access_token"]
            TestAuthFlow.user_id = data["user_id"]

            self.reporter.info("Account created successfully", context="Test")

    async def test_05_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with valid token."""
        self.reporter.info("Accessing protected endpoint...", context="Test")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base_url}/api/users/me",
                headers={"Authorization": f"Bearer {self.token}"},
            )

            assert response.status_code == 200

            data = response.json()
            assert data["wallet_address"] == self.alice_wallet
            assert data["wallet_type"] == "Phantom"
            assert data["id"] == self.user_id
            assert "pending_documents" in data
            assert isinstance(data["pending_documents"], list)
            assert len(data["pending_documents"]) == 0

            self.reporter.info("Protected endpoint accessed", context="Test")

    async def test_06_login_existing_user(self):
        """Test logging in existing user."""
        self.reporter.info("Logging in existing user...", context="Test")

        signature = sign_message_with_alice(AUTH_MESSAGE)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base_url}/api/auth/login",
                json={
                    "wallet_address": self.alice_wallet,
                    "message": AUTH_MESSAGE,
                    "signature": signature,
                    "wallet_type": "Phantom",
                },
            )

            assert response.status_code == 200

            data = response.json()
            assert data["user_id"] == self.user_id
            assert data["is_compliant"] is True

            self.reporter.info("Login successful", context="Test")

    async def test_07_verify_wallet_existing_user(self):
        """Test verifying wallet for existing user."""
        self.reporter.info("Verifying wallet (existing user)...", context="Test")

        signature = sign_message_with_alice(AUTH_MESSAGE)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base_url}/api/auth/verify",
                json={
                    "wallet_address": self.alice_wallet,
                    "message": AUTH_MESSAGE,
                    "signature": signature,
                },
            )

            assert response.status_code == 200

            data = response.json()
            assert data["signature_valid"] is True
            assert data["user_exists"] is True
            assert data["user_id"] == self.user_id

            self.reporter.info("Wallet verified - user exists", context="Test")

    async def test_08_invalid_token(self):
        """Test rejecting invalid token."""
        self.reporter.info("Testing invalid token rejection...", context="Test")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base_url}/api/users/me",
                headers={"Authorization": "Bearer invalid_token_123"},
            )

            assert response.status_code == 401

            self.reporter.info("Invalid token correctly rejected", context="Test")

    async def test_09_no_token(self):
        """Test rejecting request without token."""
        self.reporter.info("Testing request without token...", context="Test")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base_url}/api/users/me")

            assert response.status_code == 403

            self.reporter.info("Request without token rejected", context="Test")

    async def test_10_invalid_signature(self):
        """Test rejecting invalid signature."""
        self.reporter.info("Testing invalid signature rejection...", context="Test")

        fake_signature = "1" * 88

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base_url}/api/auth/verify",
                json={
                    "wallet_address": self.alice_wallet,
                    "message": AUTH_MESSAGE,
                    "signature": fake_signature,
                },
            )

            assert response.status_code == 401

            self.reporter.info("Invalid signature correctly rejected", context="Test")


if __name__ == "__main__":
    TestAuthFlow.run_as_main()

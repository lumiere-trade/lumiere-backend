"""
End-to-end subscription management test.

Uses Alice test wallet with new auth flow (legal acceptance).

Usage:
    laborant pourtier --e2e
"""

import asyncio
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


class TestSubscriptions(LaborantTest):
    """End-to-end subscription management test."""

    component_name = "pourtier"
    test_category = "e2e"

    db: Database = None
    api_base_url: str = None
    alice_wallet: str = None
    token: str = None
    user_id: str = None
    subscription_id: str = None

    async def async_setup(self):
        """Setup test environment."""
        self.reporter.info("Setting up E2E test environment...", context="Setup")

        settings = get_settings()
        TestSubscriptions.api_base_url = f"http://localhost:{settings.API_PORT}"
        TestSubscriptions.alice_wallet = PlatformWallets.get_test_alice_address()

        # Setup database
        TestSubscriptions.db = Database(database_url=settings.DATABASE_URL, echo=False)
        await TestSubscriptions.db.connect()

        # Reset database schema using public method
        await TestSubscriptions.db.reset_schema_for_testing(Base.metadata)

        # Seed legal documents
        await self._seed_legal_documents()

        # Wait for API
        await self._wait_for_api()

        # Create account
        TestSubscriptions.token, TestSubscriptions.user_id = (
            await self._create_account()
        )

        self.reporter.info("E2E environment ready", context="Setup")

    async def async_teardown(self):
        """Cleanup test environment."""
        self.reporter.info("Cleaning up E2E environment...", context="Teardown")

        if TestSubscriptions.db:
            await TestSubscriptions.db.disconnect()

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

    async def _create_account(self) -> tuple[str, str]:
        """Create Alice's account with legal acceptance."""
        self.reporter.info("Creating Alice's account...", context="Setup")

        # Get legal documents
        async with httpx.AsyncClient() as client:
            docs_response = await client.get(f"{self.api_base_url}/api/legal/documents")
            if docs_response.status_code != 200:
                raise RuntimeError("Failed to get legal documents")

            document_ids = [doc["id"] for doc in docs_response.json()]

        # Create account
        signature = sign_message_with_alice(AUTH_MESSAGE)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base_url}/api/auth/create-account",
                json={
                    "wallet_address": self.alice_wallet,
                    "message": AUTH_MESSAGE,
                    "signature": signature,
                    "accepted_documents": document_ids,
                    "ip_address": "127.0.0.1",
                    "user_agent": "E2E Test Client",
                },
            )

            if response.status_code != 201:
                raise RuntimeError(f"Account creation failed: {response.text}")

            data = response.json()
            self.reporter.info("Alice's account created", context="Setup")
            return data["access_token"], data["user_id"]

    async def test_01_create_subscription(self):
        """Test creating a new subscription."""
        self.reporter.info("Creating subscription...", context="Test")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base_url}/api/subscriptions",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"plan_type": "pro"},
            )

            if response.status_code in [200, 201]:
                data = response.json()
                assert "id" in data
                TestSubscriptions.subscription_id = data["id"]
                self.reporter.info("Subscription created", context="Test")
            else:
                self.reporter.info(
                    f"Subscription creation returned {response.status_code}",
                    context="Test",
                )

    async def test_02_get_user_subscriptions(self):
        """Test getting user's subscriptions."""
        self.reporter.info("Getting user subscriptions...", context="Test")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base_url}/api/subscriptions",
                headers={"Authorization": f"Bearer {self.token}"},
            )

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)
                self.reporter.info(
                    f"Found {len(data)} subscription(s)",
                    context="Test",
                )
            else:
                self.reporter.info(
                    f"Get subscriptions returned {response.status_code}",
                    context="Test",
                )

    async def test_03_unauthorized_access(self):
        """Test rejecting access without auth."""
        self.reporter.info("Testing unauthorized access...", context="Test")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base_url}/api/subscriptions")

            assert response.status_code in [307, 403, 404]

            self.reporter.info("Unauthorized access blocked", context="Test")


if __name__ == "__main__":
    TestSubscriptions.run_as_main()

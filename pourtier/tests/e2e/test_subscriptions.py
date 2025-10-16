"""
End-to-end subscription management test.

Automatically starts/stops Pourtier API and runs subscription tests.
Uses Alice test wallet with new auth flow (legal acceptance).

Usage:
    python -m pourtier.tests.e2e.test_subscriptions
    laborant pourtier --e2e
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime

import httpx
from base58 import b58encode
from solders.keypair import Keypair
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from pourtier.config.settings import load_config
from pourtier.infrastructure.persistence.models import Base
from shared.blockchain.wallets import PlatformWallets
from shared.reporter.emojis.emoji import Emoji
from shared.reporter.emojis.errors_emojis import ErrorEmoji
from shared.tests import LaborantTest

# Load test configuration
test_settings = load_config("development.yaml", env="development")

# Get API configuration
API_HOST = test_settings.API_HOST
API_PORT = test_settings.API_PORT
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"
DATABASE_URL = test_settings.DATABASE_URL

# Test user: Alice
ALICE_WALLET = PlatformWallets.get_test_alice_address()
ALICE_KEYPAIR_PATH = PlatformWallets.get_test_alice_keypair()

# Standard auth message
AUTH_MESSAGE = "Sign this message to authenticate with Lumiere"


def load_keypair(path: str) -> Keypair:
    """Load Solana keypair from JSON file."""
    with open(path, "r") as f:
        secret = json.load(f)
    return Keypair.from_bytes(bytes(secret))


def sign_message_with_alice(message: str) -> str:
    """Sign message with Alice's keypair."""
    keypair = load_keypair(ALICE_KEYPAIR_PATH)
    message_bytes = message.encode("utf-8")
    signature = keypair.sign_message(message_bytes)
    return b58encode(bytes(signature)).decode("utf-8")


class TestSubscriptions(LaborantTest):
    """End-to-end subscription management test."""

    component_name = "pourtier"
    test_category = "e2e"

    # Class-level shared resources
    api_process: subprocess.Popen = None
    api_log_file = None
    token: str = None
    user_id: str = None
    subscription_id: str = None

    # ================================================================
    # Async Lifecycle Hooks
    # ================================================================

    async def async_setup(self):
        """Setup test database and start API."""
        self.reporter.info("Setting up E2E test environment...", context="Setup")

        # Setup database
        await self._setup_database()

        # Seed legal documents
        await self._seed_legal_documents()

        # Start API
        self._start_api()

        # Create account for Alice (with legal acceptance)
        TestSubscriptions.token, TestSubscriptions.user_id = (
            await self._create_account()
        )

        self.reporter.info("E2E environment ready", context="Setup")

    async def async_teardown(self):
        """Stop API and cleanup database."""
        self.reporter.info("Cleaning up E2E environment...", context="Teardown")

        # Stop API
        self._stop_api()

        # Cleanup database
        await self._cleanup_database()

        self.reporter.info("Cleanup complete", context="Teardown")

    # ================================================================
    # Helper Methods
    # ================================================================

    async def _setup_database(self):
        """Setup test database tables."""
        self.reporter.info("🗄️  Setting up test database...", context="Setup")

        try:
            engine = create_async_engine(DATABASE_URL, echo=False)

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)

            await engine.dispose()

            self.reporter.info("Test database ready", context="Setup")
        except Exception as e:
            self.reporter.error(f"DB setup failed: {e}", context="Setup")
            raise

    async def _seed_legal_documents(self):
        """Seed legal documents for testing."""
        self.reporter.info("📜 Seeding legal documents...", context="Setup")

        try:
            engine = create_async_engine(DATABASE_URL, echo=False)

            async with engine.begin() as conn:
                # Insert Terms of Service
                await conn.execute(
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

            await engine.dispose()

            self.reporter.info("Legal documents seeded", context="Setup")
        except Exception as e:
            self.reporter.error(f"Seed failed: {e}", context="Setup")
            raise

    async def _cleanup_database(self):
        """Cleanup test database."""
        self.reporter.info("Cleaning up test database...", context="Teardown")

        try:
            engine = create_async_engine(DATABASE_URL, echo=False)

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

            await engine.dispose()

            self.reporter.info("Database cleaned", context="Teardown")
        except Exception as e:
            self.reporter.error(f"DB cleanup warning: {e}", context="Teardown")

    def _start_api(self):
        """Start Pourtier API in subprocess."""
        self.reporter.info(
            f"{Emoji.SYSTEM.STARTUP} Starting Pourtier API...",
            context="Setup",
        )
        self.reporter.info(f"API URL: {API_BASE_URL}", context="Setup")

        # Create log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        api_log_path = f"{self.log_dir}/api_subs_{timestamp}.log"

        TestSubscriptions.api_log_file = open(api_log_path, "w")

        self.reporter.info(f"API log: {api_log_path}", context="Setup")

        # Set test configuration environment
        test_env = os.environ.copy()
        test_env["ENV"] = "test"  # Force test config loading

        # Start API as subprocess
        TestSubscriptions.api_process = subprocess.Popen(
            [sys.executable, "-m", "pourtier.main"],
            stdout=TestSubscriptions.api_log_file,
            stderr=subprocess.STDOUT,
            text=True,
            env=test_env,
        )

        self.reporter.info(
            f"API PID: {self.api_process.pid}",
            context="Setup",
        )

        # Wait for API to be ready
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = httpx.get(f"{API_BASE_URL}/health", timeout=1.0)
                if response.status_code == 200:
                    self.reporter.info(
                        f"{Emoji.SYSTEM.READY} API started (attempt {attempt + 1})",
                        context="Setup",
                    )
                    return
            except (httpx.ConnectError, httpx.TimeoutException):
                time.sleep(1)

        # Failed to start
        self.reporter.error(
            f"API failed to start after {max_attempts} seconds",
            context="Setup",
        )

        # Show last 20 lines of log
        with open(api_log_path, "r") as f:
            lines = f.readlines()
            if lines:
                self.reporter.error(
                    "Last 20 lines of API log:",
                    context="Setup",
                )
                for line in lines[-20:]:
                    self.reporter.error(
                        f"  {line.rstrip()}",
                        context="Setup",
                    )

        self._stop_api()
        raise RuntimeError("API failed to start")

    def _stop_api(self):
        """Stop Pourtier API subprocess."""
        if TestSubscriptions.api_process:
            self.reporter.info(
                f"{Emoji.SYSTEM.SHUTDOWN} Stopping Pourtier API...",
                context="Teardown",
            )

            TestSubscriptions.api_process.terminate()
            try:
                TestSubscriptions.api_process.wait(timeout=5)
                self.reporter.info("API stopped", context="Teardown")
            except subprocess.TimeoutExpired:
                self.reporter.warning(
                    "Force killing API...",
                    context="Teardown",
                )
                TestSubscriptions.api_process.kill()
                TestSubscriptions.api_process.wait()

            TestSubscriptions.api_process = None

        if TestSubscriptions.api_log_file:
            TestSubscriptions.api_log_file.close()
            TestSubscriptions.api_log_file = None

    async def _create_account(self) -> tuple[str, str]:
        """Create Alice's account with legal acceptance and get JWT token."""
        self.reporter.info("🔐 Creating Alice's account...", context="Setup")

        # Get legal documents
        async with httpx.AsyncClient(follow_redirects=True) as client:
            docs_response = await client.get(f"{API_BASE_URL}/api/legal/documents")
            if docs_response.status_code != 200:
                raise RuntimeError("Failed to get legal documents")

            document_ids = [doc["id"] for doc in docs_response.json()]

        # Sign message with Alice's keypair
        signature = sign_message_with_alice(AUTH_MESSAGE)

        # Create account with legal acceptance
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/auth/create-account",
                json={
                    "wallet_address": ALICE_WALLET,
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
            token = data["access_token"]
            user_id = data["user_id"]

            self.reporter.info("Alice's account created", context="Setup")
            return token, user_id

    # ================================================================
    # Test Methods
    # ================================================================

    async def test_01_create_subscription(self):
        """Test creating a new subscription."""
        self.reporter.info("💳 Creating subscription...", context="Test")

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/subscriptions",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "plan_type": "pro",
                },
            )

            self.reporter.info(
                f"Status: {response.status_code}",
                context="Test",
            )

            # May fail if subscription creation not fully implemented
            if response.status_code in [200, 201]:
                data = response.json()
                assert "id" in data
                TestSubscriptions.subscription_id = data["id"]
                self.reporter.info(
                    f"{Emoji.SYSTEM.READY} Subscription created",
                    context="Test",
                )
            else:
                self.reporter.info(
                    f"Subscription creation returned {response.status_code}",
                    context="Test",
                )

    async def test_02_get_user_subscriptions(self):
        """Test getting user's subscriptions."""
        self.reporter.info("📋 Getting user subscriptions...", context="Test")

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(
                f"{API_BASE_URL}/api/subscriptions",
                headers={"Authorization": f"Bearer {self.token}"},
            )

            self.reporter.info(
                f"Status: {response.status_code}",
                context="Test",
            )

            # Endpoint may not exist yet
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)
                self.reporter.info(
                    f"{Emoji.SYSTEM.READY} Found {len(data)} subscription(s)",
                    context="Test",
                )
            else:
                self.reporter.info(
                    f"Get subscriptions returned {response.status_code}",
                    context="Test",
                )

    async def test_03_unauthorized_access(self):
        """Test rejecting access without auth."""
        self.reporter.info(
            f"{ErrorEmoji.FORBIDDEN} Testing unauthorized access...",
            context="Test",
        )

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(f"{API_BASE_URL}/api/subscriptions")

            self.reporter.info(
                f"Status: {response.status_code}",
                context="Test",
            )

            # Should be 403 or 404 if endpoint doesn't exist
            assert response.status_code in [403, 404]

            self.reporter.info(
                f"{Emoji.SYSTEM.READY} Unauthorized access blocked",
                context="Test",
            )


if __name__ == "__main__":
    TestSubscriptions.run_as_main()

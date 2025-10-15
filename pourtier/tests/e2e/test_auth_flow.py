"""
End-to-end authentication flow test with legal compliance.

Tests new auth flow:
1. Verify wallet signature
2. Get legal documents
3. Create account with legal acceptance
4. Login existing user

Uses Alice test wallet for authentication.

Usage:
    python -m pourtier.tests.e2e.test_auth_flow
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
test_settings = load_config("test.yaml")

# Get API configuration
API_HOST = test_settings.API_HOST
API_PORT = test_settings.API_PORT
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"
DATABASE_URL = test_settings.DATABASE_URL

# Test user: Alice
ALICE_WALLET = PlatformWallets.get_test_alice_address()
ALICE_KEYPAIR_PATH = PlatformWallets.get_test_alice_keypair()

# Standard Solana auth message
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


class TestAuthFlow(LaborantTest):
    """End-to-end authentication flow test."""

    component_name = "pourtier"
    test_category = "e2e"

    # Class-level shared resources
    api_process: subprocess.Popen = None
    api_log_file = None
    token: str = None
    user_id: str = None
    document_ids: list = []

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
        api_log_path = f"{self.log_dir}/api_{timestamp}.log"

        TestAuthFlow.api_log_file = open(api_log_path, "w")

        self.reporter.info(f"API log: {api_log_path}", context="Setup")

        # Set test configuration environment
        test_env = os.environ.copy()
        test_env["ENV"] = "test"  # Force test config loading

        # Start API as subprocess
        TestAuthFlow.api_process = subprocess.Popen(
            [sys.executable, "-m", "pourtier.main"],
            stdout=TestAuthFlow.api_log_file,
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
        if TestAuthFlow.api_process:
            self.reporter.info(
                f"{Emoji.SYSTEM.SHUTDOWN} Stopping Pourtier API...",
                context="Teardown",
            )

            TestAuthFlow.api_process.terminate()
            try:
                TestAuthFlow.api_process.wait(timeout=5)
                self.reporter.info("API stopped", context="Teardown")
            except subprocess.TimeoutExpired:
                self.reporter.warning(
                    "Force killing API...",
                    context="Teardown",
                )
                TestAuthFlow.api_process.kill()
                TestAuthFlow.api_process.wait()

            TestAuthFlow.api_process = None

        if TestAuthFlow.api_log_file:
            TestAuthFlow.api_log_file.close()
            TestAuthFlow.api_log_file = None

    # ================================================================
    # Test Methods - NEW AUTH FLOW
    # ================================================================

    async def test_01_health_check(self):
        """Test health check endpoint."""
        self.reporter.info(
            f"{Emoji.NETWORK.HTTP} Testing health endpoint...",
            context="Test",
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/health")

            self.reporter.info(
                f"Status: {response.status_code}",
                context="Test",
            )

            assert response.status_code == 200

            data = response.json()
            assert data["status"] in ["healthy", "degraded"]

            self.reporter.info(
                f"{Emoji.SYSTEM.READY} Health check passed",
                context="Test",
            )

    async def test_02_get_legal_documents(self):
        """Test getting active legal documents."""
        self.reporter.info(
            "📜 Getting legal documents...",
            context="Test",
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/legal/documents")

            self.reporter.info(
                f"Status: {response.status_code}",
                context="Test",
            )

            assert response.status_code == 200

            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0

            # Store document IDs for account creation
            TestAuthFlow.document_ids = [doc["id"] for doc in data]

            self.reporter.info(
                f"Found {len(data)} legal documents",
                context="Test",
            )
            self.reporter.info(
                f"Document IDs: {self.document_ids}",
                context="Test",
            )

    async def test_03_verify_wallet_new_user(self):
        """Test verifying wallet for new user."""
        self.reporter.info(
            "🔐 Verifying wallet (Alice - new user)...",
            context="Test",
        )

        # Sign message with Alice's keypair
        signature = sign_message_with_alice(AUTH_MESSAGE)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/auth/verify",
                json={
                    "wallet_address": ALICE_WALLET,
                    "message": AUTH_MESSAGE,
                    "signature": signature,
                },
            )

            self.reporter.info(
                f"Status: {response.status_code}",
                context="Test",
            )

            assert response.status_code == 200

            data = response.json()

            assert data["signature_valid"] is True
            assert data["user_exists"] is False
            assert data["wallet_address"] == ALICE_WALLET

            self.reporter.info(
                "Wallet verified - user does not exist",
                context="Test",
            )

    async def test_04_create_account_with_legal(self):
        """Test creating account with legal acceptance."""
        self.reporter.info(
            "Creating account with legal acceptance...",
            context="Test",
        )

        # Sign message with Alice's keypair
        signature = sign_message_with_alice(AUTH_MESSAGE)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/auth/create-account",
                json={
                    "wallet_address": ALICE_WALLET,
                    "message": AUTH_MESSAGE,
                    "signature": signature,
                    "accepted_documents": self.document_ids,
                    "ip_address": "127.0.0.1",
                    "user_agent": "E2E Test Client",
                },
            )

            self.reporter.info(
                f"Status: {response.status_code}",
                context="Test",
            )

            assert response.status_code == 201

            data = response.json()

            assert "access_token" in data
            assert "token_type" in data
            assert "user_id" in data
            assert "wallet_address" in data

            assert data["token_type"] == "bearer"
            assert data["wallet_address"] == ALICE_WALLET

            # Store token and user_id
            TestAuthFlow.token = data["access_token"]
            TestAuthFlow.user_id = data["user_id"]

            # Validate JWT format
            assert self.token.count(".") == 2

            self.reporter.info(
                "Account created successfully",
                context="Test",
            )
            self.reporter.info(
                f"User ID: {self.user_id}",
                context="Test",
            )
            self.reporter.info(
                f"Token: {self.token[:50]}...",
                context="Test",
            )

    async def test_05_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with valid token."""
        self.reporter.info(
            f"{Emoji.NETWORK.HTTP} Accessing protected endpoint...",
            context="Test",
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/users/me",
                headers={"Authorization": f"Bearer {self.token}"},
            )

            self.reporter.info(
                f"Status: {response.status_code}",
                context="Test",
            )

            assert response.status_code == 200

            data = response.json()

            assert data["wallet_address"] == ALICE_WALLET
            assert data["id"] == self.user_id
            assert "escrow_balance" in data

            self.reporter.info(
                "Protected endpoint accessed",
                context="Test",
            )

    async def test_06_login_existing_user(self):
        """Test logging in existing user."""
        self.reporter.info(
            "🔐 Logging in existing user (Alice)...",
            context="Test",
        )

        # Sign message with Alice's keypair
        signature = sign_message_with_alice(AUTH_MESSAGE)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/auth/login",
                json={
                    "wallet_address": ALICE_WALLET,
                    "message": AUTH_MESSAGE,
                    "signature": signature,
                },
            )

            self.reporter.info(
                f"Status: {response.status_code}",
                context="Test",
            )

            assert response.status_code == 200

            data = response.json()

            assert "access_token" in data
            assert data["wallet_address"] == ALICE_WALLET
            assert data["user_id"] == self.user_id
            assert data["is_compliant"] is True
            assert len(data["pending_documents"]) == 0

            self.reporter.info(
                "Login successful - user is compliant",
                context="Test",
            )

    async def test_07_verify_wallet_existing_user(self):
        """Test verifying wallet for existing user."""
        self.reporter.info(
            "🔐 Verifying wallet (Alice - existing user)...",
            context="Test",
        )

        # Sign message with Alice's keypair
        signature = sign_message_with_alice(AUTH_MESSAGE)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/auth/verify",
                json={
                    "wallet_address": ALICE_WALLET,
                    "message": AUTH_MESSAGE,
                    "signature": signature,
                },
            )

            self.reporter.info(
                f"Status: {response.status_code}",
                context="Test",
            )

            assert response.status_code == 200

            data = response.json()

            assert data["signature_valid"] is True
            assert data["user_exists"] is True
            assert data["user_id"] == self.user_id
            assert data["wallet_address"] == ALICE_WALLET

            self.reporter.info(
                "Wallet verified - user exists",
                context="Test",
            )

    async def test_08_invalid_token(self):
        """Test rejecting invalid token."""
        self.reporter.info(
            f"{ErrorEmoji.FORBIDDEN} Testing invalid token rejection...",
            context="Test",
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/users/me",
                headers={"Authorization": "Bearer invalid_token_123"},
            )

            self.reporter.info(
                f"Status: {response.status_code}",
                context="Test",
            )

            assert response.status_code == 401

            self.reporter.info(
                "Invalid token correctly rejected",
                context="Test",
            )

    async def test_09_no_token(self):
        """Test rejecting request without token."""
        self.reporter.info(
            f"{ErrorEmoji.FORBIDDEN} Testing request without token...",
            context="Test",
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/users/me")

            self.reporter.info(
                f"Status: {response.status_code}",
                context="Test",
            )

            assert response.status_code == 403

            self.reporter.info(
                "Request without token rejected",
                context="Test",
            )

    async def test_10_invalid_signature(self):
        """Test rejecting invalid signature."""
        self.reporter.info(
            f"{ErrorEmoji.FORBIDDEN} Testing invalid signature rejection...",
            context="Test",
        )

        # Use fake signature
        fake_signature = "1" * 88

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/auth/verify",
                json={
                    "wallet_address": ALICE_WALLET,
                    "message": AUTH_MESSAGE,
                    "signature": fake_signature,
                },
            )

            self.reporter.info(
                f"Status: {response.status_code}",
                context="Test",
            )

            assert response.status_code == 401

            self.reporter.info(
                "Invalid signature correctly rejected",
                context="Test",
            )


if __name__ == "__main__":
    TestAuthFlow.run_as_main()

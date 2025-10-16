"""
E2E Test: User Onboarding + Escrow Management Flow.

Tests complete user journey with REAL blockchain transactions via Passeur.

Flow:
1. Get legal documents
2. Create account with legal acceptance (NEW AUTH)
3. Check wallet balance (use what's available)
4. Initialize escrow (REAL Solana tx + DB update via API)
5. Deposit available funds (REAL Solana tx)
6. Delegate platform authority (REAL Solana tx)
7. Verify balance (sync from blockchain)
8. Withdraw partial funds (REAL Solana tx)
9. Revoke platform authority (REAL Solana tx)
10. Close escrow (cleanup)

Usage:
    python -m pourtier.tests.e2e.test_user_onboarding_escrow_flow
    laborant pourtier --e2e
"""

import asyncio
import json
import multiprocessing
import os
from decimal import Decimal

import httpx
from base58 import b58encode
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from passeur.tests.helpers.bridge_manager import BridgeManager
from pourtier.config.settings import load_config
from pourtier.config.settings import settings as prod_settings
from pourtier.di.container import get_container
from pourtier.di.dependencies import get_db_session
from pourtier.infrastructure.persistence.database import Database
from pourtier.infrastructure.persistence.models import Base
from pourtier.main import app
from shared.blockchain.transaction_signer import TransactionSigner
from shared.blockchain.wallets import PlatformWallets
from shared.tests import LaborantTest

# Load test configuration
test_settings = load_config("test.yaml")
TEST_DATABASE_URL = test_settings.DATABASE_URL
API_BASE_URL = f"http://{test_settings.API_HOST}:{test_settings.API_PORT}"

# Standard auth message
AUTH_MESSAGE = "Sign this message to authenticate with Lumiere"


def load_keypair(path: str) -> Keypair:
    """Load Solana keypair from JSON file."""
    with open(path, "r") as f:
        secret = json.load(f)
    return Keypair.from_bytes(bytes(secret))


def sign_message(keypair_path: str, message: str) -> str:
    """Sign message with keypair."""
    keypair = load_keypair(keypair_path)
    message_bytes = message.encode("utf-8")
    signature = keypair.sign_message(message_bytes)
    return b58encode(bytes(signature)).decode("utf-8")


def run_api_server():
    """
    Run Pourtier API server in separate process with TEST config.

    CRITICAL: Sets all environment variables BEFORE importing app
    to ensure child process uses test configuration.
    """
    # Set environment BEFORE any pourtier imports
    os.environ["POURTIER_CONFIG"] = "test.yaml"
    os.environ["ENV"] = "test"
    os.environ["API_HOST"] = test_settings.API_HOST
    os.environ["API_PORT"] = str(test_settings.API_PORT)
    os.environ["DATABASE_URL"] = test_settings.DATABASE_URL
    os.environ["PASSEUR_BRIDGE_URL"] = test_settings.PASSEUR_BRIDGE_URL
    os.environ["SOLANA_RPC_URL"] = test_settings.SOLANA_RPC_URL
    os.environ["ESCROW_PROGRAM_ID"] = test_settings.ESCROW_PROGRAM_ID
    os.environ["JWT_SECRET_KEY"] = test_settings.JWT_SECRET_KEY
    os.environ["JWT_ALGORITHM"] = test_settings.JWT_ALGORITHM
    os.environ["JWT_EXPIRATION_HOURS"] = str(test_settings.JWT_EXPIRATION_HOURS)

    # NOW import and run uvicorn
    import uvicorn

    uvicorn.run(
        "pourtier.main:app",
        host=test_settings.API_HOST,
        port=test_settings.API_PORT,
        log_level="error",
        access_log=False,
    )


class TestUserOnboardingEscrowFlow(LaborantTest):
    """E2E test for complete user onboarding and escrow flow."""

    component_name = "pourtier"
    test_category = "e2e"

    # Class-level shared resources
    db: Database = None
    api_process: multiprocessing.Process = None
    http_client: httpx.AsyncClient = None
    bridge_manager: BridgeManager = None
    transaction_signer: TransactionSigner = None
    alice_address: str = None
    alice_keypair_path: str = None
    bridge_url: str = None
    escrow_account: str = None  # Store for cleanup
    user_id: str = None  # Store for auth
    jwt_token: str = None  # JWT token from account creation

    # ================================================================
    # Async Lifecycle Hooks
    # ================================================================

    async def async_setup(self):
        """Setup test environment (runs once before all tests)."""
        self.reporter.info(
            "Setting up E2E test environment...",
            context="Setup",
        )

        # 1. Setup database
        self.reporter.info("Setting up database...", context="Setup")
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

        TestUserOnboardingEscrowFlow.db = Database(
            database_url=TEST_DATABASE_URL, echo=False
        )
        await TestUserOnboardingEscrowFlow.db.connect()

        # 2. Seed legal documents
        self.reporter.info("📜 Seeding legal documents...", context="Setup")
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async with engine.begin() as conn:
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

        # 3. Initialize GLOBAL container with test database
        container = get_container()
        container._database = TestUserOnboardingEscrowFlow.db

        self.reporter.info(
            "Container initialized with test database",
            context="Setup",
        )

        # 4. Override production settings with test settings
        prod_settings.JWT_SECRET_KEY = test_settings.JWT_SECRET_KEY
        prod_settings.JWT_ALGORITHM = test_settings.JWT_ALGORITHM
        prod_settings.JWT_EXPIRATION_HOURS = test_settings.JWT_EXPIRATION_HOURS
        prod_settings.PASSEUR_BRIDGE_URL = test_settings.PASSEUR_BRIDGE_URL
        prod_settings.SOLANA_RPC_URL = test_settings.SOLANA_RPC_URL
        prod_settings.ESCROW_PROGRAM_ID = test_settings.ESCROW_PROGRAM_ID

        self.reporter.info(
            "Production settings overridden with test config",
            context="Setup",
        )

        # 5. Override FastAPI database dependency
        async def override_get_db_session():
            """Use test database session for FastAPI."""
            async with TestUserOnboardingEscrowFlow.db.session() as session:
                yield session

        app.dependency_overrides[get_db_session] = override_get_db_session

        self.reporter.info(
            "Database dependency overridden",
            context="Setup",
        )

        # 6. Start Passeur Bridge
        self.reporter.info(
            "🌉 Starting Passeur Bridge (devnet)...",
            context="Setup",
        )
        TestUserOnboardingEscrowFlow.bridge_manager = BridgeManager(
            config_file="test.yaml", reporter=self.reporter
        )
        bridge_started = TestUserOnboardingEscrowFlow.bridge_manager.start()

        if not bridge_started:
            raise RuntimeError("Failed to start Passeur Bridge")

        TestUserOnboardingEscrowFlow.bridge_url = (
            TestUserOnboardingEscrowFlow.bridge_manager.bridge_url
        )

        self.reporter.info(
            f"Bridge URL: {TestUserOnboardingEscrowFlow.bridge_url}",
            context="Setup",
        )

        await asyncio.sleep(2)

        # 7. Start Pourtier API server in background process
        self.reporter.info(
            "Starting Pourtier API server...",
            context="Setup",
        )

        TestUserOnboardingEscrowFlow.api_process = multiprocessing.Process(
            target=run_api_server,
            daemon=True,
        )
        TestUserOnboardingEscrowFlow.api_process.start()

        # Wait for API to be ready
        await asyncio.sleep(3)

        # Verify API is up
        max_retries = 10
        for i in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{API_BASE_URL}/health",
                        timeout=2,
                    )
                    if response.status_code == 200:
                        self.reporter.info(
                            f"API server ready: {API_BASE_URL}",
                            context="Setup",
                        )
                        break
            except BaseException:
                if i == max_retries - 1:
                    raise RuntimeError("API server failed to start")
                await asyncio.sleep(1)

        # 8. Create HTTP client
        TestUserOnboardingEscrowFlow.http_client = httpx.AsyncClient(
            base_url=API_BASE_URL,
            timeout=30,
        )

        # 9. Setup Alice wallet
        self.reporter.info("🔑 Loading Alice wallet...", context="Setup")
        TestUserOnboardingEscrowFlow.alice_address = (
            PlatformWallets.get_test_alice_address()
        )
        TestUserOnboardingEscrowFlow.alice_keypair_path = (
            PlatformWallets.get_test_alice_keypair()
        )

        TestUserOnboardingEscrowFlow.transaction_signer = TransactionSigner(
            bridge_url=TestUserOnboardingEscrowFlow.bridge_url,
            keypair_path=TestUserOnboardingEscrowFlow.alice_keypair_path,
            rpc_url=test_settings.SOLANA_RPC_URL,
        )

        self.reporter.info(
            f"Alice wallet: {TestUserOnboardingEscrowFlow.alice_address}",
            context="Setup",
        )

        # 10. CLEANUP: Close any existing escrow before starting test
        self.reporter.info(
            "Cleaning up existing escrow...",
            context="Setup",
        )

        expected_escrow = self._derive_escrow_pda(self.alice_address)
        escrow_exists = await self._check_escrow_exists(expected_escrow)

        if escrow_exists:
            self.reporter.info(
                f"Found existing escrow: {expected_escrow[:8]}...",
                context="Setup",
            )
            try:
                # Try to revoke authorities first
                try:
                    sig, _ = self.transaction_signer.prepare_and_sign_revoke_platform(
                        escrow_account=expected_escrow
                    )
                    await self._wait_for_transaction(sig, max_wait=30)
                    self.reporter.info(
                        "Revoked platform authority",
                        context="Setup",
                    )
                except Exception:
                    # Already revoked or never set
                    self.reporter.info(
                        "No authority to revoke (ok)",
                        context="Setup",
                    )

                # Withdraw all funds
                sig, _ = self.transaction_signer.prepare_and_sign_withdraw(
                    escrow_account=expected_escrow
                )
                await self._wait_for_transaction(sig, max_wait=30)
                self.reporter.info("Withdrew all funds", context="Setup")

                # Close escrow
                sig, _ = self.transaction_signer.prepare_and_sign_close(
                    escrow_account=expected_escrow
                )
                await self._wait_for_transaction(sig, max_wait=30)
                self.reporter.info("Closed escrow", context="Setup")

            except Exception as e:
                self.reporter.warning(
                    f"Cleanup failed: {e} (will try to continue)",
                    context="Setup",
                )
        else:
            self.reporter.info(
                "No existing escrow (clean slate)",
                context="Setup",
            )

        # 11. Create Alice's account with legal acceptance (NEW AUTH FLOW)
        self.reporter.info(
            "👤 Creating Alice's account with legal acceptance...",
            context="Setup",
        )

        # Get legal documents
        response = await self.http_client.get("/api/legal/documents")
        if response.status_code != 200:
            raise RuntimeError("Failed to get legal documents")

        document_ids = [doc["id"] for doc in response.json()]

        # Sign auth message
        signature = sign_message(self.alice_keypair_path, AUTH_MESSAGE)

        # Create account
        response = await self.http_client.post(
            "/api/auth/create-account",
            json={
                "wallet_address": self.alice_address,
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
        TestUserOnboardingEscrowFlow.jwt_token = data["access_token"]
        TestUserOnboardingEscrowFlow.user_id = data["user_id"]

        self.reporter.info(
            f"Alice's account created: {TestUserOnboardingEscrowFlow.user_id}",
            context="Setup",
        )

        self.reporter.info("E2E test environment ready", context="Setup")

    async def async_teardown(self):
        """Cleanup test environment (runs once after all tests)."""
        self.reporter.info("Cleaning up E2E test...", context="Teardown")

        # Close HTTP client
        if TestUserOnboardingEscrowFlow.http_client:
            await TestUserOnboardingEscrowFlow.http_client.aclose()

        # Stop API server
        if TestUserOnboardingEscrowFlow.api_process:
            self.reporter.info(
                "Stopping API server...",
                context="Teardown",
            )
            TestUserOnboardingEscrowFlow.api_process.terminate()
            TestUserOnboardingEscrowFlow.api_process.join(timeout=5)
            if TestUserOnboardingEscrowFlow.api_process.is_alive():
                TestUserOnboardingEscrowFlow.api_process.kill()

        # Clear dependency overrides
        app.dependency_overrides.clear()

        # Stop Passeur Bridge
        if TestUserOnboardingEscrowFlow.bridge_manager:
            self.reporter.info(
                "🌉 Stopping Passeur Bridge...",
                context="Teardown",
            )
            TestUserOnboardingEscrowFlow.bridge_manager.stop()

        # Cleanup database
        if TestUserOnboardingEscrowFlow.db:
            await TestUserOnboardingEscrowFlow.db.disconnect()

        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

        self.reporter.info("Cleanup complete", context="Teardown")

    # ================================================================
    # Helper Methods
    # ================================================================

    def _auth_headers(self) -> dict:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.jwt_token}"}

    async def _get_wallet_balance(self, wallet_address: str) -> Decimal:
        """Get wallet USDC balance from blockchain."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.bridge_url}/wallet/balance",
                    params={"wallet": wallet_address},
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()
                balance = Decimal(str(data.get("balance", "0")))
                self.reporter.info(
                    f"💰 Wallet balance: {balance} USDC",
                    context="Helper",
                )
                return balance
        except Exception as e:
            self.reporter.warning(
                f"Could not fetch balance: {e}, using default 10 USDC",
                context="Helper",
            )
            return Decimal("10.0")

    def _derive_escrow_pda(self, user_address: str) -> str:
        """Derive escrow PDA for user-based escrow."""
        user_pubkey = Pubkey.from_string(user_address)
        program_pubkey = Pubkey.from_string(test_settings.ESCROW_PROGRAM_ID)

        seeds = [b"escrow", bytes(user_pubkey)]
        pda, _ = Pubkey.find_program_address(seeds, program_pubkey)

        return str(pda)

    async def _check_escrow_exists(self, escrow_address: str) -> bool:
        """Check if escrow account exists on-chain."""
        from solana.rpc.async_api import AsyncClient

        client = None
        try:
            client = AsyncClient(test_settings.SOLANA_RPC_URL)
            escrow_pubkey = Pubkey.from_string(escrow_address)
            response = await client.get_account_info(escrow_pubkey)
            return response.value is not None
        except Exception:
            return False
        finally:
            if client:
                await client.close()

    async def _wait_for_transaction(self, signature: str, max_wait: int = 60) -> bool:
        """Wait for transaction confirmation on blockchain (POLLING)."""
        from solana.rpc.async_api import AsyncClient
        from solders.signature import Signature

        client = None
        start_time = asyncio.get_event_loop().time()

        try:
            client = AsyncClient(test_settings.SOLANA_RPC_URL)
            sig = Signature.from_string(signature)

            self.reporter.info(
                f"⏳ Waiting for transaction: {signature[:8]}...",
                context="Helper",
            )

            poll_count = 0
            while (asyncio.get_event_loop().time() - start_time) < max_wait:
                poll_count += 1

                tx = await client.get_transaction(
                    sig,
                    encoding="json",
                    max_supported_transaction_version=0,
                )

                if tx.value is not None:
                    elapsed = int(asyncio.get_event_loop().time() - start_time)
                    self.reporter.info(
                        f"Transaction confirmed in {elapsed}s " f"({poll_count} polls)",
                        context="Helper",
                    )
                    return True

                await asyncio.sleep(2)

            elapsed = int(asyncio.get_event_loop().time() - start_time)
            raise Exception(
                f"Transaction timeout after {elapsed}s ({poll_count} polls)"
            )

        finally:
            if client:
                await client.close()

    # ================================================================
    # E2E Test Flow
    # ================================================================

    async def test_complete_user_onboarding_and_escrow_flow(self):
        """
        Test complete user journey from onboarding to withdrawal.

        This is a REAL E2E test with actual blockchain transactions!
        Uses dynamic amounts based on actual wallet balance.
        """
        self.reporter.info(
            "Starting complete E2E flow...",
            context="Test",
        )

        # ============================================================
        # STEP 0: Check Alice Wallet Balance
        # ============================================================
        self.reporter.info(
            "💳 Step 0: Checking Alice wallet balance...",
            context="Test",
        )

        available_balance = await self._get_wallet_balance(self.alice_address)

        deposit_amount = (available_balance * Decimal("0.8")).quantize(Decimal("0.01"))

        if deposit_amount < Decimal("0.01"):
            self.reporter.warning(
                "Insufficient balance, using minimum 0.01 USDC",
                context="Test",
            )
            deposit_amount = Decimal("0.01")

        self.reporter.info(
            f"Will deposit: {deposit_amount} USDC " f"(available: {available_balance})",
            context="Test",
        )

        # ============================================================
        # STEP 1: Initialize Escrow
        # ============================================================
        self.reporter.info(
            "💰 Step 1: Initializing escrow (REAL blockchain)...",
            context="Test",
        )

        escrow_account, signature, _ = (
            self.transaction_signer.prepare_and_sign_initialize()
        )

        self.reporter.info(f"Initialization tx: {signature}", context="Test")

        await self._wait_for_transaction(signature, max_wait=30)

        response = await self.http_client.post(
            "/api/escrow/initialize",
            json={"tx_signature": signature},
            headers=self._auth_headers(),
        )

        assert response.status_code == 201, f"Init failed: {response.json()}"

        self.reporter.info(
            f"Escrow initialized: {escrow_account}",
            context="Test",
        )

        TestUserOnboardingEscrowFlow.escrow_account = escrow_account

        # ============================================================
        # STEP 2: Deposit Funds
        # ============================================================
        self.reporter.info(
            f"💵 Step 2: Depositing {deposit_amount} USDC...",
            context="Test",
        )

        signature, _ = self.transaction_signer.prepare_and_sign_deposit(
            escrow_account=escrow_account,
            amount=float(deposit_amount),
        )

        self.reporter.info(f"Deposit tx: {signature}", context="Test")

        await self._wait_for_transaction(signature, max_wait=30)

        response = await self.http_client.post(
            "/api/escrow/deposit",
            json={
                "amount": str(deposit_amount),
                "tx_signature": signature,
            },
            headers=self._auth_headers(),
        )

        assert response.status_code == 201, f"Deposit failed: {response.json()}"
        deposit_data = response.json()

        assert Decimal(deposit_data["amount"]) == deposit_amount
        assert deposit_data["status"] == "confirmed"

        self.reporter.info("Deposit confirmed!", context="Test")

        # ============================================================
        # STEP 3: Delegate Platform Authority
        # ============================================================
        self.reporter.info(
            "🔑 Step 3: Delegating platform authority...",
            context="Test",
        )

        platform_authority = PlatformWallets.get_test_authority_address()

        signature, _ = self.transaction_signer.prepare_and_sign_delegate_platform(
            escrow_account=escrow_account,
            authority=platform_authority,
        )

        self.reporter.info(f"Delegate platform tx: {signature}", context="Test")

        await self._wait_for_transaction(signature, max_wait=30)

        self.reporter.info("Platform authority delegated!", context="Test")

        # ============================================================
        # STEP 4: Verify Balance
        # ============================================================
        self.reporter.info(
            "Step 4: Verifying balance...",
            context="Test",
        )

        response = await self.http_client.get(
            "/api/escrow/balance?sync=true",
            headers=self._auth_headers(),
        )

        assert response.status_code == 200
        balance_data = response.json()

        # Balance should match deposit (clean slate!)
        assert Decimal(balance_data["balance"]) == deposit_amount

        self.reporter.info(
            f"Balance verified: {balance_data['balance']} USDC",
            context="Test",
        )

        # ============================================================
        # STEP 5: Revoke Platform Authority
        # ============================================================
        self.reporter.info(
            "🔓 Step 5: Revoking platform authority...",
            context="Test",
        )

        signature, _ = self.transaction_signer.prepare_and_sign_revoke_platform(
            escrow_account=escrow_account
        )

        self.reporter.info(f"Revoke platform tx: {signature}", context="Test")

        await self._wait_for_transaction(signature, max_wait=30)

        self.reporter.info("Platform authority revoked!", context="Test")

        # ============================================================
        # STEP 6: Withdraw Partial Funds
        # ============================================================
        withdraw_amount = (deposit_amount * Decimal("0.5")).quantize(Decimal("0.01"))

        self.reporter.info(
            f"💸 Step 6: Withdrawing {withdraw_amount} USDC...",
            context="Test",
        )

        signature, _ = self.transaction_signer.prepare_and_sign_withdraw(
            escrow_account=escrow_account,
            amount=float(withdraw_amount),
        )

        self.reporter.info(f"Withdraw tx: {signature}", context="Test")

        await self._wait_for_transaction(signature, max_wait=30)

        self.reporter.info("Withdrawal confirmed!", context="Test")

        # ============================================================
        # STEP 7: Close Escrow (Final Cleanup)
        # ============================================================
        self.reporter.info(
            "Step 7: Closing escrow...",
            context="Test",
        )

        # Withdraw remaining funds first
        signature, _ = self.transaction_signer.prepare_and_sign_withdraw(
            escrow_account=escrow_account
        )
        await self._wait_for_transaction(signature, max_wait=30)
        self.reporter.info("Withdrew remaining funds", context="Test")

        # Close escrow
        signature, _ = self.transaction_signer.prepare_and_sign_close(
            escrow_account=escrow_account
        )
        await self._wait_for_transaction(signature, max_wait=30)
        self.reporter.info("Escrow closed", context="Test")

        # ============================================================
        # TEST COMPLETE
        # ============================================================
        self.reporter.info(
            "🎉 E2E TEST COMPLETED SUCCESSFULLY!",
            context="Test",
        )
        self.reporter.info(
            f"Deposited: {deposit_amount} USDC, " f"Withdrew: {withdraw_amount} USDC",
            context="Test",
        )


if __name__ == "__main__":
    TestUserOnboardingEscrowFlow.run_as_main()

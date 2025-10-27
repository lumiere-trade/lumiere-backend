"""
E2E Test: User Onboarding + Escrow Management Flow.

Tests complete user journey with REAL blockchain transactions via Passeur.

Usage:
    laborant pourtier --e2e
"""

import asyncio
import json
from decimal import Decimal

import httpx
from base58 import b58encode
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.signature import Signature
from sqlalchemy import text

from pourtier.config.settings import get_settings
from pourtier.infrastructure.persistence.database import Database
from pourtier.infrastructure.persistence.models import Base
from shared.blockchain.transaction_signer import TransactionSigner
from shared.blockchain.wallets import PlatformWallets
from shared.tests import LaborantTest

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


class TestUserOnboardingEscrowFlow(LaborantTest):
    """E2E test for complete user onboarding and escrow flow."""

    component_name = "pourtier"
    test_category = "e2e"

    db: Database = None
    api_base_url: str = None
    passeur_url: str = None
    http_client: httpx.AsyncClient = None
    transaction_signer: TransactionSigner = None
    alice_address: str = None
    alice_keypair_path: str = None
    escrow_account: str = None
    user_id: str = None
    jwt_token: str = None
    rpc_url: str = None
    program_id: str = None

    async def async_setup(self):
        """Setup test environment."""
        self.reporter.info("Setting up E2E test environment...", context="Setup")

        settings = get_settings()
        TestUserOnboardingEscrowFlow.api_base_url = (
            f"http://pourtier:{settings.API_PORT}"
        )
        TestUserOnboardingEscrowFlow.passeur_url = settings.PASSEUR_URL
        TestUserOnboardingEscrowFlow.rpc_url = settings.SOLANA_RPC_URL
        TestUserOnboardingEscrowFlow.program_id = settings.ESCROW_PROGRAM_ID

        TestUserOnboardingEscrowFlow.db = Database(
            database_url=settings.DATABASE_URL, echo=False
        )
        await TestUserOnboardingEscrowFlow.db.connect()

        await TestUserOnboardingEscrowFlow.db.reset_schema_for_testing(Base.metadata)

        await self._seed_legal_documents()
        await self._wait_for_services()

        TestUserOnboardingEscrowFlow.alice_address = (
            PlatformWallets.get_test_alice_address()
        )
        TestUserOnboardingEscrowFlow.alice_keypair_path = (
            PlatformWallets.get_test_alice_keypair()
        )

        TestUserOnboardingEscrowFlow.transaction_signer = TransactionSigner(
            bridge_url=self.passeur_url,
            keypair_path=self.alice_keypair_path,
            rpc_url=self.rpc_url,
        )

        await self._cleanup_existing_escrow()

        TestUserOnboardingEscrowFlow.http_client = httpx.AsyncClient(
            base_url=self.api_base_url, timeout=30
        )
        await self._create_account()

        self.reporter.info("E2E environment ready", context="Setup")

    async def async_teardown(self):
        """Cleanup test environment."""
        self.reporter.info("Cleaning up E2E test...", context="Teardown")

        if TestUserOnboardingEscrowFlow.http_client:
            await TestUserOnboardingEscrowFlow.http_client.aclose()

        if TestUserOnboardingEscrowFlow.db:
            await TestUserOnboardingEscrowFlow.db.disconnect()

        self.reporter.info("Cleanup complete", context="Teardown")

    async def _seed_legal_documents(self):
        """Seed legal documents for testing."""
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

    async def _wait_for_services(self):
        """Wait for API and Passeur to be ready."""
        for attempt in range(30):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.api_base_url}/health", timeout=2.0
                    )
                    if response.status_code == 200:
                        break
            except Exception:
                if attempt < 29:
                    await asyncio.sleep(1)
                else:
                    raise RuntimeError("API not accessible")

        for attempt in range(30):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.passeur_url}/health", timeout=2.0
                    )
                    if response.status_code == 200:
                        break
            except Exception:
                if attempt < 29:
                    await asyncio.sleep(1)
                else:
                    raise RuntimeError("Passeur not accessible")

    async def _cleanup_existing_escrow(self):
        """
        ROBUST cleanup: Always start with clean slate.

        Handles all edge cases:
        - Account exists with authority delegated
        - Account exists with funds
        - Account exists but empty
        - Account doesn't exist
        - Close transaction fails
        """
        expected_escrow = self._derive_escrow_pda(self.alice_address)
        escrow_exists = await self._check_escrow_exists(expected_escrow)

        if not escrow_exists:
            self.reporter.info("Clean slate: No escrow exists", context="Setup")
            return

        self.reporter.info(
            f"Cleanup needed: Escrow {expected_escrow[:8]}...", context="Setup"
        )

        try:
            sig, _ = self.transaction_signer.prepare_and_sign_revoke_platform(
                escrow_account=expected_escrow
            )
            await self._wait_for_transaction(sig, max_wait=30)
            self.reporter.info("  ✓ Authority revoked", context="Setup")
        except Exception as e:
            error_msg = str(e).lower()
            if "already" in error_msg or "not delegated" in error_msg:
                self.reporter.info("  - No authority to revoke", context="Setup")
            else:
                self.reporter.warning(
                    f"  ⚠ Revoke failed: {str(e)[:60]}", context="Setup"
                )

        try:
            sig, _ = self.transaction_signer.prepare_and_sign_withdraw(
                escrow_account=expected_escrow
            )
            await self._wait_for_transaction(sig, max_wait=30)
            self.reporter.info("  ✓ Funds withdrawn", context="Setup")
        except Exception as e:
            error_msg = str(e).lower()
            if "empty" in error_msg or "zero" in error_msg:
                self.reporter.info("  - No funds to withdraw", context="Setup")
            else:
                self.reporter.warning(
                    f"  ⚠ Withdraw failed: {str(e)[:60]}", context="Setup"
                )

        max_retries = 3
        base_delay = 2

        for attempt in range(max_retries):
            try:
                sig, _ = self.transaction_signer.prepare_and_sign_close(
                    escrow_account=expected_escrow
                )
                await self._wait_for_transaction(sig, max_wait=30)
                self.reporter.info("  ✓ Escrow closed", context="Setup")
                return
            except Exception as e:
                error_msg = str(e).lower()

                if "doesn't exist" in error_msg or "not found" in error_msg:
                    self.reporter.info("  ✓ Account already closed", context="Setup")
                    return

                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)
                    self.reporter.warning(
                        f"  ⚠ Close attempt {attempt + 1} failed, "
                        f"retrying in {delay}s: {str(e)[:60]}",
                        context="Setup",
                    )
                    await asyncio.sleep(delay)
                else:
                    self.reporter.error(
                        f"  ✗ Close failed after {max_retries} attempts: {error_msg}",
                        context="Setup",
                    )

                    still_exists = await self._check_escrow_exists(expected_escrow)

                    if still_exists:
                        raise RuntimeError(
                            f"CRITICAL: Cannot close escrow {expected_escrow[:8]}. "
                            f"Manual intervention required on Solana devnet. "
                            f"Last error: {error_msg[:100]}"
                        )
                    else:
                        self.reporter.info(
                            "  ✓ Account doesn't exist anymore (closed by network)",
                            context="Setup",
                        )
                        return

    async def _create_account(self):
        """Create Alice's account with legal acceptance."""
        response = await self.http_client.get("/api/legal/documents")
        if response.status_code != 200:
            raise RuntimeError("Failed to get legal documents")

        document_ids = [doc["id"] for doc in response.json()]
        signature = sign_message(self.alice_keypair_path, AUTH_MESSAGE)

        response = await self.http_client.post(
            "/api/auth/create-account",
            json={
                "wallet_address": self.alice_address,
                "message": AUTH_MESSAGE,
                "signature": signature,
                "wallet_type": "Phantom",
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

    def _auth_headers(self) -> dict:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.jwt_token}"}

    async def _get_wallet_balance(self, wallet_address: str) -> Decimal:
        """Get wallet USDC balance from blockchain."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.passeur_url}/wallet/balance",
                    params={"wallet": wallet_address},
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()
                return Decimal(str(data.get("balance", "0")))
        except Exception:
            return Decimal("10.0")

    def _derive_escrow_pda(self, user_address: str) -> str:
        """Derive escrow PDA for user-based escrow."""
        user_pubkey = Pubkey.from_string(user_address)
        program_pubkey = Pubkey.from_string(self.program_id)
        seeds = [b"escrow", bytes(user_pubkey)]
        pda, _ = Pubkey.find_program_address(seeds, program_pubkey)
        return str(pda)

    async def _check_escrow_exists(self, escrow_address: str) -> bool:
        """Check if escrow account exists on-chain."""
        client = None
        try:
            client = AsyncClient(self.rpc_url)
            escrow_pubkey = Pubkey.from_string(escrow_address)
            response = await client.get_account_info(escrow_pubkey)
            return response.value is not None
        except Exception:
            return False
        finally:
            if client:
                await client.close()

    async def _wait_for_transaction(self, signature: str, max_wait: int = 60) -> bool:
        """Wait for transaction confirmation on blockchain."""
        client = None
        start_time = asyncio.get_event_loop().time()

        try:
            client = AsyncClient(self.rpc_url)
            sig = Signature.from_string(signature)

            while (asyncio.get_event_loop().time() - start_time) < max_wait:
                tx = await client.get_transaction(
                    sig, encoding="json", max_supported_transaction_version=0
                )

                if tx.value is not None:
                    return True

                await asyncio.sleep(2)

            raise Exception("Transaction timeout")

        finally:
            if client:
                await client.close()

    async def test_complete_user_onboarding_and_escrow_flow(self):
        """Test complete user journey from onboarding to withdrawal."""
        available_balance = await self._get_wallet_balance(self.alice_address)
        deposit_amount = (available_balance * Decimal("0.8")).quantize(Decimal("0.01"))

        if deposit_amount < Decimal("0.01"):
            deposit_amount = Decimal("0.01")

        escrow_account, signature, _ = (
            self.transaction_signer.prepare_and_sign_initialize()
        )

        await self._wait_for_transaction(signature, max_wait=30)

        response = await self.http_client.post(
            "/api/escrow/initialize",
            json={"tx_signature": signature},
            headers=self._auth_headers(),
        )

        assert response.status_code == 201
        TestUserOnboardingEscrowFlow.escrow_account = escrow_account

        signature, _ = self.transaction_signer.prepare_and_sign_deposit(
            escrow_account=escrow_account, amount=float(deposit_amount)
        )

        await self._wait_for_transaction(signature, max_wait=30)

        response = await self.http_client.post(
            "/api/escrow/deposit",
            json={"amount": str(deposit_amount), "tx_signature": signature},
            headers=self._auth_headers(),
        )

        assert response.status_code == 201

        platform_authority = PlatformWallets.get_test_authority_address()

        signature, _ = self.transaction_signer.prepare_and_sign_delegate_platform(
            escrow_account=escrow_account, authority=platform_authority
        )

        await self._wait_for_transaction(signature, max_wait=30)

        response = await self.http_client.get(
            "/api/escrow/balance?sync=true", headers=self._auth_headers()
        )

        assert response.status_code == 200
        balance_data = response.json()
        assert Decimal(balance_data["balance"]) == deposit_amount
        assert balance_data["is_initialized"] is True
        assert balance_data["escrow_account"] == escrow_account
        assert balance_data["synced_from_blockchain"] is True

        signature, _ = self.transaction_signer.prepare_and_sign_revoke_platform(
            escrow_account=escrow_account
        )

        await self._wait_for_transaction(signature, max_wait=30)

        withdraw_amount = (deposit_amount * Decimal("0.5")).quantize(Decimal("0.01"))

        signature, _ = self.transaction_signer.prepare_and_sign_withdraw(
            escrow_account=escrow_account, amount=float(withdraw_amount)
        )

        await self._wait_for_transaction(signature, max_wait=30)

        signature, _ = self.transaction_signer.prepare_and_sign_withdraw(
            escrow_account=escrow_account
        )
        await self._wait_for_transaction(signature, max_wait=30)

        signature, _ = self.transaction_signer.prepare_and_sign_close(
            escrow_account=escrow_account
        )
        await self._wait_for_transaction(signature, max_wait=30)

        self.reporter.info("E2E TEST COMPLETED", context="Test")


if __name__ == "__main__":
    TestUserOnboardingEscrowFlow.run_as_main()

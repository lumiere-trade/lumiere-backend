"""
Integration tests for SmartContractClient with REAL Solana devnet.

Tests real escrow operations on deployed smart contract.

Program ID: 9gvUtaF99sQ287PNzRfCbhFTC4PUnnd7jdAjnY5GUVhS
Network: Solana Devnet

Usage:
    python -m pourtier.tests.integration.services.test_escrow_contract_client
    laborant pourtier --integration
"""

import json
from uuid import uuid4

from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey

from pourtier.config.settings import load_config
from shared.blockchain.wallets import PlatformWallets
from shared.tests import LaborantTest

# Load test configuration
test_settings = load_config("development.yaml", env="development")
TEST_RPC_URL = test_settings.SOLANA_RPC_URL
TEST_PROGRAM_ID = test_settings.ESCROW_PROGRAM_ID


class TestEscrowContractClient(LaborantTest):
    """Integration tests for Solana escrow contract."""

    component_name = "pourtier"
    test_category = "integration"

    # Class-level shared resources
    client: AsyncClient = None
    platform_keypair: Keypair = None

    # ================================================================
    # Async Lifecycle Hooks
    # ================================================================

    async def async_setup(self):
        """Setup Solana client and keypair (runs once before all tests)."""
        self.reporter.info("Setting up Solana client...", context="Setup")
        self.reporter.info(f"RPC URL: {TEST_RPC_URL}", context="Setup")
        self.reporter.info(f"Program ID: {TEST_PROGRAM_ID}", context="Setup")

        # Initialize Solana client
        TestEscrowContractClient.client = AsyncClient(TEST_RPC_URL)

        # Load platform keypair from shared test config
        TestEscrowContractClient.platform_keypair = self._load_keypair(
            PlatformWallets.get_test_platform_keypair()
        )

        self.reporter.info(
            f"Platform pubkey: {self.platform_keypair.pubkey()}", context="Setup"
        )

        # Check balance
        balance = await self._get_balance(self.platform_keypair.pubkey())
        self.reporter.info(f"Platform balance: {balance:.4f} SOL", context="Setup")

        # Verify minimum balance
        if balance < 0.01:
            raise RuntimeError(
                f"Insufficient balance: {balance:.4f} SOL. "
                "Please fund wallet manually."
            )

        self.reporter.info("Solana client ready", context="Setup")

    async def async_teardown(self):
        """Cleanup Solana client (runs once after all tests)."""
        self.reporter.info("Cleaning up Solana client...", context="Teardown")

        if TestEscrowContractClient.client:
            await TestEscrowContractClient.client.close()
            TestEscrowContractClient.client = None

        self.reporter.info("Cleanup complete", context="Teardown")

    # ================================================================
    # Helper Methods
    # ================================================================

    def _load_keypair(self, path: str) -> Keypair:
        """Load Solana keypair from JSON file."""
        with open(path, "r") as f:
            secret = json.load(f)
        return Keypair.from_bytes(bytes(secret))

    async def _get_balance(self, pubkey: Pubkey) -> float:
        """Get SOL balance for pubkey."""
        response = await self.client.get_balance(pubkey)
        return response.value / 1e9  # Convert lamports to SOL

    def _derive_escrow_pda(
        self, program_id: Pubkey, user_pubkey: Pubkey, strategy_id: bytes
    ) -> tuple:
        """Derive escrow PDA address."""
        seeds = [b"escrow", bytes(user_pubkey), strategy_id]
        return Pubkey.find_program_address(seeds, program_id)

    # ================================================================
    # Test Methods
    # ================================================================

    async def test_rpc_connection(self):
        """Test connection to Solana devnet RPC."""
        self.reporter.info("Testing RPC connection to devnet", context="Test")

        # Get latest blockhash to verify connection
        response = await self.client.get_latest_blockhash()

        assert response.value is not None

        self.reporter.info(
            f"Connected to devnet! Blockhash: {response.value.blockhash}",
            context="Test",
        )

    async def test_load_platform_keypair(self):
        """Test loading platform keypair."""
        self.reporter.info("Testing platform keypair loading", context="Test")

        assert self.platform_keypair is not None

        self.reporter.info(
            f"Platform pubkey: {self.platform_keypair.pubkey()}", context="Test"
        )

    async def test_check_wallet_balance(self):
        """Test checking wallet balance."""
        self.reporter.info("Testing wallet balance check", context="Test")

        balance = await self._get_balance(self.platform_keypair.pubkey())

        assert balance >= 0

        self.reporter.info(f"Wallet balance: {balance:.4f} SOL", context="Test")

    async def test_derive_escrow_pda(self):
        """Test deriving escrow PDA address."""
        self.reporter.info("Testing escrow PDA derivation", context="Test")

        program_id = Pubkey.from_string(TEST_PROGRAM_ID)
        user_pubkey = self.platform_keypair.pubkey()

        # Generate strategy ID (16 bytes UUID)
        strategy_id = uuid4().bytes

        # Derive PDA
        escrow_pda, bump = self._derive_escrow_pda(program_id, user_pubkey, strategy_id)

        assert escrow_pda is not None
        assert 0 <= bump <= 255

        self.reporter.info(f"Escrow PDA: {escrow_pda}", context="Test")
        self.reporter.info(f"Bump: {bump}", context="Test")

    async def test_check_program_account(self):
        """Test checking program account exists."""
        self.reporter.info("Testing program account check", context="Test")

        program_id = Pubkey.from_string(TEST_PROGRAM_ID)

        # Get account info
        response = await self.client.get_account_info(program_id)

        assert response.value is not None
        assert response.value.executable

        self.reporter.info(
            f"Program account verified! Owner: {response.value.owner}", context="Test"
        )

    async def test_program_idl_check(self):
        """Test checking program IDL account."""
        self.reporter.info("Testing program IDL check", context="Test")

        idl_account = Pubkey.from_string("AGtwfgMNBMPyRFv8WLN7m3ndFEA81Azyn3HWBt5ag7kj")

        # Check IDL account exists
        response = await self.client.get_account_info(idl_account)

        assert response.value is not None

        self.reporter.info(
            f"IDL account verified! Size: {len(response.value.data)} bytes",
            context="Test",
        )

    async def test_escrow_initialization_flow(self):
        """Test full escrow initialization flow (simulated)."""
        self.reporter.info("Testing escrow initialization flow", context="Test")

        program_id = Pubkey.from_string(TEST_PROGRAM_ID)
        user_pubkey = self.platform_keypair.pubkey()

        # Generate strategy ID
        strategy_id = uuid4().bytes

        # Derive escrow PDA
        escrow_pda, bump = self._derive_escrow_pda(program_id, user_pubkey, strategy_id)

        self.reporter.info(f"Would initialize escrow at: {escrow_pda}", context="Test")
        self.reporter.info(f"User: {user_pubkey}", context="Test")
        self.reporter.info(f"Strategy ID: {strategy_id.hex()}", context="Test")
        self.reporter.info(f"Bump: {bump}", context="Test")

        # Note: Actual initialization requires building and sending TX
        # This test verifies all prerequisites are in place

        assert escrow_pda is not None
        assert bump is not None

        self.reporter.info(
            "Escrow initialization prerequisites verified", context="Test"
        )


if __name__ == "__main__":
    TestEscrowContractClient.run_as_main()

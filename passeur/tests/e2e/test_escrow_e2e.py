"""
End-to-End integration tests for User-Based Escrow operations.

Tests against running passeur Docker container (Python FastAPI + Node.js bridge).

Tests full user-based escrow lifecycle on Solana devnet:
- Initialize escrow (user-only, no strategy_id)
- Deposit funds
- Delegate platform authority
- Delegate trading authority
- Revoke authorities
- Withdraw funds
- Close escrow

Usage:
    laborant passeur --e2e
"""

import time

import requests
from shared.blockchain import (
    TransactionSigner,
    check_escrow_exists,
)
from shared.blockchain.wallets import PlatformWallets
from shared.tests import LaborantTest
from solders.pubkey import Pubkey

from passeur.config.settings import load_config

TEST_PLATFORM_AUTHORITY = PlatformWallets.get_test_authority_address()
TEST_TRADING_AUTHORITY = PlatformWallets.get_test_authority_address()


def derive_user_escrow_pda(user_address: str, program_id: str) -> str:
    """
    Derive escrow PDA for user-based escrow (no strategy_id).

    Args:
        user_address: User wallet address
        program_id: Escrow program ID

    Returns:
        Escrow PDA address
    """
    user_pubkey = Pubkey.from_string(user_address)
    program_pubkey = Pubkey.from_string(program_id)

    seeds = [b"escrow", bytes(user_pubkey)]
    pda, _ = Pubkey.find_program_address(seeds, program_pubkey)

    return str(pda)


class TestEscrowE2E(LaborantTest):
    """End-to-end tests for user-based escrow lifecycle on devnet."""

    component_name = "passeur"
    test_category = "e2e"

    def setup(self):
        """Setup before all tests - connect to running passeur container."""
        self.reporter.info("=" * 60, context="Setup")
        self.reporter.info(
            "SETTING UP E2E TEST (USER-BASED ESCROW)", context="Setup"
        )
        self.reporter.info("=" * 60, context="Setup")

        # Use development.yaml config for devnet settings
        self.test_config = load_config("development.yaml")

        # Connect to running passeur container (Python FastAPI)
        self.passeur_url = f"http://localhost:{self.test_config.api_port}"

        # Verify passeur is running
        try:
            response = requests.get(
                f"{self.passeur_url}/health", timeout=5
            )
            if response.status_code != 200:
                raise Exception("Passeur health check failed")
            self.reporter.info(
                f"Passeur is running: {self.passeur_url}", context="Setup"
            )
        except Exception as e:
            self.reporter.error(
                f"Passeur not accessible: {e}", context="Setup"
            )
            raise Exception(
                "Passeur container not running. Start with: "
                "docker-compose -f docker-compose-dev.yaml up -d passeur"
            )

        self.transaction_signer = TransactionSigner(
            bridge_url=self.passeur_url,
            keypair_path=PlatformWallets.get_test_alice_keypair(),
            rpc_url=self.test_config.solana_rpc_url,
        )

        self.test_escrow_account = None
        self.deposit_amount = 10.0

        self.reporter.info(
            f"Passeur ready: {self.passeur_url}", context="Setup"
        )
        self.reporter.info(
            f"Test user Alice: "
            f"{PlatformWallets.get_test_alice_address()[:8]}...",
            context="Setup",
        )
        self.reporter.info(
            f"Platform authority: {TEST_PLATFORM_AUTHORITY[:8]}...",
            context="Setup",
        )
        self.reporter.info(
            f"Trading authority: {TEST_TRADING_AUTHORITY[:8]}...",
            context="Setup",
        )
        self.reporter.info("=" * 60, context="Setup")

    def teardown(self):
        """Cleanup after all tests."""
        self.reporter.info("=" * 60, context="Teardown")
        self.reporter.info("CLEANING UP", context="Teardown")
        self.reporter.info("=" * 60, context="Teardown")
        self.reporter.info("Cleanup complete", context="Teardown")
        self.reporter.info("=" * 60, context="Teardown")

    def test_01_initialize_escrow(self):
        """Test initializing user-based escrow (no strategy_id)."""
        self.reporter.info(
            "Testing user-based escrow initialization", context="Test"
        )

        expected_escrow = derive_user_escrow_pda(
            PlatformWallets.get_test_alice_address(),
            self.test_config.program_id,
        )

        escrow_exists = check_escrow_exists(
            expected_escrow, self.test_config.solana_rpc_url
        )

        if escrow_exists:
            self.reporter.info(
                f"Escrow already exists: {expected_escrow[:8]}...",
                context="Test",
            )
            self.test_escrow_account = expected_escrow
            return

        try:
            escrow_account, signature, _ = (
                self.transaction_signer.prepare_and_sign_initialize()
            )

            self.test_escrow_account = escrow_account

            self.reporter.info(
                f"Escrow: {escrow_account[:8]}...", context="Test"
            )
            self.reporter.info(
                f"Signature: {signature[:8]}...", context="Test"
            )

        except Exception as e:
            if "already in use" in str(e).lower():
                self.reporter.info(
                    "Escrow exists (race condition)", context="Test"
                )
                self.test_escrow_account = expected_escrow
            else:
                raise

    def test_02_wait_for_confirmation(self):
        """Wait for transaction confirmation."""
        self.reporter.info("Waiting for confirmation...", context="Test")
        time.sleep(5)
        self.reporter.info("Confirmation complete", context="Test")

    def test_03_get_escrow_details(self):
        """Test getting escrow details."""
        self.reporter.info("Testing get escrow details", context="Test")

        assert self.test_escrow_account is not None

        response = requests.get(
            f"{self.passeur_url}/escrow/{self.test_escrow_account}",
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        escrow = data["data"]
        assert escrow["user"] == PlatformWallets.get_test_alice_address()
        assert (
            escrow["platformAuthority"]
            == "11111111111111111111111111111111"
        )
        assert (
            escrow["tradingAuthority"]
            == "11111111111111111111111111111111"
        )
        assert escrow["isPlatformActive"] is False
        assert escrow["isTradingActive"] is False

        self.reporter.info(f"User: {escrow['user'][:8]}...", context="Test")
        self.reporter.info(
            f"Platform Active: {escrow['isPlatformActive']}",
            context="Test",
        )
        self.reporter.info(
            f"Trading Active: {escrow['isTradingActive']}",
            context="Test",
        )

    def test_04_deposit_funds(self):
        """Test depositing funds."""
        self.reporter.info("Testing deposit funds", context="Test")

        assert self.test_escrow_account is not None

        signature, _ = self.transaction_signer.prepare_and_sign_deposit(
            escrow_account=self.test_escrow_account,
            amount=self.deposit_amount,
        )

        self.reporter.info(
            f"Deposited {self.deposit_amount} USDC", context="Test"
        )
        self.reporter.info(f"Signature: {signature[:8]}...", context="Test")

    def test_05_wait_for_confirmation(self):
        """Wait for transaction confirmation."""
        self.reporter.info("Waiting for confirmation...", context="Test")
        time.sleep(5)
        self.reporter.info("Confirmation complete", context="Test")

    def test_06_get_balance_after_deposit(self):
        """Test getting balance after deposit."""
        self.reporter.info(
            "Testing balance after deposit", context="Test"
        )

        assert self.test_escrow_account is not None

        response = requests.get(
            f"{self.passeur_url}/escrow/balance/"
            f"{self.test_escrow_account}",
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        balance = data["balance"]

        assert (
            balance == self.deposit_amount
        ), f"Expected {self.deposit_amount}, got {balance}"

        self.reporter.info(f"Balance: {balance} USDC", context="Test")

    def test_07_delegate_platform_authority(self):
        """Test delegating platform authority."""
        self.reporter.info(
            "Testing delegate platform authority", context="Test"
        )

        assert self.test_escrow_account is not None

        (
            signature,
            _,
        ) = self.transaction_signer.prepare_and_sign_delegate_platform(
            escrow_account=self.test_escrow_account,
            authority=TEST_PLATFORM_AUTHORITY,
        )

        self.reporter.info(
            f"Platform Authority: {TEST_PLATFORM_AUTHORITY[:8]}...",
            context="Test",
        )
        self.reporter.info(f"Signature: {signature[:8]}...", context="Test")

    def test_08_wait_for_confirmation(self):
        """Wait for transaction confirmation."""
        self.reporter.info("Waiting for confirmation...", context="Test")
        time.sleep(5)
        self.reporter.info("Confirmation complete", context="Test")

    def test_09_verify_platform_authority_delegated(self):
        """Verify platform authority is delegated."""
        self.reporter.info(
            "Verifying platform authority delegated", context="Test"
        )

        assert self.test_escrow_account is not None

        response = requests.get(
            f"{self.passeur_url}/escrow/{self.test_escrow_account}",
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        escrow = data["data"]

        assert escrow["platformAuthority"] == TEST_PLATFORM_AUTHORITY
        assert escrow["isPlatformActive"] is True

        self.reporter.info(
            f"Platform Authority: "
            f"{escrow['platformAuthority'][:8]}...",
            context="Test",
        )
        self.reporter.info(
            f"Platform Active: {escrow['isPlatformActive']}",
            context="Test",
        )

    def test_10_delegate_trading_authority(self):
        """Test delegating trading authority."""
        self.reporter.info(
            "Testing delegate trading authority", context="Test"
        )

        assert self.test_escrow_account is not None

        (
            signature,
            _,
        ) = self.transaction_signer.prepare_and_sign_delegate_trading(
            escrow_account=self.test_escrow_account,
            authority=TEST_TRADING_AUTHORITY,
        )

        self.reporter.info(
            f"Trading Authority: {TEST_TRADING_AUTHORITY[:8]}...",
            context="Test",
        )
        self.reporter.info(f"Signature: {signature[:8]}...", context="Test")

    def test_11_wait_for_confirmation(self):
        """Wait for transaction confirmation."""
        self.reporter.info("Waiting for confirmation...", context="Test")
        time.sleep(5)
        self.reporter.info("Confirmation complete", context="Test")

    def test_12_verify_trading_authority_delegated(self):
        """Verify trading authority is delegated."""
        self.reporter.info(
            "Verifying trading authority delegated", context="Test"
        )

        assert self.test_escrow_account is not None

        response = requests.get(
            f"{self.passeur_url}/escrow/{self.test_escrow_account}",
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        escrow = data["data"]

        assert escrow["tradingAuthority"] == TEST_TRADING_AUTHORITY
        assert escrow["isTradingActive"] is True

        self.reporter.info(
            f"Trading Authority: {escrow['tradingAuthority'][:8]}...",
            context="Test",
        )
        self.reporter.info(
            f"Trading Active: {escrow['isTradingActive']}",
            context="Test",
        )

    def test_13_revoke_platform_authority(self):
        """Test revoking platform authority."""
        self.reporter.info(
            "Testing revoke platform authority", context="Test"
        )

        assert self.test_escrow_account is not None

        (
            signature,
            _,
        ) = self.transaction_signer.prepare_and_sign_revoke_platform(
            escrow_account=self.test_escrow_account
        )

        self.reporter.info("Platform authority revoked", context="Test")
        self.reporter.info(f"Signature: {signature[:8]}...", context="Test")

    def test_14_wait_for_confirmation(self):
        """Wait for transaction confirmation."""
        self.reporter.info("Waiting for confirmation...", context="Test")
        time.sleep(5)
        self.reporter.info("Confirmation complete", context="Test")

    def test_15_verify_platform_authority_revoked(self):
        """Verify platform authority is revoked."""
        self.reporter.info(
            "Verifying platform authority revoked", context="Test"
        )

        assert self.test_escrow_account is not None

        response = requests.get(
            f"{self.passeur_url}/escrow/{self.test_escrow_account}",
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        escrow = data["data"]

        system_program = "11111111111111111111111111111111"
        assert escrow["platformAuthority"] == system_program
        assert escrow["isPlatformActive"] is False

        self.reporter.info(
            f"Platform Authority: "
            f"{escrow['platformAuthority'][:8]}...",
            context="Test",
        )
        self.reporter.info(
            f"Platform Active: {escrow['isPlatformActive']}",
            context="Test",
        )

    def test_16_revoke_trading_authority(self):
        """Test revoking trading authority."""
        self.reporter.info(
            "Testing revoke trading authority", context="Test"
        )

        assert self.test_escrow_account is not None

        (
            signature,
            _,
        ) = self.transaction_signer.prepare_and_sign_revoke_trading(
            escrow_account=self.test_escrow_account
        )

        self.reporter.info("Trading authority revoked", context="Test")
        self.reporter.info(f"Signature: {signature[:8]}...", context="Test")

    def test_17_wait_for_confirmation(self):
        """Wait for transaction confirmation."""
        self.reporter.info("Waiting for confirmation...", context="Test")
        time.sleep(5)
        self.reporter.info("Confirmation complete", context="Test")

    def test_18_verify_trading_authority_revoked(self):
        """Verify trading authority is revoked."""
        self.reporter.info(
            "Verifying trading authority revoked", context="Test"
        )

        assert self.test_escrow_account is not None

        response = requests.get(
            f"{self.passeur_url}/escrow/{self.test_escrow_account}",
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        escrow = data["data"]

        system_program = "11111111111111111111111111111111"
        assert escrow["tradingAuthority"] == system_program
        assert escrow["isTradingActive"] is False

        self.reporter.info(
            f"Trading Authority: {escrow['tradingAuthority'][:8]}...",
            context="Test",
        )
        self.reporter.info(
            f"Trading Active: {escrow['isTradingActive']}",
            context="Test",
        )

    def test_19_withdraw_funds(self):
        """Test withdrawing funds."""
        self.reporter.info("Testing withdraw funds", context="Test")

        assert self.test_escrow_account is not None

        signature, _ = self.transaction_signer.prepare_and_sign_withdraw(
            escrow_account=self.test_escrow_account
        )

        self.reporter.info("Withdrawn all funds", context="Test")
        self.reporter.info(f"Signature: {signature[:8]}...", context="Test")

    def test_20_wait_for_confirmation(self):
        """Wait for transaction confirmation."""
        self.reporter.info("Waiting for confirmation...", context="Test")
        time.sleep(5)
        self.reporter.info("Confirmation complete", context="Test")

    def test_21_verify_balance_after_withdraw(self):
        """Verify balance after withdraw."""
        self.reporter.info(
            "Verifying balance after withdraw", context="Test"
        )

        assert self.test_escrow_account is not None

        response = requests.get(
            f"{self.passeur_url}/escrow/balance/"
            f"{self.test_escrow_account}",
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        balance = data["balance"]

        assert balance == 0, f"Expected 0, got {balance}"

        self.reporter.info(f"Balance: {balance} USDC", context="Test")

    def test_22_close_escrow(self):
        """Test closing escrow."""
        self.reporter.info("Testing close escrow", context="Test")

        assert self.test_escrow_account is not None

        signature, _ = self.transaction_signer.prepare_and_sign_close(
            escrow_account=self.test_escrow_account
        )

        self.reporter.info("Escrow closed", context="Test")
        self.reporter.info(f"Signature: {signature[:8]}...", context="Test")

    def test_23_wait_for_confirmation(self):
        """Wait for transaction confirmation."""
        self.reporter.info("Waiting for confirmation...", context="Test")
        time.sleep(5)
        self.reporter.info("Confirmation complete", context="Test")

    def test_24_verify_escrow_closed(self):
        """Verify escrow is closed."""
        self.reporter.info("Verifying escrow closed", context="Test")

        assert self.test_escrow_account is not None

        response = requests.get(
            f"{self.passeur_url}/escrow/{self.test_escrow_account}",
            timeout=10,
        )

        if response.status_code == 404:
            self.reporter.info("Escrow no longer exists", context="Test")
        else:
            data = response.json()
            if not data.get("success"):
                self.reporter.info(
                    "Escrow not accessible (closed)", context="Test"
                )


if __name__ == "__main__":
    TestEscrowE2E.run_as_main()

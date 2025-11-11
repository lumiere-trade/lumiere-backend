"""
Setup script for test accounts.

Creates all necessary token accounts for testing on devnet.
Run once before tests.

Usage:
    python tests/helpers/setup_test_accounts.py
"""

import subprocess
import sys
from pathlib import Path

from shared.blockchain.wallets import PlatformWallets
from shared.reporter.system_reporter import SystemReporter

   PlatformWallets.get_test_alice_address(),
    TEST_AUTHORITY_ADDRESS,
    PlatformWallets.get_test_authority_keypair(),
    PlatformWallets.get_test_alice_keypair(),
)

    # Add shared to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))


    # Initialize reporter
    reporter = SystemReporter(
   name = "setup_test_accounts",
    log_dir = "tests/logs",
    level = 20,
    verbose = 1,
)

    # USDC Devnet token mint
    USDC_DEVNET = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"


    def create_token_account(wallet_address: str, keypair_path: str) -> bool:
    """
    Create Associated Token Account for wallet.

    Args:
        wallet_address: Wallet public key
        keypair_path: Path to wallet keypair (for paying fees)

    Returns:
        True if successful or already exists
    """
    reporter.info(
       f"Creating token account for {wallet_address[:8]}...", context = "Setup"
    )

        try:
        # Check if already exists
    result = subprocess.run(
           [
                "spl-token",
                "accounts",
                "--owner",
                wallet_address,
                USDC_DEVNET,
            ],
            capture_output = True,
            text = True,
            timeout = 10,
        )

            if result.returncode == 0 and "Balance:" in result.stdout:
        reporter.info(
               f"✅ Token account already exists for {wallet_address[:8]}...",
                context = "Setup",
            )
                return True

            # Create account
            result = subprocess.run(
            [
                "spl-token",
                "create-account",
                USDC_DEVNET,
                "--owner",
                wallet_address,
                "--fee-payer",
                keypair_path,
            ],
            capture_output = True,
            text = True,
            timeout = 30,
        )

            if result.returncode == 0:
        reporter.info(
               f"✅ Token account created for {wallet_address[:8]}...",
                context = "Setup",
            )
                return True
            else:
            reporter.error(
               f"❌ Failed to create token account: {result.stderr}",
                context = "Setup",
            )
                return False

            except Exception as e:
            reporter.error(
            f"❌ Error creating token account: {e}",
            context = "Setup",
        )
            return False


        def fund_account_with_sol(address: str, amount: float = 1.0) -> bool:
        """
    Fund account with SOL from devnet faucet.

    Args:
        address: Wallet address to fund
        amount: Amount of SOL to request

    Returns:
        True if successful
    """
        reporter.info(f"Requesting {amount} SOL for {address[:8]}...", context="Setup")

        try:
        result = subprocess.run(
           ["solana", "airdrop", str(amount), address],
            capture_output = True,
            text = True,
            timeout = 30,
        )

            if result.returncode == 0:
        reporter.info(
               f"✅ Airdrop successful for {address[:8]}...",
                context = "Setup",
            )
                return True
            else:
            reporter.warning(
               f"⚠️  Airdrop failed: {result.stderr}",
                context = "Setup",
            )
                return False

            except Exception as e:
            reporter.error(f"❌ Airdrop error: {e}", context="Setup")
            return False


            def setup_test_accounts():
            """Setup all test accounts with SOL and token accounts."""
            reporter.info("=" * 60, context="Setup")
            reporter.info("🔧 SETTING UP TEST ACCOUNTS", context="Setup")
            reporter.info("=" * 60, context="Setup")

            success = True

            # Fund Alice with SOL (for transaction fees)
            reporter.info("\n--- Funding Alice ---", context="Setup")
            if not fund_account_with_sol(PlatformWallets.get_test_alice_address(), 2.0):
            success = False

            # Fund Authority with SOL (for transaction fees)
            reporter.info("\n--- Funding Authority ---", context="Setup")
            if not fund_account_with_sol(TEST_AUTHORITY_ADDRESS, 1.0):
            success = False

            # Create token accounts
            reporter.info("\n--- Creating Token Accounts ---", context="Setup")

            # Alice's token account (pays fees with own keypair)
            if not create_token_account(PlatformWallets.get_test_alice_address(), PlatformWallets.get_test_alice_keypair()):
            success = False

            # Authority's token account (pays fees with own keypair)
            if not create_token_account(TEST_AUTHORITY_ADDRESS, PlatformWallets.get_test_authority_keypair()):
            success = False

            reporter.info("\n" + "=" * 60, context="Setup")
            if success:
            reporter.info("✅ ALL TEST ACCOUNTS READY", context="Setup")
            else:
            reporter.error("❌ SOME ACCOUNTS FAILED TO SETUP", context="Setup")
            reporter.info("=" * 60, context="Setup")

            return success


            def main():
    """Main entry point."""
    success = setup_test_accounts()
    sys.exit(0 if success else 1)


                if __name__ == "__main__":
    main()

"""
Platform wallet configuration for Lumière.

Provides environment-specific platform wallet addresses and test wallets.
"""

import json
import os
from enum import Enum


class Environment(Enum):
    """Application environment."""

    TEST = "test"
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class PlatformWallets:
    """
    Platform wallet configuration.

    Keypairs location: shared/blockchain/keypairs/
    - test/: Test keypairs (in git)
    - production/: Production keypairs (in .gitignore)
    """

    # Keypairs directory (using importlib.resources - proper way!)
    try:
        # Python 3.9+
        from importlib.resources import files

        KEYPAIRS_DIR = str(files("shared.blockchain").joinpath("keypairs"))
    except ImportError:
        # Fallback for older Python
        import pkg_resources

        KEYPAIRS_DIR = pkg_resources.resource_filename("shared.blockchain", "keypairs")

    # ================================================================
    # Environment Detection
    # ================================================================

    @staticmethod
    def get_environment() -> Environment:
        """Get current environment from ENV variable."""
        env = os.getenv("LUMIERE_ENV", "test").lower()
        try:
            return Environment(env)
        except ValueError:
            return Environment.TEST

    # ================================================================
    # Platform Wallets (Environment-aware)
    # ================================================================

    @staticmethod
    def get_platform_wallet() -> str:
        """
        Get platform trading wallet address for current environment.

        Returns:
            Base58-encoded Solana wallet address (44 chars)
        """
        env = PlatformWallets.get_environment()

        if env == Environment.TEST:
            keypair_path = os.path.join(
                PlatformWallets.KEYPAIRS_DIR, "test", "platform.json"
            )
            return PlatformWallets._load_wallet_from_keypair(keypair_path)

        elif env == Environment.PRODUCTION:
            keypair_path = os.path.join(
                PlatformWallets.KEYPAIRS_DIR, "production", "platform.json"
            )
            return PlatformWallets._load_wallet_from_keypair(keypair_path)

        # Development fallback to test
        keypair_path = os.path.join(
            PlatformWallets.KEYPAIRS_DIR, "test", "platform.json"
        )
        return PlatformWallets._load_wallet_from_keypair(keypair_path)

    # ================================================================
    # Test Keypair Paths
    # ================================================================

    @staticmethod
    def get_test_platform_keypair() -> str:
        """Get test platform keypair path."""
        return os.path.join(PlatformWallets.KEYPAIRS_DIR, "test", "platform.json")

    @staticmethod
    def get_test_alice_keypair() -> str:
        """Get test Alice keypair path."""
        return os.path.join(PlatformWallets.KEYPAIRS_DIR, "test", "user_alice.json")

    @staticmethod
    def get_test_bob_keypair() -> str:
        """Get test Bob keypair path."""
        return os.path.join(PlatformWallets.KEYPAIRS_DIR, "test", "user_bob.json")

    @staticmethod
    def get_test_authority_keypair() -> str:
        """Get test authority keypair path."""
        return os.path.join(PlatformWallets.KEYPAIRS_DIR, "test", "authority.json")

    # ================================================================
    # Test Wallet Addresses
    # ================================================================

    @staticmethod
    def get_test_platform_address() -> str:
        """Get test platform wallet address."""
        return PlatformWallets._load_wallet_from_keypair(
            PlatformWallets.get_test_platform_keypair()
        )

    @staticmethod
    def get_test_alice_address() -> str:
        """Get test Alice wallet address."""
        return PlatformWallets._load_wallet_from_keypair(
            PlatformWallets.get_test_alice_keypair()
        )

    @staticmethod
    def get_test_bob_address() -> str:
        """Get test Bob wallet address."""
        return PlatformWallets._load_wallet_from_keypair(
            PlatformWallets.get_test_bob_keypair()
        )

    @staticmethod
    def get_test_authority_address() -> str:
        """Get test authority wallet address."""
        return PlatformWallets._load_wallet_from_keypair(
            PlatformWallets.get_test_authority_keypair()
        )

    # ================================================================
    # Helper Methods
    # ================================================================

    @staticmethod
    def _load_wallet_from_keypair(keypair_path: str) -> str:
        """
        Load wallet address from keypair JSON file.

        Args:
            keypair_path: Path to keypair JSON file

        Returns:
            Base58-encoded wallet address
        """
        try:
            from solders.keypair import Keypair

            with open(keypair_path, "r") as f:
                keypair_data = json.load(f)

            keypair = Keypair.from_bytes(bytes(keypair_data))
            return str(keypair.pubkey())

        except FileNotFoundError:
            # Fallback for missing keypairs
            return "11111111111111111111111111111111111111111111"
        except Exception:
            # Fallback for any errors
            return "11111111111111111111111111111111111111111111"

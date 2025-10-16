"""
Wallet authenticator service interface.
"""

from abc import ABC, abstractmethod


class IWalletAuthenticator(ABC):
    """
    Abstract service interface for Solana wallet authentication.

    Implements signature verification for Web3 authentication:
    - User signs message with wallet private key
    - Backend verifies signature matches wallet address
    """

    @abstractmethod
    async def verify_signature(
        self,
        wallet_address: str,
        message: str,
        signature: str,
    ) -> bool:
        """
        Verify wallet signature.

        Args:
            wallet_address: Wallet address claiming ownership
            message: Original message that was signed
            signature: Signature (base58 encoded)

        Returns:
            True if signature is valid, False otherwise
        """

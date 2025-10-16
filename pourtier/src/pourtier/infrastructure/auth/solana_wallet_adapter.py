"""
Solana wallet authentication adapter.

Implements wallet signature verification using Ed25519.
"""

import base58
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from pourtier.domain.services.i_wallet_authenticator import IWalletAuthenticator


class SolanaWalletAdapter(IWalletAuthenticator):
    """
    Solana wallet authentication using Ed25519 signatures.

    Verifies wallet ownership via signature verification.
    """

    async def verify_signature(
        self,
        wallet_address: str,
        message: str,
        signature: str,
    ) -> bool:
        """
        Verify Solana wallet signature.

        Args:
            wallet_address: Solana wallet address (base58)
            message: Original message that was signed
            signature: Signature (base58 encoded)

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Decode wallet public key from base58
            public_key_bytes = base58.b58decode(wallet_address)
            verify_key = VerifyKey(public_key_bytes)

            # Decode signature from base58
            signature_bytes = base58.b58decode(signature)

            # Encode message as bytes
            message_bytes = message.encode("utf-8")

            # Verify signature using Ed25519
            verify_key.verify(message_bytes, signature_bytes)

            return True

        except (BadSignatureError, ValueError, Exception):
            return False

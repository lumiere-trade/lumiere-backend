"""
Verify Wallet Signature use case.

Verifies wallet signature and checks if user exists WITHOUT creating user.
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from pourtier.domain.exceptions import ValidationError
from pourtier.domain.repositories.i_user_repository import IUserRepository
from pourtier.domain.services.i_wallet_authenticator import (
    IWalletAuthenticator,
)


@dataclass
class VerifyWalletSignatureResult:
    """Result of wallet signature verification."""

    signature_valid: bool
    user_exists: bool
    user_id: Optional[UUID] = None
    wallet_address: Optional[str] = None


class VerifyWalletSignature:
    """
    Verify wallet signature and check user existence.

    Business rules:
    - Signature must be valid for given wallet address
    - Does NOT create user (only checks existence)
    - Returns verification result with user status
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        wallet_authenticator: IWalletAuthenticator,
    ):
        """
        Initialize use case with dependencies.

        Args:
            user_repository: Repository for user persistence
            wallet_authenticator: Service for signature verification
        """
        self.user_repository = user_repository
        self.wallet_authenticator = wallet_authenticator

    async def execute(
        self,
        wallet_address: str,
        message: str,
        signature: str,
    ) -> VerifyWalletSignatureResult:
        """
        Execute wallet signature verification.

        Args:
            wallet_address: Wallet address claiming ownership
            message: Original message that was signed
            signature: Signature (base58 encoded)

        Returns:
            VerifyWalletSignatureResult with verification status

        Raises:
            ValidationError: If signature verification fails
        """
        # 1. Verify signature
        is_valid = await self.wallet_authenticator.verify_signature(
            wallet_address=wallet_address,
            message=message,
            signature=signature,
        )

        if not is_valid:
            raise ValidationError(
                field="signature",
                reason="Invalid signature for wallet address",
            )

        # 2. Check if user exists (DO NOT CREATE)
        user = await self.user_repository.get_by_wallet(wallet_address)

        if user:
            return VerifyWalletSignatureResult(
                signature_valid=True,
                user_exists=True,
                user_id=user.id,
                wallet_address=user.wallet_address,
            )
        else:
            return VerifyWalletSignatureResult(
                signature_valid=True,
                user_exists=False,
                user_id=None,
                wallet_address=wallet_address,
            )

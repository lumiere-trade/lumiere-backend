"""
Authenticate Wallet use case.
"""

from pourtier.domain.entities.user import User
from pourtier.domain.exceptions import ValidationError
from pourtier.domain.repositories.i_user_repository import IUserRepository
from pourtier.domain.services.i_wallet_authenticator import (
    IWalletAuthenticator,
)


class AuthenticateWallet:
    """
    Authenticate user via wallet signature.

    Business rules:
    - Signature must be valid for given wallet address
    - User must exist (or auto-create on first auth)
    - Returns user entity for token generation
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
    ) -> User:
        """
        Execute wallet authentication.

        Args:
            wallet_address: Wallet address claiming ownership
            message: Original message that was signed
            signature: Signature (base58 encoded)

        Returns:
            Authenticated User entity

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

        # 2. Get or create user
        user = await self.user_repository.get_by_wallet(wallet_address)

        if not user:
            # Auto-create user on first successful auth
            from pourtier.application.use_cases.create_user import CreateUser

            create_user = CreateUser(self.user_repository)
            user = await create_user.execute(wallet_address)

        return user

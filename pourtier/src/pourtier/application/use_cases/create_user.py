"""
Create User use case.
"""

from uuid import uuid4

from pourtier.domain.entities.user import User
from pourtier.domain.exceptions import ValidationError
from pourtier.domain.repositories.i_user_repository import IUserRepository


class CreateUser:
    """
    Create new user with wallet address.

    Business rules:
    - Wallet address must be unique
    - Wallet address must be valid Solana address (32-44 chars)
    - User starts with no escrow (must initialize separately)
    """

    def __init__(self, user_repository: IUserRepository):
        """
        Initialize use case with dependencies.

        Args:
            user_repository: Repository for user persistence
        """
        self.user_repository = user_repository

    async def execute(self, wallet_address: str) -> User:
        """
        Execute user creation.

        Args:
            wallet_address: Solana wallet address

        Returns:
            Created User entity

        Raises:
            ValidationError: If wallet already exists or invalid
        """
        # 1. Validate wallet address format
        if not (32 <= len(wallet_address) <= 44):
            raise ValidationError(
                field="wallet_address",
                reason=f"Invalid wallet address length: {len(wallet_address)}",
            )

        # 2. Check if wallet already exists
        existing_user = await self.user_repository.get_by_wallet(wallet_address)
        if existing_user:
            raise ValidationError(
                field="wallet_address",
                reason="Wallet address already registered",
            )

        # 3. Create user entity
        user = User(
            id=uuid4(),
            wallet_address=wallet_address,
        )

        # 4. Save to database
        created_user = await self.user_repository.create(user)

        return created_user

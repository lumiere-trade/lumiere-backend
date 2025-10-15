"""
Get user by wallet address use case.

Retrieves user information by wallet address.
"""

from dataclasses import dataclass

from pourtier.domain.entities.user import User
from pourtier.domain.exceptions import EntityNotFoundError
from pourtier.domain.repositories.i_user_repository import IUserRepository


@dataclass
class GetUserByWalletCommand:
    """Command to get user by wallet address."""

    wallet_address: str


class GetUserByWallet:
    """
    Use case for retrieving user profile by wallet address.

    Returns user entity with profile information.
    """

    def __init__(self, user_repository: IUserRepository):
        """
        Initialize use case.

        Args:
            user_repository: User repository
        """
        self.user_repository = user_repository

    async def execute(self, command: GetUserByWalletCommand) -> User:
        """
        Get user profile by wallet address.

        Args:
            command: Command with wallet_address

        Returns:
            User entity

        Raises:
            EntityNotFoundError: If user not found
        """
        user = await self.user_repository.get_by_wallet(command.wallet_address)

        if not user:
            raise EntityNotFoundError("User", command.wallet_address)

        return user

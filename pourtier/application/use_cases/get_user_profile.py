"""
Get user profile use case.

Retrieves user information.
"""

from dataclasses import dataclass
from uuid import UUID

from pourtier.domain.entities.user import User
from pourtier.domain.repositories.i_user_repository import IUserRepository


@dataclass
class GetUserProfileCommand:
    """Command to get user profile."""

    user_id: UUID


class GetUserProfile:
    """
    Use case for retrieving user profile.

    Returns user entity with profile information.
    """

    def __init__(self, user_repository: IUserRepository):
        """
        Initialize use case.

        Args:
            user_repository: User repository
        """
        self.user_repository = user_repository

    async def execute(self, command: GetUserProfileCommand) -> User:
        """
        Get user profile.

        Args:
            command: Command with user_id

        Returns:
            User entity

        Raises:
            EntityNotFoundError: If user not found
        """
        user = await self.user_repository.get_by_id(command.user_id)

        if not user:
            from pourtier.domain.exceptions import EntityNotFoundError

            raise EntityNotFoundError("User", str(command.user_id))

        return user

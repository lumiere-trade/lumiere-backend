"""
Update user profile use case.

Handles user profile updates.
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from pourtier.domain.entities.user import User
from pourtier.domain.repositories.i_user_repository import IUserRepository


@dataclass
class UpdateUserProfileCommand:
    """Command to update user profile."""

    user_id: UUID
    email: Optional[str] = None
    display_name: Optional[str] = None


class UpdateUserProfile:
    """
    Use case for updating user profile.

    Updates user's email and display name.
    """

    def __init__(self, user_repository: IUserRepository):
        """
        Initialize use case.

        Args:
            user_repository: User repository
        """
        self.user_repository = user_repository

    async def execute(self, command: UpdateUserProfileCommand) -> User:
        """
        Update user profile.

        Args:
            command: Command with updated fields

        Returns:
            Updated user entity

        Raises:
            EntityNotFoundError: If user not found
        """
        # Get existing user
        user = await self.user_repository.get_by_id(command.user_id)

        if not user:
            from pourtier.domain.exceptions import EntityNotFoundError

            raise EntityNotFoundError("User", str(command.user_id))

        # Update profile
        user.update_profile(email=command.email, display_name=command.display_name)

        # Save changes
        updated_user = await self.user_repository.update(user)

        return updated_user

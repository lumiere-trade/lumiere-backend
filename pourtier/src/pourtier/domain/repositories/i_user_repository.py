"""
User repository interface.
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from pourtier.domain.entities.user import User


class IUserRepository(ABC):
    """Interface for user persistence operations."""

    @abstractmethod
    async def create(self, user: User) -> User:
        """
        Create new user.

        Args:
            user: User entity to create

        Returns:
            Created user entity
        """

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User unique identifier

        Returns:
            User entity if found, None otherwise
        """

    @abstractmethod
    async def get_by_wallet(self, wallet_address: str) -> Optional[User]:
        """
        Get user by wallet address.

        Args:
            wallet_address: Wallet address

        Returns:
            User entity if found, None otherwise
        """

    @abstractmethod
    async def update(self, user: User) -> User:
        """
        Update existing user.

        Args:
            user: User entity with updated data

        Returns:
            Updated user entity
        """

    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """
        Delete user by ID.

        Args:
            user_id: User unique identifier

        Returns:
            True if deleted, False if not found
        """

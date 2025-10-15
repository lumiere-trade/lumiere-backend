"""
Subscription repository interface.
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from pourtier.domain.entities.subscription import Subscription


class ISubscriptionRepository(ABC):
    """
    Abstract repository interface for Subscription entity persistence.
    """

    @abstractmethod
    async def create(self, subscription: Subscription) -> Subscription:
        """
        Create a new subscription in the database.

        Args:
            subscription: Subscription entity to persist

        Returns:
            Created subscription with database-generated ID
        """

    @abstractmethod
    async def get_by_id(self, subscription_id: UUID) -> Optional[Subscription]:
        """
        Retrieve subscription by ID.

        Args:
            subscription_id: Subscription unique identifier

        Returns:
            Subscription entity if found, None otherwise
        """

    @abstractmethod
    async def get_active_by_user(self, user_id: UUID) -> Optional[Subscription]:
        """
        Retrieve active subscription for user.

        Args:
            user_id: User unique identifier

        Returns:
            Active subscription if found, None otherwise
        """

    @abstractmethod
    async def update(self, subscription: Subscription) -> Subscription:
        """
        Update existing subscription in database.

        Args:
            subscription: Subscription entity with updated fields

        Returns:
            Updated subscription entity

        Raises:
            ValueError: If subscription not found
        """

    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> list[Subscription]:
        """
        List all subscriptions for user (active and inactive).

        Args:
            user_id: User unique identifier

        Returns:
            List of subscription entities
        """

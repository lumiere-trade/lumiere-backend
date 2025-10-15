"""
User Legal Acceptance repository interface.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from pourtier.domain.entities.user_legal_acceptance import (
    UserLegalAcceptance,
)


class IUserLegalAcceptanceRepository(ABC):
    """Interface for user legal acceptance persistence operations."""

    @abstractmethod
    async def create(self, acceptance: UserLegalAcceptance) -> UserLegalAcceptance:
        """
        Create new user legal acceptance.

        Args:
            acceptance: UserLegalAcceptance entity to create

        Returns:
            Created user legal acceptance entity
        """

    @abstractmethod
    async def get_by_id(self, acceptance_id: UUID) -> Optional[UserLegalAcceptance]:
        """
        Get user legal acceptance by ID.

        Args:
            acceptance_id: Acceptance unique identifier

        Returns:
            UserLegalAcceptance entity if found, None otherwise
        """

    @abstractmethod
    async def get_by_user_and_document(
        self, user_id: UUID, document_id: UUID
    ) -> Optional[UserLegalAcceptance]:
        """
        Get user legal acceptance by user and document.

        Args:
            user_id: User unique identifier
            document_id: Document unique identifier

        Returns:
            UserLegalAcceptance entity if found, None otherwise
        """

    @abstractmethod
    async def get_all_by_user(self, user_id: UUID) -> List[UserLegalAcceptance]:
        """
        Get all legal acceptances for a user.

        Args:
            user_id: User unique identifier

        Returns:
            List of UserLegalAcceptance entities
        """

    @abstractmethod
    async def get_all_by_document(self, document_id: UUID) -> List[UserLegalAcceptance]:
        """
        Get all user acceptances for a document.

        Args:
            document_id: Document unique identifier

        Returns:
            List of UserLegalAcceptance entities
        """

    @abstractmethod
    async def delete(self, acceptance_id: UUID) -> bool:
        """
        Delete user legal acceptance by ID.

        Args:
            acceptance_id: Acceptance unique identifier

        Returns:
            True if deleted, False if not found
        """

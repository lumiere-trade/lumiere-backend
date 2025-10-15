"""
Legal Document repository interface.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from pourtier.domain.entities.legal_document import (
    DocumentType,
    LegalDocument,
)


class ILegalDocumentRepository(ABC):
    """Interface for legal document persistence operations."""

    @abstractmethod
    async def create(self, document: LegalDocument) -> LegalDocument:
        """
        Create new legal document.

        Args:
            document: LegalDocument entity to create

        Returns:
            Created legal document entity
        """

    @abstractmethod
    async def get_by_id(self, document_id: UUID) -> Optional[LegalDocument]:
        """
        Get legal document by ID.

        Args:
            document_id: Document unique identifier

        Returns:
            LegalDocument entity if found, None otherwise
        """

    @abstractmethod
    async def get_active_by_type(
        self, document_type: DocumentType
    ) -> Optional[LegalDocument]:
        """
        Get active legal document by type.

        Args:
            document_type: Type of document (TOS, Privacy Policy)

        Returns:
            Active LegalDocument entity if found, None otherwise
        """

    @abstractmethod
    async def get_all_active(self) -> List[LegalDocument]:
        """
        Get all active legal documents.

        Returns:
            List of active LegalDocument entities
        """

    @abstractmethod
    async def update(self, document: LegalDocument) -> LegalDocument:
        """
        Update existing legal document.

        Args:
            document: LegalDocument entity with updated data

        Returns:
            Updated legal document entity
        """

    @abstractmethod
    async def delete(self, document_id: UUID) -> bool:
        """
        Delete legal document by ID.

        Args:
            document_id: Document unique identifier

        Returns:
            True if deleted, False if not found
        """

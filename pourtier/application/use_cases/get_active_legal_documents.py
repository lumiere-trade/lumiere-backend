"""
Get Active Legal Documents use case.

Retrieves all active legal documents that users must accept.
"""

from typing import List

from pourtier.domain.entities.legal_document import LegalDocument
from pourtier.domain.repositories.i_legal_document_repository import (
    ILegalDocumentRepository,
)


class GetActiveLegalDocuments:
    """
    Get all active legal documents.

    Returns documents that are currently active and must be
    accepted by users.
    """

    def __init__(
        self,
        legal_document_repository: ILegalDocumentRepository,
    ):
        """
        Initialize use case.

        Args:
            legal_document_repository: Legal document repository
        """
        self.legal_document_repository = legal_document_repository

    async def execute(self) -> List[LegalDocument]:
        """
        Get all active legal documents.

        Returns:
            List of active LegalDocument entities

        Raises:
            Exception: If database operation fails
        """
        # Get all active documents
        documents = await self.legal_document_repository.get_all_active()

        return documents

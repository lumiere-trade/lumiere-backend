"""
Check User Legal Compliance use case.

Verifies if user has accepted all required legal documents.
"""

from typing import List
from uuid import UUID

from pourtier.domain.entities.legal_document import LegalDocument
from pourtier.domain.exceptions.base import EntityNotFoundError
from pourtier.domain.repositories.i_legal_document_repository import (
    ILegalDocumentRepository,
)
from pourtier.domain.repositories.i_user_legal_acceptance_repository import (
    IUserLegalAcceptanceRepository,
)
from pourtier.domain.repositories.i_user_repository import IUserRepository


class CheckUserLegalCompliance:
    """
    Check if user has accepted all required legal documents.

    Returns compliance status and list of pending documents.
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        legal_document_repository: ILegalDocumentRepository,
        user_legal_acceptance_repository: IUserLegalAcceptanceRepository,
    ):
        """
        Initialize use case.

        Args:
            user_repository: User repository
            legal_document_repository: Legal document repository
            user_legal_acceptance_repository: Acceptance repository
        """
        self.user_repository = user_repository
        self.legal_document_repository = legal_document_repository
        self.user_legal_acceptance_repository = user_legal_acceptance_repository

    async def execute(self, user_id: UUID) -> tuple[bool, List[LegalDocument]]:
        """
        Check if user has accepted all required documents.

        Args:
            user_id: User unique identifier

        Returns:
            Tuple of (is_compliant, pending_documents):
            - is_compliant: True if all documents accepted
            - pending_documents: List of documents not yet accepted

        Raises:
            EntityNotFoundError: If user not found
        """
        # Verify user exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError(
                entity_type="User",
                entity_id=str(user_id),
            )

        # Get all active documents
        active_documents = await self.legal_document_repository.get_all_active()

        # Get user's acceptances
        user_acceptances = await self.user_legal_acceptance_repository.get_all_by_user(
            user_id
        )

        # Create set of accepted document IDs
        accepted_ids = {acceptance.document_id for acceptance in user_acceptances}

        # Find pending documents
        pending_documents = [
            doc for doc in active_documents if doc.id not in accepted_ids
        ]

        # User is compliant if no pending documents
        is_compliant = len(pending_documents) == 0

        return is_compliant, pending_documents

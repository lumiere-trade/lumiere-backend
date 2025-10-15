"""
Accept Legal Documents use case.

Records user acceptance of legal documents with audit trail.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pourtier.domain.entities.user_legal_acceptance import (
    AcceptanceMethod,
    UserLegalAcceptance,
)
from pourtier.domain.exceptions.base import EntityNotFoundError
from pourtier.domain.repositories.i_legal_document_repository import (
    ILegalDocumentRepository,
)
from pourtier.domain.repositories.i_user_legal_acceptance_repository import (
    IUserLegalAcceptanceRepository,
)
from pourtier.domain.repositories.i_user_repository import IUserRepository


class AcceptLegalDocuments:
    """
    Accept legal documents use case.

    Records user acceptance with IP address and user agent
    for audit trail.
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

    async def execute(
        self,
        user_id: UUID,
        document_ids: List[UUID],
        acceptance_method: AcceptanceMethod = (AcceptanceMethod.WEB_CHECKBOX),
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> List[UserLegalAcceptance]:
        """
        Record user acceptance of legal documents.

        Args:
            user_id: User unique identifier
            document_ids: List of document IDs to accept
            acceptance_method: How user accepted (default: web_checkbox)
            ip_address: User IP address (for audit)
            user_agent: User agent string (for audit)

        Returns:
            List of created UserLegalAcceptance entities

        Raises:
            EntityNotFoundError: If user or document not found
            ValueError: If document already accepted
        """
        # Verify user exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError(
                entity_type="User",
                entity_id=str(user_id),
            )

        acceptances = []

        for document_id in document_ids:
            # Verify document exists
            document = await self.legal_document_repository.get_by_id(document_id)
            if not document:
                raise EntityNotFoundError(
                    entity_type="LegalDocument",
                    entity_id=str(document_id),
                )

            # Check if already accepted
            existing = await self.user_legal_acceptance_repository.get_by_user_and_document(  # noqa: E501
                user_id=user_id,
                document_id=document_id,
            )

            if existing:
                # Already accepted, skip
                acceptances.append(existing)
                continue

            # Create acceptance record
            acceptance = UserLegalAcceptance(
                id=uuid4(),
                user_id=user_id,
                document_id=document_id,
                accepted_at=datetime.now(),
                acceptance_method=acceptance_method,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=datetime.now(),
            )

            # Save to database
            created = await self.user_legal_acceptance_repository.create(acceptance)
            acceptances.append(created)

        return acceptances

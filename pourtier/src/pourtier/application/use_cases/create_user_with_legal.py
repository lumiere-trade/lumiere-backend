"""
Create User With Legal Acceptance use case.

Creates new user and records legal document acceptances.
"""

from typing import List, Optional
from uuid import UUID

from pourtier.domain.entities.user import User
from pourtier.domain.entities.user_legal_acceptance import (
    AcceptanceMethod,
    UserLegalAcceptance,
)
from pourtier.domain.exceptions import ValidationError
from pourtier.domain.repositories.i_legal_document_repository import (
    ILegalDocumentRepository,
)
from pourtier.domain.repositories.i_user_legal_acceptance_repository import (
    IUserLegalAcceptanceRepository,
)
from pourtier.domain.repositories.i_user_repository import IUserRepository


class CreateUserWithLegal:
    """
    Create new user and record legal document acceptances.

    Business rules:
    - User must not already exist
    - Must accept all required active legal documents
    - Records audit trail (IP, user agent, timestamp)
    - Transaction: User + Acceptances created together
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        legal_document_repository: ILegalDocumentRepository,
        user_legal_acceptance_repository: IUserLegalAcceptanceRepository,
    ):
        """
        Initialize use case with dependencies.

        Args:
            user_repository: Repository for user persistence
            legal_document_repository: Repository for legal documents
            user_legal_acceptance_repository: Repository for acceptances
        """
        self.user_repository = user_repository
        self.legal_document_repository = legal_document_repository
        self.user_legal_acceptance_repository = user_legal_acceptance_repository

    async def execute(
        self,
        wallet_address: str,
        accepted_document_ids: List[UUID],
        acceptance_method: AcceptanceMethod = AcceptanceMethod.WEB_CHECKBOX,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> User:
        """
        Execute user creation with legal acceptance.

        Args:
            wallet_address: Wallet address for new user
            accepted_document_ids: List of document IDs being accepted
            acceptance_method: How user accepted (default: WEB_CHECKBOX)
            ip_address: User's IP address (for audit)
            user_agent: User's user agent (for audit)

        Returns:
            Created User entity

        Raises:
            ValidationError: If user exists or documents invalid
        """
        # 1. Check user doesn't already exist
        existing_user = await self.user_repository.get_by_wallet(wallet_address)
        if existing_user:
            raise ValidationError(
                field="wallet_address",
                reason=f"User with wallet {wallet_address} already exists",
            )

        # 2. Get all active legal documents
        active_docs = await self.legal_document_repository.get_all_active()

        if not active_docs:
            raise ValidationError(
                field="legal_documents",
                reason="No active legal documents found",
            )

        # 3. Verify all active documents are accepted
        active_doc_ids = {doc.id for doc in active_docs}
        accepted_ids = set(accepted_document_ids)

        missing_docs = active_doc_ids - accepted_ids
        if missing_docs:
            raise ValidationError(
                field="accepted_documents",
                reason=(
                    f"Must accept all active documents. " f"Missing: {missing_docs}"
                ),
            )

        # 4. Create user
        user = User(wallet_address=wallet_address)
        created_user = await self.user_repository.create(user)

        # 5. Record legal acceptances
        for doc_id in accepted_document_ids:
            acceptance = UserLegalAcceptance(
                user_id=created_user.id,
                document_id=doc_id,
                acceptance_method=acceptance_method,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await self.user_legal_acceptance_repository.create(acceptance)

        return created_user

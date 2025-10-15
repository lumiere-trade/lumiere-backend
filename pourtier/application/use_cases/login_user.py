"""
Login user use case.

Authenticates existing user and checks legal compliance.
"""

from dataclasses import dataclass
from typing import List

from pourtier.domain.entities.legal_document import LegalDocument
from pourtier.domain.entities.user import User
from pourtier.domain.exceptions import EntityNotFoundError, ValidationError
from pourtier.domain.repositories.i_legal_document_repository import (
    ILegalDocumentRepository,
)
from pourtier.domain.repositories.i_user_legal_acceptance_repository import (
    IUserLegalAcceptanceRepository,
)
from pourtier.domain.repositories.i_user_repository import IUserRepository
from pourtier.domain.services.i_wallet_authenticator import (
    IWalletAuthenticator,
)


@dataclass
class LoginUserResult:
    """Result from login user use case."""

    user: User
    is_compliant: bool
    pending_documents: List[LegalDocument]


class LoginUser:
    """
    Login existing user use case.

    Flow:
    1. Verify wallet signature
    2. Get user from database
    3. Check legal compliance
    4. Return user + compliance status
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        legal_document_repository: ILegalDocumentRepository,
        user_legal_acceptance_repository: IUserLegalAcceptanceRepository,
        wallet_authenticator: IWalletAuthenticator,
    ):
        """Initialize use case with dependencies."""
        self._user_repository = user_repository
        self._legal_document_repository = legal_document_repository
        self._user_legal_acceptance_repository = user_legal_acceptance_repository
        self._wallet_authenticator = wallet_authenticator

    async def execute(
        self,
        wallet_address: str,
        message: str,
        signature: str,
    ) -> LoginUserResult:
        """
        Login existing user.

        Args:
            wallet_address: User's wallet address
            message: Message that was signed
            signature: Signature to verify

        Returns:
            LoginUserResult with user and compliance status

        Raises:
            EntityNotFoundError: User not found
            ValidationError: Invalid signature
        """
        # 1. Verify signature
        is_valid = await self._wallet_authenticator.verify_signature(
            wallet_address=wallet_address,
            message=message,
            signature=signature,
        )

        if not is_valid:
            raise ValidationError(
                field="signature",
                reason=f"Invalid signature for wallet address: {wallet_address}",
            )

        # 2. Get user from database
        user = await self._user_repository.get_by_wallet(wallet_address)

        if not user:
            raise EntityNotFoundError(
                entity_type="User",
                entity_id=wallet_address,
            )

        # 3. Get all active legal documents
        active_documents = await self._legal_document_repository.get_all_active()

        # 4. Get user's acceptances
        acceptances = await self._user_legal_acceptance_repository.get_all_by_user(
            user.id
        )

        # 5. Check which documents are pending
        accepted_doc_ids = {acc.document_id for acc in acceptances}
        pending_documents = [
            doc for doc in active_documents if doc.id not in accepted_doc_ids
        ]

        is_compliant = len(pending_documents) == 0

        return LoginUserResult(
            user=user,
            is_compliant=is_compliant,
            pending_documents=pending_documents,
        )

"""Domain repository interfaces."""

from pourtier.domain.repositories.i_escrow_transaction_repository import (
    IEscrowTransactionRepository,
)
from pourtier.domain.repositories.i_legal_document_repository import (
    ILegalDocumentRepository,
)
from pourtier.domain.repositories.i_subscription_repository import (
    ISubscriptionRepository,
)
from pourtier.domain.repositories.i_user_legal_acceptance_repository import (
    IUserLegalAcceptanceRepository,
)
from pourtier.domain.repositories.i_user_repository import IUserRepository

__all__ = [
    "IUserRepository",
    "ISubscriptionRepository",
    "IEscrowTransactionRepository",
    "ILegalDocumentRepository",
    "IUserLegalAcceptanceRepository",
]

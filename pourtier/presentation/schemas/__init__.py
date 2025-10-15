"""API schemas."""

from pourtier.presentation.schemas.auth_schemas import (
    CreateAccountRequest,
    CreateAccountResponse,
    LoginRequest,
    LoginResponse,
    PendingDocumentInfo,
    VerifyWalletRequest,
    VerifyWalletResponse,
)
from pourtier.presentation.schemas.escrow_schemas import (
    BalanceResponse,
    DepositRequest,
    EscrowAccountResponse,
    InitializeEscrowRequest,
    TransactionListResponse,
    TransactionResponse,
    WithdrawRequest,
)
from pourtier.presentation.schemas.legal_schemas import (
    AcceptLegalDocumentsRequest,
    AcceptLegalDocumentsResponse,
    LegalComplianceResponse,
    LegalDocumentResponse,
    UserLegalAcceptanceResponse,
)
from pourtier.presentation.schemas.subscription_schemas import (
    CreateSubscriptionRequest,
    SubscriptionResponse,
)
from pourtier.presentation.schemas.user_schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
)

__all__ = [
    # Auth
    "VerifyWalletRequest",
    "VerifyWalletResponse",
    "CreateAccountRequest",
    "CreateAccountResponse",
    "LoginRequest",
    "LoginResponse",
    "PendingDocumentInfo",
    # User
    "CreateUserRequest",
    "UpdateUserRequest",
    "UserResponse",
    # Subscription
    "CreateSubscriptionRequest",
    "SubscriptionResponse",
    # Escrow
    "InitializeEscrowRequest",
    "DepositRequest",
    "WithdrawRequest",
    "BalanceResponse",
    "EscrowAccountResponse",
    "TransactionResponse",
    "TransactionListResponse",
    # Legal
    "LegalDocumentResponse",
    "AcceptLegalDocumentsRequest",
    "AcceptLegalDocumentsResponse",
    "UserLegalAcceptanceResponse",
    "LegalComplianceResponse",
]

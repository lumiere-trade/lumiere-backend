"""
Passeur API request/response schemas.

This module exports Pydantic schemas for all Passeur endpoints,
mirroring the Node.js bridge API contract 1:1.
"""

from passeur.presentation.schemas.escrow import (
    EscrowBalanceResponse,
    EscrowDetailsResponse,
    PrepareCloseRequest,
    PrepareCloseResponse,
    PrepareDelegatePlatformRequest,
    PrepareDelegateResponse,
    PrepareDelegateTradingRequest,
    PrepareDepositRequest,
    PrepareDepositResponse,
    PrepareInitializeRequest,
    PrepareInitializeResponse,
    PrepareRevokeRequest,
    PrepareRevokeResponse,
    PrepareWithdrawRequest,
    PrepareWithdrawResponse,
)
from passeur.presentation.schemas.transaction import (
    SubmitTransactionRequest,
    SubmitTransactionResponse,
    TransactionStatusResponse,
)
from passeur.presentation.schemas.wallet import (
    WalletBalanceResponse,
)

__all__ = [
    # Escrow operations
    "PrepareInitializeRequest",
    "PrepareInitializeResponse",
    "PrepareDelegatePlatformRequest",
    "PrepareDelegateTradingRequest",
    "PrepareDelegateResponse",
    "PrepareRevokeRequest",
    "PrepareRevokeResponse",
    "PrepareDepositRequest",
    "PrepareDepositResponse",
    "PrepareWithdrawRequest",
    "PrepareWithdrawResponse",
    "PrepareCloseRequest",
    "PrepareCloseResponse",
    "EscrowDetailsResponse",
    "EscrowBalanceResponse",
    # Transaction operations
    "SubmitTransactionRequest",
    "SubmitTransactionResponse",
    "TransactionStatusResponse",
    # Wallet operations
    "WalletBalanceResponse",
]

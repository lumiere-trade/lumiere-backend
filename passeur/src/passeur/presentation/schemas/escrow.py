"""
Escrow operation schemas.

Mirrors Node.js bridge API contract for all escrow-related endpoints.
"""

from typing import Optional

from pydantic import BaseModel, Field


class PrepareInitializeRequest(BaseModel):
    """
    Request to prepare initialize escrow transaction.

    Corresponds to: POST /escrow/prepare-initialize
    """

    userWallet: str = Field(
        ...,
        description="User wallet public key (base58)",
        min_length=32,
        max_length=44,
    )
    maxBalance: Optional[int] = Field(
        None,
        description="Maximum balance allowed in escrow (lamports)",
        ge=0,
    )


class PrepareInitializeResponse(BaseModel):
    """
    Response from prepare initialize escrow transaction.

    Contains unsigned transaction ready for user signing.
    """

    success: bool = Field(..., description="Operation success status")
    transaction: str = Field(..., description="Base64 encoded transaction")
    escrowAccount: str = Field(..., description="Escrow PDA address")
    bump: int = Field(..., description="PDA bump seed", ge=0, le=255)
    message: str = Field(..., description="Human-readable message")


class PrepareDelegatePlatformRequest(BaseModel):
    """
    Request to delegate platform authority.

    Allows platform to withdraw subscription fees from escrow.
    Corresponds to: POST /escrow/prepare-delegate-platform
    """

    userWallet: str = Field(..., description="User wallet public key")
    escrowAccount: str = Field(..., description="Escrow account address")
    authority: str = Field(..., description="Platform authority public key")


class PrepareDelegateTradingRequest(BaseModel):
    """
    Request to delegate trading authority.

    Allows Chevalier to execute trades using escrow funds.
    Corresponds to: POST /escrow/prepare-delegate-trading
    """

    userWallet: str = Field(..., description="User wallet public key")
    escrowAccount: str = Field(..., description="Escrow account address")
    authority: str = Field(..., description="Trading authority public key")


class PrepareDelegateResponse(BaseModel):
    """
    Response from delegate authority operations.

    Used by both delegate-platform and delegate-trading endpoints.
    """

    success: bool = Field(..., description="Operation success status")
    transaction: str = Field(..., description="Base64 encoded transaction")
    message: str = Field(..., description="Human-readable message")


class PrepareRevokeRequest(BaseModel):
    """
    Request to revoke authority (platform or trading).

    Corresponds to:
    - POST /escrow/prepare-revoke-platform
    - POST /escrow/prepare-revoke-trading
    """

    userWallet: str = Field(..., description="User wallet public key")
    escrowAccount: str = Field(..., description="Escrow account address")


class PrepareRevokeResponse(BaseModel):
    """
    Response from revoke authority operations.
    """

    success: bool = Field(..., description="Operation success status")
    transaction: str = Field(..., description="Base64 encoded transaction")
    message: str = Field(..., description="Human-readable message")


class PrepareDepositRequest(BaseModel):
    """
    Request to prepare deposit transaction.

    User deposits USDC from wallet into escrow.
    Corresponds to: POST /escrow/prepare-deposit
    """

    userWallet: str = Field(..., description="User wallet public key")
    escrowAccount: str = Field(..., description="Escrow account address")
    amount: float = Field(
        ...,
        description="Amount to deposit (USDC, not lamports)",
        gt=0,
    )


class PrepareDepositResponse(BaseModel):
    """
    Response from prepare deposit transaction.
    """

    success: bool = Field(..., description="Operation success status")
    transaction: str = Field(..., description="Base64 encoded transaction")
    amount: str = Field(..., description="Deposit amount in lamports")
    message: str = Field(..., description="Human-readable message")


class PrepareWithdrawRequest(BaseModel):
    """
    Request to prepare withdraw transaction.

    User withdraws funds from escrow back to wallet.
    Corresponds to: POST /escrow/prepare-withdraw
    """

    userWallet: str = Field(..., description="User wallet public key")
    escrowAccount: str = Field(..., description="Escrow account address")
    amount: Optional[float] = Field(
        None,
        description="Amount to withdraw (USDC). If None, withdraws all",
        gt=0,
    )


class PrepareWithdrawResponse(BaseModel):
    """
    Response from prepare withdraw transaction.
    """

    success: bool = Field(..., description="Operation success status")
    transaction: str = Field(..., description="Base64 encoded transaction")
    amount: str = Field(..., description="Withdraw amount in lamports")
    message: str = Field(..., description="Human-readable message")


class PrepareCloseRequest(BaseModel):
    """
    Request to prepare close escrow transaction.

    Closes escrow account and returns rent to user.
    Corresponds to: POST /escrow/prepare-close
    """

    userWallet: str = Field(..., description="User wallet public key")
    escrowAccount: str = Field(..., description="Escrow account address")


class PrepareCloseResponse(BaseModel):
    """
    Response from prepare close escrow transaction.
    """

    success: bool = Field(..., description="Operation success status")
    transaction: str = Field(..., description="Base64 encoded transaction")
    message: str = Field(..., description="Human-readable message")


class EscrowDetailsResponse(BaseModel):
    """
    Response from GET /escrow/{address}.

    Returns complete escrow account state.
    """

    success: bool = Field(..., description="Query success status")
    data: dict = Field(
        ...,
        description="Escrow account data",
        examples=[
            {
                "address": "...",
                "user": "...",
                "platformAuthority": "...",
                "tradingAuthority": "...",
                "tokenMint": "...",
                "bump": 255,
                "isPlatformActive": True,
                "isTradingActive": False,
                "isPaused": False,
                "createdAt": "1234567890",
                "platformActivatedAt": "1234567890",
                "tradingActivatedAt": "0",
                "lastPausedAt": "0",
                "actionNonce": "0",
                "totalDeposited": "1000000",
                "totalWithdrawn": "0",
                "totalFeesPaid": "0",
                "totalTraded": "0",
                "maxBalance": "10000000",
                "maxLifetime": "0",
            }
        ],
    )


class EscrowBalanceResponse(BaseModel):
    """
    Response from GET /escrow/balance/{account}.

    Returns token balance in escrow.
    """

    success: bool = Field(..., description="Query success status")
    balance: float = Field(..., description="Balance in USDC (human-readable)")
    balanceLamports: str = Field(..., description="Balance in lamports (raw)")
    decimals: int = Field(..., description="Token decimals")
    tokenMint: str = Field(..., description="Token mint address")

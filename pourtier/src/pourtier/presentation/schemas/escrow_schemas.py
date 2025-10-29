"""
API schemas for escrow operations.

Request and response models for escrow endpoints.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

# ================================================================
# Request Schemas
# ================================================================


class InitializeEscrowRequest(BaseModel):
    """Request schema for initializing escrow."""

    tx_signature: str = Field(
        ...,
        description="Blockchain transaction signature (user-signed)",
        min_length=64,
        max_length=128,
    )
    token_mint: str = Field(
        default="USDC",
        description="Token mint address",
        max_length=44,
    )


class PrepareDepositRequest(BaseModel):
    """Request schema for preparing deposit transaction."""

    amount: Decimal = Field(
        ...,
        description="Deposit amount in tokens",
        gt=0,
        decimal_places=8,
    )


class DepositRequest(BaseModel):
    """Request schema for depositing to escrow."""

    amount: Decimal = Field(
        ...,
        description="Deposit amount in tokens",
        gt=0,
        decimal_places=8,
    )
    tx_signature: str = Field(
        ...,
        description="Blockchain transaction signature (user-signed)",
        min_length=64,
        max_length=128,
    )


class WithdrawRequest(BaseModel):
    """Request schema for withdrawing from escrow."""

    amount: Decimal = Field(
        ...,
        description="Withdrawal amount in tokens",
        gt=0,
        decimal_places=8,
    )
    tx_signature: str = Field(
        ...,
        description="Blockchain transaction signature (user-signed)",
        min_length=64,
        max_length=128,
    )


# ================================================================
# Response Schemas
# ================================================================


class PrepareInitializeResponse(BaseModel):
    """Response schema for prepare initialize escrow operation."""

    transaction: str = Field(
        ...,
        description="Unsigned transaction (base64) for user to sign",
    )
    token_mint: str = Field(
        ...,
        description="Token mint address (USDC)",
    )


class PrepareDepositResponse(BaseModel):
    """Response schema for prepare deposit operation."""

    transaction: str = Field(
        ...,
        description="Unsigned transaction (base64) for user to sign",
    )
    escrow_account: str = Field(
        ...,
        description="Escrow PDA address",
    )
    amount: Decimal = Field(
        ...,
        description="Deposit amount",
    )

    class Config:
        """Pydantic config."""

        json_encoders = {
            Decimal: str,
        }


class EscrowAccountResponse(BaseModel):
    """Response schema for escrow account information."""

    escrow_account: str = Field(
        ...,
        description="Escrow PDA address",
    )
    balance: Decimal = Field(
        ...,
        description="Current escrow balance",
    )
    token_mint: str = Field(
        ...,
        description="Token mint address",
    )

    class Config:
        """Pydantic config."""

        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }


class TransactionResponse(BaseModel):
    """Response schema for escrow transaction."""

    id: UUID = Field(..., description="Transaction unique identifier")
    user_id: UUID = Field(..., description="User unique identifier")
    tx_signature: str = Field(..., description="Blockchain tx signature")
    transaction_type: str = Field(..., description="Transaction type")
    amount: Decimal = Field(..., description="Transaction amount")
    token_mint: str = Field(..., description="Token mint address")
    status: str = Field(..., description="Transaction status")
    created_at: datetime = Field(..., description="Creation timestamp")
    confirmed_at: Optional[datetime] = Field(
        None,
        description="Confirmation timestamp",
    )

    class Config:
        """Pydantic config."""

        json_encoders = {
            UUID: str,
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }

    @classmethod
    def from_entity(cls, transaction):
        """
        Create response from EscrowTransaction entity.

        Args:
            transaction: EscrowTransaction entity

        Returns:
            TransactionResponse instance
        """
        return cls(
            id=transaction.id,
            user_id=transaction.user_id,
            tx_signature=transaction.tx_signature,
            transaction_type=transaction.transaction_type.value,
            amount=transaction.amount,
            token_mint=transaction.token_mint,
            status=transaction.status.value,
            created_at=transaction.created_at,
            confirmed_at=transaction.confirmed_at,
        )


class BalanceResponse(BaseModel):
    """
    Response schema for escrow balance.

    Returns balance and initialization status - never errors if not initialized.
    """

    escrow_account: Optional[str] = Field(
        None,
        description="Escrow PDA address (null if not initialized)",
    )
    balance: Decimal = Field(..., description="Current escrow balance")
    token_mint: str = Field(..., description="Token mint address")
    is_initialized: bool = Field(
        ...,
        description="Whether escrow account is initialized",
    )
    initialized_at: Optional[datetime] = Field(
        None,
        description="When escrow was initialized",
    )
    synced_from_blockchain: bool = Field(
        ...,
        description="Whether balance was synced from blockchain",
    )
    last_synced_at: Optional[datetime] = Field(
        None,
        description="When balance was last synced from blockchain",
    )

    class Config:
        """Pydantic config."""

        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }


class TransactionListResponse(BaseModel):
    """Response schema for list of transactions."""

    transactions: list[TransactionResponse] = Field(
        ...,
        description="List of transactions",
    )
    total: int = Field(..., description="Total number of transactions")

"""
EscrowTransaction entity - Domain model for escrow transactions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class TransactionType(str, Enum):
    """Escrow transaction types."""

    INITIALIZE = "initialize"
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    SUBSCRIPTION_FEE = "subscription_fee"


class TransactionStatus(str, Enum):
    """Transaction processing states."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


@dataclass
class EscrowTransaction:
    """
    EscrowTransaction entity representing a user escrow transaction.

    Business rules:
    - Transaction signature must be unique
    - Amount must be positive for deposits/withdraws
    - Status transitions: PENDING → CONFIRMED or FAILED
    - Cannot re-confirm or re-fail a transaction
    - SUBSCRIPTION_FEE transactions link to subscription
    """

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    tx_signature: str = field(default="")
    transaction_type: TransactionType = field(default=TransactionType.DEPOSIT)
    amount: Decimal = field(default=Decimal("0"))
    token_mint: str = field(default="USDC")
    status: TransactionStatus = field(default=TransactionStatus.PENDING)
    subscription_id: Optional[UUID] = field(default=None)
    created_at: datetime = field(default_factory=datetime.now)
    confirmed_at: Optional[datetime] = field(default=None)

    def __post_init__(self):
        """Validate transaction data after initialization."""
        if not self.tx_signature:
            raise ValueError("Transaction signature is required")

        if self.transaction_type != TransactionType.INITIALIZE:
            if self.amount <= 0:
                raise ValueError("Transaction amount must be positive")

        if not self.token_mint:
            raise ValueError("Token mint is required")

        # Validate subscription_id for SUBSCRIPTION_FEE transactions
        if (
            self.transaction_type == TransactionType.SUBSCRIPTION_FEE
            and not self.subscription_id
        ):
            raise ValueError(
                "subscription_id required for SUBSCRIPTION_FEE transactions"
            )

    def confirm(self) -> None:
        """
        Mark transaction as confirmed.

        Raises:
            ValueError: If not in PENDING status
        """
        if self.status != TransactionStatus.PENDING:
            raise ValueError(
                f"Cannot confirm transaction in {self.status.value} status"
            )

        self.status = TransactionStatus.CONFIRMED
        self.confirmed_at = datetime.now()

    def fail(self) -> None:
        """
        Mark transaction as failed.

        Raises:
            ValueError: If not in PENDING status
        """
        if self.status != TransactionStatus.PENDING:
            raise ValueError(f"Cannot fail transaction in {self.status.value} status")

        self.status = TransactionStatus.FAILED

    def to_dict(self) -> dict:
        """Convert entity to dictionary representation."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "tx_signature": self.tx_signature,
            "transaction_type": self.transaction_type.value,
            "amount": str(self.amount),
            "token_mint": self.token_mint,
            "status": self.status.value,
            "subscription_id": (
                str(self.subscription_id) if self.subscription_id else None
            ),
            "created_at": self.created_at.isoformat(),
            "confirmed_at": (
                self.confirmed_at.isoformat() if self.confirmed_at else None
            ),
        }

"""
User entity - Domain model for platform users.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class User:
    """
    User entity representing a platform user.

    Business rules:
    - Wallet address is unique identifier (Web3 identity)
    - Escrow account is derived from wallet (not stored)
    - Balance is cached from blockchain
    - All authentication via wallet signature verification

    Architecture Decision:
    - wallet_address is single source of truth
    - escrow_account computed on-the-fly (derive_escrow_pda)
    - Only cache volatile blockchain data (balance)
    """

    id: UUID = field(default_factory=uuid4)
    wallet_address: str = field(default="")
    escrow_balance: Decimal = field(default=Decimal("0"))
    last_blockchain_check: Optional[datetime] = field(default=None)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate user data after initialization."""
        if not self.wallet_address:
            raise ValueError("Wallet address is required")

        # Validate wallet address format (Solana: 32-44 chars, base58)
        if not (32 <= len(self.wallet_address) <= 44):
            raise ValueError(
                f"Invalid wallet address length: {len(self.wallet_address)}"
            )

    def update_escrow_balance(self, new_balance: Decimal) -> None:
        """
        Update escrow balance.

        Args:
            new_balance: New balance amount

        Raises:
            ValueError: If balance is negative
        """
        if new_balance < 0:
            raise ValueError("Balance cannot be negative")

        self.escrow_balance = new_balance
        self.updated_at = datetime.now()

    def update_blockchain_check_timestamp(self) -> None:
        """Update timestamp of last blockchain check."""
        self.last_blockchain_check = datetime.now()
        self.updated_at = datetime.now()

    def has_sufficient_balance(self, amount: Decimal) -> bool:
        """Check if user has sufficient escrow balance."""
        return self.escrow_balance >= amount

    def to_dict(self) -> dict:
        """Convert entity to dictionary representation."""
        return {
            "id": str(self.id),
            "wallet_address": self.wallet_address,
            "escrow_balance": str(self.escrow_balance),
            "last_blockchain_check": (
                self.last_blockchain_check.isoformat()
                if self.last_blockchain_check
                else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

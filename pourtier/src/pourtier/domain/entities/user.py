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
    - User can initialize escrow once
    - User can update escrow balance
    - All authentication via wallet signature verification
    """

    id: UUID = field(default_factory=uuid4)
    wallet_address: str = field(default="")
    escrow_account: Optional[str] = field(default=None)
    escrow_balance: Decimal = field(default=Decimal("0"))
    escrow_token_mint: Optional[str] = field(default=None)
    escrow_initialized_at: Optional[datetime] = field(default=None)
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

    def initialize_escrow(
        self,
        escrow_account: str,
        token_mint: str = "USDC",
    ) -> None:
        """
        Initialize escrow account for user.

        Args:
            escrow_account: Escrow PDA address
            token_mint: Token mint address (default: USDC)

        Raises:
            ValueError: If escrow already initialized
        """
        if self.escrow_account:
            raise ValueError("Escrow already initialized")

        self.escrow_account = escrow_account
        self.escrow_token_mint = token_mint
        self.escrow_balance = Decimal("0")
        self.escrow_initialized_at = datetime.now()
        self.updated_at = datetime.now()

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

    def has_sufficient_balance(self, amount: Decimal) -> bool:
        """Check if user has sufficient escrow balance."""
        return self.escrow_balance >= amount

    def to_dict(self) -> dict:
        """Convert entity to dictionary representation."""
        return {
            "id": str(self.id),
            "wallet_address": self.wallet_address,
            "escrow_account": self.escrow_account,
            "escrow_balance": str(self.escrow_balance),
            "escrow_token_mint": self.escrow_token_mint,
            "escrow_initialized_at": (
                self.escrow_initialized_at.isoformat()
                if self.escrow_initialized_at
                else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

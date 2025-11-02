"""
User entity - Domain model for platform users.
"""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class User:
    """
    User entity - minimal Web3 identity.
    
    User is created once when wallet connects and never changes.
    All mutable data (subscriptions, strategies) in separate tables.
    All blockchain data (balance) queried real-time.
    """
    
    id: UUID = field(default_factory=uuid4)
    wallet_address: str = field(default="")
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate user data after initialization."""
        if not self.wallet_address:
            raise ValueError("Wallet address is required")
        
        # Validate Solana wallet address format (Base58, 32-44 chars)
        if not (32 <= len(self.wallet_address) <= 44):
            raise ValueError(
                f"Invalid wallet address length: {len(self.wallet_address)}"
            )
    
    def to_dict(self) -> dict:
        """Convert entity to dictionary representation."""
        return {
            "id": str(self.id),
            "wallet_address": self.wallet_address,
            "created_at": self.created_at.isoformat(),
        }

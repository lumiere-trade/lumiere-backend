"""
WalletAddress value object - Immutable Solana wallet address.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class WalletAddress:
    """
    Value object representing a validated Solana wallet address.

    Business rules:
    - Must be valid base58 encoded string
    - Length between 32-44 characters (typical Solana address)
    - Immutable once created
    """

    address: str

    def __post_init__(self):
        """Validate wallet address on creation."""
        if not self.address:
            raise ValueError("Wallet address cannot be empty")

        if len(self.address) < 32 or len(self.address) > 44:
            raise ValueError(f"Invalid wallet address length: {len(self.address)}")

        # Basic validation - check if base58 characters
        valid_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        if not all(c in valid_chars for c in self.address):
            raise ValueError("Wallet address contains invalid characters")

    def truncated(self) -> str:
        """Return truncated address for display (e.g., 'ABC...XYZ')."""
        return f"{self.address[:6]}...{self.address[-4:]}"

    def __str__(self) -> str:
        """String representation returns full address."""
        return self.address

    def __eq__(self, other) -> bool:
        """Compare wallet addresses by value."""
        if not isinstance(other, WalletAddress):
            return False
        return self.address == other.address

    def __hash__(self) -> int:
        """Make wallet address hashable for use in sets/dicts."""
        return hash(self.address)

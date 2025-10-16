"""
Escrow Query Service interface.

Defines contract for querying escrow account state from blockchain.
"""

from abc import ABC, abstractmethod
from decimal import Decimal


class IEscrowQueryService(ABC):
    """
    Interface for querying escrow account data from blockchain.

    Clean Architecture: Domain layer defines interface,
    Infrastructure layer implements concrete blockchain queries.
    """

    @abstractmethod
    async def get_escrow_balance(self, escrow_account: str) -> Decimal:
        """
        Get current escrow account balance.

        Args:
            escrow_account: Escrow PDA address

        Returns:
            Current balance as Decimal

        Raises:
            EscrowNotFoundError: If escrow account doesn't exist
            BlockchainError: If query fails
        """

    @abstractmethod
    async def close(self) -> None:
        """Close any open connections."""

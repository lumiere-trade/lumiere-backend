"""
Escrow transaction repository interface.

Defines contract for escrow transaction persistence operations.
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from pourtier.domain.entities.escrow_transaction import (
    EscrowTransaction,
    TransactionType,
)


class IEscrowTransactionRepository(ABC):
    """
    Abstract repository interface for escrow transaction persistence.

    Defines operations for storing and retrieving escrow transactions.
    """

    @abstractmethod
    async def create(self, transaction: EscrowTransaction) -> EscrowTransaction:
        """
        Create a new escrow transaction in the database.

        Args:
            transaction: EscrowTransaction entity to persist

        Returns:
            Created transaction with database-generated ID
        """

    @abstractmethod
    async def get_by_id(self, transaction_id: UUID) -> Optional[EscrowTransaction]:
        """
        Retrieve escrow transaction by ID.

        Args:
            transaction_id: Transaction unique identifier

        Returns:
            EscrowTransaction entity if found, None otherwise
        """

    @abstractmethod
    async def get_by_tx_signature(
        self, tx_signature: str
    ) -> Optional[EscrowTransaction]:
        """
        Retrieve escrow transaction by blockchain signature.

        Args:
            tx_signature: Blockchain transaction signature

        Returns:
            EscrowTransaction entity if found, None otherwise
        """

    @abstractmethod
    async def update(self, transaction: EscrowTransaction) -> EscrowTransaction:
        """
        Update existing escrow transaction in database.

        Args:
            transaction: EscrowTransaction entity with updated fields

        Returns:
            Updated transaction entity

        Raises:
            EntityNotFoundError: If transaction not found
        """

    @abstractmethod
    async def list_by_user(
        self,
        user_id: UUID,
        transaction_type: Optional[TransactionType] = None,
    ) -> list[EscrowTransaction]:
        """
        List escrow transactions for user, filtered by type.

        Args:
            user_id: User unique identifier
            transaction_type: Optional transaction type filter

        Returns:
            List of escrow transaction entities
        """

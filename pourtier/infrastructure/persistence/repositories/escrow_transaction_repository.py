"""
EscrowTransaction repository implementation using SQLAlchemy.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pourtier.domain.entities.escrow_transaction import (
    EscrowTransaction,
    TransactionStatus,
    TransactionType,
)
from pourtier.domain.exceptions import EntityNotFoundError
from pourtier.domain.repositories.i_escrow_transaction_repository import (
    IEscrowTransactionRepository,
)
from pourtier.infrastructure.persistence.models import (
    EscrowTransactionModel,
)


class EscrowTransactionRepository(IEscrowTransactionRepository):
    """
    SQLAlchemy implementation of escrow transaction repository.

    Handles EscrowTransaction entity persistence in PostgreSQL.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(self, transaction: EscrowTransaction) -> EscrowTransaction:
        """
        Create a new escrow transaction in the database.

        Args:
            transaction: EscrowTransaction entity to persist

        Returns:
            Created transaction with database-generated ID
        """
        model = EscrowTransactionModel(
            id=transaction.id,
            user_id=transaction.user_id,
            tx_signature=transaction.tx_signature,
            transaction_type=transaction.transaction_type.value,
            amount=transaction.amount,
            token_mint=transaction.token_mint,
            status=transaction.status.value,
            subscription_id=transaction.subscription_id,
            created_at=transaction.created_at,
            confirmed_at=transaction.confirmed_at,
        )

        self.session.add(model)
        await self.session.flush()

        return self._to_entity(model)

    async def get_by_id(self, transaction_id: UUID) -> Optional[EscrowTransaction]:
        """
        Retrieve escrow transaction by ID.

        Args:
            transaction_id: Transaction unique identifier

        Returns:
            EscrowTransaction entity if found, None otherwise
        """
        stmt = select(EscrowTransactionModel).where(
            EscrowTransactionModel.id == transaction_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        return self._to_entity(model) if model else None

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
        stmt = select(EscrowTransactionModel).where(
            EscrowTransactionModel.tx_signature == tx_signature
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        return self._to_entity(model) if model else None

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
        stmt = select(EscrowTransactionModel).where(
            EscrowTransactionModel.id == transaction.id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise EntityNotFoundError("EscrowTransaction", str(transaction.id))

        # Update fields
        model.status = transaction.status.value
        model.confirmed_at = transaction.confirmed_at
        model.subscription_id = transaction.subscription_id

        await self.session.flush()

        return self._to_entity(model)

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
        stmt = select(EscrowTransactionModel).where(
            EscrowTransactionModel.user_id == user_id
        )

        if transaction_type:
            stmt = stmt.where(
                EscrowTransactionModel.transaction_type == transaction_type.value
            )

        stmt = stmt.order_by(EscrowTransactionModel.created_at.desc())

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    def _to_entity(self, model: EscrowTransactionModel) -> EscrowTransaction:
        """Convert ORM model to domain entity."""
        return EscrowTransaction(
            id=model.id,
            user_id=model.user_id,
            tx_signature=model.tx_signature,
            transaction_type=TransactionType(model.transaction_type),
            amount=model.amount,
            token_mint=model.token_mint,
            status=TransactionStatus(model.status),
            subscription_id=model.subscription_id,
            created_at=model.created_at,
            confirmed_at=model.confirmed_at,
        )

"""
Get Escrow Balance use case.

Retrieves user's escrow balance with optional blockchain sync.
"""

from decimal import Decimal
from uuid import UUID

from pourtier.domain.exceptions import EntityNotFoundError, ValidationError
from pourtier.domain.repositories.i_user_repository import IUserRepository
from pourtier.domain.services.i_escrow_query_service import (
    IEscrowQueryService,
)


class GetEscrowBalance:
    """
    Get user's escrow balance.

    Business rules:
    - User must exist
    - User must have initialized escrow
    - Optional: Sync balance from blockchain before returning
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        escrow_query_service: IEscrowQueryService,
    ):
        """
        Initialize use case with dependencies.

        Args:
            user_repository: Repository for user persistence
            escrow_query_service: Service for querying blockchain state
        """
        self.user_repository = user_repository
        self.escrow_query_service = escrow_query_service

    async def execute(
        self,
        user_id: UUID,
        sync_from_blockchain: bool = False,
    ) -> Decimal:
        """
        Execute get escrow balance.

        Args:
            user_id: User unique identifier
            sync_from_blockchain: If True, fetch from blockchain and update

        Returns:
            Current escrow balance

        Raises:
            EntityNotFoundError: If user not found
            ValidationError: If escrow not initialized
            EscrowNotFoundError: If escrow not found on blockchain
        """
        # 1. Get user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError(
                entity_type="User",
                entity_id=str(user_id),
            )

        # 2. Validate escrow initialized
        if not user.escrow_account:
            raise ValidationError(
                field="escrow_account",
                reason="Escrow not initialized for user",
            )

        # 3. Optionally sync from blockchain
        if sync_from_blockchain:
            blockchain_balance = await self.escrow_query_service.get_escrow_balance(
                user.escrow_account
            )

            # Update if different
            if blockchain_balance != user.escrow_balance:
                user.update_escrow_balance(blockchain_balance)
                await self.user_repository.update(user)

        return user.escrow_balance

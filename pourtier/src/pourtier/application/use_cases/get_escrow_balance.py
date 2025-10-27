"""
Get Escrow Balance use case.
Retrieves user's escrow balance with optional blockchain sync.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pourtier.domain.exceptions import EntityNotFoundError
from pourtier.domain.repositories.i_user_repository import IUserRepository
from pourtier.domain.services.i_escrow_query_service import (
    IEscrowQueryService,
)


@dataclass
class EscrowBalanceResult:
    """
    Result of escrow balance query.

    Attributes:
        escrow_account: Escrow PDA address (None if not initialized)
        balance: Current balance in escrow
        token_mint: Token mint address
        is_initialized: Whether escrow account exists
        initialized_at: When escrow was initialized (None if not initialized)
        last_synced_at: When balance was last synced from blockchain
    """

    escrow_account: Optional[str]
    balance: Decimal
    token_mint: str
    is_initialized: bool
    initialized_at: Optional[datetime]
    last_synced_at: Optional[datetime]


class GetEscrowBalance:
    """
    Get user's escrow balance.

    Business rules:
    - User must exist
    - Returns initialization status instead of throwing error
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
    ) -> EscrowBalanceResult:
        """
        Execute get escrow balance.

        Args:
            user_id: User unique identifier
            sync_from_blockchain: If True, fetch from blockchain and update

        Returns:
            EscrowBalanceResult with balance and initialization status

        Raises:
            EntityNotFoundError: If user not found
            EscrowNotFoundError: If escrow not found on blockchain (when syncing)
        """
        # 1. Get user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError(
                entity_type="User",
                entity_id=str(user_id),
            )

        # 2. Check initialization status (no longer throws error)
        is_initialized = bool(user.escrow_account)
        last_synced = None

        # 3. Optionally sync from blockchain if initialized
        if is_initialized and sync_from_blockchain:
            blockchain_balance = await self.escrow_query_service.get_escrow_balance(
                user.escrow_account
            )

            # Update if different
            if blockchain_balance != user.escrow_balance:
                user.update_escrow_balance(blockchain_balance)
                await self.user_repository.update(user)

            last_synced = datetime.utcnow()

        # 4. Return structured result
        return EscrowBalanceResult(
            escrow_account=user.escrow_account,
            balance=(user.escrow_balance if is_initialized else Decimal("0.00")),
            token_mint=(user.escrow_token_mint if user.escrow_token_mint else "USDC"),
            is_initialized=is_initialized,
            initialized_at=(user.escrow_initialized_at if is_initialized else None),
            last_synced_at=last_synced,
        )

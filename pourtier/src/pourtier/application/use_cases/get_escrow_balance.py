"""
Get Escrow Balance use case.
Retrieves user's escrow balance with blockchain sync.
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
from pourtier.infrastructure.blockchain.solana_utils import derive_escrow_pda


@dataclass
class EscrowBalanceResult:
    """
    Result of escrow balance query.

    Attributes:
        escrow_account: Escrow PDA address (computed from wallet)
        balance: Current balance in escrow
        is_initialized: Whether escrow account exists on blockchain
        last_synced_at: When balance was last synced from blockchain
    """

    escrow_account: str
    balance: Decimal
    is_initialized: bool
    last_synced_at: Optional[datetime]


class GetEscrowBalance:
    """
    Get user's escrow balance.

    Business rules:
    - User must exist
    - Escrow account is computed from wallet (not stored)
    - Blockchain is source of truth
    - DB caches balance for performance

    Architecture:
    - Blockchain = source of truth (always correct)
    - DB = performance cache (may be stale)
    - Auto-heal: Sync DB from blockchain when needed
    """

    # Cache blockchain checks for 2 minutes
    BLOCKCHAIN_CHECK_CACHE_SECONDS = 120

    def __init__(
        self,
        user_repository: IUserRepository,
        escrow_query_service: IEscrowQueryService,
        program_id: str,
    ):
        """
        Initialize use case with dependencies.

        Args:
            user_repository: Repository for user persistence
            escrow_query_service: Service for querying blockchain state
            program_id: Solana escrow program ID for PDA derivation
        """
        self.user_repository = user_repository
        self.escrow_query_service = escrow_query_service
        self.program_id = program_id

    def _should_check_blockchain(
        self,
        last_check: Optional[datetime],
        force_sync: bool,
    ) -> bool:
        """
        Determine if we should check blockchain.

        Check blockchain if:
        1. User explicitly requests sync (force_sync=True)
        2. Never checked before (last_check=None)
        3. Cache expired (>2 min since last check)

        Args:
            last_check: Timestamp of last blockchain check
            force_sync: Force blockchain sync

        Returns:
            True if should check blockchain
        """
        if force_sync:
            return True

        if last_check is None:
            return True

        cache_age = datetime.now() - last_check
        return cache_age.total_seconds() > self.BLOCKCHAIN_CHECK_CACHE_SECONDS

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
        """
        # 1. Get user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError(
                entity_type="User",
                entity_id=str(user_id),
            )

        # 2. Derive escrow account (always correct, ~0.01ms)
        escrow_account, _ = derive_escrow_pda(
            user.wallet_address,
            self.program_id,
        )

        # 3. Determine if we should check blockchain
        should_check = self._should_check_blockchain(
            user.last_blockchain_check,
            sync_from_blockchain,
        )

        last_synced = None
        is_initialized = False

        # 4. Check blockchain if needed
        if should_check:
            # Check if escrow exists on blockchain
            is_initialized = await self.escrow_query_service.check_escrow_exists(
                escrow_account
            )

            # If escrow exists, sync balance
            if is_initialized:
                blockchain_balance = await self.escrow_query_service.get_escrow_balance(
                    escrow_account
                )

                # Update balance if different
                if blockchain_balance != user.escrow_balance:
                    user.update_escrow_balance(blockchain_balance)

                last_synced = datetime.utcnow()

            # Update check timestamp
            user.update_blockchain_check_timestamp()
            await self.user_repository.update(user)

        # 5. Return result (escrow_account always computed)
        return EscrowBalanceResult(
            escrow_account=escrow_account,  # Computed (always correct)
            balance=user.escrow_balance,  # Cached (may be stale)
            is_initialized=(
                is_initialized if should_check else True
            ),  # From blockchain or assume true
            last_synced_at=last_synced,
        )

"""
Get Escrow Balance use case.
Retrieves user's escrow balance from blockchain (real-time).
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
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
        balance: Current balance from blockchain
        is_initialized: Whether escrow account exists on blockchain
        token_mint: Token mint address (USDC)
        last_synced_at: When balance was queried (always now)
    """

    escrow_account: str
    balance: Decimal
    is_initialized: bool
    token_mint: str
    last_synced_at: datetime


class GetEscrowBalance:
    """
    Get user's escrow balance from blockchain.

    Business rules:
    - User must exist
    - Escrow account is computed from wallet (not stored)
    - Blockchain is source of truth (no caching)
    - Always query real-time balance

    Architecture:
    - Blockchain = single source of truth
    - No caching = always current data
    - Fast enough for real-time queries (~200-300ms)
    """

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

    async def execute(self, user_id: UUID) -> EscrowBalanceResult:
        """
        Execute get escrow balance from blockchain.

        Args:
            user_id: User unique identifier

        Returns:
            EscrowBalanceResult with current blockchain balance

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

        # 2. Derive escrow account from wallet (always computed)
        escrow_account, _ = derive_escrow_pda(
            user.wallet_address,
            self.program_id,
        )

        # 3. Query blockchain for initialization status
        is_initialized = await self.escrow_query_service.check_escrow_exists(
            escrow_account
        )

        # 4. Query blockchain for balance if initialized
        balance = Decimal("0")
        if is_initialized:
            balance = await self.escrow_query_service.get_escrow_balance(
                escrow_account
            )

        # 5. Return result (all data from blockchain)
        return EscrowBalanceResult(
            escrow_account=escrow_account,  # Computed from wallet
            balance=balance,  # From blockchain (always current)
            is_initialized=is_initialized,  # From blockchain
            token_mint="USDC",  # Hardcoded for now
            last_synced_at=datetime.utcnow(),  # Just queried now
        )

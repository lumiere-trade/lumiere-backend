"""
Prepare Initialize Escrow use case.
Generates unsigned initialize escrow transaction for user to sign in wallet.
"""

from dataclasses import dataclass
from uuid import UUID

from pourtier.domain.exceptions.base import EntityNotFoundError
from pourtier.domain.exceptions.blockchain import (
    EscrowAlreadyInitializedError,
)
from pourtier.domain.repositories.i_user_repository import IUserRepository
from pourtier.domain.services.i_escrow_query_service import IEscrowQueryService
from pourtier.domain.services.i_passeur_bridge import IPasseurBridge
from pourtier.infrastructure.blockchain.solana_utils import derive_escrow_pda


@dataclass
class PrepareInitializeResult:
    """
    Result of prepare initialize operation.

    Attributes:
        transaction: Unsigned transaction (base64) for user to sign
        token_mint: Token mint address (USDC)
    """

    transaction: str
    token_mint: str


class PrepareInitializeEscrow:
    """
    Prepare initialize escrow transaction for user signing.

    Business rules:
    - User must exist
    - User must not have escrow already initialized on blockchain
    - Generates unsigned transaction via Passeur Bridge
    - User signs transaction in wallet (frontend)
    - After signing, user calls POST /api/escrow/initialize

    Architecture:
    - Check blockchain (not DB) for escrow existence
    - Blockchain is source of truth
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        passeur_bridge: IPasseurBridge,
        escrow_query_service: IEscrowQueryService,
        program_id: str,
    ):
        """
        Initialize use case with dependencies.

        Args:
            user_repository: Repository for user data access
            passeur_bridge: Bridge service for preparing transactions
            escrow_query_service: Service for querying blockchain
            program_id: Escrow program ID for PDA derivation
        """
        self.user_repository = user_repository
        self.passeur_bridge = passeur_bridge
        self.escrow_query_service = escrow_query_service
        self.program_id = program_id

    async def execute(
        self,
        user_id: UUID,
        token_mint: str = "USDC",
    ) -> PrepareInitializeResult:
        """
        Prepare initialize escrow transaction.

        Args:
            user_id: User ID
            token_mint: Token mint address (default: USDC)

        Returns:
            PrepareInitializeResult with unsigned transaction

        Raises:
            EntityNotFoundError: If user not found
            EscrowAlreadyInitializedError: If escrow already initialized
            BridgeError: If Passeur Bridge call fails
        """
        # Get user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError(
                entity_type="User",
                entity_id=str(user_id),
            )

        # Derive escrow PDA
        escrow_account, _ = derive_escrow_pda(
            user.wallet_address,
            self.program_id,
        )

        # Check blockchain (not DB) if escrow already exists
        escrow_exists = await self.escrow_query_service.check_escrow_exists(
            escrow_account
        )

        if escrow_exists:
            raise EscrowAlreadyInitializedError(str(user_id))

        # Prepare unsigned transaction via Passeur
        transaction = await self.passeur_bridge.prepare_initialize_escrow(
            user_wallet=user.wallet_address,
            token_mint=token_mint,
        )

        return PrepareInitializeResult(
            transaction=transaction,
            token_mint=token_mint,
        )

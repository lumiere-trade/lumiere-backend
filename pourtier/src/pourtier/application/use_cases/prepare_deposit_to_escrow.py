"""
Prepare Deposit to Escrow use case.
Generates unsigned deposit transaction for user to sign in wallet.
"""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from pourtier.domain.exceptions.base import EntityNotFoundError, ValidationError
from pourtier.domain.repositories.i_user_repository import IUserRepository
from pourtier.domain.services.i_escrow_query_service import IEscrowQueryService
from pourtier.domain.services.i_passeur_bridge import IPasseurBridge
from pourtier.infrastructure.blockchain.solana_utils import derive_escrow_pda


@dataclass
class PrepareDepositResult:
    """
    Result of prepare deposit operation.

    Attributes:
        transaction: Unsigned transaction (base64) for user to sign
        escrow_account: Escrow PDA address
        amount: Deposit amount
    """

    transaction: str
    escrow_account: str
    amount: Decimal


class PrepareDepositToEscrow:
    """
    Prepare deposit transaction for user signing.

    Business rules:
    - User must have initialized escrow account on blockchain
    - Amount must be positive
    - Generates unsigned transaction via Passeur Bridge
    - User signs transaction in wallet (frontend)
    - After signing, user calls POST /api/escrow/deposit

    Architecture:
    - Check blockchain for escrow existence (not DB)
    - Derive escrow account on-the-fly
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
        amount: Decimal,
    ) -> PrepareDepositResult:
        """
        Prepare deposit transaction.

        Args:
            user_id: User ID
            amount: Deposit amount in USDC

        Returns:
            PrepareDepositResult with unsigned transaction

        Raises:
            EntityNotFoundError: If user not found
            ValidationError: If escrow not initialized or amount invalid
            BridgeError: If Passeur Bridge call fails
        """
        # Validate amount
        if amount <= 0:
            raise ValidationError(
                field="amount",
                reason="Deposit amount must be greater than 0",
            )

        # Get user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError(
                entity_type="User",
                entity_id=str(user_id),
            )

        # Derive escrow account
        escrow_account, _ = derive_escrow_pda(
            user.wallet_address,
            self.program_id,
        )

        # Check blockchain if escrow exists
        escrow_exists = await self.escrow_query_service.check_escrow_exists(
            escrow_account
        )

        if not escrow_exists:
            raise ValidationError(
                field="escrow_account",
                reason="Escrow not initialized. Initialize escrow first.",
            )

        # Prepare unsigned transaction via Passeur
        transaction = await self.passeur_bridge.prepare_deposit(
            user_wallet=user.wallet_address,
            escrow_account=escrow_account,
            amount=amount,
        )

        return PrepareDepositResult(
            transaction=transaction,
            escrow_account=escrow_account,
            amount=amount,
        )

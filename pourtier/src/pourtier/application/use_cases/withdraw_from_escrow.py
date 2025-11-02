"""
Withdraw from Escrow use case.

Handles withdrawal submission and balance updates.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pourtier.domain.entities.escrow_transaction import (
    EscrowTransaction,
    TransactionStatus,
    TransactionType,
)
from pourtier.domain.exceptions import (
    EntityNotFoundError,
    InsufficientEscrowBalanceError,
    InvalidTransactionError,
    ValidationError,
)
from pourtier.domain.repositories.i_escrow_transaction_repository import (
    IEscrowTransactionRepository,
)
from pourtier.domain.repositories.i_user_repository import IUserRepository
from pourtier.domain.services.i_escrow_query_service import IEscrowQueryService
from pourtier.domain.services.i_passeur_bridge import IPasseurBridge
from pourtier.infrastructure.blockchain.solana_utils import derive_escrow_pda


class WithdrawFromEscrow:
    """
    Withdraw funds from escrow account.

    Business rules:
    - User must exist
    - User must have initialized escrow on blockchain
    - Signed transaction must be submitted to blockchain
    - Amount must be positive
    - User must have sufficient blockchain balance
    - Transaction must not be duplicate (by signature)

    Architecture:
    - Query blockchain for current balance (source of truth)
    - No user balance updates (blockchain updates automatically)
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        escrow_transaction_repository: IEscrowTransactionRepository,
        passeur_bridge: IPasseurBridge,
        escrow_query_service: IEscrowQueryService,
        program_id: str,
    ):
        """
        Initialize use case with dependencies.

        Args:
            user_repository: Repository for user persistence
            escrow_transaction_repository: Repository for transactions
            passeur_bridge: Bridge for blockchain submission
            escrow_query_service: Service for querying blockchain
            program_id: Escrow program ID for PDA derivation
        """
        self.user_repository = user_repository
        self.escrow_transaction_repository = escrow_transaction_repository
        self.passeur_bridge = passeur_bridge
        self.escrow_query_service = escrow_query_service
        self.program_id = program_id

    async def execute(
        self,
        user_id: UUID,
        amount: Decimal,
        signed_transaction: str,
    ) -> EscrowTransaction:
        """
        Execute withdrawal from escrow.

        Args:
            user_id: User unique identifier
            amount: Withdrawal amount
            signed_transaction: Base64-encoded signed transaction from wallet

        Returns:
            Created EscrowTransaction entity

        Raises:
            EntityNotFoundError: If user not found
            ValidationError: If escrow not initialized or amount invalid
            InsufficientEscrowBalanceError: If insufficient balance
            BridgeError: If blockchain submission fails
            InvalidTransactionError: If duplicate transaction
        """
        # 1. Get user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError(
                entity_type="User",
                entity_id=str(user_id),
            )

        # 2. Derive escrow account
        escrow_account, _ = derive_escrow_pda(
            user.wallet_address,
            self.program_id,
        )

        # 3. Check blockchain if escrow exists
        escrow_exists = await self.escrow_query_service.check_escrow_exists(
            escrow_account
        )

        if not escrow_exists:
            raise ValidationError(
                field="escrow_account",
                reason="Escrow not initialized for user",
            )

        # 4. Validate amount is positive
        if amount <= 0:
            raise ValidationError(
                field="amount",
                reason="Withdrawal amount must be positive",
            )

        # 5. Query blockchain for current balance (source of truth)
        current_balance = await self.escrow_query_service.get_escrow_balance(
            escrow_account
        )

        # 6. Check sufficient balance
        if current_balance < amount:
            raise InsufficientEscrowBalanceError(
                required=str(amount),
                available=str(current_balance),
            )

        # 7. Submit signed transaction to blockchain via Passeur
        tx_signature = await self.passeur_bridge.submit_signed_transaction(
            signed_transaction
        )

        # 8. Check for duplicate transaction
        existing_tx = await self.escrow_transaction_repository.get_by_tx_signature(
            tx_signature
        )
        if existing_tx:
            raise InvalidTransactionError(
                "Transaction already processed",
                tx_signature=tx_signature,
            )

        # 9. Create escrow transaction record
        # Note: Balance updates automatically on blockchain, no user update needed
        transaction = EscrowTransaction(
            id=uuid4(),
            user_id=user_id,
            tx_signature=tx_signature,
            transaction_type=TransactionType.WITHDRAW,
            amount=amount,
            token_mint="USDC",  # Hardcoded for now
            status=TransactionStatus.CONFIRMED,
            confirmed_at=datetime.now(),
        )

        created_transaction = await self.escrow_transaction_repository.create(
            transaction
        )

        return created_transaction

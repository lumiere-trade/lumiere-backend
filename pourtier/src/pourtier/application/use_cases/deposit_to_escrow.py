"""
Deposit to Escrow use case.

Handles deposit submission and balance updates.
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


class DepositToEscrow:
    """
    Deposit funds to escrow account.

    Business rules:
    - User must exist
    - User must have initialized escrow on blockchain
    - Signed transaction must be submitted to blockchain
    - Amount is trusted from user (transaction is cryptographically signed)
    - Amount must be positive
    - Transaction must not be duplicate (by signature)

    Architecture:
    - Check blockchain for escrow existence (not DB)
    - Optimistic update for INSTANT UX
    - Background job syncs real balance periodically
    - No polling - Solana-style fast finality
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
        Execute deposit to escrow.

        FAST APPROACH - Optimistic update:
        1. Submit signed transaction to blockchain
        2. Trust amount (user signed transaction cryptographically)
        3. Update balance immediately - INSTANT UX
        4. Background job reconciles later (eventual consistency)

        Args:
            user_id: User unique identifier
            amount: Deposit amount (from signed transaction)
            signed_transaction: Base64-encoded signed transaction from wallet

        Returns:
            Created EscrowTransaction entity

        Raises:
            EntityNotFoundError: If user not found
            ValidationError: If escrow not initialized or amount invalid
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
                reason="Deposit amount must be positive",
            )

        # 5. Submit signed transaction to blockchain via Passeur
        # This is CRITICAL - ensures transaction is real and user signed it
        tx_signature = await self.passeur_bridge.submit_signed_transaction(
            signed_transaction
        )

        # 6. Check for duplicate transaction
        existing_tx = await self.escrow_transaction_repository.get_by_tx_signature(
            tx_signature
        )
        if existing_tx:
            raise InvalidTransactionError(
                "Transaction already processed",
                tx_signature=tx_signature,
            )

        # 7. Update user balance immediately (INSTANT UX!)
        # We trust the amount because:
        # - Transaction is cryptographically signed by user
        # - Transaction is confirmed on blockchain
        # - User cannot fake a signed transaction
        new_balance = user.escrow_balance + amount
        user.update_escrow_balance(new_balance)

        # 8. Save user to database
        await self.user_repository.update(user)

        # 9. Create escrow transaction record
        transaction = EscrowTransaction(
            id=uuid4(),
            user_id=user_id,
            tx_signature=tx_signature,
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            token_mint="USDC",  # Hardcoded for now
            status=TransactionStatus.CONFIRMED,
            confirmed_at=datetime.now(),
        )

        created_transaction = await self.escrow_transaction_repository.create(
            transaction
        )

        return created_transaction

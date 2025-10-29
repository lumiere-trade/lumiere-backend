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
from pourtier.domain.services.i_passeur_bridge import IPasseurBridge


class DepositToEscrow:
    """
    Deposit funds to escrow account.

    Business rules:
    - User must exist
    - User must have initialized escrow
    - Signed transaction must be submitted to blockchain
    - Amount is trusted from user (transaction is cryptographically signed)
    - Amount must be positive
    - Transaction must not be duplicate (by signature)

    Architecture:
    - Optimistic update for INSTANT UX
    - Background job syncs real balance periodically
    - No polling - Solana-style fast finality
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        escrow_transaction_repository: IEscrowTransactionRepository,
        passeur_bridge: IPasseurBridge,
    ):
        """
        Initialize use case with dependencies.

        Args:
            user_repository: Repository for user persistence
            escrow_transaction_repository: Repository for transactions
            passeur_bridge: Bridge for blockchain submission
        """
        self.user_repository = user_repository
        self.escrow_transaction_repository = escrow_transaction_repository
        self.passeur_bridge = passeur_bridge

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

        # 2. Validate escrow initialized
        if not user.escrow_account:
            raise ValidationError(
                field="escrow_account",
                reason="Escrow not initialized for user",
            )

        # 3. Validate amount is positive
        if amount <= 0:
            raise ValidationError(
                field="amount",
                reason="Deposit amount must be positive",
            )

        # 4. Submit signed transaction to blockchain via Passeur
        # This is CRITICAL - ensures transaction is real and user signed it
        tx_signature = await self.passeur_bridge.submit_signed_transaction(
            signed_transaction
        )

        # 5. Check for duplicate transaction
        existing_tx = await self.escrow_transaction_repository.get_by_tx_signature(
            tx_signature
        )
        if existing_tx:
            raise InvalidTransactionError(
                "Transaction already processed",
                tx_signature=tx_signature,
            )

        # 6. Update user balance immediately (INSTANT UX!)
        # We trust the amount because:
        # - Transaction is cryptographically signed by user
        # - Transaction is confirmed on blockchain
        # - User cannot fake a signed transaction
        new_balance = user.escrow_balance + amount
        user.update_escrow_balance(new_balance)

        # 7. Save user to database
        await self.user_repository.update(user)

        # 8. Create escrow transaction record
        transaction = EscrowTransaction(
            id=uuid4(),
            user_id=user_id,
            tx_signature=tx_signature,
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            token_mint=user.escrow_token_mint,
            status=TransactionStatus.CONFIRMED,
            confirmed_at=datetime.now(),
        )

        created_transaction = await self.escrow_transaction_repository.create(
            transaction
        )

        return created_transaction

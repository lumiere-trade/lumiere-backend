"""
Withdraw from Escrow use case.

Handles withdrawal verification and balance updates.
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
from pourtier.domain.services.i_blockchain_verifier import (
    IBlockchainVerifier,
)


class WithdrawFromEscrow:
    """
    Withdraw funds from escrow account.

    Business rules:
    - User must exist
    - User must have initialized escrow
    - Transaction signature must be verified on blockchain
    - Amount must be extracted from transaction
    - Amount must be positive
    - User must have sufficient balance
    - Transaction must not be duplicate (by signature)
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        escrow_transaction_repository: IEscrowTransactionRepository,
        blockchain_verifier: IBlockchainVerifier,
    ):
        """
        Initialize use case with dependencies.

        Args:
            user_repository: Repository for user persistence
            escrow_transaction_repository: Repository for transactions
            blockchain_verifier: Service for verifying blockchain txs
        """
        self.user_repository = user_repository
        self.escrow_transaction_repository = escrow_transaction_repository
        self.blockchain_verifier = blockchain_verifier

    async def execute(
        self,
        user_id: UUID,
        amount: Decimal,
        tx_signature: str,
    ) -> EscrowTransaction:
        """
        Execute withdrawal from escrow.

        Args:
            user_id: User unique identifier
            amount: Expected withdrawal amount
            tx_signature: Blockchain transaction signature (user-signed)

        Returns:
            Created EscrowTransaction entity

        Raises:
            EntityNotFoundError: If user not found
            ValidationError: If escrow not initialized or amount invalid
            InsufficientEscrowBalanceError: If insufficient balance
            TransactionNotFoundError: If tx not found on blockchain
            TransactionNotConfirmedError: If tx not confirmed
            InvalidTransactionError: If amount mismatch or duplicate
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

        # 3. Check for duplicate transaction
        existing_tx = await self.escrow_transaction_repository.get_by_tx_signature(
            tx_signature
        )
        if existing_tx:
            raise InvalidTransactionError(
                "Transaction already processed",
                tx_signature=tx_signature,
            )

        # 4. Verify transaction on blockchain
        verified_tx = await self.blockchain_verifier.verify_transaction(tx_signature)

        # 5. Validate amount matches
        if verified_tx.amount is None:
            raise InvalidTransactionError(
                "Could not extract amount from transaction",
                tx_signature=tx_signature,
            )

        if verified_tx.amount != amount:
            raise InvalidTransactionError(
                f"Amount mismatch: expected {amount}, " f"got {verified_tx.amount}",
                tx_signature=tx_signature,
            )

        # 6. Validate amount is positive
        if amount <= 0:
            raise ValidationError(
                field="amount",
                reason="Withdrawal amount must be positive",
            )

        # 7. Check sufficient balance
        if not user.has_sufficient_balance(amount):
            raise InsufficientEscrowBalanceError(
                required=str(amount),
                available=str(user.escrow_balance),
            )

        # 8. Update user escrow balance
        new_balance = user.escrow_balance - amount
        user.update_escrow_balance(new_balance)

        # 9. Save user to database
        await self.user_repository.update(user)

        # 10. Create escrow transaction record
        transaction = EscrowTransaction(
            id=uuid4(),
            user_id=user_id,
            tx_signature=tx_signature,
            transaction_type=TransactionType.WITHDRAW,
            amount=amount,
            token_mint=user.escrow_token_mint,
            status=TransactionStatus.CONFIRMED,
            confirmed_at=(
                datetime.fromtimestamp(verified_tx.block_time)
                if verified_tx.block_time
                else datetime.now()
            ),
        )

        created_transaction = await self.escrow_transaction_repository.create(
            transaction
        )

        return created_transaction

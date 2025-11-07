"""
Deposit to Escrow use case.

Handles deposit submission and transaction recording.
CRITICAL: Idempotent to prevent double deposits.
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
from shared.resilience import IdempotencyKey


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
    - Blockchain is single source of truth for balances
    - No balance caching (query real-time instead)
    - Fast Solana finality (~400ms) means no need for optimistic updates
    - IDEMPOTENT: Same idempotency_key prevents double deposit
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        escrow_transaction_repository: IEscrowTransactionRepository,
        passeur_bridge: IPasseurBridge,
        escrow_query_service: IEscrowQueryService,
        program_id: str,
        idempotency_store=None,
    ):
        """
        Initialize use case with dependencies.

        Args:
            user_repository: Repository for user persistence
            escrow_transaction_repository: Repository for transactions
            passeur_bridge: Bridge for blockchain submission
            escrow_query_service: Service for querying blockchain
            program_id: Escrow program ID for PDA derivation
            idempotency_store: Store for idempotency keys (Redis/InMemory)
        """
        self.user_repository = user_repository
        self.escrow_transaction_repository = escrow_transaction_repository
        self.passeur_bridge = passeur_bridge
        self.escrow_query_service = escrow_query_service
        self.program_id = program_id
        self.idempotency_store = idempotency_store

    async def execute(
        self,
        user_id: UUID,
        amount: Decimal,
        signed_transaction: str,
        idempotency_key: str = None,
    ) -> EscrowTransaction:
        """
        Execute deposit to escrow with idempotency protection.

        Args:
            user_id: User unique identifier
            amount: Deposit amount (from signed transaction)
            signed_transaction: Base64-encoded signed transaction from wallet
            idempotency_key: Client-provided idempotency key (REQUIRED)

        Returns:
            Created EscrowTransaction entity

        Raises:
            EntityNotFoundError: If user not found
            ValidationError: If escrow not initialized or amount invalid
            BridgeError: If blockchain submission fails
            InvalidTransactionError: If duplicate transaction
        """
        # Generate idempotency key if not provided
        if idempotency_key is None:
            idempotency_key = IdempotencyKey.from_user_request(
                user_id=str(user_id),
                operation="deposit",
                amount=str(amount),
                token="USDC",
            )

        # Check idempotency before execution
        if self.idempotency_store:
            cached = await self.idempotency_store.get_async(idempotency_key)
            if cached:
                return cached

        # Execute deposit
        result = await self._execute_deposit(user_id, amount, signed_transaction)

        # Store result for idempotency
        if self.idempotency_store:
            await self.idempotency_store.set_async(idempotency_key, result, ttl=86400)

        return result

    async def _execute_deposit(
        self,
        user_id: UUID,
        amount: Decimal,
        signed_transaction: str,
    ) -> EscrowTransaction:
        """Internal execution logic (called after idempotency check)."""
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

        # 7. Create escrow transaction record
        now = datetime.now()

        transaction = EscrowTransaction(
            id=uuid4(),
            user_id=user_id,
            tx_signature=tx_signature,
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            token_mint="USDC",
            status=TransactionStatus.CONFIRMED,
            created_at=now,
            confirmed_at=now,
        )

        created_transaction = await self.escrow_transaction_repository.create(
            transaction
        )

        return created_transaction

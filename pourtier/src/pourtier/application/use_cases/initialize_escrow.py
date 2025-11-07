"""
Initialize Escrow use case.

Handles escrow account initialization for users.
CRITICAL: Idempotent to prevent duplicate initialization.
"""

from datetime import datetime
from uuid import UUID, uuid4

from shared.resilience import IdempotencyKey, idempotent

from pourtier.domain.entities.escrow_transaction import (
    EscrowTransaction,
    TransactionStatus,
    TransactionType,
)
from pourtier.domain.entities.user import User
from pourtier.domain.exceptions import (
    EntityNotFoundError,
    EscrowAlreadyInitializedError,
)
from pourtier.domain.repositories.i_escrow_transaction_repository import (
    IEscrowTransactionRepository,
)
from pourtier.domain.repositories.i_user_repository import IUserRepository
from pourtier.domain.services.i_passeur_bridge import IPasseurBridge
from pourtier.infrastructure.blockchain.solana_utils import derive_escrow_pda


class InitializeEscrow:
    """
    Initialize escrow account for user.

    Business rules:
    - User must exist
    - User must not have escrow already initialized on blockchain
    - Signed transaction must be submitted to blockchain
    - Escrow account is derived deterministically (PDA)

    Architecture:
    - Escrow account is NOT stored in DB
    - Only transaction record is stored for audit trail
    - Blockchain is source of truth for initialization status
    - User entity is immutable (no updates after initialization)
    - IDEMPOTENT: Same idempotency_key returns cached result
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        escrow_transaction_repository: IEscrowTransactionRepository,
        passeur_bridge: IPasseurBridge,
        program_id: str,
        idempotency_store=None,
    ):
        """
        Initialize use case with dependencies.

        Args:
            user_repository: Repository for user persistence
            escrow_transaction_repository: Repository for transactions
            passeur_bridge: Bridge for blockchain submission
            program_id: Escrow program ID for PDA derivation
            idempotency_store: Store for idempotency keys (Redis/InMemory)
        """
        self.user_repository = user_repository
        self.escrow_transaction_repository = escrow_transaction_repository
        self.passeur_bridge = passeur_bridge
        self.program_id = program_id
        self.idempotency_store = idempotency_store

    async def execute(
        self,
        user_id: UUID,
        signed_transaction: str,
        token_mint: str = "USDC",
        idempotency_key: str = None,
    ) -> tuple[User, str]:
        """
        Execute escrow initialization with idempotency protection.

        Args:
            user_id: User unique identifier
            signed_transaction: Base64-encoded signed transaction from wallet
            token_mint: Token mint address (default: USDC)
            idempotency_key: Client-provided idempotency key

        Returns:
            Tuple of (User entity, transaction signature)

        Raises:
            EntityNotFoundError: If user not found
            EscrowAlreadyInitializedError: If user has escrow on blockchain
            BridgeError: If blockchain submission fails
        """
        # Generate idempotency key if not provided
        if idempotency_key is None:
            idempotency_key = IdempotencyKey.from_user_request(
                user_id=str(user_id),
                operation="initialize_escrow",
                token_mint=token_mint,
            )

        # Check idempotency before execution
        if self.idempotency_store:
            cached = await self.idempotency_store.get_async(idempotency_key)
            if cached:
                return cached

        # Execute initialization
        result = await self._execute_initialization(
            user_id, signed_transaction, token_mint
        )

        # Store result for idempotency
        if self.idempotency_store:
            await self.idempotency_store.set_async(
                idempotency_key, result, ttl=86400
            )

        return result

    async def _execute_initialization(
        self,
        user_id: UUID,
        signed_transaction: str,
        token_mint: str,
    ) -> tuple[User, str]:
        """Internal execution logic (called after idempotency check)."""
        # 1. Get user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError(
                entity_type="User",
                entity_id=str(user_id),
            )

        # 2. Derive escrow PDA (deterministic)
        escrow_account, _ = derive_escrow_pda(
            user.wallet_address,
            self.program_id,
        )

        # 3. Submit signed transaction to blockchain via Passeur
        try:
            tx_signature = await self.passeur_bridge.submit_signed_transaction(
                signed_transaction
            )
        except Exception as e:
            # If blockchain rejects (account already exists), throw proper error
            if "already in use" in str(e).lower():
                raise EscrowAlreadyInitializedError(str(user_id))
            raise

        # 4. Create escrow transaction record (INITIALIZE type)
        now = datetime.now()
        transaction = EscrowTransaction(
            id=uuid4(),
            user_id=user_id,
            tx_signature=tx_signature,
            transaction_type=TransactionType.INITIALIZE,
            amount=0,
            token_mint=token_mint,
            status=TransactionStatus.CONFIRMED,
            created_at=now,
            confirmed_at=now,
        )

        await self.escrow_transaction_repository.create(transaction)

        # 5. Return user (immutable) and transaction signature
        return user, tx_signature

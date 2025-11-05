"""
Initialize Escrow use case.

Handles escrow account initialization for users.
"""

from datetime import datetime
from uuid import UUID, uuid4

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
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        escrow_transaction_repository: IEscrowTransactionRepository,
        passeur_bridge: IPasseurBridge,
        program_id: str,
    ):
        """
        Initialize use case with dependencies.

        Args:
            user_repository: Repository for user persistence
            escrow_transaction_repository: Repository for transactions
            passeur_bridge: Bridge for blockchain submission
            program_id: Escrow program ID for PDA derivation
        """
        self.user_repository = user_repository
        self.escrow_transaction_repository = escrow_transaction_repository
        self.passeur_bridge = passeur_bridge
        self.program_id = program_id

    async def execute(
        self,
        user_id: UUID,
        signed_transaction: str,
        token_mint: str = "USDC",
    ) -> tuple[User, str]:
        """
        Execute escrow initialization.

        Args:
            user_id: User unique identifier
            signed_transaction: Base64-encoded signed transaction from wallet
            token_mint: Token mint address (default: USDC)

        Returns:
            Tuple of (User entity, transaction signature)

        Raises:
            EntityNotFoundError: If user not found
            EscrowAlreadyInitializedError: If user has escrow on blockchain
            BridgeError: If blockchain submission fails
        """
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

        # 3. Check if escrow already exists on blockchain
        # Note: Blockchain will reject if account already exists
        # We rely on blockchain validation rather than pre-checking

        # 4. Submit signed transaction to blockchain via Passeur
        try:
            tx_signature = await self.passeur_bridge.submit_signed_transaction(
                signed_transaction
            )
        except Exception as e:
            # If blockchain rejects (account already exists), throw proper error
            if "already in use" in str(e).lower():
                raise EscrowAlreadyInitializedError(str(user_id))
            raise

        # 5. Create escrow transaction record (INITIALIZE type)
        # This is our audit trail - blockchain is source of truth
        now = datetime.now()
        transaction = EscrowTransaction(
            id=uuid4(),
            user_id=user_id,
            tx_signature=tx_signature,
            transaction_type=TransactionType.INITIALIZE,
            amount=0,  # No amount for initialization
            token_mint=token_mint,
            status=TransactionStatus.CONFIRMED,
            created_at=now,
            confirmed_at=now,
        )

        await self.escrow_transaction_repository.create(transaction)

        # 6. Return user (immutable) and transaction signature
        return user, tx_signature

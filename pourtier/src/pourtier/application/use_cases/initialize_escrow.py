"""
Initialize Escrow use case.

Handles escrow account initialization for users.
"""

from datetime import datetime
from uuid import UUID, uuid4

from solders.pubkey import Pubkey

from pourtier.config.settings import get_settings
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
from pourtier.domain.services.i_blockchain_verifier import (
    IBlockchainVerifier,
)


class InitializeEscrow:
    """
    Initialize escrow account for user.

    Business rules:
    - User must exist
    - User must not have escrow already initialized
    - Transaction signature must be verified on blockchain
    - Escrow account is derived deterministically (PDA)
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

    def _derive_escrow_pda(self, wallet_address: str) -> str:
        """
        Derive escrow PDA for user (deterministic).

        Args:
            wallet_address: User's wallet public key

        Returns:
            Escrow PDA address as string
        """
        user_pubkey = Pubkey.from_string(wallet_address)
        program_id = Pubkey.from_string(get_settings().ESCROW_PROGRAM_ID)

        # PDA seeds: ["escrow", user_pubkey]
        seeds = [b"escrow", bytes(user_pubkey)]
        escrow_pda, _ = Pubkey.find_program_address(seeds, program_id)

        return str(escrow_pda)

    async def execute(
        self,
        user_id: UUID,
        tx_signature: str,
        token_mint: str = "USDC",
    ) -> User:
        """
        Execute escrow initialization.

        Args:
            user_id: User unique identifier
            tx_signature: Blockchain transaction signature (user-signed)
            token_mint: Token mint address (default: USDC)

        Returns:
            Updated User entity with escrow_account set

        Raises:
            EntityNotFoundError: If user not found
            EscrowAlreadyInitializedError: If user has escrow
            TransactionNotFoundError: If tx not found on blockchain
            TransactionNotConfirmedError: If tx not confirmed
        """
        # 1. Get user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError(
                entity_type="User",
                entity_id=str(user_id),
            )

        # 2. Check if escrow already initialized
        if user.escrow_account:
            raise EscrowAlreadyInitializedError(str(user_id))

        # 3. Verify transaction on blockchain (exists & confirmed)
        verified_tx = await self.blockchain_verifier.verify_transaction(tx_signature)

        # 4. Derive escrow PDA (deterministic, no parsing needed!)
        escrow_account = self._derive_escrow_pda(user.wallet_address)

        # 5. Initialize user's escrow
        user.initialize_escrow(
            escrow_account=escrow_account,
            token_mint=token_mint,
        )

        # 6. Save user to database
        updated_user = await self.user_repository.update(user)

        # 7. Create escrow transaction record (INITIALIZE type)
        transaction = EscrowTransaction(
            id=uuid4(),
            user_id=user_id,
            tx_signature=tx_signature,
            transaction_type=TransactionType.INITIALIZE,
            amount=0,  # No amount for initialization
            token_mint=token_mint,
            status=TransactionStatus.CONFIRMED,
            confirmed_at=(
                datetime.fromtimestamp(verified_tx.block_time)
                if verified_tx.block_time
                else datetime.now()
            ),
        )

        await self.escrow_transaction_repository.create(transaction)

        return updated_user

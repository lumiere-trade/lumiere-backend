"""
Escrow API routes.

Handles escrow initialization, deposits, withdrawals, and balance queries.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from pourtier.application.use_cases.deposit_to_escrow import DepositToEscrow
from pourtier.application.use_cases.get_escrow_balance import GetEscrowBalance
from pourtier.application.use_cases.initialize_escrow import InitializeEscrow
from pourtier.application.use_cases.prepare_deposit_to_escrow import (
    PrepareDepositToEscrow,
)
from pourtier.application.use_cases.prepare_initialize_escrow import (
    PrepareInitializeEscrow,
)
from pourtier.application.use_cases.withdraw_from_escrow import WithdrawFromEscrow
from pourtier.di.dependencies import (
    get_db_session,
    get_deposit_to_escrow,
    get_get_escrow_balance,
    get_initialize_escrow,
    get_prepare_deposit_to_escrow,
    get_prepare_initialize_escrow,
    get_withdraw_from_escrow,
)
from pourtier.domain.entities.escrow_transaction import TransactionType
from pourtier.domain.entities.user import User
from pourtier.domain.exceptions import (
    BlockchainError,
    EntityNotFoundError,
    EscrowAlreadyInitializedError,
    InsufficientEscrowBalanceError,
    InvalidTransactionError,
    ValidationError,
)
from pourtier.infrastructure.persistence.repositories.escrow_transaction_repository import (
    EscrowTransactionRepository,
)
from pourtier.presentation.api.middleware.auth import get_current_user
from pourtier.presentation.schemas.escrow_schemas import (
    BalanceResponse,
    DepositRequest,
    EscrowAccountResponse,
    InitializeEscrowRequest,
    PrepareDepositRequest,
    PrepareDepositResponse,
    PrepareInitializeResponse,
    TransactionListResponse,
    TransactionResponse,
    WithdrawRequest,
)

router = APIRouter(prefix="/escrow", tags=["escrow"])


# ================================================================
# Prepare Initialize Escrow
# ================================================================


@router.post(
    "/prepare-initialize",
    response_model=PrepareInitializeResponse,
    status_code=status.HTTP_200_OK,
    summary="Prepare initialize escrow transaction",
    description="Generate unsigned initialize transaction for user to sign",
)
async def prepare_initialize_escrow(
    current_user: User = Depends(get_current_user),
    use_case: PrepareInitializeEscrow = Depends(get_prepare_initialize_escrow),
):
    """
    Prepare initialize escrow transaction for user signing.

    Returns unsigned transaction (base64) for user to sign in wallet.
    After signing, user calls POST /api/escrow/initialize with signed transaction.

    Flow:
    1. User calls this endpoint
    2. Backend generates unsigned transaction via Passeur
    3. User signs transaction in wallet (frontend)
    4. User calls POST /api/escrow/initialize with signed tx
    5. Backend submits to blockchain and returns signature
    """
    try:
        result = await use_case.execute(user_id=current_user.id)

        return PrepareInitializeResponse(
            transaction=result.transaction,
            token_mint=result.token_mint,
        )

    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except EscrowAlreadyInitializedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except BlockchainError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to prepare initialize: {str(e)}",
        )


# ================================================================
# Initialize Escrow
# ================================================================


@router.post(
    "/initialize",
    response_model=EscrowAccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize escrow account",
    description="Initialize user's escrow account with signed transaction",
)
async def initialize_escrow(
    request: InitializeEscrowRequest,
    current_user: User = Depends(get_current_user),
    use_case: InitializeEscrow = Depends(get_initialize_escrow),
):
    """
    Initialize escrow account for current user.

    User must have signed initialization transaction in wallet.
    Backend submits transaction to blockchain.
    """
    try:
        user, tx_signature = await use_case.execute(
            user_id=current_user.id,
            signed_transaction=request.signed_transaction,
            token_mint=request.token_mint,
        )

        return EscrowAccountResponse(
            escrow_account=user.escrow_account,
            balance=user.escrow_balance,
            token_mint=user.escrow_token_mint,
            tx_signature=tx_signature,
        )

    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except EscrowAlreadyInitializedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except (ValidationError, InvalidTransactionError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except BlockchainError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Blockchain error: {str(e)}",
        )


# ================================================================
# Prepare Deposit
# ================================================================


@router.post(
    "/prepare-deposit",
    response_model=PrepareDepositResponse,
    status_code=status.HTTP_200_OK,
    summary="Prepare deposit transaction",
    description="Generate unsigned deposit transaction for user to sign",
)
async def prepare_deposit(
    request: PrepareDepositRequest,
    current_user: User = Depends(get_current_user),
    use_case: PrepareDepositToEscrow = Depends(get_prepare_deposit_to_escrow),
):
    """
    Prepare deposit transaction for user signing.

    Returns unsigned transaction (base64) for user to sign in wallet.
    After signing, user calls POST /api/escrow/deposit with signed transaction.

    Flow:
    1. User calls this endpoint with amount
    2. Backend generates unsigned transaction via Passeur
    3. User signs transaction in wallet (frontend)
    4. User calls POST /api/escrow/deposit with signed tx
    """
    try:
        result = await use_case.execute(
            user_id=current_user.id,
            amount=request.amount,
        )

        return PrepareDepositResponse(
            transaction=result.transaction,
            escrow_account=result.escrow_account,
            amount=result.amount,
        )

    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except BlockchainError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to prepare deposit: {str(e)}",
        )


# ================================================================
# Deposit
# ================================================================


@router.post(
    "/deposit",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Deposit funds to escrow",
    description="Deposit funds with signed blockchain transaction",
)
async def deposit_to_escrow(
    request: DepositRequest,
    current_user: User = Depends(get_current_user),
    use_case: DepositToEscrow = Depends(get_deposit_to_escrow),
):
    """
    Deposit funds to escrow account.

    User must have signed deposit transaction in wallet.
    """
    try:
        transaction = await use_case.execute(
            user_id=current_user.id,
            amount=request.amount,
            signed_transaction=request.signed_transaction,
        )

        return TransactionResponse.from_entity(transaction)

    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except (ValidationError, InvalidTransactionError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except BlockchainError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Blockchain error: {str(e)}",
        )


# ================================================================
# Withdraw
# ================================================================


@router.post(
    "/withdraw",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Withdraw funds from escrow",
    description="Withdraw funds with signed blockchain transaction",
)
async def withdraw_from_escrow(
    request: WithdrawRequest,
    current_user: User = Depends(get_current_user),
    use_case: WithdrawFromEscrow = Depends(get_withdraw_from_escrow),
):
    """
    Withdraw funds from escrow account.

    User must have signed withdrawal transaction in wallet.
    """
    try:
        transaction = await use_case.execute(
            user_id=current_user.id,
            amount=request.amount,
            signed_transaction=request.signed_transaction,
        )

        return TransactionResponse.from_entity(transaction)

    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InsufficientEscrowBalanceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except (ValidationError, InvalidTransactionError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except BlockchainError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Blockchain error: {str(e)}",
        )


# ================================================================
# Get Balance
# ================================================================


@router.get(
    "/balance",
    response_model=BalanceResponse,
    summary="Get escrow balance",
    description="Get current escrow balance with optional blockchain sync",
)
async def get_escrow_balance(
    sync: bool = False,
    current_user: User = Depends(get_current_user),
    use_case: GetEscrowBalance = Depends(get_get_escrow_balance),
):
    """
    Get current escrow balance.

    Returns balance and initialization status - never errors if not initialized.

    Query params:
    - sync: If true, sync balance from blockchain before returning
    """
    try:
        result = await use_case.execute(
            user_id=current_user.id,
            sync_from_blockchain=sync,
        )

        return BalanceResponse(
            escrow_account=result.escrow_account,
            balance=result.balance,
            token_mint=result.token_mint,
            is_initialized=result.is_initialized,
            initialized_at=result.initialized_at,
            synced_from_blockchain=sync,
            last_synced_at=result.last_synced_at,
        )

    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except BlockchainError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Blockchain error: {str(e)}",
        )


# ================================================================
# List Transactions
# ================================================================


@router.get(
    "/transactions",
    response_model=TransactionListResponse,
    summary="List escrow transactions",
    description="Get list of user's escrow transactions",
)
async def list_escrow_transactions(
    transaction_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List escrow transactions for current user.

    Query params:
    - transaction_type: Filter by type (deposit, withdraw, initialize)
    """
    try:
        tx_repo = EscrowTransactionRepository(session)

        # Parse transaction type if provided
        tx_type = None
        if transaction_type:
            try:
                tx_type = TransactionType(transaction_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid transaction type: {transaction_type}",
                )

        transactions = await tx_repo.list_by_user(
            user_id=current_user.id,
            transaction_type=tx_type,
        )

        return TransactionListResponse(
            transactions=[TransactionResponse.from_entity(tx) for tx in transactions],
            total=len(transactions),
        )

    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

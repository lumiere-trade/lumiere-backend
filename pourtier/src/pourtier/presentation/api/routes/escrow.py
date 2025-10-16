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
from pourtier.application.use_cases.withdraw_from_escrow import WithdrawFromEscrow
from pourtier.di.dependencies import (
    get_db_session,
    get_deposit_to_escrow,
    get_get_escrow_balance,
    get_initialize_escrow,
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
from pourtier.infrastructure.persistence.repositories.user_repository import (
    UserRepository,
)
from pourtier.presentation.api.middleware.auth import get_current_user
from pourtier.presentation.schemas.escrow_schemas import (
    BalanceResponse,
    DepositRequest,
    EscrowAccountResponse,
    InitializeEscrowRequest,
    TransactionListResponse,
    TransactionResponse,
    WithdrawRequest,
)

router = APIRouter(prefix="/escrow", tags=["escrow"])


# ================================================================
# Initialize Escrow
# ================================================================


@router.post(
    "/initialize",
    response_model=EscrowAccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize escrow account",
    description="Initialize user's escrow account with blockchain tx",
)
async def initialize_escrow(
    request: InitializeEscrowRequest,
    current_user: User = Depends(get_current_user),
    use_case: InitializeEscrow = Depends(get_initialize_escrow),
):
    """
    Initialize escrow account for current user.

    User must have signed initialization transaction in wallet.
    """
    try:
        user = await use_case.execute(
            user_id=current_user.id,
            tx_signature=request.tx_signature,
            token_mint=request.token_mint,
        )

        return EscrowAccountResponse(
            escrow_account=user.escrow_account,
            balance=user.escrow_balance,
            token_mint=user.escrow_token_mint,
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
# Deposit
# ================================================================


@router.post(
    "/deposit",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Deposit funds to escrow",
    description="Deposit funds with user-signed blockchain transaction",
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
            tx_signature=request.tx_signature,
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
    description="Withdraw funds with user-signed blockchain transaction",
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
            tx_signature=request.tx_signature,
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
    session: AsyncSession = Depends(get_db_session),
    use_case: GetEscrowBalance = Depends(get_get_escrow_balance),
):
    """
    Get current escrow balance.

    Query params:
    - sync: If true, sync balance from blockchain before returning
    """
    try:
        balance = await use_case.execute(
            user_id=current_user.id,
            sync_from_blockchain=sync,
        )

        # Get user to fetch token_mint
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(current_user.id)

        return BalanceResponse(
            balance=balance,
            token_mint=user.escrow_token_mint if user else "USDC",
            synced_from_blockchain=sync,
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

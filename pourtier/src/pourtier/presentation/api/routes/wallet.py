"""
Wallet API routes.

Provides endpoints for wallet operations:
- GET /wallet/balance - Get wallet USDC balance
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from pourtier.application.use_cases.get_wallet_balance import GetWalletBalance
from pourtier.di.dependencies import get_get_wallet_balance
from pourtier.domain.exceptions.base import ValidationError
from pourtier.domain.exceptions.blockchain import BridgeError
from pourtier.presentation.schemas.wallet_schemas import WalletBalanceResponse

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get(
    "/balance",
    response_model=WalletBalanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get wallet balance",
    description="Get USDC balance in user's Solana wallet (not escrow)",
)
async def get_wallet_balance(
    wallet: str = Query(..., description="Solana wallet address"),
    use_case: GetWalletBalance = Depends(get_get_wallet_balance),
) -> WalletBalanceResponse:
    """
    Get wallet USDC balance.

    This returns the balance in the user's Solana wallet,
    NOT the escrow balance. Use /api/escrow/balance for escrow.

    Args:
        wallet: Solana wallet address to query
        use_case: GetWalletBalance use case (injected)

    Returns:
        Wallet balance details

    Raises:
        HTTPException: 400 if wallet address invalid
        HTTPException: 502 if Passeur Bridge unavailable
    """
    try:
        result = await use_case.execute(wallet_address=wallet)

        return WalletBalanceResponse(
            wallet_address=result.wallet_address,
            balance=str(result.balance),
            token_mint=result.token_mint,
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except BridgeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to get wallet balance: {str(e)}",
        )

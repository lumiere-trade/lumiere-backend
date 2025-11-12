"""
Wallet API routes.

Handles wallet balance queries.
"""

from fastapi import APIRouter, HTTPException, Query, Request, status

from passeur.domain.exceptions import (
    BridgeConnectionException,
    BridgeTimeoutException,
)
from passeur.presentation.schemas.wallet import WalletBalanceResponse

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get(
    "/balance",
    response_model=WalletBalanceResponse,
    status_code=status.HTTP_200_OK,
)
async def get_wallet_balance(
    wallet: str = Query(..., description="Wallet public key"),
    req: Request = None,
):
    """
    Get wallet token balance.

    No idempotency (query operation).
    """
    bridge_client = req.app.state.bridge_client

    try:
        result = await bridge_client.get_wallet_balance(wallet)
        return WalletBalanceResponse(**result)

    except BridgeConnectionException:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Bridge connection failed",
        )
    except BridgeTimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Bridge request timeout",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bridge error: {str(e)}",
        )

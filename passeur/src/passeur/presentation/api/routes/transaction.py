"""
Transaction API routes.

Handles transaction submission and status queries.
"""

from fastapi import APIRouter, HTTPException, Request, status

from passeur.config.settings import get_settings
from passeur.domain.exceptions import (
    BridgeConnectionException,
    BridgeTimeoutException,
)
from passeur.presentation.schemas.transaction import (
    SubmitTransactionRequest,
    SubmitTransactionResponse,
    TransactionStatusResponse,
)

router = APIRouter(prefix="/transaction", tags=["transaction"])


@router.post(
    "/submit",
    response_model=SubmitTransactionResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_transaction(
    request_data: SubmitTransactionRequest,
    req: Request,
):
    """
    Submit signed transaction to blockchain.

    Idempotent (7 days) - prevents duplicate submissions.
    """
    bridge_client = req.app.state.bridge_client
    redis_store = req.app.state.redis_store
    settings = get_settings()

    idempotency_key = f"tx:submit:{request_data.signedTransaction[:16]}"
    ttl = settings.resilience.idempotency.financial_operations * 86400

    is_duplicate, cached = await redis_store.check_and_store(idempotency_key, ttl)

    if is_duplicate and cached:
        return SubmitTransactionResponse(**cached)

    try:
        result = await bridge_client.submit_transaction(
            signed_transaction=request_data.signedTransaction
        )

        await redis_store.store_result(idempotency_key, result)

        return SubmitTransactionResponse(**result)

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


@router.get(
    "/status/{signature}",
    response_model=TransactionStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_transaction_status(
    signature: str,
    req: Request,
):
    """
    Get transaction confirmation status.

    No idempotency (query operation).
    """
    bridge_client = req.app.state.bridge_client

    try:
        result = await bridge_client.get_transaction_status(signature)
        return TransactionStatusResponse(**result)

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

"""
Escrow API routes.

Proxy layer between external API and Node.js bridge with resilience patterns.
"""

from fastapi import APIRouter, HTTPException, Request, status

from passeur.config.settings import get_settings
from passeur.domain.exceptions import (
    BridgeConnectionException,
    BridgeTimeoutException,
)
from passeur.presentation.schemas.escrow import (
    PrepareInitializeRequest,
    PrepareInitializeResponse,
    PrepareDelegatePlatformRequest,
    PrepareDelegateTradingRequest,
    PrepareDelegateResponse,
    PrepareRevokeRequest,
    PrepareRevokeResponse,
    PrepareDepositRequest,
    PrepareDepositResponse,
    PrepareWithdrawRequest,
    PrepareWithdrawResponse,
    PrepareCloseRequest,
    PrepareCloseResponse,
    EscrowDetailsResponse,
    EscrowBalanceResponse,
)

router = APIRouter(prefix="/escrow", tags=["escrow"])


@router.post(
    "/prepare-initialize",
    response_model=PrepareInitializeResponse,
    status_code=status.HTTP_200_OK,
)
async def prepare_initialize(
    request_data: PrepareInitializeRequest,
    req: Request,
):
    """
    Prepare initialize escrow transaction.

    Creates unsigned transaction for user to sign.
    Idempotent (7 days) - safe to retry.
    """
    bridge_client = req.app.state.bridge_client
    redis_store = req.app.state.redis_store
    settings = get_settings()

    idempotency_key = f"escrow:init:{request_data.userWallet}"
    ttl = settings.resilience.idempotency.financial_operations * 86400

    is_duplicate, cached = await redis_store.check_and_store(
        idempotency_key, ttl
    )

    if is_duplicate and cached:
        return PrepareInitializeResponse(**cached)

    try:
        result = await bridge_client.prepare_initialize(
            user_wallet=request_data.userWallet,
            max_balance=request_data.maxBalance,
        )

        await redis_store.store_result(idempotency_key, result)

        return PrepareInitializeResponse(**result)

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


@router.post(
    "/prepare-delegate-platform",
    response_model=PrepareDelegateResponse,
    status_code=status.HTTP_200_OK,
)
async def prepare_delegate_platform(
    request_data: PrepareDelegatePlatformRequest,
    req: Request,
):
    """
    Prepare delegate platform authority transaction.

    Allows platform to withdraw subscription fees.
    Idempotent (3 days) - security operation.
    """
    bridge_client = req.app.state.bridge_client
    redis_store = req.app.state.redis_store
    settings = get_settings()

    idempotency_key = (
        f"escrow:delegate-platform:{request_data.escrowAccount}"
    )
    ttl = settings.resilience.idempotency.security_operations * 86400

    is_duplicate, cached = await redis_store.check_and_store(
        idempotency_key, ttl
    )

    if is_duplicate and cached:
        return PrepareDelegateResponse(**cached)

    try:
        result = await bridge_client.prepare_delegate_platform(
            user_wallet=request_data.userWallet,
            escrow_account=request_data.escrowAccount,
            authority=request_data.authority,
        )

        await redis_store.store_result(idempotency_key, result)

        return PrepareDelegateResponse(**result)

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


@router.post(
    "/prepare-delegate-trading",
    response_model=PrepareDelegateResponse,
    status_code=status.HTTP_200_OK,
)
async def prepare_delegate_trading(
    request_data: PrepareDelegateTradingRequest,
    req: Request,
):
    """
    Prepare delegate trading authority transaction.

    Allows Chevalier to execute trades using escrow funds.
    Idempotent (3 days) - security operation.
    """
    bridge_client = req.app.state.bridge_client
    redis_store = req.app.state.redis_store
    settings = get_settings()

    idempotency_key = (
        f"escrow:delegate-trading:{request_data.escrowAccount}"
    )
    ttl = settings.resilience.idempotency.security_operations * 86400

    is_duplicate, cached = await redis_store.check_and_store(
        idempotency_key, ttl
    )

    if is_duplicate and cached:
        return PrepareDelegateResponse(**cached)

    try:
        result = await bridge_client.prepare_delegate_trading(
            user_wallet=request_data.userWallet,
            escrow_account=request_data.escrowAccount,
            authority=request_data.authority,
        )

        await redis_store.store_result(idempotency_key, result)

        return PrepareDelegateResponse(**result)

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


@router.post(
    "/prepare-revoke-platform",
    response_model=PrepareRevokeResponse,
    status_code=status.HTTP_200_OK,
)
async def prepare_revoke_platform(
    request_data: PrepareRevokeRequest,
    req: Request,
):
    """
    Prepare revoke platform authority transaction.

    Removes platform's ability to withdraw subscription fees.
    Idempotent (3 days) - security operation.
    """
    bridge_client = req.app.state.bridge_client
    redis_store = req.app.state.redis_store
    settings = get_settings()

    idempotency_key = (
        f"escrow:revoke-platform:{request_data.escrowAccount}"
    )
    ttl = settings.resilience.idempotency.security_operations * 86400

    is_duplicate, cached = await redis_store.check_and_store(
        idempotency_key, ttl
    )

    if is_duplicate and cached:
        return PrepareRevokeResponse(**cached)

    try:
        result = await bridge_client.prepare_revoke_platform(
            user_wallet=request_data.userWallet,
            escrow_account=request_data.escrowAccount,
        )

        await redis_store.store_result(idempotency_key, result)

        return PrepareRevokeResponse(**result)

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


@router.post(
    "/prepare-revoke-trading",
    response_model=PrepareRevokeResponse,
    status_code=status.HTTP_200_OK,
)
async def prepare_revoke_trading(
    request_data: PrepareRevokeRequest,
    req: Request,
):
    """
    Prepare revoke trading authority transaction.

    Removes Chevalier's ability to execute trades.
    Idempotent (3 days) - security operation.
    """
    bridge_client = req.app.state.bridge_client
    redis_store = req.app.state.redis_store
    settings = get_settings()

    idempotency_key = (
        f"escrow:revoke-trading:{request_data.escrowAccount}"
    )
    ttl = settings.resilience.idempotency.security_operations * 86400

    is_duplicate, cached = await redis_store.check_and_store(
        idempotency_key, ttl
    )

    if is_duplicate and cached:
        return PrepareRevokeResponse(**cached)

    try:
        result = await bridge_client.prepare_revoke_trading(
            user_wallet=request_data.userWallet,
            escrow_account=request_data.escrowAccount,
        )

        await redis_store.store_result(idempotency_key, result)

        return PrepareRevokeResponse(**result)

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


@router.post(
    "/prepare-deposit",
    response_model=PrepareDepositResponse,
    status_code=status.HTTP_200_OK,
)
async def prepare_deposit(
    request_data: PrepareDepositRequest,
    req: Request,
):
    """
    Prepare deposit transaction.

    User deposits USDC from wallet into escrow.
    Idempotent (7 days) - financial operation.
    """
    bridge_client = req.app.state.bridge_client
    redis_store = req.app.state.redis_store
    settings = get_settings()

    idempotency_key = (
        f"escrow:deposit:{request_data.escrowAccount}:"
        f"{request_data.amount}"
    )
    ttl = settings.resilience.idempotency.financial_operations * 86400

    is_duplicate, cached = await redis_store.check_and_store(
        idempotency_key, ttl
    )

    if is_duplicate and cached:
        return PrepareDepositResponse(**cached)

    try:
        result = await bridge_client.prepare_deposit(
            user_wallet=request_data.userWallet,
            escrow_account=request_data.escrowAccount,
            amount=request_data.amount,
        )

        await redis_store.store_result(idempotency_key, result)

        return PrepareDepositResponse(**result)

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


@router.post(
    "/prepare-withdraw",
    response_model=PrepareWithdrawResponse,
    status_code=status.HTTP_200_OK,
)
async def prepare_withdraw(
    request_data: PrepareWithdrawRequest,
    req: Request,
):
    """
    Prepare withdraw transaction.

    User withdraws funds from escrow back to wallet.
    Idempotent (7 days) - financial operation.
    """
    bridge_client = req.app.state.bridge_client
    redis_store = req.app.state.redis_store
    settings = get_settings()

    amount_key = (
        str(request_data.amount) if request_data.amount else "all"
    )
    idempotency_key = (
        f"escrow:withdraw:{request_data.escrowAccount}:{amount_key}"
    )
    ttl = settings.resilience.idempotency.financial_operations * 86400

    is_duplicate, cached = await redis_store.check_and_store(
        idempotency_key, ttl
    )

    if is_duplicate and cached:
        return PrepareWithdrawResponse(**cached)

    try:
        result = await bridge_client.prepare_withdraw(
            user_wallet=request_data.userWallet,
            escrow_account=request_data.escrowAccount,
            amount=request_data.amount,
        )

        await redis_store.store_result(idempotency_key, result)

        return PrepareWithdrawResponse(**result)

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


@router.post(
    "/prepare-close",
    response_model=PrepareCloseResponse,
    status_code=status.HTTP_200_OK,
)
async def prepare_close(
    request_data: PrepareCloseRequest,
    req: Request,
):
    """
    Prepare close escrow transaction.

    Closes escrow account and returns rent to user.
    Idempotent (7 days) - financial operation.
    """
    bridge_client = req.app.state.bridge_client
    redis_store = req.app.state.redis_store
    settings = get_settings()

    idempotency_key = f"escrow:close:{request_data.escrowAccount}"
    ttl = settings.resilience.idempotency.financial_operations * 86400

    is_duplicate, cached = await redis_store.check_and_store(
        idempotency_key, ttl
    )

    if is_duplicate and cached:
        return PrepareCloseResponse(**cached)

    try:
        result = await bridge_client.prepare_close(
            user_wallet=request_data.userWallet,
            escrow_account=request_data.escrowAccount,
        )

        await redis_store.store_result(idempotency_key, result)

        return PrepareCloseResponse(**result)

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
    "/{address}",
    response_model=EscrowDetailsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_escrow_details(
    address: str,
    req: Request,
):
    """
    Get escrow account details.

    Returns complete escrow account state.
    No idempotency (query operation).
    """
    bridge_client = req.app.state.bridge_client

    try:
        result = await bridge_client.get_escrow_details(address)
        return EscrowDetailsResponse(**result)

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
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Escrow account not found",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bridge error: {str(e)}",
        )


@router.get(
    "/balance/{account}",
    response_model=EscrowBalanceResponse,
    status_code=status.HTTP_200_OK,
)
async def get_escrow_balance(
    account: str,
    req: Request,
):
    """
    Get escrow token balance.

    Returns token balance in escrow.
    No idempotency (query operation).
    """
    bridge_client = req.app.state.bridge_client

    try:
        result = await bridge_client.get_escrow_balance(account)
        return EscrowBalanceResponse(**result)

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

"""
Subscription management API routes.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from pourtier.application.dto.subscription_dto import (
    CreateSubscriptionRequest,
    SubscriptionResponse,
    SubscriptionStatusResponse,
    UpdateSubscriptionRequest,
)
from pourtier.application.use_cases.create_subscription import (
    CreateSubscription,
    CreateSubscriptionCommand,
)
from pourtier.di.container import get_container
from pourtier.di.dependencies import (
    get_create_subscription,
    get_db_session,
)
from pourtier.domain.entities.user import User
from pourtier.domain.exceptions.payment import InsufficientFundsError
from pourtier.presentation.api.middleware.auth import get_current_user

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post(
    "/",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new subscription",
    description="Create a new subscription for the authenticated user",
)
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    create_subscription_use_case: CreateSubscription = Depends(get_create_subscription),
) -> SubscriptionResponse:
    """
    Create a new subscription.

    Payment is automatically deducted from user's escrow balance.
    Maps API request DTO to domain command, executes use case,
    and returns response DTO.
    """
    try:
        # Map DTO (presentation) → Domain Command (application)
        command = CreateSubscriptionCommand(
            user_id=current_user.id,
            plan_type=request.plan_type,
        )

        subscription = await create_subscription_use_case.execute(command)

        # Map Domain Entity → Response DTO
        return SubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            plan_type=subscription.plan_type.value,
            status=subscription.status.value,
            started_at=subscription.started_at,
            expires_at=subscription.expires_at,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
        )

    except InsufficientFundsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Subscription creation failed: {str(e)}",
        )


@router.get(
    "/",
    response_model=List[SubscriptionResponse],
    summary="Get user subscriptions",
    description="Get all subscriptions for the authenticated user",
)
async def get_user_subscriptions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> List[SubscriptionResponse]:
    """Get all subscriptions for current user."""
    try:
        container = get_container()
        subscription_repo = container.get_subscription_repository(session)

        subscriptions = await subscription_repo.list_by_user(current_user.id)

        return [
            SubscriptionResponse(
                id=sub.id,
                user_id=sub.user_id,
                plan_type=sub.plan_type.value,
                status=sub.status.value,
                started_at=sub.started_at,
                expires_at=sub.expires_at,
                created_at=sub.created_at,
                updated_at=sub.updated_at,
            )
            for sub in subscriptions
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch subscriptions: {str(e)}",
        )


@router.get(
    "/check",
    response_model=SubscriptionStatusResponse,
    summary="Check subscription validity",
    description="Check if user has an active subscription",
)
async def check_subscription_status(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SubscriptionStatusResponse:
    """Check if user has active subscription."""
    try:
        container = get_container()
        subscription_repo = container.get_subscription_repository(session)

        active_subscription = await subscription_repo.get_active_by_user(
            current_user.id
        )

        return SubscriptionStatusResponse(
            has_active_subscription=active_subscription is not None,
            current_plan=(
                active_subscription.plan_type.value if active_subscription else None
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check subscription: {str(e)}",
        )


@router.get(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
    summary="Get subscription by ID",
    description="Get a specific subscription by ID",
)
async def get_subscription_by_id(
    subscription_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SubscriptionResponse:
    """Get subscription by ID with ownership verification."""
    try:
        container = get_container()
        subscription_repo = container.get_subscription_repository(session)

        subscription = await subscription_repo.get_by_id(subscription_id)

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )

        # Verify ownership
        if subscription.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this subscription",
            )

        return SubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            plan_type=subscription.plan_type.value,
            status=subscription.status.value,
            started_at=subscription.started_at,
            expires_at=subscription.expires_at,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch subscription: {str(e)}",
        )


@router.patch(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
    summary="Update subscription",
    description="Update subscription status (cancel, expire)",
)
async def update_subscription(
    subscription_id: UUID,
    request: UpdateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SubscriptionResponse:
    """Update subscription status with ownership verification."""
    try:
        container = get_container()
        subscription_repo = container.get_subscription_repository(session)

        subscription = await subscription_repo.get_by_id(subscription_id)

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )

        # Verify ownership
        if subscription.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this subscription",
            )

        # Update status using domain methods
        if request.status == "cancelled":
            subscription.cancel()
        elif request.status == "expired":
            subscription.expire()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {request.status}",
            )

        # Persist changes
        await subscription_repo.update(subscription)

        return SubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            plan_type=subscription.plan_type.value,
            status=subscription.status.value,
            started_at=subscription.started_at,
            expires_at=subscription.expires_at,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update subscription: {str(e)}",
        )

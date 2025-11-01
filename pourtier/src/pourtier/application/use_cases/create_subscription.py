"""
Create subscription use case.

Handles subscription creation for escrow-based billing.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from pourtier.domain.entities.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)
from pourtier.domain.exceptions.payment import InsufficientFundsError
from pourtier.domain.repositories.i_subscription_repository import (
    ISubscriptionRepository,
)
from pourtier.domain.repositories.i_user_repository import IUserRepository
from pourtier.domain.services.i_escrow_query_service import IEscrowQueryService
from pourtier.domain.value_objects.subscription_plan import (
    get_plan_details,
)
from pourtier.infrastructure.blockchain.solana_utils import derive_escrow_pda


@dataclass
class CreateSubscriptionCommand:
    """Command to create subscription."""

    user_id: UUID
    plan_type: str


class CreateSubscription:
    """
    Use case for creating new subscription with escrow balance check.

    Flow:
    1. Validate plan type
    2. Check user doesn't have active subscription
    3. Check user has initialized escrow on blockchain
    4. Check sufficient escrow balance for first payment
    5. Create subscription entity
    6. Return subscription (billing handled separately by cron)

    Architecture:
    - Check blockchain for escrow existence (not DB)
    """

    def __init__(
        self,
        subscription_repository: ISubscriptionRepository,
        user_repository: IUserRepository,
        escrow_query_service: IEscrowQueryService,
        program_id: str,
    ):
        """
        Initialize use case.

        Args:
            subscription_repository: Subscription repository
            user_repository: User repository for balance check
            escrow_query_service: Service for querying blockchain
            program_id: Escrow program ID for PDA derivation
        """
        self.subscription_repository = subscription_repository
        self.user_repository = user_repository
        self.escrow_query_service = escrow_query_service
        self.program_id = program_id

    async def execute(self, command: CreateSubscriptionCommand) -> Subscription:
        """
        Create subscription with escrow balance validation.

        Args:
            command: Command with subscription details

        Returns:
            Created subscription entity

        Raises:
            ValueError: If plan type is invalid or user has active subscription
            InsufficientFundsError: If insufficient escrow balance
            EntityNotFoundError: If user not found
        """
        # Get plan details
        plan_details = get_plan_details(command.plan_type)

        # Get user and check escrow
        user = await self.user_repository.get_by_id(command.user_id)
        if not user:
            from pourtier.domain.exceptions import EntityNotFoundError

            raise EntityNotFoundError("User", str(command.user_id))

        # Check if user already has active subscription
        existing_subscription = await self.subscription_repository.get_active_by_user(
            command.user_id
        )
        if existing_subscription:
            raise ValueError(
                f"User already has an active subscription "
                f"({existing_subscription.plan_type.value}). "
                f"Please cancel the current subscription before creating a new one."
            )

        # Derive escrow account
        escrow_account, _ = derive_escrow_pda(
            user.wallet_address,
            self.program_id,
        )

        # Check blockchain if escrow exists
        escrow_exists = await self.escrow_query_service.check_escrow_exists(
            escrow_account
        )

        if not escrow_exists:
            raise ValueError("User must initialize escrow before subscribing")

        # Check sufficient balance for first payment
        if user.escrow_balance < plan_details.price:
            raise InsufficientFundsError(
                f"Insufficient escrow balance. Required: "
                f"{plan_details.price} USDC, "
                f"Available: {user.escrow_balance} USDC"
            )

        # Calculate expiration date
        expires_at = None
        if plan_details.duration_days:
            expires_at = datetime.now() + timedelta(days=plan_details.duration_days)

        # Create subscription entity
        subscription = Subscription(
            user_id=command.user_id,
            plan_type=SubscriptionPlan(command.plan_type),
            status=SubscriptionStatus.ACTIVE,
            started_at=datetime.now(),
            expires_at=expires_at,
        )

        # Save subscription
        created_subscription = await self.subscription_repository.create(subscription)

        # Note: First payment will be deducted by billing cron job
        # or immediately after subscription creation by a separate
        # ProcessSubscriptionBilling use case

        return created_subscription

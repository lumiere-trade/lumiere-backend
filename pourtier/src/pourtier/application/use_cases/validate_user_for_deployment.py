"""
Validate User For Deployment use case.

Validates if user can deploy strategies to Chevalier.
"""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from pourtier.domain.entities.subscription import SubscriptionStatus
from pourtier.domain.exceptions import EntityNotFoundError
from pourtier.domain.repositories.i_subscription_repository import (
    ISubscriptionRepository,
)
from pourtier.domain.repositories.i_user_repository import IUserRepository
from pourtier.domain.services.i_escrow_query_service import IEscrowQueryService
from pourtier.infrastructure.blockchain.solana_utils import derive_escrow_pda


@dataclass
class UserDeploymentValidation:
    """Result of user deployment validation."""

    user_id: UUID
    wallet_address: str
    is_valid: bool
    has_subscription: bool
    subscription_plan: str | None
    subscription_status: str | None
    has_escrow: bool
    escrow_account: str
    escrow_balance: Decimal
    can_deploy: bool
    validation_errors: list[str]


class ValidateUserForDeployment:
    """
    Validate user for strategy deployment.

    Business rules:
    - User must exist
    - User must have active subscription
    - User must have initialized escrow on blockchain
    - User must have balance > 0

    Architecture:
    - Check blockchain for escrow existence (not DB)
    - Derive escrow account on-the-fly

    This endpoint is called by Chevalier to validate deployment requests.
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        subscription_repository: ISubscriptionRepository,
        escrow_query_service: IEscrowQueryService,
        program_id: str,
    ):
        """
        Initialize use case with dependencies.

        Args:
            user_repository: Repository for user persistence
            subscription_repository: Repository for subscriptions
            escrow_query_service: Service for querying blockchain
            program_id: Escrow program ID for PDA derivation
        """
        self.user_repository = user_repository
        self.subscription_repository = subscription_repository
        self.escrow_query_service = escrow_query_service
        self.program_id = program_id

    async def execute(self, user_id: UUID) -> UserDeploymentValidation:
        """
        Execute validation for user deployment.

        Args:
            user_id: User unique identifier

        Returns:
            UserDeploymentValidation with detailed status

        Raises:
            EntityNotFoundError: If user not found
        """
        validation_errors = []

        # 1. Get user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError(
                entity_type="User",
                entity_id=str(user_id),
            )

        # 2. Check subscription
        has_subscription = False
        subscription_plan = None
        subscription_status_str = None

        subscription = await self.subscription_repository.get_active_by_user(user_id)

        if subscription:
            has_subscription = True
            subscription_plan = subscription.plan_type.value
            subscription_status_str = subscription.status.value

            if subscription.status != SubscriptionStatus.ACTIVE:
                validation_errors.append(
                    f"Subscription is not active: {subscription.status.value}"
                )
        else:
            validation_errors.append("No active subscription found")

        # 3. Derive escrow account
        escrow_account, _ = derive_escrow_pda(
            user.wallet_address,
            self.program_id,
        )

        # 4. Check blockchain if escrow exists
        has_escrow = await self.escrow_query_service.check_escrow_exists(
            escrow_account
        )

        if not has_escrow:
            validation_errors.append("Escrow not initialized")

        # 5. Check escrow balance (from DB cache)
        escrow_balance = user.escrow_balance if has_escrow else Decimal("0")

        if has_escrow and escrow_balance <= 0:
            validation_errors.append(f"Insufficient escrow balance: {escrow_balance}")

        # 6. Determine if can deploy
        can_deploy = (
            has_subscription
            and subscription
            and subscription.status == SubscriptionStatus.ACTIVE
            and has_escrow
            and escrow_balance > 0
        )

        # 7. Build validation result
        return UserDeploymentValidation(
            user_id=user_id,
            wallet_address=user.wallet_address,
            is_valid=can_deploy,
            has_subscription=has_subscription,
            subscription_plan=subscription_plan,
            subscription_status=subscription_status_str,
            has_escrow=has_escrow,
            escrow_account=escrow_account,  # Always computed
            escrow_balance=escrow_balance,
            can_deploy=can_deploy,
            validation_errors=validation_errors,
        )

"""
Subscription repository implementation using SQLAlchemy.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pourtier.domain.entities.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)
from pourtier.domain.exceptions import EntityNotFoundError
from pourtier.domain.repositories.i_subscription_repository import (
    ISubscriptionRepository,
)
from pourtier.infrastructure.persistence.models import SubscriptionModel


class SubscriptionRepository(ISubscriptionRepository):
    """
    SQLAlchemy implementation of subscription repository.

    Handles Subscription entity persistence in PostgreSQL.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(self, subscription: Subscription) -> Subscription:
        """
        Create a new subscription in the database.

        Args:
            subscription: Subscription entity to persist

        Returns:
            Created subscription with database-generated ID
        """
        model = SubscriptionModel(
            id=subscription.id,
            user_id=subscription.user_id,
            plan_type=subscription.plan_type.value,
            status=subscription.status.value,
            started_at=subscription.started_at,
            expires_at=subscription.expires_at,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
        )

        self.session.add(model)
        await self.session.flush()

        return self._to_entity(model)

    async def get_by_id(self, subscription_id: UUID) -> Optional[Subscription]:
        """
        Retrieve subscription by ID.

        Args:
            subscription_id: Subscription unique identifier

        Returns:
            Subscription entity if found, None otherwise
        """
        stmt = select(SubscriptionModel).where(SubscriptionModel.id == subscription_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        return self._to_entity(model) if model else None

    async def get_active_by_user(self, user_id: UUID) -> Optional[Subscription]:
        """
        Retrieve active subscription for user.

        Returns most recent active subscription if multiple exist.

        Args:
            user_id: User unique identifier

        Returns:
            Active subscription if found, None otherwise
        """
        stmt = (
            select(SubscriptionModel)
            .where(SubscriptionModel.user_id == user_id)
            .where(SubscriptionModel.status == "active")
            .order_by(SubscriptionModel.created_at.desc())
            .limit(1)  # Fix: Return only most recent active subscription
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        return self._to_entity(model) if model else None

    async def update(self, subscription: Subscription) -> Subscription:
        """
        Update existing subscription in database.

        Args:
            subscription: Subscription entity with updated fields

        Returns:
            Updated subscription entity

        Raises:
            EntityNotFoundError: If subscription not found
        """
        stmt = select(SubscriptionModel).where(SubscriptionModel.id == subscription.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise EntityNotFoundError("Subscription", str(subscription.id))

        # Update fields
        model.plan_type = subscription.plan_type.value
        model.status = subscription.status.value
        model.expires_at = subscription.expires_at
        model.updated_at = subscription.updated_at

        await self.session.flush()

        return self._to_entity(model)

    async def list_by_user(self, user_id: UUID) -> list[Subscription]:
        """
        List all subscriptions for user (active and inactive).

        Args:
            user_id: User unique identifier

        Returns:
            List of subscription entities
        """
        stmt = (
            select(SubscriptionModel)
            .where(SubscriptionModel.user_id == user_id)
            .order_by(SubscriptionModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    def _to_entity(self, model: SubscriptionModel) -> Subscription:
        """Convert ORM model to domain entity."""
        return Subscription(
            id=model.id,
            user_id=model.user_id,
            plan_type=SubscriptionPlan(model.plan_type),
            status=SubscriptionStatus(model.status),
            started_at=model.started_at,
            expires_at=model.expires_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

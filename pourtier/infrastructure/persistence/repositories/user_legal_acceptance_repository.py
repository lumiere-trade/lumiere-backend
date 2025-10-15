"""
User Legal Acceptance repository implementation.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pourtier.domain.entities.user_legal_acceptance import (
    AcceptanceMethod,
    UserLegalAcceptance,
)
from pourtier.domain.repositories.i_user_legal_acceptance_repository import (
    IUserLegalAcceptanceRepository,
)
from pourtier.infrastructure.persistence.models import (
    UserLegalAcceptanceModel,
)


class UserLegalAcceptanceRepository(IUserLegalAcceptanceRepository):
    """SQLAlchemy implementation of user legal acceptance repository."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(self, acceptance: UserLegalAcceptance) -> UserLegalAcceptance:
        """
        Create new user legal acceptance in database.

        Args:
            acceptance: UserLegalAcceptance entity to create

        Returns:
            Created user legal acceptance entity
        """
        model = UserLegalAcceptanceModel(
            id=acceptance.id,
            user_id=acceptance.user_id,
            document_id=acceptance.document_id,
            accepted_at=acceptance.accepted_at,
            acceptance_method=acceptance.acceptance_method.value,
            ip_address=acceptance.ip_address,
            user_agent=acceptance.user_agent,
            created_at=acceptance.created_at,
        )

        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)

        return self._to_entity(model)

    async def get_by_id(self, acceptance_id: UUID) -> Optional[UserLegalAcceptance]:
        """
        Get user legal acceptance by ID.

        Args:
            acceptance_id: Acceptance unique identifier

        Returns:
            UserLegalAcceptance entity if found, None otherwise
        """
        stmt = select(UserLegalAcceptanceModel).where(
            UserLegalAcceptanceModel.id == acceptance_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        return self._to_entity(model) if model else None

    async def get_by_user_and_document(
        self, user_id: UUID, document_id: UUID
    ) -> Optional[UserLegalAcceptance]:
        """
        Get user legal acceptance by user and document.

        Args:
            user_id: User unique identifier
            document_id: Document unique identifier

        Returns:
            UserLegalAcceptance entity if found, None otherwise
        """
        stmt = select(UserLegalAcceptanceModel).where(
            UserLegalAcceptanceModel.user_id == user_id,
            UserLegalAcceptanceModel.document_id == document_id,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        return self._to_entity(model) if model else None

    async def get_all_by_user(self, user_id: UUID) -> List[UserLegalAcceptance]:
        """
        Get all legal acceptances for a user.

        Args:
            user_id: User unique identifier

        Returns:
            List of UserLegalAcceptance entities
        """
        stmt = (
            select(UserLegalAcceptanceModel)
            .where(UserLegalAcceptanceModel.user_id == user_id)
            .order_by(UserLegalAcceptanceModel.accepted_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def get_all_by_document(self, document_id: UUID) -> List[UserLegalAcceptance]:
        """
        Get all user acceptances for a document.

        Args:
            document_id: Document unique identifier

        Returns:
            List of UserLegalAcceptance entities
        """
        stmt = (
            select(UserLegalAcceptanceModel)
            .where(UserLegalAcceptanceModel.document_id == document_id)
            .order_by(UserLegalAcceptanceModel.accepted_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def delete(self, acceptance_id: UUID) -> bool:
        """
        Delete user legal acceptance by ID.

        Args:
            acceptance_id: Acceptance unique identifier

        Returns:
            True if deleted, False if not found
        """
        stmt = select(UserLegalAcceptanceModel).where(
            UserLegalAcceptanceModel.id == acceptance_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return False

        await self.session.delete(model)
        await self.session.flush()

        return True

    def _to_entity(self, model: UserLegalAcceptanceModel) -> UserLegalAcceptance:
        """
        Convert UserLegalAcceptanceModel to UserLegalAcceptance entity.

        Args:
            model: SQLAlchemy model

        Returns:
            UserLegalAcceptance domain entity
        """
        return UserLegalAcceptance(
            id=model.id,
            user_id=model.user_id,
            document_id=model.document_id,
            accepted_at=model.accepted_at,
            acceptance_method=AcceptanceMethod(model.acceptance_method),
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            created_at=model.created_at,
        )

"""
User repository implementation with multi-layer caching.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from pourtier.domain.entities.user import User
from pourtier.domain.repositories.i_user_repository import IUserRepository
from pourtier.infrastructure.cache.multi_layer_cache import MultiLayerCache
from pourtier.infrastructure.persistence.models import UserModel


class UserRepository(IUserRepository):
    """
    SQLAlchemy implementation of user repository with caching.

    Cache strategy:
    - get_by_wallet: Cached (most frequent lookup)
    - get_by_id: Cached (profile queries)
    - create/update: Invalidates cache
    """

    def __init__(
        self,
        session: AsyncSession,
        cache: Optional[MultiLayerCache] = None,
    ):
        """
        Initialize repository with database session and optional cache.

        Args:
            session: SQLAlchemy async session
            cache: Optional multi-layer cache instance
        """
        self.session = session
        self.cache = cache

    async def create(self, user: User) -> User:
        """
        Create new user in database.

        Args:
            user: User entity to create

        Returns:
            Created user entity
        """
        model = UserModel(
            id=user.id,
            wallet_address=user.wallet_address,
            escrow_account=user.escrow_account,
            escrow_balance=user.escrow_balance,
            escrow_token_mint=user.escrow_token_mint,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)

        # Invalidate cache for this user
        if self.cache:
            await self._invalidate_user_cache(user.id, user.wallet_address)

        return self._to_entity(model)

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID with caching.

        Args:
            user_id: User unique identifier

        Returns:
            User entity if found, None otherwise
        """
        cache_key = f"id:{user_id}"

        # Try cache first
        if self.cache:
            cached = await self.cache.get(
                cache_key,
                fetch_func=lambda: self._fetch_by_id(user_id),
                key_prefix="user",
            )
            return cached

        # No cache - fetch directly
        return await self._fetch_by_id(user_id)

    async def _fetch_by_id(self, user_id: UUID) -> Optional[User]:
        """Fetch user by ID from database."""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_id_with_subscriptions(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID with subscriptions eager loaded.

        Not cached - complex query with relationships.

        Args:
            user_id: User unique identifier

        Returns:
            User entity with subscriptions loaded, None if not found
        """
        stmt = (
            select(UserModel)
            .where(UserModel.id == user_id)
            .options(selectinload(UserModel.subscriptions))
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        return self._to_entity(model) if model else None

    async def get_by_id_with_escrow_transactions(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID with escrow transactions eager loaded.

        Not cached - complex query with relationships.

        Args:
            user_id: User unique identifier

        Returns:
            User entity with transactions loaded, None if not found
        """
        stmt = (
            select(UserModel)
            .where(UserModel.id == user_id)
            .options(selectinload(UserModel.escrow_transactions))
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        return self._to_entity(model) if model else None

    async def get_by_wallet(self, wallet_address: str) -> Optional[User]:
        """
        Get user by wallet address with caching.

        Most frequently used query - heavily cached.

        Args:
            wallet_address: Wallet address

        Returns:
            User entity if found, None otherwise
        """
        cache_key = f"wallet:{wallet_address}"

        # Try cache first
        if self.cache:
            cached = await self.cache.get(
                cache_key,
                fetch_func=lambda: self._fetch_by_wallet(wallet_address),
                key_prefix="user",
            )
            return cached

        # No cache - fetch directly
        return await self._fetch_by_wallet(wallet_address)

    async def _fetch_by_wallet(self, wallet_address: str) -> Optional[User]:
        """Fetch user by wallet from database."""
        stmt = select(UserModel).where(UserModel.wallet_address == wallet_address)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_all_with_escrow(self) -> list[User]:
        """
        List all users with escrow accounts.

        Not cached - bulk query.

        Returns:
            List of users who have initialized escrow
        """
        stmt = select(UserModel).where(UserModel.escrow_account.isnot(None))
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def update(self, user: User) -> User:
        """
        Update existing user.

        Args:
            user: User entity with updated data

        Returns:
            Updated user entity
        """
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"User {user.id} not found")

        # Update fields
        model.wallet_address = user.wallet_address
        model.escrow_account = user.escrow_account
        model.escrow_balance = user.escrow_balance
        model.escrow_token_mint = user.escrow_token_mint
        model.updated_at = user.updated_at

        await self.session.flush()
        await self.session.refresh(model)

        # Invalidate cache for this user
        if self.cache:
            await self._invalidate_user_cache(user.id, user.wallet_address)

        return self._to_entity(model)

    async def delete(self, user_id: UUID) -> bool:
        """
        Delete user by ID.

        Args:
            user_id: User unique identifier

        Returns:
            True if deleted, False if not found
        """
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return False

        # Invalidate cache before delete
        if self.cache:
            await self._invalidate_user_cache(user_id, model.wallet_address)

        await self.session.delete(model)
        await self.session.flush()

        return True

    async def _invalidate_user_cache(self, user_id: UUID, wallet_address: str) -> None:
        """
        Invalidate all cache entries for a user.

        Args:
            user_id: User ID
            wallet_address: User wallet address
        """
        if not self.cache:
            return

        # Invalidate by ID
        await self.cache.delete(f"id:{user_id}", key_prefix="user")

        # Invalidate by wallet
        await self.cache.delete(f"wallet:{wallet_address}", key_prefix="user")

    def _to_entity(self, model: UserModel) -> User:
        """
        Convert UserModel to User entity.

        Args:
            model: SQLAlchemy model

        Returns:
            User domain entity
        """
        return User(
            id=model.id,
            wallet_address=model.wallet_address,
            escrow_account=model.escrow_account,
            escrow_balance=model.escrow_balance,
            escrow_token_mint=model.escrow_token_mint,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

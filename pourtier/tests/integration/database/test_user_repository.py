"""
Integration tests for UserRepository with real PostgreSQL.

Tests CRUD operations for immutable User identity.

Usage:
    laborant pourtier --integration
"""

import base58
import os
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from pourtier.config.settings import get_settings
from pourtier.domain.entities.user import User
from pourtier.domain.exceptions import EntityNotFoundError
from pourtier.infrastructure.persistence.database import Database
from pourtier.infrastructure.persistence.models import Base
from pourtier.infrastructure.persistence.repositories.user_repository import (
    UserRepository,
)
from shared.tests import LaborantTest


class TestUserRepository(LaborantTest):
    """Integration tests for UserRepository."""

    component_name = "pourtier"
    test_category = "integration"

    db: Database = None

    async def async_setup(self):
        """Setup test database."""
        self.reporter.info("Setting up test database...", context="Setup")

        settings = get_settings()
        self.reporter.info(f"Loaded ENV={settings.ENV}", context="Setup")

        TestUserRepository.db = Database(database_url=settings.DATABASE_URL, echo=False)
        await TestUserRepository.db.connect()
        self.reporter.info("Connected to test database", context="Setup")

        # Reset database schema using public method
        await TestUserRepository.db.reset_schema_for_testing(Base.metadata)
        self.reporter.info("Database schema reset", context="Setup")

        self.reporter.info("Test database ready", context="Setup")

    async def async_teardown(self):
        """Cleanup test database."""
        self.reporter.info("Cleaning up test database...", context="Teardown")

        if TestUserRepository.db:
            await TestUserRepository.db.disconnect()

        self.reporter.info("Cleanup complete", context="Teardown")

    def _generate_unique_wallet(self) -> str:
        """
        Generate valid Solana wallet address.

        Solana wallet addresses are 32 bytes encoded as Base58.
        """
        random_bytes = os.urandom(32)
        return base58.b58encode(random_bytes).decode('ascii')

    async def test_create_user(self):
        """Test creating a new user."""
        self.reporter.info("Testing user creation", context="Test")

        async with self.db.session() as session:
            repo = UserRepository(session)
            user = User(wallet_address=self._generate_unique_wallet())
            created_user = await repo.create(user)

            assert created_user.id is not None
            assert created_user.wallet_address == user.wallet_address
            assert created_user.created_at is not None

            self.reporter.info(f"User created: {created_user.id}", context="Test")

    async def test_get_user_by_id(self):
        """Test retrieving user by ID."""
        self.reporter.info("Testing get user by ID", context="Test")

        async with self.db.session() as session:
            repo = UserRepository(session)
            user = User(wallet_address=self._generate_unique_wallet())
            created_user = await repo.create(user)

        async with self.db.session() as session:
            repo = UserRepository(session)
            retrieved_user = await repo.get_by_id(created_user.id)

            assert retrieved_user is not None
            assert retrieved_user.id == created_user.id
            assert retrieved_user.wallet_address == created_user.wallet_address

            self.reporter.info("User retrieved successfully", context="Test")

    async def test_get_user_by_wallet(self):
        """Test retrieving user by wallet address."""
        self.reporter.info("Testing get user by wallet", context="Test")

        wallet = self._generate_unique_wallet()

        async with self.db.session() as session:
            repo = UserRepository(session)
            user = User(wallet_address=wallet)
            await repo.create(user)

        async with self.db.session() as session:
            repo = UserRepository(session)
            retrieved_user = await repo.get_by_wallet(wallet)

            assert retrieved_user is not None
            assert retrieved_user.wallet_address == wallet

            self.reporter.info("User found by wallet", context="Test")

    async def test_get_nonexistent_user(self):
        """Test retrieving non-existent user returns None."""
        self.reporter.info("Testing get non-existent user", context="Test")

        async with self.db.session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_id(uuid4())

            assert user is None

            self.reporter.info("Non-existent user handled correctly", context="Test")

    async def test_duplicate_wallet_error(self):
        """Test that creating duplicate wallet raises error."""
        self.reporter.info("Testing duplicate wallet error", context="Test")

        wallet = self._generate_unique_wallet()

        async with self.db.session() as session:
            repo = UserRepository(session)
            user1 = User(wallet_address=wallet)
            await repo.create(user1)

        try:
            async with self.db.session() as session:
                repo = UserRepository(session)
                user2 = User(wallet_address=wallet)
                await repo.create(user2)
            assert False, "Should raise IntegrityError"
        except IntegrityError:
            self.reporter.info(
                "Duplicate wallet error raised correctly", context="Test"
            )

    async def test_update_nonexistent_user(self):
        """Test updating non-existent user raises error."""
        self.reporter.info("Testing update non-existent user", context="Test")

        async with self.db.session() as session:
            repo = UserRepository(session)
            user = User(
                id=uuid4(),
                wallet_address=self._generate_unique_wallet(),
            )

            try:
                await repo.update(user)
                assert False, "Should raise EntityNotFoundError"
            except (EntityNotFoundError, ValueError):
                self.reporter.info(
                    "Update non-existent user error raised", context="Test"
                )


if __name__ == "__main__":
    TestUserRepository.run_as_main()

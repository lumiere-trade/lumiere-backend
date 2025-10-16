"""
Integration tests for UserRepository with real PostgreSQL.

Tests CRUD operations on test database.

Usage:
    python -m pourtier.tests.integration.database.test_user_repository
    laborant pourtier --integration
"""

from decimal import Decimal
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from pourtier.config.settings import load_config
from pourtier.domain.entities.user import User
from pourtier.domain.exceptions import EntityNotFoundError
from pourtier.infrastructure.persistence.database import Database
from pourtier.infrastructure.persistence.models import Base
from pourtier.infrastructure.persistence.repositories.user_repository import (
    UserRepository,
)
from shared.tests import LaborantTest

# Load test configuration
test_settings = load_config("development.yaml", env="development")
TEST_DATABASE_URL = test_settings.DATABASE_URL


class TestUserRepository(LaborantTest):
    """Integration tests for UserRepository."""

    component_name = "pourtier"
    test_category = "integration"

    # Class-level shared resources
    db: Database = None

    # ================================================================
    # Async Lifecycle Hooks
    # ================================================================

    async def async_setup(self):
        """Setup test database (runs once before all tests)."""
        self.reporter.info("Setting up test database...", context="Setup")
        self.reporter.info(f"Database: {TEST_DATABASE_URL}", context="Setup")

        # Drop and recreate tables
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

        # Connect database
        TestUserRepository.db = Database(database_url=TEST_DATABASE_URL, echo=False)
        await TestUserRepository.db.connect()

        self.reporter.info("Test database ready", context="Setup")

    async def async_teardown(self):
        """Cleanup test database (runs once after all tests)."""
        self.reporter.info("Cleaning up test database...", context="Teardown")

        if TestUserRepository.db:
            await TestUserRepository.db.disconnect()

        # Drop all tables
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

        self.reporter.info("Cleanup complete", context="Teardown")

    # ================================================================
    # Helper Methods
    # ================================================================

    def _generate_unique_wallet(self) -> str:
        """Generate unique 44-character wallet address."""
        unique_id = str(uuid4()).replace("-", "")
        return unique_id.ljust(44, "0")

    # ================================================================
    # Test Methods
    # ================================================================

    async def test_create_user(self):
        """Test creating a new user."""
        self.reporter.info("Testing user creation", context="Test")

        async with self.db.session() as session:
            repo = UserRepository(session)

            user = User(wallet_address=self._generate_unique_wallet())

            created_user = await repo.create(user)

            assert created_user.id is not None
            assert created_user.wallet_address == user.wallet_address

            self.reporter.info(f"User created: {created_user.id}", context="Test")

    async def test_get_user_by_id(self):
        """Test retrieving user by ID."""
        self.reporter.info("Testing get user by ID", context="Test")

        # Create user
        async with self.db.session() as session:
            repo = UserRepository(session)
            user = User(wallet_address=self._generate_unique_wallet())
            created_user = await repo.create(user)

        # Retrieve by ID
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

        # Create user
        async with self.db.session() as session:
            repo = UserRepository(session)
            user = User(wallet_address=wallet)
            await repo.create(user)

        # Retrieve by wallet
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

    async def test_update_user(self):
        """Test updating user information."""
        self.reporter.info("Testing user update", context="Test")

        # Create user
        async with self.db.session() as session:
            repo = UserRepository(session)
            user = User(wallet_address=self._generate_unique_wallet())
            created_user = await repo.create(user)

        # Update user escrow balance
        async with self.db.session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_id(created_user.id)

            # Initialize escrow first
            user.initialize_escrow(escrow_account="EscrowTest123", token_mint="USDC")
            user.update_escrow_balance(Decimal("100.0"))

            updated_user = await repo.update(user)

            assert updated_user.escrow_balance == Decimal("100.0")

            self.reporter.info("User updated successfully", context="Test")

    async def test_duplicate_wallet_error(self):
        """Test that creating duplicate wallet raises error."""
        self.reporter.info("Testing duplicate wallet error", context="Test")

        wallet = self._generate_unique_wallet()

        # Create first user in separate session
        async with self.db.session() as session:
            repo = UserRepository(session)
            user1 = User(wallet_address=wallet)
            await repo.create(user1)
            # Session auto-commits on exit

        # Try to create second user with same wallet in NEW session
        try:
            async with self.db.session() as session:
                repo = UserRepository(session)
                user2 = User(wallet_address=wallet)
                await repo.create(user2)
                # This should fail before commit
            assert False, "Should raise IntegrityError"
        except IntegrityError:
            self.reporter.info(
                "Duplicate wallet error raised correctly",
                context="Test",
            )

    async def test_update_nonexistent_user(self):
        """Test updating non-existent user raises error."""
        self.reporter.info("Testing update non-existent user", context="Test")

        async with self.db.session() as session:
            repo = UserRepository(session)

            # Create user that doesn't exist in DB
            user = User(
                id=uuid4(),
                wallet_address=self._generate_unique_wallet(),
            )

            try:
                await repo.update(user)
                assert False, "Should raise EntityNotFoundError"
            except (EntityNotFoundError, ValueError):
                self.reporter.info(
                    "Update non-existent user error raised",
                    context="Test",
                )

    # ================================================================
    # Escrow Tests
    # ================================================================

    async def test_update_user_escrow_balance(self):
        """Test updating user escrow balance."""
        self.reporter.info("Testing update escrow balance", context="Test")

        # Create user
        async with self.db.session() as session:
            repo = UserRepository(session)
            user = User(wallet_address=self._generate_unique_wallet())
            created_user = await repo.create(user)

        # Initialize escrow and update balance
        async with self.db.session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_id(created_user.id)

            user.initialize_escrow(
                escrow_account="EscrowPDA123456789012345678901234",
                token_mint="USDC",
            )
            user.update_escrow_balance(Decimal("500.50"))

            updated_user = await repo.update(user)

            assert updated_user.escrow_account == ("EscrowPDA123456789012345678901234")
            assert updated_user.escrow_balance == Decimal("500.50")
            assert updated_user.escrow_token_mint == "USDC"

            self.reporter.info("Escrow balance updated", context="Test")

    async def test_initialize_user_escrow(self):
        """Test initializing user escrow account."""
        self.reporter.info("Testing initialize escrow", context="Test")

        # Create user without escrow
        async with self.db.session() as session:
            repo = UserRepository(session)
            user = User(wallet_address=self._generate_unique_wallet())
            created_user = await repo.create(user)

            assert created_user.escrow_account is None
            assert created_user.escrow_balance == Decimal("0")

        # Initialize escrow
        async with self.db.session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_id(created_user.id)

            escrow_pda = "EscrowPDA987654321098765432109876543210"
            user.initialize_escrow(escrow_account=escrow_pda, token_mint="SOL")

            updated_user = await repo.update(user)

            assert updated_user.escrow_account == escrow_pda
            assert updated_user.escrow_token_mint == "SOL"

            self.reporter.info("Escrow initialized", context="Test")

    async def test_user_has_sufficient_balance(self):
        """Test checking if user has sufficient escrow balance."""
        self.reporter.info("Testing has sufficient balance", context="Test")

        # Create user with escrow balance
        async with self.db.session() as session:
            repo = UserRepository(session)
            user = User(wallet_address=self._generate_unique_wallet())
            created_user = await repo.create(user)

        # Set escrow balance
        async with self.db.session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_id(created_user.id)

            user.initialize_escrow(escrow_account="EscrowTest123456789012345678901234")
            user.update_escrow_balance(Decimal("1000.0"))

            updated_user = await repo.update(user)

            # Test sufficient balance
            assert updated_user.has_sufficient_balance(Decimal("500.0"))
            assert updated_user.has_sufficient_balance(Decimal("1000.0"))
            assert not updated_user.has_sufficient_balance(Decimal("1500.0"))

            self.reporter.info("Balance check working correctly", context="Test")

    async def test_user_default_escrow_state(self):
        """Test user has default escrow state on creation."""
        self.reporter.info("Testing default escrow state", context="Test")

        async with self.db.session() as session:
            repo = UserRepository(session)
            user = User(wallet_address=self._generate_unique_wallet())
            created_user = await repo.create(user)

            # Verify default escrow state
            assert created_user.escrow_account is None
            assert created_user.escrow_balance == Decimal("0")
            # Note: escrow_token_mint defaults to None until initialized

            self.reporter.info("Default escrow state correct", context="Test")

    async def test_multiple_balance_updates(self):
        """Test multiple escrow balance updates."""
        self.reporter.info("Testing multiple balance updates", context="Test")

        # Create user
        async with self.db.session() as session:
            repo = UserRepository(session)
            user = User(wallet_address=self._generate_unique_wallet())
            created_user = await repo.create(user)

        # Initialize and update multiple times
        async with self.db.session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_id(created_user.id)

            user.initialize_escrow(escrow_account="EscrowMulti123456789012345678901234")
            user.update_escrow_balance(Decimal("100.0"))
            await repo.update(user)

        async with self.db.session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_id(created_user.id)

            user.update_escrow_balance(Decimal("250.0"))
            await repo.update(user)

        async with self.db.session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_id(created_user.id)

            user.update_escrow_balance(Decimal("500.0"))
            updated_user = await repo.update(user)

            assert updated_user.escrow_balance == Decimal("500.0")

            self.reporter.info("Multiple balance updates successful", context="Test")


if __name__ == "__main__":
    TestUserRepository.run_as_main()

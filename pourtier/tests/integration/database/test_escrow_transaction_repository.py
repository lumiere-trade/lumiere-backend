"""
Integration tests for EscrowTransactionRepository with PostgreSQL.

Tests escrow transaction CRUD operations on test database.

Usage:
    python -m pourtier.tests.integration.database.test_escrow_transaction_repository
    laborant pourtier --integration
"""

from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine

from pourtier.config.settings import load_config
from pourtier.domain.entities.escrow_transaction import (
    EscrowTransaction,
    TransactionStatus,
    TransactionType,
)
from pourtier.domain.entities.user import User
from pourtier.infrastructure.persistence.database import Database
from pourtier.infrastructure.persistence.models import Base
from pourtier.infrastructure.persistence.repositories.escrow_transaction_repository import (  # noqa: E501
    EscrowTransactionRepository,
)
from pourtier.infrastructure.persistence.repositories.user_repository import (
    UserRepository,
)
from shared.tests import LaborantTest

# Load test configuration
test_settings = load_config("development.yaml", env="development")
TEST_DATABASE_URL = test_settings.DATABASE_URL


class TestEscrowTransactionRepository(LaborantTest):
    """Integration tests for EscrowTransactionRepository."""

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
        TestEscrowTransactionRepository.db = Database(
            database_url=TEST_DATABASE_URL, echo=False
        )
        await TestEscrowTransactionRepository.db.connect()

        self.reporter.info("Test database ready", context="Setup")

    async def async_teardown(self):
        """Cleanup test database (runs once after all tests)."""
        self.reporter.info("Cleaning up test database...", context="Teardown")

        if TestEscrowTransactionRepository.db:
            await TestEscrowTransactionRepository.db.disconnect()

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

    async def _create_test_user(self) -> User:
        """Create a test user with unique wallet."""
        async with self.db.session() as session:
            user_repo = UserRepository(session)
            user = User(wallet_address=self._generate_unique_wallet())
            return await user_repo.create(user)

    # ================================================================
    # Test Methods
    # ================================================================

    async def test_create_transaction(self):
        """Test creating escrow transaction."""
        self.reporter.info("Testing escrow transaction creation", context="Test")

        user = await self._create_test_user()

        async with self.db.session() as session:
            repo = EscrowTransactionRepository(session)

            transaction = EscrowTransaction(
                user_id=user.id,
                tx_signature="5J7Xk9N2BvPqYvJzUq4g" + "x" * 60,
                transaction_type=TransactionType.DEPOSIT,
                amount=Decimal("100.50"),
                token_mint="USDC",
                status=TransactionStatus.PENDING,
            )

            created = await repo.create(transaction)

            assert created.id is not None
            assert created.user_id == user.id
            assert created.transaction_type == TransactionType.DEPOSIT
            assert created.amount == Decimal("100.50")
            assert created.status == TransactionStatus.PENDING

            self.reporter.info(f"Transaction created: {created.id}", context="Test")

    async def test_get_transaction_by_id(self):
        """Test retrieving transaction by ID."""
        self.reporter.info("Testing get transaction by ID", context="Test")

        user = await self._create_test_user()

        # Create transaction
        async with self.db.session() as session:
            repo = EscrowTransactionRepository(session)
            transaction = EscrowTransaction(
                user_id=user.id,
                tx_signature="GetByID" + "x" * 80,
                transaction_type=TransactionType.DEPOSIT,
                amount=Decimal("50.0"),
                token_mint="USDC",
            )
            created = await repo.create(transaction)

        # Retrieve by ID
        async with self.db.session() as session:
            repo = EscrowTransactionRepository(session)
            retrieved = await repo.get_by_id(created.id)

            assert retrieved is not None
            assert retrieved.id == created.id
            assert retrieved.amount == Decimal("50.0")

            self.reporter.info("Transaction retrieved", context="Test")

    async def test_get_by_tx_signature(self):
        """Test retrieving transaction by signature."""
        self.reporter.info("Testing get by tx signature", context="Test")

        user = await self._create_test_user()

        # Create transaction
        async with self.db.session() as session:
            repo = EscrowTransactionRepository(session)
            tx_sig = "UniqueSignature" + "x" * 72
            transaction = EscrowTransaction(
                user_id=user.id,
                tx_signature=tx_sig,
                transaction_type=TransactionType.DEPOSIT,
                amount=Decimal("25.0"),
                token_mint="USDC",
            )
            await repo.create(transaction)

        # Retrieve by signature
        async with self.db.session() as session:
            repo = EscrowTransactionRepository(session)
            retrieved = await repo.get_by_tx_signature(tx_sig)

            assert retrieved is not None
            assert retrieved.tx_signature == tx_sig
            assert retrieved.amount == Decimal("25.0")

            self.reporter.info("Transaction retrieved by signature", context="Test")

    async def test_list_by_user(self):
        """Test listing transactions for user."""
        self.reporter.info("Testing list transactions by user", context="Test")

        user = await self._create_test_user()

        # Create multiple transactions
        async with self.db.session() as session:
            repo = EscrowTransactionRepository(session)

            tx1 = EscrowTransaction(
                user_id=user.id,
                tx_signature="TX1" + "x" * 85,
                transaction_type=TransactionType.DEPOSIT,
                amount=Decimal("100.0"),
                token_mint="USDC",
            )
            await repo.create(tx1)

            tx2 = EscrowTransaction(
                user_id=user.id,
                tx_signature="TX2" + "x" * 85,
                transaction_type=TransactionType.WITHDRAW,
                amount=Decimal("50.0"),
                token_mint="USDC",
            )
            await repo.create(tx2)

        # List all transactions
        async with self.db.session() as session:
            repo = EscrowTransactionRepository(session)
            transactions = await repo.list_by_user(user.id)

            assert len(transactions) == 2
            assert any(
                tx.transaction_type == TransactionType.DEPOSIT for tx in transactions
            )
            assert any(
                tx.transaction_type == TransactionType.WITHDRAW for tx in transactions
            )

            self.reporter.info(
                f"Found {len(transactions)} transactions", context="Test"
            )

    async def test_list_by_user_and_type(self):
        """Test listing transactions filtered by type."""
        self.reporter.info("Testing list by user and type", context="Test")

        user = await self._create_test_user()

        # Create transactions of different types
        async with self.db.session() as session:
            repo = EscrowTransactionRepository(session)

            # 2 deposits
            for i in range(2):
                tx = EscrowTransaction(
                    user_id=user.id,
                    tx_signature=f"DEP{i}" + "x" * 84,
                    transaction_type=TransactionType.DEPOSIT,
                    amount=Decimal("100.0"),
                    token_mint="USDC",
                )
                await repo.create(tx)

            # 1 withdraw
            tx = EscrowTransaction(
                user_id=user.id,
                tx_signature="WITH" + "x" * 84,
                transaction_type=TransactionType.WITHDRAW,
                amount=Decimal("50.0"),
                token_mint="USDC",
            )
            await repo.create(tx)

        # List only deposits
        async with self.db.session() as session:
            repo = EscrowTransactionRepository(session)
            deposits = await repo.list_by_user(
                user.id, transaction_type=TransactionType.DEPOSIT
            )

            assert len(deposits) == 2
            assert all(
                tx.transaction_type == TransactionType.DEPOSIT for tx in deposits
            )

            self.reporter.info(
                f"Found {len(deposits)} deposit transactions",
                context="Test",
            )

    async def test_confirm_transaction(self):
        """Test confirming transaction."""
        self.reporter.info("Testing confirm transaction", context="Test")

        user = await self._create_test_user()

        # Create pending transaction
        async with self.db.session() as session:
            repo = EscrowTransactionRepository(session)
            transaction = EscrowTransaction(
                user_id=user.id,
                tx_signature="CONFIRM" + "x" * 81,
                transaction_type=TransactionType.DEPOSIT,
                amount=Decimal("100.0"),
                token_mint="USDC",
                status=TransactionStatus.PENDING,
            )
            created = await repo.create(transaction)

        # Confirm transaction
        async with self.db.session() as session:
            repo = EscrowTransactionRepository(session)
            transaction = await repo.get_by_id(created.id)
            transaction.confirm()
            updated = await repo.update(transaction)

            assert updated.status == TransactionStatus.CONFIRMED
            assert updated.confirmed_at is not None

            self.reporter.info("Transaction confirmed", context="Test")

    async def test_transaction_lifecycle(self):
        """Test transaction lifecycle: PENDING → CONFIRMED."""
        self.reporter.info("Testing transaction lifecycle", context="Test")

        user = await self._create_test_user()

        # Create pending transaction
        async with self.db.session() as session:
            repo = EscrowTransactionRepository(session)
            transaction = EscrowTransaction(
                user_id=user.id,
                tx_signature="LIFECYCLE" + "x" * 79,
                transaction_type=TransactionType.DEPOSIT,
                amount=Decimal("200.0"),
                token_mint="USDC",
            )
            created = await repo.create(transaction)
            assert created.status == TransactionStatus.PENDING

        # Confirm
        async with self.db.session() as session:
            repo = EscrowTransactionRepository(session)
            transaction = await repo.get_by_id(created.id)
            transaction.confirm()
            updated = await repo.update(transaction)
            assert updated.status == TransactionStatus.CONFIRMED
            assert updated.confirmed_at is not None

            self.reporter.info("Lifecycle: PENDING → CONFIRMED", context="Test")


if __name__ == "__main__":
    TestEscrowTransactionRepository.run_as_main()

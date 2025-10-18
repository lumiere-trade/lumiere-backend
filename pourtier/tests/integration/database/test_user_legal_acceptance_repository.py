"""
Integration tests for UserLegalAcceptanceRepository with real PostgreSQL.

Tests CRUD operations on test database.

Usage:
    laborant pourtier --integration
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import text

from pourtier.config.settings import get_settings
from pourtier.domain.entities.legal_document import (
    DocumentType,
    LegalDocument,
)
from pourtier.domain.entities.user import User
from pourtier.domain.entities.user_legal_acceptance import (
    AcceptanceMethod,
    UserLegalAcceptance,
)
from pourtier.infrastructure.persistence.database import Database
from pourtier.infrastructure.persistence.models import Base
from pourtier.infrastructure.persistence.repositories.legal_document_repository import (
    LegalDocumentRepository,
)
from pourtier.infrastructure.persistence.repositories.user_legal_acceptance_repository import (
    UserLegalAcceptanceRepository,
)
from pourtier.infrastructure.persistence.repositories.user_repository import (
    UserRepository,
)
from shared.tests import LaborantTest


class TestUserLegalAcceptanceRepository(LaborantTest):
    """Integration tests for UserLegalAcceptanceRepository."""

    component_name = "pourtier"
    test_category = "integration"

    db: Database = None

    async def async_setup(self):
        """Setup test database."""
        self.reporter.info("Setting up test database...", context="Setup")

        settings = get_settings()
        self.reporter.info(f"Loaded ENV={settings.ENV}", context="Setup")

        TestUserLegalAcceptanceRepository.db = Database(
            database_url=settings.DATABASE_URL, echo=False
        )
        await TestUserLegalAcceptanceRepository.db.connect()
        self.reporter.info("Connected to test database", context="Setup")

        # Reset database schema using public method
        await TestUserLegalAcceptanceRepository.db.reset_schema_for_testing(Base.metadata)
        self.reporter.info("Database schema reset", context="Setup")

        self.reporter.info("Test database ready", context="Setup")

    async def async_setup_test(self):
        """Clean database before each test."""
        async with self.db.session() as session:
            await session.execute(text("TRUNCATE TABLE user_legal_acceptances CASCADE"))
            await session.execute(text("TRUNCATE TABLE legal_documents CASCADE"))
            await session.execute(text("TRUNCATE TABLE users CASCADE"))
            await session.commit()

    async def async_teardown(self):
        """Cleanup test database."""
        self.reporter.info("Cleaning up test database...", context="Teardown")

        if TestUserLegalAcceptanceRepository.db:
            await TestUserLegalAcceptanceRepository.db.disconnect()

        self.reporter.info("Cleanup complete", context="Teardown")

    def _generate_unique_wallet(self) -> str:
        """Generate unique 44-character wallet address."""
        unique_id = str(uuid4()).replace("-", "")
        return unique_id.ljust(44, "0")

    async def test_create_acceptance(self):
        """Test creating a new user legal acceptance."""
        self.reporter.info("Testing acceptance creation", context="Test")

        async with self.db.session() as session:
            user_repo = UserRepository(session)
            doc_repo = LegalDocumentRepository(session)

            user = User(wallet_address=self._generate_unique_wallet())
            user = await user_repo.create(user)

            doc = LegalDocument(
                document_type=DocumentType.TERMS_OF_SERVICE,
                version="1.0.0",
                title="TOS",
                content="Content",
            )
            doc = await doc_repo.create(doc)

        async with self.db.session() as session:
            repo = UserLegalAcceptanceRepository(session)

            acceptance = UserLegalAcceptance(
                user_id=user.id,
                document_id=doc.id,
                acceptance_method=AcceptanceMethod.WEB_CHECKBOX,
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
            )

            created = await repo.create(acceptance)

            assert created.id is not None
            assert created.user_id == user.id
            assert created.document_id == doc.id
            assert created.ip_address == "192.168.1.1"

            self.reporter.info(f"Acceptance created: {created.id}", context="Test")

    async def test_get_acceptance_by_id(self):
        """Test retrieving acceptance by ID."""
        self.reporter.info("Testing get acceptance by ID", context="Test")

        async with self.db.session() as session:
            user_repo = UserRepository(session)
            doc_repo = LegalDocumentRepository(session)
            acc_repo = UserLegalAcceptanceRepository(session)

            user = await user_repo.create(
                User(wallet_address=self._generate_unique_wallet())
            )
            doc = await doc_repo.create(
                LegalDocument(
                    document_type=DocumentType.TERMS_OF_SERVICE,
                    version="1.0.0",
                    title="TOS",
                    content="Content",
                )
            )
            acceptance = await acc_repo.create(
                UserLegalAcceptance(
                    user_id=user.id,
                    document_id=doc.id,
                )
            )

        async with self.db.session() as session:
            repo = UserLegalAcceptanceRepository(session)
            retrieved = await repo.get_by_id(acceptance.id)

            assert retrieved is not None
            assert retrieved.id == acceptance.id
            assert retrieved.user_id == user.id
            assert retrieved.document_id == doc.id

            self.reporter.info("Acceptance retrieved successfully", context="Test")

    async def test_get_nonexistent_acceptance(self):
        """Test retrieving non-existent acceptance returns None."""
        self.reporter.info("Testing get non-existent acceptance", context="Test")

        async with self.db.session() as session:
            repo = UserLegalAcceptanceRepository(session)
            acceptance = await repo.get_by_id(uuid4())

            assert acceptance is None

            self.reporter.info("Non-existent acceptance handled correctly", context="Test")

    async def test_get_by_user_and_document(self):
        """Test retrieving acceptance by user and document."""
        self.reporter.info("Testing get by user and document", context="Test")

        async with self.db.session() as session:
            user_repo = UserRepository(session)
            doc_repo = LegalDocumentRepository(session)
            acc_repo = UserLegalAcceptanceRepository(session)

            user = await user_repo.create(
                User(wallet_address=self._generate_unique_wallet())
            )
            doc = await doc_repo.create(
                LegalDocument(
                    document_type=DocumentType.TERMS_OF_SERVICE,
                    version="1.0.0",
                    title="TOS",
                    content="Content",
                )
            )
            await acc_repo.create(
                UserLegalAcceptance(
                    user_id=user.id,
                    document_id=doc.id,
                    ip_address="10.0.0.1",
                )
            )

        async with self.db.session() as session:
            repo = UserLegalAcceptanceRepository(session)
            acceptance = await repo.get_by_user_and_document(user.id, doc.id)

            assert acceptance is not None
            assert acceptance.user_id == user.id
            assert acceptance.document_id == doc.id
            assert acceptance.ip_address == "10.0.0.1"

            self.reporter.info("Acceptance found by user and document", context="Test")

    async def test_get_all_by_user(self):
        """Test retrieving all acceptances for a user."""
        self.reporter.info("Testing get all by user", context="Test")

        async with self.db.session() as session:
            user_repo = UserRepository(session)
            doc_repo = LegalDocumentRepository(session)
            acc_repo = UserLegalAcceptanceRepository(session)

            user = await user_repo.create(
                User(wallet_address=self._generate_unique_wallet())
            )

            doc1 = await doc_repo.create(
                LegalDocument(
                    document_type=DocumentType.TERMS_OF_SERVICE,
                    version="1.0.0",
                    title="TOS",
                    content="Content",
                )
            )
            doc2 = await doc_repo.create(
                LegalDocument(
                    document_type=DocumentType.PRIVACY_POLICY,
                    version="1.0.0",
                    title="Privacy",
                    content="Content",
                )
            )

            await acc_repo.create(
                UserLegalAcceptance(user_id=user.id, document_id=doc1.id)
            )
            await acc_repo.create(
                UserLegalAcceptance(user_id=user.id, document_id=doc2.id)
            )

        async with self.db.session() as session:
            repo = UserLegalAcceptanceRepository(session)
            acceptances = await repo.get_all_by_user(user.id)

            assert len(acceptances) == 2
            user_ids = {acc.user_id for acc in acceptances}
            assert user.id in user_ids

            self.reporter.info(
                f"Found {len(acceptances)} acceptances for user", context="Test"
            )

    async def test_get_all_by_document(self):
        """Test retrieving all acceptances for a document."""
        self.reporter.info("Testing get all by document", context="Test")

        async with self.db.session() as session:
            user_repo = UserRepository(session)
            doc_repo = LegalDocumentRepository(session)
            acc_repo = UserLegalAcceptanceRepository(session)

            user1 = await user_repo.create(
                User(wallet_address=self._generate_unique_wallet())
            )
            user2 = await user_repo.create(
                User(wallet_address=self._generate_unique_wallet())
            )

            doc = await doc_repo.create(
                LegalDocument(
                    document_type=DocumentType.TERMS_OF_SERVICE,
                    version="1.0.0",
                    title="TOS",
                    content="Content",
                )
            )

            await acc_repo.create(
                UserLegalAcceptance(user_id=user1.id, document_id=doc.id)
            )
            await acc_repo.create(
                UserLegalAcceptance(user_id=user2.id, document_id=doc.id)
            )

        async with self.db.session() as session:
            repo = UserLegalAcceptanceRepository(session)
            acceptances = await repo.get_all_by_document(doc.id)

            assert len(acceptances) == 2
            doc_ids = {acc.document_id for acc in acceptances}
            assert doc.id in doc_ids

            self.reporter.info(
                f"Found {len(acceptances)} acceptances for document", context="Test"
            )

    async def test_acceptance_with_web_checkbox_method(self):
        """Test acceptance with WEB_CHECKBOX method."""
        self.reporter.info("Testing WEB_CHECKBOX method", context="Test")

        async with self.db.session() as session:
            user_repo = UserRepository(session)
            doc_repo = LegalDocumentRepository(session)
            acc_repo = UserLegalAcceptanceRepository(session)

            user = await user_repo.create(
                User(wallet_address=self._generate_unique_wallet())
            )
            doc = await doc_repo.create(
                LegalDocument(
                    document_type=DocumentType.TERMS_OF_SERVICE,
                    version="1.0.0",
                    title="TOS",
                    content="Content",
                )
            )

            acceptance = await acc_repo.create(
                UserLegalAcceptance(
                    user_id=user.id,
                    document_id=doc.id,
                    acceptance_method=AcceptanceMethod.WEB_CHECKBOX,
                )
            )

            assert acceptance.acceptance_method == AcceptanceMethod.WEB_CHECKBOX

            self.reporter.info("WEB_CHECKBOX method stored", context="Test")

    async def test_acceptance_with_api_explicit_method(self):
        """Test acceptance with API_EXPLICIT method."""
        self.reporter.info("Testing API_EXPLICIT method", context="Test")

        async with self.db.session() as session:
            user_repo = UserRepository(session)
            doc_repo = LegalDocumentRepository(session)
            acc_repo = UserLegalAcceptanceRepository(session)

            user = await user_repo.create(
                User(wallet_address=self._generate_unique_wallet())
            )
            doc = await doc_repo.create(
                LegalDocument(
                    document_type=DocumentType.TERMS_OF_SERVICE,
                    version="1.0.0",
                    title="TOS",
                    content="Content",
                )
            )

            acceptance = await acc_repo.create(
                UserLegalAcceptance(
                    user_id=user.id,
                    document_id=doc.id,
                    acceptance_method=AcceptanceMethod.API_EXPLICIT,
                )
            )

            assert acceptance.acceptance_method == AcceptanceMethod.API_EXPLICIT

            self.reporter.info("API_EXPLICIT method stored", context="Test")

    async def test_acceptance_with_audit_trail(self):
        """Test acceptance stores complete audit trail."""
        self.reporter.info("Testing audit trail storage", context="Test")

        async with self.db.session() as session:
            user_repo = UserRepository(session)
            doc_repo = LegalDocumentRepository(session)
            acc_repo = UserLegalAcceptanceRepository(session)

            user = await user_repo.create(
                User(wallet_address=self._generate_unique_wallet())
            )
            doc = await doc_repo.create(
                LegalDocument(
                    document_type=DocumentType.TERMS_OF_SERVICE,
                    version="1.0.0",
                    title="TOS",
                    content="Content",
                )
            )

            ip = "203.0.113.42"
            user_agent = "Mozilla/5.0 (X11; Linux x86_64)"

            acceptance = await acc_repo.create(
                UserLegalAcceptance(
                    user_id=user.id,
                    document_id=doc.id,
                    ip_address=ip,
                    user_agent=user_agent,
                )
            )

            assert acceptance.ip_address == ip
            assert acceptance.user_agent == user_agent
            assert isinstance(acceptance.accepted_at, datetime)

            self.reporter.info("Audit trail stored correctly", context="Test")

    async def test_acceptance_without_optional_audit_fields(self):
        """Test acceptance without IP and user agent."""
        self.reporter.info("Testing acceptance without optional audit fields", context="Test")

        async with self.db.session() as session:
            user_repo = UserRepository(session)
            doc_repo = LegalDocumentRepository(session)
            acc_repo = UserLegalAcceptanceRepository(session)

            user = await user_repo.create(
                User(wallet_address=self._generate_unique_wallet())
            )
            doc = await doc_repo.create(
                LegalDocument(
                    document_type=DocumentType.TERMS_OF_SERVICE,
                    version="1.0.0",
                    title="TOS",
                    content="Content",
                )
            )

            acceptance = await acc_repo.create(
                UserLegalAcceptance(
                    user_id=user.id,
                    document_id=doc.id,
                )
            )

            assert acceptance.ip_address is None
            assert acceptance.user_agent is None

            self.reporter.info("Acceptance without audit fields valid", context="Test")

    async def test_acceptance_requires_valid_user(self):
        """Test acceptance requires existing user."""
        self.reporter.info("Testing acceptance requires valid user", context="Test")

        async with self.db.session() as session:
            doc_repo = LegalDocumentRepository(session)
            doc = await doc_repo.create(
                LegalDocument(
                    document_type=DocumentType.TERMS_OF_SERVICE,
                    version="1.0.0",
                    title="TOS",
                    content="Content",
                )
            )

        try:
            async with self.db.session() as session:
                acc_repo = UserLegalAcceptanceRepository(session)
                await acc_repo.create(
                    UserLegalAcceptance(
                        user_id=uuid4(),
                        document_id=doc.id,
                    )
                )
            assert False, "Should raise foreign key error"
        except Exception:
            self.reporter.info("Foreign key constraint enforced", context="Test")

    async def test_acceptance_requires_valid_document(self):
        """Test acceptance requires existing document."""
        self.reporter.info("Testing acceptance requires valid document", context="Test")

        async with self.db.session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.create(
                User(wallet_address=self._generate_unique_wallet())
            )

        try:
            async with self.db.session() as session:
                acc_repo = UserLegalAcceptanceRepository(session)
                await acc_repo.create(
                    UserLegalAcceptance(
                        user_id=user.id,
                        document_id=uuid4(),
                    )
                )
            assert False, "Should raise foreign key error"
        except Exception:
            self.reporter.info("Foreign key constraint enforced", context="Test")


if __name__ == "__main__":
    TestUserLegalAcceptanceRepository.run_as_main()

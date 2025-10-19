"""
Integration tests for LegalDocumentRepository with real PostgreSQL.

Tests CRUD operations on test database.

Usage:
    laborant pourtier --integration
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import text

from pourtier.config.settings import get_settings
from pourtier.domain.entities.legal_document import (
    DocumentStatus,
    DocumentType,
    LegalDocument,
)
from pourtier.infrastructure.persistence.database import Database
from pourtier.infrastructure.persistence.models import Base
from pourtier.infrastructure.persistence.repositories.legal_document_repository import (
    LegalDocumentRepository,
)
from shared.tests import LaborantTest


class TestLegalDocumentRepository(LaborantTest):
    """Integration tests for LegalDocumentRepository."""

    component_name = "pourtier"
    test_category = "integration"

    db: Database = None

    async def async_setup(self):
        """Setup test database."""
        self.reporter.info("Setting up test database...", context="Setup")

        settings = get_settings()
        self.reporter.info(f"Loaded ENV={settings.ENV}", context="Setup")

        TestLegalDocumentRepository.db = Database(
            database_url=settings.DATABASE_URL, echo=False
        )
        await TestLegalDocumentRepository.db.connect()
        self.reporter.info("Connected to test database", context="Setup")

        # Reset database schema using public method
        await TestLegalDocumentRepository.db.reset_schema_for_testing(Base.metadata)
        self.reporter.info("Database schema reset", context="Setup")

        self.reporter.info("Test database ready", context="Setup")

    async def async_setup_test(self):
        """Clean database before each test."""
        async with self.db.session() as session:
            await session.execute(text("TRUNCATE TABLE legal_documents CASCADE"))
            await session.commit()

    async def async_teardown(self):
        """Cleanup test database."""
        self.reporter.info("Cleaning up test database...", context="Teardown")

        if TestLegalDocumentRepository.db:
            await TestLegalDocumentRepository.db.disconnect()

        self.reporter.info("Cleanup complete", context="Teardown")

    async def test_create_legal_document(self):
        """Test creating a new legal document."""
        self.reporter.info("Testing document creation", context="Test")

        async with self.db.session() as session:
            repo = LegalDocumentRepository(session)

            doc = LegalDocument(
                document_type=DocumentType.TERMS_OF_SERVICE,
                version="1.0.0",
                title="Test Terms of Service",
                content="This is test content",
            )

            created_doc = await repo.create(doc)

            assert created_doc.id is not None
            assert created_doc.document_type == DocumentType.TERMS_OF_SERVICE
            assert created_doc.version == "1.0.0"
            assert created_doc.status == DocumentStatus.DRAFT

            self.reporter.info(f"Document created: {created_doc.id}", context="Test")

    async def test_get_document_by_id(self):
        """Test retrieving document by ID."""
        self.reporter.info("Testing get document by ID", context="Test")

        async with self.db.session() as session:
            repo = LegalDocumentRepository(session)
            doc = LegalDocument(
                document_type=DocumentType.PRIVACY_POLICY,
                version="1.0.0",
                title="Privacy Policy",
                content="Privacy content",
            )
            created_doc = await repo.create(doc)

        async with self.db.session() as session:
            repo = LegalDocumentRepository(session)
            retrieved_doc = await repo.get_by_id(created_doc.id)

            assert retrieved_doc is not None
            assert retrieved_doc.id == created_doc.id
            assert retrieved_doc.title == "Privacy Policy"

            self.reporter.info("Document retrieved successfully", context="Test")

    async def test_get_nonexistent_document(self):
        """Test retrieving non-existent document returns None."""
        self.reporter.info("Testing get non-existent document", context="Test")

        async with self.db.session() as session:
            repo = LegalDocumentRepository(session)
            doc = await repo.get_by_id(uuid4())

            assert doc is None

            self.reporter.info(
                "Non-existent document handled correctly", context="Test"
            )

    async def test_update_legal_document(self):
        """Test updating document information."""
        self.reporter.info("Testing document update", context="Test")

        async with self.db.session() as session:
            repo = LegalDocumentRepository(session)
            doc = LegalDocument(
                document_type=DocumentType.TERMS_OF_SERVICE,
                version="1.0.0",
                title="Original Title",
                content="Original content",
            )
            created_doc = await repo.create(doc)

        async with self.db.session() as session:
            repo = LegalDocumentRepository(session)
            doc = await repo.get_by_id(created_doc.id)

            doc.title = "Updated Title"
            doc.content = "Updated content"

            updated_doc = await repo.update(doc)

            assert updated_doc.title == "Updated Title"
            assert updated_doc.content == "Updated content"

            self.reporter.info("Document updated successfully", context="Test")

    async def test_activate_document(self):
        """Test activating a document."""
        self.reporter.info("Testing document activation", context="Test")

        async with self.db.session() as session:
            repo = LegalDocumentRepository(session)
            doc = LegalDocument(
                document_type=DocumentType.TERMS_OF_SERVICE,
                version="1.0.0",
                title="TOS",
                content="Content",
                effective_date=datetime.now(),
            )
            created_doc = await repo.create(doc)

        async with self.db.session() as session:
            repo = LegalDocumentRepository(session)
            doc = await repo.get_by_id(created_doc.id)

            doc.activate()

            updated_doc = await repo.update(doc)

            assert updated_doc.status == DocumentStatus.ACTIVE
            assert updated_doc.is_active() is True

            self.reporter.info("Document activated", context="Test")

    async def test_archive_document(self):
        """Test archiving a document."""
        self.reporter.info("Testing document archival", context="Test")

        async with self.db.session() as session:
            repo = LegalDocumentRepository(session)
            doc = LegalDocument(
                document_type=DocumentType.TERMS_OF_SERVICE,
                version="1.0.0",
                title="TOS",
                content="Content",
                status=DocumentStatus.ACTIVE,
                effective_date=datetime.now(),
            )
            created_doc = await repo.create(doc)

        async with self.db.session() as session:
            repo = LegalDocumentRepository(session)
            doc = await repo.get_by_id(created_doc.id)

            doc.archive()

            updated_doc = await repo.update(doc)

            assert updated_doc.status == DocumentStatus.ARCHIVED
            assert updated_doc.is_active() is False

            self.reporter.info("Document archived", context="Test")

    async def test_get_all_active_documents(self):
        """Test retrieving all active documents."""
        self.reporter.info("Testing get all active documents", context="Test")

        async with self.db.session() as session:
            repo = LegalDocumentRepository(session)

            active_doc = LegalDocument(
                document_type=DocumentType.TERMS_OF_SERVICE,
                version="1.0.0",
                title="Active TOS",
                content="Content",
                status=DocumentStatus.ACTIVE,
                effective_date=datetime.now(),
            )
            await repo.create(active_doc)

            draft_doc = LegalDocument(
                document_type=DocumentType.PRIVACY_POLICY,
                version="1.0.0",
                title="Draft Privacy",
                content="Content",
                status=DocumentStatus.DRAFT,
            )
            await repo.create(draft_doc)

            archived_doc = LegalDocument(
                document_type=DocumentType.TERMS_OF_SERVICE,
                version="0.9.0",
                title="Old TOS",
                content="Content",
                status=DocumentStatus.ARCHIVED,
                effective_date=datetime.now(),
            )
            await repo.create(archived_doc)

        async with self.db.session() as session:
            repo = LegalDocumentRepository(session)
            active_docs = await repo.get_all_active()

            assert len(active_docs) == 1
            assert active_docs[0].status == DocumentStatus.ACTIVE
            assert active_docs[0].title == "Active TOS"

            self.reporter.info(
                f"Found {len(active_docs)} active documents", context="Test"
            )

    async def test_get_by_type_and_version(self):
        """Test retrieving document by type and version."""
        self.reporter.info("Testing get by type and version", context="Test")

        async with self.db.session() as session:
            repo = LegalDocumentRepository(session)

            doc_v1 = LegalDocument(
                document_type=DocumentType.TERMS_OF_SERVICE,
                version="1.0.0",
                title="TOS v1",
                content="Content v1",
            )
            await repo.create(doc_v1)

            doc_v2 = LegalDocument(
                document_type=DocumentType.TERMS_OF_SERVICE,
                version="2.0.0",
                title="TOS v2",
                content="Content v2",
            )
            await repo.create(doc_v2)

        async with self.db.session() as session:
            repo = LegalDocumentRepository(session)
            doc = await repo.get_by_type_and_version(
                DocumentType.TERMS_OF_SERVICE,
                "1.0.0",
            )

            assert doc is not None
            assert doc.version == "1.0.0"
            assert doc.title == "TOS v1"

            self.reporter.info("Document found by type and version", context="Test")

    async def test_multiple_active_document_types(self):
        """Test having active documents of different types."""
        self.reporter.info("Testing multiple active document types", context="Test")

        async with self.db.session() as session:
            repo = LegalDocumentRepository(session)

            terms = LegalDocument(
                document_type=DocumentType.TERMS_OF_SERVICE,
                version="1.0.0",
                title="Terms",
                content="TOS content",
                status=DocumentStatus.ACTIVE,
                effective_date=datetime.now(),
            )
            await repo.create(terms)

            privacy = LegalDocument(
                document_type=DocumentType.PRIVACY_POLICY,
                version="1.0.0",
                title="Privacy",
                content="Privacy content",
                status=DocumentStatus.ACTIVE,
                effective_date=datetime.now(),
            )
            await repo.create(privacy)

        async with self.db.session() as session:
            repo = LegalDocumentRepository(session)
            active_docs = await repo.get_all_active()

            assert len(active_docs) == 2
            doc_types = {doc.document_type for doc in active_docs}
            assert DocumentType.TERMS_OF_SERVICE in doc_types
            assert DocumentType.PRIVACY_POLICY in doc_types

            self.reporter.info("Multiple active document types stored", context="Test")


if __name__ == "__main__":
    TestLegalDocumentRepository.run_as_main()

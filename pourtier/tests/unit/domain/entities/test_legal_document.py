"""
Unit tests for LegalDocument entity.

Tests document creation, validation, and lifecycle operations.

Usage:
    python -m pourtier.tests.unit.domain.entities.test_legal_document
    laborant pourtier --unit
"""

from datetime import datetime
from uuid import UUID

from pourtier.domain.entities.legal_document import (
    DocumentStatus,
    DocumentType,
    LegalDocument,
)
from shared.tests import LaborantTest


class TestLegalDocument(LaborantTest):
    """Unit tests for LegalDocument entity."""

    component_name = "pourtier"
    test_category = "unit"

    # ============================================================
    # Creation tests
    # ============================================================

    def test_create_legal_document_with_required_fields(self):
        """Test creating LegalDocument with required fields."""
        self.reporter.info(
            "Testing legal document creation",
            context="Test",
        )

        doc = LegalDocument(
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Test Terms",
            content="Test content",
        )

        assert doc.document_type == DocumentType.TERMS_OF_SERVICE
        assert doc.version == "1.0.0"
        assert doc.title == "Test Terms"
        assert doc.content == "Test content"
        assert isinstance(doc.id, UUID)
        self.reporter.info("Legal document created", context="Test")

    def test_legal_document_auto_generates_id(self):
        """Test LegalDocument auto-generates UUID."""
        self.reporter.info("Testing auto-generated UUID", context="Test")

        doc = LegalDocument(
            document_type=DocumentType.PRIVACY_POLICY,
            version="1.0.0",
            title="Privacy",
            content="Content",
        )

        assert isinstance(doc.id, UUID)
        assert doc.id is not None
        self.reporter.info(f"Generated UUID: {doc.id}", context="Test")

    def test_legal_document_default_status_is_draft(self):
        """Test LegalDocument defaults to DRAFT status."""
        self.reporter.info("Testing default status", context="Test")

        doc = LegalDocument(
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Test",
            content="Content",
        )

        assert doc.status == DocumentStatus.DRAFT
        self.reporter.info("Default status is DRAFT", context="Test")

    # ============================================================
    # Validation tests
    # ============================================================

    def test_reject_empty_title(self):
        """Test LegalDocument rejects empty title."""
        self.reporter.info("Testing rejection of empty title", context="Test")

        try:
            LegalDocument(
                document_type=DocumentType.TERMS_OF_SERVICE,
                version="1.0.0",
                title="",
                content="Content",
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "title is required" in str(e)
            self.reporter.info("Empty title rejected", context="Test")

    def test_reject_empty_content(self):
        """Test LegalDocument rejects empty content."""
        self.reporter.info(
            "Testing rejection of empty content",
            context="Test",
        )

        try:
            LegalDocument(
                document_type=DocumentType.TERMS_OF_SERVICE,
                version="1.0.0",
                title="Test",
                content="",
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "content is required" in str(e)
            self.reporter.info("Empty content rejected", context="Test")

    def test_reject_empty_version(self):
        """Test LegalDocument rejects empty version."""
        self.reporter.info(
            "Testing rejection of empty version",
            context="Test",
        )

        try:
            LegalDocument(
                document_type=DocumentType.TERMS_OF_SERVICE,
                version="",
                title="Test",
                content="Content",
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "version is required" in str(e)
            self.reporter.info("Empty version rejected", context="Test")

    # ============================================================
    # Lifecycle tests
    # ============================================================

    def test_activate_document(self):
        """Test activate() changes status to ACTIVE."""
        self.reporter.info("Testing document activation", context="Test")

        doc = LegalDocument(
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Test",
            content="Content",
            effective_date=datetime.now(),
        )

        doc.activate()

        assert doc.status == DocumentStatus.ACTIVE
        self.reporter.info("Document activated", context="Test")

    def test_activate_requires_effective_date(self):
        """Test activate() requires effective_date."""
        self.reporter.info(
            "Testing activation requires effective date",
            context="Test",
        )

        doc = LegalDocument(
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Test",
            content="Content",
        )

        try:
            doc.activate()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Effective date required" in str(e)
            self.reporter.info(
                "Activation without date rejected",
                context="Test",
            )

    def test_archive_document(self):
        """Test archive() changes status to ARCHIVED."""
        self.reporter.info("Testing document archival", context="Test")

        doc = LegalDocument(
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Test",
            content="Content",
            status=DocumentStatus.ACTIVE,
            effective_date=datetime.now(),
        )

        doc.archive()

        assert doc.status == DocumentStatus.ARCHIVED
        self.reporter.info("Document archived", context="Test")

    def test_is_active_returns_true_for_active_document(self):
        """Test is_active() returns True for active document."""
        self.reporter.info(
            "Testing is_active() for active document",
            context="Test",
        )

        doc = LegalDocument(
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Test",
            content="Content",
            status=DocumentStatus.ACTIVE,
            effective_date=datetime.now(),
        )

        assert doc.is_active() is True
        self.reporter.info("is_active() returns True", context="Test")

    def test_is_active_returns_false_for_draft(self):
        """Test is_active() returns False for draft."""
        self.reporter.info(
            "Testing is_active() for draft document",
            context="Test",
        )

        doc = LegalDocument(
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Test",
            content="Content",
            status=DocumentStatus.DRAFT,
        )

        assert doc.is_active() is False
        self.reporter.info("is_active() returns False for draft", context="Test")

    def test_is_active_returns_false_for_archived(self):
        """Test is_active() returns False for archived."""
        self.reporter.info(
            "Testing is_active() for archived document",
            context="Test",
        )

        doc = LegalDocument(
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Test",
            content="Content",
            status=DocumentStatus.ARCHIVED,
            effective_date=datetime.now(),
        )

        assert doc.is_active() is False
        self.reporter.info(
            "is_active() returns False for archived",
            context="Test",
        )

    # ============================================================
    # Serialization tests
    # ============================================================

    def test_to_dict_serialization(self):
        """Test to_dict() returns correct dictionary."""
        self.reporter.info("Testing to_dict() serialization", context="Test")

        doc = LegalDocument(
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Test Terms",
            content="Test content",
            status=DocumentStatus.ACTIVE,
            effective_date=datetime.now(),
        )

        result = doc.to_dict()

        assert result["id"] == str(doc.id)
        assert result["document_type"] == "terms_of_service"
        assert result["version"] == "1.0.0"
        assert result["title"] == "Test Terms"
        assert result["content"] == "Test content"
        assert result["status"] == "active"
        assert "effective_date" in result
        assert "created_at" in result
        assert "updated_at" in result
        self.reporter.info("to_dict() serialization correct", context="Test")

    # ============================================================
    # Document type tests
    # ============================================================

    def test_terms_of_service_document_type(self):
        """Test TERMS_OF_SERVICE document type."""
        self.reporter.info(
            "Testing TERMS_OF_SERVICE type",
            context="Test",
        )

        doc = LegalDocument(
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Terms",
            content="Content",
        )

        assert doc.document_type == DocumentType.TERMS_OF_SERVICE
        assert doc.document_type.value == "terms_of_service"
        self.reporter.info("TERMS_OF_SERVICE type works", context="Test")

    def test_privacy_policy_document_type(self):
        """Test PRIVACY_POLICY document type."""
        self.reporter.info("Testing PRIVACY_POLICY type", context="Test")

        doc = LegalDocument(
            document_type=DocumentType.PRIVACY_POLICY,
            version="1.0.0",
            title="Privacy",
            content="Content",
        )

        assert doc.document_type == DocumentType.PRIVACY_POLICY
        assert doc.document_type.value == "privacy_policy"
        self.reporter.info("PRIVACY_POLICY type works", context="Test")


if __name__ == "__main__":
    TestLegalDocument.run_as_main()

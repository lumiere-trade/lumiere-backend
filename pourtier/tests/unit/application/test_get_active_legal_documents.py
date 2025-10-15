"""
Unit tests for GetActiveLegalDocuments use case.

Tests retrieval of active legal documents.

Usage:
    python -m pourtier.tests.unit.application.test_get_active_legal_documents
    laborant pourtier --unit
"""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from pourtier.application.use_cases.get_active_legal_documents import (
    GetActiveLegalDocuments,
)
from pourtier.domain.entities.legal_document import (
    DocumentStatus,
    DocumentType,
    LegalDocument,
)
from shared.tests import LaborantTest


class TestGetActiveLegalDocuments(LaborantTest):
    """Unit tests for GetActiveLegalDocuments use case."""

    component_name = "pourtier"
    test_category = "unit"

    # ============================================================
    # Success tests
    # ============================================================

    async def test_get_active_documents_success(self):
        """Test getting active documents successfully."""
        self.reporter.info(
            "Testing get active documents success",
            context="Test",
        )

        # Mock repository
        mock_repo = AsyncMock()

        # Create mock documents
        doc1 = LegalDocument(
            id=uuid4(),
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Terms",
            content="TOS content",
            status=DocumentStatus.ACTIVE,
            effective_date=datetime.now(),
        )
        doc2 = LegalDocument(
            id=uuid4(),
            document_type=DocumentType.PRIVACY_POLICY,
            version="1.0.0",
            title="Privacy",
            content="Privacy content",
            status=DocumentStatus.ACTIVE,
            effective_date=datetime.now(),
        )

        # Mock repository response
        mock_repo.get_all_active.return_value = [doc1, doc2]

        # Create use case
        use_case = GetActiveLegalDocuments(
            legal_document_repository=mock_repo,
        )

        # Execute use case
        result = await use_case.execute()

        # Assertions
        assert len(result) == 2
        assert result[0] == doc1
        assert result[1] == doc2
        mock_repo.get_all_active.assert_called_once()
        self.reporter.info("Active documents retrieved", context="Test")

    async def test_get_active_documents_empty_list(self):
        """Test getting active documents when none exist."""
        self.reporter.info(
            "Testing get active documents empty",
            context="Test",
        )

        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.get_all_active.return_value = []

        # Create use case
        use_case = GetActiveLegalDocuments(
            legal_document_repository=mock_repo,
        )

        # Execute use case
        result = await use_case.execute()

        # Assertions
        assert result == []
        assert len(result) == 0
        mock_repo.get_all_active.assert_called_once()
        self.reporter.info("Empty list returned correctly", context="Test")

    async def test_get_active_documents_single_document(self):
        """Test getting active documents with single result."""
        self.reporter.info(
            "Testing get active documents single result",
            context="Test",
        )

        # Mock repository
        mock_repo = AsyncMock()

        # Create mock document
        doc = LegalDocument(
            id=uuid4(),
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Terms",
            content="Content",
            status=DocumentStatus.ACTIVE,
            effective_date=datetime.now(),
        )

        # Mock repository response
        mock_repo.get_all_active.return_value = [doc]

        # Create use case
        use_case = GetActiveLegalDocuments(
            legal_document_repository=mock_repo,
        )

        # Execute use case
        result = await use_case.execute()

        # Assertions
        assert len(result) == 1
        assert result[0] == doc
        self.reporter.info("Single document retrieved", context="Test")

    async def test_get_active_documents_all_types(self):
        """Test getting active documents of all types."""
        self.reporter.info(
            "Testing all document types",
            context="Test",
        )

        # Mock repository
        mock_repo = AsyncMock()

        # Create documents of different types
        terms = LegalDocument(
            id=uuid4(),
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Terms",
            content="TOS",
            status=DocumentStatus.ACTIVE,
            effective_date=datetime.now(),
        )
        privacy = LegalDocument(
            id=uuid4(),
            document_type=DocumentType.PRIVACY_POLICY,
            version="1.0.0",
            title="Privacy",
            content="Privacy",
            status=DocumentStatus.ACTIVE,
            effective_date=datetime.now(),
        )

        # Mock repository response
        mock_repo.get_all_active.return_value = [terms, privacy]

        # Create use case
        use_case = GetActiveLegalDocuments(
            legal_document_repository=mock_repo,
        )

        # Execute use case
        result = await use_case.execute()

        # Assertions
        assert len(result) == 2
        doc_types = {doc.document_type for doc in result}
        assert DocumentType.TERMS_OF_SERVICE in doc_types
        assert DocumentType.PRIVACY_POLICY in doc_types
        self.reporter.info("All document types present", context="Test")

    async def test_use_case_calls_repository_once(self):
        """Test use case calls repository exactly once."""
        self.reporter.info(
            "Testing repository called once",
            context="Test",
        )

        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.get_all_active.return_value = []

        # Create use case
        use_case = GetActiveLegalDocuments(
            legal_document_repository=mock_repo,
        )

        # Execute use case
        await use_case.execute()

        # Assertions
        assert mock_repo.get_all_active.call_count == 1
        self.reporter.info("Repository called exactly once", context="Test")

    async def test_use_case_propagates_repository_exception(self):
        """Test use case propagates repository exceptions."""
        self.reporter.info(
            "Testing exception propagation",
            context="Test",
        )

        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.get_all_active.side_effect = Exception("Database error")

        # Create use case
        use_case = GetActiveLegalDocuments(
            legal_document_repository=mock_repo,
        )

        # Execute use case and expect exception
        try:
            await use_case.execute()
            assert False, "Should have raised exception"
        except Exception as e:
            assert "Database error" in str(e)
            self.reporter.info("Exception propagated correctly", context="Test")


if __name__ == "__main__":
    TestGetActiveLegalDocuments.run_as_main()

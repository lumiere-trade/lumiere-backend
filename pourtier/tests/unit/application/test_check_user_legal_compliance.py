"""
Unit tests for CheckUserLegalCompliance use case.

Tests checking if user has accepted all required documents.

Usage:
    python -m pourtier.tests.unit.application.test_check_user_legal_compliance
    laborant pourtier --unit
"""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from pourtier.application.use_cases.check_user_legal_compliance import (
    CheckUserLegalCompliance,
)
from pourtier.domain.entities.legal_document import (
    DocumentStatus,
    DocumentType,
    LegalDocument,
)
from pourtier.domain.entities.user import User
from pourtier.domain.entities.user_legal_acceptance import (
    UserLegalAcceptance,
)
from pourtier.domain.exceptions.base import EntityNotFoundError
from shared.tests import LaborantTest


class TestCheckUserLegalCompliance(LaborantTest):
    """Unit tests for CheckUserLegalCompliance use case."""

    component_name = "pourtier"
    test_category = "unit"

    # ============================================================
    # Compliant tests
    # ============================================================

    async def test_user_compliant_all_documents_accepted(self):
        """Test user is compliant when all documents accepted."""
        self.reporter.info(
            "Testing user compliant with all documents",
            context="Test",
        )

        # Mock repositories
        mock_user_repo = AsyncMock()
        mock_doc_repo = AsyncMock()
        mock_acceptance_repo = AsyncMock()

        # Test data
        user_id = uuid4()
        doc1_id = uuid4()
        doc2_id = uuid4()

        # Mock user exists
        user = User(wallet_address="A" * 44, id=user_id)
        mock_user_repo.get_by_id.return_value = user

        # Mock active documents
        doc1 = LegalDocument(
            id=doc1_id,
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Terms",
            content="TOS",
            status=DocumentStatus.ACTIVE,
            effective_date=datetime.now(),
        )
        doc2 = LegalDocument(
            id=doc2_id,
            document_type=DocumentType.PRIVACY_POLICY,
            version="1.0.0",
            title="Privacy",
            content="Privacy",
            status=DocumentStatus.ACTIVE,
            effective_date=datetime.now(),
        )
        mock_doc_repo.get_all_active.return_value = [doc1, doc2]

        # Mock user acceptances (all documents)
        acceptance1 = UserLegalAcceptance(user_id=user_id, document_id=doc1_id)
        acceptance2 = UserLegalAcceptance(user_id=user_id, document_id=doc2_id)
        mock_acceptance_repo.get_all_by_user.return_value = [
            acceptance1,
            acceptance2,
        ]

        # Create use case
        use_case = CheckUserLegalCompliance(
            user_repository=mock_user_repo,
            legal_document_repository=mock_doc_repo,
            user_legal_acceptance_repository=mock_acceptance_repo,
        )

        # Execute use case
        is_compliant, pending_docs = await use_case.execute(user_id=user_id)

        # Assertions
        assert is_compliant is True
        assert len(pending_docs) == 0
        mock_user_repo.get_by_id.assert_called_once_with(user_id)
        mock_doc_repo.get_all_active.assert_called_once()
        mock_acceptance_repo.get_all_by_user.assert_called_once_with(user_id)
        self.reporter.info("User is compliant", context="Test")

    # ============================================================
    # Non-compliant tests
    # ============================================================

    async def test_user_non_compliant_missing_document(self):
        """Test user non-compliant when missing one document."""
        self.reporter.info(
            "Testing user non-compliant with missing document",
            context="Test",
        )

        # Mock repositories
        mock_user_repo = AsyncMock()
        mock_doc_repo = AsyncMock()
        mock_acceptance_repo = AsyncMock()

        # Test data
        user_id = uuid4()
        doc1_id = uuid4()
        doc2_id = uuid4()

        # Mock user exists
        user = User(wallet_address="A" * 44, id=user_id)
        mock_user_repo.get_by_id.return_value = user

        # Mock active documents
        doc1 = LegalDocument(
            id=doc1_id,
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Terms",
            content="TOS",
            status=DocumentStatus.ACTIVE,
            effective_date=datetime.now(),
        )
        doc2 = LegalDocument(
            id=doc2_id,
            document_type=DocumentType.PRIVACY_POLICY,
            version="1.0.0",
            title="Privacy",
            content="Privacy",
            status=DocumentStatus.ACTIVE,
            effective_date=datetime.now(),
        )
        mock_doc_repo.get_all_active.return_value = [doc1, doc2]

        # Mock user acceptances (only one document)
        acceptance1 = UserLegalAcceptance(user_id=user_id, document_id=doc1_id)
        mock_acceptance_repo.get_all_by_user.return_value = [acceptance1]

        # Create use case
        use_case = CheckUserLegalCompliance(
            user_repository=mock_user_repo,
            legal_document_repository=mock_doc_repo,
            user_legal_acceptance_repository=mock_acceptance_repo,
        )

        # Execute use case
        is_compliant, pending_docs = await use_case.execute(user_id=user_id)

        # Assertions
        assert is_compliant is False
        assert len(pending_docs) == 1
        assert pending_docs[0].id == doc2_id
        self.reporter.info("User is non-compliant", context="Test")

    async def test_user_non_compliant_no_acceptances(self):
        """Test user non-compliant when no documents accepted."""
        self.reporter.info(
            "Testing user with no acceptances",
            context="Test",
        )

        # Mock repositories
        mock_user_repo = AsyncMock()
        mock_doc_repo = AsyncMock()
        mock_acceptance_repo = AsyncMock()

        # Test data
        user_id = uuid4()
        doc_id = uuid4()

        # Mock user exists
        user = User(wallet_address="A" * 44, id=user_id)
        mock_user_repo.get_by_id.return_value = user

        # Mock active documents
        doc = LegalDocument(
            id=doc_id,
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Terms",
            content="TOS",
            status=DocumentStatus.ACTIVE,
            effective_date=datetime.now(),
        )
        mock_doc_repo.get_all_active.return_value = [doc]

        # Mock no acceptances
        mock_acceptance_repo.get_all_by_user.return_value = []

        # Create use case
        use_case = CheckUserLegalCompliance(
            user_repository=mock_user_repo,
            legal_document_repository=mock_doc_repo,
            user_legal_acceptance_repository=mock_acceptance_repo,
        )

        # Execute use case
        is_compliant, pending_docs = await use_case.execute(user_id=user_id)

        # Assertions
        assert is_compliant is False
        assert len(pending_docs) == 1
        assert pending_docs[0].id == doc_id
        self.reporter.info("User has no acceptances", context="Test")

    # ============================================================
    # Edge cases
    # ============================================================

    async def test_compliant_when_no_active_documents(self):
        """Test user compliant when no active documents exist."""
        self.reporter.info(
            "Testing compliance with no active documents",
            context="Test",
        )

        # Mock repositories
        mock_user_repo = AsyncMock()
        mock_doc_repo = AsyncMock()
        mock_acceptance_repo = AsyncMock()

        # Test data
        user_id = uuid4()

        # Mock user exists
        user = User(wallet_address="A" * 44, id=user_id)
        mock_user_repo.get_by_id.return_value = user

        # Mock no active documents
        mock_doc_repo.get_all_active.return_value = []

        # Mock no acceptances
        mock_acceptance_repo.get_all_by_user.return_value = []

        # Create use case
        use_case = CheckUserLegalCompliance(
            user_repository=mock_user_repo,
            legal_document_repository=mock_doc_repo,
            user_legal_acceptance_repository=mock_acceptance_repo,
        )

        # Execute use case
        is_compliant, pending_docs = await use_case.execute(user_id=user_id)

        # Assertions
        assert is_compliant is True
        assert len(pending_docs) == 0
        self.reporter.info(
            "User compliant with no active documents",
            context="Test",
        )

    async def test_pending_documents_only_include_active(self):
        """Test pending documents only include active ones."""
        self.reporter.info(
            "Testing pending documents are only active",
            context="Test",
        )

        # Mock repositories
        mock_user_repo = AsyncMock()
        mock_doc_repo = AsyncMock()
        mock_acceptance_repo = AsyncMock()

        # Test data
        user_id = uuid4()
        active_doc_id = uuid4()
        archived_doc_id = uuid4()

        # Mock user exists
        user = User(wallet_address="A" * 44, id=user_id)
        mock_user_repo.get_by_id.return_value = user

        # Mock only active document (archived not in list)
        active_doc = LegalDocument(
            id=active_doc_id,
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="2.0.0",
            title="Terms v2",
            content="New TOS",
            status=DocumentStatus.ACTIVE,
            effective_date=datetime.now(),
        )
        mock_doc_repo.get_all_active.return_value = [active_doc]

        # Mock acceptance of archived document only
        acceptance = UserLegalAcceptance(user_id=user_id, document_id=archived_doc_id)
        mock_acceptance_repo.get_all_by_user.return_value = [acceptance]

        # Create use case
        use_case = CheckUserLegalCompliance(
            user_repository=mock_user_repo,
            legal_document_repository=mock_doc_repo,
            user_legal_acceptance_repository=mock_acceptance_repo,
        )

        # Execute use case
        is_compliant, pending_docs = await use_case.execute(user_id=user_id)

        # Assertions
        assert is_compliant is False
        assert len(pending_docs) == 1
        assert pending_docs[0].id == active_doc_id
        self.reporter.info(
            "Only active documents in pending list",
            context="Test",
        )

    # ============================================================
    # Error tests
    # ============================================================

    async def test_check_compliance_with_nonexistent_user(self):
        """Test checking compliance with non-existent user."""
        self.reporter.info(
            "Testing non-existent user error",
            context="Test",
        )

        # Mock repositories
        mock_user_repo = AsyncMock()
        mock_doc_repo = AsyncMock()
        mock_acceptance_repo = AsyncMock()

        # Mock user not found
        user_id = uuid4()
        mock_user_repo.get_by_id.return_value = None

        # Create use case
        use_case = CheckUserLegalCompliance(
            user_repository=mock_user_repo,
            legal_document_repository=mock_doc_repo,
            user_legal_acceptance_repository=mock_acceptance_repo,
        )

        # Execute use case and expect exception
        try:
            await use_case.execute(user_id=user_id)
            assert False, "Should have raised EntityNotFoundError"
        except EntityNotFoundError as e:
            assert "User" in str(e)
            assert str(user_id) in str(e)
            self.reporter.info("User not found error raised", context="Test")


if __name__ == "__main__":
    TestCheckUserLegalCompliance.run_as_main()

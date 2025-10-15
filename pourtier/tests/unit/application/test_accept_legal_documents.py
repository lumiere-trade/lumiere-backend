"""
Unit tests for AcceptLegalDocuments use case.

Tests recording user acceptance of legal documents.

Usage:
    python -m pourtier.tests.unit.application.test_accept_legal_documents
    laborant pourtier --unit
"""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from pourtier.application.use_cases.accept_legal_documents import (
    AcceptLegalDocuments,
)
from pourtier.domain.entities.legal_document import (
    DocumentStatus,
    DocumentType,
    LegalDocument,
)
from pourtier.domain.entities.user import User
from pourtier.domain.entities.user_legal_acceptance import (
    AcceptanceMethod,
    UserLegalAcceptance,
)
from pourtier.domain.exceptions.base import EntityNotFoundError
from shared.tests import LaborantTest


class TestAcceptLegalDocuments(LaborantTest):
    """Unit tests for AcceptLegalDocuments use case."""

    component_name = "pourtier"
    test_category = "unit"

    # ============================================================
    # Success tests
    # ============================================================

    async def test_accept_single_document_success(self):
        """Test accepting single document successfully."""
        self.reporter.info(
            "Testing accept single document",
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

        # Mock document exists
        doc = LegalDocument(
            id=doc_id,
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Terms",
            content="Content",
            status=DocumentStatus.ACTIVE,
            effective_date=datetime.now(),
        )
        mock_doc_repo.get_by_id.return_value = doc

        # Mock no existing acceptance
        mock_acceptance_repo.get_by_user_and_document.return_value = None

        # Mock create acceptance
        acceptance = UserLegalAcceptance(
            user_id=user_id,
            document_id=doc_id,
        )
        mock_acceptance_repo.create.return_value = acceptance

        # Create use case
        use_case = AcceptLegalDocuments(
            user_repository=mock_user_repo,
            legal_document_repository=mock_doc_repo,
            user_legal_acceptance_repository=mock_acceptance_repo,
        )

        # Execute use case
        result = await use_case.execute(
            user_id=user_id,
            document_ids=[doc_id],
            acceptance_method=AcceptanceMethod.WEB_CHECKBOX,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        # Assertions
        assert len(result) == 1
        assert result[0] == acceptance
        mock_user_repo.get_by_id.assert_called_once_with(user_id)
        mock_doc_repo.get_by_id.assert_called_once_with(doc_id)
        mock_acceptance_repo.create.assert_called_once()
        self.reporter.info("Document accepted successfully", context="Test")

    async def test_accept_multiple_documents_success(self):
        """Test accepting multiple documents successfully."""
        self.reporter.info(
            "Testing accept multiple documents",
            context="Test",
        )

        # Mock repositories
        mock_user_repo = AsyncMock()
        mock_doc_repo = AsyncMock()
        mock_acceptance_repo = AsyncMock()

        # Mock user exists
        user_id = uuid4()
        user = User(wallet_address="A" * 44, id=user_id)
        mock_user_repo.get_by_id.return_value = user

        # Create multiple documents
        doc1_id = uuid4()
        doc2_id = uuid4()

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

        # Mock document lookups
        def get_doc_by_id(doc_id):
            if doc_id == doc1_id:
                return doc1
            elif doc_id == doc2_id:
                return doc2
            return None

        mock_doc_repo.get_by_id.side_effect = get_doc_by_id

        # Mock no existing acceptances
        mock_acceptance_repo.get_by_user_and_document.return_value = None

        # Mock create acceptances
        acceptance1 = UserLegalAcceptance(user_id=user_id, document_id=doc1_id)
        acceptance2 = UserLegalAcceptance(user_id=user_id, document_id=doc2_id)

        mock_acceptance_repo.create.side_effect = [
            acceptance1,
            acceptance2,
        ]

        # Create use case
        use_case = AcceptLegalDocuments(
            user_repository=mock_user_repo,
            legal_document_repository=mock_doc_repo,
            user_legal_acceptance_repository=mock_acceptance_repo,
        )

        # Execute use case
        result = await use_case.execute(
            user_id=user_id,
            document_ids=[doc1_id, doc2_id],
        )

        # Assertions
        assert len(result) == 2
        assert mock_acceptance_repo.create.call_count == 2
        self.reporter.info(
            "Multiple documents accepted",
            context="Test",
        )

    # ============================================================
    # Already accepted tests
    # ============================================================

    async def test_accept_already_accepted_document_returns_existing(self):
        """Test accepting already accepted document returns existing."""
        self.reporter.info(
            "Testing already accepted document",
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

        # Mock document exists
        doc = LegalDocument(
            id=doc_id,
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Terms",
            content="Content",
            status=DocumentStatus.ACTIVE,
            effective_date=datetime.now(),
        )
        mock_doc_repo.get_by_id.return_value = doc

        # Mock existing acceptance
        existing_acceptance = UserLegalAcceptance(
            user_id=user_id,
            document_id=doc_id,
        )
        mock_acceptance_repo.get_by_user_and_document.return_value = existing_acceptance

        # Create use case
        use_case = AcceptLegalDocuments(
            user_repository=mock_user_repo,
            legal_document_repository=mock_doc_repo,
            user_legal_acceptance_repository=mock_acceptance_repo,
        )

        # Execute use case
        result = await use_case.execute(
            user_id=user_id,
            document_ids=[doc_id],
        )

        # Assertions
        assert len(result) == 1
        assert result[0] == existing_acceptance
        # Should NOT call create
        mock_acceptance_repo.create.assert_not_called()
        self.reporter.info(
            "Existing acceptance returned",
            context="Test",
        )

    # ============================================================
    # Error tests
    # ============================================================

    async def test_accept_with_nonexistent_user_raises_error(self):
        """Test accepting with non-existent user raises error."""
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
        doc_id = uuid4()
        mock_user_repo.get_by_id.return_value = None

        # Create use case
        use_case = AcceptLegalDocuments(
            user_repository=mock_user_repo,
            legal_document_repository=mock_doc_repo,
            user_legal_acceptance_repository=mock_acceptance_repo,
        )

        # Execute use case and expect exception
        try:
            await use_case.execute(
                user_id=user_id,
                document_ids=[doc_id],
            )
            assert False, "Should have raised EntityNotFoundError"
        except EntityNotFoundError as e:
            assert "User" in str(e)
            assert str(user_id) in str(e)
            self.reporter.info("User not found error raised", context="Test")

    async def test_accept_with_nonexistent_document_raises_error(self):
        """Test accepting with non-existent document raises error."""
        self.reporter.info(
            "Testing non-existent document error",
            context="Test",
        )

        # Mock repositories
        mock_user_repo = AsyncMock()
        mock_doc_repo = AsyncMock()
        mock_acceptance_repo = AsyncMock()

        # Mock user exists
        user_id = uuid4()
        doc_id = uuid4()
        user = User(wallet_address="A" * 44, id=user_id)
        mock_user_repo.get_by_id.return_value = user

        # Mock document not found
        mock_doc_repo.get_by_id.return_value = None

        # Create use case
        use_case = AcceptLegalDocuments(
            user_repository=mock_user_repo,
            legal_document_repository=mock_doc_repo,
            user_legal_acceptance_repository=mock_acceptance_repo,
        )

        # Execute use case and expect exception
        try:
            await use_case.execute(
                user_id=user_id,
                document_ids=[doc_id],
            )
            assert False, "Should have raised EntityNotFoundError"
        except EntityNotFoundError as e:
            assert "LegalDocument" in str(e)
            assert str(doc_id) in str(e)
            self.reporter.info(
                "Document not found error raised",
                context="Test",
            )

    # ============================================================
    # Audit trail tests
    # ============================================================

    async def test_accept_with_ip_and_user_agent(self):
        """Test accept stores IP address and user agent."""
        self.reporter.info(
            "Testing IP and user agent storage",
            context="Test",
        )

        # Mock repositories
        mock_user_repo = AsyncMock()
        mock_doc_repo = AsyncMock()
        mock_acceptance_repo = AsyncMock()

        # Test data
        user_id = uuid4()
        doc_id = uuid4()

        # Mock user and document
        user = User(wallet_address="A" * 44, id=user_id)
        mock_user_repo.get_by_id.return_value = user

        doc = LegalDocument(
            id=doc_id,
            document_type=DocumentType.TERMS_OF_SERVICE,
            version="1.0.0",
            title="Terms",
            content="Content",
            status=DocumentStatus.ACTIVE,
            effective_date=datetime.now(),
        )
        mock_doc_repo.get_by_id.return_value = doc

        # Mock no existing acceptance
        mock_acceptance_repo.get_by_user_and_document.return_value = None

        # Capture created acceptance
        created_acceptance = None

        def capture_create(acceptance):
            nonlocal created_acceptance
            created_acceptance = acceptance
            return acceptance

        mock_acceptance_repo.create.side_effect = capture_create

        # Create use case
        use_case = AcceptLegalDocuments(
            user_repository=mock_user_repo,
            legal_document_repository=mock_doc_repo,
            user_legal_acceptance_repository=mock_acceptance_repo,
        )

        # Execute with audit data
        ip = "203.0.113.42"
        user_agent = "Mozilla/5.0 (X11; Linux x86_64)"

        await use_case.execute(
            user_id=user_id,
            document_ids=[doc_id],
            ip_address=ip,
            user_agent=user_agent,
        )

        # Verify audit data was passed
        assert created_acceptance is not None
        assert created_acceptance.ip_address == ip
        assert created_acceptance.user_agent == user_agent
        self.reporter.info("Audit data stored correctly", context="Test")


if __name__ == "__main__":
    TestAcceptLegalDocuments.run_as_main()

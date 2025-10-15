"""
Unit tests for UserLegalAcceptance entity.

Tests acceptance creation, validation, and audit trail.

Usage:
    python -m pourtier.tests.unit.domain.entities.test_user_legal_acceptance
    laborant pourtier --unit
"""

from datetime import datetime
from uuid import UUID, uuid4

from pourtier.domain.entities.user_legal_acceptance import (
    AcceptanceMethod,
    UserLegalAcceptance,
)
from shared.tests import LaborantTest


class TestUserLegalAcceptance(LaborantTest):
    """Unit tests for UserLegalAcceptance entity."""

    component_name = "pourtier"
    test_category = "unit"

    # ============================================================
    # Creation tests
    # ============================================================

    def test_create_acceptance_with_required_fields(self):
        """Test creating UserLegalAcceptance with required fields."""
        self.reporter.info(
            "Testing acceptance creation",
            context="Test",
        )

        user_id = uuid4()
        doc_id = uuid4()

        acceptance = UserLegalAcceptance(
            user_id=user_id,
            document_id=doc_id,
        )

        assert acceptance.user_id == user_id
        assert acceptance.document_id == doc_id
        assert isinstance(acceptance.id, UUID)
        assert isinstance(acceptance.accepted_at, datetime)
        self.reporter.info("Acceptance created", context="Test")

    def test_acceptance_auto_generates_id(self):
        """Test UserLegalAcceptance auto-generates UUID."""
        self.reporter.info("Testing auto-generated UUID", context="Test")

        acceptance = UserLegalAcceptance(
            user_id=uuid4(),
            document_id=uuid4(),
        )

        assert isinstance(acceptance.id, UUID)
        assert acceptance.id is not None
        self.reporter.info(f"Generated UUID: {acceptance.id}", context="Test")

    def test_acceptance_auto_generates_timestamp(self):
        """Test UserLegalAcceptance auto-generates accepted_at."""
        self.reporter.info(
            "Testing auto-generated timestamp",
            context="Test",
        )

        before = datetime.now()
        acceptance = UserLegalAcceptance(
            user_id=uuid4(),
            document_id=uuid4(),
        )
        after = datetime.now()

        assert isinstance(acceptance.accepted_at, datetime)
        assert before <= acceptance.accepted_at <= after
        self.reporter.info("Timestamp auto-generated", context="Test")

    def test_acceptance_default_method_is_web_checkbox(self):
        """Test default acceptance_method is WEB_CHECKBOX."""
        self.reporter.info("Testing default acceptance method", context="Test")

        acceptance = UserLegalAcceptance(
            user_id=uuid4(),
            document_id=uuid4(),
        )

        assert acceptance.acceptance_method == AcceptanceMethod.WEB_CHECKBOX
        self.reporter.info(
            "Default method is WEB_CHECKBOX",
            context="Test",
        )

    # ============================================================
    # Acceptance method tests
    # ============================================================

    def test_web_checkbox_acceptance_method(self):
        """Test WEB_CHECKBOX acceptance method."""
        self.reporter.info(
            "Testing WEB_CHECKBOX method",
            context="Test",
        )

        acceptance = UserLegalAcceptance(
            user_id=uuid4(),
            document_id=uuid4(),
            acceptance_method=AcceptanceMethod.WEB_CHECKBOX,
        )

        assert acceptance.acceptance_method == AcceptanceMethod.WEB_CHECKBOX
        assert acceptance.acceptance_method.value == "web_checkbox"
        self.reporter.info("WEB_CHECKBOX method works", context="Test")

    def test_api_explicit_acceptance_method(self):
        """Test API_EXPLICIT acceptance method."""
        self.reporter.info("Testing API_EXPLICIT method", context="Test")

        acceptance = UserLegalAcceptance(
            user_id=uuid4(),
            document_id=uuid4(),
            acceptance_method=AcceptanceMethod.API_EXPLICIT,
        )

        assert acceptance.acceptance_method == AcceptanceMethod.API_EXPLICIT
        assert acceptance.acceptance_method.value == "api_explicit"
        self.reporter.info("API_EXPLICIT method works", context="Test")

    def test_migration_implicit_acceptance_method(self):
        """Test MIGRATION_IMPLICIT acceptance method."""
        self.reporter.info(
            "Testing MIGRATION_IMPLICIT method",
            context="Test",
        )

        acceptance = UserLegalAcceptance(
            user_id=uuid4(),
            document_id=uuid4(),
            acceptance_method=AcceptanceMethod.MIGRATION_IMPLICIT,
        )

        assert acceptance.acceptance_method == AcceptanceMethod.MIGRATION_IMPLICIT
        assert acceptance.acceptance_method.value == "migration_implicit"
        self.reporter.info("MIGRATION_IMPLICIT method works", context="Test")

    # ============================================================
    # Audit trail tests
    # ============================================================

    def test_acceptance_with_ip_address(self):
        """Test UserLegalAcceptance stores IP address."""
        self.reporter.info("Testing IP address storage", context="Test")

        ip = "192.168.1.100"
        acceptance = UserLegalAcceptance(
            user_id=uuid4(),
            document_id=uuid4(),
            ip_address=ip,
        )

        assert acceptance.ip_address == ip
        self.reporter.info("IP address stored", context="Test")

    def test_acceptance_with_user_agent(self):
        """Test UserLegalAcceptance stores user agent."""
        self.reporter.info("Testing user agent storage", context="Test")

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        acceptance = UserLegalAcceptance(
            user_id=uuid4(),
            document_id=uuid4(),
            user_agent=user_agent,
        )

        assert acceptance.user_agent == user_agent
        self.reporter.info("User agent stored", context="Test")

    def test_acceptance_with_full_audit_trail(self):
        """Test UserLegalAcceptance with complete audit trail."""
        self.reporter.info(
            "Testing complete audit trail",
            context="Test",
        )

        user_id = uuid4()
        doc_id = uuid4()
        ip = "203.0.113.42"
        user_agent = "Mozilla/5.0 (X11; Linux x86_64)"

        acceptance = UserLegalAcceptance(
            user_id=user_id,
            document_id=doc_id,
            acceptance_method=AcceptanceMethod.WEB_CHECKBOX,
            ip_address=ip,
            user_agent=user_agent,
        )

        assert acceptance.user_id == user_id
        assert acceptance.document_id == doc_id
        assert acceptance.acceptance_method == AcceptanceMethod.WEB_CHECKBOX
        assert acceptance.ip_address == ip
        assert acceptance.user_agent == user_agent
        assert isinstance(acceptance.accepted_at, datetime)
        self.reporter.info("Full audit trail recorded", context="Test")

    def test_acceptance_without_ip_is_valid(self):
        """Test UserLegalAcceptance is valid without IP."""
        self.reporter.info(
            "Testing acceptance without IP",
            context="Test",
        )

        acceptance = UserLegalAcceptance(
            user_id=uuid4(),
            document_id=uuid4(),
            ip_address=None,
        )

        assert acceptance.ip_address is None
        self.reporter.info("Acceptance without IP is valid", context="Test")

    def test_acceptance_without_user_agent_is_valid(self):
        """Test UserLegalAcceptance is valid without user agent."""
        self.reporter.info(
            "Testing acceptance without user agent",
            context="Test",
        )

        acceptance = UserLegalAcceptance(
            user_id=uuid4(),
            document_id=uuid4(),
            user_agent=None,
        )

        assert acceptance.user_agent is None
        self.reporter.info(
            "Acceptance without user agent is valid",
            context="Test",
        )

    # ============================================================
    # IPv6 address tests
    # ============================================================

    def test_acceptance_with_ipv6_address(self):
        """Test UserLegalAcceptance stores IPv6 address."""
        self.reporter.info("Testing IPv6 address storage", context="Test")

        ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        acceptance = UserLegalAcceptance(
            user_id=uuid4(),
            document_id=uuid4(),
            ip_address=ipv6,
        )

        assert acceptance.ip_address == ipv6
        self.reporter.info("IPv6 address stored", context="Test")

    def test_acceptance_with_compressed_ipv6(self):
        """Test UserLegalAcceptance stores compressed IPv6."""
        self.reporter.info(
            "Testing compressed IPv6 storage",
            context="Test",
        )

        ipv6 = "2001:db8::8a2e:370:7334"
        acceptance = UserLegalAcceptance(
            user_id=uuid4(),
            document_id=uuid4(),
            ip_address=ipv6,
        )

        assert acceptance.ip_address == ipv6
        self.reporter.info("Compressed IPv6 stored", context="Test")

    # ============================================================
    # Serialization tests
    # ============================================================

    def test_to_dict_serialization(self):
        """Test to_dict() returns correct dictionary."""
        self.reporter.info("Testing to_dict() serialization", context="Test")

        user_id = uuid4()
        doc_id = uuid4()
        ip = "198.51.100.50"
        user_agent = "Mozilla/5.0"

        acceptance = UserLegalAcceptance(
            user_id=user_id,
            document_id=doc_id,
            acceptance_method=AcceptanceMethod.API_EXPLICIT,
            ip_address=ip,
            user_agent=user_agent,
        )

        result = acceptance.to_dict()

        assert result["id"] == str(acceptance.id)
        assert result["user_id"] == str(user_id)
        assert result["document_id"] == str(doc_id)
        assert result["acceptance_method"] == "api_explicit"
        assert result["ip_address"] == ip
        assert result["user_agent"] == user_agent
        assert "accepted_at" in result
        assert "created_at" in result
        self.reporter.info("to_dict() serialization correct", context="Test")

    def test_to_dict_timestamps_iso_format(self):
        """Test to_dict() timestamps are ISO format strings."""
        self.reporter.info("Testing to_dict() timestamp format", context="Test")

        acceptance = UserLegalAcceptance(
            user_id=uuid4(),
            document_id=uuid4(),
        )

        result = acceptance.to_dict()

        assert isinstance(result["accepted_at"], str)
        assert isinstance(result["created_at"], str)
        assert "T" in result["accepted_at"]
        assert "T" in result["created_at"]
        self.reporter.info("Timestamps in ISO format", context="Test")

    def test_to_dict_with_null_audit_fields(self):
        """Test to_dict() with null IP and user agent."""
        self.reporter.info(
            "Testing to_dict() with null audit fields",
            context="Test",
        )

        acceptance = UserLegalAcceptance(
            user_id=uuid4(),
            document_id=uuid4(),
        )

        result = acceptance.to_dict()

        assert result["ip_address"] is None
        assert result["user_agent"] is None
        self.reporter.info(
            "to_dict() handles null audit fields",
            context="Test",
        )

    # ============================================================
    # Immutability tests (audit trail should not change)
    # ============================================================

    def test_acceptance_timestamp_immutable(self):
        """Test accepted_at timestamp should not change."""
        self.reporter.info(
            "Testing accepted_at immutability",
            context="Test",
        )

        acceptance = UserLegalAcceptance(
            user_id=uuid4(),
            document_id=uuid4(),
        )

        original_time = acceptance.accepted_at

        # Simulate time passing (though timestamp shouldn't auto-update)
        import time

        time.sleep(0.01)

        # accepted_at should remain the same
        assert acceptance.accepted_at == original_time
        self.reporter.info(
            "accepted_at timestamp is immutable",
            context="Test",
        )

    def test_two_acceptances_different_ids(self):
        """Test two acceptances have different IDs."""
        self.reporter.info(
            "Testing two acceptances have different IDs",
            context="Test",
        )

        user_id = uuid4()
        doc_id = uuid4()

        acceptance1 = UserLegalAcceptance(
            user_id=user_id,
            document_id=doc_id,
        )
        acceptance2 = UserLegalAcceptance(
            user_id=user_id,
            document_id=doc_id,
        )

        assert acceptance1.id != acceptance2.id
        self.reporter.info(
            "Different acceptances have different IDs",
            context="Test",
        )

    # ============================================================
    # Edge case tests
    # ============================================================

    def test_acceptance_with_very_long_user_agent(self):
        """Test UserLegalAcceptance with very long user agent."""
        self.reporter.info(
            "Testing very long user agent",
            context="Test",
        )

        long_user_agent = "A" * 500  # Max length in schema
        acceptance = UserLegalAcceptance(
            user_id=uuid4(),
            document_id=uuid4(),
            user_agent=long_user_agent,
        )

        assert acceptance.user_agent == long_user_agent
        assert len(acceptance.user_agent) == 500
        self.reporter.info("Long user agent stored", context="Test")

    def test_acceptance_with_empty_string_ip(self):
        """Test UserLegalAcceptance with empty string IP."""
        self.reporter.info(
            "Testing empty string IP address",
            context="Test",
        )

        acceptance = UserLegalAcceptance(
            user_id=uuid4(),
            document_id=uuid4(),
            ip_address="",
        )

        assert acceptance.ip_address == ""
        self.reporter.info("Empty string IP stored", context="Test")


if __name__ == "__main__":
    TestUserLegalAcceptance.run_as_main()

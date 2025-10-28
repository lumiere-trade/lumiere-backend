"""
Unit tests for Publish DTOs.

Tests PublishEventRequest and PublishEventResponse validation and properties.

Usage:
    python -m courier.tests.unit.application.dto.test_publish_dto
    laborant courier --unit
"""

from datetime import datetime

from pydantic import ValidationError
from shared.tests import LaborantTest

from courier.application.dto.publish_dto import (
    PublishEventRequest,
    PublishEventResponse,
)


class TestPublishEventRequest(LaborantTest):
    """Unit tests for PublishEventRequest DTO."""

    component_name = "courier"
    test_category = "unit"

    # ================================================================
    # Creation tests
    # ================================================================

    def test_create_request_with_valid_data(self):
        """Test creating request with valid channel and data."""
        self.reporter.info("Testing valid request creation", context="Test")

        request = PublishEventRequest(
            channel="user.123", data={"type": "trade", "amount": 100}
        )

        assert request.channel == "user.123"
        assert request.data == {"type": "trade", "amount": 100}
        self.reporter.info("Request created successfully", context="Test")

    def test_create_request_minimal_data(self):
        """Test creating request with minimal required fields."""
        self.reporter.info("Testing minimal request", context="Test")

        request = PublishEventRequest(channel="global", data={"event": "ping"})

        assert request.channel == "global"
        assert request.data == {"event": "ping"}
        self.reporter.info("Minimal request created", context="Test")

    def test_create_request_complex_data(self):
        """Test creating request with nested data structure."""
        self.reporter.info("Testing complex data structure", context="Test")

        complex_data = {
            "type": "strategy.update",
            "payload": {"id": "abc", "status": "active", "metrics": [1, 2, 3]},
        }
        request = PublishEventRequest(channel="strategy.abc", data=complex_data)

        assert request.data == complex_data
        self.reporter.info("Complex data handled correctly", context="Test")

    # ================================================================
    # Validation tests
    # ================================================================

    def test_request_requires_channel(self):
        """Test request validation fails without channel."""
        self.reporter.info("Testing missing channel validation", context="Test")

        try:
            PublishEventRequest(data={"type": "test"})
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "channel" in str(e)
            self.reporter.info(
                "Validation correctly rejected missing channel", context="Test"
            )

    def test_request_requires_data(self):
        """Test request validation fails without data."""
        self.reporter.info("Testing missing data validation", context="Test")

        try:
            PublishEventRequest(channel="test")
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "data" in str(e)
            self.reporter.info(
                "Validation correctly rejected missing data", context="Test"
            )

    def test_request_rejects_invalid_data_type(self):
        """Test request validation fails with non-dict data."""
        self.reporter.info("Testing invalid data type", context="Test")

        try:
            PublishEventRequest(channel="test", data="invalid")
            assert False, "Should have raised ValidationError"
        except ValidationError:
            self.reporter.info(
                "Validation correctly rejected non-dict data", context="Test"
            )

    def test_request_rejects_empty_channel(self):
        """Test request validation fails with empty channel."""
        self.reporter.info("Testing empty channel validation", context="Test")

        try:
            PublishEventRequest(channel="", data={"type": "test"})
            assert False, "Should have raised ValidationError"
        except ValidationError:
            self.reporter.info(
                "Validation correctly rejected empty channel", context="Test"
            )

    # ================================================================
    # Serialization tests
    # ================================================================

    def test_request_to_dict(self):
        """Test request serialization to dict."""
        self.reporter.info("Testing request serialization", context="Test")

        request = PublishEventRequest(channel="user.123", data={"type": "notification"})
        request_dict = request.model_dump()

        assert request_dict["channel"] == "user.123"
        assert request_dict["data"] == {"type": "notification"}
        self.reporter.info("Request serialized correctly", context="Test")

    def test_request_from_dict(self):
        """Test request deserialization from dict."""
        self.reporter.info("Testing request deserialization", context="Test")

        data = {"channel": "global", "data": {"message": "hello"}}
        request = PublishEventRequest(**data)

        assert request.channel == "global"
        assert request.data == {"message": "hello"}
        self.reporter.info("Request deserialized correctly", context="Test")

    # ================================================================
    # Edge cases
    # ================================================================

    def test_request_with_empty_data_dict(self):
        """Test request with empty data dictionary."""
        self.reporter.info("Testing empty data dict", context="Test")

        request = PublishEventRequest(channel="test", data={})

        assert request.data == {}
        self.reporter.info("Empty data dict accepted", context="Test")

    def test_request_data_immutability_via_copy(self):
        """Test that modifying original data doesn't affect request."""
        self.reporter.info("Testing data immutability", context="Test")

        original_data = {"type": "test", "value": 1}
        request = PublishEventRequest(channel="test", data=original_data)

        original_data["value"] = 999

        assert request.data["value"] == 1
        self.reporter.info(
            "Request data protected from external changes", context="Test"
        )


class TestPublishEventResponse(LaborantTest):
    """Unit tests for PublishEventResponse DTO."""

    component_name = "courier"
    test_category = "unit"

    # ================================================================
    # Creation tests
    # ================================================================

    def test_create_response_with_required_fields(self):
        """Test creating response with required fields."""
        self.reporter.info("Testing response creation", context="Test")

        response = PublishEventResponse(channel="user.123", clients_reached=5)

        assert response.channel == "user.123"
        assert response.clients_reached == 5
        assert response.status == "published"
        assert isinstance(response.timestamp, str)
        self.reporter.info("Response created successfully", context="Test")

    def test_response_auto_generates_timestamp(self):
        """Test response auto-generates ISO timestamp."""
        self.reporter.info("Testing auto-generated timestamp", context="Test")

        response = PublishEventResponse(channel="global", clients_reached=10)

        assert isinstance(response.timestamp, str)
        datetime.fromisoformat(response.timestamp)
        self.reporter.info(f"Generated timestamp: {response.timestamp}", context="Test")

    def test_response_default_status(self):
        """Test response defaults to 'published' status."""
        self.reporter.info("Testing default status", context="Test")

        response = PublishEventResponse(channel="test", clients_reached=0)

        assert response.status == "published"
        self.reporter.info("Default status set correctly", context="Test")

    def test_create_response_with_custom_status(self):
        """Test creating response with custom status."""
        self.reporter.info("Testing custom status", context="Test")

        response = PublishEventResponse(
            status="queued", channel="strategy.abc", clients_reached=3
        )

        assert response.status == "queued"
        self.reporter.info("Custom status accepted", context="Test")

    def test_create_response_with_custom_timestamp(self):
        """Test creating response with custom timestamp."""
        self.reporter.info("Testing custom timestamp", context="Test")

        custom_time = "2024-01-01T12:00:00"
        response = PublishEventResponse(
            channel="test", clients_reached=1, timestamp=custom_time
        )

        assert response.timestamp == custom_time
        self.reporter.info("Custom timestamp accepted", context="Test")

    # ================================================================
    # Validation tests
    # ================================================================

    def test_response_requires_channel(self):
        """Test response validation fails without channel."""
        self.reporter.info("Testing missing channel validation", context="Test")

        try:
            PublishEventResponse(clients_reached=5)
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "channel" in str(e)
            self.reporter.info(
                "Validation correctly rejected missing channel", context="Test"
            )

    def test_response_requires_clients_reached(self):
        """Test response validation fails without clients_reached."""
        self.reporter.info("Testing missing clients_reached validation", context="Test")

        try:
            PublishEventResponse(channel="test")
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "clients_reached" in str(e)
            self.reporter.info(
                "Validation correctly rejected missing clients_reached", context="Test"
            )

    def test_response_rejects_negative_clients_reached(self):
        """Test response validation fails with negative clients_reached."""
        self.reporter.info("Testing negative clients_reached", context="Test")

        try:
            PublishEventResponse(channel="test", clients_reached=-1)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            self.reporter.info(
                "Validation correctly rejected negative value", context="Test"
            )

    def test_response_accepts_zero_clients_reached(self):
        """Test response accepts zero clients_reached."""
        self.reporter.info("Testing zero clients_reached", context="Test")

        response = PublishEventResponse(channel="test", clients_reached=0)

        assert response.clients_reached == 0
        self.reporter.info("Zero clients_reached accepted", context="Test")

    # ================================================================
    # Serialization tests
    # ================================================================

    def test_response_to_dict(self):
        """Test response serialization to dict."""
        self.reporter.info("Testing response serialization", context="Test")

        response = PublishEventResponse(
            status="published",
            channel="user.123",
            clients_reached=5,
            timestamp="2024-01-01T12:00:00",
        )
        response_dict = response.model_dump()

        assert response_dict["status"] == "published"
        assert response_dict["channel"] == "user.123"
        assert response_dict["clients_reached"] == 5
        assert response_dict["timestamp"] == "2024-01-01T12:00:00"
        self.reporter.info("Response serialized correctly", context="Test")

    def test_response_from_dict(self):
        """Test response deserialization from dict."""
        self.reporter.info("Testing response deserialization", context="Test")

        data = {
            "status": "queued",
            "channel": "global",
            "clients_reached": 10,
            "timestamp": "2024-01-01T12:00:00",
        }
        response = PublishEventResponse(**data)

        assert response.status == "queued"
        assert response.channel == "global"
        assert response.clients_reached == 10
        self.reporter.info("Response deserialized correctly", context="Test")

    # ================================================================
    # Edge cases
    # ================================================================

    def test_response_with_large_clients_reached(self):
        """Test response with very large clients_reached value."""
        self.reporter.info("Testing large clients_reached value", context="Test")

        response = PublishEventResponse(channel="global", clients_reached=1000000)

        assert response.clients_reached == 1000000
        self.reporter.info("Large value handled correctly", context="Test")

    def test_timestamp_is_valid_iso_format(self):
        """Test auto-generated timestamp is valid ISO format."""
        self.reporter.info("Testing ISO timestamp format", context="Test")

        response = PublishEventResponse(channel="test", clients_reached=1)

        try:
            parsed = datetime.fromisoformat(response.timestamp)
            assert isinstance(parsed, datetime)
            self.reporter.info("Timestamp is valid ISO format", context="Test")
        except ValueError:
            assert False, "Timestamp should be valid ISO format"


if __name__ == "__main__":
    TestPublishEventRequest.run_as_main()
    TestPublishEventResponse.run_as_main()

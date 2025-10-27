"""
Unit tests for channel exceptions.

Tests channel exception creation and properties.

Usage:
    python -m courier.tests.unit.domain.exceptions.test_channel_exceptions
    laborant courier --unit
"""

from shared.tests import LaborantTest

from courier.domain.exceptions.channel_exceptions import (
    ChannelError,
    ChannelNotFoundError,
    InvalidChannelNameError,
)


class TestChannelExceptions(LaborantTest):
    """Unit tests for channel exceptions."""

    component_name = "courier"
    test_category = "unit"

    # ================================================================
    # ChannelError tests
    # ================================================================

    def test_channel_error_is_exception(self):
        """Test ChannelError is an Exception."""
        self.reporter.info("Testing ChannelError base class", context="Test")

        error = ChannelError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"
        self.reporter.info("ChannelError is Exception", context="Test")

    # ================================================================
    # ChannelNotFoundError tests
    # ================================================================

    def test_channel_not_found_error_creation(self):
        """Test ChannelNotFoundError creation."""
        self.reporter.info("Testing ChannelNotFoundError creation", context="Test")

        error = ChannelNotFoundError(channel_name="user.123")

        assert isinstance(error, ChannelError)
        assert isinstance(error, Exception)
        assert error.channel_name == "user.123"
        self.reporter.info("ChannelNotFoundError created", context="Test")

    def test_channel_not_found_error_message(self):
        """Test ChannelNotFoundError message format."""
        self.reporter.info("Testing ChannelNotFoundError message", context="Test")

        error = ChannelNotFoundError(channel_name="strategy.abc")
        error_msg = str(error)

        assert "Channel not found" in error_msg
        assert "strategy.abc" in error_msg
        self.reporter.info(f"Error message: {error_msg}", context="Test")

    def test_channel_not_found_error_attribute_access(self):
        """Test ChannelNotFoundError channel_name attribute."""
        self.reporter.info(
            "Testing ChannelNotFoundError attribute access", context="Test"
        )

        channel_name = "forge.job.xyz-789"
        error = ChannelNotFoundError(channel_name=channel_name)

        assert error.channel_name == channel_name
        self.reporter.info("channel_name attribute accessible", context="Test")

    # ================================================================
    # InvalidChannelNameError tests
    # ================================================================

    def test_invalid_channel_name_error_creation(self):
        """Test InvalidChannelNameError creation."""
        self.reporter.info("Testing InvalidChannelNameError creation", context="Test")

        error = InvalidChannelNameError(
            channel_name="User.123", reason="contains uppercase letters"
        )

        assert isinstance(error, ChannelError)
        assert isinstance(error, Exception)
        assert error.channel_name == "User.123"
        assert error.reason == "contains uppercase letters"
        self.reporter.info("InvalidChannelNameError created", context="Test")

    def test_invalid_channel_name_error_message(self):
        """Test InvalidChannelNameError message format."""
        self.reporter.info("Testing InvalidChannelNameError message", context="Test")

        error = InvalidChannelNameError(
            channel_name="user@123", reason="contains invalid character '@'"
        )
        error_msg = str(error)

        assert "Invalid channel name" in error_msg
        assert "user@123" in error_msg
        assert "contains invalid character '@'" in error_msg
        self.reporter.info(f"Error message: {error_msg}", context="Test")

    def test_invalid_channel_name_error_attributes(self):
        """Test InvalidChannelNameError attributes."""
        self.reporter.info("Testing InvalidChannelNameError attributes", context="Test")

        channel_name = "too long name" * 20
        reason = "exceeds maximum length"
        error = InvalidChannelNameError(channel_name=channel_name, reason=reason)

        assert error.channel_name == channel_name
        assert error.reason == reason
        self.reporter.info("Attributes accessible", context="Test")

    # ================================================================
    # Exception hierarchy tests
    # ================================================================

    def test_exception_hierarchy(self):
        """Test exception inheritance hierarchy."""
        self.reporter.info("Testing exception hierarchy", context="Test")

        # ChannelNotFoundError
        not_found = ChannelNotFoundError(channel_name="test")
        assert isinstance(not_found, ChannelError)
        assert isinstance(not_found, Exception)

        # InvalidChannelNameError
        invalid = InvalidChannelNameError(channel_name="test", reason="test reason")
        assert isinstance(invalid, ChannelError)
        assert isinstance(invalid, Exception)

        self.reporter.info("Exception hierarchy correct", context="Test")

    # ================================================================
    # Exception catching tests
    # ================================================================

    def test_catch_channel_not_found_as_channel_error(self):
        """Test catching ChannelNotFoundError as ChannelError."""
        self.reporter.info(
            "Testing catching ChannelNotFoundError as base", context="Test"
        )

        try:
            raise ChannelNotFoundError(channel_name="test")
        except ChannelError as e:
            assert isinstance(e, ChannelNotFoundError)
            assert e.channel_name == "test"
            self.reporter.info("Caught as ChannelError", context="Test")

    def test_catch_invalid_channel_name_as_channel_error(self):
        """Test catching InvalidChannelNameError as ChannelError."""
        self.reporter.info(
            "Testing catching InvalidChannelNameError as base", context="Test"
        )

        try:
            raise InvalidChannelNameError(channel_name="Test", reason="uppercase")
        except ChannelError as e:
            assert isinstance(e, InvalidChannelNameError)
            assert e.channel_name == "Test"
            self.reporter.info("Caught as ChannelError", context="Test")

    # ================================================================
    # Various error scenarios tests
    # ================================================================

    def test_channel_not_found_global(self):
        """Test ChannelNotFoundError for global channel."""
        self.reporter.info("Testing ChannelNotFoundError for global", context="Test")

        error = ChannelNotFoundError(channel_name="global")
        assert "global" in str(error)
        self.reporter.info("Global channel error correct", context="Test")

    def test_channel_not_found_user_channel(self):
        """Test ChannelNotFoundError for user channel."""
        self.reporter.info(
            "Testing ChannelNotFoundError for user channel", context="Test"
        )

        error = ChannelNotFoundError(channel_name="user.abc123")
        assert "user.abc123" in str(error)
        self.reporter.info("User channel error correct", context="Test")

    def test_invalid_name_empty_string(self):
        """Test InvalidChannelNameError for empty string."""
        self.reporter.info(
            "Testing InvalidChannelNameError for empty string", context="Test"
        )

        error = InvalidChannelNameError(
            channel_name="", reason="channel name cannot be empty"
        )
        assert error.reason == "channel name cannot be empty"
        self.reporter.info("Empty string error correct", context="Test")

    def test_invalid_name_special_chars(self):
        """Test InvalidChannelNameError for special characters."""
        self.reporter.info(
            "Testing InvalidChannelNameError for special chars", context="Test"
        )

        error = InvalidChannelNameError(
            channel_name="user@#$123", reason="contains invalid characters"
        )
        assert "user@#$123" in str(error)
        assert "invalid characters" in str(error)
        self.reporter.info("Special chars error correct", context="Test")

    def test_invalid_name_uppercase(self):
        """Test InvalidChannelNameError for uppercase."""
        self.reporter.info(
            "Testing InvalidChannelNameError for uppercase", context="Test"
        )

        error = InvalidChannelNameError(
            channel_name="User.123", reason="must be lowercase"
        )
        assert "User.123" in str(error)
        assert "lowercase" in str(error)
        self.reporter.info("Uppercase error correct", context="Test")


if __name__ == "__main__":
    TestChannelExceptions.run_as_main()

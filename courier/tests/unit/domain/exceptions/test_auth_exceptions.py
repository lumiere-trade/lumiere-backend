"""
Unit tests for authentication exceptions.

Tests authentication exception creation and properties.

Usage:
    python -m courier.tests.unit.domain.exceptions.test_auth_exceptions
    laborant courier --unit
"""

from shared.tests import LaborantTest

from courier.domain.exceptions.auth_exceptions import (
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
    TokenInvalidError,
)


class TestAuthenticationExceptions(LaborantTest):
    """Unit tests for authentication exceptions."""

    component_name = "courier"
    test_category = "unit"

    # ================================================================
    # AuthenticationError tests
    # ================================================================

    def test_authentication_error_is_exception(self):
        """Test AuthenticationError is an Exception."""
        self.reporter.info("Testing AuthenticationError base class", context="Test")

        error = AuthenticationError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"
        self.reporter.info("AuthenticationError is Exception", context="Test")

    def test_authentication_error_with_message(self):
        """Test AuthenticationError with custom message."""
        self.reporter.info("Testing AuthenticationError message", context="Test")

        message = "Invalid credentials provided"
        error = AuthenticationError(message)

        assert str(error) == message
        self.reporter.info("Custom message works", context="Test")

    # ================================================================
    # TokenExpiredError tests
    # ================================================================

    def test_token_expired_error_creation(self):
        """Test TokenExpiredError creation."""
        self.reporter.info("Testing TokenExpiredError creation", context="Test")

        error = TokenExpiredError("Token has expired")

        assert isinstance(error, AuthenticationError)
        assert isinstance(error, Exception)
        assert str(error) == "Token has expired"
        self.reporter.info("TokenExpiredError created", context="Test")

    def test_token_expired_error_inheritance(self):
        """Test TokenExpiredError inherits from AuthenticationError."""
        self.reporter.info("Testing TokenExpiredError inheritance", context="Test")

        error = TokenExpiredError("Expired")

        assert isinstance(error, AuthenticationError)
        assert isinstance(error, Exception)
        self.reporter.info("Inheritance correct", context="Test")

    # ================================================================
    # TokenInvalidError tests
    # ================================================================

    def test_token_invalid_error_creation(self):
        """Test TokenInvalidError creation."""
        self.reporter.info("Testing TokenInvalidError creation", context="Test")

        error = TokenInvalidError("Token signature invalid")

        assert isinstance(error, AuthenticationError)
        assert isinstance(error, Exception)
        assert str(error) == "Token signature invalid"
        self.reporter.info("TokenInvalidError created", context="Test")

    def test_token_invalid_error_inheritance(self):
        """Test TokenInvalidError inherits from AuthenticationError."""
        self.reporter.info("Testing TokenInvalidError inheritance", context="Test")

        error = TokenInvalidError("Invalid")

        assert isinstance(error, AuthenticationError)
        assert isinstance(error, Exception)
        self.reporter.info("Inheritance correct", context="Test")

    # ================================================================
    # AuthorizationError tests
    # ================================================================

    def test_authorization_error_creation(self):
        """Test AuthorizationError creation."""
        self.reporter.info("Testing AuthorizationError creation", context="Test")

        error = AuthorizationError(
            message="Access denied", user_id="user-123", resource="channel.private"
        )

        assert isinstance(error, Exception)
        assert str(error) == "Access denied"
        assert error.user_id == "user-123"
        assert error.resource == "channel.private"
        self.reporter.info("AuthorizationError created", context="Test")

    def test_authorization_error_without_optional_fields(self):
        """Test AuthorizationError without user_id and resource."""
        self.reporter.info(
            "Testing AuthorizationError without optional fields", context="Test"
        )

        error = AuthorizationError(message="Forbidden")

        assert str(error) == "Forbidden"
        assert error.user_id is None
        assert error.resource is None
        self.reporter.info("Optional fields work", context="Test")

    def test_authorization_error_attributes(self):
        """Test AuthorizationError attributes access."""
        self.reporter.info("Testing AuthorizationError attributes", context="Test")

        user_id = "user-abc-123"
        resource = "strategy.xyz-789"
        error = AuthorizationError(
            message="Not authorized", user_id=user_id, resource=resource
        )

        assert error.user_id == user_id
        assert error.resource == resource
        self.reporter.info("Attributes accessible", context="Test")

    # ================================================================
    # Exception hierarchy tests
    # ================================================================

    def test_exception_hierarchy(self):
        """Test exception inheritance hierarchy."""
        self.reporter.info("Testing exception hierarchy", context="Test")

        # TokenExpiredError
        expired = TokenExpiredError("Expired")
        assert isinstance(expired, AuthenticationError)
        assert isinstance(expired, Exception)

        # TokenInvalidError
        invalid = TokenInvalidError("Invalid")
        assert isinstance(invalid, AuthenticationError)
        assert isinstance(invalid, Exception)

        # AuthorizationError (separate hierarchy)
        auth_error = AuthorizationError("Denied")
        assert not isinstance(auth_error, AuthenticationError)
        assert isinstance(auth_error, Exception)

        self.reporter.info("Exception hierarchy correct", context="Test")

    # ================================================================
    # Exception catching tests
    # ================================================================

    def test_catch_token_expired_as_authentication_error(self):
        """Test catching TokenExpiredError as AuthenticationError."""
        self.reporter.info("Testing catching TokenExpiredError as base", context="Test")

        try:
            raise TokenExpiredError("Token expired")
        except AuthenticationError as e:
            assert isinstance(e, TokenExpiredError)
            assert "expired" in str(e).lower()
            self.reporter.info("Caught as AuthenticationError", context="Test")

    def test_catch_token_invalid_as_authentication_error(self):
        """Test catching TokenInvalidError as AuthenticationError."""
        self.reporter.info("Testing catching TokenInvalidError as base", context="Test")

        try:
            raise TokenInvalidError("Invalid signature")
        except AuthenticationError as e:
            assert isinstance(e, TokenInvalidError)
            assert "signature" in str(e).lower()
            self.reporter.info("Caught as AuthenticationError", context="Test")

    def test_catch_all_authentication_errors(self):
        """Test catching all authentication errors with base class."""
        self.reporter.info("Testing catching all authentication errors", context="Test")

        errors = [
            AuthenticationError("Generic auth error"),
            TokenExpiredError("Expired"),
            TokenInvalidError("Invalid"),
        ]

        for error in errors:
            try:
                raise error
            except AuthenticationError as e:
                assert isinstance(e, AuthenticationError)
                self.reporter.info(f"Caught {type(e).__name__}", context="Test")

    # ================================================================
    # Various error scenarios tests
    # ================================================================

    def test_token_expired_various_messages(self):
        """Test TokenExpiredError with various messages."""
        self.reporter.info("Testing TokenExpiredError messages", context="Test")

        messages = [
            "JWT token has expired",
            "Token expired at 2025-01-01T00:00:00Z",
            "Expired token",
        ]

        for msg in messages:
            error = TokenExpiredError(msg)
            assert str(error) == msg
            self.reporter.info(f"Message: {msg}", context="Test")

    def test_token_invalid_various_reasons(self):
        """Test TokenInvalidError with various reasons."""
        self.reporter.info("Testing TokenInvalidError reasons", context="Test")

        reasons = [
            "Invalid signature",
            "Malformed token",
            "Token decode failed",
            "Missing required claims",
        ]

        for reason in reasons:
            error = TokenInvalidError(reason)
            assert str(error) == reason
            self.reporter.info(f"Reason: {reason}", context="Test")

    def test_authorization_error_various_scenarios(self):
        """Test AuthorizationError in various scenarios."""
        self.reporter.info("Testing AuthorizationError scenarios", context="Test")

        # User not allowed to access channel
        error1 = AuthorizationError(
            message="User not allowed to access private channel",
            user_id="user-123",
            resource="channel.private-vip",
        )
        assert "private channel" in str(error1)
        assert error1.user_id == "user-123"

        # Strategy access denied
        error2 = AuthorizationError(
            message="Strategy not owned by user",
            user_id="user-456",
            resource="strategy.abc-123",
        )
        assert "not owned" in str(error2)
        assert error2.resource == "strategy.abc-123"

        self.reporter.info("Various scenarios handled", context="Test")


if __name__ == "__main__":
    TestAuthenticationExceptions.run_as_main()

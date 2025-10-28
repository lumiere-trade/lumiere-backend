"""
Unit tests for AuthenticateWebSocketUseCase.

Tests WebSocket authentication and authorization.

Usage:
    python -m courier.tests.unit.application.use_cases.test_authenticate_websocket
    laborant courier --unit
"""

import time
from unittest.mock import Mock

from shared.tests import LaborantTest

from courier.application.use_cases.authenticate_websocket import (
    AuthenticateWebSocketUseCase,
)
from courier.domain.auth import TokenPayload
from courier.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
    TokenInvalidError,
)


class TestAuthenticateWebSocketUseCase(LaborantTest):
    """Unit tests for AuthenticateWebSocketUseCase."""

    component_name = "courier"
    test_category = "unit"

    # ================================================================
    # Unauthenticated access tests
    # ================================================================

    def test_execute_without_token_returns_none(self):
        """Test execute without token returns None."""
        self.reporter.info("Testing unauthenticated access", context="Test")

        mock_verifier = Mock()
        use_case = AuthenticateWebSocketUseCase(jwt_verifier=mock_verifier)

        result = use_case.execute(token=None, channel_name="global")

        assert result is None
        mock_verifier.verify_token.assert_not_called()
        self.reporter.info("Unauthenticated access allowed", context="Test")

    def test_execute_with_empty_token_returns_none(self):
        """Test execute with empty token returns None."""
        self.reporter.info("Testing empty token", context="Test")

        mock_verifier = Mock()
        use_case = AuthenticateWebSocketUseCase(jwt_verifier=mock_verifier)

        result = use_case.execute(token="", channel_name="global")

        assert result is None
        mock_verifier.verify_token.assert_not_called()
        self.reporter.info("Empty token treated as unauthenticated", context="Test")

    # ================================================================
    # Successful authentication tests
    # ================================================================

    def test_execute_with_valid_token_returns_payload(self):
        """Test execute with valid token returns TokenPayload."""
        self.reporter.info("Testing valid token authentication", context="Test")

        mock_verifier = Mock()
        current_time = int(time.time())
        mock_payload = TokenPayload(
            user_id="123",
            wallet_address="9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin",
            exp=current_time + 3600,
            iat=current_time,
        )
        mock_verifier.verify_token.return_value = mock_payload
        mock_verifier.verify_channel_access.return_value = True

        use_case = AuthenticateWebSocketUseCase(jwt_verifier=mock_verifier)

        result = use_case.execute(token="valid_token", channel_name="user.123")

        assert result == mock_payload
        assert result.user_id == "123"
        mock_verifier.verify_token.assert_called_once_with("valid_token")
        mock_verifier.verify_channel_access.assert_called_once_with("123", "user.123")
        self.reporter.info("Valid token authenticated successfully", context="Test")

    def test_execute_with_global_channel_access(self):
        """Test execute allows access to global channel."""
        self.reporter.info("Testing global channel access", context="Test")

        mock_verifier = Mock()
        current_time = int(time.time())
        mock_payload = TokenPayload(
            user_id="456",
            wallet_address="test",
            exp=current_time + 3600,
            iat=current_time,
        )
        mock_verifier.verify_token.return_value = mock_payload
        mock_verifier.verify_channel_access.return_value = True

        use_case = AuthenticateWebSocketUseCase(jwt_verifier=mock_verifier)

        result = use_case.execute(token="token", channel_name="global")

        assert result == mock_payload
        mock_verifier.verify_channel_access.assert_called_once_with("456", "global")
        self.reporter.info("Global channel access granted", context="Test")

    def test_execute_with_user_channel_access(self):
        """Test execute allows access to user's own channel."""
        self.reporter.info("Testing user channel access", context="Test")

        mock_verifier = Mock()
        current_time = int(time.time())
        mock_payload = TokenPayload(
            user_id="123",
            wallet_address="test",
            exp=current_time + 3600,
            iat=current_time,
        )
        mock_verifier.verify_token.return_value = mock_payload
        mock_verifier.verify_channel_access.return_value = True

        use_case = AuthenticateWebSocketUseCase(jwt_verifier=mock_verifier)

        result = use_case.execute(token="token", channel_name="user.123")

        assert result is not None
        self.reporter.info("User channel access granted", context="Test")

    def test_execute_with_strategy_channel_access(self):
        """Test execute allows access to strategy channel."""
        self.reporter.info("Testing strategy channel access", context="Test")

        mock_verifier = Mock()
        current_time = int(time.time())
        mock_payload = TokenPayload(
            user_id="789",
            wallet_address="test",
            exp=current_time + 3600,
            iat=current_time,
        )
        mock_verifier.verify_token.return_value = mock_payload
        mock_verifier.verify_channel_access.return_value = True

        use_case = AuthenticateWebSocketUseCase(jwt_verifier=mock_verifier)

        result = use_case.execute(token="token", channel_name="strategy.abc")

        assert result is not None
        self.reporter.info("Strategy channel access granted", context="Test")

    # ================================================================
    # Token validation error tests
    # ================================================================

    def test_execute_with_expired_token_raises_error(self):
        """Test execute with expired token raises TokenExpiredError."""
        self.reporter.info("Testing expired token", context="Test")

        mock_verifier = Mock()
        mock_verifier.verify_token.side_effect = ValueError("Token expired")

        use_case = AuthenticateWebSocketUseCase(jwt_verifier=mock_verifier)

        try:
            use_case.execute(token="expired_token", channel_name="global")
            assert False, "Should have raised TokenExpiredError"
        except TokenExpiredError as e:
            assert "expired" in str(e).lower()
            self.reporter.info("Expired token rejected", context="Test")

    def test_execute_with_invalid_token_raises_error(self):
        """Test execute with invalid token raises TokenInvalidError."""
        self.reporter.info("Testing invalid token", context="Test")

        mock_verifier = Mock()
        mock_verifier.verify_token.side_effect = ValueError("Invalid signature")

        use_case = AuthenticateWebSocketUseCase(jwt_verifier=mock_verifier)

        try:
            use_case.execute(token="invalid_token", channel_name="global")
            assert False, "Should have raised TokenInvalidError"
        except TokenInvalidError as e:
            assert "signature" in str(e).lower()
            self.reporter.info("Invalid token rejected", context="Test")

    def test_execute_with_malformed_token_raises_error(self):
        """Test execute with malformed token raises TokenInvalidError."""
        self.reporter.info("Testing malformed token", context="Test")

        mock_verifier = Mock()
        mock_verifier.verify_token.side_effect = ValueError("Malformed token")

        use_case = AuthenticateWebSocketUseCase(jwt_verifier=mock_verifier)

        try:
            use_case.execute(token="malformed", channel_name="global")
            assert False, "Should have raised TokenInvalidError"
        except TokenInvalidError:
            self.reporter.info("Malformed token rejected", context="Test")

    # ================================================================
    # Channel validation error tests
    # ================================================================

    def test_execute_with_invalid_channel_name_raises_error(self):
        """Test execute with invalid channel name raises AuthenticationError."""
        self.reporter.info("Testing invalid channel name", context="Test")

        mock_verifier = Mock()
        current_time = int(time.time())
        mock_payload = TokenPayload(
            user_id="123",
            wallet_address="test",
            exp=current_time + 3600,
            iat=current_time,
        )
        mock_verifier.verify_token.return_value = mock_payload

        use_case = AuthenticateWebSocketUseCase(jwt_verifier=mock_verifier)

        try:
            use_case.execute(token="token", channel_name="")
            assert False, "Should have raised AuthenticationError"
        except AuthenticationError as e:
            assert "invalid channel name" in str(e).lower()
            self.reporter.info("Invalid channel name rejected", context="Test")

    def test_execute_with_uppercase_channel_raises_error(self):
        """Test execute with uppercase channel name raises error."""
        self.reporter.info("Testing uppercase channel name", context="Test")

        mock_verifier = Mock()
        current_time = int(time.time())
        mock_payload = TokenPayload(
            user_id="123",
            wallet_address="test",
            exp=current_time + 3600,
            iat=current_time,
        )
        mock_verifier.verify_token.return_value = mock_payload

        use_case = AuthenticateWebSocketUseCase(jwt_verifier=mock_verifier)

        try:
            use_case.execute(token="token", channel_name="INVALID")
            assert False, "Should have raised AuthenticationError"
        except AuthenticationError:
            self.reporter.info("Uppercase channel rejected", context="Test")

    # ================================================================
    # Authorization error tests
    # ================================================================

    def test_execute_with_unauthorized_channel_raises_error(self):
        """Test execute without channel authorization raises AuthorizationError."""
        self.reporter.info("Testing unauthorized channel access", context="Test")

        mock_verifier = Mock()
        current_time = int(time.time())
        mock_payload = TokenPayload(
            user_id="123",
            wallet_address="test",
            exp=current_time + 3600,
            iat=current_time,
        )
        mock_verifier.verify_token.return_value = mock_payload
        mock_verifier.verify_channel_access.return_value = False

        use_case = AuthenticateWebSocketUseCase(jwt_verifier=mock_verifier)

        try:
            use_case.execute(token="token", channel_name="user.456")
            assert False, "Should have raised AuthorizationError"
        except AuthorizationError as e:
            assert "not authorized" in str(e).lower()
            assert e.user_id == "123"
            assert e.resource == "user.456"
            self.reporter.info("Unauthorized access blocked", context="Test")

    def test_execute_user_cannot_access_other_user_channel(self):
        """Test user cannot access another user's channel."""
        self.reporter.info("Testing cross-user channel access", context="Test")

        mock_verifier = Mock()
        current_time = int(time.time())
        mock_payload = TokenPayload(
            user_id="123",
            wallet_address="test",
            exp=current_time + 3600,
            iat=current_time,
        )
        mock_verifier.verify_token.return_value = mock_payload
        mock_verifier.verify_channel_access.return_value = False

        use_case = AuthenticateWebSocketUseCase(jwt_verifier=mock_verifier)

        try:
            use_case.execute(token="token", channel_name="user.999")
            assert False, "Should have raised AuthorizationError"
        except AuthorizationError:
            self.reporter.info("Cross-user access blocked", context="Test")

    # ================================================================
    # Edge cases
    # ================================================================

    def test_execute_verifier_called_with_correct_params(self):
        """Test JWT verifier called with correct parameters."""
        self.reporter.info("Testing verifier parameter passing", context="Test")

        mock_verifier = Mock()
        current_time = int(time.time())
        mock_payload = TokenPayload(
            user_id="abc",
            wallet_address="test",
            exp=current_time + 3600,
            iat=current_time,
        )
        mock_verifier.verify_token.return_value = mock_payload
        mock_verifier.verify_channel_access.return_value = True

        use_case = AuthenticateWebSocketUseCase(jwt_verifier=mock_verifier)

        use_case.execute(token="my_token", channel_name="strategy.xyz")

        mock_verifier.verify_token.assert_called_once_with("my_token")
        mock_verifier.verify_channel_access.assert_called_once_with(
            "abc", "strategy.xyz"
        )
        self.reporter.info("Verifier called with correct params", context="Test")

    def test_execute_with_ephemeral_channel(self):
        """Test execute allows access to ephemeral channels."""
        self.reporter.info("Testing ephemeral channel access", context="Test")

        mock_verifier = Mock()
        current_time = int(time.time())
        mock_payload = TokenPayload(
            user_id="123",
            wallet_address="test",
            exp=current_time + 3600,
            iat=current_time,
        )
        mock_verifier.verify_token.return_value = mock_payload
        mock_verifier.verify_channel_access.return_value = True

        use_case = AuthenticateWebSocketUseCase(jwt_verifier=mock_verifier)

        result = use_case.execute(token="token", channel_name="forge.job.xyz")

        assert result is not None
        self.reporter.info("Ephemeral channel access granted", context="Test")

    def test_execute_returns_correct_payload_structure(self):
        """Test execute returns payload with correct structure."""
        self.reporter.info("Testing payload structure", context="Test")

        mock_verifier = Mock()
        current_time = int(time.time())
        mock_payload = TokenPayload(
            user_id="test_user",
            wallet_address="test_wallet",
            exp=current_time + 3600,
            iat=current_time,
        )
        mock_verifier.verify_token.return_value = mock_payload
        mock_verifier.verify_channel_access.return_value = True

        use_case = AuthenticateWebSocketUseCase(jwt_verifier=mock_verifier)

        result = use_case.execute(token="token", channel_name="global")

        assert isinstance(result, TokenPayload)
        assert result.user_id == "test_user"
        assert result.wallet_address == "test_wallet"
        assert result.exp == current_time + 3600
        assert result.iat == current_time
        self.reporter.info("Payload structure correct", context="Test")


if __name__ == "__main__":
    TestAuthenticateWebSocketUseCase.run_as_main()

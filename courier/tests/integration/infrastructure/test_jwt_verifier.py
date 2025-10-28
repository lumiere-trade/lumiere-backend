"""
Integration tests for JWTVerifier.

Tests JWT token verification with real tokens.

Usage:
    python -m courier.tests.integration.infrastructure.test_jwt_verifier
    laborant courier --integration
"""

import time
from datetime import timedelta

import jwt
from shared.tests import LaborantTest

from courier.domain.auth import TokenPayload
from courier.infrastructure.auth.jwt_verifier import JWTVerifier


class TestJWTVerifier(LaborantTest):
    """Integration tests for JWTVerifier."""

    component_name = "courier"
    test_category = "integration"

    SECRET_KEY = "test-secret-key-for-integration-tests"
    ALGORITHM = "HS256"

    def _create_token(
        self, user_id: str, wallet_address: str, expires_delta: timedelta = None
    ) -> str:
        """Create a real JWT token for testing."""
        now = int(time.time())
        exp = now + int(expires_delta.total_seconds()) if expires_delta else now + 3600

        payload = {
            "user_id": user_id,
            "wallet_address": wallet_address,
            "exp": exp,
            "iat": now,
        }

        return jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)

    # ================================================================
    # Token verification tests
    # ================================================================

    def test_verify_valid_token(self):
        """Test verifying a valid JWT token."""
        self.reporter.info("Testing valid token verification", context="Test")

        verifier = JWTVerifier(secret=self.SECRET_KEY, algorithm=self.ALGORITHM)
        token = self._create_token(
            user_id="123",
            wallet_address="9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin",
            expires_delta=timedelta(hours=1),
        )

        payload = verifier.verify_token(token)

        assert isinstance(payload, TokenPayload)
        assert payload.user_id == "123"
        assert payload.wallet_address == "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"
        assert payload.exp > int(time.time())
        self.reporter.info("Valid token verified successfully", context="Test")

    def test_verify_expired_token(self):
        """Test verifying an expired JWT token."""
        self.reporter.info("Testing expired token verification", context="Test")

        verifier = JWTVerifier(secret=self.SECRET_KEY, algorithm=self.ALGORITHM)
        token = self._create_token(
            user_id="456",
            wallet_address="test_wallet",
            expires_delta=timedelta(seconds=-10),  # Expired 10 seconds ago
        )

        try:
            verifier.verify_token(token)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "expired" in str(e).lower()
            self.reporter.info("Expired token rejected", context="Test")

    def test_verify_invalid_signature(self):
        """Test verifying token with invalid signature."""
        self.reporter.info("Testing invalid signature verification", context="Test")

        verifier = JWTVerifier(secret=self.SECRET_KEY, algorithm=self.ALGORITHM)

        # Create token with different secret
        wrong_secret_token = jwt.encode(
            {
                "user_id": "789",
                "wallet_address": "test",
                "exp": int(time.time()) + 3600,
                "iat": int(time.time()),
            },
            "wrong-secret-key",
            algorithm=self.ALGORITHM,
        )

        try:
            verifier.verify_token(wrong_secret_token)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "invalid" in str(e).lower()
            self.reporter.info("Invalid signature rejected", context="Test")

    def test_verify_malformed_token(self):
        """Test verifying malformed JWT token."""
        self.reporter.info("Testing malformed token verification", context="Test")

        verifier = JWTVerifier(secret=self.SECRET_KEY, algorithm=self.ALGORITHM)

        try:
            verifier.verify_token("not.a.valid.jwt.token")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "invalid" in str(e).lower()
            self.reporter.info("Malformed token rejected", context="Test")

    def test_verify_token_with_missing_fields(self):
        """Test verifying token missing required fields."""
        self.reporter.info("Testing token with missing fields", context="Test")

        verifier = JWTVerifier(secret=self.SECRET_KEY, algorithm=self.ALGORITHM)

        # Create token without wallet_address
        incomplete_token = jwt.encode(
            {"user_id": "123", "exp": int(time.time()) + 3600, "iat": int(time.time())},
            self.SECRET_KEY,
            algorithm=self.ALGORITHM,
        )

        try:
            verifier.verify_token(incomplete_token)
            assert False, "Should have raised ValueError"
        except ValueError:
            self.reporter.info("Incomplete token rejected", context="Test")

    # ================================================================
    # Channel access authorization tests
    # ================================================================

    def test_verify_global_channel_access(self):
        """Test global channel access (always allowed)."""
        self.reporter.info("Testing global channel access", context="Test")

        verifier = JWTVerifier(secret=self.SECRET_KEY)

        assert verifier.verify_channel_access("any_user", "global") is True
        self.reporter.info("Global channel access granted", context="Test")

    def test_verify_user_channel_access_own(self):
        """Test user can access their own channel."""
        self.reporter.info("Testing user's own channel access", context="Test")

        verifier = JWTVerifier(secret=self.SECRET_KEY)

        assert verifier.verify_channel_access("123", "user.123") is True
        self.reporter.info("Own channel access granted", context="Test")

    def test_verify_user_channel_access_other(self):
        """Test user cannot access other user's channel."""
        self.reporter.info("Testing other user's channel access", context="Test")

        verifier = JWTVerifier(secret=self.SECRET_KEY)

        assert verifier.verify_channel_access("123", "user.456") is False
        self.reporter.info("Other user channel access denied", context="Test")

    def test_verify_strategy_channel_access(self):
        """Test strategy channel access (allowed for now)."""
        self.reporter.info("Testing strategy channel access", context="Test")

        verifier = JWTVerifier(secret=self.SECRET_KEY)

        assert verifier.verify_channel_access("123", "strategy.abc") is True
        self.reporter.info("Strategy channel access granted", context="Test")

    def test_verify_backtest_channel_access(self):
        """Test backtest channel access (ephemeral, allowed)."""
        self.reporter.info("Testing backtest channel access", context="Test")

        verifier = JWTVerifier(secret=self.SECRET_KEY)

        assert verifier.verify_channel_access("123", "backtest.xyz") is True
        self.reporter.info("Backtest channel access granted", context="Test")

    def test_verify_forge_job_channel_access(self):
        """Test forge.job channel access (ephemeral, allowed)."""
        self.reporter.info("Testing forge.job channel access", context="Test")

        verifier = JWTVerifier(secret=self.SECRET_KEY)

        assert verifier.verify_channel_access("123", "forge.job.xyz") is True
        self.reporter.info("Forge.job channel access granted", context="Test")

    def test_verify_public_channel_access(self):
        """Test public channel access (allowed)."""
        self.reporter.info("Testing public channel access", context="Test")

        verifier = JWTVerifier(secret=self.SECRET_KEY)

        public_channels = [
            "trade",
            "candles",
            "sys",
            "rsi",
            "extrema",
            "analysis",
            "subscription",
            "payment",
            "deposit",
        ]

        for channel in public_channels:
            assert verifier.verify_channel_access("any_user", channel) is True

        self.reporter.info("All public channels accessible", context="Test")

    def test_verify_unknown_channel_access_denied(self):
        """Test unknown channel access is denied by default."""
        self.reporter.info("Testing unknown channel access", context="Test")

        verifier = JWTVerifier(secret=self.SECRET_KEY)

        assert verifier.verify_channel_access("123", "unknown.channel") is False
        self.reporter.info("Unknown channel access denied", context="Test")

    # ================================================================
    # End-to-end integration tests
    # ================================================================

    def test_full_auth_flow_success(self):
        """Test complete authentication flow."""
        self.reporter.info("Testing full authentication flow", context="Test")

        verifier = JWTVerifier(secret=self.SECRET_KEY, algorithm=self.ALGORITHM)

        # Create token
        token = self._create_token(
            user_id="alice",
            wallet_address="alice_wallet",
            expires_delta=timedelta(hours=1),
        )

        # Verify token
        payload = verifier.verify_token(token)
        assert payload.user_id == "alice"

        # Check channel access
        assert verifier.verify_channel_access(payload.user_id, "user.alice") is True
        assert verifier.verify_channel_access(payload.user_id, "user.bob") is False
        assert verifier.verify_channel_access(payload.user_id, "global") is True

        self.reporter.info("Full authentication flow successful", context="Test")

    def test_full_auth_flow_expired_token(self):
        """Test authentication flow with expired token."""
        self.reporter.info("Testing auth flow with expired token", context="Test")

        verifier = JWTVerifier(secret=self.SECRET_KEY, algorithm=self.ALGORITHM)

        # Create expired token
        token = self._create_token(
            user_id="bob",
            wallet_address="bob_wallet",
            expires_delta=timedelta(seconds=-10),
        )

        # Attempt to verify should fail
        try:
            verifier.verify_token(token)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "expired" in str(e).lower()
            self.reporter.info("Expired token flow handled correctly", context="Test")


if __name__ == "__main__":
    TestJWTVerifier.run_as_main()

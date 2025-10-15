"""
Authentication domain exceptions.
"""

from pourtier.domain.exceptions.base import PourtierException


class AuthenticationError(PourtierException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code="AUTHENTICATION_ERROR")


class InvalidSignatureError(AuthenticationError):
    """Raised when wallet signature is invalid."""

    def __init__(self):
        super().__init__("Invalid wallet signature")


class ExpiredTokenError(AuthenticationError):
    """Raised when JWT token has expired."""

    def __init__(self):
        super().__init__("Authentication token has expired")


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is malformed or invalid."""

    def __init__(self):
        super().__init__("Invalid authentication token")

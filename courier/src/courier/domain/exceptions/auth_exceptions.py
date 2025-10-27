"""
Authentication and authorization exceptions.
"""


class AuthenticationError(Exception):
    """Base exception for authentication errors."""

    pass


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired."""

    pass


class TokenInvalidError(AuthenticationError):
    """Raised when JWT token is invalid."""

    pass


class AuthorizationError(Exception):
    """Raised when user is not authorized to access resource."""

    def __init__(self, message: str, user_id: str = None, resource: str = None):
        """
        Initialize AuthorizationError.

        Args:
            message: Error message
            user_id: Optional user ID
            resource: Optional resource name
        """
        super().__init__(message)
        self.user_id = user_id
        self.resource = resource

"""
Bridge-related exceptions.
"""

from typing import Optional


class BridgeException(Exception):
    """Base exception for bridge operations."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class BridgeConnectionException(BridgeException):
    """Bridge server connection failed."""
    pass


class BridgeTimeoutException(BridgeException):
    """Bridge operation timeout."""
    pass


class BridgeValidationException(BridgeException):
    """Bridge request validation failed."""
    pass

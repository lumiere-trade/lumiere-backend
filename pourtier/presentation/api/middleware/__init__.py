"""
API middleware for Pourtier.
"""

from pourtier.presentation.api.middleware.error_handler import (
    pourtier_exception_handler,
)

__all__ = ["pourtier_exception_handler"]

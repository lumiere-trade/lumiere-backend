"""
Base domain exceptions.
"""


class PourtierException(Exception):
    """Base exception for all Pourtier domain errors."""

    def __init__(self, message: str, code: str | None = None):
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(self.message)


class EntityNotFoundError(PourtierException):
    """Raised when entity is not found in repository."""

    def __init__(self, entity_type: str, entity_id: str):
        message = f"{entity_type} with ID {entity_id} not found"
        super().__init__(message, code="ENTITY_NOT_FOUND")


class DuplicateEntityError(PourtierException):
    """Raised when attempting to create duplicate entity."""

    def __init__(self, entity_type: str, identifier: str):
        message = f"{entity_type} with {identifier} already exists"
        super().__init__(message, code="DUPLICATE_ENTITY")


class ValidationError(PourtierException):
    """Raised when entity validation fails."""

    def __init__(self, field: str, reason: str):
        message = f"Validation failed for {field}: {reason}"
        super().__init__(message, code="VALIDATION_ERROR")

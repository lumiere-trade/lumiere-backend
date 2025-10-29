"""
Message validation use case.

Validates incoming WebSocket messages for:
- JSON structure
- Size limits
- Required fields
- Type validation
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ValidationResult:
    """Result of message validation."""

    valid: bool
    errors: List[str]
    message_type: Optional[str] = None
    size_bytes: int = 0


class ValidateMessageUseCase:
    """
    Use case for validating WebSocket messages.

    Validates message structure, size, and content.
    """

    def __init__(
        self,
        max_message_size: int = 1_048_576,  # 1MB default
        max_string_length: int = 10_000,
        max_array_size: int = 1000,
    ):
        """
        Initialize message validator.

        Args:
            max_message_size: Maximum message size in bytes
            max_string_length: Maximum string field length
            max_array_size: Maximum array field size
        """
        self.max_message_size = max_message_size
        self.max_string_length = max_string_length
        self.max_array_size = max_array_size

    def validate_message(self, raw_message: str) -> ValidationResult:
        """
        Validate incoming WebSocket message.

        Args:
            raw_message: Raw message string from WebSocket

        Returns:
            ValidationResult with validation status and errors
        """
        errors = []

        # Check message size
        size_bytes = len(raw_message.encode("utf-8"))
        if size_bytes > self.max_message_size:
            errors.append(
                f"Message too large: {size_bytes} bytes "
                f"(max: {self.max_message_size})"
            )
            return ValidationResult(
                valid=False, errors=errors, size_bytes=size_bytes
            )

        # Try to parse JSON
        try:
            message = json.loads(raw_message)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {str(e)}")
            return ValidationResult(
                valid=False, errors=errors, size_bytes=size_bytes
            )

        # Validate it's a dictionary
        if not isinstance(message, dict):
            errors.append("Message must be a JSON object")
            return ValidationResult(
                valid=False, errors=errors, size_bytes=size_bytes
            )

        # Extract message type (optional)
        message_type = message.get("type")

        # Validate message content
        content_errors = self._validate_content(message)
        errors.extend(content_errors)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            message_type=message_type,
            size_bytes=size_bytes,
        )

    def _validate_content(self, message: Dict[str, Any]) -> List[str]:
        """
        Validate message content recursively.

        Args:
            message: Parsed message dictionary

        Returns:
            List of validation errors
        """
        errors = []

        for key, value in message.items():
            # Validate key is string
            if not isinstance(key, str):
                errors.append(f"Key must be string, got {type(key).__name__}")
                continue

            # Validate string length
            if isinstance(value, str):
                if len(value) > self.max_string_length:
                    errors.append(
                        f"String field '{key}' too long: {len(value)} chars "
                        f"(max: {self.max_string_length})"
                    )

            # Validate array size
            elif isinstance(value, list):
                if len(value) > self.max_array_size:
                    errors.append(
                        f"Array field '{key}' too large: {len(value)} items "
                        f"(max: {self.max_array_size})"
                    )

                # Recursively validate array items
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        nested_errors = self._validate_content(item)
                        for err in nested_errors:
                            errors.append(f"{key}[{i}].{err}")

            # Recursively validate nested objects
            elif isinstance(value, dict):
                nested_errors = self._validate_content(value)
                for err in nested_errors:
                    errors.append(f"{key}.{err}")

        return errors

    def is_control_message(self, message_type: Optional[str]) -> bool:
        """
        Check if message is a control message (ping, pong, etc.).

        Args:
            message_type: Message type string

        Returns:
            True if control message, False otherwise
        """
        control_types = {"ping", "pong", "subscribe", "unsubscribe"}
        return message_type in control_types if message_type else False

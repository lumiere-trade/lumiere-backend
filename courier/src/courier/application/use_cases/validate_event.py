"""
Use case for validating events against schemas with size limits.

Enhanced with:
- Event payload size validation
- Metadata size validation
- Total event size validation
"""

import json
from typing import Any, Dict

from pydantic import ValidationError

from courier.domain.events import (
    BacktestCancelledEvent,
    BacktestCompletedEvent,
    BacktestFailedEvent,
    BacktestProgressEvent,
    BacktestStartedEvent,
    BaseEvent,
    ForgeJobCompletedEvent,
    ForgeJobFailedEvent,
    ForgeJobProgressEvent,
    ForgeJobStartedEvent,
    PositionClosedEvent,
    ProphetErrorEvent,
    ProphetMessageChunkEvent,
    ProphetTSDLReadyEvent,
    StrategyDeployedEvent,
    TradeOrderFilledEvent,
    TradeOrderPlacedEvent,
    TradeSignalGeneratedEvent,
)


class EventSizeExceededError(ValueError):
    """Raised when event size exceeds configured limits."""

    def __init__(self, size: int, max_size: int, component: str = "event"):
        self.size = size
        self.max_size = max_size
        self.component = component
        super().__init__(
            f"{component.capitalize()} size {size} bytes exceeds "
            f"maximum allowed {max_size} bytes"
        )


class ValidateEventUseCase:
    """
    Use case for validating events against Pydantic schemas with size limits.

    Maps event types to their corresponding Pydantic models and validates:
    - Event data structure and types
    - Business rules
    - Payload size limits
    - Metadata size limits
    - Total event size limits
    """

    # Event type to Pydantic model mapping
    EVENT_SCHEMAS = {
        # Prophet events
        "prophet.message_chunk": ProphetMessageChunkEvent,
        "prophet.tsdl_ready": ProphetTSDLReadyEvent,
        "prophet.error": ProphetErrorEvent,
        # Cartographe (Backtest) events
        "backtest.started": BacktestStartedEvent,
        "backtest.progress": BacktestProgressEvent,
        "backtest.completed": BacktestCompletedEvent,
        "backtest.failed": BacktestFailedEvent,
        "backtest.cancelled": BacktestCancelledEvent,
        # Chevalier (Trading) events
        "strategy.deployed": StrategyDeployedEvent,
        "trade.signal_generated": TradeSignalGeneratedEvent,
        "trade.order_placed": TradeOrderPlacedEvent,
        "trade.order_filled": TradeOrderFilledEvent,
        "position.closed": PositionClosedEvent,
        # Forge (Background jobs) events
        "forge.job.started": ForgeJobStartedEvent,
        "forge.job.progress": ForgeJobProgressEvent,
        "forge.job.completed": ForgeJobCompletedEvent,
        "forge.job.failed": ForgeJobFailedEvent,
    }

    def __init__(
        self,
        max_event_size: int = 1_048_576,  # 1MB default
        max_payload_size: int = 524_288,  # 512KB default
        max_metadata_size: int = 10_240,  # 10KB default
    ):
        """
        Initialize ValidateEventUseCase with size limits.

        Args:
            max_event_size: Maximum total event size in bytes (default: 1MB)
            max_payload_size: Maximum event.data size in bytes (default: 512KB)
            max_metadata_size: Maximum event.metadata size in bytes (default: 10KB)
        """
        self.max_event_size = max_event_size
        self.max_payload_size = max_payload_size
        self.max_metadata_size = max_metadata_size

    def _calculate_size(self, data: Any) -> int:
        """
        Calculate size of data in bytes.

        Args:
            data: Data to measure (dict, list, str, etc.)

        Returns:
            Size in bytes
        """
        try:
            json_str = json.dumps(data, ensure_ascii=False)
            return len(json_str.encode("utf-8"))
        except (TypeError, ValueError):
            # Fallback for non-JSON-serializable data
            return len(str(data).encode("utf-8"))

    def _validate_size(self, data: Any, max_size: int, component: str) -> None:
        """
        Validate that data size does not exceed limit.

        Args:
            data: Data to check
            max_size: Maximum allowed size in bytes
            component: Component name for error message

        Raises:
            EventSizeExceededError: If size exceeds limit
        """
        size = self._calculate_size(data)
        if size > max_size:
            raise EventSizeExceededError(size, max_size, component)

    def execute(
        self,
        event_type: str,
        event_data: Dict[str, Any],
    ) -> BaseEvent:
        """
        Validate event against its schema and size limits.

        Validation steps:
        1. Check if event type is known
        2. Validate total event size
        3. Validate metadata size (if present)
        4. Validate payload size (if present)
        5. Validate against Pydantic schema

        Args:
            event_type: Event type identifier (e.g., 'backtest.started')
            event_data: Full event payload including type, metadata, and data

        Returns:
            Validated BaseEvent instance

        Raises:
            ValueError: If event type is unknown
            EventSizeExceededError: If event exceeds size limits
            ValidationError: If event data doesn't match schema
        """
        # Check if event type is known
        schema_class = self.EVENT_SCHEMAS.get(event_type)

        if schema_class is None:
            raise ValueError(
                f"Unknown event type: {event_type}. "
                f"Supported types: {list(self.EVENT_SCHEMAS.keys())}"
            )

        # Validate total event size
        self._validate_size(event_data, self.max_event_size, "event")

        # Validate metadata size (if present)
        if "metadata" in event_data:
            self._validate_size(
                event_data["metadata"], self.max_metadata_size, "metadata"
            )

        # Validate payload size (if present)
        if "data" in event_data:
            self._validate_size(event_data["data"], self.max_payload_size, "payload")

        # Validate against schema
        try:
            validated_event = schema_class.model_validate(event_data)
            return validated_event
        except ValidationError as e:
            # Re-raise with more context
            raise ValidationError.from_exception_data(
                title=f"Event validation failed for type: {event_type}",
                line_errors=e.errors(),
            )

    def get_supported_event_types(self) -> list[str]:
        """
        Get list of all supported event types.

        Returns:
            List of event type strings
        """
        return list(self.EVENT_SCHEMAS.keys())

    def is_event_type_supported(self, event_type: str) -> bool:
        """
        Check if event type is supported.

        Args:
            event_type: Event type to check

        Returns:
            True if supported, False otherwise
        """
        return event_type in self.EVENT_SCHEMAS

    def get_size_limits(self) -> Dict[str, int]:
        """
        Get configured size limits.

        Returns:
            Dictionary with size limits in bytes
        """
        return {
            "max_event_size": self.max_event_size,
            "max_payload_size": self.max_payload_size,
            "max_metadata_size": self.max_metadata_size,
        }

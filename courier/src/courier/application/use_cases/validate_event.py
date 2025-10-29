"""
Use case for validating events against schemas.
"""

from typing import Any, Dict, Optional

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


class ValidateEventUseCase:
    """
    Use case for validating events against Pydantic schemas.

    Maps event types to their corresponding Pydantic models and validates
    event data structure, types, and business rules.
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

    def execute(
        self,
        event_type: str,
        event_data: Dict[str, Any],
    ) -> BaseEvent:
        """
        Validate event against its schema.

        Args:
            event_type: Event type identifier (e.g., 'backtest.started')
            event_data: Full event payload including type, metadata, and data

        Returns:
            Validated BaseEvent instance

        Raises:
            ValueError: If event type is unknown
            ValidationError: If event data doesn't match schema
        """
        # Check if event type is known
        schema_class = self.EVENT_SCHEMAS.get(event_type)

        if schema_class is None:
            raise ValueError(
                f"Unknown event type: {event_type}. "
                f"Supported types: {list(self.EVENT_SCHEMAS.keys())}"
            )

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

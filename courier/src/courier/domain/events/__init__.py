"""
Event schemas for Courier validation.

All events must inherit from BaseEvent and follow the schema structure.
"""

from typing import Union

from courier.domain.events.base import BaseEvent, EventMetadata
from courier.domain.events.cartographe import (
    BacktestCancelledEvent,
    BacktestCompletedEvent,
    BacktestFailedEvent,
    BacktestProgressEvent,
    BacktestStartedEvent,
    CartographeEvent,
)
from courier.domain.events.chevalier import (
    ChevalierEvent,
    PositionClosedEvent,
    StrategyDeployedEvent,
    TradeOrderFilledEvent,
    TradeOrderPlacedEvent,
    TradeSignalGeneratedEvent,
)
from courier.domain.events.forge import (
    ForgeEvent,
    ForgeJobCompletedEvent,
    ForgeJobFailedEvent,
    ForgeJobProgressEvent,
    ForgeJobStartedEvent,
)
from courier.domain.events.prophet import (
    ProphetErrorEvent,
    ProphetEvent,
    ProphetMessageChunkEvent,
    ProphetTSDLReadyEvent,
)

# Master union type for all Courier events
CourierEvent = Union[
    ProphetEvent,
    CartographeEvent,
    ChevalierEvent,
    ForgeEvent,
]

__all__ = [
    # Base
    "BaseEvent",
    "EventMetadata",
    "CourierEvent",
    # Prophet
    "ProphetEvent",
    "ProphetMessageChunkEvent",
    "ProphetTSDLReadyEvent",
    "ProphetErrorEvent",
    # Cartographe
    "CartographeEvent",
    "BacktestStartedEvent",
    "BacktestProgressEvent",
    "BacktestCompletedEvent",
    "BacktestFailedEvent",
    "BacktestCancelledEvent",
    # Chevalier
    "ChevalierEvent",
    "StrategyDeployedEvent",
    "TradeSignalGeneratedEvent",
    "TradeOrderPlacedEvent",
    "TradeOrderFilledEvent",
    "PositionClosedEvent",
    # Forge
    "ForgeEvent",
    "ForgeJobStartedEvent",
    "ForgeJobProgressEvent",
    "ForgeJobCompletedEvent",
    "ForgeJobFailedEvent",
]

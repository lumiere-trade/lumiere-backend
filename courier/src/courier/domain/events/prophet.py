"""
Prophet service event schemas.

Events published by Prophet AI during strategy generation.
"""

from typing import Any, Dict, Literal, Optional

from pydantic import Field

from courier.domain.events.base import BaseEvent


class ProphetMessageChunkEvent(BaseEvent):
    """
    Streamed message chunk from Prophet AI.
    
    Published during real-time strategy generation conversation.
    """

    type: Literal["prophet.message_chunk"] = "prophet.message_chunk"
    data: Dict[str, Any] = Field(
        ...,
        description="Chunk data",
        example={
            "conversation_id": "conv_abc123",
            "chunk": "Based on your requirements, I suggest...",
            "is_final": False,
        },
    )


class ProphetTSDLReadyEvent(BaseEvent):
    """
    TSDL strategy code ready event.
    
    Published when Prophet generates complete TSDL code.
    """

    type: Literal["prophet.tsdl_ready"] = "prophet.tsdl_ready"
    data: Dict[str, Any] = Field(
        ...,
        description="TSDL and metadata",
        example={
            "conversation_id": "conv_abc123",
            "strategy_id": "strat_xyz789",
            "tsdl": "strategy MyStrategy...",
            "metadata": {
                "name": "RSI Momentum",
                "description": "Trade based on RSI signals",
                "strategy_composition": {"base_strategies": ["indicator_based"]},
            },
        },
    )


class ProphetErrorEvent(BaseEvent):
    """
    Prophet error event.
    
    Published when strategy generation fails.
    """

    type: Literal["prophet.error"] = "prophet.error"
    data: Dict[str, Any] = Field(
        ...,
        description="Error details",
        example={
            "conversation_id": "conv_abc123",
            "error_code": "GENERATION_FAILED",
            "message": "Failed to generate valid TSDL",
            "details": "Invalid indicator configuration",
        },
    )


# Union type for type hints
ProphetEvent = (
    ProphetMessageChunkEvent | ProphetTSDLReadyEvent | ProphetErrorEvent
)

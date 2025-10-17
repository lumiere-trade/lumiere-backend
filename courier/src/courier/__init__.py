"""
Broker - Standalone WebSocket hub for real-time event broadcasting.

The Broker component decouples WebSocket communication from business logic.
It receives events via HTTP POST from multiple systems (Rebalancer, Forger)
and broadcasts them to connected UI clients via WebSocket channels.

Architecture:
    Systems → HTTP POST → Broker → WebSocket → UI Clients

Channels:
    - trade: Trading events (open, close)
    - candle: Candle updates (aggregated)
    - system: System logs and status
    - extrema: Extrema detection events (Forger)
    - analysis: Analysis results (Forger)

Usage:
    from broker import Broker, BrokerConfig

    config = BrokerConfig(host="0.0.0.0", port=8765)
    broker = Broker(config)
    broker.start()
"""

from courier.broker import Broker
from courier.config.settings import BrokerConfig, load_config

__version__ = "1.0.0"
__all__ = ["Broker", "BrokerConfig"]

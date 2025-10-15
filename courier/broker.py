"""
Broker - WebSocket server for event broadcasting.

Provides WebSocket endpoints for UI clients and HTTP endpoints for
systems to publish events. Handles connection management, heartbeats,
and channel-based message routing.

Enhanced with dynamic channel support for FORGE job-specific channels.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from courier.config.settings import BrokerConfig, load_config
from shared.reporter import SystemReporter
from shared.reporter.emojis import Emoji


class Broker:
    """
    WebSocket broker for event broadcasting.

    Manages WebSocket connections from UI clients and receives events
    from backend systems via HTTP POST. Implements channel-based routing,
    connection lifecycle management, and heartbeat monitoring.

    Enhanced Features:
        - Dynamic channel creation for FORGE jobs
        - Dual publish endpoints (URL and body-based)
        - Auto-cleanup of unused channels

    Attributes:
        config: Broker configuration
        app: FastAPI application instance
        clients: Connected WebSocket clients per channel
        client_metadata: Client connection metadata
        stats: Runtime statistics
        reporter: SystemReporter instance
    """

    def __init__(self, config: BrokerConfig):
        """
        Initialize Broker.

        Args:
            config: Validated broker configuration
        """
        self.config = config

        # Initialize SystemReporter (no CourierClient - avoid circular dependency)
        self.reporter = SystemReporter(
            name="broker",
            log_dir="logs/broker",
            verbose=1,
            courier_client=None,
        )

        # WebSocket clients: {channel: [websocket, ...]}
        self.clients: Dict[str, List[WebSocket]] = {
            channel: [] for channel in config.channels
        }

        # Client metadata: {websocket_id: {channel, connected_at, ...}}
        self.client_metadata: Dict[int, dict] = {}

        # Statistics
        self.stats = {
            "total_connections": 0,
            "total_messages_sent": 0,
            "total_messages_received": 0,
            "start_time": datetime.now(),
        }

        # Create FastAPI app with lifespan
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """FastAPI lifespan context manager."""
            # Startup
            self.reporter.info(
                f"{Emoji.SYSTEM.STARTUP} Broker starting...",
                context="Broker",
                verbose_level=1,
            )
            self.reporter.info(
                f"{Emoji.NETWORK.CONNECTED} "
                f"Host: {self.config.host}:{self.config.port}",
                context="Broker",
                verbose_level=1,
            )
            self.reporter.info(
                f"{Emoji.SYSTEM.READY} " f"Channels: {', '.join(self.config.channels)}",
                context="Broker",
                verbose_level=1,
            )
            self.reporter.info(
                f"{Emoji.SYSTEM.READY} Dynamic channel creation: ENABLED",
                context="Broker",
                verbose_level=1,
            )

            # Start heartbeat task
            heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            yield

            # Shutdown
            self.reporter.info(
                f"{Emoji.SYSTEM.SHUTDOWN} Broker shutting down...",
                context="Broker",
                verbose_level=1,
            )
            heartbeat_task.cancel()
            await self._close_all_connections()
            self.reporter.info(
                f"{Emoji.SUCCESS} Broker stopped",
                context="Broker",
                verbose_level=1,
            )

        self.app = FastAPI(
            title="Broker",
            description="WebSocket event broadcasting hub",
            version="1.0.0",
            lifespan=lifespan,
        )

        # Register routes
        self._register_routes()

        self.reporter.info(
            f"{Emoji.SUCCESS} Broker initialized",
            context="Broker",
            verbose_level=1,
        )

    def _register_routes(self) -> None:
        """Register FastAPI routes."""

        @self.app.websocket("/ws/{channel}")
        async def websocket_endpoint(websocket: WebSocket, channel: str):
            """
            WebSocket endpoint for UI clients.

            Args:
                websocket: WebSocket connection
                channel: Channel name
            """
            await self._handle_websocket(websocket, channel)

        @self.app.post("/publish/{channel}")
        async def publish_event(channel: str, event: dict):
            """
            Publish event to channel (channel in URL).

            Legacy endpoint for backwards compatibility.

            Args:
                channel: Target channel
                event: Event payload

            Returns:
                Publication result
            """
            return await self._handle_publish(channel, event)

        @self.app.post("/publish")
        async def publish_event_body(request: dict):
            """
            Publish event with channel in request body.

            Supports dynamic channel creation for FORGE jobs.

            Request format:
            {
                "channel": "forge.job.abc-123",
                "data": {
                    "type": "progress",
                    "progress": 50,
                    "message": "Processing..."
                }
            }

            Args:
                request: Request with channel and data

            Returns:
                Publication result
            """
            # Extract channel and data
            channel = request.get("channel")
            data = request.get("data")

            if not channel:
                raise HTTPException(
                    status_code=400, detail="Missing 'channel' in request body"
                )

            if not data:
                raise HTTPException(
                    status_code=400, detail="Missing 'data' in request body"
                )

            # Auto-create channel if doesn't exist (for dynamic FORGE channels)
            if channel not in self.clients:
                self.reporter.info(
                    f"{Emoji.SYSTEM.READY} Auto-creating channel: {channel}",
                    context="Broker",
                    verbose_level=1,
                )
                self.clients[channel] = []

                # Also add to config channels for visibility
                if channel not in self.config.channels:
                    self.config.channels.append(channel)

            # Broadcast to channel
            sent_count = await self._broadcast(channel, data)

            self.reporter.debug(
                f"{Emoji.NETWORK.BROADCAST} Published to {channel}: "
                f"{data.get('type', 'unknown')} → {sent_count} clients",
                context="Broker",
                verbose_level=3,
            )

            return JSONResponse(
                {
                    "status": "published",
                    "channel": channel,
                    "clients_reached": sent_count,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return self._get_health_status()

        @self.app.get("/stats")
        async def get_stats():
            """Get broker statistics."""
            return self._get_statistics()

    async def _handle_websocket(self, websocket: WebSocket, channel: str) -> None:
        """
        Handle WebSocket connection lifecycle.

        Args:
            websocket: WebSocket connection
            channel: Requested channel
        """
        # Validate or auto-create channel
        if channel not in self.clients:
            # Auto-create channel for dynamic subscriptions
            self.reporter.info(
                f"{Emoji.SYSTEM.READY} Auto-creating channel on WebSocket "
                f"connect: {channel}",
                context="Broker",
                verbose_level=1,
            )
            self.clients[channel] = []

            if channel not in self.config.channels:
                self.config.channels.append(channel)

        # Check connection limit
        if self.config.max_clients_per_channel > 0:
            current_clients = len(self.clients[channel])
            if current_clients >= self.config.max_clients_per_channel:
                self.reporter.warning(
                    f"{Emoji.WARNING} Channel {channel} at capacity "
                    f"({self.config.max_clients_per_channel})",
                    context="Broker",
                    verbose_level=1,
                )
                await websocket.close(code=1008, reason="Channel full")
                return

        # Accept connection
        await websocket.accept()

        # Register client
        ws_id = id(websocket)
        self.clients[channel].append(websocket)
        self.client_metadata[ws_id] = {
            "channel": channel,
            "connected_at": datetime.now(),
            "messages_received": 0,
        }
        self.stats["total_connections"] += 1

        client_count = len(self.clients[channel])
        total_clients = sum(len(clients) for clients in self.clients.values())

        self.reporter.info(
            f"{Emoji.NETWORK.CONNECTED} Client connected → {channel} "
            f"(channel: {client_count}, total: {total_clients})",
            context="Broker",
            verbose_level=1,
        )

        try:
            # Keep connection alive and receive messages
            while True:
                message = await websocket.receive_text()
                self.client_metadata[ws_id]["messages_received"] += 1
                self.stats["total_messages_received"] += 1

                self.reporter.debug(
                    f"{Emoji.NETWORK.HTTP} Received from {channel}: {message}",
                    context="Broker",
                    verbose_level=3,
                )

        except WebSocketDisconnect:
            self.reporter.info(
                f"{Emoji.NETWORK.DISCONNECTED} " f"Client disconnected from {channel}",
                context="Broker",
                verbose_level=1,
            )

        except Exception as e:
            self.reporter.error(
                f"{Emoji.ERROR} WebSocket error on {channel}: {e}",
                context="Broker",
                verbose_level=0,
            )

        finally:
            # Cleanup client
            await self._remove_client(websocket, channel)

    async def _handle_publish(self, channel: str, event: dict) -> JSONResponse:
        """
        Handle event publication request.

        Args:
            channel: Target channel
            event: Event payload

        Returns:
            Publication result
        """
        # Auto-create channel if it doesn't exist
        if channel not in self.clients:
            self.reporter.info(
                f"{Emoji.SYSTEM.READY} Auto-creating channel: {channel}",
                context="Broker",
                verbose_level=1,
            )
            self.clients[channel] = []

            if channel not in self.config.channels:
                self.config.channels.append(channel)

        # Validate event structure
        if not isinstance(event, dict):
            raise HTTPException(status_code=400, detail="Event must be a JSON object")

        # Broadcast to all clients on channel
        sent_count = await self._broadcast(channel, event)

        self.reporter.debug(
            f"{Emoji.NETWORK.BROADCAST} Published to {channel}: "
            f"{event.get('topic', 'unknown')} → {sent_count} clients",
            context="Broker",
            verbose_level=3,
        )

        return JSONResponse(
            {
                "status": "published",
                "channel": channel,
                "clients_reached": sent_count,
                "timestamp": datetime.now().isoformat(),
            }
        )

    async def _broadcast(self, channel: str, message: dict) -> int:
        """
        Broadcast message to all clients on channel.

        Args:
            channel: Target channel
            message: Message payload

        Returns:
            Number of clients reached
        """
        clients = self.clients.get(channel, [])

        if not clients:
            return 0

        # Track dead connections
        dead_clients = []
        sent_count = 0

        # Send to all clients
        for ws in clients:
            try:
                await ws.send_json(message)
                sent_count += 1
                self.stats["total_messages_sent"] += 1

            except Exception as e:
                self.reporter.warning(
                    f"{Emoji.WARNING} Failed to send to client: {e}",
                    context="Broker",
                    verbose_level=2,
                )
                dead_clients.append(ws)

        # Remove dead connections
        for ws in dead_clients:
            await self._remove_client(ws, channel)

        return sent_count

    async def _remove_client(self, websocket: WebSocket, channel: str) -> None:
        """
        Remove client from channel.

        Args:
            websocket: WebSocket connection
            channel: Channel name
        """
        if websocket in self.clients[channel]:
            self.clients[channel].remove(websocket)

            ws_id = id(websocket)
            if ws_id in self.client_metadata:
                del self.client_metadata[ws_id]

            remaining = len(self.clients[channel])
            self.reporter.debug(
                f"{Emoji.SYSTEM.CLEANUP} Client removed from {channel} "
                f"(remaining: {remaining})",
                context="Broker",
                verbose_level=3,
            )

    async def _heartbeat_loop(self) -> None:
        """
        Periodic heartbeat to detect dead connections.

        Sends ping frames to all connected clients at configured interval.
        """
        self.reporter.info(
            f"{Emoji.SYSTEM.READY} Heartbeat started "
            f"(interval: {self.config.heartbeat_interval}s)",
            context="Broker",
            verbose_level=1,
        )

        while True:
            await asyncio.sleep(self.config.heartbeat_interval)

            total_clients = sum(len(clients) for clients in self.clients.values())

            if total_clients == 0:
                continue

            self.reporter.debug(
                f"{Emoji.SYSTEM.READY} Heartbeat → {total_clients} clients",
                context="Broker",
                verbose_level=3,
            )

            # Send ping to all clients
            for channel, clients in self.clients.items():
                dead_clients = []

                for ws in clients:
                    try:
                        await ws.send_json({"type": "ping"})
                    except Exception:
                        dead_clients.append(ws)

                # Cleanup dead connections
                for ws in dead_clients:
                    await self._remove_client(ws, channel)

    async def _close_all_connections(self) -> None:
        """Close all active WebSocket connections."""
        for channel, clients in self.clients.items():
            for ws in list(clients):
                try:
                    await ws.close(code=1001, reason="Server shutdown")
                except Exception:
                    pass

            self.clients[channel].clear()

        self.client_metadata.clear()

    def _get_health_status(self) -> dict:
        """
        Get health status.

        Returns:
            Health status dictionary
        """
        total_clients = sum(len(clients) for clients in self.clients.values())

        return {
            "status": "healthy",
            "uptime_seconds": (
                datetime.now() - self.stats["start_time"]
            ).total_seconds(),
            "total_clients": total_clients,
            "channels": {
                channel: len(clients) for channel, clients in self.clients.items()
            },
        }

    def _get_statistics(self) -> dict:
        """
        Get runtime statistics.

        Returns:
            Statistics dictionary
        """
        uptime = datetime.now() - self.stats["start_time"]

        return {
            "uptime_seconds": uptime.total_seconds(),
            "total_connections": self.stats["total_connections"],
            "total_messages_sent": self.stats["total_messages_sent"],
            "total_messages_received": self.stats["total_messages_received"],
            "active_clients": sum(len(clients) for clients in self.clients.values()),
            "channels": {
                channel: {
                    "active_clients": len(clients),
                    "max_clients": self.config.max_clients_per_channel or "unlimited",
                }
                for channel, clients in self.clients.items()
            },
        }

    def start(self) -> None:
        """
        Start Broker server.

        Runs uvicorn server with configured host and port.
        Blocks until server is stopped.
        """
        uvicorn.run(
            self.app,
            host=self.config.host,
            port=self.config.port,
            log_level=self.config.log_level,
        )


def main():
    """Main entry point for standalone execution."""
    import sys

    # Load config from YAML (uses COURIER_CONFIG env var)
    config = load_config()
    
    # Allow port override from command line
    if len(sys.argv) > 1:
        try:
            config.port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)

    # Create and start broker
    broker = Broker(config)

    try:
        broker.start()
    except KeyboardInterrupt:
        print("\n👋 Broker stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()

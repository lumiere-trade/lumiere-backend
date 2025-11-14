"""
Courier HTTP client for event publishing.

Provides async and sync interfaces for publishing events to Courier (Broker).
Used by backend systems (Chevalier, Rebalancer, Forger) to send events for
WebSocket broadcasting to UI clients.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class CourierClient:
    """
    HTTP client for publishing events to Courier.

    Provides both async and synchronous methods for publishing events
    to Courier channels. Handles connection pooling, retries, and error
    handling automatically.

    Attributes:
        courier_url: Base URL of Courier service
        timeout: HTTP request timeout in seconds
        max_retries: Maximum retry attempts for failed requests
        client: Async HTTP client instance

    Examples:
        # Async usage
        async with CourierClient("http://localhost:8765") as client:
            await client.publish("trade", {
                "topic": "trade.open",
                "data": {"price": 100}
            })

        # Sync usage
        client = CourierClient("http://localhost:8765")
        client.publish_sync("sys", {
            "type": "system_log",
            "level": "info",
            "message": "System started"
        })
        client.close_sync()
    """

    def __init__(self, courier_url: str, timeout: float = 5.0, max_retries: int = 3):
        """
        Initialize Courier client.

        Args:
            courier_url: Base URL of Courier (e.g., "http://localhost:8765")
            timeout: HTTP request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        self.courier_url = courier_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # Async HTTP client (lazy initialization)
        self._client: Optional[httpx.AsyncClient] = None

        # Sync HTTP client (lazy initialization)
        self._sync_client: Optional[httpx.Client] = None

        logger.debug(f"CourierClient initialized: {self.courier_url}")

    @property
    def client(self) -> httpx.AsyncClient:
        """
        Get or create async HTTP client.

        Returns:
            Async HTTP client instance
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )

        return self._client

    @property
    def sync_client(self) -> httpx.Client:
        """
        Get or create sync HTTP client.

        Returns:
            Sync HTTP client instance
        """
        if self._sync_client is None or self._sync_client.is_closed:
            self._sync_client = httpx.Client(
                timeout=self.timeout,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )

        return self._sync_client

    async def publish(self, channel: str, event: Dict[str, Any]) -> bool:
        """
        Publish event to Courier channel (async).

        Args:
            channel: Target channel (trade, sys, candle, etc.)
            event: Event payload with topic, data, timestamp

        Returns:
            True if published successfully, False otherwise

        Example:
            success = await client.publish("sys", {
                "type": "system_log",
                "level": "info",
                "message": "Order placed",
                "context": "OrderManager"
            })
        """
        url = f"{self.courier_url}/publish/{channel}"

        # Validate event structure
        if not self._validate_event(event):
            logger.error(f"Invalid event structure: {event}")
            return False

        # DETAILED LOGGING: Log request details
        logger.info(f"Publishing to URL: {url}")
        logger.info(f"Event payload: {json.dumps(event, indent=2)}")

        # Retry logic
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(url, json=event)

                # DETAILED LOGGING: Log response details
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response headers: {dict(response.headers)}")
                
                # Always log response body for debugging
                try:
                    response_body = response.text
                    logger.info(f"Response body: {response_body[:500]}")
                except Exception:
                    logger.warning("Could not read response body")

                if response.status_code == 200:
                    logger.debug(
                        f"Published to {channel}: "
                        f"{event.get('topic', event.get('type', 'unknown'))}"
                    )
                    return True

                elif response.status_code == 404:
                    logger.error(f"Channel '{channel}' not found on Courier")
                    return False

                else:
                    logger.warning(
                        f"Publish failed "
                        f"(attempt {attempt + 1}/{self.max_retries}): "
                        f"HTTP {response.status_code}, body: {response.text[:200]}"
                    )

            except httpx.TimeoutException:
                logger.warning(
                    f"Publish timeout " f"(attempt {attempt + 1}/{self.max_retries})"
                )

            except httpx.ConnectError:
                logger.error(
                    f"Failed to connect to Courier at {self.courier_url} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )

            except Exception as e:
                logger.error(
                    f"Publish error "
                    f"(attempt {attempt + 1}/{self.max_retries}): {e}",
                    exc_info=True
                )

            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = 0.1 * (2**attempt)
                await asyncio.sleep(wait_time)

        logger.error(
            f"Failed to publish to {channel} " f"after {self.max_retries} attempts"
        )
        return False

    def publish_sync(self, channel: str, event: Dict[str, Any]) -> bool:
        """
        Publish event to Courier channel (sync).

        Synchronous version for use in non-async contexts (e.g., SystemReporter).
        Uses sync HTTP client internally.

        Args:
            channel: Target channel
            event: Event payload

        Returns:
            True if published successfully, False otherwise

        Example:
            success = client.publish_sync("sys", {
                "type": "system_log",
                "level": "error",
                "message": "Database connection failed"
            })
        """
        url = f"{self.courier_url}/publish/{channel}"

        # Validate event structure
        if not self._validate_event(event):
            logger.error(f"Invalid event structure: {event}")
            return False

        # DETAILED LOGGING: Log request details
        logger.info(f"Publishing to URL: {url}")
        logger.info(f"Event payload: {json.dumps(event, indent=2)}")

        # Retry logic
        for attempt in range(self.max_retries):
            try:
                response = self.sync_client.post(url, json=event)

                # DETAILED LOGGING: Log response details
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response headers: {dict(response.headers)}")
                
                # Always log response body for debugging
                try:
                    response_body = response.text
                    logger.info(f"Response body: {response_body[:500]}")
                except Exception:
                    logger.warning("Could not read response body")

                if response.status_code == 200:
                    logger.debug(
                        f"Published to {channel}: "
                        f"{event.get('topic', event.get('type', 'unknown'))}"
                    )
                    return True

                elif response.status_code == 404:
                    logger.error(f"Channel '{channel}' not found on Courier")
                    return False

                else:
                    logger.warning(
                        f"Publish failed "
                        f"(attempt {attempt + 1}/{self.max_retries}): "
                        f"HTTP {response.status_code}, body: {response.text[:200]}"
                    )

            except httpx.TimeoutException:
                logger.warning(
                    f"Publish timeout " f"(attempt {attempt + 1}/{self.max_retries})"
                )

            except httpx.ConnectError:
                logger.error(
                    f"Failed to connect to Courier at {self.courier_url} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )

            except Exception as e:
                logger.error(
                    f"Publish error "
                    f"(attempt {attempt + 1}/{self.max_retries}): {e}",
                    exc_info=True
                )

            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = 0.1 * (2**attempt)
                time.sleep(wait_time)

        logger.error(
            f"Failed to publish to {channel} " f"after {self.max_retries} attempts"
        )
        return False

    async def health_check(self) -> bool:
        """
        Check if Courier is healthy (async).

        Returns:
            True if Courier is reachable and healthy

        Example:
            if await client.health_check():
                print("Courier is healthy")
        """
        url = f"{self.courier_url}/health"

        try:
            response = await self.client.get(url)

            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "healthy"

            return False

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def health_check_sync(self) -> bool:
        """
        Check if Courier is healthy (sync).

        Returns:
            True if Courier is reachable and healthy
        """
        url = f"{self.courier_url}/health"

        try:
            response = self.sync_client.get(url)

            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "healthy"

            return False

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def get_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get Courier statistics (async).

        Returns:
            Statistics dictionary or None if failed

        Example:
            stats = await client.get_stats()
            print(f"Active clients: {stats['active_clients']}")
        """
        url = f"{self.courier_url}/stats"

        try:
            response = await self.client.get(url)

            if response.status_code == 200:
                return response.json()

            return None

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return None

    def get_stats_sync(self) -> Optional[Dict[str, Any]]:
        """
        Get Courier statistics (sync).

        Returns:
            Statistics dictionary or None if failed
        """
        url = f"{self.courier_url}/stats"

        try:
            response = self.sync_client.get(url)

            if response.status_code == 200:
                return response.json()

            return None

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return None

    def _validate_event(self, event: Dict[str, Any]) -> bool:
        """
        Validate event structure.

        Args:
            event: Event to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(event, dict):
            logger.error("Event must be a dictionary")
            return False

        # Event structure is flexible - Courier accepts any dict
        return True

    async def close(self) -> None:
        """Close async HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            logger.debug("Async HTTP client closed")

    def close_sync(self) -> None:
        """Close sync HTTP client."""
        if self._sync_client is not None and not self._sync_client.is_closed:
            self._sync_client.close()
            logger.debug("Sync HTTP client closed")

    # Context manager support (async)
    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    # Context manager support (sync)
    def __enter__(self):
        """Sync context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit."""
        self.close_sync()

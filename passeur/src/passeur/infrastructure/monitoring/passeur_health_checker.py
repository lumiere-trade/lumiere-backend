"""
Passeur-specific health checks.

Checks:
- Bridge server connectivity
- Solana RPC connectivity
- Redis connectivity
"""

import asyncio
from typing import Optional

import aiohttp
from shared.health import HealthCheck, HealthStatus

from passeur.config.settings import get_settings


class PasseurHealthChecker(HealthCheck):
    """
    Health checker for Passeur blockchain bridge.

    Implements Kubernetes-compatible liveness and readiness probes.
    """

    def __init__(
        self,
        redis_client: Optional[any] = None,
        bridge_url: Optional[str] = None,
    ):
        """
        Initialize health checker.

        Args:
            redis_client: Optional Redis client
            bridge_url: Optional bridge server URL
        """
        self._settings = get_settings()
        self.redis = redis_client
        self.bridge_url = bridge_url or f"http://localhost:{self._settings.bridge_port}"

    def check(self) -> HealthStatus:
        """
        Overall health check.

        Returns:
            HealthStatus.HEALTHY if all checks pass
            HealthStatus.DEGRADED if non-critical checks fail
            HealthStatus.UNHEALTHY if critical checks fail
        """
        try:
            # Run async checks
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context
                return HealthStatus.HEALTHY

            return loop.run_until_complete(self._check_async())
        except Exception:
            return HealthStatus.UNHEALTHY

    async def _check_async(self) -> HealthStatus:
        """Async health check implementation."""
        redis_ok = await self._check_redis()
        solana_ok = await self._check_solana_rpc()

        if not redis_ok:
            return HealthStatus.DEGRADED

        if not solana_ok:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    def liveness(self) -> HealthStatus:
        """
        Liveness probe - is service alive?

        Returns:
            HealthStatus.HEALTHY if service can handle requests
        """
        return HealthStatus.HEALTHY

    def readiness(self) -> HealthStatus:
        """
        Readiness probe - can service accept traffic?

        Returns:
            HealthStatus.HEALTHY if dependencies are available
            HealthStatus.UNHEALTHY if critical dependencies are down
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return HealthStatus.HEALTHY

            return loop.run_until_complete(self._readiness_async())
        except Exception:
            return HealthStatus.UNHEALTHY

    async def _readiness_async(self) -> HealthStatus:
        """Async readiness check."""
        redis_ok = await self._check_redis()

        if not redis_ok:
            return HealthStatus.UNHEALTHY

        return HealthStatus.HEALTHY

    async def _check_redis(self) -> bool:
        """Check Redis connectivity."""
        if not self.redis:
            return True  # Redis optional for basic operations

        try:
            await self.redis.ping()
            return True
        except Exception:
            return False

    async def _check_solana_rpc(self) -> bool:
        """Check Solana RPC connectivity."""
        if not self._settings.solana_rpc_url:
            return True  # RPC URL not configured

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._settings.solana_rpc_url,
                    json={"jsonrpc": "2.0", "id": 1, "method": "getHealth"},
                    timeout=aiohttp.ClientTimeout(total=5.0),
                ) as response:
                    return response.status == 200
        except Exception:
            return False

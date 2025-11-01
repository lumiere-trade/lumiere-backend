"""
Passeur Query Service implementation.

Queries escrow account state via Passeur Bridge with proper lifecycle management.
"""

import asyncio
from decimal import Decimal
from typing import Optional

import httpx

from pourtier.domain.exceptions import BlockchainError, EscrowNotFoundError
from pourtier.domain.services.i_escrow_query_service import (
    IEscrowQueryService,
)


class PasseurQueryService(IEscrowQueryService):
    """
    Query escrow account state via Passeur Bridge.

    Implements proper lifecycle management with lazy client initialization.
    Thread-safe and multiprocessing-safe through lazy instantiation.

    Design:
    - Client is lazily initialized on first use
    - Each process gets its own client instance
    - Proper cleanup via close() method
    - Lock ensures single client per instance
    """

    def __init__(self, bridge_url: str, timeout: int = 30):
        """
        Initialize Passeur query service.

        Args:
            bridge_url: Passeur Bridge base URL
            timeout: Request timeout in seconds
        """
        self.bridge_url = bridge_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()

    async def _ensure_client(self) -> httpx.AsyncClient:
        """
        Ensure HTTP client is initialized (lazy, process-safe).

        Returns:
            Initialized AsyncClient instance

        Design:
        - Lazy initialization (client created on first use)
        - Lock prevents race conditions
        - Each process gets its own client (multiprocessing-safe)
        """
        if self._client is None:
            async with self._lock:
                # Double-check pattern (thread-safe)
                if self._client is None:
                    self._client = httpx.AsyncClient(
                        timeout=self.timeout,
                        limits=httpx.Limits(
                            max_connections=10,
                            max_keepalive_connections=5,
                        ),
                    )
        return self._client

    async def get_escrow_balance(self, escrow_account: str) -> Decimal:
        """
        Get current escrow account balance.

        Args:
            escrow_account: Escrow PDA address

        Returns:
            Current balance as Decimal

        Raises:
            EscrowNotFoundError: If escrow account doesn't exist
            BlockchainError: If query fails
        """
        try:
            client = await self._ensure_client()
            response = await client.get(
                f"{self.bridge_url}/escrow/balance/{escrow_account}"
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                raise EscrowNotFoundError(escrow_account)

            # Balance is in human-readable format (e.g., 10.5 USDC)
            balance = Decimal(str(data.get("balance", "0")))
            return balance

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise EscrowNotFoundError(escrow_account)
            raise BlockchainError(f"Failed to query escrow balance: {e.response.text}")
        except httpx.RequestError as e:
            raise BlockchainError(f"Network error querying escrow: {e}")
        except (ValueError, KeyError) as e:
            raise BlockchainError(f"Invalid response format: {e}")

    async def check_escrow_exists(self, escrow_account: str) -> bool:
        """
        Check if escrow account exists on blockchain.

        Args:
            escrow_account: Escrow PDA address

        Returns:
            True if account exists, False otherwise

        Raises:
            BlockchainError: If query fails
        """
        try:
            client = await self._ensure_client()
            response = await client.get(
                f"{self.bridge_url}/escrow/{escrow_account}"
            )

            # 404 = account doesn't exist (normal case)
            if response.status_code == 404:
                return False

            # 200 = account exists
            if response.status_code == 200:
                data = response.json()
                return data.get("success", False)

            # Other status codes = error
            response.raise_for_status()
            return False

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise BlockchainError(f"Failed to check escrow existence: {e.response.text}")
        except httpx.RequestError as e:
            raise BlockchainError(f"Network error checking escrow: {e}")

    async def close(self) -> None:
        """
        Close HTTP client and cleanup resources.

        This should be called when service is no longer needed.
        Safe to call multiple times.
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None

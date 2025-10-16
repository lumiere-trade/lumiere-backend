"""
Solana transaction verifier implementation.

RPC client for verifying transactions on Solana blockchain.
"""

import asyncio
from decimal import Decimal
from typing import Optional

import aiohttp
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pourtier.domain.exceptions.blockchain import (
    InvalidTransactionError,
    TransactionNotConfirmedError,
    TransactionNotFoundError,
)
from pourtier.domain.services.i_blockchain_verifier import (
    IBlockchainVerifier,
    VerifiedTransaction,
)


class SolanaTransactionVerifier(IBlockchainVerifier):
    """
    Solana RPC client for transaction verification.

    Queries Solana blockchain to verify user-signed transactions
    without requiring signing capabilities.
    Includes retries and optimized timeouts for production reliability.
    """

    def __init__(
        self,
        rpc_url: str,
        total_timeout: int = 10,
        connect_timeout: int = 3,
        max_retries: int = 3,
    ):
        """
        Initialize Solana transaction verifier.

        Args:
            rpc_url: Solana RPC endpoint URL
            total_timeout: Total request timeout in seconds (default: 10s)
            connect_timeout: Connection timeout in seconds (default: 3s)
            max_retries: Max retry attempts for transient failures (default: 3)
        """
        self.rpc_url = rpc_url
        self.timeout = aiohttp.ClientTimeout(
            total=total_timeout,
            connect=connect_timeout,
        )
        self.max_retries = max_retries
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with optimized settings."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self.timeout,
                connector=aiohttp.TCPConnector(
                    limit=100,  # Connection pool size
                    limit_per_host=30,  # Per-host limit
                    ttl_dns_cache=300,  # DNS cache TTL
                ),
            )
        return self._session

    async def verify_transaction(
        self,
        tx_signature: str,
    ) -> VerifiedTransaction:
        """
        Verify transaction on blockchain and parse data.

        Includes automatic retries for transient network errors.

        Args:
            tx_signature: Transaction signature to verify

        Returns:
            VerifiedTransaction with parsed transaction details

        Raises:
            TransactionNotFoundError: If transaction not found
            TransactionNotConfirmedError: If transaction not confirmed
            InvalidTransactionError: If transaction data malformed
        """
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential(multiplier=1, min=1, max=4),
                retry=retry_if_exception_type(
                    (aiohttp.ClientError, asyncio.TimeoutError)
                ),
                reraise=True,
            ):
                with attempt:
                    return await self._verify_transaction_once(tx_signature)
        except RetryError:
            raise InvalidTransactionError(
                f"RPC verification failed after {self.max_retries} retries",
                tx_signature=tx_signature,
            )

    async def _verify_transaction_once(
        self,
        tx_signature: str,
    ) -> VerifiedTransaction:
        """
        Single attempt to verify transaction (called by retry logic).

        Args:
            tx_signature: Transaction signature to verify

        Returns:
            VerifiedTransaction with parsed transaction details

        Raises:
            TransactionNotFoundError: If transaction not found
            TransactionNotConfirmedError: If transaction not confirmed
            InvalidTransactionError: If transaction data malformed
        """
        session = await self._get_session()

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [
                tx_signature,
                {
                    "encoding": "jsonParsed",
                    "maxSupportedTransactionVersion": 0,
                },
            ],
        }

        try:
            async with session.post(self.rpc_url, json=payload) as response:
                data = await response.json()

                if "error" in data:
                    raise TransactionNotFoundError(tx_signature)

                result = data.get("result")
                if not result:
                    raise TransactionNotFoundError(tx_signature)

                # Check confirmation
                if not result.get("meta"):
                    raise TransactionNotConfirmedError(tx_signature)

                # Parse transaction
                return self._parse_transaction(tx_signature, result)

        except (aiohttp.ClientError, asyncio.TimeoutError):
            # Let retry logic handle these
            raise

    def _parse_transaction(
        self, tx_signature: str, tx_data: dict
    ) -> VerifiedTransaction:
        """
        Parse RPC response into VerifiedTransaction.

        Args:
            tx_signature: Transaction signature
            tx_data: Raw transaction data from RPC

        Returns:
            VerifiedTransaction entity

        Raises:
            InvalidTransactionError: If parsing fails
        """
        try:
            tx_data.get("meta", {})
            transaction = tx_data.get("transaction", {})
            message = transaction.get("message", {})

            # Get account keys
            account_keys = message.get("accountKeys", [])
            if not account_keys:
                raise InvalidTransactionError(
                    "Missing account keys",
                    tx_signature=tx_signature,
                )

            # Extract sender (fee payer)
            sender = account_keys[0].get("pubkey", "")

            # Try to extract transfer info from instructions
            amount = None
            recipient = None
            token_mint = None

            instructions = message.get("instructions", [])
            for instruction in instructions:
                parsed = instruction.get("parsed")
                if parsed and parsed.get("type") == "transfer":
                    info = parsed.get("info", {})
                    amount_raw = info.get("amount") or info.get("tokenAmount", {}).get(
                        "amount"
                    )
                    if amount_raw:
                        # Convert lamports/token amount to Decimal
                        amount = Decimal(amount_raw) / Decimal("1000000")
                    recipient = info.get("destination")
                    token_mint = info.get("mint")

            return VerifiedTransaction(
                signature=tx_signature,
                is_confirmed=True,
                sender=sender,
                recipient=recipient,
                amount=amount,
                token_mint=token_mint,
                block_time=tx_data.get("blockTime"),
                slot=tx_data.get("slot"),
            )

        except Exception as e:
            raise InvalidTransactionError(
                f"Failed to parse transaction: {str(e)}",
                tx_signature=tx_signature,
            )

    async def wait_for_confirmation(
        self,
        tx_signature: str,
        max_retries: int = 30,
    ) -> bool:
        """
        Wait for transaction confirmation on blockchain.

        Args:
            tx_signature: Transaction signature to monitor
            max_retries: Maximum confirmation attempts

        Returns:
            True if confirmed, False if timeout
        """
        session = await self._get_session()

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignatureStatuses",
            "params": [[tx_signature], {"searchTransactionHistory": True}],
        }

        for _ in range(max_retries):
            try:
                async with session.post(self.rpc_url, json=payload) as response:
                    data = await response.json()

                    result = data.get("result", {})
                    value = result.get("value", [])

                    if value and value[0]:
                        status = value[0]
                        # Check if confirmed
                        if status.get("confirmationStatus") in [
                            "confirmed",
                            "finalized",
                        ]:
                            return True

                # Wait before retry
                await asyncio.sleep(2)

            except Exception:
                await asyncio.sleep(2)
                continue

        return False

    async def close(self) -> None:
        """Close HTTP session and cleanup resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

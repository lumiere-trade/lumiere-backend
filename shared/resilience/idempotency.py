"""
Idempotency pattern for exactly-once execution.

Ensures operations execute exactly once, even with retries or duplicate requests.
Critical for:
- User-initiated operations (deposits, withdrawals, strategy creation)
- Autonomous trade execution (Chevalier)
- Cross-chain operations (Passeur)
- Event processing (Courier)

Example:
    # User-initiated operation
    @idempotent(key_param="idempotency_key", store=redis_store)
    async def create_strategy(user_id: str, prompt: str, idempotency_key: str):
        strategy = await generate_strategy(user_id, prompt)
        return strategy
    
    # Autonomous operation
    trade_id = IdempotencyKey.from_trade(
        strategy_id="strat_123",
        signal_hash="abc456",
        timestamp=1730500000
    )
    
    if not await store.exists(trade_id):
        result = await execute_trade(signal)
        await store.set(trade_id, result)
"""

import hashlib
import json
import time
import logging
from typing import Optional, Callable, Any, Protocol
from functools import wraps
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class IdempotencyStore(Protocol):
    """
    Protocol for idempotency key storage.
    
    Implementations can use Redis, PostgreSQL, or any persistent store.
    """

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached result for idempotency key.
        
        Args:
            key: Idempotency key
            
        Returns:
            Cached result or None if not found
        """
        ...

    def set(self, key: str, value: Any, ttl: int = 86400) -> None:
        """
        Store result for idempotency key.
        
        Args:
            key: Idempotency key
            value: Result to cache
            ttl: Time to live in seconds (default: 24 hours)
        """
        ...

    def exists(self, key: str) -> bool:
        """
        Check if idempotency key exists.
        
        Args:
            key: Idempotency key
            
        Returns:
            True if key exists, False otherwise
        """
        ...

    async def get_async(self, key: str) -> Optional[Any]:
        """Async version of get()."""
        ...

    async def set_async(self, key: str, value: Any, ttl: int = 86400) -> None:
        """Async version of set()."""
        ...

    async def exists_async(self, key: str) -> bool:
        """Async version of exists()."""
        ...


class InMemoryIdempotencyStore:
    """
    In-memory idempotency store for testing.
    
    NOT FOR PRODUCTION - data lost on restart.
    Use Redis or database for production.
    """

    def __init__(self):
        self._store = {}
        self._expiry = {}

    def get(self, key: str) -> Optional[Any]:
        # Check expiry
        if key in self._expiry:
            if time.time() > self._expiry[key]:
                del self._store[key]
                del self._expiry[key]
                return None

        return self._store.get(key)

    def set(self, key: str, value: Any, ttl: int = 86400) -> None:
        self._store[key] = value
        self._expiry[key] = time.time() + ttl

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    async def get_async(self, key: str) -> Optional[Any]:
        return self.get(key)

    async def set_async(self, key: str, value: Any, ttl: int = 86400) -> None:
        self.set(key, value, ttl)

    async def exists_async(self, key: str) -> bool:
        return self.exists(key)


class IdempotencyKey:
    """
    Utility class for generating idempotency keys.
    
    Provides standard key generation for different operation types.
    """

    @staticmethod
    def from_user_request(
        user_id: str, operation: str, **params
    ) -> str:
        """
        Generate key for user-initiated operations.
        
        Args:
            user_id: User identifier
            operation: Operation name (e.g., "deposit", "create_strategy")
            **params: Operation parameters
            
        Returns:
            Idempotency key (SHA256 hash)
            
        Example:
            key = IdempotencyKey.from_user_request(
                user_id="user123",
                operation="deposit",
                amount=1000,
                token="USDC"
            )
        """
        content = f"{user_id}_{operation}_{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()

    @staticmethod
    def from_trade(
        strategy_id: str, signal_hash: str, timestamp: int
    ) -> str:
        """
        Generate key for autonomous trade execution.
        
        Args:
            strategy_id: Strategy identifier
            signal_hash: Hash of trade signal
            timestamp: Unix timestamp
            
        Returns:
            Trade idempotency key
            
        Example:
            key = IdempotencyKey.from_trade(
                strategy_id="strat_456",
                signal_hash="abc123def456",
                timestamp=1730500000
            )
            # Returns: "trade_strat_456_1730500000_abc123def456"
        """
        return f"trade_{strategy_id}_{timestamp}_{signal_hash}"

    @staticmethod
    def from_blockchain_tx(
        operation: str, chain: str, params_hash: str
    ) -> str:
        """
        Generate key for blockchain transactions.
        
        Args:
            operation: Operation type (e.g., "bridge", "swap")
            chain: Blockchain name
            params_hash: Hash of transaction parameters
            
        Returns:
            Blockchain operation idempotency key
            
        Example:
            key = IdempotencyKey.from_blockchain_tx(
                operation="bridge",
                chain="solana",
                params_hash="def789"
            )
        """
        return f"blockchain_{operation}_{chain}_{params_hash}"

    @staticmethod
    def from_event(event_id: str) -> str:
        """
        Extract key from event.
        
        Args:
            event_id: Event identifier from event bus
            
        Returns:
            Event idempotency key
            
        Example:
            key = IdempotencyKey.from_event("evt_12345")
            # Returns: "event_evt_12345"
        """
        return f"event_{event_id}"

    @staticmethod
    def hash_params(**params) -> str:
        """
        Generate hash from parameters.
        
        Args:
            **params: Parameters to hash
            
        Returns:
            SHA256 hash of parameters
        """
        content = json.dumps(params, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class IdempotencyError(Exception):
    """Base exception for idempotency errors."""

    pass


class DuplicateRequestError(IdempotencyError):
    """Raised when duplicate request detected."""

    def __init__(self, key: str, cached_result: Any):
        self.key = key
        self.cached_result = cached_result
        super().__init__(f"Duplicate request with key: {key}")


def idempotent(
    key_param: str = "idempotency_key",
    store: Optional[IdempotencyStore] = None,
    ttl: int = 86400,
    raise_on_duplicate: bool = False,
):
    """
    Decorator to make function idempotent.
    
    Ensures function executes exactly once per idempotency key.
    Subsequent calls with same key return cached result.
    
    Args:
        key_param: Name of parameter containing idempotency key
        store: Storage backend (Redis, DB, etc.)
        ttl: Time to live for cached results (seconds, default: 24h)
        raise_on_duplicate: If True, raise DuplicateRequestError on duplicate
        
    Returns:
        Decorated function
        
    Example:
        @idempotent(key_param="request_id", store=redis_store, ttl=3600)
        def execute_trade(user_id: str, amount: float, request_id: str):
            # This executes only once per request_id
            return process_trade(user_id, amount)
        
        # First call - executes
        result1 = execute_trade("user123", 1000, "req_001")
        
        # Second call - returns cached result
        result2 = execute_trade("user123", 1000, "req_001")
        assert result1 == result2
    """
    if store is None:
        store = InMemoryIdempotencyStore()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Extract idempotency key
            key = kwargs.get(key_param)
            if not key:
                raise ValueError(
                    f"Missing required parameter: {key_param}"
                )

            # Check cache
            if store.exists(key):
                cached_result = store.get(key)
                logger.info(
                    f"Idempotent operation: returning cached result "
                    f"for key {key}"
                )

                if raise_on_duplicate:
                    raise DuplicateRequestError(key, cached_result)

                return cached_result

            # Execute function
            logger.info(f"Idempotent operation: executing for key {key}")
            result = func(*args, **kwargs)

            # Cache result
            store.set(key, result, ttl)
            logger.debug(
                f"Idempotent operation: cached result for key {key}"
            )

            return result

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract idempotency key
            key = kwargs.get(key_param)
            if not key:
                raise ValueError(
                    f"Missing required parameter: {key_param}"
                )

            # Check cache
            if await store.exists_async(key):
                cached_result = await store.get_async(key)
                logger.info(
                    f"Idempotent operation: returning cached result "
                    f"for key {key}"
                )

                if raise_on_duplicate:
                    raise DuplicateRequestError(key, cached_result)

                return cached_result

            # Execute function
            logger.info(f"Idempotent operation: executing for key {key}")
            result = await func(*args, **kwargs)

            # Cache result
            await store.set_async(key, result, ttl)
            logger.debug(
                f"Idempotent operation: cached result for key {key}"
            )

            return result

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


__all__ = [
    "IdempotencyStore",
    "InMemoryIdempotencyStore",
    "IdempotencyKey",
    "IdempotencyError",
    "DuplicateRequestError",
    "idempotent",
]

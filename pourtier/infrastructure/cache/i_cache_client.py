"""Cache client interface for key-value storage."""

from abc import ABC, abstractmethod
from typing import Optional


class ICacheClient(ABC):
    """Abstract cache client interface for Redis/Memcached."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to cache server."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to cache server."""

    @abstractmethod
    async def set(
        self,
        key: str,
        value: str,
        expire_seconds: Optional[int] = None,
    ) -> bool:
        """
        Store value with optional expiration.

        Args:
            key: Cache key
            value: Value to store (string)
            expire_seconds: TTL in seconds (None = no expiration)

        Returns:
            True if stored successfully
        """

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """
        Retrieve value by key.

        Args:
            key: Cache key

        Returns:
            Value if exists and not expired, None otherwise
        """

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if key didn't exist
        """

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists and not expired
        """

    @abstractmethod
    async def ping(self) -> bool:
        """
        Check if cache server is reachable.

        Returns:
            True if server responds
        """

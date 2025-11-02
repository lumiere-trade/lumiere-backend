"""
Distributed Indicator Registry - Redis Only

Cross-process indicator registry using Redis as single source.
Rebalancer has ZERO knowledge of InfluxDB.

Version: 2.0.0 - Redis Only
"""

import threading
from typing import Any, Dict, List, Optional

import redis
from rebalancer.interfaces.indicator_registry_interface import IIndicatorRegistry

from shared.reporter import SystemReporter
from shared.reporter.emojis import Emoji


class DistributedIndicatorRegistry(IIndicatorRegistry):
    """
    Redis-only indicator registry for rebalancer.

    Rebalancer reads indicators exclusively from Redis.
    Feeder is responsible for writing indicators to Redis.

    Redis keys format:
        indicator:{name}:{symbol}:{timeframe} = value
        indicator_history:{name}:{symbol}:{timeframe} = [v1, v2, v3...]

    Attributes:
        redis_client: Redis connection
        cache_ttl: Redis key TTL (seconds)
        _lock: Thread safety lock
    """

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        cache_ttl: int = 60,
    ):
        """
        Initialize Redis-only indicator registry.

        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
            redis_password: Redis password (optional)
            cache_ttl: Redis key TTL in seconds
        """
        self.reporter = SystemReporter(name="rebalancer")

        # Redis connection
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # Test connection
            self.redis_client.ping()

            self.reporter.info(
                f"{Emoji.DATABASE.READ} Redis connected: {redis_host}:{redis_port} (db={redis_db})",
                verbose_level=1,
            )

        except redis.RedisError as e:
            self.reporter.error(
                f"{Emoji.ERROR.CRITICAL} Failed to connect to Redis: {e}",
                verbose_level=0,
            )
            raise

        self.cache_ttl = cache_ttl
        self._lock = threading.RLock()

        self.reporter.info(
            f"{Emoji.SYSTEM.READY} DistributedIndicatorRegistry initialized (Redis-only, TTL={cache_ttl}s)",
            verbose_level=1,
        )

    def get_current_value(
        self, name: str, symbol: str, timeframe: str
    ) -> Optional[float]:
        """
        Get latest indicator value from Redis.

        Args:
            name: Indicator name (e.g., 'rsi_14')
            symbol: Trading pair symbol
            timeframe: Candle timeframe

        Returns:
            Latest indicator value or None if not found
        """
        redis_key = self._make_redis_key(name, symbol, timeframe)

        try:
            value = self.redis_client.get(redis_key)

            if value is not None:
                self.reporter.debug(
                    f"{Emoji.DATABASE.READ} Redis read: {redis_key} = {value}",
                    verbose_level=3,
                )
                return float(value)
            else:
                self.reporter.debug(
                    f"{Emoji.ERROR.WARNING} No data in Redis: {redis_key}",
                    verbose_level=3,
                )
                return None

        except redis.RedisError as e:
            self.reporter.error(
                f"{Emoji.ERROR.ERROR} Redis read failed: {e}", verbose_level=1
            )
            return None

        except ValueError as e:
            self.reporter.error(
                f"{Emoji.ERROR.ERROR} Invalid value in Redis for {redis_key}: {e}",
                verbose_level=1,
            )
            return None

    def get_historical_values(
        self, name: str, symbol: str, timeframe: str, lookback: int
    ) -> List[float]:
        """
        Get historical indicator values from Redis list.

        Args:
            name: Indicator name
            symbol: Trading pair symbol
            timeframe: Candle timeframe
            lookback: Number of values to retrieve

        Returns:
            List of historical values (chronological order)
        """
        redis_key = self._make_history_key(name, symbol, timeframe)

        try:
            # Get last N values from Redis list
            values = self.redis_client.lrange(redis_key, -lookback, -1)

            if values:
                result = [float(v) for v in values]
                self.reporter.debug(
                    f"{Emoji.DATABASE.READ} Historical: {redis_key} ({len(result)} values)",
                    verbose_level=3,
                )
                return result
            else:
                self.reporter.debug(
                    f"{Emoji.ERROR.WARNING} No historical data in Redis: {redis_key}",
                    verbose_level=3,
                )
                return []

        except redis.RedisError as e:
            self.reporter.error(
                f"{Emoji.ERROR.ERROR} Redis read failed: {e}", verbose_level=1
            )
            return []

        except ValueError as e:
            self.reporter.error(
                f"{Emoji.ERROR.ERROR} Invalid values in Redis list {redis_key}: {e}",
                verbose_level=1,
            )
            return []

    def evaluate_condition(
        self, name: str, symbol: str, timeframe: str, condition: Dict[str, Any]
    ) -> bool:
        """
        Evaluate trading condition on indicator.

        Supported operators:
            - 'greater_than': value > threshold
            - 'less_than': value < threshold
            - 'crosses_above': value[0] > threshold AND value[1] <= threshold
            - 'crosses_below': value[0] < threshold AND value[1] >= threshold
            - 'between': low < value < high

        Args:
            name: Indicator name
            symbol: Trading pair symbol
            timeframe: Candle timeframe
            condition: Condition dictionary with 'operator' and parameters

        Returns:
            True if condition is met, False otherwise
        """
        operator = condition.get("operator")
        if not operator:
            return False

        # Get current value
        current = self.get_current_value(name, symbol, timeframe)
        if current is None:
            return False

        # Simple comparisons
        if operator == "greater_than":
            threshold = condition.get("threshold", 0)
            return current > threshold

        if operator == "less_than":
            threshold = condition.get("threshold", 0)
            return current < threshold

        if operator == "between":
            low = condition.get("low", 0)
            high = condition.get("high", 100)
            return low < current < high

        # Cross operators need previous value
        if operator in ["crosses_above", "crosses_below"]:
            values = self.get_historical_values(name, symbol, timeframe, 2)
            if len(values) < 2:
                return False

            threshold = condition.get("threshold", 0)
            prev_value = values[-2]

            if operator == "crosses_above":
                return current > threshold and prev_value <= threshold

            if operator == "crosses_below":
                return current < threshold and prev_value >= threshold

        return False

    def _make_redis_key(self, name: str, symbol: str, timeframe: str) -> str:
        """
        Create Redis key for current indicator value.

        Args:
            name: Indicator name
            symbol: Trading symbol
            timeframe: Candle timeframe

        Returns:
            Redis key string
        """
        return f"indicator:{name}:{symbol}:{timeframe}"

    def _make_history_key(self, name: str, symbol: str, timeframe: str) -> str:
        """
        Create Redis key for indicator history list.

        Args:
            name: Indicator name
            symbol: Trading symbol
            timeframe: Candle timeframe

        Returns:
            Redis key string
        """
        return f"indicator_history:{name}:{symbol}:{timeframe}"

    def close(self) -> None:
        """Close Redis connection."""
        try:
            if hasattr(self, "redis_client"):
                self.redis_client.close()

            self.reporter.info(
                f"{Emoji.SYSTEM.CLEANUP} Redis connection closed", verbose_level=1
            )
        except Exception as e:
            self.reporter.warning(
                f"{Emoji.ERROR.WARNING} Error closing Redis: {e}", verbose_level=2
            )

    def __del__(self):
        """Cleanup on garbage collection."""
        try:
            if hasattr(self, "redis_client"):
                self.redis_client.close()
        except Exception:
            pass

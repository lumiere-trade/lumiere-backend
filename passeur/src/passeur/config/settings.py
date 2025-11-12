"""
Passeur configuration with hybrid YAML + ENV support.

Architecture:
- Python FastAPI (api_port): External proxy with resilience patterns
- Node.js Bridge (bridge_port): Internal blockchain operations

Priority: Environment variables > YAML config > Pydantic defaults
"""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CircuitBreakerConfig(BaseSettings):
    """Circuit breaker configuration for external services."""

    failure_threshold: int = Field(default=5, ge=1, le=100)
    success_threshold: int = Field(default=3, ge=1, le=10)
    timeout: float = Field(default=60.0, ge=1.0, le=600.0)


class RetryConfig(BaseSettings):
    """Retry configuration for transient failures."""

    max_attempts: int = Field(default=3, ge=1, le=10)
    initial_delay: float = Field(default=1.0, ge=0.1, le=10.0)
    max_delay: float = Field(default=30.0, ge=1.0, le=300.0)
    exponential_base: float = Field(default=2.0, ge=1.0, le=10.0)
    jitter: bool = Field(default=True)


class TimeoutConfig(BaseSettings):
    """Timeout configuration for operations."""

    rpc_call: float = Field(default=10.0, ge=1.0, le=60.0)
    transaction_confirmation: float = Field(default=30.0, ge=5.0, le=120.0)
    bridge_call: float = Field(default=15.0, ge=5.0, le=60.0)


class RateLimitConfig(BaseSettings):
    """Rate limiting configuration."""

    rpc_calls_per_second: float = Field(default=10.0, ge=1.0, le=1000.0)
    burst_size: int = Field(default=20, ge=1, le=1000)


class IdempotencyConfig(BaseSettings):
    """Idempotency TTL configuration (in days)."""

    financial_operations: int = Field(default=7, ge=1, le=30)
    security_operations: int = Field(default=3, ge=1, le=30)
    query_operations: int = Field(default=1, ge=1, le=7)


class ResilienceConfig(BaseSettings):
    """Resilience patterns configuration."""

    circuit_breakers: dict = Field(
        default_factory=lambda: {
            "solana_rpc": {
                "failure_threshold": 5,
                "success_threshold": 3,
                "timeout": 30.0,
            },
            "bridge_server": {
                "failure_threshold": 3,
                "success_threshold": 2,
                "timeout": 60.0,
            },
        }
    )

    retry: dict = Field(
        default_factory=lambda: {
            "transaction_submission": {
                "max_attempts": 3,
                "initial_delay": 2.0,
                "max_delay": 10.0,
                "exponential_base": 2.0,
                "jitter": True,
            },
            "rpc_query": {
                "max_attempts": 5,
                "initial_delay": 0.5,
                "max_delay": 5.0,
                "exponential_base": 2.0,
                "jitter": True,
            },
        }
    )

    timeouts: TimeoutConfig = Field(default_factory=TimeoutConfig)
    rate_limiting: RateLimitConfig = Field(default_factory=RateLimitConfig)
    idempotency: IdempotencyConfig = Field(default_factory=IdempotencyConfig)


class HealthConfig(BaseSettings):
    """Health check configuration."""

    port: int = Field(default=8080, ge=1024, le=65535)
    check_interval: int = Field(default=30, ge=5, le=300)


class MetricsConfig(BaseSettings):
    """Prometheus metrics configuration."""

    port: int = Field(default=9090, ge=1024, le=65535)
    enabled: bool = Field(default=True)


class RedisConfig(BaseSettings):
    """Redis configuration for caching and idempotency."""

    host: str = Field(default="localhost")
    port: int = Field(default=6379, ge=1024, le=65535)
    db: int = Field(default=0, ge=0, le=15)
    password: Optional[str] = Field(default=None)
    socket_timeout: float = Field(default=5.0, ge=1.0, le=60.0)
    socket_connect_timeout: float = Field(default=5.0, ge=1.0, le=60.0)


class PasseurConfig(BaseSettings):
    """
    Passeur configuration schema.

    Two-layer architecture:
    - Python FastAPI (external): Resilience proxy on api_port
    - Node.js Bridge (internal): Blockchain operations on bridge_port
    """

    model_config = SettingsConfigDict(
        env_prefix="PASSEUR_",
        case_sensitive=False,
        extra="allow",
    )

    # Python FastAPI (external - public API)
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(
        default=8766,
        ge=1024,
        le=65535,
        description="External port for Python FastAPI proxy",
    )

    # Node.js bridge (internal - localhost only)
    bridge_host: str = Field(default="127.0.0.1")
    bridge_port: int = Field(
        default=8768,
        ge=1024,
        le=65535,
        description="Internal port for Node.js bridge",
    )

    # Service URLs (Docker DNS)
    courier_url: str = Field(
        default="http://courier:8765",
        description="Courier WebSocket URL (Docker DNS)",
    )
    pourtier_url: str = Field(
        default="http://pourtier:8000",
        description="Pourtier API URL (Docker DNS)",
    )

    # Bridge behavior
    heartbeat_interval: int = Field(default=30, ge=5, le=300)
    request_timeout: int = Field(default=30, ge=5, le=300)

    # Logging
    log_level: str = Field(default="info")
    log_dir: str = Field(default="logs")

    # Blockchain configuration
    solana_rpc_url: Optional[str] = Field(default=None)
    solana_network: str = Field(default="devnet")
    program_id: str = Field(default="9gvUtaF99sQ287PNzRfCbhFTC4PUnnd7jdAjnY5GUVhS")
    platform_keypair_path: Optional[str] = Field(default=None)

    # Resilience configuration
    resilience: ResilienceConfig = Field(default_factory=ResilienceConfig)

    # Health checks
    health: HealthConfig = Field(default_factory=HealthConfig)

    # Metrics
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)

    # Redis
    redis: RedisConfig = Field(default_factory=RedisConfig)

    @computed_field
    @property
    def bridge_url(self) -> str:
        """Computed bridge URL for internal communication."""
        return f"http://{self.bridge_host}:{self.bridge_port}"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = ["debug", "info", "warning", "error", "critical"]
        v_lower = v.lower()
        if v_lower not in allowed:
            raise ValueError(f"Invalid log_level. Must be one of: {allowed}")
        return v_lower

    @field_validator("solana_network")
    @classmethod
    def validate_network(cls, v: str) -> str:
        """Validate Solana network."""
        allowed = ["devnet", "testnet", "mainnet-beta"]
        v_lower = v.lower()
        if v_lower not in allowed:
            raise ValueError(f"Invalid network. Must be one of: {allowed}")
        return v_lower

    @field_validator("platform_keypair_path")
    @classmethod
    def expand_keypair_path(cls, v: Optional[str]) -> Optional[str]:
        """Expand home directory in keypair path."""
        if v:
            return os.path.expanduser(v)
        return v

    def get_circuit_breaker_config(self, service: str) -> CircuitBreakerConfig:
        """Get circuit breaker config for a specific service."""
        config = self.resilience.circuit_breakers.get(service, {})
        return CircuitBreakerConfig(**config)

    def get_retry_config(self, operation: str) -> RetryConfig:
        """Get retry config for a specific operation."""
        config = self.resilience.retry.get(operation, {})
        return RetryConfig(**config)


def load_config(config_file: Optional[str] = None) -> PasseurConfig:
    """
    Load configuration from YAML files.

    Priority: Environment variables > environment-specific YAML > default YAML

    Args:
        config_file: Optional YAML filename override

    Returns:
        PasseurConfig instance
    """
    env = os.getenv("ENV", "production")

    config_map = {
        "production": "production.yaml",
        "development": "development.yaml",
        "test": "test.yaml",
    }

    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent
    config_dir = project_root / "config"

    default_config_path = config_dir / "default.yaml"
    merged_config = {}

    if default_config_path.exists():
        with open(default_config_path, "r") as f:
            loaded = yaml.safe_load(f)
            if loaded:
                merged_config = loaded

    if config_file is None:
        config_file = os.getenv("PASSEUR_CONFIG")
        if not config_file:
            config_file = config_map.get(env, "production.yaml")

    env_config_path = config_dir / config_file

    if env_config_path.exists():
        with open(env_config_path, "r") as f:
            loaded = yaml.safe_load(f)
            if loaded:
                merged_config.update(loaded)

    return PasseurConfig(**merged_config)


# Global settings instance
_settings: Optional[PasseurConfig] = None


def get_settings() -> PasseurConfig:
    """
    Get singleton settings instance.

    Returns:
        PasseurConfig instance
    """
    global _settings
    if _settings is None:
        _settings = load_config()
    return _settings

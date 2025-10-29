"""
Configuration management for Courier.

Hybrid configuration system using YAML files and environment variables.
Priority: Environment variables > YAML config > Pydantic defaults
"""

import os
from pathlib import Path
from typing import List, Optional

import yaml
from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Courier configuration schema.

    Loads configuration from:
    1. Environment variables (highest priority)
    2. YAML configuration files
    3. Pydantic defaults (lowest priority)

    Configuration files:
        - config/default.yaml: Base defaults
        - config/production.yaml: Production overrides
        - config/development.yaml: Development overrides
        - config/test.yaml: Test overrides
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )

    # Application
    APP_NAME: str = "Courier"
    APP_VERSION: str = "0.1.0"
    ENV: str = Field(default="production", description="Environment name")
    DEBUG: bool = Field(default=False, description="Debug mode")

    # API Server (mapped from YAML 'host' and 'port')
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8765, ge=1024, le=65535)

    # Service Discovery (Docker DNS)
    pourtier_url: str = Field(
        default="http://pourtier:8000",
        description="Pourtier service URL (Docker DNS)",
    )
    passeur_url: str = Field(
        default="http://passeur:8766",
        description="Passeur service URL (Docker DNS)",
    )

    # Channels (mapped from YAML 'channels')
    channels: List[str] = Field(
        default_factory=lambda: [
            "trade",
            "candles",
            "sys",
            "rsi",
            "extrema",
            "analysis",
            "strategy",
            "subscription",
            "payment",
            "deposit",
        ]
    )

    # Connection settings (mapped from YAML lowercase keys)
    heartbeat_interval: int = Field(default=30, ge=5, le=300)
    max_clients_per_channel: int = Field(default=0, ge=0)

    # JWT Authentication
    jwt_secret: Optional[str] = Field(
        default=None, description="JWT secret key (from environment)"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    require_auth: bool = Field(
        default=False,
        description="Require authentication for WebSocket connections",
    )

    # Graceful Shutdown
    shutdown_timeout: int = Field(
        default=30,
        ge=1,
        description="Maximum seconds to wait for graceful shutdown",
    )
    shutdown_grace_period: int = Field(
        default=5,
        ge=1,
        description="Seconds to wait for WebSocket clients to close",
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting",
    )
    rate_limit_publish_requests: int = Field(
        default=100,
        ge=1,
        description="Max publish requests per service per minute",
    )
    rate_limit_websocket_connections: int = Field(
        default=10,
        ge=1,
        description="Max WebSocket connections per user",
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        ge=1,
        description="Rate limit time window in seconds",
    )

    # Message Validation
    max_message_size: int = Field(
        default=1_048_576,  # 1MB
        ge=1024,
        description="Maximum WebSocket message size in bytes",
    )
    max_string_length: int = Field(
        default=10_000,
        ge=100,
        description="Maximum string field length in messages",
    )
    max_array_size: int = Field(
        default=1_000,
        ge=10,
        description="Maximum array field size in messages",
    )

    # Logging (mapped from YAML 'log_level')
    log_level: str = Field(default="info")
    log_file: Optional[str] = Field(default=None)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = ["debug", "info", "warning", "error", "critical"]
        v_lower = v.lower()
        if v_lower not in allowed:
            raise ValueError(f"Invalid log_level. Must be one of: {allowed}")
        return v_lower


# Legacy compatibility: BrokerConfig alias
BrokerConfig = Settings


def load_config(
    config_file: Optional[str] = None,
    env_file: Optional[str] = None,
    env: Optional[str] = None,
) -> Settings:
    """
    Load configuration from YAML files and environment variables.

    Priority: ENV vars > environment-specific YAML > default YAML > defaults

    Args:
        config_file: Optional YAML config filename override
        env_file: Optional .env filename (e.g., ".env.development")
        env: Optional environment name override

    Returns:
        Settings instance

    Raises:
        ValidationError: If required fields are missing
    """
    # Find project root (4 levels up from this file)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent
    config_dir = project_root / "config"

    # Determine environment (explicit parameter > ENV var > default)
    environment = env or os.getenv("ENV", "production")

    # Map environment to config and env files
    env_map = {
        "production": (".env.production", "production.yaml"),
        "development": (".env.development", "development.yaml"),
        "test": (".env.development", "test.yaml"),
    }

    # Load .env file FIRST (before Settings initialization)
    if env_file is None:
        default_env_file, default_config_file = env_map.get(
            environment, (".env.production", "production.yaml")
        )
        env_file = default_env_file
        if config_file is None:
            config_file = default_config_file

    env_file_path = project_root / env_file
    if env_file_path.exists():
        load_dotenv(env_file_path, override=True)

    # Load default config
    default_config_path = config_dir / "default.yaml"
    merged_config = {}

    if default_config_path.exists():
        with open(default_config_path, "r") as f:
            loaded = yaml.safe_load(f)
            if loaded:
                merged_config = loaded

    # Load environment-specific config (overrides defaults)
    if config_file:
        env_config_path = config_dir / config_file
        if env_config_path.exists():
            with open(env_config_path, "r") as f:
                loaded = yaml.safe_load(f)
                if loaded:
                    # Merge, including None values
                    for key, value in loaded.items():
                        merged_config[key] = value

    # Create Settings (env vars from dotenv + YAML merged)
    return Settings(**merged_config)


# Global settings singleton (lazy initialization)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or initialize global settings singleton.

    Returns:
        Settings instance

    Raises:
        ValidationError: If required configuration fields are missing
    """
    global _settings
    if _settings is None:
        _settings = load_config()
    return _settings


def override_settings(new_settings: Settings) -> None:
    """
    Override global settings (for testing).

    Args:
        new_settings: New Settings instance to use
    """
    global _settings
    _settings = new_settings


def reset_settings() -> None:
    """
    Reset settings to force re-initialization (for testing).

    This allows tests to change environment variables and reload config.
    """
    global _settings
    _settings = None

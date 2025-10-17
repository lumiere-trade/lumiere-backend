"""
Application settings with environment-based configuration.

Priority (highest to lowest):
1. Environment variables (from .env or system)
2. Environment-specific YAML config file (development.yaml, production.yaml)
3. Default YAML config file (default.yaml)
4. Pydantic defaults
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
    Courier application settings with environment variable support.

    All sensitive values should come from environment variables,
    not from YAML files.
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
        description="Pourtier service URL (Docker DNS)"
    )
    passeur_url: str = Field(
        default="http://passeur:8766",
        description="Passeur service URL (Docker DNS)"
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
        env: Optional environment name override (e.g., "development", "test")

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
        "test": (".env.development", "development.yaml"),
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
    # IMPORTANT: explicit None values from YAML must override defaults
    if config_file:
        env_config_path = config_dir / config_file
        if env_config_path.exists():
            with open(env_config_path, "r") as f:
                loaded = yaml.safe_load(f)
                if loaded:
                    # Merge, including None values (for explicit null in YAML)
                    for key, value in loaded.items():
                        merged_config[key] = value

    # Create Settings (env vars from dotenv + YAML merged)
    return Settings(**merged_config)


# Global settings singleton (lazy initialization)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or initialize global settings singleton.

    Lazy initialization ensures settings are only loaded when needed.

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

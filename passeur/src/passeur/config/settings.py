"""
Passeur configuration with hybrid YAML + ENV support.

This Python module wraps the Node.js bridge configuration for testing purposes.
The actual bridge uses config/default.yaml, config/development.yaml, config/production.yaml.

Priority: Environment variables > YAML config > Pydantic defaults
"""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class PasseurConfig(BaseSettings):
    """
    Passeur bridge configuration schema.

    Used by Python tests to validate config files.
    Actual bridge (Node.js) loads these same YAML files.
    """

    model_config = SettingsConfigDict(
        env_prefix="PASSEUR_",
        case_sensitive=False,
        extra="allow",
    )

    # Bridge Server
    bridge_host: str = Field(default="0.0.0.0")
    bridge_port: int = Field(default=8766, ge=1024, le=65535)

    # Service Discovery (Docker DNS)
    courier_url: str = Field(
        default="http://courier:8765", description="Courier WebSocket URL (Docker DNS)"
    )
    pourtier_url: str = Field(
        default="http://pourtier:8000", description="Pourtier API URL (Docker DNS)"
    )

    # Connection Settings
    heartbeat_interval: int = Field(default=30, ge=5, le=300)
    request_timeout: int = Field(default=30, ge=5, le=300)

    # Logging
    log_level: str = Field(default="info")
    log_dir: str = Field(default="logs")

    # Solana (from ENV)
    solana_rpc_url: Optional[str] = Field(default=None)
    solana_network: str = Field(default="devnet")
    program_id: str = Field(default="9gvUtaF99sQ287PNzRfCbhFTC4PUnnd7jdAjnY5GUVhS")

    # Platform Keypair (from ENV)
    platform_keypair_path: Optional[str] = Field(default=None)

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


def load_config(config_file: Optional[str] = None) -> PasseurConfig:
    """
    Load configuration from YAML files.

    Priority: Environment variables > environment-specific YAML > default YAML

    Args:
        config_file: Optional YAML filename override

    Returns:
        PasseurConfig instance
    """
    # Determine environment
    env = os.getenv("ENV", "production")

    # Map environment to config file
    config_map = {
        "production": "production.yaml",
        "development": "development.yaml",
    }

    # Find config directory
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent
    config_dir = project_root / "config"

    # Load default config first
    default_config_path = config_dir / "default.yaml"
    merged_config = {}

    if default_config_path.exists():
        with open(default_config_path, "r") as f:
            loaded = yaml.safe_load(f)
            if loaded:
                merged_config = loaded

    # Load environment-specific config
    if config_file is None:
        # Check for PASSEUR_CONFIG env var
        config_file = os.getenv("PASSEUR_CONFIG")
        if not config_file:
            config_file = config_map.get(env, "production.yaml")

    env_config_path = config_dir / config_file

    if env_config_path.exists():
        with open(env_config_path, "r") as f:
            loaded = yaml.safe_load(f)
            if loaded:
                merged_config.update(loaded)

    # Create config (env vars will override YAML)
    return PasseurConfig(**merged_config)

"""
Passeur configuration schema with environment variable support.
"""

import os
from pathlib import Path

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class PasseurConfig(BaseSettings):
    """
    Passeur bridge configuration.
    
    Reads from environment variables and YAML config files.
    Priority: Environment variables > YAML config > defaults
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    bridge_host: str = Field(
        default="0.0.0.0",
        description="Bridge server bind address",
    )
    bridge_port: int = Field(
        default=8766,
        ge=1024,
        le=65535,
        description="Bridge server port number",
    )
    solana_rpc_url: str = Field(
        default="https://api.devnet.solana.com",
        description="Solana RPC endpoint URL",
    )
    solana_network: str = Field(
        default="devnet",
        description="Solana network environment",
    )
    program_id: str = Field(
        default="9gvUtaF99sQ287PNzRfCbhFTC4PUnnd7jdAjnY5GUVhS",
        description="Escrow smart contract program ID",
    )
    platform_keypair_path: str = Field(
        default=os.path.expanduser("~/.lumiere/keypairs/platform.json"),
        description="Path to platform keypair JSON file",
    )
    heartbeat_interval: int = Field(
        default=30,
        ge=5,
        le=300,
        description="WebSocket heartbeat interval (seconds)",
    )
    request_timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="HTTP request timeout (seconds)",
    )
    log_level: str = Field(
        default="info",
        description="Logging level",
    )
    log_dir: str = Field(
        default="logs",
        description="Log directory path",
    )

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
    def expand_keypair_path(cls, v: str) -> str:
        """Expand home directory in keypair path."""
        return os.path.expanduser(v)


def load_config(config_file: str = "passeur.yaml") -> PasseurConfig:
    """
    Load Passeur configuration from YAML file and environment.

    Args:
        config_file: Config filename (default: passeur.yaml)

    Returns:
        PasseurConfig instance
    """
    # Allow override via environment variable
    config_file = os.getenv("PASSEUR_CONFIG", config_file)
    
    # Find config in project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent
    config_path = project_root / "config" / config_file

    # Load YAML config if exists
    yaml_config = {}
    if config_path.exists():
        with open(config_path, "r") as f:
            loaded = yaml.safe_load(f)
            if loaded:
                yaml_config = loaded

    # Create config (env vars will override)
    return PasseurConfig(**yaml_config)


# Global config instance
config = load_config()

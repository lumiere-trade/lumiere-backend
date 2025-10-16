"""
Application settings with environment-based configuration.

Priority (highest to lowest):
1. Environment variables (from .env or system)
2. YAML config file
3. Pydantic defaults
"""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All sensitive values (passwords, keys) should come from environment
    variables, not from YAML files.
    """

    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )

    # Application
    APP_NAME: str = "Pourtier"
    APP_VERSION: str = "0.1.0"
    ENV: str = Field(default="development", description="Environment name")
    DEBUG: bool = Field(default=False, description="Debug mode")

    # API Server
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000, ge=1024, le=65535)
    API_RELOAD: bool = Field(default=False)

    # Database (from environment!)
    DATABASE_URL: str = Field(..., description="Database connection URL")
    DATABASE_ECHO: bool = Field(default=False)

    # JWT Authentication (from environment!)
    JWT_SECRET_KEY: str = Field(..., description="JWT secret key")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRATION_HOURS: int = Field(default=24, ge=1)

    # Redis
    REDIS_ENABLED: bool = Field(default=False)
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379, ge=1024, le=65535)
    REDIS_DB: int = Field(default=0, ge=0, le=15)
    REDIS_PASSWORD: Optional[str] = Field(default=None)

    # Solana / Blockchain
    SOLANA_RPC_URL: str = Field(..., description="Solana RPC URL")
    SOLANA_NETWORK: str = Field(default="devnet")
    SOLANA_COMMITMENT: str = Field(default="confirmed")
    PASSEUR_BRIDGE_URL: str = Field(..., description="Passeur bridge URL")
    ESCROW_PROGRAM_ID: Optional[str] = Field(default=None)
    PLATFORM_KEYPAIR_PATH: Optional[str] = Field(default=None)

    # External Services
    COURIER_URL: str = Field(..., description="Courier event bus URL")
    COURIER_ENABLED: bool = Field(default=False)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: str = Field(default="logs/pourtier.log")

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"Invalid LOG_LEVEL. Must be one of: {allowed}")
        return v_upper

    @field_validator("SOLANA_NETWORK")
    @classmethod
    def validate_solana_network(cls, v: str) -> str:
        """Validate Solana network."""
        allowed = ["devnet", "testnet", "mainnet-beta"]
        v_lower = v.lower()
        if v_lower not in allowed:
            raise ValueError(f"Invalid SOLANA_NETWORK. Must be one of: {allowed}")
        return v_lower

    @field_validator("PLATFORM_KEYPAIR_PATH")
    @classmethod
    def expand_keypair_path(cls, v: Optional[str]) -> Optional[str]:
        """Expand home directory in keypair path."""
        if v:
            return os.path.expanduser(v)
        return v


def load_config(config_file: Optional[str] = None) -> Settings:
    """
    Load configuration from YAML file and environment variables.

    Priority: Environment variables > YAML config > Pydantic defaults

    Args:
        config_file: YAML config filename

    Returns:
        Settings instance
    """
    # Determine config file
    if config_file is None:
        env = os.getenv("ENV", "production")
        config_map = {
            "production": "pourtier.yaml",
            "test": "test.yaml",
            "development": "pourtier.yaml",
        }
        config_file = config_map.get(env, "pourtier.yaml")

    # Find config directory - look in project root
    # We're in src/pourtier/config/settings.py, go up to project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent  # Go up to project root
    config_path = project_root / "config" / config_file

    # Load YAML config if exists
    yaml_config = {}
    if config_path.exists():
        with open(config_path, "r") as f:
            loaded = yaml.safe_load(f)
            if loaded:
                yaml_config = loaded

    # Create Settings - env vars will override YAML
    return Settings(**yaml_config)


# Global settings singleton
settings: Settings = load_config()


def override_settings(new_settings: Settings) -> None:
    """Override global settings (for testing)."""
    global settings
    settings = new_settings

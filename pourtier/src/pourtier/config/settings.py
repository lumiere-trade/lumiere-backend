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
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    All sensitive values (passwords, keys) should come from environment
    variables, not from YAML files.
    """

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

    # Service Discovery (Docker DNS)
    COURIER_URL: str = Field(
        default="http://courier:8765",
        description="Courier service URL (Docker DNS)"
    )
    PASSEUR_URL: str = Field(
        default="http://passeur:8766",
        description="Passeur bridge URL (Docker DNS)"
    )

    # Database (from environment - REQUIRED in production)
    DATABASE_URL: str = Field(..., description="Database connection URL")
    DATABASE_ECHO: bool = Field(default=False)

    # JWT Authentication (from environment - REQUIRED in production)
    JWT_SECRET_KEY: str = Field(..., description="JWT secret key")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRATION_HOURS: int = Field(default=24, ge=1)

    # Redis
    REDIS_ENABLED: bool = Field(default=False)
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379, ge=1024, le=65535)
    REDIS_DB: int = Field(default=0, ge=0, le=15)
    REDIS_PASSWORD: Optional[str] = Field(default=None)

    # Solana / Blockchain (from environment - REQUIRED in production)
    SOLANA_RPC_URL: str = Field(..., description="Solana RPC URL")
    SOLANA_NETWORK: str = Field(default="devnet")
    SOLANA_COMMITMENT: str = Field(default="confirmed")
    ESCROW_PROGRAM_ID: Optional[str] = Field(default=None)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: Optional[str] = Field(default="logs/pourtier.log")

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
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent
    config_dir = project_root / "config"

    environment = env or os.getenv("ENV", "production")

    env_map = {
        "production": (".env.production", "production.yaml"),
        "development": (".env.development", "development.yaml"),
        "test": (".env.development", "test.yaml"),
    }

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

    default_config_path = config_dir / "default.yaml"
    merged_config = {}

    if default_config_path.exists():
        with open(default_config_path, "r") as f:
            loaded = yaml.safe_load(f)
            if loaded:
                merged_config = loaded

    if config_file:
        env_config_path = config_dir / config_file
        if env_config_path.exists():
            with open(env_config_path, "r") as f:
                loaded = yaml.safe_load(f)
                if loaded:
                    merged_config.update(loaded)

    return Settings(**merged_config)


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or initialize global settings singleton."""
    global _settings
    if _settings is None:
        _settings = load_config()
    return _settings


def override_settings(new_settings: Settings) -> None:
    """Override global settings (for testing)."""
    global _settings
    _settings = new_settings


def reset_settings() -> None:
    """Reset settings to force re-initialization (for testing)."""
    global _settings
    _settings = None

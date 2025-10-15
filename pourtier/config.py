"""
Configuration settings for Pourtier.
"""

from pathlib import Path

import yaml
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from config file and environment."""

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://pourtier_user:pourtier_pass@" "localhost:5432/pourtier_db"
    )
    DATABASE_ECHO: bool = False

    # Courier
    COURIER_URL: str = "http://localhost:8765"
    COURIER_ENABLED: bool = True

    # JWT Authentication
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Solana
    SOLANA_RPC_URL: str = "https://api.devnet.solana.com"
    SOLANA_COMMITMENT: str = "confirmed"
    ESCROW_PROGRAM_ID: str = ""
    PLATFORM_KEYPAIR_PATH: str = ""

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/pourtier.log"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = True


def load_config() -> Settings:
    """
    Load configuration from YAML file and environment variables.

    Priority: Environment variables > config.yaml > defaults
    """
    config_path = Path(__file__).parent / "config" / "pourtier.yaml"

    # Load from YAML if exists
    config_dict = {}
    if config_path.exists():
        with open(config_path, "r") as f:
            yaml_config = yaml.safe_load(f)
            if yaml_config:
                config_dict = yaml_config

    # Override with environment variables
    return Settings(**config_dict)


# Global settings instance
settings = load_config()

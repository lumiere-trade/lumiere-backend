"""
Unit tests for Passeur configuration.

Tests config loading, validation, and environment variable overrides.

Usage:
    python -m passeur.tests.unit.test_config
    laborant passeur --unit
"""

import os
from unittest.mock import patch

from shared.tests import LaborantTest

from passeur.config.settings import PasseurConfig, load_config


class TestPasseurConfig(LaborantTest):
    """Unit tests for Passeur configuration system."""

    component_name = "passeur"
    test_category = "unit"

    def setup(self):
        """Setup before all tests - load test config."""
        self.test_config = load_config("development.yaml")
        self.reporter.info("Loaded test configuration", context="Setup")

    def test_default_config(self):
        """Test default configuration values."""
        self.reporter.info("Testing default config values", context="Test")

        config = PasseurConfig()

        assert config.bridge_host == "0.0.0.0"
        assert config.bridge_port == 8766
        assert config.solana_network == "devnet"
        assert config.heartbeat_interval == 30
        assert config.request_timeout == 30
        assert config.log_level == "info"
        assert config.log_dir == "logs"

        self.reporter.info("Default config values correct", context="Test")

    def test_custom_config(self):
        """Test custom configuration values."""
        self.reporter.info("Testing custom config values", context="Test")

        config = PasseurConfig(
            bridge_host="127.0.0.1",
            bridge_port=8767,
            solana_network="testnet",
            log_level="debug",
            log_dir="custom/logs",
        )

        assert config.bridge_host == "127.0.0.1"
        assert config.bridge_port == 8767
        assert config.solana_network == "testnet"
        assert config.log_level == "debug"
        assert config.log_dir == "custom/logs"

        self.reporter.info("Custom config values correct", context="Test")

    def test_port_validation_min(self):
        """Test port number minimum validation."""
        self.reporter.info("Testing port minimum validation", context="Test")

        try:
            PasseurConfig(bridge_port=1023)
            assert False, "Should have raised ValueError"
        except ValueError:
            self.reporter.info("Port minimum validation works", context="Test")

    def test_port_validation_max(self):
        """Test port number maximum validation."""
        self.reporter.info("Testing port maximum validation", context="Test")

        try:
            PasseurConfig(bridge_port=65536)
            assert False, "Should have raised ValueError"
        except ValueError:
            self.reporter.info("Port maximum validation works", context="Test")

    def test_log_level_validation_valid(self):
        """Test log level validation for valid values."""
        self.reporter.info("Testing valid log levels", context="Test")

        valid_levels = ["debug", "info", "warning", "error", "critical"]
        for level in valid_levels:
            config = PasseurConfig(log_level=level)
            assert config.log_level == level.lower()

        self.reporter.info("All valid log levels accepted", context="Test")

    def test_log_level_validation_invalid(self):
        """Test log level validation rejects invalid values."""
        self.reporter.info("Testing invalid log level", context="Test")

        try:
            PasseurConfig(log_level="invalid")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid log_level" in str(e)
            self.reporter.info("Invalid log level rejected", context="Test")

    def test_network_validation_valid(self):
        """Test Solana network validation for valid values."""
        self.reporter.info("Testing valid Solana networks", context="Test")

        valid_networks = ["devnet", "testnet", "mainnet-beta"]
        for network in valid_networks:
            config = PasseurConfig(solana_network=network)
            assert config.solana_network == network.lower()

        self.reporter.info("All valid networks accepted", context="Test")

    def test_network_validation_invalid(self):
        """Test Solana network validation rejects invalid values."""
        self.reporter.info("Testing invalid Solana network", context="Test")

        try:
            PasseurConfig(solana_network="invalid-network")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid network" in str(e)
            self.reporter.info("Invalid network rejected", context="Test")

    def test_heartbeat_interval_validation_min(self):
        """Test heartbeat interval minimum validation."""
        self.reporter.info("Testing heartbeat interval minimum", context="Test")

        try:
            PasseurConfig(heartbeat_interval=4)
            assert False, "Should have raised ValueError"
        except ValueError:
            self.reporter.info("Heartbeat minimum validation works", context="Test")

    def test_heartbeat_interval_validation_max(self):
        """Test heartbeat interval maximum validation."""
        self.reporter.info("Testing heartbeat interval maximum", context="Test")

        try:
            PasseurConfig(heartbeat_interval=301)
            assert False, "Should have raised ValueError"
        except ValueError:
            self.reporter.info("Heartbeat maximum validation works", context="Test")

    def test_request_timeout_validation_min(self):
        """Test request timeout minimum validation."""
        self.reporter.info("Testing request timeout minimum", context="Test")

        try:
            PasseurConfig(request_timeout=4)
            assert False, "Should have raised ValueError"
        except ValueError:
            self.reporter.info("Timeout minimum validation works", context="Test")

    def test_request_timeout_validation_max(self):
        """Test request timeout maximum validation."""
        self.reporter.info("Testing request timeout maximum", context="Test")

        try:
            PasseurConfig(request_timeout=301)
            assert False, "Should have raised ValueError"
        except ValueError:
            self.reporter.info("Timeout maximum validation works", context="Test")

    def test_load_default_config(self):
        """Test loading default passeur.yaml config."""
        self.reporter.info("Testing load default config", context="Test")

        config = load_config()

        assert isinstance(config, PasseurConfig)
        assert config.bridge_port > 0

        self.reporter.info("Default config loaded successfully", context="Test")

    def test_load_test_config(self):
        """Test loading development.yaml config."""
        self.reporter.info("Testing load test config", context="Test")

        config = load_config("development.yaml")

        assert isinstance(config, PasseurConfig)
        assert config.bridge_host == "0.0.0.0"
        assert config.bridge_port == 9766
        assert config.solana_network == "devnet"
        assert config.log_level == "debug"
        assert config.log_dir == "logs"

        self.reporter.info("Test config loaded successfully", context="Test")

    def test_load_nonexistent_config(self):
        """Test loading non-existent config uses defaults."""
        self.reporter.info("Testing load non-existent config", context="Test")

        config = load_config("nonexistent.yaml")

        assert isinstance(config, PasseurConfig)
        assert config.bridge_port == 8766

        self.reporter.info("Non-existent config uses defaults", context="Test")

    def test_config_env_var_override(self):
        """Test PASSEUR_CONFIG environment variable override."""
        self.reporter.info("Testing PASSEUR_CONFIG env var", context="Test")

        with patch.dict(os.environ, {"PASSEUR_CONFIG": "development.yaml"}):
            config = load_config()

            assert config.bridge_port == 9766
            assert config.log_level == "debug"

        self.reporter.info("PASSEUR_CONFIG env var works", context="Test")

    def test_platform_keypair_path_expansion(self):
        """Test platform keypair path home directory expansion."""
        self.reporter.info("Testing keypair path expansion", context="Test")

        config = PasseurConfig(
            platform_keypair_path="~/.lumiere/keypairs/platform.json"
        )

        assert "~" not in config.platform_keypair_path
        assert config.platform_keypair_path.startswith("/")

        self.reporter.info("Home directory expanded correctly", context="Test")

    def test_program_id_validation(self):
        """Test program ID is valid Solana address format."""
        self.reporter.info("Testing program ID format", context="Test")

        config = PasseurConfig()

        assert len(config.program_id) == 44
        assert config.program_id.startswith(
            "9gvUtaF99sQ287PNzRfCbhFTC4PUnnd7jdAjnY5GUVhS"
        )

        self.reporter.info("Program ID format valid", context="Test")

    def test_log_dir_from_config(self):
        """Test log directory comes from config."""
        self.reporter.info("Testing log_dir from config", context="Test")

        config = load_config("development.yaml")

        assert config.log_dir == "logs"

        self.reporter.info("Log dir from config correct", context="Test")


if __name__ == "__main__":
    TestPasseurConfig.run_as_main()

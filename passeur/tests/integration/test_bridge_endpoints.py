"""
Integration tests for Bridge HTTP API endpoints.

Tests all bridge REST endpoints for user-based escrow operations.

Usage:
    laborant passeur --integration
"""

import requests

from passeur.config.settings import load_config
from shared.tests import LaborantTest


class TestBridgeEndpoints(LaborantTest):
    """Integration tests for Bridge HTTP API endpoints."""

    component_name = "passeur"
    test_category = "integration"

    def setup(self):
        """Setup before all tests - connect to running bridge service."""
        self.reporter.info("Connecting to bridge service...", context="Setup")

        self.test_config = load_config("test.yaml")
        self.bridge_url = f"http://passeur:{self.test_config.bridge_port}"

        self.reporter.info(f"Bridge URL: {self.bridge_url}", context="Setup")

    def teardown(self):
        """Cleanup after all tests."""
        self.reporter.info("Cleanup complete", context="Teardown")

    def test_health_endpoint(self):
        """Test /health endpoint returns correct structure."""
        self.reporter.info("Testing /health endpoint", context="Test")

        response = requests.get(f"{self.bridge_url}/health", timeout=5)

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"
        assert "network" in data
        assert "program" in data
        assert "wallet" in data
        assert "timestamp" in data

        self.reporter.info(
            f"Health check OK - network: {data['network']}",
            context="Test",
        )

    def test_health_endpoint_network(self):
        """Test health endpoint shows correct network."""
        self.reporter.info("Testing health endpoint network", context="Test")

        response = requests.get(f"{self.bridge_url}/health", timeout=5)
        data = response.json()

        assert data["network"] == self.test_config.solana_network

        self.reporter.info(
            f"Network correct: {self.test_config.solana_network}",
            context="Test",
        )

    def test_health_endpoint_program_id(self):
        """Test health endpoint shows correct program ID."""
        self.reporter.info("Testing health endpoint program ID", context="Test")

        response = requests.get(f"{self.bridge_url}/health", timeout=5)
        data = response.json()

        assert data["program"] == self.test_config.program_id
        assert len(data["program"]) == 44

        self.reporter.info(f"Program ID: {data['program'][:8]}...", context="Test")

    def test_prepare_initialize_missing_params(self):
        """Test /escrow/prepare-initialize rejects missing userWallet."""
        self.reporter.info("Testing prepare-initialize missing params", context="Test")

        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-initialize",
            json={},
            timeout=10,
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Missing" in data["error"]

        self.reporter.info("Missing params correctly rejected", context="Test")

    def test_prepare_initialize_invalid_wallet(self):
        """Test /escrow/prepare-initialize rejects invalid wallet."""
        self.reporter.info(
            "Testing prepare-initialize with invalid wallet", context="Test"
        )

        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-initialize",
            json={"userWallet": "invalid-wallet"},
            timeout=10,
        )

        assert response.status_code in [400, 500]
        data = response.json()
        assert data["success"] is False

        self.reporter.info("Invalid wallet rejected", context="Test")

    def test_prepare_initialize_valid_params(self):
        """Test /escrow/prepare-initialize with valid parameters."""
        self.reporter.info(
            "Testing prepare-initialize with valid params", context="Test"
        )

        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-initialize",
            json={
                "userWallet": "11111111111111111111111111111111",
                "maxBalance": 1000000,
            },
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "transaction" in data
        assert "escrowAccount" in data
        assert "bump" in data

        self.reporter.info(
            "Valid params accepted, transaction prepared", context="Test"
        )

    def test_prepare_delegate_platform_missing_params(self):
        """Test /escrow/prepare-delegate-platform missing parameters."""
        self.reporter.info(
            "Testing prepare-delegate-platform missing params",
            context="Test",
        )

        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-delegate-platform",
            json={
                "userWallet": "11111111111111111111111111111111",
                "escrowAccount": "11111111111111111111111111111111",
            },
            timeout=10,
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Missing" in data["error"]

        self.reporter.info("Missing params correctly rejected", context="Test")

    def test_prepare_delegate_platform_valid_params(self):
        """Test /escrow/prepare-delegate-platform with valid params."""
        self.reporter.info(
            "Testing prepare-delegate-platform with valid params",
            context="Test",
        )

        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-delegate-platform",
            json={
                "userWallet": "11111111111111111111111111111111",
                "escrowAccount": "11111111111111111111111111111111",
                "authority": "11111111111111111111111111111111",
            },
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "transaction" in data

        self.reporter.info(
            "Valid params accepted, transaction prepared", context="Test"
        )

    def test_prepare_delegate_trading_missing_params(self):
        """Test /escrow/prepare-delegate-trading missing parameters."""
        self.reporter.info(
            "Testing prepare-delegate-trading missing params",
            context="Test",
        )

        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-delegate-trading",
            json={
                "userWallet": "11111111111111111111111111111111",
                "escrowAccount": "11111111111111111111111111111111",
            },
            timeout=10,
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Missing" in data["error"]

        self.reporter.info("Missing params correctly rejected", context="Test")

    def test_prepare_delegate_trading_valid_params(self):
        """Test /escrow/prepare-delegate-trading with valid params."""
        self.reporter.info(
            "Testing prepare-delegate-trading with valid params",
            context="Test",
        )

        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-delegate-trading",
            json={
                "userWallet": "11111111111111111111111111111111",
                "escrowAccount": "11111111111111111111111111111111",
                "authority": "11111111111111111111111111111111",
            },
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "transaction" in data

        self.reporter.info(
            "Valid params accepted, transaction prepared", context="Test"
        )

    def test_prepare_revoke_platform_missing_params(self):
        """Test /escrow/prepare-revoke-platform missing parameters."""
        self.reporter.info(
            "Testing prepare-revoke-platform missing params",
            context="Test",
        )

        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-revoke-platform",
            json={"userWallet": "11111111111111111111111111111111"},
            timeout=10,
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Missing" in data["error"]

        self.reporter.info("Missing params correctly rejected", context="Test")

    def test_prepare_revoke_platform_valid_params(self):
        """Test /escrow/prepare-revoke-platform with valid params."""
        self.reporter.info(
            "Testing prepare-revoke-platform with valid params",
            context="Test",
        )

        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-revoke-platform",
            json={
                "userWallet": "11111111111111111111111111111111",
                "escrowAccount": "11111111111111111111111111111111",
            },
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "transaction" in data

        self.reporter.info(
            "Valid params accepted, transaction prepared", context="Test"
        )

    def test_prepare_revoke_trading_missing_params(self):
        """Test /escrow/prepare-revoke-trading missing parameters."""
        self.reporter.info(
            "Testing prepare-revoke-trading missing params",
            context="Test",
        )

        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-revoke-trading",
            json={"userWallet": "11111111111111111111111111111111"},
            timeout=10,
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Missing" in data["error"]

        self.reporter.info("Missing params correctly rejected", context="Test")

    def test_prepare_revoke_trading_valid_params(self):
        """Test /escrow/prepare-revoke-trading with valid params."""
        self.reporter.info(
            "Testing prepare-revoke-trading with valid params",
            context="Test",
        )

        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-revoke-trading",
            json={
                "userWallet": "11111111111111111111111111111111",
                "escrowAccount": "11111111111111111111111111111111",
            },
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "transaction" in data

        self.reporter.info(
            "Valid params accepted, transaction prepared", context="Test"
        )

    def test_prepare_deposit_missing_params(self):
        """Test /escrow/prepare-deposit rejects missing parameters."""
        self.reporter.info("Testing prepare-deposit missing params", context="Test")

        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-deposit",
            json={
                "userWallet": "11111111111111111111111111111111",
                "escrowAccount": "11111111111111111111111111111111",
            },
            timeout=10,
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Missing" in data["error"]

        self.reporter.info("Missing params correctly rejected", context="Test")

    def test_prepare_withdraw_missing_params(self):
        """Test /escrow/prepare-withdraw rejects missing parameters."""
        self.reporter.info("Testing prepare-withdraw missing params", context="Test")

        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-withdraw",
            json={"userWallet": "11111111111111111111111111111111"},
            timeout=10,
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Missing" in data["error"]

        self.reporter.info("Missing params correctly rejected", context="Test")

    def test_prepare_close_missing_params(self):
        """Test /escrow/prepare-close rejects missing parameters."""
        self.reporter.info("Testing prepare-close missing params", context="Test")

        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-close",
            json={"userWallet": "11111111111111111111111111111111"},
            timeout=10,
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Missing" in data["error"]

        self.reporter.info("Missing params correctly rejected", context="Test")

    def test_send_transaction_missing_params(self):
        """Test /escrow/send-transaction rejects missing parameters."""
        self.reporter.info("Testing send-transaction missing params", context="Test")

        response = requests.post(
            f"{self.bridge_url}/escrow/send-transaction",
            json={},
            timeout=10,
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Missing" in data["error"]

        self.reporter.info("Missing params correctly rejected", context="Test")

    def test_transaction_status_not_found(self):
        """Test /transaction/status with non-existent signature."""
        self.reporter.info("Testing transaction status not found", context="Test")

        fake_sig = "1" * 88

        response = requests.get(
            f"{self.bridge_url}/transaction/status/{fake_sig}", timeout=10
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["confirmed"] is False
        assert data["status"] in ["not_found", "invalid_signature"]

        self.reporter.info("Non-existent transaction handled", context="Test")

    def test_transaction_status_invalid_signature(self):
        """Test /transaction/status with invalid signature format."""
        self.reporter.info(
            "Testing transaction status invalid signature", context="Test"
        )

        response = requests.get(
            f"{self.bridge_url}/transaction/status/invalid-sig", timeout=10
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "invalid_signature"

        self.reporter.info("Invalid signature handled", context="Test")

    def test_balance_endpoint_invalid_account(self):
        """Test /escrow/balance with invalid account address."""
        self.reporter.info("Testing balance with invalid account", context="Test")

        response = requests.get(
            f"{self.bridge_url}/escrow/balance/invalid-account", timeout=10
        )

        assert response.status_code in [404, 500]
        data = response.json()
        assert data["success"] is False

        self.reporter.info("Invalid account rejected", context="Test")

    def test_balance_endpoint_nonexistent_account(self):
        """Test /escrow/balance with non-existent but valid address."""
        self.reporter.info("Testing balance with non-existent account", context="Test")

        fake_account = "11111111111111111111111111111111"

        response = requests.get(
            f"{self.bridge_url}/escrow/balance/{fake_account}", timeout=10
        )

        assert response.status_code in [404, 500]
        data = response.json()
        assert data["success"] is False

        self.reporter.info("Non-existent account handled", context="Test")

    def test_escrow_details_invalid_address(self):
        """Test /escrow/:address with invalid address."""
        self.reporter.info("Testing escrow details invalid address", context="Test")

        response = requests.get(f"{self.bridge_url}/escrow/invalid-address", timeout=10)

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

        self.reporter.info("Invalid escrow address rejected", context="Test")

    def test_escrow_details_nonexistent(self):
        """Test /escrow/:address with non-existent escrow."""
        self.reporter.info(
            "Testing escrow details non-existent account", context="Test"
        )

        fake_account = "11111111111111111111111111111111"

        response = requests.get(f"{self.bridge_url}/escrow/{fake_account}", timeout=10)

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

        self.reporter.info("Non-existent escrow handled", context="Test")


if __name__ == "__main__":
    TestBridgeEndpoints.run_as_main()

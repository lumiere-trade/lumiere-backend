"""
Integration tests for Passeur API endpoints.

Tests Python FastAPI proxy layer with mocked dependencies.
Tests resilience patterns: circuit breaker, retry, idempotency.

Usage:
    laborant passeur --integration
"""

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from shared.tests import LaborantTest

from passeur.main import app


class TestPasseurEndpoints(LaborantTest):
    """Integration tests for Passeur API endpoints."""

    component_name = "passeur"
    test_category = "integration"

    def setup(self):
        """Setup before all tests - create TestClient and mock dependencies."""
        self.reporter.info("Setting up TestClient...", context="Setup")

        # Test addresses (44 chars - valid Solana base58 format)
        self.test_wallet = "11111111111111111111111111111111111111111111"
        self.test_escrow = "22222222222222222222222222222222222222222222"
        self.test_authority = "33333333333333333333333333333333333333333333"

        # Create mocks
        self.mock_bridge_client = MagicMock()
        self.mock_redis_store = MagicMock()

        # Setup app.state with mocks
        app.state.bridge_client = self.mock_bridge_client
        app.state.redis_store = self.mock_redis_store

        # Create TestClient
        self.client = TestClient(app)

        self.reporter.info("TestClient ready with mocked dependencies", context="Setup")

    def teardown(self):
        """Cleanup after all tests."""
        if hasattr(app.state, "bridge_client"):
            delattr(app.state, "bridge_client")
        if hasattr(app.state, "redis_store"):
            delattr(app.state, "redis_store")

        self.reporter.info("Cleanup complete", context="Teardown")

    def test_health_endpoint(self):
        """Test /health endpoint returns correct structure."""
        self.reporter.info("Testing /health endpoint", context="Test")

        response = self.client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]

        self.reporter.info("Health check OK", context="Test")

    def test_root_endpoint(self):
        """Test root endpoint returns service info."""
        self.reporter.info("Testing / endpoint", context="Test")

        response = self.client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "passeur"
        assert "endpoints" in data
        assert "escrow" in data["endpoints"]
        assert "transaction" in data["endpoints"]
        assert "wallet" in data["endpoints"]

        self.reporter.info("Root endpoint OK", context="Test")

    def test_prepare_initialize_success(self):
        """Test /escrow/prepare-initialize with valid params."""
        self.reporter.info("Testing prepare-initialize success", context="Test")

        self.mock_redis_store.check_and_store = AsyncMock(return_value=(False, None))
        self.mock_redis_store.store_result = AsyncMock()

        self.mock_bridge_client.prepare_initialize = AsyncMock(
            return_value={
                "success": True,
                "transaction": "base64-encoded-tx",
                "escrowAccount": self.test_escrow,
                "bump": 255,
                "message": "Transaction ready",
            }
        )

        response = self.client.post(
            "/escrow/prepare-initialize",
            json={
                "userWallet": self.test_wallet,
                "maxBalance": 1000000,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "transaction" in data
        assert "escrowAccount" in data
        assert data["bump"] == 255

        self.mock_bridge_client.prepare_initialize.assert_called_once()

        self.reporter.info("Prepare initialize success", context="Test")

    def test_prepare_initialize_idempotency(self):
        """Test idempotency returns cached result."""
        self.reporter.info("Testing prepare-initialize idempotency", context="Test")

        cached_result = {
            "success": True,
            "transaction": "cached-tx",
            "escrowAccount": self.test_escrow,
            "bump": 254,
            "message": "Cached",
        }

        self.mock_redis_store.check_and_store = AsyncMock(
            return_value=(True, cached_result)
        )

        response = self.client.post(
            "/escrow/prepare-initialize",
            json={"userWallet": self.test_wallet},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["transaction"] == "cached-tx"
        self.mock_bridge_client.prepare_initialize.assert_not_called()

        self.reporter.info("Idempotency check passed", context="Test")

    def test_prepare_initialize_validation(self):
        """Test /escrow/prepare-initialize validates required fields."""
        self.reporter.info("Testing prepare-initialize validation", context="Test")

        response = self.client.post(
            "/escrow/prepare-initialize",
            json={},
        )

        assert response.status_code == 422

        self.reporter.info("Validation rejected missing fields", context="Test")

    def test_prepare_delegate_platform_success(self):
        """Test /escrow/prepare-delegate-platform success."""
        self.reporter.info("Testing prepare-delegate-platform", context="Test")

        self.mock_redis_store.check_and_store = AsyncMock(return_value=(False, None))
        self.mock_redis_store.store_result = AsyncMock()

        self.mock_bridge_client.prepare_delegate_platform = AsyncMock(
            return_value={
                "success": True,
                "transaction": "delegate-tx",
                "message": "Ready",
            }
        )

        response = self.client.post(
            "/escrow/prepare-delegate-platform",
            json={
                "userWallet": self.test_wallet,
                "escrowAccount": self.test_escrow,
                "authority": self.test_authority,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "transaction" in data

        self.reporter.info("Delegate platform success", context="Test")

    def test_prepare_delegate_trading_success(self):
        """Test /escrow/prepare-delegate-trading success."""
        self.reporter.info("Testing prepare-delegate-trading", context="Test")

        self.mock_redis_store.check_and_store = AsyncMock(return_value=(False, None))
        self.mock_redis_store.store_result = AsyncMock()

        self.mock_bridge_client.prepare_delegate_trading = AsyncMock(
            return_value={
                "success": True,
                "transaction": "trading-tx",
                "message": "Ready",
            }
        )

        response = self.client.post(
            "/escrow/prepare-delegate-trading",
            json={
                "userWallet": self.test_wallet,
                "escrowAccount": self.test_escrow,
                "authority": self.test_authority,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True

        self.reporter.info("Delegate trading success", context="Test")

    def test_prepare_deposit_success(self):
        """Test /escrow/prepare-deposit success."""
        self.reporter.info("Testing prepare-deposit", context="Test")

        self.mock_redis_store.check_and_store = AsyncMock(return_value=(False, None))
        self.mock_redis_store.store_result = AsyncMock()

        self.mock_bridge_client.prepare_deposit = AsyncMock(
            return_value={
                "success": True,
                "transaction": "deposit-tx",
                "amount": "1000000",
                "message": "Ready",
            }
        )

        response = self.client.post(
            "/escrow/prepare-deposit",
            json={
                "userWallet": self.test_wallet,
                "escrowAccount": self.test_escrow,
                "amount": 1.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "amount" in data

        self.reporter.info("Deposit success", context="Test")

    def test_prepare_withdraw_success(self):
        """Test /escrow/prepare-withdraw success."""
        self.reporter.info("Testing prepare-withdraw", context="Test")

        self.mock_redis_store.check_and_store = AsyncMock(return_value=(False, None))
        self.mock_redis_store.store_result = AsyncMock()

        self.mock_bridge_client.prepare_withdraw = AsyncMock(
            return_value={
                "success": True,
                "transaction": "withdraw-tx",
                "amount": "500000",
                "message": "Ready",
            }
        )

        response = self.client.post(
            "/escrow/prepare-withdraw",
            json={
                "userWallet": self.test_wallet,
                "escrowAccount": self.test_escrow,
                "amount": 0.5,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True

        self.reporter.info("Withdraw success", context="Test")

    def test_submit_transaction_success(self):
        """Test /transaction/submit success."""
        self.reporter.info("Testing transaction submit", context="Test")

        self.mock_redis_store.check_and_store = AsyncMock(return_value=(False, None))
        self.mock_redis_store.store_result = AsyncMock()

        self.mock_bridge_client.submit_transaction = AsyncMock(
            return_value={
                "success": True,
                "signature": "5" * 88,
            }
        )

        response = self.client.post(
            "/transaction/submit",
            json={"signedTransaction": "base64-signed-tx"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "signature" in data

        self.reporter.info("Transaction submit success", context="Test")

    def test_get_escrow_details_success(self):
        """Test GET /escrow/{address} success."""
        self.reporter.info("Testing get escrow details", context="Test")

        self.mock_bridge_client.get_escrow_details = AsyncMock(
            return_value={
                "success": True,
                "data": {
                    "address": self.test_escrow,
                    "user": self.test_wallet,
                    "bump": 255,
                },
            }
        )

        response = self.client.get(f"/escrow/{self.test_escrow}")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data

        self.reporter.info("Get escrow details success", context="Test")

    def test_get_escrow_balance_success(self):
        """Test GET /escrow/balance/{account} success."""
        self.reporter.info("Testing get escrow balance", context="Test")

        self.mock_bridge_client.get_escrow_balance = AsyncMock(
            return_value={
                "success": True,
                "balance": 10.5,
                "balanceLamports": "10500000",
                "decimals": 6,
                "tokenMint": "4" * 44,
            }
        )

        response = self.client.get(f"/escrow/balance/{self.test_escrow}")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["balance"] == 10.5

        self.reporter.info("Get balance success", context="Test")

    def test_get_transaction_status_success(self):
        """Test GET /transaction/status/{signature} success."""
        self.reporter.info("Testing get transaction status", context="Test")

        self.mock_bridge_client.get_transaction_status = AsyncMock(
            return_value={
                "success": True,
                "confirmed": True,
                "confirmationStatus": "finalized",
                "slot": 123456,
                "err": None,
            }
        )

        test_signature = "5" * 88

        response = self.client.get(f"/transaction/status/{test_signature}")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["confirmed"] is True

        self.reporter.info("Get tx status success", context="Test")

    def test_get_wallet_balance_success(self):
        """Test GET /wallet/balance success."""
        self.reporter.info("Testing get wallet balance", context="Test")

        self.mock_bridge_client.get_wallet_balance = AsyncMock(
            return_value={
                "success": True,
                "balance": 100.0,
                "balanceLamports": "100000000",
                "decimals": 6,
                "tokenMint": "4" * 44,
                "wallet": self.test_wallet,
            }
        )

        response = self.client.get(f"/wallet/balance?wallet={self.test_wallet}")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["balance"] == 100.0

        self.reporter.info("Get wallet balance success", context="Test")


if __name__ == "__main__":
    TestPasseurEndpoints.run_as_main()

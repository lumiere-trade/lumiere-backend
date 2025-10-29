"""
Unit tests for ValidateEventUseCase.

Tests event schema validation against Pydantic models.

Usage:
    python -m courier.tests.unit.application.use_cases.test_validate_event
    laborant courier --unit
"""

from pydantic import ValidationError
from shared.tests import LaborantTest

from courier.application.use_cases.validate_event import ValidateEventUseCase


class TestValidateEventUseCase(LaborantTest):
    """Unit tests for ValidateEventUseCase."""

    component_name = "courier"
    test_category = "unit"

    # ================================================================
    # Valid event tests
    # ================================================================

    def test_validate_backtest_started_event(self):
        """Test validating valid backtest.started event."""
        self.reporter.info("Testing backtest.started validation", context="Test")

        use_case = ValidateEventUseCase()

        valid_event = {
            "type": "backtest.started",
            "metadata": {
                "source": "cartographe",
                "user_id": "user_123",
            },
            "data": {
                "backtest_id": "bt_abc123",
                "job_id": "job_xyz789",
                "user_id": "user_123",
                "strategy_id": "strat_xyz",
                "parameters": {
                    "timeframe": {
                        "start": "2024-01-01T00:00:00Z",
                        "end": "2024-12-31T23:59:59Z",
                    },
                    "initial_capital": 10000.0,
                    "token_pair": "SOL/USDC",
                },
            },
        }

        result = use_case.execute("backtest.started", valid_event)

        assert result.type == "backtest.started"
        assert result.metadata.source == "cartographe"
        assert result.data.backtest_id == "bt_abc123"
        self.reporter.info("Valid backtest.started event validated", context="Test")

    def test_validate_prophet_tsdl_ready_event(self):
        """Test validating valid prophet.tsdl_ready event."""
        self.reporter.info("Testing prophet.tsdl_ready validation", context="Test")

        use_case = ValidateEventUseCase()

        valid_event = {
            "type": "prophet.tsdl_ready",
            "metadata": {
                "source": "prophet",
                "user_id": "user_456",
            },
            "data": {
                "conversation_id": "conv_abc123",
                "strategy_id": "strat_xyz789",
                "tsdl": "strategy MyStrategy { ... }",
                "metadata": {
                    "name": "RSI Momentum",
                    "description": "Trade based on RSI signals",
                    "strategy_composition": {"base_strategies": ["indicator_based"]},
                },
            },
        }

        result = use_case.execute("prophet.tsdl_ready", valid_event)

        assert result.type == "prophet.tsdl_ready"
        assert result.data["conversation_id"] == "conv_abc123"
        self.reporter.info("Valid prophet.tsdl_ready event validated", context="Test")

    def test_validate_trade_order_filled_event(self):
        """Test validating valid trade.order_filled event."""
        self.reporter.info("Testing trade.order_filled validation", context="Test")

        use_case = ValidateEventUseCase()

        valid_event = {
            "type": "trade.order_filled",
            "metadata": {
                "source": "chevalier",
                "user_id": "user_789",
            },
            "data": {
                "strategy_id": "strat_xyz",
                "user_id": "user_789",
                "order_id": "ord_123",
                "token": "SOL",
                "direction": "buy",
                "fill_price": 145.55,
                "fill_amount": 10.0,
                "total_value": 1455.50,
                "fees": 1.46,
                "tx_signature": "5Kq...",
            },
        }

        result = use_case.execute("trade.order_filled", valid_event)

        assert result.type == "trade.order_filled"
        assert result.data["order_id"] == "ord_123"
        self.reporter.info("Valid trade.order_filled event validated", context="Test")

    # ================================================================
    # Invalid event tests
    # ================================================================

    def test_validate_unknown_event_type(self):
        """Test validating unknown event type raises error."""
        self.reporter.info("Testing unknown event type", context="Test")

        use_case = ValidateEventUseCase()

        event = {
            "type": "unknown.event",
            "metadata": {"source": "test"},
            "data": {},
        }

        try:
            use_case.execute("unknown.event", event)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown event type" in str(e)
            self.reporter.info("Unknown event type rejected", context="Test")

    def test_validate_missing_required_field(self):
        """Test validating event with missing required field."""
        self.reporter.info("Testing missing required field", context="Test")

        use_case = ValidateEventUseCase()

        invalid_event = {
            "type": "backtest.started",
            "metadata": {"source": "cartographe"},
            "data": {
                # Missing backtest_id, strategy_id, parameters
                "job_id": "job_xyz789",
                "user_id": "user_123",
            },
        }

        try:
            use_case.execute("backtest.started", invalid_event)
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            # Check that validation error mentions missing fields
            error_fields = [err["loc"] for err in e.errors()]
            assert ("data", "backtest_id") in error_fields
            self.reporter.info("Missing required field rejected", context="Test")

    def test_validate_invalid_progress_value(self):
        """Test validating backtest.progress with invalid progress value."""
        self.reporter.info("Testing invalid progress value", context="Test")

        use_case = ValidateEventUseCase()

        invalid_event = {
            "type": "backtest.progress",
            "metadata": {"source": "cartographe"},
            "data": {
                "backtest_id": "bt_123",
                "job_id": "job_123",
                "user_id": "user_123",
                "progress": 1.5,  # Invalid: > 1.0
                "stage": "calculating",
                "message": "Processing...",
            },
        }

        try:
            use_case.execute("backtest.progress", invalid_event)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            self.reporter.info("Invalid progress value rejected", context="Test")

    def test_validate_wrong_event_type_for_data(self):
        """Test validating event with mismatched type and data."""
        self.reporter.info("Testing mismatched type and data", context="Test")

        use_case = ValidateEventUseCase()

        # Prophet event data with backtest event type
        mismatched_event = {
            "type": "backtest.started",
            "metadata": {"source": "prophet"},
            "data": {
                "conversation_id": "conv_123",  # Prophet fields
                "tsdl": "...",  # Wrong fields for backtest.started
            },
        }

        try:
            use_case.execute("backtest.started", mismatched_event)
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            # Should fail because missing backtest.started required fields
            error_fields = [err["loc"] for err in e.errors()]
            assert len(error_fields) > 0
            self.reporter.info("Mismatched type/data rejected", context="Test")

    # ================================================================
    # Helper method tests
    # ================================================================

    def test_get_supported_event_types(self):
        """Test getting list of supported event types."""
        self.reporter.info("Testing get supported event types", context="Test")

        use_case = ValidateEventUseCase()
        supported_types = use_case.get_supported_event_types()

        assert isinstance(supported_types, list)
        assert len(supported_types) > 0
        assert "backtest.started" in supported_types
        assert "prophet.tsdl_ready" in supported_types
        assert "trade.order_filled" in supported_types
        self.reporter.info(
            f"Found {len(supported_types)} supported event types", context="Test"
        )

    def test_is_event_type_supported_true(self):
        """Test checking if known event type is supported."""
        self.reporter.info("Testing is_event_type_supported (true)", context="Test")

        use_case = ValidateEventUseCase()

        assert use_case.is_event_type_supported("backtest.started") is True
        assert use_case.is_event_type_supported("prophet.tsdl_ready") is True
        self.reporter.info("Known event types recognized", context="Test")

    def test_is_event_type_supported_false(self):
        """Test checking if unknown event type is supported."""
        self.reporter.info("Testing is_event_type_supported (false)", context="Test")

        use_case = ValidateEventUseCase()

        assert use_case.is_event_type_supported("unknown.event") is False
        assert use_case.is_event_type_supported("invalid.type") is False
        self.reporter.info("Unknown event types rejected", context="Test")

    # ================================================================
    # All event type coverage tests
    # ================================================================

    def test_validate_all_prophet_events(self):
        """Test validating all Prophet event types."""
        self.reporter.info("Testing all Prophet events", context="Test")

        use_case = ValidateEventUseCase()

        prophet_events = [
            (
                "prophet.message_chunk",
                {
                    "conversation_id": "conv_123",
                    "chunk": "test",
                    "is_final": False,
                },
            ),
            (
                "prophet.tsdl_ready",
                {
                    "conversation_id": "conv_123",
                    "strategy_id": "strat_123",
                    "tsdl": "...",
                    "metadata": {},
                },
            ),
            (
                "prophet.error",
                {
                    "conversation_id": "conv_123",
                    "error_code": "TEST",
                    "message": "test",
                    "details": "",
                },
            ),
        ]

        for event_type, data in prophet_events:
            event = {
                "type": event_type,
                "metadata": {"source": "prophet"},
                "data": data,
            }
            result = use_case.execute(event_type, event)
            assert result.type == event_type

        self.reporter.info("All Prophet events validated", context="Test")

    def test_validate_all_cartographe_events(self):
        """Test validating all Cartographe event types."""
        self.reporter.info("Testing all Cartographe events", context="Test")

        use_case = ValidateEventUseCase()

        cartographe_test_data = {
            "backtest.started": {
                "backtest_id": "bt_123",
                "job_id": "job_123",
                "user_id": "user_123",
                "strategy_id": "strat_123",
                "parameters": {},
            },
            "backtest.progress": {
                "backtest_id": "bt_123",
                "job_id": "job_123",
                "user_id": "user_123",
                "progress": 0.5,
                "stage": "test",
                "message": "test",
            },
            "backtest.completed": {
                "backtest_id": "bt_123",
                "job_id": "job_123",
                "user_id": "user_123",
                "duration_seconds": 10,
                "summary": {},
            },
            "backtest.failed": {
                "backtest_id": "bt_123",
                "job_id": "job_123",
                "user_id": "user_123",
                "error_code": "TEST",
                "message": "test",
                "details": "",
            },
            "backtest.cancelled": {
                "backtest_id": "bt_123",
                "job_id": "job_123",
                "user_id": "user_123",
                "reason": "test",
                "progress_at_cancellation": 0.5,
            },
        }

        for event_type, data in cartographe_test_data.items():
            event = {
                "type": event_type,
                "metadata": {"source": "cartographe"},
                "data": data,
            }

            result = use_case.execute(event_type, event)
            assert result.type == event_type

        self.reporter.info("All Cartographe events validated", context="Test")


if __name__ == "__main__":
    TestValidateEventUseCase.run_as_main()

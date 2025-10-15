"""
Unit tests for EscrowTransaction entity.

Tests transaction confirmation lifecycle and state transitions.

Usage:
    python -m pourtier.tests.unit.domain.entities.test_escrow_transaction
    laborant pourtier --unit
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pourtier.domain.entities.escrow_transaction import (
    EscrowTransaction,
    TransactionStatus,
    TransactionType,
)
from shared.tests import LaborantTest


class TestEscrowTransaction(LaborantTest):
    """Unit tests for EscrowTransaction entity."""

    component_name = "pourtier"
    test_category = "unit"

    # ================================================================
    # Creation tests
    # ================================================================

    def test_create_transaction(self):
        """Test creating EscrowTransaction with required fields."""
        self.reporter.info("Testing transaction creation", context="Test")

        user_id = uuid4()
        tx = EscrowTransaction(
            user_id=user_id,
            tx_signature="5J7Xk9N2BvPqYvJzUq4g...",
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("100.5"),
            token_mint="USDC",
        )

        assert tx.user_id == user_id
        assert tx.tx_signature == "5J7Xk9N2BvPqYvJzUq4g..."
        assert tx.transaction_type == TransactionType.DEPOSIT
        assert tx.amount == Decimal("100.5")
        assert tx.token_mint == "USDC"
        assert tx.status == TransactionStatus.PENDING
        self.reporter.info("Transaction created", context="Test")

    def test_transaction_auto_generates_id(self):
        """Test EscrowTransaction auto-generates UUID."""
        self.reporter.info("Testing auto-generated UUID", context="Test")

        tx = EscrowTransaction(
            user_id=uuid4(),
            tx_signature="test_sig",
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("10.0"),
            token_mint="USDC",
        )

        assert isinstance(tx.id, UUID)
        self.reporter.info(f"Generated UUID: {tx.id}", context="Test")

    def test_transaction_auto_generates_timestamp(self):
        """Test EscrowTransaction auto-generates created_at."""
        self.reporter.info("Testing auto-generated timestamp", context="Test")

        tx = EscrowTransaction(
            user_id=uuid4(),
            tx_signature="test_sig",
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("10.0"),
            token_mint="USDC",
        )

        assert isinstance(tx.created_at, datetime)
        self.reporter.info("Timestamp auto-generated", context="Test")

    def test_default_status_pending(self):
        """Test default status is PENDING."""
        self.reporter.info("Testing default status is PENDING", context="Test")

        tx = EscrowTransaction(
            user_id=uuid4(),
            tx_signature="test_sig",
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("10.0"),
            token_mint="USDC",
        )

        assert tx.status == TransactionStatus.PENDING
        self.reporter.info("Default status is PENDING", context="Test")

    def test_create_initialize_transaction(self):
        """Test creating INITIALIZE transaction (no amount)."""
        self.reporter.info("Testing INITIALIZE transaction", context="Test")

        tx = EscrowTransaction(
            user_id=uuid4(),
            tx_signature="init_sig",
            transaction_type=TransactionType.INITIALIZE,
            amount=Decimal("0"),
            token_mint="USDC",
        )

        assert tx.transaction_type == TransactionType.INITIALIZE
        assert tx.amount == Decimal("0")
        self.reporter.info("INITIALIZE transaction created", context="Test")

    def test_create_withdraw_transaction(self):
        """Test creating WITHDRAW transaction."""
        self.reporter.info("Testing WITHDRAW transaction", context="Test")

        tx = EscrowTransaction(
            user_id=uuid4(),
            tx_signature="withdraw_sig",
            transaction_type=TransactionType.WITHDRAW,
            amount=Decimal("50.0"),
            token_mint="USDC",
        )

        assert tx.transaction_type == TransactionType.WITHDRAW
        assert tx.amount == Decimal("50.0")
        self.reporter.info("WITHDRAW transaction created", context="Test")

    # ================================================================
    # Validation tests
    # ================================================================

    def test_reject_empty_tx_signature(self):
        """Test transaction rejects empty tx_signature."""
        self.reporter.info("Testing rejection of empty tx_signature", context="Test")

        try:
            EscrowTransaction(
                user_id=uuid4(),
                tx_signature="",
                transaction_type=TransactionType.DEPOSIT,
                amount=Decimal("10.0"),
                token_mint="USDC",
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Transaction signature is required" in str(e)
            self.reporter.info("Empty tx_signature correctly rejected", context="Test")

    def test_reject_zero_amount_for_deposit(self):
        """Test transaction rejects zero amount for deposit."""
        self.reporter.info("Testing rejection of zero amount", context="Test")

        try:
            EscrowTransaction(
                user_id=uuid4(),
                tx_signature="test_sig",
                transaction_type=TransactionType.DEPOSIT,
                amount=Decimal("0"),
                token_mint="USDC",
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Transaction amount must be positive" in str(e)
            self.reporter.info("Zero amount correctly rejected", context="Test")

    def test_reject_negative_amount(self):
        """Test transaction rejects negative amount."""
        self.reporter.info("Testing rejection of negative amount", context="Test")

        try:
            EscrowTransaction(
                user_id=uuid4(),
                tx_signature="test_sig",
                transaction_type=TransactionType.DEPOSIT,
                amount=Decimal("-10.0"),
                token_mint="USDC",
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Transaction amount must be positive" in str(e)
            self.reporter.info("Negative amount correctly rejected", context="Test")

    def test_reject_empty_token_mint(self):
        """Test transaction rejects empty token_mint."""
        self.reporter.info("Testing rejection of empty token_mint", context="Test")

        try:
            EscrowTransaction(
                user_id=uuid4(),
                tx_signature="test_sig",
                transaction_type=TransactionType.DEPOSIT,
                amount=Decimal("10.0"),
                token_mint="",
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Token mint is required" in str(e)
            self.reporter.info("Empty token_mint correctly rejected", context="Test")

    # ================================================================
    # Confirm tests
    # ================================================================

    def test_confirm_transaction(self):
        """Test confirm() marks transaction as confirmed."""
        self.reporter.info("Testing confirm() method", context="Test")

        tx = EscrowTransaction(
            user_id=uuid4(),
            tx_signature="test_sig",
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("100.0"),
            token_mint="USDC",
        )

        tx.confirm()

        assert tx.status == TransactionStatus.CONFIRMED
        assert tx.confirmed_at is not None
        assert isinstance(tx.confirmed_at, datetime)
        self.reporter.info("Transaction confirmed successfully", context="Test")

    def test_reject_confirm_from_confirmed(self):
        """Test confirm() rejects if already CONFIRMED."""
        self.reporter.info("Testing confirm() rejection from CONFIRMED", context="Test")

        tx = EscrowTransaction(
            user_id=uuid4(),
            tx_signature="test_sig",
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("10.0"),
            token_mint="USDC",
        )

        tx.confirm()

        try:
            tx.confirm()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Cannot confirm transaction in confirmed" in str(e)
            self.reporter.info(
                "Confirm from CONFIRMED correctly rejected",
                context="Test",
            )

    def test_reject_confirm_from_failed(self):
        """Test confirm() rejects from FAILED status."""
        self.reporter.info("Testing confirm() rejection from FAILED", context="Test")

        tx = EscrowTransaction(
            user_id=uuid4(),
            tx_signature="test_sig",
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("10.0"),
            token_mint="USDC",
        )

        tx.fail()

        try:
            tx.confirm()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Cannot confirm transaction in failed" in str(e)
            self.reporter.info("Confirm from FAILED correctly rejected", context="Test")

    # ================================================================
    # Fail tests
    # ================================================================

    def test_fail_transaction(self):
        """Test fail() marks transaction as failed."""
        self.reporter.info("Testing fail() method", context="Test")

        tx = EscrowTransaction(
            user_id=uuid4(),
            tx_signature="test_sig",
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("100.0"),
            token_mint="USDC",
        )

        tx.fail()

        assert tx.status == TransactionStatus.FAILED
        self.reporter.info("Transaction failed successfully", context="Test")

    def test_reject_fail_from_confirmed(self):
        """Test fail() rejects from CONFIRMED status."""
        self.reporter.info("Testing fail() rejection from CONFIRMED", context="Test")

        tx = EscrowTransaction(
            user_id=uuid4(),
            tx_signature="test_sig",
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("10.0"),
            token_mint="USDC",
        )

        tx.confirm()

        try:
            tx.fail()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Cannot fail transaction in confirmed" in str(e)
            self.reporter.info("Fail from CONFIRMED correctly rejected", context="Test")

    def test_reject_fail_from_failed(self):
        """Test fail() rejects if already FAILED."""
        self.reporter.info("Testing fail() rejection from FAILED", context="Test")

        tx = EscrowTransaction(
            user_id=uuid4(),
            tx_signature="test_sig",
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("10.0"),
            token_mint="USDC",
        )

        tx.fail()

        try:
            tx.fail()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Cannot fail transaction in failed" in str(e)
            self.reporter.info("Fail from FAILED correctly rejected", context="Test")

    # ================================================================
    # Serialization tests
    # ================================================================

    def test_to_dict_serialization(self):
        """Test to_dict() returns correct dictionary."""
        self.reporter.info("Testing to_dict() serialization", context="Test")

        user_id = uuid4()
        tx = EscrowTransaction(
            user_id=user_id,
            tx_signature="5J7Xk9N2BvPqYvJzUq4g...",
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("100.5"),
            token_mint="USDC",
        )

        tx.confirm()

        result = tx.to_dict()

        assert result["id"] == str(tx.id)
        assert result["user_id"] == str(user_id)
        assert result["tx_signature"] == "5J7Xk9N2BvPqYvJzUq4g..."
        assert result["transaction_type"] == "deposit"
        assert result["amount"] == "100.5"
        assert result["token_mint"] == "USDC"
        assert result["status"] == "confirmed"
        assert result["subscription_id"] is None
        assert result["confirmed_at"] is not None
        assert "created_at" in result
        assert len(result) == 10
        self.reporter.info("to_dict() serialization correct", context="Test")

    def test_to_dict_with_none_values(self):
        """Test to_dict() handles None optional fields."""
        self.reporter.info("Testing to_dict() with None values", context="Test")

        tx = EscrowTransaction(
            user_id=uuid4(),
            tx_signature="test_sig",
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("10.0"),
            token_mint="USDC",
        )

        result = tx.to_dict()

        assert result["confirmed_at"] is None
        assert result["subscription_id"] is None
        self.reporter.info("to_dict() handles None values", context="Test")

    # ================================================================
    # Enum tests
    # ================================================================

    def test_transaction_type_enum_values(self):
        """Test TransactionType enum has correct values."""
        self.reporter.info("Testing TransactionType enum", context="Test")

        assert TransactionType.INITIALIZE.value == "initialize"
        assert TransactionType.DEPOSIT.value == "deposit"
        assert TransactionType.WITHDRAW.value == "withdraw"
        assert TransactionType.SUBSCRIPTION_FEE.value == "subscription_fee"
        self.reporter.info("TransactionType enum correct", context="Test")

    def test_transaction_status_enum_values(self):
        """Test TransactionStatus enum has correct values."""
        self.reporter.info("Testing TransactionStatus enum", context="Test")

        assert TransactionStatus.PENDING.value == "pending"
        assert TransactionStatus.CONFIRMED.value == "confirmed"
        assert TransactionStatus.FAILED.value == "failed"
        self.reporter.info("TransactionStatus enum correct", context="Test")

    # ================================================================
    # Lifecycle tests
    # ================================================================

    def test_transaction_lifecycle_confirmed(self):
        """Test transaction lifecycle: PENDING → CONFIRMED."""
        self.reporter.info("Testing confirmed transaction lifecycle", context="Test")

        tx = EscrowTransaction(
            user_id=uuid4(),
            tx_signature="test_sig",
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("100.0"),
            token_mint="USDC",
        )

        # PENDING
        assert tx.status == TransactionStatus.PENDING
        assert tx.confirmed_at is None

        # → CONFIRMED
        tx.confirm()
        assert tx.status == TransactionStatus.CONFIRMED
        assert tx.confirmed_at is not None

        self.reporter.info("Confirmed transaction lifecycle complete", context="Test")

    def test_transaction_lifecycle_failed(self):
        """Test transaction lifecycle: PENDING → FAILED."""
        self.reporter.info("Testing failed transaction lifecycle", context="Test")

        tx = EscrowTransaction(
            user_id=uuid4(),
            tx_signature="test_sig",
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("100.0"),
            token_mint="USDC",
        )

        # PENDING
        assert tx.status == TransactionStatus.PENDING

        # → FAILED
        tx.fail()
        assert tx.status == TransactionStatus.FAILED

        self.reporter.info("Failed transaction lifecycle complete", context="Test")


if __name__ == "__main__":
    TestEscrowTransaction.run_as_main()

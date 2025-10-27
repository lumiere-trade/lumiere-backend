"""
Unit tests for ChannelName value object.

Tests channel name validation and formatting.

Usage:
    python -m courier.tests.unit.domain.value_objects.test_channel_name
    laborant courier --unit
"""

from courier.domain.value_objects.channel_name import ChannelName
from shared.tests import LaborantTest


class TestChannelName(LaborantTest):
    """Unit tests for ChannelName value object."""

    component_name = "courier"
    test_category = "unit"

    # ================================================================
    # Creation & Validation tests
    # ================================================================

    def test_create_valid_channel_name(self):
        """Test creating ChannelName with valid name."""
        self.reporter.info("Testing valid channel name creation", context="Test")

        name = ChannelName("user.123")

        assert name.value == "user.123"
        assert str(name) == "user.123"
        self.reporter.info("Valid channel name accepted", context="Test")

    def test_create_global_channel(self):
        """Test creating global channel name."""
        self.reporter.info("Testing global channel name", context="Test")

        name = ChannelName("global")

        assert name.value == "global"
        assert name.is_global() is True
        self.reporter.info("Global channel created", context="Test")

    def test_create_user_channel(self):
        """Test creating user channel name."""
        self.reporter.info("Testing user channel name", context="Test")

        name = ChannelName("user.abc123")

        assert name.value == "user.abc123"
        assert name.is_user_channel() is True
        self.reporter.info("User channel created", context="Test")

    def test_create_strategy_channel(self):
        """Test creating strategy channel name."""
        self.reporter.info("Testing strategy channel name", context="Test")

        name = ChannelName("strategy.xyz-789")

        assert name.value == "strategy.xyz-789"
        assert name.is_strategy_channel() is True
        self.reporter.info("Strategy channel created", context="Test")

    def test_create_forge_job_channel(self):
        """Test creating forge job channel name."""
        self.reporter.info("Testing forge job channel name", context="Test")

        name = ChannelName("forge.job.abc-123")

        assert name.value == "forge.job.abc-123"
        assert name.is_ephemeral() is True
        self.reporter.info("Forge job channel created", context="Test")

    def test_reject_empty_name(self):
        """Test ChannelName rejects empty string."""
        self.reporter.info("Testing rejection of empty name", context="Test")

        try:
            ChannelName("")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "empty" in str(e).lower()
            self.reporter.info("Empty name correctly rejected", context="Test")

    def test_reject_too_long_name(self):
        """Test ChannelName rejects name longer than 100 chars."""
        self.reporter.info("Testing rejection of too long name", context="Test")

        long_name = "a" * 101
        try:
            ChannelName(long_name)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "too long" in str(e).lower() or "max" in str(e).lower()
            self.reporter.info("Too long name correctly rejected", context="Test")

    def test_accept_max_length_name(self):
        """Test ChannelName accepts 100 character name."""
        self.reporter.info("Testing max length name (100 chars)", context="Test")

        max_name = "a" * 100
        name = ChannelName(max_name)

        assert name.value == max_name
        self.reporter.info("Max length name accepted", context="Test")

    def test_reject_uppercase_letters(self):
        """Test ChannelName rejects uppercase letters."""
        self.reporter.info("Testing rejection of uppercase", context="Test")

        try:
            ChannelName("User.123")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "lowercase" in str(e).lower()
            self.reporter.info("Uppercase correctly rejected", context="Test")

    def test_reject_spaces(self):
        """Test ChannelName rejects spaces."""
        self.reporter.info("Testing rejection of spaces", context="Test")

        try:
            ChannelName("user 123")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            self.reporter.info("Spaces correctly rejected", context="Test")

    def test_reject_special_characters(self):
        """Test ChannelName rejects special characters."""
        self.reporter.info("Testing rejection of special characters", context="Test")

        invalid_names = [
            "user@123",
            "user#123",
            "user$123",
            "user%123",
            "user&123",
            "user*123",
            "user/123",
            "user\\123",
        ]

        for invalid in invalid_names:
            try:
                ChannelName(invalid)
                assert False, f"Should have rejected: {invalid}"
            except ValueError:
                self.reporter.info(
                    f"Special char rejected: {invalid}",
                    context="Test"
                )

    def test_accept_dots_and_hyphens(self):
        """Test ChannelName accepts dots and hyphens."""
        self.reporter.info("Testing acceptance of dots and hyphens", context="Test")

        valid_names = [
            "user.123",
            "strategy.abc-def",
            "forge.job.xyz-123",
            "admin.system.health-check",
        ]

        for valid in valid_names:
            name = ChannelName(valid)
            assert name.value == valid
            self.reporter.info(f"Valid name accepted: {valid}", context="Test")

    # ================================================================
    # Channel type detection tests
    # ================================================================

    def test_is_global_true_for_global(self):
        """Test is_global() returns True for global channel."""
        self.reporter.info("Testing is_global() detection", context="Test")

        name = ChannelName("global")
        assert name.is_global() is True
        self.reporter.info("Global channel detected", context="Test")

    def test_is_global_false_for_non_global(self):
        """Test is_global() returns False for non-global channels."""
        self.reporter.info("Testing is_global() false case", context="Test")

        names = ["user.123", "strategy.abc", "forge.job.xyz"]
        for n in names:
            name = ChannelName(n)
            assert name.is_global() is False

        self.reporter.info("Non-global channels detected", context="Test")

    def test_is_user_channel_detection(self):
        """Test is_user_channel() detection."""
        self.reporter.info("Testing is_user_channel() detection", context="Test")

        user_channel = ChannelName("user.123")
        assert user_channel.is_user_channel() is True

        non_user = ChannelName("strategy.abc")
        assert non_user.is_user_channel() is False

        self.reporter.info("User channel detection correct", context="Test")

    def test_is_strategy_channel_detection(self):
        """Test is_strategy_channel() detection."""
        self.reporter.info("Testing is_strategy_channel() detection", context="Test")

        strategy_channel = ChannelName("strategy.xyz")
        assert strategy_channel.is_strategy_channel() is True

        non_strategy = ChannelName("user.123")
        assert non_strategy.is_strategy_channel() is False

        self.reporter.info("Strategy channel detection correct", context="Test")

    def test_is_ephemeral_detection(self):
        """Test is_ephemeral() detection."""
        self.reporter.info("Testing is_ephemeral() detection", context="Test")

        forge_channel = ChannelName("forge.job.abc")
        assert forge_channel.is_ephemeral() is True

        backtest_channel = ChannelName("backtest.123")
        assert backtest_channel.is_ephemeral() is True

        non_ephemeral = ChannelName("user.123")
        assert non_ephemeral.is_ephemeral() is False

        self.reporter.info("Ephemeral channel detection correct", context="Test")

    # ================================================================
    # User ID extraction tests
    # ================================================================

    def test_extract_user_id_from_user_channel(self):
        """Test extract_user_id() from user channel."""
        self.reporter.info("Testing extract_user_id()", context="Test")

        name = ChannelName("user.abc123")
        user_id = name.extract_user_id()

        assert user_id == "abc123"
        self.reporter.info(f"User ID extracted: {user_id}", context="Test")

    def test_extract_user_id_from_non_user_channel_raises(self):
        """Test extract_user_id() raises for non-user channel."""
        self.reporter.info(
            "Testing extract_user_id() on non-user channel",
            context="Test"
        )

        name = ChannelName("strategy.abc")

        try:
            name.extract_user_id()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "not a user channel" in str(e).lower()
            self.reporter.info("Exception raised correctly", context="Test")

    # ================================================================
    # Equality & Hashing tests
    # ================================================================

    def test_equality_same_name(self):
        """Test two ChannelNames with same name are equal."""
        self.reporter.info("Testing equality with same name", context="Test")

        name1 = ChannelName("user.123")
        name2 = ChannelName("user.123")

        assert name1 == name2
        self.reporter.info("Equal names are equal", context="Test")

    def test_inequality_different_names(self):
        """Test two ChannelNames with different names are not equal."""
        self.reporter.info("Testing inequality with different names", context="Test")

        name1 = ChannelName("user.123")
        name2 = ChannelName("user.456")

        assert name1 != name2
        self.reporter.info("Different names are not equal", context="Test")

    def test_inequality_with_string(self):
        """Test ChannelName is not equal to string."""
        self.reporter.info("Testing inequality with string", context="Test")

        name = ChannelName("user.123")

        assert name != "user.123"
        assert not (name == "user.123")
        self.reporter.info("ChannelName not equal to string", context="Test")

    def test_hashable(self):
        """Test ChannelName can be used in sets and dicts."""
        self.reporter.info("Testing hashability", context="Test")

        name1 = ChannelName("user.123")
        name2 = ChannelName("user.456")
        name3 = ChannelName("user.123")

        # Test in set
        name_set = {name1, name2, name3}
        assert len(name_set) == 2
        self.reporter.info("ChannelName works in set", context="Test")

        # Test as dict key
        name_dict = {name1: "value1", name2: "value2"}
        assert name_dict[name3] == "value1"
        self.reporter.info("ChannelName works as dict key", context="Test")

    # ================================================================
    # String representation tests
    # ================================================================

    def test_str_returns_name_value(self):
        """Test str() returns the name value."""
        self.reporter.info("Testing str() representation", context="Test")

        name = ChannelName("user.123")
        assert str(name) == "user.123"
        self.reporter.info("str() representation correct", context="Test")

    def test_repr_includes_name(self):
        """Test repr() includes name value."""
        self.reporter.info("Testing repr() representation", context="Test")

        name = ChannelName("user.123")
        repr_str = repr(name)

        assert "ChannelName" in repr_str
        assert "user.123" in repr_str
        self.reporter.info(f"repr: {repr_str}", context="Test")

    # ================================================================
    # Immutability tests
    # ================================================================

    def test_cannot_modify_name(self):
        """Test name attribute cannot be modified after creation."""
        self.reporter.info("Testing immutability", context="Test")

        name = ChannelName("user.123")

        try:
            name.name = "user.456"
            assert False, "Should have raised FrozenInstanceError"
        except (AttributeError, Exception):
            self.reporter.info("ChannelName is immutable", context="Test")


if __name__ == "__main__":
    TestChannelName.run_as_main()

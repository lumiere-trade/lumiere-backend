"""
Example test file demonstrating LaborantTest usage.

This is a reference implementation showing:
- How to inherit from LaborantTest
- Setup and teardown hooks
- Test function structure
- Standard assertions

Usage:
    python laborant/examples/test_example.py
"""

from shared.tests import LaborantTest


class TestExample(LaborantTest):
    """
    Example test suite demonstrating LaborantTest features.

    This shows the minimal structure required for Laborant tests.
    """

    # Required: Set component name and category
    component_name = "laborant"
    test_category = "unit"

    def setup(self):
        """
        Optional: Setup before all tests.

        Called ONCE before any test_* methods execute.
        Use for expensive initialization (database, services, etc.)
        """
        # Example: Initialize test data
        self.test_data = {
            "numbers": [1, 2, 3, 4, 5],
            "strings": ["hello", "world"],
            "config": {"debug": True, "timeout": 30},
        }

    def teardown(self):
        """
        Optional: Cleanup after all tests.

        Called ONCE after all test_* methods complete.
        Use for resource cleanup.
        """
        # Example: Clean up test data
        self.test_data = None

    def setup_test(self):
        """
        Optional: Setup before each test.

        Called BEFORE every test_* method.
        Use for per-test initialization.
        """
        # Example: Reset counter for each test
        self.counter = 0

    def teardown_test(self):
        """
        Optional: Cleanup after each test.

        Called AFTER every test_* method.
        Use for per-test cleanup.
        """
        # Example: Nothing to cleanup in this case

    # ================================================================
    # TEST FUNCTIONS (must start with test_)
    # ================================================================

    def test_addition(self):
        """Test basic addition."""
        result = 2 + 2
        assert result == 4, "2 + 2 should equal 4"

    def test_subtraction(self):
        """Test basic subtraction."""
        result = 5 - 3
        assert result == 2, "5 - 3 should equal 2"

    def test_multiplication(self):
        """Test basic multiplication."""
        result = 3 * 4
        assert result == 12, "3 * 4 should equal 12"

    def test_division(self):
        """Test basic division."""
        result = 10 / 2
        assert result == 5.0, "10 / 2 should equal 5.0"

    def test_list_operations(self):
        """Test list operations using setup data."""
        numbers = self.test_data["numbers"]

        assert len(numbers) == 5, "Should have 5 numbers"
        assert sum(numbers) == 15, "Sum should be 15"
        assert max(numbers) == 5, "Max should be 5"
        assert min(numbers) == 1, "Min should be 1"

    def test_string_operations(self):
        """Test string operations using setup data."""
        strings = self.test_data["strings"]

        assert len(strings) == 2, "Should have 2 strings"
        assert "hello" in strings, "Should contain 'hello'"
        assert " ".join(strings) == "hello world", "Join should work"

    def test_dictionary_access(self):
        """Test dictionary access using setup data."""
        config = self.test_data["config"]

        assert "debug" in config, "Should have debug key"
        assert config["debug"] is True, "Debug should be True"
        assert config["timeout"] == 30, "Timeout should be 30"

    def test_exception_handling(self):
        """Test exception handling."""
        try:
            10 / 0
            assert False, "Should have raised ZeroDivisionError"
        except ZeroDivisionError:
            # Expected - test passes
            pass

    def test_with_counter(self):
        """Test using per-test setup (counter)."""
        # Counter was initialized to 0 in setup_test()
        assert self.counter == 0, "Counter should start at 0"

        self.counter += 1
        assert self.counter == 1, "Counter should be 1 after increment"

    def test_assertions_with_messages(self):
        """Test assertions with custom messages."""
        value = 42

        assert value > 0, f"Value {value} should be positive"
        assert value < 100, f"Value {value} should be less than 100"
        assert value == 42, f"Value should be 42, got {value}"

    # ================================================================
    # HELPER FUNCTIONS (don't start with test_ - not executed)
    # ================================================================

    def calculate_sum(self, numbers):
        """Helper function - not executed as test."""
        return sum(numbers)

    def validate_config(self, config):
        """Helper function - not executed as test."""
        required_keys = ["debug", "timeout"]
        return all(key in config for key in required_keys)

    def test_using_helpers(self):
        """Test that uses helper functions."""
        numbers = [1, 2, 3, 4, 5]
        total = self.calculate_sum(numbers)
        assert total == 15, "Sum should be 15"

        config = {"debug": True, "timeout": 30}
        is_valid = self.validate_config(config)
        assert is_valid, "Config should be valid"


# ====================================================================
# STANDARD ENTRY POINT (Required for all tests)
# ====================================================================

if __name__ == "__main__":
    TestExample.run_as_main()

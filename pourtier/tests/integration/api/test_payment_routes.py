"""
DEPRECATED: Payment routes tests.

Lumiere uses pure escrow model - no external payment systems.
All subscription billing is handled via escrow deductions.

These tests will be removed in favor of subscription tests.
"""

from shared.tests import LaborantTest


class TestPaymentRoutes(LaborantTest):
    """Deprecated payment tests - skip all."""

    component_name = "pourtier"
    test_category = "integration"

    async def test_skip_all_payment_tests(self):
        """Payment tests deprecated - using pure escrow model."""
        self.reporter.info(
            "Payment tests skipped - using escrow-only model", context="Test"
        )
        # All tests pass (skipped)


if __name__ == "__main__":
    TestPaymentRoutes.run_as_main()

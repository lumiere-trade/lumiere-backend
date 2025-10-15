"""
Shared testing utilities for Lumiere components.

Provides standardized test structure:
- LaborantTest: Base class for all tests
- Test result models and validation
- JSON protocol for test orchestration

All tests MUST inherit from LaborantTest.
"""

from shared.tests.models import (
    IndividualTestResult,
    TestFileResult,
    TestStatus,
)
from shared.tests.result_schema import (
    SCHEMA_VERSION,
    format_output,
    parse_test_output,
    validate_test_output,
)
from shared.tests.test_base import LaborantTest

__all__ = [
    "LaborantTest",
    "TestStatus",
    "IndividualTestResult",
    "TestFileResult",
    "SCHEMA_VERSION",
    "validate_test_output",
    "parse_test_output",
    "format_output",
]

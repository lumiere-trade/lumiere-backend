"""
Test result data models.

Shared data structures used by:
- test_base.py (generates results)
- laborant (parses and aggregates results)

These models define the contract between tests and the orchestrator.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Union


class TestStatus(Enum):
    """Test execution status - single source of truth."""

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    SKIP = "skip"


@dataclass
class IndividualTestResult:
    """
    Result from a single test function.

    Represents one test_* function execution.
    """

    name: str
    status: str  # Use TestStatus.value
    duration: float
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class TestFileResult:
    """
    Complete results from one test file execution.

    Contains aggregated stats and individual test results.
    This is the JSON contract between test files and laborant.
    """

    schema_version: str
    test_file: str
    component: str
    category: str  # "unit", "integration", "e2e"
    total: int
    passed: int
    failed: int
    errors: int
    skipped: int
    duration: float
    timestamp: str
    tests: List[Union[IndividualTestResult, dict]]
    metadata: dict

    def __post_init__(self):
        """Convert dict tests to IndividualTestResult objects."""
        # Convert any dict items to IndividualTestResult objects
        converted_tests = []
        for test in self.tests:
            if isinstance(test, dict):
                converted_tests.append(IndividualTestResult(**test))
            else:
                converted_tests.append(test)
        self.tests = converted_tests

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result["tests"] = [t.to_dict() for t in self.tests]
        return result

    @property
    def success(self) -> bool:
        """Check if all tests passed."""
        return self.failed == 0 and self.errors == 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100

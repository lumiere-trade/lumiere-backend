"""
Test executor - runs test files and parses their results.

Executes tests as subprocess and parses JSON output.
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from shared.reporter.system_reporter import SystemReporter
from shared.tests.models import TestFileResult
from shared.tests.result_schema import parse_test_output, validate_test_output


class TestExecutor:
    """
    Executes test files and parses their results.

    Runs tests as subprocess for isolation.
    Parses JSON output using standard protocol.
    """

    def __init__(
        self,
        project_root: Path,
        timeout: int = 120,
        reporter: Optional[SystemReporter] = None,
    ):
        """
        Initialize test executor.

        Args:
            project_root: Root directory of project
            timeout: Test timeout in seconds (default: 60)
            reporter: Optional reporter for logging
        """
        self.project_root = project_root
        self.timeout = timeout
        self.reporter = reporter or SystemReporter(
            name="test_executor", level=20, verbose=1
        )

    def execute_test_file(
        self, test_file: Path, component: str, category: str
    ) -> TestFileResult:
        """
        Execute a single test file.

        Runs test as subprocess and parses JSON output.

        Args:
            test_file: Path to test file
            component: Component name
            category: Test category (unit, integration, e2e)

        Returns:
            TestFileResult with execution details
        """
        relative_path = test_file.relative_to(self.project_root)

        self.reporter.debug(f"Executing: {relative_path}", context="TestExecutor")

        start_time = time.time()

        try:
            # Run test file as subprocess
            result = subprocess.run(
                [sys.executable, str(test_file)],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            duration = time.time() - start_time

            # Parse JSON output
            test_data = parse_test_output(result.stdout)

            if test_data is None:
                # Failed to parse - create error result
                return self._create_error_result(
                    test_file=test_file,
                    component=component,
                    category=category,
                    error="Failed to parse test output",
                    stderr=result.stderr,
                    duration=duration,
                )

            # Validate schema
            is_valid, error_msg = validate_test_output(test_data)

            if not is_valid:
                return self._create_error_result(
                    test_file=test_file,
                    component=component,
                    category=category,
                    error=f"Invalid test output: {error_msg}",
                    stderr=result.stderr,
                    duration=duration,
                )

            # Convert to TestFileResult
            test_result = TestFileResult(**test_data)

            # Log result
            if test_result.success:
                self.reporter.debug(
                    f"{test_result.passed}/{test_result.total} "
                    f"passed ({duration:.2f}s)",
                    context="TestExecutor",
                )
            else:
                self.reporter.debug(
                    f"{test_result.failed + test_result.errors} "
                    f"failed ({duration:.2f}s)",
                    context="TestExecutor",
                )

            return test_result

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.reporter.error(
                f"Test timeout after {self.timeout}s", context="TestExecutor"
            )

            return self._create_error_result(
                test_file=test_file,
                component=component,
                category=category,
                error=f"Test timeout after {self.timeout}s",
                stderr="",
                duration=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            self.reporter.error(f"Execution error: {e}", context="TestExecutor")

            return self._create_error_result(
                test_file=test_file,
                component=component,
                category=category,
                error=f"Execution error: {str(e)}",
                stderr="",
                duration=duration,
            )

    def _create_error_result(
        self,
        test_file: Path,
        component: str,
        category: str,
        error: str,
        stderr: str,
        duration: float,
    ) -> TestFileResult:
        """
        Create error result when test execution fails.

        Args:
            test_file: Path to test file
            component: Component name
            category: Test category
            error: Error message
            stderr: Standard error output
            duration: Execution duration

        Returns:
            TestFileResult representing error state
        """
        from shared.tests.models import IndividualTestResult
        from shared.tests.result_schema import SCHEMA_VERSION

        error_details = error
        if stderr:
            error_details += f"\n\nStderr:\n{stderr[:500]}"

        return TestFileResult(
            schema_version=SCHEMA_VERSION,
            test_file=test_file.name,
            component=component,
            category=category,
            total=1,
            passed=0,
            failed=0,
            errors=1,
            skipped=0,
            duration=duration,
            timestamp=datetime.now().isoformat(),
            tests=[
                IndividualTestResult(
                    name="execution_error",
                    status="error",
                    duration=duration,
                    error=error_details,
                )
            ],
            metadata={
                "error_type": "execution_failure",
                "test_file": str(test_file),
            },
        )

    def can_execute(self, test_file: Path) -> bool:
        """
        Check if test file can be executed.

        Validates file exists and is a Python file.

        Args:
            test_file: Path to test file

        Returns:
            True if file can be executed
        """
        if not test_file.exists():
            self.reporter.error(
                f"Test file does not exist: {test_file}", context="TestExecutor"
            )
            return False

        if test_file.suffix != ".py":
            self.reporter.error(
                f"Test file is not Python: {test_file}", context="TestExecutor"
            )
            return False

        return True

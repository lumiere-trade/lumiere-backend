"""
Base class for all Lumiere component tests.

Provides standardized test structure with:
- Automatic test discovery (test_* methods)
- Lifecycle hooks (setup/teardown)
- **Native async/await support**
- Integrated SystemReporter with logging
- Standard JSON output format
- Integration with Laborant orchestrator

All component tests should inherit from LaborantTest.
Supports both sync and async tests seamlessly.
"""

import asyncio
import inspect
import sys
import time
from abc import ABC
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from shared.reporter.system_reporter import SystemReporter
from shared.tests.models import (
    IndividualTestResult,
    TestFileResult,
    TestStatus,
)
from shared.tests.result_schema import SCHEMA_VERSION, format_output


class LaborantTest(ABC):
    """
    Base class for all component tests with async support.

    Provides standard structure, integrated reporter, and output format.
    Tests inherit from this and define test_* methods (sync or async).

    Required class attributes:
        component_name: str - Name of component being tested
        test_category: str - Category: "unit", "integration", or "e2e"

    Optional class attributes:
        log_dir: str - Custom log directory (default: {component}/tests/logs)

    Lifecycle hooks (all optional):
        setup() / async_setup() - Before all tests
        teardown() / async_teardown() - After all tests
        setup_test() / async_setup_test() - Before each test
        teardown_test() / async_teardown_test() - After each test

    Example (sync test):
        class TestMath(LaborantTest):
            component_name = "calculator"
            test_category = "unit"

            def test_addition(self):
                assert 2 + 2 == 4

    Example (async test):
        class TestAPI(LaborantTest):
            component_name = "api"
            test_category = "integration"

            async def async_setup(self):
                self.client = await create_client()

            async def test_endpoint(self):
                response = await self.client.get("/api/test")
                assert response.status_code == 200

            async def async_teardown(self):
                await self.client.close()

        if __name__ == "__main__":
            TestAPI.run_as_main()
    """

    # Required attributes (must be set by subclass)
    component_name: str = "unknown"
    test_category: str = "unit"

    # Optional attributes (can be overridden by subclass)
    log_dir: Optional[str] = None

    def __init__(self):
        """Initialize test instance with integrated reporter."""
        self.results: List[IndividualTestResult] = []
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

        # Setup log directory (convention over configuration)
        if self.log_dir is None:
            self.log_dir = f"{self.component_name}/tests/logs"

        # Ensure log directory exists
        log_path = Path(self.log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Initialize integrated reporter
        self.reporter = SystemReporter(
            name=self.__class__.__name__,
            log_dir=str(log_path),
            level=20,  # INFO
            verbose=1,
        )

    # ================================================================
    # EVENT LOOP MANAGEMENT
    # ================================================================

    def _get_event_loop(self) -> asyncio.AbstractEventLoop:
        """
        Get or create event loop for async tests.

        Returns:
            Event loop instance (shared across all tests)
        """
        if self._event_loop is None or self._event_loop.is_closed():
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)
        return self._event_loop

    def _close_event_loop(self) -> None:
        """Close event loop if it exists."""
        if self._event_loop and not self._event_loop.is_closed():
            self._event_loop.close()
            self._event_loop = None

    # ================================================================
    # LIFECYCLE HOOKS - SYNC (Override in subclass if needed)
    # ================================================================

    def setup(self) -> None:
        """
        Optional: Sync setup before all tests.

        Called ONCE before any test_* methods.
        Override in subclass if needed.
        """

    def teardown(self) -> None:
        """
        Optional: Sync cleanup after all tests.

        Called ONCE after all test_* methods.
        Override in subclass if needed.
        """

    def setup_test(self) -> None:
        """
        Optional: Sync setup before each test.

        Called BEFORE every test_* method.
        Override in subclass if needed.
        """

    def teardown_test(self) -> None:
        """
        Optional: Sync cleanup after each test.

        Called AFTER every test_* method.
        Override in subclass if needed.
        """

    # ================================================================
    # LIFECYCLE HOOKS - ASYNC (Override in subclass if needed)
    # ================================================================

    async def async_setup(self) -> None:
        """
        Optional: Async setup before all tests.

        Called ONCE before any test_* methods.
        Override in subclass if needed.

        Example:
            async def async_setup(self):
                self.db = await connect_database()
                self.client = await create_client()
        """

    async def async_teardown(self) -> None:
        """
        Optional: Async cleanup after all tests.

        Called ONCE after all test_* methods.
        Override in subclass if needed.

        Example:
            async def async_teardown(self):
                await self.db.close()
                await self.client.close()
        """

    async def async_setup_test(self) -> None:
        """
        Optional: Async setup before each test.

        Called BEFORE every test_* method.
        Override in subclass if needed.
        """

    async def async_teardown_test(self) -> None:
        """
        Optional: Async cleanup after each test.

        Called AFTER every test_* method.
        Override in subclass if needed.
        """

    # ================================================================
    # TEST DISCOVERY (Do not override)
    # ================================================================

    def _discover_tests(self) -> List[tuple]:
        """
        Discover all test_* methods in the class.

        Returns:
            List of (method_name, method_object) tuples
        """
        tests = []
        for name in dir(self):
            if name.startswith("test_"):
                attr = getattr(self, name)
                if callable(attr):
                    tests.append((name, attr))
        return sorted(tests)

    # ================================================================
    # ASYNC DETECTION HELPERS
    # ================================================================

    def _is_async_method(self, method) -> bool:
        """Check if a method is async (coroutine function)."""
        return inspect.iscoroutinefunction(method)

    def _has_async_setup(self) -> bool:
        """
        Check if class has overridden async_setup method.

        Returns True only if subclass has defined its own async_setup,
        not just the default pass implementation from base class.
        """
        # Get the method from current class
        method = getattr(self, "async_setup", None)
        if method is None:
            return False

        # Check if it's async
        if not self._is_async_method(method):
            return False

        # Check if overridden (not from LaborantTest base class)
        return method.__func__ is not LaborantTest.async_setup

    def _has_async_teardown(self) -> bool:
        """
        Check if class has overridden async_teardown method.

        Returns True only if subclass has defined its own async_teardown,
        not just the default pass implementation from base class.
        """
        # Get the method from current class
        method = getattr(self, "async_teardown", None)
        if method is None:
            return False

        # Check if it's async
        if not self._is_async_method(method):
            return False

        # Check if overridden (not from LaborantTest base class)
        return method.__func__ is not LaborantTest.async_teardown

    def _has_async_setup_test(self) -> bool:
        """
        Check if class has overridden async_setup_test method.

        Returns True only if subclass has defined its own async_setup_test,
        not just the default pass implementation from base class.
        """
        # Get the method from current class
        method = getattr(self, "async_setup_test", None)
        if method is None:
            return False

        # Check if it's async
        if not self._is_async_method(method):
            return False

        # Check if overridden (not from LaborantTest base class)
        return method.__func__ is not LaborantTest.async_setup_test

    def _has_async_teardown_test(self) -> bool:
        """
        Check if class has overridden async_teardown_test method.

        Returns True only if subclass has defined async_teardown_test,
        not just the default pass implementation from base class.
        """
        # Get the method from current class
        method = getattr(self, "async_teardown_test", None)
        if method is None:
            return False

        # Check if it's async
        if not self._is_async_method(method):
            return False

        # Check if overridden (not from LaborantTest base class)
        return method.__func__ is not LaborantTest.async_teardown_test

    # ================================================================
    # TEST EXECUTION - SYNC (Do not override)
    # ================================================================

    def _execute_sync_test(
        self, test_name: str, test_method: callable
    ) -> IndividualTestResult:
        """
        Execute a single SYNC test method and capture result.

        Args:
            test_name: Name of test method
            test_method: Sync test method to execute

        Returns:
            IndividualTestResult with execution details
        """
        start_time = time.time()

        try:
            # Per-test setup (sync)
            self.setup_test()

            # Execute test
            test_method()

            # Per-test teardown (sync)
            self.teardown_test()

            return IndividualTestResult(
                name=test_name,
                status=TestStatus.PASS.value,
                duration=time.time() - start_time,
            )

        except AssertionError as e:
            return IndividualTestResult(
                name=test_name,
                status=TestStatus.FAIL.value,
                duration=time.time() - start_time,
                error=str(e) or "Assertion failed",
            )

        except Exception as e:
            return IndividualTestResult(
                name=test_name,
                status=TestStatus.ERROR.value,
                duration=time.time() - start_time,
                error=f"{type(e).__name__}: {str(e)}",
            )

    # ================================================================
    # TEST EXECUTION - ASYNC (Do not override)
    # ================================================================

    async def _execute_async_test(
        self, test_name: str, test_method: callable
    ) -> IndividualTestResult:
        """
        Execute a single ASYNC test method and capture result.

        Args:
            test_name: Name of test method
            test_method: Async test method to execute

        Returns:
            IndividualTestResult with execution details
        """
        start_time = time.time()

        try:
            # Per-test setup (async if available, else sync)
            if self._has_async_setup_test():
                await self.async_setup_test()
            else:
                self.setup_test()

            # Execute async test
            await test_method()

            # Per-test teardown (async if available, else sync)
            if self._has_async_teardown_test():
                await self.async_teardown_test()
            else:
                self.teardown_test()

            return IndividualTestResult(
                name=test_name,
                status=TestStatus.PASS.value,
                duration=time.time() - start_time,
            )

        except AssertionError as e:
            return IndividualTestResult(
                name=test_name,
                status=TestStatus.FAIL.value,
                duration=time.time() - start_time,
                error=str(e) or "Assertion failed",
            )

        except Exception as e:
            return IndividualTestResult(
                name=test_name,
                status=TestStatus.ERROR.value,
                duration=time.time() - start_time,
                error=f"{type(e).__name__}: {str(e)}",
            )

    # ================================================================
    # UNIFIED TEST EXECUTION (Do not override)
    # ================================================================

    def _execute_test(
        self, test_name: str, test_method: callable
    ) -> IndividualTestResult:
        """
        Execute a test method (auto-detect sync/async).

        Args:
            test_name: Name of test method
            test_method: Test method to execute (sync or async)

        Returns:
            IndividualTestResult with execution details
        """
        if self._is_async_method(test_method):
            # Run async test using shared event loop
            loop = self._get_event_loop()
            return loop.run_until_complete(
                self._execute_async_test(test_name, test_method)
            )
        else:
            # Run sync test normally
            return self._execute_sync_test(test_name, test_method)

    # ================================================================
    # TEST SUITE EXECUTION (Do not override)
    # ================================================================

    def run_tests(self) -> TestFileResult:
        """
        Run all discovered tests and return structured result.

        Handles both sync and async tests seamlessly.

        Returns:
            TestFileResult with complete execution details
        """
        self.results = []

        # Execute class-level setup (sync or async)
        try:
            if self._has_async_setup():
                loop = self._get_event_loop()
                loop.run_until_complete(self.async_setup())
            else:
                self.setup()
        except Exception as e:
            # Setup failed - return error result
            self._close_event_loop()
            return TestFileResult(
                schema_version=SCHEMA_VERSION,
                test_file=self.__class__.__name__,
                component=self.component_name,
                category=self.test_category,
                total=0,
                passed=0,
                failed=0,
                errors=1,
                skipped=0,
                duration=0.0,
                timestamp=datetime.now().isoformat(),
                tests=[
                    IndividualTestResult(
                        name="setup",
                        status=TestStatus.ERROR.value,
                        duration=0.0,
                        error=f"Setup failed: {str(e)}",
                    )
                ],
                metadata={
                    "python_version": sys.version.split()[0],
                    "test_class": self.__class__.__name__,
                },
            )

        # Discover and run tests
        test_methods = self._discover_tests()

        for test_name, test_method in test_methods:
            result = self._execute_test(test_name, test_method)
            self.results.append(result)

        # Execute class-level teardown (sync or async)
        try:
            if self._has_async_teardown():
                loop = self._get_event_loop()
                loop.run_until_complete(self.async_teardown())
            else:
                self.teardown()
        except Exception as e:
            # Log teardown error but don't fail tests
            self.reporter.error(f"Teardown failed: {e}", context="Teardown")
        finally:
            # Always close event loop at the end
            self._close_event_loop()

        # Build result object
        return TestFileResult(
            schema_version=SCHEMA_VERSION,
            test_file=self.__class__.__name__,
            component=self.component_name,
            category=self.test_category,
            total=len(self.results),
            passed=sum(1 for r in self.results if r.status == TestStatus.PASS.value),
            failed=sum(1 for r in self.results if r.status == TestStatus.FAIL.value),
            errors=sum(1 for r in self.results if r.status == TestStatus.ERROR.value),
            skipped=0,
            duration=sum(r.duration for r in self.results),
            timestamp=datetime.now().isoformat(),
            tests=self.results,
            metadata={
                "python_version": sys.version.split()[0],
                "test_class": self.__class__.__name__,
            },
        )

    # ================================================================
    # STANDARD ENTRY POINT (Do not override)
    # ================================================================

    @classmethod
    def run_as_main(cls):
        """
        Standard entry point for test execution.

        Call this in if __name__ == "__main__" block.

        Outputs results in standard format for laborant parsing.
        Works seamlessly with both sync and async tests.
        """
        instance = cls()
        result = instance.run_tests()

        # Output as JSON with markers
        print(format_output(result.to_dict()))

        # Exit with appropriate code
        has_failures = result.failed + result.errors
        sys.exit(0 if has_failures == 0 else 1)

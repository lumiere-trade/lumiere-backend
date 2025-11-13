"""
Laborant reporter - creates Rich renderable objects for test results.

Responsible for:
- Creating Rich visual components (Panels, Tables, Text)
- Formatting test data into displayable objects
- NOT responsible for printing/rendering

The orchestrator handles actual rendering via Rich Console.

"""

from typing import Dict, List

from rich.panel import Panel
from rich.text import Text


class LaborantReporter:
    """
    Creates Rich renderable objects for test results.

    Returns Rich objects (Panel, Table, Text) that can be rendered
    by a Rich Console. Does not handle printing itself.
    """

    def __init__(self):
        """Initialize reporter."""

    def create_component_header(
        self, component_name: str, test_discovery: Dict[str, int]
    ) -> Panel:
        """
        Create Rich Panel for component header with test discovery info.

        Args:
            component_name: Name of component
            test_discovery: Dict mapping category to file count
                           e.g. {"unit": 9, "integration": 11, "e2e": 2}

        Returns:
            Rich Panel object with test discovery summary
        """
        # Create content text
        content = Text()

        # Category emoji map
        emoji_map = {"unit": "", "integration": "", "e2e": ""}

        content.append("\n")

        # Check if component has no tests
        if not test_discovery:
            content.append("   No tests found!\n", style="yellow")
            content.append(f"   Expected: {component_name}/tests/\n")
        else:
            content.append("  Test Discovery:\n", style="bold")
            content.append("\n")

            # Show discovered tests by category
            category_order = ["unit", "integration", "e2e"]
            total_files = 0

            for category in category_order:
                if category not in test_discovery:
                    continue

                count = test_discovery[category]
                total_files += count
                emoji = emoji_map.get(category, "")
                cat_name = category.capitalize()

                # Format: "   Unit:         9 test files"
                content.append(f"  {emoji} {cat_name}:".ljust(18))
                file_word = "file" if count == 1 else "files"
                content.append(f"{count} test {file_word}\n")

            # Total line
            content.append("\n")
            content.append("  ")
            content.append("─" * 59)
            content.append("\n")
            file_word = "file" if total_files == 1 else "files"
            content.append(
                f"  Total: {total_files} test {file_word} will be executed\n"
            )

        # Capitalize component name
        title_name = component_name.capitalize()

        # Create panel with white border
        return Panel(
            content,
            title=f"[bold] {title_name}[/bold]",
            border_style="white",
            padding=(0, 1),
            width=67,
        )

    def create_category_header_panel(
        self, category: str, file_count: int, component: str
    ) -> Panel:
        """
        Create Rich Panel for category header.

        Args:
            category: Test category (unit, integration, e2e)
            file_count: Number of test files in category
            component: Component name

        Returns:
            Rich Panel object
        """
        emoji_map = {"unit": "", "integration": "", "e2e": ""}

        emoji = emoji_map.get(category, "")
        category_title = category.capitalize()

        # Create content
        content = Text()
        content.append("\n")
        file_word = "file" if file_count == 1 else "files"
        content.append(
            f"  Running {file_count} test {file_word} from "
            f"{component}/tests/{category}/\n"
        )

        return Panel(
            content,
            title=f"[bold]{emoji} {category_title} Tests[/bold]",
            border_style="white",
            padding=(0, 1),
            width=67,
        )

    def _format_test_name(self, test_file_path: str) -> str:
        """
        Convert test filename to human-readable format.

        Args:
            test_file_path: Test filename (e.g. test_solana_pay_adapter.py)

        Returns:
            Human-readable name (e.g. Test Solana Pay Adapter)
        """
        # Remove .py extension
        name = test_file_path.replace(".py", "")

        # Remove test_ prefix if present
        if name.startswith("test_"):
            name = name[5:]

        # Split by underscores and capitalize each word
        words = name.split("_")
        formatted = " ".join(word.capitalize() for word in words)

        # Add "Test" prefix
        return f"Test {formatted}"

    def create_test_file_panel(
        self,
        test_file_path: str,
        component: str,
        category: str,
        tests: List,
        passed: int,
        total: int,
        duration: float,
    ) -> Panel:
        """
        Create Rich Panel for entire test file with results.

        Args:
            test_file_path: Name of test file (e.g. test_user.py)
            component: Component name (e.g. pourtier)
            category: Category name (e.g. unit)
            tests: List of individual test results
            passed: Number of passed tests
            total: Total number of tests
            duration: Total duration

        Returns:
            Rich Panel object containing all test file info
        """
        # Build full path
        full_path = f"{component}/tests/{category}/{test_file_path}"

        # Create content text
        content = Text()

        # Add full path with icon (4 spaces indent like tests)
        content.append("     ", style="")

        # Handle long paths with wrapping
        max_path_width = 58
        if len(full_path) > max_path_width:
            # Wrap path to multiple lines
            words = full_path.split("/")
            current_line = words[0]

            for word in words[1:]:
                test_line = f"{current_line}/{word}"
                if len(test_line) <= max_path_width:
                    current_line = test_line
                else:
                    # Finish current line
                    content.append(current_line, style="bold")
                    content.append("\n       ")
                    current_line = word

            # Add final line
            content.append(current_line, style="bold")
        else:
            content.append(full_path, style="bold")

        content.append("\n\n")

        # Add individual tests
        for test in tests:
            if test.status == "pass":
                icon = ""
                icon_style = "green"
            elif test.status == "fail":
                icon = ""
                icon_style = "red"
            else:  # error
                icon = ""
                icon_style = "red"

            # Truncate test name if too long
            max_name_len = 43
            display_name = test.name[:max_name_len]

            # Format: "     test_name                    0.000s"
            content.append("    ", style="")
            content.append(icon, style=icon_style)
            content.append(" ", style="")
            # ПРОМЯНА: Оцветяване на test name според статус
            content.append(display_name.ljust(max_name_len), style=icon_style)
            content.append(f"{test.duration:>8.3f}s", style="")
            content.append("\n")

        # Add blank line before summary
        content.append("\n")

        # Add summary line
        if passed == total:
            icon = ""
            icon_style = "green"
            percentage = "100.0%"
        else:
            icon = ""
            icon_style = "red"
            percentage = f"{(passed / total * 100):.1f}%" if total > 0 else "0%"

        summary_text = f"Summary: {passed}/{total} passed ({percentage})"

        content.append("    ", style="")
        content.append(icon, style=icon_style)
        content.append(" ", style="")
        # ПРОМЯНА: Оцветяване на summary text според статус
        content.append(summary_text.ljust(43), style=icon_style)
        content.append(f"{duration:>8.3f}s", style="")

        # Format human-readable test name
        formatted_name = self._format_test_name(test_file_path)

        # Category-specific border colors
        border_colors = {"unit": "blue", "integration": "magenta", "e2e": "green"}
        border_color = border_colors.get(category, "cyan")

        # Create panel with formatted name and category color
        return Panel(
            content,
            title=f"[bold] {formatted_name}[/bold]",
            border_style=border_color,
            padding=(0, 1),
            width=67,
        )

    def create_component_summary(
        self,
        component_name: str,
        category_results: Dict[str, List],
        total_tests: int,
        total_passed: int,
        total_failed: int,
        total_errors: int,
    ) -> Panel:
        """
        Create Rich Panel for component summary with category breakdown.

        Args:
            component_name: Component name
            category_results: Dict mapping category to TestFileResult list
            total_tests: Total tests across all categories
            total_passed: Total passed tests
            total_failed: Total failed tests
            total_errors: Total error tests

        Returns:
            Rich Panel object with matrix breakdown
        """
        # Determine overall status
        total_failed_combined = total_failed + total_errors
        if total_failed_combined == 0:
            status_icon = ""
            status_text = "PASSED"
            status_style = "green"
        else:
            status_icon = ""
            status_text = "FAILED"
            status_style = "red"

        # Create content text
        content = Text()

        # Category emoji map
        emoji_map = {"unit": "", "integration": "", "e2e": ""}

        # Header row
        content.append("\n")
        content.append("             Total    Passed    Failed    Duration\n")
        content.append("  ")
        content.append("─" * 59)
        content.append("\n")

        # Calculate category stats
        category_order = ["unit", "integration", "e2e"]
        category_stats = {}

        for category in category_order:
            if category not in category_results:
                continue

            results = category_results[category]
            cat_total = sum(r.total for r in results)
            cat_passed = sum(r.passed for r in results)
            cat_failed = sum(r.failed + r.errors for r in results)
            cat_duration = sum(r.duration for r in results)

            category_stats[category] = {
                "total": cat_total,
                "passed": cat_passed,
                "failed": cat_failed,
                "duration": cat_duration,
            }

        # Print category rows
        for category in category_order:
            if category not in category_stats:
                continue

            stats = category_stats[category]
            emoji = emoji_map.get(category, "")
            # "Unit ", "Integ", "E2e  "
            cat_name = category.capitalize()[:5].ljust(5)

            # Format: "   Unit      150       145         5      5.23s"
            content.append(f"  {emoji} {cat_name}")
            content.append(f"{stats['total']:>7}")
            content.append(f"{stats['passed']:>10}")
            content.append(f"{stats['failed']:>10}")
            content.append(f"{stats['duration']:>11.2f}s")
            content.append("\n")

        # Separator before total
        content.append("  ")
        content.append("─" * 59)
        content.append("\n")

        # Calculate total duration
        total_duration = sum(stats["duration"] for stats in category_stats.values())

        # Total row
        content.append("   Total")
        content.append(f"{total_tests:>7}")
        content.append(f"{total_passed:>10}")
        content.append(f"{total_failed_combined:>10}")
        content.append(f"{total_duration:>11.2f}s")
        content.append("\n\n")

        # Status line
        content.append("  ")
        content.append(status_icon, style=status_style)
        content.append(" Status: ", style=status_style)
        content.append(status_text, style=f"bold {status_style}")
        content.append("\n")

        # Capitalize first letter of component name
        title_name = component_name.capitalize()

        # Create panel with white border (informational)
        return Panel(
            content,
            title=f"[bold] {title_name} Summary[/bold]",
            border_style="white",
            padding=(0, 1),
            width=67,
        )

    def create_final_summary(
        self,
        total_components: int,
        total_tests: int,
        total_passed: int,
        total_failed: int,
        total_errors: int,
        total_duration: float,
        category_breakdown: Dict[str, Dict[str, int]],
        components_with_failures: List[str],
        components_without_tests: List[str],
    ) -> Panel:
        """
        Create Rich Panel for final summary section.

        Args:
            total_components: Total components tested
            total_tests: Total tests run
            total_passed: Total passed
            total_failed: Total failed
            total_errors: Total errors
            total_duration: Total duration
            category_breakdown: Dict with category stats
            components_with_failures: List of failed components
            components_without_tests: List of components without tests

        Returns:
            Rich Panel object with final summary
        """
        total_failed_combined = total_failed + total_errors

        # Determine status
        if total_failed_combined == 0:
            status_icon = ""
            status_text = "TESTS PASSED - COMMIT ALLOWED"
            status_style = "green"
        else:
            status_icon = ""
            status_text = "TESTS FAILED - COMMIT BLOCKED"
            status_style = "red"

        # Create content
        content = Text()

        # Category emoji map
        emoji_map = {"unit": "", "integration": "", "e2e": ""}

        content.append("\n")
        content.append(f"  Components Tested: {total_components}\n")
        content.append(f"  Total Tests:       {total_tests}\n")
        content.append("\n")

        # Matrix header
        content.append("              Total    Passed    Failed    Pass Rate\n")
        content.append("  ")
        content.append("─" * 59)
        content.append("\n")

        # Category breakdown
        category_order = ["unit", "integration", "e2e"]
        for category in category_order:
            if category not in category_breakdown:
                continue

            stats = category_breakdown[category]
            emoji = emoji_map.get(category, "")
            cat_name = category.capitalize()[:5].ljust(5)

            cat_total = stats["total"]
            cat_passed = stats["passed"]
            cat_failed = stats["failed"]
            pass_rate = (cat_passed / cat_total * 100) if cat_total > 0 else 0

            content.append(f"  {emoji} {cat_name}")
            content.append(f"{cat_total:>7}")
            content.append(f"{cat_passed:>10}")
            content.append(f"{cat_failed:>10}")
            content.append(f"{pass_rate:>13.1f}%")
            content.append("\n")

        # Total row
        content.append("  ")
        content.append("─" * 59)
        content.append("\n")

        pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        content.append("   Total")
        content.append(f"{total_tests:>7}")
        content.append(f"{total_passed:>10}")
        content.append(f"{total_failed_combined:>10}")
        content.append(f"{pass_rate:>13.1f}%")
        content.append("\n\n")

        # Duration
        content.append(f"  Duration: {total_duration:.2f}s\n")
        content.append("\n")

        # Failed components (capitalize names)
        if components_with_failures:
            content.append("   Components with failures:\n")
            for comp in components_with_failures:
                # Capitalize component name
                comp_name = comp.capitalize()
                content.append(f"     • {comp_name}\n")
            content.append("\n")

        # Components without tests (capitalize names, yellow bell)
        if components_without_tests:
            content.append("   Components without tests:\n", style="yellow")
            for comp in components_without_tests:
                # Capitalize component name
                comp_name = comp.capitalize()
                content.append(f"     • {comp_name}\n")
            content.append("\n")

        # Final verdict
        content.append("  ")
        content.append(status_icon, style=status_style)
        content.append(" Status: ", style=status_style)
        content.append(status_text, style=f"bold {status_style}")
        content.append("\n")

        return Panel(
            content,
            title="[bold] FINAL SUMMARY[/bold]",
            border_style="white",
            padding=(0, 1),
            width=67,
        )

    def create_no_tests_warning(self, component_name: str) -> Text:
        """
        Create Rich Text for component without tests warning.

        Args:
            component_name: Component name

        Returns:
            Rich Text object
        """
        text = Text()
        text.append("   This component has no tests - " "programmer's responsibility")

        return text

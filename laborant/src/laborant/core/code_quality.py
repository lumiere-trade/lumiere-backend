"""
Code quality checker for Laborant.

Runs black, isort, autoflake, autopep8, and flake8 on components.
Excludes build artifacts, node_modules, venv, etc.
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from shared.reporter.system_reporter import SystemReporter


class CodeQualityChecker:
    """Runs code quality checks (black, isort, flake8) on components."""

    # Directories to exclude from checks
    EXCLUDE_DIRS = {
        "__pycache__",
        "node_modules",
        "venv",
        "venv311",
        ".git",
        ".pytest_cache",
        "build",
        "dist",
        "*.egg-info",
        ".eggs",
        "target",
        "deps",
        "incremental",
        "logs",
        "docs",
    }

    # File patterns to exclude
    EXCLUDE_FILES = {
        "*.pyc",
        "*.pyo",
        "*.so",
        "*.dylib",
    }

    def __init__(self, project_root: Path, reporter: SystemReporter):
        """
        Initialize code quality checker.

        Args:
            project_root: Project root directory
            reporter: SystemReporter instance
        """
        self.project_root = project_root
        self.reporter = reporter

    def _get_python_files(self, component: Optional[str] = None) -> List[Path]:
        """
        Get all Python files for checking.

        Args:
            component: Component name (None = all components)

        Returns:
            List of Python file paths
        """
        if component:
            # Single component
            component_dir = self.project_root / component
            if not component_dir.exists():
                return []
            search_dirs = [component_dir]
        else:
            # All components (exclude common build dirs)
            search_dirs = [
                d
                for d in self.project_root.iterdir()
                if d.is_dir() and d.name not in self.EXCLUDE_DIRS
            ]

        python_files = []

        for search_dir in search_dirs:
            for py_file in search_dir.rglob("*.py"):
                # Check if in excluded directory
                if any(excl in py_file.parts for excl in self.EXCLUDE_DIRS):
                    continue

                python_files.append(py_file)

        return sorted(python_files)

    def run_black(self, component: Optional[str] = None) -> Tuple[bool, str]:
        """
        Run black formatter (always fixes).

        Args:
            component: Component name (None = all)

        Returns:
            (success, output)
        """
        files = self._get_python_files(component)

        if not files:
            return True, "No Python files found"

        # Build command - always format
        cmd = [
            "black",
            "--line-length=88",
        ]
        cmd.extend([str(f) for f in files])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=str(self.project_root)
            )

            return True, result.stdout + result.stderr

        except FileNotFoundError:
            return False, "black not found. Install: pip install black"
        except Exception as e:
            return False, f"Error running black: {e}"

    def run_isort(self, component: Optional[str] = None) -> Tuple[bool, str]:
        """
        Run isort import sorter (always fixes).

        Args:
            component: Component name (None = all)

        Returns:
            (success, output)
        """
        files = self._get_python_files(component)

        if not files:
            return True, "No Python files found"

        # Build command - always sort
        cmd = [
            "isort",
            "--profile=black",
            "--line-length=88",
        ]
        cmd.extend([str(f) for f in files])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=str(self.project_root)
            )

            return True, result.stdout + result.stderr

        except FileNotFoundError:
            return False, "isort not found. Install: pip install isort"
        except Exception as e:
            return False, f"Error running isort: {e}"

    def run_autoflake(self, component: Optional[str] = None) -> Tuple[bool, str]:
        """
        Run autoflake to remove unused imports and variables.

        Args:
            component: Component name (None = all)

        Returns:
            (success, output)
        """
        files = self._get_python_files(component)

        if not files:
            return True, "No Python files found"

        # Build command
        cmd = [
            "autoflake",
            "--in-place",  # Fix files
            "--remove-unused-variables",
            "--remove-all-unused-imports",
            "--remove-duplicate-keys",
        ]
        cmd.extend([str(f) for f in files])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=str(self.project_root)
            )

            return True, result.stdout + result.stderr

        except FileNotFoundError:
            return (False, "autoflake not found. Install: pip install autoflake")
        except Exception as e:
            return False, f"Error running autoflake: {e}"

    def run_autopep8(self, component: Optional[str] = None) -> Tuple[bool, str]:
        """
        Run autopep8 to fix PEP8 issues.

        Args:
            component: Component name (None = all)

        Returns:
            (success, output)
        """
        files = self._get_python_files(component)

        if not files:
            return True, "No Python files found"

        # Build command
        cmd = [
            "autopep8",
            "--in-place",  # Fix files
            "--aggressive",
            "--aggressive",
            "--max-line-length=88",
        ]
        cmd.extend([str(f) for f in files])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=str(self.project_root)
            )

            return True, result.stdout + result.stderr

        except FileNotFoundError:
            return (False, "autopep8 not found. Install: pip install autopep8")
        except Exception as e:
            return False, f"Error running autopep8: {e}"

    def run_flake8(self, component: Optional[str] = None) -> Tuple[bool, str]:
        """
        Run flake8 linter check (read-only).

        Args:
            component: Component name (None = all)

        Returns:
            (success, output)
        """
        files = self._get_python_files(component)

        if not files:
            return True, "No Python files found"

        # Build command
        cmd = [
            "flake8",
            "--max-line-length=88",
            "--extend-ignore=E203,W503",  # Black compatibility
        ]
        cmd.extend([str(f) for f in files])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=str(self.project_root)
            )

            return result.returncode == 0, result.stdout + result.stderr

        except FileNotFoundError:
            return False, "flake8 not found. Install: pip install flake8"
        except Exception as e:
            return False, f"Error running flake8: {e}"

    def _wrap_path(self, path: str, max_width: int = 55) -> List[str]:
        """
        Wrap long file path by breaking after slashes.

        Args:
            path: File path to wrap
            max_width: Maximum width per line

        Returns:
            List of wrapped lines
        """
        if len(path) <= max_width:
            return [path]

        # Split by /
        parts = path.split("/")
        lines = []
        current_line = ""

        for i, part in enumerate(parts):
            # Add slash except for first part
            prefix = "" if i == 0 else "/"
            candidate = current_line + prefix + part

            if len(candidate) <= max_width:
                current_line = candidate
            else:
                # Current line is full, start new line
                if current_line:
                    lines.append(current_line)
                current_line = part

        # Add remaining
        if current_line:
            lines.append(current_line)

        return lines if lines else [path]

    def lint_component(self, component: str) -> dict:
        """
        Lint a component and return results dict (no report).

        Args:
            component: Component name

        Returns:
            Dict with linting results
        """
        self.reporter.info("", context="CodeQuality")
        self.reporter.info(f"Linting {component}", context="CodeQuality")
        self.reporter.info("", context="CodeQuality")

        # Step 1: Initial scan
        self.reporter.info(" Step 1/6: Detecting issues...", context="CodeQuality")

        initial_ok, initial_out = self.run_flake8(component)

        if initial_ok:
            self.reporter.info(" No issues found!", context="CodeQuality")
            return {
                "component": component,
                "initial_count": 0,
                "final_count": 0,
                "fixed_count": 0,
                "final_output": "",
                "final_ok": True,
            }

        initial_lines = initial_out.strip().split("\n") if initial_out else []
        initial_count = len([line for line in initial_lines if line.strip()])

        self.reporter.info(f" Found {initial_count} issue(s)", context="CodeQuality")

        # Step 2: autoflake
        self.reporter.info(" Step 2/6: Removing unused code...", context="CodeQuality")
        self.run_autoflake(component)
        self.reporter.info(" autoflake: Done", context="CodeQuality")

        # Step 3: autopep8
        self.reporter.info(" Step 3/6: Fixing PEP8 issues...", context="CodeQuality")
        self.run_autopep8(component)
        self.reporter.info(" autopep8: Done", context="CodeQuality")

        # Step 4: black
        self.reporter.info(" Step 4/6: Running black...", context="CodeQuality")
        self.run_black(component)
        self.reporter.info(" black: Done", context="CodeQuality")

        # Step 5: isort
        self.reporter.info(" Step 5/6: Running isort...", context="CodeQuality")
        self.run_isort(component)
        self.reporter.info(" isort: Done", context="CodeQuality")

        self.reporter.info("", context="CodeQuality")

        # Step 6: Final check
        self.reporter.info(" Step 6/6: Final verification...", context="CodeQuality")

        final_ok, final_out = self.run_flake8(component)

        final_lines = final_out.strip().split("\n") if final_out else []
        final_count = len([line for line in final_lines if line.strip()])

        fixed_count = initial_count - final_count

        self.reporter.info(
            f" Fixed {fixed_count} issue(s) automatically", context="CodeQuality"
        )

        if final_count > 0:
            self.reporter.warning(
                f" {final_count} issue(s) require manual fixes", context="CodeQuality"
            )

        self.reporter.info("", context="CodeQuality")

        return {
            "component": component,
            "initial_count": initial_count,
            "final_count": final_count,
            "fixed_count": fixed_count,
            "final_output": final_out,
            "final_ok": final_ok,
        }

    def print_multi_component_report(self, results: List[dict]):
        """
        Print multi-component report with individual panels.

        Args:
            results: List of result dicts from lint_component()
        """
        from rich import box
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text

        console = Console()

        # Print individual component panels
        for result in results:
            console.print()

            comp_display = result["component"].capitalize()
            initial_count = result["initial_count"]
            fixed_count = result["fixed_count"]
            final_count = result["final_count"]

            # Calculate success rate
            success_rate = (
                int((fixed_count / initial_count) * 100) if initial_count > 0 else 100
            )

            # Component summary panel
            summary = Text()
            summary.append("\n")
            summary.append(f"  Component:       {comp_display}\n")
            summary.append("\n")
            summary.append(f"  Initial issues:  {initial_count}\n")

            if fixed_count > 0:
                summary.append(f"  Auto-fixed:      {fixed_count}  \n")
            else:
                summary.append("  Auto-fixed:      0\n")

            if final_count > 0:
                summary.append(f"  Remaining:       {final_count}  \n")
            else:
                summary.append("  Remaining:       0  \n")

            summary.append(f"  Success rate:    {success_rate}%\n")

            console.print(
                Panel(
                    summary,
                    title="[bold] Code Quality Report[/bold]",
                    border_style="white",
                    box=box.ROUNDED,
                    padding=(0, 1),
                    width=67,
                )
            )
            console.print()

        # Tools applied panel (one for all)
        tools = Text()
        tools.append("\n")
        tools.append("   autoflake    Removed unused imports/variables\n")
        tools.append("   autopep8     Fixed PEP8 violations\n")
        tools.append("   black        Formatted code style\n")
        tools.append("   isort        Sorted imports\n")

        console.print(
            Panel(
                tools,
                title="[bold] Auto-fix Tools Applied[/bold]",
                border_style="white",
                box=box.ROUNDED,
                padding=(0, 1),
                width=67,
            )
        )
        console.print()

        # Manual fixes for each component (if any)
        for result in results:
            if result["final_count"] == 0:
                continue

            comp_display = result["component"].capitalize()
            final_output = result["final_output"]
            final_count = result["final_count"]

            manual = Text()
            manual.append("\n")
            manual.append(f"  Component: {comp_display}\n")
            manual.append("\n")

            # Parse flake8 output
            for line in final_output.strip().split("\n"):
                if not line.strip():
                    continue

                # Format: /path/file.py:line:col: CODE message
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    filepath = parts[0]
                    line_num = parts[1]
                    col_num = parts[2]
                    issue = parts[3].strip()

                    # Split code and message
                    issue_parts = issue.split(" ", 1)
                    code = issue_parts[0] if issue_parts else ""
                    message = issue_parts[1] if len(issue_parts) > 1 else ""

                    # Wrap long paths
                    wrapped_path = self._wrap_path(filepath)

                    # First line: code and first part of path
                    manual.append(f"  {code}", style="yellow")
                    manual.append(" │ ", style="white")
                    manual.append(f"{wrapped_path[0]}")

                    # Add line:col if path fits on one line
                    if len(wrapped_path) == 1:
                        manual.append(f":{line_num}:{col_num}\n")
                    else:
                        manual.append("\n")

                    # Continue path on next lines if needed
                    for i in range(1, len(wrapped_path)):
                        manual.append("       │ ", style="white")
                        manual.append(wrapped_path[i])

                        # Add line:col on last line
                        if i == len(wrapped_path) - 1:
                            manual.append(f":{line_num}:{col_num}\n")
                        else:
                            manual.append("\n")

                    # Message line
                    manual.append("       │ ", style="white")
                    manual.append(f"{message}\n")
                    manual.append("\n")

            console.print(
                Panel(
                    manual,
                    title=f"[bold] Manual Fixes Required ({final_count})[/bold]",
                    border_style="white",
                    box=box.ROUNDED,
                    padding=(0, 1),
                    width=67,
                )
            )
            console.print()

        # Tip panel
        any_issues = any(r["final_count"] > 0 for r in results)
        if any_issues:
            tip = " Tip: Use black's magic trailing comma to auto-wrap lines"
        else:
            tip = " All checks passed! Code is clean and PEP8 compliant!"

        console.print(
            Panel(tip, border_style="white", box=box.ROUNDED, padding=(0, 1), width=67)
        )
        console.print()

    def _print_report(
        self,
        target: str,
        initial_count: int,
        final_count: int,
        fixed_count: int,
        final_output: str,
    ):
        """
        Print beautiful code quality report with Rich.

        Uses same style as LaborantReporter (width=67, white borders).

        Args:
            target: Component name or "all components"
            initial_count: Initial issue count
            final_count: Final issue count
            fixed_count: Number of fixed issues
            final_output: Final flake8 output
        """
        from rich import box
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text

        console = Console()

        # Capitalize target
        target_display = target.capitalize()

        # Summary panel with component name
        console.print()

        summary = Text()
        summary.append("\n")
        summary.append(f"  Component:       {target_display}\n")
        summary.append("\n")

        # Calculate success rate
        success_rate = (
            int((fixed_count / initial_count) * 100) if initial_count > 0 else 100
        )

        summary.append(f"  Initial issues:  {initial_count}\n")

        if fixed_count > 0:
            summary.append(f"  Auto-fixed:      {fixed_count}  \n")
        else:
            summary.append("  Auto-fixed:      0\n")

        if final_count > 0:
            summary.append(f"  Remaining:       {final_count}  \n")
        else:
            summary.append("  Remaining:       0  \n")

        summary.append(f"  Success rate:    {success_rate}%\n")

        console.print(
            Panel(
                summary,
                title="[bold] Code Quality Report[/bold]",
                border_style="white",
                box=box.ROUNDED,
                padding=(0, 1),
                width=67,
            )
        )
        console.print()

        # Tools applied panel
        tools = Text()
        tools.append("\n")
        tools.append("   autoflake    Removed unused imports/variables\n")
        tools.append("   autopep8     Fixed PEP8 violations\n")
        tools.append("   black        Formatted code style\n")
        tools.append("   isort        Sorted imports\n")

        console.print(
            Panel(
                tools,
                title="[bold] Auto-fix Tools Applied[/bold]",
                border_style="white",
                box=box.ROUNDED,
                padding=(0, 1),
                width=67,
            )
        )
        console.print()

        # Manual fixes required (if any)
        if final_count > 0:
            manual = Text()
            manual.append("\n")

            # Parse flake8 output
            for line in final_output.strip().split("\n"):
                if not line.strip():
                    continue

                # Format: /path/file.py:line:col: CODE message
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    filepath = parts[0]
                    line_num = parts[1]
                    col_num = parts[2]
                    issue = parts[3].strip()

                    # Split code and message
                    issue_parts = issue.split(" ", 1)
                    code = issue_parts[0] if issue_parts else ""
                    message = issue_parts[1] if len(issue_parts) > 1 else ""

                    # Wrap long paths
                    wrapped_path = self._wrap_path(filepath)

                    # First line: code and first part of path
                    manual.append(f"  {code}", style="yellow")
                    manual.append(" │ ", style="white")
                    manual.append(f"{wrapped_path[0]}")

                    # Add line:col if path fits on one line
                    if len(wrapped_path) == 1:
                        manual.append(f":{line_num}:{col_num}\n")
                    else:
                        manual.append("\n")

                    # Continue path on next lines if needed
                    for i in range(1, len(wrapped_path)):
                        manual.append("       │ ", style="white")
                        manual.append(wrapped_path[i])

                        # Add line:col on last line
                        if i == len(wrapped_path) - 1:
                            manual.append(f":{line_num}:{col_num}\n")
                        else:
                            manual.append("\n")

                    # Message line
                    manual.append("       │ ", style="white")
                    manual.append(f"{message}\n")
                    manual.append("\n")

            console.print(
                Panel(
                    manual,
                    title=f"[bold] Manual Fixes Required ({final_count})[/bold]",
                    border_style="white",
                    box=box.ROUNDED,
                    padding=(0, 1),
                    width=67,
                )
            )
            console.print()

        # Tip panel
        if final_count > 0:
            tip = " Tip: Use black's magic trailing comma to auto-wrap lines"
        else:
            tip = " All checks passed! Code is clean and PEP8 compliant!"

        console.print(
            Panel(tip, border_style="white", box=box.ROUNDED, padding=(0, 1), width=67)
        )
        console.print()

    def format(self, component: Optional[str] = None) -> bool:
        """
        Auto-format code with black + isort.

        Args:
            component: Component name (None = all)

        Returns:
            True if formatting succeeded, False otherwise
        """
        target = component or "all components"

        self.reporter.info("", context="CodeQuality")
        self.reporter.info(f"Formatting {target}", context="CodeQuality")
        self.reporter.info("", context="CodeQuality")

        all_passed = True

        # Run black
        self.reporter.info(
            "Running black formatter...",
            context="CodeQuality",
        )
        black_ok, black_out = self.run_black(component)

        if black_ok:
            self.reporter.info("  Black: Done", context="CodeQuality")
        else:
            self.reporter.error(
                "  Black: FAILED",
                context="CodeQuality",
            )
            if black_out:
                self.reporter.error(black_out, context="CodeQuality")
            all_passed = False

        # Run isort
        self.reporter.info(
            "Running isort import sorter...",
            context="CodeQuality",
        )
        isort_ok, isort_out = self.run_isort(component)

        if isort_ok:
            self.reporter.info("  isort: Done", context="CodeQuality")
        else:
            self.reporter.error(
                "  isort: FAILED",
                context="CodeQuality",
            )
            if isort_out:
                self.reporter.error(isort_out, context="CodeQuality")
            all_passed = False

        self.reporter.info("", context="CodeQuality")

        if all_passed:
            self.reporter.info(
                "Formatting complete!",
                context="CodeQuality",
            )
        else:
            self.reporter.error(
                "Formatting failed",
                context="CodeQuality",
            )

        self.reporter.info("", context="CodeQuality")

        return all_passed

    def lint(self, component: Optional[str] = None) -> bool:
        """
        Smart linting with auto-fix and verification.

        Process:
        1. Run flake8 to detect all issues
        2. Auto-fix with autoflake (unused imports/vars)
        3. Auto-fix with autopep8 (PEP8 issues)
        4. Format with black + isort
        5. Run flake8 again
        6. Print beautiful report with Rich

        Args:
            component: Component name (None = all)

        Returns:
            True if no issues remain, False if manual fixes needed
        """
        target = component or "all components"

        self.reporter.info("", context="CodeQuality")
        self.reporter.info(f"Linting {target}", context="CodeQuality")
        self.reporter.info("", context="CodeQuality")

        # Step 1: Initial flake8 scan
        self.reporter.info(" Step 1/6: Detecting issues...", context="CodeQuality")

        initial_ok, initial_out = self.run_flake8(component)

        if initial_ok:
            self.reporter.info(" No issues found!", context="CodeQuality")
            self.reporter.info("", context="CodeQuality")

            # Print success report
            self._print_report(target, 0, 0, 0, "")

            return True

        # Count initial issues
        initial_lines = initial_out.strip().split("\n") if initial_out else []
        initial_count = len([line for line in initial_lines if line.strip()])

        self.reporter.info(f" Found {initial_count} issue(s)", context="CodeQuality")

        # Step 2: Remove unused imports/variables
        self.reporter.info(" Step 2/6: Removing unused code...", context="CodeQuality")

        autoflake_ok, autoflake_out = self.run_autoflake(component)

        if autoflake_ok:
            self.reporter.info(" autoflake: Done", context="CodeQuality")
        else:
            self.reporter.warning(
                " autoflake: {}".format(autoflake_out), context="CodeQuality"
            )

        # Step 3: Fix PEP8 issues
        self.reporter.info(" Step 3/6: Fixing PEP8 issues...", context="CodeQuality")

        autopep8_ok, autopep8_out = self.run_autopep8(component)

        if autopep8_ok:
            self.reporter.info(" autopep8: Done", context="CodeQuality")
        else:
            self.reporter.warning(
                " autopep8: {}".format(autopep8_out), context="CodeQuality"
            )

        # Step 4: Format with black
        self.reporter.info(" Step 4/6: Running black...", context="CodeQuality")

        black_ok, black_out = self.run_black(component)

        if black_ok:
            self.reporter.info(" black: Done", context="CodeQuality")
        else:
            self.reporter.error(" black: {}".format(black_out), context="CodeQuality")

        # Step 5: Sort imports with isort
        self.reporter.info(" Step 5/6: Running isort...", context="CodeQuality")

        isort_ok, isort_out = self.run_isort(component)

        if isort_ok:
            self.reporter.info(" isort: Done", context="CodeQuality")
        else:
            self.reporter.error(" isort: {}".format(isort_out), context="CodeQuality")

        self.reporter.info("", context="CodeQuality")

        # Step 6: Final flake8 check
        self.reporter.info(" Step 6/6: Final verification...", context="CodeQuality")

        final_ok, final_out = self.run_flake8(component)

        # Count remaining issues
        final_lines = final_out.strip().split("\n") if final_out else []
        final_count = len([line for line in final_lines if line.strip()])

        fixed_count = initial_count - final_count

        self.reporter.info(
            f" Fixed {fixed_count} issue(s) automatically", context="CodeQuality"
        )

        if final_count > 0:
            self.reporter.warning(
                f" {final_count} issue(s) require manual fixes", context="CodeQuality"
            )

        self.reporter.info("", context="CodeQuality")

        # Print beautiful report
        self._print_report(target, initial_count, final_count, fixed_count, final_out)

        return final_ok

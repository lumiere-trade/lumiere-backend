"""
Change detector - discovers changed files via git.

Uses git diff to detect staged files and maps them to components.
"""

import subprocess
from pathlib import Path
from typing import List, Optional

from shared.reporter.system_reporter import SystemReporter


class ChangeDetector:
    """
    Detects changed files using git diff.

    Identifies staged files and filters out irrelevant changes.
    """

    def __init__(self, project_root: Path, reporter: Optional[SystemReporter] = None):
        """
        Initialize change detector.

        Args:
            project_root: Root directory of project
            reporter: Optional reporter for logging
        """
        self.project_root = project_root
        self.reporter = reporter or SystemReporter(
            name="change_detector", level=20, verbose=1
        )

    def get_staged_files(self) -> List[Path]:
        """
        Get list of staged files from git.

        Returns:
            List of Path objects for staged files

        Raises:
            RuntimeError: If git command fails
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )

            files = []
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line:
                    file_path = self.project_root / line
                    if file_path.exists():
                        files.append(file_path)

            # Staged files detected (log removed from output)

            return files

        except subprocess.CalledProcessError as e:
            self.reporter.error(f"Git command failed: {e}", context="ChangeDetector")
            raise RuntimeError("Failed to get staged files from git")

        except subprocess.TimeoutExpired:
            self.reporter.error("Git command timeout", context="ChangeDetector")
            raise RuntimeError("Git command timed out")

    def get_modified_files(self) -> List[Path]:
        """
        Get list of modified files (staged + unstaged).

        Returns:
            List of Path objects for modified files
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )

            files = []
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line:
                    file_path = self.project_root / line
                    if file_path.exists():
                        files.append(file_path)

            return files

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            self.reporter.warning(
                "Could not get modified files", context="ChangeDetector"
            )
            return []

    def is_git_repository(self) -> bool:
        """
        Check if project root is a git repository.

        Returns:
            True if git repo, False otherwise
        """
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=str(self.project_root),
                capture_output=True,
                check=True,
                timeout=5,
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def filter_relevant_files(self, files: List[Path]) -> List[Path]:
        """
        Filter out irrelevant files.

        Removes files that don't affect tests:
        - Documentation (.md, .txt)
        - Config files (.yaml, .json, .toml) in root
        - Git files (.gitignore, .gitattributes)
        - IDE files (.vscode, .idea)

        Args:
            files: List of file paths

        Returns:
            Filtered list of relevant files
        """
        relevant = []

        for file_path in files:
            relative = file_path.relative_to(self.project_root)
            parts = relative.parts

            # Skip root-level non-code files
            if len(parts) == 1:
                name = parts[0].lower()
                if any(name.endswith(ext) for ext in [".md", ".txt", ".rst", ".pdf"]):
                    continue
                if name in [
                    ".gitignore",
                    ".gitattributes",
                    "readme.md",
                    "license",
                    "changelog.md",
                ]:
                    continue

            # Skip IDE directories
            if any(
                part in [".vscode", ".idea", ".git", "__pycache__"] for part in parts
            ):
                continue

            # Skip non-code files
            if file_path.suffix in [".md", ".txt", ".rst", ".pdf", ".log"]:
                continue

            relevant.append(file_path)

        if len(relevant) < len(files):
            filtered = len(files) - len(relevant)
            self.reporter.info(
                f"Filtered out {filtered} irrelevant file(s)", context="ChangeDetector"
            )

        return relevant

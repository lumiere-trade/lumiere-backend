#!/usr/bin/env python3
"""
Auto-generate MkDocs API reference for Lumiere Public components.

Scans pourtier/, passeur/, courier/, shared/, laborant/ directories
and creates markdown files with mkdocstrings references.

Usage:
    python generate_docs.py
"""

import sys
from pathlib import Path
from typing import Dict, List

import yaml

# Configuration
PROJECT_ROOT = Path(__file__).parent
SOURCE_DIRS = [
    PROJECT_ROOT / "pourtier",
    PROJECT_ROOT / "passeur",
    PROJECT_ROOT / "courier",
    PROJECT_ROOT / "shared",
    PROJECT_ROOT / "laborant",
]
DOCS_API_DIR = PROJECT_ROOT / "docs" / "api"
MKDOCS_CONFIG = PROJECT_ROOT / "mkdocs.yml"

# Directories to ignore
IGNORE_DIRS = {
    "__pycache__",
    "venv",
    "venv311",
    "node_modules",
    "logs",
    ".git",
    ".pytest_cache",
    "tests",
    "config",
    "keypairs",
    "bridge",  # Node.js code in passeur
}

# Files to ignore
IGNORE_FILES = {
    "__init__.py",
}


def get_module_title(file_stem: str) -> str:
    """Get readable title for module."""
    return file_stem.replace("_", " ").title()


def get_python_files() -> List[Path]:
    """Scan source directories and find all Python files to document."""
    python_files = []

    for source_dir in SOURCE_DIRS:
        if not source_dir.exists():
            print(f"Warning: {source_dir} does not exist, skipping...")
            continue

        for py_file in source_dir.rglob("*.py"):
            if any(ignored in py_file.parts for ignored in IGNORE_DIRS):
                continue
            if py_file.name in IGNORE_FILES:
                continue
            python_files.append(py_file)

    return sorted(python_files)


def get_module_path(py_file: Path) -> str:
    """Convert file path to Python module path."""
    rel_path = py_file.relative_to(PROJECT_ROOT)
    module_parts = list(rel_path.parts[:-1])
    module_parts.append(rel_path.stem)
    return ".".join(module_parts)


def get_doc_path(py_file: Path) -> Path:
    """Get documentation path for Python file."""
    for source_dir in SOURCE_DIRS:
        if source_dir in py_file.parents or source_dir == py_file.parent:
            try:
                rel_path = py_file.relative_to(source_dir)
                doc_path = (
                    DOCS_API_DIR
                    / source_dir.name
                    / rel_path.parent
                    / f"{rel_path.stem}.md"
                )
                return doc_path
            except ValueError:
                continue

    rel_path = py_file.relative_to(PROJECT_ROOT)
    return DOCS_API_DIR / rel_path.parent / f"{rel_path.stem}.md"


def generate_markdown(py_file: Path) -> str:
    """Generate markdown content for Python module."""
    module_path = get_module_path(py_file)
    title = get_module_title(py_file.stem)

    content = f"""# {title}

::: {module_path}
    options:
      show_source: true
      heading_level: 2
      show_root_heading: true
      show_root_full_path: false
      show_object_full_path: false
      members_order: source
      group_by_category: true
      show_category_heading: true
      show_if_no_docstring: false
      show_signature: true
      show_signature_annotations: true
      separate_signature: true
"""
    return content


def create_doc_file(py_file: Path) -> None:
    """Create markdown documentation file for Python module."""
    doc_path = get_doc_path(py_file)
    doc_path.parent.mkdir(parents=True, exist_ok=True)

    content = generate_markdown(py_file)
    doc_path.write_text(content, encoding="utf-8")

    print(f"[CREATED] Created: {doc_path.relative_to(PROJECT_ROOT)}")


def build_navigation_tree() -> Dict:
    """Build navigation tree for mkdocs.yml."""
    python_files = get_python_files()
    nav_tree = {}

    for py_file in python_files:
        source_dir_name = None
        for source_dir in SOURCE_DIRS:
            if source_dir in py_file.parents or source_dir == py_file.parent:
                source_dir_name = source_dir.name
                rel_path = py_file.relative_to(source_dir)
                break

        if not source_dir_name:
            continue

        if source_dir_name not in nav_tree:
            nav_tree[source_dir_name] = {}

        parts = list(rel_path.parts)
        current = nav_tree[source_dir_name]

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        file_stem = parts[-1].replace(".py", "")
        title = get_module_title(file_stem)
        doc_rel_path = get_doc_path(py_file).relative_to(PROJECT_ROOT / "docs")
        current[title] = str(doc_rel_path).replace("\\", "/")

    return nav_tree


def dict_to_nav_list(tree: Dict) -> List:
    """Convert navigation tree to MkDocs nav format."""
    nav = []

    for key, value in sorted(tree.items()):
        if isinstance(value, dict):
            if not value:
                continue

            section_title = key.replace("_", " ").title()
            subsection = dict_to_nav_list(value)

            if subsection:
                nav.append({section_title: subsection})
        else:
            nav.append({key: value})

    return nav


def update_mkdocs_nav() -> None:
    """Update mkdocs.yml navigation with auto-generated API Reference."""
    with open(MKDOCS_CONFIG, "r", encoding="utf-8") as f:
        lines = f.readlines()

    nav_tree = build_navigation_tree()
    api_nav = dict_to_nav_list(nav_tree)

    api_nav_yaml = yaml.dump(
        api_nav, default_flow_style=False, allow_unicode=True, sort_keys=False
    )

    nav_start = None
    api_ref_start = None
    api_ref_end = None
    indent_level = 0

    for i, line in enumerate(lines):
        if line.strip().startswith("nav:"):
            nav_start = i
            continue

        if nav_start is not None:
            stripped = line.lstrip()
            current_indent = len(line) - len(stripped)

            if "- API Reference:" in line or "API Reference:" in stripped:
                api_ref_start = i
                indent_level = current_indent
                continue

            if api_ref_start is not None and api_ref_end is None:
                if line.strip().startswith("- ") and current_indent == indent_level:
                    api_ref_end = i
                    break
                elif (
                    line.strip()
                    and not line.startswith(" ")
                    and not line.startswith("-")
                ):
                    api_ref_end = i
                    break

    if api_ref_start is None:
        for i in range(nav_start + 1, len(lines)):
            if lines[i].strip() and not lines[i].startswith(" "):
                api_ref_end = i
                break
        else:
            api_ref_end = len(lines)

        new_lines = lines[:api_ref_end]
        new_lines.append("  - API Reference:\n")

        for nav_line in api_nav_yaml.strip().split("\n"):
            new_lines.append("      " + nav_line + "\n")

        new_lines.extend(lines[api_ref_end:])
        lines = new_lines

    else:
        if api_ref_end is None:
            api_ref_end = len(lines)

        new_lines = lines[:api_ref_start]
        new_lines.append("  - API Reference:\n")

        for nav_line in api_nav_yaml.strip().split("\n"):
            new_lines.append("      " + nav_line + "\n")

        new_lines.extend(lines[api_ref_end:])
        lines = new_lines

    with open(MKDOCS_CONFIG, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"\n[CREATED] Updated navigation in {MKDOCS_CONFIG.relative_to(PROJECT_ROOT)}")


def clean_old_docs() -> None:
    """Remove old generated documentation files."""
    if DOCS_API_DIR.exists():
        import shutil

        shutil.rmtree(DOCS_API_DIR)
        print(f"[CLEAN] Cleaned old docs in {DOCS_API_DIR.relative_to(PROJECT_ROOT)}")


def main():
    """Main execution function."""
    print("Auto-generating API documentation for Lumiere Public...\n")

    clean_old_docs()

    python_files = get_python_files()
    print(f"Found {len(python_files)} Python modules to document\n")

    for py_file in python_files:
        create_doc_file(py_file)

    print()
    update_mkdocs_nav()

    print(f"\nDone! Generated docs for {len(python_files)} modules")
    print(f"Run 'mkdocs serve' to preview documentation")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

"""Extract TODO comments from codebase and generate report.

This utility scans the codebase for TODO/FIXME/HACK/XXX comments
and generates a report showing where work is needed.

Usage:
    python utils/extract_todos.py
    python utils/extract_todos.py --output todos_report.md
"""
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Patterns to search for
TODO_PATTERNS = [
    (r'#\s*TODO:\s*(.+)', 'TODO'),
    (r'#\s*FIXME:\s*(.+)', 'FIXME'),
    (r'#\s*HACK:\s*(.+)', 'HACK'),
    (r'#\s*XXX:\s*(.+)', 'XXX'),
    (r'#\s*BUG:\s*(.+)', 'BUG'),
    (r'#\s*NOTE:\s*(.+)', 'NOTE'),
]

# Directories to exclude
EXCLUDE_DIRS = {
    '.git', '.venv', '__pycache__', 'node_modules',
    '.pytest_cache', '.mypy_cache', 'dist', 'build',
    'logs', '.eggs'
}

# File extensions to scan
INCLUDE_EXTENSIONS = {'.py', '.pyx', '.pyi'}


def extract_todos(project_root: Path) -> List[Tuple[str, int, str, str]]:
    """Extract all TODO-style comments from Python files.

    Args:
        project_root: Root directory of the project

    Returns:
        List of tuples: (file_path, line_number, tag, message)
    """
    todos = []

    for file_path in project_root.rglob('*.py'):
        # Skip excluded directories
        if any(excluded in file_path.parts for excluded in EXCLUDE_DIRS):
            continue

        # Skip if not in included extensions
        if file_path.suffix not in INCLUDE_EXTENSIONS:
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, start=1):
                    for pattern, tag in TODO_PATTERNS:
                        match = re.search(pattern, line)
                        if match:
                            message = match.group(1).strip()
                            rel_path = file_path.relative_to(project_root)
                            todos.append((str(rel_path), line_num, tag, message))
                            break  # Only match first pattern per line
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)

    return sorted(todos, key=lambda x: (x[2], x[0], x[1]))  # Sort by tag, file, line


def generate_markdown_report(todos: List[Tuple[str, int, str, str]]) -> str:
    """Generate a Markdown report of all TODOs.

    Args:
        todos: List of TODO items

    Returns:
        Markdown formatted string
    """
    if not todos:
        return "# Code TODOs\n\nNo TODO comments found in codebase.\n"

    report = ["# Code TODOs", ""]
    report.append(f"**Total Items:** {len(todos)}")
    report.append("")

    # Group by tag
    by_tag = {}
    for file_path, line_num, tag, message in todos:
        if tag not in by_tag:
            by_tag[tag] = []
        by_tag[tag].append((file_path, line_num, message))

    # Priority order
    priority_order = ['FIXME', 'BUG', 'TODO', 'HACK', 'XXX', 'NOTE']

    for tag in priority_order:
        if tag not in by_tag:
            continue

        items = by_tag[tag]
        report.append(f"## {tag} ({len(items)} items)")
        report.append("")

        for file_path, line_num, message in items:
            # Convert to relative path with forward slashes for consistency
            file_path = file_path.replace('\\', '/')
            report.append(f"- **{file_path}:{line_num}**")
            report.append(f"  - {message}")
            report.append("")

    return "\n".join(report)


def generate_console_report(todos: List[Tuple[str, int, str, str]]) -> str:
    """Generate a console-friendly report.

    Args:
        todos: List of TODO items

    Returns:
        Console formatted string
    """
    if not todos:
        return "No TODO comments found in codebase."

    lines = [f"\nFound {len(todos)} TODO items:\n"]
    lines.append("=" * 80)

    for file_path, line_num, tag, message in todos:
        lines.append(f"\n[{tag}] {file_path}:{line_num}")
        lines.append(f"    {message}")

    lines.append("\n" + "=" * 80)
    return "\n".join(lines)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Extract TODO comments from codebase')
    parser.add_argument('--output', '-o', help='Output file (markdown format)')
    parser.add_argument('--format', '-f', choices=['markdown', 'console'],
                        default='console', help='Output format')
    args = parser.parse_args()

    # Find project root (directory containing this script's parent)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    print(f"Scanning {project_root} for TODO comments...")
    todos = extract_todos(project_root)

    if args.format == 'markdown' or args.output:
        report = generate_markdown_report(todos)
    else:
        report = generate_console_report(todos)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report, encoding='utf-8')
        print(f"Report written to {output_path}")
    else:
        print(report)


if __name__ == '__main__':
    main()

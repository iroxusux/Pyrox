#!/usr/bin/env python3
"""
Script to check if version has been incremented before commit
Usage: python check_version_increment.py

This script:
1. Compares current pyproject.toml version with the last committed version
2. Ensures version has been incremented for commits that change code
3. Allows commits that only change documentation/non-code files
"""
import subprocess
import sys
import re
from pathlib import Path


def get_git_status():
    """Get list of changed files from git."""
    try:
        # Get staged files
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True,
            text=True,
            check=True
        )
        staged_files = result.stdout.strip().split('\n') if result.stdout.strip() else []

        # Get modified files (including unstaged)
        result = subprocess.run(
            ['git', 'diff', '--name-only'],
            capture_output=True,
            text=True,
            check=True
        )
        modified_files = result.stdout.strip().split('\n') if result.stdout.strip() else []

        return staged_files, modified_files

    except subprocess.CalledProcessError as e:
        print(f"Error getting git status: {e}")
        return [], []


def get_current_version():
    """Get version from current pyproject.toml."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            print("Error: Please install tomli: pip install tomli")
            return None

    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found")
        return None

    try:
        with open(pyproject_path, 'rb') as f:
            pyproject = tomllib.load(f)
        return pyproject.get('project', {}).get('version')
    except Exception as e:
        print(f"Error reading current pyproject.toml: {e}")
        return None


def get_committed_version():
    """Get version from last committed pyproject.toml."""
    try:
        result = subprocess.run(
            ['git', 'show', 'HEAD:pyproject.toml'],
            capture_output=True,
            text=True,
            check=True
        )

        # Extract version from TOML content
        version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', result.stdout)
        if version_match:
            return version_match.group(1)
        return None

    except subprocess.CalledProcessError:
        # No previous commit or pyproject.toml doesn't exist in HEAD
        return None
    except Exception as e:
        print(f"Error getting committed version: {e}")
        return None


def is_code_change(files):
    """Check if any of the changed files represent code changes that require version bump."""

    # Files that DON'T require version bump
    docs_patterns = [
        r'README\.md$',
        r'.*\.md$',
        r'docs/.*',
        r'\.gitignore$',
        r'\.gitattributes$',
        r'LICENSE$',
        r'.*\.txt$',
        r'.*\.yml$',
        r'.*\.yaml$',
        r'\.github/.*',
        r'hooks/.*',
        r'utils/sync_.*\.py$',  # Our sync scripts
        r'utils/setup_hooks\.py$',
    ]

    for file in files:
        if not file:  # Skip empty strings
            continue

        is_docs = False
        for pattern in docs_patterns:
            if re.match(pattern, file):
                is_docs = True
                break

        if not is_docs:
            # This is a code change that requires version bump
            return True

    return False


def compare_versions(current_version, committed_version):
    """Compare two version strings to see if current > committed."""
    if not current_version or not committed_version:
        return True  # Allow if we can't compare

    if current_version == committed_version:
        return False  # Same version, not incremented

    # Simple version comparison (works for semantic versioning)
    try:
        current_parts = [int(x) for x in current_version.split('.')]
        committed_parts = [int(x) for x in committed_version.split('.')]

        # Pad shorter version with zeros
        max_len = max(len(current_parts), len(committed_parts))
        current_parts.extend([0] * (max_len - len(current_parts)))
        committed_parts.extend([0] * (max_len - len(committed_parts)))

        return current_parts > committed_parts

    except ValueError:
        # Non-numeric version, just check if they're different
        return current_version != committed_version


def check_version_increment():
    """Main function to check version increment requirement."""

    # Get git status
    staged_files, modified_files = get_git_status()
    all_changed_files = list(set(staged_files + modified_files))

    if not all_changed_files:
        print("ℹ️  No files changed, skipping version check")
        return True

    print(f"📋 Checking version increment for {len(all_changed_files)} changed files...")

    # Check if this is a code change that requires version bump
    if not is_code_change(all_changed_files):
        print("✅ Only documentation/config files changed, no version increment required")
        return True

    # Get versions
    current_version = get_current_version()
    committed_version = get_committed_version()

    if not current_version:
        print("❌ Could not read current version from pyproject.toml")
        return False

    print(f"📊 Current version: {current_version}")

    if not committed_version:
        print("ℹ️  No previous version found (first commit?), allowing...")
        return True

    print(f"📊 Previous version: {committed_version}")

    # Compare versions
    if compare_versions(current_version, committed_version):
        print(f"✅ Version incremented: {committed_version} → {current_version}")
        return True
    else:
        print("❌ Version not incremented!")
        print(f"   Current:  {current_version}")
        print(f"   Previous: {committed_version}")
        print()
        print("💡 Code changes detected but version wasn't incremented.")
        print("   Please update the version in pyproject.toml before committing.")
        print()
        print("   Example version increment:")
        if committed_version:
            parts = committed_version.split('.')
            if len(parts) >= 3:
                parts[2] = str(int(parts[2]) + 1)  # Increment patch version
                suggested = '.'.join(parts)
                print(f"   {committed_version} → {suggested}")
        print()
        return False


if __name__ == "__main__":
    success = check_version_increment()
    sys.exit(0 if success else 1)

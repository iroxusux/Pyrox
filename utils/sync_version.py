#!/usr/bin/env python3
"""
Script to sync version from pyproject.toml to README.md
Usage: python sync_version.py
"""
import re
import sys


def sync_version():
    try:
        import tomllib
    except ImportError:
        # For Python < 3.11
        try:
            import tomli as tomllib
        except ImportError:
            print("Error: Please install tomli: pip install tomli")
            return False

    # Read version from pyproject.toml
    try:
        with open('pyproject.toml', 'rb') as f:
            pyproject = tomllib.load(f)
    except FileNotFoundError:
        print("Error: pyproject.toml not found")
        return False

    version = pyproject['project']['version']
    print(f"Found version {version} in pyproject.toml")

    # Read README.md
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except FileNotFoundError:
        print("Error: README.md not found")
        return False

    # Update version badge
    pattern = r'!\[Version\]\(https://img\.shields\.io/badge/version-[^-]+-blue\.svg\)'
    replacement = f'![Version](https://img.shields.io/badge/version-{version}-blue.svg)'

    if re.search(pattern, readme_content):
        updated_content = re.sub(pattern, replacement, readme_content)

        # Write back to README.md
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"✅ Updated README.md version badge to {version}")
        return True
    else:
        print("⚠️  Version badge pattern not found in README.md")
        return False


if __name__ == "__main__":
    success = sync_version()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Script to sync README.md badges from pyproject.toml metadata
Usage: python sync_readme.py

Syncs the following badges:
- Python Version (from requires-python)
- License (from license file and classifiers)
- Development Status (from classifiers)
- Project Version (from version)
"""
import re
import sys
from pathlib import Path


def extract_license_from_classifiers(classifiers):
    """Extract license name from project classifiers."""
    license_patterns = {
        "License :: OSI Approved :: MIT License": "MIT",
        "License :: OSI Approved :: Apache Software License": "Apache--2.0",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)": "GPL--3.0",
        "License :: OSI Approved :: BSD License": "BSD",
        "License :: OSI Approved :: ISC License (ISCL)": "ISC",
    }

    for classifier in classifiers:
        if classifier in license_patterns:
            return license_patterns[classifier]

    # Fallback: try to extract from any license classifier
    for classifier in classifiers:
        if classifier.startswith("License :: OSI Approved ::"):
            # Try to extract a simple license name (using shields.io format with double hyphens)
            license_part = classifier.replace("License :: OSI Approved ::", "").strip()
            if "MIT" in license_part:
                return "MIT"
            elif "Apache" in license_part:
                return "Apache--2.0"
            elif "GPL" in license_part:
                return "GPL--3.0"
            elif "BSD" in license_part:
                return "BSD"

    return "Unknown"


def extract_status_from_classifiers(classifiers):
    """Extract development status from project classifiers."""
    status_map = {
        "Development Status :: 1 - Planning": "planning",
        "Development Status :: 2 - Pre-Alpha": "pre-alpha",
        "Development Status :: 3 - Alpha": "alpha",
        "Development Status :: 4 - Beta": "beta",
        "Development Status :: 5 - Production/Stable": "stable",
        "Development Status :: 6 - Mature": "mature",
        "Development Status :: 7 - Inactive": "inactive",
    }

    for classifier in classifiers:
        if classifier in status_map:
            return status_map[classifier]

    return "unknown"


def extract_python_version(requires_python):
    """Extract Python version from requires-python field."""
    if not requires_python:
        return "3.13+"

    # Handle common patterns like ">=3.13", ">3.12", "~=3.13.0"
    match = re.search(r'(\d+\.\d+)', requires_python)
    if match:
        version = match.group(1)
        if ">=" in requires_python:
            return f"{version}+"
        elif "~=" in requires_python:
            return f"{version}+"
        else:
            return f"{version}+"

    return requires_python


def sync_readme():
    """Sync README.md badges from pyproject.toml"""
    try:
        import tomllib
    except ImportError:
        # For Python < 3.11
        try:
            import tomli as tomllib
        except ImportError:
            print("Error: Please install tomli: pip install tomli")
            return False

    # Read pyproject.toml
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found")
        return False

    try:
        with open(pyproject_path, 'rb') as f:
            pyproject = tomllib.load(f)
    except Exception as e:
        print(f"Error reading pyproject.toml: {e}")
        return False

    project = pyproject.get('project', {})

    # Extract metadata
    version = project.get('version', 'unknown')
    requires_python = project.get('requires-python', '>=3.13')
    classifiers = project.get('classifiers', [])

    python_version = extract_python_version(requires_python)
    license_name = extract_license_from_classifiers(classifiers)
    dev_status = extract_status_from_classifiers(classifiers)

    print("📋 Syncing README badges from pyproject.toml:")
    print(f"   Version: {version}")
    print(f"   Python: {python_version}")
    print(f"   License: {license_name}")
    print(f"   Status: {dev_status}")

    # Read README.md
    readme_path = Path("README.md")
    if not readme_path.exists():
        print("Error: README.md not found")
        return False

    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except Exception as e:
        print(f"Error reading README.md: {e}")
        return False

    # Define badge update patterns and replacements
    updates = [
        {
            'name': 'Python Version',
            'pattern': r'\[!\[Python Version\]\(https://img\.shields\.io/badge/python-[^-]+-blue\.svg\)\]',
            'replacement': f'[![Python Version](https://img.shields.io/badge/python-{python_version}-blue.svg)]'
        },
        {
            'name': 'License',
            'pattern': r'\[!\[License\]\(https://img\.shields\.io/badge/license-[^)]+-green\.svg\)\]',
            'replacement': f'[![License](https://img.shields.io/badge/license-{license_name}-green.svg)]'
        },
        {
            'name': 'Development Status',
            'pattern': r'!\[Development Status\]\(https://img\.shields\.io/badge/status-[^-]+-orange\.svg\)',
            'replacement': f'![Development Status](https://img.shields.io/badge/status-{dev_status}-orange.svg)'
        },
        {
            'name': 'Version',
            'pattern': r'!\[Version\]\(https://img\.shields\.io/badge/version-[^-]+-blue\.svg\)',
            'replacement': f'![Version](https://img.shields.io/badge/version-{version}-blue.svg)'
        }
    ]

    # Apply updates
    updated_content = readme_content
    changes_made = 0

    for update in updates:
        if re.search(update['pattern'], updated_content):
            updated_content = re.sub(update['pattern'], update['replacement'], updated_content)
            print(f"✅ Updated {update['name']} badge")
            changes_made += 1
        else:
            print(f"⚠️  {update['name']} badge pattern not found")

    # Write back if changes were made
    if changes_made > 0:
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"\n🎉 Successfully updated {changes_made} badges in README.md")
            return True
        except Exception as e:
            print(f"Error writing README.md: {e}")
            return False
    else:
        print("ℹ️  No badge updates needed")
        return True


if __name__ == "__main__":
    success = sync_readme()
    sys.exit(0 if success else 1)

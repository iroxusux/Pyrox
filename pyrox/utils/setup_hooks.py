#!/usr/bin/env python3
"""
Setup script to install Git hooks from the hooks/ directory
Run this after cloning the repository: python setup_hooks.py
"""
import os
import shutil
import stat
from pathlib import Path


def setup_hooks(hook_dir: str = "hooks") -> bool:
    """Copy hooks from hooks/ directory to .git/hooks/ and make them executable"""

    hooks_dir = Path(hook_dir)
    git_hooks_dir = Path(".git/hooks")

    if not hooks_dir.exists():
        print("❌ hooks/ directory not found")
        return False

    if not git_hooks_dir.exists():
        print("❌ .git/hooks/ directory not found. Are you in a Git repository?")
        return False

    installed_hooks = []

    for hook_file in hooks_dir.glob("*"):
        if hook_file.is_file() and not hook_file.name.startswith('.'):
            dest_file = git_hooks_dir / hook_file.name

            # Copy the hook
            shutil.copy2(hook_file, dest_file)

            # Make it executable (important for Unix-like systems)
            if os.name != 'nt':  # Not Windows
                current_permissions = dest_file.stat().st_mode
                dest_file.chmod(current_permissions | stat.S_IEXEC)

            installed_hooks.append(hook_file.name)
            print(f"✅ Installed {hook_file.name} hook")

    if installed_hooks:
        print(f"\n🎉 Successfully installed {len(installed_hooks)} Git hooks:")
        for hook in installed_hooks:
            print(f"   - {hook}")
        print("\nHooks are now active for this repository!")
        return True
    else:
        print("⚠️  No hooks found to install")
        return False


if __name__ == "__main__":
    success = setup_hooks()
    if not success:
        exit(1)

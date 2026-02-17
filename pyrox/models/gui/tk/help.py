"""Help window for Pyrox application.

This module provides a Help window that displays application information,
version details, dependencies, and other helpful information.

Usage:
    As a standalone window:
        >>> from pyrox.models.gui.tk.help import show_help_window
        >>> show_help_window()

    With a parent window:
        >>> from pyrox.models.gui.tk.help import HelpWindow
        >>> help_win = HelpWindow(parent=root)
        >>> help_win.show()

    Integrated with Application Tasks:
        >>> from pyrox.tasks.builtin import HelpTask
        >>> # The HelpTask automatically adds "About Pyrox" to the Help menu
        >>> # and binds F1 key to show the help window
"""
import sys
import platform
import tkinter as tk
from tkinter import ttk
from typing import Optional
import importlib.metadata
from pathlib import Path
import tomli


class HelpWindow:
    """A top-level window displaying help and version information.

    This window shows:
    - Application name and version
    - Python version and platform information
    - All installed dependencies with their versions
    - License information
    - Basic usage information

    The window is modal and contains a scrollable view for dependencies.
    """

    def __init__(self, parent: Optional[tk.Tk] = None):
        """Initialize the Help window.

        Args:
            parent: Parent window (optional). If None, creates standalone window.
        """
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("Pyrox Help")
        self.window.geometry("800x700")
        self.window.resizable(True, True)
        self.window.minsize(700, 800)

        # Try to center the window
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

        self._build_ui()

    def _get_pyrox_version(self) -> str:
        """Get Pyrox version from pyproject.toml or installed package.

        Tries to read from pyproject.toml first (for development),
        then falls back to installed package metadata.

        Returns:
            Version string or \"Development Version\" if not found
        """
        # First try to read from pyproject.toml (for development)
        try:
            # Look for pyproject.toml relative to this file
            current_file = Path(__file__)
            # pyrox/models/gui/tk/help.py -> go up 4 levels to project root
            project_root = current_file.parent.parent.parent.parent.parent
            pyproject_path = project_root / 'pyproject.toml'

            if pyproject_path.exists():
                with open(pyproject_path, 'rb') as f:
                    pyproject_data = tomli.load(f)
                    version = pyproject_data.get('project', {}).get('version')
                    if version:
                        return version
        except Exception:
            pass  # Fall through to next method

        # Fallback to installed package metadata
        try:
            return importlib.metadata.version('pyrox')
        except importlib.metadata.PackageNotFoundError:
            pass

        return "Development Version"

    def _build_ui(self) -> None:
        """Build the user interface."""
        # Create main container with padding
        main_frame = ttk.Frame(self.window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header section
        self._create_header(main_frame)

        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=12)

        # System information section
        self._create_system_info(main_frame)

        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=12)

        # Dependencies section with scrollable view
        self._create_dependencies_section(main_frame)

        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=12)

        # Footer with license and close button
        self._create_footer(main_frame)

    def _create_header(self, parent: ttk.Frame) -> None:
        """Create the header section with app name and version.

        Args:
            parent: Parent frame to contain the header
        """
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 8))

        # Application name
        app_name_label = ttk.Label(
            header_frame,
            text="Pyrox",
            font=('TkDefaultFont', 20, 'bold')
        )
        app_name_label.pack(anchor=tk.W, pady=(2, 4))

        # Version information
        version = self._get_pyrox_version()

        version_label = ttk.Label(
            header_frame,
            text=f"Version: {version}",
            font=('TkDefaultFont', 11)
        )
        version_label.pack(anchor=tk.W, pady=(2, 4))

        # Description
        desc_label = ttk.Label(
            header_frame,
            text="Python-based Industrial Automation Framework",
            font=('TkDefaultFont', 9, 'italic'),
            foreground='gray'
        )
        desc_label.pack(anchor=tk.W, pady=(2, 2))

    def _create_system_info(self, parent: ttk.Frame) -> None:
        """Create the system information section.

        Args:
            parent: Parent frame to contain the system info
        """
        sys_frame = ttk.Frame(parent, padding="12")
        sys_frame.pack(fill=tk.X, pady=(0, 8))

        # Section title
        ttk.Label(
            sys_frame,
            text="System Information",
            font=('TkDefaultFont', 12, 'bold')
        ).pack(anchor=tk.W, pady=(0, 8))

        # Python version
        python_version = sys.version.split('\n')[0]
        ttk.Label(
            sys_frame,
            text=f"Python: {python_version}",
            font=('TkDefaultFont', 9)
        ).pack(anchor=tk.W, padx=2, pady=(2, 4))

        # Platform
        ttk.Label(
            sys_frame,
            text=f"Platform: {platform.platform()}",
            font=('TkDefaultFont', 9)
        ).pack(anchor=tk.W, padx=2, pady=(0, 4))

        # Architecture
        ttk.Label(
            sys_frame,
            text=f"Architecture: {platform.machine()}",
            font=('TkDefaultFont', 9)
        ).pack(anchor=tk.W, padx=2, pady=(0, 2))

    def _create_dependencies_section(self, parent: ttk.Frame) -> None:
        """Create the dependencies section with scrollable list.

        Args:
            parent: Parent frame to contain the dependencies section
        """
        deps_frame = ttk.Frame(parent, padding="12")
        deps_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Section title
        ttk.Label(
            deps_frame,
            text="Installed Dependencies",
            font=('TkDefaultFont', 12, 'bold')
        ).pack(anchor=tk.W, pady=(0, 8))

        # Create treeview with scrollbar
        tree_frame = ttk.Frame(deps_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=('version',),
            show='tree headings',
            yscrollcommand=scrollbar.set,
            height=10
        )
        self.tree.heading('#0', text='Package', anchor=tk.W)
        self.tree.heading('version', text='Version', anchor=tk.W)
        self.tree.column('#0', width=420, minwidth=200, stretch=True)
        self.tree.column('version', width=250, minwidth=120, stretch=True)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=self.tree.yview)

        # Populate dependencies
        self._populate_dependencies()

    def _populate_dependencies(self) -> None:
        """Populate the treeview with installed packages."""
        # Get Pyrox dependencies from metadata
        try:
            dist = importlib.metadata.distribution('pyrox')
            requires = dist.requires or []
            pyrox_deps = {req.split('[')[0].split('>')[0].split('<')[0].split('=')[0].strip().lower()
                          for req in requires}
        except importlib.metadata.PackageNotFoundError:
            # Fallback to hardcoded list if not installed
            pyrox_deps = {
                'lxml', 'openpyxl', 'pandas', 'pillow', 'platformdirs',
                'pyinstaller', 'pylogix', 'pypdf2', 'pdfplumber', 'py7zr',
                'pymupdf', 'pytest', 'python-dotenv', 'pyyaml', 'tk',
                'tomli', 'xmltodict'
            }

        # Get all installed packages
        installed_packages = []
        for dist in importlib.metadata.distributions():
            name = dist.metadata['Name']
            version = dist.metadata['Version']

            # Check if it's a Pyrox dependency
            is_pyrox_dep = name.lower() in pyrox_deps
            installed_packages.append((name, version, is_pyrox_dep))

        # Sort: Pyrox deps first (alphabetically), then others (alphabetically)
        installed_packages.sort(key=lambda x: (not x[2], x[0].lower()))

        # Add to treeview
        for name, version, is_pyrox_dep in installed_packages:
            if is_pyrox_dep:
                # Pyrox dependencies shown in bold
                tag = 'pyrox_dep'
                self.tree.insert('', 'end', text=f"● {name}", values=(version,), tags=(tag,))
            else:
                # Other packages shown normally (for reference)
                self.tree.insert('', 'end', text=f"  {name}", values=(version,))

        # Configure tag for Pyrox dependencies
        self.tree.tag_configure('pyrox_dep', font=('TkDefaultFont', 9, 'bold'))

    def _create_footer(self, parent: ttk.Frame) -> None:
        """Create the footer section with license and buttons.

        Args:
            parent: Parent frame to contain the footer
        """
        footer_frame = ttk.Frame(parent, padding=(0, 5, 0, 0))
        footer_frame.pack(fill=tk.X)

        # License information
        license_frame = ttk.Frame(footer_frame)
        license_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(
            license_frame,
            text="License: GNU General Public License v3 (GPLv3)",
            font=('TkDefaultFont', 8),
            foreground='gray'
        ).pack(anchor=tk.W, padx=2, pady=(2, 3))

        ttk.Label(
            license_frame,
            text="Copyright © 2024-2026 Brian LaFond",
            font=('TkDefaultFont', 8),
            foreground='gray'
        ).pack(anchor=tk.W, padx=2, pady=(0, 2))

        # Close button
        button_frame = ttk.Frame(footer_frame)
        button_frame.pack(side=tk.RIGHT, pady=(5, 0))

        close_btn = ttk.Button(
            button_frame,
            text="Close",
            command=self.close,
            width=12
        )
        close_btn.pack(side=tk.RIGHT, padx=(8, 0), ipady=3)

    def close(self) -> None:
        """Close the help window."""
        self.window.destroy()

    def show(self) -> None:
        """Show the help window and wait for it to close."""
        self.window.transient()
        self.window.grab_set()
        self.window.wait_window()


def show_help_window(parent: Optional[tk.Tk] = None) -> None:
    """Show the help window.

    Args:
        parent: Parent window (optional)
    """
    help_window = HelpWindow(parent)
    help_window.window.mainloop() if parent is None else help_window.show()

"""Help window for Pyrox application.

This module provides a Help window that displays application information,
version details, dependencies, and other helpful information.

Usage:
    As a standalone window:
        >>> from pyrox.models.gui.help import show_help_window
        >>> show_help_window()

    With a parent window:
        >>> from pyrox.models.gui.help import HelpWindow
        >>> help_win = HelpWindow(parent=main_window)
        >>> help_win.show()

    Integrated with Application Tasks:
        >>> from pyrox.tasks.builtin import HelpTask
        >>> # The HelpTask automatically adds "About Pyrox" to the Help menu
        >>> # and binds F1 to show the help window
"""
from __future__ import annotations

import sys
import platform
import importlib.metadata
from pathlib import Path
from typing import Optional

import tomli
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class HelpWindow(QDialog):
    """A dialog window displaying help and version information.

    This window shows:
    - Application name and version
    - Python version and platform information
    - All installed dependencies with their versions
    - License information

    The window is modal and contains a scrollable view for dependencies.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the Help window.

        Args:
            parent: Parent window (optional).
        """
        super().__init__(parent)
        self.setWindowTitle("Pyrox Help")
        self.resize(800, 700)
        self.setMinimumSize(700, 600)

        # Center on screen when shown without a parent
        if parent is None:
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                self.move(
                    (geo.width() - self.width()) // 2,
                    (geo.height() - self.height()) // 2,
                )

        self._build_ui()

    def _get_pyrox_version(self) -> str:
        """Get Pyrox version from pyproject.toml or installed package metadata.

        Tries pyproject.toml first (for development), then falls back to
        installed package metadata.

        Returns:
            Version string, or "Development Version" if not found.
        """
        try:
            # pyrox/models/gui/help.py -> 4 levels up to project root
            project_root = Path(__file__).parent.parent.parent.parent
            pyproject_path = project_root / 'pyproject.toml'
            if pyproject_path.exists():
                with open(pyproject_path, 'rb') as f:
                    data = tomli.load(f)
                version = data.get('project', {}).get('version')
                if version:
                    return version
        except Exception:
            pass

        try:
            return importlib.metadata.version('pyrox')
        except importlib.metadata.PackageNotFoundError:
            pass

        return "Development Version"

    def _build_ui(self) -> None:
        """Build the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(0)

        self._create_header(main_layout)
        main_layout.addWidget(self._make_separator())
        self._create_system_info(main_layout)
        main_layout.addWidget(self._make_separator())
        self._create_dependencies_section(main_layout)
        main_layout.addWidget(self._make_separator())
        self._create_footer(main_layout)

    def _make_separator(self) -> QFrame:
        """Create a horizontal separator line.

        Returns:
            A styled horizontal separator QFrame with vertical margins.
        """
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setContentsMargins(0, 6, 0, 6)
        return sep

    def _create_header(self, layout: QVBoxLayout) -> None:
        """Create the header section with app name, version, and description.

        Args:
            layout: Parent layout to add the header into.
        """
        widget = QWidget()
        inner = QVBoxLayout(widget)
        inner.setContentsMargins(0, 0, 0, 8)
        inner.setSpacing(4)

        name_label = QLabel("Pyrox")
        name_font = QFont()
        name_font.setPointSize(20)
        name_font.setBold(True)
        name_label.setFont(name_font)
        inner.addWidget(name_label)

        version_label = QLabel(f"Version: {self._get_pyrox_version()}")
        version_font = QFont()
        version_font.setPointSize(11)
        version_label.setFont(version_font)
        inner.addWidget(version_label)

        desc_label = QLabel("Python-based Industrial Automation Framework")
        desc_font = QFont()
        desc_font.setPointSize(9)
        desc_font.setItalic(True)
        desc_label.setFont(desc_font)
        desc_label.setStyleSheet("color: gray;")
        inner.addWidget(desc_label)

        layout.addWidget(widget)

    def _create_system_info(self, layout: QVBoxLayout) -> None:
        """Create the system information section.

        Args:
            layout: Parent layout to add the system info into.
        """
        widget = QWidget()
        inner = QVBoxLayout(widget)
        inner.setContentsMargins(0, 0, 0, 8)
        inner.setSpacing(4)

        title_label = QLabel("System Information")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        inner.addWidget(title_label)

        small_font = QFont()
        small_font.setPointSize(9)

        python_version = sys.version.split('\n')[0]
        for text in (
            f"Python: {python_version}",
            f"Platform: {platform.platform()}",
            f"Architecture: {platform.machine()}",
        ):
            lbl = QLabel(text)
            lbl.setFont(small_font)
            inner.addWidget(lbl)

        layout.addWidget(widget)

    def _create_dependencies_section(self, layout: QVBoxLayout) -> None:
        """Create the dependencies section with a scrollable tree view.

        Args:
            layout: Parent layout to add the section into.
        """
        widget = QWidget()
        inner = QVBoxLayout(widget)
        inner.setContentsMargins(0, 0, 0, 8)
        inner.setSpacing(8)

        title_label = QLabel("Installed Dependencies")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        inner.addWidget(title_label)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Package", "Version"])
        header = self.tree.header()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tree.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        inner.addWidget(self.tree)

        self._populate_dependencies()

        layout.addWidget(widget, stretch=1)

    def _populate_dependencies(self) -> None:
        """Populate the tree widget with installed packages.

        Pyrox direct dependencies are listed first in bold with a bullet
        indicator; all other installed packages follow alphabetically.
        """
        try:
            dist = importlib.metadata.distribution('pyrox')
            requires = dist.requires or []
            pyrox_deps = {
                req.split('[')[0].split('>')[0].split('<')[0].split('=')[0].strip().lower()
                for req in requires
            }
        except importlib.metadata.PackageNotFoundError:
            pyrox_deps = {
                'lxml', 'openpyxl', 'pandas', 'pillow', 'platformdirs',
                'pyinstaller', 'pylogix', 'pypdf2', 'pdfplumber', 'py7zr',
                'pymupdf', 'pytest', 'python-dotenv', 'pyyaml', 'tk',
                'tomli', 'xmltodict',
            }

        installed: list[tuple[str, str, bool]] = []
        for dist in importlib.metadata.distributions():
            name = dist.metadata['Name']
            version = dist.metadata['Version']
            installed.append((name, version, name.lower() in pyrox_deps))

        # Pyrox deps first, then rest — both groups sorted alphabetically
        installed.sort(key=lambda x: (not x[2], x[0].lower()))

        bold_font = QFont()
        bold_font.setPointSize(9)
        bold_font.setBold(True)

        normal_font = QFont()
        normal_font.setPointSize(9)

        for name, version, is_pyrox_dep in installed:
            if is_pyrox_dep:
                item = QTreeWidgetItem([f"● {name}", version])
                item.setFont(0, bold_font)
                item.setFont(1, bold_font)
            else:
                item = QTreeWidgetItem([f"  {name}", version])
                item.setFont(0, normal_font)
                item.setFont(1, normal_font)
            self.tree.addTopLevelItem(item)

    def _create_footer(self, layout: QVBoxLayout) -> None:
        """Create the footer section with license info and a close button.

        Args:
            layout: Parent layout to add the footer into.
        """
        widget = QWidget()
        inner = QHBoxLayout(widget)
        inner.setContentsMargins(0, 5, 0, 0)

        # License / copyright block
        license_widget = QWidget()
        license_layout = QVBoxLayout(license_widget)
        license_layout.setContentsMargins(0, 0, 0, 0)
        license_layout.setSpacing(2)

        gray_small = "color: gray; font-size: 8pt;"
        license_label = QLabel("License: GNU General Public License v3 (GPLv3)")
        license_label.setStyleSheet(gray_small)
        license_layout.addWidget(license_label)

        copyright_label = QLabel("Copyright \u00a9 2024\u20132026 Brian LaFond")
        copyright_label.setStyleSheet(gray_small)
        license_layout.addWidget(copyright_label)

        inner.addWidget(license_widget)
        inner.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.close)
        inner.addWidget(
            close_btn,
            alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )

        layout.addWidget(widget)

    def show(self) -> None:
        """Show the help window modally and wait for it to close."""
        self.exec()


def show_help_window(parent: Optional[QWidget] = None) -> None:
    """Show the help window.

    Args:
        parent: Parent window (optional).
    """
    HelpWindow(parent).exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = HelpWindow()
    sys.exit(window.exec())

"""
Context Menu Widget for Pyrox applications.

This module provides a context menu (right-click menu) widget that allows easy
programmatic adding and removal of menu items for user interactions. The context
menu follows the Pyrox GUI patterns and theming system.

Usage:
    Standalone popup::

        >>> from pyrox.models.gui.contextmenu import PyroxContextMenu, MenuItem
        >>> menu = PyroxContextMenu()
        >>> menu.add_item(MenuItem(id="open", label="Open", command=my_fn, icon="📁"))
        >>> menu.show_at(x, y)

    Bound to any QWidget (right-click auto-shows)::

        >>> menu.bind_to_widget(my_widget)

    Integrated with connection editor or other widgets::

        >>> from pyrox.models.gui.contextmenu import create_file_menu
        >>> for item in create_file_menu():
        ...     menu.add_item(item)
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from pyrox.models.gui.theme import DefaultTheme


@dataclass
class MenuItem:
    """Configuration for a single context menu item.

    Attributes:
        id: Unique identifier for the menu item.
        label: Text displayed in the menu item.
        command: Function to call when the item is selected.
        icon: Unicode character (or short string) used as an icon prefix.
        enabled: Whether the item is initially enabled.
        visible: Whether the item is initially visible.
        checkable: Whether the item shows a checkbox.
        checked: Initial checked state (only used when checkable=True).
        submenu: Nested submenu items.
        separator_before: Whether to insert a separator before this item.
        separator_after: Whether to insert a separator after this item.
        accelerator: Keyboard shortcut text shown beside the label (e.g. "Ctrl+X").
    """
    id: str
    label: str
    command: Optional[Callable[[], None]] = None
    icon: Optional[str] = None
    enabled: bool = True
    visible: bool = True
    checkable: bool = False
    checked: bool = False
    submenu: Optional[List[MenuItem]] = None
    separator_before: bool = False
    separator_after: bool = False
    accelerator: Optional[str] = None


@dataclass
class _MenuEntry:
    """Internal tracking of one added item and its optional separator actions."""
    action: QAction
    sep_before: Optional[QAction] = None
    sep_after: Optional[QAction] = None


class PyroxContextMenu(QMenu):
    """
    A context menu for right-click operations.

    The context menu provides a popup menu interface where items can be
    dynamically added, removed, enabled, disabled, and organised. It follows
    the Pyrox dark theme and integrates with the application's event system.

    Features:
    - Dynamic item management (add, remove, update)
    - Nested submenu support
    - Separators and grouping
    - Icon prefix support
    - Checkable menu items
    - Keyboard accelerator display
    - Event callbacks for item selection
    - Pyrox theme integration
    - One-call binding to any QWidget
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialise the PyroxContextMenu.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)

        self._menu_items: Dict[str, MenuItem] = {}
        self._entries: Dict[str, _MenuEntry] = {}
        self._submenus: Dict[str, 'PyroxContextMenu'] = {}

        # Public callbacks
        self.on_item_selected: Optional[Callable[[str, MenuItem], None]] = None
        self.on_item_added: Optional[Callable[[str, MenuItem], None]] = None
        self.on_item_removed: Optional[Callable[[str], None]] = None
        self.on_menu_opened: Optional[Callable[[int, int], None]] = None
        self.on_menu_closed: Optional[Callable[[], None]] = None

        self._apply_styling()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_styling(self) -> None:
        """Apply the Pyrox dark theme via QSS."""
        t = DefaultTheme()
        self.setStyleSheet(f"""
            QMenu {{
                background-color: {t.background};
                color: white;
                border: 1px solid {t.bordercolor};
                font-family: Segoe UI;
                font-size: 9pt;
            }}
            QMenu::item {{
                padding: 4px 24px 4px 8px;
            }}
            QMenu::item:selected {{
                background-color: {t.background_hover};
                color: white;
            }}
            QMenu::item:disabled {{
                color: #666666;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {t.bordercolor};
                margin: 3px 6px;
            }}
            QMenu::indicator {{
                width: 14px;
                height: 14px;
            }}
        """)

    def _format_label(self, item: MenuItem) -> str:
        """Return the display label, prefixed with the icon if present."""
        return f"{item.icon} {item.label}" if item.icon else item.label

    def _handle_item_click(self, item_id: str) -> None:
        """Execute a menu item's command and fire the selection callback."""
        if item_id not in self._menu_items:
            return
        item = self._menu_items[item_id]
        if item.command:
            try:
                item.command()
            except Exception as e:
                print(f"Error executing menu item command '{item_id}': {e}")
                raise
        if self.on_item_selected:
            self.on_item_selected(item_id, item)

    def _make_action(self, item: MenuItem) -> QAction:
        """Create and configure a QAction for a regular or checkable item."""
        action = QAction(self._format_label(item), self)
        action.setEnabled(item.enabled)
        action.setVisible(item.visible)
        if item.checkable:
            action.setCheckable(True)
            action.setChecked(item.checked)
        if item.accelerator:
            action.setShortcut(QKeySequence(item.accelerator))
            action.setShortcutVisibleInContextMenu(True)
        # triggered always passes a bool (checked state); capture and discard it
        action.triggered.connect(lambda _chk=False, iid=item.id: self._handle_item_click(iid))
        return action

    def _add_submenu_item(self, item: MenuItem) -> QAction:
        """Build and attach a nested PyroxContextMenu."""
        submenu = PyroxContextMenu(self)
        submenu.setTitle(self._format_label(item))
        for sub_item in (item.submenu or []):
            submenu.add_item(sub_item)
        self._submenus[item.id] = submenu
        action = self.addMenu(submenu)
        if action:
            action.setEnabled(item.enabled)
            action.setVisible(item.visible)
            return action
        return submenu.menuAction() or QAction(self)  # menuAction() never None in practice

    # ------------------------------------------------------------------
    # Public API — item management
    # ------------------------------------------------------------------

    def add_item(self, item: MenuItem) -> bool:
        """Add a menu item.

        Args:
            item: MenuItem configuration to add.

        Returns:
            True if the item was added; False if the ID already exists.
        """
        if item.id in self._menu_items:
            return False

        self._menu_items[item.id] = item

        sep_before: Optional[QAction] = None
        sep_after: Optional[QAction] = None

        if item.separator_before:
            sep_before = self.addSeparator()

        if item.submenu:
            action = self._add_submenu_item(item)
        else:
            action = self._make_action(item)
            self.addAction(action)

        if item.separator_after:
            sep_after = self.addSeparator()

        self._entries[item.id] = _MenuEntry(
            action=action,
            sep_before=sep_before,
            sep_after=sep_after,
        )

        if self.on_item_added:
            self.on_item_added(item.id, item)

        return True

    def remove_item(self, item_id: str) -> bool:
        """Remove a menu item and any separators associated with it.

        Args:
            item_id: ID of the item to remove.

        Returns:
            True if removed; False if the item was not found.
        """
        if item_id not in self._menu_items:
            return False

        entry = self._entries.pop(item_id, None)
        if entry:
            if entry.sep_before:
                self.removeAction(entry.sep_before)
            self.removeAction(entry.action)
            if entry.sep_after:
                self.removeAction(entry.sep_after)

        del self._menu_items[item_id]
        self._submenus.pop(item_id, None)

        if self.on_item_removed:
            self.on_item_removed(item_id)

        return True

    def update_item(self, item_id: str, **kwargs) -> bool:
        """Update properties of an existing item.

        Args:
            item_id: ID of the item to update.
            **kwargs: Dataclass field names → new values.

        Returns:
            True if the item exists and was updated.
        """
        if item_id not in self._menu_items:
            return False

        item = self._menu_items[item_id]
        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)

        entry = self._entries.get(item_id)
        if entry:
            if 'label' in kwargs or 'icon' in kwargs:
                entry.action.setText(self._format_label(item))
            if 'enabled' in kwargs:
                entry.action.setEnabled(item.enabled)
            if 'visible' in kwargs:
                entry.action.setVisible(item.visible)
            if 'checked' in kwargs and item.checkable:
                entry.action.setChecked(item.checked)

        return True

    def clear_all_items(self) -> None:
        """Remove all menu items."""
        for item_id in list(self._menu_items.keys()):
            self.remove_item(item_id)

    def enable_item(self, item_id: str) -> bool:
        """Enable a menu item.

        Args:
            item_id: ID of the item to enable.

        Returns:
            True if the item was found and enabled.
        """
        if item_id not in self._menu_items:
            return False
        self._menu_items[item_id].enabled = True
        entry = self._entries.get(item_id)
        if entry:
            entry.action.setEnabled(True)
        return True

    def disable_item(self, item_id: str) -> bool:
        """Disable a menu item.

        Args:
            item_id: ID of the item to disable.

        Returns:
            True if the item was found and disabled.
        """
        if item_id not in self._menu_items:
            return False
        self._menu_items[item_id].enabled = False
        entry = self._entries.get(item_id)
        if entry:
            entry.action.setEnabled(False)
        return True

    def check_item(self, item_id: str, checked: bool = True) -> bool:
        """Set the checked state of a checkable item.

        Args:
            item_id: ID of the checkable item.
            checked: Desired checked state.

        Returns:
            True if the item exists and is checkable.
        """
        if item_id not in self._menu_items:
            return False
        item = self._menu_items[item_id]
        if not item.checkable:
            return False
        item.checked = checked
        entry = self._entries.get(item_id)
        if entry:
            entry.action.setChecked(checked)
        return True

    def get_item(self, item_id: str) -> Optional[MenuItem]:
        """Return the MenuItem for a given ID, or None."""
        return self._menu_items.get(item_id)

    def get_all_item_ids(self) -> List[str]:
        """Return all registered item IDs in insertion order."""
        return list(self._menu_items.keys())

    def has_item(self, item_id: str) -> bool:
        """Return True if an item with this ID exists."""
        return item_id in self._menu_items

    # ------------------------------------------------------------------
    # Showing the menu
    # ------------------------------------------------------------------

    def show_at(self, x: int, y: int) -> None:
        """Show the menu at absolute screen coordinates.

        Args:
            x: Screen X coordinate.
            y: Screen Y coordinate.
        """
        if self.on_menu_opened:
            self.on_menu_opened(x, y)
        self.exec(QPoint(x, y))
        if self.on_menu_closed:
            self.on_menu_closed()

    def show_at_event(self, event) -> None:
        """Show at the global position carried by a Qt mouse/context event.

        Args:
            event: Any Qt event exposing .globalPosition() or .globalPos().
        """
        try:
            pos = event.globalPosition().toPoint()
        except AttributeError:
            pos = event.globalPos()
        self.show_at(pos.x(), pos.y())

    def show_at_widget(self, widget: QWidget, event) -> None:
        """Show at a local event position mapped to global screen coordinates.

        Args:
            widget: Widget that received the event.
            event: Qt event with a local .pos().
        """
        global_pos = widget.mapToGlobal(event.pos())
        self.show_at(global_pos.x(), global_pos.y())

    # ------------------------------------------------------------------
    # Widget binding
    # ------------------------------------------------------------------

    def bind_to_widget(self, widget: QWidget) -> None:
        """Bind this context menu to a widget's right-click event.

        Sets the widget's context menu policy to CustomContextMenu and
        connects the customContextMenuRequested signal so this menu
        appears on right-click automatically.

        Args:
            widget: Any QWidget to attach the context menu to.
        """
        widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        widget.customContextMenuRequested.connect(
            lambda pos, w=widget: self.show_at(
                w.mapToGlobal(pos).x(),
                w.mapToGlobal(pos).y(),
            )
        )


# ---------------------------------------------------------------------------
# Convenience factory functions
# ---------------------------------------------------------------------------

def create_standard_text_menu() -> List[MenuItem]:
    """Return a standard text-editing context menu item list."""
    return [
        MenuItem(id="cut",        label="Cut",        accelerator="Ctrl+X", icon="✂"),
        MenuItem(id="copy",       label="Copy",       accelerator="Ctrl+C", icon="📋"),
        MenuItem(id="paste",      label="Paste",      accelerator="Ctrl+V", icon="📄"),
        MenuItem(id="separator1", label="",           separator_before=True),
        MenuItem(id="select_all", label="Select All", accelerator="Ctrl+A", icon="🔘"),
    ]


def create_file_menu() -> List[MenuItem]:
    """Return a standard file-operations context menu item list."""
    return [
        MenuItem(id="open",       label="Open",       icon="📁"),
        MenuItem(id="edit",       label="Edit",       icon="✏"),
        MenuItem(id="separator1", label="",           separator_before=True),
        MenuItem(id="copy",       label="Copy",       icon="📋"),
        MenuItem(id="cut",        label="Cut",        icon="✂"),
        MenuItem(id="delete",     label="Delete",     icon="🗑"),
        MenuItem(id="separator2", label="",           separator_before=True),
        MenuItem(id="properties", label="Properties", icon="⚙"),
    ]


def create_view_menu() -> List[MenuItem]:
    """Return a standard view-operations context menu item list."""
    return [
        MenuItem(id="refresh",     label="Refresh",     accelerator="F5", icon="🔄"),
        MenuItem(id="separator1",  label="",            separator_before=True),
        MenuItem(id="view_large",  label="Large Icons", checkable=True,  icon="🔳"),
        MenuItem(id="view_small",  label="Small Icons", checkable=True,  icon="🔲"),
        MenuItem(id="view_list",   label="List",        checkable=True,  icon="📋"),
        MenuItem(id="view_details", label="Details",    checkable=True, checked=True, icon="📊"),
    ]


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def _create_demo_window(app: QApplication) -> QMainWindow:
    """Build the demo QMainWindow."""
    _DARK = "#2b2b2b"
    _DARKER = "#1e1e1e"

    app.setStyleSheet(f"""
        QWidget           {{ background-color: {_DARK};   color: white; }}
        QGroupBox         {{ border: 1px solid #555; margin-top: 14px; padding-top: 6px; }}
        QGroupBox::title  {{ color: white; subcontrol-origin: margin; left: 8px; }}
        QTextEdit         {{ background-color: {_DARKER}; color: white;  border: 1px solid #555;
                             font-family: Consolas; font-size: 9pt; }}
        QListWidget       {{ background-color: {_DARKER}; color: white;  border: 1px solid #555;
                             font-family: Consolas; font-size: 9pt; }}
        QPushButton       {{ background-color: #4b4b4b; color: white; border: none; padding: 4px 10px; }}
        QPushButton:hover {{ background-color: #5b5b5b; }}
        QStatusBar        {{ background-color: {_DARKER}; color: white; font-size: 9pt; }}
        QSplitter::handle {{ background-color: #444; }}
    """)

    window = QMainWindow()
    window.setWindowTitle("PyroxContextMenu Test")
    window.resize(900, 700)

    central = QWidget()
    window.setCentralWidget(central)
    root_layout = QVBoxLayout(central)
    root_layout.setContentsMargins(10, 10, 10, 10)
    root_layout.setSpacing(8)

    # Title
    title = QLabel("PyroxContextMenu Test")
    title.setStyleSheet("font-size: 16pt; font-weight: bold;")
    title.setAlignment(Qt.AlignmentFlag.AlignLeft)
    root_layout.addWidget(title)

    # --- Test areas ---
    splitter = QSplitter(Qt.Orientation.Vertical)
    root_layout.addWidget(splitter, stretch=1)

    # Text area
    text_group = QGroupBox("Text Area (Right-click for text menu)")
    tg_layout = QVBoxLayout(text_group)
    text_edit = QTextEdit()
    text_edit.setPlainText(
        "Right-click here to see text context menu\n\n"
        "This area demonstrates text editing operations:\n"
        "  • Cut, Copy, Paste\n"
        "  • Select All\n\n"
        "Try selecting some text and right-clicking!"
    )
    tg_layout.addWidget(text_edit)
    splitter.addWidget(text_group)

    # File list area
    file_group = QGroupBox("File List Area (Right-click for file menu)")
    fg_layout = QVBoxLayout(file_group)
    file_list = QListWidget()
    for f in ["document.txt", "image.png", "script.py", "config.json", "README.md"]:
        file_list.addItem(f)
    fg_layout.addWidget(file_list)
    splitter.addWidget(file_group)

    # View area (canvas placeholder)
    view_group = QGroupBox("View Area (Right-click for view menu)")
    vg_layout = QVBoxLayout(view_group)
    canvas_label = QLabel("Canvas area — right-click for view options")
    canvas_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    canvas_label.setStyleSheet(f"background-color: {_DARKER}; min-height: 80px;")
    canvas_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    vg_layout.addWidget(canvas_label)
    splitter.addWidget(view_group)

    # Event log
    log_group = QGroupBox("Event Log")
    lg_layout = QVBoxLayout(log_group)
    log_edit = QTextEdit()
    log_edit.setReadOnly(True)
    log_edit.setStyleSheet(f"background-color: {_DARKER}; color: #00ff00; font-family: Consolas;")
    log_edit.setFixedHeight(140)
    lg_layout.addWidget(log_edit)
    root_layout.addWidget(log_group)

    def log(msg: str) -> None:
        log_edit.append(msg)

    log("PyroxContextMenu Test\n" + "=" * 50)
    log("Instructions:\n  • Right-click in different areas to see context menus")
    log("  • Each area has a different menu style")

    # --- Context menus ---
    text_menu = PyroxContextMenu()
    file_menu = PyroxContextMenu()
    view_menu = PyroxContextMenu()

    def on_selected(item_id: str, item: MenuItem) -> None:
        log(f"[{item_id}] '{item.label}' selected")

    def on_opened(x: int, y: int) -> None:
        log(f"Context menu opened at ({x}, {y})")

    for m in (text_menu, file_menu, view_menu):
        m.on_item_selected = on_selected
        m.on_menu_opened = on_opened

    # Text menu items
    for item in create_standard_text_menu():
        if item.id == "cut":
            item.command = lambda: log("Cut operation performed")
        elif item.id == "copy":
            item.command = lambda: log("Copy operation performed")
        elif item.id == "paste":
            item.command = lambda: log("Paste operation performed")
        elif item.id == "select_all":
            item.command = lambda: (
                text_edit.selectAll(),
                log("Select All performed"),        # type: ignore[func-returns-value]
            )
        text_menu.add_item(item)

    # File menu items
    for item in create_file_menu():
        if item.id == "open":
            item.command = lambda: log("Open file operation")
        elif item.id == "edit":
            item.command = lambda: log("Edit file operation")
        elif item.id == "delete":
            item.command = lambda: log("Delete file operation")
        elif item.id == "properties":
            item.command = lambda: log("Show properties operation")
        file_menu.add_item(item)

    # View menu items
    for item in create_view_menu():
        if item.id == "refresh":
            item.command = lambda: log("Refresh view operation")
        elif item.id.startswith("view_"):
            item.command = (
                lambda vid=item.id: log(f"View changed to: {vid}")
            )
        view_menu.add_item(item)

    # Bind menus
    text_menu.bind_to_widget(text_edit)
    file_menu.bind_to_widget(file_list)
    view_menu.bind_to_widget(canvas_label)

    # Controls
    ctrl_row = QHBoxLayout()
    root_layout.addLayout(ctrl_row)

    add_btn = QPushButton("Add Custom Item")
    toggle_btn = QPushButton("Toggle Items")
    ctrl_row.addWidget(add_btn)
    ctrl_row.addWidget(toggle_btn)
    ctrl_row.addStretch()

    def add_custom_item() -> None:
        import random
        item_id = f"custom_{random.randint(1000, 9999)}"
        text_menu.add_item(MenuItem(
            id=item_id,
            label=f"Custom Item {item_id[-4:]}",
            command=lambda iid=item_id: log(f"Custom item {iid} executed"),
            icon="⭐",
        ))
        log(f"Added custom item: {item_id}")

    def toggle_menu_items() -> None:
        for iid in ("cut", "copy", "paste"):
            mi = text_menu.get_item(iid)
            if mi:
                if mi.enabled:
                    text_menu.disable_item(iid)
                else:
                    text_menu.enable_item(iid)
        log("Toggled menu item states")

    add_btn.clicked.connect(add_custom_item)
    toggle_btn.clicked.connect(toggle_menu_items)

    sb = window.statusBar()
    if sb:
        sb.showMessage("PyroxContextMenu Test Ready")

    print("Text menu items:", text_menu.get_all_item_ids())
    print("File menu items:", file_menu.get_all_item_ids())
    print("View menu items:", view_menu.get_all_item_ids())

    return window


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = _create_demo_window(app)
    window.show()
    sys.exit(app.exec())

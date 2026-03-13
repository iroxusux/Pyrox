"""GUI management service for Pyrox.

This module provides a PyQt6-based equivalent of TkGuiManager, wrapping a
QApplication + QMainWindow pair with the same static-class interface.
"""
from __future__ import annotations
import sys
from typing import Callable

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QAction, QCloseEvent, QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
)

from pyrox.services.env import EnvManager
from pyrox.services.menu_registry import MenuRegistry
from pyrox.interfaces import EnvironmentKeys


# ---------------------------------------------------------------------------
# Key-binding helpers
# ---------------------------------------------------------------------------

_TK_MODIFIER_TO_QT: dict[str, str] = {
    'Control': 'Ctrl',
    'Alt': 'Alt',
    'Shift': 'Shift',
    'Meta': 'Meta',
    'Win': 'Meta',
    'Command': 'Meta',
}


def _tk_binding_to_qt_sequence(binding: str) -> str | None:
    """Convert a Tkinter key binding to a Qt key-sequence string.

    Examples::

        '<Control-s>'       -> 'Ctrl+S'
        '<Control-Shift-S>' -> 'Ctrl+Shift+S'
        '<F1>'              -> 'F1'
        '<Alt-F4>'          -> 'Alt+F4'

    Returns None if the binding cannot be parsed.
    """
    if not binding or not binding.startswith('<') or not binding.endswith('>'):
        return None

    inner = binding[1:-1]
    parts = inner.split('-')
    modifiers: list[str] = []
    key: str | None = None

    for part in parts:
        qt_mod = _TK_MODIFIER_TO_QT.get(part)
        if qt_mod:
            modifiers.append(qt_mod)
        else:
            key = part

    if key is None:
        return None

    # Uppercase single alpha key for Qt convention
    if len(key) == 1 and key.isalpha():
        key = key.upper()

    return '+'.join(modifiers + [key])


def _filetypes_to_qt_filter(filetypes: list[tuple[str, str]] | None) -> str:
    """Convert Tk-style ``[(label, pattern), ...]`` to a Qt filter string."""
    if not filetypes:
        return 'All files (*.*)'
    return ';;'.join(f'{label} ({pattern})' for label, pattern in filetypes)


# ---------------------------------------------------------------------------
# Internal QMainWindow subclass
# ---------------------------------------------------------------------------

class _PyQt6MainWindow(QMainWindow):
    """QMainWindow with callback-based hooks for close and configure events."""

    def __init__(self) -> None:
        super().__init__()
        self._close_callback: Callable | None = None
        self._configure_callbacks: list[Callable] = []

    def closeEvent(self, event: QCloseEvent) -> None:  # type: ignore[override]
        if self._close_callback:
            self._close_callback()
            event.ignore()  # Callback is responsible for calling quit_application()
        else:
            event.accept()

    def resizeEvent(self, a0) -> None:  # type: ignore[override]
        super().resizeEvent(a0)
        for cb in self._configure_callbacks:
            cb()

    def moveEvent(self, a0) -> None:  # type: ignore[override]
        super().moveEvent(a0)
        for cb in self._configure_callbacks:
            cb()


# ---------------------------------------------------------------------------
# PyQt6GuiManager
# ---------------------------------------------------------------------------

class GuiManager:
    """Static manager for PyQt6 GUI operations.

    Mirrors the interface of ``TkGuiManager`` using PyQt6 primitives.
    The manager owns one ``QApplication`` and one ``_PyQt6MainWindow``
    instance for the lifetime of the process.
    """

    # Class-level storage
    _initialized: bool = False
    _app: QApplication | None = None
    _root_window: _PyQt6MainWindow | None = None
    _menu_bar: QMenuBar | None = None

    # Scheduled timer tracking (for debouncing / cancellation)
    _scheduled_timers: dict[str, QTimer] = {}
    _timer_counter: int = 0

    # Debounce handle for save_root_geometry
    _after_id: str | None = None

    def __init__(self) -> None:
        """Prevent instantiation of static class."""
        raise TypeError("PyQt6GuiManager is a static class and cannot be instantiated")

    # --------------------------------------------------
    # GUI Binding Methods
    # --------------------------------------------------

    @classmethod
    def bind_hotkey(
        cls,
        hotkey: str,
        callback: Callable,
        **kwargs,
    ) -> None:
        """Bind a global hotkey to a callback function.

        Args:
            hotkey: Tk-style (e.g. ``'<Control-s>'``) or Qt-style (``'Ctrl+S'``).
            callback: Function to invoke when the hotkey fires.

        Raises:
            RuntimeError: If the root window is not initialized.
        """
        qt_seq = _tk_binding_to_qt_sequence(hotkey) if hotkey.startswith('<') else hotkey
        if qt_seq:
            shortcut = QShortcut(QKeySequence(qt_seq), cls.get_root())
            shortcut.activated.connect(callback)

    # --------------------------------------------------
    # GUI Event Handling
    # --------------------------------------------------

    @classmethod
    def schedule_event(
        cls,
        delay_ms: int,
        callback: Callable[..., None],
        **kwargs,
    ) -> str:
        """Schedule *callback* to be called after *delay_ms* milliseconds.

        Returns an opaque ID that can be passed to :meth:`cancel_scheduled_event`.
        """
        timer = QTimer()
        timer.setSingleShot(True)
        timer_id = str(cls._timer_counter)
        cls._timer_counter += 1
        cls._scheduled_timers[timer_id] = timer

        def _on_timeout() -> None:
            cls._scheduled_timers.pop(timer_id, None)
            callback(**kwargs)

        timer.timeout.connect(_on_timeout)
        timer.start(delay_ms)
        return timer_id

    @classmethod
    def cancel_scheduled_event(cls, event_id: str) -> None:
        """Cancel a previously scheduled event by its ID."""
        timer = cls._scheduled_timers.pop(event_id, None)
        if timer:
            timer.stop()
            timer.deleteLater()

    @classmethod
    def subscribe_to_window_change_event(cls, callback: Callable[..., None]) -> None:
        """Subscribe to window resize / move events.

        Multiple subscribers are supported and will all be called.
        """
        cls.get_root()._configure_callbacks.append(callback)

    @classmethod
    def subscribe_to_window_close_event(cls, callback: Callable[..., None]) -> None:
        """Subscribe to the window close event (replaces any previous subscriber)."""
        cls.get_root()._close_callback = callback

    @classmethod
    def update_idletasks(cls) -> None:
        """Process all pending GUI events."""
        QApplication.processEvents()

    # --------------------------------------------------
    # GUI Configuration
    # --------------------------------------------------

    @classmethod
    def config_from_env(cls, **kwargs) -> None:
        """Configure the root window from environment variables."""
        cls.set_title(
            EnvManager.get(
                EnvironmentKeys.core.APP_WINDOW_TITLE,
                default=kwargs.get('title', 'Pyrox Application'),
            )
        )
        cls.restore_root_geometry()
        icon_path = cls.get_default_icon_path()
        if icon_path:
            cls.set_icon(icon_path)

    @classmethod
    def get_default_icon_path(cls) -> str | None:
        """Return the default icon path from the environment."""
        return EnvManager.get(EnvironmentKeys.core.APP_ICON, None, str)

    @classmethod
    def set_icon(
        cls,
        icon_path: str | None,
        window: QMainWindow | None = None,
    ) -> None:
        """Set the window icon from *icon_path*."""
        if not isinstance(icon_path, str):
            raise TypeError('Icon path must be a string representing the file path to the icon.')

        target = window or cls.get_root()
        target.setWindowIcon(QIcon(icon_path))

    @classmethod
    def get_title(
        cls,
        window: QMainWindow | None = None,
    ) -> str:
        """Return the current window title."""
        return (window or cls.get_root()).windowTitle()

    @classmethod
    def set_title(
        cls,
        title: str,
        window: QMainWindow | None = None,
    ) -> None:
        """Set the window title to *title*."""
        if not isinstance(title, str):
            raise TypeError('Title must be a string.')

        (window or cls.get_root()).setWindowTitle(title)

    # --------------------------------------------------
    # Root Management
    # --------------------------------------------------

    @classmethod
    def create_root(cls, **kwargs) -> _PyQt6MainWindow:
        """Create (or return existing) QApplication + root QMainWindow."""
        if cls._root_window is not None:
            return cls._root_window

        if not QApplication.instance():
            cls._app = QApplication(sys.argv)
        else:
            cls._app = QApplication.instance()  # type: ignore[assignment]

        cls._root_window = _PyQt6MainWindow()
        cls.config_from_env(**kwargs)
        cls._root_window.show()
        return cls._root_window

    @classmethod
    def get_root(cls) -> _PyQt6MainWindow:
        """Return the root window, raising if not yet initialized."""
        if not cls._root_window:
            raise RuntimeError("Root window not initialized")
        return cls._root_window

    @classmethod
    def get_app(cls) -> QApplication:
        """Return the QApplication instance."""
        if not cls._app:
            raise RuntimeError("QApplication not initialized")
        return cls._app

    @classmethod
    def focus_root(cls) -> None:
        """Bring the root window to the front and give it focus."""
        cls.get_root().activateWindow()
        cls.get_root().raise_()

    @classmethod
    def _store_root_state(cls) -> None:
        """Persist current window geometry and state to the environment."""
        cls._after_id = None

        w = cls.get_root().width()
        h = cls.get_root().height()
        EnvManager.set(EnvironmentKeys.ui.UI_WINDOW_SIZE, f'{w}x{h}')

        pos = cls.get_root().x(), cls.get_root().y()
        EnvManager.set(EnvironmentKeys.ui.UI_WINDOW_POSITION, str(pos))

        if cls.get_root().isMaximized():
            state = 'zoomed'
        elif cls.get_root().isMinimized():
            state = 'iconic'
        else:
            state = 'normal'
        EnvManager.set(EnvironmentKeys.ui.UI_WINDOW_STATE, state)

        EnvManager.set(
            EnvironmentKeys.ui.UI_WINDOW_FULLSCREEN,
            str(cls.get_root().isFullScreen()),
        )

    @classmethod
    def save_root_geometry(cls) -> None:
        """Debounced geometry save — resets the 500 ms timer on each call."""
        if cls._after_id:
            cls.cancel_scheduled_event(cls._after_id)
        cls._after_id = cls.schedule_event(500, cls._store_root_state)

    @classmethod
    def restore_root_geometry(cls) -> None:
        """Restore window geometry and state from environment variables."""
        full_screen = EnvManager.get(
            key=EnvironmentKeys.ui.UI_WINDOW_FULLSCREEN,
            default=False,
            cast_type=bool,
        )
        if full_screen:
            cls.get_root().showFullScreen()
            return

        window_size = EnvManager.get(
            key=EnvironmentKeys.ui.UI_WINDOW_SIZE,
            default=None,
            cast_type=str,
        )
        if window_size:
            parts = window_size.split('x')
            if len(parts) == 2:
                try:
                    cls.get_root().resize(int(parts[0]), int(parts[1]))
                except ValueError:
                    pass

        window_position = EnvManager.get(
            key=EnvironmentKeys.ui.UI_WINDOW_POSITION,
            default=None,
            cast_type=tuple,
        )
        if window_position and len(window_position) == 2:
            try:
                cls.get_root().move(int(window_position[0]), int(window_position[1]))
            except (ValueError, TypeError):
                pass

        window_state = EnvManager.get(
            key=EnvironmentKeys.ui.UI_WINDOW_STATE,
            default='normal',
            cast_type=str,
        )
        if window_state == 'zoomed':
            cls.get_root().showMaximized()
        elif window_state in ('iconic', 'minimized'):
            cls.get_root().showMinimized()

    # --------------------------------------------------
    # Root Menu Management
    # --------------------------------------------------

    @classmethod
    def create_root_menu(cls) -> QMenuBar:
        """Create the main menu bar with standard top-level menus."""
        if cls._menu_bar is not None:
            return cls._menu_bar

        menu_bar = cls.get_root().menuBar()
        if menu_bar is None:
            raise RuntimeError("Failed to retrieve menu bar from root window")
        cls._menu_bar = menu_bar

        menus = [
            ('file_menu',  'root/file',  'File',  0),
            ('edit_menu',  'root/edit',  'Edit',  1),
            ('tools_menu', 'root/tools', 'Tools', 2),
            ('view_menu',  'root/view',  'View',  3),
            ('help_menu',  'root/help',  'Help',  4),
        ]
        for menu_id, path, label, idx in menus:
            menu_widget = cls._menu_bar.addMenu(label)
            MenuRegistry.register_item(
                menu_id=menu_id,
                menu_path=path,
                menu_widget=menu_widget,
                menu_index=idx,
                owner='PyQt6GuiManager',
                metadata={'category': 'root'},
            )

        return cls._menu_bar  # type: ignore[return-value]  # guarded above

    @classmethod
    def get_file_menu(cls) -> QMenu:
        descriptor = MenuRegistry.get_item('file_menu')
        if not descriptor:
            raise RuntimeError("File menu not found in MenuRegistry")
        return descriptor.menu_widget

    @classmethod
    def get_edit_menu(cls) -> QMenu:
        descriptor = MenuRegistry.get_item('edit_menu')
        if not descriptor:
            raise RuntimeError("Edit menu not found in MenuRegistry")
        return descriptor.menu_widget

    @classmethod
    def get_view_menu(cls) -> QMenu:
        descriptor = MenuRegistry.get_item('view_menu')
        if not descriptor:
            raise RuntimeError("View menu not found in MenuRegistry")
        return descriptor.menu_widget

    @classmethod
    def get_tools_menu(cls) -> QMenu:
        descriptor = MenuRegistry.get_item('tools_menu')
        if not descriptor:
            raise RuntimeError("Tools menu not found in MenuRegistry")
        return descriptor.menu_widget

    @classmethod
    def get_help_menu(cls) -> QMenu:
        descriptor = MenuRegistry.get_item('help_menu')
        if not descriptor:
            raise RuntimeError("Help menu not found in MenuRegistry")
        return descriptor.menu_widget

    @classmethod
    def get_root_menu(cls) -> QMenuBar:
        if not cls._menu_bar:
            raise RuntimeError("Root menu bar not initialized")
        return cls._menu_bar

    # --------------------------------------------------
    # GUI User Input Handling
    # --------------------------------------------------

    @classmethod
    def prompt_user_open_file(
        cls,
        title: str = "Open file",
        filetypes: list[tuple[str, str]] | None = None,
    ) -> str | None:
        """Show a file-open dialog. Returns the chosen path or ``None``."""
        path, _ = QFileDialog.getOpenFileName(
            cls.get_root(),
            title,
            '',
            _filetypes_to_qt_filter(filetypes),
        )
        return path if path else None

    @classmethod
    def prompt_user_save_file(
        cls,
        title: str = "Save file as",
        filetypes: list[tuple[str, str]] | None = None,
    ) -> str | None:
        """Show a file-save dialog. Returns the chosen path or ``None``."""
        path, _ = QFileDialog.getSaveFileName(
            cls.get_root(),
            title,
            '',
            _filetypes_to_qt_filter(filetypes),
        )
        return path if path else None

    @classmethod
    def prompt_user_select_directory(
        cls,
        title: str = "Select directory",
    ) -> str | None:
        """Show a directory-selection dialog. Returns the chosen path or ``None``."""
        path = QFileDialog.getExistingDirectory(cls.get_root(), title)
        return path if path else None

    @classmethod
    def prompt_user_yes_no(
        cls,
        title: str,
        message: str,
    ) -> bool:
        """Show a yes/no confirmation dialog. Returns ``True`` if the user chose Yes."""
        result = QMessageBox.question(
            cls.get_root(),
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes

    # --------------------------------------------------
    # GUI Lifecycle Management
    # --------------------------------------------------

    @classmethod
    def run_main_loop(cls) -> None:
        """Start the Qt event loop (blocks until the window is closed)."""
        cls.get_app().exec()

    @classmethod
    def quit_application(cls) -> None:
        """Quit the Qt application."""
        cls.get_app().quit()

    # --------------------------------------------------
    # Exception Handling
    # --------------------------------------------------

    @classmethod
    def reroute_excepthook(cls, callback: Callable[..., None]) -> None:
        """Redirect unhandled exceptions to *callback* via ``sys.excepthook``.

        The callback receives ``(exc_type, exc_value, exc_traceback)``,
        matching the signature of ``sys.excepthook``.
        """
        sys.excepthook = callback

    # --------------------------------------------------
    # Menu Utility
    # --------------------------------------------------

    @classmethod
    def insert_menu_command_with_accelerator(
        cls,
        menu: QMenu,
        index: int,
        label: str,
        command: Callable | None = None,
        accelerator: str = '',
        underline: int = 0,
    ) -> QAction:
        """Insert a :class:`QAction` into *menu* at *index* with an optional accelerator.

        Args:
            menu: The target ``QMenu``.
            index: Zero-based position at which to insert the action.
            label: Display text for the action.
            command: Optional callable connected to the action's ``triggered`` signal.
            accelerator: Human-readable shortcut string (e.g. ``'Ctrl+S'``).
            underline: Ignored (Qt handles mnemonics via ``&`` in *label*).

        Returns:
            QAction: The created action.
        """
        action = QAction(label, menu)

        if accelerator:
            action.setShortcut(QKeySequence(accelerator))

        if command:
            action.triggered.connect(command)

        actions = menu.actions()
        if index < len(actions):
            menu.insertAction(actions[index], action)
        else:
            menu.addAction(action)

        return action


__all__ = (
    'GuiManager',
)

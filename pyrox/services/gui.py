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
from pyrox.services.gui_state import GuiStateService
from pyrox.services.menu_registry import MenuRegistry
from pyrox.interfaces import EnvironmentKeys


# ---------------------------------------------------------------------------
# Key-binding helpers
# ---------------------------------------------------------------------------

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

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        from PyQt6.QtCore import Qt
        if event is not None and event.key() == Qt.Key.Key_F11:
            GuiManager.toggle_fullscreen()
        else:
            super().keyPressEvent(event)


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
    ) -> None:
        """Bind a global hotkey to a callback function.

        Args:
            hotkey: Qt-style (``'Ctrl+S'``).
            callback: Function to invoke when the hotkey fires.

        Raises:
            RuntimeError: If the root window is not initialized.
        """
        if hotkey:
            shortcut = QShortcut(QKeySequence(hotkey), cls.get_root())
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
        GuiStateService.load()
        cls.restore_root_geometry()
        # Auto-save window geometry whenever the window is moved or resized.
        cls.subscribe_to_window_change_event(cls.save_root_geometry)
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
    def create_root(cls, show: bool = True, **kwargs) -> _PyQt6MainWindow:
        """Create (or return existing) QApplication + root QMainWindow.

        Args:
            show: Whether to call ``show()`` on the root window immediately.
                  Pass ``False`` when a splash screen will be displayed first
                  and the caller will call ``show()`` manually later.
        """
        if cls._root_window is not None:
            return cls._root_window

        if not QApplication.instance():
            cls._app = QApplication(sys.argv)
        else:
            cls._app = QApplication.instance()  # type: ignore[assignment]

        cls._root_window = _PyQt6MainWindow()
        cls.config_from_env(**kwargs)
        if show:
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
        """Persist current window geometry and state via GuiStateService."""
        cls._after_id = None
        GuiStateService.capture_from_window(cls.get_root())
        GuiStateService.save()

    @classmethod
    def save_root_geometry(cls) -> None:
        """Debounced geometry save — resets the 500 ms timer on each call."""
        if cls._after_id:
            cls.cancel_scheduled_event(cls._after_id)
        cls._after_id = cls.schedule_event(500, cls._store_root_state)

    @classmethod
    def restore_root_geometry(cls) -> None:
        """Restore window geometry and state from GuiStateService."""
        GuiStateService.apply_to_window(cls.get_root())

    @classmethod
    def toggle_fullscreen(cls) -> None:
        """Toggle the root window between fullscreen and its previous state.

        Pressing F11 calls this method.  When leaving fullscreen the window
        is restored to its previous maximized-or-normal state as recorded in
        :class:`GuiStateService`, and the updated state is saved to disk.
        """
        root = cls.get_root()
        if root.isFullScreen():
            GuiStateService.set_fullscreen(False)
            # Restore to whichever state was active before going fullscreen.
            if GuiStateService.get_window_state() == 'zoomed':
                root.showMaximized()
            else:
                root.showNormal()
        else:
            GuiStateService.set_fullscreen(True)
            root.showFullScreen()
        GuiStateService.save()

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
        """Flush window state to disk then quit the Qt application."""
        # Cancel any pending debounce timer and do an immediate synchronous save
        # so geometry is never lost even if the user closes the window quickly.
        if cls._after_id:
            cls.cancel_scheduled_event(cls._after_id)
        cls._store_root_state()
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

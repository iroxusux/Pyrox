"""GUI framework management services for Pyrox.

This module provides functionality to manage GUI frameworks and backends
based on environment configuration.
It supports multiple GUI frameworks
and provides a unified interface for GUI operations.
"""
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import Any, Callable, Union
from pyrox.services import EnvManager, log, ThemeManager, MenuRegistry
from pyrox.interfaces import (
    EnvironmentKeys,
)


class TkGuiManager:
    """Static manager for Tk GUI operations."""

    # Class-level storage
    _initialized: bool = False
    _root_window: tk.Tk | None = None
    _root_menu: tk.Menu | None = None

    # Store additional menus for the root menu so we can access them globally
    _file_menu: tk.Menu | None = None
    _edit_menu: tk.Menu | None = None
    _view_menu: tk.Menu | None = None
    _tools_menu: tk.Menu | None = None
    _help_menu: tk.Menu | None = None

    def __init__(self):
        """Prevent instantiation of static class."""
        raise TypeError("GuiManager is a static class and cannot be instantiated")

    # --------------------------------------------------
    # GUI Binding Methods
    # --------------------------------------------------

    @classmethod
    def bind_hotkey(
        cls,
        hotkey: str,
        callback: Callable,
        **kwargs
    ) -> None:
        """Bind a global hotkey to a callback function.

        Args:
            hotkey: The hotkey string to bind (e.g., '<Control-s>').
            callback: The function to call when the hotkey is pressed.
            **kwargs: Additional keyword arguments (unused in Tkinter implementation).

        Raises:
            RuntimeError: If the root window is not initialized.
        """
        def on_key_event(event):
            callback()

        cls.get_root().bind(hotkey, on_key_event)

    # --------------------------------------------------
    # Gui Event Handling
    # --------------------------------------------------

    @classmethod
    def schedule_event(
        cls,
        delay_ms: int,
        callback: Callable[..., Any],
        **kwargs
    ) -> Union[int, str]:
        """Schedule a callback to be called after a delay in milliseconds."""
        return cls.get_root().after(delay_ms, callback, **kwargs)

    @classmethod
    def cancel_scheduled_event(cls, event_id: int | str) -> None:
        cls.get_root().after_cancel(str(event_id))

    @classmethod
    def subscribe_to_window_change_event(cls, callback: Callable[..., Any]) -> None:
        """Subscribe to the window change event."""
        cls.get_root().bind("<Configure>", lambda event: callback())

    @classmethod
    def subscribe_to_window_close_event(cls, callback: Callable[..., Any]) -> None:
        """Subscribe to the window close event."""
        cls.get_root().protocol("WM_DELETE_WINDOW", callback)

    # --------------------------------------------------
    # Gui Configuration
    # --------------------------------------------------

    @classmethod
    def config_from_env(cls, **kwargs) -> None:
        """Configure the root window from environment variables.

        This method can be expanded to read specific environment variables
        and apply configurations to the root window as needed.
        """
        cls.set_title(
            EnvManager.get(
                EnvironmentKeys.core.APP_WINDOW_TITLE,
                default=kwargs.get('title', 'Pyrox Application')
            )
        )

        cls.get_root().wm_geometry(
            EnvManager.get(
                EnvironmentKeys.ui.UI_WINDOW_SIZE,
                default=kwargs.get('geometry', '800x600')
            )
        )

        icon_path = EnvManager.get(
            EnvironmentKeys.core.APP_ICON,
            None,
            str
        )

        if icon_path and Path(icon_path).is_file():
            cls.get_root().iconbitmap(str(icon_path))
        else:
            log(cls).warning(f'Icon file not found: {icon_path}.')

        # Apply any additional configurations passed in kwargs
        cls.get_root().config(**kwargs)

    @classmethod
    def set_icon(
        cls,
        icon_path: str,
        window: tk.Tk | tk.Toplevel | None = None
    ) -> None:
        """Set the application icon for the Tkinter root window."""
        if not isinstance(icon_path, str):
            raise TypeError('Icon path must be a string representing the file path to the icon.')

        window = window or cls.get_root()
        window.iconbitmap(icon_path)

    @classmethod
    def get_title(
        cls,
        window: tk.Tk | tk.Toplevel | None
    ) -> str:
        """Get the application window title.

        Returns:
            The current window title.
        """
        window = window or cls.get_root()
        return window.title()

    @classmethod
    def set_title(
        cls,
        title: str,
        window: tk.Tk | tk.Toplevel | None = None
    ) -> None:
        """Set the application window title.

        Args:
            title: The new window title.
        """
        if not isinstance(title, str):
            raise TypeError('Title must be a string.')

        window = window or cls.get_root()
        window.title(title)

    # --------------------------------------------------
    # Root Management
    # --------------------------------------------------

    @classmethod
    def create_root(cls, **kwargs) -> tk.Tk:
        if cls._root_window is not None:
            return cls._root_window

        cls._root_window = tk.Tk()
        cls.config_from_env(**kwargs)
        ThemeManager.ensure_theme_created()
        return cls._root_window

    @classmethod
    def get_root(cls) -> tk.Tk:
        if not cls._root_window:
            raise RuntimeError("Root window not initialized")

        return cls._root_window

    @classmethod
    def focus_root(cls) -> None:
        cls.get_root().focus()

    @classmethod
    def _store_root_state(cls) -> None:
        """Store the current window state in environment variables.
        """
        cls._after_id = None  # Reset after_id since the event has fired

        size = cls.get_root().size()
        EnvManager.set(
            EnvironmentKeys.ui.UI_WINDOW_SIZE,
            f'{size[0]}x{size[1]}'
        )

        position = cls.get_root().winfo_rootx(), cls.get_root().winfo_rooty()
        EnvManager.set(
            EnvironmentKeys.ui.UI_WINDOW_POSITION,
            str(position)
        )

        state = cls.get_root().state()
        EnvManager.set(
            EnvironmentKeys.ui.UI_WINDOW_STATE,
            state
        )

        fullscreen = cls.get_root().attributes('-fullscreen')
        EnvManager.set(
            EnvironmentKeys.ui.UI_WINDOW_FULLSCREEN,
            str(fullscreen)
        )

    @classmethod
    def save_root_geometry(cls) -> None:
        """Handle window resize events.
        """
        if cls._after_id:  # If we've scheduled an event, cancel it
            cls.cancel_scheduled_event(cls._after_id)

        cls._after_id = cls.schedule_event(500, cls._store_root_state)

    @classmethod
    def restore_root_geometry(cls) -> None:
        full_screen = EnvManager.get(
            key=EnvironmentKeys.ui.UI_WINDOW_FULLSCREEN,
            default=False,
            cast_type=bool
        )
        if full_screen:
            cls.get_root().attributes('-fullscreen', True)

        window_position = EnvManager.get(
            key=EnvironmentKeys.ui.UI_WINDOW_POSITION,
            default=None,
            cast_type=tuple
        )

        # Restore window size and position if available
        geometry_str = ''
        if window_position and len(window_position) == 2:
            geometry_str = f'+{window_position[0]}+{window_position[1]}'
        window_size = EnvManager.get(
            key=EnvironmentKeys.ui.UI_WINDOW_SIZE,
            default=None,
            cast_type=str
        )
        if window_size:
            window_size_arr = window_size.split('x')
            if len(window_size_arr) == 2:
                geometry_str = f'{window_size_arr[0]}x{window_size_arr[1]}{geometry_str}'
        if geometry_str:
            cls.get_root().geometry(geometry_str)

        window_state = EnvManager.get(
            key=EnvironmentKeys.ui.UI_WINDOW_STATE,
            default='normal',
            cast_type=str
        )
        if window_state:
            cls.get_root().state(window_state)

    # --------------------------------------------------
    # Root Menu Management
    # --------------------------------------------------

    @classmethod
    def create_root_menu(cls) -> tk.Menu:
        if cls._root_menu is not None:
            return cls._root_menu

        cls._root_menu = tk.Menu(cls.get_root())
        cls.get_root().config(menu=cls._root_menu)

        # create additional menus here
        MenuRegistry.register_item(
            menu_id='file_menu',
            menu_path='root/file',
            menu_widget=tk.Menu(cls._root_menu, tearoff=0),
            menu_index=0,
            owner='TkGuiManager',
            metadata={'category': 'root'},
        )
        MenuRegistry.register_item(
            menu_id='edit_menu',
            menu_path='root/edit',
            menu_widget=tk.Menu(cls._root_menu, tearoff=0),
            menu_index=1,
            owner='TkGuiManager',
            metadata={'category': 'root'},
        )
        MenuRegistry.register_item(
            menu_id='view_menu',
            menu_path='root/view',
            menu_widget=tk.Menu(cls._root_menu, tearoff=0),
            menu_index=2,
            owner='TkGuiManager',
            metadata={'category': 'root'},
        )
        MenuRegistry.register_item(
            menu_id='tools_menu',
            menu_path='root/tools',
            menu_widget=tk.Menu(cls._root_menu, tearoff=0),
            menu_index=3,
            owner='TkGuiManager',
            metadata={'category': 'root'},
        )
        MenuRegistry.register_item(
            menu_id='help_menu',
            menu_path='root/help',
            menu_widget=tk.Menu(cls._root_menu, tearoff=0),
            menu_index=4,
            owner='TkGuiManager',
            metadata={'category': 'root'},
        )

        # add the additional menus to the root menu
        cls._root_menu.add_cascade(label="File", menu=cls.get_file_menu())
        cls._root_menu.add_cascade(label="Edit", menu=cls.get_edit_menu())
        cls._root_menu.add_cascade(label="View", menu=cls.get_view_menu())
        cls._root_menu.add_cascade(label="Tools", menu=cls.get_tools_menu())
        cls._root_menu.add_cascade(label="Help", menu=cls.get_help_menu())

        return cls._root_menu

    @classmethod
    def get_file_menu(cls) -> tk.Menu:
        descriptor = MenuRegistry.get_item('file_menu')
        if not descriptor:
            raise RuntimeError("File menu not found in MenuRegistry")
        return descriptor.menu_widget

    @classmethod
    def get_edit_menu(cls) -> tk.Menu:
        descriptor = MenuRegistry.get_item('edit_menu')
        if not descriptor:
            raise RuntimeError("Edit menu not found in MenuRegistry")
        return descriptor.menu_widget

    @classmethod
    def get_view_menu(cls) -> tk.Menu:
        descriptor = MenuRegistry.get_item('view_menu')
        if not descriptor:
            raise RuntimeError("View menu not found in MenuRegistry")
        return descriptor.menu_widget

    @classmethod
    def get_tools_menu(cls) -> tk.Menu:
        descriptor = MenuRegistry.get_item('tools_menu')
        if not descriptor:
            raise RuntimeError("Tools menu not found in MenuRegistry")
        return descriptor.menu_widget

    @classmethod
    def get_help_menu(cls) -> tk.Menu:
        descriptor = MenuRegistry.get_item('help_menu')
        if not descriptor:
            raise RuntimeError("Help menu not found in MenuRegistry")
        return descriptor.menu_widget

    @classmethod
    def get_root_menu(cls) -> tk.Menu:
        if not cls._root_menu:
            raise RuntimeError("Root menu not initialized")

        return cls._root_menu

    # --------------------------------------------------
    # Gui user input handling
    # --------------------------------------------------

    @classmethod
    def prompt_user_open_file(
        cls,
        title: str = "Open file",
        filetypes: list[tuple[str, str]] | None = None
    ) -> str | None:
        """Show a file open dialog to the user.

        Args:
            title: The title of the dialog.
            filetypes: Optional list of (label, pattern) tuples for file types.
        Returns:
            The selected file path, or None if cancelled.
        """
        file_path = filedialog.askopenfilename(
            parent=cls.get_root(),
            title=title,
            filetypes=filetypes or [("All files", "*.*")]
        )
        return file_path if file_path else None

    @classmethod
    def prompt_user_save_file(
        cls,
        title: str = "Save file as",
        filetypes: list[tuple[str, str]] | None = None
    ) -> str | None:
        """Show a file save dialog to the user.

        Args:
            title: The title of the dialog.
            filetypes: Optional list of (label, pattern) tuples for file types.
        Returns:
            The selected file path, or None if cancelled.
        """
        file_path = filedialog.asksaveasfilename(
            parent=cls.get_root(),
            title=title,
            filetypes=filetypes or [("All files", "*.*")]
        )
        return file_path if file_path else None

    @classmethod
    def prompt_user_select_directory(
        cls,
        title: str = "Select directory"
    ) -> str | None:
        """Show a directory selection dialog to the user.

        Args:
            title: The title of the dialog.
        Returns:
            The selected directory path, or None if cancelled.
        """
        directory_path = filedialog.askdirectory(
            parent=cls.get_root(),
            title=title
        )
        return directory_path if directory_path else None

    # --------------------------------------------------
    # Gui Lifecycle Management
    # --------------------------------------------------

    @classmethod
    def run_main_loop(cls) -> None:
        """Start the Tkinter main loop."""
        cls.get_root().mainloop()

    @classmethod
    def quit_application(cls) -> None:
        """Quit the Tkinter application."""
        cls.get_root().quit()

    # --------------------------------------------------
    # Exception Handling
    # --------------------------------------------------

    @classmethod
    def reroute_excepthook(cls, callback: Callable[..., Any]) -> None:
        tk.report_callback_exception = callback  # type: ignore


__all__ = (
    'TkGuiManager',
)

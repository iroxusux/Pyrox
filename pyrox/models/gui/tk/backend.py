"""GUI backend abstract base class.

This module provides abstract base classes and implementations for different GUI backends,
allowing the framework to support multiple GUI frameworks through a unified interface.
"""

from pathlib import Path
from typing import Any, Callable, Union
import tkinter as tk

from pyrox.interfaces import (
    EnvironmentKeys,
    GuiFramework,
    IGuiBackend,
    IGuiFrame,
    IGuiMenu,
)
from pyrox.services import EnvManager, GuiManager, log, ThemeManager
from pyrox.models.gui.tk.menu import TkinterApplicationMenu, TkinterMenu
from pyrox.models.gui.tk.frame import TkinterGuiFrame
from pyrox.models.gui.tk.window import TkinterGuiWindow


class TkinterBackend(IGuiBackend):
    """Tkinter GUI backend implementation.

    This class provides a concrete implementation of the GuiBackend interface
    using the Tkinter GUI framework, which is included with Python by default.
    """

    def __init__(self):
        self._root_gui = None
        self._menu = None
        self._tk = None
        self._theme_name = "default"

    @property
    def framework_name(self) -> str:
        return "Tkinter"

    def bind_hotkey(
        self,
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
        if not self._root_gui:
            raise RuntimeError("Root window not initialized")

        def on_key_event(event):
            callback()

        self.get_root_window().bind(hotkey, on_key_event)

    def cancel_scheduled_event(self, event_id: int | str) -> None:
        self.get_root_window().after_cancel(str(event_id))

    def config_from_env(self, **kwargs) -> None:
        """Configure the root window from environment variables.

        This method can be expanded to read specific environment variables
        and apply configurations to the root window as needed.
        """
        import tkinter as tk
        if not isinstance(self.get_root_window(), tk.Tk):
            raise RuntimeError("Root window is not a Tkinter Tk instance")

        self.get_root_window().title(
            EnvManager.get(
                EnvironmentKeys.core.APP_WINDOW_TITLE,
                default=kwargs.get('title', 'Pyrox Application')
            ))

        self.get_root_window().geometry(
            EnvManager.get(
                EnvironmentKeys.ui.UI_WINDOW_SIZE,
                default=kwargs.get('geometry', '800x600')
            ))

        icon_path = EnvManager.get(
            EnvironmentKeys.core.APP_ICON,
            None,
            str
        )
        if icon_path and Path(icon_path).is_file():
            self.set_icon(str(icon_path))
        else:
            log(self).warning(f'Icon file not found: {icon_path}.')

    def create_application_gui_menu(self, **kwargs) -> TkinterApplicationMenu:
        """Create and return a Tkinter application menu."""
        if not self._tk:
            if not self.initialize():
                raise RuntimeError("Tkinter not available")

        if not self._menu:
            self._menu = TkinterApplicationMenu()
            self._menu.initialize(
                master=self.get_root_window(),
                **kwargs
            )
        self.get_root_window().config(menu=self._menu.menu)
        return self._menu

    def create_gui_frame(self, **kwargs) -> TkinterGuiFrame:
        """Create and return a generic Tkinter frame/container."""
        frame = TkinterGuiFrame()
        frame.initialize(**kwargs)
        return frame

    def create_gui_menu(self, **kwargs) -> TkinterMenu:
        """Create and return a generic menu."""
        menu = TkinterMenu()
        menu.initialize(**kwargs)
        return menu

    def create_gui_window(self, **kwargs) -> TkinterGuiWindow:
        """Create an unattached Tkinter GUI window."""
        kwargs['master'] = self._root_gui
        from tkinter import Toplevel
        tk_window = Toplevel(**kwargs)
        gui_window = TkinterGuiWindow()
        gui_window.window = tk_window
        ThemeManager.ensure_theme_created()
        return gui_window

    def create_root_gui_window(self, **kwargs) -> TkinterGuiWindow:
        """Create and return a Tkinter root window."""
        if not self._tk:
            if not self.initialize():
                raise RuntimeError("Tkinter not available")

        if self._root_gui is not None:
            return self._root_gui

        if self._tk is None:
            raise RuntimeError("Tkinter not initialized")

        title = kwargs.pop('title', 'Pyrox Application')
        geometry = kwargs.pop('geometry', '800x600')

        self._root_gui = TkinterGuiWindow()
        self._root_gui.initialize(as_root=True, **kwargs)
        self.config_from_env(
            title=title,
            geometry=geometry,
        )
        ThemeManager.ensure_theme_created()
        return self._root_gui

    def destroy_gui_frame(self, frame: IGuiFrame) -> None:
        if not isinstance(frame, TkinterGuiFrame):
            raise TypeError("Expected a TkinterGuiFrame instance")
        frame.frame.destroy()

    def destroy_gui_menu(self, menu: IGuiMenu) -> None:
        if not isinstance(menu, TkinterMenu):
            raise TypeError("Expected a TkinterMenu instance")
        menu.menu.destroy()

    def destroy_gui_window(
        self,
        window,
        **kwargs
    ) -> None:
        if not isinstance(window, TkinterGuiWindow):
            raise TypeError("Expected a TkinterGuiWindow instance")
        window.destroy()

    def get_backend(self) -> Any:
        return self._tk

    def get_framework(self) -> GuiFramework:
        return GuiFramework.TKINTER

    def get_root_application_menu(self) -> Any:
        return self.get_root_application_gui_menu().menu

    def get_root_application_gui_menu(self) -> TkinterApplicationMenu:
        if not self._menu:
            self.create_application_gui_menu()
        if not self._menu:
            raise RuntimeError("Menu not initialized")
        return self._menu

    def get_root_gui_window(self) -> TkinterGuiWindow:
        if not self._root_gui:
            self.create_root_gui_window()
        if not self._root_gui:
            raise RuntimeError("Root window not initialized")
        return self._root_gui

    def get_root_window(self) -> Union[tk.Tk, tk.Toplevel]:
        return self.get_root_gui_window().window

    def initialize(self) -> bool:
        """Initialize the Tkinter backend.

        Returns:
            bool: True if initialization was successful.
        """
        self._tk = tk
        return True

    def is_available(self) -> bool:
        """Check if Tkinter is available.

        Returns:
            bool: True if Tkinter can be imported, False otherwise.
        """
        try:
            import tkinter as _  # noqa: F401
            return True
        except ImportError:
            return False

    def prompt_user_yes_no(self, title: str, message: str) -> bool:
        import tkinter.messagebox
        return tkinter.messagebox.askyesno(title, message)

    def quit_application(self) -> None:
        """Quit the Tkinter application."""
        self.get_root_window().quit()

    def reroute_excepthook(self, callback: Callable[..., Any]) -> None:
        self.get_backend().report_callback_exception = callback

    def run_main_loop(self, window: Any = None) -> None:
        """Start the Tkinter main loop."""
        window = window or self._root_gui
        if not isinstance(window, TkinterGuiWindow):
            raise TypeError("Expected a TkinterGuiWindow instance")

        window.window.mainloop()

    def schedule_event(self, delay_ms: int, callback: Callable[..., Any], **kwargs) -> Union[int, str]:
        """Schedule a callback to be called after a delay in milliseconds."""
        return self.get_root_window().after(delay_ms, callback, **kwargs)

    def set_icon(self, icon_path: str) -> None:
        """Set the application icon for the Tkinter root window."""
        self.get_root_gui_window().set_icon(icon_path)

    def set_title(self, title: str) -> None:
        """Set the application window title.

        Args:
            title: The new window title.
        """
        self.get_root_window().title(title)

    def setup_keybinds(self, **kwargs) -> None:
        """Setup default keybindings for the Tkinter application."""
        pass  # TODO: Implement default keybindings if needed

    def subscribe_to_window_change_event(self, callback: Callable[..., Any]) -> None:
        """Subscribe to the window change event."""
        self.get_root_window().bind("<Configure>", lambda event: callback())

    def subscribe_to_window_close_event(self, callback: Callable[..., Any]) -> None:
        """Subscribe to the window close event."""
        self.get_root_window().protocol("WM_DELETE_WINDOW", callback)

    def update_cursor(self, cursor: str) -> None:
        """Update the cursor for this Application.

        This method changes the cursor style for the main application window.

        Args:
            cursor: The cursor style to set.

        Raises:
            TypeError: If cursor is not a string.
        """
        if not isinstance(cursor, str):
            raise TypeError('Cursor must be a string representing a valid cursor type.')
        self.get_root_window().config(cursor=cursor)

    def update_framekwork_tasks(self) -> None:
        """Update the framework-specific background tasks, if any.
        i.e. Tkinter.Tk.update_idletasks() to update all background tasks.
        """
        self.get_root_window().update_idletasks()


GuiManager.register_backend(GuiFramework.TKINTER, TkinterBackend)

"""GUI backend abstract base class.

This module provides abstract base classes and implementations for different GUI backends,
allowing the framework to support multiple GUI frameworks through a unified interface.
"""
from typing import Any, Callable, Union

from pyrox.interfaces import (
    GuiFramework,
    IApplicationGuiMenu,
    IGuiBackend,
    IGuiFrame,
    IGuiMenu,
    IGuiWindow,
)
from pyrox.services import GuiManager


class ConsoleBackend(IGuiBackend):
    """Console/headless backend for non-GUI operations.

    This backend implements the GuiBackend interface but does not provide any GUI functionality.
    It is intended for use in environments where a GUI is not available or needed.
    """
    key_bindings: dict[str, Callable[..., Any]] = {}

    @property
    def framework_name(self) -> str:
        return "Console"

    def bind_hotkey(
        self,
        hotkey: str,
        callback: Any,
        **kwargs
    ) -> None:
        ConsoleBackend.key_bindings[hotkey] = callback

    def cancel_scheduled_event(self, event_id: int | str) -> None:
        raise NotImplementedError("Console backend does not support cancelling scheduled events")

    def config_from_env(self, **kwargs) -> None:
        print("Console backend: No GUI to configure from environment.")

    def create_application_gui_menu(self, **kwargs) -> IApplicationGuiMenu:
        raise NotImplementedError("Console backend does not support application menu creation")

    def create_gui_frame(self, **kwargs) -> IGuiFrame:
        raise NotImplementedError("Console backend does not support frame creation")

    def create_gui_menu(self, **kwargs) -> IGuiMenu:
        raise NotImplementedError("Console backend does not support menu creation")

    def create_gui_window(self, **kwargs) -> IGuiWindow:
        """Console mode has no loading bar."""
        raise NotImplementedError("Console backend does not support window creation")

    def create_root_gui_window(self, **kwargs) -> IGuiWindow:
        """Console mode has no window."""
        raise NotImplementedError("Console backend does not support window creation")

    def destroy_gui_frame(self, frame: IGuiFrame) -> None:
        raise NotImplementedError("Console backend does not support frame destruction")

    def destroy_gui_menu(self, menu: IGuiMenu) -> None:
        raise NotImplementedError("Console backend does not support menu destruction")

    def destroy_gui_window(self, window, **kwargs) -> None:
        raise NotImplementedError("Console backend does not support window destruction")

    def get_backend(self) -> Any:
        return None  # Console has no static backend manager class to interact with, unlike Tkinter which has 'Tk'.

    def get_framework(self) -> GuiFramework:
        return GuiFramework.CONSOLE

    def get_root_application_menu(self) -> Any:
        raise NotImplementedError("Console backend does not support application menu retrieval")

    def get_root_application_gui_menu(self) -> IApplicationGuiMenu:
        raise NotImplementedError("Console backend does not support application menu retrieval")

    def get_root_gui_window(self) -> Any:
        return None

    def get_root_window(self) -> Any:
        return None

    def initialize(self) -> bool:
        """Initialize console backend (always successful)."""
        return True

    def is_available(self) -> bool:
        """Console is always available."""
        return True

    def prompt_user_yes_no(
        self,
        title: str,
        message: str
    ) -> bool:
        print(f"{title}\n{message} (y/n): ", end='')
        return input().strip().lower() in ('y', 'yes')

    def quit_application(self) -> None:
        """Console mode quit (no-op)."""
        import sys
        sys.exit(0)

    def reroute_excepthook(self, callback: Callable[..., Any]) -> None:
        pass

    def run_main_loop(self, window: Any = None) -> None:
        """Console mode main loop (no-op)."""
        pass

    def schedule_event(
        self,
        delay_ms: int,
        callback: Callable[..., Any],
        **kwargs
    ) -> Union[int, str]:
        import time
        import threading

        def delayed_call():
            time.sleep(delay_ms / 1000.0)
            callback(**kwargs)
        thread = threading.Thread(target=delayed_call)
        thread.start()
        return f"console-scheduled-event-{id(thread)}"

    def set_icon(self, icon_path: str) -> None:
        raise NotImplementedError("Console backend does not support setting an app icon")

    def set_title(self, title: str) -> None:
        print(f"Console backend: Setting title to '{title}' (no GUI effect).")

    def setup_keybinds(self, **kwargs) -> None:
        pass

    def subscribe_to_window_change_event(self, callback: Callable[..., Any]) -> None:
        pass

    def subscribe_to_window_close_event(self, callback: Callable[..., Any]) -> None:
        pass

    def update_cursor(self, cursor: str) -> None:
        pass

    def update_framekwork_tasks(self) -> None:
        pass


GuiManager.register_backend(GuiFramework.CONSOLE, ConsoleBackend)

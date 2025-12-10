"""Gui Backend Interface Module.
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Union
from .frame import IGuiFrame
from .menu import IGuiMenu, IApplicationGuiMenu
from .window import IGuiWindow
from .meta import GuiFramework


class IGuiBackend(ABC):
    """Interface for GUI backend implementations.

    This interface defines the contract that all GUI backend implementations
    must follow, providing a framework-agnostic way to interact with different
    GUI libraries while eliminating circular dependencies.
    """

    @property
    @abstractmethod
    def framework_name(self) -> str:
        """Get the framework name.

        Returns:
            str: The name of the GUI framework this backend supports.
        """
        raise NotImplementedError("framework_name property not implemented.")

    @property
    @abstractmethod
    def framework(self) -> GuiFramework:
        """Get the framework enum.

        Returns:
            GuiFramework: The framework enum value.
        """
        raise NotImplementedError("framework property must be implemented by subclass.")

    @abstractmethod
    def bind_hotkey(self, hotkey: str, callback: Callable, **kwargs) -> None:
        """Bind a global hotkey to a callback.

        Args:
            hotkey: The hotkey string (e.g., '<Control-s>').
            callback: Function to call when hotkey is pressed.
            **kwargs: Additional binding parameters.
        """
        raise NotImplementedError("bind_hotkey method must be implemented by subclass.")

    @abstractmethod
    def cancel_scheduled_event(self, event_id: Union[int, str]) -> None:
        """Cancel a previously scheduled event.

        Args:
            event_id: The identifier of the scheduled event to cancel.
        """
        raise NotImplementedError("cancel_scheduled_event method must be implemented by subclass.")

    @abstractmethod
    def config_from_env(self) -> None:
        """Configure the backend using environment settings."""
        raise NotImplementedError("config_from_env method must be implemented by subclass.")

    @abstractmethod
    def create_application_gui_menu(self, **kwargs) -> IApplicationGuiMenu:
        """Create an application menu.

        Args:
            **kwargs: Menu creation parameters.

        Returns:
            IApplicationMenu: The created application menu.
        """
        raise NotImplementedError("create_application_gui_menu method must be implemented by subclass.")

    @abstractmethod
    def create_gui_frame(self, **kwargs) -> IGuiFrame:
        """Create a new frame/container.

        Args:
            **kwargs: Frame creation parameters.

        Returns:
            IGuiFrame: The created frame.
        """
        raise NotImplementedError("create_gui_frame method must be implemented by subclass.")

    @abstractmethod
    def create_gui_menu(self, **kwargs) -> IGuiMenu:
        """Create a new menu.

        Args:
            **kwargs: Menu creation parameters.

        Returns:
            IGuiMenu: The created menu.
        """
        raise NotImplementedError("create_gui_menu method must be implemented by subclass.")

    @abstractmethod
    def create_gui_window(self, **kwargs) -> IGuiWindow:
        """Create a new window.

        Args:
            **kwargs: Window creation parameters.

        Returns:
            IGuiWindow: The created window.
        """
        raise NotImplementedError("create_gui_window method must be implemented by subclass.")

    @abstractmethod
    def create_root_gui_window(self, **kwargs) -> IGuiWindow:
        """Create the application root window.

        Args:
            **kwargs: Window creation parameters.

        Returns:
            IGuiWindow: The created root window.
        """
        raise NotImplementedError("create_root_gui_window method must be implemented by subclass.")

    @abstractmethod
    def destroy_gui_frame(self, frame: IGuiFrame) -> None:
        """Destroy a GUI frame.

        Args:
            frame: The frame to destroy.
        """
        raise NotImplementedError("destroy_gui_frame method must be implemented by subclass.")

    @abstractmethod
    def destroy_gui_menu(self, menu: IGuiMenu) -> None:
        """Destroy a GUI menu.

        Args:
            menu: The menu to destroy.
        """
        raise NotImplementedError("destroy_gui_menu method must be implemented by subclass.")

    @abstractmethod
    def destroy_gui_window(self, window: IGuiWindow) -> None:
        """Destroy a GUI window.

        Args:
            window: The window to destroy.
        """
        raise NotImplementedError("destroy_gui_window method must be implemented by subclass.")

    @abstractmethod
    def get_backend(self) -> Any:
        """Get the underlying GUI backend instance.

        Returns:
            Any: The GUI backend instance specific to the framework.
        """
        raise NotImplementedError("get_backend method must be implemented by subclass.")

    @abstractmethod
    def get_root_application_menu(self) -> Any:
        """Get the root application menu.

        Returns:
            Any: The root application menu instance.
        """
        raise NotImplementedError("get_root_application_menu method must be implemented by subclass.")

    @abstractmethod
    def get_root_application_gui_menu(self) -> IApplicationGuiMenu:
        """Get the root application menu.

        Returns:
            IApplicationMenu: The root application menu instance.
        """
        raise NotImplementedError("get_root_application_gui_menu method must be implemented by subclass.")

    @abstractmethod
    def get_root_gui_window(self) -> IGuiWindow:
        """Get the root GUI window.

        Returns:
            IGuiWindow: The root window instance.
        """
        raise NotImplementedError("get_root_gui_window method must be implemented by subclass.")

    @abstractmethod
    def get_root_window(self) -> Any:
        """Get the underlying root window object.

        Returns:
            Any: The root window object specific to the GUI framework.
        """
        raise NotImplementedError("get_root_window method must be implemented by subclass.")

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the GUI backend.

        Returns:
            bool: True if initialization was successful.
        """
        raise NotImplementedError("initialize method must be implemented by subclass.")

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend is available on this system.

        Returns:
            bool: True if the backend can be used, False otherwise.
        """
        raise NotImplementedError("is_available method must be implemented by subclass.")

    @abstractmethod
    def prompt_user_yes_no(self, title: str, message: str) -> bool:
        """Show a yes/no dialog to the user.

        Args:
            title: Dialog title.
            message: Dialog message.

        Returns:
            bool: True if user clicked Yes, False for No.
        """
        raise NotImplementedError("prompt_user_yes_no method must be implemented by subclass.")

    @abstractmethod
    def quit_application(self) -> None:
        """Quit the GUI application."""
        raise NotImplementedError("quit_application method must be implemented by subclass.")

    @abstractmethod
    def reroute_excepthook(self, callback: Callable[..., Any]) -> None:
        """Reroute uncaught exceptions to a custom handler.

        Args:
            callback: Function to call on uncaught exceptions.
        """
        raise NotImplementedError("reroute_excepthook method must be implemented by subclass.")

    @abstractmethod
    def run_main_loop(self, window: Optional[IGuiWindow] = None) -> None:
        """Start the GUI main loop.

        Args:
            window: Optional window to run the loop for.
        """
        raise NotImplementedError("run_main_loop method must be implemented by subclass.")

    @abstractmethod
    def schedule_event(self, delay_ms: int, callback: Callable, **kwargs) -> Union[int, str]:
        """Schedule a callback to be called after a delay.

        Args:
            delay_ms: Delay in milliseconds.
            callback: Function to call.
            **kwargs: Additional arguments for the callback.

        Returns:
            Union[int, str]: An identifier for the scheduled event.
        """
        raise NotImplementedError("schedule_event method must be implemented by subclass.")

    @abstractmethod
    def set_icon(self, icon_path: str) -> None:
        """Set the application icon.

        Args:
            icon_path: Path to the icon file.
        """
        raise NotImplementedError("set_icon method must be implemented by subclass.")

    @abstractmethod
    def set_title(self, title: str) -> None:
        """Set the application window title.

        Args:
            title: The new window title.
        """
        raise NotImplementedError("set_title method must be implemented by subclass.")

    @abstractmethod
    def setup_keybinds(self, **kwargs) -> None:
        """Setup global keybindings.

        Args:
            **kwargs: Keybinding parameters.
        """
        raise NotImplementedError("setup_keybinds method must be implemented by subclass.")

    @abstractmethod
    def subscribe_to_window_change_event(self, callback: Callable[..., Any]) -> None:
        """Subscribe to window change events.

        Args:
            callback: Function to call on window change.
        """
        raise NotImplementedError("subscribe_to_window_change_event method must be implemented by subclass.")

    @abstractmethod
    def subscribe_to_window_close_event(self, callback: Callable[..., Any]) -> None:
        """Subscribe to window close events.

        Args:
            callback: Function to call on window close.
        """
        raise NotImplementedError("subscribe_to_window_close_event method must be implemented by subclass.")

    @abstractmethod
    def update_cursor(self, cursor: str) -> None:
        """Update the application cursor to reflect any changes."""
        raise NotImplementedError("update_cursor method must be implemented by subclass.")

    @abstractmethod
    def update_framekwork_tasks(self) -> None:
        """Update the framework-specific background tasks, if any.
        i.e. Tkinter.Tk.update_idletasks() to update all background tasks.
        """
        raise NotImplementedError("update_framework_tasks method must be implemented by subclass.")

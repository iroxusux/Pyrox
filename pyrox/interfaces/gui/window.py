"""Gui Window Interface Module.
"""
from abc import abstractmethod
from typing import Any, Optional, Tuple
from .frame import IGuiFrame


class IGuiWindow(IGuiFrame):
    """Interface for GUI windows.

    Extends IGuiFrame with window-specific functionality such as
    title management and window lifecycle events.
    """

    @property
    def root(self) -> Any:
        """Get the underlying gui object.

        Returns:
            Any: The gui object specific to the GUI framework.
        """
        return self.window

    @root.setter
    def root(self, value: Any) -> None:
        """Set the underlying gui object.

        Args:
            value: The gui object specific to the GUI framework.
        """
        self.window = value

    @property
    def frame(self) -> Any:
        """Get the underlying frame object.

        Returns:
            Any: The frame object specific to the GUI framework.
        """
        return self.window

    @frame.setter
    def frame(self, value: Any) -> None:
        """Set the underlying frame object.

        Args:
            value: The frame object specific to the GUI framework.
        """
        self.window = value

    @property
    @abstractmethod
    def window(self) -> Any:
        """Get the underlying window object.

        Returns:
            Any: The window object specific to the GUI framework.
        """
        raise NotImplementedError("window property must be implemented by subclass.")

    @window.setter
    @abstractmethod
    def window(self, value: Any) -> None:
        """Set the underlying window object.

        Args:
            value: The window object specific to the GUI framework.
        """
        raise NotImplementedError("window setter must be implemented by subclass.")

    @abstractmethod
    def center_on_screen(self) -> None:
        """Center the window on the screen."""
        raise NotImplementedError("center_on_screen method must be implemented by subclass.")

    @abstractmethod
    def close(self) -> None:
        """Close the window."""
        raise NotImplementedError("close method must be implemented by subclass.")

    @abstractmethod
    def get_position(self) -> Tuple[int, int]:
        """Get the window position.

        Returns:
            (int, int): The x and y position of the window in pixels.
        """
        raise NotImplementedError("get_position method must be implemented by subclass.")

    @abstractmethod
    def get_size(self) -> Tuple[int, int]:
        """Get the window size.

        Returns:
            (int, int): The width and height of the window in pixels.
        """
        raise NotImplementedError("get_size method must be implemented by subclass.")

    @abstractmethod
    def get_state(self) -> str:
        """Get the window state.

        Returns:
            str: The current window state (e.g., 'normal', 'iconic', 'zoomed').
        """
        raise NotImplementedError("get_state method must be implemented by subclass.")

    @abstractmethod
    def get_title(self) -> str:
        """Get the window title.

        Returns:
            str: The current window title.
        """
        raise NotImplementedError("get_title method must be implemented by subclass.")

    @abstractmethod
    def is_fullscreen(self) -> bool:
        """Check if the window is in fullscreen mode.

        Returns:
            bool: True if fullscreen, False otherwise.
        """
        raise NotImplementedError("is_fullscreen method must be implemented by subclass.")

    @abstractmethod
    def set_fullscreen(self, fullscreen: bool) -> None:
        """Set the window to fullscreen or windowed mode.

        Args:
            fullscreen: True for fullscreen, False for windowed.
        """
        raise NotImplementedError("set_fullscreen method must be implemented by subclass.")

    @abstractmethod
    def set_geometry(self, width: int, height: int, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """Set the window geometry.

        Args:
            width: Window width in pixels.
            height: Window height in pixels.
            x: Optional x position.
            y: Optional y position.
        """
        raise NotImplementedError("set_geometry method must be implemented by subclass.")

    @abstractmethod
    def set_icon(self, icon_path: str) -> None:
        """Set the window icon.

        Args:
            icon_path: Path to the icon file.
        """
        raise NotImplementedError("set_icon method must be implemented by subclass.")

    @abstractmethod
    def set_position(self, x: int, y: int) -> None:
        """Set the window position.

        Args:
            x: The x position in pixels.
            y: The y position in pixels.
        """
        raise NotImplementedError("set_position method must be implemented by subclass.")

    @abstractmethod
    def set_resizable(self, resizable: bool) -> None:
        """Set whether the window can be resized.

        Args:
            resizable: True to allow resizing, False to prevent it.
        """
        raise NotImplementedError("set_resizable method must be implemented by subclass.")

    @abstractmethod
    def set_size(self, width: int, height: int) -> None:
        """Set the window size.

        Args:
            width: The width in pixels.
            height: The height in pixels.
        """
        raise NotImplementedError("set_size method must be implemented by subclass.")

    @abstractmethod
    def set_state(self, state: str) -> None:
        """Set the window state.

        Args:
            state: The desired window state (e.g., 'normal', 'iconic', 'zoomed').
        """
        raise NotImplementedError("set_state method must be implemented by subclass.")

    @abstractmethod
    def set_title(self, title: str) -> None:
        """Set the window title.

        Args:
            title: The title to set.
        """
        raise NotImplementedError("set_title method must be implemented by subclass.")

"""Gui Window Interface Module.
"""
from abc import abstractmethod
from typing import Generic, Optional, TypeVar, Tuple
from .frame import IGuiFrame

T = TypeVar('T')
W = TypeVar('W')


class IGuiWindow(
    Generic[T, W],
    IGuiFrame[T, W]
):
    """Interface for GUI windows.

    Extends IGuiFrame with window-specific functionality such as
    title management and window lifecycle events.
    """

    @abstractmethod
    def center_on_screen(self) -> None:
        """Center the window on the screen."""
        raise NotImplementedError("center_on_screen method must be implemented by subclass.")

    @abstractmethod
    def close(self) -> None:
        """Close the window."""
        raise NotImplementedError("close method must be implemented by subclass.")

    @property
    def position(self) -> Tuple[int, int]:
        """Get the window position.

        Returns:
            (int, int): The x and y position of the window in pixels.
        """
        return self.get_position()

    @position.setter
    def position(self, value: Tuple[int, int]) -> None:
        """Set the window position.

        Args:
            value: A tuple of (x, y) position in pixels.
        """
        self.set_position(value[0], value[1])

    @abstractmethod
    def get_position(self) -> Tuple[int, int]:
        """Get the window position.

        Returns:
            (int, int): The x and y position of the window in pixels.
        """
        raise NotImplementedError("get_position method must be implemented by subclass.")

    @abstractmethod
    def set_position(self, x: int, y: int) -> None:
        """Set the window position.

        Args:
            x: The x position in pixels.
            y: The y position in pixels.
        """
        raise NotImplementedError("set_position method must be implemented by subclass.")

    @property
    def size(self) -> Tuple[int, int]:
        """Get the window size.

        Returns:
            (int, int): The width and height of the window in pixels.
        """
        return self.get_size()

    @size.setter
    def size(self, value: Tuple[int, int]) -> None:
        """Set the window size.

        Args:
            value: A tuple of (width, height) in pixels.
        """
        self.set_size(value[0], value[1])

    @abstractmethod
    def get_size(self) -> Tuple[int, int]:
        """Get the window size.

        Returns:
            (int, int): The width and height of the window in pixels.
        """
        raise NotImplementedError("get_size method must be implemented by subclass.")

    @abstractmethod
    def set_size(self, width: int, height: int) -> None:
        """Set the window size.

        Args:
            width: The width in pixels.
            height: The height in pixels.
        """
        raise NotImplementedError("set_size method must be implemented by subclass.")

    @property
    def state(self) -> str:
        """Get the window state.

        Returns:
            str: The current window state (e.g., 'normal', 'iconic', 'zoomed').
        """
        return self.get_state()

    @state.setter
    def state(self, value: str) -> None:
        """Set the window state.

        Args:
            value: The desired window state (e.g., 'normal', 'iconic', 'zoomed').
        """
        self.set_state(value)

    @abstractmethod
    def get_state(self) -> str:
        """Get the window state.

        Returns:
            str: The current window state (e.g., 'normal', 'iconic', 'zoomed').
        """
        raise NotImplementedError("get_state method must be implemented by subclass.")

    @abstractmethod
    def set_state(self, state: str) -> None:
        """Set the window state.

        Args:
            state: The desired window state (e.g., 'normal', 'iconic', 'zoomed').
        """
        raise NotImplementedError("set_state method must be implemented by subclass.")

    @property
    def title(self) -> str:
        """Get the window title.

        Returns:
            str: The current window title.
        """
        return self.get_title()

    @title.setter
    def title(self, value: str) -> None:
        """Set the window title.

        Args:
            value: The title to set.
        """
        self.set_title(value)

    @abstractmethod
    def get_title(self) -> str:
        """Get the window title.

        Returns:
            str: The current window title.
        """
        raise NotImplementedError("get_title method must be implemented by subclass.")

    @abstractmethod
    def set_title(self, title: str) -> None:
        """Set the window title.

        Args:
            title: The title to set.
        """
        raise NotImplementedError("set_title method must be implemented by subclass.")

    @property
    def fullscreen(self) -> bool:
        """Check if the window is in fullscreen mode.

        Returns:
            bool: True if fullscreen, False otherwise.
        """
        return self.is_fullscreen()

    @fullscreen.setter
    def fullscreen(self, value: bool) -> None:
        """Set the window to fullscreen or windowed mode.

        Args:
            value: True for fullscreen, False for windowed.
        """
        self.set_fullscreen(value)

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
    def set_resizable(self, resizable: bool) -> None:
        """Set whether the window can be resized.

        Args:
            resizable: True to allow resizing, False to prevent it.
        """
        raise NotImplementedError("set_resizable method must be implemented by subclass.")

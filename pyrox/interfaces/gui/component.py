"""Gui Component Interface Module.
"""
from abc import ABC, abstractmethod
from typing import Any


class IGuiComponent(ABC):
    """Base interface for all GUI components.

    Provides common functionality that all GUI elements should support,
    such as visibility, dimensions, and event handling.
    """

    @property
    def root(self) -> Any:
        """Get the underlying gui object.

        Returns:
            Any: The gui object specific to the GUI framework.
        """
        return self.get_root()

    @root.setter
    def root(self, value: Any) -> None:
        """Set the underlying gui object.

        Args:
            value: The gui object specific to the GUI framework.
        """
        return self.set_root(value)

    @abstractmethod
    def config(self, **kwargs) -> None:
        """Configure the component with given parameters.

        Args:
            **kwargs: Configuration parameters.
        """
        raise NotImplementedError("config method must be implemented by subclass.")

    @abstractmethod
    def destroy(self) -> None:
        """Destroy the component and free resources."""
        raise NotImplementedError("destroy method must be implemented by subclass.")

    @abstractmethod
    def get_root(self) -> Any:
        """Get the root GUI object.

        Returns:
            Any: The root GUI object.
        """
        raise NotImplementedError("get_root method must be implemented by subclass.")

    @abstractmethod
    def set_root(self, root: Any) -> None:
        """Set the root GUI object.

        Args:
            root: The root GUI object.
        """
        raise NotImplementedError("set_root method must be implemented by subclass.")

    @abstractmethod
    def get_height(self) -> int:
        """Get the height of the component.

        Returns:
            int: The height in pixels, or -1 if not available.
        """
        raise NotImplementedError("get_height method must be implemented by subclass.")

    @abstractmethod
    def get_width(self) -> int:
        """Get the width of the component.

        Returns:
            int: The width in pixels, or -1 if not available.
        """
        raise NotImplementedError("get_width method must be implemented by subclass.")

    @abstractmethod
    def get_x(self) -> int:
        """Get the x position of the component.

        Returns:
            int: The x position in pixels, or -1 if not available.
        """
        raise NotImplementedError("get_x method must be implemented by subclass.")

    @abstractmethod
    def get_y(self) -> int:
        """Get the y position of the component.

        Returns:
            int: The y position in pixels, or -1 if not available.
        """
        raise NotImplementedError("get_y method must be implemented by subclass.")

    @abstractmethod
    def initialize(self, **kwargs) -> bool:
        """Initialize the component.

        Args:
            **kwargs: Initialization parameters.

        Returns:
            bool: True if initialization was successful.
        """
        raise NotImplementedError("initialize method must be implemented by subclass.")

    @abstractmethod
    def is_visible(self) -> bool:
        """Check if the component is visible.

        Returns:
            bool: True if visible, False otherwise.
        """
        raise NotImplementedError("is_visible method must be implemented by subclass.")

    @abstractmethod
    def set_visible(self, visible: bool) -> None:
        """Set the visibility of the component.

        Args:
            visible: True to make visible, False to hide.
        """
        raise NotImplementedError("set_visible method must be implemented by subclass.")

    @abstractmethod
    def update(self) -> None:
        """Update the component to reflect any changes."""
        raise NotImplementedError("update method must be implemented by subclass.")


__all__ = ["IGuiComponent"]

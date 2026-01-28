"""Gui Component Interface Module.
"""
from abc import abstractmethod
from typing import Generic, TypeVar
from pyrox.interfaces import INameable

T = TypeVar('T')


class IGuiComponent(
    INameable,
    Generic[T],
):
    """Base interface for all GUI components.

    Provides common functionality that all GUI elements should support,
    such as visibility, dimensions, and event handling.
    """

    @property
    def parent(self) -> T:
        """Get the parent component.

        Returns:
            Any: The parent component.
        """
        return self.get_parent()

    @parent.setter
    def parent(self, value: T) -> None:
        """Set the parent component.

        Args:
            value: The parent component.
        """
        return self.set_parent(value)

    def get_parent(self) -> T:
        """Get the parent component.

        Returns:
            Any: The parent component.
        """
        raise NotImplementedError("get_parent method must be implemented by subclass.")

    def set_parent(self, parent: T) -> None:
        """Set the parent component.

        Args:
            parent: The parent component.
        """
        raise NotImplementedError("set_parent method must be implemented by subclass.")

    @property
    def root(self) -> T:
        """Get the underlying gui object.

        Returns:
            Any: The gui object specific to the GUI framework.
        """
        return self.get_root()

    @root.setter
    def root(self, value: T) -> None:
        """Set the underlying gui object.

        Args:
            value: The gui object specific to the GUI framework.
        """
        return self.set_root(value)

    @abstractmethod
    def get_root(self) -> T:
        """Get the root GUI object.

        Returns:
            Any: The root GUI object.
        """
        raise NotImplementedError("get_root method must be implemented by subclass.")

    @abstractmethod
    def set_root(self, root: T) -> None:
        """Set the root GUI object.

        Args:
            root: The root GUI object.
        """
        raise NotImplementedError("set_root method must be implemented by subclass.")

    @abstractmethod
    def config(self, *args, **kwargs) -> None:
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
    def focus(self) -> None:
        """Set focus to the component."""
        raise NotImplementedError("focus method must be implemented by subclass.")

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

    @property
    def height(self) -> int:
        """Get the height of the widget.

        Returns:
            int: The height in pixels, or -1 if not available.
        """
        return self.get_height()

    @abstractmethod
    def get_height(self) -> int:
        """Get the height of the component.

        Returns:
            int: The height in pixels, or -1 if not available.
        """
        raise NotImplementedError("get_height method must be implemented by subclass.")

    @property
    def width(self) -> int:
        """Get the width of the widget.

        Returns:
            int: The width in pixels, or -1 if not available.
        """
        return self.get_width()

    @abstractmethod
    def get_width(self) -> int:
        """Get the width of the component.

        Returns:
            int: The width in pixels, or -1 if not available.
        """
        raise NotImplementedError("get_width method must be implemented by subclass.")

    @property
    def x(self) -> int:
        """Get the x position of the widget.

        Returns:
            int: The x position in pixels, or -1 if not available.
        """
        return self.get_x()

    @abstractmethod
    def get_x(self) -> int:
        """Get the x position of the component.

        Returns:
            int: The x position in pixels, or -1 if not available.
        """
        raise NotImplementedError("get_x method must be implemented by subclass.")

    @property
    def y(self) -> int:
        """Get the y position of the widget.

        Returns:
            int: The y position in pixels, or -1 if not available.
        """
        return self.get_y()

    @abstractmethod
    def get_y(self) -> int:
        """Get the y position of the component.

        Returns:
            int: The y position in pixels, or -1 if not available.
        """
        raise NotImplementedError("get_y method must be implemented by subclass.")


__all__ = ["IGuiComponent"]

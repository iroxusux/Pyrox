"""Gui Frame Interface Module.
"""
from abc import abstractmethod
from typing import Callable, Generic, List, TypeVar
from .widget import IGuiWidget

T = TypeVar('T')
W = TypeVar('W')


class IGuiFrame(
    Generic[T, W],
    IGuiWidget[T]
):
    """Interface for GUI frames/containers.

    Provides functionality for container widgets that can hold other
    GUI components with layout management capabilities.
    """

    @abstractmethod
    def add_child(self, child: W) -> None:
        """Add a child component to the frame.

        Args:
            child: The component to add.
        """
        raise NotImplementedError("add_child method must be implemented by subclass.")

    @abstractmethod
    def clear_children(self) -> None:
        """Remove all child components."""
        raise NotImplementedError("clear_children method must be implemented by subclass.")

    @abstractmethod
    def get_children(self) -> List[W]:
        """Get all child components.

        Returns:
            List[IGuiComponent]: List of child components.
        """
        raise NotImplementedError("get_children method must be implemented by subclass.")

    @abstractmethod
    def remove_child(self, child: W) -> None:
        """Remove a child component from the frame.

        Args:
            child: The component to remove.
        """
        raise NotImplementedError("remove_child method must be implemented by subclass.")


class ITaskFrame(
    Generic[T, W],
    IGuiFrame[T, W]
):
    """Interface for task frames.

    Provides functionality specific to frames that represent tasks
    within the application.
    """

    @property
    def shown(self) -> bool:
        """Get or set the shown state of the task frame."""
        return self.get_shown()

    @shown.setter
    def shown(self, value: bool) -> None:
        """Set the shown state of the task frame."""
        self.set_shown(value)

    @abstractmethod
    def build(self) -> None:
        """Build the task frame UI components."""
        raise NotImplementedError("build method must be implemented by subclass.")

    @abstractmethod
    def destroy(self) -> None:
        """Destroy the task frame and clean up resources."""
        raise NotImplementedError("destroy method must be implemented by subclass.")

    @abstractmethod
    def on_destroy(self) -> List[Callable]:
        """Get the list of destroy callbacks.

        Returns:
            list[callable]: List of functions to call when the frame is destroyed.
        """
        raise NotImplementedError("on_destroy property must be implemented by subclass.")

    @abstractmethod
    def get_shown(self) -> bool:
        """Get the shown state of the task frame.

        Returns:
            bool: True if the task frame is shown, False otherwise.
        """
        raise NotImplementedError("shown property must be implemented by subclass.")

    @abstractmethod
    def set_shown(self, value: bool) -> None:
        """Set the shown state of the task frame.

        Args:
            value (bool): True to mark the frame as shown, False to mark as hidden.
        """
        raise NotImplementedError("shown property must be implemented by subclass.")

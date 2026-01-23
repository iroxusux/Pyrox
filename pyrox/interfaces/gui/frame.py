"""Gui Frame Interface Module.
"""
from abc import abstractmethod
from typing import Generic, List, TypeVar
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

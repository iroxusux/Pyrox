"""Gui Frame Interface Module.
"""
from abc import abstractmethod
from typing import Any, List
from .widget import IGuiWidget


class IGuiFrame(IGuiWidget):
    """Interface for GUI frames/containers.

    Provides functionality for container widgets that can hold other
    GUI components with layout management capabilities.
    """

    @property
    @abstractmethod
    def frame(self) -> Any:
        """Get the underlying frame object.

        Returns:
            Any: The frame object specific to the GUI framework.
        """
        raise NotImplementedError("frame property must be implemented by subclass.")

    @frame.setter
    @abstractmethod
    def frame(self, value: Any) -> None:
        """Set the underlying frame object.

        Args:
            value: The frame object specific to the GUI framework.
        """
        raise NotImplementedError("frame setter must be implemented by subclass.")

    @property
    def root(self) -> Any:
        """Get the underlying gui object.

        Returns:
            Any: The gui object specific to the GUI framework.
        """
        return self.frame

    @root.setter
    def root(self, value: Any) -> None:
        """Set the underlying gui object.

        Args:
            value: The gui object specific to the GUI framework.
        """
        self.frame = value

    @abstractmethod
    def add_child(self, child: IGuiWidget) -> None:
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
    def get_children(self) -> List[IGuiWidget]:
        """Get all child components.

        Returns:
            List[IGuiComponent]: List of child components.
        """
        raise NotImplementedError("get_children method must be implemented by subclass.")

    @abstractmethod
    def remove_child(self, child: IGuiWidget) -> None:
        """Remove a child component from the frame.

        Args:
            child: The component to remove.
        """
        raise NotImplementedError("remove_child method must be implemented by subclass.")

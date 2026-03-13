"""Gui Frame Interface Module.
"""
from abc import abstractmethod
from typing import Callable, Protocol, runtime_checkable
from pyrox.interfaces.protocols import INameable


@runtime_checkable
class ITaskFrame(
    INameable,
    Protocol
):
    """Interface for task frames.

    Provides functionality specific to frames that represent tasks
    within the application.
    """

    @abstractmethod
    def build(self) -> None:
        """Build the task frame UI components."""
        raise NotImplementedError("build method must be implemented by subclass.")

    @abstractmethod
    def destroy(self) -> None:
        """Destroy the task frame and clean up resources."""
        raise NotImplementedError("destroy method must be implemented by subclass.")

    @abstractmethod
    def on_destroy(self) -> list[Callable]:
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

    @abstractmethod
    def get_root(self):
        """Get the root widget of the task frame.

        Returns:
            The root widget of the task frame.
        """
        raise NotImplementedError("get_root method must be implemented by subclass.")

    @property
    def shown(self) -> bool:
        """Get or set the shown state of the task frame."""
        return self.get_shown()

    @shown.setter
    def shown(self, value: bool) -> None:
        """Set the shown state of the task frame."""
        self.set_shown(value)

    @property
    def root(self):
        """Get the root widget of the task frame."""
        return self.get_root()

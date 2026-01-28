"""Tkinter user-made frames.

This module provides frame implementations for the Pyrox GUI framework,
including abstract base classes and concrete implementations for task frames
and other specialized frame types.
"""
from __future__ import annotations
from typing import Callable, Generic, TypeVar
from pyrox.interfaces import IGuiFrame, ITaskFrame
from .widget import GuiWidget

T = TypeVar('T')
W = TypeVar('W')


class GuiFrame(
    GuiWidget[T],
    IGuiFrame[T, W],
    Generic[T, W],
):
    """Base implementation of GuiFrame.
    """

    def add_child(self, child: W) -> None:
        raise NotImplementedError("add_child method must be implemented by subclass.")

    def clear_children(self) -> None:
        raise NotImplementedError("clear_children method must be implemented by subclass.")

    def get_children(self) -> list[W]:
        raise NotImplementedError("get_children method must be implemented by subclass.")

    def initialize(self, **kwargs) -> bool:
        raise NotImplementedError("initialize method must be implemented by subclass.")

    def destroy(self) -> None:
        raise NotImplementedError("destroy method must be implemented by subclass.")

    def remove_child(self, child: W) -> None:
        raise NotImplementedError("remove_child method must be implemented by subclass.")


class TaskFrame(
    Generic[T, W],
    GuiFrame[T, W],
    ITaskFrame[T, W],
):
    """A frame for tasks in the application with title bar and close button.

    This frame provides a standardized interface for task windows with
    a title bar containing a close button and title label. It includes
    callback support for cleanup operations when the frame is destroyed.

    Args:
        *args: Variable length argument list passed to Frame.
        name (str, optional): The name/title of the task frame. Defaults to 'Task Frame'.
        **kwargs: Arbitrary keyword arguments passed to Frame.

    Attributes:
        _name (str): The name of the task frame.
        _shown (bool): Whether the frame is currently shown.
        _shown_var (BooleanVar): Tkinter variable tracking the shown state.
        _title_bar (Frame): The title bar frame containing controls.
        _close_button (Button): The close button in the title bar.
        _title_label (Label): The title label in the title bar.
        _content_frame (Frame): The main content area of the frame.
        _on_destroy (list[callable]): List of callbacks to execute on destroy.
    """

    def __init__(
        self,
        name: str,
        parent: T,
    ):
        GuiFrame.__init__(
            self,
            name=name
        )
        self._shown: bool = True
        self._on_destroy: list[Callable] = []

    def build(
        self,
        **kwargs,
    ) -> None:
        """Build the task frame.

        This method can be overridden by subclasses to populate
        the content frame with widgets.
        """
        pass

    def get_shown(self) -> bool:
        """Get the shown state of the task frame.

        Returns:
            bool: True if the task frame is shown, False otherwise.
        """
        return self._shown

    def on_destroy(self) -> list[Callable]:
        """Get the list of destroy callbacks.

        Returns:
            list[callable]: List of functions to call when the frame is destroyed.
        """
        return self._on_destroy

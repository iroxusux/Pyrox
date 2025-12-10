"""Tkinter user-made frames.

This module provides frame implementations for the Pyrox GUI framework,
including abstract base classes and concrete implementations for task frames
and other specialized frame types.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Callable, TypeVar, Generic
from pyrox.services import GuiManager, log
from pyrox.interfaces import IGuiFrame


T = TypeVar('T')


class PyroxFrameContainer(Generic[T]):
    """A custom frame.
    """

    def __init__(
        self,
        **kwargs,
    ) -> None:
        self._frame = GuiManager.unsafe_get_backend().create_gui_frame(**kwargs)

    @property
    def frame(self) -> IGuiFrame:
        """Get the IGuiFrame widget."""
        return self._frame

    @property
    def frame_root(self) -> T:
        """Get the underlying GUI framework frame object."""
        return self._frame.root


class TaskFrame(ttk.Frame):
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
        *args,
        name: str = '',
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._name = name or 'Task Frame'
        self._shown: bool = False
        self._shown_var: tk.BooleanVar = tk.BooleanVar(value=self._shown)
        self._title_bar = ttk.Frame(self, height=20)

        self._close_button = ttk.Button(
            self._title_bar,
            text='X',
            command=self.destroy,
            width=3,
        )
        self._close_button.pack(side=tk.RIGHT, padx=5, pady=5)

        self._title_label = ttk.Label(self._title_bar, text=name or 'Task Frame')
        self._title_label.pack(side=tk.LEFT, padx=5, pady=5)

        self._title_bar.pack(fill=tk.X, side=tk.TOP)

        self._content_frame = ttk.Frame(self)
        self._content_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        self._on_destroy: list[Callable] = []

    @property
    def content_frame(self) -> ttk.Frame:
        """Get the content frame for adding widgets.

        Returns:
            Frame: The main content area where widgets should be added.
        """
        return self._content_frame

    @property
    def name(self) -> str:
        """Get the name of the task frame.

        Returns:
            str: The name/title of the task frame.
        """
        return self._name

    @property
    def on_destroy(self) -> list[Callable]:
        """Get the list of destroy callbacks.

        Returns:
            list[callable]: List of functions to call when the frame is destroyed.
        """
        return self._on_destroy

    @property
    def shown(self) -> bool:
        """Get the shown state of the task frame.

        Returns:
            bool: True if the task frame is shown, False otherwise.
        """
        return self._shown

    @shown.setter
    def shown(self, value: bool):
        """Set the shown state of the task frame.

        Args:
            value (bool): True to mark the frame as shown, False to mark as hidden.

        Raises:
            TypeError: If value is not a boolean.
        """
        if not isinstance(value, bool):
            raise TypeError(f'Expected bool, got {type(value)}')
        self._shown = value

    @property
    def shown_var(self) -> tk.BooleanVar:
        """Get the BooleanVar tracking the shown state.

        Returns:
            BooleanVar: Tkinter variable representing the shown state.
        """
        return self._shown_var

    def build(
        self,
        **kwargs,
    ) -> None:
        """Build the task frame.

        This method can be overridden by subclasses to populate
        the content frame with widgets.
        """
        pass

    def destroy(self):
        """Destroy the task frame and execute all registered callbacks.

        Calls all functions in the on_destroy list before destroying the frame.
        Non-callable items in the list generate warning messages.
        """
        # Execute callbacks first, but handle errors gracefully
        for callback in self._on_destroy:
            if callable(callback):
                try:
                    callback(self)
                except Exception as e:
                    log(self).warning(f'Error in destroy callback: {e}')
                    raise e
            else:
                log(self).warning(f'Callback {callback} is not callable.')

        # Clear callbacks to prevent double execution
        self._on_destroy.clear()

        # Safely destroy the frame
        try:
            return super().destroy()
        except tk.TclError as e:
            log(self).warning(f'TclError during frame destruction (parent may already be destroyed): {e}')

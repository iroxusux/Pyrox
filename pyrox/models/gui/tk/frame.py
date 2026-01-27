"""Tkinter user-made frames.

This module provides frame implementations for the Pyrox GUI framework,
including abstract base classes and concrete implementations for task frames
and other specialized frame types.
"""
from typing import cast, Callable
from tkinter import (
    BooleanVar,
    BOTH,
    RIGHT,
    LEFT,
    TOP,
    X,
    TclError,
)
from tkinter.ttk import (
    Button,
    Frame,
    Label,
    Widget
)

from pyrox.models.gui.default import GuiFrame, TaskFrame
from .widget import TkinterGuiWidget


class TkinterGuiFrame(
    TkinterGuiWidget[Frame],
    GuiFrame[Frame, Widget],
):
    """Tkinter implementation of GuiFrame.

    This class provides a concrete implementation of the GuiFrame interface
    using Tkinter's ttk.Frame widget.
    """

    def add_child(self, child: Widget) -> None:
        pass  # Tkinter frames don't inherintly have children added to them in this fashion.

    def clear_children(self) -> None:
        self.root.children.clear()

    def get_children(self) -> list[Widget]:
        return cast(list[Widget], list(self.root.children.values()))

    def initialize(self, **kwargs) -> bool:
        self.root = Frame(**kwargs)
        return self.root is not None

    def destroy(self) -> None:
        self.root.destroy()
        self._frame = None

    def remove_child(self, child: Widget) -> None:
        self.root.children.pop(child.winfo_name(), None)


class TkinterTaskFrame(
    TkinterGuiFrame,
    TaskFrame[Frame, Widget],
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
        parent: Frame,
    ):
        GuiFrame.__init__(self)
        self.set_parent(parent)
        self.set_root(Frame(self.get_parent()))  # type: ignore  # TODO: Integrate with GuiManager
        self._name = name or 'Task Frame'
        self._shown: bool = False
        self._shown_var: BooleanVar = BooleanVar(value=self._shown)
        self._title_bar = Frame(self.root, height=20)

        self._close_button = Button(
            self._title_bar,
            text='X',
            command=self.destroy,
            width=3,
        )
        self._close_button.pack(side=RIGHT, padx=5, pady=5)

        self._title_label = Label(self._title_bar, text=name or 'Task Frame')
        self._title_label.pack(side=LEFT, padx=5, pady=5)

        self._title_bar.pack(fill=X, side=TOP)

        self._content_frame = Frame(self.root)
        self._content_frame.pack(fill=BOTH, expand=True, side=TOP)

        self._on_destroy: list[Callable] = []

    @property
    def content_frame(self) -> Frame:
        """Get the content frame for adding widgets.

        Returns:
            Frame: The main content area where widgets should be added.
        """
        return self._content_frame

    @property
    def shown_var(self) -> BooleanVar:
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

    def set_shown(self, value: bool) -> None:
        """Set the shown state of the task frame.

        Args:
            value (bool): The new shown state.
        """
        self._shown = value
        self._shown_var.set(value)

    def destroy(self):
        """Destroy the task frame and execute all registered callbacks.

        Calls all functions in the on_destroy list before destroying the frame.
        Non-callable items in the list generate warning messages.
        """
        # Execute callbacks first, but handle errors gracefully
        for callback in self.on_destroy():
            if callable(callback):
                try:
                    callback(self)
                except Exception as e:
                    self.log().warning(f'Error in destroy callback: {e}')
                    raise e
            else:
                self.log().warning(f'Callback {callback} is not callable.')

        # Clear callbacks to prevent double execution
        self.on_destroy().clear()

        # Safely destroy the frame
        try:
            return self.root.destroy()
        except TclError as e:
            self.log().warning(f'TclError during frame destruction (parent may already be destroyed): {e}')

    def on_destroy(self) -> list[Callable]:
        """Get the list of destroy callbacks.

        Returns:
            list[callable]: List of functions to call when the frame is destroyed.
        """
        return self._on_destroy

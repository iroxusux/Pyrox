"""Tkinter user-made frames.

This module provides frame implementations for the Pyrox GUI framework,
including abstract base classes and concrete implementations for task frames
and other specialized frame types.
"""
from typing import cast
from tkinter.ttk import Frame, Widget

from pyrox.models.gui.default import GuiFrame
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

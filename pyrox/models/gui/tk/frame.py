"""Tkinter user-made frames.

This module provides frame implementations for the Pyrox GUI framework,
including abstract base classes and concrete implementations for task frames
and other specialized frame types.
"""
from __future__ import annotations
from tkinter.ttk import Frame

from pyrox.interfaces import IGuiFrame, IGuiWidget
from .widget import TkinterGuiWidget


class TkinterGuiFrame(IGuiFrame, TkinterGuiWidget):
    """Tkinter implementation of GuiFrame.

    This class provides a concrete implementation of the GuiFrame interface
    using Tkinter's ttk.Frame widget.
    """

    @property
    def frame(self) -> Frame:
        """Get the underlying Tkinter frame widget.

        Returns:
            ttk.Frame: The Tkinter frame widget.

        Raises:
            RuntimeError: If the frame has not been created yet.
        """
        if self.widget is None:
            raise RuntimeError('Frame has not been created yet.')
        if not isinstance(self.widget, Frame):
            raise TypeError(f'Expected ttk.Frame, got {type(self.widget)}')
        return self.widget

    @frame.setter
    def frame(self, value: Frame) -> None:
        """Set the underlying Tkinter frame widget.

        Args:
            value (ttk.Frame): The Tkinter frame widget to set.
        """
        if not isinstance(value, Frame):
            raise TypeError(f'Expected ttk.Frame, got {type(value)}')
        self.widget = value

    def add_child(self, child: IGuiWidget) -> None:
        pass  # Tkinter frames don't inherintly have children added to them in this fashion.

    def clear_children(self) -> None:
        self.frame.children.clear()

    def get_children(self) -> list[IGuiWidget]:
        widgets: list[IGuiWidget] = []
        children = self.frame.children
        for child in children.values():
            widget = TkinterGuiWidget()
            widget.initialize(widget=child)
            widgets.append(widget)
        return list(widgets)

    def initialize(self, **kwargs) -> bool:
        self._widget = Frame(**kwargs)
        return self._widget is not None

    def destroy(self) -> None:
        self.frame.destroy()
        self._frame = None

    def remove_child(self, child: IGuiWidget) -> None:
        self.frame.children.pop(child.get_name(), None)

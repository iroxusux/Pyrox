"""GUI widget base class built-in implimentations.
"""
from tkinter import Widget
from typing import Optional
from pyrox.interfaces import IGuiWidget


class TkinterGuiWidget(IGuiWidget):
    """Tkinter implementation of IGuiWidget.
    """

    def __init__(self):
        self._parent = None
        self._widget = None

    @property
    def parent(self) -> Optional[IGuiWidget]:
        return self._parent

    @parent.setter
    def parent(self, value: Optional[IGuiWidget]) -> None:
        self._parent = value

    def get_widget(self) -> Optional[Widget]:
        return self._widget

    def set_widget(self, value: Optional[Widget]) -> None:
        if value and not isinstance(value, Widget):
            raise TypeError(f'Expected tkinter.Widget, got {type(value)}')
        self._widget = value

    def config(self, **kwargs) -> None:
        self.widget.configure(**kwargs)

    def destroy(self) -> None:
        self.widget.destroy()
        self._widget = None

    def disable(self) -> None:
        self.widget.configure({'state': 'disabled'})

    def enable(self) -> None:
        self.widget.configure({'state': 'normal'})

    def focus(self) -> None:
        self.widget.focus_set()

    def get_height(self) -> int:
        return self.widget.winfo_height()

    def get_name(self) -> str:
        return self.widget.winfo_name()

    def get_parent(self) -> Optional[IGuiWidget]:
        return self.parent

    def get_width(self) -> int:
        return self.widget.winfo_width()

    def get_x(self) -> int:
        return self.widget.winfo_x()

    def get_y(self) -> int:
        return self.widget.winfo_y()

    def initialize(self, **kwargs) -> bool:
        self._widget = Widget(**kwargs)
        return self._widget is not None

    def is_visible(self) -> bool:
        return bool(self.widget.winfo_ismapped())

    def pack(self, **kwargs) -> None:
        self.widget.pack(**kwargs)

    def pack_propagate(self, propagate: bool) -> None:
        self.widget.pack_propagate(propagate)

    def set_parent(self, parent: Optional[IGuiWidget]) -> None:
        self.parent = parent

    def set_visible(self, visible: bool) -> None:
        if visible:
            self.widget.pack()
        else:
            self.widget.pack_forget()

    def update(self) -> None:
        self.widget.update()

    def update_idletasks(self) -> None:
        self.widget.update_idletasks()

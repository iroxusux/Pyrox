"""GUI widget base class built-in implimentations.
"""
from typing import Generic, TypeVar
from tkinter import Widget
from pyrox.models.gui.default import GuiWidget
from .component import TkinterGuiComponent

T = TypeVar('T', bound=Widget)


class TkinterGuiWidget(
    Generic[T],
    TkinterGuiComponent[T],
    GuiWidget[T]
):
    """Tkinter implementation of IGuiWidget.
    """

    def config(self, **kwargs) -> None:
        self.root.configure(**kwargs)

    def destroy(self) -> None:
        self.root.destroy()
        self._widget = None

    def disable(self) -> None:
        self.root.configure({'state': 'disabled'})

    def enable(self) -> None:
        self.root.configure({'state': 'normal'})

    def focus(self) -> None:
        self.root.focus_set()

    def initialize(self, **kwargs) -> bool:
        self._widget = Widget(**kwargs)
        return self._widget is not None

    def is_visible(self) -> bool:
        return bool(self.root.winfo_ismapped())

    def pack(self, **kwargs) -> None:
        self.root.pack(**kwargs)

    def pack_propagate(self, propagate: bool) -> None:
        self.root.pack_propagate(propagate)

    def pack_forget(self) -> None:
        self.root.pack_forget()

    def set_visible(self, visible: bool) -> None:
        if visible:
            self.root.pack()
        else:
            self.root.pack_forget()

    def update(self) -> None:
        self.root.update()

    def update_idletasks(self) -> None:
        self.root.update_idletasks()

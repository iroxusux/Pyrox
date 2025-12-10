from typing import Union
from tkinter import Tk, Toplevel
from pyrox.interfaces import IGuiComponent


class TkinterGuiComponent(IGuiComponent):
    """Tkinter implementation of IGuiComponent.
    """

    @property
    def root(self) -> Union[Tk, Toplevel]:
        raise NotImplementedError("root getter must be implemented by subclass.")

    @root.setter
    def root(self, value: Union[Tk, Toplevel]) -> None:
        raise NotImplementedError("root setter must be implemented by subclass.")

from typing import Generic, TypeVar
from tkinter import Misc, BaseWidget
from pyrox.models.gui.default import GuiComponent

T = TypeVar('T', bound=Misc | BaseWidget)


class TkinterGuiComponent(
    Generic[T],
    GuiComponent[T]
):
    """Tkinter implementation of IGuiComponent.
    """

    def destroy(self) -> None:
        self.root.destroy()

    def focus(self) -> None:
        self.root.focus_set()

    def initialize(self, **kwargs) -> bool:
        raise NotImplementedError("initialize method must be implemented by subclass.")

    def is_visible(self) -> bool:
        raise NotImplementedError("is_visible method must be implemented by subclass.")

    def set_visible(self, visible: bool) -> None:
        raise NotImplementedError("set_visible method must be implemented by subclass.")

    def get_height(self) -> int:
        return self.root.winfo_height()

    def get_name(self) -> str:
        return self.root.winfo_name()

    def get_width(self) -> int:
        return self.root.winfo_width()

    def get_x(self) -> int:
        return self.root.winfo_x()

    def get_y(self) -> int:
        return self.root.winfo_y()

    def update(self) -> None:
        raise NotImplementedError("update method must be implemented by subclass.")

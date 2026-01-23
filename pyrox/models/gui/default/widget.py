"""GUI widget base class built-in implimentations.
"""
from typing import Generic, TypeVar
from pyrox.interfaces import IGuiWidget
from .component import GuiComponent

T = TypeVar('T')


class GuiWidget(
    IGuiWidget[T],
    GuiComponent[T],
    Generic[T],
):
    """Base implementation of IGuiWidget.
    """

    def destroy(self) -> None:
        raise NotImplementedError("destroy method must be implemented by subclass.")

    def disable(self) -> None:
        raise NotImplementedError("disable method must be implemented by subclass.")

    def enable(self) -> None:
        raise NotImplementedError("enable method must be implemented by subclass.")

    def initialize(self, **kwargs) -> bool:
        raise NotImplementedError("initialize method must be implemented by subclass.")

    def is_visible(self) -> bool:
        raise NotImplementedError("is_visible method must be implemented by subclass.")

    def pack(self, **kwargs) -> None:
        raise NotImplementedError("pack method must be implemented by subclass.")

    def pack_propagate(self, propagate: bool) -> None:
        raise NotImplementedError("pack_propagate method must be implemented by subclass.")

    def set_visible(self, visible: bool) -> None:
        raise NotImplementedError("set_visible method must be implemented by subclass.")

    def update(self) -> None:
        raise NotImplementedError("update method must be implemented by subclass.")

    def update_idletasks(self) -> None:
        raise NotImplementedError("update_idletasks method must be implemented by subclass.")

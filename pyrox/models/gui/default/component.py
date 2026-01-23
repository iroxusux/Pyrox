from typing import Generic, TypeVar
from pyrox.interfaces import IGuiComponent

T = TypeVar('T')


class GuiComponent(
    Generic[T],
    IGuiComponent[T]
):
    """Base implementation of IGuiComponent.
    """

    def __init__(self):
        self._parent: T
        self._root: T

    def config(self, *args, **kwargs) -> None:
        raise NotImplementedError("config method must be implemented by subclass.")

    def focus(self) -> None:
        raise NotImplementedError("focus method must be implemented by subclass.")

    def get_root(self) -> T:
        return self._root

    def set_root(self, root: T) -> None:
        self._root = root

    def get_parent(self) -> T:
        return self._parent

    def set_parent(self, parent: T) -> None:
        self._parent = parent

    def get_name(self) -> str:
        raise NotImplementedError("get_name method must be implemented by subclass.")

    def set_name(self, name: str) -> None:
        raise NotImplementedError("set_name method must be implemented by subclass.")

    def get_height(self) -> int:
        raise NotImplementedError("get_height method must be implemented by subclass.")

    def get_width(self) -> int:
        raise NotImplementedError("get_width method must be implemented by subclass.")

    def get_x(self) -> int:
        raise NotImplementedError("get_x method must be implemented by subclass.")

    def get_y(self) -> int:
        raise NotImplementedError("get_y method must be implemented by subclass.")

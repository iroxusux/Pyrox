from typing import Generic, TypeVar
from pyrox.interfaces import IGuiComponent
from pyrox.models.services import ServicesRunnableMixin

T = TypeVar('T')


class GuiComponent(
    Generic[T],
    IGuiComponent[T],
    ServicesRunnableMixin,
):
    """Base implementation of IGuiComponent.
    """

    def __init__(
        self,
        name: str = "GuiComponent",
        description: str = "Base GUI Component"
    ) -> None:
        self._parent: T
        self._root: T
        ServicesRunnableMixin.__init__(
            self,
            name=name,
            description=description
        )

    def config(self, *args, **kwargs) -> None:
        raise NotImplementedError("config method must be implemented by subclass.")

    def destroy(self) -> None:
        raise NotImplementedError("destroy method must be implemented by subclass.")

    def focus(self) -> None:
        raise NotImplementedError("focus method must be implemented by subclass.")

    def initialize(self, **kwargs) -> bool:
        raise NotImplementedError("initialize method must be implemented by subclass.")

    def is_visible(self) -> bool:
        raise NotImplementedError("is_visible method must be implemented by subclass.")

    def set_visible(self, visible: bool) -> None:
        raise NotImplementedError("set_visible method must be implemented by subclass.")

    def get_root(self) -> T:
        return self._root

    def set_root(self, root: T) -> None:
        self._root = root

    def get_parent(self) -> T:
        return self._parent

    def set_parent(self, parent: T) -> None:
        self._parent = parent

    def get_height(self) -> int:
        raise NotImplementedError("get_height method must be implemented by subclass.")

    def get_width(self) -> int:
        raise NotImplementedError("get_width method must be implemented by subclass.")

    def get_x(self) -> int:
        raise NotImplementedError("get_x method must be implemented by subclass.")

    def get_y(self) -> int:
        raise NotImplementedError("get_y method must be implemented by subclass.")

    def update(self) -> None:
        raise NotImplementedError("update method must be implemented by subclass.")

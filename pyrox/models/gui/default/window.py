"""GUI window base class built-in implimentations.
"""
from typing import Generic, TypeVar, Tuple
from pyrox.interfaces import IGuiWindow
from .frame import GuiFrame

T = TypeVar('T')
W = TypeVar('W')


class GuiWindow(
    Generic[T, W],
    GuiFrame[T, W],
    IGuiWindow[T, W]
):
    """Base implementation of IGuiWindow.
    """

    def center_on_screen(self) -> None:
        raise NotImplementedError("center_on_screen method must be implemented by subclass.")

    def close(self) -> None:
        raise NotImplementedError("close method must be implemented by subclass.")

    def get_state(self) -> str:
        raise NotImplementedError("get_state method must be implemented by subclass.")

    def get_title(self) -> str:
        raise NotImplementedError("get_title method must be implemented by subclass.")

    def is_fullscreen(self) -> bool:
        raise NotImplementedError("is_fullscreen method must be implemented by subclass.")

    def set_fullscreen(self, fullscreen: bool) -> None:
        raise NotImplementedError("set_fullscreen method must be implemented by subclass.")

    def set_geometry(
        self,
        width: int,
        height: int,
        x: int | None = None,
        y: int | None = None
    ) -> None:
        raise NotImplementedError("set_geometry method must be implemented by subclass.")

    def set_icon(self, icon_path: str) -> None:
        raise NotImplementedError("set_icon method must be implemented by subclass.")

    def get_position(self) -> Tuple[int, int]:
        raise NotImplementedError("get_position method must be implemented by subclass.")

    def set_position(self, x: int, y: int) -> None:
        raise NotImplementedError("set_position method must be implemented by subclass.")

    def set_resizable(self, resizable: bool) -> None:
        raise NotImplementedError("set_resizable method must be implemented by subclass.")

    def get_size(self) -> Tuple[int, int]:
        raise NotImplementedError("get_size method must be implemented by subclass.")

    def set_size(self, width: int, height: int) -> None:
        raise NotImplementedError("set_size method must be implemented by subclass.")

    def set_state(self, state: str) -> None:
        raise NotImplementedError("set_state method must be implemented by subclass.")

    def set_title(self, title: str) -> None:
        raise NotImplementedError("set_title method must be implemented by subclass.")

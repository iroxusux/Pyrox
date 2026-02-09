"""Gui Protocol Interfaces.
"""
from typing import Generic, Optional, Protocol, runtime_checkable, TypeVar


T = TypeVar('T')


@runtime_checkable
class IHasCanvas(
    Generic[T],
    Protocol
):
    def get_canvas(self) -> Optional[T]: ...
    def set_canvas(self, canvas: T) -> None: ...
    @property
    def canvas(self) -> Optional[T]: return self.get_canvas()

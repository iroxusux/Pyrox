"""Gui Protocol Interfaces.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar


T = TypeVar('T')


class IHasCanvas(
    ABC,
    Generic[T],
):
    @abstractmethod
    def get_canvas(self) -> T | None: ...
    @abstractmethod
    def set_canvas(self, canvas: T) -> None: ...
    @property
    @abstractmethod
    def canvas(self) -> T | None: ...

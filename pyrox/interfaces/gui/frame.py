"""Gui Frame Interface Module.
"""
from abc import abstractmethod
from pyrox.interfaces.base import INameable, IDescribable, IBuildable


class ITaskFrame(
    INameable,
    IDescribable,
    IBuildable
):
    """Interface for task frames.

    Provides functionality specific to frames that represent tasks
    within the application.
    """

    @abstractmethod
    def get_shown(self) -> bool: ...

    @abstractmethod
    def set_shown(self, value: bool) -> None: ...

    @abstractmethod
    def get_root(self): ...

    @property
    @abstractmethod
    def shown(self) -> bool: ...

    @shown.setter
    @abstractmethod
    def shown(self, value: bool) -> None: ...

    @property
    @abstractmethod
    def root(self): ...

"""Tkinter user-made frames.

This module provides frame implementations for the Pyrox GUI framework,
including abstract base classes and concrete implementations for task frames
and other specialized frame types.
"""
from __future__ import annotations
from typing import TypeVar, Generic
from pyrox.services import GuiManager
from pyrox.interfaces import IGuiFrame


T = TypeVar('T')


class PyroxFrameContainer(Generic[T]):
    """A custom frame.
    """

    def __init__(
        self,
        **kwargs,
    ) -> None:
        self._frame = GuiManager.unsafe_get_backend().create_gui_frame(**kwargs)

    @property
    def frame(self) -> IGuiFrame:
        """Get the IGuiFrame widget."""
        return self._frame

    @property
    def frame_root(self) -> T:
        """Get the underlying GUI framework frame object."""
        return self._frame.root

"""Tkinter user-made frames.

This module provides frame implementations for the Pyrox GUI framework,
including abstract base classes and concrete implementations for task frames
and other specialized frame types.
"""
from __future__ import annotations
from typing import Generic, TypeVar
from pyrox.interfaces import IGuiFrame
from .widget import GuiWidget

T = TypeVar('T')
W = TypeVar('W')


class GuiFrame(
    GuiWidget[T],
    IGuiFrame[T, W],
    Generic[T, W],
):
    """Base implementation of GuiFrame.
    """

    def add_child(self, child: W) -> None:
        raise NotImplementedError("add_child method must be implemented by subclass.")

    def clear_children(self) -> None:
        raise NotImplementedError("clear_children method must be implemented by subclass.")

    def get_children(self) -> list[W]:
        raise NotImplementedError("get_children method must be implemented by subclass.")

    def initialize(self, **kwargs) -> bool:
        raise NotImplementedError("initialize method must be implemented by subclass.")

    def destroy(self) -> None:
        raise NotImplementedError("destroy method must be implemented by subclass.")

    def remove_child(self, child: W) -> None:
        raise NotImplementedError("remove_child method must be implemented by subclass.")

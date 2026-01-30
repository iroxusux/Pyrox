"""Viewport panning service module.
"""
from typing import Callable, Optional
import tkinter as tk
from pyrox.interfaces import IViewport


class ViewportPanningService:
    """Service for handling panning operations in a viewport."""

    def __init__(
        self,
        canvas: Optional[tk.Canvas] = None,
        viewport: Optional[IViewport] = None
    ):
        self._canvas = canvas
        self._viewport = viewport
        self._is_panning = False
        self._start_x = 0
        self._start_y = 0
        self._on_pan_callbacks: list[Callable] = []

    def _bind_to_canvas(self):
        if not self.canvas:
            return

        self.canvas.bind("<ButtonPress-2>", self._start_pan)
        self.canvas.bind("<B2-Motion>", self._do_pan)
        self.canvas.bind("<ButtonRelease-2>", self._end_pan)

    def _start_pan(self, event):
        self._is_panning = True
        self._start_x = event.x
        self._start_y = event.y
        self.canvas.config(cursor="fleur")

    def _do_pan(self, event):
        if self._is_panning:
            dx = event.x - self._start_x
            dy = event.y - self._start_y

            self.viewport.x += dx
            self.viewport.y += dy

            for callback in self._on_pan_callbacks:
                callback()

            self._start_x = event.x
            self._start_y = event.y

    def _end_pan(self, event):
        self._is_panning = False
        self.canvas.config(cursor="")

    def get_canvas(self) -> tk.Canvas:
        """Get the canvas associated with this service."""
        if not self._canvas:
            raise ValueError("Canvas is not set for ViewportPanningService.")
        return self._canvas

    def set_canvas(self, canvas: tk.Canvas) -> None:
        """Set the canvas associated with this service."""
        self._canvas = canvas
        self._bind_to_canvas()

    def get_viewport(self) -> IViewport:
        """Get the viewport associated with this service."""
        if not self._viewport:
            raise ValueError("Viewport is not set for ViewportPanningService.")
        return self._viewport

    def set_viewport(self, viewport: IViewport) -> None:
        """Set the viewport associated with this service."""
        self._viewport = viewport

    def get_on_pan_callbacks(self) -> list[Callable]:
        """Get the list of callbacks to be called on panning events."""
        return self._on_pan_callbacks

    @property
    def canvas(self) -> tk.Canvas:
        """Get the canvas associated with this service."""
        if not self._canvas:
            raise ValueError("Canvas is not set for ViewportPanningService.")
        return self._canvas

    @property
    def viewport(self) -> IViewport:
        """Get the viewport associated with this service."""
        if not self._viewport:
            raise ValueError("Viewport is not set for ViewportPanningService.")
        return self._viewport

    @property
    def on_pan_callbacks(self) -> list[Callable]:
        """Get the list of callbacks to be called on panning events."""
        return self._on_pan_callbacks

from enum import Enum, auto
import tkinter as tk


class UserMode(Enum):
    SELECT = auto()
    MOVE = auto()
    ROTATE = auto()
    SCALE = auto()
    INSERT = auto()

    @staticmethod
    def default():
        return UserMode.SELECT


class _SceneViewerUserMode:
    """Manages user interaction modes for the SceneViewer."""

    # ==================== Equality Checking ====================

    def __eq__(self, value: object) -> bool:
        if isinstance(value, UserMode):
            return self._current_mode == value
        elif isinstance(value, _SceneViewerUserMode):
            return self._current_mode == value._current_mode
        return super().__eq__(value)

    def __init__(
        self,
        parent,
        canvas: tk.Canvas
    ):
        self._parent = parent
        self._canvas = canvas
        self._current_mode = UserMode.default()

        # Public callbacks to be set by the SceneViewerFrame
        self.on_mode_change = lambda new_mode: None

    def _on_mode_change(self) -> None:
        """Internal method to handle mode changes and trigger callbacks."""
        if callable(self.on_mode_change):
            self.on_mode_change(self._current_mode)

        match self._current_mode:
            case UserMode.SELECT:
                self._canvas.config(cursor="arrow")
            case UserMode.MOVE:
                self._canvas.config(cursor="fleur")
            case UserMode.ROTATE:
                self._canvas.config(cursor="exchange")
            case UserMode.SCALE:
                self._canvas.config(cursor="sizing")
            case UserMode.INSERT:
                self._canvas.config(cursor="crosshair")

    def set_mode(self, mode: UserMode) -> None:
        """Set the current user interaction mode.

        Args:
            mode: The new mode to set.
        """
        if mode != self._current_mode:
            self._current_mode = mode
            self._on_mode_change()

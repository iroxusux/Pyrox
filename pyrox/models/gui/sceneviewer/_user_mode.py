from enum import Enum, auto
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsView


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
        view: QGraphicsView
    ):
        self._parent = parent
        self._view = view
        self._current_mode = UserMode.default()

        # Public callbacks to be set by the SceneViewerFrame
        self.on_mode_change = lambda tool: None

    def _on_mode_change(self) -> None:
        """Internal method to handle mode changes and trigger callbacks."""
        if callable(self.on_mode_change):
            self.on_mode_change(self._current_mode)

        match self._current_mode:
            case UserMode.SELECT:
                self._view.setCursor(Qt.CursorShape.ArrowCursor)
            case UserMode.MOVE:
                self._view.setCursor(Qt.CursorShape.SizeAllCursor)
            case UserMode.ROTATE:
                self._view.setCursor(Qt.CursorShape.CrossCursor)
            case UserMode.SCALE:
                self._view.setCursor(Qt.CursorShape.SizeBDiagCursor)
            case UserMode.INSERT:
                self._view.setCursor(Qt.CursorShape.CrossCursor)

    def set_mode(self, mode: UserMode) -> None:
        """Set the current user interaction mode.

        Args:
            mode: The new mode to set.
        """
        if mode != self._current_mode:
            self._current_mode = mode
            self._on_mode_change()

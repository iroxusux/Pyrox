from typing import Callable
from pyrox.interfaces import IViewport
from pyrox.models.protocols import Area2D, Zoomable


class Viewport(
    IViewport,
    Area2D,
    Zoomable
):
    """Viewport state.

    Attributes:
        x: X offset of the viewport
        y: Y offset of the viewport
        zoom: Zoom level of the viewport
    """

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        zoom: float = 1.0,
        max_zoom: float = 10.0,
        min_zoom: float = 0.1
    ):
        Area2D.__init__(self, x, y)
        Zoomable.__init__(self, zoom)
        self.max_zoom = max_zoom
        self.min_zoom = min_zoom
        self._on_reset_callbacks: list[Callable] = []

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Viewport):
            return False
        return (
            self.x == value.x and
            self.y == value.y and
            self.zoom == value.zoom
        )

    def get_delta(
        self,
        other: IViewport,
    ) -> tuple[float, float, float]:
        """Get the delta between this viewport and another.

        Args:
            viewport: Viewport to compare against
        Returns:
            Tuple of (delta_x, delta_y, delta_zoom)
        """
        delta_x = other.x - self.x
        delta_y = other.y - self.y
        delta_zoom = other.zoom - self.zoom
        return (delta_x, delta_y, delta_zoom)

    def reset(
        self
    ) -> None:
        """Reset the viewport to default state."""
        self.x = 0.0
        self.y = 0.0
        self.zoom = 1.0
        [callback() for callback in self._on_reset_callbacks]

    def update(
        self,
        other: IViewport
    ) -> None:
        self.x = other.x
        self.y = other.y
        self.zoom = other.zoom

    @property
    def on_reset_callbacks(self) -> list[Callable]:
        """Get the list of callbacks to be called on reset events."""
        return self._on_reset_callbacks

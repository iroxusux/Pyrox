"""Spacial object protocols that extend coordinate protocols.
"""
from pyrox.models.protocols.coord import Area2D
from pyrox.interfaces import CardinalDirection, IRotatable, ISpatial2D, IZoomable


class Rotatable(IRotatable):
    """Protocol for rotatable spatial objects."""

    def __init__(
        self,
        roll: float = 0.0,
        pitch: float = 0.0,
        yaw: float = 0.0,
    ) -> None:
        super().__init__()
        self._pitch = pitch
        self._yaw = yaw
        self._roll = roll


class Zoomable(IZoomable):
    """Protocol for zoomable spatial objects."""

    def __init__(
        self,
        zoom: float = 1.0,
    ) -> None:
        super().__init__()
        self._zoom = zoom


class Spatial2D(
    ISpatial2D,
    Area2D,
):
    """Protocol for 2D spatial objects."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
        direction: CardinalDirection | None = None,
    ) -> None:
        Area2D.__init__(
            self,
            x=x,
            y=y,
            width=width,
            height=height,
        )
        self._direction = direction


__all__ = [
    "Spatial2D",
    "Rotatable",
    "Zoomable",
]

"""Coordinate protocol definitions.
"""
from pyrox.interfaces import ICoord2D, IArea2D


class Coord2D(
    ICoord2D
):
    """Protocol for 2D coordinates."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
    ) -> None:
        self._x = x
        self._y = y


class Area2D(
    IArea2D,
    Coord2D,
):
    """Protocol for 2D areas."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
    ) -> None:
        Coord2D.__init__(
            self,
            x=x,
            y=y,
        )
        self._width = width
        self._height = height


__all__ = [
    "Coord2D",
    "Area2D",
]

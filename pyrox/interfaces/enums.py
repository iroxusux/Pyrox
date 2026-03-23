"""Enumerations for Pyrox interfaces.
"""
from enum import Enum, auto
from typing import Self


class _FromStrMixin(Enum):

    @classmethod
    def from_str(cls, s: str) -> Self | None:
        """Parse a string into an enum member, or return None if invalid."""
        s = s.strip().upper()
        try:
            return cls[s]
        except KeyError:
            return None


class CardinalDirection(_FromStrMixin):
    """Cardinal directions for 2D movement and orientation.
    """
    RIGHT = auto()  # +X
    DOWN = auto()   # +Y
    LEFT = auto()   # -X
    UP = auto()     # -Y
    NORTH = UP
    SOUTH = DOWN
    EAST = RIGHT
    WEST = LEFT

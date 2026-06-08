"""Enumerations for Pyrox interfaces."""
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


class _FromIntMixin(Enum):

    @classmethod
    def from_int(cls, i: int) -> Self | None:
        """Parse an integer into an enum member, or return None if invalid."""
        try:
            return cls(i)
        except ValueError:
            return None


class CardinalDirection(_FromStrMixin, _FromIntMixin):
    """Cardinal directions for 2D movement and orientation.
    """
    EAST = auto()  # +X
    SOUTH = auto()   # +Y
    WEST = auto()   # -X
    NORTH = auto()     # -Y

    # Extensions for convenience
    UP = NORTH
    DOWN = SOUTH
    LEFT = WEST
    RIGHT = EAST

    @classmethod
    def try_parse(
        cls,
        value: 'str | int | CardinalDirection'
    ) -> Self | None:
        """Try to parse a value as either a string or integer enum member."""
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls.from_str(value)
        elif isinstance(value, int):
            return cls.from_int(value)
        return None

    @classmethod
    def next_clockwise(cls, direction: 'CardinalDirection') -> 'CardinalDirection':
        """Get the next cardinal direction in clockwise order."""
        return cls((direction.value % 4) + 1)

    @classmethod
    def next_counterclockwise(cls, direction: 'CardinalDirection') -> 'CardinalDirection':
        """Get the next cardinal direction in counter-clockwise order."""
        return cls(((direction.value - 2) % 4) + 1)

    @classmethod
    def is_perpendicular(cls, dir1: 'CardinalDirection', dir2: 'CardinalDirection') -> bool:
        """Check if two cardinal directions are perpendicular."""
        return (dir1.value - dir2.value) % 4 in (1, 3)

    @classmethod
    def is_horizontal(cls, direction: 'CardinalDirection') -> bool:
        """Check if a cardinal direction is horizontal (EAST or WEST)."""
        return direction in (cls.EAST, cls.WEST)

    @classmethod
    def is_vertical(cls, direction: 'CardinalDirection') -> bool:
        """Check if a cardinal direction is vertical (NORTH or SOUTH)."""
        return direction in (cls.NORTH, cls.SOUTH)

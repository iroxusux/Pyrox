"""Meta module for Pyrox framework base classes."""
from pathlib import Path
from pyrox.services import IdGeneratorService


__all__ = (
    'DEF_ICON',
    'PyroxObject',
    'SliceableInt',
    'SnowFlake',
)

DEF_ICON = Path(__file__).resolve().parents[2] / "ui" / "icons" / "_def.ico"


class SliceableInt(int):
    """Extension of integer class that supports bit-wise operations.
    """

    def __add__(self, other):
        return self._value + other

    def __eq__(self, other):
        return self._value == other

    def __index__(self):
        return self._value

    def __init__(self, value=0):
        self._value = value

    def __int__(self):
        return self._value

    def __radd__(self, other):  # handles cases like 5 + SliceableInt(3)
        return self.__add__(other)

    def __repr__(self):
        return str(self._value)

    def __sub__(self, other):
        return self._value - other

    def clear(self):
        """Clear this `SliceableInt's` value.
        """
        self._value = 0

    def clear_bit(
        self,
        bit_position: int
    ) -> int:
        """Binary slicing operation to clear a bit of an integer.

        Args:
            bit_position (int): Bit position of the word to clear the bit from.

        Returns:
            int: Updated integer value after clearing the bit.
        """
        self._value = self._value & ~(1 << bit_position)
        return self._value

    def read_bit(
        self,
        bit_position: int
    ) -> bool:
        """Binary slicing operation to read a bit of an integer.

        Args:
            bit_position (int): Bit position of the word to read the bit from.

        Returns:
            bool: Value of the bit at the specified position.
        """
        return bool((self._value & (1 << bit_position)) >> bit_position)

    def set_bit(
        self,
        bit_position: int
    ) -> int:
        """Binary slicing operation to set a bit of an integer.

        Args:
            bit_position (int): Bit position of the word to set the bit in.

        Returns:
            int: Updated integer value after setting the bit.
        """
        self._value = self._value | (1 << bit_position)
        return self._value

    def set_value(
        self,
        value: int
    ) -> None:
        """Set the value of this `SliceableInt`.

        Args:
            value (int): The integer value to set.
        """
        self._value = value


class SnowFlake:
    """A meta class for all classes to derive from to obtain unique IDs.

    Attributes:
        id: Unique identifier for this object.
    """
    __slots__ = ('_id',)

    def __eq__(self, other) -> bool:
        if issubclass(type(other), SnowFlake):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        return hash(self._id)

    def __init__(
        self,
        **_
    ) -> None:
        self._id = IdGeneratorService.get_id()

    def __str__(self) -> str:
        return str(self.id)

    @property
    def id(self) -> int:
        """Unique identifier for this object.

        Returns:
            int: The unique ID.
        """
        return self._id


class PyroxObject(SnowFlake):
    """A base class for all Pyrox objects."""
    __slots__ = ()

    def __init__(
        self,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return self.__class__.__name__

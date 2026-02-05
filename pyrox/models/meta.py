"""Meta module for Pyrox framework base classes and utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Generic, Optional, TypeVar, Union
from pyrox.services import IdGeneratorService


T = TypeVar('T', bound=Union[dict, str])


__all__ = (
    'DEF_ICON',
    'PyroxObject',
    'SliceableInt',
    'SnowFlake',
    'SupportsFileLocation',
    'SupportsMetaData',
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
        **kwargs
    ) -> None:
        self._id = IdGeneratorService.get_id()
        super().__init__(**kwargs)

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


class SupportsItemAccess:
    """A meta class for all classes to derive from to obtain item access capabilities.
    This class allows for accessing items using the indexing syntax (e.g., obj[key]).
    """

    def __getitem__(self, key) -> Any:
        if self.indexed_attribute is None:
            raise TypeError("This object does not support item access!")
        return self.indexed_attribute.get(key, None)

    def __setitem__(self, key, value) -> None:
        if isinstance(self.indexed_attribute, dict):
            self.indexed_attribute[key] = value
        else:
            raise TypeError("Cannot set item on a non-dict indexed attribute!")

    @property
    def indexed_attribute(self) -> Optional[Any]:
        """A specified indexed attribute for this object.

        Returns:
            dict: The data dictionary.
        """
        return getattr(self, 'meta_data', None)


class SupportsMetaData(
    SupportsItemAccess,
    Generic[T]
):
    """Meta class for all classes to derive from to obtain meta data capabilities.
    This class allows for storing arbitrary meta data as a dictionary or string.
    """

    def __init__(
        self,
        meta_data: Optional[T] = None,
        **kwargs
    ) -> None:
        self.meta_data = meta_data if meta_data is not None else {}  # type: ignore
        super().__init__(**kwargs)

    @property
    def indexed_attribute(self) -> T:
        """A specified indexed attribute for this object.

        Returns:
            Union[str, dict]: The meta data as a string or dictionary.
        """
        return self.meta_data

    @property
    def meta_data(self) -> T:
        """Meta data for this object.

        Returns:
            Optional[Union[str, dict]]: The meta data dictionary or string if set, None otherwise.
        """
        return self._meta_data

    @meta_data.setter
    def meta_data(self, value: T):
        """Set the meta data for this object.

        Args:
            value: The data to set as meta data.
        Raises:
            TypeError: If the provided value is not a dictionary or string.
        """
        if not isinstance(value, (dict, str)):
            raise TypeError('Meta data must be a dictionary or string.')
        self._meta_data = value

    def get_meta_data(self) -> T:
        """Get the meta data for this object.

        Returns:
            Union[str, dict]: The meta data as a string or dictionary.
        """
        return self.meta_data

    def set_meta_data(
        self,
        meta_data: T
    ) -> None:
        """Set the meta data for this object.

        Args:
            meta_data: The data to set as meta data.
        """
        self.meta_data = meta_data

    def get_indexed_attribute(self) -> T:
        """Get the indexed attribute for this object.

        Returns:
            Union[str, dict]: The meta data as a string or dictionary.
        """
        return self.indexed_attribute


class SupportsMetaDataAsString(SupportsMetaData):
    """A meta class for all classes to derive from to obtain meta data capabilities as a string.
    This class allows for storing arbitrary meta data as a string.
    """

    def __init__(
        self,
        meta_data: Optional[str] = None,
        **kwargs
    ) -> None:
        self.meta_data = meta_data if meta_data is not None else ''
        super().__init__(**kwargs)

    @property
    def indexed_attribute(self) -> str:
        """A specified indexed attribute for this object.

        Returns:
            str: The meta data string.
        """
        return self.meta_data

    @property
    def meta_data(self) -> str:
        """Meta data for this object.

        Returns:
            str: The meta data string if set, empty string otherwise.
        """
        return self._meta_data

    @meta_data.setter
    def meta_data(self, value: str):
        if not isinstance(value, str):
            raise TypeError('Meta data must be a string.')
        self._meta_data = value


class SupportsMetaDataAsDict(SupportsMetaData):
    """A meta class for all classes to derive from to obtain meta data capabilities as a dictionary.
    This class allows for storing arbitrary meta data as a dictionary.
    """

    def __init__(
        self,
        meta_data: Optional[dict] = None,
        **kwargs
    ) -> None:
        super().__init__(
            meta_data=meta_data if meta_data is not None else {},
            **kwargs
        )

    @property
    def indexed_attribute(self) -> dict:
        """A specified indexed attribute for this object.

        Returns:
            dict: The meta data dictionary.
        """
        return self.meta_data

    @property
    def meta_data(self) -> dict:
        """Meta data for this object.

        Returns:
            dict: The meta data dictionary if set, empty dictionary otherwise.
        """
        return self._meta_data

    @meta_data.setter
    def meta_data(self, value: dict):
        """Set the meta data for this object.

        Args:
            value: The dictionary to set as meta data.

        Raises:
            TypeError: If the provided value is not a dictionary.
        """
        if not isinstance(value, dict):
            raise TypeError('Meta data must be a dictionary.')
        self._meta_data = value


class SupportsFileLocation:
    """A meta class for all classes to derive from to obtain file location capabilities.

    Attributes:
        file_location: The file location of the object.
    """

    def __init__(
        self,
        file_location: Optional[str] = None,
        **kwargs
    ) -> None:
        self.file_location = file_location
        super().__init__(**kwargs)

    @property
    def file_location(self) -> Optional[str]:
        """The file location of the object.

        Returns:
            Optional[str]: The file location if set, None otherwise.
        """
        return self._file_location

    @file_location.setter
    def file_location(self, value: Optional[str]):
        """Set the file location of the object.

        Args:
            value: The file location to set.

        Raises:
            TypeError: If the value is not a string or None.
        """
        if value is not None and not isinstance(value, str):
            raise TypeError('File location must be a string or None.')
        self._file_location = value

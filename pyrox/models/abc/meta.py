"""Meta module for Pyrox framework base classes and utilities."""
from __future__ import annotations

from enum import Enum
from pathlib import Path
import re
from typing import Any, Optional, Union
from pyrox.models.abc.logging import Loggable

__all__ = (
    'DEF_APP_NAME',
    'DEF_AUTHOR_NAME',
    'DEF_ICON',
    'DEF_VIEW_TYPE',
    'DEF_WIN_TITLE',
    'DEF_WIN_SIZE',
    'EnforcesNaming',
    'PyroxObject',
    'SliceableInt',
    'SnowFlake',
    'SupportsFileLocation',
    'SupportsMetaData',
    'TK_CURSORS',
)

ALLOWED_CHARS = re.compile(f'[^{r'a-zA-Z0-9_\[\]'}]')
ALLOWED_REV_CHARS = re.compile(f'[^{r'0-9.'}]')
ALLOWED_MOD_CHARS = re.compile(f'[^{r'a-zA-Z0-9_.-'}]')
DEF_APP_NAME = 'Pyrox Application'
DEF_AUTHOR_NAME = 'Pyrox Author'
DEF_VIEW_TYPE = 1
DEF_WIN_TITLE = 'Pyrox Default Frame'
DEF_WIN_SIZE = '1024x768'
DEF_ICON = Path(__file__).resolve().parents[2] / "ui" / "icons" / "_def.ico"


class TK_CURSORS(Enum):
    """Static enum class for python tkinter cursors.

    Attributes:
        ARROW: Arrow cursor.
        CIRCLE: Circle cursor.
        CLOCK: Clock cursor.
        CROSS: Cross cursor.
        DOTBOX: Dotbox cursor.
        EXCHANGE: Exchange cursor.
        FLEUR: Fleur cursor.
        HEART: Heart cursor.
        MAN: Man cursor.
        MOUSE: Mouse cursor.
        PIRATE: Pirate cursor.
        PLUS: Plus cursor.
        SHUTTLE: Shuttle cursor.
        SIZING: Sizing cursor.
        SPIDER: Spider cursor.
        SPRAYCAN: Spraycan cursor.
        STAR: Star cursor.
        TARGET: Target cursor.
        TCROSS: T-cross cursor.
        TREK: Trek cursor.
        WAIT: Wait cursor.
    """
    ARROW = "arrow"
    CIRCLE = "circle"
    CLOCK = "clock"
    CROSS = "cross"
    DEFAULT = ""
    DOTBOX = "dotbox"
    EXCHANGE = "exchange"
    FLEUR = "fleur"
    HEART = "heart"
    MAN = "man"
    MOUSE = "mouse"
    PIRATE = "pirate"
    PLUS = "plus"
    SHUTTLE = "shuttle"
    SIZING = "sizing"
    SPIDER = "spider"
    SPRAYCAN = "spraycan"
    STAR = "star"
    TARGET = "target"
    TCROSS = "tcross"
    TREK = "trek"
    WAIT = "wait"


class _IdGenerator:
    """Static class for id generation for SnowFlake objects.

    Hosts a unique identifier generator for creating unique IDs.
    """
    __slots__ = ()
    _ctr = 0

    @staticmethod
    def get_id() -> int:
        """Get a unique ID from the generator.

        Returns:
            int: Unique ID for a SnowFlake object.
        """
        _IdGenerator._ctr += 1
        return _IdGenerator._ctr

    @staticmethod
    def curr_value() -> int:
        """Retrieve the current value of the ID generator.

        Returns:
            int: Current value of the counter.
        """
        return _IdGenerator._ctr


class SliceableInt(int):
    """Extension of integer class that supports bit-wise operations
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

    def clear_bit(self,
                  bit_position: int) -> int:
        """Binary slicing operation to clear a bit of an integer.

        .. -------------------------------------------------------

        Arguments
        ----------
        bit_position: :class:`int`
            Bit position of the word to clear to bit of.

        Returns
        ----------
            :class:`int`
        """
        self._value = self._value & ~(1 << bit_position)
        return self._value

    def read_bit(
        self,
        bit_position: int
    ) -> bool:
        """Binary slicing operation to read a bit of an integer.

        .. -------------------------------------------------------

        Arguments
        ----------
        bit_position: :class:`int`
            Bit position of the word to read the bit from.

        Returns
        ----------
            :class:`bool`
        """
        return (self._value & (1 << bit_position)) >> bit_position

    def set_bit(self,
                bit_position: int) -> int:
        """Binary slicing operation to set a bit of an integer.

        .. -------------------------------------------------------

        Arguments
        ----------
        bit_position: :class:`int`
            Bit position of the word to set to bit of.

        Returns
        ----------
            :class:`int`
        """
        self._value = self._value | (1 << bit_position)
        return self._value

    def set_value(self, value: int) -> None:
        """Set a value for this sliceable int without changing it's base type (`SliceableInt`).

        .. -------------------------------------------------------

        Arguments
        ----------
        value: :class:`int`
            Value to set in this object.
        """
        self._value = value


class EnforcesNaming:
    """Helper meta class to enforce naming schemes across objects."""
    __slots__ = ()
    _last_allowed_chars = ALLOWED_CHARS

    class InvalidNamingException(Exception):
        """Exception raised for invalid naming schemes.

        Attributes:
            message: The error message to display when the exception is raised.
        """
        __slots__ = ('message',)

        def __init__(self, message='Invalid naming scheme! Allowed chars are: '):
            self.message = message + f'{EnforcesNaming._last_allowed_chars.pattern}'
            super().__init__(self.message)

    @staticmethod
    def is_valid_rockwell_bool(text: str) -> bool:
        """Check if a string is valid according to the Rockwell boolean naming scheme.

        Args:
            text: The string to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        EnforcesNaming._last_allowed_chars = re.compile(f'[^{r'true|false'}]')
        if not text:
            return False
        return text in ('true', 'false')

    @staticmethod
    def is_valid_string(text: str) -> bool:
        """Check if a string is valid according to the naming scheme.

        Args:
            text: The string to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        EnforcesNaming._last_allowed_chars = ALLOWED_CHARS
        if ALLOWED_CHARS.search(text):
            return False
        return True

    @staticmethod
    def is_valid_module_string(text: str) -> bool:
        """Check if a string is valid according to the module naming scheme.

        Args:
            text: The string to validate.

        Returns:
            bool: True if valid module name, False otherwise.
        """
        EnforcesNaming._last_allowed_chars = ALLOWED_MOD_CHARS
        if ALLOWED_MOD_CHARS.search(text):
            return False
        return True

    @staticmethod
    def is_valid_revision_string(text: str) -> bool:
        """Check if a string is valid according to the revision naming scheme.

        Args:
            text: The string to validate.

        Returns:
            bool: True if valid revision name, False otherwise.
        """
        EnforcesNaming._last_allowed_chars = ALLOWED_REV_CHARS
        if ALLOWED_REV_CHARS.search(text):
            return False
        return True


class SnowFlake:
    """A meta class for all classes to derive from to obtain unique IDs.

    Attributes:
        id: Unique identifier for this object.
    """
    __slots__ = ('_id',)

    def __eq__(self, other: 'SnowFlake') -> bool:
        if type(self) is type(other):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        return hash(self._id)

    def __init__(
        self,
    ) -> None:
        self._id = _IdGenerator.get_id()

    def __str__(self) -> str:
        return str(self.id)

    @property
    def id(self) -> int:
        """Unique identifier for this object.

        Returns:
            int: The unique ID.
        """
        return self._id


class PyroxObject(SnowFlake, Loggable):
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
    @property
    def indexed_attribute(self) -> dict:
        """A specified indexed attribute for this object.

        Returns:
            dict: The data dictionary.
        """
        return getattr(self, 'meta_data', None)

    def __getitem__(self, key) -> Any:
        if self.indexed_attribute is None:
            raise TypeError("This object does not support item access!")
        return self.indexed_attribute.get(key, None)

    def __setitem__(self, key, value) -> None:
        if isinstance(self.indexed_attribute, dict):
            self.indexed_attribute[key] = value
        else:
            raise TypeError("Cannot set item on a non-dict indexed attribute!")


class SupportsMetaData(SupportsItemAccess):
    """Meta class for all classes to derive from to obtain meta data capabilities.
    This class allows for storing arbitrary meta data as a dictionary or string.
    """

    @property
    def indexed_attribute(self) -> Optional[Union[str, dict]]:
        return self.meta_data

    def __init__(
        self,
        meta_data: Optional[Union[str, dict]] = None,
        **kwargs
    ) -> None:
        self.meta_data: Optional[Union[str, dict]] = meta_data or {}
        super().__init__(**kwargs)

    @property
    def meta_data(self) -> Optional[Union[str, dict]]:
        """Meta data for this object.

        Returns:
            Optional[Union[str, dict]]: The meta data dictionary or string if set, None otherwise.
        """
        return self._meta_data

    @meta_data.setter
    def meta_data(self, value: Optional[Union[str, dict]]):
        """Set the meta data for this object.

        Args:
            value: The data to set as meta data.
        Raises:
            TypeError: If the provided value is not a dictionary or string.
        """
        if value is not None and not isinstance(value, (dict, str)):
            raise TypeError('Meta data must be a dictionary, string, or None.')
        self._meta_data = value


class NamedPyroxObject(PyroxObject):
    """A base class for all Pyrox objects that have a name.

    Attributes:
        name: Name of the object.
        description: Description of the object.
    """
    __slots__ = ('_name', '_description')

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.name = name if name else self.__class__.__name__
        self.description = description if description else ''

    def __repr__(self):
        return str(self)

    def __str__(self):
        return self.name

    @property
    def name(self) -> str:
        """Name of the object.

        Returns:
            str: The name of the object.
        """
        return self._name

    @name.setter
    def name(self, value: str):
        """Set the name of the object.

        Args:
            value: Name to set for this object.

        Raises:
            EnforcesNaming.InvalidNamingException: If the name is invalid.
        """
        if not EnforcesNaming.is_valid_string(value):
            raise EnforcesNaming.InvalidNamingException()
        self._name = value

    @property
    def description(self) -> str:
        """Description of the object.

        Returns:
            str: The description of the object.
        """
        return self._description

    @description.setter
    def description(self, value: str):
        """Set the description of the object.

        Args:
            value: Description to set for this object.

        Raises:
            TypeError: If the value is not a string.
        """
        if not isinstance(value, str):
            raise TypeError('Description must be a string.')
        self._description = value


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
        self.file_location: Optional[str] = file_location
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

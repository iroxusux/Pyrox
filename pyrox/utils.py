"""Pyrox utilities module
    """
import fnmatch
from typing import List


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

    def read_bit(self,
                 bit_position: int) -> bool:
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


def check_wildcard_patterns(
    items: List[str],
    patterns: List[str]
) -> bool:
    """Check if any item matches any wildcard pattern."""
    for item in items:
        for pattern in patterns:
            if fnmatch.fnmatch(item, pattern):
                return True
    return False


def clear_bit(word: int,
              bit_position: int) -> int:
    """Binary slicing operation to clear a bit of an integer.

        .. -------------------------------------------------------

        Arguments
        ----------
        word: :class:`int`
            Integer word to clear bit from
        bit_position: :class:`int`
            Bit position of the word to clear to bit of.

        Returns
        ----------
            :class:`int`
        """
    return SliceableInt(word).clear_bit(bit_position).__int__()


def set_bit(word: int,
            bit_position: int) -> int:
    """Binary slicing operation to set a bit of an integer.

        .. -------------------------------------------------------

        Arguments
        ----------
        word: :class:`int`
            Integer word to set bit in
        bit_position: :class:`int`
            Bit position of the word to set to bit of.

        Returns
        ----------
            :class:`int`
        """
    return SliceableInt(word).set_bit(bit_position).__int__()


def read_bit(word: int,
             bit_position: int) -> bool:
    """Binary slicing operation to read a bit of an integer.

        .. -------------------------------------------------------

        Arguments
        ----------
        word: :class:`int`
            Integer word to set read from
        bit_position: :class:`int`
            Bit position of the word to read the bit from.

        Returns
        ----------
            :class:`bool`
        """
    return SliceableInt(word).read_bit(bit_position)


def replace_strings_in_dict(data, old_string, new_string) -> dict:
    """
    Recursively searches and replaces all occurrences of a string in a dictionary,
    including nested dictionaries and lists.

    .. ---------------------------------------------------------------------------

    Arguments
    ----------
    data :class:`dict`
        The dictionary to search and replace within.

    old_string :class:`str`
        The string to be replaced.


    new_string :class:`str`
        The string to replace with.

    .. ---------------------------------------------------------------------------

    Returns
    ----------
        :class:`dict` A new dictionary with the strings replaced.
    """
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            new_key = key.replace(
                old_string, new_string) if isinstance(key, str) else key
            new_dict[new_key] = replace_strings_in_dict(
                value, old_string, new_string)
        return new_dict
    elif isinstance(data, list):
        return [replace_strings_in_dict(item, old_string, new_string) for item in data]
    elif isinstance(data, str):
        return data.replace(old_string, new_string)
    else:
        return data


def find_duplicates(input_list,
                    include_orig: bool = False):
    seen = set()
    duplicates = []

    for item in input_list:
        if item in seen:
            if not include_orig:
                duplicates.append(item)
            else:
                duplicates.append((item, next((y for y in seen if y == item), None)))
        else:
            seen.add(item)

    return duplicates

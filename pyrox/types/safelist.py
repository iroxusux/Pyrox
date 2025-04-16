"""safe list that handles non-duplicate entries
    """
from __future__ import annotations


from typing import TypeVar


T = TypeVar('T')


__all__ = (
    'SafeList',
)


class SafeList(list[T]):
    """safe list that handles non-duplicate entries

    Args:
        list (T): list
    """

    def append(self,
               value: T) -> None:
        """safe append to self

        Args:
            value (T): value to append
        """
        if value not in self:
            super().append(value)

    def remove(self,
               value: T) -> None:
        """safe remove from self

        Args:
            value (T): value to remove
        """
        if value in self:
            super().remove(value)

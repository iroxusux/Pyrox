"""provided hash classes and functions
    """
from __future__ import annotations


from typing import TypeVar


T = TypeVar('T')


__all__ = (
    'HashList',
)


class HashList(list[T]):
    """list that can hash and retrieve hash values
    """

    def __init__(self,
                 hash_key: str):
        super().__init__()
        self._hash_key: str = hash_key
        self._hashes: dict = {}

    @property
    def hash_key(self) -> str:
        """get the hash key this list uses
        to store and retrieve data

        Returns:
            str: hash key
        """
        return self._hash_key

    def append(self,
               value: T):
        """append value and hash

        Args:
            value (T): value to add / hash
        """
        if not self.by_name(getattr(value, self._hash_key)):
            super().append(value)
        self._hashes[getattr(value, self._hash_key)] = value

    def by_name(self,
                key: str) -> T:
        """get hashed value or None

        Args:
            key (str): value to lookup in hash dict

        Returns:
            T: value found or none
        """
        return self._hashes.get(key, None)

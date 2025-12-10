"""Pyrox list module for enhanced list types.

This module provides specialized list implementations with additional functionality
like hash-based indexing, safety features, and change tracking capabilities.
"""
from __future__ import annotations


from typing import (
    Any,
    Callable,
    Generic,
    Iterator,
    Optional,
    TypeVar,
    Union
)


T = TypeVar('T')


__all__ = (
    'HashList',
    'SafeList',
    'TrackedList',
)


class Subscribable:
    """Base class for objects that support subscription/notification patterns.

    This class provides a foundation for implementing the observer pattern,
    allowing objects to subscribe to notifications and emit events to subscribers.

    Attributes:
        subscribers: List of callback functions subscribed to this object.
    """
    __slots__ = ('_subscribers')

    def __init__(self):
        self._subscribers: list[Callable] = []

    @property
    def subscribers(self) -> list[Callable]:
        """A list of active subscribers to this object.

        Returns:
            list[Callable]: List of callback functions subscribed to this object.
        """
        return self._subscribers

    def safe_emit(self, *args, **kwargs):
        """Emit to all subscribers, catching exceptions.

        Args:
            *args: Positional arguments to pass to subscribers.
            **kwargs: Keyword arguments to pass to subscribers.
        """
        for subscriber in self._subscribers:
            try:
                subscriber(*args, **kwargs)
            except Exception:
                continue

    def subscribe(self, callback: Callable) -> None:
        """Subscribe to this subscribable object.

        Args:
            callback: A callback function to be called when this object emits events.
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsafe_emit(self, *args, **kwargs):
        """Emit to all subscribers that an update has occurred.

        Args:
            *args: Positional arguments to pass to subscribers.
            **kwargs: Keyword arguments to pass to subscribers.
        """
        for subscriber in self.subscribers:
            subscriber(*args, **kwargs)

    def unsubscribe(self, callback: Callable) -> None:
        """Unsubscribe from this subscribable object.

        Args:
            callback: A callback function to be removed from this object's subscribers.
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)


class HashList(Subscribable, Generic[T]):
    """A list that provides hash-based indexing alongside traditional indexing.

    This class combines the functionality of a list with hash-based lookups,
    allowing efficient access by both index and a specified hash key attribute.

    Args:
        hash_key: The attribute name to use as the hash key for items.

    Attributes:
        hash_key: The attribute name used for hash-based lookups.
    """

    __slots__ = ('_hash_key', '_hashes')

    def __bool__(self) -> bool:
        return len(self._hashes) > 0

    def __init__(
        self,
        hash_key: str
    ) -> None:
        super().__init__()
        self._hash_key: str = hash_key
        self._hashes: dict[str, T] = {}

    def __contains__(
        self,
        item: Union[dict, str, object]
    ) -> bool:
        if isinstance(item, dict):
            return getattr(item, self._hash_key, None) in self._hashes
        elif isinstance(item, str):
            return item in self._hashes
        elif isinstance(item, object):
            return getattr(item, self._hash_key, None) in self._hashes
        else:
            raise TypeError(f'Item must be a dict, object or str, got {type(item)}')

    def __getitem__(self, key) -> Optional[T]:
        if isinstance(key, int):
            return self.by_index(key)
        return self.hashes[key]

    def __iter__(self) -> Iterator[T]:
        for item in self.hashes:
            yield self.hashes[item]

    def __len__(self) -> int:
        return len(self._hashes)

    @property
    def hash_key(self) -> str:
        return self._hash_key

    @property
    def hashes(self) -> dict[str, T]:
        return self._hashes

    def append(
        self,
        value: T
    ) -> None:
        """Append value to this hash.

        If the object exists, its entity is updated in this hash list.

        Args:
            value: Object to append to this hash list.

        Raises:
            TypeError: If value is not an object or is a primitive type.
        """
        if not isinstance(value, object):
            raise TypeError("value must be an object")
        if isinstance(value, (str, int, float, bool)):
            raise TypeError("value must be an object, not a primitive type")
        self._hashes[getattr(value, self._hash_key)] = value
        self.unsafe_emit()

    def as_list_names(self) -> list[str]:
        """Get this hash as a list of keys.

        Returns:
            list[str]: List of all hash keys.
        """
        return list(self._hashes.keys())

    def as_list_values(self) -> list[T]:
        """Get this hash as a list of values.

        Returns:
            list[T]: List of all hash values.
        """
        return list(self._hashes.values())

    def as_named_list(self) -> list[tuple[str, T]]:
        """Get this hash as a list of tuples with key and value.

        Returns:
            list[tuple[str, T]]: List of tuples containing (key, value) pairs.
        """
        return [(key, value) for key, value in self._hashes.items()]

    def by_attr(
        self,
        attr_name: str,
        attr_value: Any
    ) -> Optional[T]:
        """Get object by custom attribute value.

        Args:
            attr_name: Name of the attribute to search for.
            attr_value: Value of the attribute to match.

        Returns:
            Optional[T]: The first object with matching attribute value, or None if not found.

        Example:
            >>> hash_list.by_attr('Name', 'Foo')
        """
        for x in self._hashes:
            if getattr(self._hashes[x], attr_name, None) == attr_value:
                return x

        return None

    def by_key(
        self,
        key: str
    ) -> Optional[T]:
        """Get hashed object by its given key.

        Args:
            key: The hash key to look up.

        Returns:
            Optional[T]: The object associated with the key, or None if not found.
        """
        return self._hashes.get(key, None)

    def by_index(
        self,
        index: int
    ) -> Optional[T]:
        """Get hashed object by its integer index (in insertion order).

        Args:
            index: Integer index of the object to retrieve.

        Returns:
            Optional[T]: The object at the specified index, or None if out of range.
        """
        try:
            return list(self._hashes.values())[index]
        except IndexError:
            return None

    def clear(self) -> None:
        """Clear all items from this hash list."""
        self._hashes.clear()
        self.unsafe_emit()

    def unsafe_emit(self, *args, **kwargs):
        for subscriber in self.subscribers:
            subscriber(*args,
                       models={'hash_key': self._hash_key, 'hash_list': self._hashes},
                       **kwargs,)

    def extend(
        self,
        values: list[T]
    ) -> None:
        """Extend this hash with a list of values.

        Args:
            values: List of objects to append to this hash list.
        """
        for value in values:
            self.append(value)

    def find_first(
        self,
        func: Callable[[T], bool,]
    ) -> Optional[T]:
        """Find the first item in this hash that matches the given function.

        Args:
            func: A callable that takes an item and returns True if it matches.

        Returns:
            Optional[T]: The first matching item, or None if no match found.
        """
        for item in self._hashes.values():
            if func(item):
                return item

    def get(self, key, default=None) -> Optional[T]:
        return self.hashes.get(key, default)

    def remove(
        self,
        value: T
    ) -> None:
        """Remove value from this hash.

        Args:
            value: Object to remove from this hash list.
        """
        try:
            del self._hashes[getattr(value, self._hash_key)]
        except KeyError:
            pass
        self.unsafe_emit()

    def sort(self):
        """Sort this hash by its keys.

        Sorts the internal dictionary by keys in ascending order.
        """
        self._hashes = dict(sorted(self._hashes.items()))
        self.unsafe_emit()


class SafeList(list[T]):
    """List used to prevent duplicates from being appended.

    This list implementation automatically prevents duplicate values from being
    added, ensuring all elements remain unique.
    """

    def append(self,
               value: T) -> None:
        """Append value to this list safely.

        Only appends the value if it is not already present in the list.

        Args:
            value: Value to safely add to this list.
        """
        if value not in self:
            super().append(value)


class TrackedList(list[T]):
    """A list to emit events when its contents are updated.

    This list implementation notifies all subscribers whenever the list is modified
    through append or remove operations.

    Attributes:
        subscribers: SafeList of callable subscribers that are invoked when the list changes.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscribers = SafeList()

    @property
    def subscribers(self) -> SafeList[Callable]:
        """Iterable list of subscribers who are called when this list is updated.

        Returns:
            SafeList[Callable]: List of callable subscribers.
        """
        return self._subscribers

    @subscribers.setter
    def subscribers(self, value) -> None:
        if not isinstance(value, SafeList):
            raise TypeError('subscribers must be a SafeList')
        self._subscribers = value

    def emit(self) -> None:
        """Emit to all delegates that an update has occurred.
        """
        for subscriber in self._subscribers:
            try:
                subscriber()
            except Exception:
                continue

    def append(self,
               value: T) -> None:
        """Append value to this list and call delegates.

        Args:
            value: Value to add to this list.
        """
        super().append(value)
        self.emit()

    def remove(self,
               value: T) -> None:
        """Remove value from this list and call delegates.

        Args:
            value: Value to remove from this list.
        """
        super().remove(value)
        self.emit()

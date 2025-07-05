"""irox list module
    """
from __future__ import annotations


from typing import Any, Callable, Optional, TypeVar


T = TypeVar('T')


__all__ = (
    'HashList',
    'SafeList',
    'TrackedList',
)


class Subscribable:
    """Subscribable Object to support emitting update events.

    .. ------------------------------------------------------------

    .. package:: types.list

    .. ------------------------------------------------------------

    Attributes
    -----------
    subscribers: :type:`list`
        A list of active subscribers to this object.

        Subscribers will get notified when content is updated.

    """

    __slots__ = ('_subscribers')

    def __init__(self):
        self._subscribers: list[Callable] = []

    @property
    def subscribers(self) -> list[Callable]:
        """A list of active subscribers to this object.

        Subscribers will get notified when content is updated.

        Returns
        --------
            subscribers: :type:`list`
        """
        return self._subscribers

    def emit(self, *args, **kwargs):
        """Emit an update to all subscribers.

        The inheriting class needs to set up Args and KwArgs to be emitted.

        Or, alternatively, override this method.
        """
        for subscriber in self.subscribers:
            subscriber(*args, **kwargs)

    def subscribe(self, callback: Callable) -> None:
        """Subscribe to this subscribable object

        Arguments
        ----------
        callback: :type:`Callable`
            A callback to be called when this object emits.
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable) -> None:
        """Subscribe to this subscribable object

        Arguments
        ----------
        callback: :type:`Callable`
            A callback to be called when this object emits.
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)


class HashList(Subscribable):
    """Dictionary 'list' that support hashing.

    .. ------------------------------------------------------------

    .. package:: types.list

    .. ------------------------------------------------------------

    Arguments
    -----------
    hash_key: :type:`str`
        Key to use for hashing objects into this list.

    .. ------------------------------------------------------------

    Attributes
    -----------
    hash_key: :type:`str`
        Key used for hashing objects into this list.

    hashes: :type:`dict`
        A hashed dictionary (by key) of all items in this object.

    subscribers: :type:`list`
        A list of active subscribers to this hash.

        Subscribers will get notified when content is updated.

    """

    __slots__ = ('_hash_key', '_hashes')

    def __init__(self,
                 hash_key: str):
        super().__init__()
        self._hash_key: str = hash_key
        self._hashes: dict = {}

    def __contains__(self, item: dict):
        return self.by_key(getattr(item, self._hash_key, None))

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.by_index(key)
        return self.hashes[key]

    def __iter__(self):
        for item in self.hashes:
            yield self.hashes[item]

    def __len__(self):
        return len(self._hashes)

    @property
    def hash_key(self) -> str:
        """get the hash key this list uses to store and retrieve data.

        .. ------------------------------------------------------------

        Returns
        --------
            hash_key: :type:`str`
        """
        return self._hash_key

    @property
    def hashes(self) -> dict:
        """A hashed dictionary (by key) of all items in this object.

        Returns
        --------
            hashes: :type:`dict`
        """
        return self._hashes

    def append(self,
               value: T):
        """Append value to this hash.

        If the object exists, its' entity is updated in this hash list

        """
        self._hashes[getattr(value, self._hash_key)] = value
        self.emit()

    def by_attr(self,
                attr_name: str,
                attr_value: Any) -> Optional[T]:
        """Get object by custom attribute value

        i.e. attr_name: 'Name' == attr_value: 'Foo'

        .. ------------------------------------------------------------

        Returns
        --------
            T: :class:`T`
        """
        for x in self._hashes:
            if getattr(self._hashes[x], attr_name, None) == attr_value:
                return x

        return None

    def by_key(self,
               key: str) -> Optional[T]:
        """Get hashed object by its' given `key`.

        .. ------------------------------------------------------------

        Returns
        --------
            T: :class:`T`
        """
        return self._hashes.get(key, None)

    def by_index(self,
                 index: int) -> Optional[T]:
        """Get hashed object by its integer index (in insertion order).

        Returns
        --------
            T: :class:`T` or None if out of range
        """
        try:
            return list(self._hashes.values())[index]
        except IndexError:
            return None

    def emit(self, *args, **kwargs):
        for subscriber in self.subscribers:
            subscriber(*args,
                       models={'hash_key': self._hash_key, 'hash_list': self._hashes},
                       **kwargs,)

    def get(self, key, default=None):
        return self.hashes.get(key, default)

    def remove(self,
               value: T):
        """Remove value from this hash.

        """
        try:
            del self._hashes[getattr(value, self._hash_key)]
        except KeyError:
            pass
        self.emit()


class SafeList(list[T]):
    """List used to prevent duplicates from being appended.

    .. ------------------------------------------------------------

    .. package:: types.list

    """

    def append(self,
               value: T) -> None:
        """Append value to this list `safely`.

        .. ------------------------------------------------------------

        Arguments
        --------
        value: :type:`T`
            Value to safely add to this list.
        """
        if value not in self:
            super().append(value)


class TrackedList(list[T]):
    """A list to emit events when it's contents are updated.

    .. ------------------------------------------------------------

    .. package:: types.list

    .. ------------------------------------------------------------

    Attributes
    -----------
    subscribers: Iterable[:type:`str`]
        Iterable list of subscribers who are called when this list is updated.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._subscribers: SafeList[callable] = SafeList()

    @property
    def subscribers(self) -> list[T]:
        """Iterable list of subscribers who are called when this list is updated.

        Returns:
            subscribers: Iterable[:type:`str`]
        """
        return self._subscribers

    @subscribers.setter
    def subscribers(self, value) -> None:
        self._subscribers = value

    def emit(self) -> None:
        """Emit to all delegates that an update has occured.
        """
        _ = [x() for x in self._subscribers]

    def append(self,
               value: T) -> None:
        """Append value to this list and call delegates.

        .. ------------------------------------------------------------

        Arguments
        --------
        value: :type:`T`
            Value to add to this list.
        """
        super().append(value)
        self.emit()

    def remove(self,
               value: T) -> None:
        """Remove value from this list and call delegates.

        .. ------------------------------------------------------------

        Arguments
        --------
        value: :type:`T`
            Value to remove from this list.
        """
        super().remove(value)
        self.emit()

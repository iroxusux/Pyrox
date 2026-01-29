"""Runtime ABC types for the Pyrox framework.

This module provides abstract base classes for objects that support build/run lifecycles,
including buildable objects, runnable objects, and runtime dictionary management.
"""
from __future__ import annotations
from typing import Any, Callable

__all__ = (
    'RuntimeDict',
)


class RuntimeDict:
    """A dictionary-like class to store data with automatic callbacks.

    This class provides a way to store key-value pairs and automatically save the data
    whenever an item is added, updated, or deleted.

    Attributes:
        callback: A callback function that is called whenever the data is modified.
        data: The dictionary that stores the runtime data.
        inhibit_callback: Whether to inhibit the callback function from being called.
    """
    __slots__ = ('_callback', '_data', '_inhibit_callback')

    def __contains__(self, key) -> bool:
        """Check if a key exists in the runtime data dictionary.

        Args:
            key: The key to check for.

        Returns:
            bool: True if key exists, False otherwise.
        """
        return key in self._data

    def __getitem__(self, key) -> Any:
        return self._data.get(key, None)

    def __init__(self, callback: Callable):
        if callback is None:
            raise ValueError('A valid callback function must be provided to RuntimeDict.')
        if not callable(callback):
            raise TypeError('Callback must be a callable function.')
        self._callback: Callable = callback
        self._data = {}
        self._inhibit_callback = False

    def __setitem__(self, key, value):
        self._data[key] = value
        self._call()

    def __delitem__(self, key):
        del self._data[key]
        self._call()

    @property
    def callback(self) -> Callable:
        """Get the callback function.

        Returns:
            Callable: The current callback function.
        """
        return self._callback

    @callback.setter
    def callback(self, value: Callable):
        """Set the callback function.

        Args:
            value: The callback function to set.

        Raises:
            ValueError: If the provided value is not callable.
        """
        if not value or not callable(value):
            raise ValueError('A valid callback function must be provided to RuntimeDict.')
        self._callback = value

    @property
    def data(self) -> dict:
        """Get the runtime data dictionary.

        Returns:
            dict: The internal data dictionary.
        """
        return self._data

    @data.setter
    def data(self, value: dict):
        """Set the runtime data dictionary.

        Args:
            value: The dictionary to set as the new data.

        Raises:
            TypeError: If the provided value is not a dictionary.
        """
        if not isinstance(value, dict):
            raise TypeError('Runtime data must be a dictionary.')
        self._data = value
        self._callback()

    @property
    def inhibit_callback(self) -> bool:
        """Get whether the callback is inhibited.

        Returns:
            bool: True if callback is inhibited, False otherwise.
        """
        return self._inhibit_callback

    @inhibit_callback.setter
    def inhibit_callback(self, value: bool):
        """Set whether the callback is inhibited.

        Args:
            value: Boolean indicating whether to inhibit the callback.

        Raises:
            TypeError: If the provided value is not a boolean.
        """
        if not isinstance(value, bool):
            raise TypeError('Inhibit callback must be a boolean value.')
        self._inhibit_callback = value
        self._call()

    def _call(self):
        """Call the callback function if it is set and not inhibited.

        Raises:
            TypeError: If the callback is not callable.
        """
        if self._inhibit_callback is False:
            if callable(self._callback):
                self._callback()
            else:
                raise TypeError('Callback must be a callable function.')

    def clear(self):
        """Clear the runtime data dictionary."""
        self._data.clear()
        self._callback()

    def get(self, key, default=None) -> Any:
        """Get an item from the runtime data dictionary.

        Args:
            key: The key to retrieve.
            default: The default value if key is not found.

        Returns:
            Any: The value associated with the key, or default if not found.
        """
        return self._data.get(key, default)

    def inhibit(self):
        """Inhibit the callback function."""
        self._inhibit_callback = True

    def update(self, *args, **kwargs):
        """Update the runtime data dictionary with new items.

        Args:
            *args: Positional arguments to pass to dict.update().
            **kwargs: Keyword arguments to pass to dict.update().
        """
        self._data.update(*args, **kwargs)
        self._call()

    def uninhibit(self):
        """Uninhibit the callback function."""
        self._inhibit_callback = False
        self._callback()

"""Meta module for Pyrox framework base classes and utilities."""
from __future__ import annotations

from abc import ABC, ABCMeta
from enum import Enum
import logging
import json
from pathlib import Path
import re
import sys
from typing import Any, Callable, Optional, Self, Type

__all__ = (
    'Buildable',
    'DEF_APP_NAME',
    'DEF_AUTHOR_NAME',
    'DEF_DATE_FMT',
    'DEF_FORMATTER',
    'DEF_ICON',
    'DEF_THEME',
    'DEF_VIEW_TYPE',
    'DEF_WIN_TITLE',
    'DEF_WIN_SIZE',
    'EnforcesNaming',
    'FactoryTypeMeta',
    'Loggable',
    'MetaFactory',
    'PyroxObject',
    'Runnable',
    'SnowFlake',
    'SupportsJsonLoading',
    'SupportsJsonSaving',
    'SupportsLoading',
    'SupportSaving',
    'TK_CURSORS',
)

ALLOWED_CHARS = re.compile(f'[^{r'a-zA-Z0-9_[]'}]')
ALLOWED_REV_CHARS = re.compile(f'[^{r'0-9.'}]')
ALLOWED_MOD_CHARS = re.compile(f'[^{r'a-zA-Z0-9_.-'}]')
DEF_APP_NAME = 'Pyrox Application'
DEF_AUTHOR_NAME = 'Pyrox Author'
DEF_VIEW_TYPE = 1
DEF_THEME = 'black'
DEF_WIN_TITLE = 'Pyrox Default Frame'
DEF_WIN_SIZE = '1024x768'
DEF_ICON = Path(__file__).resolve().parents[2] / "ui" / "icons" / "_def.ico"
DEF_FORMATTER = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
DEF_DATE_FMT = "%m/%d/%Y, %H:%M:%S"


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


class SimpleStream:
    """A simple stream that writes to a single provided callback.

    Attributes:
        callback: A callable that will be called with the text to write.
        closed: Whether the stream is closed.
    """

    def __init__(self, callback: Callable):
        if not callable(callback):
            raise TypeError('Callback must be a callable function.')
        self.callback = callback
        self.closed = False

    def write(self, text: str):
        """Write text to the callback."""
        if self.closed:
            return
        try:
            self.callback(text)
        except Exception as e:
            sys.__stderr__.write(f"SimpleStream error: {e}\n")

    def flush(self):
        """Flush the stream (no-op for SimpleStream)."""
        pass

    def close(self):
        """Close the stream."""
        self.closed = True


class MultiStream:
    """A stream that writes to multiple destinations simultaneously."""

    def __init__(self, *streams):
        self.streams = list(streams)
        self.closed = False

    def _fallback_write(self, text):
        """Fallback method to write to sys.__stderr__ if write fails."""
        sys.__stderr__.write(f"MultiStream error: {text}\n")

    def write(self, text):
        """Write text to all streams."""
        if self.closed:
            return

        for stream in self.streams:
            try:
                if hasattr(stream, 'write'):
                    stream.write(text)
            except Exception as e:
                self._fallback_write(e)

    def flush(self):
        """Flush all streams."""
        for stream in self.streams:
            try:
                if hasattr(stream, 'flush'):
                    stream.flush()
            except Exception as e:
                self._fallback_write(e)

    def close(self):
        """Close all streams."""
        self.closed = True
        for stream in self.streams:
            try:
                if hasattr(stream, 'close') and stream not in (sys.__stdout__, sys.__stderr__):
                    stream.close()
            except Exception as e:
                self._fallback_write(e)

    def add_stream(self, stream):
        """Add another stream to write to."""
        if stream not in self.streams:
            self.streams.append(stream)

    def remove_stream(self, stream):
        """Remove a stream from the list."""
        if stream in self.streams:
            self.streams.remove(stream)


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

    def __init__(self):
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


class LazyLoggable:
    """An easier mixin class that doesn't require a name property for logging.
    \n Rather, it uses the inheriting class's builtin name.
    """

    @classmethod
    def get_logger(self) -> logging.Logger:
        """Logger for this object.

        Returns:
            logging.Logger: The logger instance.
        """
        return Loggable.get_or_create_logger(name=self.__class__.__name__)


class PyroxObject(SnowFlake):
    """A base class for all Pyrox objects."""
    __slots__ = ()

    def __init__(self):
        super().__init__()

    def __repr__(self) -> str:
        return self.__class__.__name__


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
        description: Optional[str] = None
    ) -> None:
        super().__init__()
        self._name = name if name else self.__class__.__name__
        self._description = description if description else ''

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


class SupportsLoading(PyroxObject):
    """A meta class for all classes to derive from to obtain loading capabilities.

    Attributes:
        load_path: Path to load the object from.
    """
    __slots__ = ()

    def __init__(self):
        super().__init__()

    @property
    def load_path(self) -> Optional[Path]:
        """Path to load the object from.

        Returns:
            Optional[Path]: The path to load from.

        Raises:
            NotImplementedError: This property should be implemented in subclasses.
        """
        raise NotImplementedError("This property should be implemented in subclasses.")

    def load(self, path: Optional[Path] = None) -> Any:
        """Load the object from a file.

        Args:
            path: Path to load the object from. If not provided, uses the load_path attribute.

        Returns:
            Any: The loaded data.

        Raises:
            NotImplementedError: This method should be implemented in subclasses.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")

    def on_loaded(self, data: Any) -> None:
        """Method to be called after the object has been loaded.

        This method can be overridden in subclasses to perform additional actions after loading.

        Args:
            data: Data that was loaded from the file.
        """
        ...


class SupportSaving(PyroxObject):
    """A meta class for all classes to derive from to obtain saving capabilities.

    Attributes:
        save_path: Path to save the object to.
        save_data_callback: Callback to call when saving data.
    """
    __slots__ = ()

    def __init__(self):
        super().__init__()

    @property
    def save_path(self) -> Optional[Path]:
        """Path to save the object to.

        Returns:
            Optional[Path]: The path to save to.

        Raises:
            NotImplementedError: This property should be implemented in subclasses.
        """
        raise NotImplementedError("This property should be implemented in subclasses.")

    @property
    def save_data_callback(self) -> Optional[Callable]:
        """Callback to call when saving data.

        Returns:
            Optional[Callable]: The callback function.

        Raises:
            NotImplementedError: This property should be implemented in subclasses.
        """
        raise NotImplementedError("This property should be implemented in subclasses.")

    def save(self, path: Optional[Path] = None, data: Optional[Any] = None) -> None:
        """Save the object to a file.

        Args:
            path: Path to save the object to. If not provided, uses the save_path attribute.
            data: Data to save. If not provided, uses the save_data_callback attribute.

        Raises:
            NotImplementedError: This method should be implemented in subclasses.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")


class SupportsJsonSaving(SupportSaving):
    """A meta class for all classes to derive from to obtain JSON saving capabilities.

    Attributes:
        save_path: Path to save the object to.
        save_data_callback: Callback to call when saving data.
    """
    __slots__ = ()

    def save_to_json(self, path: Optional[Path] = None, data: Optional[dict] = None) -> None:
        """Save the object to a JSON file.

        Args:
            path: Path to save the object to. If not provided, uses the save_path attribute.
            data: Data to save. If not provided, uses the save_data_callback attribute.

        Raises:
            ValueError: If no path is provided for saving JSON data.
            IOError: If the file cannot be written.
        """
        path = path or self.save_path
        data = data or self.save_data_callback()
        if not path:
            raise ValueError("No path provided for saving JSON data.")

        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except (IOError, OSError) as e:
            raise IOError(f"Failed to save JSON to {path}: {e}")


class SupportsJsonLoading(SupportsLoading):
    """A meta class for all classes to derive from to obtain JSON loading capabilities."""
    __slots__ = ()

    def load_from_json(self, path: Optional[Path] = None) -> Any:
        """Load the object from a JSON file.

        Args:
            path: Path to load the object from. If not provided, uses the load_path attribute.

        Returns:
            Any: Loaded data from the JSON file, or None if file doesn't exist.
        """
        path = Path(path) if path else Path(self.load_path)
        if not path or not path.exists():
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.on_loaded(data)
                return data
        except (IOError, OSError, json.JSONDecodeError) as e:
            raise IOError(f"Failed to load JSON from {path}: {e}")


class Loggable(NamedPyroxObject):
    """A loggable entity, using the logging.Logger class.

    Args:
        name: Name to assign to this handler. Otherwise, defaults to class name.

    Attributes:
        logger: Logger for this loggable object.
    """
    curr_logging_level = logging.INFO
    _curr_loggers = {}

    __slots__ = ('_logger')

    def __init__(
        self,
        name: Optional[str] = None
    ) -> None:
        super().__init__(name=name)
        self._logger: logging.Logger = self._get_or_create_logger(
            name=name or self.__class__.__name__,
        )

    @property
    def logger(self) -> logging.Logger:
        """Logger for this loggable object.

        Returns:
            logging.Logger: The logger instance.
        """
        return self._logger

    @staticmethod
    def _create_logger(name: str = __name__) -> logging.Logger:
        """Create a logger that outputs to stderr (which gets captured)."""
        logger = Loggable._setup_standard_logger(name=name)
        Loggable._curr_loggers[name] = logger
        return logger

    @staticmethod
    def _get_or_create_logger(
        name: str = __name__,
    ) -> logging.Logger:
        """Get or create a logger with the specified name.

        Args:
            name: The name for the logger.

        Returns:
            logging.Logger: The logger instance.
        """
        return Loggable._curr_loggers.get(name, Loggable._create_logger(name=name))

    @staticmethod
    def _get_standard_handler(stream) -> logging.StreamHandler:
        """Get a standard logging handler that outputs to the specified stream.

        Args:
            stream: The stream to output logs to (default is sys.stderr).

        Returns:
            logging.StreamHandler: A configured StreamHandler instance.
        """
        handler = logging.StreamHandler(stream)
        formatter = logging.Formatter(fmt=DEF_FORMATTER, datefmt=DEF_DATE_FMT)
        handler.setFormatter(formatter)
        handler.setLevel(Loggable.curr_logging_level)
        return handler

    @staticmethod
    def _setup_standard_logger(name: str = None) -> logging.Logger:
        """Get a standard logger with the specified name.

        Args:
            name: The name for the logger.

        Returns:
            logging.Logger: A configured Logger instance.
        """
        logger = logging.getLogger(name)
        Loggable._remove_all_handlers(logger)
        handler = Loggable._get_standard_handler(sys.stderr)
        logger.addHandler(handler)
        logger.setLevel(Loggable.curr_logging_level)
        logger.propagate = False
        return logger

    @staticmethod
    def _remove_all_handlers(logger: logging.Logger) -> None:
        """Remove all handlers from the specified logger.

        Args:
            logger: The logger from which to remove handlers.
        """
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    @staticmethod
    def get_or_create_logger(name: str = __name__) -> logging.Logger:
        """Get or create a logger with the specified name.

        Args:
            name: The name for the logger.

        Returns:
            logging.Logger: The logger instance.
        """
        return Loggable._get_or_create_logger(name=name)

    @staticmethod
    def force_all_loggers_to_stderr():
        """Force all existing loggers to use sys.stderr."""

        # Update root logger
        Loggable._setup_standard_logger()

        # Update all existing loggers in the manager
        for name in list(logging.Logger.manager.loggerDict.keys()):
            Loggable._setup_standard_logger(name)

        # Update the Loggable class loggers too
        for name, _ in Loggable._curr_loggers.items():
            Loggable._setup_standard_logger(name)

    @staticmethod
    def set_logging_level(log_level: int = logging.INFO):
        """Set the logging level for all current loggers.

        Args:
            log_level: The logging level to set for all current loggers.
        """
        Loggable.curr_logging_level = log_level
        for logger in Loggable._curr_loggers.values():
            logger.setLevel(log_level)
            for handler in logger.handlers:
                handler.setLevel(log_level)


class Buildable(Loggable):
    """Denotes object is 'buildable' and supports build and refresh methods.

    Attributes:
        built: Whether the object has previously been built.
    """
    __slots__ = ('_built',)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._built: bool = False

    @property
    def built(self) -> bool:
        """Whether the object has previously been built.

        Returns:
            bool: True if the object has been built, False otherwise.
        """
        return self._built

    def build(self) -> None:
        """Build this object."""
        self._built = True

    def refresh(self) -> None:
        """Refresh this object."""


class Runnable(Buildable):
    """Denotes object is 'runnable' and supports run method.

    Attributes:
        running: Whether the object is currently in a running state.
    """
    __slots__ = ('_running', )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._running: bool = False

    @property
    def running(self) -> bool:
        """Whether the object is currently in a running state.

        Returns:
            bool: True if the object is running, False otherwise.
        """
        return self._running

    def start(self) -> None:
        """Start this object."""
        if self.built is False:
            self.build()
        self._running = True

    def stop(self) -> None:
        """Stop this object."""
        self._running = False


class MetaFactory(ABC, LazyLoggable):
    """Meta class for factory patterns.

    This meta class is used to create factories that can register and retrieve types.
    """

    _registered_types: dict = {}

    @classmethod
    def get_registered_types(cls) -> dict[str, Type]:
        """Get the registered types for this factory.

        Returns:
            dict: A dictionary of registered types.
        """
        return cls._registered_types

    @classmethod
    def register_type(
        cls,
        type_class: Type
    ) -> None:
        """Register a type with the factory.

        Args:
            type_class: The class type to register.
        """
        cls._registered_types[type_class.__name__] = type_class


class FactoryTypeMeta(ABCMeta, LazyLoggable):
    """Meta class for types that are used in factory patterns."""

    def __new__(
        cls,
        name,
        bases,
        attrs,
        **_
    ) -> Type[Self]:
        new_cls = super().__new__(cls, name, bases, attrs)

        factory = cls.get_factory()
        if factory is None:
            cls.get_logger().debug(f'FactoryTypeMeta: No factory found for class {name}.')
            return new_cls

        factory_class = cls.get_class()
        if factory_class is None:
            cls.get_logger().debug(f'FactoryTypeMeta: No factory class found for class {name}.')
            return new_cls

        if (name != factory_class.__name__ and
                issubclass(new_cls, factory_class)):
            factory = cls.get_factory()
            if factory is None:
                cls.get_logger().debug(f'FactoryTypeMeta: No factory found for class {name}.')
                return new_cls

            factory.register_type(new_cls)
        else:
            cls.get_logger().debug(
                f'FactoryTypeMeta: Class {name} is the factory class itself or does not subclass it.'
            )

        return new_cls

    @classmethod
    def get_class(cls) -> Optional[Type]:
        """Get the type that this meta class was created for, if any.

        Returns:
            Optional[Type]: The type, or None if not set.
        """
        return cls

    @classmethod
    def get_factory(cls) -> Optional[MetaFactory]:
        """Get the factory associated with this meta class, if any.

        Returns:
            Optional[MetaFactory]: The factory instance, or None if not set.
        """
        return None

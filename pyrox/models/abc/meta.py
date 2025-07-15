"""Meta module for Pyrox framework base classes and utilities."""
from __future__ import annotations

from enum import Enum
import inspect
import logging
import json
from pathlib import Path
import re
import sys
from typing import Any, Callable, Optional

__all__ = (
    'Buildable',
    'ConsolePanelHandler',
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
    'Loggable',
    'PyroxObject',
    'Runnable',
    'SnowFlake',
    'SupportsJsonLoading',
    'SupportsJsonSaving',
    'SupportsLoading',
    'SupportSaving',
    'TK_CURSORS',
)

ALLOWED_CHARS = re.compile(f'[^{r'a-zA-Z0-9_'}]')
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


class PyroxObject(SnowFlake):
    """A base class for all Pyrox objects."""
    __slots__ = ()

    def __init__(self):
        super().__init__()

    def __repr__(self) -> str:
        return self.__class__.__name__

    def get_all_properties(self) -> dict:
        """Get all properties of this object.

        Returns:
            dict: A dictionary of all properties of this object.
        """
        return {
            name: getattr(self, name)
            for name, _ in inspect.getmembers(type(self), lambda v: isinstance(v, property))
        }


class NamedPyroxObject(PyroxObject):
    """A base class for all Pyrox objects that have a name.

    Attributes:
        name: Name of the object.
        description: Description of the object.
    """
    __slots__ = ('_name', '_description')

    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        super().__init__()
        self._name = name or self.__class__.__name__
        self._description = description or ''

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
        path = Path(path) if path else self.load_path
        if not path or not path.exists():
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.on_loaded(data)
                return data
        except (IOError, OSError, json.JSONDecodeError) as e:
            raise IOError(f"Failed to load JSON from {path}: {e}")


class ConsolePanelHandler(logging.Handler):
    """A handler for logging that emits messages to specified callbacks.

    Attributes:
        callback: Callback to call when emitting a message.
        formatter: The logging formatter for this handler.
    """
    __slots__ = ('_callback', '_formatter')

    def __init__(self, callback: Optional[Callable] = None):
        super().__init__()
        self._callback: Callable = callback
        self._formatter: logging.Formatter = logging.Formatter(fmt=DEF_FORMATTER, datefmt=DEF_DATE_FMT)

    @property
    def formatter(self) -> logging.Formatter:
        """Get the formatter for this handler.

        Returns:
            logging.Formatter: The current formatter.
        """
        return self._formatter

    @formatter.setter
    def formatter(self, value: logging.Formatter) -> None:
        """Set the formatter for this handler.

        Args:
            value: Formatter to set for this handler.

        Raises:
            TypeError: If the value is not a logging.Formatter or None.
        """
        if isinstance(value, logging.Formatter) or value is None:
            self._formatter = value
        else:
            raise TypeError(f'Expected logging.Formatter, got {type(value)}')

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to the callback.

        Args:
            record: The log record to emit.
        """
        if self._callback:
            self._callback(self.format(record))

    def set_callback(self, callback: Callable) -> None:
        """Set the callback for this handler's emit method.

        Args:
            callback: Callback to set for this class's emit method.

        Raises:
            TypeError: If the callback is not callable.
        """
        if not callable(callback):
            raise TypeError(f'Expected callable, got {type(callback)}')
        self._callback = callback


class Loggable(NamedPyroxObject):
    """A loggable entity, using the logging.Logger class.

    Args:
        name: Name to assign to this handler. Otherwise, defaults to class name.
        add_to_globals: Whether to add this loggable's handler to the global handlers list.

    Attributes:
        logger: Logger for this loggable object.
        log_handler: User Handler for this loggable object.
    """
    global_handlers: list[logging.Handler] = []
    _curr_loggers = {}

    __slots__ = ('_logger', '_log_handler')

    def __init__(self, add_to_globals: bool = False, name: Optional[str] = None, **_):
        super().__init__(name=name)
        self._logger: logging.Logger = self._get(name=name or self.__class__.__name__,)
        self._log_handler = next((hndl for hndl in self._logger.handlers if isinstance(hndl, ConsolePanelHandler)), None)
        if not self._log_handler:
            self._log_handler: ConsolePanelHandler = ConsolePanelHandler()
            self._logger.addHandler(self._log_handler)

        if add_to_globals is True and self._log_handler not in Loggable.global_handlers:
            Loggable.global_handlers.append(self._log_handler)

    @property
    def log_handler(self) -> ConsolePanelHandler:
        """User Handler for this loggable object.

        Meant for user to modify with their own callbacks, for easy log displaying.

        Returns:
            ConsolePanelHandler: The log handler for this object.
        """
        return self._log_handler

    @property
    def logger(self) -> logging.Logger:
        """Logger for this loggable object.

        Returns:
            logging.Logger: The logger instance.
        """
        return self._logger

    @staticmethod
    def _get(name: str = __name__, ignore_globals: bool = False) -> logging.Logger:
        """Get or create a logger with the specified name.

        Args:
            name: The name for the logger.
            ignore_globals: Whether to ignore global handlers.

        Returns:
            logging.Logger: The logger instance.
        """
        if Loggable._curr_loggers.get(name):
            return Loggable._curr_loggers.get(name)

        _logger = logging.getLogger(name)
        _logger.setLevel(logging.INFO)

        cons = logging.StreamHandler()
        cons.setLevel(logging.INFO)

        formatter = logging.Formatter(fmt=DEF_FORMATTER, datefmt=DEF_DATE_FMT)

        cons.setFormatter(formatter)
        _logger.addHandler(cons)

        # additionally, apply any global handlers to the newly created logger
        if not ignore_globals:
            for glob in Loggable.global_handlers:
                if glob not in _logger.handlers:
                    _logger.addHandler(glob)

        Loggable._curr_loggers[name] = _logger
        return _logger

    @staticmethod
    def init_sys_excepthook():
        """Initialize the system exception hook to log uncaught exceptions."""
        def excepthook(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                return
            root_logger = logging.getLogger()
            root_logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        sys.excepthook = excepthook

    @staticmethod
    def set_logging_level(log_level: int = logging.INFO):
        """Set the logging level for all current loggers.

        Args:
            log_level: The logging level to set for all current loggers.
        """
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

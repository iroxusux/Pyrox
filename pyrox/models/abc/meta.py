"""meta module
    """
from __future__ import annotations


from enum import Enum
import gc
import inspect
import logging
import json
import os
from pathlib import Path
import re
from typing import Any, Callable, Optional, Union
from tkinter import Tk, Toplevel, Frame, LabelFrame, TclError, Widget
from ttkthemes import ThemedTk


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
    'View',
    'ViewType',
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
DEF_ICON = Path(__file__).resolve().parent.parent.parent / "ui" / "icons" / "_def.ico"
DEF_FORMATTER = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
DEF_DATE_FMT = "%m/%d/%Y, %H:%M:%S"


class TK_CURSORS:
    """.. description::
    Static class for python tkinter cursors.
    .. ------------------------------------------------------------
    .. package::
    models.abc.meta
    .. ------------------------------------------------------------
    .. attributes::
    ARROW: :class:`str`
        Arrow cursor.
    CIRCLE: :class:`str`
        Circle cursor.
    CLOCK: :class:`str`
        Clock cursor.
    CROSS: :class:`str`
        Cross cursor.
    DOTBOX: :class:`str`
        Dotbox cursor.
    EXCHANGE: :class:`str`
        Exchange cursor.
    FLEUR: :class:`str`
        Fleur cursor.
    HEART: :class:`str`
        Heart cursor.
    MAN: :class:`str`
        Man cursor.
    MOUSE: :class:`str`
        Mouse cursor.
    PIRATE: :class:`str`
        Pirate cursor.
    PLUS: :class:`str`
        Plus cursor.
    SHUTTLE: :class:`str`
        Shuttle cursor.
    SIZING: :class:`str`
        Sizing cursor.
    SPIDER: :class:`str`
        Spider cursor.
    SPRAYCAN: :class:`str`
        Spraycan cursor.
    STAR: :class:`str`
        Star cursor.
    TARGET: :class:`str`
        Target cursor.
    TCROSS: :class:`str`
        T-cross cursor.
    TREK: :class:`str`
        Trek cursor.
    """
    ARROW = "arrow"
    CIRCLE = "circle"
    CLOCK = "clock"
    CROSS = "cross"
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


class _IdGenerator:
    """.. description::
    Static class for id generation for :class:`SnowFlake`.
    Hosts a unique identifier `id` generator.
    .. ------------------------------------------------------------
    .. package::
    models.abc.meta
    """
    __slots__ = ()
    _ctr = 0

    @staticmethod
    def get_id() -> int:
        """.. description::
        get a unique ID from the :class:`_IdGenerator`.
        .. ------------------------------------------------------------
        .. returns::
            :type:`int`: Unique ID for a :class:`SnowFlake` object.
        """
        _IdGenerator._ctr += 1
        return _IdGenerator._ctr

    @staticmethod
    def curr_value() -> int:
        """Retrieve the current value of the ID generator
        .. ------------------------------------------------------------
        .. returns::
            :class:`int` current value
        """
        return _IdGenerator._ctr


class EnforcesNaming:
    """.. description::
    Helper meta class to enforce naming schemes across objects.
    .. ------------------------------------------------------------
    .. package::
    models.abc.meta
    """
    # store the last allowed characters for reference when showing exception message
    # this keeps the user from having to manually do this, but it IS just a best guess when the exception is raised
    __slots__ = ()
    _last_allowed_chars = ALLOWED_CHARS

    class InvalidNamingException(Exception):
        """.. description::
        Helper exception class to raise invalid naming exceptions.
        .. ------------------------------------------------------------
        .. package::
        models.abc.meta
        """

        def __init__(self,
                     message='Invalid naming scheme! Allowed chars are: '):
            self.message = message + f'{EnforcesNaming._last_allowed_chars.pattern}'
            super().__init__(self.message)

    @staticmethod
    def is_valid_rockwell_bool(text):
        """Check if a string is valid according to the Rockwell boolean naming scheme.
        .. ------------------------------------------------------------
        .. returns::
            :class:`bool` valid name
        """
        EnforcesNaming._last_allowed_chars = re.compile(f'[^{r'true|false'}]')
        if not text:
            return False
        if text == 'true' or text == 'false':
            return True
        return False

    @staticmethod
    def is_valid_string(text):
        """Check if a string is valid according to the naming scheme.
        .. ------------------------------------------------------------
        .. returns::
            :class:`bool` valid name
        """
        EnforcesNaming._last_allowed_chars = ALLOWED_CHARS
        if ALLOWED_CHARS.search(text):
            return False
        return True

    @staticmethod
    def is_valid_module_string(text):
        """Check if a string is valid according to the module naming scheme.
        .. ------------------------------------------------------------
        .. returns::
            :class:`bool` valid module name
        """
        EnforcesNaming._last_allowed_chars = ALLOWED_MOD_CHARS
        if ALLOWED_MOD_CHARS.search(text):
            return False
        return True

    @staticmethod
    def is_valid_revision_string(text):
        """Check if a string is valid according to the revision naming scheme.
        .. ------------------------------------------------------------
        .. returns::
            :class:`bool` valid revision name
        """
        EnforcesNaming._last_allowed_chars = ALLOWED_REV_CHARS
        if ALLOWED_REV_CHARS.search(text):
            return False
        return True


class SnowFlake:
    """.. description::
    A meta class for all classes to derive from to obtain unique IDs.
    .. ------------------------------------------------------------
    .. package::
    models.abc.meta
    .. ------------------------------------------------------------
    .. attributes::
    id: :type:`int`
        Unique identifer.
    """
    __slots__ = ('_id',)

    def __eq__(self, other: SnowFlake):
        if type(self) is type(other):
            return self.id == other.id
        return False

    def __hash__(self):
        return hash(self._id)

    def __init__(self):
        self._id = _IdGenerator.get_id()

    def __str__(self):
        return str(self.id)

    @property
    def id(self) -> int:
        """id of this object.
        .. ------------------------------------------------------------
        .. returns::
            :type:`int`: Unique identifier for this object.
        """
        return self._id


class RuntimeDict:
    """.. description::
    A dictionary-like class to store data.
    This class provides a way to store key-value pairs and automatically save the data
    whenever an item is added, updated, or deleted.
    .. ------------------------------------------------------------
    .. package::
    models.abc.meta
    .. ------------------------------------------------------------
    .. attributes::
    callback: :type:`Callable`
        A callback function that is called whenever the data is modified.
    data: :type:`dict`
        The dictionary that stores the runtime data.
    inhibit_callback: :type:`bool`
        Whether to inhibit the callback function from being called when data is modified.
    """
    __slots__ = ('_callback', '_data', '_inhibit_callback')

    def __contains__(self, key):
        """Check if a key exists in the runtime data dictionary."""
        return key in self._data

    def __getitem__(self, key):
        return self._data.get(key, None)

    def __init__(self, callback: Callable):
        if not callback or not callable(callback):
            raise ValueError('A valid callback function must be provided to RuntimeDict.')
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
        """Get the callback function."""
        return self._callback

    @callback.setter
    def callback(self, value: Callable):
        """Set the callback function."""
        if not value or not callable(value):
            raise ValueError('A valid callback function must be provided to RuntimeDict.')
        self._callback = value

    @property
    def data(self) -> dict:
        """Get the runtime data dictionary."""
        return self._data

    @data.setter
    def data(self, value: dict):
        """Set the runtime data dictionary."""
        if not isinstance(value, dict):
            raise TypeError('Runtime data must be a dictionary.')
        self._data = value
        self._callback()

    @property
    def inhibit_callback(self) -> bool:
        """Get whether the callback is inhibited."""
        return self._inhibit_callback

    @inhibit_callback.setter
    def inhibit_callback(self, value: bool):
        """Set whether the callback is inhibited."""
        if not isinstance(value, bool):
            raise TypeError('Inhibit callback must be a boolean value.')
        self._inhibit_callback = value

    def _call(self):
        """Call the callback function if it is set and not inhibited."""
        if not self._inhibit_callback:
            if callable(self._callback):
                self._callback()
            else:
                raise TypeError('Callback must be a callable function.')

    def clear(self):
        """Clear the runtime data dictionary."""
        self._data.clear()
        self._callback()

    def get(self, key, default=None):
        """Get an item from the runtime data dictionary."""
        return self._data.get(key, default)

    def inhibit(self):
        """Inhibit the callback function."""
        self._inhibit_callback = True

    def update(self, *args, **kwargs):
        """Update the runtime data dictionary with new items."""
        self._data.update(*args, **kwargs)
        self._callback()

    def uninhibit(self):
        """Uninhibit the callback function."""
        self._inhibit_callback = False
        self._callback()


class PyroxObject(SnowFlake):
    """.. description::
    A base class for all Pyrox objects.
    .. ------------------------------------------------------------
    .. package::
    models.abc.meta
    """
    __slots__ = ()

    def __init__(self):
        super().__init__()

    def __repr__(self):
        return self.__class__.__name__

    def get_all_properties(self) -> dict:
        """Get all properties of this object.
        .. ------------------------------------------------------------
        .. returns::
            :type:`dict`: A dictionary of all properties of this object.
        """
        return {
            name: getattr(self, name)
            for name, _ in inspect.getmembers(type(self), lambda v: isinstance(v, property))
        }


class NamedPyroxObject(PyroxObject):
    """.. description::
    A base class for all Pyrox objects that have a name.
    .. ------------------------------------------------------------
    .. package::
    models.abc.meta
    .. ------------------------------------------------------------
    .. attributes::
    name: :type:`str`
        Name of the object.
    """
    __slots__ = ('_name',)

    def __init__(self,
                 name: Optional[str] = None):
        super().__init__()
        self._name = name or self.__class__.__name__

    @property
    def name(self) -> str:
        """Name of the object.
        .. ------------------------------------------------------------
        .. returns::
            :type:`str`: Name of the object.
        """
        return self._name


class SupportsLoading(PyroxObject):
    """.. description::
    A meta class for all classes to derive from to obtain loading capabilities.
    .. ------------------------------------------------------------
    .. package::
    models.abc.meta
    .. ------------------------------------------------------------
    """

    __slots__ = ()

    def __init__(self):
        super().__init__()

    @property
    def load_path(self) -> Optional[Path]:
        """Path to load the object from.
        .. ------------------------------------------------------------
        .. returns::
            load_path: :type:`Path`
        """
        raise NotImplementedError("This property should be implemented in subclasses.")

    def load(self,
             path: Optional[Path] = None) -> Any:
        """Load the object from a file.
        .. arguments::
        path: Optional[:class:`Path`]
            Path to load the object from. If not provided, uses the `load_path` attribute
        .. ------------------------------------------------------------
        .. raises::
            NotImplementedError: This method and this doc-string should be implemented in subclasses.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")

    def on_loaded(self,
                  data: Any) -> None:
        """Method to be called after the object has been loaded.
        This method can be overridden in subclasses to perform additional actions after loading.
        .. ------------------------------------------------------------
        .. arguments::
        data: :type:`Any`
            Data that was loaded from the file.
        """
        ...


class SupportSaving(PyroxObject):
    """.. description::
    A meta class for all classes to derive from to obtain saving capabilities.
    .. ------------------------------------------------------------
    .. package::
    models.abc.meta
    .. ------------------------------------------------------------
    .. attributes::
    save_path: :type:`Path`
        Path to save the object to.
    save_data_callback: Optional[:class:`Callable`]
        Callback to call when saving data.
    """
    __slots__ = ()

    def __init__(self):
        super().__init__()

    @property
    def save_path(self) -> Optional[Path]:
        """Path to save the object to.
        .. ------------------------------------------------------------
        .. returns::
            save_path: :type:`Path`
        """
        raise NotImplementedError("This property should be implemented in subclasses.")

    @property
    def save_data_callback(self) -> Optional[Callable]:
        """Callback to call when saving data.
        .. ------------------------------------------------------------
        .. returns::
            save_data_callback: :type:`Callable`
        """
        raise NotImplementedError("This property should be implemented in subclasses.")

    def save(self,
             path: Optional[Path] = None,
             data: Optional[Any] = None) -> None:
        """Save the object to a file.
        .. ------------------------------------------------------------
        .. arguments::
        path: Optional[:class:`Path`]
            Path to save the object to. If not provided, uses the `save_path` attribute
        data: Optional[Any]
            Data to save. If not provided, uses the `save_data_callback` attribute.
        .. ------------------------------------------------------------
        .. raises::
            NotImplementedError: This method and this doc-string should be implemented in subclasses.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")


class SupportsJsonSaving(SupportSaving):
    """.. description::
    A meta class for all classes to derive from to obtain JSON saving capabilities.
    .. ------------------------------------------------------------
    .. package::
    models.abc.meta
    .. ------------------------------------------------------------
    .. attributes::
    save_path: :type:`Path`
        Path to save the object to.
    save_data_callback: Optional[:class:`Callable`]
        Callback to call when saving data. If not provided, uses the `data` attribute of the object.
    """
    __slots__ = ()

    def save_to_json(self,
                     path: Optional[Path] = None,
                     data: Optional[dict] = None) -> None:
        """Save the object to a JSON file.
        .. ------------------------------------------------------------
        .. arguments::
        path: Optional[:class:`Path`]
            Path to save the object to. If not provided, uses the `save_path` attribute
        data: Optional[:class:`dict`]
            Data to save. If not provided, uses the `save_data_callback` attribute.
        .. ------------------------------------------------------------
        .. raises::
            ValueError: If no path or data is provided for saving JSON data.
        """
        path = path or self.save_path
        data = data or self.save_data_callback()
        if not path:
            raise ValueError("No path provided for saving JSON data.")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)


class SupportsJsonLoading(SupportsLoading):
    """.. description::
    A meta class for all classes to derive from to obtain JSON loading capabilities.
    .. ------------------------------------------------------------
    .. package:: models.abc.meta
    .. ------------------------------------------------------------
    """
    __slots__ = ()

    def load_from_json(self,
                       path: Optional[Path] = None) -> Any:
        """Load the object from a JSON file.
        .. ------------------------------------------------------------
        .. arguments::
        path: Optional[:class:`Path`]
            Path to load the object from. If not provided, uses the `load_path` attribute
        .. ------------------------------------------------------------
        .. returns::
            :type:`Any`: Loaded data from the JSON file.
        """
        path = path or self.load_path
        if not os.path.isfile(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            self.on_loaded(json.load(f))


class ConsolePanelHandler(logging.Handler):
    """.. description::
    A handler for logging that emits messages to specified callbacks.
    .. ------------------------------------------------------------
    .. package::
    models.abc.meta
    .. ------------------------------------------------------------
    .. attributes::
    callback: :class:`Callable`
        Callback to call when emitting a message
    """
    __slots__ = ('_callback', '_formatter')

    def __init__(self,
                 callback: Optional[Callable] = None):
        super().__init__()
        self._callback: Callable = callback
        self._formatter: logging.Formatter = logging.Formatter(fmt=DEF_FORMATTER, datefmt=DEF_DATE_FMT)

    @property
    def formatter(self) -> logging.Formatter:
        """Get the formatter for this handler.
        .. ------------------------------------------------------------
        .. returns::
        formatter: :class:`logging.Formatter`
        """
        return self._formatter

    @formatter.setter
    def formatter(self, value: logging.Formatter) -> None:
        """Set the formatter for this handler.
        .. ------------------------------------------------------------
        .. arguments::
        value: :class:`logging.Formatter`
            Formatter to set for this handler.
        """
        if isinstance(value, logging.Formatter) or value is None:
            self._formatter = value
        else:
            raise TypeError(f'Expected logging.Formatter, got {type(value)}')

    def emit(self, record) -> None:
        """ Emit a log record to the callback.
        .. ------------------------------------------------------------
        .. arguments::
        record: :class:`logging.LogRecord`
            The log record to emit.
        """
        if self._callback:
            self._callback(self.format(record))

    def set_callback(self, callback: Callable) -> None:
        """Set the callback for this handler's emit method
        .. ------------------------------------------------------------
        .. arguments::
        callback: :def:`callable`
            Callback to set for this class's `emit` method.
        """
        self._callback = callback


class Loggable(NamedPyroxObject):
    """.. description::
    A loggable entity, using the `logging.Loggable` class.
    .. ------------------------------------------------------------
    .. package::
    models.abc.meta
    .. ------------------------------------------------------------
    .. arguments::
    name: Optional[str]
        Name to assign to this handler. Otherwise, defaults to `self.__class__.__name__`.
    add_to_globals: bool
        Whether to add this loggable's handler to the global handlers list.
    .. ------------------------------------------------------------
    .. attributes::
    logger: :class:`logging.Logger`
        `Logger` for this loggable object.
    log_handler: :class:`logging.Handler`
        User 'Handler' for this loggable object.
    """

    global_handlers: list[logging.Handler] = []
    _curr_loggers = {}

    __slots__ = ('_logger', '_log_handler')

    def __init__(self,
                 add_to_globals: bool = False,
                 name: Optional[str] = None,
                 **_):
        super().__init__(name=name)
        self._logger: logging.Logger = self._get(name=name or self.__class__.__name__,)
        self._log_handler = next((hndl for hndl in self._logger.handlers if isinstance(hndl, ConsolePanelHandler)), None)
        if not self._log_handler:
            self._log_handler: ConsolePanelHandler = ConsolePanelHandler()
            self._logger.addHandler(self._log_handler)  # add handler for user to create custom callbacks with

        if add_to_globals is True and self._log_handler not in Loggable.global_handlers:
            Loggable.global_handlers.append(self._log_handler)

    @property
    def log_handler(self) -> ConsolePanelHandler:
        """User 'Handler' for this loggable object.
        Meant for user to modify with their own callbacks, for easy log displaying.
        .. -------------------------------------------------------------------------
        .. returns::
        log_handler: :class:`logging.Handler`
        """
        return self._log_handler

    @property
    def logger(self) -> logging.Logger:
        """`Logger` for this loggable object.
        .. ------------------------------------------------------------
        .. returns::
            logger: :class:`logging.Logger`
        """
        return self._logger

    @staticmethod
    def _get(name: str = __name__,
             ignore_globals: bool = False):

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
    def set_logging_level(log_level: int = logging.INFO):
        """Set the logging level for all current loggers.
        .. ------------------------------------------------------------
        .. arguments::
        log_level: :type:`int`
            The logging level to set for all current loggers. Defaults to `logging.INFO`.
        """
        for logger in Loggable._curr_loggers.values():
            logger.setLevel(log_level)
            for handler in logger.handlers:
                handler.setLevel(log_level)


class Buildable(Loggable):
    """.. description::
    Denotes object is 'buildable' and supports `build` and `refresh` methods.
    .. ------------------------------------------------------------
    .. package::
    models.abc.meta
    .. ------------------------------------------------------------
    .. attributes::
    built: :type:`bool`
        The object has previously been built.
    """
    __slots__ = ('_built',)

    def __init__(self,
                 **kwargs):
        super().__init__(**kwargs)
        self._built: bool = False

    @property
    def built(self) -> bool:
        """The object has previously been built.
        .. ------------------------------------------------------------
        .. returns::
            built: :type:`bool`
        """
        return self._built

    def build(self) -> None:
        """Build this object
        """
        self._built = True

    def refresh(self) -> None:
        """Refresh this object.
        """


class Runnable(Buildable):
    """.. description::
    Denotes object is 'runnable' and supports `run` method.
    .. ------------------------------------------------------------
    .. package::
    models.abc.meta
    .. ------------------------------------------------------------
    .. attributes::
    running: :type:`bool`
        The object is currently in a `running` state.
    """
    __slots__ = ('_running', )

    def __init__(self,
                 **kwargs):
        super().__init__(**kwargs)
        self._running: bool = False

    @property
    def running(self) -> bool:
        """The object is currently in a `running` state.
        .. ------------------------------------------------------------
        .. returns::
            running: :type:`bool`
        """
        return self._running

    def start(self) -> None:
        """Start this object.
        """
        if self.built is False:
            self.build()
        self._running = True

    def stop(self) -> None:
        """Stop this object.
        """
        self._running = False


class ViewType(Enum):
    """Partial View Type Enumaration

    .. ------------------------------------------------------------

    .. package:: models.abc.meta
    """
    NA = 0
    ROOT = 1
    TOPLEVEL = 2
    EMBED = 3


class View(Runnable):
    """A meta view for displaying tracked GUI information.

    .. ------------------------------------------------------------

    .. package:: models.abc.meta

    .. ------------------------------------------------------------

    Arguments
    -----------
    parent: Optional[:class:`Union[Tk, Toplevel, Frame, LabelFrame]`]
        Parent of this partial view. Defaults to `None`, which will create a root view.

    .. ------------------------------------------------------------

    Attributes
    -----------
    parent: :class:`Union[Tk, Toplevel, Frame, LabelFrame]`
        Parent of this partial view.

    frame: :class:`Frame`
        Frame to mount widgets onto.
    """

    __slots__ = ('_frame', '_parent')

    def __init__(self,
                 parent: Union[Tk, Toplevel, Frame, LabelFrame] = None,
                 custom_frame_class: Optional[type[Frame]] = None):
        super().__init__()
        self._parent: Union[Tk, ThemedTk, Toplevel, Frame, LabelFrame] = parent

        if custom_frame_class:
            self._frame = custom_frame_class(master=self._parent)
        else:
            self._frame = Frame(master=self._parent, padx=2, pady=2)

        self._frame.pack(fill='both', expand=True)

    @property
    def frame(self) -> Frame:
        """Frame to mount widgets onto.

        .. ------------------------------------------------------------

        Returns
        -----------
            frame: :class:`Frame`
        """
        return self._frame

    @property
    def parent(self) -> Union[Tk, Toplevel, Frame, LabelFrame]:
        """The parent of this partial view.

        .. ------------------------------------------------------------

        Returns
        -----------
            parent: :class:`Union[Tk, Toplevel, Frame, LabelFrame]`
        """
        return self._parent

    def center(self) -> None:
        """center this partial view in the window it resides in.

        """
        x = (self.parent.winfo_screenwidth() - self.parent.winfo_reqwidth()) // 2
        y = (self.parent.winfo_screenheight() - self.parent.winfo_reqheight()) // 2
        self.parent.geometry(f'+{x}+{y}')

    def clear(self,
              widget: Optional[Widget] = None) -> None:
        """Clear a widget of all children.

        Defaults to all children under this :class:`Frame`.

        Arguments
        ----------
        widget: Optional[:class:`Widget`]
            The widget to clear all children widgets from.

        """
        if not widget:
            widget = self.frame

        for child in widget.winfo_children():
            child.pack_forget()

    def close(self) -> None:
        """Close this partial view.

        """
        self.stop()
        try:
            if isinstance(self.parent, Tk):
                self.parent.quit()
                self.parent.destroy()
            elif isinstance(self.parent, Toplevel):
                self.parent.destroy()
        except TclError:
            self.logger.error('TclError: Could not destroy the parent window')
        finally:
            gc.collect()  # process garbage collection for tk/tcl elements

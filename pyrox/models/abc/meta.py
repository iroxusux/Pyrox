"""meta module
    """
from __future__ import annotations


from enum import Enum
import gc
import logging
from pathlib import Path
import re
from typing import Callable, Optional, Union
from tkinter import Tk, Toplevel, Frame, LabelFrame, TclError, Widget
from ttkthemes import ThemedTk


__all__ = (
    'Buildable',
    'ConsolePanelHandler',
    'EnforcesNaming',
    'Loggable',
    'PyroxObject',
    'Runnable',
    'SnowFlake',
    'View',
    'ViewType',
    'DEF_VIEW_TYPE',
    'DEF_THEME',
    'DEF_WIN_TITLE',
    'DEF_WIN_SIZE',
    'DEF_ICON',
    'DEF_FORMATTER',
    'DEF_DATE_FMT',
    'TK_CURSORS',
)

ALLOWED_CHARS = re.compile(f'[^{r'a-zA-Z0-9_'}]')
DEF_VIEW_TYPE = 1
DEF_THEME = 'black'
DEF_WIN_TITLE = 'Pyrox Default Frame'
DEF_WIN_SIZE = '1024x768'
DEF_ICON = Path(__file__).resolve().parent.parent.parent / "ui" / "icons" / "_def.ico"
DEF_FORMATTER = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
DEF_DATE_FMT = "%m/%d/%Y, %H:%M:%S"


class TK_CURSORS:
    """Static class python tkinter cursors.

    .. ------------------------------------------------------------

    .. package:: models.abc.meta

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
    """Static class for id generation for :class:`SnowFlake`.

    Hosts a unique identifier `id` generator.

    .. ------------------------------------------------------------

    .. package:: models.abc.meta

    """

    __slots__ = ()

    _ctr = 0

    @staticmethod
    def get_id() -> int:
        """get a unique ID from the :class:`_IdGenerator`.

        .. ------------------------------------------------------------

        Returns
        -----------
            :type:`int`: Unique ID for a :class:`SnowFlake` object.
        """
        _IdGenerator._ctr += 1
        return _IdGenerator._ctr

    @staticmethod
    def curr_value() -> int:
        """Retrieve the current value of the ID generator

        .. ------------------------------------------------------------

        Returns
        ----------
            :class:`int` current value
        """
        return _IdGenerator._ctr


class EnforcesNaming:
    """Helper meta class to enforce naming schemes across objects.

    Valid naming scheme is alphanumeric and underscores only.

    .. ------------------------------------------------------------

    .. package:: models.abc.meta

    """

    class InvalidNamingException(Exception):
        """Helper exception class to raise invalid naming exceptions.

        .. ------------------------------------------------------------

        .. package:: models.abc.meta

        """

        def __init__(self,
                     message='Invalid naming scheme! Allowed chars are %s' % ALLOWED_CHARS):
            self.message = message
            super().__init__(self.message)

    @staticmethod
    def is_valid_string(text):
        """Check if a string is valid according to the naming scheme.

        .. ------------------------------------------------------------

        Returns
        ----------
            :class:`bool` valid name
        """
        if ALLOWED_CHARS.search(text):
            return False
        return True


class SnowFlake:
    """A meta class for all classes to derive from to obtain unique IDs.

    .. ------------------------------------------------------------

    .. package:: models.abc.meta

    .. ------------------------------------------------------------

    Attributes
    -----------
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

    def __init__(self,
                 **kwargs):
        self._id = _IdGenerator.get_id()
        super().__init__(**kwargs)

    def __str__(self):
        return str(self.id)

    @property
    def id(self) -> int:
        """id: :type:`int`
        Unique identifer.

        .. ------------------------------------------------------------

        Returns
        -----------
            :type:`int`: unique identifier
        """
        return self._id


class ConsolePanelHandler(logging.Handler):
    """A handler for logging that emits messages to specified callbacks.

    .. ------------------------------------------------------------

    .. package:: models.abc.meta

    .. ------------------------------------------------------------

    Arguments
    -----------

    callback: :class:`Callable`
        Callback to call when emitting a message

    """

    __slots__ = ('_callback',)

    def __init__(self, callback: Callable):
        super().__init__()
        self._callback: Callable = callback
        self._formatter: logging.Formatter = logging.Formatter(fmt=DEF_FORMATTER, datefmt=DEF_DATE_FMT)

    @property
    def formatter(self) -> logging.Formatter:
        """Get the formatter for this handler.

        .. ------------------------------------------------------------

        Returns
        -----------
            formatter: :class:`logging.Formatter`
        """
        return self._formatter

    @formatter.setter
    def formatter(self, value: logging.Formatter) -> None:
        """Set the formatter for this handler.

        .. ------------------------------------------------------------

        Arguments
        ----------
        value: :class:`logging.Formatter`
            Formatter to set for this handler.
        """
        if isinstance(value, logging.Formatter) or value is None:
            self._formatter = value
        else:
            raise TypeError(f'Expected logging.Formatter, got {type(value)}')

    def emit(self, record) -> None:
        if self._callback:
            self._callback(self.format(record))

    def set_callback(self, callback: Callable) -> None:
        """Set the callback for this handler's emit method

        Arguments
        ----------
        callback: :def:`callable`
            Callback to set for this class's `emit` method.
        """
        self._callback = callback


class Loggable(SnowFlake):
    """A loggable entity, using the `logging.Loggable` class.

    .. ------------------------------------------------------------

    .. package:: models.abc.meta

    .. ------------------------------------------------------------

    Arguments
    -----------

    name: Optional[:class:`str`]
        Name to assign to this handler.

        Otherwise, defaults to `self.__class__.__name__`.

    Attributes
    -----------
    logger: :class:`logging.Logger`
        `Logger` for this loggable object.

    log_handler: :class:`logging.Handler`
        User 'Handler' for this loggable object.

        Meant for user to modify with their own callbacks, for easy log displaying.


    """

    global_handlers: list[logging.Handler] = []
    _curr_loggers = {}

    __slots__ = ('_logger', '_log_handler')

    def __init__(self,
                 *_,
                 name: Optional[str] = None,
                 add_to_globals: bool = False,
                 **kwargs):
        super().__init__(**kwargs)
        self._logger: logging.Logger = self._get(name=name if name else self.__class__.__name__)
        self._log_handler: ConsolePanelHandler = ConsolePanelHandler(None)

        # check in case we got a hashed logger with the handler already attached (somehow?)
        if self._log_handler not in self._logger.handlers:
            self._logger.addHandler(self._log_handler)  # add handler for user to create custom callbacks with

        if add_to_globals is True and self._log_handler not in Loggable.global_handlers:
            Loggable.global_handlers.append(self._log_handler)

    @property
    def log_handler(self) -> ConsolePanelHandler:
        """User 'Handler' for this loggable object.

        Meant for user to modify with their own callbacks, for easy log displaying.

        .. -------------------------------------------------------------------------

        Returns
        ----------
        log_handler: :class:`logging.Handler`
        """
        return self._log_handler

    @property
    def logger(self) -> logging.Logger:
        """`Logger` for this loggable object.

        .. ------------------------------------------------------------

        Returns
        --------
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
                _logger.addHandler(glob)

        Loggable._curr_loggers[name] = _logger

        return _logger

    def add_handler(self,
                    handler: logging.Handler):
        """Add a log :class:`logging.Handler` to this logger object.

        .. ------------------------------------------------------------

        Arguments
        --------
        handler: :class:`logging.Handler`
            Handler to add to this logging object.

        """
        if handler not in self._logger.handlers:
            self._logger.addHandler(handler)

        # re-assign the hashed local list of loggers
        Loggable._curr_loggers[self._logger.name] = self._logger

    def error(self,
              msg: str):
        """Send `error` message to logger handler.

        .. ------------------------------------------------------------

        Arguments
        --------
        msg: :class:`str`
            Message to post to handler.

        """
        try:
            self._logger.error(msg)
        except TclError:
            pass

    def info(self,
             msg: str):
        """Send `info` message to logger handler.

        .. ------------------------------------------------------------

        Arguments
        --------
        msg: :class:`str`
            Message to post to handler.

        """
        self._logger.info(msg)

    @staticmethod
    def set_logging_level(log_level: int = logging.INFO):
        for logger in Loggable._curr_loggers.values():
            logger.setLevel(log_level)
            for handler in logger.handlers:
                handler.setLevel(log_level)

    def warning(self,
                msg: str):
        """Send `warning` message to logger handler.

        .. ------------------------------------------------------------

        Arguments
        --------
        msg: :class:`str`
            Message to post to handler.

        """
        self._logger.warning(msg)


class PyroxObject(Loggable):
    """A base class for all Pyrox objects.

    .. ------------------------------------------------------------

    .. package:: models.abc.meta

    .. ------------------------------------------------------------

    Attributes
    -----------
    logger: :class:`logging.Logger`
        Logger for this object.
    """

    __slots__ = ()

    def __init__(self,
                 **kwargs):
        super().__init__(**kwargs)

    def gui_interface_attributes(self) -> list[str]:
        """Return a set of attributes that are intended for GUI interface.

        This method is meant to be overridden by subclasses to provide
        specific attributes that should be displayed in a GUI context.

        Returns
        ----------
            :type:`list[str]`: Set of attribute names.
        """
        return self.public_attributes()

    def public_attributes(self) -> list[str]:
        """Return a set of public attributes for this object.

        This method is meant to be overridden by subclasses to provide
        specific attributes that should be considered public.

        Returns
        ----------
            :type:`list[str]`: Set of public attribute names.
        """
        return {attr for attr in dir(self) if not attr.startswith('_')
                and not callable(getattr(self, attr))
                and not isinstance(getattr(self, attr), property)}


class Buildable(PyroxObject):
    """Denotes object is 'buildable' and supports `build` and `refresh` methods.

    Also, supports `built` property.

    .. ------------------------------------------------------------

    .. package:: models.abc.meta

    .. ------------------------------------------------------------

    Attributes
    -----------
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

        Returns
        -----------
            built: :type:`bool`
        """
        return self._built

    def build(self,
              **_):
        """Build this object
        """
        self._built = True

    def refresh(self,
                **_):
        """Refresh this object.
        """


class Runnable(Buildable):
    """Denotes object is 'runnable' and supports `run` method.

    Also, supports `running` property.

    .. ------------------------------------------------------------

    .. package:: models.abc.meta

    .. ------------------------------------------------------------

    Attributes
    -----------
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

        Returns
        ----------
            running: :type:`bool`
        """
        return self._running

    def run(self) -> None:
        """Run this object.
        """

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

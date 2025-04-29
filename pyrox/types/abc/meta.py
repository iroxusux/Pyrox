"""meta module
    """
from __future__ import annotations


from enum import Enum
from dataclasses import dataclass
import logging
import os
from typing import Callable, Optional, Literal, Union
from tkinter import Tk, Toplevel, Frame, LabelFrame, Widget
import unittest


from ttkthemes import ThemedTk


__all__ = (
    'Buildable',
    'SnowFlake',
    'PartialView',
    'PartialViewConfiguration',
    'DEF_VIEW_TYPE',
    'DEF_THEME',
    'DEF_WIN_TITLE',
    'DEF_WIN_SIZE',
    'DEF_ICON',
    'DEF_FORMATTER',
    'DEF_DATE_FMT',
)


DEF_VIEW_TYPE = 1
DEF_THEME = 'black'
DEF_WIN_TITLE = 'Pyrox Default Frame'
DEF_WIN_SIZE = '1024x768'
DEF_ICON = f'{os.path.dirname(os.path.abspath(__file__))}\\..\\..\\ui\\icons\\_def.ico'
DEF_FORMATTER = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
DEF_DATE_FMT = "%m/%d/%Y, %H:%M:%S"


class _IdGenerator:
    """Static class for id generation for :class:`SnowFlake`.

    Hosts a unique identifier `id` generator.

    .. ------------------------------------------------------------

    .. package:: types.abc.meta

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


class SnowFlake:
    """A meta class for all classes to derive from.

    .. ------------------------------------------------------------

    .. package:: types.abc.meta

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

    def __init__(self):
        self._id = _IdGenerator.get_id()

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

    .. package:: types.abc.meta

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
        self.formatter: logging.Formatter = logging.Formatter(fmt=DEF_FORMATTER, datefmt=DEF_DATE_FMT)

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

    .. package:: types.abc.meta

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
                 name: Optional[str] = None):
        super().__init__()
        self._logger: logging.Logger = self._get(name=name if name else self.__class__.__name__)
        self._log_handler: logging.Handler = ConsolePanelHandler(None)

        # check in case we got a hashed logger with the handler already attached (somehow?)
        if self._log_handler not in self._logger.handlers:
            self._logger.addHandler(self._log_handler)  # add handler for user to create custom callbacks with

    @property
    def log_handler(self) -> logging.Handler:
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
        self._logger.error(msg)

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


class LoggableUnitTest(unittest.TestCase, Loggable):
    """Loggable Unit Test TestCase
    """

    def __init__(self, methodName="runTest"):
        unittest.TestCase.__init__(self, methodName)
        Loggable.__init__(self)


class Buildable(Loggable):
    """Denotes object is 'buildable' and supports `build` and `refresh` methods.

    Also, supports `built` property.

    .. ------------------------------------------------------------

    .. package:: types.abc.meta

    .. ------------------------------------------------------------

    Attributes
    -----------
    built: :type:`bool`
        The object has previously been built.
    """

    __slots__ = ('_built',)

    def __init__(self):
        super().__init__()
        self._built: bool = False

    @property
    def built(self) -> bool:
        """The object has previously been built.

        Returns
        -----------
            built: :type:`bool`
        """

    def build(self):
        """Build this object
        """
        self._built = True

    def refresh(self):
        """Refresh this object.
        """
        ...  # pylint: disable=unnecessary_ellipsis


class Runnable(Buildable):
    """Denotes object is 'runnable' and supports `run` method.

    Also, supports `running` property.

    .. ------------------------------------------------------------

    .. package:: types.abc.meta

    .. ------------------------------------------------------------

    Attributes
    -----------
    running: :type:`bool`
        The object is currently in a `running` state.
    """

    __slots__ = ('_running', )

    def __init__(self):
        super().__init__()
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
        self._running = True

    def stop(self) -> None:
        """Stop this object.
        """
        self._running = False


class PartialViewType(Enum):
    """Partial View Type Enumaration

    .. ------------------------------------------------------------

    .. package:: types.abc.meta
    """
    NA = 0
    ROOT = 1
    TOPLEVEL = 2
    EMBED = 3


@dataclass
class PartialViewConfiguration:
    """Partial View Configuration

    .. ------------------------------------------------------------

    .. package:: types.abc.meta

    .. ------------------------------------------------------------

    Attributes
    --------

    name: :type:`str`

    icon: :type:`str`

    win_size: :type:`str`

    theme: :type:`str`

    parent: Optional[Union[:type:`Tk`, :type:`Toplevel`, :type:`Frame`, :type:`LabelFrame`]]

    view_type: :class:`PartialViewType`

    """
    name: Optional[str] = DEF_WIN_TITLE
    icon: Optional[str] = DEF_ICON
    win_size: Optional[str] = DEF_WIN_SIZE
    theme: Optional[str] = DEF_THEME
    parent: Optional[Union[Tk, Toplevel, Frame, LabelFrame]] = None
    view_type: PartialViewType = PartialViewType.NA


class PartialView(Runnable):
    """A partial meta view for mounting :class:`Application` and :class:`View` to.

    .. ------------------------------------------------------------

    .. package:: types.abc.meta

    .. ------------------------------------------------------------

    Arguments
    -----------
    name: Optional[:type:`str`]
        Name of this partial view.

    config: :class:`PartialViewConfiguration`
        Configuration class for a :class:`PartialView`.

    .. ------------------------------------------------------------

    Attributes
    -----------
    name: Optional[:type:`str`]
        Name of this partial view.

    parent: :class:`Union[Tk, Toplevel, Frame, LabelFrame]`
        The parent of this partial view.

    frame: :class:`Frame`
        Frame to mount widgets onto.

    view_type: Literal[`1`, `2`, `3`]
        Type of view this view was created as. (Root, TopLevel or Embeded).

    config: :class:`PartialViewConfiguration`
        The configuration this view was built with.
    """

    __slots__ = ('_frame', '_name', '_parent', '_config')

    def __init__(self,
                 config: Optional[PartialViewConfiguration] = PartialViewConfiguration()):
        super().__init__()

        self._config: PartialViewConfiguration = config
        self._name: str = self._config.name

        if self._config.view_type is PartialViewType.ROOT:
            if self._config.theme:
                self._parent = ThemedTk(theme=self._config.theme)
            else:
                self._parent = Tk()

        elif self._config.view_type is PartialViewType.TOPLEVEL:
            self._parent = Toplevel()

        elif self._config.view_type is PartialViewType.EMBED:
            self._parent = self._config.parent

        else:
            raise ValueError(f'Could not create a partial view from type {self._config.view_type}')

        if not self._parent:
            return

        self._frame = Frame(master=self._parent, padx=2, pady=2)
        self._frame.pack(fill='both', expand=True)

        if self._config.view_type is PartialViewType.EMBED:
            return

        self._parent.protocol('WM_DELETE_WINDOW', self.close)

        if self._config.name:
            self._parent.title(self._config.name)

        if self._config.icon:
            self._parent.iconbitmap(self._config.icon)

        if self._config.win_size:
            self._parent.geometry(self._config.win_size)

    @property
    def config(self) -> PartialViewConfiguration:
        """The configuration this view was built with.

        .. ------------------------------------------------------------

        Returns
        -----------
            config: :class:`PartialViewConfiguration`
        """
        return self._config

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
    def name(self) -> Optional[str]:
        """Name of this partial view.

        .. ------------------------------------------------------------

        Returns
        -----------
            name: Optional[:type:`str`]
        """
        return self._name

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
            child.destroy()

    def close(self) -> None:
        """Close this partial view.

        """
        self.stop()
        self.parent.destroy()

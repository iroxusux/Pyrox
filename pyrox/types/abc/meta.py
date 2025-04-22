"""meta module
    """
from __future__ import annotations


import logging
import os
from typing import Optional, Literal, TypedDict, Union
from tkinter import Tk, Toplevel, Frame, LabelFrame, Widget


from ttkthemes import ThemedTk


__all__ = (
    'Buildable',
    'SnowFlake',
    'PartialView',
    'PartialViewConfiguration',
    'DEF_TYPE',
    'DEF_THEME',
    'DEF_WIN_TITLE',
    'DEF_WIN_SIZE',
    'DEF_ICON',
)


DEF_TYPE = 1
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

    Hosts a unique identifier `id`.

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

    callback: :class:`callable`
        Callback to call when emitting a message

    """

    __slots__ = ('_callback',)

    def __init__(self, callback: callable):
        super().__init__()
        self._callback = callback
        self.formatter = logging.Formatter(fmt=DEF_FORMATTER, datefmt=DEF_DATE_FMT)

    def emit(self, record):
        self._callback(self.format(record))

    def set_callback(self, callback: callable):
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


    """

    global_handlers: list[logging.Handler] = []
    _curr_loggers = {}

    __slots__ = ('_logger',)

    def __init__(self,
                 name: Optional[str] = None):
        super().__init__()
        self._logger: logging.Logger = self._get(name=name if name else self.__class__.__name__)

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


class PartialViewConfiguration(TypedDict):
    """Partial View Configuration

    .. ------------------------------------------------------------

    .. package:: types.abc.meta

    .. ------------------------------------------------------------

    Attributes
    --------

    title: :type:`str`

    icon: :type:`str`

    win_size: :type:`str`

    theme: :type:`str`

    parent: Optional[Union[:type:`Tk`, :type:`Toplevel`, :type:`Frame`, :type:`LabelFrame`]]

    """

    title: Optional[str] = DEF_WIN_TITLE
    icon: Optional[str] = DEF_ICON
    win_size: Optional[str] = DEF_WIN_SIZE
    theme: Optional[str] = DEF_THEME
    parent: Optional[Union[Tk, Toplevel, Frame, LabelFrame]] = None

    @classmethod
    def generic(cls,
                name: Optional[str] = DEF_WIN_TITLE) -> dict:
        """get a generic version of a partial view

        .. ------------------------------------------------------------

        Arguments
        ----------
        name: Optional[:type:`str`]
            Name of the frame to create.

        .. ------------------------------------------------------------


        Returns
        --------
        ::

            cls({
            'title': {name},
            'icon': DEF_ICON,
            'win_size': DEF_WIN_SIZE,
            'theme': DEF_THEME,
            'parent': None
            })
        """
        return cls({
            'title': name,
            'icon': DEF_ICON,
            'win_size': DEF_WIN_SIZE,
            'theme': DEF_THEME,
            'parent': None
        })


class PartialView(Buildable):
    """A partial meta view for mounting :class:`Application` and :class:`View` to.

    .. ------------------------------------------------------------

    .. package:: types.abc.meta

    .. ------------------------------------------------------------

    Arguments
    -----------
    name: Optional[:type:`str`]
        Name of this partial view.

    view_type: Literal[`1`, `2`, `3`]
        Type of view to create. (Root, TopLevel or Embeded).

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

    __slots__ = ('_frame', '_name', '_parent', '_view_type', '_config')

    def __init__(self,
                 name: Optional[str] = DEF_WIN_TITLE,
                 view_type: Literal[1, 2, 3] = DEF_TYPE,
                 config: Optional[PartialViewConfiguration] = PartialViewConfiguration.generic()):
        super().__init__()
        self._name: str = name
        self._view_type: Literal[1, 2, 3] = int(view_type)
        self._config: PartialViewConfiguration = config

        if self._view_type == 1:
            if config['theme']:
                self._parent = ThemedTk(theme=config['theme'])
            else:
                self._parent = Tk()

        elif self._view_type == 2:
            self._parent = Toplevel()

        elif self._view_type == 3:
            self._parent = config['parent']

        else:
            raise ValueError(f'Could not create a partial view from type {self._view_type}')

        if not self._parent:
            return

        self._frame = Frame(master=self._parent, padx=2, pady=2)
        self._frame.pack(fill='both', expand=True)

        if self._view_type == 3:
            return

        if config['title']:
            self._parent.title(config['title'])

        if config['icon']:
            self._parent.iconbitmap(config['icon'])

        if config['win_size']:
            self._parent.geometry(config['win_size'])

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

    @property
    def view_type(self) -> Literal[1, 2, 3]:
        """Type of view this view was created as (Root or TopLevel).

        .. ------------------------------------------------------------

        Returns
        -----------
            view_type: Literal[`1`, `2`, `3`]
        """
        return self._view_type

    def center(self) -> None:
        """center this partial view in the window it resides in.

        """
        x = (self.parent.winfo_screenwidth() - self.parent.winfo_reqwidth()) // 2
        y = (self.parent.winfo_screenheight() - self.parent.winfo_reqheight()) // 2
        self.parent.geometry(f'+{x}+{y}')

    def clear(self,
              widget: Optional[Widget] = None) -> None:
        """Clear a particular widget of all children.

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
        self.parent.destroy()

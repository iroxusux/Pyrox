"""meta module
    """
from __future__ import annotations


import os
from typing import Optional, Literal, TypedDict, Union
from tkinter import Tk, Toplevel, Frame, LabelFrame


from ttkthemes import ThemedStyle


__all__ = (
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
DEF_WIN_TITLE = 'pyrox Default Frame'
DEF_WIN_SIZE = '1024x768'
DEF_ICON = f'{os.path.dirname(os.path.abspath(__file__))}\\..\\..\\ui\\icons\\_def.ico'


class _IdGenerator:
    """Static class for id generation for :class:`SnowFlake`.

    Hosts a unique identifier `id` generator.

    .. ------------------------------------------------------------

    .. package:: types.abc.meta

    """

    _ctr = 0
    curr_value = _ctr

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
    id: int

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


class PartialViewConfiguration(TypedDict):
    """Partial View Configuration

    .. ------------------------------------------------------------

    .. package:: types.abc.meta

    """
    title: Optional[str] = DEF_WIN_TITLE
    icon: Optional[str] = DEF_ICON
    win_size: Optional[str] = DEF_WIN_SIZE
    theme: Optional[ThemedStyle] = DEF_THEME

    @classmethod
    def generic(cls) -> dict:
        """get a generic version of a partial view

        .. ------------------------------------------------------------

        Returns
        --------
        ::

            cls({
            'title': DEF_WIN_TITLE,
            'icon': DEF_ICON,
            'win_size': DEF_WIN_SIZE,
            'theme': DEF_THEME
            }
        """
        return cls({
            'title': DEF_WIN_TITLE,
            'icon': DEF_ICON,
            'win_size': DEF_WIN_SIZE,
            'theme': DEF_THEME
        })


class PartialView(SnowFlake):
    """A partial meta view for mounting :class:`Application` and :class:`View` to.

    .. ------------------------------------------------------------

    .. package:: types.abc.meta

    .. ------------------------------------------------------------

    Arguments
    -----------
    name: Optional[:type:`str`]
        Name of this partial view.

    view_type: Literal[`1`, `2`]
        Type of view to create. (Root or TopLevel).

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

    view_type: Literal[`1`, `2`]
        Type of view this view was created as. (Root or TopLevel).
    """

    frame: Frame
    name: Optional[str]
    parent: Union[Tk, Toplevel, Frame, LabelFrame]
    view_type: Literal[1, 2]

    def __init__(self,
                 name: Optional[str] = DEF_WIN_TITLE,
                 view_type: Literal[1, 2] = DEF_TYPE,
                 config: Optional[PartialViewConfiguration] = PartialViewConfiguration.generic()):
        super().__init__()
        self._name: str = name
        self._view_type: Literal[1, 2] = int(view_type)
        self._config: PartialViewConfiguration = config
        self._themed_style = ThemedStyle()

        if self._view_type == 1:
            self._parent = Tk()

        elif self._view_type == 2:
            self._parent = Toplevel()

        else:
            raise ValueError(f'Could not create a partial view from type {self._view_type}')

        self._frame = Frame(self.parent, padx=2, pady=2)

        if config['title']:
            self.parent.title(config['title'])

        if config['icon']:
            self.parent.iconbitmap(config['icon'])

        if config['win_size']:
            self.parent.geometry(config['win_size'])

        if config['theme'] and self._view_type == 1:
            self._themed_style.set_theme(config['theme'])

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
    def view_type(self) -> Literal[1, 2]:
        """Type of view this view was created as. (Root or TopLevel).

        .. ------------------------------------------------------------

        Returns
        -----------
            view_type: Literal[`1`, `2`]
        """
        return self._view_type

    def close(self) -> None:
        """Close this partial view.

        """
        self.parent.destroy()

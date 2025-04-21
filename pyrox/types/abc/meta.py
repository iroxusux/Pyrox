"""meta module
    """
from __future__ import annotations


import os
from typing import Optional, Literal, TypedDict, Union
from tkinter import Tk, Toplevel, Frame, LabelFrame


from ttkthemes import ThemedTk


from .buildable import Buildable


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
DEF_WIN_TITLE = 'Pyrox Default Frame'
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
    parent: Optional[Union[Tk, Toplevel, Frame, LabelFrame]]

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


class PartialView(SnowFlake, Buildable):
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
    """

    def __init__(self,
                 name: Optional[str] = DEF_WIN_TITLE,
                 view_type: Literal[1, 2, 3] = DEF_TYPE,
                 config: Optional[PartialViewConfiguration] = PartialViewConfiguration.generic()):
        SnowFlake.__init__(self)
        Buildable.__init__(self)
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
        self._frame.pack()

        if self._view_type == 3:
            return

        if config['title']:
            self._parent.title(config['title'])

        if config['icon']:
            self._parent.iconbitmap(config['icon'])

        if config['win_size']:
            self._parent.geometry(config['win_size'])

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
        """Type of view this view was created as. (Root or TopLevel).

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

    def clear(self) -> None:
        """Clear this partial view of all children.

        """
        for child in self.frame.winfo_children():
            child.destroy()

    def close(self) -> None:
        """Close this partial view.

        """
        self.parent.destroy()

"""application abc types
    """
from __future__ import annotations


import os
from typing import Literal, TYPE_CHECKING, TypedDict, Union


from tkinter import Menu, Tk, Toplevel


from .meta import PartialView, PartialViewConfiguration, SnowFlake


if TYPE_CHECKING:
    from .model import Model


DEF_TYPE = 1
DEF_THEME = 'black'
DEF_WIN_TITLE = 'Indicon LLC Emulation Manager Frame'
DEF_WIN_SIZE = '1024x768'
DEF_ICON = f'{os.path.dirname(os.path.abspath(__file__))}\\..\\..\\ui\\icons\\_def.ico'


__all__ = (
    'BaseMenu',
    'ApplicationTask',
    'PartialApplicationConfiguration',
    'PartialApplication',
)


class BaseMenu(SnowFlake):
    """Base menu for use in a ui :class:`Application`.

    .. ------------------------------------------------------------

    .. package:: types.abc.application

    .. ------------------------------------------------------------

    Attributes
    -----------
    menu: :type:`Tk.Menu`
        The Tk value member for this :class:`BaseMenu`.

    root: Union[:class:`Tk`, :class:`TopLevel`]
        The parent root item of this menu.

    """
    menu: Menu
    root: Union[Tk, Toplevel]

    def __init__(self,
                 root: Union[Tk, Toplevel]):
        super().__init__()
        self._root = root
        self._menu = Menu(self.root)

    @property
    def menu(self) -> Menu:
        """The Tk value member for this :class:`BaseMenu`.

        .. ------------------------------------------------------------

        Returns
        -----------
            menu: :type:`Tk.Menu`
        """
        return self._menu

    @property
    def root(self) -> Union[Tk, Toplevel]:
        """The parent root item of this :class:`BaseMenu`.

        .. ------------------------------------------------------------

        Returns
        -----------
            root: Union[:class:`Tk`, :class:`TopLevel`]
        """
        return self._root


class ApplicationTask(SnowFlake):
    """model task for injecting functionality into an existing model.

    .. ------------------------------------------------------------

    .. package:: types.abc.application

    .. ------------------------------------------------------------

    Attributes
    -----------
    application: :class:`PartialApplication`
        The parent application of this task.

    model: :class:`Model`
        The model this task reflects.
    """
    application: 'PartialApplication'
    model: Model

    def __init__(self,
                 application: 'PartialApplication',
                 model: Model):
        super().__init__()
        self._application: 'PartialApplication' = application
        self._model: Model = model

    @property
    def application(self) -> 'PartialApplication':
        """The parent application of this task.

        .. ------------------------------------------------------------

        Returns
        -----------
            application: :class:`PartialApplication`
        """
        return self._application

    @property
    def model(self) -> Model:
        """The model this task reflects.

        .. ------------------------------------------------------------

        Returns
        -----------
            model: :class:`Model`
        """
        return self._model


class PartialApplicationConfiguration(TypedDict):
    """application configuration

    .. ------------------------------------------------------------

    .. package:: types.abc.application
    """
    name: str
    type: Literal[1, 2]
    view_config: PartialViewConfiguration

    @classmethod
    def generic_toplevel(cls) -> dict:
        """get a generic version of an application configuration

        for a toplevel application

        .. ------------------------------------------------------------

        Returns
        --------
        ::

            cls({
            'name': 'Default Application',
            'type': 2,
            'view_config': PartialViewConfiguration(),
            }
        """
        return cls({
            'name': 'Default Application',
            'type': 2,
            'view_config': PartialViewConfiguration.generic()
        })

    @classmethod
    def generic_root(cls) -> dict:
        """get a generic version of an application configuration

        for a root level application

        .. ------------------------------------------------------------

        Returns
        --------
        ::

            cls({
            'name': 'Default Application',
            'type': 1,
            'view_config': PartialViewConfiguration(),
            }
        """
        return cls({
            'name': 'Default Application',
            'type': 1,
            'view_config': PartialViewConfiguration.generic(),
        })


class PartialApplication(PartialView):
    """Represents a :class:`PartialView` in the form of a Partial Application.

    .. ------------------------------------------------------------

    .. package:: types.abc.application

    .. ------------------------------------------------------------


    Attributes
    --------
    model :class:`Model`
        Model the application was built with.

    config :class:`PartialApplicationConfiguration`
        Configuration for this :class:`PartialApplication`.

    """
    model: Model
    config: PartialApplicationConfiguration

    def __init__(self,
                 model: Model,
                 config: PartialApplicationConfiguration):
        super().__init__(name=config['name'],
                         view_type=config['type'],
                         config=config['view_config'])
        self._model: Model = model
        self._config: PartialApplicationConfiguration = config

    @property
    def model(self) -> Model:
        """Model the application was built with.

        .. ------------------------------------------------------------

        Returns
        --------
            model :class:`Model`
        """
        return self._model

    @property
    def config(self) -> PartialApplicationConfiguration:
        """Configuration for this :class:`PartialApplication`.

        .. ------------------------------------------------------------

        Returns
        --------
            config :class:`PartialApplicationConfiguration`
        """
        return self._config

    def build(self) -> None:
        """build the application around the model
        """
        ...

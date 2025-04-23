"""application abc types
    """
from __future__ import annotations


import os
from typing import Literal, Optional, TypedDict, Union


from tkinter import Menu, Tk, Toplevel


from .meta import Buildable, PartialView, PartialViewConfiguration, SnowFlake
from .model import PartialModel
from .list import HashList


from ...services.dir_services import get_appdata


DEF_TYPE = 1
DEF_THEME = 'black'
DEF_WIN_TITLE = 'Indicon LLC Emulation Manager Frame'
DEF_WIN_SIZE = '1024x768'
DEF_ICON = f'{os.path.dirname(os.path.abspath(__file__))}\\..\\..\\ui\\icons\\_def.ico'


__all__ = (
    'BaseMenu',
    'PartialApplicationTask',
    'PartialApplicationConfiguration',
    'PartialApplication',
)


class BaseMenu(Buildable):
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

    __slots__ = ('_root', '_menu')

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


class PartialApplicationTask(Buildable):
    """model task for injecting functionality into an existing model.

    .. ------------------------------------------------------------

    .. package:: types.abc.application

    .. ------------------------------------------------------------

    Attributes
    -----------
    application: :class:`PartialApplication`
        The parent application of this task.

    model: :class:`PartialModel`
        The model this task reflects.
    """

    __slots__ = ('_application', '_model')

    def __init__(self,
                 application: 'PartialApplication',
                 model: PartialModel):
        super().__init__()
        self._application: 'PartialApplication' = application
        self._model: PartialModel = model

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
    def model(self) -> PartialModel:
        """The model this task reflects.

        .. ------------------------------------------------------------

        Returns
        -----------
            model: :class:`PartialModel`
        """
        return self._model


class PartialApplicationConfiguration(TypedDict):
    """application configuration

    .. ------------------------------------------------------------

    .. package:: types.abc.application

    .. ------------------------------------------------------------

    Attributes
    --------

    name: :type:`str`

    type: :type:`int`

    view_config: :class:`TypedDict`

    """
    name: str
    type: Literal[1, 2]
    view_config: PartialViewConfiguration

    @classmethod
    def generic_toplevel(cls,
                         name: Optional[str] = 'Default Application') -> dict:
        """get a generic version of an application configuration

        for a toplevel application

        .. ------------------------------------------------------------

        Arguments
        ----------
        name: Optional[:type:`str`]
            Name of the application to create.

        .. ------------------------------------------------------------

        Returns
        --------
        ::

            cls({
            'name': {name},
            'type': 2,
            'view_config': PartialViewConfiguration(),
            }
        """
        return cls({
            'name': name,
            'type': 2,
            'view_config': PartialViewConfiguration.generic(name=name)
        })

    @classmethod
    def generic_root(cls,
                     name: Optional[str] = 'Default Application') -> dict:
        """get a generic version of an application configuration

        for a root level application

        .. ------------------------------------------------------------

        Arguments
        ----------
        name: Optional[:type:`str`]
            Name of the application to create.

        .. ------------------------------------------------------------

        Returns
        --------
        ::

            cls({
            'name': {name},
            'type': 1,
            'view_config': PartialViewConfiguration(),
            }
        """
        return cls({
            'name': name,
            'type': 1,
            'view_config': PartialViewConfiguration.generic(name=name),
        })


class PartialApplication(PartialView):
    """Represents a :class:`PartialView` in the form of a Partial Application.

    .. ------------------------------------------------------------

    .. package:: types.abc.application

    .. ------------------------------------------------------------


    Attributes
    --------
    main_model :class:`Model`
        Model the application was built with / main associated model.

    model_hash :class:`HashList`
        Hashed list of all models associated with this application.

    config :class:`PartialApplicationConfiguration`
        Configuration for this :class:`PartialApplication`.

    """

    def __init__(self,
                 model: PartialModel,
                 config: PartialApplicationConfiguration):
        super().__init__(name=config['name'],
                         view_type=config['type'],
                         config=config['view_config'])

        if not os.path.isdir(self.appdata_dir):
            os.mkdir(self.appdata_dir)

        self._model_hash = HashList(SnowFlake.id.__name__)
        self._config: PartialApplicationConfiguration = config

        if model:
            self._main_model_id: int = model.id
            self._model_hash.append(model)
        else:
            self._main_model_id = None

    @property
    def appdata_dir(self) -> str:
        """Get the application data directory for this :class:`Application`.

        .. ---------------------------------------------------------------------

        Returns
        ----------
            :class:`str` `ApplicationDataDirectory`
        """
        return get_appdata() + f'/{self.name}'

    @property
    def main_model(self) -> Optional[PartialModel]:
        """The current main :class:`Model` of the :class:`Application`.

        .. ------------------------------------------------------------

        Returns
        --------
            model :class:`Model` | None
        """
        return self._model_hash.by_key(self._main_model_id)

    @property
    def model_hash(self) -> HashList[PartialModel]:
        """Hashed list of all models associated with this application.

        Returns
        ----------
            model_hash :class:`HashList`
        """
        return self._model_hash

    @property
    def parent(self) -> Union[Tk, Toplevel]:
        """The parent of this partial application.

        .. ------------------------------------------------------------

        Returns
        -----------
            parent: :class:`Union[Tk, Toplevel]`
        """
        return self._parent

    @property
    def config(self) -> PartialApplicationConfiguration:
        """Configuration for this :class:`PartialApplication`.

        .. ------------------------------------------------------------

        Returns
        --------
            config :class:`PartialApplicationConfiguration`
        """
        return self._config

    def add_model(self,
                  model: PartialModel) -> None:
        """Add a :class:`Model` to this :class:`Application`.

        Arguments
        ----------
        model :class:`PartialModel`
            Model to add to this application.
        """
        self._model_hash.append(model)
        model.build()

    def build(self) -> None:
        """build the application around the model
        """

    def set_model(self,
                  model: PartialModel):
        """Set a new model for this :class:`Application`.

        Will trigger a `build` event if a model is given (Not `None`).

        .. ------------------------------------------------------------

        Arguments
        -----------

        model: :class:`Model`
            Model to set as application main model.

        .. ------------------------------------------------------------

        Raises
        -----------
        :class:`ValueError`
            Incorrect model type was passed to application


        """
        if model is not None and not isinstance(model, PartialModel):
            raise TypeError(f'Model must be of type `Model`, not {type(model)}...')

        self._model_hash.append(model)
        self._main_model_id = model.id

        if self.main_model:
            self.build()

"""application abc types
    """
from __future__ import annotations


from dataclasses import dataclass, field
import os
from typing import Optional, Self, Union


from tkinter import (
    Event,
    Menu,
    Tk,
    Toplevel,
)


from .meta import Buildable, SnowFlake, Runnable, DEF_WIN_TITLE
from .meta import PartialView as View
from .meta import PartialViewConfiguration as ViewConfiguration
from .meta import PartialViewType as ViewType
from .model import PartialModel
from .list import HashList


DEF_TYPE = 1
DEF_THEME = 'black'
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


class PartialApplicationTask(Runnable):
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


@dataclass
class PartialApplicationConfiguration:
    """application configuration

    .. ------------------------------------------------------------

    .. package:: types.abc.application

    .. ------------------------------------------------------------

    Attributes
    --------

    headless: :type:`bool`

    name: :type:`str`

    view_config: :class:`TypedDict`

    """
    headless: bool = False
    inc_log_window: bool = False
    tasks: list[PartialApplicationTask] = field(default_factory=list)
    view_config: ViewConfiguration = field(default_factory=ViewConfiguration)

    @classmethod
    def _common_assembly(cls,
                         headless: bool,
                         inc_log_window: bool,
                         tasks: list[PartialApplicationTask],
                         view_config: ViewConfiguration) -> Self:
        return cls(
            headless=headless,
            inc_log_window=inc_log_window,
            tasks=tasks,
            view_config=view_config
        )

    @classmethod
    def toplevel(cls,
                 headless: bool = True,
                 inc_log_window: bool = False,
                 tasks: list[PartialApplicationTask] = None,
                 view_config: ViewConfiguration = None) -> Self:
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
        if not view_config:
            view_config = ViewConfiguration(name=DEF_WIN_TITLE,
                                            view_type=ViewType.TOPLEVEL)
        return PartialApplicationConfiguration._common_assembly(headless=headless,
                                                                inc_log_window=inc_log_window,
                                                                tasks=tasks,
                                                                view_config=view_config)

    @classmethod
    def root(cls,
             headless: bool = False,
             inc_log_window: bool = True,
             tasks: list[PartialApplicationTask] = None,
             view_config: ViewConfiguration = None) -> Self:
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

        if not view_config:
            view_config = ViewConfiguration(name=DEF_WIN_TITLE,
                                            view_type=ViewType.ROOT)
        return PartialApplicationConfiguration._common_assembly(headless=headless,
                                                                inc_log_window=inc_log_window,
                                                                tasks=tasks,
                                                                view_config=view_config)


class PartialApplication(View):
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
                 model: PartialModel = None,
                 config: PartialApplicationConfiguration = None):

        if not config:
            raise ValueError('Cannot create an application without a configuration!')

        super().__init__(config=config.view_config)

        self._running: bool = False
        self._model_hash = HashList(SnowFlake.id.__name__)
        self._config: PartialApplicationConfiguration = config

        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(0, weight=1)

        self._main_model_id = None
        _ = self.set_model(model) if model else None

    @property
    def config(self) -> PartialApplicationConfiguration:
        """Configuration for this :class:`PartialApplication`.

        .. ------------------------------------------------------------

        Returns
        --------
            config :class:`PartialApplicationConfiguration`
        """
        return self._config

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

    def add_model(self,
                  model: PartialModel) -> PartialModel:
        """Add a :class:`Model` to this :class:`Application`.

        Arguments
        ----------
        model :class:`PartialModel`
            Model to add to this application.

        .. ------------------------------------------------------------

        Raises
        -----------
        :class:`ValueError`
            Incorrect model type was passed to application

        .. ------------------------------------------------------------

        Returns
        ----------
        model :class:`PartialModel`
            Model to add to this application.
        """
        if not issubclass(type(model), PartialModel):
            raise TypeError(f'Model must be of type `Model`, not {type(model)}...')

        self._model_hash.append(model)

        model.build()

        return model

    def on_pre_run(self) -> None:
        """Method that is called directly before calling parent Tk `mainloop`.

        By this point, all models, view models and views should be created.

        This allows some extra logic to occur before our app begins.

        .. ------------------------------------------------------------

        Note: it is recommenbed to override this method to create your own functionality.
        """

    def start(self) -> None:
        self.on_pre_run()
        self.frame.after(100, lambda: self.logger.info('Ready...'))
        self.parent.focus()
        super().start()
        if isinstance(self.parent, Tk):
            self.parent.mainloop()

    def set_model(self,
                  model: PartialModel):
        """Set a new model for this :class:`Application`.

        Will trigger a `build` event if a model is given (Not `None`).

        .. ------------------------------------------------------------

        Arguments
        -----------

        model: :class:`Model`
            Model to set as application main model.


        """

        self._main_model_id = self.add_model(model).id

        if self.main_model:
            self.build()

    def toggle_fullscreen(self, event: Optional[Event] = None) -> None:
        """Toggle full-screen for this :class:`Application`.

        .. ------------------------------------------------------------

        Arguments
        -----------

        event: Optional[:class:`Event`]
            Optional key event passed to this method.

        """
        if event.keysym == 'F11':
            state = not self.parent.attributes('-fullscreen')
            self.parent.attributes('-fullscreen', state)
        elif self.parent.attributes('-fullscreen'):
            self.parent.attributes('-fullscreen', False)

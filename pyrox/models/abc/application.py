"""application abc types
    """
from __future__ import annotations


from dataclasses import dataclass, field
import gc
from tkinter import Frame, TclError
from typing import Optional, Self, Union


from tkinter import (
    Event,
    Menu,
    Tk,
    Toplevel,
)


from ttkthemes import ThemedTk


from .meta import (
    Buildable,
    Runnable,
    PartialViewConfiguration,
    ViewType,
    DEF_WIN_SIZE,
    DEF_WIN_TITLE,
    DEF_THEME,
    DEF_ICON,
)

from .model import PartialModel
from ..abc.meta import Loggable


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

    @model.setter
    def model(self, value):
        self._model = value


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
    inc_organizer: bool = False
    inc_workspace: bool = False
    title: Optional[str] = DEF_WIN_TITLE
    theme: Optional[str] = DEF_THEME
    type_: ViewType = ViewType.ROOT
    icon: Optional[str] = DEF_ICON
    size_: Optional[str] = DEF_WIN_SIZE
    tasks: list[PartialApplicationTask] = field(default_factory=list)
    view_config: PartialViewConfiguration = field(default_factory=PartialViewConfiguration)
    application: Union[Tk, ThemedTk, None] = None

    @classmethod
    def _common_assembly(cls,
                         headless: bool,
                         inc_log_window: bool,
                         inc_organizer: bool,
                         inc_workspace: bool,
                         title: str,
                         theme: str,
                         type_: ViewType,
                         icon: str,
                         size_: str,
                         tasks: list[PartialApplicationTask],
                         view_config: PartialViewConfiguration,
                         application: Union[Tk, ThemedTk, None]) -> Self:
        return cls(
            headless=headless,
            inc_log_window=inc_log_window,
            inc_organizer=inc_organizer,
            inc_workspace=inc_workspace,
            title=title,
            theme=theme,
            type_=type_,
            icon=icon,
            size_=size_,
            tasks=tasks,
            view_config=view_config,
            application=application
        )

    @classmethod
    def toplevel(cls) -> Self:
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
        return PartialApplicationConfiguration._common_assembly(headless=False,
                                                                inc_log_window=False,
                                                                inc_organizer=False,
                                                                inc_workspace=True,
                                                                title=DEF_WIN_TITLE,
                                                                theme=DEF_THEME,
                                                                type_=ViewType.TOPLEVEL,
                                                                icon=DEF_ICON,
                                                                size_=DEF_WIN_SIZE,
                                                                tasks=[],
                                                                view_config=PartialViewConfiguration(),
                                                                application=Toplevel)

    @classmethod
    def root(cls) -> Self:
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
        return PartialApplicationConfiguration._common_assembly(headless=False,
                                                                inc_log_window=True,
                                                                inc_organizer=True,
                                                                inc_workspace=True,
                                                                title=DEF_WIN_TITLE,
                                                                theme=DEF_THEME,
                                                                type_=ViewType.ROOT,
                                                                icon=DEF_ICON,
                                                                size_=DEF_WIN_SIZE,
                                                                tasks=[],
                                                                view_config=PartialViewConfiguration(),
                                                                application=ThemedTk)


class PartialApplication(Runnable):
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
                 config: PartialApplicationConfiguration) -> None:

        super().__init__()

        if config is None:
            config = PartialApplicationConfiguration.root()

        self._config: PartialApplicationConfiguration = config
        self._application: Union[Tk, ThemedTk, None] = None
        Loggable.global_handlers.append(self._log_handler)

    @property
    def application(self) -> Union[Tk, ThemedTk, None]:
        """The application instance for this :class:`PartialApplication`.

        .. ------------------------------------------------------------

        Returns
        -----------
            application: Union[:class:`Tk`, :class:`ThemedTk`, None]
        """
        return self._application

    @application.setter
    def application(self, value: Union[Tk, ThemedTk, None]) -> None:
        self._application = value

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
    def frame(self) -> Frame:
        """The frame for this :class:`PartialApplication`.

        .. ------------------------------------------------------------

        Returns
        -----------
            frame: :class:`Frame`
        """
        return self._frame

    def build(self) -> Self:
        """Build this :class:`PartialApplication`.

        .. ------------------------------------------------------------

        Arguments
        -----------
        **kwargs: dict
            Additional keyword arguments to pass to the build method.

        Returns
        --------
            self: :class:`PartialApplication`
        """
        if self.config.application == Tk:
            self.application = Tk()
        elif self.config.application == ThemedTk:
            self.application = ThemedTk(theme=self.config.theme)
        elif self.config.application == Toplevel:
            self.application = Toplevel()

        if self.application:
            self.application.protocol('WM_DELETE_WINDOW', self.close)
            self.application.title(self.config.title)
            self.application.iconbitmap(self.config.icon)
            self.application.geometry(self.config.size_)
            self._frame: Frame = Frame(master=self.application)
            self._frame.pack(fill='both', expand=True)
        else:
            raise ValueError('Application type is not supported. '
                             'Please use Tk, ThemedTk or Toplevel.')

        super().build()

    def center(self) -> None:
        """center this application's view in the window it resides in.

        """
        x = (self.application.winfo_screenwidth() - self.application.winfo_reqwidth()) // 2
        y = (self.application.winfo_screenheight() - self.application.winfo_reqheight()) // 2
        self.application.geometry(f'+{x}+{y}')

    def close(self) -> None:
        """Close this application.

        """
        self.stop()
        try:
            if isinstance(self.application, Tk):
                self.application.quit()
                self.application.destroy()
            elif isinstance(self.application, Toplevel):
                self.application.destroy()
        except TclError:
            self.logger.error('TclError: Could not destroy the parent window')
        finally:
            gc.collect()  # process garbage collection for tk/tcl elements

    def on_pre_run(self) -> None:
        """Method that is called directly before calling parent Tk `mainloop`.

        By this point, all models, view models and views should be created.

        This allows some extra logic to occur before our app begins.

        .. ------------------------------------------------------------

        Note: it is recommenbed to override this method to create your own functionality.
        """

    def start(self) -> None:
        super().start()
        self.on_pre_run()
        self.application.after(100, lambda: self.logger.info('Ready...'))
        self.application.focus()
        self.application.mainloop()

    def stop(self) -> None:
        super().stop()

    def toggle_fullscreen(self, event: Optional[Event] = None) -> None:
        """Toggle full-screen for this :class:`Application`.

        .. ------------------------------------------------------------

        Arguments
        -----------

        event: Optional[:class:`Event`]
            Optional key event passed to this method.

        """
        if event.keysym == 'F11':
            state = not self.view.parent.attributes('-fullscreen')
            self.view.parent.attributes('-fullscreen', state)
        elif self.view.parent.attributes('-fullscreen'):
            self.view.parent.attributes('-fullscreen', False)

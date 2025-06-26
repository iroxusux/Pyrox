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
    ViewType,
    DEF_WIN_SIZE,
    DEF_WIN_TITLE,
    DEF_THEME,
    DEF_ICON,
)

from .list import HashList


__all__ = (
    'BaseMenu',
    'ApplicationTask',
    'ApplicationConfiguration',
    'Application',
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


class MainApplicationMenu(BaseMenu):
    """Application `Main` Menu.

    Inherited from :class:`BaseMenu`, this parent class acts as the main menu for a root application

    .. ------------------------------------------------------------

    .. package:: types.application

    .. ------------------------------------------------------------

    Arguments
    -----------
    root: Union[:class:`Tk`, :class:`Toplevel`]
        The root tk object this menu belongs to.

    .. ------------------------------------------------------------

    Attributes
    -----------
    edit: :class:`Menu`
        The Edit :class:`Menu` for this :class:`MainApplicationMenu`.

    file: :class:`Menu`
        The File :class:`Menu` for this :class:`MainApplicationMenu`

    help: :class:`Menu`
        The Help :class:`Menu` for this :class:`MainApplicationMenu`

    tools: :class:`Menu`
        The Tools :class:`Menu` for this :class:`MainApplicationMenu`

    view: :class:`Menu`
        The View :class:`Menu` for this :class:`MainApplicationMenu`
    """

    __slots__ = ('_active_models', '_file', '_edit', '_tools', '_view', '_help', '_on_new_model')

    def __init__(self,
                 root: Union[Tk, Toplevel]):
        super().__init__(root=root)
        self._file: Menu = Menu(self.menu, name='file', tearoff=0)
        self._edit: Menu = Menu(self.menu, name='edit', tearoff=0)
        self._tools: Menu = Menu(self.menu, name='tools', tearoff=0)
        self._view: Menu = Menu(self.menu, name='view', tearoff=0)
        self._help: Menu = Menu(self.menu, name='help', tearoff=0)

        self.menu.add_cascade(label='File', menu=self.file)
        self.menu.add_cascade(label='Edit', menu=self.edit)
        self.menu.add_cascade(label='Tools', menu=self.tools)
        self.menu.add_cascade(label='View', menu=self.view)
        self.menu.add_cascade(label='Help', menu=self.help)

        self.root.config(menu=self.menu)

    @property
    def edit(self) -> Menu:
        """
        The Edit :class:`Menu` for this :class:`MainApplicationMenu`.

        .. ------------------------------------------------------------

        Returns
        -----------
            edit: :class:`Menu`
        """
        return self._edit

    @property
    def file(self) -> Menu:
        """
        The File :class:`Menu` for this :class:`MainApplicationMenu`.

        .. ------------------------------------------------------------

        Returns
        -----------
            file: :class:`Menu`
        """
        return self._file

    @property
    def help(self) -> Menu:
        """
        The Help :class:`Menu` for this :class:`MainApplicationMenu`.

        .. ------------------------------------------------------------

        Returns
        -----------
            help: :class:`Menu`
        """
        return self._help

    @property
    def tools(self) -> Menu:
        """
        The Tools :class:`Menu` for this :class:`MainApplicationMenu`.

        .. ------------------------------------------------------------

        Returns
        -----------
            tools: :class:`Menu`
        """
        return self._tools

    @property
    def view(self) -> Menu:
        """
        The View :class:`Menu` for this :class:`MainApplicationMenu`.

        .. ------------------------------------------------------------

        Returns
        -----------
            view: :class:`Menu`
        """
        return self._view

    @staticmethod
    def get_menu_commands(menu: Menu) -> dict:
        """Get all menu commands for a specified tk :class:`Menu`.

        .. ------------------------------------------------------------

        Arguments
        -----------

        menu: :class:`Menu`
            Menu to get all commands for.

        """
        cmds = {}
        try:
            for x in range(menu.index('end')+1):
                if menu.type(x) == 'command':
                    label = menu.entrycget(x, 'label')
                    cmd = menu.entrycget(x, 'command')
                    cmds[label] = cmd
        except TypeError:
            pass

        return cmds


class ApplicationTask(Runnable):
    """model task for injecting functionality into an existing model.

    .. ------------------------------------------------------------

    .. package:: models.abc.application

    .. ------------------------------------------------------------

    Attributes
    -----------
    application: :class:`PartialApplication`
        The parent application of this task.
    """

    __slots__ = ('_application')

    def __init__(self,
                 application: 'Application'):
        super().__init__()
        self._application: 'Application' = application

    def __repr__(self):
        return self.__class__.__name__

    @property
    def application(self) -> 'Application':
        """The parent application of this task.

        .. ------------------------------------------------------------

        Returns
        -----------
            application: :class:`PartialApplication`
        """
        return self._application

    @application.setter
    def application(self, value: 'Application'):
        self._application = value

    def inject(self) -> None:
        """Inject this task into the hosting application
        """

    def start(self) -> None:
        """Run this task
        """


@dataclass
class ApplicationConfiguration:
    """application configuration

    .. ------------------------------------------------------------

    .. package:: models.abc.application

    .. ------------------------------------------------------------

    Attributes
    --------

    headless: :type:`bool`
        If True, the application will not create a main window.

    title: :type:`str`
        The title of the application window.

    theme: :type:`str`
        The theme to use for the application window.

    type_: :class:`ViewType`
        The type of the application view, which can be one of the predefined view types.

    icon: :type:`str`
        The icon to use for the application window.

    size_: :type:`str`
        The size of the application window, specified as a string (e.g., "800x600").

    tasks: :type:`list[PartialApplicationTask]`
        A list of tasks to be executed by the application.

    application: :class:`Union[Tk, ThemedTk, None]`
        The tkinter application instance for this configuration. It can be a `Tk`, `ThemedTk`, or `Toplevel` instance.

    """
    headless: bool = False
    title: Optional[str] = DEF_WIN_TITLE
    theme: Optional[str] = DEF_THEME
    type_: ViewType = ViewType.ROOT
    icon: Optional[str] = DEF_ICON
    size_: Optional[str] = DEF_WIN_SIZE
    tasks: list[ApplicationTask] = field(default_factory=list)
    application: Union[Tk, ThemedTk, None] = None

    @classmethod
    def _common_assembly(cls,
                         headless: bool,
                         title: str,
                         theme: str,
                         type_: ViewType,
                         icon: str,
                         size_: str,
                         tasks: list[ApplicationTask],
                         application: Union[Tk, ThemedTk, None]) -> Self:
        return cls(
            headless=headless,
            title=title,
            theme=theme,
            type_=type_,
            icon=icon,
            size_=size_,
            tasks=tasks,
            application=application
        )

    @classmethod
    def toplevel(cls) -> Self:
        """get a generic version of an application configuration

        for a toplevel application

        .. ------------------------------------------------------------

        Returns
        --------
        ::

            ApplicationConfiguration._common_assembly(
                headless=False,
                title=DEF_WIN_TITLE,
                theme=DEF_THEME,
                type_=ViewType.TOPLEVEL,
                icon=DEF_ICON,
                size_=DEF_WIN_SIZE,
                tasks=[],
                application=Toplevel)
        """
        return ApplicationConfiguration._common_assembly(headless=False,
                                                         title=DEF_WIN_TITLE,
                                                         theme=DEF_THEME,
                                                         type_=ViewType.TOPLEVEL,
                                                         icon=DEF_ICON,
                                                         size_=DEF_WIN_SIZE,
                                                         tasks=[],
                                                         application=Toplevel)

    @classmethod
    def root(cls) -> Self:
        """get a generic version of an application configuration

        for a root application

        .. ------------------------------------------------------------

        Returns
        --------
        ::

            ApplicationConfiguration._common_assembly(
                headless=False,
                title=DEF_WIN_TITLE,
                theme=DEF_THEME,
                type_=ViewType.ROOT,
                icon=DEF_ICON,
                size_=DEF_WIN_SIZE,
                tasks=[],
                application=ThemedTk)
        """
        return ApplicationConfiguration._common_assembly(headless=False,
                                                         title=DEF_WIN_TITLE,
                                                         theme=DEF_THEME,
                                                         type_=ViewType.ROOT,
                                                         icon=DEF_ICON,
                                                         size_=DEF_WIN_SIZE,
                                                         tasks=[],
                                                         application=ThemedTk)


class Application(Runnable):
    """A :class:`PartialApplication` to contain the tk GUI instance, as well as reference to child views.

    .. ------------------------------------------------------------

    .. package:: models.abc.application

    .. ------------------------------------------------------------


    Attributes
    --------
    tk_app :class:`Union[Tk, ThemedTk, None]`
        tkinter application instance for this :class:`PartialApplication`.

    config :class:`PartialApplicationConfiguration`
        Configuration for this :class:`PartialApplication`.

    frame :class:`Frame`
        The frame for this :class:`PartialApplication`.

    """

    def __init__(self,
                 config: ApplicationConfiguration) -> None:

        super().__init__(add_to_globals=True)

        self._config: ApplicationConfiguration = ApplicationConfiguration.root() if config is None else config
        self._frame: Frame = None
        self._menu: MainApplicationMenu = None
        self._tasks: HashList[ApplicationTask] = None
        self._tk_app: Union[Tk, ThemedTk, None] = None

    @property
    def tk_app(self) -> Union[Tk, ThemedTk, None]:
        """The tk application instance for this :class:`PartialApplication`.

        .. ------------------------------------------------------------

        Returns
        -----------
            application: Union[:class:`Tk`, :class:`ThemedTk`, None]
        """
        return self._tk_app

    @property
    def config(self) -> ApplicationConfiguration:
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

    @property
    def menu(self) -> MainApplicationMenu:
        """Main Tk :class:`Menu` for this :class:`Application`.

        .. ------------------------------------------------------------

        Returns
        --------
            menu: :class:`MainApplicationMenu`
        """
        return self._menu

    @property
    def tasks(self) -> HashList[ApplicationTask]:
        """Hashed list of tasks for this :class:`PartialApplication`.

        .. ------------------------------------------------------------

        Returns
        --------
            tasks: :class:`HashList` [:class:`ApplicationTask`]
        """
        return self._tasks

    def build(self) -> Self:
        if self.config.application == Tk:
            self._tk_app = Tk()
        elif self.config.application == ThemedTk:
            self._tk_app = ThemedTk(theme=self.config.theme)
        elif self.config.application == Toplevel:
            self._tk_app = Toplevel()
        else:
            raise ValueError('Application type is not supported. '
                             'Please use Tk, ThemedTk or Toplevel.')

        self._tk_app.protocol('WM_DELETE_WINDOW', self.close)
        self._tk_app.title(self.config.title)
        self._tk_app.iconbitmap(self.config.icon)
        self._tk_app.geometry(self.config.size_)
        self._frame: Frame = Frame(master=self._tk_app)
        self._frame.pack(fill='both', expand=True)

        self._tasks: HashList[ApplicationTask] = HashList('id')
        self._menu = MainApplicationMenu(self.tk_app) if self.config.headless is False else None

        super().build()

    def add_task(self,
                 task: Union[ApplicationTask, type[ApplicationTask]]) -> Optional[ApplicationTask]:
        """Add an :class:`ApplicationTask` to this `Application`.

        This method calls the task's `inject` method.

        .. ---------------------------------------------------------------------

        Arguments
        ----------
        task: Union[:class:`ApplicationTask`, type[:class:`ApplicationTask`]]
            :class:`ApplicationTask` to add.

        .. ---------------------------------------------------------------------

        Returns
        ----------
        task: :class:`ApplicationTask` | `None`
            The built / injected task


        """
        if isinstance(task, ApplicationTask):
            self._tasks.append(task)
            task.inject()
            return task

        if isinstance(task, type):
            tsk = task(self)
            self._tasks.append(tsk)
            tsk.inject()
            return tsk

        return None

    def add_tasks(self,
                  tasks: Union[list[ApplicationTask], list[type[ApplicationTask]]]) -> None:
        """Add a list of :class:`ApplicationTask`s to this `Application`.

        This method calls the task's `inject` method.

        .. ---------------------------------------------------------------------

        Arguments
        ----------
        task: Union[:class:`ApplicationTask`, type[:class:`ApplicationTask`]]
            :class:`ApplicationTask` to add.

        .. ---------------------------------------------------------------------

        Returns
        ----------
        task: :class:`ApplicationTask` | `None`
            The built / injected task


        """
        if not tasks:
            return

        _ = [self.add_task(x) for x in tasks]

    def center(self) -> None:
        """center this application's view in the window it resides in.
        """
        x = (self.tk_app.winfo_screenwidth() - self.tk_app.winfo_reqwidth()) // 2
        y = (self.tk_app.winfo_screenheight() - self.tk_app.winfo_reqheight()) // 2
        self.tk_app.geometry(f'+{x}+{y}')

    def close(self) -> None:
        """Close this application.
        """
        self.stop()
        try:
            if isinstance(self.tk_app, Tk):
                self.tk_app.quit()
                self.tk_app.destroy()
            elif isinstance(self.tk_app, Toplevel):
                self.tk_app.destroy()
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
        self.tk_app.after(100, lambda: self.logger.info('Ready...'))
        self.tk_app.focus()
        self.tk_app.mainloop()

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

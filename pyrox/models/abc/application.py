"""application abc types
    """
from __future__ import annotations


from dataclasses import dataclass, field
import datetime
from enum import Enum
import gc
import os
from pathlib import Path
import platformdirs
import sys
from tkinter import Frame, TclError
from tkinter import (
    Event,
    Menu,
    Tk,
    Toplevel,
)
from typing import Any, Callable, Optional, Self, Union


from pyrox.services import file, class_services
from ttkthemes import ThemedTk


from .list import HashList
from .meta import (
    Buildable,
    Runnable,
    RuntimeDict,
    SupportsJsonLoading,
    SupportsJsonSaving,
    TK_CURSORS,
    DEF_APP_NAME,
    DEF_AUTHOR_NAME,
    DEF_WIN_SIZE,
    DEF_WIN_TITLE,
    DEF_THEME,
    DEF_ICON,
)


__all__ = (
    'BaseMenu',
    'ApplicationTask',
    'ApplicationConfiguration',
    'ApplicationDirectoryService',
    'ApplicationRuntimeInfo',
    'Application',
)


class BaseMenu(Buildable):
    """.. description::
    Base menu for use in a ui :class:`Application`.
    .. ------------------------------------------------------------
    .. package::
    models.abc.application
    .. ------------------------------------------------------------
    .. arguments::
    root: Union[:class:`Tk`, :class:`Toplevel`]
        The root tk object this menu belongs to.
    .. ------------------------------------------------------------
    .. attributes::
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
        self._menu = Menu(self._root)

    @property
    def menu(self) -> Menu:
        """The Tk value member for this :class:`BaseMenu`.
        .. ------------------------------------------------------------
        .. returns::
        menu: :type:`Tk.Menu`
        """
        return self._menu

    @property
    def root(self) -> Union[Tk, Toplevel]:
        """The parent root item of this :class:`BaseMenu`.
        .. ------------------------------------------------------------
        .. returns::
        root: Union[:class:`Tk`, :class:`TopLevel`]
        """
        return self._root

    @staticmethod
    def get_menu_commands(menu: Menu) -> dict:
        """Get all menu commands for a specified tk :class:`Menu`.
        .. ------------------------------------------------------------
        .. arguments::
        menu: :class:`Menu`
            Menu to get all commands for.
        .. ------------------------------------------------------------
        .. returns::
        :class:`dict`
            Dictionary of menu commands, where the key is the label and the value is the command.
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


class MainApplicationMenu(BaseMenu):
    """.. description::
    Application `Main` Menu.
    Inherited from :class:`BaseMenu`, this parent class acts as the main menu for a root application
    .. ------------------------------------------------------------
    .. package::
    models.abc.application
    .. ------------------------------------------------------------
    .. arguments::
    root: Union[:class:`Tk`, :class:`Toplevel`]
        The root tk object this menu belongs to.
    .. ------------------------------------------------------------
    .. attributes::
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
    __slots__ = ('_file', '_edit', '_tools', '_view', '_help',)

    def __init__(self,
                 root: Union[Tk, Toplevel]):
        super().__init__(root=root)
        self._file: Menu = Menu(self.menu, name='file', tearoff=0)
        self._edit: Menu = Menu(self.menu, name='edit', tearoff=0)
        self._tools: Menu = Menu(self.menu, name='tools', tearoff=0)
        self._view: Menu = Menu(self.menu, name='view', tearoff=0)
        self._help: Menu = Menu(self.menu, name='help', tearoff=0)

        self.menu.add_cascade(label='File', menu=self.file, accelerator='<Alt>F', underline=0)
        self.menu.add_cascade(label='Edit', menu=self.edit, accelerator='<Alt>E', underline=0)
        self.menu.add_cascade(label='Tools', menu=self.tools, accelerator='<Alt>T', underline=0)
        self.menu.add_cascade(label='View', menu=self.view, accelerator='<Alt>V', underline=0)
        self.menu.add_cascade(label='Help', menu=self.help, accelerator='<Alt>H', underline=0)

        self.root.config(menu=self.menu)

    @property
    def edit(self) -> Menu:
        """The Edit :class:`Menu` for this :class:`MainApplicationMenu`.
        .. ------------------------------------------------------------
        .. returns::
        edit: :class:`Menu`
        """
        return self._edit

    @property
    def file(self) -> Menu:
        """The File :class:`Menu` for this :class:`MainApplicationMenu`.
        .. ------------------------------------------------------------
        .. returns::
        file: :class:`Menu`
        """
        return self._file

    @property
    def help(self) -> Menu:
        """The Help :class:`Menu` for this :class:`MainApplicationMenu`.
        .. ------------------------------------------------------------
        .. returns::
        help: :class:`Menu`
        """
        return self._help

    @property
    def tools(self) -> Menu:
        """The Tools :class:`Menu` for this :class:`MainApplicationMenu`.
        .. ------------------------------------------------------------
        .. returns::
        tools: :class:`Menu`
        """
        return self._tools

    @property
    def view(self) -> Menu:
        """The View :class:`Menu` for this :class:`MainApplicationMenu`.
        .. ------------------------------------------------------------
        .. returns::
        view: :class:`Menu`
        """
        return self._view


class ApplicationTask(Runnable):
    """.. description::
    Application task to add additional functionality to the application.
    Normally, these tasks are injected into the application's main menu toolbar.
    .. ------------------------------------------------------------
    .. package::
    models.abc.application
    .. ------------------------------------------------------------
    .. attributes::
    application: :class:`PartialApplication`
        The parent application of this task.
    """
    __slots__ = ('_application')

    def __init__(self,
                 application: 'Application'):
        super().__init__()
        self._application: 'Application' = application

    @property
    def application(self) -> 'Application':
        """The parent application of this task.
        .. ------------------------------------------------------------
        .. returns::
        application: :class:`Application`
        """
        return self._application

    @application.setter
    def application(self, value: 'Application'):
        if not isinstance(value, Application):
            raise TypeError('application must be of type Application')
        self._application = value

    def inject(self) -> None:
        """Inject this task into the hosting application
        """
        raise NotImplementedError('This method should be overridden in a subclass.')


class ApplicationTkType(Enum):
    """Application Tkinter Type
    """
    NA = 0
    ROOT = 1
    TOPLEVEL = 2
    EMBED = 3


@dataclass
class ApplicationConfiguration:
    """.. description::
    Application configuration
    .. ------------------------------------------------------------
    .. package::
    models.abc.application
    .. ------------------------------------------------------------
    .. attributes::
    headless: :type:`bool`
        If True, the application will not create a main window.
    application_name: :type:`str`
        The name of the application, used for directory naming and logging.
    author_name: :type:`str`
        The name of the author, used for directory naming and logging.
    title: :type:`str`
        The title of the application window.
    theme: :type:`str`
        The theme to use for the application window.
    type_: :class:`ApplicationTkType`
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
    application_name: Optional[str] = DEF_APP_NAME
    author_name: Optional[str] = DEF_AUTHOR_NAME
    title: Optional[str] = DEF_WIN_TITLE
    theme: Optional[str] = DEF_THEME
    type_: ApplicationTkType = ApplicationTkType.ROOT
    icon: Optional[str] = DEF_ICON
    size_: Optional[str] = DEF_WIN_SIZE
    tasks: list[ApplicationTask] = field(default_factory=list)
    application: Union[Tk, ThemedTk, None] = None

    @classmethod
    def _common_assembly(cls,
                         headless: bool,
                         application_name: str,
                         author_name: str,
                         title: str,
                         theme: str,
                         type_: ApplicationTkType,
                         icon: str,
                         size_: str,
                         tasks: list[ApplicationTask],
                         application: Union[Tk, ThemedTk, None]) -> Self:
        return cls(
            headless=headless,
            application_name=application_name,
            author_name=author_name,
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
        """get a generic version of a toplevel application configuration
        .. ------------------------------------------------------------
        .. returns::
            ApplicationConfiguration._common_assembly(
                headless=False,
                application_name=DEF_APP_NAME,
                author_name=DEF_AUTHOR_NAME,
                title=DEF_WIN_TITLE,
                theme=DEF_THEME,
                type_=ViewType.TOPLEVEL,
                icon=DEF_ICON,
                size_=DEF_WIN_SIZE,
                tasks=[],
                application=Toplevel)
        """
        return ApplicationConfiguration._common_assembly(headless=False,
                                                         application_name=DEF_APP_NAME,
                                                         author_name=DEF_AUTHOR_NAME,
                                                         title=DEF_WIN_TITLE,
                                                         theme=DEF_THEME,
                                                         type_=ApplicationTkType.TOPLEVEL,
                                                         icon=DEF_ICON,
                                                         size_=DEF_WIN_SIZE,
                                                         tasks=[],
                                                         application=Toplevel)

    @classmethod
    def root(cls) -> Self:
        """get a generic version of a root application configuration.
        .. ------------------------------------------------------------
        .. returns::
            ApplicationConfiguration._common_assembly(
                headless=False,
                application_name=DEF_APP_NAME,
                author_name=DEF_AUTHOR_NAME,
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
                                                         application_name=DEF_APP_NAME,
                                                         author_name=DEF_AUTHOR_NAME,
                                                         theme=DEF_THEME,
                                                         type_=ApplicationTkType.ROOT,
                                                         icon=DEF_ICON,
                                                         size_=DEF_WIN_SIZE,
                                                         tasks=[],
                                                         application=ThemedTk)


class ApplicationDirectoryService:
    """.. description::
    Application Directory Service
    Manage Application Directories with this service class
    .. ------------------------------------------------------------
    .. package::
    meta.models.application
    .. ------------------------------------------------------------
    .. attributes::
    app_name: :type:`str`
        The name of the application, used for directory naming and logging.
    author_name: :type:`str`
        The name of the author, used for directory naming and logging.
    user_cache: :type:`str`
        The path to the user cache directory for the application.
    user_config: :type:`str`
        The path to the user config directory for the application.
    user_data: :type:`str`
        The path to the user data directory for the application.
    user_documents: :type:`str`
        The path to the user documents directory for the application.
    user_downloads: :type:`str`
        The path to the user downloads directory for the application.
    user_log: :type:`str`
        The path to the user log directory for the application.
    user_log_file: :type:`str`
        The path to the application's log file.
    """
    __slots__ = ('_app_name', '_author_name')

    def __init__(self,
                 author_name: str,
                 app_name: str):
        if not author_name or author_name == '':
            raise ValueError('A valid, non-null author name must be supplied for this class!')

        if not app_name or app_name == '':
            raise ValueError('A valid, non-null application name must be supplied for this class!')

        self._app_name = app_name
        self._author_name = author_name
        self.build_directory()

    @property
    def all_directories(self) -> dict:
        """All directories for this service class.
        .. ------------------------------------------------
        .. returns::
        :class:`dict`
            Dictionary of all directories for this service class.
        """
        return {
            'user_cache': self.user_cache,
            'user_config': self.user_config,
            'user_data': self.user_data,
            'user_log': self.user_log
        }

    @property
    def app_name(self) -> str:
        """Application Name supplied to this service class.
        .. ------------------------------------------------
        .. returns::
        :class:`str`
            The name of the application, used for directory naming and logging.
        """
        return self._app_name

    @property
    def app_runtime_info_file(self) -> str:
        """Application runtime info file.
        This is the file where the application will store runtime information.
        .. ---------------------------------------------------------------------------
        .. returns::
        :class:`str`
            The path to the application's runtime info file.
        """
        return os.path.join(self.user_data, f'{self._app_name}_runtime_info.json')

    @property
    def author_name(self) -> str:
        """Author Name supplied to this service class.
        .. ------------------------------------------------
        .. returns::
        :class:`str`
            The name of the author, used for directory naming and logging.
        """
        return self._author_name

    @property
    def user_cache(self):
        """User cache directory.
        .. ---------------------------------------------------------------------------
        .. returns::
        :class:`str`
            The path to the user cache directory for the application.
        """
        return platformdirs.user_cache_dir(self._app_name, self._author_name, ensure_exists=True)

    @property
    def user_config(self):
        """User config directory.
        .. ---------------------------------------------------------------------------
        .. returns::
        :class:`str`
            The path to the user config directory for the application.
        """
        return platformdirs.user_config_dir(self._app_name, self._author_name, ensure_exists=True)

    @property
    def user_data(self):
        """User data directory.
        Example >>> 'C:/Users/JohnSmith/AppData/Local/JSmithEnterprises/MyApplication'
        .. ---------------------------------------------------------------------------
        .. returns::
        :class:`str`
            The path to the user data directory for the application.
        """
        return platformdirs.user_data_dir(self._app_name, self._author_name, ensure_exists=True)

    @property
    def user_documents(self):
        """User documents directory.
        .. ---------------------------------------------------------------------------
        .. returns::
        :class:`str`
            The path to the user documents directory for the application.
        """
        return platformdirs.user_documents_dir()

    @property
    def user_downloads(self):
        """User downloads directory.
        .. ---------------------------------------------------------------------------
        .. returns::
        :class:`str`
            The path to the user downloads directory for the application.
        """
        return platformdirs.user_downloads_dir()

    @property
    def user_log(self):
        """User log directory.
        .. ---------------------------------------------------------------------------
        .. returns::
        :class:`str`
            The path to the user log directory for the application.
        """
        return platformdirs.user_log_dir(self._app_name, self._author_name)

    @property
    def user_log_file(self) -> str:
        """User log file.
        This is the file where the application will log messages.
        .. ---------------------------------------------------------------------------
        .. returns::
        :class:`str`
            The path to the application's log file.
        """
        return os.path.join(self.user_log, f'{self._app_name}.log')

    def build_directory(self,
                        as_refresh: bool = False):
        """Build the directory for the parent application.
        Uses the supplied name for directory naming.
        .. ------------------------------------------------------------
        .. arguments::
        as_refresh: :type:`bool`
            If True, the directories will be refreshed, removing all files in them.
        """
        for dir in self.all_directories.values():
            if not os.path.isdir(dir):
                os.makedirs(dir, exist_ok=True)
            else:
                if as_refresh:
                    file.remove_all_files(dir)


class ApplicationRuntimeInfo(SupportsJsonSaving, SupportsJsonLoading):
    """.. description::
    Application Runtime Information.
    This class is used to store and manage runtime information for the application.
    .. ------------------------------------------------------------
    .. package::
    meta.models.application
    .. ------------------------------------------------------------
    .. attributes::
    application: :class:`Application`
        The application instance associated with this runtime info.
    data: :class:`RuntimeDict`
        The runtime information data, stored as a `RuntimeDict`.
    load_path: :class:`str`
        The path to the runtime info file.
    save_path: :class:`str`
        The path to the runtime info file.
    save_data_callback: :class:`Callable[[], dict]`
        Callback function to get the data to be saved.
    """
    __slots__ = ('_application', '_data')

    def __init__(self, application: Application):
        self._application: Application = application
        self._data = RuntimeDict(self.save_to_json)
        self.load_from_json()
        self._data['last_start_time'] = datetime.datetime.now().isoformat()

    @property
    def application(self) -> Application:
        """The application instance associated with this runtime info.
        .. ------------------------------------------------------------
        .. returns::
            app: :class:`Application`
        """
        return self._application

    @property
    def application_runtime_info_file(self) -> str:
        """Application runtime info file.
        This is the file where the application will store runtime information.
        .. ---------------------------------------------------------------------------
        .. returns::
        :class:`str`
            The path to the application's runtime info file.
        """
        return os.path.join(self.application.directory_service.user_data, f'{self.application.directory_service.app_name}_runtime_info.json')

    @property
    def data(self) -> RuntimeDict:
        return self._data

    @data.setter
    def data(self, value: dict):
        if not isinstance(value, dict):
            raise TypeError('Runtime information data must be a RuntimeDict.')
        self._data.clear()
        self._data.update(value)

    @property
    def load_path(self) -> str:
        """The path to the runtime info file.
        This is used for loading the runtime information from a JSON file.
        .. ---------------------------------------------------------------------------
        .. returns::
        :class:`str`
            The path to the runtime info file.
        """
        return self.application_runtime_info_file

    @property
    def save_path(self) -> str:
        """The path to the runtime info file.
        This is used for saving the runtime information to a JSON file.
        .. ---------------------------------------------------------------------------
        .. returns::
        :class:`str`
            The path to the runtime info file.
        """
        return self.application_runtime_info_file

    @property
    def save_data_callback(self) -> Callable[[], dict]:
        """Callback function to get the data to be saved.
        This function is called when saving the runtime information to a JSON file.
        .. ---------------------------------------------------------------------------
        .. returns::
        :class:`Callable[[], dict]`
            A callable that returns the data to be saved.
        """
        return lambda: self.data.data

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the runtime information data.
        .. ------------------------------------------------------------
        .. arguments::
        key: :type:`str`
            The key to retrieve from the runtime information data.
        default: :type:`Any`
            The default value to return if the key is not found.
        .. ------------------------------------------------------------
        .. returns::
        :class:`Any`
            The value associated with the specified key, or the default value if the key is not found.
        """
        return self.data.get(key, default)

    def on_loaded(self,
                  data: Any) -> None:
        if data is None:
            self.application.logger.warning('No data loaded from the runtime info file, initializing with empty RuntimeDict.')
            self._data = RuntimeDict(self.save_to_json)
            return

        if not isinstance(data, dict):
            raise TypeError('Loaded data must be a RuntimeDict.')
        self.data = data

    def set(self, key: str, value: Any) -> None:
        """Set a key-value pair in the runtime information data.
        .. ------------------------------------------------------------
        .. arguments::
        key: :type:`str`
            The key to set in the runtime information data.
        value: :type:`Any`
            The value to set for the specified key.
        """
        self.data[key] = value


class Application(Runnable):
    """.. description::
    A :class:`Application` to manage running application data and services.
    .. ------------------------------------------------------------
    .. package::
    models.abc.application
    .. ------------------------------------------------------------
    .. attributes::
    config: :class:`ApplicationConfiguration`
        The configuration for this :class:`Application`.
    directory_service: :class:`ApplicationDirectoryService`
        The directory service for this :class:`Application`.
    frame: :class:`Frame`
        The main frame for this :class:`Application`.
    menu: :class:`MainApplicationMenu`
        The main Tk :class:`Menu` for this :class:`Application`.
    runtime_info: :class:`ApplicationRuntimeInfo`
        The runtime information for this :class:`Application`.
    tasks: :class:`HashList` [:class:`ApplicationTask`]
        A hashed list of tasks for this :class:`Application`.
    tk_app: Union[:class:`Tk`, :class:`ThemedTk`]
        The tk application instance for this :class:`Application`.
    .. ------------------------------------------------------------
    .. arguments::
    config: :class:`ApplicationConfiguration`
        The configuration for this :class:`Application`.
        If not provided, a default configuration will be created using :meth:`ApplicationConfiguration.root`.
    """

    __slots__ = ('_config', '_directory_service', '_frame', '_menu', '_runtime_info', '_tasks', '_tk_app')

    def __init__(self,
                 config: ApplicationConfiguration,
                 add_to_globals: bool = False) -> None:
        super().__init__(add_to_globals=add_to_globals)
        sys.excepthook = self._excepthook
        self._config: ApplicationConfiguration = config or ApplicationConfiguration.root()
        self._directory_service: ApplicationDirectoryService = ApplicationDirectoryService(
            author_name=self._config.author_name,
            app_name=self._config.application_name
        )
        self._frame: Frame = None
        self._menu: MainApplicationMenu = None
        self._runtime_info: ApplicationRuntimeInfo = None
        self._tasks: HashList[ApplicationTask] = None
        self._tk_app: Union[Tk, ThemedTk] = None
        self._log_handler.set_callback(self.log)

    @property
    def tk_app(self) -> Union[Tk, ThemedTk]:
        """The tk application instance for this :class:`Application`.
        .. ------------------------------------------------------------
        .. returns::
        tk_app: Union[:class:`Tk`, :class:`ThemedTk`]
            This property returns the tkinter application instance.
        """
        return self._tk_app

    @property
    def config(self) -> ApplicationConfiguration:
        """Configuration for this :class:`Application`.
        .. ------------------------------------------------------------
        .. returns::
            config :class:`ApplicationConfiguration`
        """
        return self._config

    @property
    def directory_service(self) -> ApplicationDirectoryService:
        """Directory service for this :class:`Application`.
        This service provides access to various directories used by the application.
        .. ------------------------------------------------------------
        .. returns::
            directory_service: :class:`ApplicationDirectoryService`
        """
        return self._directory_service

    @property
    def frame(self) -> Frame:
        """The frame for this :class:`Application`.
        .. ------------------------------------------------------------
        .. returns::
        frame: :class:`Frame`
        """
        return self._frame

    @property
    def menu(self) -> MainApplicationMenu:
        """Main Tk :class:`Menu` for this :class:`Application`.
        .. ------------------------------------------------------------
        .. returns::
            menu: :class:`MainApplicationMenu`
        """
        return self._menu

    @property
    def runtime_info(self) -> ApplicationRuntimeInfo:
        """Runtime information for this :class:`Application`.
        This property provides access to the runtime information of the application.
        .. ------------------------------------------------------------
        .. returns::
            runtime_info: :class:`ApplicationRuntimeInfo`
        """
        return self._runtime_info

    @property
    def tasks(self) -> HashList[ApplicationTask]:
        """Hashed list of tasks for this :class:`Application`.
        .. ------------------------------------------------------------
        .. returns::
            tasks: :class:`HashList` [:class:`ApplicationTask`]
        """
        return self._tasks

    def _excepthook(self, exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            return
        self.logger.error(msg=f'Uncaught exception: {exc_value}', exc_info=(exc_type, exc_value, exc_traceback))

    def _on_tk_configure(self,
                         event: Event) -> None:
        """Handle the Tk configure event.
        This method is called when the Tk application is configured.
        .. ------------------------------------------------------------
        .. arguments::
        event: :class:`Event`
            The Tk event that triggered this method.
        """
        if event.widget != self.tk_app:
            return
        root = event.widget
        self._runtime_info.data.inhibit()
        self._runtime_info.data['window_size'] = f'{root.winfo_width()}x{root.winfo_height()}'
        self._runtime_info.data['window_position'] = (root.winfo_x(), root.winfo_y())
        self._runtime_info.data['full_screen'] = bool(root.attributes('-fullscreen'))
        self._runtime_info.data['window_state'] = root.state()
        self._runtime_info.data.uninhibit()

    def build(self) -> None:
        """Build this :class:`Application`.
        This method initializes the tkinter application instance, sets up the main window,
        and prepares the main frame and menu.
        .. ------------------------------------------------------------
        .. raises::
        ValueError
            If the application type is not supported. Only `Tk`, `ThemedTk`, or `Toplevel` are allowed.
        """
        self._runtime_info = ApplicationRuntimeInfo(self)
        if self.config.application == Tk:
            self._tk_app = Tk()
        elif self.config.application == ThemedTk:
            self._tk_app = ThemedTk(theme=self._runtime_info.get('theme', self.config.theme))
        elif self.config.application == Toplevel:
            self._tk_app = Toplevel()
        else:
            raise ValueError('Application type is not supported. '
                             'Please use Tk, ThemedTk or Toplevel.')

        if isinstance(self._tk_app, (ThemedTk, Tk)):
            self._tk_app.bind('<Configure>', self._on_tk_configure)
            self._tk_app.bind('<F11>', lambda _: self.toggle_fullscreen(not self._tk_app.attributes('-fullscreen')))

        self._tk_app.report_callback_exception = self._excepthook
        self._tk_app.protocol('WM_DELETE_WINDOW', self.close)
        self._tk_app.title(self.config.title)
        self._tk_app.iconbitmap(self.config.icon)
        self._tk_app.iconbitmap(default=self.config.icon)
        self._frame: Frame = Frame(master=self._tk_app)
        self._frame.pack(fill='both', expand=True)
        self._tasks: HashList[ApplicationTask] = HashList('name')
        self._menu = MainApplicationMenu(self.tk_app) if self.config.headless is False else None

        try:
            self.toggle_fullscreen(self._runtime_info.get('full_screen', False))
            self._tk_app.geometry(self._runtime_info.get('window_size', self.config.size_))
            self._tk_app.state(self._runtime_info.get('window_state', 'normal'))
        except TclError as e:
            self.logger.error(f'TclError: Could not set geometry or state for the application: {e}')
            self._tk_app.geometry(self.config.size_)
            self._tk_app.state('normal')

        self._directory_service.build_directory()

        if self.menu:
            self.add_tasks(tasks=class_services.find_and_instantiate_class(directory_path=str(Path(__file__).parent.parent.parent) + '\\tasks',
                                                                           class_name=ApplicationTask.__name__,
                                                                           as_subclass=True,
                                                                           ignoring_classes=['ApplicationTask', 'AppTask'],
                                                                           parent_class=ApplicationTask,
                                                                           application=self))
        super().build()

    def add_task(self,
                 task: Union[ApplicationTask, type[ApplicationTask]]) -> None:
        """Add a task to this :class:`Application`.
        This method can accept either an instance of :class:`ApplicationTask` or a class type of :class:`ApplicationTask`.
        .. ------------------------------------------------------------
        .. arguments::
        task: Union[:class:`ApplicationTask`, type[:class:`ApplicationTask`]]
            :class:`ApplicationTask` to add. If a class type is provided, an instance will be created.
        """
        if isinstance(task, ApplicationTask):
            task.inject()
            self.tasks.append(task)

        if isinstance(task, type):
            tsk = task(self).inject()
            self.tasks.append(tsk)

    def add_tasks(self,
                  tasks: Union[list[ApplicationTask], list[type[ApplicationTask]]]) -> None:
        """Add a list of :class:`ApplicationTask`s to this `Application`.
        This method calls the task's `inject` method.
        .. ---------------------------------------------------------------------
        .. arguments::
        task: Union[:class:`ApplicationTask`, type[:class:`ApplicationTask`]]
            :class:`ApplicationTask` to add.
        """
        _ = [self.add_task(x) for x in tasks]

    def center(self) -> None:
        """center this application's view in the window it resides in.
        """
        x = (self.tk_app.winfo_screenwidth() - self.tk_app.winfo_reqwidth()) // 2
        y = (self.tk_app.winfo_screenheight() - self.tk_app.winfo_reqheight()) // 2
        self.tk_app.geometry(f'+{x}+{y}')

    def clear_log_file(self) -> None:
        """Clear the log file for this :class:`Application`.

        This method removes all content from the log file, effectively clearing it.
        """
        try:
            with open(self._directory_service.user_log_file, 'w', encoding='utf-8') as f:
                f.write('')
        except IOError as e:
            print(f'Error clearing log file {self._directory_service.user_log_file}: {e}')

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

    def log(self,
            message: str) -> None:
        """Post a message to this :class:`Application`'s  log text file.
        .. ------------------------------------------------------------
        .. arguments::
        message: :class:`str`
            Message to be sent to this :class:`Application`'s log frame and to be appended to the log text file.
        """
        try:
            with open(self._directory_service.user_log_file, 'a', encoding='utf-8') as f:
                f.write(f'{message}\n')
        except IOError as e:
            print(f'Error writing to log file {self._directory_service.user_log_file}: {e}')

    def on_pre_run(self) -> None:
        """Method that is called directly before calling parent Tk `mainloop`.

        By this point, all models, view models and views should be created.

        This allows some extra logic to occur before our app begins.

        .. ------------------------------------------------------------

        Note: it is recommenbed to override this method to create your own functionality.
        """

    def set_app_state_busy(self):
        """Set the application state to busy.
        This method changes the cursor to a busy state, indicating that the application is processing.
        """
        self.update_cursor(TK_CURSORS.WAIT)

    def set_app_state_normal(self):
        """Set the application state to normal.
        This method changes the cursor back to normal, indicating that the application is ready for user interaction.
        """
        self.update_cursor(TK_CURSORS.DEFAULT)

    def start(self) -> None:
        super().start()
        self.on_pre_run()
        self.tk_app.after(100, lambda: self.logger.info('Ready...'))
        self.tk_app.focus()
        self.tk_app.mainloop()

    def stop(self) -> None:
        super().stop()

    def toggle_fullscreen(self, fullscreen: Optional[bool] = None) -> None:
        """Toggle fullscreen mode for this :class:`Application`.

        If `fullscreen` is None, it will toggle the current state.
        If `fullscreen` is True, it will set the application to fullscreen.
        If `fullscreen` is False, it will exit fullscreen mode.

        .. ------------------------------------------------------------
        .. arguments::
        fullscreen: Optional[:type:`bool`]
            If True, the application will be set to fullscreen.
            If False, the application will exit fullscreen mode.
            If None, it will toggle the current state.
        """
        if fullscreen is None:
            fullscreen = not self._runtime_info.get('full_screen', False)

        self.tk_app.attributes('-fullscreen', fullscreen)

    def update_cursor(self, cursor: Union[TK_CURSORS, str]) -> None:
        """Update the cursor for this :class:`Application`.
        This method changes the cursor style for the main application window.
        .. ------------------------------------------------------------
        .. arguments::
        cursor: :type:`str`
            The cursor style to set. This should be a valid Tkinter cursor string.
        """
        if isinstance(cursor, TK_CURSORS):
            cursor = cursor.value
        if not isinstance(cursor, str):
            raise TypeError('Cursor must be a string representing a valid Tkinter cursor type.')
        self.tk_app.config(cursor=cursor)
        self.tk_app.update_idletasks()

"""Application ABC types for the Pyrox framework."""
from __future__ import annotations

from dataclasses import dataclass, field
import datetime
from enum import Enum
import gc
import logging
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
    """Base menu for use in a UI Application.

    Args:
        root: The root Tk object this menu belongs to.

    Attributes:
        menu: The Tk Menu instance for this BaseMenu.
        root: The parent root item of this menu.
    """
    __slots__ = ('_root', '_menu')

    def __init__(self, root: Union[ThemedTk, Toplevel]):
        super().__init__()
        self._root = root
        self._menu = Menu(self._root)

    @property
    def menu(self) -> Menu:
        """The Tk Menu instance for this BaseMenu.

        Returns:
            Menu: The Tk Menu object.
        """
        return self._menu

    @property
    def root(self) -> Union[ThemedTk, Toplevel]:
        """The parent root item of this menu.

        Returns:
            Union[Tk, Toplevel]: The parent root object.
        """
        return self._root

    @staticmethod
    def get_menu_commands(menu: Menu) -> dict:
        """Get all menu commands for a specified Tk Menu.

        Args:
            menu: Menu to get all commands for.

        Returns:
            dict: Dictionary of menu commands, where the key is the label and the value is the command.
        """
        cmds = {}
        try:
            for x in range(menu.index('end') + 1):
                if menu.type(x) == 'command':
                    label = menu.entrycget(x, 'label')
                    cmd = menu.entrycget(x, 'command')
                    cmds[label] = cmd
        except TypeError:
            pass
        return cmds


class MainApplicationMenu(BaseMenu):
    """Application Main Menu.

    Inherited from BaseMenu, this class acts as the main menu for a root application.

    Args:
        root: The root Tk object this menu belongs to.

    Attributes:
        edit: The Edit Menu for this MainApplicationMenu.
        file: The File Menu for this MainApplicationMenu.
        help: The Help Menu for this MainApplicationMenu.
        tools: The Tools Menu for this MainApplicationMenu.
        view: The View Menu for this MainApplicationMenu.
    """
    __slots__ = ('_file', '_edit', '_tools', '_view', '_help')

    def __init__(self, root: Union[ThemedTk, Toplevel]):
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
        """The Edit Menu for this MainApplicationMenu.

        Returns:
            Menu: The Edit menu object.
        """
        return self._edit

    @property
    def file(self) -> Menu:
        """The File Menu for this MainApplicationMenu.

        Returns:
            Menu: The File menu object.
        """
        return self._file

    @property
    def help(self) -> Menu:
        """The Help Menu for this MainApplicationMenu.

        Returns:
            Menu: The Help menu object.
        """
        return self._help

    @property
    def tools(self) -> Menu:
        """The Tools Menu for this MainApplicationMenu.

        Returns:
            Menu: The Tools menu object.
        """
        return self._tools

    @property
    def view(self) -> Menu:
        """The View Menu for this MainApplicationMenu.

        Returns:
            Menu: The View menu object.
        """
        return self._view


class ApplicationTask(Runnable):
    """Application task to add additional functionality to the application.

    Normally, these tasks are injected into the application's main menu toolbar.

    Args:
        application: The parent application of this task.

    Attributes:
        application: The parent application of this task.
    """
    __slots__ = ('_application',)

    def __init__(self, application: 'Application'):
        super().__init__()
        self._application: 'Application' = application

    @property
    def application(self) -> 'Application':
        """The parent application of this task.

        Returns:
            Application: The parent application instance.
        """
        return self._application

    @application.setter
    def application(self, value: 'Application'):
        """Set the parent application for this task.

        Args:
            value: The application instance to set.

        Raises:
            TypeError: If value is not an Application instance.
        """
        if not isinstance(value, Application):
            raise TypeError('application must be of type Application')
        self._application = value

    def inject(self) -> None:
        """Inject this task into the hosting application.

        Raises:
            NotImplementedError: This method should be overridden in a subclass.
        """
        raise NotImplementedError('This method should be overridden in a subclass.')


class ApplicationTkType(Enum):
    """Application Tkinter Type enumeration.

    Attributes:
        NA: Not applicable type.
        ROOT: Root window type.
        TOPLEVEL: Toplevel window type.
        EMBED: Embedded window type.
    """
    NA = 0
    ROOT = 1
    TOPLEVEL = 2
    EMBED = 3


@dataclass
class ApplicationConfiguration:
    """Application configuration dataclass.

    Attributes:
        headless: If True, the application will not create a main window.
        application_name: The name of the application, used for directory naming and logging.
        author_name: The name of the author, used for directory naming and logging.
        title: The title of the application window.
        theme: The theme to use for the application window.
        type_: The type of the application view.
        icon: The icon to use for the application window.
        size_: The size of the application window, specified as a string (e.g., "800x600").
        tasks: A list of tasks to be executed by the application.
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
                         tasks: list[ApplicationTask]) -> Self:
        """Common assembly method for creating ApplicationConfiguration instances.

        Args:
            headless: Whether the application is headless.
            application_name: Name of the application.
            author_name: Name of the author.
            title: Title of the application window.
            theme: Theme to use.
            type_: Type of the application.
            icon: Icon path.
            size_: Window size.
            tasks: List of tasks.

        Returns:
            Self: A new ApplicationConfiguration instance.
        """
        return cls(
            headless=headless,
            application_name=application_name,
            author_name=author_name,
            title=title,
            theme=theme,
            type_=type_,
            icon=icon,
            size_=size_,
            tasks=tasks
        )

    @classmethod
    def toplevel(cls) -> Self:
        """Get a generic toplevel application configuration.

        Returns:
            Self: A toplevel ApplicationConfiguration instance.
        """
        return ApplicationConfiguration._common_assembly(
            headless=False,
            application_name=DEF_APP_NAME,
            author_name=DEF_AUTHOR_NAME,
            title=DEF_WIN_TITLE,
            theme=DEF_THEME,
            type_=ApplicationTkType.TOPLEVEL,
            icon=DEF_ICON,
            size_=DEF_WIN_SIZE,
            tasks=[]
        )

    @classmethod
    def root(cls) -> Self:
        """Get a generic root application configuration.

        Returns:
            Self: A root ApplicationConfiguration instance.
        """
        return ApplicationConfiguration._common_assembly(
            headless=False,
            title=DEF_WIN_TITLE,
            application_name=DEF_APP_NAME,
            author_name=DEF_AUTHOR_NAME,
            theme=DEF_THEME,
            type_=ApplicationTkType.ROOT,
            icon=DEF_ICON,
            size_=DEF_WIN_SIZE,
            tasks=[]
        )


class ApplicationDirectoryService:
    """Application Directory Service for managing application directories.

    Args:
        author_name: The name of the author, used for directory naming and logging.
        app_name: The name of the application, used for directory naming and logging.

    Attributes:
        app_name: The name of the application.
        author_name: The name of the author.
        user_cache: The path to the user cache directory for the application.
        user_config: The path to the user config directory for the application.
        user_data: The path to the user data directory for the application.
        user_documents: The path to the user documents directory for the application.
        user_downloads: The path to the user downloads directory for the application.
        user_log: The path to the user log directory for the application.
        user_log_file: The path to the application's log file.
    """
    __slots__ = ('_app_name', '_author_name')

    def __init__(self, author_name: str, app_name: str):
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

        Returns:
            dict: Dictionary of all directories for this service class.
        """
        return {
            'user_cache': self.user_cache,
            'user_config': self.user_config,
            'user_data': self.user_data,
            'user_log': self.user_log
        }

    @property
    def app_name(self) -> str:
        """Application name supplied to this service class.

        Returns:
            str: The name of the application.
        """
        return self._app_name

    @property
    def app_runtime_info_file(self) -> str:
        """Application runtime info file path.

        This is the file where the application will store runtime information.

        Returns:
            str: The path to the application's runtime info file.
        """
        return os.path.join(self.user_data, f'{self._app_name}_runtime_info.json')

    @property
    def author_name(self) -> str:
        """Author name supplied to this service class.

        Returns:
            str: The name of the author.
        """
        return self._author_name

    @property
    def user_cache(self) -> str:
        """User cache directory.

        Returns:
            str: The path to the user cache directory for the application.
        """
        return platformdirs.user_cache_dir(self._app_name, self._author_name, ensure_exists=True)

    @property
    def user_config(self) -> str:
        """User config directory.

        Returns:
            str: The path to the user config directory for the application.
        """
        return platformdirs.user_config_dir(self._app_name, self._author_name, ensure_exists=True)

    @property
    def user_data(self) -> str:
        """User data directory.

        Example: 'C:/Users/JohnSmith/AppData/Local/JSmithEnterprises/MyApplication'

        Returns:
            str: The path to the user data directory for the application.
        """
        return platformdirs.user_data_dir(self._app_name, self._author_name, ensure_exists=True)

    @property
    def user_documents(self) -> str:
        """User documents directory.

        Returns:
            str: The path to the user documents directory.
        """
        return platformdirs.user_documents_dir()

    @property
    def user_downloads(self) -> str:
        """User downloads directory.

        Returns:
            str: The path to the user downloads directory.
        """
        return platformdirs.user_downloads_dir()

    @property
    def user_log(self) -> str:
        """User log directory.

        Returns:
            str: The path to the user log directory for the application.
        """
        return platformdirs.user_log_dir(self._app_name, self._author_name)

    @property
    def user_log_file(self) -> str:
        """User log file path.

        This is the file where the application will log messages.

        Returns:
            str: The path to the application's log file.
        """
        return os.path.join(self.user_log, f'{self._app_name}.log')

    def build_directory(self, as_refresh: bool = False) -> None:
        """Build the directory for the parent application.

        Uses the supplied name for directory naming.

        Args:
            as_refresh: If True, the directories will be refreshed, removing all files in them.

        Raises:
            OSError: If the directory creation fails.
        """
        for dir_path in self.all_directories.values():
            if not os.path.isdir(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                except OSError as e:
                    raise OSError(f'Failed to create directory {dir_path}: {e}') from e
            else:
                if as_refresh:
                    try:
                        file.remove_all_files(dir_path)
                    except OSError as e:
                        raise OSError(f'Failed to refresh directory {dir_path}: {e}') from e


class ApplicationRuntimeInfo(SupportsJsonSaving, SupportsJsonLoading):
    """Application Runtime Information manager.

    This class is used to store and manage runtime information for the application.

    Args:
        application: The application instance associated with this runtime info.

    Attributes:
        application: The application instance associated with this runtime info.
        data: The runtime information data, stored as a RuntimeDict.
        load_path: The path to the runtime info file.
        save_path: The path to the runtime info file.
        save_data_callback: Callback function to get the data to be saved.
    """
    __slots__ = ('_application', '_data')

    def __init__(self, application: 'Application'):
        self._application: 'Application' = application
        self._data = RuntimeDict(self.save_to_json)
        self.load_from_json()
        self._data['last_start_time'] = datetime.datetime.now().isoformat()

    @property
    def application(self) -> 'Application':
        """The application instance associated with this runtime info.

        Returns:
            Application: The application instance.
        """
        return self._application

    @property
    def application_runtime_info_file(self) -> str:
        """Application runtime info file path.

        This is the file where the application will store runtime information.

        Returns:
            str: The path to the application's runtime info file.
        """
        return os.path.join(
            self.application.directory_service.user_data,
            f'{self.application.directory_service.app_name}_runtime_info.json'
        )

    @property
    def data(self) -> RuntimeDict:
        """Runtime data dictionary.

        Returns:
            RuntimeDict: The runtime data.
        """
        return self._data

    @data.setter
    def data(self, value: dict) -> None:
        """Set runtime data.

        Args:
            value: Dictionary to set as runtime data.

        Raises:
            TypeError: If value is not a dictionary.
        """
        if not isinstance(value, dict):
            raise TypeError('Runtime information data must be a dictionary.')
        self._data.clear()
        self._data.update(value)

    @property
    def load_path(self) -> str:
        """The path to the runtime info file for loading.

        Returns:
            str: The path to the runtime info file.
        """
        return self.application_runtime_info_file

    @property
    def save_path(self) -> str:
        """The path to the runtime info file for saving.

        Returns:
            str: The path to the runtime info file.
        """
        return self.application_runtime_info_file

    @property
    def save_data_callback(self) -> Callable[[], dict]:
        """Callback function to get the data to be saved.

        This function is called when saving the runtime information to a JSON file.

        Returns:
            Callable[[], dict]: A callable that returns the data to be saved.
        """
        return lambda: self.data.data

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the runtime information data.

        Args:
            key: The key to retrieve from the runtime information data.
            default: The default value to return if the key is not found.

        Returns:
            Any: The value associated with the specified key, or the default value if not found.
        """
        return self.data.get(key, default)

    def on_loaded(self, data: Any) -> None:
        """Method called after data has been loaded.

        Args:
            data: Data that was loaded from the file.

        Raises:
            TypeError: If loaded data is not a dictionary.
        """
        if data is None:
            self.application.logger.warning(
                'No data loaded from the runtime info file, initializing with empty RuntimeDict.'
            )
            self._data = RuntimeDict(self.save_to_json)
            return

        if not isinstance(data, dict):
            raise TypeError('Loaded data must be a dictionary.')
        self.data = data

    def set(self, key: str, value: Any) -> None:
        """Set a key-value pair in the runtime information data.

        Args:
            key: The key to set in the runtime information data.
            value: The value to set for the specified key.
        """
        self.data[key] = value


class Application(Runnable):
    """A main Application class to manage running application data and services.

    Args:
        config: The configuration for this Application.
        add_to_globals: Whether to add this to global loggers.

    Attributes:
        config: The configuration for this Application.
        directory_service: The directory service for this Application.
        frame: The main frame for this Application.
        menu: The main Tk Menu for this Application.
        runtime_info: The runtime information for this Application.
        tasks: A hashed list of tasks for this Application.
        tk_app: The tk application instance for this Application.
    """
    __slots__ = ('_config', '_directory_service', '_frame', '_menu', '_runtime_info', '_tasks', '_tk_app')

    def __init__(self, config: ApplicationConfiguration) -> None:
        super().__init__()
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
        self._tk_app: Union[ThemedTk, Toplevel] = None

    @property
    def tk_app(self) -> Union[ThemedTk, Toplevel]:
        """The tk application instance for this Application.

        Returns:
            Union[Tk, ThemedTk]: The tkinter application instance.
        """
        return self._tk_app

    @property
    def config(self) -> ApplicationConfiguration:
        """Configuration for this Application.

        Returns:
            ApplicationConfiguration: The application configuration.
        """
        return self._config

    @property
    def directory_service(self) -> ApplicationDirectoryService:
        """Directory service for this Application.

        This service provides access to various directories used by the application.

        Returns:
            ApplicationDirectoryService: The directory service instance.
        """
        return self._directory_service

    @property
    def frame(self) -> Frame:
        """The main frame for this Application.

        Returns:
            Frame: The main application frame.
        """
        return self._frame

    @property
    def menu(self) -> MainApplicationMenu:
        """Main Tk Menu for this Application.

        Returns:
            MainApplicationMenu: The main application menu.
        """
        return self._menu

    @property
    def runtime_info(self) -> ApplicationRuntimeInfo:
        """Runtime information for this Application.

        This property provides access to the runtime information of the application.

        Returns:
            ApplicationRuntimeInfo: The runtime information instance.
        """
        return self._runtime_info

    @property
    def tasks(self) -> HashList[ApplicationTask]:
        """Hashed list of tasks for this Application.

        Returns:
            HashList[ApplicationTask]: The list of application tasks.
        """
        return self._tasks

    def _excepthook(self, exc_type, exc_value, exc_traceback) -> None:
        """Handle uncaught exceptions.

        Args:
            exc_type: Exception type.
            exc_value: Exception value.
            exc_traceback: Exception traceback.
        """
        if issubclass(exc_type, KeyboardInterrupt):
            return
        self.logger.error(
            msg=f'Uncaught exception: {exc_value}',
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    def _on_tk_configure(self, event: Event) -> None:
        """Handle the Tk configure event.

        This method is called when the Tk application is configured.

        Args:
            event: The Tk event that triggered this method.
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

    def add_task(self, task: Union[ApplicationTask, type[ApplicationTask]]) -> None:
        """Add a task to this Application.

        This method can accept either an instance of ApplicationTask or a class type.

        Args:
            task: ApplicationTask to add. If a class type is provided, an instance will be created.
        """
        if isinstance(task, ApplicationTask):
            task.inject()
            self.tasks.append(task)
        elif isinstance(task, type):
            tsk = task(self)
            tsk.inject()
            self.tasks.append(tsk)

    def add_tasks(self, tasks: Union[list[ApplicationTask], list[type[ApplicationTask]]]) -> None:
        """Add a list of ApplicationTasks to this Application.

        This method calls each task's inject method.

        Args:
            tasks: List of ApplicationTask instances or types to add.
        """
        for task in tasks:
            self.add_task(task)

    def build(self) -> None:
        """Build this Application.

        This method initializes the tkinter application instance, sets up the main window,
        and prepares the main frame and menu.

        Raises:
            ValueError: If the application type is not supported.
        """
        self._runtime_info = ApplicationRuntimeInfo(self)
        if self.runtime_info.get('logging_level') is not None:
            self.set_logging_level(self.runtime_info.get('logging_level'))

        if self.config.type_ == ApplicationTkType.ROOT:
            self._tk_app = ThemedTk(theme=self._runtime_info.get('theme', self.config.theme))
            self._tk_app.bind('<Configure>', self._on_tk_configure)
            self._tk_app.bind('<F11>', lambda _: self.toggle_fullscreen(not self._tk_app.attributes('-fullscreen')))
        elif self.config.type_ == ApplicationTkType.TOPLEVEL:
            self._tk_app = Toplevel()
        else:
            raise ValueError('Application type is not supported. Please use ROOT or TOPLEVEL.')

        self._tk_app.report_callback_exception = self._excepthook
        self._tk_app.protocol('WM_DELETE_WINDOW', self.close)
        self._tk_app.title(self.config.title)

        icon_path = Path(self.config.icon)
        if icon_path.exists():
            self._tk_app.iconbitmap(self.config.icon)
            self._tk_app.iconbitmap(default=self.config.icon)
        else:
            self.logger.warning(f'Icon file not found: {self.config.icon}.')
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
            try:
                tasks_path = Path(__file__).parents[2] / 'tasks'
                if tasks_path.exists():
                    tasks = class_services.find_and_instantiate_class(
                        directory_path=str(tasks_path),
                        class_name=ApplicationTask.__name__,
                        as_subclass=True,
                        ignoring_classes=['ApplicationTask', 'AppTask'],
                        parent_class=ApplicationTask,
                        application=self
                    )
                    self.add_tasks(tasks=tasks)
                else:
                    self.logger.warning(f'Tasks directory not found: {tasks_path}')
            except Exception as e:
                self.logger.error(f'Failed to load tasks: {e}')

        super().build()

    def center(self) -> None:
        """Center this application's view in the window it resides in."""
        x = (self.tk_app.winfo_screenwidth() - self.tk_app.winfo_reqwidth()) // 2
        y = (self.tk_app.winfo_screenheight() - self.tk_app.winfo_reqheight()) // 2
        self.tk_app.geometry(f'+{x}+{y}')

    def clear_log_file(self) -> None:
        """Clear the log file for this Application.

        This method removes all content from the log file, effectively clearing it.
        """
        try:
            with open(self._directory_service.user_log_file, 'w', encoding='utf-8') as f:
                f.write('')
        except IOError as e:
            print(f'Error clearing log file {self._directory_service.user_log_file}: {e}')

    def close(self) -> None:
        """Close this application."""
        self.logger.info('Closing application...')
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
            gc.collect()  # Process garbage collection for tk/tcl elements

    def log(self, message: str) -> None:
        """Post a message to this Application's log text file.

        Args:
            message: Message to be sent to this Application's log file.
        """
        try:
            with open(self._directory_service.user_log_file, 'a', encoding='utf-8') as f:
                f.write(f'{message}\n')
        except IOError as e:
            print(f'Error writing to log file {self._directory_service.user_log_file}: {e}')

    def on_pre_run(self) -> None:
        """Method that is called directly before calling parent Tk mainloop.

        By this point, all models, view models and views should be created.
        This allows some extra logic to occur before our app begins.

        Note:
            It is recommended to override this method to create your own functionality.
        """
        pass

    def set_app_state_busy(self) -> None:
        """Set the application state to busy.

        This method changes the cursor to a busy state, indicating that the application is processing.
        """
        self.update_cursor(TK_CURSORS.WAIT)

    def set_app_state_normal(self) -> None:
        """Set the application state to normal.

        This method changes the cursor back to normal, indicating that the application is ready for user interaction.
        """
        self.update_cursor(TK_CURSORS.DEFAULT)

    def set_logging_level(self, level: int) -> None:
        """Set the logging level for this Application.

        Args:
            level: The logging level to set. Should be one of the logging module's levels.
        """
        if not isinstance(level, int):
            raise TypeError('Logging level must be an integer.')
        super().set_logging_level(level)
        self.logger.info(f'Logging level set to {logging.getLevelName(level)}')
        self.runtime_info.set('logging_level', level)

    def start(self) -> None:
        """Start the application."""
        super().start()
        self.on_pre_run()
        self.tk_app.after(100, lambda: self.logger.info('Ready...'))
        self.tk_app.focus()
        self.tk_app.mainloop()

    def stop(self) -> None:
        """Stop the application."""
        super().stop()

    def toggle_fullscreen(self, fullscreen: Optional[bool] = None) -> None:
        """Toggle fullscreen mode for this Application.

        Args:
            fullscreen: If True, the application will be set to fullscreen.
                       If False, the application will exit fullscreen mode.
                       If None, it will toggle the current state.
        """
        if fullscreen is None:
            fullscreen = not self._runtime_info.get('full_screen', False)
        self.tk_app.attributes('-fullscreen', fullscreen)

    def update_cursor(self, cursor: Union[TK_CURSORS, str]) -> None:
        """Update the cursor for this Application.

        This method changes the cursor style for the main application window.

        Args:
            cursor: The cursor style to set. Can be a TK_CURSORS enum or valid Tkinter cursor string.

        Raises:
            TypeError: If cursor is not a string or TK_CURSORS enum.
        """
        if isinstance(cursor, TK_CURSORS):
            cursor = cursor.value
        if not isinstance(cursor, str):
            raise TypeError('Cursor must be a string representing a valid Tkinter cursor type.')
        self.tk_app.config(cursor=cursor)
        self.tk_app.update_idletasks()

"""Application ABC types for the Pyrox framework."""
from __future__ import annotations

from dataclasses import dataclass
import datetime
from enum import Enum
import gc
from logging import getLevelNamesMapping, getLevelName
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

from .abc import Buildable, Runnable, SupportsJsonLoading, SupportsJsonSaving
from .abc import meta, runtime, stream
from ..services.logging import LoggingManager
from pyrox.services.file import remove_all_files
from pyrox.services.env import EnvManager

__all__ = (
    'BaseMenu',
    'ApplicationConfiguration',
    'ApplicationDirectoryService',
    'ApplicationRuntimeInfo',
    'Application',
)

LOG_LEVEL = 'PYROX_LOG_LEVEL'
UI_FULLSCREEN = 'UI_WINDOW_FULLSCREEN'
UI_WINDOW_POSITION = 'UI_WINDOW_POSITION'
UI_WINDOW_SIZE = 'UI_WINDOW_SIZE'
UI_WINDOW_STATE = 'UI_WINDOW_STATE'


class BaseMenu(Buildable):
    """Base menu for use in a UI Application.

    Args:
        root: The root Tk object this menu belongs to.

    Attributes:
        menu: The Tk Menu instance for this BaseMenu.
        root: The parent root item of this menu.
    """
    __slots__ = ('_root', '_menu')

    def __init__(self, root: Union[Tk, Toplevel]):
        super().__init__()
        self._root: Union[Tk, Toplevel] = root
        self._menu: Menu = Menu(self._root)

    @property
    def menu(self) -> Menu:
        """The Tk Menu instance for this BaseMenu.

        Returns:
            Menu: The Tk Menu object.
        """
        return self._menu

    @property
    def root(self) -> Union[Tk, Toplevel]:
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
        if not isinstance(menu, Menu):
            raise TypeError('Menu must be a Tkinter Menu instance.')
        cmds = {}
        try:
            last_index = menu.index('end')
            if not last_index or last_index < 0:
                return cmds
            for x in range(last_index + 1):
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

    def __init__(self, root: Union[Tk, Toplevel]):
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
        type_: The type of the application view.
        icon: The icon to use for the application window.
        size_: The size of the application window, specified as a string (e.g., "800x600").
    """
    headless: bool = False
    application_name: Optional[str] = meta.DEF_APP_NAME
    author_name: Optional[str] = meta.DEF_AUTHOR_NAME
    title: Optional[str] = meta.DEF_WIN_TITLE
    type_: ApplicationTkType = ApplicationTkType.ROOT
    icon: Optional[Union[str, Path]] = meta.DEF_ICON
    size_: Optional[str] = meta.DEF_WIN_SIZE

    @classmethod
    def _common_assembly(
        cls,
        headless: bool = False,
        application_name: str = meta.DEF_APP_NAME,
        author_name: str = meta.DEF_AUTHOR_NAME,
        title: str = meta.DEF_WIN_TITLE,
        type_: ApplicationTkType = ApplicationTkType.ROOT,
        icon: Optional[Union[str, Path]] = meta.DEF_ICON,
        size_: str = meta.DEF_WIN_SIZE
    ) -> Self:
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

        Returns:
            Self: A new ApplicationConfiguration instance.
        """
        return cls(
            headless=headless,
            application_name=application_name,
            author_name=author_name,
            title=title,
            type_=type_,
            icon=icon,
            size_=size_
        )

    @classmethod
    def toplevel(cls) -> Self:
        """Get a generic toplevel application configuration.

        Returns:
            Self: A toplevel ApplicationConfiguration instance.
        """
        return cls._common_assembly(
            type_=ApplicationTkType.TOPLEVEL,
        )

    @classmethod
    def root(cls) -> Self:
        """Get a generic root application configuration.

        Returns:
            Self: A root ApplicationConfiguration instance.
        """
        return cls._common_assembly()


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

    def __init__(
        self,
        author_name: Optional[str] = meta.DEF_AUTHOR_NAME,
        app_name: Optional[str] = meta.DEF_APP_NAME
    ) -> None:
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
                        remove_all_files(dir_path)
                    except OSError as e:
                        raise OSError(f'Failed to refresh directory {dir_path}: {e}') from e

    def get_log_file_stream(self) -> Any:
        """Get a SimpleStream for the user log file.

        Returns:
            stream object: A stream object for the user log file.
        """
        log_file = open(self.user_log_file, 'a', encoding='utf-8')
        return log_file


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

    def __init__(
        self,
        application: 'Application'
    ) -> None:
        super().__init__(
            file_location=application.directory_service.app_runtime_info_file,
        )
        self._application: 'Application' = application
        self._data = runtime.RuntimeDict(self.save_to_json)
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
    def data(self) -> runtime.RuntimeDict:
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
            self.application.log().warning(
                'No data loaded from the runtime info file, initializing with empty RuntimeDict.'
            )
            self._data = runtime.RuntimeDict(self.save_to_json)
            return

        if not isinstance(data, dict):
            raise TypeError('Loaded data must be a dictionary.')
        self.data = data

    def on_saving(self) -> dict:
        """Method to be called to retrieve the save data of the object.

        Returns:
            dict: The data to be saved.
        """
        return self._data.data

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
        multi_stream: The MultiStream for this Application.
        runtime_info: The runtime information for this Application.
        tasks: A hashed list of tasks for this Application.
        tk_app: The tk application instance for this Application.
    """
    __slots__ = (
        '_config',
        '_directory_service',
        '_frame',
        '_menu',
        '_multi_stream',
        '_runtime_info',
        '_tk_app'
    )

    def __init__(
        self,
        config: ApplicationConfiguration
    ) -> None:
        super().__init__()
        sys.excepthook = self._excepthook
        self.config = config or ApplicationConfiguration.root()
        self.directory_service = ApplicationDirectoryService(
            author_name=self.config.author_name,
            app_name=self.config.application_name
        )

    @property
    def tk_app(self) -> Tk:
        """The tk application instance for this Application.

        Returns:
            Union[Tk, ThemedTk]: The tkinter application instance.
        """
        if not isinstance(self._tk_app, Tk):
            raise RuntimeError('Applications only support Tk class functionality.')
        return self._tk_app

    @property
    def config(self) -> ApplicationConfiguration:
        """Configuration for this Application.

        Returns:
            ApplicationConfiguration: The application configuration.
        """
        return self._config

    @config.setter
    def config(self, value: ApplicationConfiguration) -> None:
        """Set the configuration for this Application.

        Args:
            value: The new configuration to set.

        Raises:
            TypeError: If the value is not an instance of ApplicationConfiguration.
        """
        if not isinstance(value, ApplicationConfiguration):
            raise TypeError('Config must be an instance of ApplicationConfiguration.')
        self._config = value

    @property
    def directory_service(self) -> ApplicationDirectoryService:
        """Directory service for this Application.

        This service provides access to various directories used by the application.

        Returns:
            ApplicationDirectoryService: The directory service instance.
        """
        return self._directory_service

    @directory_service.setter
    def directory_service(self, value: ApplicationDirectoryService) -> None:
        """Set the directory service for this Application.

        Args:
            value: The new directory service to set.

        Raises:
            TypeError: If the value is not an instance of ApplicationDirectoryService.
        """
        if not isinstance(value, ApplicationDirectoryService):
            raise TypeError('Directory service must be an instance of ApplicationDirectoryService.')
        self._directory_service = value

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
    def multi_stream(self) -> stream.MultiStream:
        """The MultiStream for this Application.

        This stream captures stdout and stderr and redirects them to multiple destinations.

        Returns:
            Optional[stream.MultiStream]: The MultiStream instance, or None if not set up.
        """
        return self._multi_stream

    @multi_stream.setter
    def multi_stream(self, value: stream.MultiStream) -> None:
        """Set the MultiStream for this Application.

        Args:
            value: The new MultiStream to set.

        Raises:
            TypeError: If the value is not an instance of stream.MultiStream.
        """
        if not isinstance(value, stream.MultiStream):
            raise TypeError('MultiStream must be an instance of stream.MultiStream.')
        self._multi_stream = value

    def _build_app_icon(self) -> None:
        icon_path = Path(str(self.config.icon))
        if icon_path.exists():
            self._tk_app.iconbitmap(self.config.icon)
            self._tk_app.iconbitmap(default=self.config.icon)
        else:
            self.log().warning(f'Icon file not found: {self.config.icon}.')

    def _build_env(self) -> None:
        if not EnvManager.is_loaded():
            raise RuntimeError('Environment variables have not been loaded. Please call EnvManager.load() before building the application.')
        logging_level = EnvManager.get(LOG_LEVEL, 'INFO')
        if logging_level is not None and isinstance(logging_level, (str, int)):
            self.set_logging_level(logging_level)

    def _build_frame(self) -> None:
        self._frame: Frame = Frame(master=self._tk_app, background='#2b2b2b')
        self._frame.pack(fill='both', expand=True)

    def _build_menu(self) -> None:
        self._menu = MainApplicationMenu(self.tk_app)

    def _build_multi_stream(self) -> None:
        if hasattr(self, '_multi_stream'):
            raise RuntimeError('MultiStream has already been set up for this application.')
        try:
            self._multi_stream = stream.MultiStream(
                self._directory_service.get_log_file_stream(),
                stream.SimpleStream(self.application_log))
            LoggingManager.register_callback_to_captured_streams(self._multi_stream.write)
            self.log().info(f'Logging to file: {self._directory_service.user_log_file}')
        except Exception as e:
            raise RuntimeError(f'Failed to set up MultiStream: {e}') from e

    def _build_tk_app_instance(self) -> None:
        if self.config.type_ == ApplicationTkType.ROOT:
            self._tk_app = Tk()
            self._tk_app.bind('<Configure>', self._on_tk_configure)
            self._tk_app.bind('<F11>', lambda _: self.toggle_fullscreen(not self._tk_app.attributes('-fullscreen')))
        elif self.config.type_ == ApplicationTkType.TOPLEVEL:
            self._tk_app = Toplevel()
        else:
            raise ValueError('Application type is not supported. Please use ROOT or TOPLEVEL.')

    def _connect_tk_attributes(self) -> None:
        if isinstance(self.tk_app, Tk):
            self.tk_app.report_callback_exception = self._excepthook
        self.tk_app.protocol('WM_DELETE_WINDOW', self.close)
        self.tk_app.title(self.config.title)

    def _excepthook(self, exc_type, exc_value, exc_traceback) -> None:
        """Handle uncaught exceptions.

        Args:
            exc_type: Exception type.
            exc_value: Exception value.
            exc_traceback: Exception traceback.
        """
        if issubclass(exc_type, KeyboardInterrupt):
            return
        self.log().error(
            msg=f'Uncaught exception: {exc_value}',
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    def _on_tk_configure(self, event: Event) -> None:
        """Handle the Tk configure event.

        This method is called when the Tk application is configured.

        Args:
            event: The Tk event that triggered this method.
        """
        root = event.widget
        if not isinstance(root, Tk):
            return

        if event.widget != self.tk_app:
            return

        self._set_geometry_env(
            window_size=f'{root.winfo_width()}x{root.winfo_height()}',
            window_position=(root.winfo_x(), root.winfo_y()),
            window_state=root.state(),
            fullscreen_bool=bool(root.attributes('-fullscreen'))
        )

    def _restore_fullscreen(self) -> None:
        full_screen = EnvManager.get(UI_FULLSCREEN, False, bool)
        if not isinstance(full_screen, bool):
            raise ValueError('UI_WINDOW_FULLSCREEN must be a boolean value.')
        if full_screen:
            self.toggle_fullscreen(full_screen)

    def _restore_window_position(self) -> None:
        window_position = EnvManager.get(UI_WINDOW_POSITION, None, tuple)
        if window_position is None:
            return
        if not isinstance(window_position, tuple) or len(window_position) != 2:
            return  # Invalid format, skip setting position
        try:
            self.tk_app.geometry(f'+{window_position[0]}+{window_position[1]}')
        except TclError as e:
            self.log().error(f'TclError: Could not set window position: {e}')

    def _restore_window_size(self) -> None:
        window_size = EnvManager.get(UI_WINDOW_SIZE, self.config.size_, str)
        if not isinstance(window_size, str):
            return  # Invalid format, skip setting size
        try:
            self.tk_app.geometry(window_size)
        except TclError as e:
            self.log().error(f'TclError: Could not set window size: {e}')

    def _restore_window_state(self) -> None:
        window_state = EnvManager.get(UI_WINDOW_STATE, 'normal', str)
        if not isinstance(window_state, str):
            return  # Invalid format, skip setting state
        try:
            self.tk_app.state(window_state)
        except TclError as e:
            self.log().error(f'TclError: Could not set window state: {e}')

    def _restore_geometry_env(self) -> None:
        self._restore_fullscreen()
        self._restore_window_size()
        self._restore_window_state()
        self._restore_window_position()

    def _set_fullscreen_env(self, fullscreen: bool) -> None:
        if not isinstance(fullscreen, bool):
            raise TypeError('Fullscreen must be a boolean value.')
        EnvManager.set(UI_FULLSCREEN, str(fullscreen))

    def _set_window_position_env(self, position: tuple) -> None:
        if not isinstance(position, tuple) or len(position) != 2:
            raise ValueError('Position must be a tuple of (x, y) coordinates.')
        EnvManager.set(UI_WINDOW_POSITION, str(position))

    def _set_window_size_env(self, size: str) -> None:
        if not isinstance(size, str):
            raise TypeError('Size must be a string value.')
        EnvManager.set(UI_WINDOW_SIZE, size)

    def _set_window_state_env(self, state: str) -> None:
        if not isinstance(state, str):
            raise TypeError('State must be a string value.')
        EnvManager.set(UI_WINDOW_STATE, state)

    def _set_geometry_env(
        self,
        window_size: str,
        window_position: tuple,
        window_state: str,
        fullscreen_bool,
    ) -> None:
        if window_size is not None:
            self._set_window_size_env(window_size)

        if window_position is not None:
            self._set_window_position_env(window_position)

        if window_state is not None:
            self._set_window_state_env(window_state)

        if fullscreen_bool is not None:
            self._set_fullscreen_env(fullscreen_bool)

    def application_log(self, message: str) -> None:
        """Post a message.

        This method should be overridden to implement custom logging functionality.

        Args:
            message: Message to be sent to this Application's log file.
        """
        ...

    def build(self) -> None:
        self._build_env()
        self._build_multi_stream()
        self._build_tk_app_instance()
        self._connect_tk_attributes()
        self._build_app_icon()
        self._build_frame()
        self._build_menu()
        self._directory_service.build_directory()
        self._restore_geometry_env()
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
        self.log().info('Closing application...')
        self.stop()
        try:
            if isinstance(self.tk_app, Tk):
                self.tk_app.quit()
                self.tk_app.destroy()
            elif isinstance(self.tk_app, Toplevel):
                self.tk_app.destroy()
        except TclError:
            self.log().error('TclError: Could not destroy the parent window')
        finally:
            gc.collect()  # Process garbage collection for tk/tcl elements

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
        self.update_cursor(meta.TK_CURSORS.WAIT)

    def set_app_state_normal(self) -> None:
        """Set the application state to normal.

        This method changes the cursor back to normal, indicating that the application is ready for user interaction.
        """
        self.update_cursor(meta.TK_CURSORS.DEFAULT)

    def set_logging_level(self, level: Union[int, str]) -> None:
        """Set the logging level for this Application.

        Args:
            level: The logging level to set. Should be one of the logging module's levels.
        """
        level_mapping = getLevelNamesMapping()

        if isinstance(level, str):
            if level.upper() in level_mapping:
                level = level_mapping[level.upper()]
            else:
                raise ValueError(f'Invalid logging level string: {level}')

        if not isinstance(level, int):
            raise TypeError('Logging level must be an integer.')

        level_name = getLevelName(level)
        if level_name == 'Level %s' % level:
            raise ValueError(f'Invalid logging level integer: {level}')
        self.log().info(f'Logging level set to {level_name} ({level}).')
        LoggingManager.set_logging_level(level)
        EnvManager.set(LOG_LEVEL, level_name)

    def start(self) -> None:
        """Start the application."""
        super().start()
        self.on_pre_run()
        self.tk_app.after(100, lambda: self.log().info('Ready...'))
        self.tk_app.focus()
        self.tk_app.mainloop()

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

    def update_cursor(self, cursor: Union[meta.TK_CURSORS, str]) -> None:
        """Update the cursor for this Application.

        This method changes the cursor style for the main application window.

        Args:
            cursor: The cursor style to set. Can be a TK_CURSORS enum or valid Tkinter cursor string.

        Raises:
            TypeError: If cursor is not a string or TK_CURSORS enum.
        """
        if isinstance(cursor, meta.TK_CURSORS):
            cursor = cursor.value
        if not isinstance(cursor, str):
            raise TypeError('Cursor must be a string representing a valid Tkinter cursor type.')
        self.tk_app.config(cursor=cursor)
        self.tk_app.update_idletasks()

"""Application ABC types for the Pyrox framework."""
from __future__ import annotations

import gc
from logging import getLevelNamesMapping, getLevelName
from pathlib import Path
import sys
from tkinter import Frame, TclError
from tkinter import (
    Event,
    Tk,
    Toplevel,
)
from typing import Optional, Union
from pyrox.models.abc import Runnable, meta, stream
from pyrox.services.logging import LoggingManager
from pyrox.services.env import EnvManager
from pyrox.services.file import PlatformDirectoryService
from .menu import MainApplicationMenu

__all__ = (
    'Application',
)


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
        tk_instance: Tk,
    ) -> None:
        super().__init__()
        sys.excepthook = self._excepthook
        self._directory_service = PlatformDirectoryService()

        # Build tk info
        self._tk_app = tk_instance

        self._menu = MainApplicationMenu(self.tk_app)

        self._frame: Frame = Frame(master=self.tk_app, background='#2b2b2b')
        self._frame.pack(fill='both', expand=True)

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
    def directory_service(self) -> PlatformDirectoryService:
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
    def multi_stream(self) -> stream.MultiStream:
        """The MultiStream for this Application.

        This stream captures stdout and stderr and redirects them to multiple destinations.

        Returns:
            Optional[stream.MultiStream]: The MultiStream instance, or None if not set up.
        """
        return self._multi_stream

    def _build_app_icon(self) -> None:
        icon_path = Path(EnvManager.get('PYROX_APP_ICON', meta.DEF_ICON, str))
        if icon_path.exists():
            self.tk_app.iconbitmap(icon_path)
            self.tk_app.iconbitmap(default=icon_path)
        else:
            self.log().warning(f'Icon file not found: {icon_path}.')

    def _build_env(self) -> None:
        if not EnvManager.is_loaded():
            raise RuntimeError('Environment variables have not been loaded. Please call EnvManager.load() before building the application.')
        logging_level = EnvManager.get('PYROX_LOG_LEVEL', 'INFO')
        if logging_level is not None and isinstance(logging_level, (str, int)):
            self.set_logging_level(logging_level)

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

    def _connect_tk_attributes(self) -> None:
        self.tk_app.report_callback_exception = self._excepthook
        self.tk_app.protocol('WM_DELETE_WINDOW', self.close)
        self.tk_app.bind('<Configure>', self._on_tk_configure)
        self.tk_app.bind('<F11>', lambda _: self.toggle_fullscreen(not self.tk_app.attributes('-fullscreen')))
        self.tk_app.title(EnvManager.get('PYROX_WINDOW_TITLE', 'Pyrox Application', str))

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
        full_screen = EnvManager.get('UI_FULLSCREEN', False, bool)
        if not isinstance(full_screen, bool):
            raise ValueError('UI_WINDOW_FULLSCREEN must be a boolean value.')
        if full_screen:
            self.toggle_fullscreen(full_screen)

    def _restore_window_position(self) -> None:
        window_position = EnvManager.get('UI_WINDOW_POSITION', None, tuple)
        if window_position is None:
            return
        if not isinstance(window_position, tuple) or len(window_position) != 2:
            return  # Invalid format, skip setting position
        try:
            self.tk_app.geometry(f'+{window_position[0]}+{window_position[1]}')
        except TclError as e:
            self.log().error(f'TclError: Could not set window position: {e}')

    def _restore_window_size(self) -> None:
        window_size = EnvManager.get('UI_WINDOW_SIZE', '600x600', str)
        if not isinstance(window_size, str):
            return  # Invalid format, skip setting size
        try:
            self.tk_app.geometry(window_size)
        except TclError as e:
            self.log().error(f'TclError: Could not set window size: {e}')

    def _restore_window_state(self) -> None:
        window_state = EnvManager.get('UI_WINDOW_STATE', 'normal', str)
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
        EnvManager.set('UI_FULLSCREEN', str(fullscreen))

    def _set_window_position_env(self, position: tuple) -> None:
        if not isinstance(position, tuple) or len(position) != 2:
            raise ValueError('Position must be a tuple of (x, y) coordinates.')
        EnvManager.set('UI_WINDOW_POSITION', str(position))

    def _set_window_size_env(self, size: str) -> None:
        if not isinstance(size, str):
            raise TypeError('Size must be a string value.')
        EnvManager.set('UI_WINDOW_SIZE', size)

    def _set_window_state_env(self, state: str) -> None:
        if not isinstance(state, str):
            raise TypeError('State must be a string value.')
        EnvManager.set('UI_WINDOW_STATE', state)

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
        self._connect_tk_attributes()
        self._build_app_icon()
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
        EnvManager.set('PYROX_LOG_LEVEL', level_name)

    def start(self) -> None:
        """Start the application."""
        super().start()
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

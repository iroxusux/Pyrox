"""Application ABC types for the Pyrox framework."""
from __future__ import annotations

import gc
import sys
from typing import Union

from pyrox.interfaces import IApplicationGuiMenu, IGuiBackend, IGuiWindow
from pyrox.models.abc import Runnable, meta, stream
from pyrox.services import GuiManager, LoggingManager, log, get_env, set_env
from pyrox.models import Workspace
from pyrox.services.file import PlatformDirectoryService

__all__ = ('Application',)


class Application(Runnable):
    """A main Application class to manage running application data and services.

    This class provides a framework-agnostic GUI application using the GUI backend
    manager service. It supports multiple GUI frameworks through a unified interface.

    Attributes:
        directory_service: The directory service for this Application.
        gui_manager: The GUI manager service for backend operations.
        gui_backend: The active GUI backend instance.
        frame: The main frame for this Application (framework-specific).
        menu: The main application menu.
        multi_stream: The MultiStream for this Application.
        is_gui_enabled: Whether GUI is enabled for this application.
    """
    __slots__ = (
        '_after_id',
        '_directory_service',
        '_frame',
        '_framework',
        '_is_gui_enabled',
        '_menu',
        '_log_stream',
        '_workspace',
    )

    def __init__(
        self,
    ) -> None:
        super().__init__()
        sys.excepthook = self._excepthook
        self._after_id: Union[int, str, None] = None
        self._directory_service = PlatformDirectoryService()
        self._log_stream = self.dir_service.get_log_file_stream()
        LoggingManager.register_callback_to_captured_streams(self._log_stream.write)

        if self.is_gui_enabled:
            self.window  # Ensure window is created
            self.menu  # Ensure menu is created
            self._workspace = Workspace()

        else:
            self._workspace = None

    @property
    def dir_service(self) -> PlatformDirectoryService:
        """Directory service for this Application.

        This service provides access to various directories used by the application.

        Returns:
            ApplicationDirectoryService: The directory service instance.
        """
        return self._directory_service

    @property
    def gui_backend(self) -> IGuiBackend:
        """The active GUI backend instance for this Application.

        Returns:
            GuiBackend: The active GUI backend instance.
        """
        return GuiManager.unsafe_get_backend()

    @property
    def is_gui_enabled(self) -> bool:
        """Whether GUI is enabled for this Application.

        Returns:
            bool: True if GUI is enabled, False for headless mode.
        """
        return get_env('UI_AUTO_INIT', True, bool)

    @property
    def menu(self) -> IApplicationGuiMenu:
        """ApplicationGuiMenu menu for this Application.

        Returns:
            ApplicationGuiMenu: The main application menu.
        """
        return self.gui_backend.get_root_application_gui_menu()

    @property
    def log_stream(self) -> stream.SimpleStream:
        """The SimpleStream for this Application.

        This stream captures stdout and stderr and redirects them to the log file for this application.

        Returns:
            stream.SimpleStream: The SimpleStream instance.
        """
        return self._log_stream

    @property
    def window(self) -> IGuiWindow:
        """The root window instance for this Application.

        Returns:
            Optional[GuiWindow]: The root window instance provided by the GUI backend, or None if GUI is disabled.
        """
        return self.gui_backend.get_root_gui_window()

    @property
    def workspace(self) -> Workspace:
        """The main Workspace for this Application.

        Returns:
            Workspace: The main workspace instance.
        """
        if not self._workspace:
            raise RuntimeError('Workspace is not initialized for this Application.')
        return self._workspace

    def _connect_gui_attributes(self) -> None:
        """Connect GUI-specific attributes and events.

        This method configures the native window with event handlers and protocols.
        """
        self.gui_backend.reroute_excepthook(self._excepthook)
        self.gui_backend.subscribe_to_window_close_event(self.close)
        self.gui_backend.subscribe_to_window_change_event(self._on_gui_configure)
        self.gui_backend.set_title(get_env('PYROX_WINDOW_TITLE', 'Pyrox Application', str))

    def _on_gui_configure(self) -> None:
        """Handle GUI configure events.

        This method is called when the GUI window is configured (resized, moved, etc.).
        """

        if self._after_id:  # If we've scheduled an event, cancel it
            self.gui_backend.cancel_scheduled_event(self._after_id)

        self._after_id = self.gui_backend.schedule_event(500, self._set_geometry_env)

    def _excepthook(self, exc_type, exc_value, exc_traceback) -> None:
        """Handle uncaught exceptions.

        Args:
            exc_type: Exception type.
            exc_value: Exception value.
            exc_traceback: Exception traceback.
        """
        if issubclass(exc_type, KeyboardInterrupt):
            return
        log(self).error(
            msg=f'Uncaught exception: {exc_value}',
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    def _restore_fullscreen(self) -> None:
        """Restore fullscreen setting from environment."""
        if not self.is_gui_enabled:
            return

        full_screen = get_env(
            key='UI_WINDOW_FULLSCREEN',
            default=False,
            cast_type=bool
        )

        if full_screen:
            self.window.set_fullscreen(full_screen)

    def _restore_window_position(self) -> None:
        """Restore window position from environment settings."""
        if not self.is_gui_enabled:
            return

        window_position = get_env(
            key='UI_WINDOW_POSITION',
            default=None,
            cast_type=tuple
        )

        if not window_position:
            log(self).warning('No window position found in environment; skipping restore.')
            return

        if len(window_position) != 2:
            log(self).warning('Invalid window position format in environment; skipping restore.')
            return

        self.window.set_geometry(
            width=self.window.get_width(),
            height=self.window.get_height(),
            x=window_position[0],
            y=window_position[1]
        )

    def _restore_window_size(self) -> None:
        """Restore window size from environment settings."""
        if not self.is_gui_enabled:
            return

        window_size = get_env(
            key='UI_WINDOW_SIZE',
            default=None,
            cast_type=str
        )

        if not window_size:
            log(self).warning('No window size found in environment; skipping restore.')
            return

        window_size_arr = window_size.split('x')
        if len(window_size_arr) != 2:
            log(self).warning('Invalid window size format in environment; skipping restore.')
            return

        self.window.set_geometry(
            width=int(window_size_arr[0]),
            height=int(window_size_arr[1])
        )

    def _restore_window_state(self) -> None:
        """Restore window state from environment settings."""
        if not self.is_gui_enabled:
            return

        window_state = get_env(
            key='UI_WINDOW_STATE',
            default='normal',
            cast_type=str
        )

        if not window_state:
            log(self).warning('No window state found in environment; skipping restore.')
            return

        self.window.set_state(window_state)

    def _restore_geometry_env(self) -> None:
        """Restore window geometry settings from environment variables."""
        self._restore_fullscreen()
        self._restore_window_size()
        self._restore_window_state()
        self._restore_window_position()

    def _set_fullscreen_env(self, fullscreen: bool) -> None:
        """Set fullscreen state in environment variables.

        Args:
            fullscreen: Whether the application should be in fullscreen mode.

        Raises:
            TypeError: If fullscreen is not a boolean value.
        """
        if not isinstance(fullscreen, bool):
            raise TypeError('Fullscreen must be a boolean value.')
        set_env('UI_FULLSCREEN', str(fullscreen))

    def _set_window_position_env(self, position: tuple) -> None:
        """Set window position in environment variables.

        Args:
            position: Tuple of (x, y) coordinates for window position.

        Raises:
            ValueError: If position is not a tuple of two elements.
        """
        if not isinstance(position, tuple) or len(position) != 2:
            raise ValueError('Position must be a tuple of (x, y) coordinates.')
        set_env('UI_WINDOW_POSITION', str(position))

    def _set_window_size_env(self, size: str) -> None:
        """Set window size in environment variables.

        Args:
            size: String representation of window size (e.g., "800x600").

        Raises:
            TypeError: If size is not a string value.
        """
        if not isinstance(size, str):
            raise TypeError('Size must be a string value.')
        set_env('UI_WINDOW_SIZE', size)

    def _set_window_state_env(self, state: str) -> None:
        """Set window state in environment variables.

        Args:
            state: String representation of window state (e.g., "normal", "maximized").

        Raises:
            TypeError: If state is not a string value.
        """
        if not isinstance(state, str):
            raise TypeError('State must be a string value.')
        set_env('UI_WINDOW_STATE', state)

    def _set_geometry_env(
        self,
    ) -> None:
        """Set window geometry settings in environment variables.
        """
        window_size = self.window.get_size()
        window_position = self.window.get_position()
        window_state = self.window.get_state()
        fullscreen_bool = self.window.is_fullscreen()

        if window_size is not None:
            self._set_window_size_env(f'{window_size[0]}x{window_size[1]}')

        if window_position is not None:
            self._set_window_position_env(window_position)

        if window_state is not None:
            self._set_window_state_env(window_state)

        if fullscreen_bool is not None:
            self._set_fullscreen_env(fullscreen_bool)

    def log(self, message: str) -> None:
        """Post a message to the application log.

        This method should be overridden to implement custom logging functionality.

        Args:
            message: Message to be sent to this Application's log file.
        """
        if self.is_gui_enabled:
            self.workspace.log_window.log(message)
        else:
            print(message)

    def build(self) -> None:
        """Build and initialize the application."""
        self._connect_gui_attributes()
        self.gui_backend.set_icon(get_env('UI_ICON_PATH', '', str))
        self._restore_geometry_env()
        self._directory_service.build_directory()
        if self._workspace:
            self.workspace.build()
            self.workspace.set_status('Ready...')
        super().build()

    def close(self) -> None:
        """Close this application."""
        log(self).info('Closing application...')
        self.stop()
        try:
            if not self.is_gui_enabled or not self.gui_backend:
                return
            self.gui_backend.quit_application()
        except Exception as e:
            log(self).error(f'Error closing GUI: {e}')
        finally:
            gc.collect()  # Process garbage collection for GUI elements

    def clear_log_file(self) -> None:
        """Clear the log file for this Application.

        This method removes all content from the log file, effectively clearing it.
        """
        try:
            with open(self._directory_service.user_log_file, 'w', encoding='utf-8') as f:
                f.write('')
        except IOError as e:
            print(f'Error clearing log file {self._directory_service.user_log_file}: {e}')

    def set_app_state_busy(self) -> None:
        """Set the application state to busy.

        This method changes the cursor to a busy state, indicating that the application is processing.
        """
        if not self.is_gui_enabled or not self.gui_backend:
            return

        self.gui_backend.update_cursor(meta.TK_CURSORS.WAIT.value)

    def set_app_state_normal(self) -> None:
        """Set the application state to normal.

        This method changes the cursor back to normal, indicating that the application is ready for user interaction.
        """
        if not self.is_gui_enabled or not self.gui_backend:
            return

        self.gui_backend.update_cursor(meta.TK_CURSORS.DEFAULT.value)

    def start(self) -> None:
        """Start the application."""
        super().start()
        if not self.is_gui_enabled:
            log(self).info('Ready... (headless mode)')
            return
        self.gui_backend.schedule_event(
            100,
            lambda: log(self).info('Ready...')
        )
        self.window.focus()
        self.gui_backend.run_main_loop()


if __name__ == '__main__':
    import pyrox  # noqa: F401
    app = Application()
    app.build()
    app.start()

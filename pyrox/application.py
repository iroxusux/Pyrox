"""Application ABC types for the Pyrox framework."""
from __future__ import annotations

import gc
from io import TextIOWrapper
import sys
from typing import (
    Any,
)

from pyrox.interfaces import (
    EnvironmentKeys,
    IApplication,
    IGuiBackend,
)
from pyrox.models.protocols import (
    Nameable,
    Describable,
    Buildable,
    Runnable,
)
from pyrox.models.abc import meta
from pyrox.services import GuiManager, LoggingManager, log, EnvManager
from pyrox.models import Workspace
from pyrox.services.file import PlatformDirectoryService

__all__ = ('Application',)


def _bootstrap() -> None:
    """Bootstrap the application environment."""
    sys.excepthook = Application.except_hook

    GuiManager.unsafe_get_backend().create_root_window()
    GuiManager.unsafe_get_backend().create_application_gui_menu()
    GuiManager.unsafe_get_backend().restore_window_geometry()
    GuiManager.unsafe_get_backend().subscribe_to_window_change_event(
        GuiManager.unsafe_get_backend().save_window_geometry
    )


class Application(
    IApplication,
    Nameable,
    Describable,
    Runnable
):
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

    _env: type[EnvManager] = EnvManager
    _gui_mgr: type[GuiManager] = GuiManager
    _logging: type[LoggingManager] = LoggingManager
    _directory: type[PlatformDirectoryService] = PlatformDirectoryService

    def __init__(
        self,
    ) -> None:
        # Initialize base classes
        Nameable.__init__(self, name=EnvManager.get(
            EnvironmentKeys.core.APP_NAME,
            'Pyrox Application',
            str))
        Describable.__init__(self, description=EnvManager.get(
            EnvironmentKeys.core.APP_DESCRIPTION,
            'A Pyrox Application',
            str
        ))
        Runnable.__init__(self)

        # Initialize application services
        _bootstrap()

        # Set up logging
        LoggingManager.register_callback_to_captured_streams(self.log_stream.write)

        # Initialize workspace
        self._workspace = Workspace()

    @property
    def env(self) -> type[EnvManager]:
        """The environment manager for this Application.

        Returns:
            type[EnvManager]: The environment manager class.
        """
        return self._env

    @property
    def gui(self) -> IGuiBackend:
        """The GUI backend for this Application.

        Returns:
            IGuiBackend: The GUI backend instance.
        """
        return self.gui_mgr.unsafe_get_backend()

    @property
    def gui_mgr(self) -> type[GuiManager]:
        """The GUI manager for this Application.

        Returns:
            type[GuiManager]: The GUI manager class.
        """
        return self._gui_mgr

    @property
    def logging(self) -> type[LoggingManager]:
        """The logging manager for this Application.

        Returns:
            type[LoggingManager]: The logging manager class.
        """
        return self._logging

    @property
    def directory(self) -> type[PlatformDirectoryService]:
        """The directory service for this Application.

        Returns:
            type[PlatformDirectoryService]: The directory service class.
        """
        return self._directory

    @property
    def log_stream(self) -> TextIOWrapper:
        """The SimpleStream for this Application.

        This stream captures stdout and stderr and redirects them to the log file for this application.

        Returns:
            stream.SimpleStream: The SimpleStream instance.
        """
        return self.directory.get_log_file_stream()

    @property
    def workspace(self) -> Workspace:
        """The main Workspace for this Application.

        Returns:
            Workspace: The main workspace instance.
        """
        return self._workspace

    def get_author(self) -> str:
        """Get the application author.

        Returns:
            str: The application author.
        """
        return self.env.get(
            EnvironmentKeys.core.APP_AUTHOR,
            'Unknown Author',
            str
        )

    def get_version(self) -> str:
        """Get the application version.

        Returns:
            str: The application version.
        """
        return '1.0.0'  # Placeholder version until we get it from pyproject.toml

    def hook_to_gui(self) -> None:
        self.gui.reroute_excepthook(self.except_hook)
        self.gui.subscribe_to_window_close_event(self.on_close)
        self.gui.set_title(
            EnvManager.get(
                EnvironmentKeys.core.APP_WINDOW_TITLE,
                'Pyrox Application',
                str
            )
        )
        self.gui.set_icon(
            EnvManager.get(
                EnvironmentKeys.core.APP_ICON,
                '',
                str
            )
        )

    @staticmethod
    def except_hook(
        exc_type: type,
        exc_value: Exception,
        traceback: Any
    ) -> None:
        """Handle uncaught exceptions.

        Args:
            exc_type: Exception type.
            exc_value: Exception value.
            exc_traceback: Exception traceback.
        """
        if issubclass(exc_type, KeyboardInterrupt):
            return
        log().error(
            msg=f'Uncaught exception: {exc_value}',
            exc_info=(exc_type, exc_value, traceback)
        )

    def on_close(self) -> None:
        """Close this application."""
        log(self).info('Closing application...')
        self.stop()
        try:
            self.gui.quit_application()
        except Exception as e:
            log(self).error(f'Error closing GUI: {e}')
        finally:
            gc.collect()  # Process garbage collection for GUI elements

    def _restore_log_window_height(self) -> None:
        """Restore log window height from environment settings."""
        log_window_height = EnvManager.get(
            key=EnvironmentKeys.ui.UI_LOG_WINDOW_HEIGHT,
            default=None,
            cast_type=float
        )

        if log_window_height is None:
            return

        self.workspace.set_log_window_height(log_window_height)

    def _restore_main_window_sash(self) -> None:
        """Restore main window sash position from environment settings."""

        main_window_sash = EnvManager.get(
            key=EnvironmentKeys.ui.UI_SIDEBAR_WIDTH,
            default=None,
            cast_type=float
        )

        if main_window_sash is None:
            log(self).warning('No main window sash position found in environment; skipping restore.')
            return

        self.workspace.set_sidebar_width(main_window_sash)

    def _restore_sash_positions(self) -> None:
        """Restore sash positions from environment settings."""
        self._restore_log_window_height()
        self._restore_main_window_sash()

    def _restore_geometry_env(self) -> None:
        """Restore window geometry settings from environment variables."""
        self._restore_sash_positions()

    def _set_log_window_height_env(
        self,
        height: float,
    ) -> None:
        """Set log window height in environment variables.
        This is a percentage of the screen full height.

        Args:
            height: Height of the log window in percentage of screen.

        Raises:
            TypeError: If height is not a float value.
        """
        if not isinstance(height, float):
            raise TypeError('Height must be a float value.')
        EnvManager.set(
            EnvironmentKeys.ui.UI_LOG_WINDOW_HEIGHT,
            str(height)
        )

    def _set_main_window_sash_env(
        self,
        width: float,
    ) -> None:
        """Set main window sash position in environment variables.
        This is a percentage of the screen full width.

        Args:
            width: Width of the main window sash in percentage of screen.

        Raises:
            TypeError: If width is not a float value.
        """
        if not isinstance(width, float):
            raise TypeError('Width must be a float value.')
        EnvManager.set(
            EnvironmentKeys.ui.UI_SIDEBAR_WIDTH,
            str(width)
        )

    def log(self, message: str) -> None:
        """Post a message to the application log.

        This method should be overridden to implement custom logging functionality.

        Args:
            message: Message to be sent to this Application's log file.
        """
        self.workspace.log_window.log(message)

    def build(self) -> None:
        """Build and initialize the application."""
        if self._workspace:
            self.workspace.build()
            self.workspace.set_status('Building...')

        self.hook_to_gui()
        self._restore_geometry_env()
        Buildable.build(self)
        self.workspace.set_status('Ready.')

    def clear_log_file(self) -> None:
        """Clear the log file for this Application.

        This method removes all content from the log file, effectively clearing it.
        """
        try:
            with open(self.directory.get_user_log_file(), 'w', encoding='utf-8') as f:
                f.write('')
        except IOError as e:
            print(f'Error clearing log file {self.directory.get_user_log_file()}: {e}')

    def set_app_state_busy(self) -> None:
        """Set the application state to busy.

        This method changes the cursor to a busy state, indicating that the application is processing.
        """

        self.gui.update_cursor(meta.TK_CURSORS.WAIT.value)

    def set_app_state_normal(self) -> None:
        """Set the application state to normal.

        This method changes the cursor back to normal, indicating that the application is ready for user interaction.
        """
        self.gui.update_cursor(meta.TK_CURSORS.DEFAULT.value)

    def run(self) -> int:
        """Start the application."""
        Runnable.run(self)
        self.gui.schedule_event(
            100,
            lambda: log(self).info('Ready...')
        )
        self.gui.focus_main_window()
        self.gui.run_main_loop()
        return 0


if __name__ == '__main__':
    import pyrox  # noqa: F401
    app = Application()
    app.build()
    app.run()

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
    IApplicationTask,
    IGuiBackend,
    IWorkspace,
)

from pyrox.models.abc import meta

from pyrox.models import (
    ApplicationTaskFactory,
    ServicesRunnableMixin,
)

from pyrox.models import Workspace
from pyrox.services import EnvManager

__all__ = ('Application',)


class Application(
    IApplication,
    ServicesRunnableMixin,
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

    def __init__(
        self,
    ) -> None:
        # Initialize base classes
        ServicesRunnableMixin.__init__(
            self,
            name=EnvManager.get(
                EnvironmentKeys.core.APP_NAME,
                'Pyrox Application',
                str),
            description=EnvManager.get(
                EnvironmentKeys.core.APP_DESCRIPTION,
                'A Pyrox Application',
                str
            ))

        # Initialize application services
        sys.excepthook = self.except_hook

        self.gui.unsafe_get_backend().create_root_window()
        self.gui.unsafe_get_backend().create_application_gui_menu()
        self.gui.unsafe_get_backend().restore_window_geometry()
        self.gui.unsafe_get_backend().subscribe_to_window_change_event(
            self.gui.unsafe_get_backend().save_window_geometry
        )

        # Set up logging
        self.logging.register_callback_to_captured_streams(self.log_stream.write)
        ApplicationTaskFactory.build_tasks(self)

        # Initialize workspace
        self._workspace = Workspace()

        # Initialize tasks
        self._tasks: list[IApplicationTask] = []

    @property
    def gui_backend(self) -> IGuiBackend:
        """The GUI backend for this Application.

        Returns:
            IGuiBackend: The GUI backend instance.
        """
        return self.gui.unsafe_get_backend()

    @property
    def log_stream(self) -> TextIOWrapper:
        """The SimpleStream for this Application.

        This stream captures stdout and stderr and redirects them to the log file for this application.

        Returns:
            stream.SimpleStream: The SimpleStream instance.
        """
        return self.directory.get_log_file_stream()

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

    def get_workspace(self) -> IWorkspace:
        """Get the application workspace object.

        Returns:
            Any: The application workspace.
        """
        return self._workspace

    def set_workspace(self, workspace: IWorkspace) -> None:
        """Set the application workspace object.

        Args:
            workspace: The application workspace to set.
        """
        self._workspace = workspace

    def hook_to_gui(self) -> None:
        self.gui_backend.reroute_excepthook(self.except_hook)
        self.gui_backend.subscribe_to_window_close_event(self.on_close)
        self.gui_backend.set_title(
            self.env.get(
                EnvironmentKeys.core.APP_WINDOW_TITLE,
                'Pyrox Application',
                str
            )
        )
        self.gui_backend.set_icon(
            self.env.get(
                EnvironmentKeys.core.APP_ICON,
                '',
                str
            )
        )

    def except_hook(
        self,
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
        self.log().error(
            msg=f'Uncaught exception: {exc_value}',
            exc_info=(exc_type, exc_value, traceback)
        )

    def on_close(self) -> None:
        """Close this application."""
        self.log().info('Closing application...')
        self.stop()
        try:
            self.gui.quit_application()
        except Exception as e:
            self.log().error(f'Error closing GUI: {e}')
        finally:
            gc.collect()  # Process garbage collection for GUI elements

    def register_task(
        self,
        task: IApplicationTask
    ) -> None:
        """Register an application task.

        Args:
            task: The application task to register.
        """
        if not isinstance(task, IApplicationTask):
            raise TypeError('Task must implement IApplicationTask interface.')

        if task in self._tasks:
            self.log().warning('Task is already registered; skipping.')
            return

        self._tasks.append(task)

    def unregister_task(
        self,
        task: IApplicationTask
    ) -> None:
        """Unregister an application task.

        Args:
            task: The application task to unregister.
        """
        if task not in self._tasks:
            self.log().warning('Task is not registered; cannot unregister.')
            return

        self._tasks.remove(task)

    def get_tasks(self) -> list[IApplicationTask]:
        """Get the list of registered application tasks.

        Returns:
            list[IApplicationTask]: The list of registered tasks.
        """
        return self._tasks

    def set_tasks(
        self,
        tasks: list[IApplicationTask]
    ) -> None:
        """Set the list of registered application tasks.

        Args:
            tasks: The list of application tasks to set.
        """
        for task in tasks:
            if not isinstance(task, IApplicationTask):
                raise TypeError('All tasks must implement IApplicationTask interface.')

        self._tasks = tasks

    def clear_tasks(self) -> None:
        """Clear all registered application tasks."""
        self._tasks.clear()

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

    def build(self) -> None:
        """Build and initialize the application."""
        self.workspace.build()
        self.workspace.set_status('Building...')
        self.hook_to_gui()
        self.workspace.set_status('Ready...')
        super().build()

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

        self.gui_backend.update_cursor(meta.TK_CURSORS.WAIT.value)

    def set_app_state_normal(self) -> None:
        """Set the application state to normal.

        This method changes the cursor back to normal, indicating that the application is ready for user interaction.
        """
        self.gui_backend.update_cursor(meta.TK_CURSORS.DEFAULT.value)

    def run(self) -> int:
        """Start the application."""
        self.build()
        super().run()
        self.gui_backend.schedule_event(
            100,
            lambda: self.log().info('Ready...')
        )
        self.gui_backend.focus_main_window()
        self.gui_backend.run_main_loop()
        return 0


if __name__ == '__main__':
    import pyrox  # noqa: F401
    app = Application()
    app.build()
    app.run()

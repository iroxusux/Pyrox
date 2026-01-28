"""Application interface abstractions for Pyrox framework.

These interfaces define the contracts for applications, tasks, and factory
patterns without implementation dependencies, enabling clean architectural
boundaries and extensible application design.
"""

from __future__ import annotations
from abc import abstractmethod
from typing import Any
from .protocols import (
    INameable,
    IDescribable,
    IRunnable,
)
from .gui import IWorkspace


class IApplicationTask(
    INameable,
    IDescribable,
    IRunnable,
):
    """Interface for application tasks.

    Defines the contract for tasks that can be executed within an application,
    providing a common interface for different types of work units.
    """

    @property
    def application(self) -> IApplication:
        """Get the parent application of this task.

        Returns:
            IApplication: The parent application instance.
        """
        return self.get_application()

    @application.setter
    def application(
        self,
        application: IApplication
    ) -> None:
        """Set the parent application for this task.

        Args:
            application: The application instance to set.
        """
        self.set_application(application)

    @abstractmethod
    def get_application(self) -> IApplication:
        """Get the parent application of this task.

        Returns:
            IApplication: The parent application instance.
        """
        ...

    @abstractmethod
    def set_application(
        self,
        application: IApplication
    ) -> None:
        """Set the parent application for this task.

        Args:
            application: The application instance to set.
        """
        ...

    @abstractmethod
    def inject(self) -> None:
        """Inject this task into the application context.
        This method should be overridden by subclasses to implement
        specific injection behavior.
        """
        ...

    @abstractmethod
    def uninject(self) -> None:
        """Remove this task from the application context.
        This method should be overridden by subclasses to implement
        specific un-injection behavior.
        """
        ...


class IApplication(
    INameable,
    IDescribable,
    IRunnable,
):
    """Interface for applications.

    Defines the contract for main application objects, providing a consistent
    interface for application initialization, execution, and management.
    """

    @property
    def version(self) -> str:
        """Get the application version.

        Returns:
            str: The application version.
        """
        return self.get_version()

    @property
    def author(self) -> str:
        """Get the application author.

        Returns:
            str: The application author.
        """
        return self.get_author()

    @property
    def tasks(self) -> list[IApplicationTask]:
        """Get the list of registered application tasks.

        Returns:
            list[IApplicationTask]: The list of registered tasks.
        """
        return self.get_tasks()

    @property
    def workspace(self) -> IWorkspace:
        """Get the application workspace object.

        Returns:
            Any: The application workspace.
        """
        return self.get_workspace()

    @abstractmethod
    def on_close(self) -> None:
        """Handle application close event.

        This method should be overridden by subclasses to implement
        specific cleanup and shutdown behavior.
        """
        ...

    @abstractmethod
    def except_hook(
        self,
        exc_type: type,
        exc_value: Exception,
        traceback: Any
    ) -> None:
        """Global exception hook for uncaught exceptions.

        Args:
            exc_type: The type of the exception.
            exc_value: The exception instance.
            traceback: The traceback object.
        """
        ...

    @abstractmethod
    def get_version(self) -> str:
        """Get the application version.

        Returns:
            str: The application version.
        """
        ...

    @abstractmethod
    def get_author(self) -> str:
        """Get the application author.

        Returns:
            str: The application author.
        """
        ...

    @abstractmethod
    def hook_to_gui(self) -> None:
        """Hook the application into the GUI framework.

        This method should be overridden by subclasses to implement
        specific GUI integration behavior.
        """
        ...

    @abstractmethod
    def register_task(
        self,
        task: IApplicationTask
    ) -> None:
        """Register a task with the application.

        Args:
            task: The application task to register.
        """
        ...

    @abstractmethod
    def unregister_task(
        self,
        task: IApplicationTask
    ) -> None:
        """Unregister a task from the application.

        Args:
            task: The application task to unregister.
        """
        ...

    @abstractmethod
    def get_tasks(self) -> list[IApplicationTask]:
        """Get the list of registered application tasks.

        Returns:
            list[IApplicationTask]: The list of registered tasks.
        """
        ...

    @abstractmethod
    def set_tasks(
        self,
        tasks: list[IApplicationTask]
    ) -> None:
        """Set the list of registered application tasks.

        Args:
            tasks: The list of application tasks to set.
        """
        ...

    @abstractmethod
    def clear_tasks(self) -> None:
        """Clear all registered application tasks.
        """
        ...

    @abstractmethod
    def get_workspace(self) -> Any:
        """Get the application workspace object.

        Returns:
            Any: The application workspace.
        """
        ...

    @abstractmethod
    def set_workspace(
        self,
        workspace: Any
    ) -> None:
        """Set the application workspace object.

        Args:
            workspace: The application workspace to set.
        """
        ...


__all__ = (
    'IApplicationTask',
    'IApplication',
)

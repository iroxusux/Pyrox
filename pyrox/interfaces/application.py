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


class IApplicationTask(
    INameable,
    IDescribable,
):
    """Interface for application tasks.

    Defines the contract for tasks that can be executed within an application,
    providing a common interface for different types of work units.
    """

    @abstractmethod
    def inject(self) -> None:
        """Inject this task into the application context.
        This method should be overridden by subclasses to implement
        specific injection behavior.
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

    @abstractmethod
    def on_close(self) -> None:
        """Handle application close event.

        This method should be overridden by subclasses to implement
        specific cleanup and shutdown behavior.
        """
        ...

    @staticmethod
    @abstractmethod
    def except_hook(
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


__all__ = (
    'IApplicationTask',
    'IApplication',
)

"""Application interface abstractions for Pyrox framework.

These interfaces define the contracts for applications, tasks, and factory
patterns without implementation dependencies, enabling clean architectural
boundaries and extensible application design.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type


class IApplicationTask(ABC):
    """Interface for application tasks.

    Defines the contract for tasks that can be executed within an application,
    providing a common interface for different types of work units.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the task name.

        Returns:
            str: The name of this task.
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Get the task description.

        Returns:
            str: A description of what this task does.
        """
        pass

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the task.

        Args:
            *args: Positional arguments for task execution.
            **kwargs: Keyword arguments for task execution.

        Returns:
            Any: Task execution result.
        """
        pass

    @abstractmethod
    def can_execute(self) -> bool:
        """Check if the task can be executed.

        Returns:
            bool: True if task can be executed, False otherwise.
        """
        pass

    @abstractmethod
    def get_status(self) -> str:
        """Get the current task status.

        Returns:
            str: Current status (e.g., 'ready', 'running', 'completed', 'failed').
        """
        pass


class ITaskFactory(ABC):
    """Interface for task factories.

    Provides functionality for creating and registering different types of tasks,
    enabling extensible task systems.
    """

    @abstractmethod
    def create_task(self, task_type: str, **kwargs) -> IApplicationTask:
        """Create a task of the specified type.

        Args:
            task_type: The type of task to create.
            **kwargs: Task creation parameters.

        Returns:
            IApplicationTask: The created task.
        """
        pass

    @abstractmethod
    def register_task_type(self, task_type: str, task_class: Type[IApplicationTask]) -> None:
        """Register a new task type.

        Args:
            task_type: The name of the task type.
            task_class: The task class to register.
        """
        pass

    @abstractmethod
    def get_available_task_types(self) -> List[str]:
        """Get list of available task types.

        Returns:
            List[str]: List of registered task type names.
        """
        pass

    @abstractmethod
    def is_task_type_registered(self, task_type: str) -> bool:
        """Check if a task type is registered.

        Args:
            task_type: The task type to check.

        Returns:
            bool: True if registered, False otherwise.
        """
        pass


class ILifecycleManager(ABC):
    """Interface for application lifecycle management.

    Provides functionality for managing application startup, shutdown,
    and lifecycle events in a consistent manner.
    """

    @abstractmethod
    def startup(self) -> bool:
        """Execute application startup sequence.

        Returns:
            bool: True if startup was successful.
        """
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """Execute application shutdown sequence.

        Returns:
            bool: True if shutdown was successful.
        """
        pass

    @abstractmethod
    def restart(self) -> bool:
        """Restart the application.

        Returns:
            bool: True if restart was successful.
        """
        pass

    @abstractmethod
    def register_startup_hook(self, callback: Any) -> None:
        """Register a callback to be called during startup.

        Args:
            callback: Function to call during startup.
        """
        pass

    @abstractmethod
    def register_shutdown_hook(self, callback: Any) -> None:
        """Register a callback to be called during shutdown.

        Args:
            callback: Function to call during shutdown.
        """
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Check if the application is currently running.

        Returns:
            bool: True if running, False otherwise.
        """
        pass


class IApplication(ABC):
    """Interface for applications.

    Defines the contract for main application objects, providing a consistent
    interface for application initialization, execution, and management.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the application name.

        Returns:
            str: The application name.
        """
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Get the application version.

        Returns:
            str: The application version.
        """
        pass

    @property
    @abstractmethod
    def author(self) -> str:
        """Get the application author.

        Returns:
            str: The application author.
        """
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the application.

        Returns:
            bool: True if initialization was successful.
        """
        pass

    @abstractmethod
    def run(self) -> int:
        """Run the application main loop.

        Returns:
            int: Exit code (0 for success, non-zero for error).
        """
        pass

    @abstractmethod
    def quit(self, exit_code: int = 0) -> None:
        """Quit the application.

        Args:
            exit_code: Exit code to return.
        """
        pass

    @abstractmethod
    def get_task_factory(self) -> ITaskFactory:
        """Get the application's task factory.

        Returns:
            ITaskFactory: The task factory instance.
        """
        pass

    @abstractmethod
    def get_lifecycle_manager(self) -> ILifecycleManager:
        """Get the application's lifecycle manager.

        Returns:
            ILifecycleManager: The lifecycle manager instance.
        """
        pass

    @abstractmethod
    def execute_task(self, task_name: str, **kwargs) -> Any:
        """Execute a task by name.

        Args:
            task_name: Name of the task to execute.
            **kwargs: Task execution parameters.

        Returns:
            Any: Task execution result.
        """
        pass

    @abstractmethod
    def register_task(self, name: str, task: IApplicationTask) -> None:
        """Register a task with the application.

        Args:
            name: Task name for registration.
            task: The task to register.
        """
        pass

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Get application configuration.

        Returns:
            Dict[str, Any]: Application configuration dictionary.
        """
        pass

    @abstractmethod
    def set_config(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key.
            value: Configuration value.
        """
        pass


__all__ = (
    'IApplicationTask',
    'ITaskFactory',
    'ILifecycleManager',
    'IApplication',
)

"""Application interface abstractions for Pyrox framework.

These interfaces define the contracts for applications, tasks, and factory
patterns without implementation dependencies, enabling clean architectural
boundaries and extensible application design.
"""
from abc import abstractmethod
from .base import (
    INameable,
    IDescribable,
    IRunnable,
    IAuthored,
    IVersioned,
)
from .gui import IWorkspace, ITaskFrame


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
    @abstractmethod
    def application(self) -> 'IApplication': ...

    @application.setter
    @abstractmethod
    def application(
        self,
        application: 'IApplication'
    ) -> None: ...

    @abstractmethod
    def get_application(self) -> 'IApplication': ...

    @abstractmethod
    def set_application(
        self,
        application: 'IApplication'
    ) -> None: ...

    @abstractmethod
    def create_task_frame(self) -> ITaskFrame | None: ...


class IApplication(
    INameable,
    IDescribable,
    IRunnable,
    IAuthored,
    IVersioned,
):
    """Interface for applications.

    Defines the contract for main application objects, providing a consistent
    interface for application initialization, execution, and management.
    """

    # ----------------------------------------------------------------------------------
    # Tasks
    # ----------------------------------------------------------------------------------

    @abstractmethod
    def get_tasks(self) -> list[IApplicationTask]: ...

    @abstractmethod
    def set_tasks(
        self,
        tasks: list[IApplicationTask]
    ) -> None: ...

    @abstractmethod
    def register_task(
        self,
        task: IApplicationTask
    ) -> None: ...

    @abstractmethod
    def unregister_task(
        self,
        task: IApplicationTask
    ) -> None: ...

    @abstractmethod
    def clear_tasks(self) -> None: ...

    @property
    @abstractmethod
    def tasks(self) -> list[IApplicationTask]: ...

    # ----------------------------------------------------------------------------------
    # Workspace
    # ----------------------------------------------------------------------------------

    @abstractmethod
    def get_workspace(self) -> IWorkspace: ...

    @abstractmethod
    def set_workspace(
        self,
        workspace: IWorkspace
    ) -> None: ...

    @property
    def workspace(self) -> IWorkspace: ...

    # ----------------------------------------------------------------------------------
    # Delegation
    # ----------------------------------------------------------------------------------

    @abstractmethod
    def on_close(self) -> None: ...

    @abstractmethod
    def except_hook(
        self,
        exc_type: type,
        exc_value: Exception,
        traceback: object
    ) -> None: ...


__all__ = (
    'IApplicationTask',
    'IApplication',
)

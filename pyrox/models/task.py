"""Task module for pyrox applications.

Tasks are used to add additional functionality to the application via the toolbar
in the main application frame or as background services.
"""
from pyrox.interfaces import IApplication, IApplicationTask
from pyrox.models import ServicesRunnableMixin
from pyrox.services.logging import log
from pyrox.models.factory import MetaFactory, FactoryTypeMeta


class ApplicationTaskFactory(MetaFactory):
    """Factory for creating Application Task instances."""

    @classmethod
    def build_tasks(
        cls,
        application: IApplication
    ) -> None:
        """Build and register all available ApplicationTask types.

        Args:
            application: The application instance to build tasks for.
        """
        tasks = cls.get_registered_types().values()
        log(cls).info(f'Building {len(tasks)} tasks for application {application.name}')
        for task in tasks:
            if issubclass(task, ApplicationTask):
                log(cls).debug(f'Registering task: {task.__name__}')
            else:
                log(cls).warning(f'Task {task.__name__} is not a subclass of ApplicationTask and will be ignored.')
            task(application=application).inject()  # Instantiate to ensure registration


class ApplicationTask(
    IApplicationTask,
    ServicesRunnableMixin,
    metaclass=FactoryTypeMeta['ApplicationTask', ApplicationTaskFactory]
):
    """Application task to add additional functionality to the application.

    Normally, these tasks are injected into the application's main menu toolbar.
    If not injected, the task is still available to run programmatically.

    Args:
        application: The parent application of this task.
    """

    supports_registering = False  # This class can't be used to match anything

    def __init__(
        self,
        application: IApplication
    ) -> None:
        super().__init__()
        self._application = application

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.supports_registering = True  # Subclasses can be used to match

    @classmethod
    def get_factory(cls):
        """Get the factory associated with this task type.

        Returns:
            ApplicationTaskFactory: The factory class for application tasks.
        """
        return ApplicationTaskFactory

    def get_application(self) -> IApplication:
        """Get the parent application of this task.

        Returns:
            TApplication: The parent application instance.
        """
        return self._application

    def set_application(
        self,
        application: IApplication
    ) -> None:
        """Set the parent application for this task.

        Args:
            application: The application instance to set.
        """
        self._application = application

    def inject(self) -> None:
        """Inject this task into the hosting application.
        """
        pass

    def uninject(self) -> None:
        """Remove this task from the hosting application.
        """
        pass


__all__ = (
    'ApplicationTask',
    'ApplicationTaskFactory',
)

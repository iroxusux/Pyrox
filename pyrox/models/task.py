"""Task module for pyrox applications.

Tasks are used to add additional functionality to the application via the toolbar in the main application frame."""
from typing import Any, Self
from pyrox.services.logging import log
from .abc import FactoryTypeMeta, MetaFactory, Runnable
from .application import Application


class ApplicationTaskFactory(MetaFactory):
    """Factory for creating Application Task instances."""

    @classmethod
    def build_tasks(
        cls,
        application: Application
    ) -> None:
        """Build and register all available ApplicationTask types."""
        tasks = cls.get_registered_types().values()
        log(cls).info(f'Building {len(tasks)} tasks for application {application.name}')
        for task in tasks:
            if issubclass(task, ApplicationTask):
                log(cls).debug(f'Registering task: {task.__name__}')
            else:
                log(cls).warning(f'Task {task.__name__} is not a subclass of ApplicationTask and will be ignored.')
            task(application=application).inject()  # Instantiate to ensure registration


class ApplicationTask(Runnable, metaclass=FactoryTypeMeta[type(Self), ApplicationTaskFactory]):
    """Application task to add additional functionality to the application.

    Normally, these tasks are injected into the application's main menu toolbar.

    Args:
        application: The parent application of this task.

    Attributes:
        application: The parent application of this task.
    """
    __slots__ = ('_application',)

    supports_registering = False  # This class can't be used to match anything

    def __init__(self, application: Application):
        super().__init__()
        if self.__class__.__name__ == 'ApplicationTask':
            raise TypeError('ApplicationTask is an abstract class and cannot be instantiated directly.')
        self._application: Application = application

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.supports_registering = True  # Subclasses can be used to match

    @classmethod
    def get_factory(cls):
        return ApplicationTaskFactory

    @property
    def application(self) -> Any:
        """The parent application of this task.

        Returns:
            Application: The parent application instance.
        """
        return self._application

    @application.setter
    def application(self, value: Any):
        """Set the parent application for this task.

        Args:
            value: The application instance to set.
        """
        self._application = value

    def inject(self) -> None:
        """Inject this task into the hosting application.

        Raises:
            NotImplementedError: This method should be overridden in a subclass.
        """
        raise NotImplementedError('This method should be overridden in a subclass.')

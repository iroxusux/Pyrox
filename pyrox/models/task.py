"""Task module for pyrox applications.

Tasks are used to add additional functionality to the application via the toolbar
in the main application frame or as background services.
"""
from typing import Callable
from pyrox.interfaces import IApplication, IApplicationTask, IGuiMenu
from pyrox.models import ServicesRunnableMixin
from pyrox.services import log, MenuRegistry
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
        self._injected = False

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

    def register_menu_command(
        self,
        menu: IGuiMenu,
        registry_id: str,
        registry_path: str,
        index: int,
        label: str,
        command: Callable | None,
        accelerator: str,
        underline: int,
        category: str | None = None,
        enabled: bool = True
    ) -> None:
        """Register a command to the application's menu bar.
        Additionally, register the command with the MenuRegistry.
        """
        menu.add_item(
            index=index,
            label=label,
            command=command,
            accelerator=accelerator,
            underline=underline
        )
        if not enabled:
            menu.disable_item(index)

        MenuRegistry.register_item(
            menu_id=registry_id,
            menu_path=registry_path,
            menu_widget=menu.menu,
            menu_index=index,
            owner=self.__class__.__name__,
            category=category
        )

    def register_submenu(
        self,
        menu: IGuiMenu,
        submenu: IGuiMenu,
        registry_id: str,
        registry_path: str,
        index: int,
        label: str,
        underline: int,
        category: str | None = None
    ) -> IGuiMenu:
        """Register a submenu to the application's menu bar.
        Additionally, register the submenu with the MenuRegistry.

        Returns:
            IGuiMenu: The created submenu instance.
        """
        menu.insert_submenu(
            label=label,
            submenu=submenu,
            index=index,
            underline=underline
        )

        MenuRegistry.register_item(
            menu_id=registry_id,
            menu_path=registry_path,
            menu_widget=submenu.menu,
            menu_index=index,
            owner=self.__class__.__name__,
            category=category
        )

        return submenu

    def inject(self) -> None:
        """Inject this task into the hosting application.
        """
        if self._injected:
            log(self).warning(f'Task {self.__class__.__name__} is already injected into application {self.application.name}.')
            return
        self.application.register_task(self)
        self._injected = True

    def uninject(self) -> None:
        """Remove this task from the hosting application.
        """
        self.application.unregister_task(self)
        self._injected = False

    __all__ = (
        'ApplicationTask',
        'ApplicationTaskFactory',

    )

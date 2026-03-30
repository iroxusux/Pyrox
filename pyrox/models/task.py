"""Task module for pyrox applications.

Tasks are used to add additional functionality to the application via the toolbar
in the main application frame or as background services.
"""
from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction
from typing import Callable
from pyrox.interfaces import IApplication, IApplicationTask
from pyrox.models import ServicesRunnableMixin
from pyrox.services import log, MenuRegistry, GuiManager
from pyrox.models.gui.frame import TaskFrame
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
        log(cls).debug(f'Building {len(tasks)} tasks for application {application.name}')
        for task in tasks:
            task(application=application)


class ApplicationTask(
    IApplicationTask,
    ServicesRunnableMixin,
    metaclass=FactoryTypeMeta[ApplicationTaskFactory]
):
    """Application task to add additional functionality to the application.
    Args:
        application: The parent application of this task.
    """

    def __init__(
        self,
        application: IApplication
    ) -> None:
        super().__init__()
        self._application = application
        self._application.register_task(self)
        self._task_frame: TaskFrame | None = None
        self._frame_destroy_callback = lambda *_, **__: self._on_frame_destroyed()

    # --------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------

    def create_task_frame(self) -> TaskFrame:
        """Create the task's frame.

        Returns:
            PyQt6TaskFrame: The created task frame instance.
        """
        raise NotImplementedError("create_task_frame method must be implemented by subclass.")

    def create_or_raise_frame(self):
        """Create the task's frame if it doesn't exist, or raise it if it does.
        """
        if not self._task_frame or not self._task_frame.root.isVisible():
            del self._task_frame
            self._task_frame = self.create_task_frame()
            assert self._task_frame is not None, "create_task_frame must return a TaskFrame instance"
            self.application.workspace.register_frame(self._task_frame)
            self._task_frame.on_destroy().append(self._frame_destroy_callback)

        self.application.workspace.raise_frame(self._task_frame)

    def register_menu_command(
        self,
        menu: QMenu,
        registry_id: str,
        registry_path: str,
        index: int,
        label: str,
        command: Callable | None = None,
        accelerator: str = '',
        underline: int = 0,
        category: str | None = None,
        subcategory: str | None = None,
        enabled: bool = True
    ) -> QAction:
        """Register a command to the application's menu bar.
        Additionally, register the command with the MenuRegistry.
        """
        action = GuiManager.insert_menu_command_with_accelerator(
            menu=menu,
            index=index,
            label=label,
            command=command,
            accelerator=accelerator,
            underline=underline,
        )

        if not enabled and action is not None:
            action.setEnabled(False)

        MenuRegistry.register_item(
            menu_id=registry_id,
            menu_path=registry_path,
            menu_widget=menu,
            menu_index=index,
            owner=self.__class__.__name__,
            action=action,
            command=command,
            category=category,
            subcategory=subcategory,
        )

        return action

    def register_submenu(
        self,
        menu: QMenu,
        submenu: QMenu,
        registry_id: str,
        registry_path: str,
        index: int,
        label: str,
        underline: int,
        category: str | None = None
    ) -> QMenu:
        """Register a submenu to the application's menu bar.
        Additionally, register the submenu with the MenuRegistry.

        Returns:
            IGuiMenu: The created submenu instance.
        """
        actions = menu.actions()
        if index < len(actions):
            menu.insertMenu(actions[index], submenu)
        else:
            menu.addMenu(submenu)
        submenu.setTitle(label)

        MenuRegistry.register_item(
            menu_id=registry_id,
            menu_path=registry_path,
            menu_widget=submenu,
            menu_index=index,
            owner=self.__class__.__name__,
            category=category
        )

        return submenu

    def get_submenu(self, registry_id: str) -> QMenu | None:
        """Get a submenu by its registry ID.

        Args:
            registry_id: The registry ID of the submenu to retrieve.

        Returns:
            IGuiMenu | None: The submenu instance if found, otherwise None.
        """
        menu_item = MenuRegistry.get_item(registry_id)
        if menu_item and isinstance(menu_item.menu_widget, QMenu):
            return menu_item.menu_widget
        return None

    # --------------------------------------------------------------
    # Getters and Setters
    # --------------------------------------------------------------

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

    # --------------------------------------------------------------
    # Private Methods
    # --------------------------------------------------------------

    def _on_frame_destroyed(self) -> None:
        """Callback for when the task frame is destroyed. Resets the task frame reference."""
        self._task_frame = None

    __all__ = (
        'ApplicationTask',
        'ApplicationTaskFactory',
    )

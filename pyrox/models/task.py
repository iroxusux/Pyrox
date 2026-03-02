"""Task module for pyrox applications.

Tasks are used to add additional functionality to the application via the toolbar
in the main application frame or as background services.
"""
import tkinter as tk
from typing import Callable
from pyrox.interfaces import IApplication, IApplicationTask
from pyrox.models import ServicesRunnableMixin
from pyrox.services import log, MenuRegistry, TkGuiManager
from pyrox.models.gui.tk.frame import TkinterTaskFrame
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
        self._task_frame: TkinterTaskFrame | None = None
        self._frame_destroy_callback = lambda *_, **__: self._on_frame_destroyed()

    # --------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------

    def create_task_frame(self) -> TkinterTaskFrame:
        """Create the task's frame.

        Returns:
            TkinterTaskFrame: The created task frame instance.
        """
        raise NotImplementedError("create_task_frame method must be implemented by subclass.")

    def create_or_raise_frame(self):
        """Create the task's frame if it doesn't exist, or raise it if it does.
        """
        if not self._task_frame or not self._task_frame.root.winfo_exists():
            self._task_frame = self.create_task_frame()
            self.application.workspace.register_frame(self._task_frame)
            self._task_frame.on_destroy().append(self._frame_destroy_callback)
        else:
            self.application.workspace.raise_frame(self._task_frame)

    def register_menu_command(
        self,
        menu: tk.Menu,
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
    ) -> None:
        """Register a command to the application's menu bar.
        Additionally, register the command with the MenuRegistry.
        """
        TkGuiManager.insert_menu_command_with_accelerator(
            menu=menu,
            index=index,
            label=label,
            command=command,
            accelerator=accelerator,
            underline=underline,
        )

        if not enabled:
            menu.entryconfig(index, state=tk.DISABLED)  # Disable the menu item if not enabled

        MenuRegistry.register_item(
            menu_id=registry_id,
            menu_path=registry_path,
            menu_widget=menu,
            menu_index=index,
            owner=self.__class__.__name__,
            command=command,
            category=category,
            subcategory=subcategory,
        )

    def register_submenu(
        self,
        menu: tk.Menu,
        submenu: tk.Menu,
        registry_id: str,
        registry_path: str,
        index: int,
        label: str,
        underline: int,
        category: str | None = None
    ) -> tk.Menu:
        """Register a submenu to the application's menu bar.
        Additionally, register the submenu with the MenuRegistry.

        Returns:
            IGuiMenu: The created submenu instance.
        """
        menu.insert_cascade(
            label=label,
            menu=submenu,
            index=index,
            underline=underline
        )

        MenuRegistry.register_item(
            menu_id=registry_id,
            menu_path=registry_path,
            menu_widget=submenu,
            menu_index=index,
            owner=self.__class__.__name__,
            category=category
        )

        return submenu

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

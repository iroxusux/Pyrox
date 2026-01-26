"""Services models for consistent access to services across the application.
"""
from logging import Logger
from typing import Any
from pyrox.interfaces import IApplicationGuiMenu, IGuiMenu
from pyrox.models import CoreRunnableMixin
from pyrox.services import EnvManager, LoggingManager, GuiManager, PlatformDirectoryService


class SupportsEnvServices:
    """Model for accessing environment related services."""

    @property
    def env(self) -> type[EnvManager]:
        """Access the EnvManager service."""
        return EnvManager


class SupportsLoggingServices:
    """Model for accessing logging related services."""

    @property
    def logging(self) -> type[LoggingManager]:
        """Access the LoggingManager service."""
        return LoggingManager

    def log(
        self,
    ) -> Logger:
        """Log a message via the LoggingManager service by accessing :class:`Logger`.
        """
        return LoggingManager.log(caller=self)


class SupportsGUIServices:
    """Model for accessing GUI related services."""

    @property
    def gui(self) -> type[GuiManager]:
        """Access the GuiManager service."""
        return GuiManager

    @property
    def main_window(self) -> Any:
        """Access the application's main window via GuiManager Service."""
        return GuiManager.unsafe_get_backend().get_root_window()

    @property
    def menu(self) -> IApplicationGuiMenu:
        """Access the application's gui menu via GuiManager Service."""
        return self.gui_menu

    @property
    def gui_menu(self) -> IApplicationGuiMenu:
        """Access the application's gui menu via GuiManager Service."""
        return GuiManager.unsafe_get_backend().get_root_application_gui_menu()

    @property
    def root_menu(self) -> Any:
        """Access the application's root menu via GuiManager Service."""
        return GuiManager.unsafe_get_backend().get_root_application_menu()

    @property
    def file_menu(self) -> IGuiMenu:
        """Access the application's file menu via GuiManager Service."""
        return self.menu.get_file_menu()

    @property
    def edit_menu(self) -> IGuiMenu:
        """Access the application's edit menu via GuiManager Service."""
        return self.menu.get_edit_menu()

    @property
    def view_menu(self) -> IGuiMenu:
        """Access the application's view menu via GuiManager Service."""
        return self.menu.get_view_menu()

    @property
    def help_menu(self) -> IGuiMenu:
        """Access the application's help menu via GuiManager Service."""
        return self.menu.get_help_menu()

    @property
    def tools_menu(self) -> IGuiMenu:
        """Access the application's tools menu via GuiManager Service."""
        return self.menu.get_tools_menu()


class SupportsPlatformDirectoryServices:
    """Model for accessing platform directory related services."""

    @property
    def directory(self) -> type[PlatformDirectoryService]:
        """Access the PlatformDirectoryService service."""
        return PlatformDirectoryService


class ServicesRunnableMixin(
    CoreRunnableMixin,
    SupportsEnvServices,
    SupportsLoggingServices,
    SupportsGUIServices,
    SupportsPlatformDirectoryServices,
):
    """Mixin class that extends :class:`CoreRunnableMixin` with access to the services layer's main managers.
    """

    def __init__(
        self,
        name: str = "",
        description: str = ""
    ):
        CoreRunnableMixin.__init__(
            self,
            name=name,
            description=description
        )


__all__ = (
    'SupportsEnvServices',
    'SupportsLoggingServices',
    'SupportsGUIServices',
    'SupportsPlatformDirectoryServices',
    'ServicesRunnableMixin',
)

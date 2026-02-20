"""Services models for consistent access to services across the application.
"""
from logging import Logger
import tkinter as tk
from pyrox.interfaces import EnvironmentKeys
from pyrox.models import CoreRunnableMixin
from pyrox.services import EnvManager, LoggingManager, TkGuiManager, PlatformDirectoryService


class SupportsEnvServices:
    """Model for accessing environment related services."""

    @property
    def env(self) -> type[EnvManager]:
        """Access the EnvManager service."""
        return EnvManager

    @property
    def env_keys(self) -> type[EnvironmentKeys]:
        """Access the EnvironmentKeys from EnvManager service."""
        return EnvironmentKeys


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
    def gui(self) -> type[TkGuiManager]:
        """Access the TkGuiManager service."""
        return TkGuiManager

    @property
    def root_window(self) -> tk.Tk:
        """Access the application's root window via TkGuiManager Service."""
        return self.gui.get_root()

    @property
    def root_menu(self) -> tk.Menu:
        """Access the application's root menu via TkGuiManager Service."""
        return self.gui.get_root_menu()

    @property
    def file_menu(self) -> tk.Menu:
        """Access the application's file menu via TkGuiManager Service."""
        return self.gui.get_file_menu()

    @property
    def edit_menu(self) -> tk.Menu:
        """Access the application's edit menu via TkGuiManager Service."""
        return self.gui.get_edit_menu()

    @property
    def view_menu(self) -> tk.Menu:
        """Access the application's view menu via TkGuiManager Service."""
        return self.gui.get_view_menu()

    @property
    def help_menu(self) -> tk.Menu:
        """Access the application's help menu via TkGuiManager Service."""
        return self.gui.get_help_menu()

    @property
    def tools_menu(self) -> tk.Menu:
        """Access the application's tools menu via TkGuiManager Service."""
        return self.gui.get_tools_menu()


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

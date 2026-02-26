"""Built-in application tasks for Pyrox.

This module provides essential built-in tasks that are commonly needed
in Pyrox applications, including File and Help menu items.
"""
import os
import tkinter as tk
from pyrox.interfaces import IApplication
from pyrox.models import ApplicationTask
from pyrox.models.gui.tk.help import show_help_window
from pyrox.models.gui.editor import TextEditorFrame
from pyrox.services import PlatformDirectoryService


__all__ = (
    'FileTask',
    'HelpTask',
    'ToolsTask',
)


class FileTask(ApplicationTask):
    """File menu task providing essential file operations."""

    def __init__(self, application: IApplication) -> None:
        super().__init__(application)

        self.file_menu.insert_separator(index=99998)  # Add separator before Exit
        self.register_menu_command(
            menu=self.file_menu,
            registry_id="exit",
            registry_path="File/Exit",
            index=99999,
            label="Exit",
            command=lambda: self.application.quit(exit_code=0),  # User requested exit
            accelerator="Ctrl+Q",
            underline=0,
            category="system",
        )


class HelpTask(ApplicationTask):
    """Help menu task providing application information and help."""

    def __init__(self, application: IApplication) -> None:
        super().__init__(application)
        self.register_menu_command(
            menu=self.help_menu,
            registry_id="about",
            registry_path="Help/About Pyrox",
            index=0,
            label="About Pyrox",
            command=lambda: show_help_window(self.gui.get_root()),  # Show about/help window
            accelerator="F1",
            underline=0,
            category="help",
        )


class ToolsTask(ApplicationTask):
    """Tools menu task for additional utilities."""

    def __init__(self, application: IApplication) -> None:
        super().__init__(application)
        self._text_editor_frame: TextEditorFrame | None = None

        self.register_menu_command(
            menu=self.tools_menu,
            registry_id="text_editor",
            registry_path="Tools/Text Editor",
            index=0,
            label="Text Editor",
            command=self._create_frame,  # Open or raise the text editor frame
            accelerator="Ctrl+T",
            underline=0,
            category="tools",
        )

    def _create_frame(self) -> None:
        """Create and register the SceneViewerFrame."""
        if not self._text_editor_frame or not self._text_editor_frame.root.winfo_exists():
            self._text_editor_frame = TextEditorFrame(self.application.workspace.workspace_area)
            self.application.workspace.register_frame(self._text_editor_frame)
        else:
            self.application.workspace.raise_frame(self._text_editor_frame)


class ViewTask(ApplicationTask):
    """View menu task for managing application views and directories."""

    def __init__(self, application: IApplication) -> None:
        super().__init__(application)

        menu = self.register_submenu(
            menu=self.view_menu,
            submenu=tk.Menu(self.view_menu, tearoff=0),
            registry_id="application_directories",
            registry_path="View/Application Directories",
            index=0,
            label="Application Directories",
            underline=0,
            category="view",
        )
        for dir_name in PlatformDirectoryService.all_directories():
            self.register_menu_command(
                menu=menu,
                registry_id=f"open_{dir_name.lower()}_directory",
                registry_path=f"View/Application Directories/Open {dir_name} Directory",
                index=0,
                label=f"Open {dir_name} Directory",
                command=lambda d=dir_name: os.startfile(PlatformDirectoryService.all_directories()[d]),
                underline=0,
                category="view",
            )

        self.register_menu_command(
            menu=self.view_menu,
            registry_id="toggle_organizer",
            registry_path="View/Toggle Organizer",
            index=1,
            label="Toggle Organizer",
            command=self.application.workspace.toggle_sidebar,
            accelerator='Ctrl+B',
            underline=0,
            category="view",
        )

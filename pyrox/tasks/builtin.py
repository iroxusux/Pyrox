"""Built-in application tasks for Pyrox.

This module provides essential built-in tasks that are commonly needed
in Pyrox applications, including File and Help menu items.
"""
from pyrox.interfaces import IApplication
from pyrox.models import ApplicationTask
from pyrox.models.gui.tk.help import show_help_window


__all__ = (
    'FileTask',
    'HelpTask',
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
            command=lambda: show_help_window(self.gui.root_window()),  # Show about/help window
            accelerator="F1",
            underline=0,
            category="help",
        )

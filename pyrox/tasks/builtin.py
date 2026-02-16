"""Built-in application tasks for Pyrox.

This module provides essential built-in tasks that are commonly needed
in Pyrox applications, including File and Help menu items.
"""
import sys
from pyrox.models import ApplicationTask
from pyrox.models.gui.tk.help import show_help_window


__all__ = (
    'FileTask',
    'HelpTask',
)


class FileTask(ApplicationTask):
    """File menu task providing essential file operations."""

    def inject(self) -> None:
        """Inject file menu items into the application."""
        self.file_menu.insert_separator(index=0)
        self.file_menu.add_item(
            index=1,
            label='Exit',
            command=lambda: sys.exit(0),
        )


class HelpTask(ApplicationTask):
    """Help menu task providing application information and help."""

    def inject(self) -> None:
        """Inject help menu items into the application."""
        self.help_menu.add_item(
            index=0,
            label='About Pyrox',
            command=self._show_about,
        )

    def _show_about(self) -> None:
        """Show the About/Help window."""
        show_help_window(self.gui.root_window().root)

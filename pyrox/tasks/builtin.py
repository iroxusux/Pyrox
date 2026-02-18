"""Built-in application tasks for Pyrox.

This module provides essential built-in tasks that are commonly needed
in Pyrox applications, including File and Help menu items.
"""
from pyrox.interfaces import IApplication
from pyrox.models import ApplicationTask
from pyrox.models.gui.tk.help import show_help_window
from pyrox.models.gui.editor import TextEditorFrame


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
            command=lambda: show_help_window(self.gui.root_window()),  # Show about/help window
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
            self._text_editor_frame = TextEditorFrame(self.gui.root_window())
            self.application.workspace.register_frame(self._text_editor_frame)
        else:
            self.application.workspace.raise_frame(self._text_editor_frame)

"""Python terminal sidebar task for Pyrox.

Registers an interactive Python console as a persistent sidebar widget,
mirroring the pattern used by ControlRox for its PLC treeview panel.
"""
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from pyrox.interfaces import IApplication
from pyrox.models import ApplicationTask
from pyrox.models.gui.terminal import PythonTerminalFrame


class PythonTerminalTask(ApplicationTask):
    """Adds an interactive Python terminal to the application sidebar.

    The terminal is registered as a non-closeable sidebar tab on startup.
    A *Tools > Python Terminal* menu entry is also provided to bring the
    sidebar tab into focus and set keyboard focus to the input line.
    """

    def __init__(self, application: IApplication) -> None:
        super().__init__(application)

        # Build the sidebar widget container
        self._container = QWidget()
        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        self._terminal = PythonTerminalFrame(parent=self._container)
        container_layout.addWidget(self._terminal)

        # Register as a sidebar widget (non-closeable, like the PLC treeview)
        self._widget_id = self.application.workspace.add_sidebar_widget(
            self._container,
            "Terminal",
            "python_terminal",
            "🐍",
            closeable=False,
        )

        # Menu entry to bring the terminal into view
        self.register_menu_command(
            menu=self.tools_menu,
            registry_id="tools.python_terminal",
            registry_path="Tools/Python Terminal",
            index=10,
            label="Python Terminal",
            command=self._focus_terminal,
            accelerator="Ctrl+`",
            underline=0,
            category="tools",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _focus_terminal(self) -> None:
        """Switch the sidebar to the terminal tab and focus the input."""
        organizer = self.application.workspace.get_sidebar_organizer()
        if organizer is None:
            return

        # add_sidebar_widget reparents our container into a wrapping QWidget
        # that is registered as the actual tab widget.
        from PyQt6.QtWidgets import QWidget
        tab_wrapper = self._container.parent()
        if isinstance(tab_wrapper, QWidget):
            organizer.setCurrentWidget(tab_wrapper)

        self._terminal.focus_input()

""" help tasks
    """
from __future__ import annotations
from logging import INFO, DEBUG, WARNING, ERROR, CRITICAL
from tkinter import BooleanVar, Menu
from pyrox.models import ApplicationTask


LOGGING_LEVELS = [(INFO, 'Info'), (DEBUG, 'Debug'), (WARNING, 'Warning'), (ERROR, 'Error'), (CRITICAL, 'Critical')]


class HelpTask(ApplicationTask):
    """built-in help task.
    """

    def __init__(self, application):
        super().__init__(application)
        self._logger_var = {}

    def inject(self) -> None:
        if not self.application.menu:
            return

        drop_down = Menu(self.application.menu.help, name='logging', tearoff=0)
        self.application.menu.help.insert_cascade(0, label='Set Logging Level', menu=drop_down)

        for level, name in LOGGING_LEVELS:
            var = BooleanVar(value=(self.application.log().level == level))
            self._logger_var[level] = var

            def set_logger_level(x=level):
                """Set the logger level for this task."""
                if self.application:
                    self.application.set_logging_level(x)
                    for lvl, v in self._logger_var.items():
                        v.set(lvl == x)

            drop_down.add_checkbutton(
                label=name,
                variable=var,
                command=set_logger_level
            )

"""built-in exit task.
    """
from __future__ import annotations


import sys


from ...types.application import ApplicationTask


class ExitTask(ApplicationTask):
    """built-in exit task.
    """

    def inject(self) -> None:
        if not self.application.menu:
            return
        self.application.menu.file.add_separator()
        self.application.menu.file.add_command(label='Exit', command=lambda: sys.exit(0))

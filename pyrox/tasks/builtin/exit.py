"""built-in menu task for applications
    """
from __future__ import annotations


import sys


from ...types.application import ApplicationTask


class ExitTask(ApplicationTask):
    """built-in exit task.
    """

    def inject(self) -> None:
        self.logger.info('Exiting...')
        self.application.menu.file.add_command(label='Exit', command=lambda: sys.exit(0))

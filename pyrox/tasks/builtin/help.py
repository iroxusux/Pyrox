"""built-in help task.
    """
from __future__ import annotations


from ...types.application import ApplicationTask


class HelpTask(ApplicationTask):
    """built-in help task.
    """

    def start(self):
        self.logger.info('starting...')

    def inject(self) -> None:
        self.application.menu.help.add_separator()
        self.application.menu.help.add_command(label='Guides', command=self.start)
        self.application.menu.help.add_separator()
        self.application.menu.help.add_command(label='About', command=self.start)

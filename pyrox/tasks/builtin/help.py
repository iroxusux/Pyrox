"""built-in help task.
    """
from __future__ import annotations


from ...models.application import ApplicationTask


class HelpTask(ApplicationTask):
    """built-in help task.
    """

    def guide(self):
        self.logger.info('guides...')

    def start(self):
        self.logger.info('starting...')

    def inject(self) -> None:
        if not self.application.menu:
            return

        self.application.menu.help.add_separator()
        self.application.menu.help.add_command(label='Guides', command=self.guide)
        self.application.menu.help.add_separator()
        self.application.menu.help.add_command(label='About', command=self.start)

"""built-in preferences task.
    """
from __future__ import annotations


from pyrox.models.application import ApplicationTask


class PreferencesTask(ApplicationTask):
    """built-in preferences task.
    """

    def start(self):
        self.logger.info('running...')
        # add more logic

    def inject(self) -> None:
        if not self.application.menu:
            return

        self.application.menu.edit.add_separator()
        self.application.menu.edit.add_command(label='Preferences', command=self.start)

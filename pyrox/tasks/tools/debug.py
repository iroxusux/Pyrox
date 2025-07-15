"""Debug task.
    """
from __future__ import annotations


from pyrox.applications.app import App, AppTask


class ControllerGenerateTask(AppTask):
    """Controller generation task for the PLC Application.
    """

    def __init__(self,
                 application: App):
        super().__init__(application=application)

    def debug(self, *_, **__) -> None:
        """Debug method."""
        raise ValueError("This is a test")

    def inject(self) -> None:
        self.application.menu.tools.insert_command(0, label='Trigger Debug Event', command=self.debug)

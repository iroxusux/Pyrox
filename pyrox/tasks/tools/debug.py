"""Debug task.
    """
from __future__ import annotations


from pyrox import applications
from pyrox.services import debug

import importlib


class ControllerGenerateTask(applications.AppTask):
    """Controller generation task for the PLC Application.
    """

    def __init__(self,
                 application: applications.App):
        super().__init__(application=application)

    def debug(self, *_, **__) -> None:
        """Debug method."""
        importlib.reload(debug)
        debug.debug()

    def inject(self) -> None:
        self.application.menu.tools.insert_command(0, label='Trigger Debug Event', command=self.debug)

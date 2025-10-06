"""PLC Inspection Application
    """
from pyrox.applications import AppTask


class PlcIoTask(AppTask):
    """Controller verification task for the PLC verification Application.
    """

    def inject(self) -> None:
        self.application.menu.tools.add_command(label='PLC I/O', command=self.start)

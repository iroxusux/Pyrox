"""PLC Inspection Application
    """
import importlib
from pyrox.applications import AppTask
from pyrox.applications import plcio


class PlcIoTask(AppTask):
    """Controller verification task for the PLC verification Application.
    """

    def run(self) -> None:
        mgr = getattr(self, 'manager', None)
        if mgr:
            del self.manager
        importlib.reload(plcio)
        self.manager = plcio.PlcIoApplicationManager(self.application)

    def inject(self) -> None:
        self.application.menu.tools.add_command(label='PLC I/O', command=self.run)

"""PLC Eplan Import Task
    """
import importlib
from pyrox.applications.app import AppTask
from pyrox.services import eplan


class EPlanImportTask(AppTask):
    """Controller Eplan Import task for the PLC Application.
    """

    def _import(self):
        importlib.reload(eplan)
        eplan.import_eplan(self.application.controller)

    def inject(self) -> None:
        self.application.menu.tools.add_command(label='EPlan Import', command=self._import)

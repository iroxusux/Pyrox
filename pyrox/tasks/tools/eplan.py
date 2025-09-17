"""PLC Inspection Application
    """
from __future__ import annotations
import importlib

from pyrox.applications.app import App, AppTask
from pyrox.services import get_open_file
from pyrox.services import eplan

BASE_PLC_FILE = r'docs\controls\root.L5X'
GM_CONFIG_FILE = r'docs\_gm_controller.json'


class EPlanImportTask(AppTask):
    """Controller generation task for the PLC Application.
    """

    def __init__(self,
                 application: App):
        super().__init__(application=application)

    def import_eplan(self):
        self.logger.info('Importing EPlan...')
        epj_file = get_open_file(
            title='Select EPlan Project',
            filetypes=[('.epj Files', '*.epj'), ('All Files', '*.*')],
        )
        if not epj_file:
            self.logger.warning('No file selected for EPlan import.')
            return

        self.logger.info('Selected EPlan file: %s', epj_file)
        importlib.reload(eplan)  # Ensure the latest version is used
        results = eplan.parse_epj_to_dict(epj_file)
        if not results:
            self.logger.error('Failed to parse EPlan file.')
            return

        self.logger.info('EPlan import completed.')

    def inject(self) -> None:
        self.application.menu.tools.add_command(label='EPlan Import', command=self.import_eplan)

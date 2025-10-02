"""PLC Inspection Application
    """
import importlib
from tkinter import Menu
from pyrox.applications import AppTask
from pyrox.services import emu


class ControllerGenerateTask(AppTask):
    """Controller generation task for the PLC Application.
    """

    def _gen_checklist(self):
        if not self.controller:
            self.log().warning('No controller loaded, cannot create emulation checklist!')
            return
        importlib.reload(emu)
        emu.create_checklist_from_template(self.controller)

    def _inject(self):
        if not self.controller:
            self.log().warning('No controller loaded, cannot inject emulation routine!')
            return
        importlib.reload(emu)
        emu.inject_emulation_routine(self.controller)

    def _remove(self):
        if not self.controller:
            self.log().warning('No controller loaded, cannot remove emulation routine!')
            return
        importlib.reload(emu)
        emu.remove_emulation_routine(self.controller)

    def inject(self) -> None:
        drop_down = Menu(self.application.menu.tools, name='logic_generation', tearoff=0)
        self.application.menu.tools.insert_cascade(0, label='Logic Generation', menu=drop_down)
        drop_down.add_command(label='Inject Emulation Routine', command=self._inject)
        drop_down.add_command(label='Remove Emulation Routine', command=self._remove)
        drop_down.add_separator()
        drop_down.add_command(label='Generate Checklist', command=self._gen_checklist)

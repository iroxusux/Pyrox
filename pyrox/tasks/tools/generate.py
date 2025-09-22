"""PLC Inspection Application
    """
import importlib
from pyrox.applications import AppTask
from pyrox.services import emu
from tkinter import Menu


class ControllerGenerateTask(AppTask):
    """Controller generation task for the PLC Application.
    """

    def generate_gm(self):
        raise NotImplementedError('GM controller generation not implemented yet.')

    def generate_ford(self):
        raise NotImplementedError('Ford controller generation not implemented yet.')

    def generate_stellantis(self):
        raise NotImplementedError('Stellantis controller generation not implemented yet.')

    def _inject(self):
        importlib.reload(emu)
        emu.inject_emulation_routine(self.application.controller)

    def _remove(self):
        importlib.reload(emu)
        emu.remove_emulation_routine(self.application.controller)

    def inject(self) -> None:
        drop_down = Menu(self.application.menu.tools, name='generate_tasks', tearoff=0)
        self.application.menu.tools.insert_cascade(0, label='Generate Tasks', menu=drop_down)

        drop_down.add_command(label='Generate GM Controller', command=self.generate_gm)

        drop_down.add_command(label='Ford (WIP)', command=self.generate_ford)
        drop_down.add_command(label='Stellantis (WIP)', command=self.generate_stellantis)

        emu_drop_down = Menu(drop_down, name='emu_tasks', tearoff=0)
        drop_down.add_cascade(label='Emulation Tasks', menu=emu_drop_down)

        emu_drop_down.add_command(label='Inject Emulation Routine', command=self._inject)
        emu_drop_down.add_command(label='Remove Emulation Routine', command=self._remove)

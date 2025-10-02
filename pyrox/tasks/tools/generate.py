"""PLC Inspection Application
    """
import importlib
from pyrox.applications import AppTask
from pyrox.services import checklist, emu, env
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

    def _gen_checklist(self):
        importlib.reload(checklist)
        importlib.reload(env)

        if not self.controller:
            self.log().warning('No controller loaded, cannot generate any checklists!')
            return

        checklist_template_path = env.get_env('CHECKLIST_TEMPLATE_FILE')
        if not checklist_template_path:
            self.log().error('No checklist path found in .env file. Please refer to symbol -> CHECKLIST_TEMPLATE_FILE')
            return

        self.log().info(f'Generating checklist for controller {self.controller.name}')
        controls_checklist = checklist.compile_checklist_from_md_file(checklist_template_path)
        if controls_checklist is None:
            self.log().error('Error generating checklist... Cannot continue.')

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

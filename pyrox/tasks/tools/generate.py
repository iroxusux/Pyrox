"""PLC Inspection Application
    """
import importlib
from tkinter import Menu
from pyrox.applications import AppTask
from pyrox.models.eplan.project import EplanProject
from pyrox.services import checklist, eplan, emu, env


class ControllerGenerateTask(AppTask):
    """Controller generation task for the PLC Application.
    """

    def _get_controls_template(self) -> dict:
        importlib.reload(checklist)

        template_path = env.get_env('CHECKLIST_TEMPLATE_FILE')
        if not template_path:
            raise ValueError('No controls template file path set in environment variable CHECKLIST_TEMPLATE_FILE')

        self.log().info(f'Loading controls template from {template_path}')
        controls_template = checklist.compile_checklist_from_md_file(template_path)
        if controls_template is None:
            raise ValueError(f'Could not load controls template from {template_path}')
        return controls_template

    def _get_eplan_project(self) -> EplanProject:
        if not self.controller:
            raise ValueError('No controller loaded, cannot get EPlan project!')
        return eplan.get_project(self.controller, '')

    def _gen_checklist(self):
        if not self.controller:
            self.log().warning('No controller loaded, cannot generate any checklists!')
            return

        checklist_template = self._get_controls_template()
        if checklist_template is None:
            return
        eplan_project = self._get_eplan_project()
        if eplan_project is None:
            return

        self.log().info(f'Generating checklist for controller {self.controller.name}')

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

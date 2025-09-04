"""PLC Inspection Application
    """
from __future__ import annotations

from pyrox.applications.app import App, AppTask
from pyrox.models.plc import Controller
from pyrox.models.plc.emu import BaseEmulationGenerator
import json
from tkinter import Menu
from typing import Union

BASE_PLC_FILE = r'docs\controls\root.L5X'
GM_CONFIG_FILE = r'docs\_gm_controller.json'


class ControllerGenerateTask(AppTask):
    """Controller generation task for the PLC Application.
    """

    def __init__(self,
                 application: App):
        super().__init__(application=application)

    def _generate_precheck(self) -> Union[Controller, None]:
        controller = self.application.controller

        if not controller:
            self.logger.error('No controller set in the application.')
            return None

        return controller

    @staticmethod
    def _get_generator(controller: Controller) -> BaseEmulationGenerator:
        generator: BaseEmulationGenerator = BaseEmulationGenerator.get_generator(controller)
        if not isinstance(generator, BaseEmulationGenerator):
            raise ValueError('No valid generator found for this controller type!')
        return generator

    def generate_gm(self):
        self.logger.info('Generating GM controller...')
        with open(GM_CONFIG_FILE, 'r') as file:
            attr_dict = json.load(file)
        if attr_dict is None:
            raise ValueError('GM controller attributes not found in JSON file.')
        self.logger.info('Generating new PLC...')
        controller = Controller()

        self.logger.info('Creating GM controller with attributes: %s', attr_dict)
        for attr in attr_dict['ControllerAttributes']:
            controller[attr] = attr_dict['ControllerAttributes'][attr]
            self.logger.info('Controller %s set to %s', attr, attr_dict['ControllerAttributes'][attr])

        self.logger.info('Assigning generated controller to application...')
        self.application.controller = controller

    def inject_emulation_routine(self):
        """Injects emulation routine into the current controller.
        """
        controller = self._generate_precheck()
        generator = self._get_generator(controller)
        if not controller or not generator:
            self.logger.error('Emulation routine injection failed due to precheck failure.')
            return
        self.logger.info(f'Injecting emulation routine using {generator.__class__.__name__}...')
        generator.generate_emulation_logic()

    def remove_emulation_routine(self):
        """Removes emulation routine from the current controller.
        """
        controller = self._generate_precheck()
        generator = self._get_generator(controller)
        if not controller or not generator:
            self.logger.error('Emulation routine removal failed due to precheck failure.')
            return
        self.logger.info(f'Removing emulation routine using {generator.__class__.__name__}...')
        generator.remove_emulation_logic()

    def generate_ford(self):
        self.logger.info('Generating Ford controller...')
        raise NotImplementedError('Ford controller generation not implemented yet.')

    def generate_stellantis(self):
        self.logger.info('Generating Stellantis controller...')
        raise NotImplementedError('Stellantis controller generation not implemented yet.')

    def inject(self) -> None:
        drop_down = Menu(self.application.menu.tools, name='generate_tasks', tearoff=0)
        self.application.menu.tools.insert_cascade(0, label='Generate Tasks', menu=drop_down)

        drop_down.add_command(label='Generate GM Controller', command=self.generate_gm)

        drop_down.add_command(label='Ford (WIP)', command=self.generate_ford)
        drop_down.add_command(label='Stellantis (WIP)', command=self.generate_stellantis)

        emu_drop_down = Menu(drop_down, name='emu_tasks', tearoff=0)
        drop_down.add_cascade(label='Emulation Tasks', menu=emu_drop_down)

        emu_drop_down.add_command(label='Inject Emulation Routine', command=self.inject_emulation_routine)
        emu_drop_down.add_command(label='Remove Emulation Routine', command=self.remove_emulation_routine)

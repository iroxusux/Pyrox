"""PLC Inspection Application
    """
from __future__ import annotations


from pyrox.applications.app import App, AppTask
from pyrox.models.plc import Controller


import json
from tkinter import Menu

BASE_PLC_FILE = r'docs\controls\root.L5X'
GM_CONFIG_FILE = r'docs\_gm_controller.json'


class ControllerGenerateTask(AppTask):
    """Controller generation task for the PLC Application.
    """

    def __init__(self,
                 application: App):
        super().__init__(application=application)

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
        

    def generate_ford(self):
        self.logger.info('Generating Ford controller...')
        raise NotImplementedError('Ford controller generation not implemented yet.')

    def generate_stellantis(self):
        self.logger.info('Generating Stellantis controller...')
        raise NotImplementedError('Stellantis controller generation not implemented yet.')

    def inject(self) -> None:
        drop_down = Menu(self.application.menu.tools, name='controller_generation', tearoff=0)
        self.application.menu.tools.add_cascade(menu=drop_down, label='Controller Generation')
        drop_down.add_command(label='GM', command=self.generate_gm)
        drop_down.add_command(label='Ford', command=self.generate_ford)
        drop_down.add_command(label='Stellantis', command=self.generate_stellantis)

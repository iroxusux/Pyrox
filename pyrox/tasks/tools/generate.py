"""PLC Inspection Application
    """
from __future__ import annotations


from pyrox.applications.app import App, AppTask
from pyrox.models.plc import Controller, Program, Routine
from pyrox.applications.general_motors.gm import GmController


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

    def generate_gm_emulation_routine(self):
        if not self.application.controller:
            self.logger.error('No controller set in the application.')
            return
        if not isinstance(self.application.controller, GmController):
            self.logger.error('Controller is not a GM controller. Cannot generate emulation routine.')
            return
        self.application.controller.generate_emulation_logic()

    def remove_gm_emulation_routine(self):
        self.logger.info('Removing GM emulation routine...')

        if not self.application.controller:
            self.logger.error('No controller set in the application.')
            return

        mcp_program: Program = self.application.controller.programs.get('MCP', None)
        if not mcp_program:
            self.logger.error('MCP program not found in the controller.')
            return

        emulation_routine: Routine = mcp_program.routines.get('aaa_Emulation', None)
        if not emulation_routine:
            self.logger.warning('Emulation routine does not exist, skipping removal.')
            return

        emulation_jsr = next((x for x in mcp_program.main_routine.rungs if f'JSR({emulation_routine.name},0)' in x.text), None)
        if emulation_jsr:
            self.logger.info('Removing JSR rung from main routine...')
            mcp_program.main_routine.remove_rung(emulation_jsr.number)

        mcp_program.remove_routine(emulation_routine)
        inhibit_tag = mcp_program.tags.get('Inhibit', None)
        uninhibit_tag = mcp_program.tags.get('Uninhibit', None)
        toggle_inhibit_tag = mcp_program.tags.get('toggle_inhibit', None)
        local_mode_tag = mcp_program.tags.get('LocalMode', None)
        device_data_size_tag = mcp_program.tags.get('DeviceDataSize', None)
        sus_loop_ptr_tag = mcp_program.tags.get('SusLoopPtr', None)
        if inhibit_tag:
            mcp_program.remove_tag(inhibit_tag.name)
        if uninhibit_tag:
            mcp_program.remove_tag(uninhibit_tag.name)
        if toggle_inhibit_tag:
            mcp_program.remove_tag(toggle_inhibit_tag.name)
        if local_mode_tag:
            mcp_program.remove_tag(local_mode_tag.name)
        if device_data_size_tag:
            mcp_program.remove_tag(device_data_size_tag.name)
        if sus_loop_ptr_tag:
            mcp_program.remove_tag(sus_loop_ptr_tag.name)
        self.application.refresh()

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

        emu_drop_down.add_command(label='Create GM Emulation Routine', command=self.generate_gm_emulation_routine)
        emu_drop_down.add_command(label='Remove GM Emulation Routine', command=self.remove_gm_emulation_routine)

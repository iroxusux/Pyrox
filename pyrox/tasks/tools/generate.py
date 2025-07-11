"""PLC Inspection Application
    """
from __future__ import annotations


from pyrox.applications.app import App, AppTask
from pyrox.models.plc import Controller, Program, Routine, Rung, Tag


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
        self.logger.info('Generating GM emulation routine...')

        if not self.application.controller:
            self.logger.error('No controller set in the application.')
            return

        mcp_program: Program = self.application.controller.programs.get('MCP', None)
        if not mcp_program:
            self.logger.error('MCP program not found in the controller.')
            return

        main_routine: Routine = mcp_program.routines.get(mcp_program.main_routine_name, None)
        if not main_routine:
            self.logger.error('Main routine %s not found in MCP program.', mcp_program.main_routine_name)
            return

        emulation_routine: Routine = mcp_program.routines.get('aaa_Emulation', None)
        jsr_rung: Rung = next((x for x in main_routine.rungs if 'JSR(aaa_Emulation,0)' in x.text), None)

        if not jsr_rung or not emulation_routine:
            self.logger.info('creating...')
        elif jsr_rung and emulation_routine:
            self.logger.warning('Emulation routine already exists, skipping generation.')

        emulation_routine = Routine(controller=self.application.controller)
        emulation_routine.name = 'aaa_Emulation'
        emulation_routine.description = 'Emulation routine for GM controller'

        rung_0 = Rung(controller=self.application.controller)
        rung_0.text = 'MOV(0,Uninhibit)MOV(4,Inhibit);'
        emulation_routine.add_rung(rung_0)

        rung_1 = Rung(controller=self.application.controller)
        rung_1.text = '[XIO(toggle_inhibit)MOV(Uninhibit,LocalMode),XIC(toggle_inhibit)MOV(Inhibit,LocalMode)]SIZE(EnetStorage.DeviceData,0,DeviceDataSize)SUB(DeviceDataSize,1,DeviceDataSize)CLR(SusLoopPtr);'  # noqa: E501
        emulation_routine.add_rung(rung_1)

        rung_2 = Rung(controller=self.application.controller)
        rung_2.text = 'LBL(SusLoop)XIC(toggle_inhibit)LES(SusLoopPtr,DeviceDataSize)ADD(SusLoopPtr,1,SusLoopPtr)OTU(EnetStorage.DeviceData[SusLoopPtr].Connected)OTL(EnetStorage.DeviceData[SusLoopPtr].LinkStatusAvail)OTL(EnetStorage.DeviceData[SusLoopPtr].Link.Scanned)JMP(SusLoop);'  # noqa: E501
        emulation_routine.add_rung(rung_2)

        for x in self.application.controller.modules:
            rung_x = Rung(controller=self.application.controller)
            rung_x.text = f'SSV(Module,{x.name},Mode,LocalMode);'
            emulation_routine.add_rung(rung_x)

        uninhibit_tag = Tag(controller=self.application.controller)
        uninhibit_tag.name = 'Uninhibit'
        uninhibit_tag.tag_type = 'Base'
        uninhibit_tag.datatype = 'INT'
        uninhibit_tag.constant = False
        uninhibit_tag.external_access = 'Read/Write'

        inhibit_tag = Tag(controller=self.application.controller)
        inhibit_tag.name = 'Inhibit'
        inhibit_tag.tag_type = 'Base'
        inhibit_tag.datatype = 'INT'
        inhibit_tag.constant = False
        inhibit_tag.external_access = 'Read/Write'

        toggle_inhibit_tag = Tag(controller=self.application.controller)
        toggle_inhibit_tag.name = 'toggle_inhibit'
        toggle_inhibit_tag.tag_type = 'Base'
        toggle_inhibit_tag.datatype = 'BOOL'
        toggle_inhibit_tag.constant = False
        toggle_inhibit_tag.external_access = 'Read/Write'

        local_mode_tag = Tag(controller=self.application.controller)
        local_mode_tag.name = 'LocalMode'
        local_mode_tag.tag_type = 'Base'
        local_mode_tag.datatype = 'INT'
        local_mode_tag.constant = False
        local_mode_tag.external_access = 'Read/Write'

        device_data_size_tag = Tag(controller=self.application.controller)
        device_data_size_tag.name = 'DeviceDataSize'
        device_data_size_tag.tag_type = 'Base'
        device_data_size_tag.datatype = 'DINT'
        device_data_size_tag.constant = False
        device_data_size_tag.external_access = 'Read/Write'

        sus_loop_ptr_tag = Tag(controller=self.application.controller)
        sus_loop_ptr_tag.name = 'SusLoopPtr'
        sus_loop_ptr_tag.tag_type = 'Base'
        sus_loop_ptr_tag.datatype = 'DINT'
        sus_loop_ptr_tag.constant = False
        sus_loop_ptr_tag.external_access = 'Read/Write'

        mcp_program.add_routine(emulation_routine)
        mcp_program.add_tag(uninhibit_tag)
        mcp_program.add_tag(inhibit_tag)
        mcp_program.add_tag(toggle_inhibit_tag)
        mcp_program.add_tag(local_mode_tag)
        mcp_program.add_tag(device_data_size_tag)
        mcp_program.add_tag(sus_loop_ptr_tag)

        if not jsr_rung:
            main_routine = mcp_program.routines.get(mcp_program.main_routine_name, None)
            if not main_routine:
                self.logger.error('Main routine %s not found in MCP program.', mcp_program.main_routine_name)
            else:
                jsr_rung = Rung(controller=self.application.controller)
                jsr_rung.text = f'JSR({emulation_routine.name},0);'
                main_routine.add_rung(jsr_rung)

        self.application.refresh()

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
        drop_down = Menu(self.application.menu.file, name='new_from_template', tearoff=0)
        file_new_item = self.application.menu.file.index('New Controller')  # Get the index of the 'New Controller' item
        self.application.menu.file.insert_cascade(file_new_item+1, label='New From Template', menu=drop_down)

        drop_down.add_command(label='GM', command=self.generate_gm)
        drop_down.add_command(label='GM Emulation Routine', command=self.generate_gm_emulation_routine)
        drop_down.add_command(label='Remove GM Emulation Routine', command=self.remove_gm_emulation_routine)
        drop_down.add_command(label='Ford', command=self.generate_ford)
        drop_down.add_command(label='Stellantis', command=self.generate_stellantis)

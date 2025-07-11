"""PLC Inspection Application
    """
from __future__ import annotations


from pyrox.applications.app import App, AppTask
from pyrox.models.plc import Controller, Datatype, Program, Routine, Rung, Tag
from pyrox.services.plc_services import l5x_dict_from_file


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
            return

        ctrl_name = self.application.controller.name

        siemens_drive_modules = [x for x in self.application.controller.modules if
                                 x.catalog_number == 'ETHERNET-MODULE'
                                 and x.communications['Connections']['Connection']['@InputCxnPoint'] == '101'
                                 and x.communications['Connections']['Connection']['@OutputCxnPoint'] == '102'
                                 and x.communications['Connections']['Connection']['@InputSize'] == '26'
                                 and x.communications['Connections']['Connection']['@OutputSize'] == '4']

        if len(siemens_drive_modules) != 0:
            self.logger.info('Found %d Siemens drive modules...', len(siemens_drive_modules))
            if 'Demo3D_G115D_Drive' not in self.application.controller.datatypes:
                self.logger.info('Siemens drive datatype not found in controller, importing from L5X file...')
                dt_dict = l5x_dict_from_file(r'docs\controls\emu\Demo3D_G115D_Drive_DataType.L5X')
                if not dt_dict:
                    self.logger.error('Failed to load Siemens drive datatype from L5X file.')
                    return
                for dt in dt_dict['RSLogix5000Content']['Controller']['DataTypes']['DataType']:
                    datatype = Datatype(controller=self.application.controller,
                                        meta_data=dt)
                    self.application.controller.add_datatype(datatype, skip_compile=True)
                    self.logger.info('Siemens drive datatype %s imported successfully.', datatype.name)
            self.application.controller.compile()
            if f'zz_Demo3D_{ctrl_name}_Siemens_Drives' not in self.application.controller.tags:
                self.logger.info('Creating tag zz_Demo3D_%s_Siemens_Drives...', ctrl_name)
                siemens_drives_tag = Tag(controller=self.application.controller)
                siemens_drives_tag.name = f'zz_Demo3D_{ctrl_name}_Siemens_Drives'
                siemens_drives_tag.tag_type = 'Base'
                siemens_drives_tag.datatype = 'Demo3D_G115D_Drive'
                siemens_drives_tag.dimensions = '150'
                siemens_drives_tag.constant = False
                siemens_drives_tag.external_access = 'Read/Write'
                self.application.controller.add_tag(siemens_drives_tag)
                self.logger.info('Tag zz_Demo3D_%s_Siemens_Drives created successfully.', ctrl_name)

        safety_blocks = [x for x in self.application.controller.modules if
                         '1732ES-IB' in x.catalog_number]

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

        for index, module in enumerate(siemens_drive_modules):
            rung_x = Rung(controller=self.application.controller)
            rung_x.text = f'[CPS(zz_Demo3D_{ctrl_name}_Siemens_Drives[{index}].Inputs.StatusWord1,{module.name}:I.Data[0],1)CPS(zz_Demo3D_{ctrl_name}_Siemens_Drives[{index}].Inputs.RPMRef,{module.name}:I.Data[1],1)CPS(zz_Demo3D_{ctrl_name}_Siemens_Drives[{index}].Inputs.AmpsRef,{module.name}:I.Data[2],1),CPS(zz_Demo3D_{ctrl_name}_Siemens_Drives[{index}].Inputs.TorqueRef,{module.name}:I.Data[3],1)CPS(zz_Demo3D_{ctrl_name}_Siemens_Drives[{index}].Inputs.AlarmCode,{module.name}:I.Data[4],1)CPS(zz_Demo3D_{ctrl_name}_Siemens_Drives[{index}].Inputs.FaultCode,{module.name}:I.Data[5],1),CPS(zz_Demo3D_{ctrl_name}_Siemens_Drives[{index}].Inputs.StatusWord4,{module.name}:I.Data[6],1)CPS(zz_Demo3D_{ctrl_name}_Siemens_Drives[{index}].Inputs.SpareInt1,{module.name}:I.Data[7],1)CPS(zz_Demo3D_{ctrl_name}_Siemens_Drives[{index}].Inputs.PowerUnitTempC,{module.name}:I.Data[8],1),CPS(zz_Demo3D_{ctrl_name}_Siemens_Drives[{index}].Inputs.StatusWord5,{module.name}:I.Data[9],1)CPS(zz_Demo3D_{ctrl_name}_Siemens_Drives[{index}].Inputs.MotorTempC,{module.name}:I.Data[10],1)CPS(zz_Demo3D_{ctrl_name}_Siemens_Drives[{index}].Inputs.SafetySTO_Out,{module.name}:I.Data[11],1),CPS(zz_Demo3D_{ctrl_name}_Siemens_Drives[{index}].Inputs.SafetySTOSts,{module.name}:I.Data[12],1),CPS({module.name}:O.Data[0],zz_Demo3D_{ctrl_name}_Siemens_Drives[{index}].Outputs.ControlWord1,1)CPS({module.name}:O.Data[1],zz_Demo3D_{ctrl_name}_Siemens_Drives[{index}].Outputs.Setpoint,1)];'  # noqa: E501
            emulation_routine.add_rung(rung_x)

        any_tags_added = False
        for index, module in enumerate(safety_blocks):
            rung_x = Rung(controller=self.application.controller)
            rung_x.text = f'COP({module.name}:O,zz_Demo3D_{module.name}_O,1);'
            emulation_routine.add_rung(rung_x)
            if f'zz_Demo3D_{module.name}_O' not in self.application.controller.tags:
                self.logger.info('Creating tag zz_Demo3D_%s_O...', module.name)
                safety_tag = Tag(controller=self.application.controller)
                safety_tag.name = f'zz_Demo3D_{module.name}_O'
                safety_tag.tag_type = 'Base'
                safety_tag.datatype = 'DINT'
                safety_tag.constant = False
                safety_tag.external_access = 'Read/Write'
                self.application.controller.add_tag(safety_tag, skip_compile=True)
                self.logger.info('Tag zz_Demo3D_%s_O created successfully.', module.name)
                any_tags_added = True
        if any_tags_added:
            self.application.controller.compile()

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
        drop_down = Menu(self.application.menu.tools, name='generate_tasks', tearoff=0)
        self.application.menu.tools.insert_cascade(0, label='Generate Tasks', menu=drop_down)

        drop_down.add_command(label='Generate GM Controller', command=self.generate_gm)
        drop_down.add_command(label='Create GM Emulation Routine', command=self.generate_gm_emulation_routine)
        drop_down.add_command(label='Remove GM Emulation Routine', command=self.remove_gm_emulation_routine)
        drop_down.add_command(label='Ford (WIP)', command=self.generate_ford)
        drop_down.add_command(label='Stellantis (WIP)', command=self.generate_stellantis)

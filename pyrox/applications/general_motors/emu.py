""""General Motors specific emulation logic generator."""
from . import gm
from pyrox.models import plc


class GmEmulationGenerator(plc.BaseEmulationGenerator):
    """General Motors specific emulation logic generator."""

    generator_type = "GmController"

    @property
    def controller(self) -> gm.GmController:
        return self.generator_object

    @controller.setter
    def controller(self, value: gm.GmController):
        if value.__class__.__name__ != self.generator_type:
            raise TypeError(f'Controller must be of type {self.generator_type}, got {value.__class__.__name__} instead.')
        self._generator_object = value

    @property
    def custom_tags(self) -> list[tuple[str, str, str]]:
        """List of custom tags specific to the controller type.

        Returns:
            list[str]: List of tuples (tag_name, datatype, description, dimensions).
        """
        return [
            ('DeviceDataSize', 'DINT', 'Size of the DeviceData array.', None),
            ('DeviceData', 'EnetDeviceDataType', 'Array of ethernet device data.', '150'),
            ('LoopPtr', 'DINT', 'Pointer for looping through devices.', None),
        ]

    @property
    def target_safety_program_name(self) -> str:
        return self.controller.safety_common_program.name

    @property
    def target_standard_program_name(self) -> str:
        return self.controller.mcp_program.name

    def _generate_custom_standard_rungs(self):
        rung = self.generator_object.config.rung_type(
            controller=self.controller,
            text='XIC(Flash.Norm)OTE(Flash.Fast);',
            comment='// Reduce fast flash rate to limit communication issues with the 3d model.'
        )
        self._add_rung_to_standard_routine(rung)

        rung = self.generator_object.config.rung_type(
            controller=self.controller,
            text='SIZE(EnetStorage.DeviceData,0,DeviceDataSize)SUB(DeviceDataSize,1,DeviceDataSize)CLR(LoopPtr);',
            comment='// Prepare device data sizes for communications processing.'
        )
        self._add_rung_to_standard_routine(rung)

        rung = self.generator_object.config.rung_type(
            controller=self.controller,
            text='LBL(Loop)XIC(ToggleInhibit)LES(LoopPtr,DeviceDataSize)ADD(LoopPtr,1,LoopPtr)OTU(EnetStorage.DeviceData[LoopPtr].Connected)OTL(EnetStorage.DeviceData[LoopPtr].LinkStatusAvail)OTL(EnetStorage.DeviceData[LoopPtr].Link.Scanned)JMP(Loop);',  # noqa: E501
            comment='Loop through the devices to force the GM Network model to accept all ethernet connections as "OK".'
        )
        self._add_rung_to_standard_routine(rung)

    def _generate_g115_drive_emulation(self) -> None:
        """Generate Siemens G115 drive emulation logic."""
        g115_drives = self.get_modules_by_type('G115Drive')
        if not g115_drives:
            return

        self.schema.add_import_from_file(
            file_location=r'docs\controls\emu\Demo3D_G115D_Drive_DataType.L5X',
            asset_types=['DataTypes']
        )

        cname = self.controller.process_name
        self.add_controller_tag(
            tag_name=f'zz_Demo3D_{cname}_Siemens_Drives',
            datatype='Demo3D_G115D_Drive',
            tag_type='Base',
            dimensions='150',
            constant=False,
            external_access='Read/Write',
            description='Emulation tag for Siemens G115 drives.'
        )

        for index, drive in enumerate(g115_drives):
            rung = self.generator_object.config.rung_type(
                controller=self.controller,
                text=drive.introspective_module.get_standard_emulation_rung_text(index=index),
                comment='Move the hardware drive data to the emulation populated data.'
            )
            self._add_rung_to_standard_routine(rung)

    def _generate_hmi_card_emulation(self) -> None:
        """Generate HMI card emulation logic."""
        hmi_cards = self.get_modules_by_description_pattern('<@TYPE 502xSlot1>')
        hmi_cards = [x for x in hmi_cards if x.type_ == 'AB_1734IB8S']

        if not hmi_cards:
            return

        self.schema.add_import_from_file(
            file_location=r'docs\controls\emu\Demo3D_HMI_IN_DataType.L5X',
            asset_types=['DataTypes']
        )
        self.schema.add_import_from_file(
            file_location=r'docs\controls\emu\Demo3D_HMI_OUT_DataType.L5X',
            asset_types=['DataTypes']
        )
        self.schema.add_import_from_file(
            file_location=r'docs\controls\emu\Demo3D_CommOK_HMI_DataType.L5X',
            asset_types=['DataTypes']
        )

        # Generate generic comm word
        self.add_controller_tag(
            tag_name=f'zz_Demo3D_Comm_{self.controller.process_name}HMI',
            tag_type='Base',
            datatype='Demo3D_CommOK_HMI',
        )

        for card in hmi_cards:
            std_tag = self.add_controller_tag(
                tag_name=f'zz_Demo3D_{card.parent_module}_I',
                class_='Standard',
                datatype='Demo3D_HMI_IN',
            )

            sfty_tag = self.add_controller_tag(
                tag_name=f'sz_Demo3D_{card.parent_module}_I',
                class_='Safety',
                datatype='Demo3D_HMI_IN',
            )

            self.add_controller_tag(
                tag_name=f'zz_Demo3D_{card.parent_module}_O',
                class_='Standard',
                datatype='Demo3D_HMI_OUT',
            )

            self.schema.add_safety_tag_mapping(
                std_tag.name,
                sfty_tag.name,
            )

            rung = self.generator_object.config.rung_type(
                controller=self.controller,
                text=f'CLR({card.parent_module}:2:I.Fault)MOV(sz_Demo3D_{card.parent_module}_I.S2.Word1,{card.parent_module}:2:I.Data);',
                comment='Clear the fault and move the data from the HMI card to the input data.'
            )
            self._add_rung_to_standard_routine(rung)

            instr1 = f'COP({card.parent_module}:1:O,zz_Demo3D_{card.parent_module}_O.S1,1)'
            instr2 = f'COP({card.parent_module}:2:O,zz_Demo3D_{card.parent_module}_O.S2,1)'
            rung = self.generator_object.config.rung_type(
                controller=self.controller,
                text=f'{instr1}{instr2};',
                comment='Map output data from physical card to emulation card.'
            )
            self._add_rung_to_standard_routine(rung)

            rung = self.generator_object.config.rung_type(
                controller=self.controller,
                text=f'COP(sz_Demo3D_{card.parent_module}_I,{card.parent_module}:1:I,1);',
                comment='Copy the input data from the emulation tag to the safety input card.'
            )
            self._add_to_safety_routine(rung)

    def _generate_safety_block_emulation(self) -> None:
        """Generate safety block emulation logic."""
        sbks = self.get_modules_by_type('AB_1732EsSafetyBlock')

        if not sbks:
            return

        self.schema.add_import_from_file(
            file_location=r'docs\controls\emu\Demo3D_WDint_DataType.L5X',
            asset_types=['DataTypes']
        )
        self.schema.add_import_from_file(
            file_location=r'docs\controls\emu\Demo3D_CommOK_SBK_DataType.L5X',
            asset_types=['DataTypes']
        )

        self.add_controller_tag(
            tag_name=f'zz_Demo3D_Comm_{self.controller.process_name}SBK',
            datatype='Demo3D_CommOK_SBK',
        )

        # Generate safety block emulation logic
        for module in sbks:
            # Add standard input tag
            std_tag = self.add_controller_tag(
                tag_name=f'zz_Demo3D_{module.name}_I',
                datatype='Demo3D_WDint',
            )

            # Add safe input tag
            sfty_tag = self.add_controller_tag(
                tag_name=f'sz_Demo3D_{module.name}_I',
                class_='Safety',
                datatype='Demo3D_WDint',
            )

            # Add output tag
            self.add_controller_tag(
                tag_name=f'zz_Demo3D_{module.name}_O',
                datatype='DINT',
            )

            # Add safety tag mapping to schema
            self.schema.add_safety_tag_mapping(
                std_tag.name,
                sfty_tag.name,
            )

            # Add to main emulation routine
            rung = self.controller.config.rung_type(
                controller=self.controller,
                text=f'[XIO(zz_Demo3D_{module.name}_I.Word1.0),XIC(zz_Demo3D_{module.name}_I.Word1.1)]FLL(0,zz_Demo3D_{module.name}_I.Word2,2);',  # noqa: E501
                comment='If communication status is lost to the SBK via the emulation model, zero out the SBK words.'
            )
            self._add_rung_to_standard_routine(rung)

            rung = self.controller.config.rung_type(
                controller=self.controller,
                text=f'COP({module.name}:O,zz_Demo3D_{module.name}_O,1);',
                comment='Copy the output data from the safety block to the emulation tag.'
            )
            self._add_rung_to_standard_routine(rung)

            rung = self.controller.config.rung_type(
                controller=self.controller,
                text=f'COP(sz_Demo3D_{module.name}_I,{module.name}:I,1);',
                comment='Copy the input data from the emulation tag to the safety block.'
            )
            self._add_rung_to_standard_routine(rung)

    def _remove_base_tags(self) -> None:
        """Remove base tags required for emulation."""
        self.logger.debug('Removing base tags for GM emulation...')

        for tag_name, _, _ in self.base_tags:
            self.remove_controller_tag(
                tag_name
            )

    def _remove_all_demo_tags(self) -> None:
        for tag in list(self.controller.tags):
            if tag.name.startswith('zz_Demo3D_') or tag.name.startswith('sz_Demo3D_'):
                self.remove_controller_tag(tag.name)

    def _remove_emulation_routines(self) -> None:
        """Remove emulation routines."""
        self.logger.debug('Removing emulation routines...')
        self.remove_routine(
            self.controller.mcp_program.name,
            'aaa_Emulation'
        )
        self.remove_routine(
            self.controller.safety_common_program.name,
            's_aaa_Emulation'
        )

    def _remove_g115_drive_emulation(self) -> None:
        """Remove Siemens G115 drive emulation logic."""
        g115_drives = self.get_modules_by_type('G115Drive')
        self.logger.info('Found %d Siemens G115 drive modules...', len(g115_drives))

        if not g115_drives:
            self.logger.debug('No Siemens G115 drive modules found, skipping emulation removal.')
            return

        # Remove controller tag for drives
        self.remove_controller_tag(
            tag_name=f'zz_Demo3D_{self.controller.process_name}_Siemens_Drives'
        )

        # Remove drive emulation datatype
        self.remove_datatype('Demo3D_G115D_Drive')

    def _remove_hmi_card_emulation(self) -> None:
        """Remove HMI card emulation logic."""
        hmi_cards = self.get_modules_by_description_pattern('<@TYPE 502xSlot1>')
        hmi_cards = [x for x in hmi_cards if x.type_ == 'AB_1734IB8S']
        self.logger.info('Found %d AB 1734IB8S HMI modules...', len(hmi_cards))

        if not hmi_cards:
            return

        # Remove generic comm word
        self.remove_controller_tag(
            tag_name=f'zz_Demo3D_Comm_{self.controller.process_name}HMI'
        )

        # Remove HMI emulation logic
        for card in hmi_cards:
            self.remove_controller_tag(
                tag_name=f'zz_Demo3D_{card.parent_module}_I'
            )
            self.remove_controller_tag(
                tag_name=f'sz_Demo3D_{card.parent_module}_I'
            )
            self.remove_controller_tag(
                tag_name=f'zz_Demo3D_{card.parent_module}_O'
            )

        # Remove HMI emulation datatypes
        self.remove_datatype('Demo3D_HMI_IN')
        self.remove_datatype('Demo3D_HMI_OUT')
        self.remove_datatype('Demo3D_CommOK_HMI')

        # Remove safety tag mappings
        for card in hmi_cards:
            self.schema.remove_safety_tag_mapping(
                f'zz_Demo3D_{card.parent_module}_I',
                f'sz_Demo3D_{card.parent_module}_I'
            )

    def _remove_safety_block_emulation(self) -> None:
        """Remove safety block emulation logic."""
        sbks = self.get_modules_by_type('AB_1732EsSafetyBlock')
        self.logger.info('Found %d AB 1732ES Safety Block modules...', len(sbks))

        if not sbks:
            return

        # Remove generic comm word
        self.remove_controller_tag(
            tag_name=f'zz_Demo3D_Comm_{self.controller.process_name}SBK'
        )

        # Remove safety block emulation logic
        for module in sbks:
            self.remove_controller_tag(
                tag_name=f'zz_Demo3D_{module.name}_I'
            )
            self.remove_controller_tag(
                tag_name=f'sz_Demo3D_{module.name}_I'
            )
            self.remove_controller_tag(
                tag_name=f'zz_Demo3D_{module.name}_O'
            )

        # Remove safety block emulation datatypes
        self.remove_datatype('Demo3D_WDint')
        self.remove_datatype('Demo3D_CommOK_SBK')

        # Remove safety tag mappings
        for module in sbks:
            self.schema.remove_safety_tag_mapping(
                f'zz_Demo3D_{module.name}_I',
                f'sz_Demo3D_{module.name}_I'
            )

    def generate_custom_module_emulation(self) -> None:
        """Generate module-specific emulation logic."""
        self.logger.info("Generating GM module-specific emulation logic...")

        self._generate_g115_drive_emulation()
        self._generate_hmi_card_emulation()
        self._generate_safety_block_emulation()

    def remove_base_emulation(self):
        self.logger.info("Removing base GM emulation logic...")
        self._remove_base_tags()
        self._remove_emulation_routines()

    def remove_custom_logic(self):
        self._remove_all_demo_tags()

    def remove_module_emulation(self):
        self.logger.info("Removing GM module-specific emulation logic...")
        self._remove_g115_drive_emulation()
        self._remove_hmi_card_emulation()
        self._remove_safety_block_emulation()

    def validate_controller(self) -> bool:
        """Validate that this is a valid GM controller."""
        if not self.controller.mcp_program:
            raise ValueError('No MCP program found in the controller.')

        if not self.controller.mcp_program.main_routine:
            raise ValueError('No main routine found in the MCP program.')

        if not self.controller.safety_common_program:
            raise ValueError('No safety common program found in the controller.')

        if not self.controller.safety_common_program.main_routine:
            raise ValueError('No main routine found in the safety common program.')

        return True

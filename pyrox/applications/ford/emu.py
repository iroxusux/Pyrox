""""General Motors specific emulation logic generator."""
from . import ford
from pyrox.models import plc


class FordEmulationGenerator(plc.EmulationGenerator):
    """Ford specific emulation logic generator."""
    generator_type = 'FordController'

    @property
    def controller(self) -> ford.FordController:
        return self.generator_object

    @controller.setter
    def controller(self, value: ford.FordController):
        if value.__class__.__name__ != self.generator_type:
            raise TypeError(f'Controller must be of type {self.generator_type}, got {value.__class__.__name__} instead.')
        self._generator_object = value

    @property
    def custom_tags(self) -> list[tuple[str, str, str, str]]:
        return []

    @property
    def target_safety_program_name(self) -> str:
        if hasattr(self, '_target_safety_program_name'):
            return self._target_safety_program_name
        self._target_safety_program_name = next((x.name for x in self.controller.safety_programs if "MappingInputs_Edit" in x.name), None)
        return self._target_safety_program_name

    @property
    def target_standard_program_name(self) -> str:
        return "MainProgram"

    def _disable_all_comm_edit_routines(self):
        """Disable all Comm Edit routines in all programs."""
        for program in self.controller.programs:
            if not program.comm_edit_routine:
                continue
            program.block_routine(
                program.comm_edit_routine.name,
                self.test_mode_tag
            )

    def _scrape_all_comm_ok_bits(self) -> list[plc.LogixInstruction]:
        """Scrape all Comm OK bits from the Comm Edit routine."""
        comm_ok_bits = []
        for program in self.controller.programs:
            comm_edit = program.comm_edit_routine
            if not comm_edit:
                self.logger.debug(f"No Comm Edit routine found in program {program.name}, skipping.")
                continue
            for instruction in comm_edit.instructions:
                if 'CommOk' in instruction.meta_data and instruction.instruction_name in ['OTE', 'OTL']:
                    comm_ok_bits.append(instruction)
        return comm_ok_bits

    def generate_custom_logic(self):
        comm_ok_bits = self._scrape_all_comm_ok_bits()
        if not comm_ok_bits:
            self.logger.warning("No Comm OK bits found in Comm Edit routines.")

        for bit in comm_ok_bits:
            device_name = bit.operands[0].meta_data.split('.')[0]
            comm_tag = self.add_controller_tag(
                tag_name=f'zz_Demo3D_COMM_OK_{device_name}',
                datatype='BOOL',
                description='Emulation Comm OK Bit'
            )
            pwr1_tag = self.add_controller_tag(
                tag_name=f'zz_Demo3D_Pwr1_{device_name}',
                datatype='BOOL',
                description='Emulation Power Circuit 1 OK Bit\n(Comm Power)'
            )
            pwr2_tag = self.add_controller_tag(
                tag_name=f'zz_Demo3D_Pwr2_{device_name}',
                datatype='BOOL',
                description='Emulation Power Circuit 1 OK Bit\n(Output Power)'
            )

            top_branch_text = f"XIC(S:FS)OTL({comm_tag.name})OTL({pwr1_tag.name})OTL({pwr2_tag.name})"
            btm_branch_text = f"XIC({comm_tag.name})XIC({pwr1_tag.name})XIC({pwr2_tag.name}){bit.meta_data}"

            rung = self.controller.config.rung_type(
                controller=self.controller,
                text=f"[{top_branch_text}),{btm_branch_text}];",
                comment='// Emulate comm ok status.\nComm and Power Managed by Emulation Model.'
            )
            self._add_rung_to_standard_routine(rung)

        self._disable_all_comm_edit_routines()

    def generate_custom_module_emulation(self) -> None:
        """Generate module-specific emulation logic."""

    def remove_base_emulation(self):
        pass

    def remove_module_emulation(self):
        pass

    def validate_controller(self) -> bool:
        """Validate that this is a valid GM controller."""

        return True

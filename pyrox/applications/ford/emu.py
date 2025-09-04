""""General Motors specific emulation logic generator."""
from . import ford
from pyrox.models import plc


class FordEmulationGenerator(plc.BaseEmulationGenerator):
    """Ford specific emulation logic generator."""

    generator_type = "FordController"

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
        return "*_MappingInputs_Edit"

    @property
    def target_standard_program_name(self) -> str:
        return "MainProgram"

    def _disable_all_comm_edit_routines(self):
        """Disable all Comm Edit routines in all programs."""
        for program in self.controller.programs:
            comm_edit = program.comm_edit_routine
            if not comm_edit:
                self.logger.debug(f"No Comm Edit routine found in program {program.name}, skipping.")
                continue
            main_routine = program.main_routine
            if not main_routine:
                self.logger.debug(f"No Main routine found in program {program.name}, skipping.")
                continue

            for rung in main_routine.rungs:
                instructions = [instr.meta_data for instr in rung.instructions]
                if any(comm_edit.name in instr for instr in instructions):
                    self.logger.debug(f"Disabling call to Comm Edit routine in program {program.name}.")
                    rung.text = f"XIC(Edit.Bit1){rung.text}"

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
            rung = self.controller.config.rung_type(
                controller=self.controller,
                text=f'{bit.meta_data};',
                comment='// Emulate comm ok status'
            )
            self._add_rung_to_standard_routine(rung)

        self._disable_all_comm_edit_routines()

    def generate_custom_module_emulation(self) -> None:
        """Generate module-specific emulation logic."""
        self.logger.info("Generating Ford module-specific emulation logic...")

    def remove_base_emulation(self):
        pass

    def remove_module_emulation(self):
        pass

    def validate_controller(self) -> bool:
        """Validate that this is a valid GM controller."""

        return True

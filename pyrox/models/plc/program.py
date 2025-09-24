"""Program module for pyrox
"""
from typing import Optional, TYPE_CHECKING
from pyrox.models.plc import meta as plc_meta
from pyrox.models.plc.collections import ContainsRoutines
from pyrox.services.plc import l5x_dict_from_file
if TYPE_CHECKING:
    from pyrox.models.plc import Controller, Routine, LogixInstruction


class Program(ContainsRoutines):
    def __init__(
        self,
        meta_data: dict = None,
        controller: 'Controller' = None
    ) -> None:
        """type class for plc Program

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """

        super().__init__(
            meta_data=meta_data or l5x_dict_from_file(
                plc_meta.PLC_PROG_FILE)['Program'],
            controller=controller
        )

    @property
    def dict_key_order(self) -> list[str]:
        return [
            '@Name',
            '@TestEdits',
            '@MainRoutineName',
            '@Disabled',
            '@Class',
            '@UseAsFolder',
            'Description',
            'Tags',
            'Routines',
        ]

    @property
    def disabled(self) -> str:
        return self['@Disabled']

    @property
    def main_routine(self) -> Optional['Routine']:
        """get the main routine for this program

        Returns:
            Routine: The main routine of this program.
        """
        if not self.main_routine_name:
            return None
        return self.routines.get(self.main_routine_name, None)

    @property
    def main_routine_name(self) -> str:
        return self['@MainRoutineName']

    @property
    def test_edits(self) -> str:
        return self['@TestEdits']

    @property
    def use_as_folder(self) -> str:
        return self['@UseAsFolder']

    def block_routine(
        self,
        routine_name: str,
        blocking_bit: str
    ) -> None:
        """block a routine in this program

        Args:
            routine_name (str): name of the routine to block
            blocking_bit (str): tag name of the bit to use for blocking
        """
        jsrs = self.get_instructions(instruction_filter='JSR')
        for jsr in jsrs:
            if jsr.operands[0].meta_data != routine_name:
                continue
            rung = jsr.rung
            if not rung:
                raise ValueError(f'JSR instruction {jsr.name} has no rung!')
            if rung.text.startswith(f'XIC({blocking_bit})'):
                continue
            rung.text = f'XIC({blocking_bit}){rung.text}'

    def get_instructions(
        self,
        instruction_filter: Optional[str],
        operand_filter: Optional[str] = None
    ) -> list['LogixInstruction']:
        """get instructions in this program that match the given filters

        Args:
            instruction_filter (Optional[str]): filter for instruction name
            operand_filter (Optional[str]): filter for operand name

        Returns:
            :class:`list[LogixInstruction]`: list of instructions that match the filters
        """
        instructions = []
        for routine in self.routines:
            instructions.extend(routine.get_instructions(instruction_filter, operand_filter))
        return instructions

    def unblock_routine(
        self,
        routine_name: str,
        blocking_bit: str
    ) -> None:
        """unblock a routine in this program

        Args:
            routine_name (str): name of the routine to unblock
            blocking_bit (str): tag name of the bit to use for blocking
        """
        jsrs = self.get_instructions(instruction_filter='JSR')
        for jsr in jsrs:
            if jsr.operand_value != routine_name:
                continue
            rung = jsr.rung
            if not rung:
                raise ValueError(f'JSR instruction {jsr.name} has no rung!')
            if not rung.text.startswith(f'XIC({blocking_bit})'):
                continue
            rung.text = rung.text.replace(f'XIC({blocking_bit})', '', 1)

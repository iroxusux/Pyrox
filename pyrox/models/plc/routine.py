"""Pyrox routine model
"""
from typing import (
    TYPE_CHECKING,
    Optional,
    Union
)
from pyrox.models.plc import meta as plc_meta
from pyrox.services.plc import l5x_dict_from_file

if TYPE_CHECKING:
    from .controller import (
        AddOnInstruction,
        Controller,
        ContainsRoutines,
        LogixInstruction,
        Program,
        Rung
    )


class Routine(plc_meta.NamedPlcObject):
    def __init__(
        self,
        meta_data: dict = None,
        controller: 'Controller' = None,
        program: Optional['Program'] = None,
        aoi: Optional['AddOnInstruction'] = None,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        """type class for plc Routine

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """

        super().__init__(
            meta_data=meta_data or l5x_dict_from_file(plc_meta.PLC_ROUT_FILE)['Routine'],
            controller=controller,
            name=name,
            description=description
        )

        self._program: Optional['Program'] = program
        self._aoi: Optional['AddOnInstruction'] = aoi
        self._instructions: list['LogixInstruction'] = []
        self._input_instructions: list['LogixInstruction'] = []
        self._output_instructions: list['LogixInstruction'] = []
        self._rungs: list[Rung] = []

    @property
    def dict_key_order(self) -> list[str]:
        return [
            '@Name',
            '@Type',
            'Description',
            'RLLContent',
        ]

    @property
    def aoi(self) -> Optional['AddOnInstruction']:
        return self._aoi

    @property
    def container(self) -> 'ContainsRoutines':
        return self.aoi if self.aoi else self.program

    @property
    def input_instructions(self) -> list['LogixInstruction']:
        if not self._input_instructions:
            self._compile_instructions()
        return self._input_instructions

    @property
    def instructions(self) -> list['LogixInstruction']:
        """get the instructions in this routine

        Returns:
            :class:`list[LogixInstruction]`
        """
        if not self._instructions:
            self._compile_instructions()
        return self._instructions

    @property
    def output_instructions(self) -> list['LogixInstruction']:
        if not self._output_instructions:
            self._compile_instructions()
        return self._output_instructions

    @property
    def program(self) -> Optional['Program']:
        return self._program

    @property
    def rungs(self) -> list['Rung']:
        if not self._rungs:
            self._compile_rungs()
        return self._rungs

    @property
    def raw_rungs(self) -> list[dict]:
        if not self['RLLContent']:
            self['RLLContent'] = {'Rung': []}
        if not isinstance(self['RLLContent']['Rung'], list):
            self['RLLContent']['Rung'] = [self['RLLContent']['Rung']]
        return self['RLLContent']['Rung']

    def _compile_from_meta_data(self):
        """compile this object from its meta data

        This method should be overridden by subclasses to provide specific compilation logic.
        """
        self._rungs = []
        self._instructions = []
        self._input_instructions = []
        self._output_instructions = []
        [self._rungs.append(self.config.rung_type(
            meta_data=x,
            controller=self.controller,
            routine=self,
            rung_number=i
        )
        )
            for i, x in enumerate(self.raw_rungs)]

    def _compile_instructions(self):
        """compile the instructions in this routine

        This method compiles the instructions from the rungs and initializes the lists.
        """
        self._input_instructions = []
        self._output_instructions = []
        self._instructions = []

        for rung in self.rungs:
            self._input_instructions.extend(rung.input_instructions)
            self._output_instructions.extend(rung.output_instructions)
            self._instructions.extend(rung.instructions)

    def _compile_rungs(self):
        """compile the rungs in this routine

        This method compiles the rungs from the raw metadata and initializes the list.
        """
        self._rungs = []
        [self._rungs.append(self.config.rung_type(
            meta_data=x,
            controller=self.controller,
            routine=self,
            rung_number=i
        )
        )
            for i, x in enumerate(self.raw_rungs)]

    def _invalidate(self):
        self._instructions: list['LogixInstruction'] = []
        self._input_instructions: list['LogixInstruction'] = []
        self._output_instructions: list['LogixInstruction'] = []
        self._rungs: list['Rung'] = []

    def add_rung(self,
                 rung: 'Rung',
                 index: Optional[int] = None):
        """add a rung to this routine

        Args:
            rung (Rung): the rung to add
        """
        from pyrox.models.plc import Rung  # avoid circular import
        if not isinstance(rung, Rung):
            raise ValueError("Rung must be an instance of Rung!")

        if index is None or index == -1 or index >= len(self.rungs):
            self.raw_rungs.append(rung.meta_data)
        else:
            self.raw_rungs.insert(index, rung.meta_data)
        for i, rung_dict in enumerate(self.raw_rungs):
            rung_dict['@Number'] = str(i)
        self._invalidate()

    def check_for_jsr(
        self,
        routine_name: str,
    ) -> bool:
        """Check if this routine contains a JSR instruction to the specified routine.

        Args:
            routine_name (str): The name of the routine to check for in JSR instructions.

        Returns:
            bool: True if a JSR instruction to the specified routine is found, False otherwise.
        """
        for instruction in self.instructions:
            if instruction.type == plc_meta.LogixInstructionType.JSR and instruction.operands:
                if str(instruction.operands[0]) == routine_name:
                    return True
        return False

    def clear_rungs(self):
        """clear all rungs from this routine"""
        self.log().debug(f"Clearing all rungs from routine {self.name}")
        self.raw_rungs.clear()
        self._compile_from_meta_data()

    def get_instructions(
        self,
        instruction_filter: Optional[str],
        operand_filter: Optional[str] = None
    ) -> list['LogixInstruction']:
        """Get instructions in this routine that match the specified filters.

        Args:
            instruction_filter (str): The instruction type to filter by (e.g., 'XIC', 'OTE').
            operand_filter (str, optional): An optional operand to further filter the instructions.

        Returns:
            list[LogixInstruction]: A list of instructions that match the specified filters.
        """
        instr = []
        for rung in self.rungs:
            instr.extend(rung.get_instructions(instruction_filter, operand_filter))
        return instr

    def remove_rung(self, rung: Union['Rung', int, str]):
        """remove a rung from this routine

        Args:
            rung (Rung or int): the rung to remove, can be an instance of Rung or its index
        """

        # ideally, the rungs should be a HashList. This should be updated later

        if isinstance(rung, str):
            rung = next((x for x in self.rungs if x.number == rung), None)  # an extra check for out of bound rungs
            if not rung:
                raise ValueError("Rung with specified number not found!")

        if isinstance(rung, int):
            if rung < 0 or rung >= len(self.rungs):
                raise IndexError("Rung index out of range!")
            rung = self.rungs[rung]

        from pyrox.models.plc import Rung  # avoid circular import
        if not isinstance(rung, Rung):
            raise ValueError("Rung must be an instance of Rung!")

        self.raw_rungs.remove(rung.meta_data)
        self._invalidate()

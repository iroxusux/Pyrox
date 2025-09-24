"""Instruction module for PLC models.
"""
import re
from typing import TYPE_CHECKING, Optional, Union
from pyrox.models.plc import meta as plc_meta
if TYPE_CHECKING:
    from .controller import Controller, Program, AddOnInstruction, Routine, Rung, Tag
from .operand import LogixOperand


class LogixInstruction(plc_meta.PlcObject):
    """Logix instruction.
    """

    def __init__(self,
                 meta_data: str,
                 rung: Optional['Rung'],
                 controller: 'Controller'):
        super().__init__(meta_data=meta_data,
                         controller=controller)
        self._aliased_meta_data: str = None
        self._qualified_meta_data: str = None
        self._instruction_name: str = None
        self._rung = rung
        self._tag: Optional['Tag'] = None
        self._type: plc_meta.LogixInstructionType = None
        self._operands: list[LogixOperand] = []
        self._get_operands()

    @property
    def aliased_meta_data(self) -> str:
        """get the aliased meta data for this instruction

        Returns:
            :class:`str`
        """
        if self._aliased_meta_data:
            return self._aliased_meta_data

        self._aliased_meta_data = self.meta_data
        for operand in self.operands:
            self._aliased_meta_data = self._aliased_meta_data.replace(operand.meta_data, operand.as_aliased)
        return self._aliased_meta_data

    @property
    def container(self) -> Optional[Union['Program', 'AddOnInstruction']]:
        if not self.rung:
            return None
        return self.rung.container

    @property
    def instruction_name(self) -> str:
        """get the instruction element

        Returns:
            :class:`str`
        """
        if self._instruction_name:
            return self._instruction_name

        matches = re.findall(plc_meta.INST_TYPE_RE_PATTERN, self._meta_data)
        if not matches or len(matches) < 1:
            raise ValueError("Corrupt meta data for instruction, no type found!")

        if not matches[0]:
            raise ValueError(f"Corrupt meta data for instruction, invalid type found: '{self._meta_data}'")

        self._instruction_name = matches[0]
        return self._instruction_name

    @property
    def is_add_on_instruction(self) -> bool:
        """Check if this instruction is an Add-On Instruction
        Returns:
            bool: True if this is an Add-On Instruction, False otherwise.
        """
        if not self.container or not self.container.controller:
            return False

        return self.instruction_name in self.container.controller.aois

    @property
    def operands(self) -> list[LogixOperand]:
        """get the instruction operands

        Returns:
            :class:`list[LogixOperand]`
        """
        if not self._operands:
            self._get_operands()
        return self._operands

    @property
    def qualified_meta_data(self) -> str:
        """get the qualified meta data for this instruction

        Returns:
            :class:`str`
        """
        if self._qualified_meta_data:
            return self._qualified_meta_data

        self._qualified_meta_data = self.meta_data
        for operand in self.operands:
            self._qualified_meta_data = self._qualified_meta_data.replace(operand.meta_data, operand.as_qualified)
        return self._qualified_meta_data

    @property
    def routine(self) -> Optional['Routine']:
        """get the routine this instruction is in

        Returns:
            :class:`Routine`
        """
        if not self._rung:
            return None
        return self._rung.routine

    @property
    def rung(self) -> Optional['Rung']:
        """get the rung this instruction is in

        Returns:
            :class:`Routine`
        """
        return self._rung

    @property
    def tag(self) -> Optional['Tag']:
        """get the tag this instruction is associated with

        Returns:
            :class:`Tag`
        """
        if self._tag:
            return self._tag

        if not self.container or not self.container.tags:
            return None

        self._tag = self.container.tags.get(self.instruction_name, None)
        if not self._tag:
            self._tag = self.controller.tags.get(self.instruction_name, None)

        return self._tag

    @property
    def type(self) -> plc_meta.LogixInstructionType:
        if self._type:
            return self._type
        self._type = self._get_instruction_type()
        return self._type

    def _get_operands(self):
        """get the operands for this instruction
        """
        self._operands = []
        matches = re.findall(plc_meta.INST_OPER_RE_PATTERN, self.meta_data)
        if not matches or len(matches) < 1 or not matches[0]:
            return

        for index, match in enumerate(matches[0].split(',')):
            if not match:
                continue
            self._operands.append(LogixOperand(match, self, index, self.controller))

    def _get_instruction_type(self) -> plc_meta.LogixInstructionType:
        """get the instruction type for this instruction

        Returns:
            :class:`LogixInstructionType`
        """
        if self.instruction_name in plc_meta.INPUT_INSTRUCTIONS:
            return plc_meta.LogixInstructionType.INPUT
        elif self.instruction_name in [x[0] for x in plc_meta.OUTPUT_INSTRUCTIONS]:
            return plc_meta.LogixInstructionType.OUTPUT
        elif self.instruction_name == plc_meta.INSTR_JSR:
            return plc_meta.LogixInstructionType.JSR
        else:
            return plc_meta.LogixInstructionType.UNKOWN

    def as_report_dict(self) -> dict:
        """get this operand as a report dictionary

        Returns:
            :class:`dict`: report dictionary
        """
        return {
            'instruction': self.meta_data,
            'program': self.container.name if self.container else '???',
            'routine': self.routine.name if self.routine else '???',
            'rung': self.rung.number if self.rung else '???',
        }

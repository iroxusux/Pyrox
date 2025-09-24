"""Logix operand module."""

from typing import TYPE_CHECKING, Optional
from pyrox.models.plc import meta as plc_meta

if TYPE_CHECKING:
    from .controller import LogixInstruction, Tag, ContainsRoutines


class LogixOperand(plc_meta.PlcObject):
    """Logix Operand
    """

    def __init__(
        self,
        meta_data: str,
        instruction: 'LogixInstruction',
        arg_position: int,
        controller: Optional[plc_meta.CTRL] = None
    ) -> None:
        super().__init__(
            meta_data=meta_data,
            controller=controller
        )
        if not isinstance(meta_data, str):
            raise TypeError("Meta data must be a string!")

        self._aliased_parents: list[str] = None
        self._arg_position = arg_position
        self._as_aliased: str = None
        self._as_qualified: str = None
        self._base_name: str = None
        self._base_tag: Optional['Tag'] = None
        self._first_tag: Optional['Tag'] = None
        self._instruction = instruction
        self._instruction_type: plc_meta.LogixInstructionType = None
        self._parents: list[str] = None
        self._qualified_parents: list[str] = None

    @property
    def aliased_parents(self) -> list[str]:
        if self._aliased_parents:
            return self._aliased_parents

        parts = self.as_aliased.split('.')
        if len(parts) == 1:
            self._aliased_parents = [self.as_aliased]
            return self._aliased_parents

        self._aliased_parents = []
        for x in range(len(parts)):
            self._aliased_parents.append(self.as_aliased.rsplit('.', x)[0])

        return self._aliased_parents

    @property
    def arg_position(self) -> int:
        """get the positional argument for this logix operand
        """
        return self._arg_position

    @property
    def as_aliased(self) -> str:
        """ Get the aliased name of this operand

        Returns:
            :class:`str`: aliased name of this operand
        """
        if self._as_aliased:
            return self._as_aliased

        if not self.first_tag or not self.first_tag.alias_for:
            self._as_aliased = self.meta_data
            return self._as_aliased

        return self.first_tag.get_alias_string(additional_elements=self.trailing_name)

    @property
    def as_qualified(self) -> str:
        """Get the qualified name of this operand

        Returns:
            :class:`str`: qualified name of this operand
        """
        if not self.base_tag:
            return self.meta_data

        if self.base_tag.scope is plc_meta.LogixTagScope.PROGRAM:
            return f'Program:{self.container.name}.{self.as_aliased}'
        else:
            return self.as_aliased

    @property
    def base_name(self) -> str:
        if self._base_name:
            return self._base_name
        self._base_name = self.meta_data.split('.')[0]
        return self._base_name

    @property
    def base_tag(self) -> 'Tag':
        if self._base_tag:
            return self._base_tag

        if self.container:
            self._base_tag = self.container.tags.get(self.base_name, None)

        if not self._base_tag:
            self._base_tag = self.controller.tags.get(self.base_name, None)

        if self._base_tag:
            self._base_tag = self._base_tag.get_base_tag()

        return self._base_tag

    @property
    def container(self) -> 'ContainsRoutines':
        return self.instruction.container

    @property
    def instruction(self) -> 'LogixInstruction':
        return self._instruction

    @property
    def instruction_type(self) -> plc_meta.LogixInstructionType:
        """Get the instruction type of this operand
        """
        if self._instruction_type:
            return self._instruction_type

        if self.instruction.instruction_name == plc_meta.INSTR_JSR:
            self._instruction_type = plc_meta.LogixInstructionType.JSR
            return self._instruction_type

        if self.instruction.instruction_name in plc_meta.INPUT_INSTRUCTIONS:
            self._instruction_type = plc_meta.LogixInstructionType.INPUT
            return self._instruction_type

        for instr in plc_meta.OUTPUT_INSTRUCTIONS:
            if self.instruction.instruction_name == instr[0]:
                if self.arg_position == instr[1] or (self.arg_position+1 == len(self.instruction.operands) and instr[1] == -1):
                    self._instruction_type = plc_meta.LogixInstructionType.OUTPUT
                else:
                    self._instruction_type = plc_meta.LogixInstructionType.INPUT

                return self._instruction_type

        # for now, all AOI operands will be considered out, until i can later dig into this.
        if self.instruction.instruction_name in [aoi.name for aoi in self.instruction.rung.controller.aois]:
            self._instruction_type = plc_meta.LogixInstructionType.OUTPUT
            return self._instruction_type

        self._instruction_type = plc_meta.LogixInstructionType.UNKOWN
        return self._instruction_type

    @property
    def first_tag(self) -> 'Tag':
        if self._first_tag:
            return self._first_tag

        if self.container:
            self._first_tag = self.container.tags.get(self.base_name, None)

        if not self._first_tag:
            if self.controller and self.controller.tags:
                self._first_tag = self.controller.tags.get(self.base_name, None)
            else:
                self._first_tag = None

        return self._first_tag

    @property
    def parents(self) -> list[str]:
        if self._parents:
            return self._parents

        parts = self._meta_data.split('.')
        if len(parts) == 1:
            self._parents = [self._meta_data]
            return self._parents

        self._parents = []
        for x in range(len(parts)):
            self._parents.append(self._meta_data.rsplit('.', x)[0])

        return self._parents

    @property
    def qualified_parents(self) -> list[str]:
        """get the qualified parents of this operand

        Returns:
            :class:`list[str]`: list of qualified parents
        """
        if self._qualified_parents:
            return self._qualified_parents

        if not self.base_tag:  # could be a system flag or hardware device, maybe
            self._qualified_parents = self.aliased_parents
            return self._qualified_parents

        if self.base_tag.scope == plc_meta.LogixTagScope.CONTROLLER:
            self._qualified_parents = self.aliased_parents
            return self._qualified_parents

        self._qualified_parents = list(self.aliased_parents)

        for i, v in enumerate(self._qualified_parents):
            self._qualified_parents[i] = f'Program:{self.container.name}.{v}'

        return self._qualified_parents

    @property
    def trailing_name(self) -> str:
        """get the trailing name of this operand

        Returns:
            :class:`str`: trailing name of this operand
        """
        if not self.meta_data:
            return None

        parts = self.meta_data.split('.')
        if len(parts) == 1:
            return ''

        return '.' + '.'.join(parts[1:])

    def as_report_dict(self) -> dict:
        """get this operand as a report dictionary

        Returns:
            :class:`dict`: report dictionary
        """
        return {
            'base operand': self.meta_data,
            'aliased operand': self.as_aliased,
            'qualified operand': self.as_qualified,
            'arg_position': self.arg_position,
            'instruction': self.instruction.meta_data,
            'instruction_type': self.instruction_type.name,
            'program': self.container.name if self.container else '???',
            'routine': self.instruction.rung.routine.name if self.instruction.rung and self.instruction.rung.routine else None,
            'rung': self.instruction.rung.number if self.instruction.rung else '???',
        }

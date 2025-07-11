"""plc type module
    """
from __future__ import annotations


from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

import re
from typing import Callable, Generic, get_args, Optional, Self, TypeVar, Union

from ..abc.meta import EnforcesNaming, Loggable, NamedPyroxObject
from ..abc.list import HashList
from ...services.dictionary_services import insert_key_at_index
from ...services.plc_services import l5x_dict_from_file
from ...utils import replace_strings_in_dict

__all__ = (
    'BASE_FILES',
    'PlcObject',
    'AddOnInstruction',
    'ConnectionCommand',
    'ConnectionParameters',
    'Controller',
    'Datatype',
    'DatatypeMember',
    'DataValueMember',
    'Module',
    'Program',
    'ProgramTag',
    'Routine',
    'Rung',
    'Tag',
    'TagEndpoint',
)

ATOMIC_DATATYPES = [
    'BIT',
    'BOOL',
    'SINT',
    'INT',
    'DINT',
    'LINT',
    'REAL',
    'LREAL',
    'USINT',
    'UINT',
    'UDINT',
    'ULINT',
    'STRING',
    'TIMER',
]

T = TypeVar('T')

INST_RE_PATTERN: str = r'[A-Za-z0-9_]+\(\S+?\)'
INST_TYPE_RE_PATTERN: str = r'([A-Za-z0-9_]+)(?:\(.*?)(?:\))'
INST_OPER_RE_PATTERN: str = r'(?:[A-Za-z0-9_]+\()(.*?)(?:\))'

PLC_ROOT_FILE = r'docs\controls\root.L5X'
PLC_PROG_FILE = r'docs\controls\_program.L5X'
PLC_ROUT_FILE = r'docs\controls\_routine.L5X'
PLC_DT_FILE = r'docs\controls\_datatype.L5X'
PLC_AOI_FILE = r'docs\controls\_aoi.L5X'
PLC_MOD_FILE = r'docs\controls\_module.L5X'
PLC_RUNG_FILE = r'docs\controls\_rung.L5X'
PLC_TAG_FILE = r'docs\controls\_tag.L5X'

BASE_FILES = [
    PLC_ROOT_FILE,
    PLC_PROG_FILE,
    PLC_ROUT_FILE,
    PLC_DT_FILE,
    PLC_AOI_FILE,
    PLC_MOD_FILE,
    PLC_RUNG_FILE,
    PLC_TAG_FILE,
]

RE_PATTERN_META_PRE = r"(?:"
RE_PATTERN_META_POST = r"\()(.*?)(?:\))"

OTE_OPERAND_RE_PATTERN = r"(?:OTE\()(.*?)(?:\))"
OTL_OPERAND_RE_PATTERN = r"(?:OTL\()(.*?)(?:\))"
OTU_OPERAND_RE_PATTERN = r"(?:OTU\()(.*?)(?:\))"
MOV_OPERAND_RE_PATTERN = r"(?:MOV\()(.*?)(?:\))"
MOVE_OPERAND_RE_PATTERN = r"(?:MOVE\()(.*?)(?:\))"
COP_OPERAND_RE_PATTERN = r"(?:COP\()(.*?)(?:\))"
CPS_OPERAND_RE_PATTERN = r"(?:CPS\()(.*?)(?:\))"

OUTPUT_INSTRUCTIONS_RE_PATTERN = [OTE_OPERAND_RE_PATTERN,
                                  OTL_OPERAND_RE_PATTERN,
                                  OTU_OPERAND_RE_PATTERN,
                                  MOV_OPERAND_RE_PATTERN,
                                  MOVE_OPERAND_RE_PATTERN,
                                  COP_OPERAND_RE_PATTERN,
                                  CPS_OPERAND_RE_PATTERN]

XIC_OPERAND_RE_PATTERN = r"(?:XIC\()(.*)(?:\))"
XIO_OPERAND_RE_PATTERN = r"(?:XIO\()(.*)(?:\))"

INPUT_INSTRUCTIONS_RE_PATTER = [XIC_OPERAND_RE_PATTERN,
                                XIO_OPERAND_RE_PATTERN]
# ------------------ Input Instructions ----------------------- #
# All input instructions assume every operand is type INPUT
INSTR_XIC = 'XIC'
INSTR_XIO = 'XIO'
INSTR_LIM = 'LIM'
INSTR_MEQ = 'MEQ'
INSTR_EQU = 'EQU'
INSTR_NEQ = 'NEQ'
INSTR_LES = 'LES'
INSTR_GRT = 'GRT'
INSTR_LEQ = 'LEQ'
INSTR_GEQ = 'GEQ'
INSTR_ISINF = 'IsINF'
INSTR_ISNAN = 'IsNAN'

INPUT_INSTRUCTIONS = [INSTR_XIC,
                      INSTR_XIO]

# ------------------ Output Instructions ----------------------- #
# The first index of the tuple is the instruction type
# the second index is the location of the output operand. -1 indicates the final position of an instructions operands
# (i.e., the last operand)
INSTR_OTE = ('OTE', -1)
INSTR_OTU = ('OTU', -1)
INSTR_OTL = ('OTL', -1)
INSTR_TON = ('TON', 0)
INSTR_TOF = ('TOF', 0)
INSTR_RTO = ('RTO', 0)
INSTR_CTU = ('CTU', 0)
INSTR_CTD = ('CTD', 0)
INSTR_RES = ('RES', -1)
INSTR_MSG = ('MSG', -1)
INSTR_GSV = ('GSV', -1)
ISNTR_ONS = ('ONS', -1)
INSTR_OSR = ('OSR', -1)
INSTR_OSF = ('OSF', -1)
INSTR_IOT = ('IOT', -1)
INSTR_CPT = ('CPT', 0)
INSTR_ADD = ('ADD', -1)
INSTR_SUB = ('SUB', -1)
INSTR_MUL = ('MUL', -1)
INSTR_DIV = ('DIV', -1)
INSTR_MOD = ('MOD', -1)
INSTR_SQR = ('SQR', -1)
INSTR_NEG = ('NEG', -1)
INSTR_ABS = ('ABS', -1)
INSTR_MOV = ('MOV', -1)
INSTR_MVM = ('MVM', -1)
INSTR_AND = ('AND', -1)
INSTR_OR = ('OR', -1)
INSTR_XOR = ('XOR', -1)
INSTR_NOT = ('NOT', -1)
INSTR_SWPB = ('SWPB', -1)
INSTR_CLR = ('CLR', -1)
INSTR_BTD = ('BTD', 2)
INSTR_FAL = ('FAL', 4)
INSTR_COP = ('COP', 1)
INSTR_FLL = ('FLL', 1)
INSTR_AVE = ('AVE', 2)
INSTR_SIZE = ('SIZE', -1)
ISNTR_CPS = ('CPS', 1)

OUTPUT_INSTRUCTIONS = [INSTR_OTE,
                       INSTR_OTU,
                       INSTR_OTL,
                       INSTR_TON,
                       INSTR_TOF,
                       INSTR_RTO,
                       INSTR_CTU,
                       INSTR_CTD,
                       INSTR_RES,
                       INSTR_MSG,
                       INSTR_GSV,
                       ISNTR_ONS,
                       INSTR_OSR,
                       INSTR_OSF,
                       INSTR_IOT,
                       INSTR_CPT,
                       INSTR_ADD,
                       INSTR_SUB,
                       INSTR_MUL,
                       INSTR_DIV,
                       INSTR_MOD,
                       INSTR_SQR,
                       INSTR_NEG,
                       INSTR_ABS,
                       INSTR_MOV,
                       INSTR_MVM,
                       INSTR_AND,
                       INSTR_OR,
                       INSTR_XOR,
                       INSTR_NOT,
                       INSTR_SWPB,
                       INSTR_CLR,
                       INSTR_BTD,
                       INSTR_FAL,
                       INSTR_COP,
                       INSTR_FLL,
                       INSTR_AVE,
                       INSTR_SIZE,
                       ISNTR_CPS]


class LogixTagScope(Enum):
    """logix tag scope enumeration
    """
    PROGRAM = 0
    PUBLIC = 1
    CONTROLLER = 2


class LogixInstructionType(Enum):
    """logix instruction type enumeration
    """
    INPUT = 1
    OUTPUT = 2
    UNKOWN = 3


class LogixAssetType(Enum):
    """logix element resolver enumeration
    """
    DEFAULT = 0
    TAG = 1
    DATATYPE = 2
    AOI = 3
    MODULE = 4
    PROGRAM = 5
    ROUTINE = 6
    PROGRAMTAG = 7
    RUNG = 8
    ALL = 9


class PlcObject(EnforcesNaming, NamedPyroxObject):
    """base class for a l5x plc object.
    """

    def __getitem__(self, key):
        if isinstance(self.meta_data, dict):
            return self._meta_data.get(key, None)
        elif isinstance(self.meta_data, str):
            return self.meta_data

    def __init__(self,
                 controller: 'Controller' = None,
                 default_loader: Callable = lambda: defaultdict(None),
                 meta_data: Union[dict, str] = defaultdict(None),
                 **kwargs):
        self._meta_data = meta_data or default_loader()
        self._controller = controller
        self._init_dict_order()
        EnforcesNaming.__init__(self)
        NamedPyroxObject.__init__(self,
                                  **kwargs)

    def __repr__(self):
        return self.meta_data

    def __setitem__(self, key, value):
        if isinstance(self.meta_data, dict):
            self._meta_data[key] = value
        else:
            raise TypeError("Cannot set item on a non-dict meta data object!")

    def __str__(self):
        return str(self.meta_data)

    @property
    def dict_key_order(self) -> list[str]:
        """get the order of keys in the meta data dict.

        This is intended to be overridden by subclasses to provide a specific order of keys.

        .. -------------------------------

        Returns
        ----------
            :class:`list[str]`
        """
        return []

    @property
    def config(self) -> Optional['ControllerConfiguration']:
        """ get the controller configuration for this object

        .. -------------------------------

        Returns:
        ----------
            :class:`ControllerConfiguration`
        """
        return ControllerConfiguration() if not self._controller else self._controller._config

    @property
    def controller(self) -> Optional['Controller']:
        """get this object's controller

        .. -------------------------------

        Returns
        ----------
            :class:`Controller`
        """
        return self._controller

    @property
    def meta_data(self) -> Union[dict, str]:
        return self._meta_data

    @meta_data.setter
    def meta_data(self, value: Union[dict, str]):
        if isinstance(value, dict):
            self._meta_data = replace_strings_in_dict(value)
        elif isinstance(value, str):
            self._meta_data = value
        else:
            raise TypeError("Meta data must be a dict or a string!")

    def _compile_from_meta_data(self):
        """compile this object from its meta data

        This method should be overridden by subclasses to provide specific compilation logic.
        """
        raise NotImplementedError("This method should be overridden by subclasses to compile from meta data.")

    def _init_dict_order(self):
        """initialize the dict order for this object.

        This method relies on the child classes to define their own `dict_key_order` property.
        """
        if not self.dict_key_order:
            return

        if isinstance(self.meta_data, dict):
            for index, key in enumerate(self.dict_key_order):
                if key not in self.meta_data:
                    insert_key_at_index(d=self.meta_data, key=key, index=index)

    def validate(self,
                 report: Optional[ControllerReportItem] = None) -> ControllerReportItem:
        if not report:
            report = ControllerReportItem(self,
                                          f'Validating {self.__class__.__name__} object: {str(self)}')

        if self.config is None:
            report.test_notes.append('No controller configuration found!')
            report.pass_fail = False

        if self.controller is None:
            report.test_notes.append('No controller found!')
            report.pass_fail = False

        if self.meta_data is None:
            report.test_notes.append('No meta data found!')
            report.pass_fail = False

        return report


class NamedPlcObject(PlcObject):
    """Supports a name and description for a PLC object.
    """

    def __init__(self,
                 meta_data=defaultdict(None),
                 controller=None,
                 **kwargs):
        super().__init__(controller=controller,
                         meta_data=meta_data,
                         name=meta_data.get('@Name', None),
                         **kwargs)

    def __repr__(self):
        return self.name

    def __str__(self):
        return str(self.name)

    @property
    def name(self) -> str:
        """get this object's meta data name

        .. -------------------------------

        Returns
        ----------
            :class:`str`
        """
        return self['@Name']

    @name.setter
    def name(self, value: str):
        if not self.is_valid_string(value):
            raise self.InvalidNamingException

        self['@Name'] = value

    @property
    def description(self) -> str:
        """get this object's meta data description

        .. -------------------------------

        Returns
        ----------
            :class:`str`
        """
        return self['Description']

    @description.setter
    def description(self, value: str):
        self['Description'] = value

    def validate(self,
                 report: Optional[ControllerReportItem] = None) -> ControllerReportItem:
        report = super().validate(report=report)

        if self.name is None:
            report.test_notes.append('No name found!')
            report.pass_fail = False

        if self.description is None:
            report.test_notes.append('No description found!')
            report.pass_fail = False

        return report


class LogixOperand(PlcObject):
    """Logix Operand
    """

    def __init__(self,
                 meta_data: str,
                 instruction: 'LogixInstruction',
                 arg_position: int,
                 controller: 'Controller'):
        super().__init__(meta_data=meta_data,
                         controller=controller)
        if isinstance(self._meta_data, defaultdict):
            raise TypeError("Meta data must be a a string!")
        self._aliased_parents: list[str] = None
        self._arg_position = arg_position
        self._as_aliased: str = None
        self._as_qualified: str = None
        self._base_name: str = None
        self._base_tag: Optional['Tag'] = None
        self._first_tag: Optional['Tag'] = None
        self._instruction = instruction
        self._instruction_type: LogixInstructionType = None
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

        if self.base_tag.scope is LogixTagScope.PROGRAM:
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
    def base_tag(self) -> Tag:
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
    def container(self) -> ContainsRoutines:
        return self.instruction.container

    @property
    def instruction(self) -> 'LogixInstruction':
        return self._instruction

    @property
    def instruction_type(self) -> LogixInstructionType:
        """Get the instruction type of this operand
        """
        if self._instruction_type:
            return self._instruction_type

        if self.instruction.instruction_name in INPUT_INSTRUCTIONS:
            self._instruction_type = LogixInstructionType.INPUT
            return self._instruction_type

        for instr in OUTPUT_INSTRUCTIONS:
            if self.instruction.instruction_name == instr[0]:
                if self.arg_position == instr[1] or (self.arg_position+1 == len(self.instruction.operands) and instr[1] == -1):
                    self._instruction_type = LogixInstructionType.OUTPUT
                else:
                    self._instruction_type = LogixInstructionType.INPUT

                return self._instruction_type

        # for now, all AOI operands will be considered out, until i can later dig into this.
        if self.instruction.instruction_name in [aoi.name for aoi in self.instruction.rung.controller.aois]:
            # if self.instruction.element in self.instruction.routine.controller.aois:
            self._instruction_type = LogixInstructionType.OUTPUT
            return self._instruction_type

        self._instruction_type = LogixInstructionType.UNKOWN
        return self._instruction_type

    @property
    def first_tag(self) -> Tag:
        if self._first_tag:
            return self._first_tag

        if self.container:
            self._first_tag = self.container.tags.get(self.base_name, None)

        if not self._first_tag:
            self._first_tag = self.controller.tags.get(self.base_name, None)

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

        if self.base_tag.scope == LogixTagScope.CONTROLLER:
            self._qualified_parents = self.aliased_parents
            return self._qualified_parents

        self._qualified_parents = self.aliased_parents

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

    def validate(self) -> ControllerReportItem:
        report = ControllerReportItem(self,
                                      f'Validating {self.__class__.__name__} object: {self.meta_data}',
                                      True,
                                      [])

        if self.arg_position < 0:
            report.test_notes.append(f'Invalid argument position for operand {self.meta_data}!')
            report.pass_fail = False

        try:
            if not self.as_aliased:
                report.test_notes.append(f'No qualified name found for operand {self.meta_data}!')
                report.pass_fail = False
        except ValueError as e:
            report.test_notes.append(f'Error getting aliased name for operand {self.meta_data}: {str(e)}')
            report.pass_fail = False

        if not self.base_name:
            report.test_notes.append(f'No base name found for operand {self.meta_data}!')
            report.pass_fail = False

        if not self.container:
            report.test_notes.append(f'No container found for operand {self.meta_data}!')
            report.pass_fail = False

        if not self.instruction:
            report.test_notes.append(f'No instruction found for operand {self.meta_data}!')
            report.pass_fail = False

        if not self.instruction_type or self.instruction_type == LogixInstructionType.UNKOWN:
            report.test_notes.append(f'No instruction type found for operand {self.meta_data}!')
            report.pass_fail = False

        if not self.parents:
            report.test_notes.append(f'No parents found for operand {self.meta_data}!')
            report.pass_fail = False

        try:
            if not self.aliased_parents:
                report.test_notes.append(f'No aliased parents found for operand {self.meta_data}!')
                report.pass_fail = False
        except ValueError as e:
            report.test_notes.append(f'Error getting aliased parents for operand {self.meta_data}: {str(e)}')
            report.pass_fail = False

        return report


class LogixInstruction(PlcObject):
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
        self._type: LogixInstructionType = None
        self._operands: list[LogixOperand] = []
        self._get_operands()

    @property
    def aliased_meta_data(self) -> str:
        """get the aliased meta data for this instruction

        .. -------------------------------

        Returns
        ----------
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
        return self._rung.container

    @property
    def instruction_name(self) -> str:
        """get the instruction element

        .. -------------------------------

        Returns
        ----------
            :class:`str`
        """
        if self._instruction_name:
            return self._instruction_name

        matches = re.findall(INST_TYPE_RE_PATTERN, self._meta_data)
        if not matches or len(matches) < 1:
            raise ValueError("Corrupt meta data for instruction, no type found!")

        self._instruction_name = matches[0]
        return self._instruction_name

    @property
    def operands(self) -> list[LogixOperand]:
        """get the instruction operands

        .. -------------------------------

        Returns
        ----------
            :class:`list[LogixOperand]`
        """
        return self._operands

    @property
    def qualified_meta_data(self) -> str:
        """get the qualified meta data for this instruction

        .. -------------------------------

        Returns
        ----------
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

        .. -------------------------------

        Returns
        ----------
            :class:`Routine`
        """
        if not self._rung:
            return None
        return self._rung.routine

    @property
    def rung(self) -> Optional['Rung']:
        """get the rung this instruction is in

        .. -------------------------------

        Returns
        ----------
            :class:`Routine`
        """
        return self._rung

    @property
    def type(self) -> LogixInstructionType:
        if self._type:
            return self._type
        self._type = LogixInstructionType.INPUT if self.instruction_name in INPUT_INSTRUCTIONS else LogixInstructionType.OUTPUT
        return self._type

    def _get_operands(self):
        """get the operands for this instruction
        """
        matches = re.findall(INST_OPER_RE_PATTERN, self.meta_data)
        if not matches or len(matches) < 1:
            raise ValueError("Corrupt meta data for instruction, no operands found!")

        self._operands = []
        for index, match in enumerate(matches[0].split(',')):
            if not match:
                continue
            self._operands.append(LogixOperand(match, self, index, self.controller))

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

    def validate(self) -> ControllerReportItem:
        report = ControllerReportItem(self,
                                      f'Validating {self.__class__.__name__} object: {self.meta_data}')
        if not self.type or self.type == LogixInstructionType.UNKOWN:
            report.test_notes.append('No instruction type found for instruction!')
            report.pass_fail = False

        return report


class SupportsMeta(Generic[T], NamedPlcObject):
    """meta type for 'supports' structuring
    """

    @property
    def __key__(self) -> str:
        raise NotImplementedError()

    def __set__(self, value: T, key: Optional[str] = None):
        key_ = self.__key__ if not key else key
        try:
            base = get_args(self.__orig_bases__[0])[0]
        except TypeError:
            base = get_args(self.__orig_bases__[0])
        if not isinstance(value, base):
            raise ValueError(f'Value must be of type {T}!')
        self[key_] = value

    def __get__(self, key: Optional[str] = None):
        key_ = self.__key__ if not key else key
        return self[key_]


class ContainsTags(NamedPlcObject):
    def __init__(self,
                 meta_data=defaultdict(None),
                 controller=None):
        super().__init__(meta_data,
                         controller)

        self._tags: HashList
        self._compile_from_meta_data()

    @property
    def raw_tags(self) -> list[dict]:
        if not self['Tags']:
            self['Tags'] = {'Tag': []}
        if not isinstance(self['Tags']['Tag'], list):
            self['Tags']['Tag'] = [self['Tags']['Tag']]
        return self['Tags']['Tag']

    @property
    def tags(self) -> HashList:
        return self._tags

    def _compile_from_meta_data(self):
        """compile this object from its meta data
        """
        self._tags: HashList = HashList('name')
        [self._tags.append(self.config.tag_type(meta_data=x, controller=self.controller, container=self))
         for x in self.raw_tags]

    def add_tag(self, tag: 'Tag'):
        """add a tag to this container

        Args:
            routine (Tag): tag to add
        """
        if not isinstance(tag, Tag):
            raise TypeError("Tag must be of type Tag!")

        if tag.name in self._tags:
            self.raw_tags.remove(tag.meta_data)

        self.raw_tags.append(tag.meta_data)
        self._compile_from_meta_data()

    def remove_tag(self, tag: Union['Tag', str]) -> None:
        """remove a tag from this container

        Args:
            tag (Union[Tag, str]): tag to remove
        """
        if isinstance(tag, str):
            tag_name = tag
        elif isinstance(tag, Tag):
            tag_name = tag.name
        else:
            raise TypeError("Tag must be of type Tag or str!")

        if tag_name not in self._tags:
            raise ValueError(f"Tag with name {tag_name} does not exist in this container!")

        self.raw_tags.remove(self._tags[tag_name].meta_data)
        self._compile_from_meta_data()


class ContainsRoutines(ContainsTags):
    """This PLC Object contains routines
    """

    def __init__(self,
                 meta_data=defaultdict(None), controller=None):
        super().__init__(meta_data, controller)

        self._input_instructions: list[LogixInstruction] = []
        self._output_instructions: list[LogixInstruction] = []
        self._instructions: list[LogixInstruction] = []
        self._routines: HashList = HashList('name')
        self._compile_from_meta_data()

    @property
    def input_instructions(self) -> list[LogixInstruction]:
        if self._input_instructions:
            return self._input_instructions

        self._input_instructions = []
        [self._input_instructions.extend(x.input_instructions) for x in self.routines]
        return self._input_instructions

    @property
    def instructions(self) -> list[LogixInstruction]:
        """get the instructions in this container

        .. -------------------------------

        Returns
        ----------
            :class:`list[LogixInstruction]`
        """
        if self._instructions:
            return self._instructions
        self._instructions = []
        [self._instructions.extend(x.instructions) for x in self.routines]
        return self._instructions

    @property
    def output_instructions(self) -> list[LogixInstruction]:
        if self._output_instructions:
            return self._output_instructions

        self._output_instructions = []
        [self._output_instructions.extend(x.output_instructions) for x in self.routines]
        return self._output_instructions

    @property
    def routines(self) -> list[Routine]:
        return self._routines

    @property
    def raw_routines(self) -> list[dict]:
        if not self['Routines']:
            self['Routines'] = {'Routine': []}
        if not isinstance(self['Routines']['Routine'], list):
            self['Routines']['Routine'] = [self['Routines']['Routine']]
        return self['Routines']['Routine']

    def _compile_from_meta_data(self):
        """compile this object from its meta data
        """
        super()._compile_from_meta_data()
        self._input_instructions = []
        self._output_instructions = []
        self._instructions = []
        self._routines: HashList = HashList('name')
        for routine in self.raw_routines:
            self._routines.append(self.config.routine_type(meta_data=routine, controller=self.controller, program=self))

    def add_routine(self, routine: 'Routine'):
        """add a routine to this container

        Args:
            routine (Routine): routine to add
        """
        if not isinstance(routine, Routine):
            raise TypeError("Routine must be of type Routine!")

        if routine.name in self._routines:
            raise ValueError(f"Routine with name {routine.name} already exists in this container!")

        self.raw_routines.append(routine.meta_data)
        self._compile_from_meta_data()

    def remove_routine(self, routine: 'Routine'):
        """remove a routine from this container

        Args:
            routine (Routine): routine to remove
        """
        if not isinstance(routine, Routine):
            raise TypeError("Routine must be of type Routine!")

        if routine.name not in self._routines:
            raise ValueError(f"Routine with name {routine.name} does not exist in this container!")

        self.raw_routines.remove(routine.meta_data)
        self._compile_from_meta_data()


class AddOnInstruction(ContainsRoutines):
    """AddOn Instruction Definition for a rockwell plc
    """

    def __init__(self,
                 meta_data: dict = None,
                 controller: 'Controller' = None):
        """type class for plc AddOn Instruction Definition

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """

        super().__init__(meta_data=meta_data or l5x_dict_from_file(PLC_AOI_FILE)['AddOnInstructionDefinition'],
                         controller=controller)
        # this is due to a weird rockwell issue with the character '<' in the revision extension
        if self.revision_extension is not None:
            self.revision_extension = self.revision_extension  # force the setter logic to replace anything that is input

    @property
    def dict_key_order(self) -> list[str]:
        return [
            '@Name',
            '@Class',
            '@Revision',
            '@ExecutePrescan',
            '@ExecutePostscan',
            '@ExecuteEnableInFalse',
            '@CreatedDate',
            '@CreatedBy',
            '@EditedDate',
            '@EditedBy',
            '@SoftwareRevision',
            'Description',
            'RevisionNote',
            'Parameters',
            'LocalTags',
            'Routines',
        ]

    @property
    def revision(self) -> str:
        return self['@Revision']

    @revision.setter
    def revision(self, value: str):
        if not self.is_valid_revision_string(value):
            raise self.InvalidNamingException

        self['@Revision'] = value

    @property
    def execute_prescan(self) -> str:
        return self['@ExecutePrescan']

    @execute_prescan.setter
    def execute_prescan(self, value: str):
        if isinstance(value, bool):
            value = 'true' if value else 'false'
        if not self.is_valid_rockwell_bool(value):
            raise self.InvalidNamingException

        self['@ExecutePrescan'] = value

    @property
    def execute_postscan(self) -> str:
        return self['@ExecutePostscan']

    @execute_postscan.setter
    def execute_postscan(self, value: str):
        if isinstance(value, bool):
            value = 'true' if value else 'false'
        if not self.is_valid_rockwell_bool(value):
            raise self.InvalidNamingException

        self['@ExecutePostscan'] = value

    @property
    def execute_enable_in_false(self) -> str:
        return self['@ExecuteEnableInFalse']

    @execute_enable_in_false.setter
    def execute_enable_in_false(self, value: str):
        if isinstance(value, bool):
            value = 'true' if value else 'false'
        if not self.is_valid_rockwell_bool(value):
            raise self.InvalidNamingException

        self['@ExecuteEnableInFalse'] = value

    @property
    def created_date(self) -> str:
        return self['@CreatedDate']

    @property
    def created_by(self) -> str:
        return self['@CreatedBy']

    @property
    def edited_date(self) -> str:
        return self['@EditedDate']

    @property
    def edited_by(self) -> str:
        return self['@EditedBy']

    @property
    def software_revision(self) -> str:
        return self['@SoftwareRevision']

    @software_revision.setter
    def software_revision(self, value: str):
        if not self.is_valid_string(value):
            raise self.InvalidNamingException

        self['@SoftwareRevision'] = value

    @property
    def revision_extension(self) -> str:
        """get the revision extension for this AOI

        Returns:
            :class:`str`: revision extension
        """
        return self['@RevisionExtension']

    @revision_extension.setter
    def revision_extension(self, value: str):
        if not isinstance(value, str):
            raise ValueError("Revision extension must be a string!")

        self['@RevisionExtension'] = value.replace('<', '&lt;')

    @property
    def revision_note(self) -> str:
        return self['RevisionNote']

    @revision_note.setter
    def revision_note(self, value: str):
        if not isinstance(value, str):
            raise ValueError("Revision note must be a string!")

        self['RevisionNote'] = value

    @property
    def parameters(self) -> list[dict]:
        if not self['Parameters']:
            return []

        if not isinstance(self['Parameters']['Parameter'], list):
            return [self['Parameters']['Parameter']]
        return self['Parameters']['Parameter']

    @property
    def local_tags(self) -> list[dict]:
        if not self['LocalTags']:
            return []

        if not isinstance(self['LocalTags']['LocalTag'], list):
            return [self['LocalTags']['LocalTag']]
        return self['LocalTags']['LocalTag']

    @property
    def raw_tags(self) -> list[dict]:
        # rockwell is weird and this is the only instance they use 'local tags' instead of 'tags'
        if not self['LocalTags']:
            self['LocalTags'] = {'LocalTag': []}
        if not isinstance(self['LocalTags']['LocalTag'], list):
            self['LocalTags']['LocalTag'] = [self['LocalTags']['LocalTag']]
        return self['LocalTags']['LocalTag']

    def validate(self):
        report = ControllerReportItem(self,
                                      f'Validating {self.__class__.__name__} object: {self.name}')

        return report


class ConnectionParameters:
    """connection parameters for connecting to a plc
    """

    def __init__(self,
                 ip_address: str,
                 slot: int,
                 rpi: int = 50):
        # explicit type-casting to enform type protection for this class
        slot = int(slot)
        rpi = int(rpi)

        if len(ip_address.split('.')) != 4:
            raise ValueError('Ip addresses must be specified in groups of 4 - e.g. 192.168.1.2')

        self._ip_address: str = ip_address  # PLC IP Address
        self._slot: int = slot              # PLC Slot
        self._rpi: float = rpi              # PLC Requested Packet Interval

    @property
    def ip_address(self) -> str:
        return self._ip_address

    @property
    def rpi(self) -> int:
        return self._rpi

    @property
    def slot(self) -> int:
        return self._slot


class ConnectionCommandType(Enum):
    NA = 0
    READ = 1
    WRITE = 2


class ConnectionCommand:
    """Connection Command for a PLC
    """

    def __init__(self,
                 type: ConnectionCommandType,
                 tag_name: str,
                 tag_value: int,
                 data_type: int,
                 response_cb: Callable):
        self._type = type
        self._tag_name = tag_name
        self._tag_value = tag_value
        self._data_type = data_type
        self._response_cb = response_cb

    @property
    def type(self) -> ConnectionCommandType:
        return self._type

    @property
    def tag_name(self) -> str:
        return self._tag_name

    @property
    def tag_value(self) -> int:
        return self._tag_value

    @property
    def data_type(self) -> int:
        return self._data_type

    @property
    def response_cb(self) -> Callable:
        return self._response_cb


class DatatypeMember(NamedPlcObject):
    def __init__(self,
                 l5x_meta_data: dict,
                 parent_datatype: 'Datatype',
                 controller: Controller):
        """type class for plc Datatype Member

        Args:
            l5x_meta_data (str): meta data
            datatype (Datatype): parent datatype
            controller (Self): controller dictionary
        """
        super().__init__(meta_data=l5x_meta_data,
                         controller=controller)
        self._parent_datatype = parent_datatype

    @property
    def datatype(self) -> str:
        """get the datatype of this member

        Returns:
            :class:`str`: datatype of this member
        """
        return self['@DataType']

    @property
    def dimension(self) -> str:
        return self['@Dimension']

    @property
    def hidden(self) -> str:
        return self['@Hidden']

    @property
    def is_atomic(self) -> bool:
        """check if this member is atomic

        Returns:
            :class:`bool`: True if atomic, False otherwise
        """
        return self.datatype in ATOMIC_DATATYPES

    @property
    def parent_datatype(self) -> 'Datatype':
        return self._parent_datatype


class Datatype(NamedPlcObject):
    """.. description::
        Datatype for a rockwell plc
        .. --------------------------------
        .. package::
        models.plc.plc
        .. --------------------------------
        .. attributes::
        :class:`list[str]` endpoint_operands:
            list of endpoint operands for this datatype
        """

    def __init__(self,
                 **kwargs):

        super().__init__(default_loader=lambda: l5x_dict_from_file(PLC_DT_FILE)['DataType'],
                         **kwargs)
        self._endpoint_operands: list[str] = []
        self._members: list[DatatypeMember] = []
        [self._members.append(DatatypeMember(l5x_meta_data=x, controller=self.controller, parent_datatype=self))
         for x in self.raw_members]

    @property
    def endpoint_operands(self) -> list[str]:
        """get the endpoint operands for this datatype
        for example, for a datatype with members like::
        .. code-block:: xml
        <Datatype Name="MyDatatype" ...>
            <Member Name="MyAtomicMember" @Datatype="BOOL" ... />
            <Member Name="MyMember" @Datatype="SomeOtherDatatype" ...>
                <Member Name"MyChildMember" @Datatype="BOOL" ... />
            </Member>
        </Datatype>

        the endpoint operands would be:
            ['.MyAtomicMember', '.MyMember.MyChildMember']

        .. -------------------------------
        .. returns::
        :class:`list[str]`:
            list of endpoint operands
        """
        if self.is_atomic:
            return ['']
        if self._endpoint_operands:
            return self._endpoint_operands
        self._endpoint_operands = []
        for member in self.members:
            if member.hidden == 'true':
                continue
            if member.is_atomic:
                self._endpoint_operands.append(f'.{member.name}')
            else:
                datatype = self.controller.datatypes.get(member['@DataType'], None)
                if not datatype:
                    self.logger.warning(f"Datatype {member['@DataType']} not found for member {member.name} in {self.name}.")
                    continue
                self._endpoint_operands.extend([f'.{member.name}{x}' for x in datatype.endpoint_operands])
        return self._endpoint_operands

    @property
    def dict_key_order(self) -> list[str]:
        return [
            '@Name',
            '@Family',
            '@Class',
            'Description',
            'Members',
        ]

    @property
    def family(self) -> str:
        return self['@Family']

    @property
    def is_atomic(self) -> bool:
        """check if this member is atomic

        Returns:
            :class:`bool`: True if atomic, False otherwise
        """
        return self.name in ATOMIC_DATATYPES

    @property
    def members(self) -> list[DatatypeMember]:
        return self._members

    @property
    def raw_members(self) -> list[dict]:
        if not self['Members']:
            self['Members'] = {'Member': []}
        if not isinstance(self['Members']['Member'], list):
            self['Members']['Member'] = [self['Members']['Member']]
        return self['Members']['Member']

    def validate(self):
        report = ControllerReportItem(self,
                                      f'Validating {self.__class__.__name__} object: {self.name}')

        return report


class Module(NamedPlcObject):
    def __init__(self,
                 name: str = None,
                 l5x_meta_data: dict = None,
                 controller: Controller = None):
        """type class for plc Module

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """

        if not l5x_meta_data:
            l5x_meta_data = l5x_dict_from_file(PLC_MOD_FILE)['Module']

        super().__init__(meta_data=l5x_meta_data,
                         controller=controller)

        if name:
            self.name = name

    @property
    def dict_key_order(self) -> list[str]:
        return [
            '@Name',
            '@CatalogNumber',
            '@Vendor',
            '@ProductType',
            '@ProductCode',
            '@Major',
            '@Minor',
            '@ParentModule',
            '@ParentModPortId',
            '@Inhibited',
            '@MajorFault',
            'Description',
            'EKey',
            'Ports',
            'Communications',
        ]

    @property
    def catalog_number(self) -> str:
        return self['@CatalogNumber']

    @catalog_number.setter
    def catalog_number(self, value: str):
        if not self.is_valid_module_string(value):
            raise self.InvalidNamingException

        self['@CatalogNumber'] = value

    @property
    def vendor(self) -> str:
        return self['@Vendor']

    @vendor.setter
    def vendor(self, value: str):
        if not isinstance(int(value), int):
            raise ValueError("Vendor must be an integer!")

        self['@Vendor'] = value

    @property
    def product_type(self) -> str:
        return self['@ProductType']

    @product_type.setter
    def product_type(self, value: str):
        if not isinstance(int(value), int):
            raise ValueError("Product type must be an integer!")

        self['@ProductType'] = value

    @property
    def product_code(self) -> str:
        return self['@ProductCode']

    @product_code.setter
    def product_code(self, value: str):
        if not isinstance(int(value), int):
            raise ValueError("Product code must be an integer!")

        self['@ProductCode'] = value

    @property
    def major(self) -> str:
        return self['@Major']

    @major.setter
    def major(self, value: str):
        if not isinstance(int(value), int):
            raise ValueError("Major version must be an integer!")

        self['@Major'] = value

    @property
    def minor(self) -> str:
        return self['@Minor']

    @minor.setter
    def minor(self, value: str):
        if not isinstance(int(value), int):
            raise ValueError("Minor version must be an integer!")

        self['@Minor'] = value

    @property
    def parent_module(self) -> str:
        return self['@ParentModule']

    @property
    def parent_mod_port_id(self) -> str:
        return self['@ParentModPortId']

    @property
    def inhibited(self) -> str:
        return self['@Inhibited']

    @inhibited.setter
    def inhibited(self, value: Union[str, bool]):
        if isinstance(value, bool):
            value = 'true' if value else 'false'

        if not self.is_valid_rockwell_bool(value):
            raise self.InvalidNamingException

        self['@Inhibited'] = value

    @property
    def major_fault(self) -> str:
        return self['@MajorFault']

    @major_fault.setter
    def major_fault(self, value: Union[str, bool]):
        if isinstance(value, bool):
            value = 'true' if value else 'false'

        if not self.is_valid_rockwell_bool(value):
            raise self.InvalidNamingException

        self['@MajorFault'] = value

    @property
    def ekey(self) -> dict:
        return self['EKey']

    @property
    def ports(self) -> list[dict]:
        if not self['Ports']:
            return []

        if not isinstance(self['Ports']['Port'], list):
            return [self['Ports']['Port']]

        return self['Ports']['Port']

    @property
    def communications(self) -> dict:
        if not self['Communications']:
            return None

        return self['Communications']

    def validate(self) -> ControllerReportItem:

        report = ControllerReportItem(self,
                                      f'Validating {self.__class__.__name__} object: {self.name}')

        return report


class Program(ContainsRoutines):
    def __init__(self,
                 meta_data: dict = None,
                 controller: Controller = None):
        """type class for plc Program

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """

        super().__init__(meta_data=meta_data or l5x_dict_from_file(PLC_PROG_FILE)['Program'],
                         controller=controller)

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
    def main_routine(self) -> Optional[Routine]:
        """get the main routine for this program

        .. -------------------------------

        Returns
        ----------
            :class:`Routine`
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

    def validate(self) -> ControllerReportItem:
        report = super().validate()

        if not self.main_routine_name:
            report.test_notes.append('No main routine name found in program!')
            report.pass_fail = False

        return report


class ProgramTag(NamedPlcObject):
    def __init__(self,
                 l5x_meta_data: dict,
                 controller: Controller,
                 program: Optional[Program] = None):
        """type class for plc Program Tag

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """
        super().__init__(meta_data=l5x_meta_data,
                         controller=controller)
        self._program: Optional[Program] = program

    @property
    def program(self) -> Optional[Program]:
        return self._program


class Routine(NamedPlcObject):
    def __init__(self,
                 meta_data: dict = None,
                 controller: Controller = None,
                 program: Optional[Program] = None,
                 aoi: Optional[AddOnInstruction] = None):
        """type class for plc Routine

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """

        super().__init__(meta_data=meta_data or l5x_dict_from_file(PLC_ROUT_FILE)['Routine'],
                         controller=controller)

        self._program: Optional[Program] = program
        self._aoi: Optional[AddOnInstruction] = aoi
        self._instructions: list[LogixInstruction] = []
        self._input_instructions: list[LogixInstruction] = []
        self._output_instructions: list[LogixInstruction] = []
        self._rungs: list[Rung] = []
        self._compile_from_meta_data()

    @property
    def dict_key_order(self) -> list[str]:
        return [
            '@Name',
            '@Type',
            'Description',
            'RLLContent',
        ]

    @property
    def aoi(self) -> Optional[AddOnInstruction]:
        return self._aoi

    @property
    def container(self) -> ContainsRoutines:
        return self.aoi if self.aoi else self.program

    @property
    def input_instructions(self) -> list[LogixInstruction]:
        if self._input_instructions:
            return self._input_instructions
        self._input_instructions = []
        [self._input_instructions.extend(x.input_instructions) for x in self.rungs]
        return self._input_instructions

    @property
    def instructions(self) -> list[LogixInstruction]:
        """get the instructions in this routine

        .. -------------------------------

        Returns
        ----------
            :class:`list[LogixInstruction]`
        """
        if self._instructions:
            return self._instructions
        self._instructions = []
        [self._instructions.extend(x.instructions) for x in self.rungs]
        return self._instructions

    @property
    def output_instructions(self) -> list[LogixInstruction]:
        if self._output_instructions:
            return self._output_instructions
        self._output_instructions = []
        [self._output_instructions.extend(x.output_instructions) for x in self.rungs]
        return self._output_instructions

    @property
    def program(self) -> Optional[Program]:
        return self._program

    @property
    def rungs(self) -> list[Rung]:
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
        [self._rungs.append(self.config.rung_type(meta_data=x,
                                                  controller=self.controller,
                                                  routine=self))
         for x in self.raw_rungs]

    def add_rung(self, rung: Rung):
        """add a rung to this routine

        Args:
            rung (Rung): the rung to add
        """
        if not isinstance(rung, Rung):
            raise ValueError("Rung must be an instance of Rung!")

        rung.number = len(self.rungs)  # auto-increment rung number
        self.raw_rungs.append(rung.meta_data)
        self._compile_from_meta_data()

    def remove_rung(self, rung: Union[Rung, int, str]):
        """remove a rung from this routine

        Args:
            rung (Rung or int): the rung to remove, can be an instance of Rung or its index
        """

        # ideally, the rungs should be a HashList. This should be updated later

        if isinstance(rung, str):
            rung = next((x for x in self.rungs if x.number == rung), None)  # an extra check for out of bound rungs

        if isinstance(rung, int):
            if rung < 0 or rung >= len(self.rungs):
                raise IndexError("Rung index out of range!")
            rung = self.rungs[rung]

        if not isinstance(rung, Rung):
            raise ValueError("Rung must be an instance of Rung!")

        self.raw_rungs.remove(rung.meta_data)
        self._compile_from_meta_data()

    def validate(self) -> ControllerReportItem:
        report = ControllerReportItem(self,
                                      f'Validating {self.__class__.__name__} object: {self.name}')
        if not self.rungs:
            report.test_notes.append('No rungs found in routine!')
            report.pass_fail = False

        for rung in self.rungs:
            rung_report = rung.validate()
            report.pass_fail = report.pass_fail and rung_report.pass_fail
            report.child_reports.append(rung_report)

        return report


class Rung(PlcObject):
    def __init__(self,
                 meta_data: dict = None,
                 controller: Controller = None,
                 routine: Optional[Routine] = None):
        """type class for plc Rung

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """
        super().__init__(meta_data=meta_data or l5x_dict_from_file(PLC_RUNG_FILE)['Rung'],
                         controller=controller)

        self._routine: Optional[Routine] = routine
        self._instructions: list[LogixInstruction] = []
        self._get_instructions()
        self._input_instructions: list[LogixInstruction] = []
        self._output_instructions: list[LogixInstruction] = []

    def __repr__(self):
        return (
            f'Rung(number={self.number}, '
            f'routine={self.routine.name}, '
            f'type={self.type}, '
            f'comment={self.comment}, '
            f'text={self.text}),'
            f'instructions={self.instructions}),'
        )

    def __str__(self):
        return self.text

    @property
    def dict_key_order(self) -> list[str]:
        return [
            '@Number',
            '@Type',
            'Comment',
            'Text'
        ]

    @property
    def comment(self) -> str:
        return self['Comment']

    @comment.setter
    def comment(self, value: str):
        self['Comment'] = value

    @property
    def container(self) -> Routine:
        return self.routine.container

    @property
    def input_instructions(self) -> list[LogixInstruction]:
        if self._input_instructions:
            return self._input_instructions
        self._input_instructions = [x for x in self.instructions if x.type is LogixInstructionType.INPUT]
        return self._input_instructions

    @property
    def instructions(self) -> list[LogixInstruction]:
        return self._instructions

    @property
    def output_instructions(self) -> list[LogixInstruction]:
        if self._output_instructions:
            return self._output_instructions
        self._output_instructions = [x for x in self.instructions if x.type is LogixInstructionType.OUTPUT]
        return self._output_instructions

    @property
    def number(self) -> str:
        return self['@Number']

    @number.setter
    def number(self, value: Union[int, str]):
        if not isinstance(value, (str, int)):
            raise ValueError("Rung number must be a string or int!")

        self['@Number'] = str(value)

    @property
    def routine(self) -> Optional[Routine]:
        return self._routine

    @routine.setter
    def routine(self, value: Routine):
        self._routine = value

    @property
    def text(self) -> str:
        return self['Text']

    @text.setter
    def text(self, value: str):
        self['Text'] = value
        self._instructions = []  # text has changed, we need to reprocess instructions

    @property
    def type(self) -> str:
        return self['@Type']

    def _get_instructions(self):
        matches = re.findall(INST_RE_PATTERN, self.text)
        if not matches:
            return []

        self._instructions = [LogixInstruction(x, self, self.controller) for x in matches]

    def validate(self) -> ControllerReportItem:
        report = ControllerReportItem(self,
                                      f'Validating {self.__class__.__name__} object: {self.meta_data}')
        if not self.instructions:
            report.test_notes.append('No instructions found in rung!')
            report.pass_fail = False

        return report


class TagEndpoint(PlcObject):
    def __init__(self,
                 meta_data: str,
                 controller: Controller,
                 parent_tag: 'Tag'):
        super().__init__(meta_data=meta_data,
                         name=meta_data,
                         controller=controller)
        self._parent_tag: 'Tag' = parent_tag

    @property
    def name(self) -> str:
        """get the name of this tag endpoint

        Returns:
            :class:`str`: name of this tag endpoint
        """
        return self._meta_data


class Tag(NamedPlcObject):
    def __init__(self,
                 container: Union[Program, AddOnInstruction, Controller] = None,
                 **kwargs):
        """type class for plc Tag

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """

        super().__init__(default_loader=lambda: l5x_dict_from_file(PLC_TAG_FILE)['Tag'],
                         **kwargs)
        self._container = container

    @property
    def dict_key_order(self) -> list[str]:
        return [
            '@Name',
            '@Class',
            '@TagType',
            '@DataType',
            '@Radix',
            '@AliasFor',
            '@Constant',
            '@ExternalAccess',
            'Description',
            'Data',
        ]

    @property
    def alias_for(self) -> str:
        return self._meta_data.get('@AliasFor', None)

    @property
    def alias_for_base_name(self) -> str:
        """get the base name of the aliased tag

        .. -------------------------------

        Returns
        ----------
            :class:`str`
        """
        if not self.alias_for:
            return None

        return self.alias_for.split('.')[0].split(':')[0]

    @property
    def class_(self) -> str:
        return self['@Class']

    @property
    def constant(self) -> str:
        return self['@Constant']

    @constant.setter
    def constant(self, value: Union[str, bool]):
        if isinstance(value, bool):
            value = 'true' if value else 'false'

        if not self.is_valid_rockwell_bool(value):
            raise self.InvalidNamingException

        self['@Constant'] = value

    @property
    def container(self) -> Optional[Union[Program, AddOnInstruction, Controller]]:
        return self._container

    @property
    def data(self) -> list[dict]:
        if not isinstance(self['Data'], list):
            return [self['Data']]

        return self['Data']

    @property
    def datatype(self) -> str:
        return self['@DataType']

    @datatype.setter
    def datatype(self, value: str):
        if not isinstance(value, str):
            raise ValueError("Datatype must be a string!")

        if value not in self.controller.datatypes:
            raise ValueError(f"Datatype {value} not found in controller datatypes!")

        self['@DataType'] = value
        self['Data'] = []

    @property
    def datavalue_members(self) -> list[DataValueMember]:
        if not self.decorated_data:
            return []

        if not self.decorated_data.get('Structure', None):
            return []

        if not self.decorated_data['Structure'].get('DataValueMember', None):
            return []

        return [DataValueMember(l5x_meta_data=x,
                                controller=self.controller,
                                parent=self)
                for x in self.decorated_data['Structure']['DataValueMember']]

    @property
    def decorated_data(self) -> dict:
        return next((x for x in self.data if x and x['@Format'] == 'Decorated'), None)

    @property
    def endpoint_operands(self) -> list[str]:
        """get the endpoint operands for this tag

        Returns:
            :class:`list[str]`: list of endpoint operands
        """
        if not self.datatype:
            return []

        datatype = self.controller.datatypes.get(self.datatype, None)
        if not datatype:
            self.logger.warning(f"Datatype {self.datatype} not found for tag {self.name}.")
            return []

        endpoints = datatype.endpoint_operands
        if not endpoints:
            self.logger.warning(f"No endpoint operands found for datatype {self.datatype} in tag {self.name}.")
            return []

        return [TagEndpoint(meta_data=f'{self.name}{x}',
                            controller=self.controller,
                            parent_tag=self) for x in endpoints]

    @property
    def external_access(self) -> str:
        return self['@ExternalAccess']

    @external_access.setter
    def external_access(self, value: str):
        if not isinstance(value, str):
            raise ValueError("External access must be a string!")

        if value not in ['None', 'ReadOnly', 'Read/Write']:
            raise ValueError("External access must be one of: None, ReadOnly, Read/Write!")

        self['@ExternalAccess'] = value

    @property
    def l5k_data(self) -> dict:
        return next((x for x in self.data if x and x['@Format'] == 'L5K'), None)

    @property
    def opc_ua_access(self) -> str:
        return self['@OpcUaAccess']

    @property
    def scope(self) -> LogixTagScope:
        if isinstance(self.container, Controller):
            return LogixTagScope.CONTROLLER
        elif isinstance(self.container, Program) or isinstance(self.container, AddOnInstruction):
            return LogixTagScope.PROGRAM
        else:
            raise ValueError('Unknown tag scope!')

    @property
    def tag_type(self) -> str:
        return self['@TagType']

    @tag_type.setter
    def tag_type(self, value: str):
        if not isinstance(value, str):
            raise ValueError("Tag type must be a string!")

        if value not in ['Base', 'Structure', 'Array']:
            raise ValueError("Tag type must be one of: Atomic, Structure, Array!")

        self['@TagType'] = value

    def get_alias_string(self,
                         additional_elements: str = None) -> str:
        """get the alias string for this tag

        .. -------------------------------

        Returns
        ----------
            :class:`str`
        """
        if not additional_elements:
            additional_elements = ''

        if not self.alias_for:
            return f'{self.name}{additional_elements}'

        parent_tag = self.get_parent_tag(self)
        if not parent_tag:
            return f'{self.alias_for}{additional_elements}'

        alias_element_pointer = self.alias_for.find('.')
        if alias_element_pointer != -1:
            additional_elements = f'{self.alias_for[alias_element_pointer:]}{additional_elements}'

        return parent_tag.get_alias_string(additional_elements=additional_elements)

    def get_base_tag(self,
                     tracked_tag: Self = None):
        tag = self if not tracked_tag else tracked_tag

        if not tag.alias_for:
            return tag

        alias = tag.get_parent_tag(tag)

        if not alias:
            return tag

        if alias.alias_for:
            return self.get_base_tag(tracked_tag=alias)
        else:
            return alias

    @staticmethod
    def get_parent_tag(tag: Self):
        if not tag.alias_for:
            return None

        alias = None

        if tag.container:
            alias: Self = tag.container.tags.get(tag.alias_for_base_name, None)

        if not alias:
            alias: Self = tag.controller.tags.get(tag.alias_for_base_name, None)

        return alias

    def validate(self):
        report = ControllerReportItem(self,
                                      f'Validating {self.__class__.__name__} object: {self.name}')
        return report


class DataValueMember(NamedPlcObject):
    """type class for plc Tag DataValueMember

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """

    def __init__(self,
                 name: str = None,
                 l5x_meta_data: dict = None,
                 controller: 'Controller' = None,
                 parent: Union[Tag, Self] = None):

        if not l5x_meta_data:
            raise ValueError('Cannot have an empty DataValueMember!')

        if not parent:
            raise ValueError('Cannot have a datavalue member without a parent!')

        super().__init__(meta_data=l5x_meta_data,
                         controller=controller)

        self._parent = parent

        if name:
            self.name = name

    @property
    def parent(self) -> Union[Tag, Self]:
        return self._parent


@dataclass
class ControllerConfiguration:
    aoi_type: type = AddOnInstruction
    datatype_type: type = Datatype
    module_type: type = Module
    program_type: type = Program
    routine_type: type = Routine
    rung_type: type = Rung
    tag_type: type = Tag


class Controller(NamedPlcObject, Loggable):
    """Controller container for Allen Bradley L5X Files.
    .. ------------------------------------------------------------

    .. package:: emulation_preparation.types.plc

    .. ------------------------------------------------------------

        """

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if key == '@MajorRev' or key == '@MinorRev':
            self.logger.info('Changing revisions of processor...')
            self.content_meta_data['@SoftwareRevision'] = f'{self.controller.major_revision}.{self.controller.minor_revision}'
            self.plc_module['@Major'] = self.major_revision
            self.plc_module['@Minor'] = self.minor_revision

    def __init__(self,
                 root_meta_data: str = None,
                 config: Optional[ControllerConfiguration] = None,
                 **kwargs):

        self._root_meta_data: dict = root_meta_data or l5x_dict_from_file(PLC_ROOT_FILE)
        self._file_location, self._ip_address, self._slot = '', '', 0
        self._config = config if config else ControllerConfiguration()

        NamedPlcObject.__init__(self,
                                meta_data=self.l5x_meta_data,
                                controller=self,
                                **kwargs)
        Loggable.__init__(self)
        self._aois: HashList
        self._datatypes: HashList
        self._modules: HashList
        self._programs: HashList
        self._tags: HashList
        self._compile_from_meta_data()

    @property
    def aois(self) -> HashList[AddOnInstruction]:
        return self._aois

    @property
    def raw_aois(self) -> list[dict]:
        if not self['AddOnInstructionDefinitions']:
            self['AddOnInstructionDefinitions'] = {'AddOnInstructionDefinition': []}
        if not isinstance(self['AddOnInstructionDefinitions']['AddOnInstructionDefinition'], list):
            self['AddOnInstructionDefinitions']['AddOnInstructionDefinition'] = [
                self['AddOnInstructionDefinitions']['AddOnInstructionDefinition']]
        return self['AddOnInstructionDefinitions']['AddOnInstructionDefinition']

    @property
    def comm_path(self) -> str:
        return self['@CommPath']

    @comm_path.setter
    def comm_path(self, value: str):
        if not isinstance(value, str):
            raise ValueError('CommPath must be a string!')
        self['@CommPath'] = value

    @property
    def content_meta_data(self) -> dict:
        return self.root_meta_data['RSLogix5000Content']

    @property
    def datatypes(self) -> HashList[Datatype]:
        return self._datatypes

    @property
    def raw_datatypes(self) -> list[dict]:

        if not self['DataTypes']:
            self['DataTypes'] = {'DataType': []}
        if not isinstance(self['DataTypes']['DataType'], list):
            self['DataTypes']['DataType'] = [self['DataTypes']['DataType']]
        return self['DataTypes']['DataType']

    @property
    def file_location(self) -> str:

        return self._file_location

    @file_location.setter
    def file_location(self,
                      value: str):
        self._file_location = value

    @property
    def input_instructions(self) -> list[LogixInstruction]:
        instr = []
        [instr.extend(x.input_instructions) for x in self.programs]
        return instr

    @property
    def instructions(self) -> list[LogixInstruction]:
        """get the instructions in this controller

        .. -------------------------------

        Returns
        ----------
            :class:`list[LogixInstruction]`
        """
        instr = []
        [instr.extend(x.instructions) for x in self.programs]
        # [instr.extend(x.instructions) for x in self.aois]
        return instr

    @property
    def output_instructions(self) -> list[LogixInstruction]:
        instr = []
        [instr.extend(x.output_instructions) for x in self.programs]
        return instr

    @property
    def l5x_meta_data(self) -> dict:
        return self.content_meta_data['Controller']

    @l5x_meta_data.setter
    def l5x_meta_data(self, value) -> None:
        self.content_meta_data['Controller'] = value

    @property
    def major_revision(self) -> int:
        return int(self['@MajorRev'])

    @major_revision.setter
    def major_revision(self, value: int):
        self['@MajorRev'] = int(value)

    @property
    def minor_revision(self) -> int:
        return int(self['@MinorRev'])

    @minor_revision.setter
    def minor_revision(self, value: int):
        self['@MinorRev'] = int(value)

    @property
    def modules(self) -> HashList[Module]:
        return self._modules

    @property
    def raw_modules(self) -> list[dict]:
        if not self['Modules']:
            self['Modules'] = {'Module': []}
        if not isinstance(self['Modules']['Module'], list):
            self['Modules']['Module'] = [self['Modules']['Module']]
        return self['Modules']['Module']

    @property
    def plc_module(self) -> dict:
        return next((x for x in self.raw_modules if x['@Name'] == 'Local'), None)

    @property
    def plc_module_icp_port(self) -> dict:
        return next((x for x in self.plc_module_ports if x['@Type'] == 'ICP' or x['@Type'] == '5069'), None)

    @property
    def plc_module_ports(self) -> list[dict]:
        if not self.plc_module:
            return []

        if not isinstance(self.plc_module['Ports']['Port'], list):
            return [self.plc_module['Ports']['Port']]
        return self.plc_module['Ports']['Port']

    @property
    def programs(self) -> HashList[Program]:
        return self._programs

    @property
    def raw_programs(self) -> list[dict]:
        if not self['Programs']:
            self['Programs'] = {'Program': []}
        if not isinstance(self['Programs']['Program'], list):
            self['Programs']['Program'] = [self['Programs']['Program']]
        return self['Programs']['Program']

    @property
    def root_meta_data(self) -> dict:
        return self._root_meta_data

    @property
    def slot(self) -> int:
        if not self.plc_module_icp_port:
            return None
        return int(self.plc_module_icp_port['@Address'])

    @slot.setter
    def slot(self,
             value: int):
        self._slot = int(value)

    @property
    def tags(self) -> HashList[Tag]:
        return self._tags

    @property
    def raw_tags(self) -> list[dict]:
        if not self['Tags']:
            self['Tags'] = {'Tag': []}
        if not isinstance(self['Tags']['Tag'], list):
            self['Tags']['Tag'] = [self['Tags']['Tag']]
        return self['Tags']['Tag']

    @raw_tags.setter
    def raw_tags(self,
                 value: dict):
        if value is None:
            raise ValueError('Tags cannot be None!')
        if not isinstance(value, dict) and not isinstance(value, list):
            raise ValueError('Tags must be a dictionary or a list!')

        if isinstance(value, dict):
            self['Tags'] = value
        elif isinstance(value, list):
            self['Tags']['Tag'] = value

    @classmethod
    def from_file(cls: Self,
                  file_location: str) -> Optional[Self]:
        root_data = l5x_dict_from_file(file_location)
        if not root_data:
            return None

        return cls(root_data)

    def _compile_atomic_datatypes(self) -> None:
        """Compile atomic datatypes from the controller's datatypes."""
        self.datatypes.append(Datatype(meta_data={'@Name': 'BOOL'}, controller=self))
        self.datatypes.append(Datatype(meta_data={'@Name': 'BIT'}, controller=self))
        self.datatypes.append(Datatype(meta_data={'@Name': 'SINT'}, controller=self))
        self.datatypes.append(Datatype(meta_data={'@Name': 'INT'}, controller=self))
        self.datatypes.append(Datatype(meta_data={'@Name': 'DINT'}, controller=self))
        self.datatypes.append(Datatype(meta_data={'@Name': 'LINT'}, controller=self))
        self.datatypes.append(Datatype(meta_data={'@Name': 'USINT'}, controller=self))
        self.datatypes.append(Datatype(meta_data={'@Name': 'UINT'}, controller=self))
        self.datatypes.append(Datatype(meta_data={'@Name': 'UDINT'}, controller=self))
        self.datatypes.append(Datatype(meta_data={'@Name': 'ULINT'}, controller=self))
        self.datatypes.append(Datatype(meta_data={'@Name': 'REAL'}, controller=self))
        self.datatypes.append(Datatype(meta_data={'@Name': 'LREAL'}, controller=self))
        self.datatypes.append(Datatype(meta_data={'@Name': 'STRING'}, controller=self))
        self.datatypes.append(Datatype(meta_data={'@Name': 'TIMER',
                                                  'Members': {'Member': [
                                                      {'@Name': 'PRE'},
                                                      {'@Name': 'ACC'},
                                                      {'@Name': 'EN'},
                                                      {'@Name': 'TT'},
                                                      {'@Name': 'DN'}
                                                  ]}}, controller=self))

    def _compile_from_meta_data(self):
        """Compile this controller from its meta data."""
        self._aois = HashList('name')
        [self._aois.append(self.config.aoi_type(meta_data=x, controller=self))
         for x in self.raw_aois]

        self._datatypes = HashList('name')
        self._compile_atomic_datatypes()
        [self._datatypes.append(self.config.datatype_type(meta_data=x, controller=self))
         for x in self.raw_datatypes]

        self._modules = HashList('name')
        [self._modules.append(self.config.module_type(l5x_meta_data=x, controller=self))
         for x in self.raw_modules]

        self._programs = HashList('name')
        [self._programs.append(self.config.program_type(meta_data=x, controller=self))
         for x in self.raw_programs]

        self._tags = HashList('name')
        [self._tags.append(self.config.tag_type(meta_data=x, controller=self, container=self))
         for x in self.raw_tags]

    def _assign_address(self,
                        address: str):
        octets = address.split('.')
        if not octets or len(octets) != 4:
            raise ValueError('IP Octets invalid!')

        for _, v in enumerate(octets):
            if 0 > int(v) > 255:
                raise ValueError(f'IP address octet range ivalid: {v}')

        self._ip_address = address

    def _add_common(self,
                    item: NamedPlcObject,
                    item_class: type,
                    target_list: HashList,
                    target_meta_list: list[dict]):

        if not isinstance(item, item_class):
            raise TypeError(f"{item.name} must be of type {item_class}!")

        if item.name in target_list:
            raise ValueError(f"{item_class} with name {item.name} already exists in this list!")

        target_meta_list.append(item.meta_data)

    def _remove_common(self,
                       plcobject: PlcObject,
                       target_list: list):
        if plcobject in target_list:
            target_list.remove(plcobject)

    def add_aoi(self,
                aoi: AddOnInstruction,
                skip_compile: Optional[bool] = False):
        """Add an AOI to this controller.
        .. -------------------------------
        .. arguments::
        :class:`AddOnInstruction` aoi:
            the AOI to add
        :class:`bool` skip_compile:
            If True, skip the compilation step after adding the AOI.
        """
        self._add_common(aoi,
                         self._config.aoi_type,
                         self._aois,
                         self.raw_aois)
        if not skip_compile:
            self._compile_from_meta_data()

    def add_datatype(self,
                     datatype: Datatype,
                     skip_compile: Optional[bool] = False):
        """Add a datatype to this controller.
        .. -------------------------------
        .. arguments::
        :class:`Datatype` datatype:
            the datatype to add
        :class:`bool` skip_compile:
            If True, skip the compilation step after adding the datatype.
        """
        self._add_common(datatype,
                         self._config.datatype_type,
                         self._datatypes,
                         self.raw_datatypes)
        if not skip_compile:
            self._compile_from_meta_data()

    def add_module(self,
                   module: Module,
                   skip_compile: Optional[bool] = False):
        """Add a module to this controller.
        .. -------------------------------
        .. arguments::
        :class:`Module` module:
            the module to add
        :class:`bool` skip_compile:
            If True, skip the compilation step after adding the module.
        """
        self._add_common(module,
                         self._config.module_type,
                         self._modules,
                         self.raw_modules)
        if not skip_compile:
            self._compile_from_meta_data()

    def add_program(self,
                    program: Program,
                    skip_compile: Optional[bool] = False):
        """Add a program to this controller.
        .. -------------------------------
        .. arguments::
        :class:`Program` program:
            the program to add
        :class:`bool` skip_compile:
            If True, skip the compilation step after adding the program.
        """
        self._add_common(program,
                         self._config.program_type,
                         self._programs,
                         self.raw_programs)
        if not skip_compile:
            self._compile_from_meta_data()

    def add_tag(self,
                tag: Tag,
                skip_compile: Optional[bool] = False):
        """Add a tag to this controller.
        .. -------------------------------
        .. arguments::
        :class:`Tag` tag:
            the tag to add
        :class:`bool` skip_compile:
            If True, skip the compilation step after adding the tag.
        """
        self._add_common(tag,
                         self._config.tag_type,
                         self._tags,
                         self.raw_tags)
        if not skip_compile:
            self._compile_from_meta_data()

    def remove_aoi(self, aoi: AddOnInstruction):
        self._remove_common(aoi, self._aois)

    def remove_datatype(self, datatype: Datatype):
        self._remove_common(datatype, self._datatypes)

    def remove_module(self, module: Module):
        self._remove_common(module, self._modules)

    def remove_program(self, program: Program):
        self._remove_common(program, self._programs)

    def remove_tag(self, tag: Tag):
        self._remove_common(tag, self._tags)

    def find_diagnostic_rungs(self) -> list[Rung]:
        diagnostic_rungs = []

        for program in self.programs:
            for routine in program.routines:
                for rung in routine.rungs:
                    if rung.comment is not None and '<@DIAG>' in rung.comment:
                        diagnostic_rungs.append(rung)
                    else:
                        for instruction in rung.instructions:
                            if 'JSR' in instruction and 'zZ999_Diagnostics' in instruction:
                                diagnostic_rungs.append(rung)
                                break

        return diagnostic_rungs

    def find_unpaired_controller_inputs(self):
        self.logger.info('Finding unpaired controller inputs...')
        inputs = defaultdict(list)
        outputs = set()

        # Collect all input and output operands
        for instr in self.input_instructions:
            for operand in instr.operands:
                inputs[operand.as_qualified].append(operand)
        for instr in self.output_instructions:
            for operand in instr.operands:
                outputs.add(operand.as_qualified)

        unpaired_inputs = {}

        for key, value in inputs.items():
            if key not in outputs:
                # Use set intersection for fast check
                qualified_parents = set(value[0].qualified_parents)
                if qualified_parents.isdisjoint(outputs):
                    unpaired_inputs[key] = [x.as_report_dict() for x in value]

        # Remove common hardware flags
        for key in ['S:FS', 'S:Fs', 'S:fs', 's:fs', 's:FS']:
            unpaired_inputs.pop(key, None)

        return unpaired_inputs

    def find_redundant_otes(self):
        self.logger.info('Finding redundant OTEs...')
        outputs = defaultdict(list)

        for inst in [x for x in self.output_instructions if x.instruction_name == 'OTE']:
            outputs[inst.qualified_meta_data].append(inst.as_report_dict())

        shallow_outputs = outputs.copy()

        for key, value in shallow_outputs.items():
            if len(value) < 2:
                del outputs[key]

        return outputs

    def rename_asset(self,
                     element_type: LogixAssetType,
                     name: str,
                     replace_name: str):
        if not element_type or not name or not replace_name:
            return

        match element_type:
            case LogixAssetType.TAG:
                self.raw_tags = replace_strings_in_dict(
                    self.raw_tags, name, replace_name)

            case LogixAssetType.ALL:
                self.l5x_meta_data = replace_strings_in_dict(
                    self.l5x_meta_data, name, replace_name)

            case _:
                return

    def verify(self) -> dict:
        return {
            'ControllerReport': ControllerReport(self).run().as_dictionary(),
            'UnpairedControllerInputs': self.find_unpaired_controller_inputs(),
            'RedundantOutputs': self.find_redundant_otes(),
        }


class ControllerReportItem:
    def __init__(self,
                 plc_object: PlcObject,
                 test_description: str,
                 pass_fail: bool = True,
                 test_notes: list[str] = None):
        if plc_object is None or test_description is None:
            raise ValueError('Cannot leave any fields empty/None!')
        self._plc_object: PlcObject = plc_object
        self._test_description: str = test_description
        self._pass_fail: bool = pass_fail
        self._test_notes: list[str] = test_notes if test_notes is not None else []
        self._child_reports: list['ControllerReportItem'] = []

    @property
    def child_reports(self) -> list['ControllerReportItem']:
        return self._child_reports

    @child_reports.setter
    def child_reports(self, value: list['ControllerReportItem']):
        if not isinstance(value, list):
            raise ValueError('Child reports must be a list!')
        self._child_reports = value

    @property
    def plc_object(self) -> PlcObject:
        return self._plc_object

    @property
    def test_description(self) -> str:
        return self._test_description

    @test_description.setter
    def test_description(self, value: str):
        if not isinstance(value, str):
            raise ValueError('Test description must be a string!')
        self._test_description = value

    @property
    def pass_fail(self) -> bool:
        return self._pass_fail

    @pass_fail.setter
    def pass_fail(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError('Pass/Fail must be a boolean value!')
        self._pass_fail = value

    @property
    def test_notes(self) -> list[str]:
        return self._test_notes

    @test_notes.setter
    def test_notes(self, value: list[str]):
        if not isinstance(value, list):
            raise ValueError('Test notes must be a list!')
        self._test_notes = value

    def as_dictionary(self) -> dict:
        """Get the report item as a dictionary.

        Returns
        -------
            :class:`dict`
        """
        name = str(self.plc_object.name) if hasattr(self.plc_object, 'name') else str(self.plc_object.meta_data)
        name += ' [%s]' % self.plc_object.__class__.__name__

        return {
            'Name': name,
            'PLC Object': self.plc_object.meta_data,
            'Test Description': self.test_description,
            'Pass?': self.pass_fail,
            'Test Notes': self.test_notes,
            'Child Reports': [x.as_dictionary() for x in self.child_reports]
        }


class ControllerReport(Loggable):
    """Controller status report

    Get detailed information about a controller, showing problem areas, etc.
    """

    def __init__(self,
                 controller: Controller):
        super().__init__()
        self._controller: Controller = controller
        self._report_items: list[ControllerReportItem] = []

    @property
    def report_items(self) -> list[ControllerReportItem]:
        return self._report_items

    @property
    def categorized_items(self) -> dict[list[ControllerReportItem]]:
        return self._as_categorized()

    def _check_controller(self):
        self.logger.info('Checking controller...')

        # comm path
        self.logger.info('Comms path...')
        good = True if self._controller.comm_path != '' else False
        if good:
            self.logger.info('ok... -> %s' % str(self._controller.comm_path))
        else:
            self.logger.error('error!')

        # slot
        self.logger.info('Slot...')
        good = True if self._controller.slot is not None else False
        if good:
            self.logger.info('ok... -> %s' % str(self._controller.slot))
        else:
            self.logger.error('error!')

        # plc module
        self.logger.info('PLC Module...')
        good = True if self._controller.plc_module else False
        if good:
            self.logger.info('ok... -> %s' % str(self._controller.plc_module['@Name']))
        else:
            self.logger.error('error!')

    def _check_common(self, plc_objects: list[PlcObject]):

        if not isinstance(plc_objects, list) and not isinstance(plc_objects, HashList):
            raise ValueError

        [self.report_items.append(plc_object.validate()) for plc_object in plc_objects]

    def _as_categorized(self) -> dict[list[ControllerReportItem]]:
        categories = {}
        for report in self._report_items:
            if report.plc_object.__class__.__name__ not in categories:
                categories[report.plc_object.__class__.__name__] = []
            categories[report.plc_object.__class__.__name__].append(report.as_dictionary())
        return categories

    def as_dictionary(self) -> dict:
        """Get the report as a dictionary.

        Returns
        -------
            :class:`dict`
        """
        self.logger.info('Converting report to dictionary...')
        report = {
            'controller': self._controller.l5x_meta_data,
            'report_items': [x.as_dictionary() for x in self._report_items],
            'categorized_items': self.categorized_items
        }
        return report

    def run(self) -> Self:
        self.logger.info('Starting report...')
        self.logger.info('Checking controller attributes...')
        self._check_controller()
        self.logger.info('Checking modules...')
        self._check_common(self._controller.modules)
        self.logger.info('Checking datatypes...')
        self._check_common(self._controller.datatypes)
        self.logger.info('Checking add on instructions...')
        self._check_common(self._controller.aois)
        self.logger.info('Checking tags...')
        self._check_common(self._controller.tags)
        self.logger.info('Checking programs...')
        self._check_common(self._controller.programs)
        self.logger.info('Finalizing report...')
        return self

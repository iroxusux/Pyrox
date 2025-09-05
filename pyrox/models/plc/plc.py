"""PLC type module for Pyrox framework."""
from __future__ import annotations

from abc import abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
import fnmatch
from pathlib import Path
import re
from typing import (
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Self,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from ..abc.meta import EnforcesNaming, Loggable, PyroxObject, NamedPyroxObject, FactoryTypeMeta, MetaFactory
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
    'ControllerFactory',
    'ControllerModificationSchema',
    'ControllerSafetyInfo',
    'Datatype',
    'DatatypeMember',
    'DataValueMember',
    'EmulationGenerator',
    'EmulationGeneratorFactory',
    'IntrospectiveModule',
    'Module',
    'ModuleControlsType',
    'ModuleVendorFactory',
    'ModuleWarehouse',
    'ModuleWarehouseFactory',
    'Program',
    'Routine',
    'Rung',
    'Tag',
    'TagEndpoint',
)


T = TypeVar('T')
CTRL = TypeVar('CTRL', bound='Controller')

INST_RE_PATTERN: str = r'[A-Za-z0-9_]+\(\S*?\)'
INST_TYPE_RE_PATTERN: str = r'([A-Za-z0-9_]+)(?:\(.*?)(?:\))'
INST_OPER_RE_PATTERN: str = r'(?:[A-Za-z0-9_]+\()(.*?)(?:\))'

PLC_ROOT_FILE = Path(__file__).resolve().parents[3] / 'docs' / 'controls' / 'root.L5X'
PLC_PROG_FILE = Path(__file__).resolve().parents[3] / 'docs' / 'controls' / '_program.L5X'
PLC_ROUT_FILE = Path(__file__).resolve().parents[3] / 'docs' / 'controls' / '_routine.L5X'
PLC_DT_FILE = Path(__file__).resolve().parents[3] / 'docs' / 'controls' / '_datatype.L5X'
PLC_AOI_FILE = Path(__file__).resolve().parents[3] / 'docs' / 'controls' / '_aoi.L5X'
PLC_MOD_FILE = Path(__file__).resolve().parents[3] / 'docs' / 'controls' / '_module.L5X'
PLC_RUNG_FILE = Path(__file__).resolve().parents[3] / 'docs' / 'controls' / '_rung.L5X'
PLC_TAG_FILE = Path(__file__).resolve().parents[3] / 'docs' / 'controls' / '_tag.L5X'

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


# ------------------ Atomic Datatypes ------------------------- #
# Atomic datatypes in Logix that are not explicitly defined by the xml formatting file.
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

INPUT_INSTRUCTIONS = [
    INSTR_XIC,
    INSTR_XIO
]

XIC_OPERAND_RE_PATTERN = r"(?:XIC\()(.*)(?:\))"
XIO_OPERAND_RE_PATTERN = r"(?:XIO\()(.*)(?:\))"

INPUT_INSTRUCTIONS_RE_PATTER = [
    XIC_OPERAND_RE_PATTERN,
    XIO_OPERAND_RE_PATTERN
]

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

OUTPUT_INSTRUCTIONS = [
    INSTR_OTE,
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
    ISNTR_CPS
]

OTE_OPERAND_RE_PATTERN = r"(?:OTE\()(.*?)(?:\))"
OTL_OPERAND_RE_PATTERN = r"(?:OTL\()(.*?)(?:\))"
OTU_OPERAND_RE_PATTERN = r"(?:OTU\()(.*?)(?:\))"
MOV_OPERAND_RE_PATTERN = r"(?:MOV\()(.*?)(?:\))"
MOVE_OPERAND_RE_PATTERN = r"(?:MOVE\()(.*?)(?:\))"
COP_OPERAND_RE_PATTERN = r"(?:COP\()(.*?)(?:\))"
CPS_OPERAND_RE_PATTERN = r"(?:CPS\()(.*?)(?:\))"

OUTPUT_INSTRUCTIONS_RE_PATTERN = [
    OTE_OPERAND_RE_PATTERN,
    OTL_OPERAND_RE_PATTERN,
    OTU_OPERAND_RE_PATTERN,
    MOV_OPERAND_RE_PATTERN,
    MOVE_OPERAND_RE_PATTERN,
    COP_OPERAND_RE_PATTERN,
    CPS_OPERAND_RE_PATTERN
]

# ------------------ Special Instructions ----------------------- #
# Special instructions not known to be input or output instructions
INSTR_JSR = 'JSR'

# ------------------- Logix Assets ------------------------------ #
# Hardcoded asset types for L5X files
L5X_ASSET_DATATYPES = 'DataTypes'
L5X_ASSET_TAGS = 'Tags'
L5X_ASSET_PROGRAMS = 'Programs'
L5X_ASSET_ADDONINSTRUCTIONDEFINITIONS = 'AddOnInstructionDefinitions'
L5X_ASSET_MODULES = 'Modules'

L5X_ASSETS = [
    L5X_ASSET_DATATYPES,
    L5X_ASSET_TAGS,
    L5X_ASSET_PROGRAMS,
    L5X_ASSET_ADDONINSTRUCTIONDEFINITIONS,
    L5X_ASSET_MODULES
]

# ------------------- L5X Common Properties --------------------- #
# Common properties found in L5X files
L5X_PROP_NAME = '@Name'
L5X_PROP_DESCRIPTION = 'Description'

# ------------------- CIP Types --------------------------------- #
# CIP Type format: Type ID: (Size in bytes, Type Name, Struct Format)
CIPTypes = {0x00: (1, "UNKNOWN", '<B'),
            0xa0: (88, "STRUCT", '<B'),
            0xc0: (8, "DT", '<Q'),
            0xc1: (1, "BOOL", '<?'),
            0xc2: (1, "SINT", '<b'),
            0xc3: (2, "INT", '<h'),
            0xc4: (4, "DINT", '<i'),
            0xc5: (8, "LINT", '<q'),
            0xc6: (1, "USINT", '<B'),
            0xc7: (2, "UINT", '<H'),
            0xc8: (4, "UDINT", '<I'),
            0xc9: (8, "LWORD", '<Q'),
            0xca: (4, "REAL", '<f'),
            0xcc: (8, "LDT", '<Q'),
            0xcb: (8, "LREAL", '<d'),
            0xd0: (1, "O_STRING", '<B'),
            0xd1: (1, "BYTE", "<B"),
            0xd2: (2, "WORD", "<I"),
            0xd3: (4, "DWORD", '<i'),
            0xd6: (4, "TIME32", '<I'),
            0xd7: (8, "TIME", '<Q'),
            0xda: (1, "STRING", '<B'),
            0xdf: (8, "LTIME", '<Q')}


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
    JSR = 4


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


class PlcObject(EnforcesNaming, PyroxObject, Generic[CTRL]):
    """Base class for a L5X PLC object.

    Args:
        controller: The controller this object belongs to.
        default_loader: Default loader function for metadata.
        meta_data: Metadata for this object.

    Attributes:
        meta_data: The metadata dictionary or string for this object.
        controller: The controller this object belongs to.
        on_compiled: List of functions to call when object is compiled.
        on_compiling: List of functions to call when object is compiling.
    """

    def __getitem__(
        self,
        key
    ) -> Union[str, dict, None]:
        """Get item from metadata.

        Args:
            key: The key to retrieve.

        Returns:
            Union[str, dict, None]: The value associated with the key, or None if not found.

        Raises:
            TypeError: If metadata is not a dictionary.
        """
        if isinstance(self.meta_data, dict):
            return self._meta_data.get(key, None)
        else:
            raise TypeError("Meta data must be a dict!")

    def __init__(
        self,
        controller: Optional[CTRL] = None,
        default_loader: Callable = lambda: defaultdict(None),
        meta_data: Union[dict, str] = defaultdict(None)
    ) -> None:
        self.meta_data = meta_data or default_loader()
        self.controller = controller

        self._on_compiling: list[Callable] = []
        self._on_compiled: list[Callable] = []
        self._init_dict_order()
        super().__init__()

    def __repr__(self) -> str:
        return str(self)

    def __setitem__(
        self,
        key,
        value
    ) -> None:
        """Set item in metadata.

        Args:
            key: The key to set.
            value: The value to set.

        Raises:
            TypeError: If metadata is not a dictionary.
        """
        if isinstance(self.meta_data, dict):
            self._meta_data[key] = value
        else:
            raise TypeError("Cannot set item on a non-dict meta data object!")

    def __str__(self) -> str:
        return str(self.meta_data)

    @property
    def dict_key_order(self) -> list[str]:
        """Get the order of keys in the metadata dict.

        This is intended to be overridden by subclasses to provide a specific order of keys.

        Returns:
            list[str]: List of keys in preferred order.
        """
        return []

    @property
    def config(self) -> Optional['ControllerConfiguration']:
        """Get the controller configuration for this object.

        Returns:
            ControllerConfiguration: The controller configuration, or default if no controller.
        """
        return ControllerConfiguration() if not self._controller else self._controller._config

    @property
    def controller(self) -> Optional[CTRL]:
        """Get this object's controller.

        Returns:
            Controller: The controller this object belongs to.
        """
        return self._controller

    @controller.setter
    def controller(self, value: Optional[CTRL]):
        """Set this object's controller.

        Args:
            value: The controller to set.

        Raises:
            TypeError: If controller is not of type Controller or None.
        """
        if value is None or isinstance(value, Controller):
            self._controller = value
        else:
            raise TypeError(f"Controller must be of type {CTRL} or None!")

    @property
    def meta_data(self) -> Union[dict, str]:
        """Get the metadata for this object.

        Returns:
            Union[dict, str]: The metadata.
        """
        return self._meta_data

    @meta_data.setter
    def meta_data(self, value: Union[dict, str]):
        """Set the metadata for this object.

        Args:
            value: The metadata to set.

        Raises:
            TypeError: If metadata is not a dict or string.
        """
        if isinstance(value, (dict, str)):
            self._meta_data = value
        else:
            raise TypeError("Meta data must be a dict or a string!")

    @property
    def on_compiled(self) -> list[Callable]:
        """Get the list of functions to call when this object is compiled.

        Returns:
            list[Callable]: List of callback functions.
        """
        return self._on_compiled

    @property
    def on_compiling(self) -> list[Callable]:
        """Get the list of functions to call when this object is compiling.

        Returns:
            list[Callable]: List of callback functions.
        """
        return self._on_compiling

    def _compile_from_meta_data(self):
        """Compile this object from its metadata.

        This method should be overridden by subclasses to provide specific compilation logic.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError("This method should be overridden by subclasses to compile from meta data.")

    def _init_dict_order(self):
        """Initialize the dict order for this object.

        This method relies on the child classes to define their own dict_key_order property.
        """
        if not self.dict_key_order:
            return

        if isinstance(self.meta_data, dict):
            for index, key in enumerate(self.dict_key_order):
                if key not in self.meta_data:
                    insert_key_at_index(d=self.meta_data, key=key, index=index)

    def _invalidate(self) -> None:
        """Invalidate this object.

        This method is called when the object needs to be recompiled or reset.
        """
        raise NotImplementedError("This method should be overridden by subclasses to invalidate the object.")

    def compile(self) -> Self:
        """Compile this object.

        Additionally, this method will call all functions in the on_compiled list.

        Returns:
            Self: This object for method chaining.
        """
        [call() for call in self._on_compiling]
        self._compile_from_meta_data()
        self._init_dict_order()
        [call() for call in self._on_compiled]
        return self

    def validate(self, report: Optional['ControllerReportItem'] = None) -> 'ControllerReportItem':
        """Validate this object.

        Args:
            report: Existing report to add to, creates new one if None.

        Returns:
            ControllerReportItem: Validation report for this object.
        """
        if not report:
            report = ControllerReportItem(self, f'Validating {self.__class__.__name__} object: {str(self)}')

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


class NamedPlcObject(PlcObject, Loggable, Generic[CTRL]):
    """Supports a name and description for a PLC object.

    Args:
        meta_data: Metadata for this object.
        default_loader: Default loader for this object.
        name: Name of this object.
        description: Description of this object.
        controller: Controller for this object.

    Attributes:
        name: Name of this object.
        description: Description of this object.
    """

    def __init__(
        self,
        meta_data=defaultdict(None),
        default_loader: Callable = lambda: defaultdict(None),
        name: Optional[str] = None,
        description: Optional[str] = None,
        controller: Optional[CTRL] = None
    ) -> None:
        PlcObject.__init__(self,
                           controller=controller,
                           default_loader=default_loader,
                           meta_data=meta_data)
        if name:
            meta_data[L5X_PROP_NAME] = name

        if meta_data.get(L5X_PROP_NAME, None) is None:
            raise ValueError("A name must be provided via argument or meta_data!")

        if description is not None:
            meta_data[L5X_PROP_DESCRIPTION] = description

        NamedPyroxObject.__init__(
            self,
            name=meta_data[L5X_PROP_NAME],
            description=meta_data.get(L5X_PROP_DESCRIPTION, None)
        )

    def __str__(self):
        return str(self.name)

    @property
    def name(self) -> str:
        """Get this object's metadata name.

        Returns:
            str: The name of this object.
        """
        return self[L5X_PROP_NAME]

    @name.setter
    def name(self, value: str):
        """Set this object's name.

        Args:
            value: The name to set.

        Raises:
            InvalidNamingException: If the name is invalid.
        """
        if not self.is_valid_string(value):
            raise self.InvalidNamingException

        self[L5X_PROP_NAME] = value

    @property
    def description(self) -> str:
        """Get this object's metadata description.

        Returns:
            str: The description of this object.
        """
        return self[L5X_PROP_DESCRIPTION]

    @description.setter
    def description(self, value: str):
        """Set this object's description.

        Args:
            value: The description to set.
        """
        self[L5X_PROP_DESCRIPTION] = value

    @property
    def process_name(self) -> str:
        """Get the name of this controller without Customer plant identification prefixes

        Overrides the base class to return the name instead of the metadata string.
        """
        return self.name

    def _remove_asset_from_meta_data(
        self,
        asset: Union['NamedPlcObject', str],
        asset_list: HashList,
        raw_asset_list: list[dict]
    ) -> None:
        """Remove an asset from this object's metadata.

        Args:
            asset: The asset to remove.
            asset_list: The HashList containing the asset.
            raw_asset_list: The raw metadata list.

        Raises:
            ValueError: If asset is wrong type or doesn't exist.
        """
        if not isinstance(asset, (NamedPlcObject, str)):
            raise ValueError(f"asset must be of type {type(NamedPlcObject)} or str!")

        if not isinstance(asset_list, HashList):
            raise ValueError('asset list must be of type HashList!')

        if not isinstance(raw_asset_list, list):
            raise ValueError('raw asset list must be of type list!')

        asset_name = asset if isinstance(asset, str) else getattr(asset, asset_list.hash_key, None)

        if asset_name not in asset_list:
            raise ValueError(f"Asset with name {asset_name} does not exist in this container!")

        raw_asset_list.remove(next((x for x in raw_asset_list if x[L5X_PROP_NAME] == asset_name), None))
        self._invalidate()

    def validate(self, report: Optional['ControllerReportItem'] = None) -> 'ControllerReportItem':
        """Validate this named PLC object.

        Args:
            report: Existing report to add to.

        Returns:
            ControllerReportItem: Validation report.
        """
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

    def __init__(
        self,
        meta_data: str,
        instruction: 'LogixInstruction',
        arg_position: int,
        controller: Optional[CTRL] = None
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

        if self.instruction.instruction_name == INSTR_JSR:
            self._instruction_type = LogixInstructionType.JSR
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
        self._tag: Optional['Tag'] = None
        self._type: LogixInstructionType = None
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
        return self._rung.container

    @property
    def instruction_name(self) -> str:
        """get the instruction element

        Returns:
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
    def type(self) -> LogixInstructionType:
        if self._type:
            return self._type
        self._type = self._get_instruction_type()
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

    def _get_instruction_type(self) -> LogixInstructionType:
        """get the instruction type for this instruction

        Returns:
            :class:`LogixInstructionType`
        """
        if self.instruction_name in INPUT_INSTRUCTIONS:
            return LogixInstructionType.INPUT
        elif self.instruction_name in [x[0] for x in OUTPUT_INSTRUCTIONS]:
            return LogixInstructionType.OUTPUT
        elif self.instruction_name == INSTR_JSR:
            return LogixInstructionType.JSR
        else:
            return LogixInstructionType.UNKOWN

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


class ContainsTags(NamedPlcObject):
    def __init__(
        self,
        meta_data=defaultdict(None),
        controller=None
    ) -> None:
        super().__init__(
            meta_data=meta_data,
            controller=controller
        )
        self._tags: HashList = None

    @property
    def raw_tags(self) -> list[dict]:
        if not self['Tags']:
            self['Tags'] = {'Tag': []}
        if not isinstance(self['Tags']['Tag'], list):
            self['Tags']['Tag'] = [self['Tags']['Tag']]
        return self['Tags']['Tag']

    @property
    def tags(self) -> HashList:
        if not self._tags:
            self._compile_tags()
        return self._tags

    def _compile_from_meta_data(self):
        """compile this object from its meta data
        """
        self._compile_tags()

    def _compile_tags(self):
        """compile the tags in this container
        """
        self._tags = HashList('name')
        for tag in self.raw_tags:
            self._tags.append(self.config.tag_type(meta_data=tag, controller=self.controller))

    def _invalidate(self):
        self._tags = None

    def add_tag(self, tag: 'Tag') -> None:
        """add a tag to this container

        Args:
            routine (Tag): tag to add
        """
        if not isinstance(tag, Tag):
            raise TypeError("Tag must be of type Tag!")

        if tag.name in self.tags:
            self.remove_tag(tag)

        self.raw_tags.append(tag.meta_data)
        self._invalidate()

    def remove_tag(self, tag: Union['Tag', str]) -> None:
        """remove a tag from this container

        Args:
            tag (Union[Tag, str]): tag to remove
        """
        self._remove_asset_from_meta_data(tag,
                                          self.tags,
                                          self.raw_tags)


class ContainsRoutines(ContainsTags):
    """This PLC Object contains routines
    """

    def __init__(
        self,
        meta_data=defaultdict(None),
        controller=None
    ) -> None:
        super().__init__(
            meta_data,
            controller
        )

        self._input_instructions: list[LogixInstruction] = None
        self._output_instructions: list[LogixInstruction] = None
        self._instructions: list[LogixInstruction] = None
        self._routines: HashList[Routine] = None

    @property
    def class_(self) -> str:
        return self['@Class']

    @property
    def input_instructions(self) -> list[LogixInstruction]:
        if not self._input_instructions:
            self._compile_instructions()
        return self._input_instructions

    @property
    def instructions(self) -> list[LogixInstruction]:
        """get the instructions in this container

        Returns:
            :class:`list[LogixInstruction]`
        """
        if not self._instructions:
            self._compile_instructions()
        return self._instructions

    @property
    def output_instructions(self) -> list[LogixInstruction]:
        if not self._output_instructions:
            self._compile_instructions()
        return self._output_instructions

    @property
    def routines(self) -> HashList[Routine]:
        if not self._routines:
            self._compile_routines()
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
        self._compile_routines()
        self._compile_instructions()

    def _compile_instructions(self):
        """compile the instructions in this container
        """
        self._input_instructions = []
        self._output_instructions = []
        self._instructions = []

        for routine in self.routines:
            self._input_instructions.extend(routine.input_instructions)
            self._output_instructions.extend(routine.output_instructions)
            self._instructions.extend(routine.instructions)

    def _compile_routines(self):
        """compile the routines in this container

        This method compiles the routines from the raw metadata and initializes the HashList.
        """
        self._routines = HashList('name')
        for routine in self.raw_routines:
            self._routines.append(
                self.config.routine_type(
                    meta_data=routine,
                    controller=self.controller,
                    program=self
                )
            )

    def _invalidate(self):
        """invalidate this object

        This method is called when the object needs to be recompiled or reset.
        """
        super()._invalidate()
        self._input_instructions = []
        self._output_instructions = []
        self._instructions = []
        self._routines = HashList('name')

    def add_routine(self, routine: 'Routine'):
        """add a routine to this container

        Args:
            routine (Routine): routine to add
        """
        if not isinstance(routine, Routine):
            raise TypeError("Routine must be of type Routine!")

        if routine.name in self.routines:
            self.remove_routine(routine)

        self.raw_routines.append(routine.meta_data)
        self._invalidate()

    def remove_routine(self, routine: Union[Routine, str]):
        """remove a routine from this container

        Args:
            routine (Routine): routine to remove
        """
        self._remove_asset_from_meta_data(routine,
                                          self.routines,
                                          self.raw_routines)


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
        if not self.is_valid_revision_string(value):
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

        Returns:
            list[str]: List of endpoint operands.
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


class ModuleControlsType(Enum):
    """Module controls type enumeration
    """
    UNKOWN = 'Unknown'
    PLC = 'PLC'
    BLOCK = 'Block'
    SAFETY_BLOCK = 'SafetyBlock'
    DRIVE = 'Drive'


class IntrospectiveModuleFactory(MetaFactory):
    """Factory for creating Introspective Module instances."""

    _registered_types: dict = {}


class IntrospectiveModuleMeta(FactoryTypeMeta):
    """Metaclass for auto-registering Warehouse subclasses."""

    @classmethod
    def get_class(cls) -> Type['IntrospectiveModule']:
        try:
            return IntrospectiveModule
        except NameError:
            return None

    @classmethod
    def get_factory(cls):
        return IntrospectiveModuleFactory


class IntrospectiveModule:
    """Introspective Module for a rockwell plc.
    This is a wrapper around the Module class to provide introspection capabilities.
    Such as, a Siemens G115Drive, or a Rockwell 1756-L85E controller.
    It is used to extend capabilities of known modules, or to provide a way to introspect unknown modules.
    """

    def __init__(
        self,
        module: Optional[Module] = None
    ) -> None:
        self._module = module

    @classmethod
    def get_controls_type(cls) -> ModuleControlsType:
        """Get the controls type of the module."""
        obj = cls()
        return obj.controls_type
        # raise NotImplementedError('This method should be implemented by the subclass.')

    @classmethod
    def get_required_imports(cls) -> list[tuple[str, str]]:
        """Get the required datatype imports for the module.

        Returns:
            list[tuple[str, str]]: List of tuples containing the module and class name to import.
        """
        return []

    def get_required_safety_rungs(self) -> list[Rung]:
        """Get the required safety rungs for the module.

        Returns:
            list[Rung]: List of rungs.
        """
        return []

    def get_required_standard_rungs(self) -> list[Rung]:
        """Get the required standard rungs for the module.

        Returns:
            list[Rung]: List of rungs.
        """
        return []

    def get_required_standard_to_safety_mapping(self) -> tuple[str, str]:
        """Get the required standard to safety mapping for the module.

        Returns:
            dict[str, str]: Dictionary of standard to safety mapping.
        """
        return self.get_standard_input_tag_name(), self.get_safety_input_tag_name()

    @classmethod
    def get_required_tags(cls) -> list[dict]:
        """Get the required tags for the module.

        Returns:
            list[dict]: List of tag dictionaries.
        """
        return []

    def get_safety_input_tag_name(self) -> str:
        """Get the safety tag name for the module.

        Returns:
            str: Safety tag name.
        """
        return ''

    def get_standard_input_tag_name(self) -> str:
        """Get the standard tag name for the module.

        Returns:
            str: Standard tag name.
        """
        return ''

    def get_standard_output_tag_name(self) -> str:
        """Get the standard output tag name for the module.

        Returns:
            str: Standard output tag name.
        """
        return ''

    @property
    def catalog_number(self) -> str:
        """The catalog number of the module."""
        return ''

    @property
    def controls_type(cls) -> ModuleControlsType:
        """The controls type of the module."""
        return ModuleControlsType.UNKOWN

    @property
    def input_cxn_point(self) -> str:
        """The input connection point of the module."""
        return ''

    @property
    def output_cxn_point(self) -> str:
        """The output connection point of the module."""
        return ''

    @property
    def input_size(self) -> int:
        """The input size of the module."""
        return ''

    @property
    def module(self) -> Optional[Module]:
        """The module being wrapped by the IntrospectiveModule."""
        return self._module

    @module.setter
    def module(self, value: Module) -> None:
        if not isinstance(value, Module):
            raise ValueError('Module must be an instance of Module.')
        self._module = value

    @property
    def output_size(self) -> int:
        """The output size of the module."""
        raise NotImplementedError('This method should be implemented by the subclass.')

    @property
    def type_(self) -> str:
        """Get the type of the module."""
        return self.__class__.__name__

    @classmethod
    def from_meta_data(
        cls,
        module: Module,
        lazy_match_catalog: Optional[bool] = False
    ) -> IntrospectiveModule:
        """Create an IntrospectiveModule from a Module instance.
        This method will attempt to match the module to a known IntrospectiveModule subclass

        Args:
            module (Module): The Module instance to wrap.
            lazy_match_catalog (bool, optional): If True, will attempt to match the catalog number
                using a substring match if an exact match is not found. Defaults to False.

        Returns:
            IntrospectiveModule: An instance of the matched IntrospectiveModule subclass,
                or a generic IntrospectiveModule if no match is found.

        Raises:
            ValueError: If the module is None.
        """
        if not module:
            raise ValueError('Module is required to create an IntrospectiveModule.')

        if not module.catalog_number:
            return cls(module)

        known_modules = ModuleWarehouseFactory.get_all_known_modules()
        if not known_modules:
            return cls(module)

        for m in known_modules:
            mod = m(module)
            if (mod.catalog_number == module.catalog_number and
                    mod.input_cxn_point == module.input_connection_point and
                    mod.output_cxn_point == module.output_connection_point and
                    mod.input_size == module.input_connection_size and
                    mod.output_size == module.output_connection_size):
                return mod
            if lazy_match_catalog and module.catalog_number != 'ETHERNET-MODULE':
                if mod.catalog_number in module.catalog_number:
                    return mod
        return cls(module)

    def get_safety_emulation_rung_text(self) -> str:
        """Get the emulation rung text for the safety module.
        This is used to generate the emulation logic for the safety module.
        .. ------------------------------------------------------------
        .. returns::
            :class:`str`
                The emulation rung text for the safety module.
        """
        raise NotImplementedError('This method should be implemented by the subclass.')

    def get_standard_emulation_rung_text(self) -> str:
        """Get the emulation rung text for the module.
        This is used to generate the emulation logic for the module.
        .. ------------------------------------------------------------
        .. returns::
            :class:`str`
                The emulation rung text for the module.
        """
        raise NotImplementedError('This method should be implemented by the subclass.')


class Module(NamedPlcObject):
    def __init__(self,
                 l5x_meta_data: dict = None,
                 controller: Controller = None):

        super().__init__(meta_data=l5x_meta_data or l5x_dict_from_file(PLC_MOD_FILE)['Module'],
                         controller=controller)
        self._introspective_module: IntrospectiveModule = None
        self._compile_from_meta_data()

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
    def communications(self) -> dict:
        return self['Communications']

    @property
    def connections(self) -> dict:
        """get the connections for this module

        Returns:
            :class:`dict`: connections for this module
        """
        if not self.communications:
            return {}
        if not isinstance(self.communications.get('Connections', {}), dict):
            self.communications['Connections'] = {'Connection': []}
        if not isinstance(self.communications['Connections']['Connection'], list):
            self.communications['Connections']['Connection'] = [self.communications['Connections']['Connection']]
        return self.communications['Connections']['Connection']

    @property
    def input_connection_point(self) -> str:
        """get the input connection point for this module

        Returns:
            :class:`str`: input connection point
        """
        return self.connections[0].get('@InputCxnPoint', '')

    @property
    def output_connection_point(self) -> str:
        """get the output connection point for this module

        Returns:
            :class:`str`: output connection point
        """
        return self.connections[0].get('@OutputCxnPoint', '')

    @property
    def input_connection_size(self) -> str:
        """get the input connection size for this module

        Returns:
            :class:`str`: input connection size
        """
        return self.communications.get('@PrimCxnInputSize', '')

    @property
    def output_connection_size(self) -> str:
        """get the output connection size for this module

        Returns:
            :class:`str`: output connection size
        """
        return self.communications.get('@PrimCxnOutputSize', '')

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
    def introspective_module(self) -> IntrospectiveModule:
        """get the introspective module for this module

        Returns:
            :class:`IntrospectiveModule`: introspective module
        """
        return self._introspective_module

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
    def type_(self) -> str:
        """get the type of this module

        Returns:
            :class:`str`: type of this module
        """
        return self.introspective_module.type_ if self.introspective_module else 'Unknown'

    def _compile_from_meta_data(self):
        self._introspective_module = IntrospectiveModule.from_meta_data(self, lazy_match_catalog=True)

    def validate(self) -> ControllerReportItem:

        report = ControllerReportItem(self,
                                      f'Validating {self.__class__.__name__} object: {self.name}')

        return report


class Program(ContainsRoutines):
    def __init__(
        self,
        meta_data: dict = None,
        controller: Controller = None
    ) -> None:
        """type class for plc Program

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """

        super().__init__(
            meta_data=meta_data or l5x_dict_from_file(PLC_PROG_FILE)['Program'],
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
    def main_routine(self) -> Optional[Routine]:
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
    ) -> list[LogixInstruction]:
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

    def validate(self) -> ControllerReportItem:
        report = super().validate()

        if not self.main_routine_name:
            report.test_notes.append('No main routine name found in program!')
            report.pass_fail = False

        return report


class Routine(NamedPlcObject):
    def __init__(
        self,
        meta_data: dict = None,
        controller: Controller = None,
        program: Optional[Program] = None,
        aoi: Optional[AddOnInstruction] = None,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        """type class for plc Routine

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """

        super().__init__(
            meta_data=meta_data or l5x_dict_from_file(PLC_ROUT_FILE)['Routine'],
            controller=controller,
            name=name,
            description=description
        )

        self._program: Optional[Program] = program
        self._aoi: Optional[AddOnInstruction] = aoi
        self._instructions: list[LogixInstruction] = []
        self._input_instructions: list[LogixInstruction] = []
        self._output_instructions: list[LogixInstruction] = []
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
    def aoi(self) -> Optional[AddOnInstruction]:
        return self._aoi

    @property
    def container(self) -> ContainsRoutines:
        return self.aoi if self.aoi else self.program

    @property
    def input_instructions(self) -> list[LogixInstruction]:
        if not self._input_instructions:
            self._compile_instructions()
        return self._input_instructions

    @property
    def instructions(self) -> list[LogixInstruction]:
        """get the instructions in this routine

        Returns:
            :class:`list[LogixInstruction]`
        """
        if not self._instructions:
            self._compile_instructions()
        return self._instructions

    @property
    def output_instructions(self) -> list[LogixInstruction]:
        if not self._output_instructions:
            self._compile_instructions()
        return self._output_instructions

    @property
    def program(self) -> Optional[Program]:
        return self._program

    @property
    def rungs(self) -> list[Rung]:
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
        [self._rungs.append(self.config.rung_type(meta_data=x,
                                                  controller=self.controller,
                                                  routine=self,
                                                  rung_number=i))
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
        [self._rungs.append(self.config.rung_type(meta_data=x,
                                                  controller=self.controller,
                                                  routine=self,
                                                  rung_number=i))
         for i, x in enumerate(self.raw_rungs)]

    def _invalidate(self):
        self._instructions: list[LogixInstruction] = []
        self._input_instructions: list[LogixInstruction] = []
        self._output_instructions: list[LogixInstruction] = []
        self._rungs: list[Rung] = []

    def add_rung(self,
                 rung: Rung,
                 index: Optional[int] = None):
        """add a rung to this routine

        Args:
            rung (Rung): the rung to add
        """
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
            if instruction.type == LogixInstructionType.JSR and instruction.operands:
                if str(instruction.operands[0]) == routine_name:
                    return True
        return False

    def clear_rungs(self):
        """clear all rungs from this routine"""
        self.logger.debug(f"Clearing all rungs from routine {self.name}")
        self.raw_rungs.clear()
        self._compile_from_meta_data()

    def get_instructions(
        self,
        instruction_filter: Optional[str],
        operand_filter: Optional[str] = None
    ) -> list[LogixInstruction]:
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
        self._invalidate()

    def validate(self) -> ControllerReportItem:
        report = ControllerReportItem(self,
                                      f'Validating {self.__class__.__name__} object: {self.meta_data}')
        if not self.rungs:
            report.test_notes.append('No rungs found in routine!')
            report.pass_fail = False

        for rung in self.rungs:
            rung_report = rung.validate()
            report.pass_fail = report.pass_fail and rung_report.pass_fail
            report.child_reports.append(rung_report)

        return report


class RungElementType(Enum):
    """Types of elements in a rung sequence."""
    INSTRUCTION = "instruction"
    BRANCH_START = "branch_start"
    BRANCH_END = "branch_end"
    BRANCH_NEXT = "branch_next"


@dataclass
class RungElement:
    """Represents an element in the rung sequence."""
    element_type: RungElementType
    instruction: Optional[LogixInstruction] = None
    branch_id: Optional[str] = None
    root_branch_id: Optional[str] = None  # ID of the parent branch if this is a nested branch
    branch_level: Optional[int] = 0  # Level of the branch in the rung
    position: int = 0  # Sequential position in rung
    rung: Optional[Rung] = None  # Reference to the Rung this element belongs to
    rung_number: int = 0  # Rung number this element belongs to


@dataclass
class RungBranch:
    """Represents a branch structure in the rung."""
    branch_id: str
    start_position: int
    end_position: int
    root_branch_id: Optional[str] = None  # ID of the parent branch
    nested_branches: List['RungBranch'] = field(default_factory=list)


class Rung(PlcObject):
    _branch_id_counter: int = 0  # Static counter for unique branch IDs

    def __init__(self,
                 meta_data: dict = None,
                 controller: Controller = None,
                 routine: Optional[Routine] = None,
                 rung_number: Optional[Union[int, str]] = None,
                 text: Optional[str] = None,
                 comment: Optional[str] = None):
        """type class for plc Rung"""
        super().__init__(meta_data=meta_data or l5x_dict_from_file(PLC_RUNG_FILE)['Rung'],
                         controller=controller)

        self._routine: Optional[Routine] = routine
        self._instructions: list[LogixInstruction] = []
        self._rung_sequence: List[RungElement] = []
        self._branches: Dict[str, RungBranch] = {}

        if text:
            self.text = text
        if comment:
            self.comment = comment
        if rung_number is not None:
            self.number = rung_number
        self._input_instructions: list[LogixInstruction] = []
        self._output_instructions: list[LogixInstruction] = []
        self._refresh_internal_structures()
        self._parse_rung_sequence()

    def __eq__(self, other):
        if not isinstance(other, Rung):
            return False
        if self.text == other.text:
            return True
        return False

    def __repr__(self):
        return (
            f'Rung(number={self.number}, '
            f'routine={self.routine.name if self.routine else "None"}, '
            f'type={self.type}, '
            f'comment={self.comment}, '
            f'text={self.text}, '
            f'instructions={len(self.instructions)}, '
            f'branches={len(self._branches)})'
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
        return self.routine.container if self.routine else None

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
        if not self['Text']:
            self['Text'] = ''
        return self['Text']

    @text.setter
    def text(self, value: str):
        if value is not None and not value.endswith(';'):
            value += ';'
        self['Text'] = value
        self._parse_rung_sequence()

    @property
    def type(self) -> str:
        return self['@Type']

    @property
    def rung_sequence(self) -> List[RungElement]:
        """Get the sequential elements of this rung including branches."""
        return self._rung_sequence

    @property
    def branches(self) -> Dict[str, RungBranch]:
        """Get all branches in this rung."""
        return self._branches

    @staticmethod
    def _extract_instructions(
        text
    ) -> List[str]:
        """Extract instructions with properly balanced parentheses.

        Args:
            text (str): The rung text to extract instructions from.

        Returns:
            List[str]: A list of extracted instructions.
        """
        instructions = []

        # Find instruction starts
        starts = list(re.finditer(r'[A-Za-z0-9_]+\(', text))

        for match in starts:
            start_pos = match.start()
            paren_pos = match.end() - 1  # Position of opening parenthesis

            # Find matching closing parenthesis
            paren_count = 1
            pos = paren_pos + 1

            while pos < len(text) and paren_count > 0:
                if text[pos] == '(':
                    paren_count += 1
                elif text[pos] == ')':
                    paren_count -= 1
                pos += 1

            if paren_count == 0:  # Found matching closing parenthesis
                instruction = text[start_pos:pos]
                instructions.append(instruction)

        return instructions

    @staticmethod
    def _insert_branch_tokens(
        original_tokens: List[str],
        start_pos: int,
        end_pos: int,
        branch_instructions: List[str]
    ) -> List[str]:
        """Insert branch markers and instructions into token sequence.

        Args:
            original_tokens (List[str]): Original token sequence
            start_pos (int): Start position for branch
            end_pos (int): End position for branch
            branch_instructions (List[str]): Instructions to place in branch

        Returns:
            List[str]: New token sequence with branch inserted
        """
        new_tokens = []

        if end_pos < start_pos:
            raise ValueError("End position must be greater than or equal to start position!")

        if not original_tokens:
            original_tokens = ['']

        def write_branch_end():
            new_tokens.append(',')
            for instr in branch_instructions:
                new_tokens.append(instr)
            new_tokens.append(']')

        for index, token in enumerate(original_tokens):
            if index == start_pos:
                new_tokens.append('[')
            if index == end_pos:
                write_branch_end()
            if token:
                new_tokens.append(token)
            if (end_pos == len(original_tokens) and index == len(original_tokens) - 1):
                write_branch_end()

        return new_tokens

    def _build_sequence_from_tokens(
        self,
        tokens: List[str]
    ) -> None:
        """Build the rung sequence from tokenized text.
        """
        position = 0
        root_branch_id = None  # Track each branch's parent, since the symbols appear on the parent rail
        branch_id = None
        branch_stack: list[RungBranch] = []
        branch_counter = 0
        branch_level = 0
        branch_level_history: list[int] = []  # Track branch levels for nesting
        branch_root_id_history: list[str] = []  # Track root branch IDs for nesting
        instruction_index = 0

        for token in tokens:
            if token == '[':  # Branch start
                branch_id = self._get_unique_branch_id()
                branch_counter += 1
                branch_level_history.append(branch_level)
                branch_level = 0  # Reset branch level for new branch

                branch_start = RungElement(
                    element_type=RungElementType.BRANCH_START,
                    branch_id=branch_id,
                    root_branch_id=root_branch_id,
                    branch_level=branch_level,
                    position=position,
                    rung=self,
                    rung_number=int(self.number)
                )

                branch = RungBranch(
                    branch_id=branch_id,
                    root_branch_id=root_branch_id,
                    start_position=position,
                    end_position=-1,
                    nested_branches=[],
                )

                branch_stack.append(branch)
                self._branches[branch_id] = branch
                self._rung_sequence.append(branch_start)
                branch_root_id_history.append(root_branch_id)  # Save current root branch id
                root_branch_id = branch_id  # Change branch id after assignment so we get the proper parent
                position += 1

            elif token == ']':  # Branch end
                branch = branch_stack.pop()
                self._branches[branch.branch_id].end_position = position
                if not self._branches[branch.branch_id].nested_branches:
                    # If no nested branches, we need to delete this major branch and reconstruct the rung again
                    fresh_tokens = self._remove_token_by_index(self._tokenize_rung_text(self.text), position)
                    fresh_tokens = self._remove_token_by_index(fresh_tokens, branch.start_position)
                    self.text = "".join(fresh_tokens)
                    self._refresh_internal_structures()
                    return

                self._branches[branch.branch_id].nested_branches[-1].end_position = position - 1
                root_branch_id = branch_root_id_history.pop() if branch_root_id_history else None
                branch_id = self._branches[branch.branch_id].root_branch_id
                branch_level = branch_level_history.pop() if branch_level_history else 0

                branch_end = RungElement(
                    element_type=RungElementType.BRANCH_END,
                    branch_id=branch.branch_id,
                    root_branch_id=branch.root_branch_id,
                    branch_level=branch_level,
                    position=position,
                    rung=self,
                    rung_number=int(self.number)
                )

                self._rung_sequence.append(branch_end)
                position += 1

            elif token == ',':  # Next branch marker
                parent_branch = branch_stack[-1] if branch_stack else None
                if not parent_branch:
                    raise ValueError("Next branch marker found without an active branch!")

                branch_level += 1
                branch_id = f'{parent_branch.branch_id}:{branch_level}'

                if branch_level > 1:
                    # update the previous nested branch's end position
                    parent_branch.nested_branches[-1].end_position = position - 1  # ends at the previous position

                next_branch = RungElement(
                    element_type=RungElementType.BRANCH_NEXT,
                    branch_id=branch_id,
                    root_branch_id=root_branch_id,
                    branch_level=branch_level,
                    position=position,
                    rung=self,
                    rung_number=int(self.number)
                )
                nested_branch = RungBranch(branch_id=branch_id, start_position=position,
                                           end_position=-1, root_branch_id=parent_branch.branch_id)

                parent_branch.nested_branches.append(nested_branch)
                self._branches[branch_id] = nested_branch
                self._rung_sequence.append(next_branch)
                position += 1

            else:  # Regular instruction
                instruction = self._find_instruction_by_text(token, instruction_index)
                if instruction:
                    element = RungElement(
                        element_type=RungElementType.INSTRUCTION,
                        instruction=instruction,
                        position=position,
                        branch_id=branch_id,
                        root_branch_id=root_branch_id,
                        branch_level=branch_level,
                        rung=self,
                        rung_number=int(self.number)
                    )

                    self._rung_sequence.append(element)
                    position += 1
                    instruction_index += 1
                else:
                    raise ValueError(f"Instruction '{token}' not found in rung text.")

    def _find_instruction_by_text(self, text: str, index: int) -> Optional[LogixInstruction]:
        """Find an instruction object by its text representation."""
        # First try exact match
        for instruction in self.instructions:
            if instruction.meta_data == text:
                return instruction

        # If no exact match, try by index (fallback)
        if 0 <= index < len(self.instructions):
            return self.instructions[index]

        return None

    def _find_instruction_index_in_text(self, instruction_text: str, occurrence: int = 0) -> int:
        """Find the index of an instruction in the text by its occurrence.

        Args:
            instruction_text (str): The instruction text to find
            occurrence (int): Which occurrence to find (0-based)

        Returns:
            int: The index of the instruction

        Raises:
            ValueError: If instruction not found or occurrence out of range
        """
        tokens = self._tokenize_rung_text(self.text)
        # existing_instructions = re.findall(INST_RE_PATTERN, self.text)
        matches = [i for i, token in enumerate(tokens) if token == instruction_text]

        if not matches:
            raise ValueError(f"Instruction '{instruction_text}' not found in rung")

        if occurrence >= len(matches):
            raise ValueError(f"Occurrence {occurrence} not found. Only {len(matches)} occurrences exist.")

        return matches[occurrence]

    def _get_element_at_position(
        self,
        position: int
    ) -> Optional[RungElement]:
        """Get the RungElement at a specific position in the rung sequence.
        Args:
            position (int): The position in the rung sequence
        Returns:
            Optional[RungElement]: The RungElement at the specified position, or None if not found
        """
        if position < 0 or position >= len(self._rung_sequence) or position is None:
            raise IndexError("Position out of range in rung sequence.")

        return self._rung_sequence[position]

    def _get_instructions(self):
        """Extract instructions from rung text."""
        if not self.text:
            return

        instr = self._extract_instructions(self.text)
        if not instr:
            return

        self._instructions = [LogixInstruction(x, self, self.controller) for x in instr]

    def _get_unique_branch_id(self) -> str:
        """Generate a unique branch ID."""
        branch_id = f"rung_{self.number}_branch_{self._branch_id_counter}"
        self._branch_id_counter += 1
        return branch_id

    def _parse_rung_sequence(self):
        """Parse the rung text to identify instruction sequence and branches."""
        self._refresh_internal_structures()
        self._get_instructions()
        self._build_sequence_from_tokens(self._tokenize_rung_text(self.text))

    def _tokenize_rung_text(self, text: str) -> List[str]:
        """Tokenize rung text to identify instructions and branch markers."""

        tokens = []

        # First, extract all instructions using the balanced parentheses method
        instructions = self._extract_instructions(text)
        instruction_ranges = []

        # Find the positions of each instruction in the text
        search_start = 0
        for instruction in instructions:
            pos = text.find(instruction, search_start)
            if pos != -1:
                instruction_ranges.append((pos, pos + len(instruction)))
                search_start = pos + len(instruction)

        # Process the text character by character
        i = 0
        current_segment = ""

        while i < len(text):
            char = text[i]

            if char in ['[', ']', ',']:
                # Check if this symbol is inside any instruction
                inside_instruction = any(start <= i < end for start, end in instruction_ranges)

                if inside_instruction:
                    # This bracket is part of an instruction (array reference), keep it
                    current_segment += char
                else:
                    # This is a branch marker or next-branch marker
                    if current_segment.strip():
                        # Extract instructions from current segment using our method
                        segment_instructions = self._extract_instructions(current_segment)
                        tokens.extend(segment_instructions)
                        current_segment = ""

                    # Add the branch marker
                    tokens.append(char)
            else:
                current_segment += char

            i += 1

        # Process any remaining segment
        if current_segment.strip():
            segment_instructions = self._extract_instructions(current_segment)
            tokens.extend(segment_instructions)

        return tokens

    def _reconstruct_text_with_branches(self, instructions: List[str],
                                        branch_markers: List[str],
                                        original_text: str) -> str:
        """Reconstruct text preserving branch structure.

        This is a complex operation that attempts to maintain the relative positioning
        of branch markers with the instruction sequence.
        """
        # Get original tokens to understand structure
        original_tokens = self._tokenize_rung_text(original_text)

        # Create a map of instruction positions to branch operations
        instruction_index = 0
        result_tokens = []

        for token in original_tokens:
            if token in ['[', ']', ',']:
                # Preserve branch markers
                result_tokens.append(token)
            else:
                # Replace with new instruction if available
                if instruction_index < len(instructions):
                    result_tokens.append(instructions[instruction_index])
                    instruction_index += 1

        # Add any remaining instructions at the end
        while instruction_index < len(instructions):
            result_tokens.append(instructions[instruction_index])
            instruction_index += 1

        return "".join(result_tokens)

    def _refresh_internal_structures(self):
        """Refresh the internal instruction and sequence structures after text changes."""
        # Clear existing structures
        self._instructions = []
        self._rung_sequence = []
        self._branches = {}
        self._branch_id_counter = 0
        self._input_instructions = []
        self._output_instructions = []

    def _remove_branch_tokens(self, original_tokens: List[str], branch_id: str,
                              keep_instructions: bool) -> List[str]:
        """Remove branch tokens from token sequence.

        Args:
            original_tokens (List[str]): Original token sequence
            branch_id (str): Branch ID to remove
            keep_instructions (bool): Whether to keep branch instructions

        Returns:
            List[str]: New token sequence with branch removed
        """
        # This is a simplified implementation
        # In practice, you'd need to track which '[' and ']' belong to which branch
        new_tokens = []
        skip_until_close = False
        branch_instructions = []

        if branch_id in self._branches:
            branch = self._branches[branch_id]
            branch_instructions = [instr.meta_data for instr in branch.instructions]

        for token in original_tokens:
            if token == '[' and not skip_until_close:
                # Check if this is the branch we want to remove
                # This is simplified - in practice you'd need better branch tracking
                skip_until_close = True
                continue
            elif token == ']' and skip_until_close:
                skip_until_close = False
                if keep_instructions:
                    new_tokens.extend(branch_instructions)
                continue
            elif not skip_until_close:
                new_tokens.append(token)

        return new_tokens

    def _remove_token_by_index(self, tokens: List[str], index: int) -> List[str]:
        """Remove a token at a specific index from the token list.

        Args:
            tokens (List[str]): List of tokens
            index (int): Index of the token to remove

        Returns:
            List[str]: New token list with the specified token removed
        """
        if index < 0 or index >= len(tokens):
            raise IndexError("Index out of range!")

        return tokens[:index] + tokens[index + 1:]

    def _remove_tokens(self, tokens: List[str], start: int, end: int) -> List[str]:
        """Remove a range of tokens from the token list.

        Args:
            tokens (List[str]): List of tokens
            start (int): Start index of the range to remove
            end (int): End index of the range to remove

        Returns:
            List[str]: New token list with the specified range removed
        """
        if start < 0 or end >= len(tokens) or start > end:
            raise IndexError("Invalid start or end indices for removal!")

        return tokens[:start] + tokens[end + 1:]

    def add_instruction(self, instruction_text: str, position: Optional[int] = None):
        """Add an instruction to this rung at the specified position.

        Args:
            instruction_text (str): The instruction text to add (e.g., "XIC(Tag1)")
            position (Optional[int]): Position to insert at. If None, appends to end.
        """
        if not instruction_text or not isinstance(instruction_text, str):
            raise ValueError("Instruction text must be a non-empty string!")

        # Validate instruction format
        if not re.match(INST_RE_PATTERN, instruction_text):
            raise ValueError(f"Invalid instruction format: {instruction_text}")

        current_text = self.text or ""

        if not current_text.strip():
            # Empty rung, just set the instruction
            current_tokens = [instruction_text]
        else:
            # Parse existing instructions to find insertion point
            current_tokens = self._tokenize_rung_text(current_text)

            if position is None or position >= len(current_tokens):
                # Append to end
                current_tokens.append(instruction_text)
            elif position == 0:
                # Insert at beginning
                current_tokens.insert(0, instruction_text)

            else:
                # Insert at specific position
                current_tokens.insert(position, instruction_text)

        # Refresh internal structures
        self.text = "".join(current_tokens)

    def find_instruction_positions(self, instruction_text: str) -> List[int]:
        """Find all positions of a specific instruction in the rung.

        Args:
            instruction_text (str): The instruction text to find

        Returns:
            List[int]: List of positions where the instruction appears
        """
        import re
        existing_instructions = re.findall(INST_RE_PATTERN, self.text) if self.text else []
        return [i for i, inst in enumerate(existing_instructions) if inst == instruction_text]

    def find_matching_branch_end(self, start_position: int) -> Optional[int]:
        """Find the matching end position for a branch start.

        Args:
            start_position (int): Position where branch starts

        Returns:
            Optional[int]: Position where branch ends, or None if not found
        """
        if not self.text:
            return None

        tokens = self._tokenize_rung_text(self.text)
        if len(tokens) <= start_position or tokens[start_position] != '[':
            raise ValueError("Start position must be a valid branch start token position.")

        bracket_count = 1  # Since we start on a bracket
        instruction_count = start_position

        for token in tokens[start_position+1:]:
            instruction_count += 1
            if token == '[':
                bracket_count += 1
            elif token == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    return instruction_count

        return None

    def get_branch_count(self) -> int:
        """Get the number of branches in this rung."""
        return len(self._branches)

    def get_branch_info(self, branch_id: str) -> Dict:
        """Get detailed information about a branch.

        Args:
            branch_id (str): ID of the branch

        Returns:
            Dict: Branch information including positions and instructions

        Raises:
            ValueError: If branch ID doesn't exist
        """
        if branch_id not in self._branches:
            raise ValueError(f"Branch '{branch_id}' not found in rung!")

        branch = self._branches[branch_id]

        return {
            'branch_id': branch_id,
            'start_position': branch.start_position,
            'end_position': branch.end_position,
            'instruction_count': len(branch.instructions),
            'instructions': [instr.meta_data for instr in branch.instructions],
            'instruction_types': [instr.instruction_name for instr in branch.instructions]
        }

    def get_branch_internal_nesting_level(self, branch_position: int) -> int:
        """Get nesting levels of elements inside of a branch.
        """
        end_position = self.find_matching_branch_end(branch_position)
        if end_position is None:
            raise ValueError(f"No matching end found for branch starting at position {branch_position}.")

        tokens = self._tokenize_rung_text(self.text)
        open_counter, nesting_counter, nesting_level = 0, 0, 0
        indexed_tokens = tokens[branch_position+1:end_position]
        for token in indexed_tokens:
            if open_counter < 0:
                raise ValueError("Mismatched brackets in rung text.")
            if token == '[':
                open_counter += 1
            elif token == ',' and open_counter:
                nesting_counter += 1
                if nesting_counter > nesting_level:
                    nesting_level = nesting_counter
            elif token == ']':
                open_counter -= 1

        return nesting_level

    def get_branch_nesting_level(self, instruction_position: int) -> int:
        """Get the nesting level of branches at a specific instruction position.

        Args:
            instruction_position (int): Position of the instruction (0-based)

        Returns:
            int: Nesting level (0 = main line, 1+ = inside branches)
        """
        if not self.text:
            return 0

        tokens = self._tokenize_rung_text(self.text)
        nesting_level = 0

        for index, token in enumerate(tokens):
            if token == '[':
                nesting_level += 1
            elif token == ']':
                nesting_level -= 1
            if index == instruction_position:
                return nesting_level

        return 0

    def get_comment_lines(self) -> int:
        """Get the number of comment lines in this rung.
        """
        if not self.comment:
            return 0

        # Count the number of comment lines by splitting on newlines
        return len(self.comment.splitlines())

    def get_execution_sequence(self) -> List[Dict]:
        """Get the logical execution sequence of the rung."""
        sequence = []

        for i, element in enumerate(self._rung_sequence):
            if element.element_type == RungElementType.INSTRUCTION:
                sequence.append({
                    'step': i,
                    'instruction_type': element.instruction.instruction_name,
                    'instruction_text': element.instruction.meta_data,
                    'operands': [op.meta_data for op in element.instruction.operands],
                    'is_input': element.instruction.type == LogixInstructionType.INPUT,
                    'is_output': element.instruction.type == LogixInstructionType.OUTPUT
                })
            elif element.element_type in [RungElementType.BRANCH_START, RungElementType.BRANCH_END]:
                sequence.append({
                    'step': i,
                    'element_type': element.element_type.value,
                    'branch_id': element.branch_id
                })

        return sequence

    def get_instruction_count(self) -> int:
        """Get the total number of instructions in this rung."""
        return len(self.instructions)

    def get_instruction_at_position(
        self,
        position: int
    ) -> Optional[LogixInstruction]:
        """Get the instruction at a specific position.

        Args:
            position (int): The position index

        Returns:
            Optional[LogixInstruction]: The instruction at that position, or None
        """
        if 0 <= position < len(self.instructions):
            return self.instructions[position]
        return None

    def get_instruction_summary(self) -> Dict[str, int]:
        """Get a summary of instruction types and their counts.

        Returns:
            Dict[str, int]: Dictionary mapping instruction names to their counts
        """
        summary = {}
        for instruction in self.instructions:
            inst_name = instruction.instruction_name
            summary[inst_name] = summary.get(inst_name, 0) + 1
        return summary

    def get_instructions(
        self,
        instruction_filter: Optional[str] = None,
        operand_filter: Optional[str] = None
    ) -> List[LogixInstruction]:
        """Get instructions filtered by operand or name.

        Args:
            instruction_filter (Optional[str]): Instruction text to filter by
            operand_filter (Optional[str]): Instruction name to filter by

        Returns:
            List[LogixInstruction]: List of matching instructions
        """
        filtered_instructions = self.instructions

        if instruction_filter:
            filtered_instructions = [
                instr for instr in filtered_instructions
                if instruction_filter == instr.instruction_name
            ]

        if operand_filter:
            filtered_instructions = [
                instr for instr in filtered_instructions
                if any(operand_filter in op.meta_data for op in instr.operands)
            ]

        return filtered_instructions

    def get_branch_instructions(self, branch_id: str) -> List[LogixInstruction]:
        """Get all instructions within a specific branch."""
        if branch_id not in self._branches:
            return []
        return self._branches[branch_id].instructions.copy()

    def get_main_line_instructions(self) -> List[LogixInstruction]:
        """Get instructions that are on the main line (not in branches)."""
        branch_instructions = set()
        for branch in self._branches.values():
            branch_instructions.update(branch.instructions)

        return [instr for instr in self.instructions if instr not in branch_instructions]

    def get_max_branch_depth(self) -> int:
        """Get the maximum nesting depth of branches in this rung.

        Returns:
            int: Maximum branch depth (0 = no branches, 1+ = nested levels)
        """
        if not self.text:
            return 0

        tokens = self._tokenize_rung_text(self.text)
        first_branch_token_found = False
        current_depth = 0
        max_depth = 0
        restore_depth = 0

        for token in tokens:
            if token == '[':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif token == ',':
                # ',' increases the nested branch count
                # But the first occurence is included with the '[' token
                # So, ignore the first one and set a flag
                # Additionally, mark where to restore the depth level when this branch sequence ends
                if first_branch_token_found is False:
                    first_branch_token_found = True
                    restore_depth = current_depth
                    continue
                else:
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)

            elif token == ']':
                current_depth -= 1
                first_branch_token_found = False
                current_depth = restore_depth

        return max_depth

    def has_instruction(self, instruction_text: str) -> bool:
        """Check if the rung contains a specific instruction.

        Args:
            instruction_text (str): The instruction text to check for

        Returns:
            bool: True if the instruction exists in the rung
        """
        return len(self.find_instruction_positions(instruction_text)) > 0

    def has_branches(self) -> bool:
        """Check if this rung contains any branches."""
        return len(self._branches) > 0

    def insert_branch(self,
                      start_position: int = 0,
                      end_position: int = 0) -> None:
        """Insert a new branch structure in the rung.

        Args:
            start_position (int): Position where the branch should start (0-based)
            end_position (int): Position where the branch should end (0-based)

        Raises:
            ValueError: If positions are invalid
            IndexError: If positions are out of range
        """
        original_tokens = self._tokenize_rung_text(self.text)

        if start_position < 0 or end_position < 0:
            raise ValueError("Branch positions must be non-negative!")

        if start_position > len(original_tokens) or end_position > len(original_tokens):
            raise IndexError("Branch positions out of range!")

        if start_position > end_position:
            raise ValueError("Start position must be less than or equal to end position!")

        new_tokens = self._insert_branch_tokens(
            original_tokens,
            start_position,
            end_position,
            []
        )

        self.text = "".join(new_tokens)
        return self._get_element_at_position(start_position).branch_id

    def insert_branch_level(self,
                            branch_position: int = 0,):
        """Insert a new branch level in the existing branch structure.
        """
        original_tokens = self._tokenize_rung_text(self.text)
        if branch_position < 0 or branch_position >= len(original_tokens):
            raise IndexError("Start position out of range!")
        if original_tokens[branch_position] != '[' and original_tokens[branch_position] != ',':
            raise ValueError("Start position must be on a branch start token!")
        # Find index of first 'next branch' marker after the start position, which is a ',' token
        next_branch_index = branch_position + 1
        nested_branch_count = 0
        while next_branch_index < len(original_tokens):
            if original_tokens[next_branch_index] == '[':
                nested_branch_count += 1
            elif original_tokens[next_branch_index] == ']':
                if nested_branch_count <= 0:
                    break
                nested_branch_count -= 1
            elif original_tokens[next_branch_index] == ',' and nested_branch_count <= 0:
                break
            next_branch_index += 1
        if next_branch_index >= len(original_tokens):
            raise ValueError("No next branch marker found after the start position!")
        if original_tokens[next_branch_index] != ',' and original_tokens[next_branch_index] != ']':
            raise ValueError("Next branch marker must be a ',' token!")
        # Insert a ',' at the next branch index
        new_tokens = original_tokens[:next_branch_index] + [','] + original_tokens[next_branch_index:]
        # Reconstruct text
        self.text = "".join(new_tokens)

    def list_branches(self) -> List[Dict]:
        """Get information about all branches in the rung.

        Returns:
            List[Dict]: List of branch information dictionaries
        """
        return [self.get_branch_info(branch_id) for branch_id in self._branches.keys()]

    def move_branch(self, branch_id: str, new_start_position: int, new_end_position: int):
        """Move an existing branch to a new position.

        Args:
            branch_id (str): ID of the branch to move
            new_start_position (int): New start position for the branch
            new_end_position (int): New end position for the branch

        Raises:
            ValueError: If branch ID doesn't exist or positions are invalid
        """
        if branch_id not in self._branches:
            raise ValueError(f"Branch '{branch_id}' not found in rung!")

        branch = self._branches[branch_id]
        branch_instructions = [instr.meta_data for instr in branch.instructions]

        # Remove the existing branch
        self.remove_branch(branch_id, keep_instructions=False)

        # Insert at new position
        self.insert_branch(new_start_position, new_end_position, branch_instructions)

    def move_instruction(self, instruction: Union[LogixInstruction, str, int],
                         new_position: int, occurrence: int = 0):
        """Move an instruction to a new position in the rung.

        Args:
            instruction: The instruction to move (LogixInstruction, str, or int index)
            new_position (int): The new position for the instruction
            occurrence (int): Which occurrence to move if there are duplicates (0-based)
        """
        current_tokens = self._tokenize_rung_text(self.text)

        if not current_tokens:
            raise ValueError("No instructions found in rung!")

        if new_position < 0 or new_position >= len(current_tokens):
            raise IndexError(f"New position {new_position} out of range!")

        # Find the instruction to move
        if isinstance(instruction, LogixInstruction):
            try:
                old_index = self._find_instruction_index_in_text(instruction.meta_data, occurrence)
            except ValueError:
                raise ValueError(f"Instruction '{instruction.meta_data}' not found in rung!")

        elif isinstance(instruction, str):
            try:
                old_index = self._find_instruction_index_in_text(instruction, occurrence)
            except ValueError:
                raise ValueError(f"Instruction '{instruction}' not found in rung!")

        elif isinstance(instruction, int):
            if instruction < 0 or instruction >= len(current_tokens):
                raise IndexError(f"Instruction index {instruction} out of range!")
            old_index = instruction
        else:
            raise TypeError("Instruction must be LogixInstruction, str, or int!")

        if old_index == new_position:
            return  # No move needed

        # Move the instruction
        moved_instruction = current_tokens.pop(old_index)
        current_tokens.insert(new_position, moved_instruction)

        # Rebuild text with reordered instructions
        self.text = "".join(current_tokens)

    def remove_branch(self, branch_id: str):
        """Remove a branch structure from the rung.

        Args:
            branch_id (str): ID of the branch to remove
            keep_instructions (bool): If True, keep branch instructions in main line

        Raises:
            ValueError: If branch ID doesn't exist
        """
        if branch_id not in self._branches:
            raise ValueError(f"Branch '{branch_id}' not found in rung!")

        branch = self._branches[branch_id]
        if branch.start_position < 0 or branch.end_position < 0:
            raise ValueError("Branch start or end position is invalid!")

        tokens = self._tokenize_rung_text(self.text)
        tokens = self._remove_tokens(tokens, branch.start_position, branch.end_position)
        for b in branch.nested_branches:
            if b.branch_id in self._branches:
                del self._branches[b.branch_id]
        del self._branches[branch_id]
        self.text = "".join(tokens)

    def remove_instruction(self, instruction: Union[LogixInstruction, str, int],
                           occurrence: int = 0):
        """Remove an instruction from this rung.

        Args:
            instruction: The instruction to remove. Can be:
                - LogixInstruction object
                - str: instruction text to remove
                - int: index of instruction to remove
            occurrence (int): Which occurrence to remove if there are duplicates (0-based).
                            Only used when instruction is a string.
        """
        if not self.text:
            raise ValueError("Cannot remove instruction from empty rung!")

        existing_instructions = re.findall(INST_RE_PATTERN, self.text)
        current_tokens = self._tokenize_rung_text(self.text)

        if not existing_instructions:
            raise ValueError("No instructions found in rung!")

        # Determine which instruction to remove
        if isinstance(instruction, LogixInstruction):
            # Find the instruction by its meta_data
            try:
                remove_index = self._find_instruction_index_in_text(instruction.meta_data, occurrence)
            except ValueError:
                raise ValueError(f"Instruction '{instruction.meta_data}' not found in rung!")

        elif isinstance(instruction, str):
            # Remove by instruction text
            try:
                remove_index = self._find_instruction_index_in_text(instruction, occurrence)
            except ValueError:
                raise ValueError(f"Instruction '{instruction}' not found in rung!")

        elif isinstance(instruction, int):
            # Remove by index
            if instruction < 0 or instruction >= len(current_tokens):
                raise IndexError(f"Instruction index {instruction} out of range!")
            remove_index = instruction
        else:
            raise TypeError("Instruction must be LogixInstruction, str, or int!")

        # Remove the instruction and rebuild text
        current_tokens.pop(remove_index)

        if not current_tokens:
            # Last instruction removed, clear the rung
            self.text = ""
        else:
            # Rebuild text with remaining instructions
            self.text = "".join(current_tokens)

    def replace_instruction(self, old_instruction: Union[LogixInstruction, str, int],
                            new_instruction_text: str, occurrence: int = 0):
        """Replace an instruction in this rung.

        Args:
            old_instruction: The instruction to replace (LogixInstruction, str, or int index)
            new_instruction_text (str): The new instruction text
            occurrence (int): Which occurrence to replace if there are duplicates (0-based)
        """
        if not new_instruction_text or not isinstance(new_instruction_text, str):
            raise ValueError("New instruction text must be a non-empty string!")

        # Validate new instruction format
        import re
        if not re.match(INST_RE_PATTERN, new_instruction_text):
            raise ValueError(f"Invalid instruction format: {new_instruction_text}")

        current_tokens = self._tokenize_rung_text(self.text)

        if not current_tokens:
            raise ValueError("No instructions found in rung!")

        # Determine which instruction to replace
        if isinstance(old_instruction, LogixInstruction):
            instruction_text = old_instruction.meta_data
            try:
                replace_index = self._find_instruction_index_in_text(instruction_text, occurrence)
            except ValueError:
                raise ValueError(f"Instruction '{instruction_text}' not found in rung!")

        elif isinstance(old_instruction, str):
            try:
                replace_index = self._find_instruction_index_in_text(old_instruction, occurrence)
            except ValueError:
                raise ValueError(f"Instruction '{old_instruction}' not found in rung!")

        elif isinstance(old_instruction, int):
            if old_instruction < 0 or old_instruction >= len(current_tokens):
                raise IndexError(f"Instruction index {old_instruction} out of range!")
            replace_index = old_instruction
        else:
            raise TypeError("Old instruction must be LogixInstruction, str, or int!")

        # Replace the instruction
        current_tokens[replace_index] = new_instruction_text

        # Rebuild text with updated instructions
        self.text = "".join(current_tokens)

    def to_sequence_dict(self) -> Dict:
        """Convert rung to dictionary format showing the sequence structure."""
        return {
            'rung_number': self.number,
            'comment': self.comment,
            'text': self.text,
            'instruction_count': len(self.instructions),
            'branch_count': len(self._branches),
            'execution_sequence': self.get_execution_sequence(),
            'main_line_instructions': [instr.meta_data for instr in self.get_main_line_instructions()],
            'branches': {
                branch_id: {
                    'start_position': branch.start_position,
                    'end_position': branch.end_position,
                    'instructions': [instr.meta_data for instr in branch.instructions]
                }
                for branch_id, branch in self._branches.items()
            }
        }

    def validate(self) -> ControllerReportItem:
        report = ControllerReportItem(self,
                                      f'Validating {self.__class__.__name__} object: {self.number}')

        if not self.instructions:
            report.test_notes.append('No instructions found in rung!')
            report.pass_fail = False

        # Validate branch structure
        for branch_id, branch in self._branches.items():
            if branch.end_position <= branch.start_position:
                report.test_notes.append(f'Invalid branch structure for {branch_id}: end position not after start position!')
                report.pass_fail = False

            if not branch.instructions:
                report.test_notes.append(f'Branch {branch_id} contains no instructions!')
                report.pass_fail = False

        return report

    def validate_branch_structure(self) -> bool:
        """Validate that branch markers are properly paired.

        Returns:
            bool: True if branch structure is valid, False otherwise
        """
        if not self.text:
            return True

        tokens = self._tokenize_rung_text(self.text)
        bracket_count = 0

        for token in tokens:
            if token == '[':
                bracket_count += 1
            elif token == ']':
                bracket_count -= 1
                if bracket_count < 0:
                    return False

        return bracket_count == 0

    def wrap_instructions_in_branch(self, start_position: int, end_position: int) -> str:
        """Wrap existing instructions in a new branch structure.

        Args:
            start_position (int): Start position of instructions to wrap
            end_position (int): End position of instructions to wrap

        Returns:
            str: The branch ID that was created

        Raises:
            ValueError: If positions are invalid
            IndexError: If positions are out of range
        """
        if not self.text:
            raise ValueError("Cannot wrap instructions in empty rung!")

        current_instructions = re.findall(INST_RE_PATTERN, self.text)
        if not current_instructions:
            raise ValueError("No instructions found in rung!")

        if start_position < 0 or end_position < 0:
            raise ValueError("Positions must be non-negative!")

        if start_position >= len(current_instructions) or end_position > len(current_instructions):
            raise IndexError("Positions out of range!")

        if start_position > end_position:
            raise ValueError("Start position must be less than or equal to end position!")

        # Get instructions to wrap
        instructions_to_wrap = current_instructions[start_position:end_position]

        # Remove the original instructions
        for i in range(start_position, end_position):
            self.remove_instruction(i)

        # Insert branch with wrapped instructions
        branch_id = self.insert_branch(start_position, start_position, instructions_to_wrap)

        return branch_id


class TagEndpoint(PlcObject):
    def __init__(self,
                 meta_data: str,
                 controller: Controller,
                 parent_tag: 'Tag'):
        super().__init__(meta_data=meta_data,
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
                 meta_data: Optional[dict] = None,
                 controller: Optional[Controller] = None,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 class_: Optional[str] = None,
                 tag_type: Optional[str] = None,
                 datatype: Optional[str] = None,
                 dimensions: Optional[str] = None,
                 constant: Optional[bool] = None,
                 external_access: Optional[str] = None,
                 container: Union[Program, AddOnInstruction, Controller] = None):
        """type class for plc Tag

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """
        if controller is None and container is not None:
            controller = container.controller if isinstance(container, (Program, AddOnInstruction)) else None
        container = container or controller
        super().__init__(
            controller=controller,
            meta_data=meta_data or l5x_dict_from_file(PLC_TAG_FILE)['Tag'],
            name=name,
            description=description
        )
        self._container = container
        if class_:
            self.class_ = class_
        if tag_type:
            self.tag_type = tag_type
        if datatype:
            self.datatype = datatype
        if dimensions:
            self.dimensions = dimensions
        if constant is not None:
            self.constant = constant
        if external_access:
            self.external_access = external_access

    @property
    def dict_key_order(self) -> list[str]:
        return [
            '@Name',
            '@Class',
            '@TagType',
            '@DataType',
            '@Dimensions',
            '@Radix',
            '@AliasFor',
            '@Constant',
            '@ExternalAccess',
            'ConsumeInfo',
            'ProduceInfo',
            'Description',
            'Data',
        ]

    @property
    def alias_for(self) -> str:
        return self._meta_data.get('@AliasFor', None)

    @property
    def alias_for_base_name(self) -> str:
        """get the base name of the aliased tag

        Returns:
            :class:`str`
        """
        if not self.alias_for:
            return None

        return self.alias_for.split('.')[0].split(':')[0]

    @property
    def class_(self) -> str:
        return self['@Class']

    @class_.setter
    def class_(self, value: str):
        if not isinstance(value, str):
            raise ValueError("Class must be a string!")

        if value not in ['Standard', 'Safety']:
            raise ValueError("Class must be one of: Standard, Safety!")

        self['@Class'] = value

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
        if not self.is_valid_string(value) or not value:
            raise ValueError("Data type must be a valid string!")

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
    def dimensions(self) -> str:
        """get the dimensions of this tag

        Returns:
            :class:`str`: dimensions of this datatype
        """
        return self['@Dimensions']

    @dimensions.setter
    def dimensions(self, value: Union[str, int]):
        if isinstance(value, int):
            if value < 0:
                raise ValueError("Dimensions must be a positive integer!")
            value = str(value)

        if not isinstance(value, str):
            raise ValueError("Dimensions must be a string or an integer!")

        self['@Dimensions'] = value

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
            return []

        endpoints = datatype.endpoint_operands
        if not endpoints:
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

        Returns:
            :class:`str`: alias string of this tag
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


class ControllerSafetyInfo(PlcObject):
    def __init__(self,
                 meta_data: str,
                 controller: 'Controller'):
        super().__init__(meta_data=meta_data,
                         controller=controller)

    @property
    def safety_locked(self) -> str:
        return self['@SafetyLocked']

    @safety_locked.setter
    def safety_locked(self, value: str):
        if not self.is_valid_rockwell_bool(value):
            raise ValueError("Safety locked must be a valid boolean string (true/false)!")

        self['@SafetyLocked'] = value

    @property
    def signature_runmode_protect(self) -> str:
        return self['@SignatureRunModeProtect']

    @signature_runmode_protect.setter
    def signature_runmode_protect(self, value: str):
        if not self.is_valid_rockwell_bool(value):
            raise ValueError("Signature run mode protect must be a valid boolean string (true/false)!")

        self['@SignatureRunModeProtect'] = value

    @property
    def configure_safety_io_always(self) -> str:
        return self['@ConfigureSafetyIOAlways']

    @configure_safety_io_always.setter
    def configure_safety_io_always(self, value: str):
        if not self.is_valid_rockwell_bool(value):
            raise ValueError("Configure safety IO always must be a valid boolean string (true/false)!")

        self['@ConfigureSafetyIOAlways'] = value

    @property
    def safety_level(self) -> str:
        return self['@SafetyLevel']

    @safety_level.setter
    def safety_level(self, value: str):
        if not isinstance(value, str):
            raise ValueError("Safety level must be a string!")

        if not any(x in value for x in ['SIL1', 'SIL2', 'SIL3', 'SIL4']):
            raise ValueError("Safety level must contain one of: SIL1, SIL2, SIL3, SIL4!")

        self['@SafetyLevel'] = value

    @property
    def safety_tag_map(self) -> str:
        if self['SafetyTagMap'] is None:
            return ''

        return self['SafetyTagMap']

    @safety_tag_map.setter
    def safety_tag_map(self, value: str):
        if not isinstance(value, str):
            raise ValueError("Safety tag map must be a string!")

        if not value:
            self['SafetyTagMap'] = None
            return

        # Validate format: should be "tag_name=safety_tag_name, ..."
        pairs = value.split(',')
        for pair in pairs:
            pair = pair.strip()
            if not pair:
                continue
            if '=' not in pair or len(pair.split('=')) != 2:
                raise ValueError("Safety tag map must be in the format 'tag_name=safety_tag_name, ...'")

        self['SafetyTagMap'] = value.strip()

    @property
    def safety_tag_map_dict_list(self) -> list[dict]:
        if not self.safety_tag_map:
            return self.safety_tag_map

        if not isinstance(self.safety_tag_map, str):
            raise ValueError("Safety tag map must be a string!")

        string_data = self.safety_tag_map.strip().split(',')
        if len(string_data) == 1 and string_data[0] == '':
            return []

        dict_list = []
        for pair in string_data:
            dict_list.append({
                '@Name': pair.split('=')[0].strip(),
                'TagName': pair.split('=')[0].strip(),
                'SafetyTagName': pair.split('=')[1].strip()
            })

        return dict_list

    def add_safety_tag_mapping(
        self,
        tag_name: str,
        safety_tag_name: str
    ) -> None:
        """Add a new safety tag mapping to the safety tag map.

        Args:
            tag_name (str): The standard tag name
            safety_tag_name (str): The corresponding safety tag name

        Raises:
            ValueError: If tag names are not strings
        """
        if not isinstance(tag_name, str) or not isinstance(safety_tag_name, str):
            raise ValueError("Tag names must be strings!")

        if not self.safety_tag_map:
            self.safety_tag_map = f"{tag_name}={safety_tag_name}"
            return

        self.safety_tag_map = self.safety_tag_map.strip()
        if f',{tag_name}={safety_tag_name}' in self.safety_tag_map:
            self.safety_tag_map = self.safety_tag_map.replace(f",{tag_name}={safety_tag_name}", '')
        elif f"{tag_name}={safety_tag_name}," in self.safety_tag_map:
            self.safety_tag_map = self.safety_tag_map.replace(f"{tag_name}={safety_tag_name},", '')
        self.safety_tag_map += f",{tag_name}={safety_tag_name}"

    def remove_safety_tag_mapping(
        self,
        tag_name: str,
        safety_tag_name: str
    ) -> None:
        """Remove a safety tag mapping from the safety tag map.

        Args:
            tag_name (str): The standard tag name
            safety_tag_name (str): The corresponding safety tag name
        Raises:
            ValueError: If tag names are not strings
        """
        if not isinstance(tag_name, str) or not isinstance(safety_tag_name, str):
            raise ValueError("Tag names must be strings!")

        if not self.safety_tag_map:
            return

        self.safety_tag_map = self.safety_tag_map.strip()
        if f",{tag_name}={safety_tag_name}" in self.safety_tag_map:
            self.safety_tag_map = self.safety_tag_map.replace(f",{tag_name}={safety_tag_name}", '')
        elif f"{tag_name}={safety_tag_name}," in self.safety_tag_map:
            self.safety_tag_map = self.safety_tag_map.replace(f"{tag_name}={safety_tag_name},", '')
        elif f"{tag_name}={safety_tag_name}" in self.safety_tag_map:
            self.safety_tag_map = self.safety_tag_map.replace(f"{tag_name}={safety_tag_name}", '')

        if not self.safety_tag_map:
            self.safety_tag_map = None


@dataclass
class ControllerConfiguration:
    aoi_type: type = AddOnInstruction
    datatype_type: type = Datatype
    module_type: type = Module
    program_type: type = Program
    routine_type: type = Routine
    rung_type: type = Rung
    tag_type: type = Tag


class ControllerMeta(FactoryTypeMeta):
    """Metaclass for auto-registering Controller subclasses."""

    @classmethod
    def get_class(cls) -> Type['Controller']:
        try:
            return Controller
        except Exception:
            return None

    @classmethod
    def get_factory(cls):
        return ControllerFactory


class ControllerFactory(MetaFactory):
    """Controller factory with scoring-based matching."""

    _registered_types: dict = {}

    @classmethod
    def get_best_match(
        cls,
        controller_data: dict,
        min_score: float = 0.3
    ) -> Type:
        """Get the best matching controller type based on scoring."""
        if not controller_data:
            cls.logger.warning("No controller data provided")
            return None

        scored_matches: List[Tuple[float, Type]] = []

        for _, matcher in ControllerMatcherFactory.get_registered_types().items():
            score = matcher.calculate_score(controller_data)
            ctrl_class = matcher.get_controller_constructor()
            if score >= min_score:
                scored_matches.append((score, matcher.get_controller_constructor()))
                cls.get_logger().info(
                    f"Matched {ctrl_class.__name__} with score {score:.2f}"
                )
            else:
                cls.get_logger().info(
                    f"{ctrl_class.__name__} score {score:.2f} below min score {min_score}"
                )

        if not scored_matches:
            cls.get_logger().info(f"No matches found above min score {min_score}")
            return None

        # Sort by score (highest first) and return the best match
        scored_matches.sort(key=lambda x: x[0], reverse=True)
        best_score, best_class = scored_matches[0]

        cls.get_logger().info(f"Best match: {best_class} with score {best_score:.2f}")
        return best_class

    @classmethod
    def create_controller(
        cls,
        controller_data: dict,
        **kwargs
    ) -> object:
        """Create the best matching controller instance."""
        controller_class = cls.get_best_match(controller_data)
        if not controller_class:
            return None
        return controller_class(meta_data=controller_data, **kwargs)


class Controller(NamedPlcObject, Loggable, metaclass=ControllerMeta):
    """Controller container for Allen Bradley L5X Files.
    .. ------------------------------------------------------------

    .. package:: emulation_preparation.types.plc

    .. ------------------------------------------------------------
    """

    generator_type = 'EmulationGenerator'

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if key == '@MajorRev' or key == '@MinorRev':
            self.logger.info('Changing revisions of processor...')
            self.content_meta_data['@SoftwareRevision'] = f'{self.controller.major_revision}.{self.controller.minor_revision}'
            self.plc_module['@Major'] = self.major_revision
            self.plc_module['@Minor'] = self.minor_revision

    def __init__(self,
                 meta_data: str = None,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 config: Optional[ControllerConfiguration] = None,
                 file_location: Optional[str] = None,
                 ip_address: Optional[str] = None,
                 slot: Optional[int] = 0,
                 compile_immediately: bool = False):

        self._root_meta_data: dict = meta_data or l5x_dict_from_file(PLC_ROOT_FILE)
        self._file_location, self._ip_address, self._slot = file_location, ip_address, slot
        self._config = config or ControllerConfiguration()

        NamedPlcObject.__init__(self,
                                meta_data=self.l5x_meta_data,
                                name=name,
                                description=description,
                                controller=self)
        Loggable.__init__(self)
        self._aois: Optional[HashList[AddOnInstruction]] = None
        self._datatypes: Optional[HashList[Datatype]] = None
        self._modules: Optional[HashList[Module]] = None
        self._programs: Optional[HashList[Program]] = None
        self._tags: Optional[HashList[Tag]] = None
        self._safety_info: Optional[ControllerSafetyInfo] = None

        if compile_immediately:
            self._compile_from_meta_data()

    @property
    def aois(self) -> HashList[AddOnInstruction]:
        if not self._aois:
            self._compile_aois()
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
        if not self._datatypes:
            self._compile_datatypes()
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

        Returns:
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
        if not self._modules:
            self._compile_modules()
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
        if not self._programs:
            self._compile_programs()
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
    def safety_info(self) -> Optional[ControllerSafetyInfo]:
        if not self._safety_info:
            self._compile_safety_info()
        return self._safety_info

    @property
    def safety_programs(self) -> list[Program]:
        val = [x for x in self.programs if x.class_ == 'Safety']
        val.sort(key=lambda x: x.name)
        return val

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
    def standard_programs(self) -> list[Program]:
        val = [x for x in self.programs if x.class_ == 'Standard']
        val.sort(key=lambda x: x.name)
        return val

    @property
    def tags(self) -> HashList[Tag]:
        if not self._tags:
            self._compile_tags()
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
    def from_file(
        cls: Self,
        file_location: str
    ) -> Optional[Self]:
        """Create a Controller instance from an L5X file.

        Args:
            file_location (str): The file path to the L5X file.

        Returns:
            Optional[Controller]: The created Controller instance, or None if the file could not be read.
        """
        root_data = l5x_dict_from_file(file_location)
        if not root_data:
            return None

        ctrl = ControllerFactory.create_controller(root_data)
        if not ctrl:
            print('Could not determine controller type from file! Creating generic controller')
            ctrl = cls(
                meta_data=root_data,
                file_location=file_location
            )
        return ctrl

    @classmethod
    def from_meta_data(
        cls: Self,
        meta_data: dict,
        config: Optional[ControllerConfiguration] = None
    ) -> Self:
        """Create a Controller instance from meta data.

        Args:
            meta_data (dict): The meta data dictionary to create the controller from.
            config (ControllerConfiguration, optional): Configuration for custom types. Defaults to None.

        Returns:
            Controller: The created Controller instance.

        Raises:
            ValueError: If meta_data is None or not a dictionary
            \n\tor if required keys are missing
            \n\tor if config is not a ControllerConfiguration instance.
        """
        if not meta_data:
            raise ValueError('Meta data cannot be None!')
        if not isinstance(meta_data, dict):
            raise ValueError('Meta data must be a dictionary!')
        if 'RSLogix5000Content' not in meta_data:
            raise ValueError('Meta data must contain RSLogix5000Content!')
        if 'Controller' not in meta_data['RSLogix5000Content']:
            raise ValueError('Meta data must contain Controller!')
        if not config:
            config = ControllerConfiguration()
        if not isinstance(config, ControllerConfiguration):
            raise ValueError('Config must be an instance of ControllerConfiguration!')
        controller = cls(meta_data=meta_data,
                         config=config)
        return controller

    def _compile_aois(self) -> None:
        """Compile Add-On Instructions from the controller's AOIs.
        """
        self.logger.debug('Compiling AOIs from controller...')
        if self._aois is None:
            self._aois = HashList('name')
            for aoi in self.raw_aois:
                if isinstance(aoi, dict):
                    self._aois.append(
                        self.config.aoi_type(
                            meta_data=aoi,
                            controller=self
                        )
                    )
                else:
                    self.logger.warning(f'Invalid AOI data: {aoi}. Skipping...')

    def _compile_atomic_datatypes(self) -> None:
        """Compile atomic datatypes from the controller's datatypes."""
        self._datatypes.append(Datatype(meta_data={'@Name': 'BOOL'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'BIT'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'SINT'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'INT'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'DINT'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'LINT'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'USINT'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'UINT'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'UDINT'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'ULINT'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'REAL'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'LREAL'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'STRING'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'TIMER',
                                                   'Members': {'Member': [
                                                       {'@Name': 'PRE'},
                                                       {'@Name': 'ACC'},
                                                       {'@Name': 'EN'},
                                                       {'@Name': 'TT'},
                                                       {'@Name': 'DN'}
                                                   ]}}, controller=self))

    def _compile_datatypes(self) -> None:
        """Compile datatypes from the controller's datatypes."""
        self.logger.debug('Compiling datatypes from controller...')
        if self._datatypes is None:
            self._datatypes = HashList('name')
            self._compile_atomic_datatypes()
            for datatype in self.raw_datatypes:
                if isinstance(datatype, dict):
                    self._datatypes.append(
                        self.config.datatype_type(
                            meta_data=datatype,
                            controller=self
                        ))
                else:
                    self.logger.warning(
                        f'Invalid datatype data: {datatype}. Skipping...'
                    )

    def _compile_from_meta_data(self):
        """Compile this controller from its meta data."""
        self.logger.info('Compiling controller from meta data...')
        self._aois = None
        self._compile_aois()

        self._datatypes = None
        self._compile_datatypes()

        self._modules = None
        self._compile_modules()

        self._programs = None
        self._compile_programs()

        self._tags = None
        self._compile_tags()

        self._safety_info = None
        self._compile_safety_info()

    def _compile_modules(self) -> None:
        """Compile modules from the controller's modules."""
        self.logger.debug('Compiling modules from controller...')
        if self._modules is None:
            self._modules = HashList('name')
            for module in self.raw_modules:
                if isinstance(module, dict):
                    self._modules.append(
                        self.config.module_type(
                            l5x_meta_data=module,
                            controller=self
                        ))
                else:
                    self.logger.warning(f'Invalid module data: {module}. Skipping...')

    def _compile_programs(self) -> None:
        """Compile programs from the controller's programs."""
        self.logger.debug('Compiling programs from controller...')
        if self._programs is None:
            self._programs = HashList('name')
            for program in self.raw_programs:
                if isinstance(program, dict):
                    self._programs.append(
                        self.config.program_type(
                            meta_data=program,
                            controller=self
                        ))
                else:
                    self.logger.warning(f'Invalid program data: {program}. Skipping...')

    def _compile_tags(self) -> None:
        """Compile tags from the controller's tags."""
        self.logger.debug('Compiling tags from controller...')
        if self._tags is None:
            self._tags = HashList('name')
            for tag in self.raw_tags:
                if isinstance(tag, dict):
                    self._tags.append(
                        self.config.tag_type(
                            meta_data=tag,
                            controller=self,
                            container=self
                        ))
                else:
                    self.logger.warning(f'Invalid tag data: {tag}. Skipping...')

    def _compile_safety_info(self) -> None:
        """Compile safety information from the controller's safety info."""
        self.logger.debug('Compiling safety info from controller...')
        if self._safety_info is None:
            safety_info_data = self.content_meta_data['Controller'].get('SafetyInfo', None)
            if safety_info_data:
                self._safety_info = ControllerSafetyInfo(
                    meta_data=safety_info_data,
                    controller=self
                )
            else:
                self.logger.warning('No SafetyInfo found in controller metadata.')

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
            self.logger.debug(f'{item.name} already exists in this collection. Updating...')
            meta_item = next((x for x in target_meta_list if x['@Name'] == item.name), None)
            if not meta_item:
                raise ValueError(f'{item.name} not found in target meta list!')
            target_meta_list.remove(meta_item)

        target_meta_list.append(item.meta_data)
        self._invalidate_list_cache(target_list)

    def _remove_common(
        self,
        item: PlcObject,
        target_list: HashList,
        target_meta_list: list[dict]
    ) -> None:
        """Remove an item from the controller's collection."""
        if not isinstance(item, PlcObject):
            raise TypeError(f"{item.name} must be of type PlcObject!")

        if item.name not in target_list:
            self.logger.warning(f'{item.name} does not exist in this collection. Cannot remove.')
            return

        target_meta_list.remove(next((x for x in target_meta_list if x['@Name'] == item.name), None))
        self._invalidate_list_cache(target_list)

    def _invalidate_list_cache(
        self,
        target_list: HashList
    ) -> None:
        """Invalidate the cached list."""
        if target_list is self.aois:
            self._aois = None
        elif target_list is self.datatypes:
            self._datatypes = None
        elif target_list is self.modules:
            self._modules = None
        elif target_list is self.programs:
            self._programs = None
        elif target_list is self.tags:
            self._tags = None
        else:
            raise ValueError('Unknown target list!')

    def import_assets_from_file(
        self,
        file_location: str,
        asset_types: Optional[List[str]] = L5X_ASSETS
    ) -> None:
        """Import assets from an L5X file into this controller.
            .. -------------------------------
            .. arguments::
            :class:`str` file_location:
                the L5X file to import from
            :class:`list[str]` asset_types:
                the types of assets to import (e.g., ['DataTypes', 'Tags'])
            """
        l5x_dict = l5x_dict_from_file(file_location)
        if not l5x_dict:
            self.logger.warning(f'No L5X dictionary could be read from file: {file_location}')
            return

        self.import_assets_from_l5x_dict(l5x_dict, asset_types=asset_types)

    def import_assets_from_l5x_dict(
        self,
        l5x_dict: dict,
        asset_types: Optional[List[str]] = L5X_ASSETS
    ) -> None:
        """Import assets from an L5X dictionary into this controller.
            .. -------------------------------
            .. arguments::
            :class:`dict` l5x_dict:
                the L5X dictionary to import from
            :class:`list[str]` asset_types:
                the types of assets to import (e.g., ['DataTypes', 'Tags'])
            """
        if not l5x_dict:
            self.logger.warning('No L5X dictionary provided for import.')
            return

        if 'RSLogix5000Content' not in l5x_dict:
            self.logger.warning('No RSLogix5000Content found in provided L5X dictionary.')
            return
        if 'Controller' not in l5x_dict['RSLogix5000Content']:
            self.logger.warning('No Controller found in RSLogix5000Content in provided L5X dictionary.')
            return

        controller_data = l5x_dict['RSLogix5000Content']['Controller']

        for asset_type in asset_types:
            if asset_type not in controller_data:
                self.logger.warning(f'No {asset_type} found in Controller in provided L5X dictionary.')
                continue

            items = controller_data[asset_type]

            item_list = items.get(asset_type[:-1], [])
            if not isinstance(item_list, list):
                item_list = [item_list]

            for item in item_list:
                try:
                    match asset_type:
                        case 'DataTypes':
                            datatype = self.config.datatype_type(controller=self, meta_data=item)
                            self.add_datatype(datatype)
                            self.logger.info(f'Datatype {datatype.name} imported successfully.')
                        case 'Tags':
                            tag = self.config.tag_type(controller=self, meta_data=item, container=self)
                            self.add_tag(tag)
                            self.logger.info(f'Tag {tag.name} imported successfully.')
                        case 'Programs':
                            program = self.config.program_type(controller=self, meta_data=item)
                            self.add_program(program)
                            self.logger.info(f'Program {program.name} imported successfully.')
                        case 'AddOnInstructionDefinitions':
                            aoi = self.config.aoi_type(controller=self, meta_data=item)
                            self.add_aoi(aoi)
                            self.logger.info(f'AOI {aoi.name} imported successfully.')
                        case 'Modules':
                            module = self.config.module_type(controller=self, l5x_meta_data=item)
                            self.add_module(module)
                            self.logger.info(f'Module {module.name} imported successfully.')
                        case _:
                            self.logger.warning(f'Unknown asset type: {asset_type}. Skipping...')
                except ValueError as e:
                    self.logger.warning(f'Failed to add {asset_type[:-1]}:\n{e}')
                    continue

    def add_aoi(
        self,
        aoi: AddOnInstruction
    ) -> None:
        """Add an AOI to this controller.
        .. -------------------------------
        .. arguments::
        :class:`AddOnInstruction` aoi:
            the AOI to add
        """
        self._add_common(aoi,
                         self.config.aoi_type,
                         self.aois,
                         self.raw_aois)

    def add_datatype(
        self,
        datatype: Datatype,
    ) -> None:
        """Add a datatype to this controller.
        .. -------------------------------
        .. arguments::
        :class:`Datatype` datatype:
            the datatype to add
        """
        self._add_common(datatype,
                         self.config.datatype_type,
                         self.datatypes,
                         self.raw_datatypes)

    def add_module(
        self,
        module: Module
    ) -> None:
        """Add a module to this controller.
        .. -------------------------------
        .. arguments::
        :class:`Module` module:
            the module to add
        """
        self._add_common(module,
                         self.config.module_type,
                         self.modules,
                         self.raw_modules)

    def add_program(
        self,
        program: Program
    ) -> None:
        """Add a program to this controller.
        .. -------------------------------
        .. arguments::
        :class:`Program` program:
            the program to add
        """
        self._add_common(program,
                         self.config.program_type,
                         self.programs,
                         self.raw_programs)

    def add_tag(
        self,
        tag: Tag
    ) -> None:
        """Add a tag to this controller.
        .. -------------------------------
        .. arguments::
        :class:`Tag` tag:
            the tag to add
        """
        self._add_common(
            tag,
            self.config.tag_type,
            self.tags,
            self.raw_tags
        )

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

    def remove_aoi(self, aoi: AddOnInstruction):
        self._remove_common(aoi, self.aois, self.raw_aois)

    def remove_datatype(self, datatype: Datatype):
        self._remove_common(datatype, self.datatypes, self.raw_datatypes)

    def remove_module(self, module: Module):
        self._remove_common(module, self.modules, self.raw_modules)

    def remove_program(self, program: Program):
        self._remove_common(program, self.programs, self.raw_programs)

    def remove_tag(self, tag: Tag):
        self._remove_common(tag, self.tags, self.raw_tags)

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


class ControllerModificationSchema(Loggable):
    """
    Defines a schema for modifying a controller, such as migrating assets between controllers,
    or importing assets from an L5X dictionary.
    """

    def __init__(
        self,
        source: Controller,
        destination: Controller
    ) -> None:
        super().__init__()
        self.source = source
        self.destination = destination
        self.actions = []  # List of migration actions

    def _execute_add_controller_tag(
        self,
        action: dict
    ) -> None:
        tag_data = action.get('asset')
        if not tag_data:
            self.logger.warning('No tag data provided for add_controller_tag action.')
            return

        config = self.destination.config

        tag = config.tag_type(
            meta_data=tag_data,
            controller=self.destination,
            container=self.destination
        )

        try:
            self.destination.add_tag(tag)
            self.logger.info(f'Added tag {tag.name} to destination controller.')
        except ValueError as e:
            self.logger.warning(f'Failed to add tag {tag.name}:\n{e}')

    def _execute_add_datatype(
        self,
        action: dict
    ) -> None:
        datatype_data = action.get('asset')
        if not datatype_data:
            self.logger.warning('No datatype data provided for add_datatype action.')
            return

        config = self.destination.config

        datatype = config.datatype_type(
            meta_data=datatype_data,
            controller=self.destination
        )

        try:
            self.destination.add_datatype(datatype)
            self.logger.info(f'Added datatype {datatype.name} to destination controller.')
        except ValueError as e:
            self.logger.warning(f'Failed to add datatype {datatype.name}:\n{e}')

    def _execute_add_program_tag(
        self,
        action: dict
    ) -> None:
        program_name = action.get('program')
        tag_data = action.get('asset')
        if not program_name or not tag_data:
            self.logger.warning('Program name or tag data missing for add_program_tag action.')
            return

        program: Program = self.destination.programs.get(program_name)
        if not program:
            self.logger.warning(f'Program {program_name} not found in destination controller.')
            return

        config = self.destination.config

        tag = config.tag_type(
            meta_data=tag_data,
            controller=self.destination,
            container=program
        )

        try:
            program.add_tag(tag)
            self.logger.info(f'Added tag {tag.name} to program {program_name}.')
        except ValueError as e:
            self.logger.warning(f'Failed to add tag {tag.name} to program {program_name}:\n{e}')

    def _execute_add_routine(
        self,
        action: dict
    ) -> None:
        program_name = action.get('program')
        routine_data = action.get('routine')
        if not program_name or not routine_data:
            self.logger.warning('Program name or routine data missing for add_routine action.')
            return

        program: Program = self.destination.programs.get(program_name)
        if not program:
            self.logger.warning(f'Program {program_name} not found in destination controller.')
            return

        config = self.destination.config

        routine = config.routine_type(
            meta_data=routine_data,
            program=program
        )

        try:
            program.add_routine(routine)
            self.logger.info(f'Added routine {routine.name} to program {program_name}.')
        except ValueError as e:
            self.logger.warning(f'Failed to add routine {routine.name} to program {program_name}:\n{e}')

    def _execute_add_rung(
        self,
        action: dict
    ) -> None:
        program_name = action.get('program')
        routine_name = action.get('routine')
        rung_data = action.get('new_rung')
        rung_number = action.get('rung_number')
        if not program_name or not routine_name or not rung_data:
            self.logger.warning('Program name, routine name, or rung data missing for add_rung action.')
            return

        program: Program = self.destination.programs.get(program_name)
        if not program:
            self.logger.warning(f'Program {program_name} not found in destination controller.')
            return

        routine: Routine = program.routines.get(routine_name)
        if not routine:
            self.logger.warning(f'Routine {routine_name} not found in program {program_name}.')
            return

        config = self.destination.config

        rung = config.rung_type(
            meta_data=rung_data,
            routine=routine,
            rung_number=rung_number
        )

        try:
            routine.add_rung(rung, index=rung_number)
            self.logger.info(f'Added rung {rung.number} to routine {routine_name} in program {program_name}.')
        except ValueError as e:
            self.logger.warning(f'Failed to add rung {rung.number} to routine {routine_name} in program {program_name}:\n{e}')

    def _execute_add_safety_tag_mapping(
        self,
        action: dict
    ) -> None:
        std_tag = action.get('standard')
        sfty_tag = action.get('safety')
        if not std_tag or not sfty_tag:
            self.logger.warning('Standard or safety tag missing for add_safety_tag_mapping action.')
            return

        try:
            self.destination.safety_info.add_safety_tag_mapping(std_tag, sfty_tag)
            self.logger.info(f'Added safety tag mapping: {std_tag} -> {sfty_tag}')
        except ValueError as e:
            self.logger.warning(f'Failed to add safety tag mapping {std_tag} -> {sfty_tag}:\n{e}')

    def _execute_controller_tag_migration(
        self,
        action: dict
    ) -> None:
        tag_name = action.get('name')
        tag: Tag = self.source.tags.get(tag_name)
        if not tag:
            self.logger.warning(f'Tag {tag_name} not found in source controller.')
            return

        try:
            self.destination.add_tag(tag)
            self.logger.info(f'Migrated tag {tag_name} to destination controller.')
        except ValueError as e:
            self.logger.warning(f'Failed to migrate tag {tag_name}:\n{e}')

    def _execute_datatype_migration(
        self,
        action: dict
    ) -> None:
        datatype_name = action.get('name')
        datatype: Datatype = self.source.datatypes.get(datatype_name)
        if not datatype:
            self.logger.warning(f'Datatype {datatype_name} not found in source controller.')
            return

        try:
            self.destination.add_datatype(datatype)
            self.logger.info(f'Migrated datatype {datatype_name} to destination controller.')
        except ValueError as e:
            self.logger.warning(f'Failed to migrate datatype {datatype_name}:\n{e}')

    def _execute_import_assets_from_file(
        self,
        action: dict
    ) -> None:
        file_location = action.get('file')
        asset_types = action.get('asset_types', L5X_ASSETS)
        if not file_location:
            self.logger.warning('No file location provided for import_datatypes_from_file action.')
            return

        try:
            self.destination.import_assets_from_file(file_location, asset_types)
            self.logger.info(f'Imported assets from file {file_location} to destination controller.')
        except Exception as e:
            self.logger.warning(f'Failed to import assets from file {file_location}:\n{e}')
            raise e

    def _execute_import_assets_from_l5x_dict(
        self,
        action: dict
    ) -> None:
        l5x_dict = action.get('l5x_dict')
        asset_types = action.get('asset_types', L5X_ASSETS)
        if not l5x_dict:
            self.logger.warning('No L5X dictionary provided for import_assets_from_l5x_dict action.')
            return

        try:
            self.destination.import_assets_from_l5x_dict(l5x_dict, asset_types)
            self.logger.info('Imported assets from L5X dictionary to destination controller.')
        except Exception as e:
            self.logger.warning(f'Failed to import assets from L5X dictionary:\n{e}')
            raise e

    def _execute_remove_controller_tag(
        self,
        action: dict
    ) -> None:
        tag_name = action.get('name')
        tag: Tag = self.destination.tags.get(tag_name)
        if not tag:
            self.logger.warning(f'Tag {tag_name} not found in destination controller.')
            return

        self.destination.remove_tag(tag)
        self.logger.info(f'Removed tag {tag_name} from destination controller.')

    def _execute_remove_datatype(
        self,
        action: dict
    ) -> None:
        datatype_name = action.get('name')
        datatype: Datatype = self.destination.datatypes.get(datatype_name)
        if not datatype:
            self.logger.warning(f'Datatype {datatype_name} not found in destination controller.')
            return

        self.destination.remove_datatype(datatype)
        self.logger.info(f'Removed datatype {datatype_name} from destination controller.')

    def _execute_remove_program_tag(
        self,
        action: dict
    ) -> None:
        program_name = action.get('program')
        tag_name = action.get('name')

        program: Program = self.destination.programs.get(program_name)
        if not program:
            self.logger.warning(f'Program {program_name} not found in destination controller.')
            return

        tag: Tag = program.tags.get(tag_name)
        if not tag:
            self.logger.warning(f'Tag {tag_name} not found in program {program_name}.')
            return

        program.remove_tag(tag)
        self.logger.info(f'Removed tag {tag_name} from program {program_name}.')

    def _execute_remove_routine(
        self,
        action: dict
    ) -> None:
        program_name = action.get('program')
        routine_name = action.get('name')

        program: Program = self.destination.programs.get(program_name)
        if not program:
            self.logger.warning(f'Program {program_name} not found in destination controller.')
            return

        routine: Routine = program.routines.get(routine_name)
        if not routine:
            self.logger.warning(f'Routine {routine_name} not found in program {program_name}.')
            return

        program.remove_routine(routine)
        self.logger.info(f'Removed routine {routine_name} from program {program_name}.')
        self.logger.debug('Searching for JSR instructions to %s...', routine_name)
        jsr = program.get_instructions('JSR', routine_name)
        if jsr:
            for op in jsr:
                rung: Rung = op.rung
                if not rung:
                    raise ValueError('JSR instruction has no parent rung!')
                jsr_routine: Routine = program.routines.get(rung.routine.name)
                self.logger.debug('Found JSR in rung %s of routine %s. Removing rung...', rung.number, jsr_routine.name)
                jsr_routine.remove_rung(rung)

    def _execute_remove_safety_tag_mapping(
        self,
        action: dict
    ) -> None:
        std_tag = action.get('standard')
        sfty_tag = action.get('safety')
        self.logger.debug(f'Removing safety tag mapping: {std_tag} -> {sfty_tag}')
        self.destination.safety_info.remove_safety_tag_mapping(std_tag, sfty_tag)

    def _execute_routine_migration(
        self,
        action: dict
    ) -> None:
        source_program_name = action.get('source_program')
        destination_program_name = action.get('destination_program')
        routine_name = action.get('routine')
        rung_updates = action.get('rung_updates', {})

        source_program: Program = self.source.programs.get(source_program_name)
        if not source_program:
            self.logger.warning(f'Program {source_program_name} not found in source controller.')
            return

        source_routine: Routine = source_program.routines.get(routine_name)
        if not source_routine:
            self.logger.warning(f'Routine {routine_name} not found in program {source_program_name}.')
            return

        destination_program: Program = self.destination.programs.get(destination_program_name)
        if not destination_program:
            self.logger.warning(f'Program {destination_program_name} not found in destination controller.')
            return

        destination_program.add_routine(source_routine)
        self.logger.info(f'Migrated routine {routine_name} from program {source_program_name} to program {destination_program_name}.')

        dest_routine = self.destination.programs.get(destination_program_name).routines.get(routine_name)
        for rung_num, new_rung in rung_updates.items():
            dest_routine.rungs[rung_num] = new_rung
            self.logger.info(f'Updated rung {rung_num} in routine {routine_name} of program {destination_program_name}.')

    def _safe_register_action(
        self,
        action: dict
    ) -> None:
        if action not in self.actions:
            self.actions.append(action)
        else:
            self.logger.debug('Action already registered, skipping duplicate.')

    def add_controller_tag(
        self,
        tag: Tag
    ) -> None:
        """Add an individual tag to import directly to the destination controller.

        Args:
            tag (Tag): The tag to add.

        Raises:
            ValueError: If the provided tag is not an instance of the Tag class.
        """
        if not isinstance(tag, Tag):
            raise ValueError('Tag must be an instance of Tag class.')
        self._safe_register_action({
            'type': 'add_controller_tag',
            'asset': tag.meta_data,
            'method': self._execute_add_controller_tag
        })

    def add_controller_tag_migration(
        self,
        tag_name: str
    ) -> None:
        """Specify a tag to migrate from source to destination.

        Args:
            tag_name (str): The name of the tag to migrate.
        """
        self._safe_register_action({
            'type': 'migrate_controller_tag',
            'name': tag_name,
            'method': self._execute_controller_tag_migration
        })

    def add_datatype_migration(
        self,
        datatype_name: str
    ) -> None:
        """Specify a datatype to migrate from source to destination.

        Args:
            datatype_name (str): The name of the datatype to migrate.
        """
        self._safe_register_action({
            'type': 'migrate_datatype',
            'name': datatype_name,
            'method': self._execute_datatype_migration
        })

    def add_program_tag(
        self,
        program_name: str,
        tag: Tag
    ) -> None:
        """Add a tag to import directly to the destination controller within a specific program.

        Args:
            program_name (str): The name of the program to add the tag to.
            tag (Tag): The tag to add.

        Raises:
            ValueError: If the provided tag is not an instance of the Tag class.
        """
        if not isinstance(tag, Tag):
            raise ValueError('Tag must be an instance of Tag class.')
        self._safe_register_action({
            'type': 'add_program_tag',
            'program': program_name,
            'asset': tag.meta_data,
            'method': self._execute_add_program_tag
        })

    def add_routine(
        self,
        program_name: str,
        routine: Routine
    ) -> None:
        """Add a routine to import directly to the destination controller.

        Args:
            program_name (str): The name of the program to add the routine to.
            routine (Routine): The routine to add.

        Raises:
            ValueError: If the provided routine is not an instance of the Routine class.
        """
        if not isinstance(routine, Routine):
            raise ValueError('Routine must be an instance of Routine class.')
        self._safe_register_action({
            'type': 'add_routine',
            'program': program_name,
            'routine': routine.meta_data,
            'method': self._execute_add_routine
        })

    def add_routine_migration(
        self,
        source_program_name: str,
        routine_name: str,
        destination_program_name: str = None,
        rung_updates: dict = None
    ) -> None:
        """Specify a routine to migrate, with optional rung updates.

        Args:
            source_program_name (str): The name of the program containing the routine from the source controller.
            routine_name (str): The name of the routine to migrate.
            destination_program_name (str, optional): The name of the program to add the routine to in the destination controller.
                                                        \n\tIf None, uses the same program name as the source.
            rung_updates (dict, optional): A dictionary of rung updates to apply during migration.
        """
        self._safe_register_action({
            'type': 'migrate_routine',
            'source_program': source_program_name,
            'routine': routine_name,
            'destination_program': destination_program_name or source_program_name,
            'rung_updates': rung_updates or {},
            'method': self._execute_routine_migration
        })

    def add_rung(
        self,
        program_name: str,
        routine_name: str,
        new_rung: Rung,
        rung_number: Optional[int] = None
    ) -> None:
        """Add a rung to import directly to the destination controller.

        Args:
            program_name (str): The name of the program containing the routine.
            routine_name (str): The name of the routine to add the rung to.
            new_rung (Rung): The rung to add.
            rung_number (Optional[int]): The index at which to insert the new rung. If None, appends to the end.

        Raises:
            ValueError: If the provided rung is not an instance of the Rung class.
        """
        if not isinstance(new_rung, Rung):
            raise ValueError('Rung must be an instance of Rung class.')
        self._safe_register_action({
            'type': 'add_rung',
            'program': program_name,
            'routine': routine_name,
            'rung_number': rung_number,
            'new_rung': new_rung.meta_data,
            'method': self._execute_add_rung
        })

    def add_import_from_l5x_dict(
        self,
        l5x_dict: dict,
        asset_types: list[str] = L5X_ASSETS
    ) -> None:
        """
        Add actions to import assets from an L5X dictionary.

        Args:
            l5x_dict (dict): The L5X data as a dictionary.
            asset_types (list[str], optional): List of asset types to import, e.g. ['DataTypes', 'Tags', 'Programs'].
                                                \n\tDefaults to all if None.
        """

        self._safe_register_action({
            'type': 'import_from_l5x_dict',
            'l5x_dict': l5x_dict,
            'asset_types': asset_types,
            'method': self._execute_import_assets_from_l5x_dict
        })

    def add_import_from_file(
        self,
        file_location: str,
        asset_types: list[str] = L5X_ASSETS
    ) -> None:
        """
        Add actions to import assets from an L5X file.

        Args:
            file_location (str): The path to the L5X file.
            asset_types (list[str], optional): List of asset types to import, e.g. ['DataTypes', 'Tags', 'Programs'].
                                                \n\tDefaults to all if None.

        Raises:
            ValueError: If no valid L5X data is found in the specified file.
        """

        self._safe_register_action({
            'type': 'import_from_file',
            'file': file_location,
            'asset_types': asset_types,
            'method': self._execute_import_assets_from_file
        })

    def add_safety_tag_mapping(
        self,
        std_tag: str,
        sfty_tag: str
    ) -> None:
        """Add a mapping for tags from standard to safety code space.

        Args:
            std_tag (str): The standard tag name.
            sfty_tag (str): The safety tag name.

        Raises:
            ValueError: If either tag name is not a string.
        """
        if not isinstance(std_tag, str) or not isinstance(sfty_tag, str):
            raise ValueError('Source and destination tags must be strings.')
        self._safe_register_action({
            'type': 'safety_tag_mapping',
            'standard': std_tag,
            'safety': sfty_tag,
            'method': self._execute_add_safety_tag_mapping
        })

    def remove_controller_tag(
        self,
        tag_name: str
    ) -> None:
        """Specify a tag to remove from the destination controller.

        Args:
            tag_name (str): The name of the tag to remove.
        """
        self._safe_register_action({
            'type': 'remove_controller_tag',
            'name': tag_name,
            'method': self._execute_remove_controller_tag
        })

    def remove_datatype(
        self,
        datatype_name: str
    ) -> None:
        """Specify a datatype to remove from the destination controller.

        Args:
            datatype_name (str): The name of the datatype to remove.
        """
        self._safe_register_action({
            'type': 'remove_datatype',
            'name': datatype_name,
            'method': self._execute_remove_datatype
        })

    def remove_program_tag(
        self,
        program_name: str,
        tag_name: str
    ) -> None:
        """Specify a tag to remove from a specific program in the destination controller.

        Args:
            program_name (str): The name of the program containing the tag.
            tag_name (str): The name of the tag to remove.
        """
        self._safe_register_action({
            'type': 'remove_program_tag',
            'program': program_name,
            'name': tag_name,
            'method': self._execute_remove_program_tag
        })

    def remove_routine(
        self,
        program_name: str,
        routine_name: str
    ) -> None:
        """Specify a routine to remove from a specific program in the destination controller.

        Args:
            program_name (str): The name of the program containing the routine.
            routine_name (str): The name of the routine to remove.
        """
        self._safe_register_action({
            'type': 'remove_routine',
            'program': program_name,
            'name': routine_name,
            'method': self._execute_remove_routine
        })

    def remove_safety_tag_mapping(
        self,
        std_tag: str,
        sfty_tag: str
    ) -> None:
        """Specify a safety tag mapping to remove from the destination controller.

        Args:
            std_tag (str): The standard tag name.
            sfty_tag (str): The safety tag name.
        """
        self._safe_register_action({
            'type': 'remove_safety_tag_mapping',
            'standard': std_tag,
            'safety': sfty_tag,
            'method': self._execute_remove_safety_tag_mapping
        })

    def execute(self):
        """Perform all migration and import actions."""
        self.logger.info('Executing controller modification schema...')

        # call all action's methods
        for action in self.actions:
            method = action.get('method')
            if callable(method):
                method(action)
            else:
                self.logger.warning(f"No method defined for action type: {action['type']}. Skipping...")

        # Compile after all imports
        self.destination.compile()


def check_wildcard_patterns(
    items: List[str],
    patterns: List[str]
) -> bool:
    """Check if any item matches any wildcard pattern."""
    for item in items:
        for pattern in patterns:
            if fnmatch.fnmatch(item, pattern):
                return True
    return False


class ControllerMatcherFactory(MetaFactory):
    """Controller matcher factory."""

    _registered_types: dict = {}


class ControllerMatcherMeta(FactoryTypeMeta):
    """Metaclass for controller matchers."""

    @classmethod
    def get_class(cls) -> Type['ControllerMatcher']:
        try:
            return ControllerMatcher
        except NameError:
            return None

    @classmethod
    def get_factory(cls):
        return ControllerMatcherFactory


class ControllerMatcher(metaclass=ControllerMatcherMeta):
    """Abstract base class for controller matching strategies."""

    def get_datatype_patterns(self) -> List[str]:
        """List of patterns to identify the controller by datatype."""
        raise NotImplementedError("Subclasses must implement this method")

    def get_module_patterns(self) -> List[str]:
        """List of patterns to identify the controller by module."""
        raise NotImplementedError("Subclasses must implement this method")

    def get_program_patterns(self) -> List[str]:
        """List of patterns to identify the controller by program."""
        raise NotImplementedError("Subclasses must implement this method")

    def get_safety_program_patterns(self) -> List[str]:
        """List of patterns to identify the controller by safety program."""
        raise NotImplementedError("Subclasses must implement this method")

    def get_tag_patterns(self) -> List[str]:
        """List of patterns to identify the controller by tag."""
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    def calculate_score(
        cls,
        controller_data: dict
    ) -> float:
        """Calculate a matching score (0.0 to 1.0, higher is better).

        Args:
            controller_data (dict): The controller data to evaluate.
        """
        score = 0.0
        if cls.check_controller_datatypes(controller_data):
            score += 0.2
        if cls.check_controller_modules(controller_data):
            score += 0.2
        if cls.check_controller_programs(controller_data):
            score += 0.2
        if cls.check_controller_safety_programs(controller_data):
            score += 0.2
        if cls.check_controller_tags(controller_data):
            score += 0.2
        return score

    @classmethod
    def get_controller_constructor(
        cls,
    ) -> Type[Controller]:
        """Get the appropriate controller constructor for this matcher.

        Returns:
            Type[Controller]: The constructor for the appropriate controller type.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    def check_controller_datatypes(
        cls,
        controller_data: dict,
    ) -> bool:
        """Check if controller datatypes match controller pattern.

        Args:
            controller_data (dict): The controller data to evaluate.
        """
        return cls.check_dict_list_for_patterns(
            cls.get_controller_data_list(controller_data, 'DataType'),
            '@Name',
            cls.get_datatype_patterns()
        )

    @classmethod
    def check_controller_modules(
        cls,
        controller_data: dict,
    ) -> bool:
        """Check if controller modules match controller pattern."""
        return cls.check_dict_list_for_patterns(
            cls.get_controller_data_list(controller_data, 'Module'),
            '@Name',
            cls.get_module_patterns()
        )

    @classmethod
    def check_controller_programs(
        cls,
        controller_data: dict,
    ) -> bool:
        """Check if controller programs match controller pattern."""
        return cls.check_dict_list_for_patterns(
            cls.get_controller_data_list(controller_data, 'Program'),
            '@Name',
            cls.get_program_patterns()
        )

    @classmethod
    def check_controller_safety_programs(
        cls,
        controller_data: dict,
    ) -> bool:
        """Check if controller safety programs match controller pattern."""
        programs = cls.get_controller_data_list(controller_data, 'Program')
        safety_programs = [p for p in programs if p.get('@Class') == 'Safety']
        return cls.check_dict_list_for_patterns(
            safety_programs,
            '@Name',
            cls.get_safety_program_patterns()
        )

    @classmethod
    def check_controller_tags(
        cls,
        controller_data: dict,
    ) -> bool:
        """Check if controller tags match controller pattern."""
        return cls.check_dict_list_for_patterns(
            cls.get_controller_data_list(controller_data, 'Tag'),
            '@Name',
            cls.get_tag_patterns()
        )

    @classmethod
    def check_dict_list_for_patterns(
        cls,
        dict_list: List[dict],
        key: str,
        patterns: List[str]
    ) -> bool:
        """Check if any dictionary in the list has a value for the given key that matches any of the patterns.

        Args:
            dict_list (List[dict]): List of dictionaries to check.
            key (str): The key in the dictionary to check the value of.
            patterns (List[str]): List of patterns to match against the value.

        Returns:
            bool: True if any value matches any pattern, False otherwise.
        """
        if not patterns:
            return False
        cls.get_logger().debug(f"Checking patterns {patterns} in key '{key}' of dict list")
        result = check_wildcard_patterns(
            [item.get(key, '') for item in dict_list],
            patterns
        )
        cls.get_logger().debug(f"Pattern match result: {result}")
        return result

    @classmethod
    def get_controller_meta(
        cls,
        controller_data: dict
    ) -> dict:
        """Extract relevant metadata for the controller.

        Args:
        something
        """
        if not controller_data:
            raise ValueError("No controller data provided")
        return controller_data.get('RSLogix5000Content', {}).get('Controller', {})

    @classmethod
    def get_controller_data_list(
        cls,
        controller_data: dict,
        data_string: str,
    ) -> List[dict]:
        """Extract the list of data from the controller data.

        Args:
            controller_data (dict): The controller data to extract from.
            data_string (str): The key string to extract (e.g., 'Program', 'Tag').

        Returns:
            List[dict]: The list of data dictionaries.
        """
        controller_meta = cls.get_controller_meta(controller_data)
        data_list = controller_meta.get(f'{data_string}s', {}).get(data_string, [])
        if isinstance(data_list, dict):
            data_list = [data_list]
        return data_list


class ModuleWarehouseFactory(MetaFactory):
    """Factory for creating ModuleWarehouse instances."""

    _registered_types: dict = {}

    @classmethod
    def get_all_known_modules(cls) -> List[IntrospectiveModule]:
        """Get all known modules from all registered warehouses.

        Returns:
            List[IntrospectiveModule]: List of all known modules.
        """
        modules = []
        warehouses = cls.get_registered_types()

        for warehouse_name, warehouse_cls in warehouses.items():
            if warehouse_cls:
                modules.extend(warehouse_cls.get_known_modules())
            else:
                cls.get_logger().warning(f'Warehouse class for {warehouse_name} is None')

        return modules

    @classmethod
    def get_modules_by_type(
        cls,
        module_type: ModuleControlsType
    ) -> List[IntrospectiveModule]:
        """Get all modules of a specific type from all registered warehouses.

        Args:
            module_type (ModuleControlsType): The type of module to filter by.

        Returns:
            List[IntrospectiveModule]: List of modules matching the specified type.
        """
        modules = []
        warehouses = cls.get_registered_types()

        for warehouse_name, warehouse_cls in warehouses.items():
            if warehouse_cls:
                modules.extend(warehouse_cls.get_modules_by_type(module_type))
            else:
                cls.get_logger().warning(f'Warehouse class for {warehouse_name} is None')

        return modules

    @classmethod
    def filter_modules_by_type(
        cls,
        modules: List[Module],
        module_type: ModuleControlsType
    ) -> List[IntrospectiveModule]:
        """Filter a list of modules by a specific type.

        Args:
            modules (List[IntrospectiveModule]): The list of modules to filter.
            module_type (ModuleControlsType): The type of module to filter by.

        Returns:
            List[IntrospectiveModule]: List of modules matching the specified type.
        """
        filtered = []
        for module in modules:
            if not module.introspective_module:
                cls.get_logger().warning(f'Module {module} has no introspective_module, skipping...')
                continue
            if module.introspective_module.controls_type != module_type:
                continue
            filtered.append(module.introspective_module)
        return filtered


class ModuleWarehouseMeta(FactoryTypeMeta):
    """Metaclass for auto-registering Warehouse subclasses."""

    @classmethod
    def get_class(cls) -> Type['ModuleWarehouse']:
        try:
            return ModuleWarehouse
        except NameError:
            return None

    @classmethod
    def get_factory(cls):
        return ModuleWarehouseFactory


class ModuleWarehouse(metaclass=ModuleWarehouseMeta):
    """Class used to manage a collection of IntrospectiveModules.

    Can filter types, catalog numbers, etc.
    """

    @classmethod
    def get_known_modules(cls) -> list[IntrospectiveModule]:
        factory = cls.get_factory()
        if not factory:
            raise ValueError('No factory found for ModuleWarehouse.')
        if factory.__name__ == 'ModuleWarehouseFactory':
            raise ValueError('ModuleWarehouseFactory is abstract and cannot be used directly.')

        registered_types = factory.get_registered_types()
        if not registered_types:
            raise ValueError('No registered module warehouses found.')

        return list(registered_types.values())

    @classmethod
    def get_modules_by_type(
        cls,
        module_type: ModuleControlsType
    ) -> List[IntrospectiveModule]:
        """Get all modules of a specific type from this warehouse.

        Args:
            module_type (ModuleControlsType): The type of module to filter by.

        Returns:
            List[IntrospectiveModule]: List of modules matching the specified type.
        """
        modules = cls.get_known_modules()

        return [
            module for module in modules
            if module.module_type == module_type
        ]


class ModuleVendorFactory(MetaFactory):
    """Factory for creating ModuleVendor instances."""
    _registered_types: dict = {}

    @classmethod
    def get_known_modules(cls) -> List[IntrospectiveModule]:
        """Get all known modules from all registered vendors.

        Returns:
            List[IntrospectiveModule]: List of all known modules.
        """
        modules = []
        for module in cls.get_registered_types().values():
            if not module:
                cls.get_logger().warning('IntrospectiveModule class is None, skipping...')
                continue
            if not issubclass(module, IntrospectiveModule):
                cls.get_logger().warning(f'IntrospectiveModule subclass {module} is not a IntrospectiveModule, skipping...')
                continue
            modules.append(module)
        return modules

    @classmethod
    def get_modules_by_type(
        cls,
        module_type: ModuleControlsType
    ) -> List[IntrospectiveModule]:
        """Get all modules of a specific type from all registered vendors.

        Args:
            module_type (ModuleControlsType): The type of module to filter by.

        Returns:
            List[IntrospectiveModule]: List of modules matching the specified type.
        """
        modules = []
        for module in cls.get_registered_types().values():
            if not module:
                cls.get_logger().warning('IntrospectiveModule class is None, skipping...')
                continue
            if not issubclass(module, IntrospectiveModule):
                cls.get_logger().warning(f'IntrospectiveModule subclass {module} is not a IntrospectiveModule, skipping...')
                continue
            if not hasattr(module, 'controls_type'):
                cls.get_logger().warning(f'IntrospectiveModule subclass {module} has no controls_type attribute, skipping...')
                continue
            if module.get_controls_type() != module_type:
                continue
            modules.append(module)

        return modules


class EmulationGeneratorFactory(MetaFactory):
    """Factory for creating EmulationGenerator instances."""
    _registered_types: dict = {}

    @staticmethod
    def get_generator(controller: Controller) -> EmulationGenerator:
        """Get an appropriate EmulationGenerator for the given controller.

        Args:
            controller (Controller): The controller to get a generator for.

        Returns:
            EmulationGenerator: An instance of the appropriate EmulationGenerator subclass.

        Raises:
            ValueError: If no suitable generator is found for the controller type.
        """

        for generator_cls in EmulationGeneratorFactory.get_registered_types().values():
            if not generator_cls:
                continue
            if not issubclass(generator_cls, EmulationGenerator):
                continue
            if controller.__class__.__name__ == generator_cls.generator_type:
                return generator_cls(controller)

        raise ValueError(f'No suitable emulation generator found for controller type {controller.__class__.__name__}')


class EmulationGeneratorMeta(FactoryTypeMeta):
    """Metaclass for auto-registering EmulationGenerator subclasses."""

    @classmethod
    def get_class(cls) -> Type['EmulationGenerator']:
        try:
            return EmulationGenerator
        except NameError:
            return None

    @classmethod
    def get_factory(cls):
        return EmulationGeneratorFactory


class EmulationGenerator(metaclass=EmulationGeneratorMeta):
    """Base class for emulation logic generators."""
    generator_type = 'Controller'

    def __init__(
        self,
        controller: Controller
    ) -> None:
        super().__init__()
        self.generator_object: Controller = controller
        self.logger = Loggable.get_or_create_logger(f'{self.__class__.__name__}')
        self.schema = ControllerModificationSchema(
            source=None,
            destination=self.generator_object
        )
        self.emu_routine: Optional[Routine] = None
        self.safety_emu_routine: Optional[Routine] = None

    @property
    def base_tags(self) -> list[str]:
        """List of base tags common to all controllers.

        Returns:
            list[str]: List of tuples (tag_name, datatype, description)
        """
        return [
            ('zz_Demo3D_Uninhibit', 'INT', 'Uninhibit mode for the controller.'),
            ('zz_Demo3D_Inhibit', 'INT', 'Inhibit mode for the controller.'),
            ('zz_Demo3D_ToggleInhibit', 'BOOL', 'Toggle inhibit mode for the controller.'),
            ('zz_Demo3D_LocalMode', 'INT', 'Local mode for the controller.'),
            ('zz_Demo3D_TestMode', 'BOOL', 'Demo 3D\nEmulation Test Mode\n-----\nREMOVE IF FOUND IN PRODUCTION'),
        ]

    @property
    def custom_tags(self) -> list[tuple[str, str, str, Optional[str]]]:
        """List of custom tags specific to the controller type.

        Returns:
            list[str]: List of tuples (tag_name, datatype, description, dimensions).
        """
        raise NotImplementedError("Subclasses must implement custom_tags")

    @property
    def emulation_safety_routine_description(self) -> str:
        """Description for the safety routine to add emulation logic to.

        Returns:
            str: Description of the safety routine
        """
        return self.emulation_standard_routine_description

    @property
    def emulation_safety_routine_name(self) -> str:
        """Name of the safety routine to add emulation logic to.

        Returns:
            str: Name of the safety routine
        """
        return 'zzz_s_Emulation'

    @property
    def emulation_standard_routine_description(self) -> str:
        """Description for the standard routine to add emulation logic to.

        Returns:
            str: Description of the standard routine
        """
        return ''.join([
            'Emulation routine for automation controller.\n',
            'This routine is auto-generated by Indicon LLC.\n',
            'Do not modify.'
        ])

    @property
    def emulation_standard_routine_name(self) -> str:
        """Name of the standard routine to add emulation logic to.

        Returns:
            str: Name of the standard routine
        """
        return 'zzz_Emulation'

    @property
    def generator_object(self) -> Controller:
        return self._generator_object

    @generator_object.setter
    def generator_object(self, value: Controller):
        if value.__class__.__name__ != self.generator_type:
            raise TypeError(f'Controller must be of type {self.generator_type}, got {value.__class__.__name__} instead.')
        self._generator_object = value

    @property
    def target_safety_program_name(self) -> str:
        """Name of the safety program to add emulation logic to.

        Returns:
            str: Name of the safety program
        """
        raise NotImplementedError("Subclasses must implement target_safety_program_name")

    @property
    def target_standard_program_name(self) -> str:
        """Name of the standard program to add emulation logic to.

        Returns:
            str: Name of the standard program
        """
        raise NotImplementedError("Subclasses must implement target_standard_program_name")

    @property
    def test_mode_tag(self) -> str:
        """Name of the test mode tag.

        Returns:
            str: Name of the test mode tag
        """
        return self.base_tags[4][0]

    def _add_to_safety_routine(self, rung: Rung) -> None:
        """Helper to add a rung to the safety emulation routine."""
        if not self.safety_emu_routine:
            raise ValueError("Safety emulation routine has not been created yet.")

        self.schema.add_rung(
            program_name=self.target_safety_program_name,
            routine_name=self.emulation_safety_routine_name,
            new_rung=rung
        )

    def _add_rung_to_standard_routine(self, rung: Rung) -> None:
        """Helper to add a rung to the standard emulation routine."""
        if not self.emu_routine:
            raise ValueError("Emulation routine has not been created yet.")

        self.schema.add_rung(
            program_name=self.target_standard_program_name,
            routine_name=self.emulation_standard_routine_name,
            new_rung=rung
        )

    def _generate_base_emulation(self) -> None:
        """Generate the base emulation logic common to all controllers."""
        self._generate_base_tags()
        self._generate_custom_tags()

        self._generate_base_standard_routine()
        self._generate_base_standard_rungs()

        self._generate_base_safety_routine()
        self._generate_base_safety_rungs()

        self._generate_base_module_emulation()

        self._generate_custom_standard_routines()
        self._generate_custom_standard_rungs()
        self._generate_custom_safety_routines()
        self._generate_custom_safety_rungs()

    def _generate_base_module_emulation(self) -> None:
        """Generate base module emulation logic common to all controllers."""
        self._generate_builtin_common(ModuleControlsType.BLOCK)
        self._generate_builtin_common(ModuleControlsType.SAFETY_BLOCK)
        self._generate_builtin_common(ModuleControlsType.DRIVE)

    def _generate_base_safety_routine(self) -> None:
        """Generate a safety routine common to all controllers."""
        self.logger.debug("Generating base safety routine")
        self.safety_emu_routine = self.add_emulation_routine(
            program_name=self.target_safety_program_name,
            routine_name=self.emulation_safety_routine_name,
            routine_description=self.emulation_safety_routine_description,
            call_from_main=True,
            rung_position=0
        )

    def _generate_base_safety_rungs(self) -> None:
        """Generate base rungs in the safety emulation routine."""
        if not self.safety_emu_routine:
            raise ValueError("Safety emulation routine has not been created yet.")

        self.safety_emu_routine.clear_rungs()
        self.logger.debug("Generating base safety rungs")

        # Header rung
        header_rung = Rung(
            controller=self.controller,
            text='NOP();',
            comment='// Emulation Safety Logic Routine\n// Auto-generated by Indicon LLC\n// Do not modify.'
        )
        self._add_to_safety_routine(header_rung)

    def _generate_base_standard_routine(self) -> None:
        """Generate a standard base routine common to all controllers."""
        self.logger.info("Generating base standard routine")
        self.emu_routine = self.add_emulation_routine(
            program_name=self.target_standard_program_name,
            routine_name=self.emulation_standard_routine_name,
            routine_description=self.emulation_standard_routine_description,
            call_from_main=True,
            rung_position=0
        )

    def _generate_base_standard_rungs(self) -> None:
        """Generate base rungs in the standard emulation routine."""
        if not self.emu_routine:
            raise ValueError("Emulation routine has not been created yet.")

        self.emu_routine.clear_rungs()
        self.logger.debug("Generating base standard rungs")

        uninhibit = self.base_tags[0][0]  # Uninhibit tag name
        inhibit = self.base_tags[1][0]  # Inhibit tag name
        toggle_inhibit = self.base_tags[2][0]  # ToggleInhibit tag name
        local_mode = self.base_tags[3][0]  # LocalMode tag name
        test_mode = self.base_tags[4][0]  # zz_Demo3D_TestMode tag name

        # Header rung
        header_rung = Rung(
            controller=self.controller,
            text='NOP();',
            comment='// Emulation Logic Routine\n// Auto-generated by Indicon LLC\n// Do not modify.'
        )
        self._add_rung_to_standard_routine(header_rung)

        # Setup Rung
        setup_rung = Rung(
            controller=self.controller,
            text=f'[XIC(S:FS)OTU({toggle_inhibit})OTU({test_mode}),MOV(0,{uninhibit})MOV(4,{inhibit})];',
            comment='// This routine is auto-generated by Indicon LLC.\n// Do not modify.'
        )
        self._add_rung_to_standard_routine(setup_rung)

        # Inhibit Logic Rung
        inhibit_logic_rung = Rung(
            controller=self.controller,
            text=f'[XIO({toggle_inhibit})MOV({uninhibit},{local_mode}),XIC({toggle_inhibit})MOV({inhibit},{local_mode})];',
            comment='// Handle toggle inhibit.'
        )
        self._add_rung_to_standard_routine(inhibit_logic_rung)

        self._generate_module_inhibit_rungs()

    def _generate_base_tags(self) -> None:
        """Generate base tags common to all controllers."""
        if not self.base_tags:
            self.logger.debug("No base tags defined, skipping base tag generation.")
        self.logger.info("Generating base tags")
        for tag_name, datatype, description in self.base_tags:
            self.add_controller_tag(tag_name, datatype, description=description)

    def _generate_builtin_common(
        self,
        generation_type: ModuleControlsType
    ) -> None:
        modules: list[IntrospectiveModule] = ModuleWarehouseFactory.filter_modules_by_type(
            self.generator_object.modules,
            generation_type
        )
        if not modules:
            self.logger.debug("No modules found, skipping builtin emulation for type %s.", generation_type.value)
            return

        for mod in modules:
            self._schedule_imports(mod.get_required_imports())
            self.add_controller_tags(mod.get_required_tags())
            self.add_safety_tag_mapping(*mod.get_required_standard_to_safety_mapping())
            self.add_rungs(
                self.target_standard_program_name,
                self.emulation_standard_routine_name,
                mod.get_required_standard_rungs()
            )
            self.add_rungs(
                self.target_safety_program_name,
                self.emulation_safety_routine_name,
                mod.get_required_safety_rungs()
            )

    def _generate_custom_safety_routines(self) -> None:
        """Generate custom safety routines. Override in subclasses if needed."""
        pass

    def _generate_custom_safety_rungs(self) -> None:
        """Generate custom safety rungs. Override in subclasses if needed."""
        pass

    def _generate_custom_standard_routines(self) -> None:
        """Generate custom standard routines. Override in subclasses if needed."""
        pass

    def _generate_custom_standard_rungs(self) -> None:
        """Generate custom standard rungs. Override in subclasses if needed."""
        pass

    def _generate_custom_tags(self) -> None:
        """Generate custom tags. Override in subclasses if needed."""
        if not self.custom_tags:
            self.logger.debug("No custom tags defined, skipping custom tag generation.")
        self.logger.info("Generating custom tags")
        for tag_name, datatype, description, dimensions in self.custom_tags:
            self.add_controller_tag(tag_name, datatype, description=description, dimensions=dimensions)

    def _generate_module_inhibit_rungs(self) -> None:
        """Generate inhibit logic for modules."""
        if not self.emu_routine:
            raise ValueError("Emulation routine has not been created yet.")

        self.logger.debug("Generating module inhibit rungs")
        local_mode = self.base_tags[3][0]  # LocalMode tag name

        for module in self.generator_object.modules:
            if module.name == 'Local':
                continue
            inhibit_rung = self.generator_object.config.rung_type(
                controller=self.controller,
                text=f'SSV(Module,{module.name},Mode,{local_mode});',
                comment=f'// Inhibit logic for module {module.name}'
            )
            self._add_rung_to_standard_routine(inhibit_rung)

    def _import_safety_block_udts(self) -> None:
        """Import UDTs required for safety block emulation."""
        self.schema.add_import_from_file(
            file_location=r'docs\controls\emu\Demo3D_WDint_DataType.L5X',
            asset_types=['DataTypes']
        )
        self.schema.add_import_from_file(
            file_location=r'docs\controls\emu\Demo3D_CommOK_SBK_DataType.L5X',
            asset_types=['DataTypes']
        )

    def _schedule_imports(
        self,
        imports: List[tuple[str, List[str]]]
    ) -> None:
        """Helper to schedule imports in the modification schema.

        Args:
            imports: List of tuples (file_location, [asset_types])
        """
        for file_location, asset_types in imports:
            self.logger.debug(f"Scheduling import of {asset_types} from {file_location}")
            self.schema.add_import_from_file(
                file_location=file_location,
                asset_types=asset_types
            )

    def add_emulation_routine(
        self,
        program_name: str,
        routine_name: str,
        routine_description: str,
        call_from_main: bool = True,
        rung_position: int = -1
    ) -> Routine:
        """Helper method to add an emulation routine to a program.

        Args:
            program_name: Name of the program to add routine to
            routine_name: Name of the new routine
            routine_description: Description for the routine
            call_from_main: Whether to add JSR call from main routine
            rung_position: Position to insert JSR call (-1 for end)

        Returns:
            Routine: The created routine
        """
        self.logger.debug(f"Adding emulation routine '{routine_name}' to program '{program_name}' to schema.")

        # Create the routine
        routine: Routine = self.controller.config.routine_type(controller=self.controller)
        routine.name = routine_name
        routine.description = routine_description
        routine.clear_rungs()

        # Add routine to program
        self.schema.add_routine(
            program_name=program_name,
            routine=routine
        )

        # Add JSR call if requested
        if call_from_main:
            program: Program = self.controller.programs.get(program_name)
            if program and program.main_routine:
                if program.main_routine.check_for_jsr(routine_name):
                    self.logger.debug(f"JSR to '{routine_name}' already exists in main routine of program '{program_name}'")
                else:
                    self.logger.debug(f"Adding JSR call to '{routine_name}' in main routine of program '{program_name}'")
                    jsr_rung = Rung(
                        controller=self.controller,
                        text=f'JSR({routine_name},0);',
                        comment=f'Call the {routine_name} routine.'
                    )
                    self.schema.add_rung(
                        program_name=program_name,
                        routine_name=program.main_routine_name,
                        rung_number=rung_position,
                        new_rung=jsr_rung
                    )

        return routine

    def add_program_tag(
        self,
        program_name: str,
        tag_name: str,
        datatype: str,
        **kwargs
    ) -> Tag:
        """Helper method to add a tag to a program.

        Args:
            program_name: Name of the program
            tag_name: Name of the tag
            datatype: Datatype of the tag
            **kwargs: Additional tag properties

        Returns:
            Tag: The created tag
        """
        self.logger.debug(f"Adding program tag: {tag_name} with datatype {datatype} to program {program_name}")

        tag = Tag(
            controller=self.controller,
            name=tag_name,
            datatype=datatype,
            **kwargs
        )

        self.schema.add_program_tag(
            program_name=program_name,
            tag=tag
        )

        return tag

    def add_controller_tag(
        self,
        tag_name: str,
        datatype: str,
        description: str = "",
        constant: bool = False,
        external_access: str = "Read/Write",
        tag_type: str = 'Base',
        **kwargs
    ) -> Tag:
        """Helper method to add a controller-scoped tag.

        Args:
            tag_name: Name of the tag
            datatype: Datatype of the tag
            **kwargs: Additional tag properties

        Returns:
            Tag: The created tag
        """
        self.logger.debug(f"Adding controller tag: {tag_name} with datatype {datatype} to schema.")

        tag = self.controller.config.tag_type(
            controller=self.controller,
            name=tag_name,
            datatype=datatype,
            description=description,
            constant=constant,
            external_access=external_access,
            tag_type=tag_type,
            **kwargs
        )

        self.schema.add_controller_tag(tag)
        return tag

    def add_controller_tags(
        self,
        tags: List[dict]
    ) -> None:
        """Helper method to add multiple controller-scoped tags.

        Args:
            tags: List of tag dictionaries with keys matching Tag properties
        """
        for tag_info in tags:
            self.add_controller_tag(**tag_info)

    def add_rung(
        self,
        program_name: str,
        routine_name: str,
        new_rung: Rung,
        rung_number: Optional[int] = None
    ) -> None:
        """Helper method to add a rung to a routine.

        Args:
            program_name: Name of the program
            routine_name: Name of the routine
            new_rung: The rung to add
            rung_number: Position to insert the rung (-1 for end)
        """

        self.schema.add_rung(
            program_name=program_name,
            routine_name=routine_name,
            rung_number=rung_number,
            new_rung=new_rung
        )

    def add_rungs(
        self,
        program_name: str,
        routine_name: str,
        new_rungs: List[Rung],
        rung_number: Optional[int] = None
    ) -> None:
        """Helper method to add multiple rungs to a routine.

        Args:
            program_name: Name of the program
            routine_name: Name of the routine
            new_rungs: List of rungs to add
            rung_number: Position to insert the first rung (-1 for end)
        """
        for i, rung in enumerate(new_rungs):
            position = rung_number + i if rung_number is not None and rung_number >= 0 else -1
            self.add_rung(
                program_name=program_name,
                routine_name=routine_name,
                new_rung=rung,
                rung_number=position
            )

    def add_safety_tag_mapping(
        self,
        standard_tag: str,
        safety_tag: str,
    ) -> None:
        """Helper method to add a safety tag mapping.

        Args:
            standard_tag: Name of the standard tag
            safety_tag: Name of the safety tag
        """
        if not standard_tag or not safety_tag:
            return
        self.schema.add_safety_tag_mapping(
            std_tag=standard_tag,
            sfty_tag=safety_tag
        )

    def block_routine_jsr(
        self,
        program_name: str,
        routine_name: str
    ) -> None:
        """Helper method to block a JSR call to a routine.

        Args:
            program_name: Name of the program
            routine_name: Name of the routine
        """
        self.logger.debug(f"Blocking JSR call to routine '{routine_name}' in program '{program_name}'")
        ...

    @abstractmethod
    def generate_custom_module_emulation(self) -> None:
        """Generate module-specific emulation logic."""
        pass

    @abstractmethod
    def remove_base_emulation(self) -> None:
        """Remove the base emulation logic common to all controllers."""
        pass

    @abstractmethod
    def remove_module_emulation(self) -> None:
        """Remove module-specific emulation logic."""
        pass

    @abstractmethod
    def validate_controller(self) -> bool:
        """Validate that the controller is compatible with this generator.

        Returns:
            bool: True if controller is valid for this generator type.

        Raises:
            ValueError: If controller validation fails.
        """
        pass

    def generate_custom_logic(self) -> None:
        """Generate custom emulation logic. Override in subclasses if needed."""
        pass

    def generate_emulation_logic(self) -> ControllerModificationSchema:
        """Main entry point to generate emulation logic.

        Returns:
            ControllerModificationSchema: The modification schema with all changes.
        """
        self.logger.info(f"Starting emulation generation for {self.controller.name}")

        # Validate controller
        if not self.validate_controller():
            raise ValueError(f"Controller {self.controller.name} is not valid for {self.controller_type} emulation")

        # Generate emulation logic
        self._generate_base_emulation()
        self.generate_custom_module_emulation()
        self.generate_custom_logic()

        # Execute the schema
        self.schema.execute()

        self.logger.info(f"Emulation generation completed for {self.controller.name}")
        return self.schema

    def remove_emulation_logic(self) -> ControllerModificationSchema:
        """Remove previously added emulation logic.

        Returns:
            ControllerModificationSchema: The modification schema with all removals.
        """
        self.logger.info(f"Starting emulation removal for {self.controller.name}")

        # Remove emulation logic
        self.remove_base_emulation()
        self.remove_module_emulation()
        self.remove_custom_logic()

        # Execute the schema to remove added elements
        self.schema.execute()

        self.logger.info(f"Emulation removal completed for {self.controller.name}")
        return self.schema

    def get_modules_by_type(self, module_type: str) -> List[Module]:
        """Get all modules of a specific type.

        Args:
            module_type: The module type to filter by

        Returns:
            List[Module]: List of matching modules
        """
        mods = [module for module in self.controller.modules if module.type_ == module_type]
        self.logger.info('Found %d modules of type %s...', len(mods), module_type)
        return mods

    def get_modules_by_description_pattern(self, pattern: str) -> List[Module]:
        """Get modules matching a description pattern.

        Args:
            pattern: Pattern to match in module description

        Returns:
            List[Module]: List of matching modules
        """
        mods = [m for m in self.controller.modules if m.description and pattern in m.description]
        self.logger.info('Found %d modules matching description pattern "%s"...', len(mods), pattern)
        return mods

    def remove_custom_logic(self) -> None:
        """Remove custom emulation logic."""
        pass

    def remove_controller_tag(
        self,
        tag_name: str
    ) -> None:
        """Helper method to remove a controller-scoped tag.

        Args:
            tag_name: Name of the tag to remove
        """
        self.logger.debug(f"Removing controller tag '{tag_name}'")

        self.schema.remove_controller_tag(
            tag_name=tag_name
        )

    def remove_datatype(
        self,
        datatype_name: str
    ) -> None:
        """Helper method to remove a datatype from the controller.

        Args:
            datatype_name: Name of the datatype to remove
        """
        self.logger.debug(f"Removing datatype '{datatype_name}' from controller")

        self.schema.remove_datatype(
            datatype_name=datatype_name
        )

    def remove_program_tag(
        self,
        program_name: str,
        tag_name: str
    ) -> None:
        """Helper method to remove a tag from a program.

        Args:
            program_name: Name of the program
            tag_name: Name of the tag to remove
        """
        self.logger.debug(f"Removing tag '{tag_name}' from program '{program_name}'")

        self.schema.remove_program_tag(
            program_name=program_name,
            tag_name=tag_name
        )

    def remove_routine(
            self,
            program_name: str,
            routine_name: str
    ) -> None:
        """Helper method to remove a routine from the controller.

        Args:
            program_name: Name of the program containing the routine
            routine_name: Name of the routine to remove
        """
        self.logger.debug(f"Removing routine '{routine_name}' from controller")

        self.schema.remove_routine(
            program_name,
            routine_name
        )

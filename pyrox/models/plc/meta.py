"""Meta definitions for PLC models and architecture.
"""
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import (
    Callable,
    Generic,
    Optional,
    Self,
    TYPE_CHECKING,
    TypeVar,
    Union
)
from pyrox.models.abc.list import HashList
from pyrox.models.abc.meta import EnforcesNaming, NamedPyroxObject, SupportsMetaData
from pyrox.services.dict import insert_key_at_index

if TYPE_CHECKING:
    from pyrox.models.plc.plc import Controller, ControllerConfiguration

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


class PlcObject(EnforcesNaming, SupportsMetaData, Generic[CTRL]):
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

    def __init__(
        self,
        controller: Optional[CTRL] = None,
        meta_data: Union[dict, str] = defaultdict(None)
    ) -> None:
        super().__init__(meta_data=meta_data)
        self.controller = controller

        self._on_compiling: list[Callable] = []
        self._on_compiled: list[Callable] = []
        self._init_dict_order()

    def __repr__(self) -> str:
        return str(self)

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
            ControllerConfiguration: The controller configuration, or None if no controller.
        """
        if hasattr(self, '_config'):
            return self._config
        return None if not self.controller else self.controller.config

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
        if value is None:
            self._controller = value
            return
        if not hasattr(self, 'config'):
            self._controller = value
            return  # If there is no config, then the type must not be important enough to check.
        if not isinstance(value, self.config.controller_type):
            raise TypeError(f'controller must be of type {self.config.controller_type} or None!')
        self._controller = value

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


class NamedPlcObject(NamedPyroxObject, PlcObject):
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
        meta_data=None,
        controller: Optional[CTRL] = None,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        PlcObject.__init__(
            self,
            meta_data=meta_data,
            controller=controller
        )
        # Because these attrs could be defined by meta data,
        # capture their values here before we continue the object resolution order.
        final_name = name or self.name
        final_description = description or self.description

        NamedPyroxObject.__init__(
            self,
            name=final_name,
            description=final_description,
        )

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

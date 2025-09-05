"""General motors implimentation specific plc types
    """
from enum import Enum
import fnmatch
from pyrox.models import HashList, plc
import re
from typing import Optional, TypeVar, Union

from ...utils import find_duplicates

GM_CTRL = TypeVar('GM_CTRL', bound='GmController')

GM_CHAR = 'z'
GM_SAFE_CHAR = 's_z'
USER_CHAR = 'u'
USER_SAFE_CHAR = 's_u'
ALARM_PATTERN:   str = '*<Alarm[[]*[]]:*>'
PROMPT_PATTERN:  str = '*<Prompt[[]*[]]:*>'

DIAG_RE_PATTERN:    str = r"(<.+\[\d*\].*>)"
TL_RE_PATTERN:      str = r"(?:.*)(<.*\[\d*\]:.*>)(?:.*)"
TL_ID_PATTERN:      str = r"(?:.*<)(.*)(?:\[\d*\]:.*>.*)"
DIAG_NUM_RE_PATTERN: str = r"(?:<.*\[)(\d*)(?:\].*>)"
COLUMN_RE_PATTERN:   str = r"(?:<.*\[\d+\]:\s)(@[a-zA-Z]+\d+)(?:.*)>"
DIAG_NAME_RE_PATTER: str = r"(?!MOV\(\d*,HMI\.Diag\.Pgm\.Name\.LEN\))(MOV\(.*?,HMI\.Diag\.Pgm\.Name\.DATA\[\d*?\])"


class TextListElement:
    """General Motors Text List Generic Element
    """

    def __init__(self,
                 text: str,
                 rung: 'GmRung'):
        self._text:      str = self._get_diag_text(text)
        self._text_list_id: str = self._get_tl_id()
        self._number:    int = self._get_diag_number()
        self._rung: 'GmRung' = rung

    def __eq__(self, other):
        if isinstance(other, TextListElement):
            return self.number == other.number
        return False

    def __hash__(self):
        return hash((self.text, self.number))

    def __repr__(self) -> str:
        return (
            f'text={self.text}, '
            f'text_list_id={self.text_list_id}'
            f'number={self.number}, '
            f'rung={self.rung}'
        )

    def __str__(self):
        return self.text

    @property
    def number(self) -> int:
        return self._number

    @property
    def rung(self) -> 'GmRung':
        return self._rung

    @property
    def text(self) -> str:
        return self._text

    @property
    def text_list_id(self) -> str:
        return self._text_list_id

    def _get_diag_number(self):
        match = re.search(DIAG_NUM_RE_PATTERN, self._text)
        if match:
            return int(match.groups()[0])

        raise ValueError('Could not find diag number in diag string! -> %s' % self._text)

    def _get_diag_text(self, text: str):
        match = re.search(DIAG_RE_PATTERN, text)
        if match:
            return match.groups()[0]

        raise ValueError('Could not find diag text in diag string! -> %s' % text)

    def _get_tl_id(self) -> str:
        if not self.text:
            return None

        match = re.search(TL_ID_PATTERN, self.text)
        if match:
            return match.groups()[0].strip()
        else:
            return None


class KDiagType(Enum):
    NA:     int = 0
    ALARM:  int = 1
    PROMPT: int = 2
    VALUE:  int = 3


class KDiagProgramType(Enum):
    NA:      int = 0
    MCP:     int = 1
    STATION: int = 2
    DEVICE:  int = 3
    ROBOT:   int = 4
    HMI:     int = 5
    PFE:     int = 6


class KDiag(TextListElement):
    """General Motors "k" Diagnostic Object
    """

    def __init__(self,
                 diag_type: KDiagType,
                 text: str,
                 parent_offset: Optional[Union[str, int]],
                 rung: 'GmRung'):
        if diag_type is KDiagType.NA:
            raise ValueError('Cannot be NA!')
        if parent_offset is None:
            parent_offset = 0
        super().__init__(text=text,
                         rung=rung)

        self.diag_type: KDiagType = diag_type
        self.col_location:    str = self._get_col_location()
        self.parent_offset:   int = int(parent_offset)

    def __eq__(self, other):
        if isinstance(other, KDiag):
            return self.global_number == other.global_number
        return False

    def __hash__(self):
        return hash((self.text, self.diag_type.value, self.col_location, self.number, self.parent_offset))

    def __repr__(self) -> str:
        return (
            f'KDiag(text={self.text}, '
            f'diag_type={self.diag_type}, '
            f'col_location={self.col_location}, '
            f'number={self.number}, '
            f'parent_offset={self.parent_offset}), '
            f'rung={self.rung}'
        )

    @property
    def global_number(self) -> int:
        return self.number + self.parent_offset

    def _get_col_location(self):
        col_match = re.search(COLUMN_RE_PATTERN, self.text)
        if col_match:
            return col_match.groups()[0]

        return None


class GmPlcObject(plc.PlcObject[GM_CTRL]):

    @property
    def config(self) -> plc.ControllerConfiguration:
        return plc.ControllerConfiguration(aoi_type=GmAddOnInstruction,
                                           datatype_type=GmDatatype,
                                           module_type=GmModule,
                                           program_type=GmProgram,
                                           routine_type=GmRoutine,
                                           rung_type=GmRung,
                                           tag_type=GmTag)


class NamedGmPlcObject(plc.NamedPlcObject[GM_CTRL], GmPlcObject):
    """General Motors Named Plc Object
    """

    @property
    def is_gm_owned(self) -> bool:
        return True if (self.name.lower().startswith(GM_CHAR)
                        or self.name.lower().startswith(GM_SAFE_CHAR)) else False

    @property
    def is_user_owned(self) -> bool:
        return True if (self.name.lower().startswith(USER_CHAR)
                        or self.name.lower().startswith(USER_SAFE_CHAR)) else False

    @property
    def process_name(self) -> str:
        if self.name.startswith(('CG_', 'zz_', 'sz_', 'zs_')):
            return self.name[3:]

        return self.name


class GmAddOnInstruction(NamedGmPlcObject[GM_CTRL], plc.AddOnInstruction):
    """General Motors AddOn Instruction Definition
    """


class GmDatatype(NamedGmPlcObject, plc.Datatype):
    """General Motors Datatype
    """


class GmModule(NamedGmPlcObject, plc.Module):
    """General Motors Module
    """


class GmRung(GmPlcObject, plc.Rung):
    """General Motors Rung
    """

    @property
    def has_kdiag(self) -> bool:
        if not self.comment:
            return False

        return True if '<@DIAG>' in self.comment else False

    @property
    def kdiags(self) -> list[KDiag]:
        if not self.comment:
            return []

        comment_lines = self.comment.splitlines()
        ret_list = []

        for line in comment_lines:
            if fnmatch.fnmatch(line, ALARM_PATTERN):
                ret_list.append(KDiag(KDiagType.ALARM,
                                      line,
                                      self.routine.program.parameter_offset,
                                      self))

            elif fnmatch.fnmatch(line, PROMPT_PATTERN):
                ret_list.append(KDiag(KDiagType.PROMPT,
                                      line,
                                      self.routine.program.parameter_offset,
                                      self))

        return ret_list

    @property
    def text_list_items(self) -> list[TextListElement]:
        if not self.comment:
            return []

        comment_lines = self.comment.splitlines()
        ret_list = []

        for line in comment_lines:
            match = re.match(TL_RE_PATTERN, line)
            if match:
                ret_list.append(TextListElement(match.groups()[0], self))

        return ret_list


class GmRoutine(NamedGmPlcObject, plc.Routine):
    """General Motors Routine
    """

    @property
    def kdiag_rungs(self) -> list[KDiag]:
        x = []
        for rung in self.rungs:
            x.extend(rung.kdiags)
        return x

    @property
    def program(self) -> "GmProgram":
        return self._program

    @property
    def rungs(self) -> list[GmRung]:
        return super().rungs

    @property
    def text_list_items(self) -> list[TextListElement]:
        x = []
        for rung in self.rungs:
            x.extend(rung.text_list_items)
        return x


class GmTag(NamedGmPlcObject, plc.Tag):
    """General Motors Tag
    """


class GmProgram(NamedGmPlcObject, plc.Program):
    """General Motors Program
    """
    PARAM_RTN_STR = 'B*_Parameters'

    PARAM_MATCH_STR = "MOV(*,HMI.Diag.Pgm.MsgOffset);"

    PGM_NAME_STR = "MOV(*,HMI.Diag.Pgm.Name.LEN)*"

    @property
    def is_gm_owned(self) -> bool:
        return len(self.gm_routines) > 0

    @property
    def is_user_owned(self) -> bool:
        return len(self.user_routines) > 0

    @property
    def diag_name(self) -> str:
        if not self.parameter_routine:
            return None

        diag_rung = None
        for rung in self.parameter_routine.rungs:
            match = re.search(DIAG_NAME_RE_PATTER, rung.text)
            if match:
                diag_rung = rung
                break
        if not diag_rung:
            return None

        # Extract the length of the string
        length_match = re.search(r'MOV\((\d+),HMI\.Diag\.Pgm\.Name\.LEN\)', diag_rung.text)
        if length_match:
            string_length = int(length_match.group(1))
        else:
            raise ValueError("String length not found in the PLC code")

        # Extract the ASCII characters and their positions
        data_matches = re.findall(r'MOV\((kAscii\.\w+),HMI\.Diag\.Pgm\.Name\.DATA\[(\d+)\]\)', diag_rung.text)
        if not data_matches:
            raise ValueError("No ASCII characters found in the PLC code")

        # Create a dictionary to map ASCII positions to characters
        ascii_map = {
            'kAscii.A': 'A',
            'kAscii.B': 'B',
            'kAscii.C': 'C',
            'kAscii.D': 'D',
            'kAscii.E': 'E',
            'kAscii.F': 'F',
            'kAscii.G': 'G',
            'kAscii.H': 'H',
            'kAscii.I': 'I',
            'kAscii.J': 'J',
            'kAscii.K': 'K',
            'kAscii.L': 'L',
            'kAscii.M': 'M',
            'kAscii.N': 'N',
            'kAscii.O': 'O',
            'kAscii.P': 'P',
            'kAscii.Q': 'Q',
            'kAscii.R': 'R',
            'kAscii.S': 'S',
            'kAscii.T': 'T',
            'kAscii.U': 'U',
            'kAscii.V': 'V',
            'kAscii.W': 'W',
            'kAscii.X': 'X',
            'kAscii.Y': 'Y',
            'kAscii.Z': 'Z',
            'kAscii.a': 'a',
            'kAscii.b': 'b',
            'kAscii.c': 'c',
            'kAscii.d': 'd',
            'kAscii.e': 'e',
            'kAscii.f': 'f',
            'kAscii.g': 'g',
            'kAscii.h': 'h',
            'kAscii.i': 'i',
            'kAscii.j': 'j',
            'kAscii.k': 'k',
            'kAscii.l': 'l',
            'kAscii.m': 'm',
            'kAscii.n': 'n',
            'kAscii.o': 'o',
            'kAscii.p': 'p',
            'kAscii.q': 'q',
            'kAscii.r': 'r',
            'kAscii.s': 's',
            'kAscii.t': 't',
            'kAscii.u': 'u',
            'kAscii.v': 'v',
            'kAscii.w': 'w',
            'kAscii.x': 'x',
            'kAscii.y': 'y',
            'kAscii.z': 'z',
            'kAscii.n0': '0',
            'kAscii.n1': '1',
            'kAscii.n2': '2',
            'kAscii.n3': '3',
            'kAscii.n4': '4',
            'kAscii.n5': '5',
            'kAscii.n6': '6',
            'kAscii.n7': '7',
            'kAscii.n8': '8',
            'kAscii.n9': '9',
        }

        # Initialize the string with placeholders
        string_chars = [''] * string_length

        # Fill the string with the extracted characters
        for char, pos in data_matches:
            string_chars[int(pos)] = ascii_map.get(char, '?')

        # Join the characters to form the final string
        final_string = ''.join(string_chars)

        return final_string

    @property
    def diag_setup(self) -> dict:
        return {
            'program_name': self.name,
            'diag_name': self.diag_name,
            'msg_offset': self.parameter_offset,
            'hmi_tag': 'TBD',
            'program_type': self.program_type,
            'tag_alias_refs': 'TBD'
        }

    @property
    def kdiags(self) -> list[KDiag]:
        x = []
        for routine in self.routines:
            x.extend(routine.kdiag_rungs)
        return x

    @property
    def parameter_offset(self) -> int:
        if not self.parameter_routine:
            return 0

        for rung in self.parameter_routine.rungs:
            if fnmatch.fnmatch(rung.text, self.PARAM_MATCH_STR):
                return int(rung.text.replace("MOV(", '').replace(',HMI.Diag.Pgm.MsgOffset);', ''))
        return 0

    @property
    def parameter_routine(self) -> GmRoutine:
        for routine in self.routines:
            if fnmatch.fnmatch(routine.name, self.PARAM_RTN_STR):
                return routine
        return None

    @property
    def program_type(self) -> KDiagProgramType:
        return KDiagProgramType.NA

    @property
    def routines(self) -> list[GmRoutine]:
        return super().routines

    @property
    def text_list_items(self) -> list[TextListElement]:
        x = []
        for routine in self.routines:
            x.extend(routine.text_list_items)
        return x

    @property
    def gm_routines(self) -> list[GmRoutine]:
        return [x for x in self.routines if x.is_gm_owned]

    @property
    def user_routines(self) -> list[GmRoutine]:
        return [x for x in self.routines if x.is_user_owned]


class GmController(NamedGmPlcObject, plc.Controller):
    """General Motors Plc Controller
    """

    generator_type = 'GmEmulationGenerator'

    @property
    def kdiags(self) -> list[KDiag]:
        x = []
        for program in self.programs:
            x.extend(program.kdiags)
        return x

    @property
    def mcp_program(self) -> Optional[GmProgram]:
        return self.programs.get('MCP', None)

    @property
    def programs(self) -> HashList[GmProgram]:
        return super().programs

    @property
    def safety_common_program(self) -> Optional[GmProgram]:
        """Get the safety common program if it exists
        """
        return self.programs.get('s_Common', None)

    @property
    def text_list_items(self) -> list[TextListElement]:
        x = []
        for program in self.programs:
            x.extend(program.text_list_items)
        return x

    @property
    def gm_programs(self) -> list[GmProgram]:
        return [x for x in self.programs if x.is_gm_owned]

    @property
    def modules(self) -> HashList[GmModule]:
        return super().modules

    @property
    def user_program(self) -> list[GmProgram]:
        return [x for x in self.programs if x.is_user_owned]

    def extract_messages(self):
        tl_items = self.text_list_items
        filtered = {}

        for item in tl_items:
            if item.text_list_id not in filtered:
                filtered[item.text_list_id] = []
            filtered[item.text_list_id].append(item)

        return {
            'text_lists': tl_items,
            'filtered': filtered,
            'duplicates': find_duplicates(tl_items, True),
            'programs': [x.diag_setup for x in self.programs]
        }

    def validate_text_lists(self):
        """validate all text lists within controller
        """
        duplicate_diags = find_duplicates(self.kdiags, True)

        return duplicate_diags


class GmControllerMatcher(plc.ControllerMatcher):
    """Matcher for GM controllers."""

    @classmethod
    def get_controller_constructor(cls):
        return GmController

    @classmethod
    def get_datatype_patterns(cls) -> list[str]:
        return [
            'zz_Version',
            'zz_Prompt',
            'zz_PFEAlarm',
            'za_Toggle'
        ]

    @classmethod
    def get_module_patterns(cls) -> list[str]:
        return [
            'sz_*',
            'zz_*',
            'cg_*',
            'zs_*'
        ]

    @classmethod
    def get_program_patterns(cls) -> list[str]:
        return [
            'MCP',
            'PFE',
            'GROUP1',
            'GROUP2',
            'HMI1',
            'HMI2',
        ]

    @classmethod
    def get_safety_program_patterns(cls) -> list[str]:
        return [
            's_Common',
            's_Segment1',
            's_Segment2',
        ]

    @classmethod
    def get_tag_patterns(cls) -> list[str]:
        return [
            'z_FifoDataElement',
            'z_JunkData',
            'z_NoData'
        ]


class GmEmulationGenerator(plc.EmulationGenerator):
    """General Motors specific emulation logic generator."""

    generator_type = "GmController"

    @property
    def controller(self) -> GmController:
        return self.generator_object

    @controller.setter
    def controller(self, value: GmController):
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

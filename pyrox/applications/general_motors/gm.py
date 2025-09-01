"""General motors implimentation specific plc types
    """
from enum import Enum
import fnmatch
import importlib
from pyrox.models import HashList
import re
from typing import Optional, Union

from ...models.plc import emu


from ...models.plc.plc import (
    AddOnInstruction,
    Controller,
    Datatype,
    Module,
    NamedPlcObject,
    Program,
    Routine,
    Rung,
    PlcObject,
    Tag,
    ControllerConfiguration
)


from ...utils import find_duplicates


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


class GmPlcObject(PlcObject):

    @property
    def config(self) -> ControllerConfiguration:
        return ControllerConfiguration(aoi_type=GmAddOnInstruction,
                                       datatype_type=GmDatatype,
                                       module_type=GmModule,
                                       program_type=GmProgram,
                                       routine_type=GmRoutine,
                                       rung_type=GmRung,
                                       tag_type=GmTag)


class NamedGmPlcObject(NamedPlcObject, GmPlcObject):
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
        """Get the name of this controller without GM plant identification prefixes"""
        if self.name.startswith(('CG_', 'zz_', 'sz_', 'zs_')):
            return self.name[3:]

        return self.name


class GmAddOnInstruction(NamedGmPlcObject, AddOnInstruction):
    """General Motors AddOn Instruction Definition
    """


class GmDatatype(NamedGmPlcObject, Datatype):
    """General Motors Datatype
    """


class GmModule(NamedGmPlcObject, Module):
    """General Motors Module
    """


class GmRung(GmPlcObject, Rung):
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


class GmRoutine(NamedGmPlcObject, Routine):
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


class GmTag(NamedGmPlcObject, Tag):
    """General Motors Tag
    """


class GmProgram(NamedGmPlcObject, Program):
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


class GmController(NamedGmPlcObject, Controller):
    """General Motors Plc Controller
    """

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

    def generate_emulation_logic(self):
        """Generate GM emulation logic for the controller using the factory pattern."""
        generator = emu.EmulationFactory.create_generator(self)
        return generator.generate_emulation_logic()

    def remove_emulation_logic(self):
        """Remove GM emulation logic from the controller using the factory pattern."""
        from ...models.plc.emu import EmulationFactory

        generator = EmulationFactory.create_generator(self)
        return generator.remove_emulation_logic()

    def validate_text_lists(self):
        """validate all text lists within controller
        """
        duplicate_diags = find_duplicates(self.kdiags, True)

        return duplicate_diags

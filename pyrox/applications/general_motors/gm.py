"""General motors implimentation specific plc types
    """
from enum import Enum
import fnmatch
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
        if not self._controller:
            return ControllerConfiguration(aoi_type=GmAddOnInstruction,
                                           datatype_type=GmDatatype,
                                           module_type=GmModule,
                                           program_type=GmProgram,
                                           routine_type=GmRoutine,
                                           rung_type=GmRung,
                                           tag_type=GmTag)
        return self._controller._config


class NamedGmPlcObject(GmPlcObject, NamedPlcObject):
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


class GmController(GmPlcObject, Controller):
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
        from ...models.plc.emu import EmulationFactory

        generator = EmulationFactory.create_generator(self)
        return generator.generate_emulation_logic()

    # def generate_emulation_logic(self):
    #     """Generate GM emulation logic for the controller.
    #     """
    #     if not self.mcp_program:
    #         raise ValueError('No MCP program found in the controller.')

    #     if not self.mcp_program.main_routine:
    #         raise ValueError('No main routine found in the MCP program.')

    #     if not self.safety_common_program:
    #         raise ValueError('No safety common program found in the controller.')

    #     if not self.safety_common_program.main_routine:
    #         raise ValueError('No main routine found in the safety common program.')

    #     schema = ControllerModificationSchema(
    #         source=None,
    #         destination=self
    #     )

    #     emu_routine: GmRoutine = GmRoutine(
    #         controller=self
    #     )
    #     emu_routine.name = 'aaa_Emulation'
    #     emu_routine.description = ''.join(
    #         [
    #             'Emulation routine for GM controller.\n',
    #             'This routine is auto-generated by Indicon LLC.\n',
    #             'Do not modify.'
    #         ]
    #     )
    #     emu_routine.clear_rungs()

    #     schema.add_routine_import(  # Import the emulation routine into the MCP program
    #         program_name=self.mcp_program.name,
    #         routine=emu_routine
    #     )
    #     schema.add_rung_import(  # Add JSR rung to the MCP program's main routine
    #         program_name=self.mcp_program.name,
    #         routine_name=self.mcp_program.main_routine_name,
    #         rung_number=-1,
    #         new_rung=Rung(controller=self,
    #                       text=f'JSR({emu_routine.name},0);',
    #                       comment='Call the emulation routine.')
    #     )
    #     schema.add_program_tag_import(  # Add uninhibit tag
    #         program_name=self.mcp_program.name,
    #         tag=Tag(controller=self,
    #                 name='Uninhibit',
    #                 datatype='INT',)
    #     )
    #     schema.add_program_tag_import(  # Add inhibit tag
    #         program_name=self.mcp_program.name,
    #         tag=Tag(controller=self,
    #                 name='Inhibit',
    #                 datatype='INT',)
    #     )
    #     schema.add_program_tag_import(  # Add toggle inhibit tag
    #         program_name=self.mcp_program.name,
    #         tag=Tag(controller=self,
    #                 name='toggle_inhibit',
    #                 datatype='BOOL',)
    #     )
    #     schema.add_program_tag_import(  # Add local mode tag
    #         program_name=self.mcp_program.name,
    #         tag=Tag(controller=self,
    #                 name='LocalMode',
    #                 datatype='INT',)
    #     )
    #     schema.add_program_tag_import(  # Add device data size tag
    #         program_name=self.mcp_program.name,
    #         tag=Tag(controller=self,
    #                 name='DeviceDataSize',
    #                 datatype='DINT',)
    #     )
    #     schema.add_program_tag_import(  # Add loop pointer tag
    #         program_name=self.mcp_program.name,
    #         tag=Tag(controller=self,
    #                 name='SusLoopPtr',
    #                 datatype='DINT',)
    #     )
    #     emu_routine.add_rung(  # Add rung to set up the emulation routine
    #         Rung(
    #             controller=self, text='MOV(0,Uninhibit)MOV(4,Inhibit);',
    #             comment='This routine is auto-generated by Indicon LLC. Do not modify.'
    #         )
    #     )
    #     emu_routine.add_rung(  # Add rung to handle toggle inhibit and set up the loop for scanning devices
    #         Rung(
    #             controller=self,
    #             text='[XIO(toggle_inhibit)MOV(Uninhibit,LocalMode),XIC(toggle_inhibit)MOV(Inhibit,LocalMode)]SIZE(EnetStorage.DeviceData,0,DeviceDataSize)SUB(DeviceDataSize,1,DeviceDataSize)CLR(SusLoopPtr);',  # noqa: E501
    #             comment='Handle toggle inhibit and set up the loop for scanning devices.',
    #             )
    #         )
    #     emu_routine.add_rung(  # Add rung to loop through devices and check if they are connected
    #         Rung(
    #             controller=self,
    #             text='LBL(SusLoop)XIC(toggle_inhibit)LES(SusLoopPtr,DeviceDataSize)ADD(SusLoopPtr,1,SusLoopPtr)OTU(EnetStorage.DeviceData[SusLoopPtr].Connected)OTL(EnetStorage.DeviceData[SusLoopPtr].LinkStatusAvail)OTL(EnetStorage.DeviceData[SusLoopPtr].Link.Scanned)JMP(SusLoop);',  # noqa: E501
    #             comment='Loop through the devices and check if they are connected.'
    #             )
    #         )

    #     for module in self.modules:
    #         emu_routine.add_rung(  # Add rung to set the mode of each module to LocalMode
    #             Rung(
    #                 controller=self,
    #                 text=f'SSV(Module,{module.name},Mode,LocalMode);',
    #                 comment=f'Set the mode of module {module.name} to LocalMode.'
    #             )
    #         )

    #     s_emu_routine: GmRoutine = GmRoutine(controller=self)
    #     s_emu_routine.name = 's_aaa_Emulation'
    #     s_emu_routine.description = ''.join(
    #         [
    #             'Emulation routine for GM controller in safety context.\n',
    #             'This routine is auto-generated by Indicon LLC.\n',
    #             'Do not modify.'
    #         ]
    #     )
    #     s_emu_routine.clear_rungs()

    #     schema.add_routine_import(  # Import the safety emulation routine into the safety common program
    #         program_name=self.safety_common_program.name,
    #         routine=s_emu_routine
    #     )
    #     schema.add_rung_import(  # Add JSR rung to the safety common program's main routine
    #         program_name=self.safety_common_program.name,
    #         routine_name=self.safety_common_program.main_routine_name,
    #         rung_number=0,
    #         new_rung=Rung(controller=self,
    #                       text=f'JSR({s_emu_routine.name},0);',
    #                       comment='Call the safety emulation routine.')
    #     )
    #     g115_drives = [x for x in self.modules if x.type_ == 'G115Drive']
    #     sbks = [x for x in self.modules if x.type_ == 'AB_1732EsSafetyBlock']
    #     hmi_cards = [x for x in self.modules if x.type_ == 'AB_1734IB8S' and 'ECS5022 HMI\nSlot 1 Safety Module' in x.description]
    #     self.logger.info('Found %d Siemens G115 drive modules...', len(g115_drives))
    #     self.logger.info('Found %d AB 1732ES Safety Block modules...', len(sbks))
    #     self.logger.info('Found %d AB 1734IB8S HMI modules...', len(hmi_cards))

    #     if g115_drives:
    #         schema.add_import_from_file(
    #             file_location=r'docs\controls\emu\Demo3D_G115D_Drive_DataType.L5X',
    #             asset_types=['DataTypes']
    #         )
    #         schema.add_tag_import(Tag(controller=self,
    #                                   name=f'zz_Demo3D_{self.name}_Siemens_Drives',
    #                                   tag_type='Base',
    #                                   datatype='Demo3D_G115D_Drive',
    #                                   dimensions='150',
    #                                   constant=False,
    #                                   external_access='Read/Write',))
    #         for index, drive in enumerate(g115_drives):
    #             emu_routine.add_rung(Rung(controller=self.controller,
    #                                       text=f'[CPS(zz_Demo3D_{self.name}_Siemens_Drives[{index}].Inputs.StatusWord1,{drive.name}:I.Data[0],1)CPS(zz_Demo3D_{self.name}_Siemens_Drives[{index}].Inputs.RPMRef,{drive.name}:I.Data[1],1)CPS(zz_Demo3D_{self.name}_Siemens_Drives[{index}].Inputs.AmpsRef,{drive.name}:I.Data[2],1),CPS(zz_Demo3D_{self.name}_Siemens_Drives[{index}].Inputs.TorqueRef,{drive.name}:I.Data[3],1)CPS(zz_Demo3D_{self.name}_Siemens_Drives[{index}].Inputs.AlarmCode,{drive.name}:I.Data[4],1)CPS(zz_Demo3D_{self.name}_Siemens_Drives[{index}].Inputs.FaultCode,{drive.name}:I.Data[5],1),CPS(zz_Demo3D_{self.name}_Siemens_Drives[{index}].Inputs.StatusWord4,{drive.name}:I.Data[6],1)CPS(zz_Demo3D_{self.name}_Siemens_Drives[{index}].Inputs.SpareInt1,{drive.name}:I.Data[7],1)CPS(zz_Demo3D_{self.name}_Siemens_Drives[{index}].Inputs.PowerUnitTempC,{drive.name}:I.Data[8],1),CPS(zz_Demo3D_{self.name}_Siemens_Drives[{index}].Inputs.StatusWord5,{drive.name}:I.Data[9],1)CPS(zz_Demo3D_{self.name}_Siemens_Drives[{index}].Inputs.MotorTempC,{drive.name}:I.Data[10],1)CPS(zz_Demo3D_{self.name}_Siemens_Drives[{index}].Inputs.SafetySTO_Out,{drive.name}:I.Data[11],1),CPS(zz_Demo3D_{self.name}_Siemens_Drives[{index}].Inputs.SafetySTOSts,{drive.name}:I.Data[12],1),CPS({drive.name}:O.Data[0],zz_Demo3D_{self.name}_Siemens_Drives[{index}].Outputs.ControlWord1,1)CPS({drive.name}:O.Data[1],zz_Demo3D_{self.name}_Siemens_Drives[{index}].Outputs.Setpoint,1)];',  # noqa: E501
    #                                       comment='Clear the fault and move the data from the G115 drive to the input data.'))

    #     if hmi_cards:
    #         schema.add_import_from_file(
    #             file_location=r'docs\controls\emu\Demo3D_HMI_IN_DataType.L5X',
    #             asset_types=['DataTypes']
    #         )
    #         for card in hmi_cards:
    #             schema.add_tag_import(Tag(controller=self,
    #                                       name=f'sz_Demo3D_{card.name}_I',
    #                                       class_='Safety',
    #                                       tag_type='Base',
    #                                       datatype='Demo3D_HMI_IN',
    #                                       constant=False,
    #                                       external_access='Read/Write',))
    #             emu_routine.add_rung(Rung(controller=self.controller,
    #                                       text=f'CLR({card.parent_module}:2:I.Fault)MOV(sz_Demo3D_{card.name}_I.S2.Word1,{card.parent_module}:2:I.Data);',  # noqa: E501
    #                                       comment='Clear the fault and move the data from the HMI card to the input data.'))

    #     if sbks:
    #         schema.add_import_from_file(
    #             file_location=r'docs\controls\emu\Demo3D_WDint_DataType.L5X',
    #             asset_types=['DataTypes'])
    #         for index, module in enumerate(sbks):
    #             schema.add_tag_import(Tag(controller=self,
    #                                       name=f'sz_Demo3D_{module.name}_I',
    #                                       class_='Safety',
    #                                       tag_type='Base',
    #                                       datatype='Demo3D_WDint',
    #                                       constant=False,
    #                                       external_access='Read/Write',))

    #             schema.add_tag_import(Tag(controller=self,
    #                                       name=f'zz_Demo3D_{module.name}_O',
    #                                       tag_type='Base',
    #                                       datatype='DINT',
    #                                       constant=False,
    #                                       external_access='Read/Write',))

    #             emu_routine.add_rung(Rung(controller=self,
    #                                       text=f'COP({module.name}:O,zz_Demo3D_{module.name}_O,1);',
    #                                       comment='Copy the output data from the safety block to the emulation tag.'))

    #             s_emu_routine.add_rung(Rung(controller=self,
    #                                         text=f'COP(sz_Demo3D_{module.name}_I,{module.name}:I,1);',
    #                                         comment='Copy the input data from the emulation tag to the safety block.'))

    #     schema.execute()
    #     self.logger.info('Emulation logic generated for MCP program: %s', self.mcp_program.name)

    def validate_text_lists(self):
        """validate all text lists within controller
        """
        duplicate_diags = find_duplicates(self.kdiags, True)

        return duplicate_diags


class GmEmulationGenerator(emu.BaseEmulationGenerator):
    """General Motors specific emulation logic generator."""

    controller_type = "GmController"

    def _add_base_tags(self) -> None:
        """Add base tags required for emulation."""
        self.logger.debug('Adding base tags for GM emulation...')

        program_name = self.controller.mcp_program.name

        self.add_program_tag(program_name, 'Uninhibit', 'INT')
        self.add_program_tag(program_name, 'Inhibit', 'INT')
        self.add_program_tag(program_name, 'toggle_inhibit', 'BOOL')
        self.add_program_tag(program_name, 'LocalMode', 'INT')
        self.add_program_tag(program_name, 'DeviceDataSize', 'DINT')
        self.add_program_tag(program_name, 'SusLoopPtr', 'DINT')

    def _add_base_rungs(self, emu_routine: Routine) -> None:
        """Add base emulation rungs."""
        self.logger.debug('Adding base rungs for GM emulation...')

        emu_routine.add_rung(Rung(  # Setup rung
            controller=self.controller,
            text='MOV(0,Uninhibit)MOV(4,Inhibit);',
            comment='This routine is auto-generated by Indicon LLC. Do not modify.'
        ))

        emu_routine.add_rung(Rung(
            controller=self.controller,
            text='XIC(Flash.Norm)OTE(Flash.Fast);',
            comment='Reduce fast flash rate to limit communication issues with the 3d model.'
        ))

        emu_routine.add_rung(Rung(  # Toggle inhibit and device loop setup
            controller=self.controller,
            text='[XIO(toggle_inhibit)MOV(Uninhibit,LocalMode),XIC(toggle_inhibit)MOV(Inhibit,LocalMode)]SIZE(EnetStorage.DeviceData,0,DeviceDataSize)SUB(DeviceDataSize,1,DeviceDataSize)CLR(SusLoopPtr);',  # noqa: E501
            comment='Handle toggle inhibit and set up the loop for scanning devices.'
        ))

        emu_routine.add_rung(Rung(  # Device loop rung
            controller=self.controller,
            text='LBL(SusLoop)XIC(toggle_inhibit)LES(SusLoopPtr,DeviceDataSize)ADD(SusLoopPtr,1,SusLoopPtr)OTU(EnetStorage.DeviceData[SusLoopPtr].Connected)OTL(EnetStorage.DeviceData[SusLoopPtr].LinkStatusAvail)OTL(EnetStorage.DeviceData[SusLoopPtr].Link.Scanned)JMP(SusLoop);',  # noqa: E501
            comment='Loop through the devices and check if they are connected.'
        ))

        # Module mode setting
        for module in self.controller.modules:
            emu_routine.add_rung(Rung(
                controller=self.controller,
                text=f'SSV(Module,{module.name},Mode,LocalMode);',
                comment=f'Set the mode of module {module.name} to LocalMode.'
            ))

    def _generate_g115_drive_emulation(self) -> None:
        """Generate Siemens G115 drive emulation logic."""
        g115_drives = self.get_modules_by_type('G115Drive')
        self.logger.info('Found %d Siemens G115 drive modules...', len(g115_drives))

        if not g115_drives:
            self.logger.debug('No Siemens G115 drive modules found, skipping emulation generation.')
            return

        # Import required datatypes
        self.schema.add_import_from_file(
            file_location=r'docs\controls\emu\Demo3D_G115D_Drive_DataType.L5X',
            asset_types=['DataTypes']
        )

        # Add controller tag for drives
        self.add_controller_tag(
            tag_name=f'zz_Demo3D_{self.controller.name}_Siemens_Drives',
            datatype='Demo3D_G115D_Drive',
            tag_type='Base',
            dimensions='150',
            constant=False,
            external_access='Read/Write'
        )

        # Generate drive emulation rungs
        for index, drive in enumerate(g115_drives):
            rung_text = f'[CPS(zz_Demo3D_{self.controller.name}_Siemens_Drives[{index}].Inputs.StatusWord1,{drive.name}:I.Data[0],1)CPS(zz_Demo3D_{self.controller.name}_Siemens_Drives[{index}].Inputs.RPMRef,{drive.name}:I.Data[1],1)CPS(zz_Demo3D_{self.controller.name}_Siemens_Drives[{index}].Inputs.AmpsRef,{drive.name}:I.Data[2],1),CPS(zz_Demo3D_{self.controller.name}_Siemens_Drives[{index}].Inputs.TorqueRef,{drive.name}:I.Data[3],1)CPS(zz_Demo3D_{self.controller.name}_Siemens_Drives[{index}].Inputs.AlarmCode,{drive.name}:I.Data[4],1)CPS(zz_Demo3D_{self.controller.name}_Siemens_Drives[{index}].Inputs.FaultCode,{drive.name}:I.Data[5],1),CPS(zz_Demo3D_{self.controller.name}_Siemens_Drives[{index}].Inputs.StatusWord4,{drive.name}:I.Data[6],1)CPS(zz_Demo3D_{self.controller.name}_Siemens_Drives[{index}].Inputs.SpareInt1,{drive.name}:I.Data[7],1)CPS(zz_Demo3D_{self.controller.name}_Siemens_Drives[{index}].Inputs.PowerUnitTempC,{drive.name}:I.Data[8],1),CPS(zz_Demo3D_{self.controller.name}_Siemens_Drives[{index}].Inputs.StatusWord5,{drive.name}:I.Data[9],1)CPS(zz_Demo3D_{self.controller.name}_Siemens_Drives[{index}].Inputs.MotorTempC,{drive.name}:I.Data[10],1)CPS(zz_Demo3D_{self.controller.name}_Siemens_Drives[{index}].Inputs.SafetySTO_Out,{drive.name}:I.Data[11],1),CPS(zz_Demo3D_{self.controller.name}_Siemens_Drives[{index}].Inputs.SafetySTOSts,{drive.name}:I.Data[12],1),CPS({drive.name}:O.Data[0],zz_Demo3D_{self.controller.name}_Siemens_Drives[{index}].Outputs.ControlWord1,1)CPS({drive.name}:O.Data[1],zz_Demo3D_{self.controller.name}_Siemens_Drives[{index}].Outputs.Setpoint,1)];'  # noqa: E501

            self._emu_routine.add_rung(Rung(
                controller=self.controller,
                text=rung_text,
                comment='Clear the fault and move the data from the G115 drive to the input data.'
            ))

    def _generate_hmi_card_emulation(self) -> None:
        """Generate HMI card emulation logic."""
        hmi_cards = self.get_modules_by_description_pattern('<@TYPE 502xSlot1>')
        hmi_cards = [x for x in hmi_cards if x.type_ == 'AB_1734IB8S']
        self.logger.info('Found %d AB 1734IB8S HMI modules...', len(hmi_cards))

        if not hmi_cards:
            return

        # Import required datatypes
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
            tag_name=f'zz_Demo3D_Comm_{self.controller.name}HMI',
            tag_type='Base',
            datatype='Demo3D_CommOK_HMI',
            constant=False,
            external_access='Read/Write'
        )

        # Generate HMI emulation logic
        for card in hmi_cards:
            std_tag = self.add_controller_tag(
                tag_name=f'zz_Demo3D_{card.parent_module}_I',
                class_='Standard',
                tag_type='Base',
                datatype='Demo3D_HMI_IN',
                constant=False,
                external_access='Read/Write'
            )

            sfty_tag = self.add_controller_tag(
                tag_name=f'sz_Demo3D_{card.parent_module}_I',
                class_='Safety',
                tag_type='Base',
                datatype='Demo3D_HMI_IN',
                constant=False,
                external_access='Read/Write'
            )

            self.add_controller_tag(
                tag_name=f'zz_Demo3D_{card.parent_module}_O',
                tag_type='Base',
                datatype='Demo3D_HMI_OUT',
                constant=False,
                external_access='Read/Write'
            )

            # Add safety tag mapping to schema
            self.schema.add_safety_tag_mapping(
                std_tag.name,
                sfty_tag.name,
            )

            self._emu_routine.add_rung(Rung(
                controller=self.controller,
                text=f'CLR({card.parent_module}:2:I.Fault)MOV(sz_Demo3D_{card.parent_module}_I.S2.Word1,{card.parent_module}:2:I.Data);',
                comment='Clear the fault and move the data from the HMI card to the input data.'
            ))

            self._emu_routine.add_rung(Rung(
                controller=self.controller,
                text=f'COP({card.parent_module}:2:O,zz_Demo3D_{card.parent_module}_O.S2,1);',
                comment='Map output data from physical card to emulation card.'
            ))

            # Add to safety emulation routine
            self._s_emu_routine.add_rung(Rung(
                controller=self.controller,
                text=f'COP(sz_Demo3D_{card.name}_I,{card.parent_module}:1:I,1);',
                comment='Copy the input data from the emulation tag to the safety input card.'
            ))

    def _generate_safety_block_emulation(self) -> None:
        """Generate safety block emulation logic."""
        sbks = self.get_modules_by_type('AB_1732EsSafetyBlock')
        self.logger.info('Found %d AB 1732ES Safety Block modules...', len(sbks))

        if not sbks:
            return

        # Import required datatypes
        self.schema.add_import_from_file(
            file_location=r'docs\controls\emu\Demo3D_WDint_DataType.L5X',
            asset_types=['DataTypes']
        )
        self.schema.add_import_from_file(
            file_location=r'docs\controls\emu\Demo3D_CommOK_SBK_DataType.L5X',
            asset_types=['DataTypes']
        )

        # Generate generic comm word
        self.add_controller_tag(
            tag_name=f'zz_Demo3D_Comm_{self.controller.name}SBK',
            tag_type='Base',
            datatype='Demo3D_CommOK_SBK',
            constant=False,
            external_access='Read/Write'
        )

        # Generate safety block emulation logic
        for module in sbks:
            # Add standard input tag
            std_tag = self.add_controller_tag(
                tag_name=f'zz_Demo3D_{module.name}_I',
                class_='Standard',
                tag_type='Base',
                datatype='Demo3D_WDint',
                constant=False,
                external_access='Read/Write'
            )

            # Add safe input tag
            sfty_tag = self.add_controller_tag(
                tag_name=f'sz_Demo3D_{module.name}_I',
                class_='Safety',
                tag_type='Base',
                datatype='Demo3D_WDint',
                constant=False,
                external_access='Read/Write'
            )

            # Add output tag
            self.add_controller_tag(
                tag_name=f'zz_Demo3D_{module.name}_O',
                tag_type='Base',
                datatype='DINT',
                constant=False,
                external_access='Read/Write'
            )

            # Add safety tag mapping to schema
            self.schema.add_safety_tag_mapping(
                std_tag.name,
                sfty_tag.name,
            )

            # Add to main emulation routine
            self._emu_routine.add_rung(Rung(
                controller=self.controller,
                text=f'COP({module.name}:O,zz_Demo3D_{module.name}_O,1);',
                comment='Copy the output data from the safety block to the emulation tag.'
            ))

            # Add to safety emulation routine
            self._s_emu_routine.add_rung(Rung(
                controller=self.controller,
                text=f'COP(sz_Demo3D_{module.name}_I,{module.name}:I,1);',
                comment='Copy the input data from the emulation tag to the safety block.'
            ))

    def generate_base_emulation(self) -> None:
        """Generate base GM emulation logic."""
        self.logger.info("Generating base GM emulation logic...")

        # Create main emulation routine
        emu_routine = self.add_emulation_routine(
            program_name=self.controller.mcp_program.name,
            routine_name='aaa_Emulation',
            routine_description=''.join([
                'Emulation routine for GM controller.\n',
                'This routine is auto-generated by Indicon LLC.\n',
                'Do not modify.'
            ])
        )

        # Add base program tags
        self._add_base_tags()

        # Add base emulation rungs
        self._add_base_rungs(emu_routine)

        # Create safety emulation routine
        s_emu_routine = self.add_emulation_routine(
            program_name=self.controller.safety_common_program.name,
            routine_name='s_aaa_Emulation',
            routine_description=''.join([
                'Emulation routine for GM controller in safety context.\n',
                'This routine is auto-generated by Indicon LLC.\n',
                'Do not modify.'
            ]),
            rung_position=0  # Insert at beginning for safety
        )

        # Store routines for module emulation
        self._emu_routine = emu_routine
        self._s_emu_routine = s_emu_routine

    def generate_module_emulation(self) -> None:
        """Generate module-specific emulation logic."""
        self.logger.info("Generating GM module-specific emulation logic...")

        self._generate_g115_drive_emulation()
        self._generate_hmi_card_emulation()
        self._generate_safety_block_emulation()

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

"""General motors implimentation specific plc types
    """
from enum import Enum
import fnmatch
import re
from typing import Optional, Union


from .plc import (
    AddOnInstruction,
    Controller,
    Datatype,
    Module,
    Program,
    Routine,
    Rung,
    PlcObject,
    Tag,
    ControllerConfiguration
)


GM_CHAR = 'z'
USER_CHAR = 'u'
ALARM_PATTERN:   str = '*<Alarm[[]*[]]:*>'
PROMPT_PATTERN:  str = '*<Prompt[[]*[]]:*>'

DIAG_RE_PATTERN:    str = r"(<.+\[\d*\].*>)"
DIAG_NUM_RE_PATTERN: str = r"(?:<.*\[)(\d*)(?:\].*>)"
COLUMN_RE_PATTERN:   str = r"(?:<.*\[\d+\]:\s)(@[a-zA-Z]+\d+)(?:.*)>"


class KDiagType(Enum):
    NA:     int = 0
    ALARM:  int = 1
    PROMPT: int = 2
    VALUE:  int = 3


class KDiag:
    """General Motors "k" Diagnostic Object
    """

    def __init__(self,
                 diag_type: KDiagType,
                 text: str,
                 parent_offset: Optional[Union[str, int]] = 0):
        if diag_type is KDiagType.NA:
            raise ValueError('Cannot be NA!')

        self.text:            str = self._get_diag_text(text)
        self.diag_type: KDiagType = diag_type
        self.col_location:    str = self._get_col_location()
        self.number:          int = self._get_diag_number()
        self.parent_offset:   int = int(parent_offset)

    def __repr__(self) -> str:
        return (
            f'KDiag(text={self.text}, '
            f'diag_type={self.diag_type}, '
            f'col_location={self.col_location}, '
            f'number={self.number}, '
            f'parent_offset={self.parent_offset})'
        )

    def __str__(self):
        return self.text

    @property
    def global_number(self) -> int:
        return self.number + self.parent_offset

    def _get_col_location(self):
        col_match = re.search(COLUMN_RE_PATTERN, self.text)
        if col_match:
            return col_match.groups()[0]

        return None

    def _get_diag_number(self):
        match = re.search(DIAG_NUM_RE_PATTERN, self.text)
        if match:
            return int(match.groups()[0])

        raise ValueError('Could not find diag number in diag string! -> %s' % self.text)

    def _get_diag_text(self, text: str):
        match = re.search(DIAG_RE_PATTERN, text)
        if match:
            return match.groups()[0]

        raise ValueError('Could not find diag text in diag string! -> %s' % self.text)


class SupportsGmNaming(PlcObject):
    """This Plc object supports General Motors Stylized Naming Schemes

    e.g. 'za_Action' or 'zZ999_Diagnostics'.
    """

    @property
    def is_gm_owned(self) -> bool:
        return True if self.name.lower().startswith(GM_CHAR) else False

    @property
    def is_user_owned(self) -> bool:
        return True if self.name.lower().startswith(USER_CHAR) else False


class GmAddOnInstruction(SupportsGmNaming, AddOnInstruction):
    """General Motors AddOn Instruction Definition
    """


class GmDatatype(SupportsGmNaming, Datatype):
    """General Motors Datatype
    """


class GmModule(SupportsGmNaming, Module):
    """General Motors Module
    """


class GmRung(SupportsGmNaming, Rung):
    """General Motors Rung
    """

    @property
    def kdiags(self) -> list[KDiag]:
        return self._get_comment_diags()

    @property
    def has_kdiag(self) -> bool:
        if not self.comment:
            return False

        return True if '<@DIAG>' in self.comment else False

    def _get_comment_diags(self) -> list[KDiag]:
        if not self.comment:
            return []

        comment_lines = self.comment.splitlines()
        ret_list = []

        for line in comment_lines:
            if fnmatch.fnmatch(line, ALARM_PATTERN):
                ret_list.append(KDiag(KDiagType.ALARM,
                                      line,
                                      self.routine.program.parameter_offset))

            elif fnmatch.fnmatch(line, PROMPT_PATTERN):
                ret_list.append(KDiag(KDiagType.PROMPT,
                                      line,
                                      self.routine.program.parameter_offset))

        return ret_list

    @property
    def routine(self) -> "GmRoutine":
        return self._routine


class GmRoutine(SupportsGmNaming, Routine):
    """General Motors Routine
    """

    @property
    def kdiags(self) -> list[GmRung]:
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


class GmTag(SupportsGmNaming, Tag):
    """General Motors Tag
    """


class GmProgram(SupportsGmNaming, Program):
    """General Motors Program
    """
    PARAM_RTN_STR = 'B*_Parameters'

    PARAM_MATCH_STR = "MOV(*,HMI.Diag.Pgm.MsgOffset);"

    @property
    def is_gm_owned(self) -> bool:
        return len(self.gm_routines) > 0

    @property
    def is_user_owned(self) -> bool:
        return len(self.user_routines) > 0

    @property
    def kdiags(self) -> list[KDiag]:
        x = []
        for routine in self.routines:
            x.extend(routine.kdiags)
        return x

    @property
    def parameter_offset(self) -> int:
        if not self.parameter_routine:
            return None

        for rung in self.parameter_routine.rungs:
            if fnmatch.fnmatch(rung.text, self.PARAM_MATCH_STR):
                return int(rung.text.replace("MOV(", '').replace(',HMI.Diag.Pgm.MsgOffset);', ''))
        return None

    @property
    def parameter_routine(self) -> GmRoutine:
        for routine in self.routines:
            if fnmatch.fnmatch(routine.name, self.PARAM_RTN_STR):
                return routine
        return None

    @property
    def routines(self) -> list[GmRoutine]:
        return super().routines

    @property
    def gm_routines(self) -> list[GmRoutine]:
        return [x for x in self.routines if x.is_gm_owned]

    @property
    def user_routines(self) -> list[GmRoutine]:
        return [x for x in self.routines if x.is_user_owned]


class GmController(SupportsGmNaming, Controller):
    """General Motors Plc Controller
    """

    def __init__(self, root_meta_data):
        config = ControllerConfiguration(
            aoi_type=GmAddOnInstruction,
            datatype_type=GmDatatype,
            module_type=GmModule,
            program_type=GmProgram,
            routine_type=GmRoutine,
            rung_type=GmRung,
            tag_type=GmTag,
        )
        super().__init__(root_meta_data=root_meta_data,
                         config=config)

    @property
    def kdiags(self) -> list[KDiag]:
        x = []
        for program in self.programs:
            x.extend(program.kdiags)
        return x

    @property
    def programs(self) -> list[GmProgram]:
        return super().programs

    @property
    def gm_programs(self) -> list[GmProgram]:
        return [x for x in self.programs if x.is_gm_owned]

    @property
    def user_program(self) -> list[GmProgram]:
        return [x for x in self.programs if x.is_user_owned]

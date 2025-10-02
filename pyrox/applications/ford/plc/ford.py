"""Ford implimentation specific plc types
"""
from typing import Optional, TypeVar

from pyrox.models import HashList, plc, SupportsMetaData
from pyrox.models import eplan
from pyrox.services.logging import log
from pyrox.applications.eplan import BaseEplanProject


FORD_CTRL = TypeVar('FORD_CTRL', bound='FordController')


class FordPlcObject(plc.PlcObject[FORD_CTRL]):

    @property
    def config(self) -> plc.ControllerConfiguration:
        return plc.ControllerConfiguration(
            aoi_type=FordAddOnInstruction,
            controller_type=FordController,
            datatype_type=FordDatatype,
            module_type=FordModule,
            program_type=FordProgram,
            routine_type=FordRoutine,
            rung_type=FordRung,
            tag_type=FordTag
        )


class NamedFordPlcObject(plc.NamedPlcObject, FordPlcObject):
    """Ford Named Plc Object"""


class FordAddOnInstruction(NamedFordPlcObject, plc.AddOnInstruction):
    """General Motors AddOn Instruction Definition"""


class FordDatatype(NamedFordPlcObject, plc.Datatype):
    """General Motors Datatype"""


class FordModule(NamedFordPlcObject, plc.Module):
    """General Motors Module
    """


class FordRung(FordPlcObject[FORD_CTRL], plc.Rung):
    """Ford Rung
    """


class FordRoutine(NamedFordPlcObject, plc.Routine):
    """Ford Routine
    """

    @property
    def program(self) -> "FordProgram":
        return self._program

    @property
    def rungs(self) -> list[FordRung]:
        return super().rungs


class FordTag(NamedFordPlcObject, plc.Tag):
    """Ford Tag
    """


class FordProgram(NamedFordPlcObject, plc.Program):
    """Ford Program
    """

    @property
    def routines(self) -> HashList[FordRoutine]:
        return super().routines

    @property
    def comm_edit_routine(self) -> Optional[FordRoutine]:
        return self.routines.get('A_Comm_Edit', None)


class FordController(NamedFordPlcObject, plc.Controller):
    """Ford Plc Controller
    """

    generator_type = 'FordEmulationGenerator'

    @property
    def main_program(self) -> Optional[FordProgram]:
        return self.programs.get('MainProgram', None)

    @property
    def modules(self) -> HashList[FordModule]:
        return super().modules

    @property
    def programs(self) -> HashList[FordProgram]:
        return super().programs


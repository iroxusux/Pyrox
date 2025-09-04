"""Ford implimentation specific plc types
"""
from typing import Optional

from pyrox.models import HashList
from pyrox.models.abc.generator import GeneratorFactory

from ...models.plc import (
    AddOnInstruction,
    Controller,
    ControllerMatcher,
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


class FordPlcObject(PlcObject):

    @property
    def config(self) -> ControllerConfiguration:
        return ControllerConfiguration(
            aoi_type=FordAddOnInstruction,
            datatype_type=FordDatatype,
            module_type=FordModule,
            program_type=FordProgram,
            routine_type=FordRoutine,
            rung_type=FordRung,
            tag_type=FordTag
        )


class NamedFordPlcObject(NamedPlcObject, FordPlcObject):
    """Ford Named Plc Object
    """


class FordAddOnInstruction(NamedFordPlcObject, AddOnInstruction):
    """General Motors AddOn Instruction Definition
    """


class FordDatatype(NamedFordPlcObject, Datatype):
    """General Motors Datatype
    """


class FordModule(NamedFordPlcObject, Module):
    """General Motors Module
    """


class FordRung(FordPlcObject, Rung):
    """Ford Rung
    """


class FordRoutine(NamedFordPlcObject, Routine):
    """Ford Routine
    """

    @property
    def program(self) -> "FordProgram":
        return self._program

    @property
    def rungs(self) -> list[FordRung]:
        return super().rungs


class FordTag(NamedFordPlcObject, Tag):
    """Ford Tag
    """


class FordProgram(NamedFordPlcObject, Program):
    """Ford Program
    """

    @property
    def routines(self) -> HashList[FordRoutine]:
        return super().routines

    @property
    def comm_edit_routine(self) -> Optional[FordRoutine]:
        return self.routines.get('A_Comm_Edit', None)


class FordController(NamedFordPlcObject, Controller):
    """Ford Plc Controller
    """

    controller_type = 'FordController'

    @property
    def main_program(self) -> Optional[FordProgram]:
        return self.programs.get('MainProgram', None)

    @property
    def modules(self) -> HashList[FordModule]:
        return super().modules

    @property
    def programs(self) -> HashList[FordProgram]:
        return super().programs

    def generate_emulation_logic(self):
        """Generate GM emulation logic for the controller using the factory pattern."""
        generator = GeneratorFactory.create_generator(self)
        return generator.generate_emulation_logic()

    def remove_emulation_logic(self):
        """Remove GM emulation logic from the controller using the factory pattern."""
        from ...models.plc.emu import EmulationFactory

        generator = EmulationFactory.create_generator(self)
        return generator.remove_emulation_logic()


class FordControllerMatcher(ControllerMatcher):
    """Matcher for GM controllers.
    """
    
    @classmethod
    def get_controller_constructor(cls):
        return FordController

    @classmethod
    def get_datatype_patterns(cls) -> list[str]:
        return [
            'Fudc_*',
            'Fudf_*',
            'Fudh_*',
            'Fuds_*',
            'Fudm_*',
        ]

    @classmethod
    def get_module_patterns(cls) -> list[str]:
        return [
            'HMI1KS1',
            'HMI1KS2',
        ]

    @classmethod
    def get_program_patterns(cls) -> list[str]:
        return [
            'NETWORK_DIAG',
            'HMI_COMN',
            'CONV_FIS',
            'HMI1_SCREENDRIVER',
        ]

    @classmethod
    def get_safety_program_patterns(cls) -> list[str]:
        return [
            '*_MAPPINGINPUTS_EDIT',
            '*_MAPPINGOUTPUTS_EDIT',
            '*_COMMONSAFETY_EDIT',
        ]

    @classmethod
    def get_tag_patterns(cls) -> list[str]:
        return [
            'FB1',
            'MB1',
            'WB1',
            'ZeroRef',
            'ZeroRefSafety'
        ]

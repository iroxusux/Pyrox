"""General motors implimentation specific plc types
    """


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


class GmRoutine(SupportsGmNaming, Routine):
    """General Motors Routine
    """


class GmTag(SupportsGmNaming, Tag):
    """General Motors Tag
    """


class GmProgram(SupportsGmNaming, Program):
    """General Motors Program
    """

    @property
    def is_gm_owned(self) -> bool:
        return len(self.gm_routines) > 0

    @property
    def is_user_owned(self) -> bool:
        return len(self.user_routines) > 0

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
    def programs(self) -> list[GmProgram]:
        return super().programs

    @property
    def gm_programs(self) -> list[GmProgram]:
        return [x for x in self.programs if x.is_gm_owned]

    @property
    def user_program(self) -> list[GmProgram]:
        return [x for x in self.programs if x.is_user_owned]

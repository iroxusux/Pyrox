"""Ford implimentation specific plc types
"""
from typing import Optional, TypeVar

from pyrox.models import HashList, plc, SupportsMetaData
from pyrox.models import eplan
from pyrox.services.logging import log
from .generator import BaseEmulationGenerator
from .indicon import BaseControllerValidator, BaseEplanProject


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


class FordControllerMatcher(plc.ControllerMatcher):
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


class FordEmulationGenerator(BaseEmulationGenerator):
    """Ford specific emulation logic generator."""
    supporting_class = FordController

    @property
    def controller(self) -> FordController:
        return self.generator_object

    @controller.setter
    def controller(self, value: FordController):
        if value.__class__.__name__ != self.supporting_class:
            raise TypeError(f'Controller must be of type {self.supporting_class}, got {value.__class__.__name__} instead.')
        self._generator_object = value

    @property
    def custom_tags(self) -> list[tuple[str, str, str, str]]:
        return []

    @property
    def target_safety_program_name(self) -> str:
        if hasattr(self, '_target_safety_program_name'):
            return self._target_safety_program_name
        self._target_safety_program_name = next((x.name for x in self.controller.safety_programs if "MappingInputs_Edit" in x.name), None)
        return self._target_safety_program_name

    @property
    def target_standard_program_name(self) -> str:
        return "MainProgram"

    def disable_all_comm_edit_routines(self):
        """Disable all Comm Edit routines in all programs."""
        for program in self.controller.programs:
            if not program.comm_edit_routine:
                continue
            program.block_routine(
                program.comm_edit_routine.name,
                self.test_mode_tag
            )

    def _scrape_all_comm_ok_bits(self) -> list[plc.LogixInstruction]:
        """Scrape all Comm OK bits from the Comm Edit routine."""
        comm_ok_bits = []
        for program in self.controller.programs:
            comm_edit = program.comm_edit_routine
            if not comm_edit:
                log().debug(f"No Comm Edit routine found in program {program.name}, skipping.")
                continue
            for instruction in comm_edit.instructions:
                if 'CommOk' in instruction.meta_data and instruction.instruction_name in ['OTE', 'OTL']:
                    comm_ok_bits.append(instruction)
        return comm_ok_bits

    def _generate_custom_logic(self):
        comm_ok_bits = self._scrape_all_comm_ok_bits()
        if not comm_ok_bits:
            log().warning("No Comm OK bits found in Comm Edit routines.")

        for bit in comm_ok_bits:
            device_name = bit.operands[0].meta_data.split('.')[0]
            comm_tag = self.add_controller_tag(
                tag_name=f'zz_Demo3D_COMM_OK_{device_name}',
                datatype='BOOL',
                description='Emulation Comm OK Bit'
            )
            pwr1_tag = self.add_controller_tag(
                tag_name=f'zz_Demo3D_Pwr1_{device_name}',
                datatype='BOOL',
                description='Emulation Power Circuit 1 OK Bit\n(Comm Power)'
            )
            pwr2_tag = self.add_controller_tag(
                tag_name=f'zz_Demo3D_Pwr2_{device_name}',
                datatype='BOOL',
                description='Emulation Power Circuit 1 OK Bit\n(Output Power)'
            )

            top_branch_text = f"XIC(S:FS)OTL({comm_tag.name})OTL({pwr1_tag.name})OTL({pwr2_tag.name})"
            btm_branch_text = f"XIC({comm_tag.name})XIC({pwr1_tag.name})XIC({pwr2_tag.name}){bit.meta_data}"

            rung = self.controller.config.rung_type(
                controller=self.controller,
                text=f"[{top_branch_text}),{btm_branch_text}];",
                comment='// Emulate comm ok status.\nComm and Power Managed by Emulation Model.'
            )
            self.add_rung_to_standard_routine(rung)

        self.disable_all_comm_edit_routines()


class FordControllerValidator(BaseControllerValidator):
    """Validator for Ford controllers.
    """
    supporting_class = FordController


class FordEplanProject(BaseEplanProject):
    supporting_class = FordController

    class IpAddressSheet(SupportsMetaData):
        def __init__(self, sheet: dict):
            super().__init__(sheet)
            self._devices: list[eplan.project.EplanNetworkDevice] = []

        @property
        def indexed_attribute(self) -> dict:
            return self.meta_data.get('data', {})

        @property
        def sheet_objects(self) -> list[dict]:
            return self[eplan.meta.EPLAN_SHEET_OBJECTS_KEY]

        def _parse_sheet_object(self, obj: dict) -> Optional[eplan.project.EplanNetworkDevice]:
            meta_data: list[dict] = obj.get(eplan.meta.EPLAN_SHEET_META_DATA_KEY, [])

            if not isinstance(meta_data, list):
                return None

            if len(meta_data) != 3:
                log().warning(f"Unexpected metadata format in sheet object: {meta_data}")
                return None

            interest_key = '@A511'
            device_index = 0
            description_index = 1
            ip_index = 2

            device_name = BaseEplanProject.strip_eplan_naming_conventions(
                meta_data[device_index].get(interest_key, eplan.meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)
            )
            description = BaseEplanProject.strip_eplan_naming_conventions(
                meta_data[description_index].get(interest_key, eplan.meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)
            )
            ip_address = BaseEplanProject.strip_eplan_naming_conventions(
                meta_data[ip_index].get(interest_key, eplan.meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)
            )

            return eplan.project.EplanNetworkDevice(
                name=device_name,
                description=description,
                ip_address=ip_address,
                data=meta_data
            )

        def get_project_devices(self) -> list[eplan.project.EplanProjectDevice]:
            if self._devices:
                return self._devices

            for obj in self.sheet_objects:
                device = self._parse_sheet_object(obj)
                if device is None:
                    log().debug(f"Skipping invalid or incomplete sheet object: {obj}")
                    continue
                self._devices.append(device)

            if len(self._devices) == 0:
                log().warning("No valid devices found in the IP Address sheet.")

            return self._devices

    @property
    def ip_address_sheet(self) -> Optional[IpAddressSheet]:
        sheet = next((
            sheet for sheet in self.sheet_details if 'Device IP / Network Address List' in sheet.get('name', '')
        ), None)
        if not sheet:
            return None
        return self.IpAddressSheet(sheet)

    def _gather_project_ethernet_devices(self):
        ip_sheet = self.ip_address_sheet
        if not ip_sheet:
            log().warning("No 'Device IP / Network Address List' sheet found in the project.")
            return

        devices = ip_sheet.get_project_devices()
        if not devices:
            log().warning("No devices found on the 'Device IP / Network Address List' sheet.")
            return

        self.devices.extend(devices)

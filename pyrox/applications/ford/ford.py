"""Ford implimentation specific plc types
"""
from typing import Optional, TypeVar

from pyrox.models import HashList, plc, SupportsMetaData
from pyrox.models import eplan
from pyrox.services.logging import log
from ..indicon import BaseEplanProject


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

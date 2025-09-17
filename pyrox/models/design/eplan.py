"""EPLAN design models.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Self
from pyrox.models.abc import MetaFactory, FactoryTypeMeta, SupportsFileLocation, SupportsMetaData

EPLAN_PROJECT_ROOT = 'EplanPxfRoot'
EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT = 'Unknown'
EPLAN_PROJECT_SHEET_KEY = 'O4'
EPLAN_PROJECT_DATA_KEY = 'O14'
EPLAN_PROJECT_BOM_KEY = 'O117'
EPLAN_PROJECT_DEVICE_KEY = 'O6'
EPLAN_PROJECT_PROPERTY_KEY = 'P11'
EPLAN_PROJECT_DESIGN_SOURCE_KEY = '@P10015'
EPLAN_PROJECT_FACTORY_NAME_KEY = '@P10035'
EPLAN_PROJECT_FACTORY_TYPE_KEY = '@P10032'
EPLAN_PROJECT_ADDRESS_LINE1_KEY = '@P10016'
EPLAN_PROJECT_ADDRESS_LINE2_KEY = '@P10017'
EPLAN_PROJECT_NUMBER_KEY = '@P10180'
EPLAN_PROJECT_TEMPLATE_KEY = '@P10011'


class EplanProjectFactory(MetaFactory):
    """Eplan Project factory."""


class EplanProject(SupportsFileLocation, SupportsMetaData, metaclass=FactoryTypeMeta[Self, EplanProjectFactory]):
    """EPLAN project model.

    Attributes:
        file_location (str): The file location of the EPLAN project.
    """

    def __init__(
        self,
        file_location: str = None,
        meta_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            file_location=file_location,
            meta_data=meta_data,
        )
        self.project_name: str = None
        self.devices: Dict[str, Any] = None
        self.connections: List[Dict] = None
        self.properties: Dict[str, str] = None
        self.sheet_details: List[Dict] = None
        self.bom_details: List[Dict] = None

    @property
    def indexed_attribute(self) -> dict:
        """Return the key from eplan root that looks like the most promising for project data.
        """
        return self.meta_data.get(
            EPLAN_PROJECT_ROOT,
            {}
        )

    @property
    def main_interest_attributes(self) -> dict:
        """Return the key from eplan root that looks like the most promising for project data.
        """
        return self[EPLAN_PROJECT_DATA_KEY]

    @property
    def project_bom_list(self) -> list[dict]:
        """Get the project BOM dictionary."""
        return self.main_interest_attributes.get(
            EPLAN_PROJECT_BOM_KEY,
            [{}]
        )

    @property
    def project_design_source(self) -> Optional[str]:
        """Get the project design source if available."""
        return self.project_property_dict.get(
            EPLAN_PROJECT_DESIGN_SOURCE_KEY,
            EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )

    @property
    def project_design_source_address(self) -> Optional[str]:
        """Get the project design source address if available."""
        addr_line1 = self.project_property_dict.get(
            EPLAN_PROJECT_ADDRESS_LINE1_KEY,
            EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )
        addr_line2 = self.project_property_dict.get(
            EPLAN_PROJECT_ADDRESS_LINE2_KEY,
            EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )

        if addr_line1 == EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT and addr_line2 == EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT:
            return EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT

        return f"{addr_line1}, {addr_line2}"

    @property
    def project_device_list(self) -> list[dict]:
        """Get the project devices dictionary list."""
        return self.main_interest_attributes.get(
            EPLAN_PROJECT_DEVICE_KEY,
            [{}]
        )

    @property
    def project_factory_name(self) -> Optional[str]:
        """Get the project factory name if available."""
        return self.project_property_dict.get(
            EPLAN_PROJECT_FACTORY_NAME_KEY,
            EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )

    @property
    def project_factory_type(self) -> Optional[str]:
        """Get the project factory type if available."""
        return self.project_property_dict.get(
            EPLAN_PROJECT_FACTORY_TYPE_KEY,
            EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )

    @property
    def project_job_number(self) -> Optional[str]:
        """Get the project job number if available."""
        return self.project_property_dict.get(
            EPLAN_PROJECT_NUMBER_KEY,
            EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )

    @property
    def project_property_dict(self) -> dict:
        """Get the project properties dictionary."""
        return self.main_interest_attributes.get(
            EPLAN_PROJECT_PROPERTY_KEY,
            {}
        )

    @property
    def project_sheet_list(self) -> list[dict]:
        """Get the project sheets dictionary."""
        return self.main_interest_attributes.get(
            EPLAN_PROJECT_SHEET_KEY,
            [{}]
        )

    @property
    def pxf_root(self) -> dict:
        """Get the root metadata dictionary for EPLAN PXF files."""
        return self.meta_data.get(
            EPLAN_PROJECT_ROOT,
            {}
        )

    @property
    def template_source(self) -> Optional[str]:
        """Get the template source file if available."""
        return self.project_property_dict.get(
            EPLAN_PROJECT_TEMPLATE_KEY,
            EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )

    def _gather_project_bom_details(
        self,
        skip_zero_counts: bool = True,
    ) -> List[dict]:
        """Gather all BOM details from the project."""
        bom_dicts: list[dict] = []
        bom_items = self.project_bom_list
        if isinstance(bom_items, dict):
            bom_items = [bom_items]

        for item in bom_items:
            item_bom_meta: dict = item.get('P11', {})
            if not item_bom_meta:
                continue  # Don't process items without metadata

            part_number = item_bom_meta.get('@P22003', '')
            if part_number == '':
                continue  # Don't process items without part number

            description = item_bom_meta.get('@P22004', '').split('@')[-1].strip()
            quantity = item_bom_meta.get('@P2200', 0)
            manufacturer = item_bom_meta.get('@P22007', '')
            bom_dicts.append(
                {
                    'part_number': part_number,
                    'description': description,
                    'quantity': quantity,
                    'manufacturer': manufacturer,
                    'data': item
                }
            )

        return bom_dicts

    def _gather_project_sheet_details(self) -> List[dict]:
        """Gather all sheet details from the project."""
        sheet_dicts: list[dict] = []
        sheets = self.project_sheet_list
        if isinstance(sheets, dict):
            sheets = [sheets]

        for sheet in sheets:
            sheet_props = sheet.get('P11', {})
            sheet_number_dict = sheet.get('P49', {})

            sheet_name = sheet_props.get('@P11011', '').split('@')[-1].strip()
            sheet_number_major = sheet_number_dict.get('@P11012', '')
            sheet_number_minor = sheet_number_dict.get('@P11013', '')
            if sheet_number_major and sheet_number_minor:
                sheet_number = f"{sheet_number_major}.{sheet_number_minor}"
            else:
                sheet_number = sheet_number_major or sheet_number_minor or 'N/A'

            sheet_dicts.append(
                {
                    'name': sheet_name,
                    'number': sheet_number,
                    'data': sheet,
                }
            )

        return sheet_dicts

    def _gather_project_ip_addresses(self) -> List[str]:
        """Gather all IP addresses from the project."""
        ip_addresses: List[str] = []
        for device in self.project_device_list:
            ip_address = device.get('P11', {}).get('@P1009', '')
            if ip_address and ip_address not in ip_addresses:
                ip_addresses.append(ip_address)
        return ip_addresses

    @classmethod
    def get_factory(cls):
        return EplanProjectFactory

    def parse(self) -> None:
        """Parse the EPLAN project file.

        This is a placeholder method. Actual implementation will depend on
        the EPLAN file format and parsing logic.
        """
        if not self.file_location:
            raise ValueError("File location is not set for the EPLAN project.")
        if not self.meta_data:
            raise ValueError("Meta data is not set for the EPLAN project.")

        self._gather_project_sheet_details()

        raise NotImplementedError("EPLAN project parse.")

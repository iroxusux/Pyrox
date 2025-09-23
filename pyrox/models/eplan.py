"""EPLAN design models.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Self, TYPE_CHECKING
from pyrox.models.abc.meta import NamedPyroxObject, PyroxObject, SupportsMetaData
from pyrox.models.abc.factory import FactoryTypeMeta, MetaFactory
from pyrox.models.abc.list import HashList
from pyrox.models.abc.save import SupportsFileLocation
from pyrox.services.dict import rename_keys
from pyrox.services.xml import dict_from_xml_file

if TYPE_CHECKING:
    from .plc import Controller, Module

# -------------- EPLAN Constants -----------------
EPLAN_PROJECT_ROOT = 'EplanPxfRoot'
EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT = 'Unknown'

# -------------- EPLAN Property Keys -----------------
EPLAN_PROPERTY_KEY = 'P11'
EPLAN_PROJECT_INDEX_NUMBER_KEY = 'P49'
EPLAN_SHEET_OBJECTS_KEY = 'O3'
EPLAN_PROJECT_SHEET_KEY = 'O4'
EPLAN_PROJECT_GROUP_KEY = 'O6'
EPLAN_PROJECT_DATA_KEY = 'O14'
EPLAN_SHEET_TAGS_KEY = 'O17'
EPLAN_SHEET_TEXT_OBJECTS_KEY = 'O30'
EPLAN_SHEET_META_DATA_KEY = 'O52'
EPLAN_GRAPHIC_DATA_KEY = 'O76'
EPLAN_PROJECT_BOM_KEY = 'O117'
EPLAN_USER_SUPPL_DATA_KEY = 'O211'
EPLAN_USER_SUPPL_FIELD_KEY = 'S212x5'
EPLAN_FORM_PROPERTY_KEY = 'S75x5'

# -------------- EPLAN Meta Keys -----------------
EPLAN_PARENT_FORM_KEY = '@A22'  # Maybe?
EPLAN_LAST_EDIT_TIME_EPOCH_KEY = '@A48'
EPLAN_GROUP_NAME_KEY = '@A82'
EPLAN_PROJECT_TITLE_KEY = '@A133'
EPLAN_OBJECT_DETAIL_KEY = '@A511'
EPLAN_BOM_PART_NO_KEY = '@A1101'
EPLAN_PAGE_NUMBER_MAJOR_KEY = '@A1101'
EPLAN_PAGE_NUMBER_MINOR_KEY = '@A1102'
EPLAN_FORM_LAST_EDITED_BY_KEY = '@A1408'
EPLAN_FORM_DESCRIPTION_KEY = '@A1410'
EPLAN_FORM_TEMPLATE_NAME_KEY = '@A1413'
EPLAN_FORM_NAME_KEY = '@A2196'
EPLAN_GROUP_META_KEY = '@P1002'
EPLAN_DEVICE_IP_ADDRESS_KEY = '@P1009'
EPLAN_MAJOR_DEVICE_KEY = '@P1100'  # where symbol is "="XXXyyy
EPLAN_MINOR_DEVICE_KEY = '@P1200'  # where symbol is =XXXyyy"+"abc
EPLAN_PROJECT_STRUCT_FUNCTIONAL_ASSIGNMENT_KEY = '@P10001'
EPLAN_PROJECT_STRUCT_HIGHER_LEVEL_FUNCTION_KEY = '@P10002'
EPLAN_PROJECT_STRUCT_INSTALLATION_SITE_KEY = '@P10003'
EPLAN_PROJECT_STRUCT_MOUNTING_LOCATION_KEY = '@P10004'
EPLAN_PROJECT_NAME_FULL_KEY = '@P10009'
EPLAN_PROJECT_PATH_KEY = '@P10010'
EPLAN_PROJECT_DESCRIPTION_KEY = '@P10011'
EPLAN_USE_PAGE_NAME_IN_DT_KEY = '@P10012'
EPLAN_JOB_NUMBER_KEY = '@P10013'
EPLAN_COMPANY_NAME_KEY = '@P10015'
EPLAN_COMPANY_ADDRESS_LINE1_KEY = '@P10016'
EPLAN_COMPANY_ADDRESS_LINE2_KEY = '@P10017'
EPLAN_CREATOR_KEY = '@P10020'
EPLAN_CREATION_DATE_EPOCH_KEY = '@P10021'
EPLAN_LAST_EDITOR_KEY = '@P10022'
EPLAN_MODIFICATION_DATE_EPOCH_KEY = '@P10023'
EPLAN_DATE_KEY = '@P10027'
EPLAN_PLACE_OF_INSTALL_KEY = '@P10032'
EPLAN_LOCATION_KEY = '@P10035'
EPLAN_LAST_VERSION_USED_KEY = '@P10043'
EPLAN_PROJECT_PATH_FULL_KEY = '@P10045'
EPLAN_CREATION_TIME_KEY = '@P10046'
EPLAN_PROJECT_TEMPLATE_KEY = '@P10069'
EPLAN_APPROVED_BY_KEY = '@P10160'
EPLAN_CUSTOMER_CODE_KEY = '@P10180'
EPLAN_UNIQUE_PROJECT_ID_KEY = '@P10184'
EPLAN_LICENSE_DONGLE_ID_KEY = '@P10185'
EPLAN_NAME_KEY = '@P11011'
EPLAN_INDEX_MAJOR_KEY = '@P11012'
EPLAN_INDEX_MINOR_KEY = '@P11013'
EPLAN_TEMPLATE_FORM_NAME_KEY = '@P11015'
EPLAN_TITLE_BLOCK_KEY = '@P11016'
EPLAN_CREATED_BY_KEY = '@P11020'
EPLAN_CREATED_ON_EPOCH_KEY = '@P11021'
EPLAN_EDITED_BY_KEY = '@P11022'
EPLAN_EDITED_ON_EPOCH_KEY = '@P11023'
EPLAN_SUPPLY_FIELD_SHEET_NO_KEY = '@P11033'
EPLAN_PROJECT_NAME_KEY = '@P11056'
EPLAN_SPECIAL_REMARKS_KEY = '@P11059'
EPLAN_REFERENCED_OBJECTS_KEY = '@P11063'
EPLAN_SOURCE_KEY = '@P11066'
EPLAN_SOURCE_PROJECT_KEY = '@P11067'
EPLAN_BOM_QUANTITY_KEY = '@P2200'
EPLAN_BOM_ITEM_DUP_KEY = '@P22001'
EPLAN_BOM_SPEC_NO_KEY = '@P22002'
EPLAN_BOM_PART_NO_KEY = '@P22003'
EPLAN_BOM_PART_DESC_KEY = '@P22004'
EPLAN_BOM_CABLE_CONDUIT_COUNT_KEY = '@P22005'
EPLAN_BOM_CABLE_SIZE_LENGTH_KEY = '@P22006'
EPLAN_BOM_MANUFACTURER_KEY = '@P22007'
EPLAN_BOM_PART_ADDED_BY_FULL_KEY = '@P22901'
EPLAN_BOM_PART_EDITED_BY_FULL_KEY = '@P22902'
EPLAN_BOM_ADDED_BY_KEY = '@P22980'
EPLAN_BOM_ADDED_ON_EPOCH_KEY = '@P22981'
EPLAN_BOM_EDITED_BY_KEY = '@P22982'
EPLAN_BOM_EDITED_ON_EPOCH_KEY = '@P22983'

# -------------- EPLAN Key Map -----------------
# Mapping of EPLAN property keys to more user-friendly names
EPLAN_DICT_MAP = {
    EPLAN_APPROVED_BY_KEY: 'Approved By',
    EPLAN_BOM_ADDED_BY_KEY: 'BOM Added By',
    EPLAN_BOM_ADDED_ON_EPOCH_KEY: 'BOM Added On (Epoch)',
    EPLAN_BOM_CABLE_CONDUIT_COUNT_KEY: 'Cable/Conduit Count',
    EPLAN_BOM_CABLE_SIZE_LENGTH_KEY: 'Cable Size/Length',
    EPLAN_BOM_EDITED_BY_KEY: 'BOM Edited By',
    EPLAN_BOM_EDITED_ON_EPOCH_KEY: 'BOM Edited On (Epoch)',
    EPLAN_BOM_ITEM_DUP_KEY: 'BOM Item Dup',
    EPLAN_BOM_MANUFACTURER_KEY: 'Manufacturer',
    EPLAN_BOM_PART_NO_KEY: 'Part Number',
    EPLAN_BOM_PART_DESC_KEY: 'Part Description',
    EPLAN_BOM_QUANTITY_KEY: 'Quantity',
    EPLAN_BOM_SPEC_NO_KEY: 'BOM Spec No.',
    EPLAN_CREATED_BY_KEY: 'Created By',
    EPLAN_CREATED_ON_EPOCH_KEY: 'Created On (Epoch)',
    EPLAN_CREATION_DATE_EPOCH_KEY: 'Created On (Epoch)',
    EPLAN_CREATOR_KEY: 'Created By',
    EPLAN_COMPANY_ADDRESS_LINE1_KEY: 'Address Line 1',
    EPLAN_COMPANY_ADDRESS_LINE2_KEY: 'Address Line 2',
    EPLAN_CUSTOMER_CODE_KEY: 'Project Number',
    EPLAN_DEVICE_IP_ADDRESS_KEY: 'IP Address',
    EPLAN_EDITED_BY_KEY: 'Edit By',
    EPLAN_EDITED_ON_EPOCH_KEY: 'Edited On (Epoch)',
    EPLAN_FORM_DESCRIPTION_KEY: 'Description',
    EPLAN_FORM_LAST_EDITED_BY_KEY: 'Last Edited By',
    EPLAN_FORM_NAME_KEY: 'Form Name',
    EPLAN_FORM_PROPERTY_KEY: 'Form Properties',
    EPLAN_FORM_TEMPLATE_NAME_KEY: 'Form Template Name',
    EPLAN_GRAPHIC_DATA_KEY: 'Graphic Meta Data',
    EPLAN_GROUP_NAME_KEY: 'Group Name',
    EPLAN_GROUP_META_KEY: 'Group Meta Data',
    EPLAN_INDEX_MAJOR_KEY: 'Major Index',
    EPLAN_INDEX_MINOR_KEY: 'Minor Index',
    EPLAN_JOB_NUMBER_KEY: 'Job Number',
    EPLAN_LAST_EDIT_TIME_EPOCH_KEY: 'Last Edit Time (Epoch)',
    EPLAN_MAJOR_DEVICE_KEY: 'Device Major Relation',
    EPLAN_MINOR_DEVICE_KEY: 'Device Minor Relation',
    EPLAN_NAME_KEY: 'Name',
    EPLAN_OBJECT_DETAIL_KEY: 'Object Detail',
    EPLAN_PAGE_NUMBER_MAJOR_KEY: 'Page Number Major',
    EPLAN_PAGE_NUMBER_MINOR_KEY: 'Page Number Minor',
    EPLAN_PARENT_FORM_KEY: 'Parent Form',
    EPLAN_PROJECT_BOM_KEY: 'Project BOM',
    EPLAN_PROJECT_DATA_KEY: 'Project Data',
    EPLAN_COMPANY_NAME_KEY: 'Company Name',
    EPLAN_LOCATION_KEY: 'Location',
    EPLAN_PLACE_OF_INSTALL_KEY: 'Place Of Installation',
    EPLAN_PROJECT_DESCRIPTION_KEY: 'Project Description',
    EPLAN_PROJECT_GROUP_KEY: 'Project Groups',
    EPLAN_PROJECT_INDEX_NUMBER_KEY: 'Indexes',
    EPLAN_PROJECT_NAME_KEY: 'Project Name',
    EPLAN_PROJECT_NAME_FULL_KEY: 'Project Name Full',
    EPLAN_PROJECT_PATH_KEY: 'Project Path',
    EPLAN_PROJECT_PATH_FULL_KEY: 'Project Path Full',
    EPLAN_PROJECT_STRUCT_FUNCTIONAL_ASSIGNMENT_KEY: 'Functional Assignment',
    EPLAN_PROJECT_STRUCT_HIGHER_LEVEL_FUNCTION_KEY: 'Higher Level Function',
    EPLAN_PROJECT_STRUCT_INSTALLATION_SITE_KEY: 'Installation Site',
    EPLAN_PROJECT_STRUCT_MOUNTING_LOCATION_KEY: 'Mounting Location',
    EPLAN_PROJECT_SHEET_KEY: 'Sheets',
    EPLAN_PROJECT_TEMPLATE_KEY: 'Project Template',
    EPLAN_PROJECT_TITLE_KEY: 'Project Title',
    EPLAN_PROPERTY_KEY: 'Properties',
    EPLAN_SHEET_META_DATA_KEY: 'Sheet Meta Data',
    EPLAN_SHEET_OBJECTS_KEY: 'Sheet Objects',
    EPLAN_SHEET_TAGS_KEY: 'Sheet Tags',
    EPLAN_SHEET_TEXT_OBJECTS_KEY: 'Sheet Text Objects',
    EPLAN_SOURCE_KEY: 'Source',
    EPLAN_SOURCE_PROJECT_KEY: 'Report: Source Project',
    EPLAN_SPECIAL_REMARKS_KEY: 'Special Remarks',
    EPLAN_SUPPLY_FIELD_SHEET_NO_KEY: 'Supply Field Sheet No.',
    EPLAN_TEMPLATE_FORM_NAME_KEY: 'Template Form Name',
    EPLAN_TITLE_BLOCK_KEY: 'Title Block',
    EPLAN_UNIQUE_PROJECT_ID_KEY: 'Unique Project ID',
    EPLAN_USE_PAGE_NAME_IN_DT_KEY: 'Use Page Name In DT',
    EPLAN_USER_SUPPL_DATA_KEY: 'User Supplimental Data',
    EPLAN_USER_SUPPL_FIELD_KEY: 'User Supplimental Field',
}


class EplanProjectDevice(NamedPyroxObject):
    """EPLAN Project Device model.

    Attributes:
        name (str): The name of the device.
        data (dict): The raw data dictionary of the device.
        description (Optional[str]): An optional description of the device.
    """

    def __init__(
        self,
        name: str,
        data: dict,
        description: Optional[str] = None,
    ) -> None:
        NamedPyroxObject.__init__(self, name, description)
        self.data: dict = data


class EplanNetworkDevice(EplanProjectDevice):
    """EPLAN Network Device model.

    Attributes:
        name (str): The name of the network device.
        ip_address (str): The IP address of the network device.
        data (dict): The raw data dictionary of the network device.
    """

    def __init__(
        self,
        name: str,
        ip_address: str,
        data: dict,
        description: Optional[str] = None,
    ) -> None:
        super().__init__(name, data, description)
        self.ip_address = ip_address


class EplanProjectFactory(MetaFactory):
    """Eplan Project factory."""


class EplanProject(SupportsFileLocation, SupportsMetaData, metaclass=FactoryTypeMeta[Self, EplanProjectFactory]):
    """EPLAN project model.

    Attributes:
        file_location (str): The file location of the EPLAN project.
    """
    supporting_class = None
    supports_registering = False

    def __init__(
        self,
        file_location: str = None,
        meta_data: Optional[Dict[str, Any]] = None,
        controller: Optional[Any] = None,
    ) -> None:
        SupportsFileLocation.__init__(self, file_location)
        SupportsMetaData.__init__(self, meta_data)
        # re-assign file location to trigger meta_data load if provided
        self.file_location: str = file_location
        self.controller: Optional[Any] = controller
        self.devices: HashList[EplanProjectDevice] = HashList('name')

        self.project_name: str = []
        self.groups: Dict[str, Any] = []
        self.connections: List[Dict] = []
        self.properties: Dict[str, str] = []
        self.sheet_details: List[Dict] = []
        self.bom_details: List[Dict] = []

    def __init_subclass__(cls, **kwargs):
        cls.supports_registering = True
        return super().__init_subclass__(**kwargs)

    @SupportsFileLocation.file_location.setter
    def file_location(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError('file_location must be a string!')
        if not value.endswith('.epj'):
            raise ValueError('file_location must be an EPLAN .epj file!')
        self._file_location = value
        meta_data = dict_from_xml_file(value)
        rename_keys(meta_data, EPLAN_DICT_MAP)
        self.meta_data = meta_data

    @property
    def indexed_attribute(self) -> dict:
        """Return the key from eplan root that looks like the most promising for project data.
        """
        return self.meta_data.get(
            EPLAN_PROJECT_ROOT,
            {}
        )

    @property
    def project_data(self) -> dict:
        """Get the Eplan project data dictionary.
        """
        return self[EPLAN_DICT_MAP[EPLAN_PROJECT_DATA_KEY]]

    @property
    def project_bom(self) -> list[dict]:
        """Get the project BOM dictionary."""
        return self.project_data.get(
            EPLAN_DICT_MAP[EPLAN_PROJECT_BOM_KEY],
            [{}]
        )

    @property
    def design_source(self) -> Optional[str]:
        """Get the project design source if available."""
        return self.project_properties.get(
            EPLAN_DICT_MAP[EPLAN_COMPANY_NAME_KEY],
            EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )

    @property
    def design_source_address(self) -> Optional[str]:
        """Get the project design source address if available."""
        addr_line1 = self.project_properties.get(
            EPLAN_DICT_MAP[EPLAN_COMPANY_ADDRESS_LINE1_KEY],
            EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )
        addr_line2 = self.project_properties.get(
            EPLAN_DICT_MAP[EPLAN_COMPANY_ADDRESS_LINE2_KEY],
            EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )

        if addr_line1 == EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT and addr_line2 == EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT:
            return EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT

        return f"{addr_line1}, {addr_line2}"

    @property
    def groups(self) -> list[dict]:
        """Get the project devices dictionary list."""
        return self.project_data.get(
            EPLAN_DICT_MAP[EPLAN_PROJECT_GROUP_KEY],
            [{}]
        )

    @property
    def factory_name(self) -> Optional[str]:
        """Get the project factory name if available."""
        return self.project_properties.get(
            EPLAN_DICT_MAP[EPLAN_LOCATION_KEY],
            EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )

    @property
    def factory_type(self) -> Optional[str]:
        """Get the project factory type if available."""
        return self.project_properties.get(
            EPLAN_DICT_MAP[EPLAN_PLACE_OF_INSTALL_KEY],
            EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )

    @property
    def job_number(self) -> Optional[str]:
        """Get the project job number if available."""
        return self.project_properties.get(
            EPLAN_DICT_MAP[EPLAN_CUSTOMER_CODE_KEY],
            EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )

    @property
    def project_properties(self) -> dict:
        """Get the project properties dictionary."""
        return self.project_data.get(
            EPLAN_DICT_MAP[EPLAN_PROPERTY_KEY],
            {}
        )

    @property
    def sheets(self) -> list[dict]:
        """Get the project sheets dictionary."""
        return self.project_data.get(
            EPLAN_DICT_MAP[EPLAN_PROJECT_SHEET_KEY],
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
        return self.project_properties.get(
            EPLAN_DICT_MAP[EPLAN_PROJECT_TEMPLATE_KEY],
            EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )

    @staticmethod
    def strip_eplan_naming_conventions(name: str) -> str:
        """Strip EPLAN naming conventions from a given name.

        Args:
            name (str): The name to strip.
        Returns:
            str: The stripped name.
        """
        stripped_name = name.split('@')[-1].strip()
        if stripped_name.endswith(';'):
            stripped_name = stripped_name[:-1].strip()
        return stripped_name

    def _gather_project_bom_details(
        self,
        skip_zero_counts: bool = True,
    ) -> List[dict]:
        """Gather all BOM details from the project."""
        self.bom_details.clear()
        bom_items = self.project_bom

        if isinstance(bom_items, dict):
            bom_items = [bom_items]

        for item in bom_items:
            self.bom_details.append(
                self._process_bom_item(item)
            )

    def _gather_project_device_io_details(self) -> None:
        """Gather all device IO details from the project."""
        raise NotImplementedError("Subclasses should override this method to gather device IO details.")

    def _gather_project_ethernet_devices(self) -> None:
        """Gather all ethernet devices from the project."""
        raise NotImplementedError("Subclasses should override this method to gather ethernet devices.")

    def _gather_project_group_details(self) -> None:
        """Gather all groups from the project."""
        self.groups.clear()
        groups = self.groups

        if isinstance(groups, dict):
            groups = [groups]

        for group in groups:
            self.groups.append(
                self._process_group_data(group)
            )

    def _gather_project_sheet_details(self) -> None:
        """Gather all sheet details from the project."""
        self.sheet_details.clear()
        sheets = self.sheets

        if isinstance(sheets, dict):
            sheets = [sheets]

        for sheet in sheets:
            self.sheet_details.append(
                self._process_sheet(sheet)
            )

    def _process_bom_item(
        self,
        item: dict,
    ) -> dict:
        """Process a single BOM item from the project.

        Args:
            item (dict): The BOM item dictionary to process.

        Returns:
            dict: Processed BOM item information.
        """
        item_bom_meta: dict = item.get(EPLAN_PROPERTY_KEY, {})
        if not item_bom_meta:
            return

        part_number = item_bom_meta.get(EPLAN_BOM_PART_NO_KEY, EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)
        if part_number == EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT:
            return

        description = item_bom_meta.get(EPLAN_BOM_PART_DESC_KEY, EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT).split('@')[-1].strip()
        quantity = item_bom_meta.get(EPLAN_BOM_QUANTITY_KEY, 0)
        manufacturer = item_bom_meta.get(EPLAN_BOM_MANUFACTURER_KEY, EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)

        return {
            'part_number': part_number,
            'description': description,
            'quantity': quantity,
            'manufacturer': manufacturer,
            'data': item
        }

    def _process_group_data(
        self,
        group: dict,
    ) -> dict:
        """Process a single group from the project.

        Args:
            device (dict): The group dictionary to process.

        Returns:
            dict: Processed group information.
        """
        name = group.get(EPLAN_GROUP_NAME_KEY, EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)
        if name == EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT:
            return  # Don't process devices without a name

        group_props = group.get(EPLAN_PROPERTY_KEY, {})

        group_descriptor_meta_string = group_props.get(EPLAN_GROUP_META_KEY, EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)

        return {
            'name': name,
            'data': group,
            'descriptor': group_descriptor_meta_string.split('@')[-1].strip(),
        }

    def _process_sheet(
        self,
        sheet: dict,
    ) -> dict:
        """Process a single sheet from the project.

        Args:
            sheet (dict): The sheet dictionary to process.

        Returns:
            dict: Processed sheet information.
        """
        sheet_props = sheet.get(EPLAN_PROPERTY_KEY, {})
        sheet_number_dict = sheet.get(EPLAN_PROJECT_INDEX_NUMBER_KEY, {})

        sheet_name: str = self.strip_eplan_naming_conventions(
            sheet_props.get(EPLAN_NAME_KEY, EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)
        )

        sheet_number_major = sheet_number_dict.get(EPLAN_INDEX_MAJOR_KEY, EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)
        sheet_number_minor = sheet_number_dict.get(EPLAN_INDEX_MINOR_KEY, EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)
        if sheet_number_major and sheet_number_minor:
            sheet_number = f"{sheet_number_major}.{sheet_number_minor}"
        else:
            sheet_number = sheet_number_major or sheet_number_minor or EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT

        return {
            'name': sheet_name,
            'number': sheet_number,
            'data': sheet,
        }

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
        self._gather_project_bom_details()
        self._gather_project_group_details()
        self._gather_project_ethernet_devices()
        self._gather_project_device_io_details()

        self.logger.info('Done!')


class EplanControllerValidatorFactory(MetaFactory):
    """Eplan Controller Validator factory."""


class EplanControllerValidator(PyroxObject, metaclass=FactoryTypeMeta[Self, EplanControllerValidatorFactory]):
    """EPLAN controller validator model.

    Attributes:
        controller (Any): The controller to validate.
    """
    supporting_class = None
    supports_registering = False

    def __init__(
        self,
        controller: Controller = None,
        project: EplanProject = None,
    ) -> None:
        self.controller: Optional[Controller] = controller
        self.project: Optional[EplanProject] = project

    def __init_subclass__(cls, **kwargs):
        cls.supports_registering = True
        return super().__init_subclass__(**kwargs)

    @classmethod
    def get_factory(cls):
        return EplanControllerValidatorFactory

    def _validate_controller_properties(self) -> None:
        """Internal controller properties validation method."""
        raise NotImplementedError("Subclasses should implement this method.")

    def _validate_modules(self) -> None:
        """Internal module validation method."""
        raise NotImplementedError("Subclasses should implement this method.")

    def find_almost_matching_device_in_controller(
        self,
        device_name: str
    ) -> Optional[Any]:
        """Find an almost matching device in the controller by name.

        Args:
            device_name (str): The name of the device to find.
        Returns:
            Optional[Any]: The almost matching device or None if not found.
        """
        if not self.controller:
            raise ValueError("Controller is not set for validation.")

        almost_matching_device = next((m for m in self.controller.modules if m.name.lower() in device_name.lower()), None)
        return almost_matching_device

    def find_matching_device_in_controller(
        self,
        device_name: str
    ) -> Optional[Any]:
        """Find a matching device in the controller by name.

        Args:
            device_name (str): The name of the device to find.
        Returns:
            Optional[Any]: The matching device or None if not found.
        """
        if not self.controller:
            raise ValueError("Controller is not set for validation.")

        matching_device = next((m for m in self.controller.modules if m.name == device_name), None)
        return matching_device

    def find_almost_matching_module_in_project(
        self,
        module: Module,
    ) -> Optional[EplanProjectDevice]:
        """Find an almost matching module in the EPLAN project by name.

        Args:
            module_name (str): The name of the module to find.
        Returns:
            Optional[EplanProjectDevice]: The almost matching module or None if not found.
        """
        if not self.project:
            raise ValueError("EPLAN project is not set for validation.")

        almost_matching_module = self.project.devices.find_first(lambda d: module.name.lower() in d.name.lower())
        return almost_matching_module

    def find_matching_module_in_project(
        self,
        module: Module,
    ) -> Optional[EplanProjectDevice]:
        """Find a matching module in the EPLAN project by name.

        Args:
            module_name (str): The name of the module to find.
        Returns:
            Optional[EplanProjectDevice]: The matching module or None if not found.
        """
        if not self.project:
            raise ValueError("EPLAN project is not set for validation.")

        matching_module = self.project.devices.find_first(lambda d: d.name == module.name)
        return matching_module

    def validate(self) -> None:
        """Validate the EPLAN controller.

        This is a placeholder method. Actual implementation will depend on
        the validation logic.
        """
        if not self.controller:
            raise ValueError("Controller is not set for validation.")

        if not self.project:
            raise ValueError("EPLAN project is not set for validation.")

        self.logger.info('Validating controller...')
        self._validate_controller_properties()
        self._validate_modules()
        self.logger.info('Validation complete!')

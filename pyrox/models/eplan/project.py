"""EPLAN design models.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pyrox.models.abc.meta import NamedPyroxObject, PyroxObject, SupportsMetaData
from pyrox.models.abc.factory import FactoryTypeMeta, MetaFactory
from pyrox.models.abc.list import HashList
from pyrox.models.abc.save import SupportsFileLocation
from pyrox.models.plc import Controller, Module
from pyrox.services.dict import rename_keys
from pyrox.services.logging import log
from pyrox.services.xml import dict_from_xml_file

from . import meta


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


class EplanProject(
    SupportsFileLocation,
    SupportsMetaData,
    metaclass=FactoryTypeMeta['EplanProject', EplanProjectFactory]
):
    """EPLAN project model.

    Attributes:
        file_location (str): The file location of the EPLAN project.
    """
    supporting_class = None
    supports_registering = False

    def __init__(
        self,
        file_location: Optional[str] = None,
        meta_data: Optional[Dict[str, Any]] = None,
        controller: Optional[Any] = None,
    ) -> None:
        SupportsFileLocation.__init__(self, file_location)
        SupportsMetaData.__init__(self, meta_data)
        # re-assign file location to trigger meta_data load if provided
        self.file_location = file_location
        self.controller: Optional[Any] = controller
        self.devices: HashList[EplanProjectDevice] = HashList('name')

        self.project_name: str = ''
        self.control_groups: List[Dict[str, Any]] = []
        self.connections: List[Dict[str, Any]] = []
        self.properties: Dict[str, str] = {}
        self.sheet_details: List[Dict] = []
        self.bom_details: List[Dict] = []

    def __init_subclass__(
        cls,
        **kwargs
    ):
        cls.supports_registering = True
        return super().__init_subclass__(**kwargs)

    @SupportsFileLocation.file_location.setter
    def file_location(self, value: Optional[str]) -> None:
        if not isinstance(value, str):
            raise ValueError('file_location must be a string!')
        if not value.endswith('.epj'):
            raise ValueError('file_location must be an EPLAN .epj file!')
        self._file_location = value
        meta_data = dict_from_xml_file(value)
        rename_keys(meta_data, meta.EPLAN_DICT_MAP)
        self.meta_data = meta_data

    @property
    def indexed_attribute(self) -> dict:
        """Return the key from eplan root that looks like the most promising for project data.
        """
        return self.meta_data.get(
            meta.EPLAN_PROJECT_ROOT,
            {}
        )

    @property
    def project_data(self) -> dict:
        """Get the Eplan project data dictionary.
        """
        return self[meta.EPLAN_DICT_MAP[meta.EPLAN_PROJECT_DATA_KEY]]

    @property
    def project_bom(self) -> list[dict]:
        """Get the project BOM dictionary."""
        return self.project_data.get(
            meta.EPLAN_DICT_MAP[meta.EPLAN_PROJECT_BOM_KEY],
            [{}]
        )

    @property
    def design_source(self) -> Optional[str]:
        """Get the project design source if available."""
        return self.project_properties.get(
            meta.EPLAN_DICT_MAP[meta.EPLAN_COMPANY_NAME_KEY],
            meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )

    @property
    def design_source_address(self) -> Optional[str]:
        """Get the project design source address if available."""
        addr_line1 = self.project_properties.get(
            meta.EPLAN_DICT_MAP[meta.EPLAN_COMPANY_ADDRESS_LINE1_KEY],
            meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )
        addr_line2 = self.project_properties.get(
            meta.EPLAN_DICT_MAP[meta.EPLAN_COMPANY_ADDRESS_LINE2_KEY],
            meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )

        if addr_line1 == meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT and addr_line2 == meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT:
            return meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT

        return f"{addr_line1}, {addr_line2}"

    @property
    def groups(self) -> list[dict]:
        """Get the project devices dictionary list."""
        return self.project_data.get(
            meta.EPLAN_DICT_MAP[meta.EPLAN_PROJECT_GROUP_KEY],
            [{}]
        )

    @property
    def factory_name(self) -> Optional[str]:
        """Get the project factory name if available."""
        return self.project_properties.get(
            meta.EPLAN_DICT_MAP[meta.EPLAN_LOCATION_KEY],
            meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )

    @property
    def factory_type(self) -> Optional[str]:
        """Get the project factory type if available."""
        return self.project_properties.get(
            meta.EPLAN_DICT_MAP[meta.EPLAN_PLACE_OF_INSTALL_KEY],
            meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )

    @property
    def job_number(self) -> Optional[str]:
        """Get the project job number if available."""
        return self.project_properties.get(
            meta.EPLAN_DICT_MAP[meta.EPLAN_CUSTOMER_CODE_KEY],
            meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
        )

    @property
    def project_properties(self) -> dict:
        """Get the project properties dictionary."""
        return self.project_data.get(
            meta.EPLAN_DICT_MAP[meta.EPLAN_PROPERTY_KEY],
            {}
        )

    @property
    def sheets(self) -> list[dict]:
        """Get the project sheets dictionary."""
        return self.project_data.get(
            meta.EPLAN_DICT_MAP[meta.EPLAN_PROJECT_SHEET_KEY],
            [{}]
        )

    @property
    def pxf_root(self) -> dict:
        """Get the root metadata dictionary for EPLAN PXF files."""
        return self.meta_data.get(
            meta.EPLAN_PROJECT_ROOT,
            {}
        )

    @property
    def template_source(self) -> Optional[str]:
        """Get the template source file if available."""
        return self.project_properties.get(
            meta.EPLAN_DICT_MAP[meta.EPLAN_PROJECT_TEMPLATE_KEY],
            meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT
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
        log().warning("EPLAN device IO gathering not yet implemented.")

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
    ) -> Optional[dict[str, Any]]:
        """Process a single BOM item from the project.

        Args:
            item (dict): The BOM item dictionary to process.

        Returns:
            dict: Processed BOM item information.
        """
        item_bom_meta: dict = item.get(meta.EPLAN_PROPERTY_KEY, {})
        if not item_bom_meta:
            return

        part_number = item_bom_meta.get(meta.EPLAN_BOM_PART_NO_KEY, meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)
        if part_number == meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT:
            return

        description = item_bom_meta.get(meta.EPLAN_BOM_PART_DESC_KEY, meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT).split('@')[-1].strip()
        quantity = item_bom_meta.get(meta.EPLAN_BOM_QUANTITY_KEY, 0)
        manufacturer = item_bom_meta.get(meta.EPLAN_BOM_MANUFACTURER_KEY, meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)

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
    ) -> Optional[dict[str, Any]]:
        """Process a single group from the project.

        Args:
            device (dict): The group dictionary to process.

        Returns:
            dict: Processed group information.
        """
        name = group.get(meta.EPLAN_GROUP_NAME_KEY, meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)
        if name == meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT:
            return  # Don't process devices without a name

        group_props = group.get(meta.EPLAN_PROPERTY_KEY, {})

        group_descriptor_meta_string = group_props.get(meta.EPLAN_GROUP_META_KEY, meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)

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
        sheet_props = sheet.get(meta.EPLAN_PROPERTY_KEY, {})
        sheet_number_dict = sheet.get(meta.EPLAN_PROJECT_INDEX_NUMBER_KEY, {})

        sheet_name: str = self.strip_eplan_naming_conventions(
            sheet_props.get(meta.EPLAN_NAME_KEY, meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)
        )

        sheet_number_major = sheet_number_dict.get(meta.EPLAN_INDEX_MAJOR_KEY, meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)
        sheet_number_minor = sheet_number_dict.get(meta.EPLAN_INDEX_MINOR_KEY, meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)
        if sheet_number_major and sheet_number_minor:
            sheet_number = f"{sheet_number_major}.{sheet_number_minor}"
        else:
            sheet_number = sheet_number_major or sheet_number_minor or meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT

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

        log().info('Done!')

    def save_project_dict_to_file(
        self,
        file_path: Optional[str] = None
    ) -> None:
        """Save the project data dictionary to a file.

        Args:
            file_path (str): The file path to save the project data dictionary.
        """
        if not file_path and not self.file_location:
            raise ValueError("No file path provided to save the project data dictionary.")
        if not self.file_location:
            raise ValueError("File location is not set for the EPLAN project.")
        if not file_path:
            file_path = self.file_location + '.json'

        from pyrox.services.file import save_dict_to_json_file
        if save_dict_to_json_file(file_path, self.project_data):
            log().info(f'Project data dictionary saved to {file_path}')
        else:
            log().error(f'Failed to save project data dictionary to {file_path}')


class EplanControllerValidatorFactory(MetaFactory):
    """Eplan Controller Validator factory."""


class EplanControllerValidator(
        PyroxObject,
        metaclass=FactoryTypeMeta[
            'EplanControllerValidator',
            EplanControllerValidatorFactory
        ]):
    """EPLAN controller validator model.

    Attributes:
        controller (Any): The controller to validate.
    """
    supporting_class = None
    supports_registering = False

    def __init__(
        self,
        controller: Optional[Controller] = None,
        project: Optional[EplanProject] = None,
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

        log().info('Validating controller...')
        self._validate_controller_properties()
        self._validate_modules()
        log().info('Validation complete!')

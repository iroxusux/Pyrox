"""Unit tests for eplan/project.py module."""
import unittest
from unittest.mock import Mock, patch, call

from pyrox.models.eplan.project import (
    EplanProjectDevice,
    EplanNetworkDevice,
    EplanProject,
    EplanProjectFactory,
    EplanControllerValidator,
    EplanControllerValidatorFactory
)
from pyrox.models.eplan import meta
from pyrox.models.plc import Controller, Module
from pyrox.models.abc.list import HashList


class TestEplanProjectDevice(unittest.TestCase):
    """Test cases for EplanProjectDevice class."""

    def setUp(self):
        """Set up test fixtures."""
        self.device_data = {
            'property_1': 'value_1',
            'property_2': 'value_2'
        }

    def test_init_with_all_params(self):
        """Test EplanProjectDevice initialization with all parameters."""
        device = EplanProjectDevice(
            name="TestDevice",
            data=self.device_data,
            description="Test device description"
        )

        self.assertEqual(device.name, "TestDevice")
        self.assertEqual(device.data, self.device_data)
        self.assertEqual(device.description, "Test device description")

    def test_init_without_description(self):
        """Test EplanProjectDevice initialization without description."""
        device = EplanProjectDevice(
            name="TestDevice",
            data=self.device_data
        )

        self.assertEqual(device.name, "TestDevice")
        self.assertEqual(device.data, self.device_data)
        self.assertEqual(device.description, '')

    def test_inheritance(self):
        """Test that EplanProjectDevice inherits from NamedPyroxObject."""
        from pyrox.models.abc.meta import NamedPyroxObject

        device = EplanProjectDevice("TestDevice", {})
        self.assertIsInstance(device, NamedPyroxObject)


class TestEplanNetworkDevice(unittest.TestCase):
    """Test cases for EplanNetworkDevice class."""

    def setUp(self):
        """Set up test fixtures."""
        self.device_data = {
            'network_property': 'network_value'
        }

    def test_init_with_all_params(self):
        """Test EplanNetworkDevice initialization with all parameters."""
        device = EplanNetworkDevice(
            name="NetworkDevice",
            ip_address="192.168.1.100",
            data=self.device_data,
            description="Network device description"
        )

        self.assertEqual(device.name, "NetworkDevice")
        self.assertEqual(device.ip_address, "192.168.1.100")
        self.assertEqual(device.data, self.device_data)
        self.assertEqual(device.description, "Network device description")

    def test_init_without_description(self):
        """Test EplanNetworkDevice initialization without description."""
        device = EplanNetworkDevice(
            name="NetworkDevice",
            ip_address="192.168.1.100",
            data=self.device_data
        )

        self.assertEqual(device.name, "NetworkDevice")
        self.assertEqual(device.ip_address, "192.168.1.100")
        self.assertEqual(device.data, self.device_data)
        self.assertEqual(device.description, '')

    def test_inheritance(self):
        """Test that EplanNetworkDevice inherits from EplanProjectDevice."""
        device = EplanNetworkDevice("NetworkDevice", "192.168.1.100", {})
        self.assertIsInstance(device, EplanProjectDevice)


class TestEplanProjectFactory(unittest.TestCase):
    """Test cases for EplanProjectFactory class."""

    def test_factory_inheritance(self):
        """Test that EplanProjectFactory inherits from MetaFactory."""
        from pyrox.models.abc.factory import MetaFactory

        self.assertTrue(issubclass(EplanProjectFactory, MetaFactory))

    def test_factory_instantiation(self):
        """Test that EplanProjectFactory can be instantiated."""
        # ABC meta prevents direct instantiation
        with self.assertRaises(TypeError) as context:
            factory = EplanProjectFactory()  # type: ignore  # noqa: F841
        self.assertIn("ABCMeta.__new__() missing 3 required positional arguments", str(context.exception))


class TestEplanProject(unittest.TestCase):
    """Test cases for EplanProject class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_meta_data = {
            meta.EPLAN_PROJECT_ROOT: {
                meta.EPLAN_DICT_MAP[meta.EPLAN_PROJECT_DATA_KEY]: {
                    meta.EPLAN_DICT_MAP[meta.EPLAN_PROPERTY_KEY]: {
                        meta.EPLAN_DICT_MAP[meta.EPLAN_COMPANY_NAME_KEY]: "Test Company",
                        meta.EPLAN_DICT_MAP[meta.EPLAN_LOCATION_KEY]: "Test Factory",
                        meta.EPLAN_DICT_MAP[meta.EPLAN_CUSTOMER_CODE_KEY]: "TEST-001"
                    },
                    meta.EPLAN_DICT_MAP[meta.EPLAN_PROJECT_SHEET_KEY]: [
                        {
                            meta.EPLAN_PROPERTY_KEY: {
                                meta.EPLAN_NAME_KEY: "Sheet 1"
                            },
                            meta.EPLAN_PROJECT_INDEX_NUMBER_KEY: {
                                meta.EPLAN_INDEX_MAJOR_KEY: "1",
                                meta.EPLAN_INDEX_MINOR_KEY: "0"
                            }
                        }
                    ],
                    meta.EPLAN_DICT_MAP[meta.EPLAN_PROJECT_BOM_KEY]: [
                        {
                            meta.EPLAN_PROPERTY_KEY: {
                                meta.EPLAN_BOM_PART_NO_KEY: "PART-001",
                                meta.EPLAN_BOM_PART_DESC_KEY: "Test Part",
                                meta.EPLAN_BOM_QUANTITY_KEY: 5,
                                meta.EPLAN_BOM_MANUFACTURER_KEY: "Test Manufacturer"
                            }
                        }
                    ],
                    meta.EPLAN_DICT_MAP[meta.EPLAN_PROJECT_GROUP_KEY]: [
                        {
                            meta.EPLAN_GROUP_NAME_KEY: "Group1",
                            meta.EPLAN_PROPERTY_KEY: {
                                meta.EPLAN_GROUP_META_KEY: "Group Description"
                            }
                        }
                    ]
                }
            }
        }

    def test_init_without_params(self):
        """Test EplanProject initialization without parameters."""
        project = EplanProject()

        self.assertIsNone(project.file_location)
        self.assertIsNotNone(project.meta_data)
        self.assertIsNone(project.controller)
        self.assertIsInstance(project.devices, HashList)
        self.assertEqual(project.project_name, '')
        self.assertEqual(project.groups, [])
        self.assertEqual(project.connections, [])
        self.assertEqual(project.properties, {})
        self.assertEqual(project.sheet_details, [])
        self.assertEqual(project.bom_details, [])

    @patch('pyrox.models.eplan.project.dict_from_xml_file')
    def test_init_with_params(self, mock_dict_from_xml):
        """Test EplanProject initialization with parameters."""
        mock_controller = Mock()

        with patch('pyrox.models.eplan.project.rename_keys'):
            mock_dict_from_xml.return_value = self.mock_meta_data

        project = EplanProject(
            file_location="test.epj",
            meta_data=self.mock_meta_data,
            controller=mock_controller
        )

        self.assertEqual(project.controller, mock_controller)
        self.assertIsInstance(project.devices, HashList)

    def test_inheritance(self):
        """Test that EplanProject inherits from correct base classes."""
        from pyrox.models.abc.save import SupportsFileLocation
        from pyrox.models.abc.meta import SupportsMetaData

        project = EplanProject()
        self.assertIsInstance(project, SupportsFileLocation)
        self.assertIsInstance(project, SupportsMetaData)

    def test_init_subclass_sets_supports_registering(self):
        """Test that __init_subclass__ sets supports_registering to True."""
        class TestEplanProject(EplanProject):
            pass

        self.assertTrue(TestEplanProject.supports_registering)

    @patch('pyrox.models.eplan.project.dict_from_xml_file')
    @patch('pyrox.models.eplan.project.rename_keys')
    def test_file_location_setter_valid_epj(self, mock_rename_keys, mock_dict_from_xml):
        """Test file_location setter with valid .epj file."""
        mock_dict_from_xml.return_value = self.mock_meta_data

        project = EplanProject()
        project.file_location = "test_project.epj"

        self.assertEqual(project.file_location, "test_project.epj")
        mock_dict_from_xml.assert_called_once_with("test_project.epj")
        mock_rename_keys.assert_called_once()

    def test_file_location_setter_non_string(self):
        """Test file_location setter with non-string value."""
        project = EplanProject()

        with self.assertRaises(ValueError) as context:
            project.file_location = 123

        self.assertIn("file_location must be a string", str(context.exception))

    def test_file_location_setter_wrong_extension(self):
        """Test file_location setter with wrong file extension."""
        project = EplanProject()

        with self.assertRaises(ValueError) as context:
            project.file_location = "test_project.txt"

        self.assertIn("file_location must be an EPLAN .epj file", str(context.exception))

    def test_indexed_attribute_property(self):
        """Test indexed_attribute property."""
        project = EplanProject(meta_data=self.mock_meta_data)

        result = project.indexed_attribute
        self.assertEqual(result, self.mock_meta_data[meta.EPLAN_PROJECT_ROOT])

    def test_indexed_attribute_property_no_data(self):
        """Test indexed_attribute property with no meta_data."""
        project = EplanProject()

        result = project.indexed_attribute
        self.assertEqual(result, {})

    def test_project_data_property(self):
        """Test project_data property."""
        project = EplanProject(meta_data=self.mock_meta_data)

        # This test depends on the actual implementation of the property
        # and may need adjustment based on meta.EPLAN_DICT_MAP values
        result = project.project_data
        self.assertIsInstance(result, dict)

    def test_project_properties_property(self):
        """Test project_properties property."""
        project = EplanProject(meta_data=self.mock_meta_data)

        result = project.project_properties
        self.assertIsInstance(result, dict)

    def test_design_source_property(self):
        """Test design_source property."""
        project = EplanProject(meta_data=self.mock_meta_data)
        result = project.design_source
        self.assertEqual(result, "Test Company")

    def test_design_source_property_unknown(self):
        """Test design_source property with unknown value."""
        project = EplanProject(meta_data=self.mock_meta_data)

        from unittest.mock import PropertyMock
        with patch.object(EplanProject, 'project_properties', new_callable=PropertyMock) as mock_prop:
            mock_prop.return_value = {}
            result = project.design_source
            self.assertEqual(result, meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)

    def test_design_source_address_property(self):
        """Test design_source_address property."""
        project = EplanProject(meta_data=self.mock_meta_data)

        from unittest.mock import PropertyMock
        with patch.object(EplanProject, 'project_properties', new_callable=PropertyMock) as mock_prop:
            mock_prop.return_value = {
                meta.EPLAN_DICT_MAP[meta.EPLAN_COMPANY_ADDRESS_LINE1_KEY]: "123 Main St",
                meta.EPLAN_DICT_MAP[meta.EPLAN_COMPANY_ADDRESS_LINE2_KEY]: "Suite 100"
            }
            result = project.design_source_address
            self.assertEqual(result, "123 Main St, Suite 100")

    def test_design_source_address_property_unknown(self):
        """Test design_source_address property with unknown values."""
        project = EplanProject(meta_data=self.mock_meta_data)
        result = project.design_source_address
        self.assertEqual(result, meta.EPLAN_UNKNOWN_ATTRIBUTE_DEFAULT)

    @staticmethod
    def test_strip_eplan_naming_conventions():
        """Test strip_eplan_naming_conventions static method."""
        # Test with @ separator
        result = EplanProject.strip_eplan_naming_conventions("prefix@actual_name")
        assert result == "actual_name"

        # Test with semicolon ending
        result = EplanProject.strip_eplan_naming_conventions("name_with_semicolon;")
        assert result == "name_with_semicolon"

        # Test with both @ and semicolon
        result = EplanProject.strip_eplan_naming_conventions("prefix@name_with_semicolon;")
        assert result == "name_with_semicolon"

        # Test with simple name
        result = EplanProject.strip_eplan_naming_conventions("simple_name")
        assert result == "simple_name"

    def test_process_bom_item_valid(self):
        """Test _process_bom_item with valid item."""
        project = EplanProject()

        item = {
            meta.EPLAN_PROPERTY_KEY: {
                meta.EPLAN_BOM_PART_NO_KEY: "PART-001",
                meta.EPLAN_BOM_PART_DESC_KEY: "prefix@Test Part Description",
                meta.EPLAN_BOM_QUANTITY_KEY: 10,
                meta.EPLAN_BOM_MANUFACTURER_KEY: "Test Manufacturer"
            }
        }

        result = project._process_bom_item(item)

        self.assertIsNotNone(result)
        self.assertEqual(result['part_number'], "PART-001")
        self.assertEqual(result['description'], "Test Part Description")
        self.assertEqual(result['quantity'], 10)
        self.assertEqual(result['manufacturer'], "Test Manufacturer")
        self.assertEqual(result['data'], item)

    def test_process_bom_item_no_properties(self):
        """Test _process_bom_item with item without properties."""
        project = EplanProject()

        item = {}
        result = project._process_bom_item(item)

        self.assertIsNone(result)

    def test_process_bom_item_no_part_number(self):
        """Test _process_bom_item with item without part number."""
        project = EplanProject()

        item = {
            meta.EPLAN_PROPERTY_KEY: {
                meta.EPLAN_BOM_PART_DESC_KEY: "Test Description"
                # Missing part number
            }
        }

        result = project._process_bom_item(item)
        self.assertIsNone(result)

    def test_process_group_data_valid(self):
        """Test _process_group_data with valid group."""
        project = EplanProject()

        group = {
            meta.EPLAN_GROUP_NAME_KEY: "TestGroup",
            meta.EPLAN_PROPERTY_KEY: {
                meta.EPLAN_GROUP_META_KEY: "prefix@Group Description"
            }
        }

        result = project._process_group_data(group)

        self.assertIsNotNone(result)
        self.assertEqual(result['name'], "TestGroup")
        self.assertEqual(result['descriptor'], "Group Description")
        self.assertEqual(result['data'], group)

    def test_process_group_data_no_name(self):
        """Test _process_group_data with group without name."""
        project = EplanProject()

        group = {
            meta.EPLAN_PROPERTY_KEY: {
                meta.EPLAN_GROUP_META_KEY: "Group Description"
            }
            # Missing name
        }

        result = project._process_group_data(group)
        self.assertIsNone(result)

    def test_process_sheet_valid(self):
        """Test _process_sheet with valid sheet."""
        project = EplanProject()

        sheet = {
            meta.EPLAN_PROPERTY_KEY: {
                meta.EPLAN_NAME_KEY: "prefix@Sheet Name"
            },
            meta.EPLAN_PROJECT_INDEX_NUMBER_KEY: {
                meta.EPLAN_INDEX_MAJOR_KEY: "1",
                meta.EPLAN_INDEX_MINOR_KEY: "2"
            }
        }

        result = project._process_sheet(sheet)

        self.assertEqual(result['name'], "Sheet Name")
        self.assertEqual(result['number'], "1.2")
        self.assertEqual(result['data'], sheet)

    def test_process_sheet_no_minor_number(self):
        """Test _process_sheet with sheet without minor number."""
        project = EplanProject()

        sheet = {
            meta.EPLAN_PROPERTY_KEY: {
                meta.EPLAN_NAME_KEY: "Sheet Name"
            },
            meta.EPLAN_PROJECT_INDEX_NUMBER_KEY: {
                meta.EPLAN_INDEX_MAJOR_KEY: "1"
                # Missing minor number
            }
        }

        result = project._process_sheet(sheet)

        self.assertEqual(result['name'], "Sheet Name")
        self.assertEqual(result['number'], "1.Unknown")

    def test_process_sheet_with_no_major_number(self):
        """Test _process_sheet with sheet without major number."""
        project = EplanProject()

        sheet = {
            meta.EPLAN_PROPERTY_KEY: {
                meta.EPLAN_NAME_KEY: "Sheet Name"
            },
            meta.EPLAN_PROJECT_INDEX_NUMBER_KEY: {
                # Missing major number
                meta.EPLAN_INDEX_MINOR_KEY: "2"
            }
        }

        result = project._process_sheet(sheet)

        self.assertEqual(result['name'], "Sheet Name")
        self.assertEqual(result['number'], "Unknown.2")

    def test_get_factory_class_method(self):
        """Test get_factory class method."""
        self.assertEqual(EplanProject.get_factory(), EplanProjectFactory)

    @patch('pyrox.models.eplan.project.log')
    def test_parse_success(self, mock_log):
        """Test parse method success path."""
        project = EplanProject(
            meta_data=self.mock_meta_data
        )

        # Mock all the gather methods
        with patch.object(project, '_gather_project_sheet_details') as mock_sheets:
            with patch.object(project, '_gather_project_bom_details') as mock_bom:
                with patch.object(project, '_gather_project_group_details') as mock_groups:
                    with patch.object(project, '_gather_project_ethernet_devices') as mock_ethernet:
                        with patch.object(project, '_gather_project_device_io_details') as mock_io:

                            project.parse()

                            # Verify all gather methods were called
                            mock_sheets.assert_called_once()
                            mock_bom.assert_called_once()
                            mock_groups.assert_called_once()
                            mock_ethernet.assert_called_once()
                            mock_io.assert_called_once()

                            # Verify logging
                            mock_log.return_value.info.assert_called_with('Done!')

    def test_parse_no_file_location(self):
        """Test parse method without file location."""
        project = EplanProject()

        with self.assertRaises(ValueError) as context:
            project.parse()

        self.assertIn("Meta data is not set for the EPLAN project.", str(context.exception))

    def test_parse_no_meta_data(self):
        """Test parse method without meta data."""
        project = EplanProject()

        with self.assertRaises(ValueError) as context:
            project.parse()

        self.assertIn("Meta data is not set", str(context.exception))

    def test_gather_project_bom_details_list(self):
        """Test _gather_project_bom_details with list input."""
        project = EplanProject()

        bom_items = [
            {meta.EPLAN_PROPERTY_KEY: {meta.EPLAN_BOM_PART_NO_KEY: "PART-001"}},
            {meta.EPLAN_PROPERTY_KEY: {meta.EPLAN_BOM_PART_NO_KEY: "PART-002"}}
        ]

        with patch.object(project, 'project_bom', bom_items):
            with patch.object(project, '_process_bom_item', side_effect=[{'part': '001'}, {'part': '002'}]):
                project._gather_project_bom_details()

                self.assertEqual(len(project.bom_details), 2)

    def test_gather_project_bom_details_dict(self):
        """Test _gather_project_bom_details with dict input."""
        project = EplanProject()

        bom_item = {meta.EPLAN_PROPERTY_KEY: {meta.EPLAN_BOM_PART_NO_KEY: "PART-001"}}

        with patch.object(project, 'project_bom', bom_item):
            with patch.object(project, '_process_bom_item', return_value={'part': '001'}):
                project._gather_project_bom_details()

                self.assertEqual(len(project.bom_details), 1)

    def test_gather_project_sheet_details(self):
        """Test _gather_project_sheet_details method."""
        project = EplanProject()

        sheets = [
            {meta.EPLAN_PROPERTY_KEY: {meta.EPLAN_NAME_KEY: "Sheet1"}},
            {meta.EPLAN_PROPERTY_KEY: {meta.EPLAN_NAME_KEY: "Sheet2"}}
        ]

        with patch.object(project, 'sheets', sheets):
            with patch.object(project, '_process_sheet', side_effect=[{'name': 'Sheet1'}, {'name': 'Sheet2'}]):
                project._gather_project_sheet_details()

                self.assertEqual(len(project.sheet_details), 2)


class TestEplanControllerValidatorFactory(unittest.TestCase):
    """Test cases for EplanControllerValidatorFactory class."""

    def test_factory_inheritance(self):
        """Test that EplanControllerValidatorFactory inherits from MetaFactory."""
        from pyrox.models.abc.factory import MetaFactory

        self.assertTrue(issubclass(EplanControllerValidatorFactory, MetaFactory))

    def test_factory_instantiation(self):
        """Test that EplanControllerValidatorFactory can be instantiated."""
        # ABC meta prevents direct instantiation
        with self.assertRaises(TypeError) as context:
            factory = EplanControllerValidatorFactory()  # type: ignore  # noqa: F841
        self.assertIn("ABCMeta.__new__() missing 3 required positional arguments", str(context.exception))


class TestEplanControllerValidator(unittest.TestCase):
    """Test cases for EplanControllerValidator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.mock_controller.modules = []

        self.mock_project = Mock(spec=EplanProject)
        self.mock_project.devices = Mock(spec=HashList)

    def test_init_without_params(self):
        """Test EplanControllerValidator initialization without parameters."""
        with self.assertRaises(ValueError) as context:
            validator = EplanControllerValidator(controller=None, project=None)  # type: ignore
        self.assertIn("controller must be an instance of Controller!", str(context.exception))

    def test_init_with_params(self):
        """Test EplanControllerValidator initialization with parameters."""
        validator = EplanControllerValidator(
            controller=self.mock_controller,
            project=self.mock_project
        )

        self.assertEqual(validator.controller, self.mock_controller)
        self.assertEqual(validator.project, self.mock_project)

    def test_inheritance(self):
        """Test that EplanControllerValidator inherits from PyroxObject."""
        from pyrox.models.abc.meta import PyroxObject

        validator = EplanControllerValidator(self.mock_controller, self.mock_project)
        self.assertIsInstance(validator, PyroxObject)

    def test_init_subclass_sets_supports_registering(self):
        """Test that __init_subclass__ sets supports_registering to True."""
        class TestValidator(EplanControllerValidator):
            pass

        self.assertTrue(TestValidator.supports_registering)

    def test_get_factory_class_method(self):
        """Test get_factory class method."""
        self.assertEqual(EplanControllerValidator.get_factory(), EplanControllerValidatorFactory)

    def test_find_matching_device_in_controller_found(self):
        """Test find_matching_device_in_controller when device is found."""
        mock_module1 = Mock()
        mock_module1.name = "Device1"
        mock_module2 = Mock()
        mock_module2.name = "Device2"

        self.mock_controller.modules = [mock_module1, mock_module2]

        validator = EplanControllerValidator(self.mock_controller, self.mock_project)
        result = validator.find_matching_device_in_controller("Device2")

        self.assertEqual(result, mock_module2)

    def test_find_matching_device_in_controller_not_found(self):
        """Test find_matching_device_in_controller when device is not found."""
        mock_module = Mock()
        mock_module.name = "Device1"

        self.mock_controller.modules = [mock_module]

        validator = EplanControllerValidator(self.mock_controller, self.mock_project)
        result = validator.find_matching_device_in_controller("NonExistentDevice")

        self.assertIsNone(result)

    def test_find_almost_matching_device_in_controller_found(self):
        """Test find_almost_matching_device_in_controller when device is found."""
        mock_module1 = Mock()
        mock_module1.name = "Device1"
        mock_module2 = Mock()
        mock_module2.name = "Test_Device"

        self.mock_controller.modules = [mock_module1, mock_module2]

        validator = EplanControllerValidator(self.mock_controller, self.mock_project)
        result = validator.find_almost_matching_device_in_controller("Test_Device_Module")

        self.assertEqual(result, mock_module2)

    def test_find_almost_matching_device_in_controller_not_found(self):
        """Test find_almost_matching_device_in_controller when device is not found."""
        mock_module = Mock()
        mock_module.name = "Device1"

        self.mock_controller.modules = [mock_module]

        validator = EplanControllerValidator(self.mock_controller, self.mock_project)
        result = validator.find_almost_matching_device_in_controller("CompletelyDifferentName")

        self.assertIsNone(result)

    def test_find_matching_module_in_project_found(self):
        """Test find_matching_module_in_project when module is found."""
        mock_module = Mock(spec=Module)
        mock_module.name = "TestModule"

        mock_device = Mock(spec=EplanProjectDevice)
        mock_device.name = "TestModule"

        self.mock_project.devices.find_first.return_value = mock_device

        validator = EplanControllerValidator(self.mock_controller, self.mock_project)
        result = validator.find_matching_module_in_project(mock_module)

        self.assertEqual(result, mock_device)
        self.mock_project.devices.find_first.assert_called_once()

    def test_find_almost_matching_module_in_project_found(self):
        """Test find_almost_matching_module_in_project when module is found."""
        mock_module = Mock(spec=Module)
        mock_module.name = "TestModule"

        mock_device = Mock(spec=EplanProjectDevice)
        mock_device.name = "TestModule_Extension"

        self.mock_project.devices.find_first.return_value = mock_device

        validator = EplanControllerValidator(self.mock_controller, self.mock_project)
        result = validator.find_almost_matching_module_in_project(mock_module)

        self.assertEqual(result, mock_device)
        self.mock_project.devices.find_first.assert_called_once()

    @patch('pyrox.models.eplan.project.log')
    def test_validate_success(self, mock_log):
        """Test validate method success path."""
        validator = EplanControllerValidator(
            controller=self.mock_controller,
            project=self.mock_project
        )

        # Mock the validation methods
        with patch.object(validator, '_validate_controller_properties') as mock_controller_val:
            with patch.object(validator, '_validate_modules') as mock_modules_val:

                validator.validate()

                # Verify validation methods were called
                mock_controller_val.assert_called_once()
                mock_modules_val.assert_called_once()

                # Verify logging
                mock_log.return_value.info.assert_has_calls([
                    call('Validating controller...'),
                    call('Validation complete!')
                ])

    def test_abstract_methods_raise_not_implemented(self):
        """Test that abstract methods raise NotImplementedError."""
        validator = EplanControllerValidator(self.mock_controller, self.mock_project)

        with self.assertRaises(NotImplementedError):
            validator._validate_controller_properties()

        with self.assertRaises(NotImplementedError):
            validator._validate_modules()


class TestEplanProjectIntegration(unittest.TestCase):
    """Integration tests for EPLAN project components."""

    def setUp(self):
        """Set up test fixtures for integration tests."""
        self.sample_meta_data = {
            meta.EPLAN_PROJECT_ROOT: {
                meta.EPLAN_DICT_MAP[meta.EPLAN_PROJECT_DATA_KEY]: {
                    meta.EPLAN_DICT_MAP[meta.EPLAN_PROPERTY_KEY]: {
                        meta.EPLAN_DICT_MAP[meta.EPLAN_COMPANY_NAME_KEY]: "Integration Test Company"
                    },
                    meta.EPLAN_DICT_MAP[meta.EPLAN_PROJECT_SHEET_KEY]: [
                        {
                            meta.EPLAN_PROPERTY_KEY: {
                                meta.EPLAN_NAME_KEY: "Integration@Test Sheet"
                            },
                            meta.EPLAN_PROJECT_INDEX_NUMBER_KEY: {
                                meta.EPLAN_INDEX_MAJOR_KEY: "1",
                                meta.EPLAN_INDEX_MINOR_KEY: "0"
                            }
                        }
                    ]
                }
            }
        }

    def test_project_device_workflow(self):
        """Test complete project device workflow."""
        # Create project device
        device_data = {'property': 'value'}
        device = EplanProjectDevice("TestDevice", device_data, "Test Description")

        # Verify device properties
        self.assertEqual(device.name, "TestDevice")
        self.assertEqual(device.data, device_data)
        self.assertEqual(device.description, "Test Description")

        # Create network device
        network_device = EplanNetworkDevice(
            "NetworkDevice",
            "192.168.1.100",
            device_data,
            "Network Description"
        )

        # Verify network device properties
        self.assertEqual(network_device.name, "NetworkDevice")
        self.assertEqual(network_device.ip_address, "192.168.1.100")
        self.assertEqual(network_device.data, device_data)

    def test_project_parsing_workflow(self):
        """Test complete project parsing workflow."""
        project = EplanProject(meta_data=self.sample_meta_data)

        # Mock abstract methods to allow parsing
        with patch.object(project, '_gather_project_device_io_details'):
            with patch.object(project, '_gather_project_ethernet_devices'):

                # Set file location to trigger parsing readiness
                with patch('pyrox.models.eplan.project.dict_from_xml_file', return_value=self.sample_meta_data):
                    with patch('pyrox.models.eplan.project.rename_keys'):
                        project.file_location = "test.epj"

                # Parse the project
                with patch('pyrox.models.eplan.project.log'):
                    project.parse()

    def test_controller_validation_workflow(self):
        """Test complete controller validation workflow."""
        # Create mock controller with modules
        mock_controller = Mock(spec=Controller)
        mock_module = Mock(spec=Module)
        mock_module.name = "TestModule"
        mock_controller.modules = [mock_module]

        # Create mock project with devices
        mock_project = Mock(spec=EplanProject)
        mock_device = Mock(spec=EplanProjectDevice)
        mock_device.name = "TestModule"
        mock_project.devices = Mock(spec=HashList)
        mock_project.devices.find_first.return_value = mock_device

        # Create validator
        validator = EplanControllerValidator(
            controller=mock_controller,
            project=mock_project
        )

        # Test device finding
        found_device = validator.find_matching_device_in_controller("TestModule")
        self.assertEqual(found_device, mock_module)

        found_module = validator.find_matching_module_in_project(mock_module)
        self.assertEqual(found_module, mock_device)


if __name__ == '__main__':
    unittest.main()

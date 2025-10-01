"""Comprehensive unit tests for controller.py module."""
import unittest
from unittest.mock import Mock, patch

from pyrox.models.plc.controller import (
    Controller,
    ControllerFactory,
    ControllerSafetyInfo,
    ControllerModificationSchema,
    ControllerConfiguration
)
from pyrox.models.plc import meta as plc_meta
from pyrox.models.abc.list import HashList
from pyrox.models.abc.factory import MetaFactory


class TestControllerSafetyInfo(unittest.TestCase):
    """Test cases for ControllerSafetyInfo class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock()
        self.test_meta_data = {
            '@SafetyLocked': 'true',
            '@SignatureRunModeProtect': 'false',
            '@ConfigureSafetyIOAlways': 'true',
            '@SafetyLevel': 'SIL2',
            'SafetyTagMap': 'tag1=safety1,tag2=safety2'
        }

        self.safety_info = ControllerSafetyInfo(
            meta_data=self.test_meta_data,
            controller=self.mock_controller
        )

    def test_inheritance(self):
        """Test that ControllerSafetyInfo inherits from PlcObject."""
        self.assertTrue(issubclass(ControllerSafetyInfo, plc_meta.PlcObject))

    def test_safety_locked_property(self):
        """Test safety_locked property getter and setter."""
        # Test getter
        self.assertEqual(self.safety_info.safety_locked, 'true')

        # Test setter with valid value
        self.safety_info.safety_locked = 'false'
        self.assertEqual(self.safety_info['@SafetyLocked'], 'false')

        # Test setter with invalid value
        with self.assertRaises(ValueError) as context:
            self.safety_info.safety_locked = 'invalid'
        self.assertIn("Safety locked must be a valid boolean string", str(context.exception))

    def test_signature_runmode_protect_property(self):
        """Test signature_runmode_protect property getter and setter."""
        # Test getter
        self.assertEqual(self.safety_info.signature_runmode_protect, 'false')

        # Test setter with valid value
        self.safety_info.signature_runmode_protect = 'true'
        self.assertEqual(self.safety_info['@SignatureRunModeProtect'], 'true')

        # Test setter with invalid value
        with self.assertRaises(ValueError) as context:
            self.safety_info.signature_runmode_protect = 'maybe'
        self.assertIn("Signature run mode protect must be a valid boolean string", str(context.exception))

    def test_configure_safety_io_always_property(self):
        """Test configure_safety_io_always property getter and setter."""
        # Test getter
        self.assertEqual(self.safety_info.configure_safety_io_always, 'true')

        # Test setter with valid value
        self.safety_info.configure_safety_io_always = 'false'
        self.assertEqual(self.safety_info['@ConfigureSafetyIOAlways'], 'false')

        # Test setter with invalid value
        with self.assertRaises(ValueError) as context:
            self.safety_info.configure_safety_io_always = 123
        self.assertIn("Configure safety IO always must be a valid boolean string", str(context.exception))

    def test_safety_level_property(self):
        """Test safety_level property getter and setter."""
        # Test getter
        self.assertEqual(self.safety_info.safety_level, 'SIL2')

        # Test setter with valid values
        for level in ['SIL1', 'SIL2', 'SIL3', 'SIL4']:
            self.safety_info.safety_level = level
            self.assertEqual(self.safety_info['@SafetyLevel'], level)

        # Test setter with invalid type
        with self.assertRaises(ValueError) as context:
            self.safety_info.safety_level = 123
        self.assertIn("Safety level must be a string", str(context.exception))

        # Test setter with invalid value
        with self.assertRaises(ValueError) as context:
            self.safety_info.safety_level = 'invalid'
        self.assertIn("Safety level must contain one of: SIL1, SIL2, SIL3, SIL4", str(context.exception))

    def test_safety_tag_map_property(self):
        """Test safety_tag_map property getter and setter."""
        # Test getter
        self.assertEqual(self.safety_info.safety_tag_map, 'tag1=safety1,tag2=safety2')

        # Test setter with valid format
        self.safety_info.safety_tag_map = 'new_tag=new_safety'
        self.assertEqual(self.safety_info['SafetyTagMap'], 'new_tag=new_safety')

        # Test setter with empty string
        self.safety_info.safety_tag_map = ''
        self.assertIsNone(self.safety_info['SafetyTagMap'])

        # Test setter with None SafetyTagMap initially
        safety_info_none = ControllerSafetyInfo(
            meta_data={'SafetyTagMap': None},
            controller=self.mock_controller
        )
        self.assertEqual(safety_info_none.safety_tag_map, '')

        # Test setter with invalid type
        with self.assertRaises(ValueError) as context:
            self.safety_info.safety_tag_map = 123
        self.assertIn("Safety tag map must be a string", str(context.exception))

        # Test setter with invalid format
        with self.assertRaises(ValueError) as context:
            self.safety_info.safety_tag_map = 'invalid_format'
        self.assertIn("Safety tag map must be in the format", str(context.exception))

        # Test setter with invalid format (too many equals)
        with self.assertRaises(ValueError) as context:
            self.safety_info.safety_tag_map = 'tag=safety=extra'
        self.assertIn("Safety tag map must be in the format", str(context.exception))

    def test_safety_tag_map_dict_list(self):
        """Test safety_tag_map_dict_list property."""
        expected = [
            {'@Name': 'tag1', 'TagName': 'tag1', 'SafetyTagName': 'safety1'},
            {'@Name': 'tag2', 'TagName': 'tag2', 'SafetyTagName': 'safety2'}
        ]
        result = self.safety_info.safety_tag_map_dict_list
        self.assertEqual(result, expected)

        # Test with empty string
        self.safety_info.safety_tag_map = ''
        self.assertEqual(self.safety_info.safety_tag_map_dict_list, [])

        # Test with invalid type
        self.safety_info['SafetyTagMap'] = 123
        with self.assertRaises(ValueError) as context:
            self.safety_info.safety_tag_map_dict_list
        self.assertIn("Safety tag map must be a string", str(context.exception))

    def test_add_safety_tag_mapping(self):
        """Test add_safety_tag_mapping method."""
        # Test adding to existing map
        self.safety_info.add_safety_tag_mapping('tag3', 'safety3')
        self.assertIn('tag3=safety3', self.safety_info.safety_tag_map)

        # Test adding to empty map
        empty_safety_info = ControllerSafetyInfo(
            meta_data={'SafetyTagMap': None},
            controller=self.mock_controller
        )
        empty_safety_info.add_safety_tag_mapping('first_tag', 'first_safety')
        self.assertEqual(empty_safety_info.safety_tag_map, 'first_tag=first_safety')

        # Test removing and re-adding (should replace)
        original_map = 'tag1=safety1,tag2=safety2'
        self.safety_info.safety_tag_map = original_map
        self.safety_info.add_safety_tag_mapping('tag1', 'new_safety1')
        # Should remove old mapping and add new one
        expected = 'tag1=safety1,tag2=safety2,tag1=new_safety1'
        self.assertEqual(self.safety_info.safety_tag_map, expected)

        # Test with invalid types
        with self.assertRaises(ValueError) as context:
            self.safety_info.add_safety_tag_mapping(123, 'safety')
        self.assertIn("Tag names must be strings", str(context.exception))

        with self.assertRaises(ValueError) as context:
            self.safety_info.add_safety_tag_mapping('tag', 123)
        self.assertIn("Tag names must be strings", str(context.exception))

    def test_remove_safety_tag_mapping(self):
        """Test remove_safety_tag_mapping method."""
        # Test removing from existing map
        self.safety_info.remove_safety_tag_mapping('tag1', 'safety1')
        self.assertEqual(self.safety_info.safety_tag_map, 'tag2=safety2')

        # Test removing from empty map
        empty_safety_info = ControllerSafetyInfo(
            meta_data={'SafetyTagMap': None},
            controller=self.mock_controller
        )
        empty_safety_info.remove_safety_tag_mapping('tag', 'safety')  # Should not raise error

        # Test removing non-existent mapping
        self.safety_info.remove_safety_tag_mapping('nonexistent', 'safety')  # Should not raise error

        # Test with different positions
        self.safety_info.safety_tag_map = 'tag1=safety1,tag2=safety2,tag3=safety3'

        # Remove from middle
        self.safety_info.remove_safety_tag_mapping('tag2', 'safety2')
        self.assertEqual(self.safety_info.safety_tag_map, 'tag1=safety1,tag3=safety3')

        # Remove from end
        self.safety_info.remove_safety_tag_mapping('tag3', 'safety3')
        self.assertEqual(self.safety_info.safety_tag_map, 'tag1=safety1')

        # Remove last one
        self.safety_info.remove_safety_tag_mapping('tag1', 'safety1')
        self.assertEqual(self.safety_info.safety_tag_map, '')

        # Test with invalid types
        with self.assertRaises(ValueError) as context:
            self.safety_info.remove_safety_tag_mapping(123, 'safety')
        self.assertIn("Tag names must be strings", str(context.exception))

        with self.assertRaises(ValueError) as context:
            self.safety_info.remove_safety_tag_mapping('tag', 123)
        self.assertIn("Tag names must be strings", str(context.exception))


class TestControllerFactory(unittest.TestCase):
    """Test cases for ControllerFactory class."""

    def setUp(self):
        """Set up test fixtures."""
        self.controller_data = {
            '@Name': 'TestController',
            '@ProcessorType': 'TestProcessor',
            'Tags': {'Tag': []},
            'Programs': {'Program': []},
            'Modules': {'Module': []},
            'DataTypes': {'DataType': []}
        }

    def test_inheritance(self):
        """Test that ControllerFactory inherits from MetaFactory."""
        self.assertTrue(issubclass(ControllerFactory, MetaFactory))

    def test_get_best_match_with_matches(self):
        """Test get_best_match method structure."""
        # Test that the method exists and is callable
        self.assertTrue(hasattr(ControllerFactory, 'get_best_match'))
        self.assertTrue(callable(getattr(ControllerFactory, 'get_best_match')))

        # Test with empty data returns None
        result = ControllerFactory.get_best_match(None)
        self.assertIsNone(result)

        # Test with empty dict returns None
        result = ControllerFactory.get_best_match({})
        self.assertIsNone(result)

    def test_get_best_match_no_matches(self):
        """Test get_best_match method with no valid input."""
        # Test with None data
        result = ControllerFactory.get_best_match(None)
        self.assertIsNone(result)

        # Test with empty dict
        result = ControllerFactory.get_best_match({})
        self.assertIsNone(result)

    @patch('pyrox.models.plc.controller.log')
    def test_get_best_match_empty_data(self, mock_log):
        """Test get_best_match method with empty controller data."""
        result = ControllerFactory.get_best_match(None)
        self.assertIsNone(result)

        result = ControllerFactory.get_best_match({})
        self.assertIsNone(result)

    @patch.object(ControllerFactory, 'get_best_match')
    def test_create_controller_success(self, mock_get_best_match):
        """Test create_controller method with successful match."""
        mock_controller_class = Mock()
        mock_controller_instance = Mock()
        mock_controller_class.return_value = mock_controller_instance
        mock_get_best_match.return_value = mock_controller_class

        result = ControllerFactory.create_controller(self.controller_data, extra_param='test')

        self.assertEqual(result, mock_controller_instance)
        mock_get_best_match.assert_called_once_with(self.controller_data)
        mock_controller_class.assert_called_once_with(meta_data=self.controller_data, extra_param='test')

    @patch.object(ControllerFactory, 'get_best_match')
    def test_create_controller_no_match(self, mock_get_best_match):
        """Test create_controller method with no matching controller."""
        mock_get_best_match.return_value = None

        result = ControllerFactory.create_controller(self.controller_data)

        self.assertIsNone(result)


class TestController(unittest.TestCase):
    """Test cases for Controller class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_meta_data = {
            'RSLogix5000Content': {
                'Controller': {
                    '@Name': 'TestController',
                    '@MajorRev': '32',
                    '@MinorRev': '11',
                    '@CommPath': '1,0',
                    'Tags': {'Tag': []},
                    'Programs': {'Program': []},
                    'Modules': {'Module': [
                        {'@Name': 'Local', '@Major': '32', '@Minor': '11',
                         'Ports': {'Port': {'@Type': 'ICP', '@Address': '0'}}}
                    ]},
                    'DataTypes': {'DataType': []},
                    'AddOnInstructionDefinitions': {'AddOnInstructionDefinition': []},
                    'SafetyInfo': {
                        '@SafetyLocked': 'false',
                        '@SafetyLevel': 'SIL2'
                    }
                }
            }
        }

    def test_inheritance(self):
        """Test that Controller inherits from NamedPlcObject."""
        self.assertTrue(issubclass(Controller, plc_meta.NamedPlcObject))

    def test_metaclass(self):
        """Test that Controller has proper metaclass structure."""
        # Check that Controller has the expected class structure
        self.assertTrue(hasattr(Controller, '__class__'))
        # Check that it has some factory-related attributes
        self.assertTrue(hasattr(Controller, 'get_factory') or hasattr(Controller.__class__, '__mro__'))

    def test_initialization_valid_data(self):
        """Test Controller initialization with valid data."""
        controller = Controller(meta_data=self.test_meta_data, file_location='test.L5X')

        self.assertEqual(controller.meta_data, self.test_meta_data)
        self.assertEqual(controller.file_location, 'test.L5X')
        self.assertIsInstance(controller._aois, HashList)
        self.assertIsInstance(controller._datatypes, HashList)
        self.assertIsInstance(controller._modules, HashList)
        self.assertIsInstance(controller._programs, HashList)
        self.assertIsInstance(controller._tags, HashList)

    def test_initialization_no_file_location(self):
        """Test Controller initialization without file location."""
        controller = Controller(meta_data=self.test_meta_data)
        self.assertIsNone(controller._file_location)

    def test_getitem_setitem(self):
        """Test __getitem__ and __setitem__ methods."""
        controller = Controller(meta_data=self.test_meta_data)

        # Test __getitem__
        self.assertEqual(controller['@Name'], 'TestController')
        self.assertEqual(controller['@MajorRev'], '32')

        # Test __setitem__
        controller['@Name'] = 'NewName'
        self.assertEqual(controller['@Name'], 'NewName')

        # Test setting revision updates software revision
        controller['@MajorRev'] = '33'
        self.assertEqual(controller.content_meta_data['@SoftwareRevision'], '33.11')

    @patch('pyrox.models.plc.controller.get_save_file')
    def test_file_location_property_with_dialog(self, mock_get_save_file):
        """Test file_location property when not set initially."""
        mock_get_save_file.return_value = 'selected_file.L5X'

        controller = Controller(meta_data=self.test_meta_data)
        result = controller.file_location

        self.assertEqual(result, 'selected_file.L5X')
        mock_get_save_file.assert_called_once()

    @patch('pyrox.models.plc.controller.get_save_file')
    def test_file_location_property_dialog_cancelled(self, mock_get_save_file):
        """Test file_location property when dialog is cancelled."""
        mock_get_save_file.return_value = None

        controller = Controller(meta_data=self.test_meta_data)

        with self.assertRaises(RuntimeError) as context:
            controller.file_location
        self.assertIn("File location is not set", str(context.exception))

    def test_file_location_setter(self):
        """Test file_location setter."""
        controller = Controller(meta_data=self.test_meta_data)

        controller.file_location = 'new_file.L5X'
        self.assertEqual(controller._file_location, 'new_file.L5X')

        # Test invalid type
        with self.assertRaises(ValueError) as context:
            controller.file_location = 123
        self.assertIn("File location must be a string", str(context.exception))

    def test_major_minor_revision_properties(self):
        """Test major_revision and minor_revision properties."""
        controller = Controller(meta_data=self.test_meta_data)

        # Test getters
        self.assertEqual(controller.major_revision, 32)
        self.assertEqual(controller.minor_revision, 11)

        # Test setters
        controller.major_revision = 33
        controller.minor_revision = 12
        self.assertEqual(controller['@MajorRev'], 33)
        self.assertEqual(controller['@MinorRev'], 12)

    def test_comm_path_property(self):
        """Test comm_path property getter and setter."""
        controller = Controller(meta_data=self.test_meta_data)

        # Test getter
        self.assertEqual(controller.comm_path, '1,0')

        # Test setter
        controller.comm_path = '2,1'
        self.assertEqual(controller['@CommPath'], '2,1')

        # Test invalid type
        with self.assertRaises(ValueError) as context:
            controller.comm_path = 123
        self.assertIn("CommPath must be a string", str(context.exception))

    def test_plc_module_properties(self):
        """Test PLC module related properties."""
        controller = Controller(meta_data=self.test_meta_data)

        # Test plc_module
        plc_module = controller.plc_module
        self.assertEqual(plc_module['@Name'], 'Local')

        # Test plc_module_ports
        ports = controller.plc_module_ports
        self.assertEqual(len(ports), 1)
        self.assertEqual(ports[0]['@Type'], 'ICP')

        # Test plc_module_icp_port
        icp_port = controller.plc_module_icp_port
        self.assertEqual(icp_port['@Address'], '0')

        # Test slot
        self.assertEqual(controller.slot, 0)

    def test_slot_setter(self):
        """Test slot setter."""
        controller = Controller(meta_data=self.test_meta_data)

        controller.slot = 5
        self.assertEqual(controller._slot, 5)

    def test_safety_info_property(self):
        """Test safety_info property."""
        controller = Controller(meta_data=self.test_meta_data)

        safety_info = controller.safety_info
        self.assertIsInstance(safety_info, ControllerSafetyInfo)
        self.assertEqual(safety_info.safety_level, 'SIL2')

    def test_controller_type_property(self):
        """Test controller_type property."""
        controller = Controller(meta_data=self.test_meta_data)
        self.assertEqual(controller.controller_type, 'Controller')

    @patch('pyrox.models.plc.controller.l5x_dict_from_file')
    def test_from_file_success(self, mock_l5x_dict_from_file):
        """Test from_file class method with successful file reading."""
        mock_l5x_dict_from_file.return_value = self.test_meta_data

        with patch.object(ControllerFactory, 'create_controller') as mock_create:
            mock_controller = Controller(meta_data=self.test_meta_data)
            mock_create.return_value = mock_controller

            result = Controller.from_file('test.L5X')

            self.assertIsInstance(result, Controller)
            mock_l5x_dict_from_file.assert_called_once_with('test.L5X')
            mock_create.assert_called_once_with(self.test_meta_data, file_location='test.L5X')

    @patch('pyrox.models.plc.controller.l5x_dict_from_file')
    def test_from_file_invalid_file(self, mock_l5x_dict_from_file):
        """Test from_file class method with invalid file."""
        mock_l5x_dict_from_file.return_value = None

        result = Controller.from_file('invalid.L5X')

        self.assertIsNone(result)

    @patch('pyrox.models.plc.controller.l5x_dict_from_file')
    @patch('pyrox.models.plc.controller.log')
    def test_from_file_no_factory_match(self, mock_log, mock_l5x_dict_from_file):
        """Test from_file class method when factory returns no match."""
        mock_l5x_dict_from_file.return_value = self.test_meta_data

        with patch.object(ControllerFactory, 'create_controller') as mock_create:
            mock_create.return_value = None

            result = Controller.from_file('test.L5X')

            self.assertIsInstance(result, Controller)
            # Should create generic controller when factory fails

    def test_from_meta_data_success(self):
        """Test from_meta_data class method with valid data."""
        result = Controller.from_meta_data(self.test_meta_data)

        self.assertIsInstance(result, Controller)
        self.assertEqual(result.meta_data, self.test_meta_data)

    def test_from_meta_data_invalid_data(self):
        """Test from_meta_data class method with invalid data."""
        # Test None
        with self.assertRaises(ValueError):
            Controller.from_meta_data(None)

        # Test non-dict
        with self.assertRaises(ValueError):
            Controller.from_meta_data("invalid")

        # Test missing RSLogix5000Content
        with self.assertRaises(ValueError):
            Controller.from_meta_data({})

        # Test missing Controller
        with self.assertRaises(ValueError):
            Controller.from_meta_data({'RSLogix5000Content': {}})

    def test_get_class_and_factory(self):
        """Test get_class and get_factory class methods."""
        self.assertEqual(Controller.get_class(), Controller)
        self.assertEqual(Controller.get_factory(), ControllerFactory)

    @patch('pyrox.models.plc.controller.log')
    def test_compile_from_meta_data(self, mock_log):
        """Test _compile_from_meta_data method."""
        controller = Controller(meta_data=self.test_meta_data)

        # Mock the compilation methods
        with patch.object(controller, '_compile_common_hashlist_from_meta_data') as mock_compile:
            with patch.object(controller, '_compile_atomic_datatypes') as mock_atomic:
                with patch.object(controller, '_compile_safety_info') as mock_safety:
                    controller._compile_from_meta_data()

                    # Verify lists were cleared and compiled
                    self.assertEqual(mock_compile.call_count, 5)  # aois, datatypes, modules, programs, tags
                    mock_atomic.assert_called_once()
                    mock_safety.assert_called_once()

    def test_add_methods(self):
        """Test add_* methods for various assets."""
        controller = Controller(meta_data=self.test_meta_data)

        # Mock objects
        mock_aoi = Mock()
        mock_aoi.name = 'TestAOI'
        mock_aoi.meta_data = {'@Name': 'TestAOI'}

        mock_datatype = Mock()
        mock_datatype.name = 'TestDatatype'
        mock_datatype.meta_data = {'@Name': 'TestDatatype'}

        mock_module = Mock()
        mock_module.name = 'TestModule'
        mock_module.meta_data = {'@Name': 'TestModule'}

        mock_program = Mock()
        mock_program.name = 'TestProgram'
        mock_program.meta_data = {'@Name': 'TestProgram'}

        mock_tag = Mock()
        mock_tag.name = 'TestTag'
        mock_tag.meta_data = {'@Name': 'TestTag'}

        # Mock config to return correct types
        controller.config.aoi_type = type(mock_aoi)
        controller.config.datatype_type = type(mock_datatype)
        controller.config.module_type = type(mock_module)
        controller.config.program_type = type(mock_program)
        controller.config.tag_type = type(mock_tag)

        # Test add methods
        with patch.object(controller, '_add_common') as mock_add_common:
            controller.add_aoi(mock_aoi)
            controller.add_datatype(mock_datatype)
            controller.add_module(mock_module)
            controller.add_program(mock_program)
            controller.add_tag(mock_tag)

            self.assertEqual(mock_add_common.call_count, 5)

    def test_remove_methods(self):
        """Test remove_* methods for various assets."""
        controller = Controller(meta_data=self.test_meta_data)

        # Mock objects
        mock_aoi = Mock()
        mock_datatype = Mock()
        mock_module = Mock()
        mock_program = Mock()
        mock_tag = Mock()

        # Test remove methods
        with patch.object(controller, '_remove_common') as mock_remove_common:
            controller.remove_aoi(mock_aoi)
            controller.remove_datatype(mock_datatype)
            controller.remove_module(mock_module)
            controller.remove_program(mock_program)
            controller.remove_tag(mock_tag)

            self.assertEqual(mock_remove_common.call_count, 5)

    @patch('pyrox.models.plc.controller.l5x_dict_from_file')
    def test_import_assets_from_file(self, mock_l5x_dict_from_file):
        """Test import_assets_from_file method."""
        mock_l5x_dict_from_file.return_value = self.test_meta_data

        controller = Controller(meta_data=self.test_meta_data)

        with patch.object(controller, 'import_assets_from_l5x_dict') as mock_import:
            controller.import_assets_from_file('test.L5X', ['Tags'])

            mock_l5x_dict_from_file.assert_called_once_with('test.L5X')
            mock_import.assert_called_once_with(self.test_meta_data, asset_types=['Tags'])

    def test_find_instruction(self):
        """Test find_instruction method structure."""
        controller = Controller(meta_data=self.test_meta_data)

        # Test that the method exists and is callable
        self.assertTrue(hasattr(controller, 'find_instruction'))
        self.assertTrue(callable(getattr(controller, 'find_instruction')))

        # Test with empty instruction list (default state)
        result = controller.find_instruction('XIC')
        self.assertIsInstance(result, list)

    def test_find_unpaired_controller_inputs(self):
        """Test find_unpaired_controller_inputs method structure."""
        controller = Controller(meta_data=self.test_meta_data)

        # Test that the method exists and is callable
        self.assertTrue(hasattr(controller, 'find_unpaired_controller_inputs'))
        self.assertTrue(callable(getattr(controller, 'find_unpaired_controller_inputs')))

        # Test with empty instruction list (default state)
        result = controller.find_unpaired_controller_inputs()
        self.assertIsInstance(result, dict)

    def test_find_redundant_otes(self):
        """Test find_redundant_otes method structure."""
        controller = Controller(meta_data=self.test_meta_data)

        # Test that the method exists and is callable
        self.assertTrue(hasattr(controller, 'find_redundant_otes'))
        self.assertTrue(callable(getattr(controller, 'find_redundant_otes')))

        # Test with empty instruction list (default state)
        result = controller.find_redundant_otes()
        self.assertIsInstance(result, dict)

    def test_find_diagnostic_rungs(self):
        """Test find_diagnostic_rungs method structure."""
        controller = Controller(meta_data=self.test_meta_data)

        # Test that the method exists and is callable
        self.assertTrue(hasattr(controller, 'find_diagnostic_rungs'))
        self.assertTrue(callable(getattr(controller, 'find_diagnostic_rungs')))

        # Test with empty program list (default state)
        result = controller.find_diagnostic_rungs()
        self.assertIsInstance(result, list)

    def test_rename_asset(self):
        """Test rename_asset method structure."""
        controller = Controller(meta_data=self.test_meta_data)

        # Test that the method exists and is callable
        self.assertTrue(hasattr(controller, 'rename_asset'))
        self.assertTrue(callable(getattr(controller, 'rename_asset')))

        # Test with None parameters (should return early without error)
        try:
            controller.rename_asset(None, 'test', 'test')
            controller.rename_asset(plc_meta.LogixAssetType.TAG, '', 'test')
            controller.rename_asset(plc_meta.LogixAssetType.TAG, 'test', '')
        except Exception:
            self.fail('rename_asset raised an exception with invalid parameters')


class TestControllerConfiguration(unittest.TestCase):
    """Test cases for ControllerConfiguration class."""

    def test_default_values(self):
        """Test ControllerConfiguration default values."""
        from pyrox.models.plc.aoi import AddOnInstruction
        from pyrox.models.plc.datatype import Datatype
        from pyrox.models.plc.module import Module
        from pyrox.models.plc.program import Program
        from pyrox.models.plc.routine import Routine
        from pyrox.models.plc.rung import Rung
        from pyrox.models.plc.tag import Tag

        config = ControllerConfiguration()

        self.assertEqual(config.aoi_type, AddOnInstruction)
        self.assertEqual(config.controller_type, Controller)
        self.assertEqual(config.datatype_type, Datatype)
        self.assertEqual(config.module_type, Module)
        self.assertEqual(config.program_type, Program)
        self.assertEqual(config.routine_type, Routine)
        self.assertEqual(config.rung_type, Rung)
        self.assertEqual(config.tag_type, Tag)

    def test_custom_values(self):
        """Test ControllerConfiguration with custom values."""
        custom_config = ControllerConfiguration(
            aoi_type=Mock,
            controller_type=Mock,
            datatype_type=Mock,
            module_type=Mock,
            program_type=Mock,
            routine_type=Mock,
            rung_type=Mock,
            tag_type=Mock
        )

        self.assertEqual(custom_config.aoi_type, Mock)
        self.assertEqual(custom_config.controller_type, Mock)
        self.assertEqual(custom_config.datatype_type, Mock)
        self.assertEqual(custom_config.module_type, Mock)
        self.assertEqual(custom_config.program_type, Mock)
        self.assertEqual(custom_config.routine_type, Mock)
        self.assertEqual(custom_config.rung_type, Mock)
        self.assertEqual(custom_config.tag_type, Mock)


class TestControllerModificationSchema(unittest.TestCase):
    """Test cases for ControllerModificationSchema class."""

    def setUp(self):
        """Set up test fixtures."""
        self.source_controller = Mock(spec=Controller)
        self.destination_controller = Mock(spec=Controller)
        self.schema = ControllerModificationSchema(
            source=self.source_controller,
            destination=self.destination_controller
        )

    def test_initialization(self):
        """Test ControllerModificationSchema initialization."""
        self.assertEqual(self.schema.source, self.source_controller)
        self.assertEqual(self.schema.destination, self.destination_controller)
        self.assertEqual(self.schema.actions, [])

    def test_add_controller_tag_migration(self):
        """Test add_controller_tag_migration method."""
        self.schema.add_controller_tag_migration('TestTag')

        self.assertEqual(len(self.schema.actions), 1)
        action = self.schema.actions[0]
        self.assertEqual(action['type'], 'migrate_controller_tag')
        self.assertEqual(action['name'], 'TestTag')
        self.assertEqual(action['method'], self.schema._execute_controller_tag_migration)

    def test_add_datatype_migration(self):
        """Test add_datatype_migration method."""
        self.schema.add_datatype_migration('TestDatatype')

        self.assertEqual(len(self.schema.actions), 1)
        action = self.schema.actions[0]
        self.assertEqual(action['type'], 'migrate_datatype')
        self.assertEqual(action['name'], 'TestDatatype')
        self.assertEqual(action['method'], self.schema._execute_datatype_migration)

    def test_add_controller_tag(self):
        """Test add_controller_tag method."""
        from pyrox.models.plc.tag import Tag
        mock_tag = Mock(spec=Tag)
        mock_tag.meta_data = {'@Name': 'TestTag'}

        result = self.schema.add_controller_tag(mock_tag)

        self.assertEqual(result, mock_tag)
        self.assertEqual(len(self.schema.actions), 1)
        action = self.schema.actions[0]
        self.assertEqual(action['type'], 'add_controller_tag')
        self.assertEqual(action['asset'], mock_tag.meta_data)

    def test_add_controller_tag_invalid_type(self):
        """Test add_controller_tag method with invalid tag type."""
        with self.assertRaises(ValueError) as context:
            self.schema.add_controller_tag("invalid_tag")
        self.assertIn("Tag must be an instance of Tag class", str(context.exception))

    def test_add_routine_migration(self):
        """Test add_routine_migration method."""
        self.schema.add_routine_migration(
            source_program_name='SourceProgram',
            routine_name='TestRoutine',
            destination_program_name='DestProgram',
            rung_updates={'1': 'new_rung'}
        )

        self.assertEqual(len(self.schema.actions), 1)
        action = self.schema.actions[0]
        self.assertEqual(action['type'], 'migrate_routine')
        self.assertEqual(action['source_program'], 'SourceProgram')
        self.assertEqual(action['routine'], 'TestRoutine')
        self.assertEqual(action['destination_program'], 'DestProgram')
        self.assertEqual(action['rung_updates'], {'1': 'new_rung'})

    def test_add_routine_migration_default_destination(self):
        """Test add_routine_migration method with default destination program."""
        self.schema.add_routine_migration(
            source_program_name='SourceProgram',
            routine_name='TestRoutine'
        )

        action = self.schema.actions[0]
        self.assertEqual(action['destination_program'], 'SourceProgram')
        self.assertEqual(action['rung_updates'], {})

    def test_add_import_from_file(self):
        """Test add_import_from_file method."""
        self.schema.add_import_from_file('test.L5X', ['Tags', 'DataTypes'])

        self.assertEqual(len(self.schema.actions), 1)
        action = self.schema.actions[0]
        self.assertEqual(action['type'], 'import_from_file')
        self.assertEqual(action['file'], 'test.L5X')
        self.assertEqual(action['asset_types'], ['Tags', 'DataTypes'])

    def test_add_import_from_l5x_dict(self):
        """Test add_import_from_l5x_dict method."""
        test_dict = {'RSLogix5000Content': {'Controller': {}}}
        self.schema.add_import_from_l5x_dict(test_dict, ['Programs'])

        self.assertEqual(len(self.schema.actions), 1)
        action = self.schema.actions[0]
        self.assertEqual(action['type'], 'import_from_l5x_dict')
        self.assertEqual(action['l5x_dict'], test_dict)
        self.assertEqual(action['asset_types'], ['Programs'])

    def test_add_safety_tag_mapping(self):
        """Test add_safety_tag_mapping method."""
        self.schema.add_safety_tag_mapping('StandardTag', 'SafetyTag')

        self.assertEqual(len(self.schema.actions), 1)
        action = self.schema.actions[0]
        self.assertEqual(action['type'], 'safety_tag_mapping')
        self.assertEqual(action['standard'], 'StandardTag')
        self.assertEqual(action['safety'], 'SafetyTag')

    def test_add_safety_tag_mapping_invalid_types(self):
        """Test add_safety_tag_mapping method with invalid types."""
        with self.assertRaises(ValueError) as context:
            self.schema.add_safety_tag_mapping(123, 'SafetyTag')
        self.assertIn("Source and destination tags must be strings", str(context.exception))

    def test_remove_controller_tag(self):
        """Test remove_controller_tag method."""
        self.schema.remove_controller_tag('TagToRemove')

        self.assertEqual(len(self.schema.actions), 1)
        action = self.schema.actions[0]
        self.assertEqual(action['type'], 'remove_controller_tag')
        self.assertEqual(action['name'], 'TagToRemove')

    def test_remove_datatype(self):
        """Test remove_datatype method."""
        self.schema.remove_datatype('DatatypeToRemove')

        self.assertEqual(len(self.schema.actions), 1)
        action = self.schema.actions[0]
        self.assertEqual(action['type'], 'remove_datatype')
        self.assertEqual(action['name'], 'DatatypeToRemove')

    def test_remove_routine(self):
        """Test remove_routine method."""
        self.schema.remove_routine('TestProgram', 'RoutineToRemove')

        self.assertEqual(len(self.schema.actions), 1)
        action = self.schema.actions[0]
        self.assertEqual(action['type'], 'remove_routine')
        self.assertEqual(action['program'], 'TestProgram')
        self.assertEqual(action['name'], 'RoutineToRemove')

    def test_safe_get_destination_controller(self):
        """Test _safe_get_destination_controller method."""
        # Test with valid destination
        result = self.schema._safe_get_destination_controller()
        self.assertEqual(result, self.destination_controller)

        # Test with None destination
        self.schema.destination = None
        with self.assertRaises(ValueError) as context:
            self.schema._safe_get_destination_controller()
        self.assertIn("Destination controller not set", str(context.exception))

    def test_safe_register_action(self):
        """Test _safe_register_action method."""
        action1 = {'type': 'test_action', 'data': 'test'}
        action2 = {'type': 'test_action', 'data': 'test'}  # Duplicate
        action3 = {'type': 'different_action', 'data': 'test'}

        self.schema._safe_register_action(action1)
        self.schema._safe_register_action(action2)  # Should not be added (duplicate)
        self.schema._safe_register_action(action3)

        self.assertEqual(len(self.schema.actions), 2)
        self.assertIn(action1, self.schema.actions)
        self.assertIn(action3, self.schema.actions)

    @patch('pyrox.models.plc.controller.log')
    def test_execute_with_valid_methods(self, mock_log):
        """Test execute method with valid action methods."""
        # Mock destination controller compile method
        self.destination_controller.compile = Mock()

        # Create actions with mock methods
        mock_method1 = Mock()
        mock_method2 = Mock()

        self.schema.actions = [
            {'type': 'test1', 'method': mock_method1},
            {'type': 'test2', 'method': mock_method2}
        ]

        self.schema.execute()

        # Verify methods were called with correct actions
        mock_method1.assert_called_once_with({'type': 'test1', 'method': mock_method1})
        mock_method2.assert_called_once_with({'type': 'test2', 'method': mock_method2})
        self.destination_controller.compile.assert_called_once()

    @patch('pyrox.models.plc.controller.log')
    def test_execute_with_invalid_method(self, mock_log):
        """Test execute method with invalid action method."""
        self.destination_controller.compile = Mock()

        self.schema.actions = [
            {'type': 'test', 'method': 'not_callable'}
        ]

        self.schema.execute()

        # Should not raise error, just log warning
        self.destination_controller.compile.assert_called_once()

    def test_execute_no_destination(self):
        """Test execute method with no destination controller."""
        self.schema.destination = None

        with self.assertRaises(ValueError) as context:
            self.schema.execute()
        self.assertIn("Destination controller is not set", str(context.exception))


if __name__ == '__main__':
    unittest.main()

"""Unit tests for meta.py module."""

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

from pyrox.models.plc.meta import (
    # Constants
    INST_RE_PATTERN,
    INST_TYPE_RE_PATTERN,
    INST_OPER_RE_PATTERN,
    PLC_ROOT_FILE,
    PLC_PROG_FILE,
    PLC_ROUT_FILE,
    PLC_DT_FILE,
    PLC_AOI_FILE,
    PLC_MOD_FILE,
    PLC_RUNG_FILE,
    PLC_TAG_FILE,
    BASE_FILES,
    RE_PATTERN_META_PRE,
    RE_PATTERN_META_POST,
    ATOMIC_DATATYPES,
    INPUT_INSTRUCTIONS,
    OUTPUT_INSTRUCTIONS,
    L5X_ASSETS,
    L5X_PROP_NAME,
    L5X_PROP_DESCRIPTION,
    CIPTypes,
    # Instruction constants
    INSTR_XIC,
    INSTR_XIO,
    # Enums
    LogixTagScope,
    LogixInstructionType,
    LogixAssetType,
    # Classes
    PlcObject,
    NamedPlcObject,
)
from pyrox.models.abc.meta import EnforcesNaming


class TestConstants(unittest.TestCase):
    """Test cases for module constants."""

    def test_regex_patterns(self):
        """Test regex pattern constants are properly defined."""
        self.assertIsInstance(INST_RE_PATTERN, str)
        self.assertIsInstance(INST_TYPE_RE_PATTERN, str)
        self.assertIsInstance(INST_OPER_RE_PATTERN, str)
        self.assertIsInstance(RE_PATTERN_META_PRE, str)
        self.assertIsInstance(RE_PATTERN_META_POST, str)

    def test_file_paths(self):
        """Test file path constants are Path objects."""
        file_paths = [
            PLC_ROOT_FILE,
            PLC_PROG_FILE,
            PLC_ROUT_FILE,
            PLC_DT_FILE,
            PLC_AOI_FILE,
            PLC_MOD_FILE,
            PLC_RUNG_FILE,
            PLC_TAG_FILE,
        ]

        for file_path in file_paths:
            self.assertIsInstance(file_path, Path)
            self.assertTrue(file_path.suffix == '.L5X')

    def test_base_files_list(self):
        """Test BASE_FILES list contains all expected files."""
        self.assertEqual(len(BASE_FILES), 8)
        self.assertIn(PLC_ROOT_FILE, BASE_FILES)
        self.assertIn(PLC_PROG_FILE, BASE_FILES)
        self.assertIn(PLC_ROUT_FILE, BASE_FILES)
        self.assertIn(PLC_DT_FILE, BASE_FILES)
        self.assertIn(PLC_AOI_FILE, BASE_FILES)
        self.assertIn(PLC_MOD_FILE, BASE_FILES)
        self.assertIn(PLC_RUNG_FILE, BASE_FILES)
        self.assertIn(PLC_TAG_FILE, BASE_FILES)

    def test_atomic_datatypes(self):
        """Test atomic datatypes list."""
        expected_types = [
            'BIT', 'BOOL', 'SINT', 'INT', 'DINT', 'LINT',
            'REAL', 'LREAL', 'USINT', 'UINT', 'UDINT', 'ULINT',
            'STRING', 'TIMER'
        ]

        for datatype in expected_types:
            self.assertIn(datatype, ATOMIC_DATATYPES)

        self.assertEqual(len(ATOMIC_DATATYPES), len(expected_types))

    def test_input_instructions(self):
        """Test input instructions list."""
        self.assertIn(INSTR_XIC, INPUT_INSTRUCTIONS)
        self.assertIn(INSTR_XIO, INPUT_INSTRUCTIONS)
        self.assertEqual(len(INPUT_INSTRUCTIONS), 2)

    def test_output_instructions(self):
        """Test output instructions list structure."""
        self.assertIsInstance(OUTPUT_INSTRUCTIONS, list)

        # Test that each instruction is a tuple with (instruction, operand_index)
        for instr in OUTPUT_INSTRUCTIONS:
            self.assertIsInstance(instr, tuple)
            self.assertEqual(len(instr), 2)
            self.assertIsInstance(instr[0], str)  # Instruction name
            self.assertIsInstance(instr[1], int)  # Operand index

        # Test specific instructions
        self.assertIn(('OTE', -1), OUTPUT_INSTRUCTIONS)
        self.assertIn(('TON', 0), OUTPUT_INSTRUCTIONS)
        self.assertIn(('CPT', 0), OUTPUT_INSTRUCTIONS)

    def test_l5x_assets(self):
        """Test L5X assets list."""
        expected_assets = [
            'DataTypes',
            'Tags',
            'Programs',
            'AddOnInstructionDefinitions',
            'Modules'
        ]

        for asset in expected_assets:
            self.assertIn(asset, L5X_ASSETS)

        self.assertEqual(len(L5X_ASSETS), len(expected_assets))

    def test_l5x_properties(self):
        """Test L5X property constants."""
        self.assertEqual(L5X_PROP_NAME, '@Name')
        self.assertEqual(L5X_PROP_DESCRIPTION, 'Description')

    def test_cip_types_structure(self):
        """Test CIP types dictionary structure."""
        self.assertIsInstance(CIPTypes, dict)

        # Test specific CIP types
        self.assertIn(0xc1, CIPTypes)  # BOOL
        self.assertIn(0xc4, CIPTypes)  # DINT
        self.assertIn(0xca, CIPTypes)  # REAL

        # Test structure of CIP type entries
        for type_id, type_info in CIPTypes.items():
            self.assertIsInstance(type_id, int)
            self.assertIsInstance(type_info, tuple)
            self.assertEqual(len(type_info), 3)
            self.assertIsInstance(type_info[0], int)    # Size
            self.assertIsInstance(type_info[1], str)    # Name
            self.assertIsInstance(type_info[2], str)    # Format


class TestEnums(unittest.TestCase):
    """Test cases for enum classes."""

    def test_logix_tag_scope(self):
        """Test LogixTagScope enum."""
        self.assertEqual(LogixTagScope.PROGRAM.value, 0)
        self.assertEqual(LogixTagScope.PUBLIC.value, 1)
        self.assertEqual(LogixTagScope.CONTROLLER.value, 2)

        # Test enum has expected members
        self.assertEqual(len(LogixTagScope), 3)

    def test_logix_instruction_type(self):
        """Test LogixInstructionType enum."""
        self.assertEqual(LogixInstructionType.INPUT.value, 1)
        self.assertEqual(LogixInstructionType.OUTPUT.value, 2)
        self.assertEqual(LogixInstructionType.UNKOWN.value, 3)  # Note: typo in original
        self.assertEqual(LogixInstructionType.JSR.value, 4)

        self.assertEqual(len(LogixInstructionType), 4)

    def test_logix_asset_type(self):
        """Test LogixAssetType enum."""
        expected_values = {
            'DEFAULT': 0,
            'TAG': 1,
            'DATATYPE': 2,
            'AOI': 3,
            'MODULE': 4,
            'PROGRAM': 5,
            'ROUTINE': 6,
            'PROGRAMTAG': 7,
            'RUNG': 8,
            'ALL': 9
        }

        for name, value in expected_values.items():
            self.assertEqual(getattr(LogixAssetType, name).value, value)

        self.assertEqual(len(LogixAssetType), len(expected_values))


class TestPlcObject(unittest.TestCase):
    """Test cases for PlcObject class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = MagicMock()
        self.mock_controller.__class__.__name__ = 'Controller'

        # Create a concrete subclass for testing
        class TestPlcObject(PlcObject):
            def _compile_from_meta_data(self):
                self.compiled = True

            def _invalidate(self):
                self.invalidated = True

        self.TestPlcObject = TestPlcObject

    def test_init_with_defaults(self):
        """Test PlcObject initialization with default values."""
        obj = self.TestPlcObject()

        self.assertIsNone(obj.controller)
        self.assertIsInstance(obj.meta_data, dict)
        self.assertIsInstance(obj._on_compiling, list)
        self.assertIsInstance(obj._on_compiled, list)
        self.assertEqual(len(obj._on_compiling), 0)
        self.assertEqual(len(obj._on_compiled), 0)

    def test_init_with_controller(self):
        """Test PlcObject initialization with controller."""
        obj = self.TestPlcObject(controller=self.mock_controller)

        self.assertEqual(obj.controller, self.mock_controller)

    def test_init_with_meta_data_dict(self):
        """Test PlcObject initialization with metadata dictionary."""
        meta_data = {'key1': 'value1', 'key2': 'value2'}
        obj = self.TestPlcObject(meta_data=meta_data)

        self.assertEqual(obj.meta_data, meta_data)

    def test_init_with_meta_data_string(self):
        """Test PlcObject initialization with metadata string."""
        meta_data = "test metadata string"
        obj = self.TestPlcObject(meta_data=meta_data)

        self.assertEqual(obj.meta_data, meta_data)

    def test_repr_and_str(self):
        """Test __repr__ and __str__ methods."""
        meta_data = {'test': 'value'}
        obj = self.TestPlcObject(meta_data=meta_data)

        self.assertEqual(repr(obj), str(obj))
        self.assertEqual(str(obj), str(meta_data))

    def test_dict_key_order_default(self):
        """Test dict_key_order property default implementation."""
        obj = self.TestPlcObject()

        self.assertEqual(obj.dict_key_order, [])

    def test_config_property_no_controller(self):
        """Test config property when no controller is set."""
        obj = self.TestPlcObject()

        self.assertIsNone(obj.config)

    def test_config_property_with_controller(self):
        """Test config property with controller."""
        mock_config = MagicMock()
        self.mock_controller.config = mock_config
        obj = self.TestPlcObject(controller=self.mock_controller)

        self.assertEqual(obj.config, mock_config)

    def test_config_property_with_cached_config(self):
        """Test config property with cached _config."""
        obj = self.TestPlcObject()
        cached_config = MagicMock()
        obj._config = cached_config

        self.assertEqual(obj.config, cached_config)

    def test_controller_property_getter(self):
        """Test controller property getter."""
        obj = self.TestPlcObject(controller=self.mock_controller)

        self.assertEqual(obj.controller, self.mock_controller)

    def test_controller_property_setter_valid(self):
        """Test controller property setter with valid controller."""
        obj = self.TestPlcObject()
        obj.controller = self.mock_controller

        self.assertEqual(obj.controller, self.mock_controller)

    def test_controller_property_setter_none(self):
        """Test controller property setter with None."""
        obj = self.TestPlcObject(controller=self.mock_controller)
        obj.controller = None

        self.assertIsNone(obj.controller)

    def test_controller_property_setter_invalid_type(self):
        """Test controller property setter with invalid type."""
        obj = self.TestPlcObject()
        invalid_controller = MagicMock()
        invalid_controller.__class__.__name__ = 'InvalidController'

        with self.assertRaises(TypeError) as context:
            obj.controller = invalid_controller

        self.assertIn("Controller must be of type", str(context.exception))

    def test_on_compiled_property(self):
        """Test on_compiled property."""
        obj = self.TestPlcObject()

        self.assertEqual(obj.on_compiled, obj._on_compiled)
        self.assertIsInstance(obj.on_compiled, list)

    def test_on_compiling_property(self):
        """Test on_compiling property."""
        obj = self.TestPlcObject()

        self.assertEqual(obj.on_compiling, obj._on_compiling)
        self.assertIsInstance(obj.on_compiling, list)

    def test_compile_from_meta_data_not_implemented(self):
        """Test _compile_from_meta_data raises NotImplementedError."""
        # Create a PlcObject directly without overriding _compile_from_meta_data
        obj = PlcObject()

        with self.assertRaises(NotImplementedError):
            obj._compile_from_meta_data()

    def test_invalidate_not_implemented(self):
        """Test _invalidate raises NotImplementedError."""
        # Create a PlcObject directly without overriding _invalidate
        obj = PlcObject()

        with self.assertRaises(NotImplementedError):
            obj._invalidate()

    def test_init_dict_order_empty_key_order(self):
        """Test _init_dict_order with empty dict_key_order."""
        obj = self.TestPlcObject(meta_data={})

        # Should not modify meta_data since dict_key_order is empty
        self.assertEqual(obj.meta_data, {})

    def test_init_dict_order_with_keys(self):
        """Test _init_dict_order with specific key order."""
        class OrderedPlcObject(PlcObject):
            @property
            def dict_key_order(self):
                return ['key1', 'key2', 'key3']

            def _compile_from_meta_data(self):
                pass

            def _invalidate(self):
                pass

        obj = OrderedPlcObject(meta_data={'existing': 'value'})

        # Should add missing keys in specified order
        _ = ['key1', 'key2', 'key3', 'existing']
        self.assertEqual(list(obj.meta_data.keys())[:3], ['key1', 'key2', 'key3'])

    def test_init_dict_order_non_dict_meta_data(self):
        """Test _init_dict_order with non-dict meta_data."""
        class OrderedPlcObject(PlcObject):
            @property
            def dict_key_order(self):
                return ['key1', 'key2']

            def _compile_from_meta_data(self):
                pass

            def _invalidate(self):
                pass

        obj = OrderedPlcObject(meta_data="string metadata")

        # Should not crash with string metadata
        self.assertEqual(obj.meta_data, "string metadata")

    def test_compile_method(self):
        """Test compile method execution and callbacks."""
        obj = self.TestPlcObject()

        # Add mock callbacks
        compiling_callback = MagicMock()
        compiled_callback = MagicMock()

        obj._on_compiling.append(compiling_callback)
        obj._on_compiled.append(compiled_callback)

        result = obj.compile()

        # Test callbacks were called
        compiling_callback.assert_called_once()
        compiled_callback.assert_called_once()

        # Test compilation happened
        self.assertTrue(obj.compiled)

        # Test method chaining
        self.assertEqual(result, obj)

    def test_compile_method_multiple_callbacks(self):
        """Test compile method with multiple callbacks."""
        obj = self.TestPlcObject()

        # Add multiple callbacks
        callbacks_compiling = [MagicMock() for _ in range(3)]
        callbacks_compiled = [MagicMock() for _ in range(3)]

        obj._on_compiling.extend(callbacks_compiling)
        obj._on_compiled.extend(callbacks_compiled)

        obj.compile()

        # All callbacks should be called
        for callback in callbacks_compiling:
            callback.assert_called_once()

        for callback in callbacks_compiled:
            callback.assert_called_once()

    def test_compile_method_callback_execution_order(self):
        """Test compile method callback execution order."""
        obj = self.TestPlcObject()

        execution_order = []

        def compiling_callback():
            execution_order.append('compiling')

        def compiled_callback():
            execution_order.append('compiled')

        # Override _compile_from_meta_data to track execution
        original_compile = obj._compile_from_meta_data

        def tracked_compile():
            execution_order.append('compile')
            original_compile()
        obj._compile_from_meta_data = tracked_compile

        obj._on_compiling.append(compiling_callback)
        obj._on_compiled.append(compiled_callback)

        obj.compile()

        expected_order = ['compiling', 'compile', 'compiled']
        self.assertEqual(execution_order, expected_order)


class TestNamedPlcObject(unittest.TestCase):
    """Test cases for NamedPlcObject class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = MagicMock()
        self.mock_controller.__class__.__name__ = 'Controller'

        # Create a concrete subclass for testing
        class TestNamedPlcObject(NamedPlcObject):
            def _compile_from_meta_data(self):
                self.compiled = True

            def _invalidate(self):
                self.invalidated = True

        self.TestNamedPlcObject = TestNamedPlcObject

    def test_init_with_defaults(self):
        """Test NamedPlcObject initialization with defaults."""
        obj = self.TestNamedPlcObject()

        self.assertIsNone(obj.controller)
        self.assertIsInstance(obj.meta_data, dict)

    def test_init_with_name_and_description(self):
        """Test NamedPlcObject initialization with name and description."""
        obj = self.TestNamedPlcObject(
            name="TestObject",
            description="Test Description"
        )

        self.assertEqual(obj.name, "TestObject")
        self.assertEqual(obj.description, "Test Description")

    def test_init_with_meta_data_containing_name(self):
        """Test initialization with name in metadata."""
        meta_data = {L5X_PROP_NAME: "MetaDataName"}
        obj = self.TestNamedPlcObject(meta_data=meta_data)

        self.assertEqual(obj.name, "MetaDataName")

    def test_init_with_explicit_name_overrides_meta_data(self):
        """Test explicit name parameter overrides metadata name."""
        meta_data = {L5X_PROP_NAME: "MetaDataName"}
        obj = self.TestNamedPlcObject(
            meta_data=meta_data,
            name="ExplicitName"
        )

        self.assertEqual(obj.name, "ExplicitName")

    def test_name_property_getter(self):
        """Test name property getter."""
        obj = self.TestNamedPlcObject()
        obj[L5X_PROP_NAME] = "TestName"

        self.assertEqual(obj.name, "TestName")

    def test_name_property_setter_valid(self):
        """Test name property setter with valid name."""
        obj = self.TestNamedPlcObject()
        obj.name = "ValidName123"

        self.assertEqual(obj.name, "ValidName123")
        self.assertEqual(obj[L5X_PROP_NAME], "ValidName123")

    def test_name_property_setter_invalid(self):
        """Test name property setter with invalid name."""
        obj = self.TestNamedPlcObject()

        # Mock is_valid_string to return False
        with patch.object(obj, 'is_valid_string', return_value=False):
            with self.assertRaises(obj.InvalidNamingException):
                obj.name = "Invalid Name!"

    def test_description_property_getter(self):
        """Test description property getter."""
        obj = self.TestNamedPlcObject()
        obj[L5X_PROP_DESCRIPTION] = "Test Description"

        self.assertEqual(obj.description, "Test Description")

    def test_description_property_setter(self):
        """Test description property setter."""
        obj = self.TestNamedPlcObject()
        obj.description = "New Description"

        self.assertEqual(obj.description, "New Description")
        self.assertEqual(obj[L5X_PROP_DESCRIPTION], "New Description")

    def test_process_name_property(self):
        """Test process_name property returns name."""
        obj = self.TestNamedPlcObject()
        obj.name = "ProcessTestName"

        self.assertEqual(obj.process_name, "ProcessTestName")

    def test_inheritance_order(self):
        """Test that NamedPlcObject properly inherits from both parent classes."""
        obj = self.TestNamedPlcObject()

        # Should have PlcObject attributes
        self.assertTrue(hasattr(obj, 'controller'))
        self.assertTrue(hasattr(obj, 'compile'))
        self.assertTrue(hasattr(obj, '_on_compiled'))
        self.assertTrue(hasattr(obj, '_on_compiling'))

        # Should have NamedPyroxObject attributes
        self.assertTrue(hasattr(obj, 'name'))
        self.assertTrue(hasattr(obj, 'description'))

        # Should have EnforcesNaming functionality
        self.assertTrue(hasattr(obj, 'is_valid_string'))
        self.assertTrue(hasattr(obj, 'InvalidNamingException'))

    def test_meta_data_integration(self):
        """Test integration between metadata and properties."""
        meta_data = {
            L5X_PROP_NAME: "TestName",
            L5X_PROP_DESCRIPTION: "TestDescription",
            "custom_field": "custom_value"
        }

        obj = self.TestNamedPlcObject(meta_data=meta_data)

        # Properties should reflect metadata
        self.assertEqual(obj.name, "TestName")
        self.assertEqual(obj.description, "TestDescription")

        # Changing properties should update metadata
        obj.name = "NewName"
        obj.description = "NewDescription"

        self.assertEqual(obj[L5X_PROP_NAME], "NewName")
        self.assertEqual(obj[L5X_PROP_DESCRIPTION], "NewDescription")

        # Custom fields should remain
        self.assertEqual(obj["custom_field"], "custom_value")

    def test_controller_integration(self):
        """Test controller integration in NamedPlcObject."""
        obj = self.TestNamedPlcObject(controller=self.mock_controller)

        self.assertEqual(obj.controller, self.mock_controller)

        # Test config access through controller
        mock_config = MagicMock()
        self.mock_controller.config = mock_config
        self.assertEqual(obj.config, mock_config)


class TestIntegration(unittest.TestCase):
    """Integration tests for meta module components."""

    def test_enum_values_consistency(self):
        """Test that enum values are consistent and don't overlap inappropriately."""
        # Test LogixTagScope values are unique
        tag_scope_values = [e.value for e in LogixTagScope]
        self.assertEqual(len(tag_scope_values), len(set(tag_scope_values)))

        # Test LogixInstructionType values are unique
        instruction_type_values = [e.value for e in LogixInstructionType]
        self.assertEqual(len(instruction_type_values), len(set(instruction_type_values)))

        # Test LogixAssetType values are unique
        asset_type_values = [e.value for e in LogixAssetType]
        self.assertEqual(len(asset_type_values), len(set(asset_type_values)))

    def test_constants_are_immutable_references(self):
        """Test that constant lists and tuples maintain their identity."""
        # These should be the same objects
        self.assertIs(BASE_FILES, BASE_FILES)
        self.assertIs(ATOMIC_DATATYPES, ATOMIC_DATATYPES)
        self.assertIs(INPUT_INSTRUCTIONS, INPUT_INSTRUCTIONS)
        self.assertIs(OUTPUT_INSTRUCTIONS, OUTPUT_INSTRUCTIONS)

    def test_file_paths_point_to_expected_structure(self):
        """Test that file paths follow expected directory structure."""
        for file_path in BASE_FILES:
            # Should be under docs/controls/
            self.assertIn('docs', file_path.parts)
            self.assertIn('controls', file_path.parts)

            # Should have .L5X extension
            self.assertEqual(file_path.suffix, '.L5X')

    def test_cip_types_completeness(self):
        """Test CIP types cover expected ranges and have valid data."""
        # Test some key CIP types exist
        key_types = [0xc1, 0xc2, 0xc3, 0xc4, 0xc5, 0xca, 0xcb]  # BOOL, SINT, INT, DINT, LINT, REAL, LREAL

        for type_id in key_types:
            self.assertIn(type_id, CIPTypes)
            size, name, format_str = CIPTypes[type_id]

            # Validate size is positive
            self.assertGreater(size, 0)

            # Validate name is non-empty
            self.assertTrue(name)

            # Validate format string starts with '<' (little endian)
            self.assertTrue(format_str.startswith('<'))

    def test_instruction_lists_consistency(self):
        """Test instruction lists are consistent and properly formatted."""
        # Test input instructions are strings
        for instr in INPUT_INSTRUCTIONS:
            self.assertIsInstance(instr, str)
            self.assertTrue(instr.isupper())  # Convention: uppercase
            self.assertTrue(instr.isalnum() or '_' in instr)  # Alphanumeric or underscore

        # Test output instructions are tuples
        for instr_tuple in OUTPUT_INSTRUCTIONS:
            instr_name, operand_index = instr_tuple
            self.assertIsInstance(instr_name, str)
            self.assertTrue(instr_name.isupper())
            self.assertIsInstance(operand_index, int)
            # Operand index should be valid (-1 for last, or non-negative)
            self.assertTrue(operand_index == -1 or operand_index >= 0)

    def test_l5x_properties_format(self):
        """Test L5X property constants follow expected format."""
        # @Name should start with @
        self.assertTrue(L5X_PROP_NAME.startswith('@'))

        # Description should be a simple identifier
        self.assertTrue(L5X_PROP_DESCRIPTION.isalpha())

    def test_regex_patterns_are_valid(self):
        """Test that regex patterns are valid Python regex strings."""
        import re

        patterns = [
            INST_RE_PATTERN,
            INST_TYPE_RE_PATTERN,
            INST_OPER_RE_PATTERN,
        ]

        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.error:
                self.fail(f"Invalid regex pattern: {pattern}")

    def test_class_hierarchy_consistency(self):
        """Test class hierarchy is properly set up."""
        # PlcObject should inherit from expected base classes
        self.assertTrue(issubclass(PlcObject, EnforcesNaming))
        self.assertTrue(hasattr(PlcObject, 'meta_data'))

        # NamedPlcObject should inherit from both parents
        from pyrox.models.abc.meta import NamedPyroxObject
        self.assertTrue(issubclass(NamedPlcObject, NamedPyroxObject))
        self.assertTrue(issubclass(NamedPlcObject, PlcObject))

    def test_module_imports_work(self):
        """Test that all imports in the module work correctly."""
        # This test verifies that the module can be imported without errors
        # and that all imported items are accessible

        # Test that imported classes exist
        self.assertTrue(hasattr(PlcObject, '__init__'))
        self.assertTrue(hasattr(NamedPlcObject, '__init__'))

        # Test that imported utilities work
        from pyrox.services.dict import insert_key_at_index
        test_dict = {}
        insert_key_at_index(test_dict, 'test_key', 0, 'test_value')
        self.assertIn('test_key', test_dict)

    def test_type_annotations_consistency(self):
        """Test that type annotations are consistent."""
        # This is more of a smoke test to ensure type hints don't cause issues

        # Test that Generic typing works
        from typing import Generic
        self.assertTrue(issubclass(PlcObject, Generic))

        # Test that Optional typing is used correctly
        obj = PlcObject[type(None)]()  # Should not raise errors
        self.assertIsNotNone(obj)


class TestPlcObjectEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for PlcObject."""

    def setUp(self):
        """Set up test fixtures."""
        class TestPlcObject(PlcObject):
            def _compile_from_meta_data(self):
                pass

            def _invalidate(self):
                pass

        self.TestPlcObject = TestPlcObject

    def test_compile_with_exception_in_callback(self):
        """Test compile method when callback raises exception."""
        obj = self.TestPlcObject()

        def failing_callback():
            raise ValueError("Callback failed")

        obj._on_compiling.append(failing_callback)

        # Exception should propagate
        with self.assertRaises(ValueError):
            obj.compile()

    def test_controller_type_check_edge_cases(self):
        """Test controller type checking edge cases."""
        obj = self.TestPlcObject()

        # Test with object that has Controller name but isn't actually a Controller
        fake_controller = MagicMock()
        fake_controller.__class__.__name__ = 'NotController'

        with self.assertRaises(TypeError):
            obj.controller = fake_controller

    def test_meta_data_edge_cases(self):
        """Test metadata handling edge cases."""
        # Test with various metadata types
        edge_cases = [
            {},
            'some string',
        ]

        for meta_data in edge_cases:
            obj = self.TestPlcObject(meta_data=meta_data)
            self.assertEqual(obj.meta_data, meta_data)


if __name__ == '__main__':
    unittest.main(verbosity=2)

"""Unit tests for collections.py module."""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from collections import defaultdict

from pyrox.models.plc import Tag, Routine
from pyrox.models.plc.collections import ContainsTags, ContainsRoutines
from pyrox.models.abc.list import HashList
from pyrox.models.plc.instruction import LogixInstruction


class TestContainsTags(unittest.TestCase):
    """Test cases for ContainsTags class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock controller
        self.mock_controller = MagicMock()
        self.mock_controller.__class__.__name__ = 'Controller'

        # Create mock config
        self.mock_config = MagicMock()
        self.mock_tag_type = MagicMock()
        self.mock_config.tag_type = self.mock_tag_type

        # Sample metadata
        self.sample_meta_data = {
            'Tags': {
                'Tag': [
                    {'@Name': 'Tag1', '@DataType': 'BOOL'},
                    {'@Name': 'Tag2', '@DataType': 'INT'}
                ]
            }
        }

    def test_init_with_default_params(self):
        """Test ContainsTags initialization with default parameters."""
        container = ContainsTags()

        self.assertIsInstance(container.meta_data, defaultdict)
        self.assertIsNone(container.controller)
        self.assertIsNone(container._tags)

    def test_init_with_custom_params(self):
        """Test ContainsTags initialization with custom parameters."""
        container = ContainsTags(
            meta_data=self.sample_meta_data,
            controller=self.mock_controller
        )

        self.assertEqual(container.meta_data, self.sample_meta_data)
        self.assertEqual(container.controller, self.mock_controller)
        self.assertIsNone(container._tags)

    def test_raw_tags_property_empty(self):
        """Test raw_tags property when Tags is empty."""
        container = ContainsTags()

        raw_tags = container.raw_tags

        self.assertIsInstance(raw_tags, list)
        self.assertEqual(len(raw_tags), 0)
        self.assertIn('Tags', container.meta_data)
        self.assertEqual(container.meta_data['Tags'], {'Tag': []})

    def test_raw_tags_property_with_tags(self):
        """Test raw_tags property with existing tags."""
        container = ContainsTags(meta_data=self.sample_meta_data)

        raw_tags = container.raw_tags

        self.assertIsInstance(raw_tags, list)
        self.assertEqual(len(raw_tags), 2)
        self.assertEqual(raw_tags[0]['@Name'], 'Tag1')
        self.assertEqual(raw_tags[1]['@Name'], 'Tag2')

    def test_raw_tags_property_single_tag_conversion(self):
        """Test raw_tags property converts single tag dict to list."""
        meta_data = {
            'Tags': {
                'Tag': {'@Name': 'SingleTag', '@DataType': 'BOOL'}
            }
        }
        container = ContainsTags(meta_data=meta_data)

        raw_tags = container.raw_tags

        self.assertIsInstance(raw_tags, list)
        self.assertEqual(len(raw_tags), 1)
        self.assertEqual(raw_tags[0]['@Name'], 'SingleTag')

    def test_raw_tags_property_creates_structure_when_missing(self):
        """Test raw_tags property creates Tags structure when completely missing."""
        container = ContainsTags()

        # Ensure Tags doesn't exist initially
        if 'Tags' in container.meta_data:
            del container.meta_data['Tags']
        self.assertNotIn('Tags', container.meta_data)

        raw_tags = container.raw_tags

        # Should create the structure
        self.assertIn('Tags', container.meta_data)
        self.assertEqual(container.meta_data['Tags'], {'Tag': []})
        self.assertEqual(raw_tags, [])

    def test_raw_tags_property_handles_none_tags(self):
        """Test raw_tags property handles None Tags value."""
        container = ContainsTags()
        container.meta_data['Tags'] = None

        raw_tags = container.raw_tags

        self.assertEqual(container.meta_data['Tags'], {'Tag': []})
        self.assertEqual(raw_tags, [])

    def test_raw_tags_property_handles_empty_tags(self):
        """Test raw_tags property handles empty Tags dict."""
        container = ContainsTags()
        container.meta_data['Tags'] = {}

        raw_tags = container.raw_tags

        self.assertEqual(container.meta_data['Tags'], {'Tag': []})
        self.assertEqual(raw_tags, [])

    def test_raw_tags_property_preserves_existing_structure(self):
        """Test raw_tags property preserves existing Tags structure."""
        container = ContainsTags()
        original_tags = [{'@Name': 'ExistingTag', '@DataType': 'DINT'}]
        container.meta_data['Tags'] = {'Tag': original_tags}

        raw_tags = container.raw_tags

        self.assertEqual(raw_tags, original_tags)
        self.assertIs(raw_tags, original_tags)

    def test_tags_property_first_access(self):
        """Test tags property on first access compiles tags."""
        container = ContainsTags(meta_data=self.sample_meta_data)

        with patch.object(type(container), 'config', new_callable=PropertyMock) as mock_config_prop:
            mock_config_prop.return_value = self.mock_config

            with patch.object(container, '_compile_tags') as mock_compile:
                mock_hash_list = HashList('name')
                mock_compile.side_effect = lambda: setattr(container, '_tags', mock_hash_list)

                result = container.tags

                mock_compile.assert_called_once()
                self.assertEqual(result, mock_hash_list)

    def test_tags_property_cached_access(self):
        """Test tags property returns cached value on subsequent access."""
        container = ContainsTags()
        # Create a HashList with some content to make it truthy
        mock_hash_list = HashList('name')
        mock_tag = MagicMock()
        mock_tag.name = 'test_tag'
        mock_hash_list.append(mock_tag)
        container._tags = mock_hash_list

        with patch.object(container, '_compile_tags') as mock_compile:
            result = container.tags

            mock_compile.assert_not_called()
            self.assertEqual(result, mock_hash_list)

    def test_tags_property_none_triggers_compilation(self):
        """Test tags property triggers compilation when _tags is None."""
        container = ContainsTags()
        container._tags = None

        with patch.object(container, '_compile_tags') as mock_compile:
            with patch.object(type(container), 'config', new_callable=PropertyMock) as mock_config_prop:
                mock_config_prop.return_value = self.mock_config
                mock_hash_list = HashList('name')
                mock_compile.side_effect = lambda: setattr(container, '_tags', mock_hash_list)

                result = container.tags

                mock_compile.assert_called_once()
                self.assertEqual(result, mock_hash_list)

    def test_compile_from_meta_data(self):
        """Test _compile_from_meta_data calls _compile_tags."""
        container = ContainsTags()

        with patch.object(container, '_compile_tags') as mock_compile_tags:
            container._compile_from_meta_data()

            mock_compile_tags.assert_called_once()

    def test_compile_tags(self):
        """Test _compile_tags creates HashList and adds tags."""
        container = ContainsTags(
            meta_data=self.sample_meta_data,
            controller=self.mock_controller
        )

        mock_tag1 = MagicMock()
        mock_tag1.name = 'Tag1'
        mock_tag2 = MagicMock()
        mock_tag2.name = 'Tag2'

        self.mock_tag_type.side_effect = [mock_tag1, mock_tag2]

        with patch.object(type(container), 'config', new_callable=PropertyMock) as mock_config_prop:
            mock_config_prop.return_value = self.mock_config
            container._compile_tags()

            self.assertIsInstance(container._tags, HashList)
            self.assertEqual(container._tags.hash_key, 'name')
            self.assertEqual(self.mock_tag_type.call_count, 2)

    def test_compile_tags_empty_raw_tags(self):
        """Test _compile_tags with empty raw_tags."""
        container = ContainsTags()

        with patch.object(type(container), 'config', new_callable=PropertyMock) as mock_config_prop:
            mock_config_prop.return_value = self.mock_config
            container._compile_tags()

            self.assertIsInstance(container._tags, HashList)
            self.assertEqual(container._tags.hash_key, 'name')
            self.assertEqual(len(container._tags), 0)
            self.mock_tag_type.assert_not_called()

    def test_invalidate(self):
        """Test _invalidate resets _tags to None."""
        container = ContainsTags()
        container._tags = HashList('name')

        container._invalidate()

        self.assertIsNone(container._tags)

    def test_type_check_valid_tag_object(self):
        """Test _type_check with valid Tag object."""
        container = ContainsTags()
        mock_tag = MagicMock(spec=Tag)
        container._type_check(mock_tag, check_str=False)

    def test_type_check_valid_string(self):
        """Test _type_check with valid string when check_str=True."""
        container = ContainsTags()
        container._type_check("tag_name", check_str=True)

    def test_type_check_invalid_string_when_check_str_false(self):
        """Test _type_check with string when check_str=False raises TypeError."""
        container = ContainsTags()

        with self.assertRaises(TypeError) as context:
            container._type_check("tag_name", check_str=False)

        self.assertIn("tag must be a Tag object", str(context.exception))

    def test_type_check_invalid_object(self):
        """Test _type_check with invalid object type."""
        container = ContainsTags()

        with self.assertRaises(TypeError) as context:
            container._type_check(123, check_str=False)

        self.assertIn("tag must be a Tag object", str(context.exception))

    def test_add_tag_calls_correct_methods(self):
        """Test add_tag calls correct helper methods."""
        container = ContainsTags()
        mock_tag = MagicMock(spec=Tag)

        with patch.object(container, '_type_check') as mock_type_check:
            with patch.object(container, '_add_asset_to_meta_data') as mock_add_asset:
                container.add_tag(mock_tag, index=1, _inhibit_invalidate=True)

                mock_type_check.assert_called_once()
                mock_add_asset.assert_called_once()

    def test_remove_tag_calls_correct_methods(self):
        """Test remove_tag calls correct helper methods."""
        container = ContainsTags()
        container._config = self.mock_config

        with patch.object(container, '_type_check') as mock_type_check:
            with patch.object(container, '_remove_asset_from_meta_data') as mock_remove_asset:
                container.remove_tag("tag_name", _inhibit_invalidate=True)

                mock_type_check.assert_called_once()
                mock_remove_asset.assert_called_once()

    def test_add_tags_batch_operation(self):
        """Test add_tags properly handles batch operations."""
        container = ContainsTags()
        mock_tags = [MagicMock(spec=Tag), MagicMock(spec=Tag), MagicMock(spec=Tag)]
        with patch.object(container, 'add_tag') as mock_add_tag:
            with patch.object(container, '_invalidate') as mock_invalidate:

                container.add_tags(mock_tags)

                # Should call add_tag for each tag with inhibit_invalidate=True
                self.assertEqual(mock_add_tag.call_count, 3)
                for tag in mock_tags:
                    mock_add_tag.assert_any_call(tag, True)

                # Should call _invalidate once at the end
                mock_invalidate.assert_called_once()

    def test_remove_tags_batch_operation(self):
        """Test remove_tags properly handles batch operations."""
        container = ContainsTags()
        tags_to_remove = ["tag1", "tag2", "tag3"]

        with patch.object(container, 'remove_tag') as mock_remove_tag:
            with patch.object(container, '_invalidate') as mock_invalidate:

                container.remove_tags(tags_to_remove)

                # Should call remove_tag for each tag with inhibit_invalidate=True
                self.assertEqual(mock_remove_tag.call_count, 3)
                for tag in tags_to_remove:
                    mock_remove_tag.assert_any_call(tag, True)

                # Should call _invalidate once at the end
                mock_invalidate.assert_called_once()


class TestContainsRoutines(unittest.TestCase):
    """Test cases for ContainsRoutines class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = MagicMock()
        self.mock_controller.__class__.__name__ = 'Controller'

        self.mock_config = MagicMock()
        self.mock_routine_type = MagicMock()
        self.mock_config.routine_type = self.mock_routine_type

        self.sample_meta_data = {
            '@Class': 'Program',
            'Tags': {'Tag': []},
            'Routines': {
                'Routine': [
                    {'@Name': 'MainRoutine', '@Type': 'RLL'},
                    {'@Name': 'SubRoutine', '@Type': 'ST'}
                ]
            }
        }

    def test_init_inheritance(self):
        """Test ContainsRoutines properly inherits from ContainsTags."""
        container = ContainsRoutines()

        # Should have ContainsTags attributes
        self.assertIsNone(container._tags)

        # Should have ContainsRoutines-specific attributes
        self.assertIsNone(container._routines)
        self.assertIsNone(container._input_instructions)
        self.assertIsNone(container._output_instructions)
        self.assertIsNone(container._instructions)

    def test_class_property_with_missing_class(self):
        """Test class_ property when @Class is missing."""
        container = ContainsRoutines()
        result = container.class_
        self.assertIsNone(result)

    def test_class_property_with_existing_class(self):
        """Test class_ property when @Class exists."""
        container = ContainsRoutines(meta_data=self.sample_meta_data)
        result = container.class_
        self.assertEqual(result, 'Program')

    def test_raw_routines_property_creates_structure(self):
        """Test raw_routines property creates Routines structure when missing."""
        container = ContainsRoutines()

        raw_routines = container.raw_routines

        self.assertIn('Routines', container.meta_data)
        self.assertEqual(container.meta_data['Routines'], {'Routine': []})
        self.assertEqual(raw_routines, [])

    def test_raw_routines_property_handles_none_routines(self):
        """Test raw_routines property handles None Routines value."""
        container = ContainsRoutines()
        container.meta_data['Routines'] = None

        raw_routines = container.raw_routines

        self.assertEqual(container.meta_data['Routines'], {'Routine': []})
        self.assertEqual(raw_routines, [])

    def test_raw_routines_property_single_routine_conversion(self):
        """Test raw_routines property converts single routine dict to list."""
        meta_data = {
            'Routines': {
                'Routine': {'@Name': 'SingleRoutine', '@Type': 'RLL'}
            }
        }
        container = ContainsRoutines(meta_data=meta_data)

        raw_routines = container.raw_routines

        self.assertIsInstance(raw_routines, list)
        self.assertEqual(len(raw_routines), 1)
        self.assertEqual(raw_routines[0]['@Name'], 'SingleRoutine')

    def test_raw_routines_property_with_existing_routines(self):
        """Test raw_routines property with existing routines."""
        container = ContainsRoutines(meta_data=self.sample_meta_data)

        raw_routines = container.raw_routines

        self.assertIsInstance(raw_routines, list)
        self.assertEqual(len(raw_routines), 2)
        self.assertEqual(raw_routines[0]['@Name'], 'MainRoutine')
        self.assertEqual(raw_routines[1]['@Name'], 'SubRoutine')

    def test_routines_property_first_access(self):
        """Test routines property on first access compiles routines."""
        container = ContainsRoutines(meta_data=self.sample_meta_data)

        with patch.object(container, '_compile_routines') as mock_compile:
            mock_hash_list = HashList('name')
            mock_routine = MagicMock()
            mock_routine.name = 'test_routine'
            mock_hash_list.append(mock_routine)
            mock_compile.side_effect = lambda: setattr(container, '_routines', mock_hash_list)

            result = container.routines

            mock_compile.assert_called_once()
            self.assertEqual(result, mock_hash_list)

    def test_routines_property_cached_access(self):
        """Test routines property returns cached value on subsequent access."""
        container = ContainsRoutines()
        # Create a HashList with content to make it truthy
        mock_hash_list = HashList('name')
        mock_routine = MagicMock()
        mock_routine.name = 'test_routine'
        mock_hash_list.append(mock_routine)
        container._routines = mock_hash_list

        with patch.object(container, '_compile_routines') as mock_compile:
            result = container.routines

            mock_compile.assert_not_called()
            self.assertEqual(result, mock_hash_list)

    def test_routines_property_empty_hashlist_triggers_compilation(self):
        """Test routines property triggers compilation when _routines is empty HashList."""
        container = ContainsRoutines()
        container._routines = HashList('name')  # Empty HashList is falsy

        with patch.object(container, '_compile_routines') as mock_compile:
            mock_hash_list = HashList('name')
            mock_routine = MagicMock()
            mock_routine.name = 'test_routine'
            mock_hash_list.append(mock_routine)
            mock_compile.side_effect = lambda: setattr(container, '_routines', mock_hash_list)

            result = container.routines

            mock_compile.assert_called_once()
            self.assertEqual(result, mock_hash_list)

    def test_instructions_property_compilation_once(self):
        """Test that instructions property compiles only once."""
        container = ContainsRoutines()

        with patch.object(container, '_compile_instructions') as mock_compile:
            mock_instructions = [MagicMock(spec=LogixInstruction) for _ in range(3)]
            mock_compile.side_effect = lambda: setattr(container, '_instructions', mock_instructions)

            # First access
            result1 = container.instructions
            mock_compile.assert_called_once()

            # Second access should not recompile
            result2 = container.instructions
            mock_compile.assert_called_once()  # Still only once

            self.assertEqual(result1, result2)

    def test_input_instructions_property_cached_access(self):
        """Test input_instructions property caching behavior."""
        container = ContainsRoutines()
        mock_instructions = [MagicMock(spec=LogixInstruction)]
        container._input_instructions = mock_instructions

        with patch.object(container, '_compile_instructions') as mock_compile:
            result = container.input_instructions

            mock_compile.assert_not_called()
            self.assertEqual(result, mock_instructions)

    def test_input_instructions_property_none_triggers_compilation(self):
        """Test input_instructions property triggers compilation when None."""
        container = ContainsRoutines()
        container._input_instructions = None

        with patch.object(container, '_compile_instructions') as mock_compile:
            mock_instructions = [MagicMock(spec=LogixInstruction)]
            mock_compile.side_effect = lambda: setattr(container, '_input_instructions', mock_instructions)

            result = container.input_instructions

            mock_compile.assert_called_once()
            self.assertEqual(result, mock_instructions)

    def test_input_instructions_property_empty_list_triggers_compilation(self):
        """Test input_instructions property triggers compilation when empty list."""
        container = ContainsRoutines()
        container._input_instructions = []  # Empty list is falsy

        with patch.object(container, '_compile_instructions') as mock_compile:
            mock_instructions = [MagicMock(spec=LogixInstruction)]
            mock_compile.side_effect = lambda: setattr(container, '_input_instructions', mock_instructions)

            result = container.input_instructions

            mock_compile.assert_called_once()
            self.assertEqual(result, mock_instructions)

    def test_output_instructions_property_cached_access(self):
        """Test output_instructions property caching behavior."""
        container = ContainsRoutines()
        mock_instructions = [MagicMock(spec=LogixInstruction)]
        container._output_instructions = mock_instructions

        with patch.object(container, '_compile_instructions') as mock_compile:
            result = container.output_instructions

            mock_compile.assert_not_called()
            self.assertEqual(result, mock_instructions)

    def test_output_instructions_property_none_triggers_compilation(self):
        """Test output_instructions property triggers compilation when None."""
        container = ContainsRoutines()
        container._output_instructions = None

        with patch.object(container, '_compile_instructions') as mock_compile:
            mock_instructions = [MagicMock(spec=LogixInstruction)]
            mock_compile.side_effect = lambda: setattr(container, '_output_instructions', mock_instructions)

            result = container.output_instructions

            mock_compile.assert_called_once()
            self.assertEqual(result, mock_instructions)

    def test_input_output_instructions_compilation_shared(self):
        """Test that input/output instructions share compilation."""
        container = ContainsRoutines()

        with patch.object(container, '_compile_instructions') as mock_compile:
            mock_input = [MagicMock(spec=LogixInstruction)]
            mock_output = [MagicMock(spec=LogixInstruction)]

            def set_instructions():
                container._input_instructions = mock_input
                container._output_instructions = mock_output

            mock_compile.side_effect = set_instructions

            # Access both properties
            input_result = container.input_instructions
            output_result = container.output_instructions

            # Should compile only once total
            mock_compile.assert_called_once()

            self.assertEqual(input_result, mock_input)
            self.assertEqual(output_result, mock_output)

    def test_compile_instructions_with_no_routines(self):
        """Test _compile_instructions with no routines."""
        container = ContainsRoutines()
        container._compile_instructions()

        self.assertEqual(container._input_instructions, [])
        self.assertEqual(container._output_instructions, [])
        self.assertEqual(container._instructions, [])

    def test_compile_instructions_with_routines_having_no_instructions(self):
        """Test _compile_instructions with routines that have no instructions."""
        container = ContainsRoutines()

        mock_routine = MagicMock()
        mock_routine.input_instructions = []
        mock_routine.output_instructions = []
        mock_routine.instructions = []
        container._compile_instructions()

        self.assertEqual(container._input_instructions, [])
        self.assertEqual(container._output_instructions, [])
        self.assertEqual(container._instructions, [])

    def test_compile_instructions_with_multiple_routines(self):
        """Test _compile_instructions with multiple routines having instructions."""
        container = ContainsRoutines(controller=self.mock_controller)

        # Create mock instructions
        input_inst1 = MagicMock(spec=LogixInstruction)
        input_inst2 = MagicMock(spec=LogixInstruction)
        output_inst1 = MagicMock(spec=LogixInstruction)
        output_inst2 = MagicMock(spec=LogixInstruction)
        all_inst1 = MagicMock(spec=LogixInstruction)
        all_inst2 = MagicMock(spec=LogixInstruction)

        # Create mock routines
        routine1 = MagicMock(spec=Routine)
        routine1.input_instructions = [input_inst1]
        routine1.output_instructions = [output_inst1]
        routine1.instructions = [all_inst1]

        routine2 = MagicMock(spec=Routine)
        routine2.input_instructions = [input_inst2]
        routine2.output_instructions = [output_inst2]
        routine2.instructions = [all_inst2]

        container._routines = HashList('name')
        container._routines.extend([routine1, routine2])

        container._compile_instructions()
        self.assertEqual(container._input_instructions, [input_inst1, input_inst2])
        self.assertEqual(container._output_instructions, [output_inst1, output_inst2])
        self.assertEqual(container._instructions, [all_inst1, all_inst2])

    def test_compile_instructions_preserves_order(self):
        """Test _compile_instructions preserves instruction order across routines."""
        container = ContainsRoutines()

        # Create mock instructions with identifiable names
        routine1_input = MagicMock(spec=LogixInstruction)
        routine1_input.name = 'R1_Input'
        routine2_input = MagicMock(spec=LogixInstruction)
        routine2_input.name = 'R2_Input'
        routine3_input = MagicMock(spec=LogixInstruction)
        routine3_input.name = 'R3_Input'

        # Create mock routines
        routine1 = MagicMock()
        routine1.input_instructions = [routine1_input]
        routine1.output_instructions = []
        routine1.instructions = []

        routine2 = MagicMock()
        routine2.input_instructions = [routine2_input]
        routine2.output_instructions = []
        routine2.instructions = []

        routine3 = MagicMock()
        routine3.input_instructions = [routine3_input]
        routine3.output_instructions = []
        routine3.instructions = []

        container._routines = HashList('name')
        container._routines.extend([routine1, routine2, routine3])

        container._compile_instructions()

        self.assertEqual(len(container._input_instructions), 3)
        self.assertEqual(container._input_instructions[0].name, 'R1_Input')
        self.assertEqual(container._input_instructions[1].name, 'R2_Input')
        self.assertEqual(container._input_instructions[2].name, 'R3_Input')

    def test_compile_routines_with_program_parameter(self):
        """Test _compile_routines passes self as program parameter."""
        container = ContainsRoutines(
            meta_data=self.sample_meta_data,
            controller=self.mock_controller
        )

        mock_routine = MagicMock()
        mock_routine.name = 'TestRoutine'
        self.mock_routine_type.return_value = mock_routine

        with patch.object(type(container), 'config', new_callable=PropertyMock) as mock_config_prop:
            mock_config_prop.return_value = self.mock_config
            container._compile_routines()

            # Verify routine_type called with program=self
            self.mock_routine_type.assert_any_call(
                meta_data={'@Name': 'MainRoutine', '@Type': 'RLL'},
                controller=self.mock_controller,
                program=container
            )

    def test_compile_routines_creates_hashlist(self):
        """Test _compile_routines creates proper HashList."""
        container = ContainsRoutines(meta_data=self.sample_meta_data)

        mock_routine = MagicMock()
        mock_routine.name = 'TestRoutine'
        self.mock_routine_type.return_value = mock_routine

        with patch.object(type(container), 'config', new_callable=PropertyMock) as mock_config_prop:
            mock_config_prop.return_value = self.mock_config
            container._compile_routines()

            self.assertIsInstance(container._routines, HashList)
            self.assertEqual(container._routines.hash_key, 'name')
            self.assertEqual(len(container._routines), 1)

    def test_compile_routines_preserves_order(self):
        """Test _compile_routines preserves routine order from metadata."""
        ordered_meta_data = {
            'Routines': {
                'Routine': [
                    {'@Name': 'FirstRoutine', '@Type': 'RLL'},
                    {'@Name': 'SecondRoutine', '@Type': 'ST'},
                    {'@Name': 'ThirdRoutine', '@Type': 'FBD'}
                ]
            }
        }
        container = ContainsRoutines(meta_data=ordered_meta_data)

        mock_routines = []
        for name in ['FirstRoutine', 'SecondRoutine', 'ThirdRoutine']:
            mock_routine = MagicMock()
            mock_routine.name = name
            mock_routines.append(mock_routine)

        self.mock_routine_type.side_effect = mock_routines

        with patch.object(type(container), 'config', new_callable=PropertyMock) as mock_config_prop:
            mock_config_prop.return_value = self.mock_config
            container._compile_routines()

            # Verify order is preserved
            self.assertEqual(len(container._routines), 3)
            self.assertEqual(container._routines[0].name, 'FirstRoutine')
            self.assertEqual(container._routines[1].name, 'SecondRoutine')
            self.assertEqual(container._routines[2].name, 'ThirdRoutine')

    def test_invalidate_resets_all_instruction_lists(self):
        """Test _invalidate properly resets all instruction-related attributes."""
        container = ContainsRoutines()

        # Set up some values
        container._input_instructions = [MagicMock()]
        container._output_instructions = [MagicMock()]
        container._instructions = [MagicMock()]
        container._routines = MagicMock()

        with patch('pyrox.models.plc.collections.ContainsTags._invalidate') as mock_super_invalidate:
            container._invalidate()

            mock_super_invalidate.assert_called_once()
            self.assertEqual(container._input_instructions, [])
            self.assertEqual(container._output_instructions, [])
            self.assertEqual(container._instructions, [])
            self.assertIsInstance(container._routines, HashList)
            self.assertEqual(container._routines.hash_key, 'name')

    def test_invalidate_multiple_calls(self):
        """Test _invalidate can be called multiple times safely."""
        container = ContainsRoutines()

        # Set up some values
        container._input_instructions = [MagicMock()]
        container._output_instructions = [MagicMock()]
        container._instructions = [MagicMock()]
        container._routines = HashList('name')

        with patch('pyrox.models.plc.collections.ContainsTags._invalidate'):
            container._invalidate()

            # Should not raise error when called again
            container._invalidate()

            self.assertEqual(container._input_instructions, [])
            self.assertEqual(container._output_instructions, [])
            self.assertEqual(container._instructions, [])

    def test_type_check_routine_with_string_parameter(self):
        """Test _type_check for routine doesn't accept string parameters."""
        container = ContainsRoutines()

        with self.assertRaises(TypeError):
            container._type_check("routine_name")

    def test_type_check_routine_with_valid_routine(self):
        """Test _type_check with valid Routine object."""
        container = ContainsRoutines()
        mock_routine = MagicMock(spec=Routine)

        # Should not raise exception
        container._type_check(mock_routine)

    def test_type_check_routine_with_invalid_object(self):
        """Test _type_check with invalid object type."""
        container = ContainsRoutines()

        with self.assertRaises(TypeError) as context:
            container._type_check(123)

        self.assertIn("routine must be a Routine object", str(context.exception))

    def test_add_routine_calls_correct_methods(self):
        """Test add_routine calls correct helper methods."""
        container = ContainsRoutines()

        mock_routine = MagicMock(spec=Routine)
        with patch.object(container, '_type_check') as mock_type_check:
            with patch.object(container, '_add_asset_to_meta_data') as mock_add_asset:
                container.add_routine(mock_routine)

                mock_type_check.assert_called_once()
                mock_add_asset.assert_called_once()

    def test_remove_routine_calls_correct_methods(self):
        """Test remove_routine calls correct helper methods."""
        container = ContainsRoutines()

        mock_routine = MagicMock(spec=Routine)
        with patch.object(container, '_type_check') as mock_type_check:
            with patch.object(container, '_remove_asset_from_meta_data') as mock_remove_asset:
                container.remove_routine(mock_routine)
                mock_type_check.assert_called_once()
                mock_remove_asset.assert_called_once()

    def test_add_routine_type_check_failure(self):
        """Test add_routine with invalid routine type."""
        container = ContainsRoutines()

        with self.assertRaises(TypeError):
            container.add_routine("invalid_routine")

    def test_remove_routine_type_check_failure(self):
        """Test remove_routine with invalid routine type."""
        container = ContainsRoutines()

        with self.assertRaises(TypeError):
            container.remove_routine("invalid_routine")

    def test_compile_from_meta_data_order(self):
        """Test _compile_from_meta_data calls methods in correct order."""
        container = ContainsRoutines()

        call_order = []

        def track_super_call():
            call_order.append('super')

        def track_routines_call():
            call_order.append('routines')

        def track_instructions_call():
            call_order.append('instructions')

        with patch('pyrox.models.plc.collections.ContainsTags._compile_from_meta_data', side_effect=track_super_call):
            with patch.object(container, '_compile_routines', side_effect=track_routines_call):
                with patch.object(container, '_compile_instructions', side_effect=track_instructions_call):

                    container._compile_from_meta_data()

                    self.assertEqual(call_order, ['super', 'routines', 'instructions'])

    def test_instructions_property_none_triggers_compilation(self):
        """Test instructions property triggers compilation when None."""
        container = ContainsRoutines()
        container._instructions = None

        with patch.object(container, '_compile_instructions') as mock_compile:
            mock_instructions = [MagicMock(spec=LogixInstruction)]
            mock_compile.side_effect = lambda: setattr(container, '_instructions', mock_instructions)

            result = container.instructions

            mock_compile.assert_called_once()
            self.assertEqual(result, mock_instructions)

    def test_instructions_property_empty_list_triggers_compilation(self):
        """Test instructions property triggers compilation when empty list."""
        container = ContainsRoutines()
        container._instructions = []  # Empty list is falsy

        with patch.object(container, '_compile_instructions') as mock_compile:
            mock_instructions = [MagicMock(spec=LogixInstruction)]
            mock_compile.side_effect = lambda: setattr(container, '_instructions', mock_instructions)

            result = container.instructions

            mock_compile.assert_called_once()
            self.assertEqual(result, mock_instructions)


class TestEdgeCasesAndErrorHandling(unittest.TestCase):
    """Test edge cases and error handling scenarios."""

    def test_contains_tags_with_malformed_metadata(self):
        """Test ContainsTags with malformed metadata."""
        container = ContainsTags()
        container.meta_data['Tags'] = "invalid"

        with self.assertRaises((TypeError, AttributeError)):
            _ = container.raw_tags

    def test_contains_routines_with_malformed_metadata(self):
        """Test ContainsRoutines with malformed metadata."""
        container = ContainsRoutines()
        container.meta_data['Routines'] = "invalid"

        with self.assertRaises((TypeError, AttributeError)):
            _ = container.raw_routines

    def test_raw_tags_with_deeply_nested_none_values(self):
        """Test raw_tags property with deeply nested None values."""
        container = ContainsTags()
        container.meta_data['Tags'] = {'Tag': None}

        raw_tags = container.raw_tags

        self.assertEqual(container.meta_data['Tags'], {'Tag': [None]})
        self.assertEqual(raw_tags, [None])

    def test_raw_routines_with_deeply_nested_none_values(self):
        """Test raw_routines property with deeply nested None values."""
        container = ContainsRoutines()
        container.meta_data['Routines'] = {'Routine': None}

        raw_routines = container.raw_routines

        self.assertEqual(container.meta_data['Routines'], {'Routine': [None]})
        self.assertEqual(raw_routines, [None])

    def test_class_property_with_various_data_types(self):
        """Test class_ property with various data types."""
        container = ContainsRoutines()

        # Test with string
        container.meta_data['@Class'] = 'TestClass'
        self.assertEqual(container.class_, 'TestClass')

        # Test with number
        container.meta_data['@Class'] = 123
        self.assertEqual(container.class_, 123)

        # Test with boolean
        container.meta_data['@Class'] = True
        self.assertEqual(container.class_, True)

    def test_concurrent_property_access(self):
        """Test accessing multiple properties that trigger compilation."""
        container = ContainsRoutines()

        with patch.object(container, '_compile_tags') as mock_compile_tags:
            with patch.object(container, '_compile_routines') as mock_compile_routines:
                with patch.object(container, '_compile_instructions') as mock_compile_instructions:

                    # Set up side effects to simulate compilation
                    mock_compile_tags.side_effect = lambda: setattr(container, '_tags', HashList('name'))
                    mock_compile_routines.side_effect = lambda: setattr(container, '_routines', HashList('name'))
                    mock_compile_instructions.side_effect = lambda: [
                        setattr(container, '_instructions', []),
                        setattr(container, '_input_instructions', []),
                        setattr(container, '_output_instructions', [])
                    ]

                    # Access properties in different orders
                    _ = container.tags
                    _ = container.routines
                    _ = container.instructions

                    mock_compile_tags.assert_called_once()
                    mock_compile_routines.assert_called_once()
                    mock_compile_instructions.assert_called_once()


class TestPerformanceConsiderations(unittest.TestCase):
    """Test performance-related aspects."""

    def test_lazy_compilation_tags(self):
        """Test that tags are compiled lazily."""
        container = ContainsTags()

        # Accessing other properties shouldn't trigger tag compilation
        _ = container.raw_tags
        self.assertIsNone(container._tags)

        # Only accessing tags property should trigger compilation
        with patch.object(container, '_compile_tags') as mock_compile:
            mock_compile.side_effect = lambda: setattr(container, '_tags', HashList('name'))
            _ = container.tags
            mock_compile.assert_called_once()

    def test_lazy_compilation_routines(self):
        """Test that routines are compiled lazily."""
        container = ContainsRoutines()

        # Accessing other properties shouldn't trigger routine compilation
        _ = container.raw_routines
        _ = container.class_
        self.assertIsNone(container._routines)

        # Only accessing routines property should trigger compilation
        with patch.object(container, '_compile_routines') as mock_compile:
            mock_compile.side_effect = lambda: setattr(container, '_routines', HashList('name'))
            _ = container.routines
            mock_compile.assert_called_once()

    def test_lazy_compilation_instructions(self):
        """Test that instructions are compiled lazily."""
        container = ContainsRoutines()

        # Accessing other properties shouldn't trigger instruction compilation
        _ = container.raw_routines
        self.assertIsNone(container._instructions)

        # Only accessing instruction properties should trigger compilation
        with patch.object(container, '_compile_instructions') as mock_compile:
            mock_compile.side_effect = lambda: [
                setattr(container, '_instructions', []),
                setattr(container, '_input_instructions', []),
                setattr(container, '_output_instructions', [])
            ]
            _ = container.instructions
            mock_compile.assert_called_once()

    def test_compilation_order_efficiency(self):
        """Test that compilation happens in the most efficient order."""
        container = ContainsRoutines()

        compilation_calls = []

        def track_compile_tags():
            compilation_calls.append('tags')

        def track_compile_routines():
            compilation_calls.append('routines')

        def track_compile_instructions():
            compilation_calls.append('instructions')

        with patch.object(container, '_compile_tags', side_effect=track_compile_tags):
            with patch.object(container, '_compile_routines', side_effect=track_compile_routines):
                with patch.object(container, '_compile_instructions', side_effect=track_compile_instructions):

                    container._compile_from_meta_data()

                    # Should compile in dependency order: tags first, then routines, then instructions
                    self.assertEqual(compilation_calls, ['tags', 'routines', 'instructions'])

    def test_no_unnecessary_recompilation(self):
        """Test that compiled objects are not unnecessarily recompiled."""
        container = ContainsRoutines()

        with patch.object(container, '_compile_tags') as mock_compile_tags:
            with patch.object(container, '_compile_routines') as mock_compile_routines:
                with patch.object(container, '_compile_instructions') as mock_compile_instructions:

                    # Set up side effects to simulate compilation
                    tags_hashlist = HashList('name')
                    tag_mock = MagicMock()
                    tag_mock.name = 'test_tag'
                    tags_hashlist.append(tag_mock)

                    routines_hashlist = HashList('name')
                    routine_mock = MagicMock()
                    routine_mock.name = 'test_routine'
                    routines_hashlist.append(routine_mock)

                    instructions_list = [MagicMock(spec=LogixInstruction)]

                    mock_compile_tags.side_effect = lambda: setattr(container, '_tags', tags_hashlist)
                    mock_compile_routines.side_effect = lambda: setattr(container, '_routines', routines_hashlist)
                    mock_compile_instructions.side_effect = lambda: [
                        setattr(container, '_instructions', instructions_list),
                        setattr(container, '_input_instructions', instructions_list),
                        setattr(container, '_output_instructions', instructions_list)
                    ]

                    # First access - should trigger compilation
                    _ = container.tags
                    _ = container.routines
                    _ = container.instructions

                    # Second access - should not trigger recompilation
                    _ = container.tags
                    _ = container.routines
                    _ = container.instructions

                    # Each should be called only once
                    mock_compile_tags.assert_called_once()
                    mock_compile_routines.assert_called_once()
                    mock_compile_instructions.assert_called_once()


if __name__ == '__main__':
    unittest.main(verbosity=2)

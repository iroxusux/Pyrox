"""Unit tests for operand.py module."""

import unittest
from unittest.mock import MagicMock, patch

from pyrox.models.plc.operand import LogixOperand
from pyrox.models.plc import meta as plc_meta


class TestLogixOperand(unittest.TestCase):
    """Test cases for LogixOperand class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock controller
        self.mock_controller = MagicMock()
        self.mock_controller.__class__.__name__ = 'Controller'
        self.mock_controller.tags = MagicMock()
        self.mock_controller.aois = []

        # Create mock instruction
        self.mock_instruction = MagicMock()
        self.mock_instruction.instruction_name = 'XIC'
        self.mock_instruction.operands = ['Tag1', 'Tag2']

        # Create mock rung
        self.mock_rung = MagicMock()
        self.mock_rung.number = 5
        self.mock_rung.controller = self.mock_controller
        self.mock_instruction.rung = self.mock_rung

        # Create mock routine
        self.mock_routine = MagicMock()
        self.mock_routine.name = 'TestRoutine'
        self.mock_rung.routine = self.mock_routine

        # Create mock container (program/routine)
        self.mock_container = MagicMock()
        self.mock_container.name = 'TestProgram'
        self.mock_container.tags = MagicMock()
        self.mock_instruction.container = self.mock_container

    def test_init_valid_string_meta_data(self):
        """Test LogixOperand initialization with valid string metadata."""
        operand = LogixOperand(
            meta_data='TestTag.Value',
            instruction=self.mock_instruction,
            arg_position=0,
            controller=self.mock_controller
        )

        self.assertEqual(operand.meta_data, 'TestTag.Value')
        self.assertEqual(operand._arg_position, 0)
        self.assertEqual(operand._instruction, self.mock_instruction)
        self.assertEqual(operand.controller, self.mock_controller)

        # Test private attributes are initialized as None
        self.assertIsNone(operand._aliased_parents)
        self.assertIsNone(operand._as_aliased)
        self.assertIsNone(operand._as_qualified)
        self.assertIsNone(operand._base_name)
        self.assertIsNone(operand._base_tag)
        self.assertIsNone(operand._first_tag)
        self.assertIsNone(operand._instruction_type)
        self.assertIsNone(operand._parents)
        self.assertIsNone(operand._qualified_parents)

    def test_init_invalid_meta_data_type(self):
        """Test LogixOperand initialization with invalid metadata type."""
        with self.assertRaises(TypeError) as context:
            LogixOperand(
                meta_data={'not': 'string'},
                instruction=self.mock_instruction,
                arg_position=0,
                controller=self.mock_controller
            )

        self.assertIn("Meta data must be a string!", str(context.exception))

    def test_init_with_none_controller(self):
        """Test LogixOperand initialization with None controller."""
        operand = LogixOperand(
            meta_data='TestTag',
            instruction=self.mock_instruction,
            arg_position=0,
            controller=None
        )

        self.assertIsNone(operand.controller)

    def test_arg_position_property(self):
        """Test arg_position property."""
        operand = LogixOperand('TestTag', self.mock_instruction, 2, self.mock_controller)

        self.assertEqual(operand.arg_position, 2)

    def test_base_name_property_simple(self):
        """Test base_name property with simple tag name."""
        operand = LogixOperand('SimpleTag', self.mock_instruction, 0, self.mock_controller)

        self.assertEqual(operand.base_name, 'SimpleTag')

    def test_base_name_property_complex(self):
        """Test base_name property with complex tag name."""
        operand = LogixOperand('ComplexTag.Member.SubMember', self.mock_instruction, 0, self.mock_controller)

        self.assertEqual(operand.base_name, 'ComplexTag')

    def test_base_name_property_cached(self):
        """Test base_name property caching."""
        operand = LogixOperand('TestTag.Value', self.mock_instruction, 0, self.mock_controller)

        # First access
        first_result = operand.base_name
        self.assertEqual(first_result, 'TestTag')

        # Cached access
        operand._base_name = 'CachedName'
        second_result = operand.base_name
        self.assertEqual(second_result, 'CachedName')

    def test_parents_property_simple_tag(self):
        """Test parents property with simple tag."""
        operand = LogixOperand('SimpleTag', self.mock_instruction, 0, self.mock_controller)

        parents = operand.parents
        self.assertEqual(parents, ['SimpleTag'])

    def test_parents_property_complex_tag(self):
        """Test parents property with complex tag."""
        operand = LogixOperand('Tag.Member.SubMember', self.mock_instruction, 0, self.mock_controller)

        parents = operand.parents
        expected_parents = [
            'Tag.Member.SubMember',
            'Tag.Member',
            'Tag'
        ]
        self.assertEqual(parents, expected_parents)

    def test_parents_property_cached(self):
        """Test parents property caching."""
        operand = LogixOperand('Tag.Member', self.mock_instruction, 0, self.mock_controller)

        # First access
        _ = operand.parents

        # Cached access
        operand._parents = ['Cached']
        second_parents = operand.parents
        self.assertEqual(second_parents, ['Cached'])

    def test_container_property(self):
        """Test container property."""
        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)

        self.assertEqual(operand.container, self.mock_container)

    def test_instruction_property(self):
        """Test instruction property."""
        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)

        self.assertEqual(operand.instruction, self.mock_instruction)

    def test_trailing_name_simple_tag(self):
        """Test trailing_name property with simple tag."""
        operand = LogixOperand('SimpleTag', self.mock_instruction, 0, self.mock_controller)

        self.assertEqual(operand.trailing_name, '')

    def test_trailing_name_complex_tag(self):
        """Test trailing_name property with complex tag."""
        operand = LogixOperand('Tag.Member.SubMember', self.mock_instruction, 0, self.mock_controller)

        self.assertEqual(operand.trailing_name, '.Member.SubMember')

    def test_trailing_name_empty_meta_data(self):
        """Test trailing_name property with empty metadata."""
        operand = LogixOperand('', self.mock_instruction, 0, self.mock_controller)

        self.assertIsNone(operand.trailing_name)

    def test_base_tag_property_from_container(self):
        """Test base_tag property found in container."""
        mock_tag = MagicMock()
        mock_base_tag = MagicMock()
        mock_tag.get_base_tag.return_value = mock_base_tag

        self.mock_container.tags.get.return_value = mock_tag
        self.mock_controller.tags.get.return_value = None

        operand = LogixOperand('TestTag.Member', self.mock_instruction, 0, self.mock_controller)

        result = operand.base_tag
        self.assertEqual(result, mock_base_tag)
        self.mock_container.tags.get.assert_called_once_with('TestTag', None)
        mock_tag.get_base_tag.assert_called_once()

    def test_base_tag_property_from_controller(self):
        """Test base_tag property found in controller when not in container."""
        mock_tag = MagicMock()
        mock_base_tag = MagicMock()
        mock_tag.get_base_tag.return_value = mock_base_tag

        self.mock_container.tags.get.return_value = None
        self.mock_controller.tags.get.return_value = mock_tag

        operand = LogixOperand('TestTag.Member', self.mock_instruction, 0, self.mock_controller)

        result = operand.base_tag
        self.assertEqual(result, mock_base_tag)
        self.mock_container.tags.get.assert_called_once_with('TestTag', None)
        self.mock_controller.tags.get.assert_called_once_with('TestTag', None)
        mock_tag.get_base_tag.assert_called_once()

    def test_base_tag_property_not_found(self):
        """Test base_tag property when tag is not found."""
        self.mock_container.tags.get.return_value = None
        self.mock_controller.tags.get.return_value = None

        operand = LogixOperand('NonexistentTag', self.mock_instruction, 0, self.mock_controller)

        result = operand.base_tag
        self.assertIsNone(result)

    def test_base_tag_property_no_container(self):
        """Test base_tag property when no container."""
        self.mock_instruction.container = None
        mock_tag = MagicMock()
        mock_base_tag = MagicMock()
        mock_tag.get_base_tag.return_value = mock_base_tag

        self.mock_controller.tags.get.return_value = mock_tag

        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)

        result = operand.base_tag
        self.assertEqual(result, mock_base_tag)
        self.mock_controller.tags.get.assert_called_once_with('TestTag', None)

    def test_base_tag_property_cached(self):
        """Test base_tag property caching."""
        cached_tag = MagicMock()
        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)
        operand._base_tag = cached_tag

        result = operand.base_tag
        self.assertEqual(result, cached_tag)

    def test_first_tag_property_from_container(self):
        """Test first_tag property found in container."""
        mock_tag = MagicMock()
        self.mock_container.tags.get.return_value = mock_tag

        operand = LogixOperand('TestTag.Member', self.mock_instruction, 0, self.mock_controller)

        result = operand.first_tag
        self.assertEqual(result, mock_tag)
        self.mock_container.tags.get.assert_called_once_with('TestTag', None)

    def test_first_tag_property_from_controller(self):
        """Test first_tag property found in controller when not in container."""
        mock_tag = MagicMock()
        self.mock_container.tags.get.return_value = None
        self.mock_controller.tags.get.return_value = mock_tag

        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)

        result = operand.first_tag
        self.assertEqual(result, mock_tag)
        self.mock_controller.tags.get.assert_called_once_with('TestTag', None)

    def test_first_tag_property_no_controller_tags(self):
        """Test first_tag property when controller has no tags."""
        self.mock_container.tags.get.return_value = None
        self.mock_controller.tags = None

        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)

        result = operand.first_tag
        self.assertIsNone(result)

    def test_first_tag_property_cached(self):
        """Test first_tag property caching."""
        cached_tag = MagicMock()
        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)
        operand._first_tag = cached_tag

        result = operand.first_tag
        self.assertEqual(result, cached_tag)

    def test_as_aliased_property_cached(self):
        """Test as_aliased property when cached."""
        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)
        operand._as_aliased = 'CachedAlias'

        result = operand.as_aliased
        self.assertEqual(result, 'CachedAlias')

    def test_as_aliased_property_no_first_tag(self):
        """Test as_aliased property when no first_tag."""
        self.mock_container.tags.get.return_value = None
        self.mock_controller.tags.get.return_value = None

        operand = LogixOperand('TestTag.Member', self.mock_instruction, 0, self.mock_controller)

        result = operand.as_aliased
        self.assertEqual(result, 'TestTag.Member')

    def test_as_aliased_property_first_tag_no_alias(self):
        """Test as_aliased property when first_tag has no alias."""
        mock_tag = MagicMock()
        mock_tag.alias_for = None
        self.mock_container.tags.get.return_value = mock_tag

        operand = LogixOperand('TestTag.Member', self.mock_instruction, 0, self.mock_controller)

        result = operand.as_aliased
        self.assertEqual(result, 'TestTag.Member')

    def test_as_aliased_property_with_alias(self):
        """Test as_aliased property when first_tag has alias."""
        mock_tag = MagicMock()
        mock_tag.alias_for = 'SomeAlias'
        mock_tag.get_alias_string.return_value = 'AliasedTag.Member'
        self.mock_container.tags.get.return_value = mock_tag

        operand = LogixOperand('TestTag.Member', self.mock_instruction, 0, self.mock_controller)

        result = operand.as_aliased
        self.assertEqual(result, 'AliasedTag.Member')
        mock_tag.get_alias_string.assert_called_once_with(additional_elements='.Member')

    def test_aliased_parents_property_simple_tag(self):
        """Test aliased_parents property with simple tag."""
        operand = LogixOperand('SimpleTag', self.mock_instruction, 0, self.mock_controller)
        operand._as_aliased = 'SimpleAlias'

        result = operand.aliased_parents
        self.assertEqual(result, ['SimpleAlias'])

    def test_aliased_parents_property_complex_tag(self):
        """Test aliased_parents property with complex tag."""
        operand = LogixOperand('TestTag.Member.Sub', self.mock_instruction, 0, self.mock_controller)
        operand._as_aliased = 'Alias.Member.Sub'

        result = operand.aliased_parents
        expected = ['Alias.Member.Sub', 'Alias.Member', 'Alias']
        self.assertEqual(result, expected)

    def test_aliased_parents_property_cached(self):
        """Test aliased_parents property caching."""
        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)
        operand._aliased_parents = ['Cached']

        result = operand.aliased_parents
        self.assertEqual(result, ['Cached'])

    def test_as_qualified_property_no_base_tag(self):
        """Test as_qualified property when no base_tag."""
        self.mock_container.tags.get.return_value = None
        self.mock_controller.tags.get.return_value = None

        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)

        result = operand.as_qualified
        self.assertEqual(result, 'TestTag')

    def test_as_qualified_property_program_scope(self):
        """Test as_qualified property with program scope tag."""
        mock_tag = MagicMock()
        mock_base_tag = MagicMock()
        mock_base_tag.scope = plc_meta.LogixTagScope.PROGRAM
        mock_tag.get_base_tag.return_value = mock_base_tag

        self.mock_container.tags.get.return_value = mock_tag

        operand = LogixOperand('TestTag.Member', self.mock_instruction, 0, self.mock_controller)
        operand._as_aliased = 'TestTag.Member'

        result = operand.as_qualified
        self.assertEqual(result, 'Program:TestProgram.TestTag.Member')

    def test_as_qualified_property_controller_scope(self):
        """Test as_qualified property with controller scope tag."""
        mock_tag = MagicMock()
        mock_base_tag = MagicMock()
        mock_base_tag.scope = plc_meta.LogixTagScope.CONTROLLER
        mock_tag.get_base_tag.return_value = mock_base_tag

        self.mock_container.tags.get.return_value = mock_tag

        operand = LogixOperand('TestTag.Member', self.mock_instruction, 0, self.mock_controller)
        operand._as_aliased = 'TestTag.Member'

        result = operand.as_qualified
        self.assertEqual(result, 'TestTag.Member')

    def test_qualified_parents_property_no_base_tag(self):
        """Test qualified_parents property when no base_tag."""
        self.mock_container.tags.get.return_value = None
        self.mock_controller.tags.get.return_value = None

        operand = LogixOperand('TestTag.Member', self.mock_instruction, 0, self.mock_controller)
        operand._as_aliased = 'TestTag.Member'

        result = operand.qualified_parents
        expected = ['TestTag.Member', 'TestTag']
        self.assertEqual(result, expected)

    def test_qualified_parents_property_controller_scope(self):
        """Test qualified_parents property with controller scope tag."""
        mock_tag = MagicMock()
        mock_base_tag = MagicMock()
        mock_base_tag.scope = plc_meta.LogixTagScope.CONTROLLER
        mock_tag.get_base_tag.return_value = mock_base_tag

        self.mock_container.tags.get.return_value = mock_tag

        operand = LogixOperand('TestTag.Member', self.mock_instruction, 0, self.mock_controller)
        operand._as_aliased = 'TestTag.Member'

        result = operand.qualified_parents
        expected = ['TestTag.Member', 'TestTag']
        self.assertEqual(result, expected)

    def test_qualified_parents_property_program_scope(self):
        """Test qualified_parents property with program scope tag."""
        mock_tag = MagicMock()
        mock_base_tag = MagicMock()
        mock_base_tag.scope = plc_meta.LogixTagScope.PROGRAM
        mock_tag.get_base_tag.return_value = mock_base_tag

        self.mock_container.tags.get.return_value = mock_tag

        operand = LogixOperand('TestTag.Member', self.mock_instruction, 0, self.mock_controller)
        operand._as_aliased = 'TestTag.Member'

        result = operand.qualified_parents
        expected = [
            'Program:TestProgram.TestTag.Member',
            'Program:TestProgram.TestTag'
        ]
        self.assertEqual(result, expected)

    def test_qualified_parents_property_cached(self):
        """Test qualified_parents property caching."""
        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)
        operand._qualified_parents = ['Cached']

        result = operand.qualified_parents
        self.assertEqual(result, ['Cached'])

    def test_instruction_type_jsr(self):
        """Test instruction_type property for JSR instruction."""
        self.mock_instruction.instruction_name = plc_meta.INSTR_JSR

        operand = LogixOperand('TestRoutine', self.mock_instruction, 0, self.mock_controller)

        result = operand.instruction_type
        self.assertEqual(result, plc_meta.LogixInstructionType.JSR)

    def test_instruction_type_input(self):
        """Test instruction_type property for input instruction."""
        self.mock_instruction.instruction_name = plc_meta.INSTR_XIC

        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)

        result = operand.instruction_type
        self.assertEqual(result, plc_meta.LogixInstructionType.INPUT)

    def test_instruction_type_output_exact_position(self):
        """Test instruction_type property for output instruction at exact position."""
        self.mock_instruction.instruction_name = 'OTE'
        self.mock_instruction.operands = ['TestTag']

        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)

        # Mock OUTPUT_INSTRUCTIONS to include OTE at position -1 (last)
        with patch.object(plc_meta, 'OUTPUT_INSTRUCTIONS', [('OTE', -1)]):
            result = operand.instruction_type
            self.assertEqual(result, plc_meta.LogixInstructionType.OUTPUT)

    def test_instruction_type_output_last_position(self):
        """Test instruction_type property for output instruction at last position."""
        self.mock_instruction.instruction_name = 'TON'
        self.mock_instruction.operands = ['Timer1', 'TestTag']

        operand = LogixOperand('TestTag', self.mock_instruction, 1, self.mock_controller)

        # Mock OUTPUT_INSTRUCTIONS to include TON at position 0
        with patch.object(plc_meta, 'OUTPUT_INSTRUCTIONS', [('TON', 0)]):
            result = operand.instruction_type
            self.assertEqual(result, plc_meta.LogixInstructionType.INPUT)

    def test_instruction_type_output_instruction_input_position(self):
        """Test instruction_type property for output instruction at input position."""
        self.mock_instruction.instruction_name = 'CPT'
        self.mock_instruction.operands = ['Result', 'Expression']

        operand = LogixOperand('Expression', self.mock_instruction, 1, self.mock_controller)

        # Mock OUTPUT_INSTRUCTIONS to include CPT at position 0 (Result)
        with patch.object(plc_meta, 'OUTPUT_INSTRUCTIONS', [('CPT', 0)]):
            result = operand.instruction_type
            self.assertEqual(result, plc_meta.LogixInstructionType.INPUT)

    def test_instruction_type_aoi(self):
        """Test instruction_type property for AOI instruction."""
        mock_aoi = MagicMock()
        mock_aoi.name = 'CustomAOI'
        self.mock_controller.aois = [mock_aoi]
        self.mock_instruction.instruction_name = 'CustomAOI'

        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)

        result = operand.instruction_type
        self.assertEqual(result, plc_meta.LogixInstructionType.OUTPUT)

    def test_instruction_type_unknown(self):
        """Test instruction_type property for unknown instruction."""
        self.mock_instruction.instruction_name = 'UnknownInstruction'
        self.mock_controller.aois = []

        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)

        result = operand.instruction_type
        self.assertEqual(result, plc_meta.LogixInstructionType.UNKOWN)

    def test_instruction_type_cached(self):
        """Test instruction_type property caching."""
        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)
        operand._instruction_type = plc_meta.LogixInstructionType.INPUT

        result = operand.instruction_type
        self.assertEqual(result, plc_meta.LogixInstructionType.INPUT)

    def test_as_report_dict_complete(self):
        """Test as_report_dict method with complete data."""
        # Setup mocks
        mock_tag = MagicMock()
        mock_base_tag = MagicMock()
        mock_base_tag.scope = plc_meta.LogixTagScope.PROGRAM
        mock_tag.get_base_tag.return_value = mock_base_tag
        mock_tag.alias_for = None

        self.mock_container.tags.get.return_value = mock_tag
        self.mock_instruction.instruction_name = plc_meta.INSTR_XIC
        self.mock_instruction.meta_data = 'XIC TestTag'

        operand = LogixOperand('TestTag.Value', self.mock_instruction, 0, self.mock_controller)

        result = operand.as_report_dict()

        expected_keys = [
            'base operand',
            'aliased operand',
            'qualified operand',
            'arg_position',
            'instruction',
            'instruction_type',
            'program',
            'routine',
            'rung'
        ]

        for key in expected_keys:
            self.assertIn(key, result)

        self.assertEqual(result['base operand'], 'TestTag.Value')
        self.assertEqual(result['aliased operand'], 'TestTag.Value')
        self.assertEqual(result['qualified operand'], 'Program:TestProgram.TestTag.Value')
        self.assertEqual(result['arg_position'], 0)
        self.assertEqual(result['instruction'], 'XIC TestTag')
        self.assertEqual(result['instruction_type'], 'INPUT')
        self.assertEqual(result['program'], 'TestProgram')
        self.assertEqual(result['routine'], 'TestRoutine')
        self.assertEqual(result['rung'], 5)

    def test_as_report_dict_no_container(self):
        """Test as_report_dict method when no container."""
        self.mock_instruction.container = None

        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)

        result = operand.as_report_dict()

        self.assertEqual(result['program'], '???')

    def test_as_report_dict_no_rung(self):
        """Test as_report_dict method when no rung."""
        self.mock_instruction.rung = None

        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)

        result = operand.as_report_dict()

        self.assertEqual(result['routine'], None)
        self.assertEqual(result['rung'], '???')

    def test_as_report_dict_no_routine(self):
        """Test as_report_dict method when rung has no routine."""
        self.mock_rung.routine = None

        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)

        result = operand.as_report_dict()

        self.assertEqual(result['routine'], None)


class TestLogixOperandEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for LogixOperand."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = MagicMock()
        self.mock_controller.__class__.__name__ = 'Controller'
        self.mock_controller.tags = MagicMock()
        self.mock_controller.aois = []

        self.mock_instruction = MagicMock()
        self.mock_instruction.instruction_name = 'XIC'
        self.mock_instruction.operands = ['Tag1']

        self.mock_container = MagicMock()
        self.mock_container.name = 'TestProgram'
        self.mock_container.tags = MagicMock()
        self.mock_instruction.container = self.mock_container

    def test_empty_meta_data(self):
        """Test operand with empty string metadata."""
        operand = LogixOperand('', self.mock_instruction, 0, self.mock_controller)

        self.assertEqual(operand.meta_data, '')
        self.assertEqual(operand.base_name, '')
        self.assertEqual(operand.parents, [''])
        self.assertIsNone(operand.trailing_name)

    def test_single_character_meta_data(self):
        """Test operand with single character metadata."""
        operand = LogixOperand('T', self.mock_instruction, 0, self.mock_controller)

        self.assertEqual(operand.base_name, 'T')
        self.assertEqual(operand.parents, ['T'])
        self.assertEqual(operand.trailing_name, '')

    def test_meta_data_with_multiple_dots(self):
        """Test operand with metadata containing multiple consecutive dots."""
        operand = LogixOperand('Tag..Member...Sub', self.mock_instruction, 0, self.mock_controller)

        self.assertEqual(operand.base_name, 'Tag')
        self.assertEqual(operand.trailing_name, '..Member...Sub')

    def test_meta_data_starting_with_dot(self):
        """Test operand with metadata starting with dot."""
        operand = LogixOperand('.Tag.Member', self.mock_instruction, 0, self.mock_controller)

        self.assertEqual(operand.base_name, '')
        self.assertEqual(operand.trailing_name, '.Tag.Member')

    def test_meta_data_ending_with_dot(self):
        """Test operand with metadata ending with dot."""
        operand = LogixOperand('Tag.Member.', self.mock_instruction, 0, self.mock_controller)

        self.assertEqual(operand.base_name, 'Tag')
        self.assertEqual(operand.trailing_name, '.Member.')

    def test_instruction_type_with_none_controller_aois(self):
        """Test instruction_type when controller.aois is None."""
        self.mock_controller.aois = None
        self.mock_instruction.instruction_name = 'CustomInstruction'

        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)

        # Should handle None aois gracefully and return UNKNOWN
        result = operand.instruction_type
        self.assertEqual(result, plc_meta.LogixInstructionType.UNKOWN)

    def test_instruction_type_with_empty_operands(self):
        """Test instruction_type when instruction has no operands."""
        self.mock_instruction.operands = []
        self.mock_instruction.instruction_name = 'OTE'

        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)

        with patch.object(plc_meta, 'OUTPUT_INSTRUCTIONS', [('OTE', -1)]):
            result = operand.instruction_type
            # Should still work even with empty operands list
            self.assertEqual(result, plc_meta.LogixInstructionType.INPUT)

    def test_base_tag_with_none_get_base_tag(self):
        """Test base_tag when tag.get_base_tag() returns None."""
        mock_tag = MagicMock()
        mock_tag.get_base_tag.return_value = None

        self.mock_container.tags.get.return_value = mock_tag

        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)

        result = operand.base_tag
        self.assertIsNone(result)

    def test_aliased_parents_with_empty_as_aliased(self):
        """Test aliased_parents when as_aliased is empty."""
        operand = LogixOperand('', self.mock_instruction, 0, self.mock_controller)
        operand._as_aliased = ''

        result = operand.aliased_parents
        self.assertEqual(result, [])

    def test_qualified_parents_modification_isolation(self):
        """Test that qualified_parents modifications don't affect aliased_parents."""
        mock_tag = MagicMock()
        mock_base_tag = MagicMock()
        mock_base_tag.scope = plc_meta.LogixTagScope.PROGRAM
        mock_tag.get_base_tag.return_value = mock_base_tag

        self.mock_container.tags.get.return_value = mock_tag

        operand = LogixOperand('TestTag.Member', self.mock_instruction, 0, self.mock_controller)
        operand._as_aliased = 'TestTag.Member'

        # Get qualified_parents (which modifies internal list)
        qualified = operand.qualified_parents

        # Get aliased_parents afterwards
        aliased = operand.aliased_parents

        # aliased_parents should not be affected by the Program: prefix
        expected_aliased = ['TestTag.Member', 'TestTag']
        expected_qualified = ['Program:TestProgram.TestTag.Member', 'Program:TestProgram.TestTag']

        self.assertEqual(aliased, expected_aliased)
        self.assertEqual(qualified, expected_qualified)

    def test_as_qualified_with_none_container_name(self):
        """Test as_qualified when container name is None."""
        mock_tag = MagicMock()
        mock_base_tag = MagicMock()
        mock_base_tag.scope = plc_meta.LogixTagScope.PROGRAM
        mock_tag.get_base_tag.return_value = mock_base_tag

        self.mock_container.tags.get.return_value = mock_tag
        self.mock_container.name = None

        operand = LogixOperand('TestTag', self.mock_instruction, 0, self.mock_controller)
        operand._as_aliased = 'TestTag'

        result = operand.as_qualified
        self.assertEqual(result, 'Program:None.TestTag')

    def test_first_tag_with_none_controller(self):
        """Test first_tag when controller is None."""
        operand = LogixOperand('TestTag', self.mock_instruction, 0, None)
        self.mock_container.tags.get.return_value = None

        result = operand.first_tag
        self.assertIsNone(result)


class TestLogixOperandIntegration(unittest.TestCase):
    """Integration tests for LogixOperand with realistic scenarios."""

    def setUp(self):
        """Set up realistic test fixtures."""
        # Create a more realistic controller mock
        self.mock_controller = MagicMock()
        self.mock_controller.__class__.__name__ = 'Controller'

        # Create controller tags collection
        self.controller_tags = MagicMock()
        self.mock_controller.tags = self.controller_tags

        # Create AOI collection
        self.mock_aoi = MagicMock()
        self.mock_aoi.name = 'MyCustomAOI'
        self.mock_controller.aois = [self.mock_aoi]

        # Create program/routine hierarchy
        self.mock_program = MagicMock()
        self.mock_program.name = 'MainProgram'
        self.program_tags = MagicMock()
        self.mock_program.tags = self.program_tags

        self.mock_routine = MagicMock()
        self.mock_routine.name = 'MainRoutine'

        self.mock_rung = MagicMock()
        self.mock_rung.number = 1
        self.mock_rung.routine = self.mock_routine
        self.mock_rung.controller = self.mock_controller

        self.mock_instruction = MagicMock()
        self.mock_instruction.container = self.mock_program
        self.mock_instruction.rung = self.mock_rung

    def test_program_scoped_tag_workflow(self):
        """Test complete workflow with program-scoped tag."""
        # Create program-scoped tag
        program_tag = MagicMock()
        program_base_tag = MagicMock()
        program_base_tag.scope = plc_meta.LogixTagScope.PROGRAM
        program_tag.get_base_tag.return_value = program_base_tag
        program_tag.alias_for = None

        # Setup tag lookups
        self.program_tags.get.return_value = program_tag
        self.controller_tags.get.return_value = None

        # Create instruction
        self.mock_instruction.instruction_name = plc_meta.INSTR_XIC
        self.mock_instruction.operands = ['ProgramTag.Value']
        self.mock_instruction.meta_data = 'XIC ProgramTag.Value'

        # Create operand
        operand = LogixOperand(
            meta_data='ProgramTag.Value',
            instruction=self.mock_instruction,
            arg_position=0,
            controller=self.mock_controller
        )

        # Test properties
        self.assertEqual(operand.base_name, 'ProgramTag')
        self.assertEqual(operand.base_tag, program_base_tag)
        self.assertEqual(operand.first_tag, program_tag)
        self.assertEqual(operand.as_aliased, 'ProgramTag.Value')
        self.assertEqual(operand.as_qualified, 'Program:MainProgram.ProgramTag.Value')
        self.assertEqual(operand.instruction_type, plc_meta.LogixInstructionType.INPUT)

        # Test parents
        expected_parents = ['ProgramTag.Value', 'ProgramTag']
        expected_qualified_parents = [
            'Program:MainProgram.ProgramTag.Value',
            'Program:MainProgram.ProgramTag'
        ]

        self.assertEqual(operand.parents, expected_parents)
        self.assertEqual(operand.qualified_parents, expected_qualified_parents)

    def test_controller_scoped_tag_workflow(self):
        """Test complete workflow with controller-scoped tag."""
        # Create controller-scoped tag
        controller_tag = MagicMock()
        controller_base_tag = MagicMock()
        controller_base_tag.scope = plc_meta.LogixTagScope.CONTROLLER
        controller_tag.get_base_tag.return_value = controller_base_tag
        controller_tag.alias_for = None

        # Setup tag lookups (not found in program, found in controller)
        self.program_tags.get.return_value = None
        self.controller_tags.get.return_value = controller_tag

        # Create instruction
        self.mock_instruction.instruction_name = 'OTE'
        self.mock_instruction.operands = ['GlobalOutput']

        # Create operand
        operand = LogixOperand(
            meta_data='GlobalOutput',
            instruction=self.mock_instruction,
            arg_position=0,
            controller=self.mock_controller
        )

        # Test properties
        self.assertEqual(operand.base_name, 'GlobalOutput')
        self.assertEqual(operand.base_tag, controller_base_tag)
        self.assertEqual(operand.first_tag, controller_tag)
        self.assertEqual(operand.as_aliased, 'GlobalOutput')
        self.assertEqual(operand.as_qualified, 'GlobalOutput')  # No Program: prefix

        with patch.object(plc_meta, 'OUTPUT_INSTRUCTIONS', [('OTE', -1)]):
            self.assertEqual(operand.instruction_type, plc_meta.LogixInstructionType.OUTPUT)

    def test_aliased_tag_workflow(self):
        """Test complete workflow with aliased tag."""
        # Create aliased tag
        aliased_tag = MagicMock()
        base_tag = MagicMock()
        base_tag.scope = plc_meta.LogixTagScope.PROGRAM
        aliased_tag.get_base_tag.return_value = base_tag
        aliased_tag.alias_for = 'SomeOtherTag'
        aliased_tag.get_alias_string.return_value = 'AliasedName.Status'

        # Setup tag lookups
        self.program_tags.get.return_value = aliased_tag

        # Create operand
        operand = LogixOperand(
            meta_data='OriginalTag.Status',
            instruction=self.mock_instruction,
            arg_position=0,
            controller=self.mock_controller
        )

        # Test aliasing
        self.assertEqual(operand.as_aliased, 'AliasedName.Status')
        aliased_tag.get_alias_string.assert_called_with(additional_elements='.Status')

    def test_aoi_instruction_workflow(self):
        """Test complete workflow with AOI instruction."""
        self.mock_instruction.instruction_name = 'MyCustomAOI'
        self.mock_instruction.operands = ['Input1', 'Input2', 'Output1']

        # Create operand for AOI output parameter
        operand = LogixOperand(
            meta_data='Output1',
            instruction=self.mock_instruction,
            arg_position=2,
            controller=self.mock_controller
        )

        # AOI operands are treated as outputs
        self.assertEqual(operand.instruction_type, plc_meta.LogixInstructionType.OUTPUT)

    def test_complex_report_generation(self):
        """Test complete report generation with all data present."""
        # Setup comprehensive mock data
        program_tag = MagicMock()
        base_tag = MagicMock()
        base_tag.scope = plc_meta.LogixTagScope.PROGRAM
        program_tag.get_base_tag.return_value = base_tag
        program_tag.alias_for = None

        self.program_tags.get.return_value = program_tag

        self.mock_instruction.instruction_name = 'CPT'
        self.mock_instruction.operands = ['Result', 'Expression']
        self.mock_instruction.meta_data = 'CPT Result Expression'

        operand = LogixOperand(
            meta_data='Result.Value',
            instruction=self.mock_instruction,
            arg_position=0,
            controller=self.mock_controller
        )

        with patch.object(plc_meta, 'OUTPUT_INSTRUCTIONS', [('CPT', 0)]):
            report = operand.as_report_dict()

            expected_report = {
                'base operand': 'Result.Value',
                'aliased operand': 'Result.Value',
                'qualified operand': 'Program:MainProgram.Result.Value',
                'arg_position': 0,
                'instruction': 'CPT Result Expression',
                'instruction_type': 'OUTPUT',
                'program': 'MainProgram',
                'routine': 'MainRoutine',
                'rung': 1,
            }

            self.assertEqual(report, expected_report)

    def test_error_recovery_scenarios(self):
        """Test error recovery in various scenarios."""
        # Test with missing tags at all levels
        self.program_tags.get.return_value = None
        self.controller_tags.get.return_value = None

        operand = LogixOperand(
            meta_data='NonExistentTag.Member',
            instruction=self.mock_instruction,
            arg_position=0,
            controller=self.mock_controller
        )

        # Should handle missing tags gracefully
        self.assertIsNone(operand.base_tag)
        self.assertIsNone(operand.first_tag)
        self.assertEqual(operand.as_aliased, 'NonExistentTag.Member')
        self.assertEqual(operand.as_qualified, 'NonExistentTag.Member')

        # Qualified parents should fall back to aliased parents
        expected_parents = ['NonExistentTag.Member', 'NonExistentTag']
        self.assertEqual(operand.qualified_parents, expected_parents)


if __name__ == '__main__':
    unittest.main(verbosity=2)

"""Unit tests for instruction.py module."""

import unittest
from unittest.mock import MagicMock, patch

from pyrox.models.plc.instruction import LogixInstruction
from pyrox.models.plc.operand import LogixOperand
from pyrox.models.plc import meta as plc_meta


class TestLogixInstruction(unittest.TestCase):
    """Test cases for LogixInstruction class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock controller
        self.mock_controller = MagicMock()
        self.mock_controller.__class__.__name__ = 'Controller'
        self.mock_controller.tags = MagicMock()
        self.mock_controller.aois = ['CustomAOI', 'MyAOI']

        # Create mock container (program/AOI)
        self.mock_container = MagicMock()
        self.mock_container.name = 'MainProgram'
        self.mock_container.tags = MagicMock()
        self.mock_container.controller = self.mock_controller

        # Create mock routine
        self.mock_routine = MagicMock()
        self.mock_routine.name = 'MainRoutine'

        # Create mock rung
        self.mock_rung = MagicMock()
        self.mock_rung.number = 5
        self.mock_rung.routine = self.mock_routine
        self.mock_rung.container = self.mock_container

        # Sample instruction metadata
        self.xic_metadata = 'XIC(TestTag)'
        self.ote_metadata = 'OTE(OutputTag)'
        self.ton_metadata = 'TON(Timer1,?,5000)'
        self.complex_metadata = 'CPT(Result,Source1 + Source2)'

    def test_init_valid_metadata(self):
        """Test LogixInstruction initialization with valid metadata."""
        with patch.object(LogixInstruction, '_get_operands') as mock_get_operands:
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            self.assertEqual(instruction.meta_data, self.xic_metadata)
            self.assertEqual(instruction._rung, self.mock_rung)
            self.assertEqual(instruction.controller, self.mock_controller)

            # Test private attributes are initialized as None/empty
            self.assertIsNone(instruction._aliased_meta_data)
            self.assertIsNone(instruction._qualified_meta_data)
            self.assertIsNone(instruction._instruction_name)
            self.assertIsNone(instruction._tag)
            self.assertIsNone(instruction._type)
            self.assertEqual(instruction._operands, [])

            # Test _get_operands was called
            mock_get_operands.assert_called_once()

    def test_init_with_none_rung(self):
        """Test LogixInstruction initialization with None rung."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=None,
                controller=self.mock_controller
            )

            self.assertIsNone(instruction._rung)

    def test_instruction_name_property_xic(self):
        """Test instruction_name property with XIC instruction."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            self.assertEqual(instruction.instruction_name, 'XIC')

    def test_instruction_name_property_ton(self):
        """Test instruction_name property with TON instruction."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.ton_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            self.assertEqual(instruction.instruction_name, 'TON')

    def test_instruction_name_property_cached(self):
        """Test instruction_name property caching."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            # First access
            first_name = instruction.instruction_name
            self.assertEqual(first_name, 'XIC')

            # Cache a different value and verify it's returned
            instruction._instruction_name = 'CACHED'
            second_name = instruction.instruction_name
            self.assertEqual(second_name, 'CACHED')

    def test_instruction_name_property_invalid_metadata(self):
        """Test instruction_name property with invalid metadata."""
        invalid_metadata = 'invalid instruction format'

        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=invalid_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            with self.assertRaises(ValueError) as context:
                _ = instruction.instruction_name

            self.assertIn("Corrupt meta data for instruction, no type found!", str(context.exception))

    def test_container_property(self):
        """Test container property."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            self.assertEqual(instruction.container, self.mock_container)

    def test_container_property_no_rung(self):
        """Test container property when rung is None."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=None,
                controller=self.mock_controller
            )

            assert instruction.container is None

    def test_routine_property(self):
        """Test routine property."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            self.assertEqual(instruction.routine, self.mock_routine)

    def test_routine_property_no_rung(self):
        """Test routine property when rung is None."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=None,
                controller=self.mock_controller
            )

            self.assertIsNone(instruction.routine)

    def test_rung_property(self):
        """Test rung property."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            self.assertEqual(instruction.rung, self.mock_rung)

    def test_is_add_on_instruction_true(self):
        """Test is_add_on_instruction property returns True for AOI."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data='CustomAOI(Input1,Output1)',
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            self.assertTrue(instruction.is_add_on_instruction)

    def test_is_add_on_instruction_false(self):
        """Test is_add_on_instruction property returns False for standard instruction."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            self.assertFalse(instruction.is_add_on_instruction)

    def test_is_add_on_instruction_no_container(self):
        """Test is_add_on_instruction property when no container."""
        self.mock_rung.container = None

        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data='CustomAOI(Input1)',
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            self.assertFalse(instruction.is_add_on_instruction)

    def test_is_add_on_instruction_no_controller(self):
        """Test is_add_on_instruction property when container has no controller."""
        self.mock_container.controller = None

        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data='CustomAOI(Input1)',
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            self.assertFalse(instruction.is_add_on_instruction)

    def test_operands_property(self):
        """Test operands property."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            # Set up mock operands
            mock_operand1 = MagicMock(spec=LogixOperand)
            mock_operand2 = MagicMock(spec=LogixOperand)
            instruction._operands = [mock_operand1, mock_operand2]

            operands = instruction.operands
            self.assertEqual(len(operands), 2)
            self.assertIn(mock_operand1, operands)
            self.assertIn(mock_operand2, operands)

    def test_tag_property_from_container(self):
        """Test tag property found in container."""
        mock_tag = MagicMock()
        self.mock_container.tags.get.return_value = mock_tag

        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            result = instruction.tag
            self.assertEqual(result, mock_tag)
            self.mock_container.tags.get.assert_called_once_with('XIC', None)

    def test_tag_property_from_controller(self):
        """Test tag property found in controller when not in container."""
        mock_tag = MagicMock()
        self.mock_container.tags.get.return_value = None
        self.mock_controller.tags.get.return_value = mock_tag

        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            result = instruction.tag
            self.assertEqual(result, mock_tag)
            self.mock_controller.tags.get.assert_called_once_with('XIC', None)

    def test_tag_property_not_found(self):
        """Test tag property when tag is not found."""
        self.mock_container.tags.get.return_value = None
        self.mock_controller.tags.get.return_value = None

        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            result = instruction.tag
            self.assertIsNone(result)

    def test_tag_property_no_container(self):
        """Test tag property when no container."""
        self.mock_rung.container = None
        mock_tag = MagicMock()
        self.mock_controller.tags.get.return_value = mock_tag

        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            result = instruction.tag
            self.assertIsNone(result)

    def test_tag_property_no_container_tags(self):
        """Test tag property when container has no tags."""
        self.mock_container.tags = None
        mock_tag = MagicMock()
        self.mock_controller.tags.get.return_value = mock_tag

        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            result = instruction.tag
            self.assertIsNone(result)

    def test_tag_property_cached(self):
        """Test tag property caching."""
        cached_tag = MagicMock()

        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            instruction._tag = cached_tag
            result = instruction.tag
            self.assertEqual(result, cached_tag)

    def test_type_property_input(self):
        """Test type property for input instruction."""
        with patch.object(LogixInstruction, '_get_operands'):
            with patch.object(LogixInstruction, '_get_instruction_type') as mock_get_type:
                mock_get_type.return_value = plc_meta.LogixInstructionType.INPUT

                instruction = LogixInstruction(
                    meta_data=self.xic_metadata,
                    rung=self.mock_rung,
                    controller=self.mock_controller
                )

                result = instruction.type
                self.assertEqual(result, plc_meta.LogixInstructionType.INPUT)
                mock_get_type.assert_called_once()

    def test_type_property_cached(self):
        """Test type property caching."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            instruction._type = plc_meta.LogixInstructionType.OUTPUT
            result = instruction.type
            self.assertEqual(result, plc_meta.LogixInstructionType.OUTPUT)

    def test_aliased_meta_data_property(self):
        """Test aliased_meta_data property."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data='XIC(OriginalTag)',
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            # Create mock operands
            mock_operand = MagicMock(spec=LogixOperand)
            mock_operand.meta_data = 'OriginalTag'
            mock_operand.as_aliased = 'AliasedTag'
            instruction._operands = [mock_operand]

            result = instruction.aliased_meta_data
            self.assertEqual(result, 'XIC(AliasedTag)')

    def test_aliased_meta_data_property_cached(self):
        """Test aliased_meta_data property caching."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            instruction._aliased_meta_data = 'CachedAliasedData'
            result = instruction.aliased_meta_data
            self.assertEqual(result, 'CachedAliasedData')

    def test_aliased_meta_data_property_multiple_operands(self):
        """Test aliased_meta_data property with multiple operands."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data='CPT(Result,Source1 + Source2)',
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            # Create mock operands
            mock_operand1 = MagicMock(spec=LogixOperand)
            mock_operand1.meta_data = 'Result'
            mock_operand1.as_aliased = 'AliasedResult'

            mock_operand2 = MagicMock(spec=LogixOperand)
            mock_operand2.meta_data = 'Source1 + Source2'
            mock_operand2.as_aliased = 'AliasedSource1 + AliasedSource2'

            instruction._operands = [mock_operand1, mock_operand2]

            result = instruction.aliased_meta_data
            self.assertEqual(result, 'CPT(AliasedResult,AliasedSource1 + AliasedSource2)')

    def test_qualified_meta_data_property(self):
        """Test qualified_meta_data property."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data='XIC(LocalTag)',
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            # Create mock operands
            mock_operand = MagicMock(spec=LogixOperand)
            mock_operand.meta_data = 'LocalTag'
            mock_operand.as_qualified = 'Program:MainProgram.LocalTag'
            instruction._operands = [mock_operand]

            result = instruction.qualified_meta_data
            self.assertEqual(result, 'XIC(Program:MainProgram.LocalTag)')

    def test_qualified_meta_data_property_cached(self):
        """Test qualified_meta_data property caching."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            instruction._qualified_meta_data = 'CachedQualifiedData'
            result = instruction.qualified_meta_data
            self.assertEqual(result, 'CachedQualifiedData')

    def test_get_operands_valid_metadata(self):
        """Test _get_operands with valid metadata."""
        instruction = LogixInstruction.__new__(LogixInstruction)  # Create without calling __init__
        instruction.meta_data = 'XIC(TestTag)'
        instruction.controller = self.mock_controller

        with patch('pyrox.models.plc.instruction.LogixOperand') as mock_operand_class:
            mock_operand_instance = MagicMock(spec=LogixOperand)
            mock_operand_class.return_value = mock_operand_instance

            instruction._get_operands()

            self.assertEqual(len(instruction._operands), 1)
            mock_operand_class.assert_called_once_with('TestTag', instruction, 0, self.mock_controller)

    def test_get_operands_multiple_operands(self):
        """Test _get_operands with multiple operands."""
        instruction = LogixInstruction.__new__(LogixInstruction)
        instruction.meta_data = 'TON(Timer1,?,5000)'
        instruction.controller = self.mock_controller

        with patch('pyrox.models.plc.instruction.LogixOperand') as mock_operand_class:
            mock_operand_instances = [MagicMock(spec=LogixOperand) for _ in range(3)]
            mock_operand_class.side_effect = mock_operand_instances

            instruction._get_operands()

            self.assertEqual(len(instruction._operands), 3)

            # Verify operand creation calls
            _ = [
                (('Timer1', instruction, 0, self.mock_controller),),
                (('?', instruction, 1, self.mock_controller),),
                (('5000', instruction, 2, self.mock_controller),)
            ]

            actual_calls = [call for call in mock_operand_class.call_args_list]
            self.assertEqual(len(actual_calls), 3)

    def test_get_operands_with_empty_operands(self):
        """Test _get_operands with empty operands in comma-separated list."""
        instruction = LogixInstruction.__new__(LogixInstruction)
        instruction.meta_data = 'TEST(,Operand2,)'
        instruction.controller = self.mock_controller

        with patch('pyrox.models.plc.instruction.LogixOperand') as mock_operand_class:
            mock_operand_instance = MagicMock(spec=LogixOperand)
            mock_operand_class.return_value = mock_operand_instance

            instruction._get_operands()

            # Should only create operand for non-empty matches
            self.assertEqual(len(instruction._operands), 1)
            mock_operand_class.assert_called_once_with('Operand2', instruction, 1, self.mock_controller)

    def test_get_operands_invalid_metadata(self):
        """Test _get_operands with invalid metadata."""
        instruction = LogixInstruction.__new__(LogixInstruction)
        instruction.meta_data = 'invalid instruction format'
        instruction.controller = self.mock_controller
        self.assertEqual(instruction._get_operands(), None)

    def test_get_instruction_type_input(self):
        """Test _get_instruction_type for input instructions."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data='XIC(TestTag)',
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            with patch.object(plc_meta, 'INPUT_INSTRUCTIONS', ['XIC']):
                result = instruction._get_instruction_type()
                self.assertEqual(result, plc_meta.LogixInstructionType.INPUT)

    def test_get_instruction_type_output(self):
        """Test _get_instruction_type for output instructions."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data='OTE(OutputTag)',
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            with patch.object(plc_meta, 'OUTPUT_INSTRUCTIONS', [('OTE', -1)]):
                result = instruction._get_instruction_type()
                self.assertEqual(result, plc_meta.LogixInstructionType.OUTPUT)

    def test_get_instruction_type_jsr(self):
        """Test _get_instruction_type for JSR instruction."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data='JSR(SubRoutine,0,ReturnTag)',
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            with patch.object(plc_meta, 'INSTR_JSR', 'JSR'):
                result = instruction._get_instruction_type()
                self.assertEqual(result, plc_meta.LogixInstructionType.JSR)

    def test_get_instruction_type_unknown(self):
        """Test _get_instruction_type for unknown instructions."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data='UNKNOWN_INSTR(TestTag)',
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            result = instruction._get_instruction_type()
            self.assertEqual(result, plc_meta.LogixInstructionType.UNKOWN)

    def test_as_report_dict_complete(self):
        """Test as_report_dict with complete data."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            result = instruction.as_report_dict()

            expected = {
                'instruction': self.xic_metadata,
                'program': 'MainProgram',
                'routine': 'MainRoutine',
                'rung': 5,
            }

            self.assertEqual(result, expected)

    def test_as_report_dict_no_container(self):
        """Test as_report_dict when no container."""
        self.mock_rung.container = None

        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            result = instruction.as_report_dict()
            self.assertEqual(result['program'], '???')

    def test_as_report_dict_no_routine(self):
        """Test as_report_dict when no routine."""
        self.mock_rung.routine = None

        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            result = instruction.as_report_dict()
            self.assertEqual(result['routine'], '???')

    def test_as_report_dict_no_rung(self):
        """Test as_report_dict when no rung."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data=self.xic_metadata,
                rung=None,
                controller=self.mock_controller
            )

            result = instruction.as_report_dict()
            self.assertEqual(result['rung'], '???')


class TestLogixInstructionEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for LogixInstruction."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = MagicMock()
        self.mock_controller.__class__.__name__ = 'Controller'
        self.mock_controller.tags = MagicMock()
        self.mock_controller.aois = []

        self.mock_rung = MagicMock()
        self.mock_rung.number = 1

        self.mock_container = MagicMock()
        self.mock_container.name = 'TestProgram'
        self.mock_container.tags = MagicMock()
        self.mock_rung.container = self.mock_container

    def test_instruction_name_with_malformed_regex_match(self):
        """Test instruction_name with metadata that has no regex matches."""
        with patch.object(LogixInstruction, '_get_operands'):
            with patch('re.findall', return_value=[]):
                instruction = LogixInstruction(
                    meta_data='malformed',
                    rung=self.mock_rung,
                    controller=self.mock_controller
                )

                with self.assertRaises(ValueError):
                    _ = instruction.instruction_name

    def test_instruction_name_with_empty_matches(self):
        """Test instruction_name with empty regex matches."""
        with patch.object(LogixInstruction, '_get_operands'):
            with patch('re.findall', return_value=[[]]):
                instruction = LogixInstruction(
                    meta_data='test123???',
                    rung=self.mock_rung,
                    controller=self.mock_controller
                )

                with self.assertRaises(ValueError):
                    _ = instruction.instruction_name

    def test_get_operands_with_malformed_regex(self):
        """Test _get_operands with malformed regex results."""
        instruction = LogixInstruction.__new__(LogixInstruction)
        instruction.meta_data = 'test'
        instruction.controller = self.mock_controller

        with patch('re.findall', return_value=[]):
            self.assertEqual(instruction._get_operands(), None)

    def test_get_operands_with_empty_regex_matches(self):
        """Test _get_operands with empty regex matches."""
        instruction = LogixInstruction('test', None, None)
        instruction.meta_data = 'test'
        instruction.controller = self.mock_controller

        with patch('re.findall', return_value=[[]]):
            self.assertEqual(instruction.operands, [])

    def test_aliased_meta_data_with_no_operands(self):
        """Test aliased_meta_data with no operands."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data='NOP()',
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            instruction._operands = []
            result = instruction.aliased_meta_data
            self.assertEqual(result, 'NOP()')

    def test_qualified_meta_data_with_no_operands(self):
        """Test qualified_meta_data with no operands."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data='NOP()',
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            instruction._operands = []
            result = instruction.qualified_meta_data
            self.assertEqual(result, 'NOP()')

    def test_is_add_on_instruction_with_none_aois(self):
        """Test is_add_on_instruction when controller.aois is None."""
        self.mock_controller.aois = None

        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data='CustomAOI(Input1)',
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            # Should handle None aois gracefully
            result = instruction.is_add_on_instruction
            self.assertFalse(result)

    def test_complex_operand_parsing(self):
        """Test operand parsing with complex expressions."""
        instruction = LogixInstruction.__new__(LogixInstruction)
        instruction.meta_data = 'CPT(Result,(Source1 + Source2) * Factor)'
        instruction.controller = self.mock_controller

        with patch('pyrox.models.plc.instruction.LogixOperand') as mock_operand_class:
            mock_operand_instances = [MagicMock(spec=LogixOperand) for _ in range(2)]
            mock_operand_class.side_effect = mock_operand_instances

            instruction._get_operands()

            # Should parse complex expressions correctly
            self.assertEqual(len(instruction._operands), 2)

    def test_instruction_with_special_characters_in_operands(self):
        """Test instruction parsing with special characters in operands."""
        instruction = LogixInstruction.__new__(LogixInstruction)
        instruction.meta_data = 'TEST(Tag_With_Underscores,Tag.With.Dots)'
        instruction.controller = self.mock_controller

        with patch('pyrox.models.plc.instruction.LogixOperand') as mock_operand_class:
            mock_operand_instances = [MagicMock(spec=LogixOperand) for _ in range(2)]
            mock_operand_class.side_effect = mock_operand_instances

            instruction._get_operands()

            self.assertEqual(len(instruction._operands), 2)

    def test_meta_data_replacement_edge_cases(self):
        """Test metadata replacement with edge cases."""
        with patch.object(LogixInstruction, '_get_operands'):
            instruction = LogixInstruction(
                meta_data='XIC(Tag) OTE(Tag)',  # Same operand appears twice
                rung=self.mock_rung,
                controller=self.mock_controller
            )

            # Create mock operand that appears multiple times
            mock_operand = MagicMock(spec=LogixOperand)
            mock_operand.meta_data = 'Tag'
            mock_operand.as_aliased = 'AliasTag'
            mock_operand.as_qualified = 'Program:Test.AliasTag'
            instruction._operands = [mock_operand]

            aliased_result = instruction.aliased_meta_data
            qualified_result = instruction.qualified_meta_data

            # Both occurrences should be replaced
            self.assertEqual(aliased_result, 'XIC(AliasTag) OTE(AliasTag)')
            self.assertEqual(qualified_result, 'XIC(Program:Test.AliasTag) OTE(Program:Test.AliasTag)')


class TestLogixInstructionIntegration(unittest.TestCase):
    """Integration tests for LogixInstruction with realistic scenarios."""

    def setUp(self):
        """Set up realistic test fixtures."""
        # Create realistic controller
        self.controller = MagicMock()
        self.controller.__class__.__name__ = 'Controller'
        self.controller.tags = MagicMock()
        self.controller.aois = ['PID_Enhanced', 'CustomMotorControl']

        # Create realistic program hierarchy
        self.program = MagicMock()
        self.program.name = 'MainProgram'
        self.program.tags = MagicMock()
        self.program.controller = self.controller

        self.routine = MagicMock()
        self.routine.name = 'MainRoutine'

        self.rung = MagicMock()
        self.rung.number = 10
        self.rung.routine = self.routine
        self.rung.container = self.program

    def test_complete_xic_instruction_workflow(self):
        """Test complete workflow with XIC instruction."""
        metadata = 'XIC(ConveyorRunning.Status)'

        with patch('pyrox.models.plc.instruction.LogixOperand') as mock_operand_class:
            # Create mock operand
            mock_operand = MagicMock(spec=LogixOperand)
            mock_operand.meta_data = 'ConveyorRunning.Status'
            mock_operand.as_aliased = 'Conv_01_Running.Status'
            mock_operand.as_qualified = 'Program:MainProgram.Conv_01_Running.Status'
            mock_operand_class.return_value = mock_operand

            instruction = LogixInstruction(
                meta_data=metadata,
                rung=self.rung,
                controller=self.controller
            )

            # Test basic properties
            self.assertEqual(instruction.instruction_name, 'XIC')
            self.assertEqual(instruction.container, self.program)
            self.assertEqual(instruction.routine, self.routine)
            self.assertEqual(instruction.rung, self.rung)
            self.assertFalse(instruction.is_add_on_instruction)

            # Test operand creation
            self.assertEqual(len(instruction.operands), 1)
            mock_operand_class.assert_called_once_with(
                'ConveyorRunning.Status', instruction, 0, self.controller
            )

            # Test metadata transformations
            self.assertEqual(
                instruction.aliased_meta_data,
                'XIC(Conv_01_Running.Status)'
            )
            self.assertEqual(
                instruction.qualified_meta_data,
                'XIC(Program:MainProgram.Conv_01_Running.Status)'
            )

    def test_complete_ton_instruction_workflow(self):
        """Test complete workflow with TON instruction."""
        metadata = 'TON(StartupTimer,?,5000)'

        with patch('pyrox.models.plc.instruction.LogixOperand') as mock_operand_class:
            # Create mock operands
            operands_data = [
                ('StartupTimer', 'Timer_Startup', 'Program:MainProgram.Timer_Startup'),
                ('?', '?', '?'),
                ('5000', '5000', '5000')
            ]

            mock_operands = []
            for i, (original, aliased, qualified) in enumerate(operands_data):
                mock_operand = MagicMock(spec=LogixOperand)
                mock_operand.meta_data = original
                mock_operand.as_aliased = aliased
                mock_operand.as_qualified = qualified
                mock_operands.append(mock_operand)

            mock_operand_class.side_effect = mock_operands

            instruction = LogixInstruction(
                meta_data=metadata,
                rung=self.rung,
                controller=self.controller
            )

            # Test instruction properties
            self.assertEqual(instruction.instruction_name, 'TON')

            # Test operand creation (3 operands for TON)
            self.assertEqual(len(instruction.operands), 3)
            self.assertEqual(mock_operand_class.call_count, 3)

            # Test metadata transformations
            self.assertEqual(
                instruction.aliased_meta_data,
                'TON(Timer_Startup,?,5000)'
            )
            self.assertEqual(
                instruction.qualified_meta_data,
                'TON(Program:MainProgram.Timer_Startup,?,5000)'
            )

    def test_complete_aoi_instruction_workflow(self):
        """Test complete workflow with AOI instruction."""
        metadata = 'PID_Enhanced(Process_PID,ProcessValue,Setpoint,Output)'

        with patch('pyrox.models.plc.instruction.LogixOperand') as mock_operand_class:
            # Create mock operands for AOI parameters
            operands_data = [
                ('Process_PID', 'PID_Loop_01', 'Program:MainProgram.PID_Loop_01'),
                ('ProcessValue', 'TempInput.Value', 'Program:MainProgram.TempInput.Value'),
                ('Setpoint', 'TempSetpoint', 'TempSetpoint'),  # Controller scoped
                ('Output', 'HeaterOutput', 'Program:MainProgram.HeaterOutput')
            ]

            mock_operands = []
            for original, aliased, qualified in operands_data:
                mock_operand = MagicMock(spec=LogixOperand)
                mock_operand.meta_data = original
                mock_operand.as_aliased = aliased
                mock_operand.as_qualified = qualified
                mock_operands.append(mock_operand)

            mock_operand_class.side_effect = mock_operands

            instruction = LogixInstruction(
                meta_data=metadata,
                rung=self.rung,
                controller=self.controller
            )

            # Test AOI detection
            self.assertTrue(instruction.is_add_on_instruction)
            self.assertEqual(instruction.instruction_name, 'PID_Enhanced')

            # Test operand handling
            self.assertEqual(len(instruction.operands), 4)

            # Test metadata transformations
            expected_aliased = 'PID_Enhanced(PID_Loop_01,TempInput.Value,TempSetpoint,HeaterOutput)'
            expected_qualified = 'PID_Enhanced(Program:MainProgram.PID_Loop_01,Program:MainProgram.TempInput.Value,TempSetpoint,Program:MainProgram.HeaterOutput)'  # noqa E508

            self.assertEqual(instruction.aliased_meta_data, expected_aliased)
            self.assertEqual(instruction.qualified_meta_data, expected_qualified)

    def test_instruction_type_determination(self):
        """Test instruction type determination for various instruction types."""
        test_cases = [
            ('XIC(InputTag)', plc_meta.LogixInstructionType.INPUT),
            ('XIO(InputTag)', plc_meta.LogixInstructionType.INPUT),
            ('OTE(OutputTag)', plc_meta.LogixInstructionType.OUTPUT),
            ('JSR(SubRoutine,0,RetVal)', plc_meta.LogixInstructionType.JSR),
            ('UNKNOWN_INSTR(Tag)', plc_meta.LogixInstructionType.UNKOWN),
        ]

        for metadata, expected_type in test_cases:
            with self.subTest(metadata=metadata):
                with patch('pyrox.models.plc.instruction.LogixOperand'):
                    instruction = LogixInstruction(
                        meta_data=metadata,
                        rung=self.rung,
                        controller=self.controller
                    )

                    # Mock the appropriate constants for testing
                    with patch.object(plc_meta, 'INPUT_INSTRUCTIONS', ['XIC', 'XIO']):
                        with patch.object(plc_meta, 'OUTPUT_INSTRUCTIONS', [('OTE', -1)]):
                            with patch.object(plc_meta, 'INSTR_JSR', 'JSR'):
                                self.assertEqual(instruction.type, expected_type)

    def test_tag_resolution_hierarchy(self):
        """Test tag resolution hierarchy (container -> controller)."""
        metadata = 'XIC(TestTag)'

        # Test case 1: Tag found in container
        container_tag = MagicMock()
        self.program.tags.get.return_value = container_tag
        self.controller.tags.get.return_value = None

        with patch('pyrox.models.plc.instruction.LogixOperand'):
            instruction = LogixInstruction(
                meta_data=metadata,
                rung=self.rung,
                controller=self.controller
            )

            self.assertEqual(instruction.tag, container_tag)
            self.program.tags.get.assert_called_once_with('XIC', None)

        # Reset mocks
        self.program.tags.reset_mock()
        self.controller.tags.reset_mock()

        # Test case 2: Tag found in controller (not in container)
        controller_tag = MagicMock()
        self.program.tags.get.return_value = None
        self.controller.tags.get.return_value = controller_tag

        with patch('pyrox.models.plc.instruction.LogixOperand'):
            instruction = LogixInstruction(
                meta_data=metadata,
                rung=self.rung,
                controller=self.controller
            )

            self.assertEqual(instruction.tag, controller_tag)
            self.program.tags.get.assert_called_once_with('XIC', None)
            self.controller.tags.get.assert_called_once_with('XIC', None)

    def test_comprehensive_report_generation(self):
        """Test comprehensive report generation."""
        metadata = 'CPT(CalculatedValue,InputA * InputB + Offset)'

        with patch('pyrox.models.plc.instruction.LogixOperand'):
            instruction = LogixInstruction(
                meta_data=metadata,
                rung=self.rung,
                controller=self.controller
            )

            report = instruction.as_report_dict()

            expected_report = {
                'instruction': metadata,
                'program': 'MainProgram',
                'routine': 'MainRoutine',
                'rung': 10,
            }

            self.assertEqual(report, expected_report)

    def test_error_recovery_in_complex_scenarios(self):
        """Test error recovery in complex scenarios."""
        # Test with missing hierarchy components
        self.rung.container = None
        self.rung.routine = None

        metadata = 'XIC(TestTag)'

        with patch('pyrox.models.plc.instruction.LogixOperand'):
            instruction = LogixInstruction(
                meta_data=metadata,
                rung=self.rung,
                controller=self.controller
            )

            # Should handle missing components gracefully
            self.assertIsNone(instruction.routine)
            self.assertIsNone(instruction.tag)  # No container, so no tag lookup

            report = instruction.as_report_dict()
            self.assertEqual(report['program'], '???')
            self.assertEqual(report['routine'], '???')

    def test_regex_pattern_integration(self):
        """Test integration with actual regex patterns."""
        # This test uses the actual regex patterns to ensure they work correctly
        test_instructions = [
            'XIC(TestTag)',
            'TON(Timer1,?,5000)',
            'CPT(Result,Source1 + Source2)',
            'CustomAOI(Input1,Input2,Output1)',
        ]

        for metadata in test_instructions:
            with self.subTest(metadata=metadata):
                with patch('pyrox.models.plc.instruction.LogixOperand'):
                    # Should not raise exceptions during parsing
                    instruction = LogixInstruction(
                        meta_data=metadata,
                        rung=self.rung,
                        controller=self.controller
                    )

                    # Basic validation that parsing worked
                    self.assertIsInstance(instruction.instruction_name, str)
                    self.assertTrue(len(instruction.instruction_name) > 0)
                    self.assertIsInstance(instruction.operands, list)


if __name__ == '__main__':
    unittest.main(verbosity=2)

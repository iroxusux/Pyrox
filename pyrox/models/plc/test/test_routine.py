"""Unit tests for pyrox.models.plc.routine module."""

import unittest
from unittest.mock import Mock, patch

from pyrox.models.plc.routine import Routine
from pyrox.models.plc import Controller, Program, AddOnInstruction, LogixInstruction, Rung
from pyrox.models.plc.meta import LogixInstructionType


class TestRoutineInit(unittest.TestCase):
    """Test Routine initialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.mock_controller.name = "TestController"

        self.mock_program = Mock(spec=Program)
        self.mock_program.name = "TestProgram"

        self.mock_aoi = Mock(spec=AddOnInstruction)
        self.mock_aoi.name = "TestAOI"

        self.basic_routine_meta = {
            '@Name': 'TestRoutine',
            '@Type': 'RLL',
            'Description': 'Test routine description',
            'RLLContent': {
                'Rung': []
            }
        }

        self.routine_with_rungs_meta = {
            '@Name': 'TestRoutine',
            '@Type': 'RLL',
            'Description': 'Test routine with rungs',
            'RLLContent': {
                'Rung': [
                    {
                        '@Number': '0',
                        'Text': 'XIC(Input1)OTE(Output1);'
                    },
                    {
                        '@Number': '1',
                        'Text': 'XIO(Input2)OTL(Output2);'
                    }
                ]
            }
        }

    @patch('pyrox.models.plc.routine.l5x_dict_from_file')
    def test_init_with_meta_data(self, mock_l5x_dict):
        """Test Routine initialization with provided meta_data."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller,
            program=self.mock_program
        )

        self.assertEqual(routine['@Name'], 'TestRoutine')
        self.assertEqual(routine.controller, self.mock_controller)
        self.assertEqual(routine.program, self.mock_program)
        mock_l5x_dict.assert_not_called()

    @patch('pyrox.models.plc.routine.l5x_dict_from_file')
    def test_init_without_meta_data(self, mock_l5x_dict):
        """Test Routine initialization without meta_data loads from file."""
        mock_l5x_dict.return_value = {'Routine': self.basic_routine_meta}

        routine = Routine(controller=self.mock_controller)

        mock_l5x_dict.assert_called_once()
        self.assertEqual(routine['@Name'], 'TestRoutine')

    @patch('pyrox.models.plc.routine.l5x_dict_from_file')
    def test_init_with_aoi(self, mock_l5x_dict):
        """Test Routine initialization with AOI."""
        mock_l5x_dict.return_value = {'Routine': self.basic_routine_meta}

        routine = Routine(
            controller=self.mock_controller,
            aoi=self.mock_aoi
        )

        self.assertEqual(routine.aoi, self.mock_aoi)
        self.assertIsNone(routine.program)

    def test_init_with_name_and_description(self):
        """Test Routine initialization with name and description parameters."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller,
            name="CustomName",
            description="Custom description"
        )

        self.assertEqual(routine.controller, self.mock_controller)
        # Note: The actual name/description handling depends on NamedPlcObject implementation

    def test_init_sets_private_attributes(self):
        """Test that initialization properly sets private attributes."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        self.assertEqual(routine._instructions, [])
        self.assertEqual(routine._input_instructions, [])
        self.assertEqual(routine._output_instructions, [])
        self.assertEqual(routine._rungs, [])


class TestRoutineProperties(unittest.TestCase):
    """Test Routine properties."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.mock_program = Mock(spec=Program)
        self.mock_aoi = Mock(spec=AddOnInstruction)

        self.basic_routine_meta = {
            '@Name': 'TestRoutine',
            '@Type': 'RLL',
            'Description': 'Test routine description',
            'RLLContent': {
                'Rung': []
            }
        }

    def test_dict_key_order(self):
        """Test dict_key_order property returns correct order."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        expected_order = [
            '@Name',
            '@Type',
            'Description',
            'RLLContent',
        ]

        self.assertEqual(routine.dict_key_order, expected_order)

    def test_aoi_property(self):
        """Test aoi property."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller,
            aoi=self.mock_aoi
        )

        self.assertEqual(routine.aoi, self.mock_aoi)

    def test_program_property(self):
        """Test program property."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller,
            program=self.mock_program
        )

        self.assertEqual(routine.program, self.mock_program)

    def test_container_property_with_aoi(self):
        """Test container property returns AOI when present."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller,
            aoi=self.mock_aoi,
            program=self.mock_program
        )

        self.assertEqual(routine.container, self.mock_aoi)

    def test_container_property_with_program(self):
        """Test container property returns program when no AOI."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller,
            program=self.mock_program
        )

        self.assertEqual(routine.container, self.mock_program)

    def test_raw_rungs_property_empty(self):
        """Test raw_rungs property with empty RLLContent."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        raw_rungs = routine.raw_rungs
        self.assertIsInstance(raw_rungs, list)
        self.assertEqual(len(raw_rungs), 0)

    def test_raw_rungs_property_no_rll_content(self):
        """Test raw_rungs property when RLLContent is None."""
        meta_without_rll = {
            '@Name': 'TestRoutine',
            '@Type': 'RLL',
            'Description': 'Test routine'
        }

        routine = Routine(
            meta_data=meta_without_rll,
            controller=self.mock_controller
        )

        raw_rungs = routine.raw_rungs
        self.assertIsInstance(raw_rungs, list)
        self.assertEqual(len(raw_rungs), 0)

    def test_raw_rungs_property_single_rung(self):
        """Test raw_rungs property with single rung (not in list)."""
        meta_single_rung = {
            '@Name': 'TestRoutine',
            '@Type': 'RLL',
            'Description': 'Test routine',
            'RLLContent': {
                'Rung': {
                    '@Number': '0',
                    'Text': 'XIC(Input1)OTE(Output1);'
                }
            }
        }

        routine = Routine(
            meta_data=meta_single_rung,
            controller=self.mock_controller
        )

        raw_rungs = routine.raw_rungs
        self.assertIsInstance(raw_rungs, list)
        self.assertEqual(len(raw_rungs), 1)
        self.assertEqual(raw_rungs[0]['@Number'], '0')


class TestRoutineInstructionMethods(unittest.TestCase):
    """Test Routine instruction-related methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.mock_controller.config = Mock()
        self.mock_controller.config.rung_type = Mock()

        self.basic_routine_meta = {
            '@Name': 'TestRoutine',
            '@Type': 'RLL',
            'Description': 'Test routine description',
            'RLLContent': {
                'Rung': []
            }
        }

    def test_instructions_property_compiles_when_empty(self):
        """Test instructions property compiles when _instructions is empty."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        with patch.object(routine, '_compile_instructions') as mock_compile:
            _ = routine.instructions
            mock_compile.assert_called_once()

    def test_input_instructions_property_compiles_when_empty(self):
        """Test input_instructions property compiles when empty."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        with patch.object(routine, '_compile_instructions') as mock_compile:
            _ = routine.input_instructions
            mock_compile.assert_called_once()

    def test_output_instructions_property_compiles_when_empty(self):
        """Test output_instructions property compiles when empty."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        with patch.object(routine, '_compile_instructions') as mock_compile:
            _ = routine.output_instructions
            mock_compile.assert_called_once()

    def test_instructions_property_returns_cached(self):
        """Test instructions property returns cached value when available."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        mock_instruction = Mock(spec=LogixInstruction)
        routine._instructions = [mock_instruction]

        with patch.object(routine, '_compile_instructions') as mock_compile:
            result = routine.instructions
            mock_compile.assert_not_called()
            self.assertEqual(result, [mock_instruction])

    def test_get_instructions_with_filters(self):
        """Test get_instructions method with filters."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        # Mock rungs
        mock_rung1 = Mock(spec=Rung)
        mock_rung2 = Mock(spec=Rung)

        mock_instruction1 = Mock(spec=LogixInstruction)
        mock_instruction2 = Mock(spec=LogixInstruction)

        mock_rung1.get_instructions.return_value = [mock_instruction1]
        mock_rung2.get_instructions.return_value = [mock_instruction2]

        routine._rungs = [mock_rung1, mock_rung2]

        result = routine.get_instructions('XIC', 'Input1')

        self.assertEqual(len(result), 2)
        self.assertIn(mock_instruction1, result)
        self.assertIn(mock_instruction2, result)

        mock_rung1.get_instructions.assert_called_once_with('XIC', 'Input1')
        mock_rung2.get_instructions.assert_called_once_with('XIC', 'Input1')

    def test_get_instructions_no_operand_filter(self):
        """Test get_instructions method without operand filter."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        mock_rung = Mock(spec=Rung)
        mock_instruction = Mock(spec=LogixInstruction)
        mock_rung.get_instructions.return_value = [mock_instruction]

        routine._rungs = [mock_rung]

        result = routine.get_instructions('XIC')

        self.assertEqual(len(result), 1)
        self.assertIn(mock_instruction, result)
        mock_rung.get_instructions.assert_called_once_with('XIC', None)


class TestRoutineJSRMethods(unittest.TestCase):
    """Test Routine JSR-related methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)

        self.basic_routine_meta = {
            '@Name': 'TestRoutine',
            '@Type': 'RLL',
            'Description': 'Test routine description',
            'RLLContent': {
                'Rung': []
            }
        }

    def test_check_for_jsr_found(self):
        """Test check_for_jsr method when JSR is found."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        # Mock JSR instruction
        mock_jsr = Mock(spec=LogixInstruction)
        mock_jsr.type = LogixInstructionType.JSR
        mock_operand = Mock()
        mock_operand.__str__ = Mock(return_value='SubRoutine1')
        mock_jsr.operands = [mock_operand]

        # Mock non-JSR instruction
        mock_other = Mock(spec=LogixInstruction)
        mock_other.type = LogixInstructionType.INPUT

        routine._instructions = [mock_other, mock_jsr]

        result = routine.check_for_jsr('SubRoutine1')
        self.assertTrue(result)

    def test_check_for_jsr_not_found(self):
        """Test check_for_jsr method when JSR is not found."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        # Mock JSR instruction with different operand
        mock_jsr = Mock(spec=LogixInstruction)
        mock_jsr.type = LogixInstructionType.JSR
        mock_operand = Mock()
        mock_operand.__str__ = Mock(return_value='DifferentRoutine')
        mock_jsr.operands = [mock_operand]

        routine._instructions = [mock_jsr]

        result = routine.check_for_jsr('SubRoutine1')
        self.assertFalse(result)

    def test_check_for_jsr_no_operands(self):
        """Test check_for_jsr method when JSR has no operands."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        # Mock JSR instruction with no operands
        mock_jsr = Mock(spec=LogixInstruction)
        mock_jsr.type = LogixInstructionType.JSR
        mock_jsr.operands = []

        routine._instructions = [mock_jsr]

        result = routine.check_for_jsr('SubRoutine1')
        self.assertFalse(result)

    def test_check_for_jsr_no_instructions(self):
        """Test check_for_jsr method with no instructions."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        routine._instructions = []

        result = routine.check_for_jsr('SubRoutine1')
        self.assertFalse(result)


class TestRoutineRungMethods(unittest.TestCase):
    """Test Routine rung management methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.mock_controller.config = Mock()
        self.mock_controller.config.rung_type = Mock()

        self.basic_routine_meta = {
            '@Name': 'TestRoutine',
            '@Type': 'RLL',
            'Description': 'Test routine description',
            'RLLContent': {
                'Rung': []
            }
        }

    def test_rungs_property_compiles_when_empty(self):
        """Test rungs property compiles when _rungs is empty."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        with patch.object(routine, '_compile_rungs') as mock_compile:
            _ = routine.rungs
            mock_compile.assert_called_once()

    def test_rungs_property_returns_cached(self):
        """Test rungs property returns cached value when available."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        mock_rung = Mock(spec=Rung)
        routine._rungs = [mock_rung]

        with patch.object(routine, '_compile_rungs') as mock_compile:
            result = routine.rungs
            mock_compile.assert_not_called()
            self.assertEqual(result, [mock_rung])

    def test_add_rung_to_end(self):
        """Test add_rung method adding to end."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        mock_rung = Mock(spec=Rung)
        mock_rung.meta_data = {
            '@Number': '1',
            'Text': 'XIC(Input)OTE(Output);'
        }

        with patch.object(routine, '_invalidate') as mock_invalidate:
            routine.add_rung(mock_rung)

            self.assertEqual(len(routine.raw_rungs), 1)
            self.assertEqual(routine.raw_rungs[0], mock_rung.meta_data)
            self.assertEqual(routine.raw_rungs[0]['@Number'], '0')
            mock_invalidate.assert_called_once()

    def test_add_rung_at_index(self):
        """Test add_rung method adding at specific index."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        # Add initial rung
        initial_rung_meta = {
            '@Number': '0',
            'Text': 'XIC(Input1)OTE(Output1);'
        }
        routine.raw_rungs.append(initial_rung_meta)

        mock_rung = Mock(spec=Rung)
        mock_rung.meta_data = {
            '@Number': '1',
            'Text': 'XIC(Input2)OTE(Output2);'
        }

        with patch.object(routine, '_invalidate') as mock_invalidate:
            routine.add_rung(mock_rung, index=0)

            self.assertEqual(len(routine.raw_rungs), 2)
            self.assertEqual(routine.raw_rungs[0], mock_rung.meta_data)
            self.assertEqual(routine.raw_rungs[0]['@Number'], '0')
            self.assertEqual(routine.raw_rungs[1]['@Number'], '1')
            mock_invalidate.assert_called_once()

    def test_add_rung_invalid_type(self):
        """Test add_rung method with invalid rung type."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        with self.assertRaises(ValueError) as context:
            routine.add_rung("not a rung")

        self.assertIn("Rung must be an instance of Rung", str(context.exception))

    def test_remove_rung_by_instance(self):
        """Test remove_rung method with Rung instance."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        rung_meta = {
            '@Number': '0',
            'Text': 'XIC(Input)OTE(Output);'
        }
        routine.raw_rungs.append(rung_meta)

        mock_rung = Mock(spec=Rung)
        mock_rung.meta_data = rung_meta
        routine._rungs = [mock_rung]

        with patch.object(routine, '_invalidate') as mock_invalidate:
            routine.remove_rung(mock_rung)

            self.assertEqual(len(routine.raw_rungs), 0)
            mock_invalidate.assert_called_once()

    def test_remove_rung_by_index(self):
        """Test remove_rung method with index."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        rung_meta = {
            '@Number': '0',
            'Text': 'XIC(Input)OTE(Output);'
        }
        routine.raw_rungs.append(rung_meta)

        mock_rung = Mock(spec=Rung)
        mock_rung.meta_data = rung_meta
        routine._rungs = [mock_rung]

        with patch.object(routine, '_invalidate') as mock_invalidate:
            routine.remove_rung(0)

            self.assertEqual(len(routine.raw_rungs), 0)
            mock_invalidate.assert_called_once()

    def test_remove_rung_by_string_number(self):
        """Test remove_rung method with string number."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        rung_meta = {
            '@Number': '0',
            'Text': 'XIC(Input)OTE(Output);'
        }
        routine.raw_rungs.append(rung_meta)

        mock_rung = Mock(spec=Rung)
        mock_rung.number = '0'
        mock_rung.meta_data = rung_meta
        routine._rungs = [mock_rung]

        with patch.object(routine, '_invalidate') as mock_invalidate:
            routine.remove_rung('0')

            self.assertEqual(len(routine.raw_rungs), 0)
            mock_invalidate.assert_called_once()

    def test_remove_rung_index_out_of_range(self):
        """Test remove_rung method with out of range index."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        with self.assertRaises(IndexError) as context:
            routine.remove_rung(5)

        self.assertIn("Rung index out of range", str(context.exception))

    def test_remove_rung_invalid_type(self):
        """Test remove_rung method with invalid type."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )

        with self.assertRaises(ValueError) as context:
            routine.remove_rung({"not": "a rung"})

        self.assertIn("Rung must be an instance of Rung", str(context.exception))

    def test_clear_rungs(self):
        """Test clear_rungs method."""
        routine = Routine(
            meta_data=self.basic_routine_meta,
            controller=self.mock_controller
        )
        routine.logger = Mock()

        # Add some rungs
        routine.raw_rungs.extend([
            {'@Number': '0', 'Text': 'XIC(Input1)OTE(Output1);'},
            {'@Number': '1', 'Text': 'XIC(Input2)OTE(Output2);'}
        ])

        with patch.object(routine, '_compile_from_meta_data') as mock_compile:
            routine.clear_rungs()

            self.assertEqual(len(routine.raw_rungs), 0)
            routine.logger.debug.assert_called_once()
            mock_compile.assert_called_once()


class TestRoutineCompilationMethods(unittest.TestCase):
    """Test Routine compilation methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.mock_controller.config = Mock()
        self.mock_controller.config.rung_type = Mock()

        self.routine_with_rungs_meta = {
            '@Name': 'TestRoutine',
            '@Type': 'RLL',
            'Description': 'Test routine',
            'RLLContent': {
                'Rung': [
                    {
                        '@Number': '0',
                        'Text': 'XIC(Input1)OTE(Output1);'
                    }
                ]
            }
        }

    def test_compile_from_meta_data(self):
        """Test _compile_from_meta_data method."""
        routine = Routine(
            meta_data=self.routine_with_rungs_meta,
            controller=self.mock_controller
        )

        mock_rung = Mock(spec=Rung)
        self.mock_controller.config.rung_type.return_value = mock_rung

        routine._compile_from_meta_data()

        self.assertEqual(len(routine._rungs), 1)
        self.assertEqual(routine._rungs[0], mock_rung)
        self.mock_controller.config.rung_type.assert_called_once_with(
            meta_data=self.routine_with_rungs_meta['RLLContent']['Rung'][0],
            controller=self.mock_controller,
            routine=routine,
            rung_number=0
        )

    def test_compile_rungs(self):
        """Test _compile_rungs method."""
        routine = Routine(
            meta_data=self.routine_with_rungs_meta,
            controller=self.mock_controller
        )

        mock_rung = Mock(spec=Rung)
        self.mock_controller.config.rung_type.return_value = mock_rung

        routine._compile_rungs()

        self.assertEqual(len(routine._rungs), 1)
        self.assertEqual(routine._rungs[0], mock_rung)

    def test_compile_instructions(self):
        """Test _compile_instructions method."""
        routine = Routine(
            meta_data=self.routine_with_rungs_meta,
            controller=self.mock_controller
        )

        # Mock rungs with instructions
        mock_rung1 = Mock(spec=Rung)
        mock_rung2 = Mock(spec=Rung)

        mock_input_instr = Mock(spec=LogixInstruction)
        mock_output_instr = Mock(spec=LogixInstruction)
        mock_all_instr = Mock(spec=LogixInstruction)

        mock_rung1.input_instructions = [mock_input_instr]
        mock_rung1.output_instructions = [mock_output_instr]
        mock_rung1.instructions = [mock_all_instr]

        mock_rung2.input_instructions = []
        mock_rung2.output_instructions = []
        mock_rung2.instructions = []

        routine._rungs = [mock_rung1, mock_rung2]

        routine._compile_instructions()

        self.assertEqual(len(routine._input_instructions), 1)
        self.assertEqual(len(routine._output_instructions), 1)
        self.assertEqual(len(routine._instructions), 1)
        self.assertIn(mock_input_instr, routine._input_instructions)
        self.assertIn(mock_output_instr, routine._output_instructions)
        self.assertIn(mock_all_instr, routine._instructions)

    def test_invalidate(self):
        """Test _invalidate method."""
        routine = Routine(
            meta_data=self.routine_with_rungs_meta,
            controller=self.mock_controller
        )

        # Set up some data to be invalidated
        routine._instructions = [Mock()]
        routine._input_instructions = [Mock()]
        routine._output_instructions = [Mock()]
        routine._rungs = [Mock()]

        routine._invalidate()

        self.assertEqual(routine._instructions, [])
        self.assertEqual(routine._input_instructions, [])
        self.assertEqual(routine._output_instructions, [])
        self.assertEqual(routine._rungs, [])


class TestRoutineEdgeCases(unittest.TestCase):
    """Test Routine edge cases and error conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.mock_controller.config = Mock()

    def test_raw_rungs_with_malformed_meta_data(self):
        """Test raw_rungs property with malformed meta data."""
        malformed_meta = {
            '@Name': 'TestRoutine',
            '@Type': 'RLL',
            'RLLContent': {'Rung': None}  # None instead of list
        }

        routine = Routine(
            meta_data=malformed_meta,
            controller=self.mock_controller
        )

        # Should handle None gracefully
        raw_rungs = routine.raw_rungs
        self.assertIsInstance(raw_rungs, list)

    def test_check_for_jsr_with_none_operands(self):
        """Test check_for_jsr with None operands."""
        routine = Routine(
            meta_data={'@Name': 'Test', '@Type': 'RLL'},
            controller=self.mock_controller
        )

        mock_jsr = Mock(spec=LogixInstruction)
        mock_jsr.type = LogixInstructionType.JSR
        mock_jsr.operands = None

        routine._instructions = [mock_jsr]

        result = routine.check_for_jsr('TestRoutine')
        self.assertFalse(result)

    def test_remove_rung_string_not_found(self):
        """Test remove_rung with string number that doesn't exist."""
        routine = Routine(
            meta_data={'@Name': 'Test', '@Type': 'RLL', 'RLLContent': {'Rung': []}},
            controller=self.mock_controller
        )

        mock_rung = Mock(spec=Rung)
        mock_rung.number = '0'
        routine._rungs = [mock_rung]

        with self.assertRaises(ValueError) as context:
            routine.remove_rung('1')  # '1' does not exist
        self.assertIn("Rung with specified number not found", str(context.exception))


class TestRoutineIntegration(unittest.TestCase):
    """Integration tests for Routine class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.mock_controller.config = Mock()
        self.mock_controller.config.rung_type = Mock()

    @patch('pyrox.models.plc.routine.l5x_dict_from_file')
    def test_full_routine_lifecycle(self, mock_l5x_dict):
        """Test full routine creation and usage lifecycle."""
        routine_meta = {
            '@Name': 'MainRoutine',
            '@Type': 'RLL',
            'Description': 'Main routine for testing',
            'RLLContent': {
                'Rung': [
                    {
                        '@Number': '0',
                        'Text': 'XIC(StartButton)OTE(Motor);'
                    }
                ]
            }
        }

        mock_l5x_dict.return_value = {'Routine': routine_meta}

        # Create routine
        routine = Routine(controller=self.mock_controller)

        # Verify properties
        self.assertEqual(routine.name, 'MainRoutine')
        self.assertEqual(routine['@Type'], 'RLL')

        # Test rung operations
        self.assertEqual(len(routine.raw_rungs), 1)
        self.assertEqual(routine.raw_rungs[0]['@Number'], '0')


if __name__ == '__main__':
    unittest.main()

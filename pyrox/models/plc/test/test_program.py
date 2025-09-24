"""Unit tests for pyrox.models.plc.program module."""

import pytest
from unittest.mock import Mock, patch

from pyrox.models.abc.list import HashList
from pyrox.models.plc.program import Program
from pyrox.models.plc import Controller, Routine, LogixInstruction


@pytest.fixture
def mock_controller():
    """Mock controller fixture."""
    controller = Mock(spec=Controller)
    controller.name = "TestController"
    return controller


@pytest.fixture
def basic_program_meta():
    """Basic program metadata fixture."""
    return {
        '@Name': 'TestProgram',
        '@TestEdits': 'false',
        '@MainRoutineName': 'MainRoutine',
        '@Disabled': 'false',
        '@Class': 'Standard',
        '@UseAsFolder': 'false',
        'Description': 'Test program description',
        'Tags': {},
        'Routines': {}
    }


@pytest.fixture
def program_with_routines_meta():
    """Program metadata with routines fixture."""
    return {
        '@Name': 'TestProgram',
        '@TestEdits': 'false',
        '@MainRoutineName': 'MainRoutine',
        '@Disabled': 'false',
        '@Class': 'Standard',
        '@UseAsFolder': 'false',
        'Description': 'Test program description',
        'Tags': {},
        'Routines': {
            'Routine': [
                {
                    '@Name': 'MainRoutine',
                    '@Type': 'RLL',
                    'RLLContent': {'Rung': []}
                },
                {
                    '@Name': 'SubRoutine1',
                    '@Type': 'RLL',
                    'RLLContent': {'Rung': []}
                }
            ]
        }
    }


@pytest.fixture
def mock_routine():
    """Mock routine fixture."""
    routine = Mock(spec=Routine)
    routine.name = "TestRoutine"
    routine.get_instructions.return_value = []
    return routine


@pytest.fixture
def mock_jsr_instruction():
    """Mock JSR instruction fixture."""
    instruction = Mock(spec=LogixInstruction)
    instruction.name = "JSR"
    instruction.operands = [Mock(meta_data="SubRoutine1")]
    instruction.operand_value = "SubRoutine1"

    # Mock rung
    rung = Mock()
    rung.text = "JSR(SubRoutine1);"
    instruction.rung = rung

    return instruction


class TestProgramInit:
    """Test Program initialization."""

    @patch('pyrox.models.plc.program.l5x_dict_from_file')
    def test_init_with_meta_data(self, mock_l5x_dict, mock_controller, basic_program_meta):
        """Test Program initialization with provided meta_data."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)

        assert program['@Name'] == 'TestProgram'
        assert program.controller == mock_controller
        mock_l5x_dict.assert_not_called()

    @patch('pyrox.models.plc.program.l5x_dict_from_file')
    def test_init_without_meta_data(self, mock_l5x_dict, mock_controller, basic_program_meta):
        """Test Program initialization without meta_data loads from file."""
        mock_l5x_dict.return_value = {'Program': basic_program_meta}

        program = Program(controller=mock_controller)

        mock_l5x_dict.assert_called_once()
        assert program['@Name'] == 'TestProgram'

    def test_init_with_none_meta_data(self, mock_controller, basic_program_meta):
        """Test Program initialization with None meta_data."""
        with patch('pyrox.models.plc.program.l5x_dict_from_file') as mock_l5x_dict:
            mock_l5x_dict.return_value = {'Program': basic_program_meta}
            _ = Program(meta_data=None, controller=mock_controller)
            mock_l5x_dict.assert_called_once()

    def test_init_without_controller(self, basic_program_meta):
        """Test Program initialization without controller."""
        program = Program(meta_data=basic_program_meta)
        assert program.controller is None


class TestProgramProperties:
    """Test Program properties."""

    def test_dict_key_order(self, basic_program_meta, mock_controller):
        """Test dict_key_order property returns correct order."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)

        expected_order = [
            '@Name',
            '@TestEdits',
            '@MainRoutineName',
            '@Disabled',
            '@Class',
            '@UseAsFolder',
            'Description',
            'Tags',
            'Routines',
        ]

        assert program.dict_key_order == expected_order

    def test_disabled_property(self, basic_program_meta, mock_controller):
        """Test disabled property."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)
        assert program.disabled == 'false'

    def test_test_edits_property(self, basic_program_meta, mock_controller):
        """Test test_edits property."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)
        assert program.test_edits == 'false'

    def test_main_routine_name_property(self, basic_program_meta, mock_controller):
        """Test main_routine_name property."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)
        assert program.main_routine_name == 'MainRoutine'

    def test_use_as_folder_property(self, basic_program_meta, mock_controller):
        """Test use_as_folder property."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)
        assert program.use_as_folder == 'false'

    def test_main_routine_property_exists(self, program_with_routines_meta):
        """Test main_routine property when routine exists."""
        program = Program(meta_data=program_with_routines_meta)
        program.invalidate()

        assert program.main_routine.name == 'MainRoutine'

    def test_main_routine_property_not_exists(self, basic_program_meta):
        """Test main_routine property when routine doesn't exist."""
        program = Program(meta_data=basic_program_meta)
        program.invalidate()

        assert program.main_routine is None

    def test_main_routine_property_no_name(self, mock_controller):
        """Test main_routine property when no main routine name."""
        meta_data = {
            '@Name': 'TestProgram',
            '@MainRoutineName': '',
            'Routines': {}
        }
        program = Program(meta_data=meta_data, controller=mock_controller)

        assert program.main_routine is None


class TestProgramMethods:
    """Test Program methods."""

    def test_get_instructions_with_filter(self, program_with_routines_meta):
        """Test get_instructions with instruction filter."""
        program_with_routines_meta['Routines']['Routine'][0]['RLLContent']['Rung'] = [
            {'Number': '0', 'Type': 'N', 'Text': 'JSR(test);'}
        ]
        program_with_routines_meta['Routines']['Routine'][1]['RLLContent']['Rung'] = [
            {'Number': '0', 'Type': 'N', 'Text': 'JSR(test);'}
        ]

        program = Program(
            meta_data=program_with_routines_meta,
            controller=None
        )
        program._invalidate()

        # Mock the routines property directly to avoid HashList issues
        result = program.get_instructions(instruction_filter='JSR', operand_filter='test')

        assert len(result) == 2

    def test_get_instructions_no_routines(self, basic_program_meta, mock_controller):
        """Test get_instructions with no routines."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)
        program.routines.clear()

        result = program.get_instructions(instruction_filter='JSR')

        assert result == []

    def test_get_instructions_empty_results(self, basic_program_meta, mock_controller):
        """Test get_instructions when routines return empty results."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)

        mock_routine = Mock(spec=Routine)
        mock_routine.get_instructions.return_value = []
        program.routines.append(mock_routine)

        result = program.get_instructions(instruction_filter='JSR')

        assert result == []


class TestProgramBlockRoutine:
    """Test Program block_routine method."""

    def test_block_routine_success(self, basic_program_meta, mock_controller, mock_jsr_instruction):
        """Test successful routine blocking."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)
        program.get_instructions = Mock(return_value=[mock_jsr_instruction])

        program.block_routine('SubRoutine1', 'BlockingBit')

        program.get_instructions.assert_called_once_with(instruction_filter='JSR')
        assert mock_jsr_instruction.rung.text == 'XIC(BlockingBit)JSR(SubRoutine1);'

    def test_block_routine_already_blocked(self, basic_program_meta, mock_controller, mock_jsr_instruction):
        """Test blocking routine that's already blocked."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)
        program.get_instructions = Mock(return_value=[mock_jsr_instruction])

        # Set rung text to already include the blocking condition
        mock_jsr_instruction.rung.text = 'XIC(BlockingBit)JSR(SubRoutine1);'
        original_text = mock_jsr_instruction.rung.text

        program.block_routine('SubRoutine1', 'BlockingBit')

        # Text should remain unchanged
        assert mock_jsr_instruction.rung.text == original_text

    def test_block_routine_no_matching_jsr(self, basic_program_meta, mock_controller, mock_jsr_instruction):
        """Test blocking routine with no matching JSR."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)
        mock_jsr_instruction.operands[0].meta_data = "DifferentRoutine"
        program.get_instructions = Mock(return_value=[mock_jsr_instruction])

        original_text = mock_jsr_instruction.rung.text
        program.block_routine('SubRoutine1', 'BlockingBit')

        # Text should remain unchanged
        assert mock_jsr_instruction.rung.text == original_text

    def test_block_routine_no_rung(self, basic_program_meta, mock_controller, mock_jsr_instruction):
        """Test blocking routine when JSR has no rung."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)
        mock_jsr_instruction.rung = None
        program.get_instructions = Mock(return_value=[mock_jsr_instruction])

        with pytest.raises(ValueError, match="JSR instruction .* has no rung!"):
            program.block_routine('SubRoutine1', 'BlockingBit')

    def test_block_routine_no_jsrs(self, basic_program_meta, mock_controller):
        """Test blocking routine with no JSR instructions."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)
        program.get_instructions = Mock(return_value=[])

        # Should not raise any exceptions
        program.block_routine('SubRoutine1', 'BlockingBit')
        program.get_instructions.assert_called_once_with(instruction_filter='JSR')


class TestProgramUnblockRoutine:
    """Test Program unblock_routine method."""

    def test_unblock_routine_success(self, basic_program_meta, mock_controller, mock_jsr_instruction):
        """Test successful routine unblocking."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)
        mock_jsr_instruction.rung.text = 'XIC(BlockingBit)JSR(SubRoutine1);'
        mock_jsr_instruction.operand_value = 'SubRoutine1'
        program.get_instructions = Mock(return_value=[mock_jsr_instruction])

        program.unblock_routine('SubRoutine1', 'BlockingBit')

        program.get_instructions.assert_called_once_with(instruction_filter='JSR')
        assert mock_jsr_instruction.rung.text == 'JSR(SubRoutine1);'

    def test_unblock_routine_not_blocked(self, basic_program_meta, mock_controller, mock_jsr_instruction):
        """Test unblocking routine that's not blocked."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)
        mock_jsr_instruction.operand_value = 'SubRoutine1'
        original_text = mock_jsr_instruction.rung.text
        program.get_instructions = Mock(return_value=[mock_jsr_instruction])

        program.unblock_routine('SubRoutine1', 'BlockingBit')

        # Text should remain unchanged since it doesn't start with XIC(BlockingBit)
        assert mock_jsr_instruction.rung.text == original_text

    def test_unblock_routine_no_matching_jsr(self, basic_program_meta, mock_controller, mock_jsr_instruction):
        """Test unblocking routine with no matching JSR."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)
        mock_jsr_instruction.operand_value = 'DifferentRoutine'
        original_text = mock_jsr_instruction.rung.text
        program.get_instructions = Mock(return_value=[mock_jsr_instruction])

        program.unblock_routine('SubRoutine1', 'BlockingBit')

        # Text should remain unchanged
        assert mock_jsr_instruction.rung.text == original_text

    def test_unblock_routine_no_rung(self, basic_program_meta, mock_controller, mock_jsr_instruction):
        """Test unblocking routine when JSR has no rung."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)
        mock_jsr_instruction.rung = None
        mock_jsr_instruction.operand_value = 'SubRoutine1'
        program.get_instructions = Mock(return_value=[mock_jsr_instruction])

        with pytest.raises(ValueError, match="JSR instruction .* has no rung!"):
            program.unblock_routine('SubRoutine1', 'BlockingBit')

    def test_unblock_routine_partial_match_blocking_bit(self, basic_program_meta, mock_controller, mock_jsr_instruction):
        """Test unblocking when blocking bit appears elsewhere in text."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)
        mock_jsr_instruction.rung.text = 'XIC(OtherBit)XIC(BlockingBit)JSR(SubRoutine1);'
        mock_jsr_instruction.operand_value = 'SubRoutine1'
        original_text = mock_jsr_instruction.rung.text
        program.get_instructions = Mock(return_value=[mock_jsr_instruction])

        program.unblock_routine('SubRoutine1', 'BlockingBit')

        # Text should remain unchanged since it doesn't START with XIC(BlockingBit)
        assert mock_jsr_instruction.rung.text == original_text

    def test_unblock_routine_multiple_occurrences(self, basic_program_meta, mock_controller, mock_jsr_instruction):
        """Test unblocking only removes first occurrence."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)
        mock_jsr_instruction.rung.text = 'XIC(BlockingBit)XIC(BlockingBit)JSR(SubRoutine1);'
        mock_jsr_instruction.operand_value = 'SubRoutine1'
        program.get_instructions = Mock(return_value=[mock_jsr_instruction])

        program.unblock_routine('SubRoutine1', 'BlockingBit')

        # Should only remove the first occurrence
        assert mock_jsr_instruction.rung.text == 'XIC(BlockingBit)JSR(SubRoutine1);'


class TestProgramEdgeCases:
    """Test Program edge cases and error conditions."""

    def test_missing_properties_in_meta_data(self, mock_controller):
        """Test handling of missing properties in meta_data."""
        incomplete_meta = {'@Name': 'TestProgram'}

        # Should not raise exceptions
        program = Program(meta_data=incomplete_meta, controller=mock_controller)
        _ = program.disabled

    def test_block_unblock_with_special_characters(self, basic_program_meta, mock_controller, mock_jsr_instruction):
        """Test blocking/unblocking with special characters in names."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)

        # Test with routine name containing special characters
        mock_jsr_instruction.operands[0].meta_data = "Sub_Routine.1"
        mock_jsr_instruction.operand_value = "Sub_Routine.1"
        program.get_instructions = Mock(return_value=[mock_jsr_instruction])

        program.block_routine('Sub_Routine.1', 'Block_Bit.1')

        assert 'XIC(Block_Bit.1)' in mock_jsr_instruction.rung.text

    def test_empty_routine_name_block_unblock(self, basic_program_meta, mock_controller):
        """Test blocking/unblocking with empty routine name."""
        program = Program(meta_data=basic_program_meta, controller=mock_controller)
        program.get_instructions = Mock(return_value=[])

        # Should handle gracefully
        program.block_routine('', 'BlockingBit')
        program.unblock_routine('', 'BlockingBit')


# Integration-style tests
class TestProgramIntegration:
    """Integration tests for Program class."""

    @patch('pyrox.models.plc.program.l5x_dict_from_file')
    def test_full_program_lifecycle(self, mock_l5x_dict, mock_controller, program_with_routines_meta):
        """Test full program creation and usage lifecycle."""
        mock_l5x_dict.return_value = {'Program': program_with_routines_meta}

        # Create program
        program = Program(controller=mock_controller)

        # Verify properties
        assert program.name == 'TestProgram'
        assert program.main_routine_name == 'MainRoutine'
        assert program.disabled == 'false'

        # Test instruction operations
        program.get_instructions = Mock(return_value=[])
        instructions = program.get_instructions('JSR')
        assert instructions == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

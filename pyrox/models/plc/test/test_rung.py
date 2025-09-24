"""Unit tests for pyrox.models.plc.rung module."""

import unittest
from unittest.mock import Mock, patch

from pyrox.models.plc.rung import Rung, RungElement, RungBranch, RungElementType
from pyrox.models.plc import Controller, Routine
from pyrox.models.plc.instruction import LogixInstruction
from pyrox.models.plc.meta import LogixInstructionType


class TestRungElementType(unittest.TestCase):
    """Test RungElementType enum."""

    def test_enum_values(self):
        """Test that enum has correct values."""
        self.assertEqual(RungElementType.INSTRUCTION.value, "instruction")
        self.assertEqual(RungElementType.BRANCH_START.value, "branch_start")
        self.assertEqual(RungElementType.BRANCH_END.value, "branch_end")
        self.assertEqual(RungElementType.BRANCH_NEXT.value, "branch_next")


class TestRungElement(unittest.TestCase):
    """Test RungElement dataclass."""

    def test_rung_element_creation(self):
        """Test RungElement creation with all parameters."""
        mock_instruction = Mock(spec=LogixInstruction)
        mock_rung = Mock(spec=Rung)

        element = RungElement(
            element_type=RungElementType.INSTRUCTION,
            instruction=mock_instruction,
            branch_id="test_branch",
            root_branch_id="root_branch",
            branch_level=1,
            position=5,
            rung=mock_rung,
            rung_number=2
        )

        self.assertEqual(element.element_type, RungElementType.INSTRUCTION)
        self.assertEqual(element.instruction, mock_instruction)
        self.assertEqual(element.branch_id, "test_branch")
        self.assertEqual(element.root_branch_id, "root_branch")
        self.assertEqual(element.branch_level, 1)
        self.assertEqual(element.position, 5)
        self.assertEqual(element.rung, mock_rung)
        self.assertEqual(element.rung_number, 2)

    def test_rung_element_defaults(self):
        """Test RungElement creation with default values."""
        element = RungElement(element_type=RungElementType.BRANCH_START)

        self.assertEqual(element.element_type, RungElementType.BRANCH_START)
        self.assertIsNone(element.instruction)
        self.assertIsNone(element.branch_id)
        self.assertIsNone(element.root_branch_id)
        self.assertEqual(element.branch_level, 0)
        self.assertEqual(element.position, 0)
        self.assertIsNone(element.rung)
        self.assertEqual(element.rung_number, 0)


class TestRungBranch(unittest.TestCase):
    """Test RungBranch dataclass."""

    def test_rung_branch_creation(self):
        """Test RungBranch creation with all parameters."""
        nested_branch = RungBranch(
            branch_id="nested_1",
            start_position=3,
            end_position=5
        )

        branch = RungBranch(
            branch_id="main_branch",
            start_position=1,
            end_position=10,
            root_branch_id="root",
            nested_branches=[nested_branch]
        )

        self.assertEqual(branch.branch_id, "main_branch")
        self.assertEqual(branch.start_position, 1)
        self.assertEqual(branch.end_position, 10)
        self.assertEqual(branch.root_branch_id, "root")
        self.assertEqual(len(branch.nested_branches), 1)
        self.assertEqual(branch.nested_branches[0], nested_branch)

    def test_rung_branch_defaults(self):
        """Test RungBranch creation with default values."""
        branch = RungBranch(
            branch_id="test_branch",
            start_position=0,
            end_position=5
        )

        self.assertEqual(branch.branch_id, "test_branch")
        self.assertEqual(branch.start_position, 0)
        self.assertEqual(branch.end_position, 5)
        self.assertIsNone(branch.root_branch_id)
        self.assertEqual(len(branch.nested_branches), 0)


class TestRungInit(unittest.TestCase):
    """Test Rung initialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.mock_controller.name = "TestController"

        self.mock_routine = Mock(spec=Routine)
        self.mock_routine.name = "TestRoutine"

        self.basic_rung_meta = {
            '@Number': '0',
            '@Type': 'N',
            'Text': 'XIC(Input1)OTE(Output1);',
            'Comment': 'Test rung comment'
        }

        self.empty_rung_meta = {
            '@Number': '0',
            '@Type': 'N',
            'Text': '',
            'Comment': ''
        }

    @patch('pyrox.models.plc.rung.l5x_dict_from_file')
    def test_init_with_meta_data(self, mock_l5x_dict):
        """Test Rung initialization with provided meta_data."""
        rung = Rung(
            meta_data=self.basic_rung_meta,
            controller=self.mock_controller,
            routine=self.mock_routine
        )

        self.assertEqual(rung['@Number'], '0')
        self.assertEqual(rung.controller, self.mock_controller)
        self.assertEqual(rung.routine, self.mock_routine)
        mock_l5x_dict.assert_not_called()

    @patch('pyrox.models.plc.rung.l5x_dict_from_file')
    def test_init_without_meta_data(self, mock_l5x_dict):
        """Test Rung initialization without meta_data loads from file."""
        mock_l5x_dict.return_value = {'Rung': self.basic_rung_meta}

        rung = Rung(controller=self.mock_controller)

        mock_l5x_dict.assert_called_once()
        self.assertEqual(rung['@Number'], '0')

    def test_init_with_parameters(self):
        """Test Rung initialization with direct parameters."""
        rung = Rung(
            meta_data=self.basic_rung_meta,
            controller=self.mock_controller,
            routine=self.mock_routine,
            rung_number=5,
            text="XIC(Test)OTE(Output);",
            comment="Custom comment"
        )

        self.assertEqual(rung.number, '5')
        self.assertEqual(rung.text, "XIC(Test)OTE(Output);")
        self.assertEqual(rung.comment, "Custom comment")

    def test_init_sets_private_attributes(self):
        """Test that initialization properly sets private attributes."""
        rung = Rung(
            meta_data=self.basic_rung_meta,
            controller=self.mock_controller
        )

        self.assertIsInstance(rung._instructions, list)
        self.assertIsInstance(rung._rung_sequence, list)
        self.assertIsInstance(rung._branches, dict)
        self.assertEqual(rung._branch_id_counter, 0)

    def test_init_with_empty_text(self):
        """Test initialization with empty text."""
        rung = Rung(
            meta_data=self.empty_rung_meta,
            controller=self.mock_controller
        )

        self.assertEqual(rung.text, '')
        self.assertEqual(len(rung._instructions), 0)


class TestRungEquality(unittest.TestCase):
    """Test Rung equality methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.rung_meta = {
            '@Number': '0',
            '@Type': 'N',
            'Text': 'XIC(Input1)OTE(Output1);',
            'Comment': 'Test comment'
        }

    def test_equality_same_text(self):
        """Test equality when rungs have same text."""
        rung1 = Rung(meta_data=self.rung_meta, controller=self.mock_controller)
        rung2 = Rung(meta_data=self.rung_meta.copy(), controller=self.mock_controller)

        self.assertEqual(rung1, rung2)

    def test_equality_different_text(self):
        """Test inequality when rungs have different text."""
        rung1 = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        different_meta = self.rung_meta.copy()
        different_meta['Text'] = 'XIO(Input2)OTL(Output2);'
        rung2 = Rung(meta_data=different_meta, controller=self.mock_controller)

        self.assertNotEqual(rung1, rung2)

    def test_equality_different_type(self):
        """Test inequality when comparing with different type."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        self.assertNotEqual(rung, "not a rung")
        self.assertNotEqual(rung, 123)
        self.assertNotEqual(rung, None)


class TestRungProperties(unittest.TestCase):
    """Test Rung properties."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.mock_routine = Mock(spec=Routine)

        self.rung_meta = {
            '@Number': '5',
            '@Type': 'N',
            'Text': 'XIC(Input1)OTE(Output1);',
            'Comment': 'Test rung comment'
        }

    def test_dict_key_order(self):
        """Test dict_key_order property."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        expected_order = ['@Number', '@Type', 'Comment', 'Text']
        self.assertEqual(rung.dict_key_order, expected_order)

    def test_comment_property(self):
        """Test comment property getter and setter."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        self.assertEqual(rung.comment, 'Test rung comment')

        rung.comment = 'New comment'
        self.assertEqual(rung.comment, 'New comment')
        self.assertEqual(rung['Comment'], 'New comment')

    def test_number_property(self):
        """Test number property getter and setter."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        self.assertEqual(rung.number, '5')

        rung.number = 10
        self.assertEqual(rung.number, '10')

        rung.number = '15'
        self.assertEqual(rung.number, '15')

    def test_number_property_invalid_type(self):
        """Test number property with invalid type."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        with self.assertRaises(ValueError) as context:
            rung.number = []

        self.assertIn("Rung number must be a string or int", str(context.exception))

    def test_text_property(self):
        """Test text property getter and setter."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        self.assertEqual(rung.text, 'XIC(Input1)OTE(Output1);')

        rung.text = 'XIO(Input2)OTL(Output2)'
        self.assertEqual(rung.text, 'XIO(Input2)OTL(Output2);')  # Should add semicolon

    def test_text_property_empty(self):
        """Test text property with empty text."""
        meta = self.rung_meta.copy()
        meta['Text'] = None
        rung = Rung(meta_data=meta, controller=self.mock_controller)

        self.assertEqual(rung.text, '')

    def test_routine_property(self):
        """Test routine property getter and setter."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        self.assertIsNone(rung.routine)

        rung.routine = self.mock_routine
        self.assertEqual(rung.routine, self.mock_routine)

    def test_container_property(self):
        """Test container property."""
        rung = Rung(
            meta_data=self.rung_meta,
            controller=self.mock_controller,
            routine=self.mock_routine
        )

        mock_container = Mock()
        self.mock_routine.container = mock_container

        self.assertEqual(rung.container, mock_container)

    def test_container_property_no_routine(self):
        """Test container property when no routine."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        self.assertIsNone(rung.container)

    def test_type_property(self):
        """Test type property."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        self.assertEqual(rung.type, 'N')


class TestRungInstructionExtraction(unittest.TestCase):
    """Test Rung instruction extraction methods."""

    def test_extract_instructions_simple(self):
        """Test extraction of simple instructions."""
        text = "XIC(Input1)XIO(Input2)OTE(Output1);"
        instructions = Rung._extract_instructions(text)

        expected = ["XIC(Input1)", "XIO(Input2)", "OTE(Output1)"]
        self.assertEqual(instructions, expected)

    def test_extract_instructions_nested_parentheses(self):
        """Test extraction with nested parentheses."""
        text = "MOV(Array[0],Dest)EQU(Value[Index],Target);"
        instructions = Rung._extract_instructions(text)

        expected = ["MOV(Array[0],Dest)", "EQU(Value[Index],Target)"]
        self.assertEqual(instructions, expected)

    def test_extract_instructions_complex_operands(self):
        """Test extraction with complex operands."""
        text = "ADD(Tag.Value[Index],Constant,Result.Data);"
        instructions = Rung._extract_instructions(text)

        expected = ["ADD(Tag.Value[Index],Constant,Result.Data)"]
        self.assertEqual(instructions, expected)

    def test_extract_instructions_empty_text(self):
        """Test extraction from empty text."""
        instructions = Rung._extract_instructions("")
        self.assertEqual(instructions, [])

    def test_extract_instructions_with_branches(self):
        """Test extraction with branch markers."""
        text = "XIC(Input1)[XIO(Input2),XIC(Input3)]OTE(Output1);"
        instructions = Rung._extract_instructions(text)

        expected = ["XIC(Input1)", "XIO(Input2)", "XIC(Input3)", "OTE(Output1)"]
        self.assertEqual(instructions, expected)


class TestRungTokenization(unittest.TestCase):
    """Test Rung tokenization methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.rung_meta = {
            '@Number': '0',
            '@Type': 'N',
            'Text': '',
            'Comment': ''
        }

    def test_tokenize_simple_instructions(self):
        """Test tokenization of simple instructions."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        text = "XIC(Input1)XIO(Input2)OTE(Output1);"
        tokens = rung._tokenize_rung_text(text)

        expected = ["XIC(Input1)", "XIO(Input2)", "OTE(Output1)"]
        self.assertEqual(tokens, expected)

    def test_tokenize_with_branches(self):
        """Test tokenization with branch structures."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        text = "XIC(Input1)[XIO(Input2),XIC(Input3)]OTE(Output1);"
        tokens = rung._tokenize_rung_text(text)

        expected = ["XIC(Input1)", "[", "XIO(Input2)", ",", "XIC(Input3)", "]", "OTE(Output1)"]
        self.assertEqual(tokens, expected)

    def test_tokenize_nested_branches(self):
        """Test tokenization with nested branches."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        text = "XIC(Input1)[XIO(Input2)[XIC(Input3),XIO(Input4)],XIC(Input5)]OTE(Output1);"
        tokens = rung._tokenize_rung_text(text)

        expected = [
            "XIC(Input1)", "[", "XIO(Input2)", "[", "XIC(Input3)", ",",
            "XIO(Input4)", "]", ",", "XIC(Input5)", "]", "OTE(Output1)"
        ]
        self.assertEqual(tokens, expected)

    def test_tokenize_array_references(self):
        """Test tokenization preserves array references in instructions."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        text = "MOV(Array[0],Dest[1]);"
        tokens = rung._tokenize_rung_text(text)

        expected = ["MOV(Array[0],Dest[1])"]
        self.assertEqual(tokens, expected)

    def test_tokenize_empty_text(self):
        """Test tokenization of empty text."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        tokens = rung._tokenize_rung_text("")
        self.assertEqual(tokens, [])


class TestRungSequenceBuilding(unittest.TestCase):
    """Test Rung sequence building methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.mock_instruction = Mock(spec=LogixInstruction)
        self.mock_instruction.meta_data = "XIC(Input1)"

        self.rung_meta = {
            '@Number': '0',
            '@Type': 'N',
            'Text': 'XIC(Input1)OTE(Output1);',
            'Comment': ''
        }

    @patch('pyrox.models.plc.rung.LogixInstruction')
    def test_build_sequence_simple_instructions(self, mock_logix_instruction):
        """Test building sequence with simple instructions."""
        mock_logix_instruction.return_value = self.mock_instruction

        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        # Should have 2 instruction elements
        instruction_elements = [elem for elem in rung._rung_sequence
                                if elem.element_type == RungElementType.INSTRUCTION]
        self.assertEqual(len(instruction_elements), 2)

    @patch('pyrox.models.plc.rung.LogixInstruction')
    def test_build_sequence_with_branches(self, mock_logix_instruction):
        """Test building sequence with branches."""
        mock_logix_instruction.return_value = self.mock_instruction

        branch_meta = self.rung_meta.copy()
        branch_meta['Text'] = 'XIC(Input1)[XIO(Input2),XIC(Input3)]OTE(Output1);'

        rung = Rung(meta_data=branch_meta, controller=self.mock_controller)

        # Should have branch start, next, and end elements
        branch_starts = [elem for elem in rung._rung_sequence
                         if elem.element_type == RungElementType.BRANCH_START]
        branch_nexts = [elem for elem in rung._rung_sequence
                        if elem.element_type == RungElementType.BRANCH_NEXT]
        branch_ends = [elem for elem in rung._rung_sequence
                       if elem.element_type == RungElementType.BRANCH_END]

        self.assertEqual(len(branch_starts), 1)
        self.assertEqual(len(branch_nexts), 1)
        self.assertEqual(len(branch_ends), 1)

    def test_get_unique_branch_id(self):
        """Test unique branch ID generation."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        id1 = rung._get_unique_branch_id()
        id2 = rung._get_unique_branch_id()

        self.assertNotEqual(id1, id2)
        self.assertIn("rung_0_branch", id1)
        self.assertIn("rung_0_branch", id2)


class TestRungInstructionMethods(unittest.TestCase):
    """Test Rung instruction-related methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.rung_meta = {
            '@Number': '0',
            '@Type': 'N',
            'Text': 'XIC(Input1)XIO(Input2)OTE(Output1);',
            'Comment': ''
        }

    def test_instructions_property(self):
        """Test instructions property."""
        mock_instr1 = Mock(spec=LogixInstruction)
        mock_instr1.meta_data = "XIC(Input1)"
        mock_instr1.type = LogixInstructionType.INPUT

        mock_instr2 = Mock(spec=LogixInstruction)
        mock_instr2.meta_data = "XIO(Input2)"
        mock_instr2.type = LogixInstructionType.INPUT

        mock_instr3 = Mock(spec=LogixInstruction)
        mock_instr3.meta_data = "OTE(Output1)"
        mock_instr3.type = LogixInstructionType.OUTPUT

        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        self.assertEqual(len(rung.instructions), 3)
        self.assertEqual(rung.instructions[0].meta_data, mock_instr1.meta_data)
        self.assertEqual(rung.instructions[1].meta_data, mock_instr2.meta_data)
        self.assertEqual(rung.instructions[2].meta_data, mock_instr3.meta_data)

    @patch('pyrox.models.plc.rung.LogixInstruction')
    def test_input_instructions_property(self, mock_logix_instruction):
        """Test input_instructions property."""
        mock_instr1 = Mock(spec=LogixInstruction)
        mock_instr1.type = LogixInstructionType.INPUT

        mock_instr2 = Mock(spec=LogixInstruction)
        mock_instr2.type = LogixInstructionType.OUTPUT

        mock_logix_instruction.side_effect = [mock_instr1, mock_instr2, mock_instr1]

        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        input_instructions = rung.input_instructions
        self.assertEqual(len(input_instructions), 2)
        self.assertEqual(input_instructions[0].type, LogixInstructionType.INPUT)

    @patch('pyrox.models.plc.rung.LogixInstruction')
    def test_output_instructions_property(self, mock_logix_instruction):
        """Test output_instructions property."""
        mock_instr1 = Mock(spec=LogixInstruction)
        mock_instr1.type = LogixInstructionType.INPUT

        mock_instr2 = Mock(spec=LogixInstruction)
        mock_instr2.type = LogixInstructionType.OUTPUT

        mock_logix_instruction.side_effect = [mock_instr1, mock_instr2, mock_instr1]

        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        output_instructions = rung.output_instructions
        self.assertEqual(len(output_instructions), 1)
        self.assertEqual(output_instructions[0].type, LogixInstructionType.OUTPUT)

    def test_get_instructions_with_filter(self):
        """Test get_instructions method with filters."""
        mock_instr1 = Mock(spec=LogixInstruction)
        mock_instr1.instruction_name = "XIC"
        mock_operand1 = Mock()
        mock_operand1.meta_data = "Input1"
        mock_instr1.operands = [mock_operand1]

        mock_instr2 = Mock(spec=LogixInstruction)
        mock_instr2.instruction_name = "OTE"
        mock_operand2 = Mock()
        mock_operand2.meta_data = "Output1"
        mock_instr2.operands = [mock_operand2]

        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        # Filter by instruction name
        xic_instructions = rung.get_instructions(instruction_filter="XIC")
        self.assertEqual(len(xic_instructions), 1)

        # Filter by operand
        input1_instructions = rung.get_instructions(operand_filter="Input1")
        self.assertEqual(len(input1_instructions), 1)

    def test_get_instruction_count(self):
        """Test get_instruction_count method."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        # Mock the instructions property
        mock_instructions = [Mock(), Mock(), Mock()]
        rung._instructions = mock_instructions

        self.assertEqual(rung.get_instruction_count(), 3)

    def test_get_instruction_at_position(self):
        """Test get_instruction_at_position method."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        mock_instr1 = Mock(spec=LogixInstruction)
        mock_instr2 = Mock(spec=LogixInstruction)
        rung._instructions = [mock_instr1, mock_instr2]

        self.assertEqual(rung.get_instruction_at_position(0), mock_instr1)
        self.assertEqual(rung.get_instruction_at_position(1), mock_instr2)
        self.assertIsNone(rung.get_instruction_at_position(2))
        self.assertIsNone(rung.get_instruction_at_position(-1))

    def test_get_instruction_summary(self):
        """Test get_instruction_summary method."""
        mock_instr1 = Mock(spec=LogixInstruction)
        mock_instr1.instruction_name = "XIC"

        mock_instr2 = Mock(spec=LogixInstruction)
        mock_instr2.instruction_name = "XIO"

        mock_instr3 = Mock(spec=LogixInstruction)
        mock_instr3.instruction_name = "OTE"

        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        summary = rung.get_instruction_summary()
        expected = {"XIC": 1, 'XIO': 1, "OTE": 1}
        self.assertEqual(summary, expected)


class TestRungInstructionManipulation(unittest.TestCase):
    """Test Rung instruction manipulation methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.rung_meta = {
            '@Number': '0',
            '@Type': 'N',
            'Text': 'XIC(Input1)OTE(Output1);',
            'Comment': ''
        }

    def test_add_instruction_to_empty_rung(self):
        """Test adding instruction to empty rung."""
        empty_meta = self.rung_meta.copy()
        empty_meta['Text'] = ''

        rung = Rung(meta_data=empty_meta, controller=self.mock_controller)

        rung.add_instruction("XIC(Input1)")
        self.assertEqual(rung.text, "XIC(Input1);")

    def test_add_instruction_at_position(self):
        """Test adding instruction at specific position."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        with patch.object(rung, '_tokenize_rung_text') as mock_tokenize:
            mock_tokenize.return_value = ["XIC(Input1)", "OTE(Output1)"]

            rung.add_instruction("XIO(Input2)", position=1)

            mock_tokenize.assert_called()
            # Verify text was updated
            self.assertIn("XIO(Input2)", rung.text)

    def test_add_instruction_invalid_format(self):
        """Test adding instruction with invalid format."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        with self.assertRaises(ValueError) as context:
            rung.add_instruction("INVALID_FORMAT")

        self.assertIn("Invalid instruction format", str(context.exception))

    def test_add_instruction_empty_string(self):
        """Test adding empty instruction string."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        with self.assertRaises(ValueError) as context:
            rung.add_instruction("")

        self.assertIn("Instruction text must be a non-empty string", str(context.exception))

    def test_remove_instruction_by_text(self):
        """Test removing instruction by text."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        with patch.object(rung, '_find_instruction_index_in_text') as mock_find:
            with patch.object(rung, '_tokenize_rung_text') as mock_tokenize:
                mock_find.return_value = 0
                mock_tokenize.return_value = ["XIC(Input1)", "OTE(Output1)"]

                rung.remove_instruction("XIC(Input1)")

                mock_find.assert_called_once_with("XIC(Input1)", 0)

    def test_remove_instruction_by_index(self):
        """Test removing instruction by index."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        with patch.object(rung, '_tokenize_rung_text') as mock_tokenize:
            mock_tokenize.return_value = ["XIC(Input1)", "OTE(Output1)"]

            rung.remove_instruction(0)

            # Should rebuild text without first instruction
            self.assertNotIn("XIC(Input1)", rung.text)

    def test_remove_instruction_index_out_of_range(self):
        """Test removing instruction with out of range index."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        with patch.object(rung, '_tokenize_rung_text') as mock_tokenize:
            mock_tokenize.return_value = ["XIC(Input1)"]

            with self.assertRaises(IndexError) as context:
                rung.remove_instruction(5)

            self.assertIn("Instruction index 5 out of range", str(context.exception))

    def test_remove_instruction_empty_rung(self):
        """Test removing instruction from empty rung."""
        empty_meta = self.rung_meta.copy()
        empty_meta['Text'] = ''

        rung = Rung(meta_data=empty_meta, controller=self.mock_controller)

        with self.assertRaises(ValueError) as context:
            rung.remove_instruction("XIC(Input1)")

        self.assertIn("Cannot remove instruction from empty rung", str(context.exception))

    def test_replace_instruction_by_text(self):
        """Test replacing instruction by text."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        with patch.object(rung, '_find_instruction_index_in_text') as mock_find:
            with patch.object(rung, '_tokenize_rung_text') as mock_tokenize:
                mock_find.return_value = 0
                mock_tokenize.return_value = ["XIC(Input1)", "OTE(Output1)"]

                rung.replace_instruction("XIC(Input1)", "XIO(Input2)")

                mock_find.assert_called_once_with("XIC(Input1)", 0)

    def test_replace_instruction_invalid_format(self):
        """Test replacing instruction with invalid format."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        with self.assertRaises(ValueError) as context:
            rung.replace_instruction("XIC(Input1)", "INVALID_FORMAT")

        self.assertIn("Invalid instruction format", str(context.exception))

    def test_move_instruction_by_index(self):
        """Test moving instruction by index."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        with patch.object(rung, '_tokenize_rung_text') as mock_tokenize:
            mock_tokenize.return_value = ["XIC(Input1)", "XIO(Input2)", "OTE(Output1)"]

            rung.move_instruction(0, 2)  # Move first instruction to position 2

            # Should have reordered the tokens
            mock_tokenize.assert_called()

    def test_move_instruction_same_position(self):
        """Test moving instruction to same position."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        original_text = rung.text
        rung.move_instruction(0, 0)  # Same position

        # Text should remain unchanged
        self.assertEqual(rung.text, original_text)


class TestRungBranchMethods(unittest.TestCase):
    """Test Rung branch-related methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.branch_rung_meta = {
            '@Number': '0',
            '@Type': 'N',
            'Text': 'XIC(Input1)[XIO(Input2),XIC(Input3)]OTE(Output1);',
            'Comment': ''
        }

    def test_has_branches_true(self):
        """Test has_branches method when branches exist."""
        rung = Rung(meta_data=self.branch_rung_meta, controller=self.mock_controller)

        # Mock branches
        rung._branches = {"branch_1": Mock()}

        self.assertTrue(rung.has_branches())

    def test_has_branches_false(self):
        """Test has_branches method when no branches exist."""
        simple_meta = {
            '@Number': '0',
            '@Type': 'N',
            'Text': 'XIC(Input1)OTE(Output1);',
            'Comment': ''
        }

        rung = Rung(meta_data=simple_meta, controller=self.mock_controller)

        self.assertFalse(rung.has_branches())

    def test_get_branch_count(self):
        """Test get_branch_count method."""
        rung = Rung(meta_data=self.branch_rung_meta, controller=self.mock_controller)

        # Mock branches
        rung._branches = {"branch_1": Mock(), "branch_2": Mock()}

        self.assertEqual(rung.get_branch_count(), 2)

    def test_get_max_branch_depth_no_branches(self):
        """Test get_max_branch_depth with no branches."""
        simple_meta = {
            '@Number': '0',
            '@Type': 'N',
            'Text': 'XIC(Input1)OTE(Output1);',
            'Comment': ''
        }

        rung = Rung(meta_data=simple_meta, controller=self.mock_controller)

        self.assertEqual(rung.get_max_branch_depth(), 0)

    def test_get_max_branch_depth_with_branches(self):
        """Test get_max_branch_depth with branches."""
        rung = Rung(meta_data=self.branch_rung_meta, controller=self.mock_controller)

        with patch.object(rung, '_tokenize_rung_text') as mock_tokenize:
            mock_tokenize.return_value = ["XIC(Input1)", "[", "XIO(Input2)", ",", "XIC(Input3)", "]", "OTE(Output1)"]

            depth = rung.get_max_branch_depth()
            self.assertGreaterEqual(depth, 1)

    def test_get_branch_nesting_level(self):
        """Test get_branch_nesting_level method."""
        rung = Rung(meta_data=self.branch_rung_meta, controller=self.mock_controller)

        with patch.object(rung, '_tokenize_rung_text') as mock_tokenize:
            mock_tokenize.return_value = ["XIC(Input1)", "[", "XIO(Input2)", "]", "OTE(Output1)"]

            # Position inside branch should have nesting level > 0
            level = rung.get_branch_nesting_level(2)
            self.assertGreaterEqual(level, 0)

    def test_insert_branch(self):
        """Test insert_branch method."""
        simple_meta = {
            '@Number': '0',
            '@Type': 'N',
            'Text': 'XIC(Input1)OTE(Output1);',
            'Comment': ''
        }

        rung = Rung(meta_data=simple_meta, controller=self.mock_controller)

        with patch.object(rung, '_tokenize_rung_text') as mock_tokenize:
            with patch.object(rung, '_insert_branch_tokens') as mock_insert:
                mock_tokenize.return_value = ["XIC(Input1)", "OTE(Output1)"]
                mock_insert.return_value = ["XIC(Input1)", "[", "]", "OTE(Output1)"]

                rung.insert_branch(0, 1)

                mock_insert.assert_called_once()

    def test_insert_branch_invalid_positions(self):
        """Test insert_branch with invalid positions."""
        rung = Rung(meta_data=self.branch_rung_meta, controller=self.mock_controller)

        with self.assertRaises(ValueError) as context:
            rung.insert_branch(-1, 2)

        self.assertIn("Branch positions must be non-negative", str(context.exception))

    def test_remove_branch_not_found(self):
        """Test remove_branch with non-existent branch."""
        rung = Rung(meta_data=self.branch_rung_meta, controller=self.mock_controller)

        with self.assertRaises(ValueError) as context:
            rung.remove_branch("non_existent_branch")

        self.assertIn("Branch 'non_existent_branch' not found", str(context.exception))

    def test_validate_branch_structure_valid(self):
        """Test validate_branch_structure with valid structure."""
        rung = Rung(meta_data=self.branch_rung_meta, controller=self.mock_controller)

        with patch.object(rung, '_tokenize_rung_text') as mock_tokenize:
            mock_tokenize.return_value = ["XIC(Input1)", "[", "XIO(Input2)", "]", "OTE(Output1)"]

            self.assertTrue(rung.validate_branch_structure())

    def test_validate_branch_structure_invalid(self):
        """Test validate_branch_structure with invalid structure."""
        invalid_meta = {
            '@Number': '0',
            '@Type': 'N',
            'Text': 'XIC(Input1)[XIO(Input2)OTE(Output1);',  # Missing closing bracket
            'Comment': ''
        }

        rung = Rung(meta_data=invalid_meta, controller=self.mock_controller)

        with patch.object(rung, '_tokenize_rung_text') as mock_tokenize:
            mock_tokenize.return_value = ["XIC(Input1)", "[", "XIO(Input2)", "OTE(Output1)"]

            self.assertFalse(rung.validate_branch_structure())

    def test_find_matching_branch_end(self):
        """Test find_matching_branch_end method."""
        rung = Rung(meta_data=self.branch_rung_meta, controller=self.mock_controller)

        with patch.object(rung, '_tokenize_rung_text') as mock_tokenize:
            mock_tokenize.return_value = ["XIC(Input1)", "[", "XIO(Input2)", "]", "OTE(Output1)"]

            end_position = rung.find_matching_branch_end(1)  # Position of '['
            self.assertEqual(end_position, 3)  # Position of ']'

    def test_find_matching_branch_end_invalid_start(self):
        """Test find_matching_branch_end with invalid start position."""
        rung = Rung(meta_data=self.branch_rung_meta, controller=self.mock_controller)

        with patch.object(rung, '_tokenize_rung_text') as mock_tokenize:
            mock_tokenize.return_value = ["XIC(Input1)", "OTE(Output1)"]

            with self.assertRaises(ValueError) as context:
                rung.find_matching_branch_end(0)  # Not a '[' token

            self.assertIn("Start position must be a valid branch start token", str(context.exception))


class TestRungUtilityMethods(unittest.TestCase):
    """Test Rung utility methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.rung_meta = {
            '@Number': '5',
            '@Type': 'N',
            'Text': 'XIC(Input1)OTE(Output1);',
            'Comment': 'Test comment\nSecond line'
        }

    def test_str_method(self):
        """Test __str__ method."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        self.assertEqual(str(rung), rung.text)

    def test_repr_method(self):
        """Test __repr__ method."""
        mock_routine = Mock(spec=Routine)
        mock_routine.name = "TestRoutine"

        rung = Rung(
            meta_data=self.rung_meta,
            controller=self.mock_controller,
            routine=mock_routine
        )

        # Mock instructions for repr
        rung._instructions = [Mock(), Mock()]

        repr_str = repr(rung)

        self.assertIn("Rung(", repr_str)
        self.assertIn("number=5", repr_str)
        self.assertIn("routine=TestRoutine", repr_str)
        self.assertIn("instructions=2", repr_str)

    def test_get_comment_lines(self):
        """Test get_comment_lines method."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        self.assertEqual(rung.get_comment_lines(), 2)

    def test_get_comment_lines_no_comment(self):
        """Test get_comment_lines with no comment."""
        meta = self.rung_meta.copy()
        meta['Comment'] = ''

        rung = Rung(meta_data=meta, controller=self.mock_controller)

        self.assertEqual(rung.get_comment_lines(), 0)

    def test_has_instruction_true(self):
        """Test has_instruction method when instruction exists."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        with patch.object(rung, 'find_instruction_positions') as mock_find:
            mock_find.return_value = [0, 2]  # Found at positions 0 and 2

            self.assertTrue(rung.has_instruction("XIC(Input1)"))

    def test_has_instruction_false(self):
        """Test has_instruction method when instruction doesn't exist."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        with patch.object(rung, 'find_instruction_positions') as mock_find:
            mock_find.return_value = []  # Not found

            self.assertFalse(rung.has_instruction("XIO(Input2)"))

    def test_find_instruction_positions(self):
        """Test find_instruction_positions method."""
        multi_instruction_meta = {
            '@Number': '0',
            '@Type': 'N',
            'Text': 'XIC(Input1)XIC(Input1)OTE(Output1);',
            'Comment': ''
        }

        rung = Rung(meta_data=multi_instruction_meta, controller=self.mock_controller)

        positions = rung.find_instruction_positions("XIC(Input1)")
        self.assertEqual(len(positions), 2)

    def test_get_execution_sequence(self):
        """Test get_execution_sequence method."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        # Mock rung sequence
        mock_instruction = Mock(spec=LogixInstruction)
        mock_instruction.instruction_name = "XIC"
        mock_instruction.meta_data = "XIC(Input1)"
        mock_instruction.type = LogixInstructionType.INPUT
        mock_operand = Mock()
        mock_operand.meta_data = "Input1"
        mock_instruction.operands = [mock_operand]

        mock_element = RungElement(
            element_type=RungElementType.INSTRUCTION,
            instruction=mock_instruction,
            position=0
        )

        rung._rung_sequence = [mock_element]

        sequence = rung.get_execution_sequence()

        self.assertEqual(len(sequence), 1)
        self.assertEqual(sequence[0]['instruction_type'], "XIC")
        self.assertEqual(sequence[0]['instruction_text'], "XIC(Input1)")
        self.assertTrue(sequence[0]['is_input'])

    def test_to_sequence_dict(self):
        """Test to_sequence_dict method."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        # Mock required properties
        rung._instructions = [Mock(), Mock()]
        rung._branches = {}

        with patch.object(rung, 'get_execution_sequence') as mock_exec:
            with patch.object(rung, 'get_main_line_instructions') as mock_main:
                mock_exec.return_value = []
                mock_main.return_value = []

                result = rung.to_sequence_dict()

                self.assertEqual(result['rung_number'], '5')
                self.assertEqual(result['comment'], 'Test comment\nSecond line')
                self.assertEqual(result['instruction_count'], 2)
                self.assertEqual(result['branch_count'], 0)


class TestRungErrorHandling(unittest.TestCase):
    """Test Rung error handling and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.rung_meta = {
            '@Number': '0',
            '@Type': 'N',
            'Text': 'XIC(Input1)OTE(Output1);',
            'Comment': ''
        }

    def test_get_element_at_position_out_of_range(self):
        """Test _get_element_at_position with out of range position."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        with self.assertRaises(IndexError) as context:
            rung._get_element_at_position(999)

        self.assertIn("Position out of range", str(context.exception))

    def test_get_element_at_position_negative(self):
        """Test _get_element_at_position with negative position."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        with self.assertRaises(IndexError) as context:
            rung._get_element_at_position(-1)

        self.assertIn("Position out of range", str(context.exception))

    def test_remove_token_by_index_out_of_range(self):
        """Test _remove_token_by_index with out of range index."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        tokens = ["XIC(Input1)", "OTE(Output1)"]

        with self.assertRaises(IndexError) as context:
            rung._remove_token_by_index(tokens, 5)

        self.assertIn("Index out of range", str(context.exception))

    def test_remove_tokens_invalid_range(self):
        """Test _remove_tokens with invalid range."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        tokens = ["XIC(Input1)", "OTE(Output1)"]

        with self.assertRaises(IndexError) as context:
            rung._remove_tokens(tokens, 1, 0)  # start > end

        self.assertIn("Invalid start or end indices", str(context.exception))

    def test_insert_branch_tokens_invalid_positions(self):
        """Test _insert_branch_tokens with invalid positions."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        tokens = ["XIC(Input1)", "OTE(Output1)"]

        with self.assertRaises(ValueError) as context:
            rung._insert_branch_tokens(tokens, 2, 1, [])  # end < start

        self.assertIn("End position must be greater than or equal to start position", str(context.exception))

    def test_find_instruction_index_not_found(self):
        """Test _find_instruction_index_in_text with non-existent instruction."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        with patch.object(rung, '_tokenize_rung_text') as mock_tokenize:
            mock_tokenize.return_value = ["XIC(Input1)", "OTE(Output1)"]

            with self.assertRaises(ValueError) as context:
                rung._find_instruction_index_in_text("XIO(Input2)")

            self.assertIn("Instruction 'XIO(Input2)' not found", str(context.exception))

    def test_find_instruction_index_occurrence_out_of_range(self):
        """Test _find_instruction_index_in_text with occurrence out of range."""
        rung = Rung(meta_data=self.rung_meta, controller=self.mock_controller)

        with patch.object(rung, '_tokenize_rung_text') as mock_tokenize:
            mock_tokenize.return_value = ["XIC(Input1)", "OTE(Output1)"]

            with self.assertRaises(ValueError) as context:
                rung._find_instruction_index_in_text("XIC(Input1)", occurrence=5)

            self.assertIn("Occurrence 5 not found", str(context.exception))


class TestRungIntegration(unittest.TestCase):
    """Integration tests for Rung class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=Controller)
        self.mock_routine = Mock(spec=Routine)

    @patch('pyrox.models.plc.rung.l5x_dict_from_file')
    @patch('pyrox.models.plc.rung.LogixInstruction')
    def test_full_rung_lifecycle(self, mock_logix_instruction, mock_l5x_dict):
        """Test full rung creation and usage lifecycle."""
        rung_meta = {
            '@Number': '0',
            '@Type': 'N',
            'Text': 'XIC(StartButton)[XIO(SafetyStop),XIC(Enable)]OTE(Motor);',
            'Comment': 'Motor control logic with safety'
        }

        mock_l5x_dict.return_value = {'Rung': rung_meta}

        # Mock instructions
        mock_instr1 = Mock(spec=LogixInstruction)
        mock_instr1.meta_data = "XIC(StartButton)"
        mock_instr1.instruction_name = "XIC"
        mock_instr1.type = LogixInstructionType.INPUT

        mock_instr2 = Mock(spec=LogixInstruction)
        mock_instr2.meta_data = "XIO(SafetyStop)"
        mock_instr2.instruction_name = "XIO"
        mock_instr2.type = LogixInstructionType.INPUT

        mock_instr3 = Mock(spec=LogixInstruction)
        mock_instr3.meta_data = "XIC(Enable)"
        mock_instr3.instruction_name = "XIC"
        mock_instr3.type = LogixInstructionType.INPUT

        mock_instr4 = Mock(spec=LogixInstruction)
        mock_instr4.meta_data = "OTE(Motor)"
        mock_instr4.instruction_name = "OTE"
        mock_instr4.type = LogixInstructionType.OUTPUT

        mock_logix_instruction.side_effect = [mock_instr1, mock_instr2, mock_instr3, mock_instr4]

        # Create rung
        rung = Rung(
            controller=self.mock_controller,
            routine=self.mock_routine
        )

        # Verify properties
        self.assertEqual(rung.number, '0')
        self.assertEqual(rung.type, 'N')
        self.assertIn('Motor control logic', rung.comment)

        # Verify instructions
        self.assertEqual(len(rung.instructions), 4)

        # Verify branch detection
        self.assertTrue(rung.has_branches())
        self.assertGreater(rung.get_max_branch_depth(), 0)

        # Test instruction manipulation
        rung.add_instruction("XIC(NewInput)")
        self.assertIn("XIC(NewInput)", rung.text)

        # Test branch validation
        self.assertTrue(rung.validate_branch_structure())

    @patch('pyrox.models.plc.rung.LogixInstruction')
    def test_complex_branch_operations(self, mock_logix_instruction):
        """Test complex branch operations."""
        complex_meta = {
            '@Number': '1',
            '@Type': 'N',
            'Text': 'XIC(A)[XIO(B)[XIC(C),XIO(D)],XIC(E)]OTE(F);',
            'Comment': 'Complex nested branches'
        }

        # Setup mock instructions
        mock_instructions = []
        for i in range(6):  # 6 instructions in the complex text
            mock_instr = Mock(spec=LogixInstruction)
            mock_instr.meta_data = f"INSTR{i}"
            mock_instr.instruction_name = "TEST"
            mock_instr.type = LogixInstructionType.INPUT
            mock_instructions.append(mock_instr)

        mock_logix_instruction.side_effect = mock_instructions

        rung = Rung(meta_data=complex_meta, controller=self.mock_controller)

        # Verify complex structure
        self.assertTrue(rung.has_branches())
        self.assertGreaterEqual(rung.get_max_branch_depth(), 2)  # Should have nested branches

        # Test branch validation on complex structure
        self.assertTrue(rung.validate_branch_structure())


if __name__ == '__main__':
    unittest.main()

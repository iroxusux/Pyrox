"""Rung model for PLC.
"""
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Dict,
    List,
    Optional,
    Union
)
from dataclasses import dataclass, field
import re
from pyrox.models.plc import meta as plc_meta
from pyrox.models.plc.instruction import LogixInstruction
from pyrox.services.plc import l5x_dict_from_file
if TYPE_CHECKING:
    from .controller import (
        Controller,
        Routine,
    )


class RungElementType(Enum):
    """Types of elements in a rung sequence."""
    INSTRUCTION = "instruction"
    BRANCH_START = "branch_start"
    BRANCH_END = "branch_end"
    BRANCH_NEXT = "branch_next"


@dataclass
class RungElement:
    """Represents an element in the rung sequence."""
    element_type: RungElementType
    instruction: Optional[LogixInstruction] = None
    branch_id: Optional[str] = None
    root_branch_id: Optional[str] = None  # ID of the parent branch if this is a nested branch
    branch_level: Optional[int] = 0  # Level of the branch in the rung
    position: int = 0  # Sequential position in rung
    rung: Optional['Rung'] = None  # Reference to the Rung this element belongs to
    rung_number: int = 0  # Rung number this element belongs to


@dataclass
class RungBranch:
    """Represents a branch structure in the rung."""
    branch_id: str
    start_position: int
    end_position: int
    root_branch_id: Optional[str] = None  # ID of the parent branch
    nested_branches: List['RungBranch'] = field(default_factory=list)


class Rung(plc_meta.PlcObject):
    _branch_id_counter: int = 0  # Static counter for unique branch IDs

    def __init__(self,
                 meta_data: dict = None,
                 controller: 'Controller' = None,
                 routine: Optional['Routine'] = None,
                 rung_number: Optional[Union[int, str]] = None,
                 text: Optional[str] = None,
                 comment: Optional[str] = None):
        """type class for plc Rung"""
        super().__init__(meta_data=meta_data or l5x_dict_from_file(plc_meta.PLC_RUNG_FILE)['Rung'],
                         controller=controller)

        self._routine: Optional['Routine'] = routine
        self._instructions: list[LogixInstruction] = []
        self._rung_sequence: List[RungElement] = []
        self._branches: Dict[str, RungBranch] = {}

        if text:
            self.text = text
        if comment:
            self.comment = comment
        if rung_number is not None:
            self.number = rung_number
        self._input_instructions: list[LogixInstruction] = []
        self._output_instructions: list[LogixInstruction] = []
        self._refresh_internal_structures()
        self._parse_rung_sequence()

    def __eq__(self, other):
        if not isinstance(other, Rung):
            return False
        if self.text == other.text:
            return True
        return False

    def __repr__(self):
        return (
            f'Rung(number={self.number}, '
            f'routine={self.routine.name if self.routine else "None"}, '
            f'type={self.type}, '
            f'comment={self.comment}, '
            f'text={self.text}, '
            f'instructions={len(self.instructions)}, '
            f'branches={len(self._branches)})'
        )

    def __str__(self):
        return self.text

    @property
    def dict_key_order(self) -> list[str]:
        return [
            '@Number',
            '@Type',
            'Comment',
            'Text'
        ]

    @property
    def comment(self) -> str:
        return self['Comment']

    @comment.setter
    def comment(self, value: str):
        self['Comment'] = value

    @property
    def container(self) -> 'Routine':
        return self.routine.container if self.routine else None

    @property
    def input_instructions(self) -> list[LogixInstruction]:
        if self._input_instructions:
            return self._input_instructions
        self._input_instructions = [x for x in self.instructions if x.type is plc_meta.LogixInstructionType.INPUT]
        return self._input_instructions

    @property
    def instructions(self) -> list[LogixInstruction]:
        return self._instructions

    @property
    def output_instructions(self) -> list[LogixInstruction]:
        if self._output_instructions:
            return self._output_instructions
        self._output_instructions = [x for x in self.instructions if x.type is plc_meta.LogixInstructionType.OUTPUT]
        return self._output_instructions

    @property
    def number(self) -> str:
        return self['@Number']

    @number.setter
    def number(self, value: Union[int, str]):
        if not isinstance(value, (str, int)):
            raise ValueError("Rung number must be a string or int!")
        self['@Number'] = str(value)

    @property
    def routine(self) -> Optional['Routine']:
        return self._routine

    @routine.setter
    def routine(self, value: 'Routine'):
        self._routine = value

    @property
    def text(self) -> str:
        if not self['Text']:
            self['Text'] = ''
        return self['Text']

    @text.setter
    def text(self, value: str):
        if value is not None and not value.endswith(';'):
            value += ';'
        self['Text'] = value
        self._parse_rung_sequence()

    @property
    def type(self) -> str:
        return self['@Type']

    @property
    def rung_sequence(self) -> List[RungElement]:
        """Get the sequential elements of this rung including branches."""
        return self._rung_sequence

    @property
    def branches(self) -> Dict[str, RungBranch]:
        """Get all branches in this rung."""
        return self._branches

    @staticmethod
    def _extract_instructions(
        text
    ) -> List[str]:
        """Extract instructions with properly balanced parentheses.

        Args:
            text (str): The rung text to extract instructions from.

        Returns:
            List[str]: A list of extracted instructions.
        """
        instructions = []

        # Find instruction starts
        starts = list(re.finditer(r'[A-Za-z0-9_]+\(', text))

        for match in starts:
            start_pos = match.start()
            paren_pos = match.end() - 1  # Position of opening parenthesis

            # Find matching closing parenthesis
            paren_count = 1
            pos = paren_pos + 1

            while pos < len(text) and paren_count > 0:
                if text[pos] == '(':
                    paren_count += 1
                elif text[pos] == ')':
                    paren_count -= 1
                pos += 1

            if paren_count == 0:  # Found matching closing parenthesis
                instruction = text[start_pos:pos]
                instructions.append(instruction)

        return instructions

    @staticmethod
    def _insert_branch_tokens(
        original_tokens: List[str],
        start_pos: int,
        end_pos: int,
        branch_instructions: List[str]
    ) -> List[str]:
        """Insert branch markers and instructions into token sequence.

        Args:
            original_tokens (List[str]): Original token sequence
            start_pos (int): Start position for branch
            end_pos (int): End position for branch
            branch_instructions (List[str]): Instructions to place in branch

        Returns:
            List[str]: New token sequence with branch inserted
        """
        new_tokens = []

        if end_pos < start_pos:
            raise ValueError("End position must be greater than or equal to start position!")

        if not original_tokens:
            original_tokens = ['']

        def write_branch_end():
            new_tokens.append(',')
            for instr in branch_instructions:
                new_tokens.append(instr)
            new_tokens.append(']')

        for index, token in enumerate(original_tokens):
            if index == start_pos:
                new_tokens.append('[')
            if index == end_pos:
                write_branch_end()
            if token:
                new_tokens.append(token)
            if (end_pos == len(original_tokens) and index == len(original_tokens) - 1):
                write_branch_end()

        return new_tokens

    def _build_sequence_from_tokens(
        self,
        tokens: List[str]
    ) -> None:
        """Build the rung sequence from tokenized text.
        """
        position = 0
        root_branch_id = None  # Track each branch's parent, since the symbols appear on the parent rail
        branch_id = None
        branch_stack: list[RungBranch] = []
        branch_counter = 0
        branch_level = 0
        branch_level_history: list[int] = []  # Track branch levels for nesting
        branch_root_id_history: list[str] = []  # Track root branch IDs for nesting
        instruction_index = 0

        for token in tokens:
            if token == '[':  # Branch start
                branch_id = self._get_unique_branch_id()
                branch_counter += 1
                branch_level_history.append(branch_level)
                branch_level = 0  # Reset branch level for new branch

                branch_start = RungElement(
                    element_type=RungElementType.BRANCH_START,
                    branch_id=branch_id,
                    root_branch_id=root_branch_id,
                    branch_level=branch_level,
                    position=position,
                    rung=self,
                    rung_number=int(self.number)
                )

                branch = RungBranch(
                    branch_id=branch_id,
                    root_branch_id=root_branch_id,
                    start_position=position,
                    end_position=-1,
                    nested_branches=[],
                )

                branch_stack.append(branch)
                self._branches[branch_id] = branch
                self._rung_sequence.append(branch_start)
                branch_root_id_history.append(root_branch_id)  # Save current root branch id
                root_branch_id = branch_id  # Change branch id after assignment so we get the proper parent
                position += 1

            elif token == ']':  # Branch end
                branch = branch_stack.pop()
                self._branches[branch.branch_id].end_position = position
                if not self._branches[branch.branch_id].nested_branches:
                    # If no nested branches, we need to delete this major branch and reconstruct the rung again
                    fresh_tokens = self._remove_token_by_index(self._tokenize_rung_text(self.text), position)
                    fresh_tokens = self._remove_token_by_index(fresh_tokens, branch.start_position)
                    self.text = "".join(fresh_tokens)
                    self._refresh_internal_structures()
                    return

                self._branches[branch.branch_id].nested_branches[-1].end_position = position - 1
                root_branch_id = branch_root_id_history.pop() if branch_root_id_history else None
                branch_id = self._branches[branch.branch_id].root_branch_id
                branch_level = branch_level_history.pop() if branch_level_history else 0

                branch_end = RungElement(
                    element_type=RungElementType.BRANCH_END,
                    branch_id=branch.branch_id,
                    root_branch_id=branch.root_branch_id,
                    branch_level=branch_level,
                    position=position,
                    rung=self,
                    rung_number=int(self.number)
                )

                self._rung_sequence.append(branch_end)
                position += 1

            elif token == ',':  # Next branch marker
                parent_branch = branch_stack[-1] if branch_stack else None
                if not parent_branch:
                    raise ValueError("Next branch marker found without an active branch!")

                branch_level += 1
                branch_id = f'{parent_branch.branch_id}:{branch_level}'

                if branch_level > 1:
                    # update the previous nested branch's end position
                    parent_branch.nested_branches[-1].end_position = position - 1  # ends at the previous position

                next_branch = RungElement(
                    element_type=RungElementType.BRANCH_NEXT,
                    branch_id=branch_id,
                    root_branch_id=root_branch_id,
                    branch_level=branch_level,
                    position=position,
                    rung=self,
                    rung_number=int(self.number)
                )
                nested_branch = RungBranch(branch_id=branch_id, start_position=position,
                                           end_position=-1, root_branch_id=parent_branch.branch_id)

                parent_branch.nested_branches.append(nested_branch)
                self._branches[branch_id] = nested_branch
                self._rung_sequence.append(next_branch)
                position += 1

            else:  # Regular instruction
                instruction = self._find_instruction_by_text(token, instruction_index)
                if instruction:
                    element = RungElement(
                        element_type=RungElementType.INSTRUCTION,
                        instruction=instruction,
                        position=position,
                        branch_id=branch_id,
                        root_branch_id=root_branch_id,
                        branch_level=branch_level,
                        rung=self,
                        rung_number=int(self.number)
                    )

                    self._rung_sequence.append(element)
                    position += 1
                    instruction_index += 1
                else:
                    raise ValueError(f"Instruction '{token}' not found in rung text.")

    def _find_instruction_by_text(self, text: str, index: int) -> Optional[LogixInstruction]:
        """Find an instruction object by its text representation."""
        # First try exact match
        for instruction in self.instructions:
            if instruction.meta_data == text:
                return instruction

        # If no exact match, try by index (fallback)
        if 0 <= index < len(self.instructions):
            return self.instructions[index]

        return None

    def _find_instruction_index_in_text(self, instruction_text: str, occurrence: int = 0) -> int:
        """Find the index of an instruction in the text by its occurrence.

        Args:
            instruction_text (str): The instruction text to find
            occurrence (int): Which occurrence to find (0-based)

        Returns:
            int: The index of the instruction

        Raises:
            ValueError: If instruction not found or occurrence out of range
        """
        tokens = self._tokenize_rung_text(self.text)
        # existing_instructions = re.findall(INST_RE_PATTERN, self.text)
        matches = [i for i, token in enumerate(tokens) if token == instruction_text]

        if not matches:
            raise ValueError(f"Instruction '{instruction_text}' not found in rung")

        if occurrence >= len(matches):
            raise ValueError(f"Occurrence {occurrence} not found. Only {len(matches)} occurrences exist.")

        return matches[occurrence]

    def _get_element_at_position(
        self,
        position: int
    ) -> Optional[RungElement]:
        """Get the RungElement at a specific position in the rung sequence.
        Args:
            position (int): The position in the rung sequence
        Returns:
            Optional[RungElement]: The RungElement at the specified position, or None if not found
        """
        if position < 0 or position >= len(self._rung_sequence) or position is None:
            raise IndexError("Position out of range in rung sequence.")

        return self._rung_sequence[position]

    def _get_instructions(self):
        """Extract instructions from rung text."""
        if not self.text:
            return

        instr = self._extract_instructions(self.text)
        if not instr:
            return

        from pyrox.models.plc.instruction import LogixInstruction
        self._instructions = [LogixInstruction(x, self, self.controller) for x in instr]

    def _get_unique_branch_id(self) -> str:
        """Generate a unique branch ID."""
        branch_id = f"rung_{self.number}_branch_{self._branch_id_counter}"
        self._branch_id_counter += 1
        return branch_id

    def _parse_rung_sequence(self):
        """Parse the rung text to identify instruction sequence and branches."""
        self._refresh_internal_structures()
        self._get_instructions()
        self._build_sequence_from_tokens(self._tokenize_rung_text(self.text))

    def _tokenize_rung_text(self, text: str) -> List[str]:
        """Tokenize rung text to identify instructions and branch markers."""

        tokens = []

        # First, extract all instructions using the balanced parentheses method
        instructions = self._extract_instructions(text)
        instruction_ranges = []

        # Find the positions of each instruction in the text
        search_start = 0
        for instruction in instructions:
            pos = text.find(instruction, search_start)
            if pos != -1:
                instruction_ranges.append((pos, pos + len(instruction)))
                search_start = pos + len(instruction)

        # Process the text character by character
        i = 0
        current_segment = ""

        while i < len(text):
            char = text[i]

            if char in ['[', ']', ',']:
                # Check if this symbol is inside any instruction
                inside_instruction = any(start <= i < end for start, end in instruction_ranges)

                if inside_instruction:
                    # This bracket is part of an instruction (array reference), keep it
                    current_segment += char
                else:
                    # This is a branch marker or next-branch marker
                    if current_segment.strip():
                        # Extract instructions from current segment using our method
                        segment_instructions = self._extract_instructions(current_segment)
                        tokens.extend(segment_instructions)
                        current_segment = ""

                    # Add the branch marker
                    tokens.append(char)
            else:
                current_segment += char

            i += 1

        # Process any remaining segment
        if current_segment.strip():
            segment_instructions = self._extract_instructions(current_segment)
            tokens.extend(segment_instructions)

        return tokens

    def _reconstruct_text_with_branches(self, instructions: List[str],
                                        branch_markers: List[str],
                                        original_text: str) -> str:
        """Reconstruct text preserving branch structure.

        This is a complex operation that attempts to maintain the relative positioning
        of branch markers with the instruction sequence.
        """
        # Get original tokens to understand structure
        original_tokens = self._tokenize_rung_text(original_text)

        # Create a map of instruction positions to branch operations
        instruction_index = 0
        result_tokens = []

        for token in original_tokens:
            if token in ['[', ']', ',']:
                # Preserve branch markers
                result_tokens.append(token)
            else:
                # Replace with new instruction if available
                if instruction_index < len(instructions):
                    result_tokens.append(instructions[instruction_index])
                    instruction_index += 1

        # Add any remaining instructions at the end
        while instruction_index < len(instructions):
            result_tokens.append(instructions[instruction_index])
            instruction_index += 1

        return "".join(result_tokens)

    def _refresh_internal_structures(self):
        """Refresh the internal instruction and sequence structures after text changes."""
        # Clear existing structures
        self._instructions = []
        self._rung_sequence = []
        self._branches = {}
        self._branch_id_counter = 0
        self._input_instructions = []
        self._output_instructions = []

    def _remove_branch_tokens(self, original_tokens: List[str], branch_id: str,
                              keep_instructions: bool) -> List[str]:
        """Remove branch tokens from token sequence.

        Args:
            original_tokens (List[str]): Original token sequence
            branch_id (str): Branch ID to remove
            keep_instructions (bool): Whether to keep branch instructions

        Returns:
            List[str]: New token sequence with branch removed
        """
        # This is a simplified implementation
        # In practice, you'd need to track which '[' and ']' belong to which branch
        new_tokens = []
        skip_until_close = False
        branch_instructions = []

        if branch_id in self._branches:
            branch = self._branches[branch_id]
            branch_instructions = [instr.meta_data for instr in branch.instructions]

        for token in original_tokens:
            if token == '[' and not skip_until_close:
                # Check if this is the branch we want to remove
                # This is simplified - in practice you'd need better branch tracking
                skip_until_close = True
                continue
            elif token == ']' and skip_until_close:
                skip_until_close = False
                if keep_instructions:
                    new_tokens.extend(branch_instructions)
                continue
            elif not skip_until_close:
                new_tokens.append(token)

        return new_tokens

    def _remove_token_by_index(self, tokens: List[str], index: int) -> List[str]:
        """Remove a token at a specific index from the token list.

        Args:
            tokens (List[str]): List of tokens
            index (int): Index of the token to remove

        Returns:
            List[str]: New token list with the specified token removed
        """
        if index < 0 or index >= len(tokens):
            raise IndexError("Index out of range!")

        return tokens[:index] + tokens[index + 1:]

    def _remove_tokens(self, tokens: List[str], start: int, end: int) -> List[str]:
        """Remove a range of tokens from the token list.

        Args:
            tokens (List[str]): List of tokens
            start (int): Start index of the range to remove
            end (int): End index of the range to remove

        Returns:
            List[str]: New token list with the specified range removed
        """
        if start < 0 or end >= len(tokens) or start > end:
            raise IndexError("Invalid start or end indices for removal!")

        return tokens[:start] + tokens[end + 1:]

    def add_instruction(self, instruction_text: str, position: Optional[int] = None):
        """Add an instruction to this rung at the specified position.

        Args:
            instruction_text (str): The instruction text to add (e.g., "XIC(Tag1)")
            position (Optional[int]): Position to insert at. If None, appends to end.
        """
        if not instruction_text or not isinstance(instruction_text, str):
            raise ValueError("Instruction text must be a non-empty string!")

        # Validate instruction format
        if not re.match(plc_meta.INST_RE_PATTERN, instruction_text):
            raise ValueError(f"Invalid instruction format: {instruction_text}")

        current_text = self.text or ""

        if not current_text.strip():
            # Empty rung, just set the instruction
            current_tokens = [instruction_text]
        else:
            # Parse existing instructions to find insertion point
            current_tokens = self._tokenize_rung_text(current_text)

            if position is None or position >= len(current_tokens):
                # Append to end
                current_tokens.append(instruction_text)
            elif position == 0:
                # Insert at beginning
                current_tokens.insert(0, instruction_text)

            else:
                # Insert at specific position
                current_tokens.insert(position, instruction_text)

        # Refresh internal structures
        self.text = "".join(current_tokens)

    def find_instruction_positions(self, instruction_text: str) -> List[int]:
        """Find all positions of a specific instruction in the rung.

        Args:
            instruction_text (str): The instruction text to find

        Returns:
            List[int]: List of positions where the instruction appears
        """
        import re
        existing_instructions = re.findall(plc_meta.INST_RE_PATTERN, self.text) if self.text else []
        return [i for i, inst in enumerate(existing_instructions) if inst == instruction_text]

    def find_matching_branch_end(self, start_position: int) -> Optional[int]:
        """Find the matching end position for a branch start.

        Args:
            start_position (int): Position where branch starts

        Returns:
            Optional[int]: Position where branch ends, or None if not found
        """
        if not self.text:
            return None

        tokens = self._tokenize_rung_text(self.text)
        if len(tokens) <= start_position or tokens[start_position] != '[':
            raise ValueError("Start position must be a valid branch start token position.")

        bracket_count = 1  # Since we start on a bracket
        instruction_count = start_position

        for token in tokens[start_position+1:]:
            instruction_count += 1
            if token == '[':
                bracket_count += 1
            elif token == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    return instruction_count

        return None

    def get_branch_count(self) -> int:
        """Get the number of branches in this rung."""
        return len(self._branches)

    def get_branch_info(self, branch_id: str) -> Dict:
        """Get detailed information about a branch.

        Args:
            branch_id (str): ID of the branch

        Returns:
            Dict: Branch information including positions and instructions

        Raises:
            ValueError: If branch ID doesn't exist
        """
        if branch_id not in self._branches:
            raise ValueError(f"Branch '{branch_id}' not found in rung!")

        branch = self._branches[branch_id]

        return {
            'branch_id': branch_id,
            'start_position': branch.start_position,
            'end_position': branch.end_position,
            'instruction_count': len(branch.instructions),
            'instructions': [instr.meta_data for instr in branch.instructions],
            'instruction_types': [instr.instruction_name for instr in branch.instructions]
        }

    def get_branch_internal_nesting_level(self, branch_position: int) -> int:
        """Get nesting levels of elements inside of a branch.
        """
        end_position = self.find_matching_branch_end(branch_position)
        if end_position is None:
            raise ValueError(f"No matching end found for branch starting at position {branch_position}.")

        tokens = self._tokenize_rung_text(self.text)
        open_counter, nesting_counter, nesting_level = 0, 0, 0
        indexed_tokens = tokens[branch_position+1:end_position]
        for token in indexed_tokens:
            if open_counter < 0:
                raise ValueError("Mismatched brackets in rung text.")
            if token == '[':
                open_counter += 1
            elif token == ',' and open_counter:
                nesting_counter += 1
                if nesting_counter > nesting_level:
                    nesting_level = nesting_counter
            elif token == ']':
                open_counter -= 1

        return nesting_level

    def get_branch_nesting_level(self, instruction_position: int) -> int:
        """Get the nesting level of branches at a specific instruction position.

        Args:
            instruction_position (int): Position of the instruction (0-based)

        Returns:
            int: Nesting level (0 = main line, 1+ = inside branches)
        """
        if not self.text:
            return 0

        tokens = self._tokenize_rung_text(self.text)
        nesting_level = 0

        for index, token in enumerate(tokens):
            if token == '[':
                nesting_level += 1
            elif token == ']':
                nesting_level -= 1
            if index == instruction_position:
                return nesting_level

        return 0

    def get_comment_lines(self) -> int:
        """Get the number of comment lines in this rung.
        """
        if not self.comment:
            return 0

        # Count the number of comment lines by splitting on newlines
        return len(self.comment.splitlines())

    def get_execution_sequence(self) -> List[Dict]:
        """Get the logical execution sequence of the rung."""
        sequence = []

        for i, element in enumerate(self._rung_sequence):
            if element.element_type == RungElementType.INSTRUCTION:
                sequence.append({
                    'step': i,
                    'instruction_type': element.instruction.instruction_name,
                    'instruction_text': element.instruction.meta_data,
                    'operands': [op.meta_data for op in element.instruction.operands],
                    'is_input': element.instruction.type == plc_meta.LogixInstructionType.INPUT,
                    'is_output': element.instruction.type == plc_meta.LogixInstructionType.OUTPUT
                })
            elif element.element_type in [RungElementType.BRANCH_START, RungElementType.BRANCH_END]:
                sequence.append({
                    'step': i,
                    'element_type': element.element_type.value,
                    'branch_id': element.branch_id
                })

        return sequence

    def get_instruction_count(self) -> int:
        """Get the total number of instructions in this rung."""
        return len(self.instructions)

    def get_instruction_at_position(
        self,
        position: int
    ) -> Optional[LogixInstruction]:
        """Get the instruction at a specific position.

        Args:
            position (int): The position index

        Returns:
            Optional[LogixInstruction]: The instruction at that position, or None
        """
        if 0 <= position < len(self.instructions):
            return self.instructions[position]
        return None

    def get_instruction_summary(self) -> Dict[str, int]:
        """Get a summary of instruction types and their counts.

        Returns:
            Dict[str, int]: Dictionary mapping instruction names to their counts
        """
        summary = {}
        for instruction in self.instructions:
            inst_name = instruction.instruction_name
            summary[inst_name] = summary.get(inst_name, 0) + 1
        return summary

    def get_instructions(
        self,
        instruction_filter: Optional[str] = None,
        operand_filter: Optional[str] = None
    ) -> List[LogixInstruction]:
        """Get instructions filtered by operand or name.

        Args:
            instruction_filter (Optional[str]): Instruction text to filter by
            operand_filter (Optional[str]): Instruction name to filter by

        Returns:
            List[LogixInstruction]: List of matching instructions
        """
        filtered_instructions = self.instructions

        if instruction_filter:
            filtered_instructions = [
                instr for instr in filtered_instructions
                if instruction_filter == instr.instruction_name
            ]

        if operand_filter:
            filtered_instructions = [
                instr for instr in filtered_instructions
                if any(operand_filter in op.meta_data for op in instr.operands)
            ]

        return filtered_instructions

    def get_branch_instructions(self, branch_id: str) -> List[LogixInstruction]:
        """Get all instructions within a specific branch."""
        if branch_id not in self._branches:
            return []
        return self._branches[branch_id].instructions.copy()

    def get_main_line_instructions(self) -> List[LogixInstruction]:
        """Get instructions that are on the main line (not in branches)."""
        branch_instructions = set()
        for branch in self._branches.values():
            branch_instructions.update(branch.instructions)

        return [instr for instr in self.instructions if instr not in branch_instructions]

    def get_max_branch_depth(self) -> int:
        """Get the maximum nesting depth of branches in this rung.

        Returns:
            int: Maximum branch depth (0 = no branches, 1+ = nested levels)
        """
        if not self.text:
            return 0

        tokens = self._tokenize_rung_text(self.text)
        first_branch_token_found = False
        current_depth = 0
        max_depth = 0
        restore_depth = 0

        for token in tokens:
            if token == '[':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif token == ',':
                # ',' increases the nested branch count
                # But the first occurence is included with the '[' token
                # So, ignore the first one and set a flag
                # Additionally, mark where to restore the depth level when this branch sequence ends
                if first_branch_token_found is False:
                    first_branch_token_found = True
                    restore_depth = current_depth
                    continue
                else:
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)

            elif token == ']':
                current_depth -= 1
                first_branch_token_found = False
                current_depth = restore_depth

        return max_depth

    def has_instruction(self, instruction_text: str) -> bool:
        """Check if the rung contains a specific instruction.

        Args:
            instruction_text (str): The instruction text to check for

        Returns:
            bool: True if the instruction exists in the rung
        """
        return len(self.find_instruction_positions(instruction_text)) > 0

    def has_branches(self) -> bool:
        """Check if this rung contains any branches."""
        return len(self._branches) > 0

    def insert_branch(self,
                      start_position: int = 0,
                      end_position: int = 0) -> None:
        """Insert a new branch structure in the rung.

        Args:
            start_position (int): Position where the branch should start (0-based)
            end_position (int): Position where the branch should end (0-based)

        Raises:
            ValueError: If positions are invalid
            IndexError: If positions are out of range
        """
        original_tokens = self._tokenize_rung_text(self.text)

        if start_position < 0 or end_position < 0:
            raise ValueError("Branch positions must be non-negative!")

        if start_position > len(original_tokens) or end_position > len(original_tokens):
            raise IndexError("Branch positions out of range!")

        if start_position > end_position:
            raise ValueError("Start position must be less than or equal to end position!")

        new_tokens = self._insert_branch_tokens(
            original_tokens,
            start_position,
            end_position,
            []
        )

        self.text = "".join(new_tokens)
        return self._get_element_at_position(start_position).branch_id

    def insert_branch_level(self,
                            branch_position: int = 0,):
        """Insert a new branch level in the existing branch structure.
        """
        original_tokens = self._tokenize_rung_text(self.text)
        if branch_position < 0 or branch_position >= len(original_tokens):
            raise IndexError("Start position out of range!")
        if original_tokens[branch_position] != '[' and original_tokens[branch_position] != ',':
            raise ValueError("Start position must be on a branch start token!")
        # Find index of first 'next branch' marker after the start position, which is a ',' token
        next_branch_index = branch_position + 1
        nested_branch_count = 0
        while next_branch_index < len(original_tokens):
            if original_tokens[next_branch_index] == '[':
                nested_branch_count += 1
            elif original_tokens[next_branch_index] == ']':
                if nested_branch_count <= 0:
                    break
                nested_branch_count -= 1
            elif original_tokens[next_branch_index] == ',' and nested_branch_count <= 0:
                break
            next_branch_index += 1
        if next_branch_index >= len(original_tokens):
            raise ValueError("No next branch marker found after the start position!")
        if original_tokens[next_branch_index] != ',' and original_tokens[next_branch_index] != ']':
            raise ValueError("Next branch marker must be a ',' token!")
        # Insert a ',' at the next branch index
        new_tokens = original_tokens[:next_branch_index] + [','] + original_tokens[next_branch_index:]
        # Reconstruct text
        self.text = "".join(new_tokens)

    def list_branches(self) -> List[Dict]:
        """Get information about all branches in the rung.

        Returns:
            List[Dict]: List of branch information dictionaries
        """
        return [self.get_branch_info(branch_id) for branch_id in self._branches.keys()]

    def move_branch(self, branch_id: str, new_start_position: int, new_end_position: int):
        """Move an existing branch to a new position.

        Args:
            branch_id (str): ID of the branch to move
            new_start_position (int): New start position for the branch
            new_end_position (int): New end position for the branch

        Raises:
            ValueError: If branch ID doesn't exist or positions are invalid
        """
        if branch_id not in self._branches:
            raise ValueError(f"Branch '{branch_id}' not found in rung!")

        branch = self._branches[branch_id]
        branch_instructions = [instr.meta_data for instr in branch.instructions]

        # Remove the existing branch
        self.remove_branch(branch_id, keep_instructions=False)

        # Insert at new position
        self.insert_branch(new_start_position, new_end_position, branch_instructions)

    def move_instruction(self, instruction: Union[LogixInstruction, str, int],
                         new_position: int, occurrence: int = 0):
        """Move an instruction to a new position in the rung.

        Args:
            instruction: The instruction to move (LogixInstruction, str, or int index)
            new_position (int): The new position for the instruction
            occurrence (int): Which occurrence to move if there are duplicates (0-based)
        """
        current_tokens = self._tokenize_rung_text(self.text)

        if not current_tokens:
            raise ValueError("No instructions found in rung!")

        if new_position < 0 or new_position >= len(current_tokens):
            raise IndexError(f"New position {new_position} out of range!")

        # Find the instruction to move
        if isinstance(instruction, LogixInstruction):
            try:
                old_index = self._find_instruction_index_in_text(instruction.meta_data, occurrence)
            except ValueError:
                raise ValueError(f"Instruction '{instruction.meta_data}' not found in rung!")

        elif isinstance(instruction, str):
            try:
                old_index = self._find_instruction_index_in_text(instruction, occurrence)
            except ValueError:
                raise ValueError(f"Instruction '{instruction}' not found in rung!")

        elif isinstance(instruction, int):
            if instruction < 0 or instruction >= len(current_tokens):
                raise IndexError(f"Instruction index {instruction} out of range!")
            old_index = instruction
        else:
            raise TypeError("Instruction must be LogixInstruction, str, or int!")

        if old_index == new_position:
            return  # No move needed

        # Move the instruction
        moved_instruction = current_tokens.pop(old_index)
        current_tokens.insert(new_position, moved_instruction)

        # Rebuild text with reordered instructions
        self.text = "".join(current_tokens)

    def remove_branch(self, branch_id: str):
        """Remove a branch structure from the rung.

        Args:
            branch_id (str): ID of the branch to remove
            keep_instructions (bool): If True, keep branch instructions in main line

        Raises:
            ValueError: If branch ID doesn't exist
        """
        if branch_id not in self._branches:
            raise ValueError(f"Branch '{branch_id}' not found in rung!")

        branch = self._branches[branch_id]
        if branch.start_position < 0 or branch.end_position < 0:
            raise ValueError("Branch start or end position is invalid!")

        tokens = self._tokenize_rung_text(self.text)
        tokens = self._remove_tokens(tokens, branch.start_position, branch.end_position)
        for b in branch.nested_branches:
            if b.branch_id in self._branches:
                del self._branches[b.branch_id]
        del self._branches[branch_id]
        self.text = "".join(tokens)

    def remove_instruction(self, instruction: Union[LogixInstruction, str, int],
                           occurrence: int = 0):
        """Remove an instruction from this rung.

        Args:
            instruction: The instruction to remove. Can be:
                - LogixInstruction object
                - str: instruction text to remove
                - int: index of instruction to remove
            occurrence (int): Which occurrence to remove if there are duplicates (0-based).
                            Only used when instruction is a string.
        """
        if not self.text:
            raise ValueError("Cannot remove instruction from empty rung!")

        existing_instructions = re.findall(plc_meta.INST_RE_PATTERN, self.text)
        current_tokens = self._tokenize_rung_text(self.text)

        if not existing_instructions:
            raise ValueError("No instructions found in rung!")

        # Determine which instruction to remove
        if isinstance(instruction, LogixInstruction):
            # Find the instruction by its meta_data
            try:
                remove_index = self._find_instruction_index_in_text(instruction.meta_data, occurrence)
            except ValueError:
                raise ValueError(f"Instruction '{instruction.meta_data}' not found in rung!")

        elif isinstance(instruction, str):
            # Remove by instruction text
            try:
                remove_index = self._find_instruction_index_in_text(instruction, occurrence)
            except ValueError:
                raise ValueError(f"Instruction '{instruction}' not found in rung!")

        elif isinstance(instruction, int):
            # Remove by index
            if instruction < 0 or instruction >= len(current_tokens):
                raise IndexError(f"Instruction index {instruction} out of range!")
            remove_index = instruction
        else:
            raise TypeError("Instruction must be LogixInstruction, str, or int!")

        # Remove the instruction and rebuild text
        current_tokens.pop(remove_index)

        if not current_tokens:
            # Last instruction removed, clear the rung
            self.text = ""
        else:
            # Rebuild text with remaining instructions
            self.text = "".join(current_tokens)

    def replace_instruction(self, old_instruction: Union[LogixInstruction, str, int],
                            new_instruction_text: str, occurrence: int = 0):
        """Replace an instruction in this rung.

        Args:
            old_instruction: The instruction to replace (LogixInstruction, str, or int index)
            new_instruction_text (str): The new instruction text
            occurrence (int): Which occurrence to replace if there are duplicates (0-based)
        """
        if not new_instruction_text or not isinstance(new_instruction_text, str):
            raise ValueError("New instruction text must be a non-empty string!")

        # Validate new instruction format
        import re
        if not re.match(plc_meta.INST_RE_PATTERN, new_instruction_text):
            raise ValueError(f"Invalid instruction format: {new_instruction_text}")

        current_tokens = self._tokenize_rung_text(self.text)

        if not current_tokens:
            raise ValueError("No instructions found in rung!")

        # Determine which instruction to replace
        if isinstance(old_instruction, LogixInstruction):
            instruction_text = old_instruction.meta_data
            try:
                replace_index = self._find_instruction_index_in_text(instruction_text, occurrence)
            except ValueError:
                raise ValueError(f"Instruction '{instruction_text}' not found in rung!")

        elif isinstance(old_instruction, str):
            try:
                replace_index = self._find_instruction_index_in_text(old_instruction, occurrence)
            except ValueError:
                raise ValueError(f"Instruction '{old_instruction}' not found in rung!")

        elif isinstance(old_instruction, int):
            if old_instruction < 0 or old_instruction >= len(current_tokens):
                raise IndexError(f"Instruction index {old_instruction} out of range!")
            replace_index = old_instruction
        else:
            raise TypeError("Old instruction must be LogixInstruction, str, or int!")

        # Replace the instruction
        current_tokens[replace_index] = new_instruction_text

        # Rebuild text with updated instructions
        self.text = "".join(current_tokens)

    def to_sequence_dict(self) -> Dict:
        """Convert rung to dictionary format showing the sequence structure."""
        return {
            'rung_number': self.number,
            'comment': self.comment,
            'text': self.text,
            'instruction_count': len(self.instructions),
            'branch_count': len(self._branches),
            'execution_sequence': self.get_execution_sequence(),
            'main_line_instructions': [instr.meta_data for instr in self.get_main_line_instructions()],
            'branches': {
                branch_id: {
                    'start_position': branch.start_position,
                    'end_position': branch.end_position,
                    'instructions': [instr.meta_data for instr in branch.instructions]
                }
                for branch_id, branch in self._branches.items()
            }
        }

    def validate_branch_structure(self) -> bool:
        """Validate that branch markers are properly paired.

        Returns:
            bool: True if branch structure is valid, False otherwise
        """
        if not self.text:
            return True

        tokens = self._tokenize_rung_text(self.text)
        bracket_count = 0

        for token in tokens:
            if token == '[':
                bracket_count += 1
            elif token == ']':
                bracket_count -= 1
                if bracket_count < 0:
                    return False

        return bracket_count == 0

    def wrap_instructions_in_branch(self, start_position: int, end_position: int) -> str:
        """Wrap existing instructions in a new branch structure.

        Args:
            start_position (int): Start position of instructions to wrap
            end_position (int): End position of instructions to wrap

        Returns:
            str: The branch ID that was created

        Raises:
            ValueError: If positions are invalid
            IndexError: If positions are out of range
        """
        if not self.text:
            raise ValueError("Cannot wrap instructions in empty rung!")

        current_instructions = re.findall(plc_meta.INST_RE_PATTERN, self.text)
        if not current_instructions:
            raise ValueError("No instructions found in rung!")

        if start_position < 0 or end_position < 0:
            raise ValueError("Positions must be non-negative!")

        if start_position >= len(current_instructions) or end_position > len(current_instructions):
            raise IndexError("Positions out of range!")

        if start_position > end_position:
            raise ValueError("Start position must be less than or equal to end position!")

        # Get instructions to wrap
        instructions_to_wrap = current_instructions[start_position:end_position]

        # Remove the original instructions
        for i in range(start_position, end_position):
            self.remove_instruction(i)

        # Insert branch with wrapped instructions
        branch_id = self.insert_branch(start_position, start_position, instructions_to_wrap)

        return branch_id

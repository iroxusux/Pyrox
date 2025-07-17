"""Ladder Logic Editor components for Pyrox framework."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import tkinter as tk
from tkinter import ttk, Canvas
from typing import Optional, Dict, List
import re

from .frames import TaskFrame
from ..plc import plc
from ..abc.meta import Loggable


class LadderEditorMode(Enum):
    """Editing modes for the ladder editor."""
    VIEW = "view"
    EDIT = "edit"
    INSERT_CONTACT = "insert_contact"
    INSERT_COIL = "insert_coil"
    INSERT_BLOCK = "insert_block"
    INSERT_BRANCH = "insert_branch"
    CONNECT_BRANCH = "connect_branch"


@dataclass
class LadderElement:
    """Represents a ladder logic element on the canvas."""
    element_type: str  # 'contact', 'coil', 'block', 'wire', 'branch_start', 'branch_end'
    x: int
    y: int
    width: int
    height: int
    canvas_id: int
    instruction: Optional[plc.LogixInstruction] = None
    text: str = ""
    is_selected: bool = False
    branch_level: int = 0
    branch_id: Optional[str] = None
    position: int = 0  # Position in rung sequence


@dataclass
class LadderBranch:
    """Represents a branch structure in ladder logic."""
    start_x: int
    end_x: int
    main_y: int
    branch_y: int
    rung_number: int
    branch_id: str
    elements: List[LadderElement]
    start_position: int = 0
    end_position: int = 0


class LadderCanvas(Canvas, Loggable):
    """Canvas for drawing ladder logic diagrams."""

    GRID_SIZE = 20
    RUNG_HEIGHT = 60
    CONTACT_WIDTH = 40
    CONTACT_HEIGHT = 30
    COIL_WIDTH = 40
    COIL_HEIGHT = 30
    BLOCK_WIDTH = 80
    BLOCK_HEIGHT = 40
    BRANCH_SPACING = 25

    def __init__(self, master, routine: Optional[plc.Routine] = None, **kwargs):
        Canvas.__init__(self,
                        master,
                        bg=kwargs.pop('bg', 'white'),
                        **kwargs)
        Loggable.__init__(self)

        self._routine = routine
        self._elements: List[LadderElement] = []
        self._selected_elements: List[LadderElement] = []
        self._mode = LadderEditorMode.VIEW
        self._current_rung = 0
        self._rung_y_positions: Dict[int, int] = {}
        self._branches: Dict[str, LadderBranch] = {}
        self._pending_branch_start: Optional[LadderElement] = None
        self._branch_counter = 0

        # Bind events
        self.bind('<Button-1>', self._on_click)
        self.bind('<Button-3>', self._on_right_click)
        self.bind('<Motion>', self._on_motion)
        self.bind('<B1-Motion>', self._on_drag)
        self.bind('<Double-Button-1>', self._on_double_click)

        # Setup scrolling
        self.bind('<MouseWheel>', self._on_mousewheel)

        if self._routine:
            self._draw_routine()

    @property
    def routine(self) -> Optional[plc.Routine]:
        """Get the current routine being edited."""
        return self._routine

    @routine.setter
    def routine(self, value: Optional[plc.Routine]):
        """Set the routine to edit."""
        self._routine = value
        self.clear_canvas()
        if self._routine:
            self._draw_routine()

    @property
    def mode(self) -> LadderEditorMode:
        """Get the current editing mode."""
        return self._mode

    @mode.setter
    def mode(self, value: LadderEditorMode):
        """Set the editing mode."""
        self._mode = value
        self.config(cursor=self._get_cursor_for_mode(value))

    def _get_cursor_for_mode(self, mode: LadderEditorMode) -> str:
        """Get appropriate cursor for editing mode."""
        cursors = {
            LadderEditorMode.VIEW: "arrow",
            LadderEditorMode.EDIT: "hand2",
            LadderEditorMode.INSERT_CONTACT: "crosshair",
            LadderEditorMode.INSERT_COIL: "crosshair",
            LadderEditorMode.INSERT_BLOCK: "crosshair",
            LadderEditorMode.INSERT_BRANCH: "crosshair",
            LadderEditorMode.CONNECT_BRANCH: "target"
        }
        return cursors.get(mode, "arrow")

    def clear_canvas(self):
        """Clear all elements from the canvas."""
        self.delete("all")
        self._elements.clear()
        self._selected_elements.clear()
        self._rung_y_positions.clear()
        self._branches.clear()
        self._pending_branch_start = None

    def _draw_routine(self):
        """Draw the entire routine on the canvas."""
        self.clear_canvas()
        if not self._routine or not self._routine.rungs:
            self._draw_rung(None, 0, 50)  # Draw empty rung if no routine
            return

        y_pos = 50
        for i, rung in enumerate(self._routine.rungs):
            self._draw_rung(rung, i, y_pos)
            y_pos += self.RUNG_HEIGHT + 20

        # Update scroll region
        self.configure(scrollregion=self.bbox("all"))

    def _draw_rung(self, rung: plc.Rung, rung_number: int, y_pos: int):
        """Draw a single rung using the enhanced PLC data structure."""
        self._rung_y_positions[rung_number] = y_pos

        # Draw rung number
        self.create_text(10, y_pos + self.RUNG_HEIGHT // 2,
                         text=str(rung_number), anchor='w', font=('Arial', 10))

        # Draw power rails
        rail_x = 40
        self.create_line(rail_x, y_pos, rail_x, y_pos + self.RUNG_HEIGHT,
                         width=3, tags=f"rung_{rung_number}")

        right_rail_x = self.winfo_reqwidth() - 40 if self.winfo_reqwidth() > 100 else 600
        self.create_line(right_rail_x, y_pos, right_rail_x, y_pos + self.RUNG_HEIGHT,
                         width=3, tags=f"rung_{rung_number}")

        center_y = y_pos + self.RUNG_HEIGHT // 2

        if rung and hasattr(rung, 'rung_sequence') and rung.rung_sequence:
            # Use the enhanced rung sequence from PLC model
            self._draw_rung_sequence(rung, rung_number, y_pos, rail_x + 10)
        elif rung and hasattr(rung, 'instructions') and rung.instructions:
            # Fallback to basic instruction drawing
            self._draw_rung_instructions(rung.instructions, rung_number, y_pos, rail_x + 10)
        else:
            # Draw empty rung line
            self.create_line(rail_x, center_y, right_rail_x, center_y,
                             width=2, tags=f"rung_{rung_number}")

    def _draw_rung_sequence(self, rung: plc.Rung, rung_number: int, y_pos: int, start_x: int):
        """Draw rung using the enhanced sequence structure from PLC model."""
        current_x = start_x
        center_y = y_pos + self.RUNG_HEIGHT // 2
        branch_stack = []  # Track active branches

        for element in rung.rung_sequence:
            if element.element_type == plc.RungElementType.INSTRUCTION:
                # Draw the instruction
                ladder_element = self._draw_instruction(element.instruction, current_x, center_y, rung_number)
                if ladder_element:
                    ladder_element.position = element.position

                    # Determine branch level based on active branches
                    ladder_element.branch_level = len(branch_stack)
                    if branch_stack:
                        ladder_element.branch_id = branch_stack[-1]

                    self._elements.append(ladder_element)
                    current_x += ladder_element.width + 10

            elif element.element_type == plc.RungElementType.BRANCH_START:
                # Handle branch start
                branch_y = center_y + (len(branch_stack) + 1) * self.BRANCH_SPACING

                # Create visual branch start marker
                branch_start_id = self.create_oval(
                    current_x - 5, center_y - 5,
                    current_x + 5, center_y + 5,
                    fill='green', outline='darkgreen', width=2,
                    tags=f"rung_{rung_number}_branch_marker"
                )

                ladder_element = LadderElement(
                    element_type='branch_start',
                    x=current_x - 5,
                    y=center_y - 5,
                    width=10, height=10,
                    canvas_id=branch_start_id,
                    branch_level=len(branch_stack) + 1,
                    branch_id=element.branch_id,
                    position=element.position
                )
                self._elements.append(ladder_element)

                # Create branch structure
                branch = LadderBranch(
                    start_x=current_x,
                    end_x=-1,  # Will be set at branch end
                    main_y=center_y,
                    branch_y=branch_y,
                    rung_number=rung_number,
                    branch_id=element.branch_id,
                    elements=[],
                    start_position=element.position,
                    end_position=-1
                )
                self._branches[element.branch_id] = branch
                branch_stack.append(element.branch_id)

                # Draw vertical line down to branch
                self.create_line(
                    current_x, center_y,
                    current_x, branch_y,
                    width=2, tags=f"rung_{rung_number}_branch"
                )

            elif element.element_type == plc.RungElementType.BRANCH_END:
                # Handle branch end
                if branch_stack and element.branch_id in branch_stack:
                    branch_stack.remove(element.branch_id)

                if element.branch_id in self._branches:
                    branch = self._branches[element.branch_id]
                    branch.end_x = current_x
                    branch.end_position = element.position

                    # Create visual branch end marker
                    branch_end_id = self.create_oval(
                        current_x - 5, center_y - 5,
                        current_x + 5, center_y + 5,
                        fill='red', outline='darkred', width=2,
                        tags=f"rung_{rung_number}_branch_marker"
                    )

                    ladder_element = LadderElement(
                        element_type='branch_end',
                        x=current_x - 5,
                        y=center_y - 5,
                        width=10, height=10,
                        canvas_id=branch_end_id,
                        branch_level=len(branch_stack),
                        branch_id=element.branch_id,
                        position=element.position
                    )
                    self._elements.append(ladder_element)

                    # Draw vertical line back up to main rung
                    self.create_line(
                        current_x, branch.branch_y,
                        current_x, center_y,
                        width=2, tags=f"rung_{rung_number}_branch"
                    )

                    # Draw horizontal branch line
                    self.create_line(
                        branch.start_x, branch.branch_y,
                        current_x, branch.branch_y,
                        width=2, tags=f"rung_{rung_number}_branch"
                    )

    def _draw_rung_instructions(self,
                                instructions: List[plc.LogixInstruction],
                                rung_number: int, y_pos: int,
                                start_x: int):
        """Draw instructions for a rung (fallback method)."""
        current_x = start_x
        center_y = y_pos + self.RUNG_HEIGHT // 2

        for instruction in instructions:
            element = self._draw_instruction(instruction, current_x, center_y, rung_number)
            if element:
                self._elements.append(element)
                current_x += element.width + 10

    def _draw_instruction(self, instruction: plc.LogixInstruction, x: int, y: int,
                          rung_number: int) -> Optional[LadderElement]:
        """Draw a single instruction.

        Args:
            instruction: The LogixInstruction to draw
            x: X position for the instruction
            y: Y position (should be the rung centerline)
            rung_number: The rung number this instruction belongs to
        """
        inst_type = instruction.instruction_name.lower()

        if inst_type in ['xic', 'xio']:  # Contacts
            return self._draw_contact(instruction, x, y, rung_number)
        elif inst_type in ['ote', 'otl', 'otu']:  # Coils
            return self._draw_coil(instruction, x, y, rung_number)
        else:  # Function blocks
            return self._draw_block(instruction, x, y, rung_number)

    def _draw_contact(self, instruction: plc.LogixInstruction, x: int, center_y: int,
                      rung_number: int) -> LadderElement:
        """Draw a contact instruction centered on the rung."""
        # Determine contact type
        is_normally_closed = instruction.instruction_name.lower() == 'xio'

        # Calculate top and bottom Y positions for centering
        top_y = center_y - self.CONTACT_HEIGHT // 2
        bottom_y = center_y + self.CONTACT_HEIGHT // 2

        # Draw contact symbol (centered on rung)
        rect_id = self.create_rectangle(
            x, top_y,
            x + self.CONTACT_WIDTH, bottom_y,
            outline='black', fill='white', width=2,
            tags=f"rung_{rung_number}_instruction"
        )

        # Add contact bars
        if is_normally_closed:
            # Diagonal line for normally closed (centered in contact)
            self.create_line(
                x + 5, top_y + 5,
                x + self.CONTACT_WIDTH - 5, bottom_y - 5,
                width=2, tags=f"rung_{rung_number}_instruction"
            )
        else:
            # Vertical lines for normally open (centered in contact)
            bar_top = top_y + 5
            bar_bottom = bottom_y - 5
            self.create_line(
                x + 10, bar_top,
                x + 10, bar_bottom,
                width=2, tags=f"rung_{rung_number}_instruction"
            )
            self.create_line(
                x + self.CONTACT_WIDTH - 10, bar_top,
                x + self.CONTACT_WIDTH - 10, bar_bottom,
                width=2, tags=f"rung_{rung_number}_instruction"
            )

        # Draw connecting wires to power rail (horizontal lines at rung center)
        wire_y = center_y
        # Left connecting wire (from power rail to contact)
        self.create_line(
            x - 10, wire_y,  # Start 10 pixels before contact
            x, wire_y,       # End at contact left edge
            width=2, tags=f"rung_{rung_number}_wire"
        )
        # Right connecting wire (from contact to next element)
        self.create_line(
            x + self.CONTACT_WIDTH, wire_y,
            x + self.CONTACT_WIDTH + 10, wire_y,
            width=2, tags=f"rung_{rung_number}_wire"
        )

        # Add operand text below the contact
        operand = instruction.operands[0].meta_data if instruction.operands else "???"
        _ = self.create_text(
            x + self.CONTACT_WIDTH // 2, bottom_y + 15,
            text=operand, font=('Arial', 8), tags=f"rung_{rung_number}_instruction"
        )

        return LadderElement(
            element_type='contact',
            x=x, y=top_y,
            width=self.CONTACT_WIDTH, height=self.CONTACT_HEIGHT,
            canvas_id=rect_id,
            instruction=instruction,
            text=operand
        )

    def _draw_coil(self, instruction: plc.LogixInstruction, x: int, center_y: int,
                   rung_number: int) -> LadderElement:
        """Draw a coil instruction centered on the rung."""
        # Calculate top and bottom Y positions for centering
        top_y = center_y - self.COIL_HEIGHT // 2
        bottom_y = center_y + self.COIL_HEIGHT // 2

        # Draw coil circle (centered on rung)
        circle_id = self.create_oval(
            x, top_y,
            x + self.COIL_WIDTH, bottom_y,
            outline='black', fill='white', width=2,
            tags=f"rung_{rung_number}_instruction"
        )

        # Add coil type indicators (centered in coil)
        inst_type = instruction.instruction_name.lower()
        if inst_type == 'otl':  # Latch
            self.create_text(
                x + self.COIL_WIDTH // 2, center_y,
                text='L', font=('Arial', 12, 'bold'),
                tags=f"rung_{rung_number}_instruction"
            )
        elif inst_type == 'otu':  # Unlatch
            self.create_text(
                x + self.COIL_WIDTH // 2, center_y,
                text='U', font=('Arial', 12, 'bold'),
                tags=f"rung_{rung_number}_instruction"
            )

        # Draw connecting wires at rung centerline
        wire_y = center_y
        # Left connecting wire
        self.create_line(
            x - 10, wire_y,
            x, wire_y,
            width=2, tags=f"rung_{rung_number}_wire"
        )
        # Right connecting wire (to power rail if this is the last element)
        self.create_line(
            x + self.COIL_WIDTH, wire_y,
            x + self.COIL_WIDTH + 10, wire_y,
            width=2, tags=f"rung_{rung_number}_wire"
        )

        # Add operand text below the coil
        operand = instruction.operands[0].meta_data if instruction.operands else "???"
        _ = self.create_text(
            x + self.COIL_WIDTH // 2, bottom_y + 15,
            text=operand, font=('Arial', 8), tags=f"rung_{rung_number}_instruction"
        )

        return LadderElement(
            element_type='coil',
            x=x, y=top_y,
            width=self.COIL_WIDTH, height=self.COIL_HEIGHT,
            canvas_id=circle_id,
            instruction=instruction,
            text=operand
        )

    def _draw_block(self, instruction: plc.LogixInstruction, x: int, center_y: int,
                    rung_number: int) -> LadderElement:
        """Draw a function block instruction centered on the rung."""
        # Calculate top and bottom Y positions for centering
        top_y = center_y - self.BLOCK_HEIGHT // 2
        bottom_y = center_y + self.BLOCK_HEIGHT // 2

        # Draw block rectangle (centered on rung)
        rect_id = self.create_rectangle(
            x, top_y,
            x + self.BLOCK_WIDTH, bottom_y,
            outline='black', fill='lightblue', width=2,
            tags=f"rung_{rung_number}_instruction"
        )

        # Add instruction type text (centered in top half of block)
        inst_name = instruction.instruction_name
        self.create_text(
            x + self.BLOCK_WIDTH // 2, center_y - 10,
            text=inst_name, font=('Arial', 10, 'bold'),
            tags=f"rung_{rung_number}_instruction"
        )

        # Add operands text (centered in bottom half of block)
        operands_text = ', '.join([op.meta_data for op in instruction.operands]) if instruction.operands else ""
        if len(operands_text) > 12:
            operands_text = operands_text[:12] + "..."

        self.create_text(
            x + self.BLOCK_WIDTH // 2, center_y + 5,
            text=operands_text, font=('Arial', 8),
            tags=f"rung_{rung_number}_instruction"
        )

        # Draw connecting wires at rung centerline
        wire_y = center_y
        # Left connecting wire
        self.create_line(
            x - 10, wire_y,
            x, wire_y,
            width=2, tags=f"rung_{rung_number}_wire"
        )
        # Right connecting wire
        self.create_line(
            x + self.BLOCK_WIDTH, wire_y,
            x + self.BLOCK_WIDTH + 10, wire_y,
            width=2, tags=f"rung_{rung_number}_wire"
        )

        return LadderElement(
            element_type='block',
            x=x, y=top_y,
            width=self.BLOCK_WIDTH, height=self.BLOCK_HEIGHT,
            canvas_id=rect_id,
            instruction=instruction,
            text=operands_text
        )

    def _on_click(self, event):
        """Handle mouse click events."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)

        if self._mode == LadderEditorMode.VIEW:
            self._select_element_at(x, y)
        elif self._mode == LadderEditorMode.INSERT_BRANCH:
            self._start_branch_creation(x, y)
        elif self._mode == LadderEditorMode.CONNECT_BRANCH:
            self._connect_branch_endpoint(x, y)
        elif self._mode in [LadderEditorMode.INSERT_CONTACT,
                            LadderEditorMode.INSERT_COIL,
                            LadderEditorMode.INSERT_BLOCK]:
            self._insert_element_at(x, y)

    def _start_branch_creation(self, x: int, y: int):
        """Start creating a branch at the clicked location."""
        rung_number = self._get_rung_at_y(y)
        if rung_number is None:
            return

        # Find the nearest element to start the branch from
        nearest_element = self._find_nearest_element_on_rung(x, y, rung_number)
        if not nearest_element:
            return

        # Create branch start marker
        branch_id = f"branch_{self._branch_counter}"
        self._branch_counter += 1

        rung_y_pos = self._rung_y_positions[rung_number]
        center_y = rung_y_pos + self.RUNG_HEIGHT // 2
        _ = center_y + self.BRANCH_SPACING

        # Visual indicator for branch start
        branch_start_id = self.create_oval(
            nearest_element.x + nearest_element.width - 5,
            center_y - 5,
            nearest_element.x + nearest_element.width + 5,
            center_y + 5,
            fill='green', outline='darkgreen', width=2,
            tags=f"rung_{rung_number}_branch_marker"
        )

        branch_element = LadderElement(
            element_type='branch_start',
            x=nearest_element.x + nearest_element.width,
            y=center_y - 5,
            width=10, height=10,
            canvas_id=branch_start_id,
            branch_level=1,
            branch_id=branch_id,
            position=nearest_element.position + 1
        )

        self._elements.append(branch_element)
        self._pending_branch_start = branch_element

        # Switch to connect mode
        self.mode = LadderEditorMode.CONNECT_BRANCH
        self._show_status("Click where you want the branch to reconnect")

    def _connect_branch_endpoint(self, x: int, y: int):
        """Connect the branch back to the main rung."""
        if not self._pending_branch_start:
            return

        rung_number = self._get_rung_at_y(y)
        if rung_number is None:
            return

        # Find connection point
        connection_element = self._find_nearest_element_on_rung(x, y, rung_number)
        if not connection_element:
            return

        # Create branch end marker
        rung_y_pos = self._rung_y_positions[rung_number]
        center_y = rung_y_pos + self.RUNG_HEIGHT // 2

        branch_end_id = self.create_oval(
            connection_element.x - 5,
            center_y - 5,
            connection_element.x + 5,
            center_y + 5,
            fill='red', outline='darkred', width=2,
            tags=f"rung_{rung_number}_branch_marker"
        )

        branch_end = LadderElement(
            element_type='branch_end',
            x=connection_element.x - 5,
            y=center_y - 5,
            width=10, height=10,
            canvas_id=branch_end_id,
            branch_level=1,
            branch_id=self._pending_branch_start.branch_id,
            position=connection_element.position
        )

        self._elements.append(branch_end)

        # Create the branch structure
        branch = LadderBranch(
            start_x=self._pending_branch_start.x,
            end_x=branch_end.x,
            main_y=center_y,
            branch_y=center_y + self.BRANCH_SPACING,
            rung_number=rung_number,
            branch_id=self._pending_branch_start.branch_id,
            elements=[],
            start_position=self._pending_branch_start.position,
            end_position=branch_end.position
        )

        self._branches[branch.branch_id] = branch

        # Draw the branch connections
        self._draw_branch_connections(
            branch.start_x, branch.end_x,
            branch.main_y, branch.branch_y,
            rung_number
        )

        # Update the underlying PLC rung structure
        self._update_rung_structure_with_branch(rung_number, branch)

        self._pending_branch_start = None
        self.mode = LadderEditorMode.VIEW
        self._show_status(f"Branch created: {branch.branch_id}")

    def _update_rung_structure_with_branch(self, rung_number: int, branch: LadderBranch):
        """Update the underlying PLC rung structure to include the new branch."""
        if not self._routine or rung_number >= len(self._routine.rungs):
            return

        rung = self._routine.rungs[rung_number]

        # Parse current rung text to insert branch markers
        current_text = rung.text if rung.text else ""

        # Find positions in the text where branch markers should be inserted
        # This is a simplified approach - you may need more sophisticated parsing
        instructions = re.findall(plc.INST_RE_PATTERN, current_text)

        if len(instructions) >= 2:
            # Insert branch start after first instruction
            start_instr = instructions[0] if instructions else ""
            end_instr = instructions[-1] if len(instructions) > 1 else ""

            # Create new rung text with branch markers
            # This is a basic implementation - you may need to handle more complex cases
            new_text = f"{start_instr}[{end_instr}]"

            # Update the rung
            rung.text = new_text

            self.logger.info(f"Updated rung {rung_number} with branch structure: {new_text}")

    def _draw_branch_connections(self, start_x: int, end_x: int, main_y: int,
                                 branch_y: int, rung_number: int):
        """Draw the connecting lines for a branch."""
        # Vertical line down to branch
        self.create_line(
            start_x, main_y,
            start_x, branch_y,
            width=2, tags=f"rung_{rung_number}_branch"
        )

        # Vertical line back up from branch
        self.create_line(
            end_x, branch_y,
            end_x, main_y,
            width=2, tags=f"rung_{rung_number}_branch"
        )

        # Horizontal line for the branch
        self.create_line(
            start_x, branch_y,
            end_x, branch_y,
            width=2, tags=f"rung_{rung_number}_branch"
        )

    def _find_nearest_element_on_rung(self, x: int, y: int, rung_number: int) -> Optional[LadderElement]:
        """Find the nearest element on the specified rung."""
        rung_elements = [e for e in self._elements
                         if self._get_rung_at_y(e.y + e.height // 2) == rung_number
                         and e.element_type in ['contact', 'coil', 'block']]

        if not rung_elements:
            return None

        # Find closest element by X distance
        closest = min(rung_elements, key=lambda e: abs(e.x + e.width // 2 - x))
        return closest

    def _insert_element_at(self, x: int, y: int):
        """Insert new element at given coordinates, handling branches."""
        rung_number = self._get_rung_at_y(y)
        if rung_number is None:
            return

        # Determine if we're inserting on a branch
        branch_level = self._get_branch_level_at_y(y, rung_number)

        rung_y_pos = self._rung_y_positions[rung_number]
        center_y = rung_y_pos + self.RUNG_HEIGHT // 2 + (branch_level * self.BRANCH_SPACING)

        # Create new instruction based on mode
        if self._mode == LadderEditorMode.INSERT_CONTACT:
            self._insert_contact(x, center_y, rung_number, branch_level)
        elif self._mode == LadderEditorMode.INSERT_COIL:
            self._insert_coil(x, center_y, rung_number, branch_level)
        elif self._mode == LadderEditorMode.INSERT_BLOCK:
            self._insert_block(x, center_y, rung_number, branch_level)

    def _get_branch_level_at_y(self, y: int, rung_number: int) -> int:
        """Determine which branch level the Y coordinate corresponds to."""
        if rung_number not in self._rung_y_positions:
            return 0

        rung_y = self._rung_y_positions[rung_number]
        center_y = rung_y + self.RUNG_HEIGHT // 2

        # Calculate branch level based on Y offset
        offset = y - center_y
        if abs(offset) < self.BRANCH_SPACING // 2:
            return 0  # Main rung
        else:
            return max(1, int(offset / self.BRANCH_SPACING))

    def _insert_contact(self, x: int, center_y: int, rung_number: int, branch_level: int = 0):
        """Insert a contact, optionally on a branch."""
        new_instruction = plc.LogixInstruction(
            meta_data='XIC(NewContact)',
            rung=self._routine.rungs[rung_number] if self._routine else None,
            controller=self._routine.controller if self._routine else None
        )

        element = self._draw_contact(new_instruction, x, center_y, rung_number)
        if element:
            element.branch_level = branch_level
            self._elements.append(element)
            self._add_instruction_to_rung(new_instruction, rung_number)

    def _insert_coil(self, x: int, center_y: int, rung_number: int, branch_level: int = 0):
        """Insert a new coil at given position (centered on rung)."""
        new_instruction = plc.LogixInstruction(
            meta_data='OTE(NewCoil)',
            rung=self._routine.rungs[rung_number] if self._routine else None,
            controller=self._routine.controller if self._routine else None
        )

        element = self._draw_coil(new_instruction, x, center_y, rung_number)
        if element:
            element.branch_level = branch_level
            self._elements.append(element)
            self._add_instruction_to_rung(new_instruction, rung_number)

    def _insert_block(self, x: int, center_y: int, rung_number: int, branch_level: int = 0):
        """Insert a new function block at given position (centered on rung)."""
        new_instruction = plc.LogixInstruction(
            meta_data='TON(Timer1,1000,0)',
            rung=self._routine.rungs[rung_number] if self._routine else None,
            controller=self._routine.controller if self._routine else None
        )

        element = self._draw_block(new_instruction, x, center_y, rung_number)
        if element:
            element.branch_level = branch_level
            self._elements.append(element)
            self._add_instruction_to_rung(new_instruction, rung_number)

    def _add_instruction_to_rung(self, instruction: plc.LogixInstruction, rung_number: int):
        """Add instruction to the appropriate rung in the routine."""
        if not self._routine or not hasattr(self._routine, 'rungs'):
            return

        if rung_number < len(self._routine.rungs):
            rung = self._routine.rungs[rung_number]

            # Add to text-based representation
            current_text = rung.text if rung.text else ""
            if current_text:
                rung.text = f"{current_text} {instruction.meta_data}"
            else:
                rung.text = instruction.meta_data

    def _show_status(self, message: str):
        """Show status message (to be connected to status bar)."""
        self.logger.info(message)

    def _on_right_click(self, event):
        """Handle right-click context menu."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        element = self._get_element_at(x, y)

        if element:
            self._show_context_menu(event, element)

    def _on_double_click(self, event):
        """Handle double-click to edit element."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        element = self._get_element_at(x, y)

        if element and element.instruction:
            self._edit_instruction(element.instruction)

    def _on_motion(self, event):
        """Handle mouse motion for hover effects."""
        pass

    def _on_drag(self, event):
        """Handle mouse drag for moving elements."""
        pass

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _select_element_at(self, x: int, y: int):
        """Select element at given coordinates."""
        element = self._get_element_at(x, y)

        # Clear previous selection
        for elem in self._selected_elements:
            self.itemconfig(elem.canvas_id, outline='black', width=2)
            elem.is_selected = False

        self._selected_elements.clear()

        if element:
            self.itemconfig(element.canvas_id, outline='red', width=3)
            element.is_selected = True
            self._selected_elements.append(element)

    def _get_element_at(self, x: int, y: int) -> Optional[LadderElement]:
        """Get element at given coordinates."""
        for element in self._elements:
            if (element.x <= x <= element.x + element.width and
                    element.y <= y <= element.y + element.height):
                return element
        return None

    def _get_rung_at_y(self, y: int) -> Optional[int]:
        """Get rung number at given Y coordinate."""
        for rung_num, rung_y in self._rung_y_positions.items():
            if rung_y <= y <= rung_y + self.RUNG_HEIGHT:
                return rung_num
        return None

    def _show_context_menu(self, event, element: LadderElement):
        """Show context menu for element."""
        menu = tk.Menu(self, tearoff=0)

        if element.element_type in ['contact', 'coil', 'block']:
            menu.add_command(label="Edit", command=lambda: self._edit_instruction(element.instruction))
            menu.add_command(label="Delete", command=lambda: self._delete_element(element))
            menu.add_separator()
            menu.add_command(label="Add Branch Here", command=lambda: self._add_branch_at_element(element))
            menu.add_separator()
            menu.add_command(label="Copy", command=lambda: self._copy_element(element))
            menu.add_command(label="Paste", command=lambda: self._paste_element())
        elif element.element_type in ['branch_start', 'branch_end']:
            menu.add_command(label="Delete Branch", command=lambda: self._delete_branch(element.branch_id))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _edit_instruction(self, instruction: plc.LogixInstruction):
        """Edit an instruction (placeholder - implement instruction editor dialog)."""
        self._show_status(f"Edit instruction: {instruction.meta_data}")

    def _delete_element(self, element: LadderElement):
        """Delete an element from the rung."""
        # Remove from canvas
        self.delete(element.canvas_id)

        # Remove from elements list
        if element in self._elements:
            self._elements.remove(element)

        # Remove from selection if selected
        if element in self._selected_elements:
            self._selected_elements.remove(element)

        self._show_status(f"Deleted element: {element.text}")

    def _add_branch_at_element(self, element: LadderElement):
        """Add a branch starting at the specified element."""
        self._pending_branch_start = element
        self.mode = LadderEditorMode.CONNECT_BRANCH
        self._show_status("Click where you want the branch to reconnect")

    def _copy_element(self, element: LadderElement):
        """Copy an element (placeholder)."""
        self._show_status(f"Copied element: {element.text}")

    def _paste_element(self):
        """Paste an element (placeholder)."""
        self._show_status("Paste functionality not implemented")

    def _delete_branch(self, branch_id: str):
        """Delete a branch and all its elements."""
        if branch_id in self._branches:
            branch = self._branches[branch_id]

            # Remove branch elements from canvas
            elements_to_remove = [e for e in self._elements if e.branch_id == branch_id]
            for element in elements_to_remove:
                self.delete(element.canvas_id)
                self._elements.remove(element)

            # Remove branch lines
            self.delete(f"rung_{branch.rung_number}_branch")

            # Remove from branches dict
            del self._branches[branch_id]

            self._show_status(f"Deleted branch: {branch_id}")

    def add_rung(self) -> int:
        """Add a new empty rung to the routine."""
        if not self._routine:
            # Create a basic routine if none exists
            self._routine = plc.Routine(controller=None)

        # Create new rung
        new_rung = plc.Rung(controller=self._routine.controller if self._routine else None)
        new_rung.number = str(len(self._routine.rungs))
        new_rung.text = ""
        new_rung.comment = ""

        # Add to routine
        self._routine.add_rung(new_rung)

        # Redraw routine
        self._draw_routine()

        return len(self._routine.rungs) - 1

    def delete_rung(self, rung_number: int):
        """Delete a rung from the routine."""
        if (not self._routine or not hasattr(self._routine, 'rungs') or
                rung_number >= len(self._routine.rungs)):
            return

        # Remove from routine data
        self._routine.remove_rung(rung_number)

        # Redraw routine
        self._draw_routine()

        self.logger.info(f"Deleted rung {rung_number}")


class LadderEditorTaskFrame(TaskFrame):
    """Main task frame for the ladder logic editor."""

    def __init__(self,
                 master,
                 routine: Optional[plc.Routine] = None,
                 controller: Optional[plc.Controller] = None,
                 **kwargs):
        name = f"Ladder Editor - {routine.name if routine else 'New Routine'}"
        super().__init__(master,
                         name=name,
                         **kwargs)

        self._routine = routine
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self):
        """Setup the ladder editor UI."""
        # Create toolbar
        self._create_toolbar()

        # Create main editor area with scrollbars
        self._create_editor_area()

        # Create status bar
        self._create_status_bar()

    def _create_toolbar(self):
        """Create the editor toolbar."""
        toolbar = tk.Frame(self.content_frame, height=40, relief='raised', bd=1)
        toolbar.pack(fill='x', side='top')

        # Mode buttons
        tk.Button(toolbar, text="Select",
                  command=lambda: self._set_mode(LadderEditorMode.VIEW)).pack(side='left', padx=2)
        tk.Button(toolbar, text="Contact",
                  command=lambda: self._set_mode(LadderEditorMode.INSERT_CONTACT)).pack(side='left', padx=2)
        tk.Button(toolbar, text="Coil",
                  command=lambda: self._set_mode(LadderEditorMode.INSERT_COIL)).pack(side='left', padx=2)
        tk.Button(toolbar, text="Block",
                  command=lambda: self._set_mode(LadderEditorMode.INSERT_BLOCK)).pack(side='left', padx=2)

        # Branch controls
        tk.Button(toolbar, text="Branch",
                  command=lambda: self._set_mode(LadderEditorMode.INSERT_BRANCH)).pack(side='left', padx=2)

        # Separator
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=5)

        # Rung operations
        tk.Button(toolbar, text="Add Rung",
                  command=self._add_rung).pack(side='left', padx=2)
        tk.Button(toolbar, text="Delete Rung",
                  command=self._delete_current_rung).pack(side='left', padx=2)

        # Separator
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=5)

        # File operations
        tk.Button(toolbar, text="Verify",
                  command=self._verify_routine).pack(side='left', padx=2)
        tk.Button(toolbar, text="Accept",
                  command=self._accept_changes).pack(side='left', padx=2)

    def _create_editor_area(self):
        """Create the main editor canvas with scrollbars."""
        editor_frame = tk.Frame(self.content_frame)
        editor_frame.pack(fill='both', expand=True)

        # Create canvas with scrollbars
        self._ladder_canvas = LadderCanvas(editor_frame,
                                           routine=self._routine,
                                           bg='white',
                                           width=800,
                                           height=600)

        # Vertical scrollbar
        v_scrollbar = tk.Scrollbar(editor_frame, orient='vertical',
                                   command=self._ladder_canvas.yview)
        self._ladder_canvas.configure(yscrollcommand=v_scrollbar.set)

        # Horizontal scrollbar
        h_scrollbar = tk.Scrollbar(editor_frame, orient='horizontal',
                                   command=self._ladder_canvas.xview)
        self._ladder_canvas.configure(xscrollcommand=h_scrollbar.set)

        # Grid layout
        self._ladder_canvas.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        editor_frame.grid_rowconfigure(0, weight=1)
        editor_frame.grid_columnconfigure(0, weight=1)

    def _create_status_bar(self):
        """Create the status bar."""
        self._status_bar = tk.Frame(self.content_frame, height=25, relief='sunken', bd=1)
        self._status_bar.pack(fill='x', side='bottom')

        self._status_label = tk.Label(self._status_bar, text="Ready", anchor='w')
        self._status_label.pack(side='left', padx=5)

        # Mode indicator
        self._mode_label = tk.Label(self._status_bar, text="Mode: View", anchor='e')
        self._mode_label.pack(side='right', padx=5)

    def _set_mode(self, mode: LadderEditorMode):
        """Set the editor mode."""
        self._ladder_canvas.mode = mode
        self._mode_label.config(text=f"Mode: {mode.value.title()}")
        self._status_label.config(text=f"Mode changed to {mode.value}")

    def _add_rung(self):
        """Add a new rung to the routine."""
        rung_number = self._ladder_canvas.add_rung()
        self._status_label.config(text=f"Added rung {rung_number}")

    def _delete_current_rung(self):
        """Delete the currently selected rung."""
        # This would need logic to determine which rung is selected
        self._status_label.config(text="Delete rung functionality not implemented")

    def _verify_routine(self):
        """Verify the routine for errors."""
        if self._routine:
            # This would integrate with your validation system
            report = self._routine.validate()
            status = "verified successfully" if report.pass_fail else "has errors"
            self._status_label.config(text=f"Routine {status}")
        else:
            self._status_label.config(text="No routine to verify")

    def _accept_changes(self):
        """Accept changes and close editor."""
        if self._routine:
            # This would save changes back to the routine
            self._status_label.config(text="Changes accepted")
        self.destroy()

    @property
    def routine(self) -> Optional[plc.Routine]:
        """Get the current routine."""
        return self._routine

    @routine.setter
    def routine(self, value: Optional[plc.Routine]):
        """Set the routine to edit."""
        self._routine = value
        self._ladder_canvas.routine = value
        if value:
            self.name = f"Ladder Editor - {value.name}"
            self._status_label.config(text=f"Loaded routine: {value.name}")

"""Ladder Logic Editor components for Pyrox framework."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import tkinter as tk
from tkinter import ttk, Canvas
from typing import Optional, Dict, List, Literal
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
    rung_number: int  # Rung number this element belongs to
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
    BLOCK_WIDTH = 80  # default width of a function block
    BLOCK_HEIGHT = 40  # default height of a function block
    BRANCH_SPACING = 60
    ELEMENT_SPACING = 30  # spacing between elements on a rail
    MIN_WIRE_LENGTH = 25
    RAIL_X_LEFT = 40  # Position of the left side power rail

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

        # Hover preview elements
        self._rung_hover_preview_id: Optional[int] = None
        self._hover_preview_id: Optional[int] = None
        self._last_hover_position: Optional[tuple] = None

        # Bind events
        self.bind('<Button-1>', self._on_click)
        self.bind('<Button-3>', self._on_right_click)
        self.bind('<Motion>', self._on_motion)
        self.bind('<B1-Motion>', self._on_drag)
        self.bind('<Double-Button-1>', self._on_double_click)
        self.bind('<Leave>', self._on_mouse_leave)

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
        # Clear hover preview when changing modes
        self._clear_hover_preview()
        self._mode = value
        self.config(cursor=self._get_cursor_for_mode(value))

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

    def _add_branch_at_element(self, element: LadderElement):
        """Add a branch starting at the specified element."""
        self._pending_branch_start = element
        self.mode = LadderEditorMode.CONNECT_BRANCH
        self._show_status("Click where you want the branch to reconnect")

    def _calculate_insertion_coordinates(self, click_x: int, click_y: int,
                                         rung_number: int, insertion_position: int,
                                         branch_level: int = 0,
                                         branch_id: Optional[str] = None) -> tuple[int, int]:
        """Calculate the exact coordinates where an element would be inserted."""
        rung_y_pos = self._rung_y_positions[rung_number]
        center_y = rung_y_pos + self.RUNG_HEIGHT // 2

        # Adjust Y for branch level
        if branch_level > 0:
            center_y += branch_level * self.BRANCH_SPACING

        # Get existing elements in this context
        rung_elements = self._get_rung_elements(rung_number, branch_level, branch_id)

        if not rung_elements:
            # No elements, insert at start
            return self.RAIL_X_LEFT + self.ELEMENT_SPACING + 30, center_y
        elif insertion_position == 0:
            return self.RAIL_X_LEFT + (self.ELEMENT_SPACING/2), center_y
        elif insertion_position >= len(rung_elements):
            # Insert at the end
            last_element = rung_elements[-1]
            return last_element.x + last_element.width + self.ELEMENT_SPACING + self.MIN_WIRE_LENGTH, center_y
        else:
            # Insert between elements
            prev_element = rung_elements[insertion_position - 1]
            this_element = rung_elements[insertion_position]
            prev_element_x_right = prev_element.x + prev_element.width
            element_dist_delta = this_element.x - prev_element_x_right
            insert_x = this_element.x - element_dist_delta // 2

            # Position between the two elements
            # insert_x = prev_element.x + prev_element.width + self.ELEMENT_SPACING + self.MIN_WIRE_LENGTH // 2
            return insert_x, center_y

    def _calculate_element_positions(self, rung_elements: List[LadderElement],
                                     start_x: int) -> Dict[int, int]:
        """Calculate X positions for elements with proper spacing."""
        positions = {}
        current_x = start_x

        # Sort elements by their position in the sequence
        sorted_elements = sorted(rung_elements, key=lambda e: e.position)

        for element in sorted_elements:
            positions[element.position] = current_x
            current_x += element.width + self.ELEMENT_SPACING + self.MIN_WIRE_LENGTH

        return positions

    def _clear_rung_visuals(self, rung_number: int):
        """Clear all visual elements for a specific rung."""
        # Remove canvas items
        self.delete(f"rung_{rung_number}_instruction")
        self.delete(f"rung_{rung_number}_wire")
        self.delete(f"rung_{rung_number}_branch")
        self.delete(f"rung_{rung_number}_branch_marker")

        # Remove elements from our tracking list
        elements_to_remove = [e for e in self._elements
                              if self._get_rung_at_y(e.y + e.height // 2) == rung_number]

        for element in elements_to_remove:
            self._elements.remove(element)

        # Remove branches for this rung
        branches_to_remove = [bid for bid, branch in self._branches.items()
                              if branch.rung_number == rung_number]

        for branch_id in branches_to_remove:
            del self._branches[branch_id]

    def _connect_branch_endpoint(self, x: int, y: int):
        """Connect the branch back to the main rung."""
        if not self._pending_branch_start:
            return

        rung_number = self._get_rung_at_y(y)
        if rung_number is None:
            return

        # Find connection point
        nearest_element = self._find_nearest_element_on_rung(x, y, rung_number)
        if not nearest_element:
            return

        # Create branch end marker
        rung_y_pos = self._rung_y_positions[rung_number]
        center_y = rung_y_pos + self.RUNG_HEIGHT // 2

        branch_end_id = self.create_oval(
            nearest_element.x + nearest_element.width + (self.ELEMENT_SPACING // 2) - 5,
            center_y - 5,
            nearest_element.x + nearest_element.width + (self.ELEMENT_SPACING // 2) + 5,
            center_y + 5,
            fill='red', outline='darkred', width=2,
            tags=f"rung_{rung_number}_branch_marker"
        )

        branch_end = LadderElement(
            element_type='branch_end',
            x=nearest_element.x + nearest_element.width + (self.ELEMENT_SPACING // 2),
            y=center_y - 5,
            width=10, height=10,
            canvas_id=branch_end_id,
            branch_level=1,
            branch_id=self._pending_branch_start.branch_id,
            position=nearest_element.position+1,
            rung_number=rung_number
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

        # Update the underlying PLC rung structure
        self._update_rung_structure_with_branch(rung_number, branch)
        self._pending_branch_start = None
        self.mode = LadderEditorMode.VIEW
        self._show_status(f"Branch created: {branch.branch_id}")
        self._redraw_rung(rung_number)

    def _create_contact_instruction(self, rung_number: int) -> plc.LogixInstruction:
        """Create a new contact instruction."""
        return plc.LogixInstruction(
            meta_data='XIC(NewContact)',
            rung=self._routine.rungs[rung_number] if self._routine else None,
            controller=self._routine.controller if self._routine else None
        )

    def _create_coil_instruction(self, rung_number: int) -> plc.LogixInstruction:
        """Create a new coil instruction."""
        return plc.LogixInstruction(
            meta_data='OTE(NewCoil)',
            rung=self._routine.rungs[rung_number] if self._routine else None,
            controller=self._routine.controller if self._routine else None
        )

    def _create_block_instruction(self, rung_number: int) -> plc.LogixInstruction:
        """Create a new function block instruction."""
        return plc.LogixInstruction(
            meta_data='TON(Timer1,1000,0)',
            rung=self._routine.rungs[rung_number] if self._routine else None,
            controller=self._routine.controller if self._routine else None
        )

    def _create_branch_start_visual(self, x: int, center_y: int, branch_y: int,
                                    rung_number: int, element, branch_stack: List[str]):
        """Create visual elements for branch start."""
        branch_start_id = self.create_oval(
            x - 5, center_y - 5, x + 5, center_y + 5,
            fill='green', outline='darkgreen', width=2,
            tags=f"rung_{rung_number}_branch_marker"
        )

        ladder_element = LadderElement(
            element_type='branch_start',
            x=x - 5, y=center_y - 5,
            width=10, height=10,
            canvas_id=branch_start_id,
            branch_level=len(branch_stack) + 1,
            branch_id=element.branch_id,
            position=element.position,
            rung_number=rung_number
        )
        self._elements.append(ladder_element)

        # Create branch structure
        branch = LadderBranch(
            start_x=x, end_x=-1,
            main_y=center_y, branch_y=branch_y,
            rung_number=rung_number,
            branch_id=element.branch_id,
            elements=[], start_position=element.position, end_position=-1
        )
        self._branches[element.branch_id] = branch
        branch_stack.append(element.branch_id)

        # Draw vertical line down to branch
        self.create_line(x, center_y, x, branch_y, width=2,
                         tags=f"rung_{rung_number}_branch")

    def _create_branch_end_visual(self, x: int, center_y: int, rung_number: int,
                                  element, branch_stack: List[str]):
        """Create visual elements for branch end."""
        if branch_stack and element.branch_id in branch_stack:
            branch_stack.remove(element.branch_id)

        if element.branch_id in self._branches:
            branch = self._branches[element.branch_id]
            branch.end_x = x
            branch.end_position = element.position

            # Create visual branch end marker
            branch_end_id = self.create_oval(
                x - 5, center_y - 5, x + 5, center_y + 5,
                fill='red', outline='darkred', width=2,
                tags=f"rung_{rung_number}_branch_marker"
            )

            ladder_element = LadderElement(
                element_type='branch_end',
                x=x - 5, y=center_y - 5,
                width=10, height=10,
                canvas_id=branch_end_id,
                branch_level=len(branch_stack),
                branch_id=element.branch_id,
                position=element.position
            )
            self._elements.append(ladder_element)

            # Draw branch connection lines
            self.create_line(x, branch.branch_y, x, center_y, width=2,
                             tags=f"rung_{rung_number}_branch")
            self.create_line(branch.start_x, branch.branch_y, x, branch.branch_y, width=2,
                             tags=f"rung_{rung_number}_branch")

    def _clear_hover_preview(self):
        """Clear the hover preview."""
        if self._hover_preview_id:
            self.delete("hover_preview")
            self._hover_preview_id = None
            self._last_hover_position = None

    def _copy_element(self, element: LadderElement):
        """Copy an element (placeholder)."""
        self._show_status(f"Copied element: {element.text}")

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

    def _delete_element(self, event, element: LadderElement):
        """Delete an element from the rung."""
        # Remove from rung meta data
        rung_number = int(element.instruction.rung.number)
        if rung_number is None or rung_number < 0:
            self.logger.debug(f"No rung found for element at Y={element.y}")
            return
        element.instruction.rung.remove_instruction(element.instruction)

        # Remove from canvas
        self.delete(element.canvas_id)

        # Remove from elements list
        if element in self._elements:
            self._elements.remove(element)

        # Remove from selection if selected
        if element in self._selected_elements:
            self._selected_elements.remove(element)

        self._show_status(f"Deleted element: {element.text}")
        self._redraw_rung(rung_number)

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

    def _draw_instruction_texts(self, instruction: plc.LogixInstruction,
                                x: int, y: int, rung_number: int, element_width: int):
        alias = False
        # Optionally add alias information above contact
        if instruction.operands[0].as_aliased != instruction.operands[0].meta_data:
            self.create_text(
                x + element_width // 2, y - 15,
                text=f'<{instruction.operands[0].as_aliased}>',
                fill="#2739FB",
                font=('Roboto', 8,),
                tags=f"rung_{rung_number}_instruction"
            )
            alias = True

        # Add operand text above the contact
        operand = instruction.operands[0].meta_data if instruction.operands else "???"
        _ = self.create_text(
            x + element_width // 2, y - (15 if alias is False else 25),
            text=operand, font=('Roboto', 8,), tags=f"rung_{rung_number}_instruction"
        )

        # return the operand text for further use
        return operand

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

        operand = self._draw_instruction_texts(instruction, x, top_y, rung_number, self.CONTACT_WIDTH)

        return LadderElement(
            element_type='contact',
            x=x, y=top_y,
            width=self.CONTACT_WIDTH, height=self.CONTACT_HEIGHT,
            canvas_id=rect_id,
            instruction=instruction,
            text=operand,
            rung_number=rung_number
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
                text='L', font=('Roboto', 12, 'bold'),
                tags=f"rung_{rung_number}_instruction"
            )
        elif inst_type == 'otu':  # Unlatch
            self.create_text(
                x + self.COIL_WIDTH // 2, center_y,
                text='U', font=('Roboto', 12, 'bold'),
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

        operand = self._draw_instruction_texts(instruction, x, top_y, rung_number, self.COIL_WIDTH)

        return LadderElement(
            element_type='coil',
            x=x, y=top_y,
            width=self.COIL_WIDTH, height=self.COIL_HEIGHT,
            canvas_id=circle_id,
            instruction=instruction,
            text=operand,
            rung_number=rung_number
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
            text=operands_text,
            rung_number=rung_number
        )

    def _draw_hover_preview(self, x: int, y: int, mode: LadderEditorMode):
        """Draw a hover preview indicator."""
        if mode == LadderEditorMode.INSERT_CONTACT:
            # Small rectangle preview for contact
            self._hover_preview_id = self.create_rectangle(
                x - self.CONTACT_WIDTH // 4,
                y - self.CONTACT_HEIGHT // 4,
                x + self.CONTACT_WIDTH // 4,
                y + self.CONTACT_HEIGHT // 4,
                outline='blue', fill='lightblue', stipple='gray50',
                width=2, tags="hover_preview"
            )
        elif mode == LadderEditorMode.INSERT_COIL:
            # Small circle preview for coil
            self._hover_preview_id = self.create_oval(
                x - self.COIL_WIDTH // 4,
                y - self.COIL_HEIGHT // 4,
                x + self.COIL_WIDTH // 4,
                y + self.COIL_HEIGHT // 4,
                outline='blue', fill='lightblue', stipple='gray50',
                width=2, tags="hover_preview"
            )
        elif mode == LadderEditorMode.INSERT_BLOCK:
            # Small rectangle preview for block
            self._hover_preview_id = self.create_rectangle(
                x - self.BLOCK_WIDTH // 4,
                y - self.BLOCK_HEIGHT // 4,
                x + self.BLOCK_WIDTH // 4,
                y + self.BLOCK_HEIGHT // 4,
                outline='blue', fill='lightblue', stipple='gray50',
                width=2, tags="hover_preview"
            )

        # Add insertion point dot
        if self._hover_preview_id:
            self.create_oval(
                x - 3, y - 3, x + 3, y + 3,
                fill='red', outline='darkred', width=1,
                tags="hover_preview"
            )

    def _draw_branch_hover_preview(self, x: int, y: int):
        """Draw a hover preview for branch creation."""
        # Draw branch start indicator
        self._hover_preview_id = self.create_oval(
            x - 5, y - 5, x + 5, y + 5,
            fill='lightgreen', outline='green', width=2,
            tags="hover_preview"
        )

        # Add preview branch line
        branch_y = y + self.BRANCH_SPACING
        self.create_line(
            x, y, x, branch_y,
            fill='green', width=2, dash=(3, 3),
            tags="hover_preview"
        )

        # Add preview horizontal branch line
        self.create_line(
            x, branch_y, x + 50, branch_y,
            fill='green', width=2, dash=(3, 3),
            tags="hover_preview"
        )

        # Add text
        self.create_text(
            x, y - 15,
            text="Branch Start", font=('Arial', 8),
            fill='green', tags="hover_preview"
        )

    def _draw_branch_connect_preview(self, x: int, y: int):
        """Draw a hover preview for branch connection."""
        # Draw branch end indicator
        self._hover_preview_id = self.create_oval(
            x - 5, y - 5, x + 5, y + 5,
            fill='lightcoral', outline='red', width=2,
            tags="hover_preview"
        )

        # Add preview branch line
        branch_y = y + self.BRANCH_SPACING
        self.create_line(
            x, y, x, branch_y,
            fill='red', width=2, dash=(3, 3),
            tags="hover_preview"
        )

        # Add preview horizontal branch line
        self.create_line(
            x, branch_y, x - 50, branch_y,
            fill='red', width=2, dash=(3, 3),
            tags="hover_preview"
        )

        # Add text
        self.create_text(
            x, y + 15,
            text="Branch End", font=('Arial', 8),
            fill='red', tags="hover_preview"
        )

    def _draw_branch_rail_connector(self, x, y, oval_fill='lightgreen',
                                    oval_outline='green', tags=None) -> LadderElement:
        """Draw the oval indicator for branch rail connector.
        Args:
            x: X position for the branch rail connector
            y: Y position for the branch rail connector
            oval_fill: Fill color for the oval indicator
            oval_outline: Outline color for the oval indicator
            tags: Additional tags for the canvas item
        Returns:
            The canvas ID of the created oval indicator.
        """
        id = self.create_oval(
            x - 5, y - 5, x + 5, y + 5,
            fill=oval_fill, outline=oval_outline, width=2, tags=tags
        )
        return LadderElement(
            element_type='branch_rail_connector',
            x=x - 5, y=y - 5,
            width=10, height=10,
            canvas_id=id,
            branch_level=0,
            branch_id=tags,  # Use tags as branch ID
            rung_number=self._get_rung_at_y(y)  # Get current rung number
        )

    def _draw_branch_rail_line(self, x: int, y: int, end_x: int, end_y: int,
                               fill: str = 'green', width: int = 2,
                               tags: str = None, dashed_line: bool = False):
        """Draw a line for the branch rail connector.
        Args:
            x: Start X position
            y: Start Y position
            end_x: End X position
            end_y: End Y position
            fill: Color of the line
            width: Width of the line
            tags: Additional tags for the canvas item
            dashed_line: Whether to use a dashed line
        """
        self.create_line(
            x, y, end_x, end_y,
            fill=fill, width=width,
            dash=(3, 3) if dashed_line else None,
            tags=tags
        )

    def _draw_branch_left_rail(self,
                               x: int,
                               y: int,
                               oval_fill: str = 'lightgreen',
                               oval_outline: str = 'green',
                               tags: str = None,
                               dashed_line: bool = False,
                               branch_text: str = None) -> LadderElement:
        """Draw the left rail branch start indicator and preview lines.
        Args:
            x: X position for the branch start
            y: Y position for the branch start
            oval_fill: Fill color for the oval indicator
            oval_outline: Outline color for the oval indicator
            tags: Additional tags for the canvas item
            dashed_line: Whether to use a dashed line for the preview
            branch_text: Optional text to display above the branch start
        Returns:
            LadderElement: The created branch rail connector element.
        """
        # Draw branch start indicator
        ladder_element = self._draw_branch_rail_connector(x, y, oval_fill, oval_outline, tags)

        # Add preview branch line
        branch_y = y + self.BRANCH_SPACING
        self._draw_branch_rail_line(x, y, x, branch_y,
                                    oval_outline, width=2,
                                    tags=tags, dashed_line=dashed_line)

        # Add preview horizontal branch line
        self._draw_branch_rail_line(
            x, branch_y, x + 50, branch_y,
            oval_outline, width=2,
            tags=tags, dashed_line=dashed_line
        )

        # Add text
        if branch_text:
            self.create_text(
                x, y - 15,
                text=branch_text, font=('Roboto', 8),
                fill=oval_outline, tags=tags
            )
        return ladder_element

    def _draw_branch_right_rail(self,
                                x: int,
                                y: int,
                                oval_fill: str = 'lightcoral',
                                oval_outline: str = 'red',
                                tags: str = None,
                                dashed_line: bool = False,
                                branch_text: str = None) -> LadderElement:
        """Draw the right rail branch end indicator and preview lines.
        Args:
            x: X position for the branch end
            y: Y position for the branch end
            oval_fill: Fill color for the oval indicator
            oval_outline: Outline color for the oval indicator
            tags: Additional tags for the canvas item
            dashed_line: Whether to use a dashed line for the preview
            branch_text: Optional text to display below the branch end
        Returns:
            LadderElement: The created branch rail connector element.
        """
        # Draw branch end indicator
        ladder_element = self._draw_branch_rail_connector(x, y, oval_fill, oval_outline, tags)

        # Add preview branch line
        branch_y = y + self.BRANCH_SPACING
        self._draw_branch_rail_line(x, y, x, branch_y,
                                    oval_outline, width=2,
                                    tags=tags, dashed_line=dashed_line)

        # Add preview horizontal branch line
        self._draw_branch_rail_line(
            x, branch_y, x - 50, branch_y,
            oval_outline, width=2,
            tags=tags, dashed_line=dashed_line
        )

        # Add text
        if branch_text:
            self.create_text(
                x, y + 15,
                text=branch_text, font=('Roboto', 8),
                fill=oval_outline, tags=tags
            )

        return ladder_element

    def _draw_routine(self):
        """Draw the entire routine on the canvas."""
        self.clear_canvas()

        if not self._routine:
            self._show_status("No routine loaded")
            return

        if not self._routine.rungs:
            self._routine.add_rung(plc.Rung(controller=self._routine.controller, routine=self._routine))

        y_pos = 50
        for i, rung in enumerate(self._routine.rungs):
            self._draw_rung(rung, i, y_pos)
            y_pos += self.RUNG_HEIGHT + (self.BRANCH_SPACING * rung.get_max_branch_depth()) + 20

        # Update scroll region
        self.configure(scrollregion=self.bbox("all"))

    def _draw_rung(self, rung: plc.Rung, rung_number: int, y_pos: int):
        """Draw a single rung using the enhanced PLC data structure."""
        self._rung_y_positions[rung_number] = y_pos

        # Draw rung number
        self.create_text(10, y_pos + self.RUNG_HEIGHT // 2,
                         text=str(rung_number), anchor='w', font=('Arial', 10))

        # Draw power rails
        self.create_line(self.RAIL_X_LEFT, y_pos, self.RAIL_X_LEFT, y_pos + self.RUNG_HEIGHT,
                         width=3, tags=f"rung_{rung_number}")

        right_rail_x = self.winfo_reqwidth() - 40 if self.winfo_reqwidth() > 100 else 600
        self.create_line(right_rail_x, y_pos, right_rail_x, y_pos + self.RUNG_HEIGHT,
                         width=3, tags=f"rung_{rung_number}")

        center_y = y_pos + self.RUNG_HEIGHT // 2

        start_pos_x = self.RAIL_X_LEFT + self.ELEMENT_SPACING + 30  # Start after left rail

        if rung and hasattr(rung, 'rung_sequence') and rung.rung_sequence:
            # Use the enhanced rung sequence from PLC model
            self._draw_rung_sequence_new(rung, rung_number, y_pos, start_pos_x)
        elif rung and hasattr(rung, 'instructions') and rung.instructions:
            # Fallback to basic instruction drawing
            self._draw_rung_instructions(rung.instructions, rung_number, y_pos, start_pos_x)
        else:
            # Draw empty rung line
            self.create_line(self.RAIL_X_LEFT, center_y, right_rail_x, center_y,
                             width=2, tags=f"rung_{rung_number}")

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

    def _draw_rung_rail_section(self, x: int, y: int, end_x: int, end_y: int,
                                tags: str = ""):
        """Draw a section of the power rail."""
        self.create_line(x, y, end_x, end_y,
                         width=3, fill='black', tags=tags)

    def _draw_rung_sequence(self, rung: plc.Rung, rung_number: int, y_pos: int, start_x: int):
        """Draw rung using the enhanced sequence structure with proper spacing."""
        current_x = start_x
        center_y = y_pos + self.RUNG_HEIGHT // 2
        branch_stack = []
        element_positions = {}
        branch_depth_map = {}  # Track actual depth for each branch

        # First pass: calculate positions for all elements
        temp_x = start_x
        for i, element in enumerate(rung.rung_sequence):
            if element.element_type == plc.RungElementType.INSTRUCTION:
                nesting_level = rung.get_branch_nesting_level(element.position)
                pos_x = temp_x  # store the original x position before we modify this value to determine width

                # Determine width based on instruction type
                inst_type = element.instruction.instruction_name.lower()
                if inst_type in ['xic', 'xio']:
                    width = self.CONTACT_WIDTH
                    temp_x += self.CONTACT_WIDTH + self.ELEMENT_SPACING + self.MIN_WIRE_LENGTH
                elif inst_type in ['ote', 'otl', 'otu']:
                    width = self.COIL_WIDTH
                    temp_x += self.COIL_WIDTH + self.ELEMENT_SPACING + self.MIN_WIRE_LENGTH
                else:
                    width = self.BLOCK_WIDTH
                    temp_x += self.BLOCK_WIDTH + self.ELEMENT_SPACING + self.MIN_WIRE_LENGTH
                element_positions[i] = (pos_x, nesting_level, width)

            elif element.element_type == plc.RungElementType.BRANCH_START:
                # Use PLC model to determine proper branch depth
                branch_depth = rung.get_branch_nesting_level(element.position)
                branch_depth_map[element.branch_id] = branch_depth

        # Second pass: draw elements at calculated positions
        prev_x = self.RAIL_X_LEFT
        for i, element in enumerate(rung.rung_sequence):
            if element.element_type == plc.RungElementType.INSTRUCTION:
                current_x = element_positions[i][0]
                center_y = y_pos + self.RUNG_HEIGHT // 2 + \
                    element_positions[i][1] * self.BRANCH_SPACING

                # Draw the power rail
                if i == 0 or current_x != prev_x:
                    self._draw_rung_rail_section(
                        prev_x, center_y, current_x, center_y,
                        tags=f"rung_{rung_number}_wire"
                    )
                    prev_x = current_x + element_positions[i][2]  # Update prev_x to current element's end

                # Draw the instruction
                ladder_element = self._draw_instruction(element.instruction, current_x, center_y, rung_number)
                if ladder_element:
                    ladder_element.position = element.position
                    ladder_element.branch_level = len(branch_stack)
                    if branch_stack:
                        ladder_element.branch_id = branch_stack[-1]
                    self._elements.append(ladder_element)

            elif element.element_type == plc.RungElementType.BRANCH_START:
                # Handle branch start with proper positioning
                actual_depth = branch_depth_map.get(element.branch_id, 1)
                branch_y = center_y + actual_depth * self.BRANCH_SPACING

                # Use the calculated position
                if i in element_positions:
                    current_x = element_positions[i]

                # Create branch structure and visuals
                self._draw_branch_left_rail(
                    current_x, branch_y,
                    oval_fill='lightgreen', oval_outline='green',
                    tags=f"rung_{rung_number}_branch_start"
                )

            elif element.element_type == plc.RungElementType.BRANCH_END:
                # Handle branch end
                if i in element_positions:
                    current_x = element_positions[i]

                self._draw_branch_right_rail(
                    current_x, center_y + (len(branch_stack) * self.BRANCH_SPACING),
                    oval_fill='lightcoral', oval_outline='red',
                    tags=f"rung_{rung_number}_branch_end"
                )
                # self._create_branch_end_visual(current_x, center_y, rung_number,
                #                                element, branch_stack)

        # Draw final power rail section if needed
        if prev_x < self.winfo_reqwidth() - 40:  # Right rail
            self._draw_rung_rail_section(
                prev_x, center_y,
                self.winfo_reqwidth() - 40, center_y,
                tags=f"rung_{rung_number}_wire"
            )

    def _draw_rung_sequence_new(self, rung: plc.Rung, rung_number: int, y_pos: int, start_x: int):
        """Draw rung using the new sequence structure with proper spacing."""
        current_x = start_x
        center_y = y_pos + self.RUNG_HEIGHT // 2
        branch_stack = []
        ladder_element: Optional[LadderElement] = None

        for index, element in enumerate(rung.rung_sequence):
            if element.element_type == plc.RungElementType.INSTRUCTION:
                ladder_element = self._draw_instruction(element.instruction, current_x, center_y, rung_number)
                if ladder_element:
                    ladder_element.position = element.position
                    ladder_element.branch_level = len(branch_stack)
                    if branch_stack:
                        ladder_element.branch_id = branch_stack[-1]
                    self._elements.append(ladder_element)

                # Update current_x based on instruction width
                current_x += ladder_element.width + self.ELEMENT_SPACING + self.MIN_WIRE_LENGTH

            elif element.element_type == plc.RungElementType.BRANCH_START:
                # Handle branch start
                branch_id = element.branch_id

                if ladder_element:
                    branch_x, branch_y = self._get_branch_x_y_spacing_from_element(ladder_element,
                                                                                   rung_number=rung_number,
                                                                                   side='right')
                else:
                    branch_x, branch_y = current_x, self._rung_y_positions[rung_number] + (self.RUNG_HEIGHT // 2)

                # Draw branch start visual
                left_branch_element = self._draw_branch_left_rail(
                    branch_x, branch_y,
                    oval_fill='lightgreen', oval_outline='green',
                    tags=f"rung_{rung_number}_branch_start"
                )
                if left_branch_element:
                    left_branch_element.position = element.position
                    left_branch_element.branch_id = branch_id
                    left_branch_element.branch_level = len(branch_stack)
                    left_branch_element.rung_number = rung_number
                self._elements.append(left_branch_element)
                # branch_stack.append(branch_id)  # we need better tracking for branches first
                current_x += (self.ELEMENT_SPACING)

            elif element.element_type == plc.RungElementType.BRANCH_NEXT:
                # Handle branch next (continue branch)
                raise NotImplementedError("Branch next handling is not implemented yet.")
                # if branch_stack:
                #     branch_id = branch_stack[-1]
                #     branch_depth = rung.get_branch_nesting_level(branch_id)
                #     branch_x, branch_y = self._get_branch_x_y_spacing_from_element(ladder_element,
                #                                                                    rung_number=rung_number,
                #                                                                    side='right',
                #                                                                    depth=branch_depth)
                # else:
                #     raise ValueError("No active branch found for branch next.")

                # # Draw branch next visual
                # left_branch_element = self._draw_branch_left_rail(
                #     branch_x, branch_y,
                #     oval_fill='lightgreen', oval_outline='green',
                #     tags=f"rung_{rung_number}_branch_next"
                # )
                # self._elements.append(left_branch_element)
                # current_x += (self.ELEMENT_SPACING)

            elif element.element_type == plc.RungElementType.BRANCH_END:
                # Handle branch end
                if branch_stack:
                    branch_stack.pop()

                if ladder_element:
                    branch_x, branch_y = self._get_branch_x_y_spacing_from_element(ladder_element,
                                                                                   rung_number=rung_number,
                                                                                   side='right')
                else:
                    raise ValueError("No ladder element found for branch end.")

                # Draw branch end visual
                right_branch_element = self._draw_branch_right_rail(
                    branch_x, branch_y,
                    oval_fill='lightcoral', oval_outline='red',
                    tags=f"rung_{rung_number}_branch_end"
                )
                if right_branch_element:
                    right_branch_element.position = element.position
                    right_branch_element.branch_id = branch_stack[-1] if branch_stack else None
                    right_branch_element.branch_level = len(branch_stack)
                    right_branch_element.rung_number = rung_number
                self._elements.append(right_branch_element)
                current_x += (self.ELEMENT_SPACING)

        # Draw final power rail section if needed
        right_rail_x = self.winfo_reqwidth() - 40 if self.winfo_reqwidth() > 100 else 600
        if current_x < right_rail_x:
            self._draw_rung_rail_section(
                current_x, center_y,
                right_rail_x, center_y,
                tags=f"rung_{rung_number}_wire"
            )

    def _edit_instruction(self, instruction: plc.LogixInstruction):
        """Edit an instruction (placeholder - implement instruction editor dialog)."""
        self._show_status(f"Edit instruction: {instruction.meta_data}")

    def _find_insertion_position(self, x: int, rung_number: int, branch_level: int = 0,
                                 branch_id: Optional[str] = None) -> int:
        """Find the correct position to insert a new element in the rung sequence."""
        rung_elements = self._get_rung_elements(rung_number, branch_level, branch_id)

        if not rung_elements:
            return 0

        # Find the element closest to the click position
        closest_element = None
        min_distance = float('inf')

        for element in rung_elements:
            element_center_x = element.x + element.width // 2
            distance = abs(element_center_x - x)

            if distance < min_distance:
                min_distance = distance
                closest_element = element

        if closest_element is None:
            return len(rung_elements)

        # Determine if we should insert before or after the closest element
        element_center_x = closest_element.x + closest_element.width // 2

        if x < element_center_x:
            # Insert before this element
            return closest_element.position
        else:
            # Insert after this element
            return closest_element.position + 1

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

    def _get_element_at(self, x: int, y: int) -> Optional[LadderElement]:
        """Get element at given coordinates."""
        for element in self._elements:
            if (element.x <= x <= element.x + element.width and
                    element.y <= y <= element.y + element.height):
                return element
        return None

    def _get_rung_elements(self, rung_number: int, branch_level: int = 0,
                           branch_id: Optional[str] = None) -> List[LadderElement]:
        """Get all elements for a specific rung and branch level."""
        elements = []

        for element in self._elements:
            if (element.rung_number == rung_number and
                element.branch_level == branch_level and
                    element.element_type in ['contact', 'coil', 'block', 'branch_rail_connector']
                    and (branch_id is None or element.branch_id == branch_id)):
                elements.append(element)

        # Sort by position
        elements.sort(key=lambda e: e.position)
        return elements

    def _get_branch_id_at_position(self, x: int, y: int, rung_number: int,
                                   branch_level: int) -> Optional[str]:
        """Get the branch ID for elements at a specific position."""
        if branch_level == 0:
            return None

        # Find which branch this position belongs to
        for branch_id, branch in self._branches.items():
            if (branch.rung_number == rung_number and
                    branch.start_x <= x <= branch.end_x):
                return branch_id

        return None

    def _get_branch_x_y_spacing_from_element(self,
                                             element: LadderElement,
                                             rung_number: int,
                                             side: Literal['left', 'right'] = 'left') -> tuple[int, int]:
        """Get the branch spacing based on the element's position.
        Args:
            element: The LadderElement to base the spacing on.
            rung_number: The rung number to which the element belongs.
            side: 'left' or 'right' to determine which side to calculate from.
        Returns:
            A tuple containing the X and Y coordinates for the branch spacing.
        Raises:
            ValueError: If side is not 'left' or 'right', or element is None.
        """
        if side not in ['left', 'right']:
            raise ValueError("side must be 'left' or 'right'")
        if element is None:
            raise ValueError("element cannot be None")
        y = self._rung_y_positions[rung_number] + self.RUNG_HEIGHT // 2
        if side == 'left':
            return (element.x - (self.ELEMENT_SPACING // 2), y)
        elif side == 'right':
            return (element.x + element.width + (self.ELEMENT_SPACING // 2) + self.MIN_WIRE_LENGTH, y)

    def _get_rung_at_y(self, y: int) -> Optional[int]:
        """Get rung number at given Y coordinate."""
        for rung_num, rung_y in self._rung_y_positions.items():
            if rung_y <= y <= rung_y + self.RUNG_HEIGHT:
                return rung_num
        return None

    def _highlight_current_rung(self, rung_number: int):
        """highlight the current rung by changing the background color of the left bar area.
        """
        if rung_number is None or rung_number not in self._rung_y_positions:
            return

        # Clear previous highlights
        self.delete("current_rung_highlight")

        # Highlight the current rung
        y_pos = self._rung_y_positions[rung_number]
        self.create_rectangle(
            0, y_pos, 30, y_pos + self.RUNG_HEIGHT,
            fill='yellow', stipple='gray50', tags="current_rung_highlight"
        )

    def _insert_element_at(self, x: int, y: int):
        """Insert new element at given coordinates, handling branches and spacing."""
        rung_number = self._get_rung_at_y(y)
        if rung_number is None:
            return

        # Validate insertion position
        if not self._validate_insertion_position(x, y, rung_number):
            self._show_status("Invalid insertion position")
            return

        # Determine if we're inserting on a branch
        branch_level = self._get_branch_level_at_y(y, rung_number)
        branch_id = self._get_branch_id_at_position(x, y, rung_number, branch_level)

        # Find insertion position in the rung sequence
        insertion_position = self._find_insertion_position(x, rung_number, branch_level, branch_id)

        # Create new instruction based on mode
        if self._mode == LadderEditorMode.INSERT_CONTACT:
            instruction = self._create_contact_instruction(rung_number)
        elif self._mode == LadderEditorMode.INSERT_COIL:
            instruction = self._create_coil_instruction(rung_number)
        elif self._mode == LadderEditorMode.INSERT_BLOCK:
            instruction = self._create_block_instruction(rung_number)
        else:
            return

        # Insert the instruction into the rung structure
        self._insert_instruction_at_position(instruction, rung_number, insertion_position,
                                             branch_level, branch_id)

        # Redraw the entire rung to reflect the new layout
        self._redraw_rung(rung_number)

        self._show_status(f"Inserted {instruction.instruction_name} at position {insertion_position}")

    def _insert_instruction_at_position(self, instruction: plc.LogixInstruction,
                                        rung_number: int, position: int,
                                        branch_level: int = 0,
                                        branch_id: Optional[str] = None):
        """Insert instruction into the rung structure at the specified position."""
        if not self._routine or rung_number >= len(self._routine.rungs):
            return

        rung: plc.Rung = self._routine.rungs[rung_number]
        rung.add_instruction(instruction.meta_data, position=position)

        # # Update positions of existing elements that come after insertion point
        # self._shift_element_positions(rung_number, position, branch_level, branch_id)

        # # Add instruction to rung text/sequence
        # self._update_rung_text_with_insertion(rung, instruction, position, branch_level, branch_id)

    def _on_click(self, event):
        """Handle mouse click events."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)

        # Clear hover preview on click
        self._clear_hover_preview()

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

    def _on_double_click(self, event):
        """Handle double-click to edit element."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        element = self._get_element_at(x, y)

        if element and element.instruction:
            self._edit_instruction(element.instruction)

    def _on_drag(self, event):
        """Handle mouse drag for moving elements."""
        pass

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_motion(self, event):
        """Handle mouse motion for hover effects."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        self._current_rung = self._get_rung_at_y(y)
        if self._current_rung is not None:
            self._highlight_current_rung(self._current_rung)

            # Only show hover preview in insert modes
        if self._mode in [LadderEditorMode.INSERT_CONTACT,
                          LadderEditorMode.INSERT_COIL,
                          LadderEditorMode.INSERT_BLOCK]:
            self._update_hover_preview(x, y)
        elif self._mode == LadderEditorMode.INSERT_BRANCH:
            self._update_branch_hover_preview(x, y)
        elif self._mode == LadderEditorMode.CONNECT_BRANCH:
            self._update_branch_connect_preview(x, y)
        else:
            self._clear_hover_preview()

    def _on_mouse_leave(self, event):
        """Handle mouse leaving the canvas."""
        self._clear_hover_preview()

    def _on_right_click(self, event):
        """Handle right-click context menu."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        element = self._get_element_at(x, y)

        if element:
            self._show_context_menu(event, element)

    def _paste_element(self):
        """Paste an element (placeholder)."""
        self._show_status("Paste functionality not implemented")

    def _redraw_rung(self, rung_number: int):
        """Redraw a specific rung with proper spacing."""
        if not self._routine or rung_number >= len(self._routine.rungs):
            return

        # Remove existing visual elements for this rung
        self._clear_rung_visuals(rung_number)

        # Get rung position
        y_pos = self._rung_y_positions.get(rung_number, 50)

        # Redraw the rung
        rung = self._routine.rungs[rung_number]
        self._draw_rung(rung, rung_number, y_pos)

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

    def _shift_element_positions(self, rung_number: int, insertion_position: int,
                                 branch_level: int = 0, branch_id: Optional[str] = None):
        """Shift the positions of elements that come after the insertion point."""
        for element in self._elements:
            if (self._get_rung_at_y(element.y + element.height // 2) == rung_number and
                element.branch_level == branch_level and
                    element.position >= insertion_position):

                # Check if we're in the same branch context
                if branch_level > 0 and branch_id is not None:
                    if element.branch_id == branch_id:
                        element.position += 1
                elif branch_level == 0 and not element.branch_id:
                    element.position += 1

    def _show_context_menu(self, event, element: LadderElement):
        """Show context menu for element."""
        menu = tk.Menu(self, tearoff=0)

        if element.element_type in ['contact', 'coil', 'block']:
            menu.add_command(label="Edit", command=lambda: self._edit_instruction(element.instruction))
            menu.add_command(label="Delete", command=lambda: self._delete_element(event, element))
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

    def _show_status(self, message: str):
        """Show status message (to be connected to status bar)."""
        self.logger.info(message)

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
            nearest_element.x - (self.ELEMENT_SPACING // 2) - 5,
            center_y - 5,
            nearest_element.x - (self.ELEMENT_SPACING // 2) + 5,
            center_y + 5,
            fill='green', outline='darkgreen', width=2,
            tags=f"rung_{rung_number}_branch_marker"
        )

        branch_element = LadderElement(
            element_type='branch_start',
            x=nearest_element.x - (self.ELEMENT_SPACING // 2),
            y=center_y - 5,
            width=10, height=10,
            canvas_id=branch_start_id,
            branch_level=1,
            branch_id=branch_id,
            position=nearest_element.position,
            rung_number=rung_number,
        )

        self._elements.append(branch_element)
        self._pending_branch_start = branch_element

        # Switch to connect mode
        self.mode = LadderEditorMode.CONNECT_BRANCH
        self._show_status("Click where you want the branch to reconnect")

    def _update_hover_preview(self, x: int, y: int):
        """Update the hover preview for element insertion."""
        # Get the rung at this position
        rung_number = self._get_rung_at_y(y)

        # Clear existing preview if we're not over a valid rung
        if rung_number is None:
            self._clear_hover_preview()
            return

        # Validate insertion position
        if not self._validate_insertion_position(x, y, rung_number):
            self._clear_hover_preview()
            return

        # Determine insertion details
        branch_level = self._get_branch_level_at_y(y, rung_number)
        branch_id = self._get_branch_id_at_position(x, y, rung_number, branch_level)
        if not branch_id:
            branch_level = 0
        insertion_position = self._find_insertion_position(x, rung_number, branch_level, branch_id)

        # Calculate the exact insertion point
        insertion_x, insertion_y = self._calculate_insertion_coordinates(
            x, y, rung_number, insertion_position, branch_level, branch_id
        )

        current_position = (insertion_x, insertion_y, self._mode)

        # Only update if position has changed
        if current_position != self._last_hover_position:
            self._clear_hover_preview()
            self._draw_hover_preview(insertion_x, insertion_y, self._mode)
            self._last_hover_position = current_position

    def _update_branch_hover_preview(self, x: int, y: int):
        """Update the hover preview for branch creation."""
        rung_number = self._get_rung_at_y(y)

        if rung_number is None:
            self._clear_hover_preview()
            return

        # Find nearest element for branch start
        nearest_element = self._find_nearest_element_on_rung(x, y, rung_number)
        if not nearest_element:
            self._clear_hover_preview()
            return

        # Calculate branch start position
        branch_x, branch_y = self._get_branch_x_y_spacing_from_element(nearest_element, rung_number, side='left')
        current_position = (branch_x, branch_y, LadderEditorMode.INSERT_BRANCH)

        if current_position != self._last_hover_position:
            self._clear_hover_preview()
            self._hover_preview_id = self._draw_branch_left_rail(branch_x, branch_y, tags="hover_preview",
                                                                 dashed_line=True, branch_text="Branch Start")
            self._last_hover_position = current_position

    def _update_branch_connect_preview(self, x: int, y: int):
        """Update the hover preview for branch connection."""
        if not self._pending_branch_start:
            return

        # Get the pending branch start element
        branch_start = self._pending_branch_start
        rung_number = branch_start.rung_number

        if rung_number is None:
            self._clear_hover_preview()
            return

        # Find nearest element for branch start
        nearest_element = self._find_nearest_element_on_rung(x, y, rung_number)
        if not nearest_element:
            self._clear_hover_preview()
            return

        # Calculate branch end position
        branch_x = nearest_element.x + nearest_element.width + (self.ELEMENT_SPACING // 2)
        rung_y_pos = self._rung_y_positions[rung_number]
        branch_y = rung_y_pos + self.RUNG_HEIGHT // 2

        current_position = (branch_x, branch_y, LadderEditorMode.CONNECT_BRANCH)

        if current_position != self._last_hover_position:
            self._clear_hover_preview()
            self._hover_preview_id = self._draw_branch_right_rail(
                branch_x, branch_y, tags="hover_preview",
                dashed_line=True, branch_text="Branch End"
            )
            self._last_hover_position = current_position

    def _update_rung_structure_with_branch(self, rung_number: int, branch: LadderBranch):
        """Update the underlying PLC rung structure to include the new branch."""
        if not self._routine or rung_number >= len(self._routine.rungs):
            return

        rung = self._routine.rungs[rung_number]
        rung.insert_branch(branch.start_position, branch.end_position)
        self.logger.debug(f"Updated rung {rung_number} with branch structure.")

    def _update_rung_text_with_deletion(self, rung: plc.Rung, instruction: plc.LogixInstruction,
                                        position: int, branch_level: int = 0,
                                        branch_id: Optional[str] = None):
        """Update the rung text to remove the instruction at the specified position."""
        current_text = rung.text if rung.text else ""

        if not current_text:
            return

        # Parse existing instructions
        instructions = re.findall(plc.INST_RE_PATTERN, current_text)

        if position < 0 or position >= len(instructions):
            self.logger.warning(f"Invalid position {position} for deletion in rung {rung.number}")
            return

        # Remove the instruction at the specified position
        del instructions[position]

        # Reconstruct the rung text
        if instructions:
            rung.text = " ".join(instructions)
        else:
            rung.text = ""

        self.logger.info(f"Updated rung {rung.number} after deletion: {rung.text}")

    def _update_rung_text_with_insertion(self, rung: plc.Rung, instruction: plc.LogixInstruction,
                                         position: int, branch_level: int = 0,
                                         branch_id: Optional[str] = None):
        """Update the rung text to include the new instruction at the correct position."""
        current_text = rung.text if rung.text else ""

        if not current_text:
            rung.text = instruction.meta_data
            return

        # Parse existing instructions
        instructions = re.findall(plc.INST_RE_PATTERN, current_text)

        if branch_level == 0:
            # Main rung insertion
            if position >= len(instructions):
                rung.text = f"{current_text} {instruction.meta_data}"
            else:
                # Insert at specific position
                instructions.insert(position, instruction.meta_data)
                rung.text = " ".join(instructions)
        else:
            # Branch insertion - more complex logic needed
            # This is a simplified approach for branch text manipulation
            rung.text = f"{current_text} {instruction.meta_data}"

    def _validate_insertion_position(self, x: int, y: int, rung_number: int) -> bool:
        """Validate that the insertion position is appropriate."""
        # Check if we're within the rung boundaries
        if rung_number not in self._rung_y_positions:
            return False

        rung_y = self._rung_y_positions[rung_number]
        if not (rung_y <= y <= rung_y + self.RUNG_HEIGHT + self.BRANCH_SPACING * 3):
            return False

        # Check if we're not too close to power rails
        rail_x = 40
        right_rail_x = self.winfo_reqwidth() - 40 if self.winfo_reqwidth() > 100 else 600

        if x < rail_x + 20 or x > right_rail_x - 60:  # Leave more space on right for coils
            return False

        return True

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

    def clear_canvas(self):
        """Clear all elements from the canvas."""
        self.delete("all")
        self._elements.clear()
        self._selected_elements.clear()
        self._rung_y_positions.clear()
        self._branches.clear()
        self._pending_branch_start = None
        self._clear_hover_preview()

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

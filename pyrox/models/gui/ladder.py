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


THEME: dict = {
    "font": "Roboto",
    "background": "#333333",
    "comment_background": "#444444",
    "comment_foreground": "#09C83F",
    "foreground": "#f00bd5",
    "highlight_color": "#4A90E2",
    "button_color": "#4A90E2",
    "button_hover_color": "#357ABD",
    "button_text_color": "#ffffff",
    "ladder_rung_color": "#EF1010",
}


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
    element_type: str  # 'contact', 'coil', 'block', 'wire', 'branch_start', 'branch_end', 'rung'
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
    parent_branch_id: Optional[str] = None
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
    root_branch_id: Optional[str] = None
    branch_level: int = 0
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
    RUNG_START_Y = 50  # Starting Y position for the first rung

    def __init__(self, master, routine: Optional[plc.Routine] = None, **kwargs):
        Canvas.__init__(self,
                        master,
                        bg=THEME["background"])
        Loggable.__init__(self)

        self._routine = routine
        self._elements: List[LadderElement] = []
        self._selected_elements: List[LadderElement] = []
        self._mode = LadderEditorMode.VIEW
        self._current_rung = 0
        self._current_ladder_element: Optional[LadderElement] = None
        self._rung_y_positions: Dict[int, int] = {}
        self._branches: Dict[str, LadderBranch] = {}
        self._pending_branch_start: Optional[LadderElement] = None
        self._branch_counter = 0

        # Add debug mode support
        self._debug_mode = False
        self._debug_overlays = []

        # Add tooltip support
        self._tooltip = None
        self._tooltip_delay = 1000  # 1 second delay
        self._tooltip_id = None
        self._tooltip_element = None

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

    def _add_debug_element_tooltip_content(self, frame: tk.Frame, element: LadderElement):
        """Add debug tooltip content for non-instruction elements."""

        # Element type header
        type_colors = {
            'rung': '#4A90E2',
            'branch_rail_connector': '#7ED321',
            'branch_start': '#50E3C2',
            'branch_end': '#F5A623',
            'branch_next': '#BD10E0',
            'wire': '#9013FE'
        }

        color = type_colors.get(element.element_type, '#666666')

        header_label = tk.Label(
            frame,
            text=f"{element.element_type.replace('_', ' ').title()}",
            background="#fffacd",
            font=("Arial", 10, "bold"),
            foreground=color
        )
        header_label.pack(anchor="w")

        # Element-specific information
        if element.element_type == 'rung':
            self._add_rung_debug_info(frame, element)
        elif element.element_type in ['branch_rail_connector', 'branch_start', 'branch_end', 'branch_next']:
            self._add_branch_debug_info(frame, element)
        elif element.element_type == 'wire':
            self._add_wire_debug_info(frame, element)

        # Always add general debug info for debug mode
        self._add_debug_tooltip_section(frame, element)

    def _add_debug_overlay_for_element(self, element: LadderElement):
        """Add debug visual overlay for a single element."""
        # Coordinate text
        coord_text_id = self.create_text(
            element.x + element.width + 5,
            element.y - 5,
            text=f"({element.x},{element.y})",
            font=("Arial", 6),
            fill="red",
            anchor="nw",
            tags="debug_overlay"
        )
        self._debug_overlays.append(coord_text_id)

        # Position text
        pos_text_id = self.create_text(
            element.x,
            element.y + element.height + 5,
            text=f"Pos:{element.position}",
            font=("Arial", 6),
            fill="blue",
            anchor="nw",
            tags="debug_overlay"
        )
        self._debug_overlays.append(pos_text_id)

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

    def _add_instruction_tooltip_content(self, frame: tk.Frame, element: LadderElement):
        """Add instruction-specific tooltip content."""
        instruction = element.instruction

        # Instruction header
        header_label = tk.Label(
            frame,
            text=f"{instruction.instruction_name}",
            background="#fffacd",
            font=("Arial", 10, "bold"),
            foreground="#000080"
        )
        header_label.pack(anchor="w")

        # Operand information
        if instruction.operands:
            operand = instruction.operands[0]

            # Main operand
            operand_label = tk.Label(
                frame,
                text=f"Tag: {operand.meta_data}",
                background="#fffacd",
                font=("Arial", 9)
            )
            operand_label.pack(anchor="w")

            # Alias if different
            if operand.as_aliased != operand.meta_data:
                alias_label = tk.Label(
                    frame,
                    text=f"Alias: {operand.as_aliased}",
                    background="#fffacd",
                    font=("Arial", 9),
                    foreground="#2739FB"
                )
                alias_label.pack(anchor="w")

        # Element position info
        if hasattr(element, 'position'):
            position_label = tk.Label(
                frame,
                text=f"Position: {element.position}",
                background="#fffacd",
                font=("Arial", 8),
                foreground="gray"
            )
            position_label.pack(anchor="w")

        # Branch info if applicable
        if element.branch_level > 0:
            branch_label = tk.Label(
                frame,
                text=f"Branch: {element.branch_id} (Level {element.branch_level})",
                background="#fffacd",
                font=("Arial", 8),
                foreground="gray"
            )
            branch_label.pack(anchor="w")

        # Add debug information if enabled
        if self._debug_mode:
            self._add_debug_tooltip_section(frame, element)

    def _add_branch_at_element(self, element: LadderElement):
        """Add a branch starting at the specified element."""
        self._pending_branch_start = element
        self.mode = LadderEditorMode.CONNECT_BRANCH
        self._show_status("Click where you want the branch to reconnect")

    def _add_branch_debug_info(self, frame: tk.Frame, element: LadderElement):
        """Add branch-specific debug information."""

        # Branch ID
        if element.branch_id:
            tk.Label(
                frame,
                text=f"Branch ID: {element.branch_id}",
                background="#fffacd",
                font=("Arial", 9),
                foreground="black"
            ).pack(anchor="w")

        # Branch level
        tk.Label(
            frame,
            text=f"Branch Level: {element.branch_level}",
            background="#fffacd",
            font=("Arial", 8),
            foreground="gray"
        ).pack(anchor="w")

        # Parent branch
        if element.parent_branch_id:
            tk.Label(
                frame,
                text=f"Parent Branch: {element.parent_branch_id}",
                background="#fffacd",
                font=("Arial", 8),
                foreground="gray"
            ).pack(anchor="w")

        # Position in sequence
        tk.Label(
            frame,
            text=f"Sequence Position: {element.position}",
            background="#fffacd",
            font=("Arial", 8),
            foreground="gray"
        ).pack(anchor="w")

        # Branch structure info
        if element.branch_id and element.branch_id in self._branches:
            branch = self._branches[element.branch_id]

            tk.Label(
                frame,
                text=f"Start Position: {branch.start_position}",
                background="#fffacd",
                font=("Arial", 8),
                foreground="gray"
            ).pack(anchor="w")

            tk.Label(
                frame,
                text=f"End Position: {branch.end_position}",
                background="#fffacd",
                font=("Arial", 8),
                foreground="gray"
            ).pack(anchor="w")

            tk.Label(
                frame,
                text=f"Elements in Branch: {len(branch.elements)}",
                background="#fffacd",
                font=("Arial", 8),
                foreground="gray"
            ).pack(anchor="w")

    def _add_debug_overlay_for_any_element(self, element: LadderElement):
        """Add debug visual overlay for any element type."""

        # Color coding for different element types
        overlay_colors = {
            'contact': 'blue',
            'coil': 'green',
            'block': 'purple',
            'rung': 'orange',
            'branch_rail_connector': 'cyan',
            'branch_start': 'lime',
            'branch_end': 'red',
            'branch_next': 'magenta',
            'wire': 'gray'
        }

        color = overlay_colors.get(element.element_type, 'black')

        # Element bounds rectangle with type-specific color
        bounds_id = self.create_rectangle(
            element.x, element.y,
            element.x + element.width, element.y + element.height,
            outline=color,
            width=1,
            dash=(2, 2),
            tags="debug_overlay"
        )
        self._debug_overlays.append(bounds_id)

        # Only show detailed debug info for instruction elements to avoid clutter
        if element.element_type in ['contact', 'coil', 'block']:
            # Coordinate text
            coord_text_id = self.create_text(
                element.x + element.width + 5,
                element.y - 5,
                text=f"({element.x},{element.y})",
                font=("Arial", 6),
                fill=color,
                anchor="nw",
                tags="debug_overlay"
            )
            self._debug_overlays.append(coord_text_id)

            # Position text
            pos_text_id = self.create_text(
                element.x,
                element.y + element.height + 5,
                text=f"Pos:{element.position}",
                font=("Arial", 6),
                fill=color,
                anchor="nw",
                tags="debug_overlay"
            )
            self._debug_overlays.append(pos_text_id)

        # For branch elements, show branch ID
        elif element.element_type in ['branch_rail_connector', 'branch_start', 'branch_end', 'branch_next']:
            if element.branch_id:
                branch_text_id = self.create_text(
                    element.x + element.width // 2,
                    element.y - 12,
                    text=f"B:{element.branch_id[-1] if len(element.branch_id) > 8 else element.branch_id}",
                    font=("Arial", 6),
                    fill=color,
                    anchor="center",
                    tags="debug_overlay"
                )
                self._debug_overlays.append(branch_text_id)

        # For rung elements, show rung number
        elif element.element_type == 'rung':
            rung_text_id = self.create_text(
                element.x + 5,
                element.y + 5,
                text=f"R:{element.rung_number}",
                font=("Arial", 6),
                fill=color,
                anchor="nw",
                tags="debug_overlay"
            )
            self._debug_overlays.append(rung_text_id)

    def _add_debug_tooltip_section(self, frame: tk.Frame, element: LadderElement):
        """Add the debug information section to tooltips."""

        # Add separator for debug info
        ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=2)

        # Debug header
        debug_header = tk.Label(
            frame,
            text="Debug Info:",
            background="#fffacd",
            font=("Arial", 8, "bold"),
            foreground="red"
        )
        debug_header.pack(anchor="w")

        # Element coordinates
        coords_label = tk.Label(
            frame,
            text=f"Coords: ({element.x}, {element.y})",
            background="#fffacd",
            font=("Arial", 7),
            foreground="red"
        )
        coords_label.pack(anchor="w")

        # Element size
        size_label = tk.Label(
            frame,
            text=f"Size: {element.width}x{element.height}",
            background="#fffacd",
            font=("Arial", 7),
            foreground="red"
        )
        size_label.pack(anchor="w")

        # Canvas ID
        canvas_id_label = tk.Label(
            frame,
            text=f"Canvas ID: {element.canvas_id}",
            background="#fffacd",
            font=("Arial", 7),
            foreground="red"
        )
        canvas_id_label.pack(anchor="w")

        # Element type
        type_label = tk.Label(
            frame,
            text=f"Type: {element.element_type}",
            background="#fffacd",
            font=("Arial", 7),
            foreground="red"
        )
        type_label.pack(anchor="w")

        # Memory address (for debugging)
        memory_label = tk.Label(
            frame,
            text=f"Object ID: {id(element)}",
            background="#fffacd",
            font=("Arial", 7),
            foreground="red"
        )
        memory_label.pack(anchor="w")

    def _add_rung_debug_info(self, frame: tk.Frame, element: LadderElement):
        """Add rung-specific debug information."""
        rung_number = element.rung_number

        # Rung number
        tk.Label(
            frame,
            text=f"Rung Number: {rung_number}",
            background="#fffacd",
            font=("Arial", 9),
            foreground="black"
        ).pack(anchor="w")

        if self._routine and rung_number < len(self._routine.rungs):
            rung = self._routine.rungs[rung_number]

            # Instruction count
            tk.Label(
                frame,
                text=f"Instructions: {len(rung.instructions)}",
                background="#fffacd",
                font=("Arial", 8),
                foreground="gray"
            ).pack(anchor="w")

            # Branch count
            tk.Label(
                frame,
                text=f"Branches: {len(rung._branches) if hasattr(rung, '_branches') else 0}",
                background="#fffacd",
                font=("Arial", 8),
                foreground="gray"
            ).pack(anchor="w")

            # Max branch depth
            max_depth = rung.get_max_branch_depth() if hasattr(rung, 'get_max_branch_depth') else 0
            tk.Label(
                frame,
                text=f"Max Branch Depth: {max_depth}",
                background="#fffacd",
                font=("Arial", 8),
                foreground="gray"
            ).pack(anchor="w")

            # Rung text (truncated)
            rung_text = rung.text if rung.text else "(empty)"
            if len(rung_text) > 30:
                rung_text = rung_text[:30] + "..."
            tk.Label(
                frame,
                text=f"Text: {rung_text}",
                background="#fffacd",
                font=("Arial", 8),
                foreground="gray"
            ).pack(anchor="w")

    def _add_wire_debug_info(self, frame: tk.Frame, element: LadderElement):
        """Add wire-specific debug information."""

        tk.Label(
            frame,
            text="Wire Element",
            background="#fffacd",
            font=("Arial", 9),
            foreground="black"
        ).pack(anchor="w")

        # Connection info would go here if we tracked wire connections
        tk.Label(
            frame,
            text="Connection: Main Rail",
            background="#fffacd",
            font=("Arial", 8),
            foreground="gray"
        ).pack(anchor="w")

    def _assm_ladder_element_from_rung_element(self, ladder_element: LadderElement, rung_element: plc.RungElement, rung_number: int) -> None:
        """Assemble a LadderElement from a RungElement."""
        ladder_element.branch_level = rung_element.branch_level
        ladder_element.branch_id = rung_element.branch_id
        ladder_element.parent_branch_id = rung_element.root_branch_id
        ladder_element.rung_number = rung_number
        ladder_element.instruction = rung_element.instruction
        ladder_element.position = rung_element.position

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
        rung_elements = self._get_rung_ladder_elements(rung_number, branch_level, branch_id)
        last_position = max((e.position for e in rung_elements), default=-1)
        default_start = self.RAIL_X_LEFT + self.ELEMENT_SPACING + 30, center_y

        if not rung_elements:
            # No elements, insert at start
            return default_start
        elif insertion_position == 0:
            return self.RAIL_X_LEFT + (self.ELEMENT_SPACING/2), center_y
        elif insertion_position > last_position:
            # Insert at the end
            last_element = rung_elements[-1]
            return last_element.x + last_element.width + self.ELEMENT_SPACING + self.MIN_WIRE_LENGTH, center_y
        else:
            # Because positions are shared across branches, we need to find the exact position
            this_element_index = 0
            for index, element in enumerate(rung_elements):
                if element.position == insertion_position:
                    this_element_index = index
                    break
                if element.position < insertion_position:
                    this_element_index = index + 1
            if this_element_index == 0:
                # Insert at the start
                if len(rung_elements) > 0:
                    last_element = rung_elements[-1]
                    return last_element.x + last_element.width + self.ELEMENT_SPACING + self.MIN_WIRE_LENGTH, center_y
                return default_start
            else:
                prev_element_index = this_element_index - 1
            # Insert between elements
            prev_element = rung_elements[prev_element_index]
            this_element = rung_elements[this_element_index]
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
        self.delete(f"rung_{rung_number}")
        self.delete(f"rung_{rung_number}_instruction")
        self.delete(f"rung_{rung_number}_wire")
        self.delete(f"rung_{rung_number}_branch")
        self.delete(f"rung_{rung_number}_branch_marker")
        self.delete(f"rung_{rung_number}_branch_start")
        self.delete(f"rung_{rung_number}_branch_end")
        self.delete(f"rung_{rung_number}_branch_next")

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

    def _clear_hover_preview(self):
        """Clear the hover preview."""
        if self._hover_preview_id:
            self.delete("hover_preview")
            self._hover_preview_id = None
            self._last_hover_position = None

    def _clear_element_hover_preview(self):
        """Clear the element hover preview."""
        self.delete('current_element_highlight')

    def _clear_rung_hover_preview(self):
        """Clear the rung hover preview."""
        self.delete('current_rung_highlight')

    def _copy_element(self, element: LadderElement):
        """Copy an element (placeholder)."""
        self._show_status(f"Copied element: {element.text}")

    def _create_ladder_branch(self, ladder_element: LadderElement, element: plc.RungElement, rung_number: int):
        return LadderBranch(
            start_x=ladder_element.x,
            end_x=ladder_element.x + 50,  # this will be updated when the branch closes
            main_y=self._rung_y_positions[rung_number],
            branch_y=ladder_element.y,
            rung_number=rung_number,
            branch_id=element.branch_id,
            root_branch_id=element.root_branch_id,
            branch_level=element.branch_level,
            elements=[],
            start_position=element.position,
            end_position=element.position  # this will be updated when the branch closes
        )

    def _delete_branch(self, branch_id: str):
        """Delete a branch and all its elements."""
        if branch_id in self._branches:
            branch = self._branches[branch_id]

            # Remove branch from rung
            rung = self._routine.rungs[branch.rung_number] if self._routine else None
            if not rung:
                raise ValueError(f"Rung {branch.rung_number} not found in routine.")
            rung.remove_branch(branch_id)

            # Remove from branches dict
            del self._branches[branch_id]

            self._redraw_rung(branch.rung_number)

            self._show_status(f"Deleted branch: {branch_id}")

    def _delete_element(self, event, element: LadderElement):
        """Delete an element from the rung."""
        # Remove from rung meta data
        rung_number = int(element.instruction.rung.number)
        if rung_number is None or rung_number < 0:
            self.logger.debug(f"No rung found for element at Y={element.y}")
            return
        if element.position is None:
            self.logger.debug(f"No position found for element at Y={element.y}")
            return
        element.instruction.rung.remove_instruction(element.position)

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
            outline=THEME["foreground"], fill=THEME["background"], width=2,
            tags=f"rung_{rung_number}_instruction"
        )

        # Add instruction type text (centered in top half of block)
        inst_name = instruction.instruction_name
        self.create_text(
            x + self.BLOCK_WIDTH // 2, center_y - 10,
            text=inst_name, font=(THEME["font"], 10, 'bold'),
            tags=f"rung_{rung_number}_instruction"
        )

        # Add operands text (centered in bottom half of block)
        operands_text = ', '.join([op.meta_data for op in instruction.operands]) if instruction.operands else ""
        if len(operands_text) > 12:
            operands_text = operands_text[:12] + "..."

        self.create_text(
            x + self.BLOCK_WIDTH // 2, center_y + 5,
            text=operands_text, font=(THEME["font"], 8),
            tags=f"rung_{rung_number}_instruction"
        )

        # Draw connecting wires at rung centerline
        wire_y = center_y
        # Left connecting wire
        self.create_line(
            x - 10, wire_y,
            x, wire_y,
            fill=THEME["foreground"],  # Use theme color for wires
            width=2, tags=f"rung_{rung_number}_wire"
        )
        # Right connecting wire
        self.create_line(
            x + self.BLOCK_WIDTH, wire_y,
            x + self.BLOCK_WIDTH + 10, wire_y,
            fill=THEME["foreground"],  # Use theme color for wires
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

    def _draw_branch_rail_connector(self, x, y, tags=None) -> LadderElement:
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
            fill=THEME["background"], outline=THEME["ladder_rung_color"], width=1, tags=tags
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
                               tags: str = None, dashed_line: bool = False):
        """Draw a line for the branch rail connector.
        Args:
            x: Start X position
            y: Start Y position
            end_x: End X position
            end_y: End Y position
            tags: Additional tags for the canvas item
            dashed_line: Whether to use a dashed line
        """
        self.create_line(
            x, y, end_x, end_y,
            fill=THEME["ladder_rung_color"], width=1,
            dash=(3, 3) if dashed_line else None,
            tags=tags
        )

    def _draw_branch_left_rail(self,
                               x: int,
                               y: int,
                               nesting_level: Optional[int] = 0,
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
        # Add branch line
        branch_y = y + (self.BRANCH_SPACING * (nesting_level + 1))
        self._draw_branch_rail_line(x, y, x, branch_y, tags=tags, dashed_line=dashed_line)

        # Add horizontal branch line
        self._draw_branch_rail_line(x, branch_y, x + 50, branch_y, tags=tags, dashed_line=dashed_line)

        # Draw branch start indicator last to ensure it appears on top
        ladder_element = self._draw_branch_rail_connector(x, y, tags)

        # Add text
        if branch_text:
            self.create_text(x, y - 15,
                             text=branch_text, font=(THEME["font"], 8),
                             fill=THEME["foreground"], tags=tags)
        return ladder_element

    def _draw_branch_next_rail(self,
                               x: int,
                               y: int,
                               nesting_level: Optional[int] = 0,
                               oval_fill: str = 'lightgreen',
                               oval_outline: str = 'green',
                               tags: str = None) -> LadderElement:
        """Draw the next rail branch start indicator.
        Args:
            x: X position for the branch start
            y: Y position for the branch start
            oval_fill: Fill color for the oval indicator
            oval_outline: Outline color for the oval indicator
            tags: Additional tags for the canvas item
        Returns:
            LadderElement: The created branch rail connector element.
        """
        branch_y = y + (self.BRANCH_SPACING * (nesting_level + 1))
        return self._draw_branch_rail_connector(x, branch_y, tags)

    def _draw_branch_right_rail(self,
                                x: int,
                                y: int,
                                nesting_level: Optional[int] = 0,
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

        # Add preview branch line
        branch_y = y + (self.BRANCH_SPACING * (nesting_level + 1))
        self._draw_branch_rail_line(x, y, x, branch_y,
                                    tags=tags, dashed_line=dashed_line)

        # Add preview horizontal branch line
        self._draw_branch_rail_line(
            x, branch_y, x - 50, branch_y,
            tags=tags, dashed_line=dashed_line
        )

        # Draw branch end indicator last to ensure it appears on top
        ladder_element = self._draw_branch_rail_connector(x, y, tags)

        # Add text
        if branch_text:
            self.create_text(
                x, y + 15,
                text=branch_text, font=(THEME["font"], 8),
                fill=THEME["foreground"], tags=tags
            )

        return ladder_element

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
            outline=THEME["ladder_rung_color"], fill=THEME["background"], width=2,
            tags=f"rung_{rung_number}_instruction"
        )

        # Add coil type indicators (centered in coil)
        inst_type = instruction.instruction_name.lower()
        if inst_type == 'otl':  # Latch
            self.create_text(
                x + self.COIL_WIDTH // 2, center_y,
                text='L', font=(THEME["font"], 12, 'bold'),
                fill=THEME["foreground"],
                tags=f"rung_{rung_number}_instruction"
            )
        elif inst_type == 'otu':  # Unlatch
            self.create_text(
                x + self.COIL_WIDTH // 2, center_y,
                text='U', font=(THEME["font"], 12, 'bold'),
                fill=THEME["foreground"],
                tags=f"rung_{rung_number}_instruction"
            )

        # Draw connecting wires at rung centerline
        wire_y = center_y
        # Left connecting wire
        self.create_line(
            x - 10, wire_y,
            x, wire_y,
            fill=THEME["ladder_rung_color"],  # Use theme color for wires
            width=1, tags=f"rung_{rung_number}_wire"
        )
        # Right connecting wire (to power rail if this is the last element)
        self.create_line(
            x + self.COIL_WIDTH, wire_y,
            x + self.COIL_WIDTH + 10, wire_y,
            fill=THEME["ladder_rung_color"],  # Use theme color for wires
            width=1, tags=f"rung_{rung_number}_wire"
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
            outline=THEME["ladder_rung_color"], fill=THEME["background"], width=2,
            tags=f"rung_{rung_number}_instruction"
        )

        # Add contact bars
        if is_normally_closed:
            # Diagonal line for normally closed (centered in contact)
            self.create_line(
                x + 5, top_y + 5,
                x + self.CONTACT_WIDTH - 5, bottom_y - 5,
                fill=THEME["ladder_rung_color"],
                width=2, tags=f"rung_{rung_number}_instruction"
            )
        else:
            # Vertical lines for normally open (centered in contact)
            bar_top = top_y + 5
            bar_bottom = bottom_y - 5
            self.create_line(
                x + 10, bar_top,
                x + 10, bar_bottom,
                fill=THEME["ladder_rung_color"],
                width=2, tags=f"rung_{rung_number}_instruction"
            )
            self.create_line(
                x + self.CONTACT_WIDTH - 10, bar_top,
                x + self.CONTACT_WIDTH - 10, bar_bottom,
                fill=THEME["ladder_rung_color"],
                width=2, tags=f"rung_{rung_number}_instruction"
            )

        # Draw connecting wires to power rail (horizontal lines at rung center)
        wire_y = center_y
        # Left connecting wire (from power rail to contact)
        self.create_line(
            x - 10, wire_y,  # Start 10 pixels before contact
            x, wire_y,       # End at contact left edge
            fill=THEME["ladder_rung_color"],  # Use theme color for wires
            width=1, tags=f"rung_{rung_number}_wire"
        )
        # Right connecting wire (from contact to next element)
        self.create_line(
            x + self.CONTACT_WIDTH, wire_y,
            x + self.CONTACT_WIDTH + 10, wire_y,
            fill=THEME["ladder_rung_color"],  # Use theme color for wires
            width=1, tags=f"rung_{rung_number}_wire"
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

    def _draw_instruction(self, instruction: plc.LogixInstruction, x: int, y: int,
                          rung_number: int) -> LadderElement:
        """Draw a single instruction.

        Args:
            instruction: The LogixInstruction to draw
            x: X position for the instruction
            y: Y position (should be the rung centerline)
            rung_number: The rung number this instruction belongs to
        """
        inst_type = instruction.instruction_name.lower()

        if inst_type in ['xic', 'xio']:  # Contacts
            element = self._draw_contact(instruction, x, y, rung_number)
        elif inst_type in ['ote', 'otl', 'otu']:  # Coils
            element = self._draw_coil(instruction, x, y, rung_number)
        else:  # Function blocks
            element = self._draw_block(instruction, x, y, rung_number)

        # Add debug overlays if debug mode is enabled
        if self._debug_mode and element:
            self._add_debug_overlay_for_element(element)

        return element

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
            fill=THEME["foreground"],
            text=operand, font=(THEME["font"], 8,), tags=f"rung_{rung_number}_instruction"
        )

        # return the operand text for further use
        return operand

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

    def _draw_routine(self):
        """Draw the entire routine on the canvas."""
        self.clear_canvas()

        if not self._routine:
            self._show_status("No routine loaded")
            return

        if not self._routine.rungs:
            self._routine.add_rung(plc.Rung(controller=self._routine.controller, routine=self._routine))

        y_pos = self.RUNG_START_Y
        for i, rung in enumerate(self._routine.rungs):
            ladder_element = self._draw_rung(rung, i, y_pos)
            if ladder_element:
                self._elements.append(ladder_element)
            y_pos += self.RUNG_HEIGHT + (self.BRANCH_SPACING * rung.get_max_branch_depth()) + 20

        # Update scroll region
        self.configure(scrollregion=self.bbox("all"))

    def _draw_rung(self, rung: plc.Rung, rung_number: int, y_pos: int) -> LadderElement:
        """Draw a single rung using the enhanced PLC data structure."""
        self._rung_y_positions[rung_number] = y_pos
        branch_depth = rung.get_max_branch_depth()
        rung_height = self.RUNG_HEIGHT + (self.BRANCH_SPACING * branch_depth)

        # Create rectangle for rung number
        rect_id = self.create_rectangle(0, y_pos,
                                        self.RAIL_X_LEFT, y_pos + rung_height,
                                        outline=THEME["background"], fill=THEME["background"],
                                        tags=f"rung_{rung_number}")

        # Draw rung number
        self.create_text(15, y_pos + rung_height // 2,
                         text=str(rung_number), anchor='w', font=('Roboto', 10), tag=f"rung_{rung_number}", fill=THEME["foreground"])

        # Draw power rails
        self.create_line(self.RAIL_X_LEFT, y_pos, self.RAIL_X_LEFT, y_pos + rung_height,
                         width=3, tags=f"rung_{rung_number}", fill=THEME["ladder_rung_color"])

        center_y = y_pos + self.RUNG_HEIGHT // 2

        self.create_line(self.RAIL_X_LEFT, center_y, self.winfo_reqwidth() - 40, center_y,
                         width=2, tags=f"rung_{rung_number}", fill=THEME["ladder_rung_color"])

        if rung and rung.rung_sequence:
            self._draw_rung_sequence(rung)
            # element = [e for e in self._elements if e.rung_number == rung_number].sort(key=lambda e: e.position)
            # right_rail_x = element[-1].x + element[-1].width if element else self.winfo_reqwidth() - 40
            # self.create_line(right_rail_x, y_pos, right_rail_x, y_pos + rung_height,
            #                  width=3, tags=f"rung_{rung_number}", fill=THEME["ladder_rung_color"])

        return LadderElement(
            element_type='rung',
            x=0, y=y_pos,
            width=self.RAIL_X_LEFT, height=rung_height,
            canvas_id=rect_id,
            rung_number=rung_number
        )

    def _draw_rung_sequence(self, rung: plc.Rung):
        """Draw rung using the new sequence structure with proper spacing.
        Args:
            rung: The PLC rung to draw
            rung_number: The number of the rung being drawn
            y_pos: The Y position where the rung starts
            start_x: The starting X position for the first element in the rung
        """
        rung_number = int(rung.number)
        current_branch_level = 0
        ladder_element: Optional[LadderElement] = None
        branch_tracking: list[dict] = []

        for element in rung.rung_sequence:
            if element.element_type == plc.RungElementType.INSTRUCTION:
                x, y = self._get_element_x_y_sequence_spacing(element)
                ladder_element = self._draw_instruction(element.instruction, x, y, rung_number)
                self._assm_ladder_element_from_rung_element(ladder_element, element, rung_number)
                self._elements.append(ladder_element)

            elif element.element_type == plc.RungElementType.BRANCH_START:
                x, y = self._get_element_x_y_sequence_spacing(element)
                nesting_level = rung.get_branch_internal_nesting_level(element.position)
                ladder_element = self._draw_branch_left_rail(x, y, nesting_level, oval_fill='gray', oval_outline='black',
                                                             tags=f"rung_{rung_number}_branch_start")
                self._assm_ladder_element_from_rung_element(ladder_element, element, rung_number)
                branch_element = self._create_ladder_branch(ladder_element, element, rung_number)
                self._elements.append(ladder_element)
                self._branches[element.branch_id] = branch_element
                branch_tracking.append({
                    'branch_id': element.branch_id,
                    'branch_level': current_branch_level,
                    'branch_element': ladder_element,
                    'branch_nesting': nesting_level
                })

            elif element.element_type == plc.RungElementType.BRANCH_NEXT:
                matching_branch = self._get_element_root_branch(element)
                if not matching_branch:
                    raise ValueError(f"Branch with ID {element.root_branch_id} not found in branches.")
                branch_depth = rung.get_branch_internal_nesting_level(matching_branch.start_position)
                x, y = matching_branch.start_x + 5, matching_branch.branch_y + (branch_depth * self.BRANCH_SPACING) + 5
                ladder_element = self._draw_branch_next_rail(x, y, oval_fill='gray', oval_outline='black',
                                                             tags=f"rung_{rung_number}_branch_next")
                self._assm_ladder_element_from_rung_element(ladder_element, element, rung_number)
                branch_element = self._create_ladder_branch(ladder_element, element, rung_number)
                self._elements.append(ladder_element)
                self._branches[element.branch_id] = branch_element

            elif element.element_type == plc.RungElementType.BRANCH_END:
                if not branch_tracking:
                    raise ValueError("Branch end found without a matching branch start.")
                branch = branch_tracking.pop()
                parent_branch = self._branches.get(branch['branch_id'], None)
                if not parent_branch:
                    raise ValueError(f"Parent branch with ID {branch['branch_id']} not found in branches.")
                current_branch_level = branch['branch_level']
                child_branches = [x for x in self._branches.values()
                                  if x.root_branch_id == parent_branch.branch_id]
                x, y = self._get_element_x_y_sequence_spacing(element)
                nesting_level = branch['branch_nesting']

                ladder_element = self._draw_branch_right_rail(x, y, nesting_level, oval_fill='gray', oval_outline='black',
                                                              tags=f"rung_{rung_number}_branch_end")
                self._assm_ladder_element_from_rung_element(ladder_element, element, rung_number)
                self._elements.append(ladder_element)
                parent_branch.end_x = ladder_element.x + ladder_element.width
                parent_branch.end_position = element.position

                for b in child_branches:
                    b.end_x = parent_branch.end_x
                    b.end_position = element.position

    def _edit_instruction(self, instruction: plc.LogixInstruction):
        """Edit an instruction (placeholder - implement instruction editor dialog)."""
        self._show_status(f"Edit instruction: {instruction.meta_data}")

    def _find_insertion_position(self, x: int, rung_number: int, branch_level: int = 0,
                                 branch_id: Optional[str] = None) -> int:
        """Find the correct position to insert a new element in the rung sequence."""
        rung_elements = self._get_rung_ladder_elements(rung_number, branch_level, branch_id)

        if not rung_elements:
            self.logger.debug(f"No elements found for rung {rung_number} at branch level {branch_level}")
            return 0

        # Find the element closest to the click position
        closest_element = None
        closest_element_index = -1
        min_distance = float('inf')

        for index, element in enumerate(rung_elements):
            element_center_x = element.x + element.width // 2
            distance = abs(element_center_x - x)

            if distance < min_distance:
                min_distance = distance
                closest_element_index = index
                closest_element = element

        if closest_element is None:
            return rung_elements[-1].position if rung_elements else 0

        # Determine if we should insert before or after the closest element
        element_center_x = closest_element.x + closest_element.width // 2

        if x < element_center_x:
            # Insert before this element
            return rung_elements[closest_element_index-1].position+1 if closest_element_index > 0 else 0
        else:
            # Insert after this element
            return rung_elements[closest_element_index].position + 1

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

    def _get_branch_id_at_position(self, x: int, y: int, rung_number: int,
                                   branch_level: int) -> Optional[str]:
        """Get the branch ID for elements at a specific position."""
        if branch_level == 0:
            return None

        # Find which branch this position belongs to
        for branch_id, branch in self._branches.items():
            if (branch.rung_number == rung_number and
                    branch.start_x <= x <= branch.end_x and
                    branch.main_y <= y <= branch.branch_y + self.BRANCH_SPACING and
                    branch.branch_level == branch_level):
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

    def _get_branch_level_at_y(self, y: int, rung_number: int) -> int:
        """Determine which branch level the Y coordinate corresponds to."""
        if rung_number not in self._rung_y_positions:
            return 0

        branches = [b for b in self._branches.values() if b.rung_number == rung_number]
        for branch in branches:
            if branch.branch_y <= y <= branch.branch_y + self.BRANCH_SPACING:
                return branch.branch_level
        # If no branch found, return main rung level
        return 0

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

    def _get_element_root_branch(self, element: LadderElement) -> Optional[LadderBranch]:
        """Get the root branch ID for a given element."""
        matching_branch: LadderBranch = self._branches.get(element.root_branch_id, None)
        if not matching_branch:  # Because sub branches are named after their root, we can attempt parsing it that way
            return next((x for x in self._branches.values() if x.branch_id in element.branch_id), None)
        return matching_branch

    def _get_element_x_spacing(self, prev_element: LadderElement) -> int:
        """Get the spacing needed for the next element based on the current element."""
        if not prev_element:
            return self.RAIL_X_LEFT + self.MIN_WIRE_LENGTH
        return prev_element.x + prev_element.width + self.ELEMENT_SPACING + self.MIN_WIRE_LENGTH

    def _get_element_y_spacing(self, element: LadderElement) -> int:
        """Get the Y spacing for elements in a rung based on branch level."""
        rung_y = self._rung_y_positions.get(element.rung_number, None)
        if not rung_y:
            raise ValueError(f"Rung number {element.rung_number} not found in rung positions.")
        return rung_y + (self.RUNG_HEIGHT // 2) + (self.BRANCH_SPACING * element.branch_level)

    def _get_element_x_y_sequence_spacing(self, element: plc.RungElement,):
        if element.element_type == plc.RungElementType.BRANCH_END:
            prev_element = self._get_last_branch_ladder_x_element(element)
        else:
            prev_element = self._get_last_ladder_element(element)
        element_x = self._get_element_x_spacing(prev_element)
        element_y = self._get_element_y_spacing(element)
        return (element_x, element_y)

    def _get_last_branch_ladder_x_element(self, element: plc.RungElement) -> Optional[LadderElement]:
        """Get the last ladder element in a main branch seqeuence (The most to the right)."""
        last_element: Optional[LadderElement] = None

        for branch in self._branches.values():
            if branch.branch_id == element.branch_id or branch.root_branch_id == element.root_branch_id:
                ladder_elements = self._get_rung_ladder_elements(element.rung_number,
                                                                 branch.branch_level,
                                                                 branch.branch_id,
                                                                 element.root_branch_id)
                if not ladder_elements:
                    continue
                if not last_element:
                    last_element = ladder_elements[-1]
                    continue
                if ladder_elements[-1].x + ladder_elements[-1].width > last_element.x + last_element.width:
                    last_element = ladder_elements[-1]
        return last_element

    def _get_last_ladder_element(self, element: plc.RungElement) -> Optional[LadderElement]:
        """Get the last ladder element in the rung sequence."""
        ladder_elements = self._get_rung_ladder_elements(element.rung_number, element.branch_level, element.root_branch_id)
        return ladder_elements[-1] if ladder_elements else None

    def _get_parent_branch_id_at_position(self, x: int, y: int, rung_number: int) -> Optional[str]:
        """Get the parent branch ID at a specific position."""
        for branch in self._branches.values():
            if (branch.rung_number == rung_number and
                    branch.start_x <= x <= branch.end_x and
                    branch.main_y <= y <= branch.branch_y + self.BRANCH_SPACING):
                return branch.branch_id
        return None

    def _get_rung_ladder_elements(self, rung_number: int, branch_level: int = 0,
                                  branch_id: Optional[str] = None,
                                  root_branch_id: Optional[str] = None) -> List[LadderElement]:
        """Get all elements for a specific rung and branch level."""
        elements = []

        for element in self._elements:
            if element.rung_number != rung_number:
                continue
            if element.branch_level != branch_level:
                continue
            if element.element_type not in ['contact', 'coil', 'block', 'branch_rail_connector']:
                continue
            if branch_id is not None and element.branch_id != branch_id:
                if root_branch_id is not None and element.root_branch_id != root_branch_id:
                    continue
            elements.append(element)

        # Sort by position
        elements.sort(key=lambda e: e.position)
        return elements

    def _get_rung_at_y(self, y: int) -> Optional[int]:
        """Get rung number at given Y coordinate."""
        for rung_num, rung_y in self._rung_y_positions.items():
            rung_height = self.RUNG_HEIGHT + (self.BRANCH_SPACING * self._routine.rungs[rung_num].get_max_branch_depth())
            if rung_y <= y <= rung_y + rung_height:
                return rung_num
        return None

    def _hide_tooltip(self):
        """Hide the current tooltip."""
        if self._tooltip_id:
            self.after_cancel(self._tooltip_id)
            self._tooltip_id = None

        if self._tooltip:
            self._tooltip.destroy()
            self._tooltip = None

        self._tooltip_element = None

    def _highlight_current_element(self, element: LadderElement):
        """Highlight the currently hovered element by changing its outline color."""
        self._clear_element_hover_preview()

        if element is None:
            return

        # Highlight the current element
        self._hover_preview_id = self.create_rectangle(
            element.x, element.y,
            element.x + element.width, element.y + element.height,
            outline='orange', width=2, tags="current_element_highlight"
        )

    def _highlight_current_rung(self, rung_number: int):
        """highlight the current rung by changing the background color of the left bar area.
        """
        self._clear_rung_hover_preview()

        if rung_number is None or rung_number not in self._rung_y_positions:
            return

        # Highlight the current rung
        y_pos = self._rung_y_positions[rung_number]
        rung = self._routine.rungs[rung_number]
        rung_height = self.RUNG_HEIGHT + (self.BRANCH_SPACING * rung.get_max_branch_depth())
        self._hover_preview_id = self.create_rectangle(
            0, y_pos, self.RAIL_X_LEFT, y_pos + rung_height,
            stipple='gray50', tags="current_rung_highlight", outline='lightgreen', width=2
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

    def _on_motion(self, event: tk.Event) -> None:
        """Handle mouse motion for hover effects.
        This method updates the hover preview and highlights the current rung and element.
        Args:
            event: The mouse event containing the x and y coordinates.
        """
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        self._on_tooltip_motion(event, x, y)
        self._highlight_current_rung(self._get_rung_at_y(y))
        self._highlight_current_element(self._get_element_at(x, y))

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

    def _on_mouse_leave(self, _: tk.Event):
        """Handle mouse leaving the canvas."""
        self._clear_hover_preview()
        self._clear_rung_hover_preview()
        self._hide_tooltip()

    def _on_right_click(self, event):
        """Handle right-click context menu."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        element = self._get_element_at(x, y)

        if element:
            self._show_context_menu(event, element)

    def _on_tooltip_motion(self, event, x: int, y: int):
        """Enhanced motion handler with tooltip support."""
        # Handle tooltip
        element = self._get_element_at(x, y)

        if element != self._tooltip_element:
            self._hide_tooltip()
            self._tooltip_element = element

            if element and element.instruction:
                # Schedule tooltip
                self._tooltip_id = self.after(
                    self._tooltip_delay,
                    lambda: self._show_element_tooltip(event.x_root, event.y_root, element)
                )

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

    def _show_element_tooltip(self, x: int, y: int, element: LadderElement):
        """Show tooltip for ladder element with debug info for all element types."""
        if not element:
            return

        # Create tooltip window
        self._tooltip = tk.Toplevel(self)
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.wm_geometry(f"+{x + 15}+{y + 15}")

        # Create tooltip content frame
        frame = tk.Frame(
            self._tooltip,
            background="#fffacd",  # Light yellow
            relief="solid",
            borderwidth=1,
            padx=6,
            pady=4
        )
        frame.pack()

        # Show content based on element type
        if element.instruction:
            self._add_instruction_tooltip_content(frame, element)
        elif self._debug_mode:
            # Debug mode: show tooltips for non-instruction elements
            self._add_debug_element_tooltip_content(frame, element)
        else:
            # No tooltip for non-instruction elements in normal mode
            self._tooltip.destroy()
            self._tooltip = None
            return

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
        elif element.element_type in ['branch_rail_connector']:
            menu.add_command(label="Delete Branch", command=lambda: self._delete_branch(element.branch_id))
        elif element.element_type in ['rung']:
            menu.add_command(label="Delete Rung", command=lambda: self.delete_rung(element.rung_number))
            menu.add_separator()
            menu.add_command(label="Add Contact", command=lambda: self._insert_element_at(event.x, event.y))
            menu.add_command(label="Add Coil", command=lambda: self._insert_element_at(event.x, event.y))
            menu.add_command(label="Add Block", command=lambda: self._insert_element_at(event.x, event.y))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _show_status(self, message: str):
        """Show status message with debug prefix if in debug mode."""
        debug_prefix = "[DEBUG] " if self._debug_mode else ""
        full_message = f"{debug_prefix}{message}"
        self.logger.info(full_message)

        # Also show in status bar if available
        if hasattr(self, '_status_label'):
            self._status_label.config(text=full_message)

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
        rung_number = self._get_rung_at_y(y)

        if rung_number is None:
            self._clear_hover_preview()
            return

        if not self._validate_insertion_position(x, y, rung_number):
            self._clear_hover_preview()
            return

        branch_level = self._get_branch_level_at_y(y, rung_number)
        branch_id = self._get_branch_id_at_position(x, y, rung_number, branch_level)
        insertion_position = self._find_insertion_position(x, rung_number, branch_level, branch_id)
        insertion_x, insertion_y = self._calculate_insertion_coordinates(x, y, rung_number,
                                                                         insertion_position, branch_level, branch_id)
        current_position = (insertion_x, insertion_y, self._mode)

        if current_position != self._last_hover_position:
            self._clear_hover_preview()
            self._draw_hover_preview(insertion_x, insertion_y, self._mode)
            self._last_hover_position = current_position

    def _update_branch_hover_preview(self, x: int, y: int):
        """Update the hover preview for branch creation."""
        rung_number = self._get_rung_at_y(y)
        self.logger.debug(f"Updating branch hover preview at ({x}, {y}) on rung {rung_number}")

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

    def _update_debug_display(self):
        """Update debug visual overlays for all element types."""
        # Clear existing debug overlays
        for overlay_id in self._debug_overlays:
            self.delete(overlay_id)
        self._debug_overlays.clear()

        if not self._debug_mode:
            return

        # Add debug overlays for all elements
        for element in self._elements:
            self._add_debug_overlay_for_any_element(element)

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

        if x < self.RAIL_X_LEFT:
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
        self._debug_mode = False
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

        # Separator
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=5)

        # Debug mode toggle button
        self._debug_button = tk.Button(
            toolbar,
            text="Debug: OFF",
            command=self._toggle_debug_mode,
            bg='lightgray',
            relief='raised'
        )
        self._debug_button.pack(side='right', padx=2)

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

    def _toggle_debug_mode(self):
        """Toggle developer debug mode on/off."""
        self._debug_mode = not self._debug_mode

        # Update button appearance
        if self._debug_mode:
            self._debug_button.config(
                text="Debug: ON",
                bg='lightgreen',
                relief='sunken'
            )
            self._status_label.config(text="Debug mode enabled - Additional info will be shown")
        else:
            self._debug_button.config(
                text="Debug: OFF",
                bg='lightgray',
                relief='raised'
            )
            self._status_label.config(text="Debug mode disabled")

        # Pass debug state to canvas
        if hasattr(self._ladder_canvas, '_debug_mode'):
            self._ladder_canvas._debug_mode = self._debug_mode

        # Optionally redraw with debug info
        if hasattr(self._ladder_canvas, '_update_debug_display'):
            self._ladder_canvas._update_debug_display()

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

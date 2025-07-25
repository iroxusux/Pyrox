"""Ladder Logic Editor components for Pyrox framework."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import tkinter as tk
from tkinter import ttk, Canvas
from typing import Any, Optional, Dict, List, Literal, Union
import re

from .frames import TaskFrame
from ..plc import plc
from ..abc.meta import Loggable


THEME: dict = {
    "font": "Roboto",
    "instruction_alias": "#EF1010",
    "background": "#333333",
    "comment_background": "#444444",
    "comment_foreground": "#09C83F",
    "foreground": "#f00bd5",
    "highlight_color": "#4A90E2",
    "button_color": "#4A90E2",
    "button_hover_color": "#357ABD",
    "button_text_color": "#ffffff",
    "ladder_rung_color": "#EF1010",
    "ladder_line_width": 2,
    "tooltip_background": "#e6f3ff",
    "tooltip_label_background": "#e6f3ff",
    "tooltip_label_foreground": "#0066cc",
}
"""Theme for the ladder editor components."""


class LadderEditorMode(Enum):
    """Editing modes for the ladder editor.
    Available modes:
    - VIEW: View mode, no editing allowed.
    - EDIT: Edit mode, allows adding and modifying elements.
    - INSERT_CONTACT: Insert a contact element.
    - INSERT_COIL: Insert a coil element.
    - INSERT_BLOCK: Insert a function block element.
    - INSERT_BRANCH: Insert a branch element.
    - CONNECT_BRANCH: Connect a branch to an existing element.
    """
    VIEW = "view"
    EDIT = "edit"
    INSERT_CONTACT = "insert_contact"
    INSERT_COIL = "insert_coil"
    INSERT_BLOCK = "insert_block"
    INSERT_BRANCH = "insert_branch"
    CONNECT_BRANCH = "connect_branch"
    DRAG_ELEMENT = "draw_element"


@dataclass
class LadderOperand:
    """Represents an operand within a ladder element.
    """
    text: str
    x: int
    y: int
    width: int
    height: int
    canvas_id: int
    instruction: Optional['plc.LogixInstruction'] = None
    operand_index: int = 0


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
    root_branch_id: Optional[str] = None
    position: int = 0  # Position in rung sequence

    # Theme settings
    theme_overrides: Optional[Dict[str, Any]] = field(default_factory=dict)
    custom_fill: Optional[str] = THEME["background"]
    custom_outline: Optional[str] = THEME["ladder_rung_color"]
    custom_text_color: Optional[str] = THEME["foreground"]

    # Operand support
    operands: List[LadderOperand] = field(default_factory=list)


@dataclass
class LadderBranch:
    """Represents a branch structure in ladder logic."""
    start_x: int
    end_x: int
    main_y: int
    start_y: int
    branch_y: int
    end_y: int
    rung_number: int
    branch_id: str
    elements: List[LadderElement]
    children_branch_ids: List[str] = field(default_factory=list)  # IDs ONLY of child nested branches
    root_branch_id: Optional[str] = None
    parent_branch_id: Optional[str] = None  # For nested branches, this will track which branch this element belongs to
    branch_level: int = 0
    start_position: int = 0
    end_position: int = 0


class LadderCanvas(Canvas, Loggable):
    """Canvas for drawing ladder logic diagrams.

    Args:
        master: The parent widget.
        routine: Optional PLC routine to load into the canvas.
    """

    GRID_SIZE = 20
    RUNG_HEIGHT = 100
    CONTACT_WIDTH = 40
    CONTACT_HEIGHT = 30
    COIL_WIDTH = 40
    COIL_HEIGHT = 30
    BLOCK_WIDTH = 80  # default width of a function block
    BLOCK_HEIGHT = 40  # default height of a function block
    BRANCH_SPACING = 60
    ELEMENT_SPACING = 50  # spacing between elements on a rail
    MIN_WIRE_LENGTH = 50  # Minimum length of a wire connection before and after an element (e.g. -> ' --[]-- ')
    RAIL_X_LEFT = 40  # Position of the left side power rail
    RAIL_X_RIGHT = 1400  # Position of the right side power rail
    RUNG_START_Y = 50  # Starting Y position for the first rung
    RUNG_COMMENT_ASCII_Y_SIZE = 16  # Size of ascii chars for rung comments (Vertical / Y)
    RUNG_COMMENT_ASCII_X_SIZE = 6  # Size of ascii chars for rung comments (Horizontal / X)

    def __init__(
        self,
        master,
        routine: Optional[plc.Routine] = None
    ):
        Canvas.__init__(
            self,
            master,
            bg=THEME["background"]
        )
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
        self.bind('<ButtonRelease-1>', self._on_release)
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
        self._clear_hover_preview()
        self._mode = value
        self.config(cursor=self._get_cursor_for_mode(value))

    def _add_branch_connector_tooltip_content(
        self,
        frame: tk.Frame,
        element: LadderElement
    ) -> None:
        """Add specialized tooltip content for branch rail connectors.

        Args:
            frame: The frame to add the tooltip content to.
            element: The LadderElement representing the branch connector.
        """
        header_label = tk.Label(  # Branch connector header with icon
            frame,
            text="🔗 Branch Connector",
            background=THEME["tooltip_label_background"],
            font=(THEME["font"], 10, "bold"),
            foreground=THEME["tooltip_label_foreground"]
        )
        header_label.pack(anchor="w")

        type_label = tk.Label(  # Branch type indicator
            frame,
            text=f"Type: {self._determine_branch_connector_type(element)}",
            background=THEME["tooltip_label_background"],
            font=(THEME["font"], 9),
            foreground=THEME["tooltip_label_foreground"]
        )
        type_label.pack(anchor="w")

        if element.branch_id:
            id_label = tk.Label(  # Branch ID (always shown for connectors)
                frame,
                text=f"Branch ID: {element.branch_id}",
                background=THEME["tooltip_label_background"],
                font=(THEME["font"], 9),
                foreground="black"
            )
            id_label.pack(anchor="w")

        # Branch level
        level_label = tk.Label(
            frame,
            text=f"Nesting Level: {element.branch_level}",
            background=THEME["tooltip_label_background"],
            font=(THEME["font"], 8),
            foreground="gray"
        )
        level_label.pack(anchor="w")

        # Position in sequence
        pos_label = tk.Label(
            frame,
            text=f"Position: {element.position}",
            background=THEME["tooltip_label_background"],
            font=(THEME["font"], 8),
            foreground="gray"
        )
        pos_label.pack(anchor="w")

        # Enhanced branch information if available
        if element.branch_id and element.branch_id in self._branches:
            branch = self._branches[element.branch_id]

            # Separator
            ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=2)

            stats_label = tk.Label(  # Branch statistics
                frame,
                text="Branch Statistics:",
                background=THEME["tooltip_label_background"],
                font=(THEME["font"], 8, "bold"),
                foreground=THEME["tooltip_label_foreground"]
            )
            stats_label.pack(anchor="w")

            span_label = tk.Label(  # Span information
                frame,
                text=f"Span: Positions {branch.start_position} → {branch.end_position}",
                background=THEME["tooltip_label_background"],
                font=(THEME["font"], 8),
                foreground="gray"
            )
            span_label.pack(anchor="w")

            count_label = tk.Label(  # Element count
                frame,
                text=f"Contains: {len(branch.elements)} elements",
                background=THEME["tooltip_label_background"],
                font=(THEME["font"], 8),
                foreground="gray"
            )
            count_label.pack(anchor="w")

            if branch.children_branch_ids:
                child_label = tk.Label(  # Child branches
                    frame,
                    text=f"Child Branches: {len(branch.children_branch_ids)}",
                    background=THEME["tooltip_label_background"],
                    font=(THEME["font"], 8),
                    foreground="gray"
                )
                child_label.pack(anchor="w")

            if branch.parent_branch_id:
                parent_label = tk.Label(  # Parent branch
                    frame,
                    text=f"Parent: {branch.parent_branch_id}",
                    background=THEME["tooltip_label_background"],
                    font=(THEME["font"], 8),
                    foreground="gray"
                )
                parent_label.pack(anchor="w")

        # Add debug information if enabled
        if self._debug_mode:
            self._add_debug_tooltip_section(frame, element)

    def _add_branch_level(self, branch_id: str):
        """Add branch level to a specified branch."""
        if branch_id not in self._branches:
            self.log_error(f"Branch ID {branch_id} not found.")
            return

        branch = self._branches[branch_id]
        if not branch:
            raise ValueError(f"Branch with ID {branch_id} not found.")

        rung: plc.Rung = self._routine.rungs[branch.rung_number]
        if not rung:
            raise ValueError(f"Rung number {branch.rung_number} does not exist in the routine.")

        rung.insert_branch_level(branch.start_position)
        self._redraw_rung(branch.rung_number)

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

        # Root branch ID
        if element.root_branch_id:
            tk.Label(
                frame,
                text=f"Root Branch: {element.root_branch_id}",
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

        # Enhanced branch structure info
        if element.branch_id and element.branch_id in self._branches:
            branch = self._branches[element.branch_id]

            # Add separator for branch structure details
            ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=2)

            tk.Label(
                frame,
                text="Branch Structure:",
                background="#fffacd",
                font=("Arial", 8, "bold"),
                foreground="darkgreen"
            ).pack(anchor="w")

            # Branch coordinates
            tk.Label(
                frame,
                text=f"Start: ({branch.start_x}, {branch.start_y})",
                background="#fffacd",
                font=("Arial", 7),
                foreground="darkgreen"
            ).pack(anchor="w")

            tk.Label(
                frame,
                text=f"End: ({branch.end_x}, {branch.end_y})",
                background="#fffacd",
                font=("Arial", 7),
                foreground="darkgreen"
            ).pack(anchor="w")

            tk.Label(
                frame,
                text=f"Branch Y: {branch.branch_y}",
                background="#fffacd",
                font=("Arial", 7),
                foreground="darkgreen"
            ).pack(anchor="w")

            # Position range
            tk.Label(
                frame,
                text=f"Positions: {branch.start_position} → {branch.end_position}",
                background="#fffacd",
                font=("Arial", 7),
                foreground="darkgreen"
            ).pack(anchor="w")

            # Element count in branch
            tk.Label(
                frame,
                text=f"Elements in Branch: {len(branch.elements)}",
                background="#fffacd",
                font=("Arial", 7),
                foreground="darkgreen"
            ).pack(anchor="w")

            # Child branches
            if branch.children_branch_ids:
                tk.Label(
                    frame,
                    text=f"Child Branches: {len(branch.children_branch_ids)}",
                    background="#fffacd",
                    font=("Arial", 7),
                    foreground="darkgreen"
                ).pack(anchor="w")

                # List child branch IDs (truncated if too many)
                child_list = ", ".join(branch.children_branch_ids[:3])
                if len(branch.children_branch_ids) > 3:
                    child_list += f" +{len(branch.children_branch_ids) - 3} more"

                tk.Label(
                    frame,
                    text=f"Children: {child_list}",
                    background="#fffacd",
                    font=("Arial", 7),
                    foreground="darkgreen"
                ).pack(anchor="w")

            # Parent branch info
            if branch.parent_branch_id:
                tk.Label(
                    frame,
                    text=f"Parent: {branch.parent_branch_id}",
                    background="#fffacd",
                    font=("Arial", 7),
                    foreground="darkgreen"
                ).pack(anchor="w")

            # Branch nesting information
            if self._routine and element.rung_number < len(self._routine.rungs):
                rung = self._routine.rungs[element.rung_number]
                nesting_level = rung.get_branch_internal_nesting_level(
                    element.position) if hasattr(rung, 'get_branch_internal_nesting_level') else 0

                tk.Label(
                    frame,
                    text=f"Nesting Level: {nesting_level}",
                    background="#fffacd",
                    font=("Arial", 7),
                    foreground="darkgreen"
                ).pack(anchor="w")

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

    def _add_debug_overlay_for_any_element(self, element: LadderElement):
        """Add debug visual overlay for any element type with enhanced branch connector support."""

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
            width=2,
            dash=(2, 2),
            tags="debug_overlay"
        )
        self._debug_overlays.append(bounds_id)

        # Enhanced debug info for branch connectors
        if element.element_type == 'branch_rail_connector':
            # Show branch connector details
            if element.branch_id:
                # Branch ID label (shortened)
                branch_id_short = element.branch_id[-8:] if len(element.branch_id) > 8 else element.branch_id
                branch_text_id = self.create_text(
                    element.x + element.width // 2,
                    element.y - 20,
                    text=f"ID:{branch_id_short}",
                    font=("Arial", 6, "bold"),
                    fill=color,
                    anchor="center",
                    tags="debug_overlay"
                )
                self._debug_overlays.append(branch_text_id)

            # Position indicator
            pos_text_id = self.create_text(
                element.x + element.width // 2,
                element.y + element.height + 12,
                text=f"Pos:{element.position}",
                font=("Arial", 6),
                fill=color,
                anchor="center",
                tags="debug_overlay"
            )
            self._debug_overlays.append(pos_text_id)

            # Branch level indicator
            level_text_id = self.create_text(
                element.x - 15,
                element.y + element.height // 2,
                text=f"L{element.branch_level}",
                font=("Arial", 6),
                fill=color,
                anchor="center",
                tags="debug_overlay"
            )
            self._debug_overlays.append(level_text_id)

            # Draw branch structure lines if in branches dict
            if element.branch_id and element.branch_id in self._branches:
                branch = self._branches[element.branch_id]

                # Draw branch bounds rectangle
                branch_bounds_id = self.create_rectangle(
                    branch.start_x - 5, branch.start_y - 5,
                    branch.end_x + 5, branch.end_y + 5,
                    outline=color,
                    width=1,
                    dash=(4, 4),
                    tags="debug_overlay"
                )
                self._debug_overlays.append(branch_bounds_id)

                # Draw branch centerline
                centerline_id = self.create_line(
                    branch.start_x, branch.branch_y,
                    branch.end_x, branch.branch_y,
                    fill=color,
                    width=1,
                    dash=(6, 2),
                    tags="debug_overlay"
                )
                self._debug_overlays.append(centerline_id)

        # Standard debug info for instruction elements
        elif element.element_type in ['contact', 'coil', 'block']:
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

        # For other branch elements, show branch ID
        elif element.element_type in ['branch_start', 'branch_end', 'branch_next']:
            if element.branch_id:
                branch_text_id = self.create_text(
                    element.x + element.width // 2,
                    element.y - 12,
                    text=f"B:{element.branch_id[-4:] if len(element.branch_id) > 4 else element.branch_id}",
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

    def _add_debug_overlay_for_any_branch(self, branch: LadderBranch):
        """Add debug visual overlay for branch structures with detailed information."""
        # Color coding for branches
        colors = ['orange', 'purple', 'brown', 'pink', 'gray']
        color = colors[branch.branch_level % len(colors)]

        # Branch bounds rectangle
        bounds_id = self.create_rectangle(
            branch.start_x, branch.start_y,
            branch.end_x, branch.end_y,
            outline=color,
            width=2,
            dash=(4, 4),
            tags="debug_overlay"
        )
        self._debug_overlays.append(bounds_id)

        # Branch ID label
        branch_id_short = branch.branch_id[-8:] if len(branch.branch_id) > 8 else branch.branch_id
        id_text_id = self.create_text(
            (branch.start_x + branch.end_x) // 2,
            branch.start_y - 10,
            text=f"Branch: {branch_id_short}",
            font=("Arial", 7, "bold"),
            fill=color,
            anchor="center",
            tags="debug_overlay"
        )
        self._debug_overlays.append(id_text_id)

        # Branch level indicator
        level_text_id = self.create_text(
            branch.start_x - 20,
            (branch.start_y + branch.end_y) // 2,
            text=f"Lvl {branch.branch_level}",
            font=("Arial", 6),
            fill=color,
            anchor="center",
            tags="debug_overlay"
        )
        self._debug_overlays.append(level_text_id)

        # Position range
        pos_text_id = self.create_text(
            (branch.start_x + branch.end_x) // 2,
            branch.end_y + 15,
            text=f"Pos: {branch.start_position}-{branch.end_position}",
            font=("Arial", 6),
            fill=color,
            anchor="center",
            tags="debug_overlay"
        )
        self._debug_overlays.append(pos_text_id)

        # Element count
        element_count_id = self.create_text(
            branch.end_x + 10,
            (branch.start_y + branch.end_y) // 2,
            text=f"{len(branch.elements)} elem",
            font=("Arial", 6),
            fill=color,
            anchor="w",
            tags="debug_overlay"
        )
        self._debug_overlays.append(element_count_id)

        # Draw connection lines to child branches
        if branch.children_branch_ids:
            for child_id in branch.children_branch_ids:
                if child_id in self._branches:
                    child_branch = self._branches[child_id]
                    # Draw line from parent to child
                    connection_line_id = self.create_line(
                        (branch.start_x + branch.end_x) // 2, branch.branch_y,
                        (child_branch.start_x + child_branch.end_x) // 2, child_branch.branch_y,
                        fill=color,
                        width=1,
                        dash=(8, 4),
                        tags="debug_overlay"
                    )
                    self._debug_overlays.append(connection_line_id)

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
        ladder_element.root_branch_id = rung_element.root_branch_id
        ladder_element.rung_number = rung_number
        ladder_element.instruction = rung_element.instruction
        ladder_element.position = rung_element.position

    def _calculate_insertion_coordinates(
        self,
        rung_number: int, insertion_position: int,
        branch_level: int = 0,
        branch_id: Optional[str] = None
    ) -> tuple[int, int]:
        """Calculate the exact coordinates where an element would be inserted."""
        if not branch_id:
            branch_level = 0  # we only use the ID
            rung_y_pos = self._rung_y_positions[rung_number]
            comment_height = self._get_rung_comment_height(self._routine.rungs[rung_number])
            center_y = rung_y_pos + self.RUNG_HEIGHT // 2 + comment_height
            default_start = self.RAIL_X_LEFT + (self.ELEMENT_SPACING // 2), center_y
        else:
            branch = self._branches.get(branch_id, None)
            if not branch:
                raise ValueError(f"Branch with ID {branch_id} not found.")
            center_y = branch.branch_y + 5
            default_start = branch.start_x + (self.ELEMENT_SPACING // 2), center_y

        # Get existing elements in this context
        rung_elements = self._get_rung_ladder_elements(rung_number, branch_level, branch_id)
        last_position = max((e.position for e in rung_elements), default=-1)

        if not rung_elements:
            return default_start
        elif insertion_position == 0:
            return default_start
        elif insertion_position > last_position:
            last_element = rung_elements[-1]
            return last_element.x + last_element.width + self.ELEMENT_SPACING + self.MIN_WIRE_LENGTH, center_y
        else:
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
            return insert_x, center_y

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
            start_y=center_y + self.BRANCH_SPACING,
            branch_y=center_y + self.BRANCH_SPACING,
            end_y=center_y + self.BRANCH_SPACING,
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

    def _create_ladder_branch(self, ladder_element: LadderElement,
                              element: plc.RungElement, rung_number: int, parent_branch_id: Optional[str] = None) -> LadderBranch:
        return LadderBranch(
            start_x=ladder_element.x,
            end_x=ladder_element.x + 50,  # this will be updated when the branch closes
            main_y=self._rung_y_positions[rung_number],
            start_y=ladder_element.y - self.BRANCH_SPACING // 2,
            branch_y=ladder_element.y,
            end_y=ladder_element.y + ladder_element.height + self.BRANCH_SPACING // 2,  # This will be updated when the branch closes
            rung_number=rung_number,
            branch_id=element.branch_id,
            root_branch_id=element.root_branch_id,
            parent_branch_id=parent_branch_id,
            branch_level=element.branch_level,
            elements=[],
            start_position=element.position,
            end_position=element.position
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

    def _clear_rung_visuals(self, rung_number: int):
        """Clear all visual elements for a specific rung."""
        # Remove canvas items
        self.delete(f"rung_{rung_number}")
        self.delete(f"rung_{rung_number}_comment")
        self.delete(f"rung_{rung_number}_instruction")
        self.delete(f"rung_{rung_number}_wire")
        self.delete(f"rung_{rung_number}_branch")
        self.delete(f"rung_{rung_number}_branch_marker")
        self.delete(f"rung_{rung_number}_branch_start")
        self.delete(f"rung_{rung_number}_branch_end")
        self.delete(f"rung_{rung_number}_branch_next")

        # Remove elements from our tracking list
        elements_to_remove = [e for e in self._elements
                              if e.rung_number == rung_number]

        for element in elements_to_remove:
            self._elements.remove(element)

        # Remove branches for this rung
        branches_to_remove = [bid for bid, branch in self._branches.items()
                              if branch.rung_number == rung_number]

        for branch_id in branches_to_remove:
            del self._branches[branch_id]

    def _copy_element(self, element: LadderElement):
        """Copy an element (placeholder)."""
        self._show_status(f"Copied element: {element.text}")

    def _delete_branch(self, branch_id: str):
        """Delete a branch and all its elements."""
        if branch_id not in self._branches:
            raise ValueError(f"Branch with ID {branch_id} not found.")

        branch = self._branches[branch_id]
        rung = self._routine.rungs[branch.rung_number] if self._routine else None
        if not rung:
            raise ValueError(f"Rung {branch.rung_number} not found in routine.")
        rung.remove_branch(branch_id)
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

    def _determine_branch_connector_type(self, element: LadderElement) -> str:
        """Determine the type of branch connector based on its position and context."""
        if not element.branch_id or element.branch_id not in self._branches:
            return "Unknown"

        branch = self._branches[element.branch_id]

        if element.position == branch.start_position:
            return "Branch Start"
        elif element.position == branch.end_position:
            return "Branch End"
        elif element.position > branch.start_position and element.position < branch.end_position:
            return "Branch Node"
        else:
            return "Branch Point"

    def _draw_block(
        self,
        instruction: plc.LogixInstruction,
        x: int,
        center_y: int,
        rung_number: int
    ) -> LadderElement:
        """Draw a function block instruction centered on the rung."""
        top_y = center_y - self.BLOCK_HEIGHT // 2

        # First, find the length of operands
        operand_count = len(instruction.operands) if instruction.operands else 0
        # This extra height is for displaying each operand individually
        bottom_y = center_y + self.BLOCK_HEIGHT // 2 + (operand_count * self.RUNG_COMMENT_ASCII_Y_SIZE)

        rect_id = self.create_rectangle(  # Instruction rectangle
            x,
            top_y,
            x + self.BLOCK_WIDTH,
            bottom_y,
            outline=THEME["ladder_rung_color"],
            fill=THEME["background"],
            width=THEME["ladder_line_width"],
            tags=f"rung_{rung_number}_instruction"
        )

        self.create_text(  # Instruction name text
            x + self.BLOCK_WIDTH // 2,
            center_y - 10,
            text=instruction.instruction_name,
            font=(THEME["font"], 10, 'bold'),
            tags=f"rung_{rung_number}_instruction"
        )

        if instruction.operands:
            operands_text = [op.meta_data for op in instruction.operands]
        else:
            operands_text = ""

        if len(operands_text) != len(instruction.operands):
            raise ValueError(
                f"Operands length mismatch: {len(operands_text)} vs {len(instruction.operands)}"
            )

        for text in operands_text:
            self.create_text(  # Each operand text
                x + self.BLOCK_WIDTH // 2,
                center_y + 5 + (operands_text.index(text) * self.RUNG_COMMENT_ASCII_Y_SIZE),
                text=text,
                font=(THEME["font"], 8),
                fill=THEME["foreground"],
                tags=f"rung_{rung_number}_instruction"
            )

        self.create_line(  # Left connecting wire
            x - 10,
            center_y,
            x, center_y,
            fill=THEME["ladder_rung_color"],
            width=THEME["ladder_line_width"],
            tags=f"rung_{rung_number}_wire"
        )

        self.create_line(  # Right connecting wire
            x + self.BLOCK_WIDTH,
            center_y,
            x + self.BLOCK_WIDTH + 10,
            center_y,
            fill=THEME["ladder_rung_color"],
            width=THEME["ladder_line_width"],
            tags=f"rung_{rung_number}_wire"
        )

        return LadderElement(
            element_type='block',
            x=x,
            y=top_y,
            width=self.BLOCK_WIDTH,
            height=bottom_y - top_y,
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
            fill='lightcoral', outline='red', width=THEME["ladder_line_width"],
            tags="hover_preview"
        )

        # Add preview branch line
        branch_y = y + self.BRANCH_SPACING
        self.create_line(
            x, y, x, branch_y,
            fill='red', width=THEME["ladder_line_width"], dash=(3, 3),
            tags="hover_preview"
        )

        # Add preview horizontal branch line
        self.create_line(
            x, branch_y, x - 50, branch_y,
            fill='red', width=THEME["ladder_line_width"], dash=(3, 3),
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
            fill='lightgreen', outline='green', width=THEME["ladder_line_width"],
            tags="hover_preview"
        )

        # Add preview branch line
        branch_y = y + self.BRANCH_SPACING
        self.create_line(
            x, y, x, branch_y,
            fill='green', width=THEME["ladder_line_width"], dash=(3, 3),
            tags="hover_preview"
        )

        # Add preview horizontal branch line
        self.create_line(
            x, branch_y, x + 50, branch_y,
            fill='green', width=THEME["ladder_line_width"], dash=(3, 3),
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
            fill=THEME["background"], outline=THEME["ladder_rung_color"], width=THEME["ladder_line_width"], tags=tags
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
            fill=THEME["ladder_rung_color"], width=THEME["ladder_line_width"],
            dash=(3, 3) if dashed_line else None,
            tags=tags
        )

    def _draw_branch_left_rail(self,
                               x: int,
                               y: int,
                               element: plc.RungElement,
                               rung_number: int,
                               tags: str = None,
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
        ladder_element = self._draw_branch_rail_connector(x, y, tags)

        # Add text
        if branch_text:
            self.create_text(
                x,
                y - 15,
                text=branch_text,
                font=(THEME["font"], 8),
                fill=THEME["foreground"], tags=tags
            )

        self._assm_ladder_element_from_rung_element(
            ladder_element,
            element,
            rung_number
        )
        return ladder_element

    def _draw_branch_next_rail(self,
                               x: int,
                               y: int,
                               nesting_level: Optional[int] = 0,
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
        # Add branch line
        branch_y = y - (self.BRANCH_SPACING * (nesting_level + 1) - 5)
        self._draw_branch_rail_line(x, y, x, branch_y, tags=tags)
        # Add horizontal branch line
        self._draw_branch_rail_line(x, y, x + 50, y, tags=tags)
        return self._draw_branch_rail_connector(x, y, tags)

    def _draw_branch_right_rail(self,
                                x: int,
                                y: int,
                                nesting_level: Optional[int] = 0,
                                rung_number: int = 0,
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
        self._draw_branch_rail_line(x, y, x, branch_y, tags=tags, dashed_line=dashed_line)

        # Add preview horizontal branch line
        self._draw_branch_rail_line(x, branch_y, x - 50, branch_y,
                                    tags=tags, dashed_line=dashed_line)

        # Draw branch end indicator last to ensure it appears on top
        ladder_element = self._draw_branch_rail_connector(x, y, tags)

        # Add text
        if branch_text:
            self.create_text(
                x, y + 15,
                text=branch_text, font=(THEME["font"], 8),
                fill=THEME["foreground"], tags=tags
            )

        self._assm_ladder_element_from_rung_element(
            ladder_element,
            ladder_element,
            rung_number
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
            outline=THEME["ladder_rung_color"], fill=THEME["background"], width=THEME["ladder_line_width"],
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
            width=THEME["ladder_line_width"], tags=f"rung_{rung_number}_wire"
        )
        # Right connecting wire (to power rail if this is the last element)
        self.create_line(
            x + self.COIL_WIDTH, wire_y,
            x + self.COIL_WIDTH + 10, wire_y,
            fill=THEME["ladder_rung_color"],  # Use theme color for wires
            width=THEME["ladder_line_width"], tags=f"rung_{rung_number}_wire"
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

    def _draw_contact(
        self,
        instruction: plc.LogixInstruction,
        x: int,
        center_y: int,
        rung_number: int
    ) -> LadderElement:
        """Draw a contact instruction centered on the rung."""
        # Determine contact type
        is_normally_closed = instruction.instruction_name.lower() == 'xio'

        # Calculate top and bottom Y positions for centering
        top_y = center_y - self.CONTACT_HEIGHT // 2
        bottom_y = center_y + self.CONTACT_HEIGHT // 2

        rect_id = self.create_rectangle(  # Draw contact symbol
            x,
            top_y,
            x + self.CONTACT_WIDTH,
            bottom_y,
            outline=THEME["ladder_rung_color"],
            fill=THEME["background"],
            width=THEME["ladder_line_width"],
            tags=f"rung_{rung_number}_instruction"
        )
        # Draw the contact type indicator
        if is_normally_closed:
            self.create_line(  # Diagonal line for normally closed
                x + 5,
                top_y + 5,
                x + self.CONTACT_WIDTH - 5,
                bottom_y - 5,
                fill=THEME["ladder_rung_color"],
                width=THEME["ladder_line_width"],
                tags=f"rung_{rung_number}_instruction"
            )
        else:
            bar_top = top_y + 5
            bar_bottom = bottom_y - 5
            self.create_line(  # Vertical lines for normally open
                x + 10,
                bar_top,
                x + 10,
                bar_bottom,
                fill=THEME["ladder_rung_color"],
                width=THEME["ladder_line_width"],
                tags=f"rung_{rung_number}_instruction"
            )
            self.create_line(
                x + self.CONTACT_WIDTH - 10,
                bar_top,
                x + self.CONTACT_WIDTH - 10,
                bar_bottom,
                fill=THEME["ladder_rung_color"],
                width=THEME["ladder_line_width"],
                tags=f"rung_{rung_number}_instruction"
            )

        # Draw connecting wires to power rail (horizontal lines at rung center)
        wire_y = center_y
        # Left connecting wire (from power rail to contact)
        self.create_line(
            x - 10,
            wire_y,  # Start 10 pixels before contact
            x,
            wire_y,       # End at contact left edge
            fill=THEME["ladder_rung_color"],
            # Use theme color for wires
            width=THEME["ladder_line_width"],
            tags=f"rung_{rung_number}_wire"
        )
        # Right connecting wire (from contact to next element)
        self.create_line(
            x + self.CONTACT_WIDTH, wire_y,
            x + self.CONTACT_WIDTH + 10, wire_y,
            fill=THEME["ladder_rung_color"],  # Use theme color for wires
            width=THEME["ladder_line_width"], tags=f"rung_{rung_number}_wire"
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

        prev_element = self._get_previous_element(element)
        if prev_element:
            # Draw wire from previous element to this instruction
            self.create_line(
                prev_element.x + prev_element.width,
                y,
                x,
                y,
                fill=THEME["ladder_rung_color"],
                width=THEME["ladder_line_width"],
                tags=f"rung_{rung_number}_wire"
            )

        # Add debug overlays if debug mode is enabled
        if self._debug_mode and element:
            self._add_debug_overlay_for_any_element(element)

        return element

    def _draw_instruction_texts(
        self,
        instruction: plc.LogixInstruction,
        x: int,
        y: int,
        rung_number: int,
        element_width: int
    ):
        alias = False
        # Optionally add alias information above contact
        if instruction.operands[0].as_aliased != instruction.operands[0].meta_data:
            self.create_text(
                x + element_width // 2,
                y - 10,
                text=f'<{instruction.operands[0].as_aliased}>',
                fill=THEME["instruction_alias"],
                font=(THEME["font"], 8,),
                tags=f"rung_{rung_number}_instruction"
            )
            alias = True

        # Add operand text above the contact
        operand = instruction.operands[0].meta_data if instruction.operands else "???"
        text_length = len(operand) * self.RUNG_COMMENT_ASCII_X_SIZE
        start_x = x + element_width // 2 - text_length // 2
        end_x = x + element_width // 2 + text_length // 2

        # Creating a bound rectangle for the operand text
        text_box = self.create_rectangle(
            start_x,
            y - (25 if alias is False else 35) + 2,
            end_x,
            y + self.RUNG_COMMENT_ASCII_Y_SIZE - (25 if alias is False else 35) + 2,
            outline=THEME["background"],
            fill=THEME["background"],
            width=1,
            tags=f"rung_{rung_number}_instruction"
        )
        self._elements.append(
            LadderElement(
                element_type='text_box',
                x=start_x,
                y=y - (25 if alias is False else 35) + 2,
                width=text_length,
                height=self.RUNG_COMMENT_ASCII_Y_SIZE,
                canvas_id=text_box,
                rung_number=rung_number,
                instruction=instruction,
                custom_outline=THEME["background"],
            ))

        self.create_text(
            x + element_width // 2,
            y - (15 if alias is False else 25),
            fill=THEME["foreground"],
            text=operand,
            font=(THEME["font"], 8,),
            tags=f"rung_{rung_number}_instruction"
        )

        # return the operand text for further use
        return operand

    def _draw_hover_preview(self, x: int, y: int, mode: LadderEditorMode):
        """Draw a hover preview indicator."""
        if mode == LadderEditorMode.INSERT_CONTACT or mode == LadderEditorMode.DRAG_ELEMENT:
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
        elif mode == LadderEditorMode.INSERT_BRANCH:
            # Small oval preview for branch start
            self._hover_preview_id = self.create_oval(
                x - 5, y - 5, x + 5, y + 5,
                outline='blue', fill='lightblue', stipple='gray50',
                width=2, tags="hover_preview"
            )
        elif mode == LadderEditorMode.CONNECT_BRANCH:
            # Small oval preview for branch end
            self._hover_preview_id = self.create_oval(
                x - 5, y - 5, x + 5, y + 5,
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
            raise ValueError("No routine set for drawing.")

        if not self._routine.rungs:
            self._routine.add_rung(plc.Rung(controller=self._routine.controller, routine=self._routine))

        y_pos = self.RUNG_START_Y
        for i, rung in enumerate(self._routine.rungs):
            self._elements.append(self._draw_rung(rung, i, y_pos))
            y_pos += self._get_rung_height(rung.number)

        # Update scroll region
        self.configure(scrollregion=self.bbox("all"))

    def _draw_rung(
        self,
        rung: plc.Rung,
        rung_number: int,
        y_pos: int
    ) -> LadderElement:
        """Draw a single rung using the enhanced PLC data structure.
        """
        self._rung_y_positions[rung_number] = y_pos
        branch_depth = rung.get_max_branch_depth()
        rung_height = self.RUNG_HEIGHT + (self.BRANCH_SPACING * branch_depth)
        rung_rail_height = rung_height

        rung_comment = self._draw_rung_comment(rung, y_pos)
        if rung_comment:
            self._elements.append(rung_comment)
            rung_height += rung_comment.height
            rung_start_y = y_pos + rung_comment.height
        else:
            rung_start_y = y_pos

        # Create rectangle for rung number
        rect_id = self.create_rectangle(
            0,
            y_pos,
            self.RAIL_X_LEFT,
            y_pos + rung_height,
            outline=THEME["background"],
            fill=THEME["background"],
            tags=f"rung_{rung_number}"
        )

        # Draw rung number
        self.create_text(
            15,
            rung_start_y + rung_rail_height // 2,
            text=str(rung_number),
            anchor='w',
            font=('Roboto', 10),
            tag=f"rung_{rung_number}",
            fill=THEME["foreground"]
        )

        # Draw power rails
        self.create_line(  # Left power rail
            self.RAIL_X_LEFT,
            rung_start_y,
            self.RAIL_X_LEFT,
            rung_start_y + rung_rail_height,
            width=3,
            tags=f"rung_{rung_number}",
            fill=THEME["ladder_rung_color"]
        )

        self.create_line(  # Right power rail
            self.RAIL_X_RIGHT,
            rung_start_y,
            self.RAIL_X_RIGHT,
            rung_start_y + rung_rail_height,
            width=3,
            tags=f"rung_{rung_number}",
            fill=THEME["ladder_rung_color"]
        )

        center_y = rung_start_y + self.RUNG_HEIGHT // 2

        self.create_line(  # Main power line (rung)
            self.RAIL_X_LEFT,
            center_y,
            self.RAIL_X_RIGHT,
            center_y,
            width=2,
            tags=f"rung_{rung_number}",
            fill=THEME["ladder_rung_color"]
        )

        if rung and rung.rung_sequence:
            self._draw_rung_sequence(rung)

        return LadderElement(
            element_type='rung',
            x=0, y=y_pos,
            width=self.RAIL_X_LEFT, height=rung_height,
            canvas_id=rect_id,
            rung_number=rung_number,
            custom_outline=THEME["background"],
            custom_fill=THEME["background"],
        )

    def _draw_rung_comment(
        self,
        rung: plc.Rung,
        y_pos: int
    ) -> LadderElement:
        """Draw the comment for a rung."""
        if not rung.comment:
            return None

        comment_height = self._get_rung_comment_height(rung)

        rect_id = self.create_rectangle(
            self.RAIL_X_LEFT,
            y_pos,
            self.RAIL_X_RIGHT,
            y_pos + comment_height,
            outline=THEME["comment_background"],
            fill=THEME["comment_background"],
            tags=f"rung_{rung.number}_comment"
        )
        self.create_text(
            self.RAIL_X_LEFT,
            y_pos,
            text=rung.comment,
            anchor='nw',
            font=(THEME["font"], 10),
            tags=f"rung_{rung.number}_comment",
            fill=THEME["comment_foreground"],
        )

        return LadderElement(
            element_type='rung_comment',
            x=self.RAIL_X_LEFT,
            y=y_pos,
            width=self.RAIL_X_RIGHT - self.RAIL_X_LEFT,
            height=comment_height,
            canvas_id=rect_id,
            rung_number=int(rung.number),
            custom_outline=THEME["comment_background"],
            custom_fill=THEME["comment_background"],
        )

    def _draw_rung_sequence(
            self,
            rung: plc.Rung) -> None:
        """Draw rung using the new sequence structure with proper spacing.
        Args:
            rung: The PLC rung to draw
        """
        branch_tracking: list[dict] = []

        for element in rung.rung_sequence:
            if element.element_type == plc.RungElementType.INSTRUCTION:
                self._draw_rung_sequence_instruction(element)

            elif element.element_type == plc.RungElementType.BRANCH_START:
                self._draw_rung_sequence_branch_start(
                    element,
                    rung,
                    branch_tracking,
                )

            elif element.element_type == plc.RungElementType.BRANCH_NEXT:
                self._draw_rung_sequence_branch_next(
                    element,
                    rung,
                    branch_tracking,
                )

            elif element.element_type == plc.RungElementType.BRANCH_END:
                self._draw_rung_sequence_branch_end(
                    element,
                    branch_tracking,
                )

    def _draw_rung_sequence_branch_end(
            self,
            element: plc.RungElement,
            branch_tracking: list[dict],
    ):
        rung_number = int(element.rung_number)
        if rung_number is None:
            raise ValueError("Rung number is required for drawing sequence instruction.")

        if not branch_tracking:
            raise ValueError("Branch end found without a matching branch start.")

        branch = branch_tracking.pop()
        if not branch:
            raise ValueError("Branch end found without a valid branch.")

        x, y = self._get_element_x_y_sequence_spacing(element)

        ladder_element = self._draw_branch_right_rail(
            x,
            y,
            branch['branch_nesting'],
            rung_number,
            tags=f"rung_{rung_number}_branch_end"
        )
        # This needs to be set to get all the proper instructions on this root branch
        parent_branch = self._branches.get(branch['branch_id'], None)
        if not parent_branch:
            raise ValueError(f"Parent branch with ID {branch['branch_id']} not found in branches.")
        self._assm_ladder_element_from_rung_element(ladder_element, element, rung_number)
        ladder_element.root_branch_id = parent_branch.root_branch_id
        ladder_element.branch_level = parent_branch.branch_level
        ladder_element.branch_id = parent_branch.branch_id

        self._elements.append(ladder_element)
        parent_branch.end_x = ladder_element.x + ladder_element.width
        parent_branch.end_position = element.position

        self._reassign_child_branch_attrs(parent_branch)

    def _draw_rung_sequence_branch_start(
            self,
            element: plc.RungElement,
            rung: plc.Rung,
            branch_tracking: list[dict],
    ):
        rung_number = int(element.rung_number)
        if rung_number is None:
            raise ValueError("Rung number is required for drawing sequence instruction.")

        x, y = self._get_element_x_y_sequence_spacing(element)
        nesting_level = rung.get_branch_internal_nesting_level(element.position)
        ladder_element = self._draw_branch_left_rail(
            x,
            y,
            element,
            rung_number,
            tags=f"rung_{rung_number}_branch_start"
        )

        branch_element = self._create_ladder_branch(
            ladder_element,
            element,
            rung_number
        )

        self._elements.append(ladder_element)
        self._branches[element.branch_id] = branch_element
        branch_tracking.append({
            'branch_id': element.branch_id,
            'branch_element': ladder_element,
            'branch_nesting': nesting_level
        })

    def _draw_rung_sequence_instruction(
            self,
            element: plc.RungElement,
    ) -> None:
        rung_number = int(element.rung_number)
        if rung_number is None:
            raise ValueError("Rung number is required for drawing sequence instruction.")

        x, y = self._get_element_x_y_sequence_spacing(element)
        if element.branch_id:
            parent_branch = self._branches.get(element.branch_id, None)
            if not parent_branch:
                raise ValueError(f"Parent branch with ID {element.branch_id} not found in branches.")
            y = parent_branch.branch_y + 5

        ladder_element = self._draw_instruction(element.instruction, x, y, rung_number)
        self._assm_ladder_element_from_rung_element(ladder_element, element, rung_number)
        self._elements.append(ladder_element)

    def _draw_rung_sequence_branch_next(
        self,
        element: plc.RungElement,
        rung: plc.Rung,
        branch_tracking: list[dict]
    ):
        rung_number = int(element.rung_number)
        if rung_number is None:
            raise ValueError("Rung number is required for drawing sequence instruction.")
        matching_branch = self._branches[branch_tracking[-1]['branch_id']] if branch_tracking else None
        if not matching_branch:
            raise ValueError(f"Branch with ID {element.root_branch_id} not found in branches.")
        if matching_branch.branch_id not in element.branch_id:
            raise ValueError(f"Branch ID mismatch: {matching_branch.branch_id} != {element.branch_id}")
        branch_depth = rung.get_branch_internal_nesting_level(matching_branch.start_position)
        x, y = matching_branch.start_x + 5, matching_branch.branch_y + \
            (branch_depth * self.BRANCH_SPACING) + (self.BRANCH_SPACING * element.branch_level) + 5
        ladder_element = self._draw_branch_next_rail(x, y,
                                                     nesting_level=branch_depth,
                                                     tags=f"rung_{rung_number}_branch_next")
        self._assm_ladder_element_from_rung_element(ladder_element, element, rung_number)
        branch_element = self._create_ladder_branch(ladder_element, element, rung_number,
                                                    parent_branch_id=matching_branch.branch_id)
        self._elements.append(ladder_element)
        self._branches[element.branch_id] = branch_element
        matching_branch.children_branch_ids.append(element.branch_id)

    def _edit_instruction(self, instruction: plc.LogixInstruction):
        """Edit an instruction (placeholder - implement instruction editor dialog)."""
        self._show_status(f"Edit instruction: {instruction.meta_data}")

    def _edit_rung_comment(self, rung_number: int):
        """Edit the comment for a rung using a popup dialog.

        Args:
            rung_number: The rung number to edit the comment for
        """
        if not self._routine or rung_number >= len(self._routine.rungs):
            self._show_status(f"Invalid rung number: {rung_number}")
            return

        rung = self._routine.rungs[rung_number]
        current_comment = rung.comment if rung.comment else ""

        # Create popup dialog
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Comment - Rung {rung_number}")
        dialog.geometry("700x500")
        dialog.transient(self)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Header label
        header_frame = tk.Frame(dialog)
        header_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(
            header_frame,
            text=f"Rung {rung_number} Comment:",
            font=('Arial', 12, 'bold')
        ).pack(anchor='w')

        # Text widget with scrollbar
        text_frame = tk.Frame(dialog)
        text_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Create text widget
        text_widget = tk.Text(
            text_frame,
            wrap='word',
            font=('Consolas', 10),
            bg='white',
            fg='black',
            insertbackground='black'
        )

        # Scrollbar
        scrollbar = tk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        # Pack text widget and scrollbar
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Insert current comment
        text_widget.insert('1.0', current_comment)
        text_widget.focus_set()

        # Button frame
        button_frame = tk.Frame(dialog)
        button_frame.pack(fill='x', padx=10, pady=10)

        def on_accept():
            """Save the comment and close dialog."""
            new_comment = text_widget.get('1.0', 'end-1c')  # Get text without trailing newline

            # Update the rung comment
            rung.comment = new_comment

            # Redraw the rung to show the updated comment
            self._redraw_rung(rung_number)

            # Update status
            if new_comment.strip():
                self._show_status(f"Updated comment for rung {rung_number}")
            else:
                self._show_status(f"Removed comment from rung {rung_number}")

            dialog.destroy()

        def on_cancel():
            """Close dialog without saving."""
            dialog.destroy()

        def on_clear():
            """Clear the comment text."""
            text_widget.delete('1.0', 'end')
            text_widget.focus_set()

        # Buttons
        tk.Button(
            button_frame,
            text="Accept",
            command=on_accept,
            width=10,
            bg='lightgreen'
        ).pack(side='left', padx=5)

        tk.Button(
            button_frame,
            text="Cancel",
            command=on_cancel,
            width=10,
            bg='lightcoral'
        ).pack(side='left', padx=5)

        tk.Button(
            button_frame,
            text="Clear",
            command=on_clear,
            width=10,
            bg='lightyellow'
        ).pack(side='left', padx=5)

        # Character count label
        char_count_label = tk.Label(
            button_frame,
            text=f"Characters: {len(current_comment)}",
            font=('Arial', 8),
            fg='gray'
        )
        char_count_label.pack(side='right', padx=5)

        def update_char_count(event=None):
            """Update character count as user types."""
            count = len(text_widget.get('1.0', 'end-1c'))
            char_count_label.config(text=f"Characters: {count}")

        # Bind character count update
        text_widget.bind('<KeyRelease>', update_char_count)
        text_widget.bind('<Button-1>', update_char_count)

        # Keyboard shortcuts
        dialog.bind('<Control-Return>', lambda e: on_accept())
        dialog.bind('<Escape>', lambda e: on_cancel())

        # Handle window close button
        dialog.protocol("WM_DELETE_WINDOW", on_cancel)

        # Wait for dialog to close
        dialog.wait_window()

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
            return rung_elements[-1].position

        # Determine if we should insert before or after the closest element
        element_center_x = closest_element.x + closest_element.width // 2

        if x < element_center_x:
            # Insert before this element
            if closest_element_index > 0:
                return rung_elements[closest_element_index-1].position+1
            else:
                return rung_elements[closest_element_index].position
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

    def _find_operand_at_position(self, x: float, y: float) -> Optional[LadderOperand]:
        """Find operand at the given canvas coordinates."""
        for element in self._elements:
            if element.element_type in ['contact', 'coil', 'block']:
                for operand in element.operands:
                    if (operand.x <= x <= operand.x + operand.width and
                            operand.y <= y <= operand.y + operand.height):
                        return operand
        return None

    def _get_branch_at_x_y(self, x: int, y: int, rung_number: int) -> Optional[LadderBranch]:
        """Get the branch at the specified X and Y coordinates."""
        for branch in self._branches.values():
            if (branch.rung_number == rung_number and
                    branch.start_x <= x <= branch.end_x and
                    branch.start_y <= y <= branch.end_y):
                return branch
        return None

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
            if branch.start_y <= y <= branch.end_y:
                return branch.branch_level
        # If no branch found, return main rung level
        return 0

    def _get_coordinate_info(self, x: int, y: int) -> Optional[dict]:
        rung_number = self._get_rung_at_y(y)

        if rung_number is None:
            self._clear_hover_preview()
            return None

        if not self._validate_insertion_position(x, y, rung_number):
            return None

        branch = self._get_branch_at_x_y(x, y, rung_number)
        if not branch:
            branch_level = 0
            branch_id = None
        else:
            branch_level = branch.branch_level
            branch_id = branch.branch_id

        return {
            'rung_number': rung_number,
            'branch_level': branch_level,
            'branch_id': branch_id,
            'x': x,
            'y': y
        }

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
        rung = self._routine.rungs[element.rung_number]
        if not rung:
            raise ValueError(f"Rung {element.rung_number} not found in routine.")
        return rung_y + (self.RUNG_HEIGHT // 2) + (self.BRANCH_SPACING * element.branch_level) + self._get_rung_comment_height(rung)

    def _get_element_x_y_sequence_spacing(
        self,
        element: plc.RungElement
    ) -> tuple[int, int]:
        if element.element_type == plc.RungElementType.BRANCH_END:
            prev_element = self._get_last_branch_ladder_x_element(element)
        else:
            prev_element = self._get_last_ladder_element(element)
        element_x = self._get_element_x_spacing(prev_element)
        element_y = self._get_element_y_spacing(element)
        return (element_x, element_y)

    def _get_insertion_position(self, x: int, y: int) -> tuple[int, int, LadderEditorMode]:
        coord_info = self._get_coordinate_info(x, y)
        if not coord_info:
            return

        insertion_position = self._find_insertion_position(
            x,
            coord_info['rung_number'],
            coord_info['branch_level'],
            coord_info['branch_id'])
        insertion_x, insertion_y = self._calculate_insertion_coordinates(
            coord_info['rung_number'],
            insertion_position,
            coord_info['branch_level'],
            coord_info['branch_id']
        )
        return (insertion_x, insertion_y, self._mode)

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

    def _get_previous_element(self, element: LadderElement) -> Optional[LadderElement]:
        """Get the previous element in the sequence."""
        if not self._elements:
            return None

        elements = self._get_rung_ladder_elements(
            element.rung_number,
            element.branch_level,
            element.branch_id,
            element.root_branch_id
        )

        for e in elements:
            if e.position == element.position - 1:
                return e
        return None

    def _get_rung_at_y(self, y: int) -> Optional[int]:
        """Get rung number at given Y coordinate."""
        for rung_num, rung_y in self._rung_y_positions.items():
            rung_height = self._get_rung_height(rung_num)
            if rung_y <= y <= rung_y + rung_height:
                return rung_num
        return None

    def _get_rung_height(
        self,
        rung_number: Union[int, str]
    ) -> int:
        """Get the height of a rung based on its number."""
        rung_number = int(rung_number)
        rung_y = self._rung_y_positions.get(rung_number, None)
        if not rung_y:
            raise ValueError(f"Rung number {rung_number} not found in rung positions.")
        rung = self._routine.rungs[rung_number]
        if not rung:
            raise ValueError(f"Rung {rung_number} not found in routine.")
        return (
            self.RUNG_HEIGHT +
            (self.BRANCH_SPACING * rung.get_max_branch_depth()) +
            self._get_rung_comment_height(rung)
        )

    def _get_rung_comment_height(
        self,
        rung: plc.Rung,
    ) -> int:
        """Get the height of the comment section for a rung.
        """
        if not rung.comment:
            return 0
        comment_lines = rung.get_comment_lines()
        return comment_lines * self.RUNG_COMMENT_ASCII_Y_SIZE + 20

    def _get_rung_comment_width(
        self,
        rung: plc.Rung,
    ) -> int:
        """Get the width of the comment section for a rung."""
        if not rung.comment:
            return 0
        longest_line = max(len(line) for line in rung.comment.splitlines())
        return max(300, longest_line * self.RUNG_COMMENT_ASCII_X_SIZE + 20)

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

    def _get_rung_rail_height(
        self,
        rung: plc.Rung,
    ) -> int:
        return self.RUNG_HEIGHT + (self.BRANCH_SPACING * rung.get_max_branch_depth())

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

        self._show_status(f"Inserted {instruction.instruction_name} at position {insertion_position} on rung {rung_number}")

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
            self._select_element_at(x, y, event)
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
        elif element and (element.element_type == 'rung' or
                          element.element_type == 'rung_comment'):
            self._edit_rung_comment(element.rung_number)

    def _on_drag(self, event):
        """Handle mouse drag for moving elements."""
        if self._selected_elements:
            if self.mode == LadderEditorMode.VIEW:
                self.mode = LadderEditorMode.DRAG_ELEMENT
                self._show_status("Drag mode activated. Click and drag to move elements.")

            if self.mode == LadderEditorMode.DRAG_ELEMENT:
                x, y = self.canvasx(event.x), self.canvasy(event.y)
                self._update_hover_preview(x, y)

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
        self._highlight_current_element(self._get_element_at(x, y))

        if self._mode in [LadderEditorMode.INSERT_CONTACT,
                          LadderEditorMode.INSERT_COIL,
                          LadderEditorMode.INSERT_BRANCH,
                          LadderEditorMode.INSERT_BLOCK,
                          LadderEditorMode.CONNECT_BRANCH]:
            self._update_hover_preview(x, y)
        else:
            self._clear_hover_preview()

    def _on_mouse_leave(self, _: tk.Event):
        """Handle mouse leaving the canvas."""
        self._clear_hover_preview()
        self._clear_rung_hover_preview()
        self._hide_tooltip()

    def _on_release(self, event: tk.Event):
        """Handle mouse release events."""
        if self._mode == LadderEditorMode.DRAG_ELEMENT:
            try:
                coord_info = self._get_coordinate_info(self.canvasx(event.x), self.canvasy(event.y))
                if not coord_info:
                    self._show_status("Invalid drop position")
                    return
                position = self._find_insertion_position(
                    coord_info['x'],
                    coord_info['rung_number'],
                    coord_info['branch_level'],
                    coord_info['branch_id']
                )
                rung = self._routine.rungs[coord_info['rung_number']]
                rungs_to_draw = {rung.number: rung}
                if position > len(rung.rung_sequence) - 1:
                    position = len(rung.rung_sequence) - 1
                for element in self._selected_elements:
                    r = self._routine.rungs[element.rung_number]
                    r.remove_instruction(element.position, element.position)
                    rung.add_instruction(element.instruction.meta_data, position=position)
                    rungs_to_draw[r.number] = r
                for r in rungs_to_draw.values():
                    self._redraw_rung(r.number)
            except ValueError as e:
                self._show_status(f"Error during drag operation: {str(e)}")
            finally:
                self._show_status("Drag mode deactivated. Click to select or insert elements.")
                self._mode = LadderEditorMode.VIEW
                self._clear_hover_preview()

    def _on_right_click(self, event):
        """Handle right-click context menu."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        element = self._get_element_at(x, y)

        if element:
            self._show_context_menu(event, element)

    def _on_tooltip_motion(self, event, x, y):
        """Enhanced motion handler with tooltip support.
        """
        # Handle tooltip
        element = self._get_element_at(x, y)

        if element != self._tooltip_element:
            self._hide_tooltip()
            self._tooltip_element = element

            if element is not None:
                # Schedule tooltip
                self._tooltip_id = self.after(
                    self._tooltip_delay,
                    lambda: self._show_element_tooltip(event.x_root, event.y_root, element)
                )

    def _paste_element(self):
        """Paste an element (placeholder)."""
        self._show_status("Paste functionality not implemented")

    def _reassign_child_branch_attrs(
        self,
        branch: LadderBranch,
    ):
        for index, child_branch_id in enumerate(branch.children_branch_ids):
            child_branch = self._branches.get(child_branch_id, None)
            if not child_branch:
                raise ValueError(f"Child branch with ID {child_branch_id} not found in branches.")

            if index < len(branch.children_branch_ids) - 1:
                next_child = self._branches.get(branch.children_branch_ids[index + 1], None)
                if not next_child:
                    raise ValueError(f"Next child branch with ID {branch.children_branch_ids[index + 1]} not found in branches.")

                child_branch.end_y = next_child.branch_y - self.BRANCH_SPACING // 2
            child_branch.start_x = branch.start_x
            child_branch.end_x = branch.end_x

    def _redraw_rung(
        self,
        rung_number: int,
        new_y_pos: Optional[int] = None
    ):
        """Redraw a specific rung with proper spacing."""
        rung_number = int(rung_number)

        if not self._routine or rung_number >= len(self._routine.rungs):
            return
        y_pos = self._rung_y_positions.get(rung_number, None)
        if not y_pos:
            raise ValueError(f"Rung number {rung_number} not found in rung positions.")
        rung = self._routine.rungs[rung_number]
        if not rung:
            raise ValueError(f"Rung number {rung_number} does not exist in the routine.")

        rung_element = None
        for element in self._elements:
            if element.rung_number == rung_number and element.element_type == 'rung':
                rung_element = element
                break
        if not rung_element:
            raise ValueError(f"Rung element for rung {rung_number} not found in elements.")

        rung_pre_y = rung_element.y
        rung_pre_height = rung_element.height

        self._clear_rung_visuals(rung_number)

        new_rung = self._draw_rung(rung, rung_number, new_y_pos or y_pos)
        self._elements.append(new_rung)

        if new_rung.y != rung_pre_y or new_rung.height != rung_pre_height:
            # find the next rung, it will need to be redrawn as well
            next_rung_number = rung_number + 1
            next_rung_y = self._rung_y_positions.get(next_rung_number, None)
            if next_rung_y is not None:
                self._redraw_rung(
                    next_rung_number,
                    new_y_pos=self._get_rung_height(new_rung.rung_number) + new_rung.y
                )

    def _select_element_at(
        self,
        x: int,
        y: int,
        event: tk.Event
    ) -> None:
        """Select element at given coordinates.

        Args:
            x: X coordinate of the click.
            y: Y coordinate of the click.
            event: The mouse event that triggered the selection.
        """
        element = self._get_element_at(x, y)

        # Check if Ctrl button is clicked
        ctrl_pressed = bool(event.state & 0x4)  # 0x4 is the Control modifier mask
        if not ctrl_pressed:
            # Clear previous selection
            for elem in self._selected_elements:
                self.itemconfig(
                    elem.canvas_id,
                    fill=elem.custom_fill,
                    outline=elem.custom_outline,
                    width=THEME["ladder_line_width"]
                )
                elem.is_selected = False

            self._selected_elements.clear()

        if element:
            if not element.is_selected:
                self.itemconfig(element.canvas_id, outline=THEME["highlight_color"], width=3)
                element.is_selected = True
                self._selected_elements.append(element)
            else:
                self.itemconfig(
                    element.canvas_id,
                    fill=element.custom_fill,
                    outline=element.custom_outline,
                    width=THEME["ladder_line_width"]
                )
                element.is_selected = False
                self._selected_elements.remove(element)

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
        """Enhanced tooltip for ladder elements with special handling for branch connectors."""
        if not element or self._tooltip is not None:
            return

        # Create tooltip window
        self._tooltip = tk.Toplevel(self)
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.wm_geometry(f"+{x + 15}+{y + 15}")

        # Create tooltip content frame with enhanced styling for branch connectors

        frame = tk.Frame(
            self._tooltip,
            background=THEME["tooltip_background"],
            relief="solid",
            borderwidth=1,
            padx=6,
            pady=4
        )
        frame.pack()

        # Show content based on element type
        if element.instruction:
            self._add_instruction_tooltip_content(frame, element)
        elif element.element_type == 'branch_rail_connector':
            self._add_branch_connector_tooltip_content(frame, element)
        elif self._debug_mode:
            # Debug mode: show tooltips for other non-instruction elements
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
            menu.add_command(label="Copy", command=lambda: self._copy_element(element))
            menu.add_command(label="Paste", command=lambda: self._paste_element())
        elif element.element_type in ['branch_rail_connector']:
            menu.add_command(label="Add Branch level", command=lambda: self._add_branch_level(element.branch_id))
            menu.add_command(label="Delete Branch", command=lambda: self._delete_branch(element.branch_id))
        elif element.element_type in ['rung']:
            menu.add_command(label="Edit Comment", command=lambda: self._edit_rung_comment(element.rung_number))
            menu.add_separator()
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
            nearest_element.y + 5,
            nearest_element.x - (self.ELEMENT_SPACING // 2) + 5,
            nearest_element.y + 15,
            fill='green',
            outline='darkgreen',
            width=THEME["ladder_line_width"],
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
        current_position = self._get_insertion_position(x, y)

        if current_position != self._last_hover_position:
            self._clear_hover_preview()
            self._draw_hover_preview(current_position[0], current_position[1], current_position[2])
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

        for branch in self._branches.values():
            self._add_debug_overlay_for_any_branch(branch)

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
        if rung_number not in self._rung_y_positions:
            return False

        rung_height = self._rung_y_positions[rung_number] + self._get_rung_height(rung_number)
        if not (self._rung_y_positions[rung_number] <= y <= rung_height):
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

    def _setup_ui(
        self
    ):
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
                                           routine=self._routine)

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

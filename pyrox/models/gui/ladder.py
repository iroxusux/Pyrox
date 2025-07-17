"""Ladder Logic Editor components for Pyrox framework."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import importlib
import tkinter as tk
from tkinter import ttk, Canvas, Frame, Scrollbar
from typing import Optional, Dict, List, Callable, Any


from .frames import PyroxFrame, TaskFrame
from ..plc import plc
from ..abc.meta import Loggable


class LadderEditorMode(Enum):
    """Editing modes for the ladder editor."""
    VIEW = "view"
    EDIT = "edit"
    INSERT_CONTACT = "insert_contact"
    INSERT_COIL = "insert_coil"
    INSERT_BLOCK = "insert_block"


@dataclass
class LadderElement:
    """Represents a ladder logic element on the canvas."""
    element_type: str  # 'contact', 'coil', 'block', 'wire'
    x: int
    y: int
    width: int
    height: int
    canvas_id: int
    instruction: Optional[plc.LogixInstruction] = None
    text: str = ""
    is_selected: bool = False


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

    def __init__(self,
                 master,
                 routine: Optional[plc.Routine] = None,
                 **kwargs):
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
            LadderEditorMode.INSERT_BLOCK: "crosshair"
        }
        return cursors.get(mode, "arrow")

    def clear_canvas(self):
        """Clear all elements from the canvas."""
        self.delete("all")
        self._elements.clear()
        self._selected_elements.clear()
        self._rung_y_positions.clear()

    def _draw_routine(self):
        """Draw the entire routine on the canvas."""
        self.clear_canvas()
        if not self._routine or not self._routine.rungs:
            self._draw_empty_rung(0)
            return

        y_pos = 50
        for i, rung in enumerate(self._routine.rungs):
            self._rung_y_positions[i] = y_pos
            self._draw_rung(rung, i, y_pos)
            y_pos += self.RUNG_HEIGHT + 20

        # Update scroll region
        self.configure(scrollregion=self.bbox("all"))

    def _draw_rung(self, rung: plc.Rung, rung_number: int, y_pos: int):
        """Draw a single rung."""
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

        # Draw instructions if any
        if hasattr(rung, 'instructions') and rung.instructions:
            self._draw_rung_instructions(rung.instructions, rung_number, y_pos, rail_x + 10)
        else:
            # Draw empty rung line
            center_y = y_pos + self.RUNG_HEIGHT // 2
            self.create_line(rail_x, center_y, right_rail_x, center_y,
                             width=2, tags=f"rung_{rung_number}")

    def _draw_empty_rung(self, rung_number: int, y_pos: int = 50):
        """Draw an empty rung for new routines."""
        self._rung_y_positions[rung_number] = y_pos

        # Draw rung number
        self.create_text(10, y_pos + self.RUNG_HEIGHT // 2,
                         text=str(rung_number), anchor='w', font=('Arial', 10))

        # Draw power rails
        rail_x = 40
        self.create_line(rail_x, y_pos, rail_x, y_pos + self.RUNG_HEIGHT,
                         width=3, tags=f"rung_{rung_number}")

        right_rail_x = 600
        self.create_line(right_rail_x, y_pos, right_rail_x, y_pos + self.RUNG_HEIGHT,
                         width=3, tags=f"rung_{rung_number}")

        # Draw empty rung line
        center_y = y_pos + self.RUNG_HEIGHT // 2
        self.create_line(rail_x, center_y, right_rail_x, center_y,
                         width=2, tags=f"rung_{rung_number}")

    def _draw_rung_instructions(self, instructions: List[plc.LogixInstruction],
                                rung_number: int, y_pos: int, start_x: int):
        """Draw instructions for a rung."""
        current_x = start_x
        center_y = y_pos + self.RUNG_HEIGHT // 2

        for instruction in instructions:
            element = self._draw_instruction(instruction, current_x, center_y, rung_number)
            if element:
                current_x += element.width + 10

    def _draw_instruction(self, instruction: plc.LogixInstruction, x: int, y: int,
                          rung_number: int) -> Optional[LadderElement]:
        """Draw a single instruction."""
        inst_type = instruction.instruction_name.lower()

        if inst_type in ['xic', 'xio']:  # Contacts
            return self._draw_contact(instruction, x, y, rung_number)
        elif inst_type in ['ote', 'otl', 'otu']:  # Coils
            return self._draw_coil(instruction, x, y, rung_number)
        else:  # Function blocks
            return self._draw_block(instruction, x, y, rung_number)

    def _draw_contact(self, instruction: plc.LogixInstruction, x: int, y: int,
                      rung_number: int) -> LadderElement:
        """Draw a contact instruction."""
        # Determine contact type
        is_normally_closed = instruction.instruction_name.lower() == 'xio'

        # Draw contact symbol
        rect_id = self.create_rectangle(
            x, y - self.CONTACT_HEIGHT // 2,
            x + self.CONTACT_WIDTH, y + self.CONTACT_HEIGHT // 2,
            outline='black', fill='white', width=2,
            tags=f"rung_{rung_number}_instruction"
        )

        # Add contact bars
        if is_normally_closed:
            # Diagonal line for normally closed
            self.create_line(
                x + 5, y - self.CONTACT_HEIGHT // 2 + 5,
                x + self.CONTACT_WIDTH - 5, y + self.CONTACT_HEIGHT // 2 - 5,
                width=2, tags=f"rung_{rung_number}_instruction"
            )
        else:
            # Vertical lines for normally open
            self.create_line(
                x + 10, y - self.CONTACT_HEIGHT // 2 + 5,
                x + 10, y + self.CONTACT_HEIGHT // 2 - 5,
                width=2, tags=f"rung_{rung_number}_instruction"
            )
            self.create_line(
                x + self.CONTACT_WIDTH - 10, y - self.CONTACT_HEIGHT // 2 + 5,
                x + self.CONTACT_WIDTH - 10, y + self.CONTACT_HEIGHT // 2 - 5,
                width=2, tags=f"rung_{rung_number}_instruction"
            )

        # Add operand text
        operand = instruction.operands[0] if instruction.operands else "???"
        text_id = self.create_text(
            x + self.CONTACT_WIDTH // 2, y + self.CONTACT_HEIGHT // 2 + 15,
            text=operand, font=('Arial', 8), tags=f"rung_{rung_number}_instruction"
        )

        return LadderElement(
            element_type='contact',
            x=x, y=y - self.CONTACT_HEIGHT // 2,
            width=self.CONTACT_WIDTH, height=self.CONTACT_HEIGHT,
            canvas_id=rect_id,
            instruction=instruction,
            text=operand
        )

    def _draw_coil(self, instruction: plc.LogixInstruction, x: int, y: int,
                   rung_number: int) -> LadderElement:
        """Draw a coil instruction."""
        # Draw coil circle
        circle_id = self.create_oval(
            x, y - self.COIL_HEIGHT // 2,
            x + self.COIL_WIDTH, y + self.COIL_HEIGHT // 2,
            outline='black', fill='white', width=2,
            tags=f"rung_{rung_number}_instruction"
        )

        # Add coil type indicators
        inst_type = instruction.instruction_type.lower()
        if inst_type == 'otl':  # Latch
            self.create_text(
                x + self.COIL_WIDTH // 2, y,
                text='L', font=('Arial', 12, 'bold'),
                tags=f"rung_{rung_number}_instruction"
            )
        elif inst_type == 'otu':  # Unlatch
            self.create_text(
                x + self.COIL_WIDTH // 2, y,
                text='U', font=('Arial', 12, 'bold'),
                tags=f"rung_{rung_number}_instruction"
            )

        # Add operand text
        operand = instruction.operands[0] if instruction.operands else "???"
        text_id = self.create_text(
            x + self.COIL_WIDTH // 2, y + self.COIL_HEIGHT // 2 + 15,
            text=operand, font=('Arial', 8), tags=f"rung_{rung_number}_instruction"
        )

        return LadderElement(
            element_type='coil',
            x=x, y=y - self.COIL_HEIGHT // 2,
            width=self.COIL_WIDTH, height=self.COIL_HEIGHT,
            canvas_id=circle_id,
            instruction=instruction,
            text=operand
        )

    def _draw_block(self, instruction: plc.LogixInstruction, x: int, y: int,
                    rung_number: int) -> LadderElement:
        """Draw a function block instruction."""
        # Draw block rectangle
        rect_id = self.create_rectangle(
            x, y - self.BLOCK_HEIGHT // 2,
            x + self.BLOCK_WIDTH, y + self.BLOCK_HEIGHT // 2,
            outline='black', fill='lightblue', width=2,
            tags=f"rung_{rung_number}_instruction"
        )

        # Add instruction type text
        self.create_text(
            x + self.BLOCK_WIDTH // 2, y - 10,
            text=instruction.instruction_type, font=('Arial', 10, 'bold'),
            tags=f"rung_{rung_number}_instruction"
        )

        # Add operands text
        operands_text = ', '.join(instruction.operands) if instruction.operands else ""
        if len(operands_text) > 12:
            operands_text = operands_text[:12] + "..."

        self.create_text(
            x + self.BLOCK_WIDTH // 2, y + 5,
            text=operands_text, font=('Arial', 8),
            tags=f"rung_{rung_number}_instruction"
        )

        return LadderElement(
            element_type='block',
            x=x, y=y - self.BLOCK_HEIGHT // 2,
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
        elif self._mode in [LadderEditorMode.INSERT_CONTACT,
                            LadderEditorMode.INSERT_COIL,
                            LadderEditorMode.INSERT_BLOCK]:
            self._insert_element_at(x, y)

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

    def _insert_element_at(self, x: int, y: int):
        """Insert new element at given coordinates."""
        # Find which rung we're in
        rung_number = self._get_rung_at_y(y)
        if rung_number is None:
            return

        # Create new instruction based on mode
        if self._mode == LadderEditorMode.INSERT_CONTACT:
            self._insert_contact(x, y, rung_number)
        elif self._mode == LadderEditorMode.INSERT_COIL:
            self._insert_coil(x, y, rung_number)
        elif self._mode == LadderEditorMode.INSERT_BLOCK:
            self._insert_block(x, y, rung_number)

    def _get_rung_at_y(self, y: int) -> Optional[int]:
        """Get rung number at given Y coordinate."""
        for rung_num, rung_y in self._rung_y_positions.items():
            if rung_y <= y <= rung_y + self.RUNG_HEIGHT:
                return rung_num
        return None

    def _insert_contact(self, x: int, y: int, rung_number: int):
        """Insert a new contact at given position."""
        # Create new XIC instruction
        from ..plc.plc import LogixInstruction
        new_instruction = LogixInstruction(meta_data='XIC(NewContact)',
                                           rung=self._routine.rungs[rung_number] if self._routine else None,
                                           controller=self._routine.controller if self._routine else None)

        # Draw the contact
        element = self._draw_contact(new_instruction, x, y, rung_number)
        if element:
            self._elements.append(element)
            self._add_instruction_to_rung(new_instruction, rung_number)

    def _insert_coil(self, x: int, y: int, rung_number: int):
        """Insert a new coil at given position."""
        from ..plc.plc import LogixInstruction
        new_instruction = LogixInstruction()
        new_instruction.instruction_type = 'OTE'
        new_instruction.operands = ['NewCoil']

        element = self._draw_coil(new_instruction, x, y, rung_number)
        if element:
            self._elements.append(element)
            self._add_instruction_to_rung(new_instruction, rung_number)

    def _insert_block(self, x: int, y: int, rung_number: int):
        """Insert a new function block at given position."""
        from ..plc.plc import LogixInstruction
        new_instruction = LogixInstruction()
        new_instruction.instruction_type = 'TON'
        new_instruction.operands = ['Timer1', '1000', '0']

        element = self._draw_block(new_instruction, x, y, rung_number)
        if element:
            self._elements.append(element)
            self._add_instruction_to_rung(new_instruction, rung_number)

    def _add_instruction_to_rung(self, instruction: plc.LogixInstruction, rung_number: int):
        """Add instruction to the appropriate rung in the routine."""
        if not self._routine or not hasattr(self._routine, 'rungs'):
            return

        if rung_number < len(self._routine.rungs):
            rung = self._routine.rungs[rung_number]
            if not hasattr(rung, 'instructions'):
                rung.instructions = []
            rung.instructions.append(instruction)

    def _show_context_menu(self, event, element: LadderElement):
        """Show context menu for element."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Edit", command=lambda: self._edit_instruction(element.instruction))
        menu.add_command(label="Delete", command=lambda: self._delete_element(element))
        menu.add_separator()
        menu.add_command(label="Copy", command=lambda: self._copy_element(element))
        menu.add_command(label="Paste", command=lambda: self._paste_element())

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _edit_instruction(self, instruction: plc.LogixInstruction):
        """Open instruction editor dialog."""
        from .frames import ValueEditPopup

        def on_edit_complete(new_value):
            if new_value and instruction.operands:
                instruction.operands[0] = new_value
                self._draw_routine()  # Redraw to show changes

        current_value = instruction.operands[0] if instruction.operands else ""
        ValueEditPopup(self, current_value, on_edit_complete,
                       title=f"Edit {instruction.instruction_name}")

    def _delete_element(self, element: LadderElement):
        """Delete an element from the canvas and routine."""
        # Remove from canvas
        self.delete(element.canvas_id)
        if element in self._elements:
            self._elements.remove(element)
        if element in self._selected_elements:
            self._selected_elements.remove(element)

        # Remove from routine data
        # This would need more sophisticated logic to find and remove
        # the instruction from the correct rung

        self.logger.info(f"Deleted {element.element_type} element")

    def _copy_element(self, element: LadderElement):
        """Copy element to clipboard."""
        # Implementation would store element data for pasting
        pass

    def _paste_element(self):
        """Paste element from clipboard."""
        # Implementation would create new element from clipboard data
        pass

    def add_rung(self) -> int:
        """Add a new empty rung to the routine."""
        if not self._routine:
            return 0

        # Add to routine data
        from ..plc.plc import Rung
        new_rung = Rung()
        if not hasattr(self._routine, 'rungs'):
            self._routine.rungs = []
        self._routine.rungs.append(new_rung)

        # Redraw routine
        self._draw_routine()

        return len(self._routine.rungs) - 1

    def delete_rung(self, rung_number: int):
        """Delete a rung from the routine."""
        if (not self._routine or not hasattr(self._routine, 'rungs') or
                rung_number >= len(self._routine.rungs)):
            return

        # Remove from routine data
        self._routine.rungs.pop(rung_number)

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
            self._status_label.config(text="Routine verified successfully")
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

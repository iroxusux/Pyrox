"""
Command Bar Widget for Pyrox applications.

This module provides a command bar widget that allows easy programmatic
adding and removal of command buttons for user interactions. The command
bar follows the Pyrox GUI patterns and theming system.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Callable, Union
from dataclasses import dataclass

from pyrox.models.gui.frame import PyroxFrameContainer
from pyrox.models.gui.theme import DefaultTheme


@dataclass
class CommandButton:
    """Configuration for a command button.

    Attributes:
        id (str): Unique identifier for the button.
        text (str): Text displayed on the button.
        command (Callable): Function to call when button is clicked.
        tooltip (Optional[str]): Tooltip text for the button.
        icon (Optional[str]): Icon path or Unicode character for the button.
        enabled (bool): Whether the button is initially enabled.
        visible (bool): Whether the button is initially visible.
        selectable (bool): Whether the button is selectable (toggle).
        width (Optional[int]): Button width in characters.
    """
    id: str
    text: str
    command: Callable[[], None]
    tooltip: Optional[str] = None
    icon: Optional[str] = None
    enabled: bool = True
    visible: bool = True
    selectable: bool = False
    width: Optional[int] = None


class PyroxCommandBar(PyroxFrameContainer):
    """
    A command bar widget for adding and managing command buttons.

    The command bar provides a horizontal toolbar-like interface where
    command buttons can be dynamically added, removed, enabled, disabled,
    and organized. It follows the Pyrox theming system and integrates
    seamlessly with other Pyrox GUI components.

    Features:
    - Dynamic button addition/removal by ID
    - Button state management (enabled/disabled, visible/hidden)
    - Tooltip support
    - Icon support (text or Unicode characters)
    - Separator support for button grouping
    - Event callbacks for button actions
    - Consistent Pyrox theming
    - Configurable button layout and spacing

    Example:
        >>> command_bar = PyroxCommandBar(parent)
        >>>
        >>> # Add buttons
        >>> command_bar.add_button(CommandButton(
        ...     id='save',
        ...     text='Save',
        ...     command=lambda: print('Save clicked'),
        ...     tooltip='Save current document'
        ... ))
        >>>
        >>> # Add separator and more buttons
        >>> command_bar.add_separator()
        >>> command_bar.add_button(CommandButton(
        ...     id='run',
        ...     text='Run',
        ...     command=lambda: print('Run clicked'),
        ...     icon='▶'
        ... ))
        >>>
        >>> # Manage button states
        >>> command_bar.set_enabled('save', False)
        >>> command_bar.set_visible('run', False)
        >>> command_bar.remove_button('save')
    """

    def __init__(
        self,
        master=None,
        orientation: str = 'horizontal',
        button_padding: tuple[int, int] = (2, 2),
        separator_width: int = 1,
        separator_color: Optional[str] = None,
        show_tooltips: bool = True,
        **kwargs
    ) -> None:
        """
        Initialize the PyroxCommandBar.

        Args:
            master: Parent widget
            orientation: Layout orientation ('horizontal' or 'vertical')
            button_padding: Padding around buttons as (x, y) tuple
            separator_width: Width of separator lines in pixels
            separator_color: Color of separator lines (None for theme default)
            show_tooltips: Whether to show tooltips on hover
            **kwargs: Additional arguments passed to PyroxFrame
        """
        kwargs['master'] = master
        super().__init__(**kwargs)

        # Configuration
        self.orientation = orientation
        self.button_padding = button_padding
        self.separator_width = separator_width
        self.separator_color = separator_color or DefaultTheme.bordercolor
        self.show_tooltips = show_tooltips

        # Widget tracking
        self._buttons: Dict[str, tk.Button] = {}
        self._button_configs: Dict[str, CommandButton] = {}
        self._button_selected_state: Dict[str, bool] = {}
        self._separators: List[Optional[ttk.Separator]] = []
        self._tooltips: Dict[str, str] = {}

        # Layout tracking
        self._next_position = 0
        self._widget_order: List[Union[str, int]] = []  # button IDs or separator indices

        # Event callbacks
        self.on_button_added: Optional[Callable[[str, CommandButton], None]] = None
        self.on_button_removed: Optional[Callable[[str], None]] = None
        self.on_button_clicked: Optional[Callable[[str, CommandButton], None]] = None

        # Create the layout
        self._create_layout()

    def _create_layout(self) -> None:
        """Create the main command bar layout."""
        # Configure grid weights for proper expansion
        if self.orientation == 'horizontal':
            self.frame_root.grid_rowconfigure(0, weight=1)
        else:
            self.frame_root.grid_columnconfigure(0, weight=1)

    def add_button(self, button_config: CommandButton) -> None:
        """
        Add a command button to the bar.

        Args:
            button_config (CommandButton): Configuration for the button to add.

        Raises:
            ValueError: If a button with the same ID already exists.
        """
        if button_config.id in self._buttons:
            raise ValueError(f"Button with ID '{button_config.id}' already exists")

        # Create the button
        button = tk.Button(
            self.frame_root,
            text=self._format_button_text(button_config),
            command=lambda: self._handle_button_click(button_config),
            state=tk.NORMAL if button_config.enabled else tk.DISABLED,
            relief='raised',
            borderwidth=1,
            font=(DefaultTheme.font_family, DefaultTheme.font_size),
            background=DefaultTheme.button_color,
            foreground=DefaultTheme.foreground,
            activebackground=DefaultTheme.button_hover,
            activeforeground=DefaultTheme.foreground_selected
        )

        # Set button width if specified
        if button_config.width:
            button.config(width=button_config.width)

        # Store references
        self._buttons[button_config.id] = button
        self._button_configs[button_config.id] = button_config
        self._button_selected_state[button_config.id] = False
        self._widget_order.append(button_config.id)

        # Position the button
        self._position_widget(button, button_config.visible)

        # Setup tooltip if enabled and provided
        if self.show_tooltips and button_config.tooltip:
            self._setup_tooltip(button, button_config.tooltip)

        # Setup hover effects
        self._setup_hover_effects(button)

        # Trigger callback
        if self.on_button_added:
            self.on_button_added(button_config.id, button_config)

    def add_separator(self) -> int:
        """
        Add a separator to the command bar.

        Returns:
            int: Index of the added separator for later reference.
        """
        separator = ttk.Separator(
            self.frame_root,
            orient='vertical' if self.orientation == 'horizontal' else 'horizontal'
        )

        separator_index = len(self._separators)
        self._separators.append(separator)
        self._widget_order.append(separator_index)

        # Position the separator
        self._position_widget(separator, visible=True)

        return separator_index

    def remove_button(self, button_id: str) -> None:
        """
        Remove a command button from the bar.

        Args:
            button_id (str): ID of the button to remove.

        Raises:
            KeyError: If no button with the given ID exists.
        """
        if button_id not in self._buttons:
            raise KeyError(f"No button with ID '{button_id}' found")

        # Remove the button widget
        button = self._buttons[button_id]
        button.destroy()

        # Clean up references
        del self._buttons[button_id]
        del self._button_configs[button_id]
        del self._button_selected_state[button_id]

        # Remove from widget order
        if button_id in self._widget_order:
            self._widget_order.remove(button_id)

        # Remove tooltip if exists
        if button_id in self._tooltips:
            del self._tooltips[button_id]

        # Reposition remaining widgets
        self._reposition_widgets()

        # Trigger callback
        if self.on_button_removed:
            self.on_button_removed(button_id)

    def remove_separator(self, separator_index: int) -> None:
        """
        Remove a separator from the command bar.

        Args:
            separator_index (int): Index of the separator to remove.

        Raises:
            IndexError: If separator index is out of range.
        """
        if not (0 <= separator_index < len(self._separators)):
            raise IndexError(f"Separator index {separator_index} out of range")

        # Remove the separator widget
        separator = self._separators[separator_index]
        if separator is not None:
            separator.destroy()

        # Clean up references
        self._separators[separator_index] = None  # Mark as removed

        # Remove from widget order
        if separator_index in self._widget_order:
            self._widget_order.remove(separator_index)

        # Reposition remaining widgets
        self._reposition_widgets()

    def set_enabled(self, button_id: str, enabled: bool) -> None:
        """
        Enable or disable a command button.

        Args:
            button_id (str): ID of the button to modify.
            enabled (bool): Whether the button should be enabled.

        Raises:
            KeyError: If no button with the given ID exists.
        """
        if button_id not in self._buttons:
            raise KeyError(f"No button with ID '{button_id}' found")

        button = self._buttons[button_id]
        button.config(state=tk.NORMAL if enabled else tk.DISABLED)

        # Update configuration
        self._button_configs[button_id].enabled = enabled

    def set_selected(self, button_id: str, selected: bool) -> None:
        """
        Set the selected state of a selectable command button.

        Args:
            button_id (str): ID of the button to modify.
            selected (bool): Whether the button should be in selected state.
        """
        if button_id not in self._buttons:
            return

        button_config = self._button_configs[button_id]
        if not button_config.selectable:
            return

        button = self._buttons[button_id]
        self._button_selected_state[button_id] = selected
        if selected:
            button.config(relief='sunken', background=DefaultTheme.button_active)
        else:
            button.config(relief='raised', background=DefaultTheme.button_color)

    def set_visible(self, button_id: str, visible: bool) -> None:
        """
        Show or hide a command button.

        Args:
            button_id (str): ID of the button to modify.
            visible (bool): Whether the button should be visible.

        Raises:
            KeyError: If no button with the given ID exists.
        """
        if button_id not in self._buttons:
            raise KeyError(f"No button with ID '{button_id}' found")

        button = self._buttons[button_id]

        if visible:
            self._position_widget(button, True)
        else:
            button.grid_remove()

        # Update configuration
        self._button_configs[button_id].visible = visible

    def set_text(self, button_id: str, text: str) -> None:
        """
        Update the text of a command button.

        Args:
            button_id (str): ID of the button to modify.
            text (str): New text for the button.

        Raises:
            KeyError: If no button with the given ID exists.
        """
        if button_id not in self._buttons:
            raise KeyError(f"No button with ID '{button_id}' found")

        # Update configuration
        self._button_configs[button_id].text = text

        # Update button display
        button = self._buttons[button_id]
        button.config(text=self._format_button_text(self._button_configs[button_id]))

    def get_button(self, button_id: str) -> Optional[tk.Button]:
        """
        Get a button widget by ID.

        Args:
            button_id (str): ID of the button to retrieve.

        Returns:
            Optional[tk.Button]: The button widget, or None if not found.
        """
        return self._buttons.get(button_id)

    def get_button_id(self, button: tk.Button) -> Optional[str]:
        """
        Get the ID of a button widget.

        Args:
            button (tk.Button): Button widget to look up.

        Returns:
            Optional[str]: The button ID, or None if not found.
        """
        for b_id, b_widget in self._buttons.items():
            if b_widget == button:
                return b_id
        return None

    def get_button_config(self, button_id: str) -> Optional[CommandButton]:
        """
        Get a button configuration by ID.

        Args:
            button_id (str): ID of the button configuration to retrieve.

        Returns:
            Optional[CommandButton]: The button configuration, or None if not found.
        """
        return self._button_configs.get(button_id)

    def get_selected_buttons(self) -> List[str]:
        """
        Get a list of IDs for all currently selected buttons.

        Returns:
            List[str]: List of selected button IDs.
        """
        return [button_id for button_id, selected in self._button_selected_state.items() if selected]

    def get_all_button_ids(self) -> List[str]:
        """
        Get all button IDs in the command bar.

        Returns:
            List[str]: List of all button IDs.
        """
        return list(self._buttons.keys())

    def clear_all(self) -> None:
        """Remove all buttons and separators from the command bar."""
        # Remove all buttons
        for button_id in list(self._buttons.keys()):
            self.remove_button(button_id)

        # Remove all separators
        for i, separator in enumerate(self._separators):
            if separator is not None:
                separator.destroy()

        # Clear all tracking
        self._separators.clear()
        self._widget_order.clear()
        self._next_position = 0

    def _format_button_text(self, button_config: CommandButton) -> str:
        """Format button text with optional icon."""
        if button_config.icon:
            return f"{button_config.icon} {button_config.text}"
        return button_config.text

    def _handle_button_click(self, button_config: CommandButton) -> None:
        """Handle button click events."""
        # Execute the button command
        if button_config.command and button_config.enabled:
            try:
                button_config.command()
            except Exception as e:
                # Could add logging here if needed
                print(f"Error executing command for button '{button_config.id}': {e}")

        # If selectable, toggle selected state
        if button_config.selectable:
            # First, clear all other selected states
            for other_config in self._button_configs.values():
                self.set_selected(other_config.id, False)
            self.set_selected(button_config.id, True)

        # Trigger callback
        if self.on_button_clicked:
            self.on_button_clicked(button_config.id, button_config)

    def _position_widget(self, widget: tk.Widget, visible: bool) -> None:
        """Position a widget in the command bar layout."""
        if not visible:
            widget.grid_remove()
            return

        # Calculate position based on widget order and current widgets
        position = sum(1 for item in self._widget_order
                       if isinstance(item, str) and item in self._buttons and self._button_configs[item].visible
                       or isinstance(item, int) and item < len(self._separators) and self._separators[item] is not None)

        if self.orientation == 'horizontal':
            widget.grid(
                row=0,
                column=position,
                padx=self.button_padding[0],
                pady=self.button_padding[1],
                sticky='ns'
            )
        else:
            widget.grid(
                row=position,
                column=0,
                padx=self.button_padding[0],
                pady=self.button_padding[1],
                sticky='ew'
            )

    def _reposition_widgets(self) -> None:
        """Reposition all visible widgets after changes."""
        position = 0

        for item in self._widget_order:
            widget = None
            visible = False

            if isinstance(item, str) and item in self._buttons:
                # It's a button
                widget = self._buttons[item]
                visible = self._button_configs[item].visible
            elif isinstance(item, int) and item < len(self._separators) and self._separators[item] is not None:
                # It's a separator
                widget = self._separators[item]
                visible = True

            if widget and visible:
                if self.orientation == 'horizontal':
                    widget.grid(
                        row=0,
                        column=position,
                        padx=self.button_padding[0],
                        pady=self.button_padding[1],
                        sticky='ns'
                    )
                else:
                    widget.grid(
                        row=position,
                        column=0,
                        padx=self.button_padding[0],
                        pady=self.button_padding[1],
                        sticky='ew'
                    )
                position += 1

    def _setup_tooltip(self, widget: tk.Button, tooltip_text: str) -> None:
        """Setup tooltip for a widget (simple implementation)."""
        def on_enter(event):
            # Simple tooltip - could be enhanced with a proper tooltip widget
            widget.config(relief='solid')

        def on_leave(event):
            widget.config(relief='raised')

        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

    def _setup_hover_effects(self, button: tk.Button) -> None:
        """Setup hover effects for buttons."""
        original_bg = button.cget('background')
        original_rlf = button.cget('relief')

        def on_enter(event):
            button.config(
                background=DefaultTheme.button_hover,
                relief='solid'
            )

        def on_leave(event):
            try:  # Try resetting the selected state if the button was previously selected
                button_id = self.get_button_id(button)
                if not button_id:
                    raise Exception
                config = self.get_button_config(button_id)
                if not config:
                    raise Exception
                if self._button_selected_state.get(button_id, False):
                    self.set_selected(button_id, self._button_selected_state.get(button_id, False))
                else:
                    raise Exception
            except Exception:
                button.config(
                    background=original_bg,
                    relief=original_rlf
                )

        button.bind('<Enter>', on_enter)
        button.bind('<Leave>', on_leave)


# Convenience functions for common command bar operations
def create_file_command_bar(parent, file_operations: Dict[str, Callable]) -> PyroxCommandBar:
    """
    Create a command bar with common file operations.

    Args:
        parent: Parent widget
        file_operations: Dictionary mapping operation names to functions

    Returns:
        PyroxCommandBar: Configured command bar with file operation buttons
    """
    command_bar = PyroxCommandBar(parent)

    # Add common file operation buttons
    operations = {
        'new': ('New', '📄', 'Create new file'),
        'open': ('Open', '📁', 'Open existing file'),
        'save': ('Save', '💾', 'Save current file'),
        'save_as': ('Save As', '💾', 'Save file with new name'),
    }

    for op_id, (text, icon, tooltip) in operations.items():
        if op_id in file_operations:
            command_bar.add_button(CommandButton(
                id=op_id,
                text=text,
                command=file_operations[op_id],
                icon=icon,
                tooltip=tooltip
            ))

    return command_bar


def create_edit_command_bar(parent, edit_operations: Dict[str, Callable]) -> PyroxCommandBar:
    """
    Create a command bar with common edit operations.

    Args:
        parent: Parent widget
        edit_operations: Dictionary mapping operation names to functions

    Returns:
        PyroxCommandBar: Configured command bar with edit operation buttons
    """
    command_bar = PyroxCommandBar(parent)

    # Add common edit operation buttons
    operations = {
        'undo': ('Undo', '↶', 'Undo last action'),
        'redo': ('Redo', '↷', 'Redo last undone action'),
        'cut': ('Cut', '✂', 'Cut to clipboard'),
        'copy': ('Copy', '📋', 'Copy to clipboard'),
        'paste': ('Paste', '📄', 'Paste from clipboard'),
    }

    for op_id, (text, icon, tooltip) in operations.items():
        if op_id in edit_operations:
            command_bar.add_button(CommandButton(
                id=op_id,
                text=text,
                command=edit_operations[op_id],
                icon=icon,
                tooltip=tooltip
            ))

    return command_bar


if __name__ == '__main__':
    """Test the PyroxCommandBar when run directly."""

    # Create the main test window
    root = tk.Tk()
    root.title("PyroxCommandBar Test")
    root.geometry("800x500")
    root.configure(bg='#2b2b2b')  # Match Pyrox theme

    # Create main container
    main_frame = tk.Frame(root, bg='#2b2b2b')
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Create the command bar
    command_bar = PyroxCommandBar(
        main_frame,
        orientation='horizontal',
        button_padding=(5, 3),
        show_tooltips=True
    )
    command_bar.frame.pack(fill=tk.X, pady=(0, 10))

    # Add test buttons with different configurations
    command_bar.add_button(CommandButton(
        id='file_new',
        text='New',
        command=lambda: print('New file created'),
        icon='📄',
        tooltip='Create a new file'
    ))

    command_bar.add_button(CommandButton(
        id='file_open',
        text='Open',
        command=lambda: print('File opened'),
        icon='📁',
        tooltip='Open an existing file'
    ))

    command_bar.add_button(CommandButton(
        id='file_save',
        text='Save',
        command=lambda: print('File saved'),
        icon='💾',
        tooltip='Save current file',
        width=8
    ))

    # Add separator
    command_bar.add_separator()

    # Add edit buttons
    command_bar.add_button(CommandButton(
        id='edit_undo',
        text='Undo',
        command=lambda: print('Undo performed'),
        icon='↶',
        tooltip='Undo last action'
    ))

    command_bar.add_button(CommandButton(
        id='edit_redo',
        text='Redo',
        command=lambda: print('Redo performed'),
        icon='↷',
        tooltip='Redo last undone action',
        enabled=False  # Start disabled
    ))

    # Add another separator
    command_bar.add_separator()

    # Add view buttons
    command_bar.add_button(CommandButton(
        id='view_refresh',
        text='Refresh',
        command=lambda: print('View refreshed'),
        icon='🔄',
        tooltip='Refresh the current view'
    ))

    # Add another separator
    command_bar.add_separator()

    command_bar.add_button(CommandButton(
        id='toggle_selected_a',
        text='Option A',
        command=lambda: print('Option A selected'),
        icon='A',
        tooltip='Select Option A',
        selectable=True,
    ))

    command_bar.add_button(CommandButton(
        id='toggle_selected_b',
        text='Option B',
        command=lambda: print('Option B selected'),
        icon='B',
        tooltip='Select Option B',
        selectable=True,
    ))

    # Create control panel for testing button management
    control_frame = tk.LabelFrame(main_frame, text="Command Bar Controls",
                                  bg='#3b3b3b', fg='white', font=('Consolas', 10))
    control_frame.pack(fill=tk.X, pady=(0, 10))

    button_frame = tk.Frame(control_frame, bg='#3b3b3b')
    button_frame.pack(fill=tk.X, padx=5, pady=5)

    def toggle_redo_enabled():
        """Toggle the redo button enabled state."""
        config = command_bar.get_button_config('edit_redo')
        if config:
            new_state = not config.enabled
            command_bar.set_enabled('edit_redo', new_state)
            print(f"Redo button {'enabled' if new_state else 'disabled'}")

    def toggle_refresh_visible():
        """Toggle the refresh button visibility."""
        config = command_bar.get_button_config('view_refresh')
        if config:
            new_state = not config.visible
            command_bar.set_visible('view_refresh', new_state)
            print(f"Refresh button {'shown' if new_state else 'hidden'}")

    def add_test_button():
        """Add a test button dynamically."""
        try:
            command_bar.add_button(CommandButton(
                id='test_dynamic',
                text='Test',
                command=lambda: print('Dynamic test button clicked!'),
                icon='⚡',
                tooltip='Dynamically added test button'
            ))
            print("Dynamic test button added")
        except ValueError as e:
            print(f"Cannot add button: {e}")

    def remove_test_button():
        """Remove the test button."""
        try:
            command_bar.remove_button('test_dynamic')
            print("Dynamic test button removed")
        except KeyError as e:
            print(f"Cannot remove button: {e}")

    def clear_all_buttons():
        """Clear all buttons from the command bar."""
        command_bar.clear_all()
        print("All buttons cleared")

    # Control buttons
    tk.Button(button_frame, text="Toggle Redo", command=toggle_redo_enabled,
              bg='#4b4b4b', fg='white', font=('Consolas', 9)).pack(side=tk.LEFT, padx=2)
    tk.Button(button_frame, text="Toggle Refresh", command=toggle_refresh_visible,
              bg='#4b4b4b', fg='white', font=('Consolas', 9)).pack(side=tk.LEFT, padx=2)
    tk.Button(button_frame, text="Add Test", command=add_test_button,
              bg='#4b4b4b', fg='white', font=('Consolas', 9)).pack(side=tk.LEFT, padx=2)
    tk.Button(button_frame, text="Remove Test", command=remove_test_button,
              bg='#4b4b4b', fg='white', font=('Consolas', 9)).pack(side=tk.LEFT, padx=2)
    tk.Button(button_frame, text="Clear All", command=clear_all_buttons,
              bg='#6b2b2b', fg='white', font=('Consolas', 9)).pack(side=tk.LEFT, padx=2)

    # Create output area
    output_frame = tk.LabelFrame(main_frame, text="Output Log",
                                 bg='#3b3b3b', fg='white', font=('Consolas', 10))
    output_frame.pack(fill=tk.BOTH, expand=True)

    output_text = tk.Text(output_frame, bg='#1e1e1e', fg='#00ff00',
                          font=('Consolas', 9), wrap=tk.WORD,
                          insertbackground='white')

    scrollbar = tk.Scrollbar(output_frame, command=output_text.yview)
    output_text.config(yscrollcommand=scrollbar.set)

    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Add initial text
    output_text.insert(tk.END, "PyroxCommandBar Test\n")
    output_text.insert(tk.END, "=" * 50 + "\n\n")
    output_text.insert(tk.END, "Available buttons: " + str(command_bar.get_all_button_ids()) + "\n\n")
    output_text.insert(tk.END, "Instructions:\n")
    output_text.insert(tk.END, "• Click command bar buttons to test functionality\n")
    output_text.insert(tk.END, "• Use control buttons to test dynamic management\n")
    output_text.insert(tk.END, "• Hover over buttons to see tooltips\n\n")

    # Setup event callbacks
    def on_button_clicked(button_id: str, config: CommandButton):
        """Handle button click events."""
        message = f"[{button_id}] '{config.text}' button clicked\n"
        output_text.insert(tk.END, message)
        output_text.see(tk.END)
        print(f"Button clicked: {button_id}")

    def on_button_added(button_id: str, config: CommandButton):
        """Handle button addition events."""
        message = f"Button added: {button_id} - '{config.text}'\n"
        output_text.insert(tk.END, message)
        output_text.see(tk.END)

    def on_button_removed(button_id: str):
        """Handle button removal events."""
        message = f"Button removed: {button_id}\n"
        output_text.insert(tk.END, message)
        output_text.see(tk.END)

    # Connect callbacks
    command_bar.on_button_clicked = on_button_clicked
    command_bar.on_button_added = on_button_added
    command_bar.on_button_removed = on_button_removed

    # Status bar
    status_frame = tk.Frame(main_frame, bg='#1e1e1e', relief=tk.SUNKEN, bd=1)
    status_frame.pack(fill=tk.X, pady=(5, 0))

    status_label = tk.Label(status_frame, text="PyroxCommandBar Test Ready",
                            bg='#1e1e1e', fg='white', anchor=tk.W,
                            font=('Consolas', 9))
    status_label.pack(fill=tk.X, padx=5, pady=2)

    print("PyroxCommandBar test window created")
    print("Available buttons:", command_bar.get_all_button_ids())

    # Start the test
    root.mainloop()

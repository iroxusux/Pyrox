"""Reusable Property Panel for Tkinter GUI.

This module provides a reusable Tkinter-based property panel for displaying
and editing object properties using the IHasProperties protocol.

Example Usage:
    ```python
    # Create a property panel
    panel = TkPropertyPanel(
        parent=parent_frame,
        title="Object Properties",
        on_property_changed=handle_property_change
    )

    # Display properties for an object that implements IHasProperties
    scene_obj = scene.get_scene_object("obj_001")
    panel.set_object(scene_obj, readonly_properties={"id", "type"})

    # Show the panel
    panel.pack(side=tk.RIGHT, fill=tk.Y)

    # Update when selection changes
    panel.refresh()
    ```
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, Callable
from pyrox.interfaces.protocols import IHasProperties


class TkPropertyPanel(ttk.Frame):
    """A reusable Tkinter property panel widget.

    This panel displays properties from objects implementing IHasProperties.
    It supports both display-only and editable property fields, with automatic
    rendering based on property types.

    Features:
        - Displays properties from IHasProperties objects
        - Support for read-only and editable fields
        - Automatic type-based rendering (string, int, float, bool, color)
        - Scrollable content area for many properties
        - Property change callbacks
        - Multi-selection support

    Attributes:
        target_object: The current object being displayed
        property_widgets: Dictionary mapping property names to their widgets
        on_property_changed: Optional callback for property value changes
    """

    def __init__(
        self,
        parent: tk.Widget,
        title: str = "Properties",
        width: int = 250,
        on_property_changed: Optional[Callable[[str, Any], None]] = None,
        **kwargs
    ):
        """Initialize the TkPropertyPanel.

        Args:
            parent: Parent widget
            title: Title displayed at the top of the panel
            width: Width of the panel in pixels
            on_property_changed: Optional callback function(property_name, new_value)
                                 called when a property is modified
            **kwargs: Additional arguments passed to ttk.Frame
        """
        super().__init__(parent, width=width, **kwargs)

        self._title = title
        self._target_object: Optional[IHasProperties] = None
        self._property_widgets: Dict[str, tk.Widget] = {}
        self._on_property_changed = on_property_changed
        self._readonly_properties: set[str] = set()

        # Build the UI structure
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the property panel UI structure."""
        # Header
        self._header = ttk.Label(
            self,
            text=self._title,
            font=("TkDefaultFont", 10, "bold")
        )
        self._header.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(
            side=tk.TOP, fill=tk.X, padx=5
        )

        # Scrollable content area
        self._content_frame = ttk.Frame(self)
        self._content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # TODO: Add scrollbar support for many properties
        # self._canvas = tk.Canvas(self)
        # self._scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._canvas.yview)
        # self._canvas.configure(yscrollcommand=self._scrollbar.set)

    def set_title(self, title: str) -> None:
        """Set the panel title.

        Args:
            title: New title text
        """
        self._title = title
        self._header.config(text=title)

    def set_object(
        self,
        obj: Optional[IHasProperties],
        readonly_properties: Optional[set[str]] = None
    ) -> None:
        """Set the object to display properties for.

        Args:
            obj: Object implementing IHasProperties, or None to clear
            readonly_properties: Set of property names that should be read-only
        """
        self._target_object = obj
        self._readonly_properties = readonly_properties or set()
        self.refresh()

    def refresh(self) -> None:
        """Refresh the property panel display from the current object.

        This performs a full rebuild of all widgets. Use update_values() instead
        for frequent updates to avoid flickering.
        """
        # Clear existing widgets
        self._clear_properties()

        if not self._target_object:
            self._show_empty_state("No object selected")
            return

        # Get properties from the object
        try:
            properties = self._target_object.get_properties()
        except Exception as e:
            self._show_empty_state(f"Error: {str(e)}")
            return

        if not properties:
            self._show_empty_state("No properties available")
            return

        # Display all properties
        self._display_properties(properties)

    def update_values(self) -> None:
        """Update property values in existing widgets without rebuilding.

        This is much more efficient than refresh() and doesn't cause flickering.
        Only updates values for properties that have changed.
        """
        if not self._target_object:
            return

        # Get current properties
        try:
            properties = self._target_object.get_properties()
        except Exception:
            return

        # Update each existing widget with new values
        for prop_name, widget in self._property_widgets.items():
            if prop_name not in properties:
                continue

            new_value = properties[prop_name]

            # Skip updating if the widget currently has focus (user is editing)
            if widget.focus_get() == widget:
                continue

            # Update based on widget type
            if isinstance(widget, ttk.Label):
                # Read-only label
                current_text = widget.cget("text")
                new_text = self._format_value(new_value)
                if current_text != new_text:
                    widget.config(text=new_text)
            elif isinstance(widget, ttk.Entry):
                # Entry widget - only update if value actually changed
                current_value = widget.get()
                new_text = self._format_value(new_value)
                if current_value != new_text:
                    # Save cursor position
                    try:
                        cursor_pos = widget.index(tk.INSERT)
                    except tk.TclError:
                        cursor_pos = 0

                    widget.delete(0, tk.END)
                    widget.insert(0, new_text)

                    # Restore cursor position if possible
                    try:
                        widget.icursor(min(cursor_pos, len(new_text)))
                    except tk.TclError:
                        pass
            elif isinstance(widget, ttk.Checkbutton):
                # Checkbutton - update the variable
                if hasattr(self, '_bool_vars') and prop_name in self._bool_vars:
                    var = self._bool_vars[prop_name]
                    if isinstance(new_value, bool) and var.get() != new_value:
                        var.set(new_value)

    def _clear_properties(self) -> None:
        """Clear all property widgets from the panel."""
        for widget in self._content_frame.winfo_children():
            widget.destroy()
        self._property_widgets.clear()
        if hasattr(self, '_bool_vars'):
            self._bool_vars.clear()

    def _show_empty_state(self, message: str) -> None:
        """Show an empty state message.

        Args:
            message: Message to display
        """
        label = ttk.Label(
            self._content_frame,
            text=message,
            foreground="gray"
        )
        label.pack(pady=20)

    def _display_properties(self, properties: Dict[str, Any]) -> None:
        """Display properties in the panel.

        Args:
            properties: Dictionary of property names to values
        """
        # Sort properties by name for consistent display
        sorted_props = sorted(properties.items())
        field_length = max(len(name) for name in properties.keys()) + 2

        for prop_name, prop_value in sorted_props:
            readonly = prop_name in self._readonly_properties
            self._add_property_field(prop_name, prop_value, readonly, field_length)

    def _add_property_field(
        self,
        name: str,
        value: Any,
        readonly: bool = False,
        field_length: int = 20
    ) -> None:
        """Add a property field to the panel.

        Args:
            name: Property name
            value: Property value
            readonly: Whether the field is read-only
            field_length: Length of the label field
        """
        row_frame = ttk.Frame(self._content_frame)
        row_frame.pack(side=tk.TOP, fill=tk.X, pady=2)

        # Label
        label_widget = ttk.Label(
            row_frame,
            text=f"{name}:",
            width=field_length,
            anchor=tk.W
        )
        label_widget.pack(side=tk.LEFT, padx=(0, 5))

        # Value widget - type-based rendering
        value_widget = self._create_value_widget(
            row_frame,
            name,
            value,
            readonly
        )
        value_widget.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._property_widgets[name] = value_widget

    def _create_value_widget(
        self,
        parent: tk.Widget,
        prop_name: str,
        value: Any,
        readonly: bool
    ) -> tk.Widget:
        """Create an appropriate widget for the property value.

        Args:
            parent: Parent widget
            prop_name: Property name
            value: Property value
            readonly: Whether the widget should be read-only

        Returns:
            The created widget
        """
        # Convert value to string for display
        value_str = self._format_value(value)

        if readonly:
            # Read-only label
            widget = ttk.Label(
                parent,
                text=value_str,
                anchor=tk.W,
                foreground="#666666"
            )
        else:
            # Determine widget type based on value type
            if isinstance(value, bool):
                # Boolean -> Checkbutton
                var = tk.BooleanVar(value=value)
                widget = ttk.Checkbutton(
                    parent,
                    variable=var,
                    command=lambda: self._on_value_changed(prop_name, var.get())
                )
                # Store the variable separately to prevent garbage collection
                # Use a mapping to track boolean variables
                if not hasattr(self, '_bool_vars'):
                    self._bool_vars: Dict[str, tk.BooleanVar] = {}
                self._bool_vars[prop_name] = var
            elif isinstance(value, (int, float)):
                # Numeric -> Entry with validation
                widget = ttk.Entry(parent)
                widget.insert(0, value_str)
                widget.bind(
                    "<FocusOut>",
                    lambda e: self._on_entry_changed(prop_name, widget, type(value))
                )
                widget.bind(
                    "<Return>",
                    lambda e: self._on_entry_changed(prop_name, widget, type(value))
                )
            elif isinstance(value, str) and value.startswith("#") and len(value) in (7, 9):
                # Color hex value -> Entry with color preview
                widget = ttk.Entry(parent)
                widget.insert(0, value_str)
                widget.bind(
                    "<FocusOut>",
                    lambda e: self._on_entry_changed(prop_name, widget, str)
                )
                widget.bind(
                    "<Return>",
                    lambda e: self._on_entry_changed(prop_name, widget, str)
                )
                # TODO: Add color picker button
            else:
                # Default -> Entry
                widget = ttk.Entry(parent)
                widget.insert(0, value_str)
                widget.bind(
                    "<FocusOut>",
                    lambda e: self._on_entry_changed(prop_name, widget, str)
                )
                widget.bind(
                    "<Return>",
                    lambda e: self._on_entry_changed(prop_name, widget, str)
                )

        return widget

    def _format_value(self, value: Any) -> str:
        """Format a property value for display.

        Args:
            value: The value to format

        Returns:
            Formatted string representation
        """
        if value is None:
            return "None"
        elif isinstance(value, bool):
            return str(value)
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return value
        elif isinstance(value, (list, tuple)):
            return f"[{len(value)} items]"
        elif isinstance(value, dict):
            return f"{{{len(value)} items}}"
        else:
            return str(value)

    def _on_entry_changed(
        self,
        prop_name: str,
        widget: ttk.Entry,
        value_type: type
    ) -> None:
        """Handle entry widget value changes.

        Args:
            prop_name: Property name
            widget: The entry widget
            value_type: Expected type for the value
        """
        new_value_str = widget.get()

        try:
            # Convert string to appropriate type
            if value_type == int:
                new_value = int(new_value_str)
            elif value_type == float:
                new_value = float(new_value_str)
            else:
                new_value = new_value_str

            self._on_value_changed(prop_name, new_value)
        except ValueError:
            # Invalid value - revert to original
            if self._target_object:
                original_value = self._target_object.get_property(prop_name)
                widget.delete(0, tk.END)
                widget.insert(0, self._format_value(original_value))

    def _on_value_changed(self, prop_name: str, new_value: Any) -> None:
        """Handle property value changes.

        Args:
            prop_name: Property name
            new_value: New property value
        """
        # Update the object if available
        if self._target_object:
            try:
                self._target_object.set_property(prop_name, new_value)
            except Exception as e:
                print(f"Error setting property {prop_name}: {e}")

        # Call the callback if provided
        if self._on_property_changed:
            self._on_property_changed(prop_name, new_value)

    def get_property_value(self, prop_name: str) -> Optional[Any]:
        """Get the current value of a property from the widget.

        Args:
            prop_name: Property name

        Returns:
            Current value, or None if not found
        """
        widget = self._property_widgets.get(prop_name)
        if not widget:
            return None

        if isinstance(widget, ttk.Entry):
            return widget.get()
        elif isinstance(widget, ttk.Checkbutton):
            # Get the value from the stored BooleanVar
            if hasattr(self, '_bool_vars') and prop_name in self._bool_vars:
                return self._bool_vars[prop_name].get()
            return None
        elif isinstance(widget, ttk.Label):
            return widget.cget("text")

        return None

    def set_readonly(self, prop_name: str, readonly: bool = True) -> None:
        """Set a property as read-only or editable.

        Args:
            prop_name: Property name
            readonly: Whether the property should be read-only
        """
        if readonly:
            self._readonly_properties.add(prop_name)
        else:
            self._readonly_properties.discard(prop_name)

        # Refresh to apply changes
        self.refresh()

    @property
    def target_object(self) -> Optional[IHasProperties]:
        """Get the current target object."""
        return self._target_object

    @property
    def property_widgets(self) -> Dict[str, tk.Widget]:
        """Get the dictionary of property widgets."""
        return self._property_widgets


__all__ = ['TkPropertyPanel']

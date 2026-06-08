"""Reusable Property Panel for PyQt6 GUI.

This module provides a reusable PyQt6-based property panel for displaying
and editing object properties using the IHasProperties protocol.

``PropertyPanel`` extends ``TaskFrame`` and therefore ships with a title bar
and a built-in close button.  The underlying QWidget is exposed via
``panel.root``; use that reference wherever a bare widget is expected
(e.g. when adding to a ``QSplitter``).

Example Usage:
    ```python
    # Create a property panel
    panel = PropertyPanel(
        parent=parent_widget,
        title="Object Properties",
        on_property_changed=handle_property_change
    )

    # Display properties for an object that implements IHasProperties
    scene_obj = scene.get_scene_object("obj_001")
    panel.set_object(scene_obj, readonly_properties={"id", "type"})

    # Add the underlying widget to a QSplitter
    splitter.addWidget(panel.root)

    # Update when selection changes
    panel.refresh()
    ```
"""
import sys
from typing import Optional, Dict, Any, Callable, Mapping

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from pyrox.interfaces.base import IHasProperties
from pyrox.services import log
from pyrox.models.gui.frame import TaskFrame


class PropertyPanel(TaskFrame):
    """A reusable PyQt6 property panel widget.

    This panel displays properties from objects implementing IHasProperties.
    It supports both display-only and editable property fields, with automatic
    rendering based on property types.

    Features:
        - Displays properties from IHasProperties objects
        - Support for read-only and editable fields
        - Automatic type-based rendering (string, int, float, bool, list)
        - Scrollable content area for many properties
        - Property change callbacks

    Attributes:
        target_object: The current object being displayed
        property_widgets: Dictionary mapping property names to their widgets
        on_property_changed: Optional callback for property value changes
    """

    def __init__(
        self,
        parent: QWidget,
        title: str = "Properties",
        width: int = 250,
        on_property_changed: Optional[Callable[[str, Any], None]] = None,
    ):
        """Initialize the PropertyPanel.

        Args:
            parent: Parent widget
            title: Title displayed at the top of the panel
            width: Width of the panel in pixels
            on_property_changed: Optional callback function(property_name, new_value)
                                 called when a property is modified
        """
        super().__init__(name=title, parent=parent)
        self.root.setMinimumWidth(width)

        self._title = title
        self._target_object: Optional[IHasProperties] = None
        self._property_widgets: Dict[str, QWidget] = {}
        self._list_widgets: Dict[str, QListWidget] = {}
        self._on_property_changed = on_property_changed
        self._readonly_properties: set[str] = set()
        self._section_objects: Dict[str, Any] = {}
        self._prop_to_object: Dict[str, Any] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the property panel UI structure."""
        content_layout = self.content_frame.layout()
        content_layout.setContentsMargins(0, 0, 0, 0)  # type: ignore[union-attr]

        self._scroll_area = QScrollArea(self.content_frame)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self._properties_widget = QWidget()
        self._properties_layout = QVBoxLayout(self._properties_widget)
        self._properties_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._properties_layout.setContentsMargins(8, 8, 8, 8)
        self._properties_layout.setSpacing(4)

        self._scroll_area.setWidget(self._properties_widget)
        content_layout.addWidget(self._scroll_area)  # type: ignore[union-attr]

    def set_title(self, title: str) -> None:
        """Set the panel title.

        Args:
            title: New title text
        """
        self._title = title
        self._title_label.setText(title)

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
        self._sections: Optional[Dict[str, Dict[str, Any]]] = None
        self._section_objects = {}
        self._prop_to_object = {}
        self._readonly_properties = readonly_properties or set()
        self.refresh()

    def set_sections(
        self,
        sections: Dict[str, Dict[str, Any]],
        readonly_properties: Optional[set[str]] = None,
        section_objects: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """Display properties grouped into named sections with headers.

        This replaces the current panel contents.  Pass an ordered dict so
        sections appear in insertion order.

        Args:
            sections: Ordered mapping of section_title -> {prop_name: value}
            readonly_properties: Property names that should be read-only
            section_objects: Optional mapping of section_title -> IHasProperties
                             object that owns each section's properties.  When
                             supplied, edits are written back via set_property
                             on the correct object instead of being lost.
        """
        self._sections = sections
        self._target_object = None
        self._section_objects: Dict[str, Any] = dict(section_objects) if section_objects else {}
        self._readonly_properties = readonly_properties or set()
        # Build prop_name -> object reverse map for O(1) writeback lookups
        self._prop_to_object = {
            prop_name: obj
            for section_title, obj in self._section_objects.items()
            if section_title in sections
            for prop_name in sections[section_title]
        }
        self._refresh_sections()

    def _refresh_sections(self) -> None:
        """Rebuild the panel from the stored sections dict."""
        self._clear_properties()
        if not self._sections:
            self._show_empty_state("No object selected")
            return

        all_keys = [
            k for section in self._sections.values() for k in section
        ]
        field_length = max((len(k) for k in all_keys), default=10) + 2

        for section_title, props in self._sections.items():
            if not props:
                continue
            self._add_section_header(section_title)
            for prop_name, prop_value in sorted(props.items()):
                readonly = prop_name in self._readonly_properties
                self._add_property_field(prop_name, prop_value, readonly, field_length)

    def _add_section_header(self, title: str) -> None:
        """Add a bold section header row to the properties layout."""
        header = QLabel(title, self._properties_widget)
        font = QFont()
        font.setBold(True)
        header.setFont(font)
        header.setStyleSheet(
            "background-color: #3a3a3a; color: #ffffff; padding: 3px 6px; border-radius: 2px;"
        )
        self._properties_layout.addWidget(header)

    def refresh(self) -> None:
        """Refresh the property panel display from the current object.

        This performs a full rebuild of all widgets. Use update_values() instead
        for frequent updates to avoid flickering.
        """
        # If populated via set_sections, delegate to that path
        if getattr(self, '_sections', None) is not None:
            self._refresh_sections()
            return

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
        if not self._target_object and not self._prop_to_object:
            return

        try:
            if self._target_object:
                properties = self._target_object.get_properties()
            else:
                # Rebuild the merged properties dict from each section object
                properties = {}
                for section_title, obj in self._section_objects.items():
                    properties.update(obj.get_properties())
        except Exception:
            return

        for prop_name, widget in self._property_widgets.items():
            if prop_name not in properties:
                continue

            new_value = properties[prop_name]

            if isinstance(widget, QLabel):
                new_text = self._format_value(new_value)
                if widget.text() != new_text:
                    widget.setText(new_text)
            elif isinstance(widget, QLineEdit):
                if not widget.hasFocus():
                    new_text = self._format_value(new_value)
                    if widget.text() != new_text:
                        cursor = widget.cursorPosition()
                        widget.setText(new_text)
                        widget.setCursorPosition(min(cursor, len(new_text)))
            elif isinstance(widget, QCheckBox):
                if isinstance(new_value, bool) and widget.isChecked() != new_value:
                    widget.setChecked(new_value)
            elif prop_name in self._list_widgets:
                listbox = self._list_widgets[prop_name]
                if isinstance(new_value, (list, tuple)):
                    current_items = [
                        it.text() for i in range(listbox.count())
                        if (it := listbox.item(i)) is not None
                    ]
                    new_items = [str(item) for item in new_value]
                    if current_items != new_items:
                        selected_row = listbox.currentRow()
                        listbox.clear()
                        listbox.addItems(new_items)
                        if 0 <= selected_row < len(new_items):
                            listbox.setCurrentRow(selected_row)

    def _clear_properties(self) -> None:
        """Clear all property widgets from the panel."""
        while self._properties_layout.count():
            item = self._properties_layout.takeAt(0)
            if item is not None:
                w = item.widget()
                if w is not None:
                    w.deleteLater()
        self._property_widgets.clear()
        self._list_widgets.clear()

    def _show_empty_state(self, message: str) -> None:
        """Show an empty state message.

        Args:
            message: Message to display
        """
        label = QLabel(message)
        label.setStyleSheet("color: gray;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._properties_layout.addWidget(label)

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
            field_length: Length of the label field in characters (approx)
        """
        if isinstance(value, (list, tuple)):
            # Lists get a vertical block with label above
            block = QWidget(self._properties_widget)
            block_layout = QVBoxLayout(block)
            block_layout.setContentsMargins(0, 2, 0, 2)
            block_layout.setSpacing(2)

            label_widget = QLabel(f"{name}:", block)
            block_layout.addWidget(label_widget)

            value_widget = self._create_value_widget(block, name, value, readonly)
            block_layout.addWidget(value_widget)
            self._properties_layout.addWidget(block)
        else:
            row = QWidget(self._properties_widget)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(6)

            label_widget = QLabel(f"{name}:", row)
            label_widget.setFixedWidth(field_length * 7)
            label_widget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            row_layout.addWidget(label_widget)

            value_widget = self._create_value_widget(row, name, value, readonly)
            row_layout.addWidget(value_widget, 1)
            self._properties_layout.addWidget(row)

        self._property_widgets[name] = value_widget

    def _create_value_widget(
        self,
        parent: QWidget,
        prop_name: str,
        value: Any,
        readonly: bool
    ) -> QWidget:
        """Create an appropriate widget for the property value.

        Args:
            parent: Parent widget
            prop_name: Property name
            value: Property value
            readonly: Whether the widget should be read-only

        Returns:
            The created widget
        """
        value_str = self._format_value(value)

        if readonly:
            widget: QWidget = QLabel(value_str, parent)
            widget.setStyleSheet("color: #666666;")
        elif isinstance(value, (list, tuple)):
            widget = self._create_list_widget(parent, prop_name, value)
        elif isinstance(value, bool):
            widget = QCheckBox(parent)
            cast_widget: QCheckBox = widget  # type: ignore[assignment]
            cast_widget.setChecked(bool(value))
            cast_widget.toggled.connect(
                lambda checked, pn=prop_name: self._on_value_changed(pn, checked)
            )
        else:
            # str, int, float, color hex — all use QLineEdit
            value_type = type(value)
            widget = QLineEdit(value_str, parent)
            cast_line: QLineEdit = widget  # type: ignore[assignment]
            cast_line.editingFinished.connect(
                lambda pn=prop_name, w=cast_line, vt=value_type:
                    self._on_entry_changed(pn, w, vt)
            )
            # TODO: Add colour-picker button for hex colour strings

        return widget

    def _create_list_widget(
        self,
        parent: QWidget,
        prop_name: str,
        value: list | tuple,
    ) -> QWidget:
        """Create a list widget for list/tuple properties.

        Args:
            parent: Parent widget
            prop_name: Property name
            value: List/tuple value

        Returns:
            Container widget with list and add/remove controls
        """
        container = QWidget(parent)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(4)

        listbox = QListWidget(container)
        listbox.setFixedHeight(min(6, max(3, len(value))) * 20 + 4)
        listbox.addItems([str(item) for item in value])
        container_layout.addWidget(listbox)
        self._list_widgets[prop_name] = listbox

        # Add / remove controls
        btn_row = QWidget(container)
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(4)

        entry = QLineEdit(btn_row)
        btn_layout.addWidget(entry, 1)

        add_btn = QPushButton("+", btn_row)
        add_btn.setFixedWidth(28)
        add_btn.clicked.connect(
            lambda checked=False, pn=prop_name, lb=listbox, e=entry:
                self._on_list_add(pn, lb, e)
        )
        btn_layout.addWidget(add_btn)

        remove_btn = QPushButton("-", btn_row)
        remove_btn.setFixedWidth(28)
        remove_btn.clicked.connect(
            lambda checked=False, pn=prop_name, lb=listbox:
                self._on_list_remove(pn, lb)
        )
        btn_layout.addWidget(remove_btn)

        entry.returnPressed.connect(
            lambda pn=prop_name, lb=listbox, e=entry:
                self._on_list_add(pn, lb, e)
        )

        container_layout.addWidget(btn_row)
        return container

    def _on_list_add(self, prop_name: str, listbox: QListWidget, entry: QLineEdit) -> None:
        """Handle adding an item to a list property.

        Args:
            prop_name: Property name
            listbox: The list widget
            entry: The entry widget for new items
        """
        new_item = entry.text().strip()
        if not new_item:
            return
        listbox.addItem(new_item)
        entry.clear()
        self._update_list_property(prop_name, listbox)

    def _on_list_remove(self, prop_name: str, listbox: QListWidget) -> None:
        """Handle removing an item from a list property.

        Args:
            prop_name: Property name
            listbox: The list widget
        """
        row = listbox.currentRow()
        if row < 0:
            return
        listbox.takeItem(row)
        self._update_list_property(prop_name, listbox)

    def _update_list_property(self, prop_name: str, listbox: QListWidget) -> None:
        """Update the list property with current list widget values.

        Args:
            prop_name: Property name
            listbox: The list widget
        """
        items = [
            it.text() for i in range(listbox.count())
            if (it := listbox.item(i)) is not None
        ]
        self._on_value_changed(prop_name, items)

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
            if len(value) == 0:
                return "[empty]"
            return f"[{len(value)} items]"
        elif isinstance(value, dict):
            return f"{{{len(value)} items}}"
        else:
            return str(value)

    def _on_entry_changed(
        self,
        prop_name: str,
        widget: QLineEdit,
        value_type: type
    ) -> None:
        """Handle entry widget value changes.

        Args:
            prop_name: Property name
            widget: The line-edit widget
            value_type: Expected type for the value
        """
        new_value_str = widget.text()

        try:
            if value_type == int:
                new_value: Any = int(new_value_str)
            elif value_type == float:
                new_value = float(new_value_str)
            else:
                new_value = new_value_str
            self._on_value_changed(prop_name, new_value)
        except ValueError:
            # Restore the original value from whichever object owns this property
            owner = self._target_object or self._prop_to_object.get(prop_name)
            if owner:
                original_value = owner.get_property(prop_name)
                widget.setText(self._format_value(original_value))

    def _on_value_changed(self, prop_name: str, new_value: Any) -> None:
        """Handle property value changes.

        Args:
            prop_name: Property name
            new_value: New property value
        """
        # Determine which object owns this property
        owner: Optional[Any] = (
            self._target_object or self._prop_to_object.get(prop_name)
        )

        if owner:
            try:
                owner.set_property(prop_name, new_value)
            except Exception as e:
                log(self).warning(f"Error setting property '{prop_name}': {e}")

            # Keep the sections cache in sync so refresh() doesn't flicker back
            if self._sections is not None:
                for section in self._sections.values():
                    if prop_name in section:
                        section[prop_name] = new_value
                        break

            if self._on_property_changed:
                self._on_property_changed(prop_name, new_value)
        else:
            log(self).warning(f"Property '{prop_name}' changed to {new_value!r} but no target object is set.")

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

        if isinstance(widget, QLineEdit):
            return widget.text()
        elif isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QLabel):
            return widget.text()
        elif prop_name in self._list_widgets:
            lb = self._list_widgets[prop_name]
            return [
                it.text() for i in range(lb.count())
                if (it := lb.item(i)) is not None
            ]

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
    def property_widgets(self) -> Dict[str, QWidget]:
        """Get the dictionary of property widgets."""
        return self._property_widgets


__all__ = ['PropertyPanel']


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def create_demo_window() -> QWidget:
    """Create a standalone demo window for :class:`PropertyPanel`.

    Builds several mock objects that implement :class:`~pyrox.interfaces.protocols.IHasProperties`
    so every widget type (QLineEdit, QCheckBox, QListWidget, read-only QLabel,
    colour QLineEdit) and the property-change callback can be exercised without
    a live scene.

    Returns:
        QWidget: The configured root window.
    """

    # ------------------------------------------------------------------
    # Minimal IHasProperties stand-in
    # ------------------------------------------------------------------

    class _MockObject:
        """Simple dict-backed property object."""

        def __init__(self, label: str, props: Dict[str, Any]) -> None:
            self._label = label
            self._props: Dict[str, Any] = dict(props)

        def __repr__(self) -> str:
            return self._label

        def get_properties(self) -> Dict[str, Any]:
            return dict(self._props)

        def get_property(self, name: str) -> Any:
            return self._props.get(name)

        def set_property(self, name: str, value: Any) -> None:
            self._props[name] = value

    # ------------------------------------------------------------------
    # Sample objects with varied property types
    # ------------------------------------------------------------------

    _CONVEYOR = _MockObject("Conveyor Belt A", {
        "id":          "conv_001",          # read-only
        "name":        "Main Infeed Belt",
        "speed_m_s":   1.25,
        "width_mm":    600,
        "enabled":     True,
        "reversible":  False,
        "fill_color":  "#4a90d9",
        "tags":        ["infeed", "zone-1", "auto"],
    })

    _SENSOR = _MockObject("Proximity Sensor PX-01", {
        "id":           "sens_001",          # read-only
        "name":         "PX-01 Entry Gate",
        "range_mm":     250,
        "hysteresis":   0.05,
        "normally_open": True,
        "active":       False,
        "mount_angle":  0.0,
        "channels":     ["ch0", "ch1"],
    })

    _ROBOT = _MockObject("Pick & Place Robot A", {
        "id":              "rob_001",        # read-only
        "name":            "Robot A",
        "max_speed_mm_s":  800,
        "payload_kg":      2.5,
        "simulation_mode": True,
        "home_position":   [0.0, 0.0, 450.0],
        "highlight_color": "#e74c3c",
        "programs":        ["pick_program", "place_program", "home_routine"],
    })

    _OBJECTS = [_CONVEYOR, _SENSOR, _ROBOT]

    # ------------------------------------------------------------------
    # Root window
    # ------------------------------------------------------------------

    window = QWidget()
    window.setWindowTitle("PropertyPanel — Demo")
    window.resize(420, 580)

    main_layout = QVBoxLayout(window)
    main_layout.setContentsMargins(8, 8, 8, 0)
    main_layout.setSpacing(4)

    # ------------------------------------------------------------------
    # Toolbar: object switcher
    # ------------------------------------------------------------------

    toolbar = QWidget(window)
    toolbar_layout = QHBoxLayout(toolbar)
    toolbar_layout.setContentsMargins(0, 0, 0, 0)
    toolbar_layout.setSpacing(4)
    toolbar_layout.addWidget(QLabel("Inspect:"))

    status_label = QLabel("No change yet.")

    def _on_change(prop_name: str, new_value: Any) -> None:
        status_label.setText(f"Changed  '{prop_name}'  →  {new_value!r}")

    panel = PropertyPanel(
        parent=window,
        title="Properties",
        on_property_changed=_on_change,
    )

    def _load(obj: _MockObject) -> None:
        panel.set_title(str(obj))
        panel.set_object(obj, readonly_properties={"id"})  # type: ignore[arg-type]
        status_label.setText(f"Loaded: {obj}")

    for obj in _OBJECTS:
        btn = QPushButton(str(obj), toolbar)
        btn.clicked.connect(lambda checked=False, o=obj: _load(o))
        toolbar_layout.addWidget(btn)

    clear_btn = QPushButton("Clear", toolbar)
    clear_btn.clicked.connect(lambda: (panel.set_object(None), status_label.setText("Panel cleared.")))
    toolbar_layout.addWidget(clear_btn)
    toolbar_layout.addStretch()

    main_layout.addWidget(toolbar)

    # ------------------------------------------------------------------
    # Property panel
    # ------------------------------------------------------------------

    main_layout.addWidget(panel.root, 1)
    _load(_CONVEYOR)

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------

    sep = QFrame(window)
    sep.setFrameShape(QFrame.Shape.HLine)
    main_layout.addWidget(sep)
    main_layout.addWidget(status_label)

    return window


if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo_window = create_demo_window()
    demo_window.show()
    sys.exit(app.exec())

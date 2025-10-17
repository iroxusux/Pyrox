"""
Context Menu Widget for Pyrox applications.

This module provides a context menu (right-click menu) widget that allows easy
programmatic adding and removal of menu items for user interactions. The context
menu follows the Pyrox GUI patterns and theming system.
"""
from __future__ import annotations

import tkinter as tk
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

from pyrox.models.gui.meta import PyroxDefaultTheme


@dataclass
class MenuItem:
    """Configuration for a context menu item.

    Attributes:
        id (str): Unique identifier for the menu item.
        label (str): Text displayed in the menu item.
        command (Optional[Callable]): Function to call when item is selected.
        icon (Optional[str]): Icon path or Unicode character for the item.
        enabled (bool): Whether the item is initially enabled.
        visible (bool): Whether the item is initially visible.
        checkable (bool): Whether the item shows a checkbox.
        checked (bool): Initial checked state (if checkable).
        submenu (Optional[List[MenuItem]]): Nested submenu items.
        separator_before (bool): Whether to add a separator before this item.
        separator_after (bool): Whether to add a separator after this item.
        accelerator (Optional[str]): Keyboard shortcut display text.
    """
    id: str
    label: str
    command: Optional[Callable[[], None]] = None
    icon: Optional[str] = None
    enabled: bool = True
    visible: bool = True
    checkable: bool = False
    checked: bool = False
    submenu: Optional[List[MenuItem]] = None
    separator_before: bool = False
    separator_after: bool = False
    accelerator: Optional[str] = None


class PyroxContextMenu(tk.Menu):
    """
    A context menu widget for right-click operations.

    The context menu provides a popup menu interface where menu items can be
    dynamically added, removed, enabled, disabled, and organized. It follows
    the Pyrox theming system and integrates with the application's event system.

    Features:
    - Dynamic menu item management (add, remove, update)
    - Nested submenus support
    - Separators and grouping
    - Icon support
    - Checkable menu items
    - Keyboard accelerators
    - Event callbacks for item selection
    - Theme integration
    - Context-aware positioning
    """

    def __init__(
        self,
        parent,
        **kwargs
    ) -> None:
        """
        Initialize the PyroxContextMenu.

        Args:
            parent: Parent widget (optional, defaults to root window).
            **kwargs: Additional arguments passed to tk.Menu.
        """
        kwargs.update(self._get_theme_kwargs())

        super().__init__(
            parent,
            tearoff=kwargs.pop('tearoff', 0),
            **kwargs
        )

        self.parent_widget = parent
        self._menu_items: Dict[str, MenuItem] = {}
        self._item_widgets: Dict[str, int] = {}  # Maps item ID to menu index
        self._submenus: Dict[str, tk.Menu] = {}

        # Event callbacks
        self.on_item_selected: Optional[Callable[[str, MenuItem], None]] = None
        self.on_item_added: Optional[Callable[[str, MenuItem], None]] = None
        self.on_item_removed: Optional[Callable[[str], None]] = None
        self.on_menu_opened: Optional[Callable[[int, int], None]] = None
        self.on_menu_closed: Optional[Callable[[], None]] = None

    def _add_checkable_item(self, item: MenuItem):
        """Add a checkable menu item."""
        var = tk.BooleanVar(value=item.checked)
        self.add_checkbutton(
            label=self._format_label(item),
            command=lambda: self._handle_item_click(item.id),
            variable=var,
            state=tk.NORMAL if item.enabled else tk.DISABLED,
            accelerator=item.accelerator  # type: ignore
        )

    def _add_regular_item(self, item: MenuItem):
        """Add a regular menu item."""
        self.add_command(
            label=self._format_label(item),
            command=lambda: self._handle_item_click(item.id),
            state=tk.NORMAL if item.enabled else tk.DISABLED,
            accelerator=item.accelerator  # type: ignore
        )

    def _add_submenu_item(self, item: MenuItem):
        """Add a submenu item."""
        submenu = tk.Menu(self, **self._get_theme_kwargs())

        # Add submenu items
        for sub_item in item.submenu or []:
            if sub_item.separator_before:
                submenu.add_separator()

            if sub_item.checkable:
                var = tk.BooleanVar(value=sub_item.checked)
                submenu.add_checkbutton(
                    label=self._format_label(sub_item),
                    command=lambda sid=sub_item.id: self._handle_item_click(sid),
                    variable=var,
                    state=tk.NORMAL if sub_item.enabled else tk.DISABLED,
                    accelerator=sub_item.accelerator  # type: ignore
                )
            else:
                submenu.add_command(
                    label=self._format_label(sub_item),
                    command=lambda sid=sub_item.id: self._handle_item_click(sid),
                    state=tk.NORMAL if sub_item.enabled else tk.DISABLED,
                    accelerator=sub_item.accelerator  # type: ignore
                )

            if sub_item.separator_after:
                submenu.add_separator()

        self.add_cascade(
            label=self._format_label(item),
            menu=submenu,
            state=tk.NORMAL if item.enabled else tk.DISABLED
        )

        self._submenus[item.id] = submenu

    def _format_label(self, item: MenuItem) -> str:
        """Format the label with icon if available."""
        if item.icon:
            return f"{item.icon} {item.label}"
        return item.label

    def _get_theme_kwargs(self) -> dict:
        """Get theme-specific configuration for the menu."""
        theme = PyroxDefaultTheme()
        return {
            'tearoff': 0,
            'bg': theme.background,
            'fg': 'white',
            'activebackground': theme.background_hover,
            'activeforeground': 'white',
            'selectcolor': 'white',
            'relief': tk.FLAT,
            'borderwidth': 1,
            'font': ('Segoe UI', 9)
        }

    def _handle_item_click(self, item_id: str):
        """Handle menu item selection."""
        if item_id not in self._menu_items:
            return

        item = self._menu_items[item_id]

        # Execute item command
        if item.command:
            try:
                item.command()
            except Exception as e:
                print(f"Error executing menu item command: {e}")

        # Trigger callback
        if self.on_item_selected:
            self.on_item_selected(item_id, item)

    def _update_item_indices(self):
        """Update the item widget index mapping."""
        self._item_widgets.clear()
        # Note: This is a simplified approach; full implementation would need
        # to track separators and map items more precisely

    def add_item(self, item: MenuItem) -> bool:
        """
        Add a menu item to the context menu.

        Args:
            item: MenuItem configuration to add.

        Returns:
            True if the item was added successfully, False otherwise.
        """
        if item.id in self._menu_items:
            return False  # Item already exists

        # Store the menu item
        self._menu_items[item.id] = item

        # Add separator before if requested
        if item.separator_before:
            self.add_separator()

        # Handle different menu item types
        if item.submenu:
            self._add_submenu_item(item)
        elif item.checkable:
            self._add_checkable_item(item)
        else:
            self._add_regular_item(item)

        # Add separator after if requested
        if item.separator_after:
            self.add_separator()

        # Update item widget mapping
        self._update_item_indices()

        # Trigger callback
        if self.on_item_added:
            self.on_item_added(item.id, item)

        return True

    def bind_to_widget(self, widget: tk.Widget):
        """
        Bind this context menu to a widget's right-click event.

        Args:
            widget: Widget to bind the context menu to.
        """
        def show_menu(event):
            self.show_at_widget(widget, event)

        widget.bind("<Button-3>", show_menu)  # Right-click
        # Also bind to context menu key (usually Menu key or Shift+F10)
        widget.bind("<KeyPress-Menu>", lambda e: self.show_at_widget(widget, e))

    def check_item(self, item_id: str, checked: bool = True) -> bool:
        """Set the checked state of a checkable menu item."""
        if item_id not in self._menu_items:
            return False

        item = self._menu_items[item_id]
        if not item.checkable:
            return False

        item.checked = checked
        # Note: Full implementation would need to update the actual checkbox state
        return True

    def clear_all_items(self):
        """Remove all menu items."""
        item_ids = list(self._menu_items.keys())
        for item_id in item_ids:
            self.remove_item(item_id)

    def disable_item(self, item_id: str) -> bool:
        """Disable a menu item."""
        if item_id not in self._menu_items:
            return False

        self._menu_items[item_id].enabled = False
        if item_id in self._item_widgets:
            index = self._item_widgets[item_id]
            self.entryconfig(index, state=tk.DISABLED)
        return True

    def enable_item(self, item_id: str) -> bool:
        """Enable a menu item."""
        if item_id not in self._menu_items:
            return False

        self._menu_items[item_id].enabled = True
        if item_id in self._item_widgets:
            index = self._item_widgets[item_id]
            self.entryconfig(index, state=tk.NORMAL)
        return True

    def get_item(self, item_id: str) -> Optional[MenuItem]:
        """Get a menu item by ID."""
        return self._menu_items.get(item_id)

    def get_all_item_ids(self) -> List[str]:
        """Get all menu item IDs."""
        return list(self._menu_items.keys())

    def has_item(self, item_id: str) -> bool:
        """Check if a menu item exists."""
        return item_id in self._menu_items

    def remove_item(self, item_id: str) -> bool:
        """
        Remove a menu item from the context menu.

        Args:
            item_id: ID of the item to remove.

        Returns:
            True if the item was removed successfully, False otherwise.
        """
        if item_id not in self._menu_items:
            return False

        # Find the menu item index
        if item_id in self._item_widgets:
            index = self._item_widgets[item_id]
            self.delete(index)

        # Remove from tracking
        del self._menu_items[item_id]
        if item_id in self._item_widgets:
            del self._item_widgets[item_id]
        if item_id in self._submenus:
            del self._submenus[item_id]

        # Update indices
        self._update_item_indices()

        # Trigger callback
        if self.on_item_removed:
            self.on_item_removed(item_id)

        return True

    def show_at(self, x: int, y: int):
        """
        Show the context menu at the specified screen coordinates.

        Args:
            x: X coordinate on screen.
            y: Y coordinate on screen.
        """
        if self.on_menu_opened:
            self.on_menu_opened(x, y)

        try:
            self.tk_popup(x, y)
        except Exception as e:
            print(f"Error showing context menu: {e}")
        finally:
            # Note: Menu close callback would need proper event handling
            pass

    def show_at_event(self, event: tk.Event):
        """
        Show the context menu at the event's screen coordinates.

        Args:
            event: Mouse event containing coordinates.
        """
        self.show_at(event.x_root, event.y_root)

    def show_at_widget(self, widget: tk.Widget, event: tk.Event):
        """
        Show the context menu at the widget's position from an event.

        Args:
            widget: Widget that received the event.
            event: Mouse event containing coordinates.
        """
        x = widget.winfo_rootx() + event.x
        y = widget.winfo_rooty() + event.y
        self.show_at(x, y)

    def update_item(self, item_id: str, **kwargs) -> bool:
        """
        Update properties of an existing menu item.

        Args:
            item_id: ID of the item to update.
            **kwargs: Properties to update (label, enabled, etc.).

        Returns:
            True if the item was updated successfully.
        """
        if item_id not in self._menu_items:
            return False

        item = self._menu_items[item_id]

        # Update item properties
        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)

        # Refresh the menu item (simplified approach)
        # Full implementation would need to update the actual menu entry

        return True


# Convenience functions for common menu patterns

def create_standard_text_menu() -> List[MenuItem]:
    """Create a standard text editing context menu."""
    return [
        MenuItem(id="cut", label="Cut", accelerator="Ctrl+X", icon="✂"),
        MenuItem(id="copy", label="Copy", accelerator="Ctrl+C", icon="📋"),
        MenuItem(id="paste", label="Paste", accelerator="Ctrl+V", icon="📄"),
        MenuItem(id="separator1", label="", separator_before=True),
        MenuItem(id="select_all", label="Select All", accelerator="Ctrl+A", icon="🔘"),
    ]


def create_file_menu() -> List[MenuItem]:
    """Create a standard file operations context menu."""
    return [
        MenuItem(id="open", label="Open", icon="📁"),
        MenuItem(id="edit", label="Edit", icon="✏"),
        MenuItem(id="separator1", label="", separator_before=True),
        MenuItem(id="copy", label="Copy", icon="📋"),
        MenuItem(id="cut", label="Cut", icon="✂"),
        MenuItem(id="delete", label="Delete", icon="🗑"),
        MenuItem(id="separator2", label="", separator_before=True),
        MenuItem(id="properties", label="Properties", icon="⚙"),
    ]


def create_view_menu() -> List[MenuItem]:
    """Create a standard view operations context menu."""
    return [
        MenuItem(id="refresh", label="Refresh", accelerator="F5", icon="🔄"),
        MenuItem(id="separator1", label="", separator_before=True),
        MenuItem(id="view_large", label="Large Icons", checkable=True, icon="🔳"),
        MenuItem(id="view_small", label="Small Icons", checkable=True, icon="🔲"),
        MenuItem(id="view_list", label="List", checkable=True, icon="📋"),
        MenuItem(id="view_details", label="Details", checkable=True, checked=True, icon="📊"),
    ]


if __name__ == "__main__":
    """Test harness for PyroxContextMenu widget."""
    print("Starting PyroxContextMenu test...")

    # Create test window
    root = tk.Tk()
    root.title("PyroxContextMenu Test")
    root.geometry("800x600")
    root.configure(bg='#2b2b2b')

    # Main frame
    main_frame = tk.Frame(root, bg='#2b2b2b')
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Title
    title_label = tk.Label(main_frame, text="PyroxContextMenu Test",
                           bg='#2b2b2b', fg='white',
                           font=('Segoe UI', 16, 'bold'))
    title_label.pack(pady=(0, 10))

    # Test areas frame
    test_frame = tk.Frame(main_frame, bg='#3b3b3b', relief=tk.RAISED, bd=2)
    test_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    # Create different test areas with context menus
    areas_frame = tk.Frame(test_frame, bg='#3b3b3b')
    areas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Test area 1: Text operations
    text_frame = tk.LabelFrame(areas_frame, text="Text Area (Right-click for text menu)",
                               bg='#3b3b3b', fg='white', font=('Segoe UI', 10, 'bold'))
    text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    text_widget = tk.Text(text_frame, bg='#2b2b2b', fg='white',
                          font=('Consolas', 10), height=8,
                          insertbackground='white')
    text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    text_widget.insert('1.0', "Right-click here to see text context menu\n\n" +
                              "This area demonstrates text editing operations:\n" +
                              "• Cut, Copy, Paste\n" +
                              "• Select All\n\n" +
                              "Try selecting some text and right-clicking!")

    # Test area 2: File operations
    file_frame = tk.LabelFrame(areas_frame, text="File List Area (Right-click for file menu)",
                               bg='#3b3b3b', fg='white', font=('Segoe UI', 10, 'bold'))
    file_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    file_listbox = tk.Listbox(file_frame, bg='#2b2b2b', fg='white',
                              font=('Consolas', 9), height=6,
                              selectbackground='#4b4b4b')
    file_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    sample_files = ["document.txt", "image.png", "script.py", "config.json", "README.md"]
    for file in sample_files:
        file_listbox.insert(tk.END, file)

    # Test area 3: View operations
    view_frame = tk.LabelFrame(areas_frame, text="View Area (Right-click for view menu)",
                               bg='#3b3b3b', fg='white', font=('Segoe UI', 10, 'bold'))
    view_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    canvas = tk.Canvas(view_frame, bg='#1e1e1e', height=100)
    canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    canvas.create_text(canvas.winfo_reqwidth()//2, 50,
                       text="Canvas area - right-click for view options",
                       fill='white', font=('Segoe UI', 10))

    # Output area
    output_frame = tk.LabelFrame(main_frame, text="Event Log",
                                 bg='#2b2b2b', fg='white', font=('Segoe UI', 10, 'bold'))
    output_frame.pack(fill=tk.X, pady=(10, 0))

    output_text = tk.Text(output_frame, bg='#1e1e1e', fg='#00ff00',
                          font=('Consolas', 9), height=8)
    output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Create context menus
    text_menu = PyroxContextMenu(root)
    file_menu = PyroxContextMenu(root)
    view_menu = PyroxContextMenu(root)

    # Add initial text
    output_text.insert(tk.END, "PyroxContextMenu Test\n")
    output_text.insert(tk.END, "=" * 50 + "\n\n")
    output_text.insert(tk.END, "Instructions:\n")
    output_text.insert(tk.END, "• Right-click in different areas to see context menus\n")
    output_text.insert(tk.END, "• Select menu items to see events logged here\n")
    output_text.insert(tk.END, "• Each area has a different menu style\n\n")

    # Setup event callbacks
    def on_menu_item_selected(item_id: str, item: MenuItem):
        """Handle menu item selection events."""
        message = f"[{item_id}] '{item.label}' selected\n"
        output_text.insert(tk.END, message)
        output_text.see(tk.END)
        print(f"Menu item selected: {item_id}")

    def on_menu_opened(x: int, y: int):
        """Handle menu opened events."""
        message = f"Context menu opened at ({x}, {y})\n"
        output_text.insert(tk.END, message)
        output_text.see(tk.END)

    # Setup text menu
    text_items = create_standard_text_menu()
    for item in text_items:
        if item.id == "cut":
            item.command = lambda: output_text.insert(tk.END, "Cut operation performed\n")
        elif item.id == "copy":
            item.command = lambda: output_text.insert(tk.END, "Copy operation performed\n")
        elif item.id == "paste":
            item.command = lambda: output_text.insert(tk.END, "Paste operation performed\n")
        elif item.id == "select_all":
            item.command = lambda: [text_widget.tag_add(tk.SEL, "1.0", tk.END),
                                    output_text.insert(tk.END, "Select All performed\n")]  # type: ignore
        text_menu.add_item(item)

    # Setup file menu
    file_items = create_file_menu()
    for item in file_items:
        if item.id == "open":
            item.command = lambda: output_text.insert(tk.END, "Open file operation\n")
        elif item.id == "edit":
            item.command = lambda: output_text.insert(tk.END, "Edit file operation\n")
        elif item.id == "delete":
            item.command = lambda: output_text.insert(tk.END, "Delete file operation\n")
        elif item.id == "properties":
            item.command = lambda: output_text.insert(tk.END, "Show properties operation\n")
        file_menu.add_item(item)

    # Setup view menu
    view_items = create_view_menu()
    for item in view_items:
        if item.id == "refresh":
            item.command = lambda: output_text.insert(tk.END, "Refresh view operation\n")
        elif item.id.startswith("view_"):
            item.command = lambda vid=item.id: output_text.insert(tk.END, f"View changed to: {vid}\n")
        view_menu.add_item(item)

    # Connect callbacks
    text_menu.on_item_selected = on_menu_item_selected
    text_menu.on_menu_opened = on_menu_opened
    file_menu.on_item_selected = on_menu_item_selected
    file_menu.on_menu_opened = on_menu_opened
    view_menu.on_item_selected = on_menu_item_selected
    view_menu.on_menu_opened = on_menu_opened

    # Bind context menus to widgets
    text_menu.bind_to_widget(text_widget)
    file_menu.bind_to_widget(file_listbox)
    view_menu.bind_to_widget(canvas)

    # Control buttons frame
    control_frame = tk.Frame(main_frame, bg='#2b2b2b')
    control_frame.pack(fill=tk.X, pady=(10, 0))

    def add_custom_item():
        """Add a custom menu item to text menu."""
        import random
        item_id = f"custom_{random.randint(1000, 9999)}"
        item = MenuItem(
            id=item_id,
            label=f"Custom Item {item_id[-4:]}",
            command=lambda: output_text.insert(tk.END, f"Custom item {item_id} executed\n"),
            icon="⭐"
        )
        text_menu.add_item(item)
        output_text.insert(tk.END, f"Added custom item: {item_id}\n")

    def toggle_menu_items():
        """Toggle enabled state of some menu items."""
        items_to_toggle = ["cut", "copy", "paste"]
        for item_id in items_to_toggle:
            item = text_menu.get_item(item_id)
            if item:
                if item.enabled:
                    text_menu.disable_item(item_id)
                else:
                    text_menu.enable_item(item_id)
        output_text.insert(tk.END, "Toggled menu item states\n")

    # Control buttons
    tk.Button(control_frame, text="Add Custom Item",
              command=add_custom_item,
              bg='#4b4b4b', fg='white', relief=tk.FLAT,
              font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=5)

    tk.Button(control_frame, text="Toggle Items",
              command=toggle_menu_items,
              bg='#4b4b4b', fg='white', relief=tk.FLAT,
              font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=5)

    # Status bar
    status_frame = tk.Frame(main_frame, bg='#1e1e1e', relief=tk.SUNKEN, bd=1)
    status_frame.pack(fill=tk.X, pady=(5, 0))

    status_label = tk.Label(status_frame, text="PyroxContextMenu Test Ready",
                            bg='#1e1e1e', fg='white', anchor=tk.W,
                            font=('Consolas', 9))
    status_label.pack(fill=tk.X, padx=5, pady=2)

    print("PyroxContextMenu test window created")
    print("Text menu items:", text_menu.get_all_item_ids())
    print("File menu items:", file_menu.get_all_item_ids())
    print("View menu items:", view_menu.get_all_item_ids())

    # Start the test
    root.mainloop()

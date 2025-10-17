"""
Dynamic TreeView for displaying arbitrary objects with lazy loading.

This module provides a Tkinter TreeView widget that can display any Python object
(dictionaries, lists, custom objects) with recursive expansion and lazy loading
for efficient memory usage and performance.
"""
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, Set, Optional, List
from pyrox.models.gui.meta import PyroxDefaultTheme, PyroxThemeManager
from pyrox.models.gui.contextmenu import PyroxContextMenu, MenuItem


class PyroxTreeView(ttk.Treeview):
    """
    A TreeView widget that can display any Python object with lazy loading.

    Features:
    - Displays dictionaries, lists, tuples, sets, and custom objects
    - Recursive expansion of nested structures
    - Lazy loading - only loads attributes when expanded
    - Handles circular references safely
    - Customizable display formatting
    - Filters private attributes by default
    """

    def __init__(
        self,
        parent,
        show_private=False,
        max_items=100,
        **kwargs
    ) -> None:
        """
        Initialize the PyroxTreeView.

        Args:
            parent: Parent widget
            show_private: Whether to show private attributes (starting with _)
            max_items: Maximum number of items to show in collections
            **kwargs: Additional arguments passed to ttk.Treeview
        """
        # Set up columns if not specified
        if 'columns' not in kwargs:
            kwargs['columns'] = ('type', 'value')
        if 'show' not in kwargs:
            kwargs['show'] = 'tree headings'

        super().__init__(parent, **kwargs)

        # Configuration
        self.show_private = show_private
        self.max_items = max_items

        # Track expanded items and their objects to prevent circular references
        self._object_cache: Dict[str, Any] = {}
        self._visited_objects: Set[int] = set()
        self._placeholder_items: Set[str] = set()

        # Manage callbacks for selection events
        self._selection_callbacks: Set[Callable] = set()

        # Set up columns
        self.heading('#0', text='Name')
        self.heading('type', text='Type')
        self.heading('value', text='Value')

        self.column('#0', width=200, minwidth=100)
        self.column('type', width=100, minwidth=50)
        self.column('value', width=300, minwidth=100)

        # Bind events for lazy loading
        self.bind('<<TreeviewOpen>>', self._on_item_open)
        self.bind('<<TreeviewClose>>', self._on_item_close)
        self.bind('<Motion>', self._on_hover)
        self.bind('<Button-1>', self._on_click)
        self.bind('<Button-3>', self._on_right_click)

        # Style configuration
        self._configure_style()

    def _add_object_item(
        self,
        parent_id: str,
        name: str,
        obj: Any
    ) -> None:
        """Add a single object as a tree item."""
        # Create the item
        type_name = self._get_object_type_name(obj)
        value_preview = self._get_object_value_preview(obj)

        item_id = self.insert(
            parent_id,
            'end',
            text=name,
            values=(type_name, value_preview)
        )

        # Store the object for later access
        self._object_cache[item_id] = obj

        # Add a placeholder if the object is expandable
        if self._is_expandable(obj):
            self._create_placeholder(item_id)
            self._placeholder_items.add(item_id)

    def _call_callbacks(
        self,
        selected_object: Any,
        is_right_click: bool,
        context_menu: Optional[PyroxContextMenu] = None,
        event: Optional[tk.Event] = None
    ) -> None:
        """Invoke all registered selection callbacks."""
        for callback in self._selection_callbacks:
            callback(
                selected_object=selected_object,
                is_right_click=is_right_click,
                context_menu=context_menu,
                event=event
            )

    def _configure_style(self) -> None:
        PyroxThemeManager.ensure_theme_created()
        self._setup_hover_tags()

    def _create_context_menu(
        self,
    ) -> PyroxContextMenu:
        """Create a context menu for the tree view."""
        menu = PyroxContextMenu(self)

        # Example menu items - customize as needed
        menu.add_item(MenuItem(
            id='refresh',
            label='Refresh',
            command=lambda: self.refresh()
        ))

        return menu

    def _create_placeholder(self, parent_id: str):
        """Create a placeholder item to indicate that children can be loaded."""
        placeholder_id = self.insert(parent_id, 'end', text='Loading...',
                                     values=('', ''))
        return placeholder_id

    def _get_object_attributes(self, obj: Any) -> Dict[str, Any]:
        """Get the attributes of an object that should be displayed."""
        attributes = {}

        try:
            # Handle different types of objects
            if isinstance(obj, dict):
                return obj
            elif isinstance(obj, (list, tuple)):
                return {f"[{i}]": item for i, item in enumerate(obj)}
            elif isinstance(obj, set):
                return {f"item_{i}": item for i, item in enumerate(obj)}
            else:
                # For regular objects, get their attributes
                for name in dir(obj):
                    # Skip private attributes unless requested
                    if not self.show_private and name.startswith('_'):
                        continue

                    # Skip methods and built-in attributes we don't want to show
                    if name in ('__class__', '__doc__', '__module__', '__dict__'):
                        continue

                    try:
                        value = getattr(obj, name)
                        # Skip methods unless they're properties
                        if callable(value) and not isinstance(getattr(type(obj), name, None), property):
                            continue
                        attributes[name] = value
                    except Exception:
                        # Skip attributes that can't be accessed
                        continue

        except Exception:
            pass

        return attributes

    def _get_object_type_name(self, obj: Any) -> str:
        """Get a friendly name for the object's type."""
        obj_type = type(obj)
        if hasattr(obj_type, '__name__'):
            return obj_type.__name__
        return str(obj_type)

    def _get_object_value_preview(self, obj: Any) -> str:
        """Get a preview string for the object's value."""
        try:
            if obj is None:
                return "None"
            elif isinstance(obj, (str, int, float, bool)):
                return repr(obj)
            elif isinstance(obj, (list, tuple)):
                count = len(obj)
                return f"[{count} item{'s' if count != 1 else ''}]"
            elif isinstance(obj, dict):
                count = len(obj)
                return f"{{{count} item{'s' if count != 1 else ''}}}"
            elif isinstance(obj, set):
                count = len(obj)
                return f"{{{count} item{'s' if count != 1 else ''}}}"
            elif hasattr(obj, '__len__'):
                try:
                    count = len(obj)
                    return f"[{count} item{'s' if count != 1 else ''}]"
                except Exception:
                    pass

            # For other objects, try to get a meaningful representation
            str_repr = str(obj)
            if len(str_repr) > 50:
                return str_repr[:47] + "..."
            return str_repr
        except Exception as e:
            return f"<Error: {str(e)}>"

    def _is_expandable(self, obj: Any) -> bool:
        """Check if an object has expandable attributes or items."""
        try:
            if isinstance(obj, (dict, list, tuple, set)) and len(obj) > 0:
                return True

            # Check if it has attributes (excluding built-in types that we don't want to expand)
            if not isinstance(obj, (str, int, float, bool, type(None))):
                # Get attributes, filtering based on show_private setting
                attrs = self._get_object_attributes(obj)
                return len(attrs) > 0

            return False
        except Exception:
            return False

    def _on_click(
        self,
        event,
        is_right_click=False,
    ) -> None:
        """Handle mouse click events."""
        item = self.identify_row(event.y)
        if item:
            self.selection_set(item)

        self._call_callbacks(
            self.get_selected_object(),
            is_right_click,
            self._create_context_menu() if is_right_click else None,
            event
        )

    def _on_hover(self, event):
        """Handle mouse hover over items."""
        item = self.identify_row(event.y)
        self.tk.call(self, 'tag', 'remove', 'hover')
        self.tk.call(self, 'tag', 'add', 'hover', item)

    def _on_item_open(self, event):
        """Handle tree item expansion with lazy loading."""
        selection = self.selection()
        if not selection:
            return

        item_id = selection[0]

        # Check if this item has already been loaded
        if item_id not in self._placeholder_items:
            return

        # Remove the placeholder
        self._placeholder_items.discard(item_id)

        # Get the object associated with this item
        if item_id not in self._object_cache:
            return

        obj = self._object_cache[item_id]

        # Clear any existing children (should just be the placeholder)
        for child in self.get_children(item_id):
            self.delete(child)

        # Load the actual children
        self._populate_item_children(item_id, obj)

    def _on_item_close(self, event):
        """Handle tree item collapse."""
        # For now, we keep the loaded items even when collapsed
        # This could be enhanced to unload items for memory efficiency
        pass

    def _on_right_click(
        self,
        event,
        show_context_menu: bool = True
    ) -> None:
        """Handle right-click context menu (if needed)."""
        self._on_click(
            event,
            is_right_click=show_context_menu,
        )

    def _populate_item_children(self, parent_id: str, obj: Any):
        """Populate the children of a tree item."""
        # Prevent circular references
        obj_id = id(obj)
        if obj_id in self._visited_objects:
            self.insert(parent_id, 'end', text='<Circular Reference>',
                        values=('circular', 'Reference to parent object'))
            return

        self._visited_objects.add(obj_id)

        try:
            attributes = self._get_object_attributes(obj)

            # Limit the number of items shown
            items = list(attributes.items())
            if len(items) > self.max_items:
                items = items[:self.max_items]
                # Add an indicator for truncated items
                self.insert(parent_id, 'end',
                            text=f'... ({len(attributes) - self.max_items} more items)',
                            values=('info', 'Items truncated for performance'))

            for name, value in items:
                self._add_object_item(parent_id, name, value)

        finally:
            self._visited_objects.discard(obj_id)

    def _setup_hover_tags(self):
        """Set up tags for hover effects."""
        # Configure hover tag with your desired color
        self.tag_configure(
            'hover',
            foreground=PyroxDefaultTheme.foreground_hover,
            background=PyroxDefaultTheme.background_hover
        )

    def display_object(
        self,
        obj: Any,
        name: str = "Root",
        force_open: bool = False,
        soft_open_limit: int = 10
    ) -> None:
        """
        Display an object in the tree view.

        Args:
            obj: The object to display
            name: The name to show for the root item
        """
        # Clear existing items
        self.clear()

        # Add the root object
        self._add_object_item('', name, obj)

        # Auto-expand the root if it's a simple container
        root_items = self.get_children('')
        if root_items and (isinstance(obj, (dict, list)) and (len(obj) <= soft_open_limit) or force_open):
            self.item(root_items[0], open=True)
            if not self.selection():
                self.selection_set(root_items[0])
            if not self.selection():
                raise RuntimeError("Failed to select the root item.")
            # Trigger loading of children
            self._on_item_open(None)

    def clear(self):
        """Clear all items from the tree."""
        # Clear the tree
        for item in self.get_children():
            self.delete(item)

        # Clear internal caches
        self._object_cache.clear()
        self._visited_objects.clear()
        self._placeholder_items.clear()

    def refresh(self):
        """Refresh the current tree display."""
        # Get the current root object if any
        root_items = self.get_children('')
        if root_items:
            root_item = root_items[0]
            if root_item in self._object_cache:
                root_obj = self._object_cache[root_item]
                root_name = self.item(root_item, 'text')
                self.display_object(root_obj, root_name)

    def get_selected_object(self) -> Any:
        """Get the object associated with the currently selected item."""
        selection = self.selection()
        if selection:
            item_id = selection[0]
            return self._object_cache.get(item_id)
        return None

    def get_object_path(self, item_id: Optional[str] = None) -> List[str]:
        """Get the path from root to the specified item (or selected item)."""
        if item_id is None:
            selection = self.selection()
            if not selection:
                return []
            item_id = selection[0]

        path = []
        current = item_id
        while current:
            item_text = self.item(current, 'text')
            path.insert(0, item_text)
            current = self.parent(current)

        return path

    def subscribe_to_selection(
        self,
        callback: Callable[[Any, bool, Optional[PyroxContextMenu]], None]
    ) -> None:
        """
        Subscribe to selection change events.

        Args:
            callback: A function that takes (selected_object, is_right_click, context_menu)
        """
        self._selection_callbacks.add(callback)

    def unsubscribe_from_selection(
        self,
        callback: Callable[[Any, bool, Optional[PyroxContextMenu]], None]
    ) -> None:
        """
        Unsubscribe from selection change events.

        Args:
            callback: The previously subscribed callback function
        """
        self._selection_callbacks.discard(callback)


def create_demo_window():
    """Create a demo window showing the DynamicTreeView in action."""

    root = tk.Tk()
    root.title("Dynamic TreeView Demo")
    root.geometry("800x600")

    # Create a frame for the tree
    frame = ttk.Frame(root)
    frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Create the dynamic tree view
    tree = PyroxTreeView(frame, show_private=False)

    # Add scrollbars
    v_scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
    h_scrollbar = ttk.Scrollbar(frame, orient='horizontal', command=tree.xview)
    tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

    # Grid layout
    tree.grid(row=0, column=0, sticky='nsew')
    v_scrollbar.grid(row=0, column=1, sticky='ns')
    h_scrollbar.grid(row=1, column=0, sticky='ew')

    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    # Create some demo data
    class DemoClass:
        def __init__(self):
            self.name = "Demo Object"
            self.value = 42
            self.data = [1, 2, 3, {'nested': 'value'}]
            self.settings = {'debug': True, 'level': 'info'}

    demo_data = {
        'string': 'Hello World',
        'number': 123,
        'float': 3.14159,
        'boolean': True,
        'list': [1, 2, 3, [4, 5, {'deep': 'nested'}]],
        'dict': {
            'key1': 'value1',
            'key2': {'nested_key': 'nested_value'},
            'key3': [1, 2, 3]
        },
        'tuple': (1, 2, 'three'),
        'set': {1, 2, 3, 4, 5},
        'custom_object': DemoClass(),
        'none_value': None
    }

    # Display the demo data
    tree.display_object(demo_data, "Demo Data")

    # Add buttons for different demo objects
    button_frame = ttk.Frame(root)
    button_frame.pack(fill='x', padx=10, pady=5)

    def show_sys_modules():
        import sys
        tree.display_object(dict(list(sys.modules.items())[:20]), "sys.modules (first 20)")

    def show_demo_object():
        tree.display_object(DemoClass(), "Custom Object")

    def show_demo_data():
        tree.display_object(demo_data, "Demo Data")

    ttk.Button(button_frame, text="Show Demo Data", command=show_demo_data).pack(side='left', padx=5)
    ttk.Button(button_frame, text="Show Custom Object", command=show_demo_object).pack(side='left', padx=5)
    ttk.Button(button_frame, text="Show sys.modules", command=show_sys_modules).pack(side='left', padx=5)

    # Add status bar
    status_var = tk.StringVar()
    status_bar = ttk.Label(root, textvariable=status_var, relief='sunken')
    status_bar.pack(fill='x', side='bottom')

    def on_select(event):
        selected_obj = tree.get_selected_object()
        path = tree.get_object_path()
        if selected_obj is not None:
            status_var.set(f"Selected: {' → '.join(path)} | Type: {type(selected_obj).__name__}")
        else:
            status_var.set("No selection")

    tree.bind('<<TreeviewSelect>>', on_select)

    return root


if __name__ == "__main__":
    # Run the demo
    demo_window = create_demo_window()
    demo_window.mainloop()

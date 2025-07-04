from tkinter.ttk import Treeview

from .menu import ContextMenu
from pyrox.models.abc import PyroxObject, HashList
from pyrox.models.plc import Controller

UNITTEST_PLC_FILE = r'docs\controls\unittest.L5X'


class LazyLoadingTreeView(Treeview):
    """A Treeview that supports lazy loading of items.

    This class extends the standard ttk.Treeview to support lazy loading
    of items, which can be useful for large datasets where loading all
    items at once would be inefficient.
    """

    def __init__(self,
                 *args,
                 context_menu: ContextMenu = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._context_menu = context_menu or ContextMenu(self, tearoff=0)
        self.bind('<Button-3>', self.on_right_click)
        self.bind('<Button-1>', self.on_click)
        self._lazy_load_map = {}
        self._item_hash = {}

    @property
    def context_menu(self) -> ContextMenu:
        """Get the context menu associated with this treeview."""
        return self._context_menu

    def clear(self):
        """Clear the treeview and reset the lazy loading map."""
        if not self.winfo_exists():
            return
        for item in self.get_children():
            self.delete(item)
        self._lazy_load_map.clear()
        self._item_hash.clear()

    def on_click(self, event):
        """Handle click events to load items lazily."""
        item = self.identify_row(event.y)
        if item and self._lazy_load_map.get(item):
            self.load_children(item)
            del self._lazy_load_map[item]  # Remove item from map after loading

    def on_right_click(self, event):
        item = self.identify_row(event.y)
        if item:
            self.selection_set(item)
            self.focus(item)
        self._context_menu.on_right_click(event.x_root,
                                          event.y_root,
                                          item=item,
                                          data=self._item_hash.get(item, None))

    def load_children(self, item):
        """Load children for the given item."""
        for x in self.get_children(item):
            self.delete(x)
        self.populate_tree(item, self._lazy_load_map.get(item, {}))

    def populate_tree(self,
                      parent,
                      data,
                      container=None,
                      key=None):
        """
        Recursively populates a ttk.Treeview with keys and values from a dictionary, list, or custom class.
        Stores (container, key/index) for each node to allow modification.
        """
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, (dict, list, HashList, PyroxObject)):
                    node = self.insert(parent, 'end', text=str(k), values=['[...]'])
                    self._lazy_load_map[node] = v
                    self.insert(node, 'end', text='Empty...', values=['...'])
                else:
                    node = self.insert(parent, 'end', text=str(k), values=(v,))
                self._item_hash[node] = (data, k)  # Store reference to parent dict and key

        elif isinstance(data, (list, HashList)):
            for idx, item in enumerate(data):
                node_label = f"[{idx}]"
                if isinstance(item, dict):
                    node_label = item.get('@Name') or item.get('name') or item.get('Name') or node_label
                elif isinstance(item, PyroxObject):
                    node_label = item.name or item.description or node_label
                if isinstance(item, (dict, list, HashList, PyroxObject)):
                    node = self.insert(parent, 'end', text=node_label, values=['[...]'])
                    self._lazy_load_map[node] = item
                    self.insert(node, 'end', text='Empty...', values=['...'])
                else:
                    node = self.insert(parent, 'end', text=node_label, values=(item,))
                self._item_hash[node] = (data, idx)  # Store reference to parent list and index

        elif isinstance(data, PyroxObject):
            # Handle PyroxObject specifically
            for attr in data.gui_interface_attributes():
                value = getattr(data, attr)
                if isinstance(value, (dict, list, HashList, PyroxObject)):
                    node = self.insert(parent, 'end', text=attr, values=['[...]'])
                    self._lazy_load_map[node] = value
                    self.insert(node, 'end', text='Empty...', values=['...'])
                else:
                    node = self.insert(parent, 'end', text=attr, values=(value,))
                self._item_hash[node] = (data, attr)

        else:
            node = self.insert(parent, 'end', text=str(data), values=['...'])
            self._item_hash[node] = (container, key)  # fallback

    def update_node_value(self, node, new_value):
        """
        Update the value displayed in the Treeview node.

        Args:
            node: The Treeview node ID to update.
            new_value: The new value to set.
        """
        # Update the Treeview display (assumes value is in the first value column)
        self.item(node, values=(new_value,))


if __name__ == "__main__":
    from tkinter import Tk
    root = Tk()
    tree = LazyLoadingTreeView(root)
    tree.pack(expand=True, fill='both')
    controller = Controller.from_file(UNITTEST_PLC_FILE)
    tree.populate_tree('', controller.l5x_meta_data)
    root.mainloop()

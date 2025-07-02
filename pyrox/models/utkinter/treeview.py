from tkinter.ttk import Treeview

from pyrox.models.plc import Controller

UNITTEST_PLC_FILE = r'docs\controls\unittest.L5X'


class LazyLoadingTreeView(Treeview):
    """A Treeview that supports lazy loading of items.

    This class extends the standard ttk.Treeview to support lazy loading
    of items, which can be useful for large datasets where loading all
    items at once would be inefficient.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind('<Button-1>', self.on_click)
        self._dict_map = {}

    def clear(self):
        """Clear the treeview and reset the lazy loading map."""
        if not self.winfo_exists():
            return
        for item in self.get_children():
            self.delete(item)
        self._dict_map.clear()

    def on_click(self, event):
        """Handle click events to load items lazily."""
        item = self.identify_row(event.y)
        if item and self._dict_map.get(item):
            self.load_children(item)
            del self._dict_map[item]  # Remove item from map after loading

    def load_children(self, item):
        """Load children for the given item."""
        # Placeholder for actual loading logic
        for x in self.get_children(item):
            self.delete(x)
        self.populate_tree(item, self._dict_map.get(item, {}))

    def populate_tree(self,
                      parent,
                      data) -> None:
        """
        Recursively populates a ttk.Treeview with keys and values from a dictionary or list.

        Parameters:
        - parent: parent node ID in the tree (use '' for root)
        - data: dictionary or list to populate the tree with
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)) and len(value) > 0:
                    # insert value, then add placeholder for lazy loading
                    node = self.insert(parent, 'end', text=str(key), values=['[...]'])
                    self._dict_map[node] = value
                    self.insert(node, 'end', text='Loading...', values=['...'])
                else:
                    self.insert(parent, 'end', text=str(key), values=(value,))
        elif isinstance(data, list):
            for index, item in enumerate(data):
                node_label = "[???]"
                if isinstance(item, dict):
                    if '@Name' in item:
                        node_label = item['@Name']
                    elif 'name' in item:
                        node_label = item['name']
                    elif 'Name' in item:
                        node_label = item['Name']
                    else:
                        node_label = f"[{index}]"
                else:
                    node_label = f"[{index}]"

                if isinstance(item, (dict, list)) and len(item) > 0:
                    # insert value, then add placeholder for lazy loading
                    node = self.insert(parent=parent, index='end', text=node_label, values=['[...]'])
                    self._dict_map[node] = item
                    self.insert(node, 'end', text='Loading...', values=['...'])
                else:
                    self.insert(parent, 'end', text=node_label, values=(item,))


if __name__ == "__main__":
    from tkinter import Tk
    root = Tk()
    tree = LazyLoadingTreeView(root)
    tree.pack(expand=True, fill='both')
    controller = Controller.from_file(UNITTEST_PLC_FILE)
    tree.populate_tree('', controller.l5x_meta_data)
    root.mainloop()

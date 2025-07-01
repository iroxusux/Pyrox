from tkinter.ttk import Treeview

from pyrox.models.plc import Controller
from pyrox.services.utkinter import populate_tree

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

    def on_click(self, event):
        """Handle click events to load items lazily."""
        item = self.identify_row(event.y)
        if item and not self.get_children(item):
            self.load_children(item)

    def load_children(self, item):
        """Load children for the given item."""
        # Placeholder for actual loading logic
        populate_tree(self, item, self.get_children(item), fill_recursive=False)


if __name__ == "__main__":
    from tkinter import Tk
    root = Tk()
    tree = LazyLoadingTreeView(root)
    tree.pack(expand=True, fill='both')
    controller = Controller.from_file(UNITTEST_PLC_FILE)
    populate_tree(tree, '', controller.l5x_meta_data, fill_recursive=False)
    root.mainloop()

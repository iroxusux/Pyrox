from tkinter import Event, Widget
from typing import Optional, Union

from .menu import ContextMenu
from .meta import PyroxTreeview
from pyrox.models.abc.meta import PyroxObject
from pyrox.models.abc.list import HashList
from pyrox.models.gui.pyroxguiobject import PyroxGuiObject


class LazyLoadingTreeView(PyroxTreeview):
    """A Treeview that supports lazy loading of items.

    This class extends the standard ttk.Treeview to support lazy loading
    of items, which can be useful for large datasets where loading all
    items at once would be inefficient.
    """

    def __init__(
        self,
        master: Optional[Widget] = None,
        columns: Optional[list[str]] = None,
        show: str = 'tree',
        base_gui_class: type[PyroxGuiObject] = PyroxGuiObject,
        context_menu: Optional[ContextMenu] = None
    ) -> None:
        super().__init__(
            master=master,
            columns=columns,
            show=show
        )
        self._base_gui_class: type[PyroxGuiObject] = base_gui_class
        self._context_menu = context_menu or ContextMenu(master=self)
        self.bind('<Button-3>', self.on_right_click)
        self.bind('<<TreeviewOpen>>', self.on_expand)
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

    def on_expand(self, _: Event):
        """Handle expand events to load items lazily when about to be expanded."""
        # Get the item that's being expanded
        selection = self.selection()
        if not selection:
            return

        item = selection[0]

        # Check if this item needs lazy loading
        if item and self._lazy_load_map.get(item):
            self.load_children(item)
            del self._lazy_load_map[item]

    def on_right_click(self,
                       event: Event,
                       treeview_item: str = None):
        if not treeview_item:
            treeview_item = self.identify_row(event.y)
            if treeview_item:
                self.selection_set(treeview_item)
                self.focus(treeview_item)
        hash_item, lookup_attribute = self._item_hash.get(treeview_item, (None, None))
        self._context_menu.on_right_click(event=event,
                                          treeview_item=treeview_item,
                                          hash_item=hash_item,
                                          lookup_attribute=lookup_attribute)

    def load_children(self, item):
        """Load children for the given item."""
        for x in self.get_children(item):
            self.delete(x)
        self.populate_tree(item, self._lazy_load_map.get(item, {}))

    def _populate_base_node(
        self,
        parent,
        data: PyroxGuiObject
    ) -> None:
        """Helper method to populate a base GUI object node."""
        for edit_field in data.gui_interface_attributes():
            value = getattr(data.pyrox_object, edit_field.property_name, None)
            if isinstance(value, (dict, list, HashList, PyroxObject)):
                node = self.insert(parent, 'end', text=edit_field.display_name, values=['[...]'])
                self._lazy_load_map[node] = value
                self.insert(node, 'end', text='Empty...', values=['...'])
            else:
                node = self.insert(parent, 'end', text=edit_field.display_name, values=(value,))
            self._item_hash[node] = (data, edit_field.property_name)  # Store reference to parent object and property name

    def _populate_dict_node(
        self,
        parent,
        data: dict
    ) -> None:
        """Helper method to populate a dictionary node."""
        for k, v in data.items():
            if isinstance(v, (dict, list, HashList, PyroxObject)):
                node = self.insert(parent, 'end', text=str(k), values=['[...]'])
                self._lazy_load_map[node] = v
                self.insert(node, 'end', text='Empty...', values=['[...]'])
            else:
                node = self.insert(parent, 'end', text=str(k), values=(v,))
            self._item_hash[node] = (data, k)  # Store reference to parent dict and key

    def _populate_list_node(
        self,
        parent,
        data: Union[list, HashList]
    ) -> None:
        """Helper method to populate a list node."""
        for idx, item in enumerate(data):
            node_label = f"[{idx}]"
            if isinstance(item, dict):
                node_label = item.get('@Name') or item.get('name') or item.get('Name') or node_label
            elif isinstance(item, PyroxObject):
                node_label = getattr(item, 'name', None) or getattr(item, 'description', None) or node_label
            if isinstance(item, (dict, list, HashList, PyroxObject)):
                node = self.insert(parent, 'end', text=node_label, values=['[...]'])
                self._lazy_load_map[node] = item
                self.insert(node, 'end', text='Empty...', values=['...'])
            else:
                node = self.insert(parent, 'end', text=node_label, values=(item,))
            self._item_hash[node] = (data, idx)  # Store reference to parent list and index

    def populate_tree(
        self,
        parent,
        data,
        container=None,
        key=None
    ) -> None:
        """
        Recursively populates a ttk.Treeview with keys and values from a dictionary, list, or custom class.
        Stores (container, key/index) for each node to allow modification.
        """
        if isinstance(data, PyroxObject):
            data = self._base_gui_class.from_data(data)

        if isinstance(data, dict):
            self._populate_dict_node(parent, data)

        elif isinstance(data, (list, HashList)):
            self._populate_list_node(parent, data)

        elif isinstance(data, self._base_gui_class):
            self._populate_base_node(parent, data)

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
        self.item(node, values=(new_value,))

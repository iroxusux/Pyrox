from __future__ import annotations

from tkinter.ttk import Treeview


def populate_tree(tree: Treeview, parent, data):
    """
    Recursively populates a ttk.Treeview with keys and values from a dictionary or list.

    Parameters:
    - tree: ttk.Treeview widget
    - parent: parent node ID in the tree (use '' for root)
    - data: dictionary or list to populate the tree with
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                node = tree.insert(parent, 'end', text=str(key), values=['[...]'])
                populate_tree(tree, node, value)
            else:
                tree.insert(parent, 'end', text=str(key), values=(str(value).replace('\n', ' '),))
    elif isinstance(data, list):
        for index, item in enumerate(data):
            if isinstance(item, dict) and '@Name' in item:
                node_label = item['@Name']
            elif isinstance(item, dict) and 'name' in item:
                node_label = item['name']
            elif isinstance(item, dict) and 'Name' in item:
                node_label = item['Name']
            else:
                node_label = f"[{index}]"
            if node_label == '' or node_label is None:
                node_label = "[???]"
            if isinstance(item, (dict, list)):
                node = tree.insert(parent=parent, index='end', text=node_label, values=['[...]'])
                populate_tree(tree, node, item)
            else:
                tree.insert(parent, 'end', text=node_label, values=(str(item).replace('\n', ' '),))

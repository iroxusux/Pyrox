import tkinter as tk
from tkinter import ttk


def populate_tree(tree, parent, data):
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
                node = tree.insert(parent, 'end', text=str(key), values=('[...]'))
                populate_tree(tree, node, value)
            else:
                tree.insert(parent, 'end', text=str(key), values=(str(value),))
    elif isinstance(data, list):
        for index, item in enumerate(data):
            node_label = f"[{index}]"
            if isinstance(item, (dict, list)):
                node = tree.insert(parent, 'end', text=node_label, values=('[...]'))
                populate_tree(tree, node, item)
            else:
                tree.insert(parent, 'end', text=node_label, values=(str(item),))


# Example usage
if __name__ == "__main__":
    sample_data = {
        'Name': 'Alice',
        'Age': 30,
        'Hobbies': ['Reading', 'Chess'],
        'Education': {
            'Undergrad': 'Physics',
            'Graduate': {
                'Degree': 'PhD',
                'Field': 'Quantum Computing'
            }
        }
    }

    root = tk.Tk()
    root.title("Dictionary Tree Viewer")

    tree = ttk.Treeview(root, columns=('Value',), show='tree headings')
    tree.heading('#0', text='Key')
    tree.heading('Value', text='Value')
    tree.pack(fill='both', expand=True)

    populate_tree(tree, '', sample_data)

    root.mainloop()

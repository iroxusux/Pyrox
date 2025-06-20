def insert_to_treeview(tree, parent, obj, name="root"):
    """
    Recursively inserts public attributes of a class instance into a ttk.Treeview.
    Handles nested objects, lists, and dictionaries.
    """
    node = tree.insert(parent, "end", text=name)
    if isinstance(obj, (str, int, float, bool, type(None))):
        tree.insert(node, "end", text=str(obj))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            insert_to_treeview(tree, node, v, name=str(k))
    elif isinstance(obj, (list, tuple, set)):
        for idx, item in enumerate(obj):
            insert_to_treeview(tree, node, item, name=f"[{idx}]")
    elif hasattr(obj, "__dict__"):
        for attr, value in vars(obj).items():
            if not attr.startswith("_"):
                insert_to_treeview(tree, node, value, name=attr)
    else:
        tree.insert(node, "end", text=str(obj))

"""provide common dictionary services
    """


def insert_key_at_index(d, key, index, value=None):
    # Step 1: Extract items
    items = list(d.items())
    # Step 2: Insert new key-value at the desired index
    items.insert(index, (key, value))
    # Step 3: Clear the original dict
    d.clear()
    # Step 4: Re-insert all items (including the new one) back into the original dict
    d.update(items)


def key_index(d, key):
    try:
        return list(d.keys()).index(key)
    except ValueError:
        return -1  # or raise an exception if preferred


def remove_none_values_inplace(d):
    """
    Recursively remove all key-value pairs from a dictionary where the value is None,
    operating in-place (preserving the original dictionary's memory address).
    """
    keys_to_delete = [k for k, v in d.items() if v is None]
    for k in keys_to_delete:
        del d[k]
    for k, v in d.items():
        if isinstance(v, dict):
            remove_none_values_inplace(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    remove_none_values_inplace(item)

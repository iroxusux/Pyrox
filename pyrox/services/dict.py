"""provide common dictionary services
    """


def insert_key_at_index(d, key, index, value=None):
    if key in d:
        del d[key]
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


def rename_keys(d, key_map):
    """
    Rename keys in a dictionary based on a provided mapping.
    Supports circular renaming and preserves key positions.

    :param d: The original dictionary.
    :param key_map: A dictionary mapping old keys to new keys.
    """
    if not isinstance(d, dict):
        return

    # Handle circular renaming by using temporary keys first
    temp_mapping = {}
    items_list = list(d.items())

    # Step 1: Create a list of (old_key, new_key, value, original_index) for keys that need renaming
    renames_needed = []
    for i, (key, value) in enumerate(items_list):
        if key in key_map:
            new_key = key_map[key]
            renames_needed.append((key, new_key, value, i))

    if not renames_needed:
        # No renames needed at this level, but still process nested structures
        for v in d.values():
            if isinstance(v, dict):
                rename_keys(v, key_map)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        rename_keys(item, key_map)
        return

    # Step 2: Handle circular renaming by using temporary keys
    temp_key_prefix = "__TEMP_RENAME__"
    temp_counter = 0

    # First pass: rename to temporary keys to avoid conflicts
    for old_key, new_key, value, index in renames_needed:
        if old_key in d:  # Key might have been already renamed in circular case
            temp_key = f"{temp_key_prefix}{temp_counter}"
            temp_counter += 1
            temp_mapping[temp_key] = (new_key, value, index)
            d[temp_key] = d.pop(old_key)

    # Step 3: Rename from temporary keys to final keys
    for temp_key, (final_key, value, original_index) in temp_mapping.items():
        d[final_key] = d.pop(temp_key)

    # Step 4: Restore original order by reconstructing the dictionary
    # Create new items list with renamed keys in their original positions
    new_items = []
    renamed_keys_info = {original_index: (new_key, value)
                         for old_key, new_key, value, original_index in renames_needed}

    for i, (original_key, original_value) in enumerate(items_list):
        if i in renamed_keys_info:
            # Use the renamed key and value
            new_key, value = renamed_keys_info[i]
            new_items.append((new_key, value))
        elif original_key not in key_map:
            # Key wasn't renamed, keep original
            new_items.append((original_key, d[original_key]))
        # If original_key was renamed, it's already handled above

    # Rebuild the dictionary to preserve order
    d.clear()
    d.update(new_items)

    # Step 5: Recursively process nested structures
    for v in d.values():
        if isinstance(v, dict):
            rename_keys(v, key_map)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    rename_keys(item, key_map)

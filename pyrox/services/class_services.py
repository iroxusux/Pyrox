def class_to_dict(obj):
    """
    Recursively converts a class instance and its nested class instances
    into a dictionary.
    """
    if not hasattr(obj, '__dict__'):
        # If the object does not have a __dict__ (e.g., a basic type like int, str, list),
        # return it directly. Handle lists/tuples recursively if they contain objects.
        if isinstance(obj, (list, tuple)):
            return [class_to_dict(item) for item in obj]
        return obj

    result = {}
    for key, value in obj.__dict__.items():
        if key.startswith('__'):  # Skip built-in attributes
            continue

        if hasattr(value, '__dict__'):
            # If the value is another class instance, recurse
            result[key] = class_to_dict(value)
        elif isinstance(value, (list, tuple)):
            # If the value is a list or tuple, iterate and recurse on its elements
            result[key] = [class_to_dict(item) for item in value]
        else:
            # Otherwise, add the value directly
            result[key] = value
    return result

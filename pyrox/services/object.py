"""General object services.
"""
from typing import Any, Dict


def get_object_attributes(
    obj: Any,
    show_private: bool = False
) -> Dict[str, Any]:
    """Get the attributes of an object that should be displayed.

    Args:
        obj: The object to inspect.
        show_private: Whether to include private attributes (those starting with '_').
    Returns:
        A dictionary of attribute names and their corresponding values.
    """
    attributes = {}

    try:
        if isinstance(obj, dict):
            return obj
        if isinstance(obj, (list, tuple)):
            return {f"[{i}]": item for i, item in enumerate(obj)}
        if isinstance(obj, set):
            return {f"item_{i}": item for i, item in enumerate(obj)}

        for name in dir(obj):
            if not show_private and name.startswith('_'):
                continue

            if name in ('__class__', '__doc__', '__module__', '__dict__'):
                continue

            try:
                value = getattr(obj, name)
                if callable(value) and not isinstance(getattr(type(obj), name, None), property):
                    continue
                attributes[name] = value
            except Exception:  # pylint: disable=broad-except
                # Skip attributes that can't be accessed
                continue

    except Exception:  # pylint: disable=broad-except
        pass

    return attributes

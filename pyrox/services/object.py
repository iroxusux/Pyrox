"""General object services.
"""
from typing import Any, Dict, Optional, List
from pyrox.services import object as object_services


def is_builtin(obj: Any) -> bool:
    """Check if an object is of a built-in type.

    Args:
        obj: The object to check.
    Returns:
        True if the object is of a built-in type, False otherwise.
    """
    return isinstance(obj, (int, float, str, bool, bytes, bytearray, complex))


def is_iterable(obj: Any) -> bool:
    """Check if an object is iterable.

    Args:
        obj: The object to check.
    Returns:
        True if the object is iterable, False otherwise.
    """
    return hasattr(obj, '__iter__')


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
        if is_builtin(obj):
            return {}

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


def resolve_object_path(
    object_path: List[str],
    root_objects: List[Any],
) -> Optional[Any]:
    """Resolve an object path to get the actual object in memory.

    This function walks through a path like ['Controller1', 'tags', 'MyTag', 'description']
    and returns the final object or attribute value.

    Args:
        object_path: List of path segments to navigate
        root_objects: List of root objects to start searching from

    Returns:
        The resolved object/attribute, or None if not found

    Example:
        Given path ['Controller1', 'tags', 'MyTag', 'description']:
        1. Find 'Controller1' in root_objects
        2. Get the 'tags' attribute from Controller
        3. Find 'MyTag' in the tags collection
        4. Get the 'description' attribute from MyTag
        5. Return the description value
    """
    if not object_path or not root_objects:
        return None

    current_object = None
    current_search_space = root_objects

    for path_segment in object_path:

        found = False

        # If we have a current object, we're navigating its attributes
        if current_object is not None:
            attributes = object_services.get_object_attributes(current_object, show_private=False)

            if path_segment in attributes:
                current_object = attributes[path_segment]
                found = True

        # Otherwise, we're searching through a collection of objects
        else:
            for obj in current_search_space:
                # Try different ways to get the object's identifier
                obj_identifiers = []

                # Primary: use 'name' attribute if available
                if hasattr(obj, 'name'):
                    obj_identifiers.append(str(obj.name))

                # Secondary: use string representation
                obj_identifiers.append(str(obj))

                # Tertiary: use class name if it's a simple case
                if hasattr(obj, '__class__'):
                    obj_identifiers.append(obj.__class__.__name__)

                # Check if any identifier matches our path segment
                for identifier in obj_identifiers:
                    if identifier.lower() == path_segment.lower():
                        current_object = obj
                        found = True
                        break

                if found:
                    break

        if not found:
            return None

    return current_object


def resolve_object_path_with_parent(
    object_path: List[str],
    root_objects: List[Any],
) -> tuple[Optional[Any], Optional[Any], Optional[str]]:
    """Resolve an object path and return both the target and its parent.

    This is useful when you need to know both the selected object/attribute
    and the object that contains it (for editing operations).

    Args:
        object_path: List of path segments to navigate
        root_objects: List of root objects to start searching from

    Returns:
        Tuple of (target_object, parent_object, attribute_name)
        - target_object: The final resolved object/value
        - parent_object: The object that contains the target (None if target is a root object)
        - attribute_name: The attribute name if target is an attribute (None if target is an object)
    """
    if not object_path or not root_objects:
        return None, None, None

    if len(object_path) == 1:
        # Target is a root object
        target = resolve_object_path(object_path, root_objects)
        return target, None, None

    # Target is nested - resolve parent and get target from it
    parent_path = object_path[:-1]
    attribute_name = object_path[-1]

    parent_object = resolve_object_path(parent_path, root_objects)
    if parent_object is None:
        return None, None, None

    # Get the target from the parent's attributes
    attributes = object_services.get_object_attributes(parent_object, show_private=False)
    target_object = attributes.get(attribute_name)

    return target_object, parent_object, attribute_name

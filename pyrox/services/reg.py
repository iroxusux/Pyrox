"""Global registries that persist across reloads."""

from typing import Optional

# Global registry that won't be reset during class reloads
_generators = {}


def register_generator(
    object_type: str,
    generator_class
) -> None:
    """Register a generator class.

    Args:
        object_type (str): The type of object the generator handles.
        generator_class: The generator class to register.
    """
    _generators[object_type] = generator_class


def get_generator(object_type: str) -> Optional[type]:
    """Get a generator class by object type.

    Args:
        object_type (str): The type of object the generator handles.

    Returns:
        The generator class if found, else None.
    """
    return _generators.get(object_type)


def get_all_generators() -> dict:
    """Get all registered generators.

    Returns:
        dict: A copy of the dictionary of all registered generators.
    """
    return _generators.copy()


def clear_generators() -> None:
    """Clear all registered generators."""
    _generators.clear()

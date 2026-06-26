from typing import Any


def unsafe_assert_is_type(value: Any, type_check: type) -> None:
    """Common use type check assertion.
    Useful for single line, compact type checking to raise a common message to the user.
    Doesn't return anything, as it is unsafe and will stop execution in place.

    Args:
        value (Any): Value object to check.
        type_check (type): Type that the 'value' must be, otherwise a value is raised

    Raises:
        ValueError: If value is not type(type_check)
    """
    if not isinstance(value, type_check):
        raise ValueError(f'Expected type {str(type_check)}, but got {str(type(value))}!')

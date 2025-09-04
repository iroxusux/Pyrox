"""Decorators for pyrox environment.
"""

import warnings
import functools
from typing import Callable


def deprecated(reason: str = "This function is deprecated", version: str = None):
    """Decorator to mark functions as deprecated.

    Args:
        reason: Explanation of why it's deprecated and what to use instead
        version: Version when it will be removed

    Example:
    >>>
        @deprecated("Use new_function instead", version="2.0")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            message = f"{func.__name__} is deprecated"
            if reason:
                message += f": {reason}"
            if version:
                message += f" (will be removed in version {version})"

            warnings.warn(
                message,
                category=DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator

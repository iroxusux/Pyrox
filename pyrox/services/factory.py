"""Factory services for the pyrox application environment.
"""
import importlib
import sys
from pyrox.models.abc.factory import MetaFactory


def reload_factory_while_preserving_registered_types(
    factory: type[MetaFactory]
) -> None:
    """Reload the module of the given factory while preserving its registered types.

    Args:
        factory: The factory whose module should be reloaded.
    """
    # Store the currently registered types
    registered_types = factory._registered_types.copy()

    # Reload the module of the factory
    if hasattr(factory, '__module__'):
        module_name = factory.__module__
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        else:
            raise ImportError(f'Module {module_name} not found in sys.modules.')
    else:
        raise ValueError("Factory does not have a __module__ attribute.")

    # Restore the registered types
    factory._registered_types = registered_types

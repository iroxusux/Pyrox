"""Factory services for the pyrox application environment.
"""
import importlib
import sys
from pyrox.models.factory import MetaFactory


__all__ = [
    'reload_factory_module_while_preserving_registered_types',
]


def reload_factory_module_while_preserving_registered_types(
    factory: type[MetaFactory]
) -> type[MetaFactory]:
    """Reload the module of the given factory while preserving its registered types.

    Args:
        factory: The factory whose module should be reloaded.

    Returns:
        The reloaded factory class with restored registered types.
    """
    # Store the currently registered types and factory class name
    registered_types = factory._registered_types.copy()
    factory_class_name = factory.__name__

    # Reload the module of the factory
    if hasattr(factory, '__module__'):
        module_name = factory.__module__
        if module_name in sys.modules:
            reloaded_module = importlib.reload(sys.modules[module_name])
        else:
            raise ImportError(f'Module {module_name} not found in sys.modules.')
    else:
        raise ValueError("Factory does not have a __module__ attribute.")

    # Get the reloaded factory class from the reloaded module
    if hasattr(reloaded_module, factory_class_name):
        reloaded_factory = getattr(reloaded_module, factory_class_name)
    else:
        raise ImportError(f'Factory class {factory_class_name} attribute not found in reloaded module {module_name}.')

    if reloaded_factory is None:
        raise ImportError(f'Factory class {factory_class_name} returned as None from reloaded module {module_name}.')

    if not issubclass(reloaded_factory, MetaFactory):
        raise TypeError(f'Reloaded class {factory_class_name} is not a subclass of MetaFactory.')

    # Restore the registered types to the reloaded factory
    reloaded_factory._registered_types = registered_types

    return reloaded_factory

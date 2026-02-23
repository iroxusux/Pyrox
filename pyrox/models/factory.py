"""Factory metas for Pyrox framework base classes and utilities.
"""
import importlib
import sys
from typing import Any, Type

from pyrox.interfaces.protocols.meta import IFactoryMixinProtocolMeta
from pyrox.services.logging import log


__all__ = (
    'FactoryTypeMeta',
    'MetaFactory'
)


class MetaFactory:
    """Meta class for factory patterns.

    This meta class is used to create factories that can register and retrieve types.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._registered_types: dict[str, type] = {}

    @classmethod
    def _get_class_from_module(cls, module, class_name: str) -> Type | None:
        """Get a class from a module by name, handling various naming patterns."""
        # Direct lookup
        if hasattr(module, class_name):
            return getattr(module, class_name)
        return None

    @classmethod
    def _get_class_from_module_safe(cls, module, class_name: str) -> Type:
        """Get a class from a module by name, raising if not found."""
        klass = cls._get_class_from_module(module, class_name)
        if not klass:
            raise ImportError(f'Class {class_name} not found in module {module.__name__}.')
        return klass

    @classmethod
    def _reload_class_module(
        cls,
        class_type: Type[Any] | None
    ) -> Type:
        """Reload the module of the given class type to ensure the latest version is used.

        Args:
            class_type: The class type whose module should be reloaded.
        """
        if class_type is None:
            raise ValueError("class_type cannot be None")

        if not isinstance(class_type, type):
            raise TypeError("class_type must be a class type")

        module_name = class_type.__module__
        class_name = class_type.__name__

        if module_name not in sys.modules:
            raise ImportError(f'Module {module_name} not found in sys.modules.')

        try:
            importlib.reload(sys.modules[module_name])
            class_type = cls._get_class_from_module_safe(sys.modules[module_name], class_name)
            cls.register_type(class_type)
            log(cls).debug(f'Reloaded module {module_name} for class {class_name}.')
        except Exception as e:
            raise ImportError(f'Failed to reload module {module_name}: {e}') from e

        klass_type = cls.get_registered_type(class_name)
        if not klass_type:
            raise ImportError(f'Class {class_name} not found after reloading module {module_name}.')

        return klass_type

    @classmethod
    def create_instance(
        cls,
        type_name: str,
        *args,
        **kwargs
    ) -> Any | None:
        """Create an instance of the specified type."""
        type_class = cls.get_registered_types().get(type_name)
        if type_class:
            return type_class(*args, **kwargs)
        log(cls).warning(f'Type {type_name} not found in {cls.__name__}')
        return None

    @classmethod
    def get_available_types(cls) -> list[str]:
        """Get list of available type names."""
        return list(cls.get_registered_types().keys())

    @classmethod
    def get_registered_type(
        cls,
        type_name: str | object
    ) -> type | None:
        """Get the registered type class for the given type name.

        Args:
            type_name: The name of the type to retrieve (or an object to derive the name from).

        Returns:
            Optional[Type]: The class type if found, else None.
        """
        if isinstance(type_name, str):
            type_search = type_name
        elif isinstance(type_name, object):
            type_search = type_name.__class__.__name__
        else:
            raise ValueError('type_name must be a string or an object instance.')
        registered_types = cls.get_registered_types()
        return registered_types.get(type_search, None)

    @classmethod
    def get_registered_type_by_supporting_class(
        cls,
        supporting_class: object | str | type,
        reload_class: bool = False
    ) -> type | None:
        """Get the registered type class that supports the given class.

        Args:
            supporting_class: The class that the registered type should support.

        Returns:
            Optional[Type]: The class type if found, else None.

        Raises:
            ValueError: If supporting_class is not a string, type, or object instance.
        """
        if isinstance(supporting_class, (int, float, bool, list, dict, set, tuple)):
            raise ValueError('supporting_class must be a string, type, or an object instance.')
        if isinstance(supporting_class, type):
            compare = supporting_class.__name__
        elif isinstance(supporting_class, object) and not isinstance(supporting_class, str):
            compare = supporting_class.__class__.__name__
        elif isinstance(supporting_class, type):
            compare = supporting_class.__name__
        elif isinstance(supporting_class, str):
            compare = supporting_class
        else:
            raise RuntimeError('Unreachable code reached in get_registered_type_by_supporting_class.')

        for type_class in cls.get_registered_types().values():
            if not hasattr(type_class, 'supporting_class'):
                continue
            if not isinstance(type_class.supporting_class, type):
                continue

            if str(type_class.supporting_class) == compare:
                if reload_class:
                    return cls._reload_class_module(type_class)
                else:
                    return cls.get_registered_type(type_class.__name__)

            if str(type_class.supporting_class.__name__) == compare:
                if reload_class:
                    return cls._reload_class_module(type_class)
                else:
                    return cls.get_registered_type(type_class.__name__)
        return None

    @classmethod
    def get_registered_types(cls) -> dict[str, type]:
        """Get the registered types for this factory.

        Returns:
            dict: A dictionary of registered types.
        """
        return getattr(cls, '_registered_types', {})

    @classmethod
    def register_type(
        cls,
        type_class: Type[Any]
    ) -> None:
        """Register a type with the factory.

        Args:
            type_class: The class type to register.
        """
        base = getattr(cls, '_base_type', None)
        if base is not None and not issubclass(type_class, base):
            raise TypeError(f'Type {type_class} must be a subclass of {base} to be registered in {cls.__name__}.')

        if not hasattr(cls, '_registered_types'):
            raise RuntimeError(f'Factory {cls.__name__} is not properly initialized.')

        log(cls).debug(f'Registering type {type_class.__name__} with factory {cls.__name__}')
        cls._registered_types[type_class.__name__] = type_class


class FactoryTypeMeta(IFactoryMixinProtocolMeta):
    """Meta class for types that are used in factory patterns.
    """
    _bound_factory: Type[MetaFactory] | None = None

    def __new__(
        mcs,
        name,
        bases,
        namespace,
        **kwargs
    ) -> Type:
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        factory = getattr(mcs, '_bound_factory', None)
        if factory is None:
            return cls  # No factory bound, just return the class

        # First class through the door (the abstract base) anchors the allowed type
        if getattr(factory, '_base_type', None) is None:
            factory._base_type = cls

        # No abstract methods means this is a concrete class that should be registered
        if not cls.__abstractmethods__:
            factory.register_type(cls)

        return cls

    def __class_getitem__(cls, factory):
        """Returns a parameterized metaclass with the factory pre-bound.

        e.g. metaclass=FactoryTypeMeta[ApplicationTaskFactory]
        """
        if not isinstance(factory, type):
            raise TypeError(f'Expected a factory type, got {factory!r}')
        return type(cls.__name__, (cls,), {'_bound_factory': factory})

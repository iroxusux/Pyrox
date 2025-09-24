"""Factory metas for Pyrox framework base classes and utilities.
"""
from abc import ABCMeta
import importlib
import sys
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pyrox.models.abc.logging import Loggable


__all__ = (
    'FactoryTypeMeta',
    'MetaFactory'
)


T = TypeVar('T')


class MetaFactory(ABCMeta, Loggable):
    """Meta class for factory patterns.

    This meta class is used to create factories that can register and retrieve types.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._registered_types: Dict[str, type] = {}

    @classmethod
    def _get_class_from_module(cls, module, class_name: str) -> Optional[Type]:
        """Get a class from a module by name, handling various naming patterns."""
        # Direct lookup
        if hasattr(module, class_name):
            return getattr(module, class_name)
        return None

    @classmethod
    def _reload_class_module(
        cls,
        class_type: Optional[Type[T]]
    ) -> Type:
        """Reload the module of the given class type to ensure the latest version is used.

        Args:
            class_type: The class type whose module should be reloaded.
        """
        if class_type is None:
            raise ValueError("class_type cannot be None")

        module_name = class_type.__module__
        class_name = class_type.__name__

        if module_name in sys.modules:
            try:
                importlib.reload(sys.modules[module_name])
                class_type = cls._get_class_from_module(sys.modules[module_name], class_name)
                if not class_type:
                    raise ImportError(f'Class {class_name} not found in module {module_name} after reload.')
                cls.register_type(class_type)
                cls.logger.debug(f'Reloaded module {module_name} for class {class_name}.')
            except Exception as e:
                raise ImportError(f'Failed to reload module {module_name}: {e}') from e
        else:
            cls.logger.warning(f'Module {module_name} not found in sys.modules; cannot reload.')

        return class_type

    @classmethod
    def create_instance(
        cls,
        type_name: str,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """Create an instance of the specified type."""
        type_class = cls.get_registered_types().get(type_name)
        if type_class:
            return type_class(*args, **kwargs)
        cls.logger.warning(f'Type {type_name} not found in {cls.__name__}')
        return None

    @classmethod
    def get_available_types(cls) -> List[str]:
        """Get list of available type names."""
        return list(cls.get_registered_types().keys())

    @classmethod
    def get_registered_type(
        cls,
        type_name: Union[str, object]
    ) -> Optional[type]:
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
        return cls.get_registered_types().get(type_search, None)

    @classmethod
    def get_registered_type_by_supporting_class(
        cls,
        supporting_class: Union[object, str, Type]
    ) -> Optional[type]:
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
            supporting_class = supporting_class.__name__
        elif isinstance(supporting_class, object) and not isinstance(supporting_class, str):
            supporting_class = supporting_class.__class__.__name__
        elif isinstance(supporting_class, type):
            supporting_class = supporting_class.__name__

        if isinstance(supporting_class, str):
            for type_class in cls.get_registered_types().values():
                if not hasattr(type_class, 'supporting_class'):
                    continue
                if str(type_class.supporting_class) == supporting_class:
                    return cls._reload_class_module(type_class)
                if not isinstance(type_class.supporting_class, type):
                    continue
                if type_class.supporting_class.__name__ == supporting_class:
                    return cls._reload_class_module(type_class)
            return None
        else:
            raise ValueError('supporting_class must be a string, type, or an object instance.')

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
        type_class: Type[T]
    ) -> None:
        """Register a type with the factory.

        Args:
            type_class: The class type to register.
        """
        if not hasattr(cls, '_registered_types'):
            raise RuntimeError(f'Factory {cls.__name__} is not properly initialized.')

        type_name = getattr(type_class, 'supporting_class', type_class.__name__)
        if not type_name:
            type_name = type_class.__name__

        cls._registered_types[type_name] = type_class


F = TypeVar('F', bound=MetaFactory)


class FactoryTypeMeta(ABCMeta, Loggable, Generic[T, F]):
    """Meta class for types that are used in factory patterns.
    """
    supporting_class: Optional[Type] = None  # The class that this type supports, if any. i.e., 'Controller'
    supports_registering: bool = True  # Whether this class should be registered with a factory.

    def __init__(
        cls,
        name,
        bases,
        attrs,
        **_
    ) -> None:
        super().__init__(name, bases, attrs)

    def __new__(
        cls,
        name,
        bases,
        attrs,
        **_
    ) -> Type:
        new_cls = super().__new__(cls, name, bases, attrs)
        if new_cls.supports_registering is False:
            cls.logger.debug(f'FactoryTypeMeta: Class {name} does not support registering with a factory.')
            return new_cls

        factory = new_cls.get_factory()
        if factory is None:
            cls.logger.warning(f'FactoryTypeMeta: No factory found for class {name}.')
            return new_cls

        if (new_cls.__name__ != 'FactoryTypeMeta'):
            cls.logger.debug(f'FactoryTypeMeta: Registering class {name} with factory {factory.__name__}.')
            factory.register_type(new_cls)
        else:
            cls.logger.warning(
                f'FactoryTypeMeta: Class {name} is the factory class itself or does not subclass it.'
            )

        return new_cls

    @classmethod
    def get_factory(cls) -> Optional[Type[F]]:
        """Get the factory associated with this type, if any.

        Returns:
            Optional[MetaFactory]: The factory, or None if not set.
        """
        raise NotImplementedError("Subclasses must implement get_factory")

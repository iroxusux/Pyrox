"""Factory metas for Pyrox framework base classes and utilities.
"""
from abc import ABC, ABCMeta
from typing import Dict, Generic, List, Optional, Self, Type, TypeVar, Union

from .logging import Loggable


__all__ = (
    'FactoryTypeMeta',
    'MetaFactory'
)


T = TypeVar('T')
F = TypeVar('F', bound='MetaFactory')


class MetaFactory(ABC, Loggable):
    """Meta class for factory patterns.

    This meta class is used to create factories that can register and retrieve types.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._registered_types: Dict[str, Type[T]] = {}

    @classmethod
    def create_instance(
        cls,
        type_name: str,
        *args,
        **kwargs
    ) -> Optional[T]:
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
    ) -> Optional[Type[T]]:
        """Get the registered type class for the given type name.

        Args:
            type_name: The name of the type to retrieve (or an object to derive the name from).

        Returns:
            Optional[Type]: The class type if found, else None.
        """
        if isinstance(type_name, object):
            type_search = type_name.__class__.__name__
        elif isinstance(type_name, str):
            type_search = type_name
        else:
            raise ValueError('type_name must be a string or an object instance.')
        return cls.get_registered_types().get(type_search, None)

    @classmethod
    def get_registered_types(cls) -> dict[str, Type[T]]:
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
            cls._registered_types = {}

        if hasattr(type_class, 'generator_type'):
            type_name = getattr(type_class, 'generator_type')
        else:
            type_name = type_class.__name__

        cls._registered_types[type_name] = type_class


class FactoryTypeMeta(ABCMeta, Loggable, Generic[T, F]):
    """Meta class for types that are used in factory patterns.
    """
    supports_registering: bool = True

    def __new__(
        cls,
        name,
        bases,
        attrs,
        **_
    ) -> Type[Self]:
        new_cls = super().__new__(cls, name, bases, attrs)
        if new_cls.supports_registering is False:
            print(f'FactoryTypeMeta: Class {name} does not support registering with a factory.')
            return new_cls

        factory = new_cls.get_factory()
        if factory is None:
            print(f'FactoryTypeMeta: No factory found for class {name}.')
            return new_cls

        if (new_cls.__name__ != 'FactoryTypeMeta'):
            print(f'FactoryTypeMeta: Registering class {name} with factory {factory.__name__}.')
            factory.register_type(new_cls)
        else:
            print(
                f'FactoryTypeMeta: Class {name} is the factory class itself or does not subclass it.'
            )

        return new_cls

    @classmethod
    def get_class(cls) -> Optional[Type[T]]:
        """Get the type that this meta class was created for, if any.

        Returns:
            Optional[Type]: The type, or None if not set.
        """
        return cls

    @classmethod
    def get_factory(cls) -> Optional[Type[F]]:
        """Get the factory associated with this type, if any.

        Returns:
            Optional[MetaFactory]: The factory, or None if not set.
        """
        return None

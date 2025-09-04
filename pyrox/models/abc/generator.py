from abc import ABC, ABCMeta
from typing import Any, Dict, List, Optional, Self, Type
from .meta import Loggable


class GeneratorMeta(ABCMeta):
    """Metaclass for emulation generator registration."""

    _generators: Dict[str, Type[Self]] = {}

    def __new__(
        cls,
        name,
        bases,
        attrs,
        **_
    ) -> Type[Self]:
        new_cls = super().__new__(cls, name, bases, attrs)

        if name != 'GeneratorMeta' and hasattr(new_cls, 'generator_type'):
            cls._generators[new_cls.generator_type] = new_cls

        return new_cls

    @classmethod
    def get_generator(
        cls,
        generator_type: str
    ) -> Optional[Type[Self]]:
        """Get a registered generator.

        Args:
            generator_type (str): The type of generator to retrieve.

        Returns:
            Optional[Type[Self]]: The generator class if found, else None.
        """
        return cls._generators.get(generator_type, None)

    @classmethod
    def list_generators(cls) -> List[str]:
        """List all registered generator types.

        Returns:
            List[str]: A list of registered generator types.
        """
        return list(cls._generators.keys())


class BaseGenerator(Loggable, ABC, metaclass=GeneratorMeta):
    """Base class for emulation logic generators."""

    generator_type: str = None  # Override in subclasses

    def __init__(
        self,
        generator_object: Any
    ) -> None:
        super().__init__(name=f"{self.__class__.__name__}")
        self._generator_object = generator_object

    @property
    def generator_object(self) -> Any:
        return self._generator_object

    @staticmethod
    def get_generator(generator_object: Any) -> Self:
        generator: BaseGenerator = GeneratorFactory.create_generator(generator_object)
        if not isinstance(generator, BaseGenerator):
            raise ValueError('No valid generator found for this object type!')
        return generator


class GeneratorFactory:
    """Factory class for creating generic generators."""

    @staticmethod
    def create_generator(generator_object: Any) -> BaseGenerator:
        """Create an appropriate emulation generator for an object.

        Args:
            generator_object: The object to generate for

        Returns:
            BaseGenerator: The appropriate generator instance

        Raises:
            ValueError: If no suitable generator is found
        """
        # Try to determine object type from object class
        object_type = generator_object.__class__.__name__

        # Look for a registered generator
        generator_class = GeneratorMeta.get_generator(object_type)

        if generator_class:
            return generator_class(generator_object)

        # Fallback to base generator if no specific one found
        if hasattr(generator_object, 'generator_type'):
            generator_class = GeneratorMeta.get_generator(generator_object.generator_type)
            if generator_class:
                return generator_class(generator_object)

        raise ValueError(f"No emulation generator found for object type: {object_type}")

    @staticmethod
    def list_supported_types() -> List[str]:
        """List all supported controller types.

        Returns:
            List[str]: List of supported controller type names
        """
        return GeneratorMeta.list_generators()

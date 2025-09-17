"""Controller matcher module for pyrox applications.
"""
from __future__ import annotations
from typing import List, Self, Type
from pyrox.models.abc.meta import PyroxObject
from pyrox.models.abc.factory import FactoryTypeMeta, MetaFactory
from pyrox.utils import check_wildcard_patterns

from .plc import Controller


class ControllerMatcherFactory(MetaFactory):
    """Controller matcher factory."""


class ControllerMatcher(PyroxObject, metaclass=FactoryTypeMeta[Self, ControllerMatcherFactory]):
    """Abstract base class for controller matching strategies."""

    supports_registering = False  # This class can't be used to match anything

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.supports_registering = True  # Subclasses can be used to match

    @staticmethod
    def get_datatype_patterns() -> List[str]:
        """List of patterns to identify the controller by datatype."""
        raise NotImplementedError("Subclasses must implement this method")

    @staticmethod
    def get_module_patterns() -> List[str]:
        """List of patterns to identify the controller by module."""
        raise NotImplementedError("Subclasses must implement this method")

    @staticmethod
    def get_program_patterns() -> List[str]:
        """List of patterns to identify the controller by program."""
        raise NotImplementedError("Subclasses must implement this method")

    @staticmethod
    def get_safety_program_patterns() -> List[str]:
        """List of patterns to identify the controller by safety program."""
        raise NotImplementedError("Subclasses must implement this method")

    @staticmethod
    def get_tag_patterns() -> List[str]:
        """List of patterns to identify the controller by tag."""
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    def calculate_score(
        cls,
        controller_data: dict
    ) -> float:
        """Calculate a matching score (0.0 to 1.0, higher is better).

        Args:
            controller_data (dict): The controller data to evaluate.
        """
        score = 0.0
        if cls.check_controller_datatypes(controller_data):
            score += 0.2
        if cls.check_controller_modules(controller_data):
            score += 0.2
        if cls.check_controller_programs(controller_data):
            score += 0.2
        if cls.check_controller_safety_programs(controller_data):
            score += 0.2
        if cls.check_controller_tags(controller_data):
            score += 0.2
        return score

    @classmethod
    def can_match(
        cls,
    ) -> bool:
        """
        """
        return False

    @classmethod
    def get_class(cls) -> Self:
        return cls

    @classmethod
    def get_factory(cls):
        return ControllerMatcherFactory

    @classmethod
    def get_controller_constructor(
        cls,
    ) -> Type[Controller]:
        """Get the appropriate controller constructor for this matcher.

        Returns:
            Type[Controller]: The constructor for the appropriate controller type.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    def check_controller_datatypes(
        cls,
        controller_data: dict,
    ) -> bool:
        """Check if controller datatypes match controller pattern.

        Args:
            controller_data (dict): The controller data to evaluate.
        """
        return cls.check_dict_list_for_patterns(
            cls.get_controller_data_list(controller_data, 'DataType'),
            '@Name',
            cls.get_datatype_patterns()
        )

    @classmethod
    def check_controller_modules(
        cls,
        controller_data: dict,
    ) -> bool:
        """Check if controller modules match controller pattern."""
        return cls.check_dict_list_for_patterns(
            cls.get_controller_data_list(controller_data, 'Module'),
            '@Name',
            cls.get_module_patterns()
        )

    @classmethod
    def check_controller_programs(
        cls,
        controller_data: dict,
    ) -> bool:
        """Check if controller programs match controller pattern."""
        return cls.check_dict_list_for_patterns(
            cls.get_controller_data_list(controller_data, 'Program'),
            '@Name',
            cls.get_program_patterns()
        )

    @classmethod
    def check_controller_safety_programs(
        cls,
        controller_data: dict,
    ) -> bool:
        """Check if controller safety programs match controller pattern."""
        programs = cls.get_controller_data_list(controller_data, 'Program')
        safety_programs = [p for p in programs if p.get('@Class') == 'Safety']
        return cls.check_dict_list_for_patterns(
            safety_programs,
            '@Name',
            cls.get_safety_program_patterns()
        )

    @classmethod
    def check_controller_tags(
        cls,
        controller_data: dict,
    ) -> bool:
        """Check if controller tags match controller pattern."""
        return cls.check_dict_list_for_patterns(
            cls.get_controller_data_list(controller_data, 'Tag'),
            '@Name',
            cls.get_tag_patterns()
        )

    @classmethod
    def check_dict_list_for_patterns(
        cls,
        dict_list: List[dict],
        key: str,
        patterns: List[str]
    ) -> bool:
        """Check if any dictionary in the list has a value for the given key that matches any of the patterns.

        Args:
            dict_list (List[dict]): List of dictionaries to check.
            key (str): The key in the dictionary to check the value of.
            patterns (List[str]): List of patterns to match against the value.

        Returns:
            bool: True if any value matches any pattern, False otherwise.
        """
        if not patterns:
            return False
        cls.logger.debug(f"Checking patterns {patterns} in key '{key}' of dict list")
        result = check_wildcard_patterns(
            [item.get(key, '') for item in dict_list],
            patterns
        )
        cls.logger.debug(f"Pattern match result: {result}")
        return result

    @classmethod
    def get_controller_meta(
        cls,
        controller_data: dict
    ) -> dict:
        """Extract relevant metadata for the controller.

        Args:
        something
        """
        if not controller_data:
            raise ValueError("No controller data provided")
        return controller_data.get('RSLogix5000Content', {}).get('Controller', {})

    @classmethod
    def get_controller_data_list(
        cls,
        controller_data: dict,
        data_string: str,
    ) -> List[dict]:
        """Extract the list of data from the controller data.

        Args:
            controller_data (dict): The controller data to extract from.
            data_string (str): The key string to extract (e.g., 'Program', 'Tag').

        Returns:
            List[dict]: The list of data dictionaries.
        """
        controller_meta = cls.get_controller_meta(controller_data)
        data_list = controller_meta.get(f'{data_string}s', {}).get(data_string, [])
        if isinstance(data_list, dict):
            data_list = [data_list]
        return data_list

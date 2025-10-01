"""Warehouse module for pyrox module applications.
"""
from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING, Union
from pyrox.models.abc import FactoryTypeMeta, HashList, MetaFactory, PyroxObject
from pyrox.services.logging import log


if TYPE_CHECKING:
    from ..plc import Module, ModuleControlsType, Rung

__all__ = (
    'ModuleWarehouse',
    'ModuleWarehouseFactory',
)


class ModuleWarehouseFactory(MetaFactory):
    """Factory for creating ModuleWarehouse instances."""

    @classmethod
    def get_all_known_modules(cls) -> List[type[IntrospectiveModule]]:
        """Get all known module CLASSES from all registered warehouses.

        Returns:
            List[type[IntrospectiveModule]]: List of all known module classes.
        """
        module_classes = []
        warehouses = cls.get_registered_types()

        for warehouse_name, warehouse_cls in warehouses.items():
            if warehouse_cls:
                module_classes.extend(warehouse_cls.get_known_module_classes())
            else:
                log(cls).warning(f'Warehouse class for {warehouse_name} is None')

        return module_classes

    @classmethod
    def get_modules_by_type(
        cls,
        module_type: ModuleControlsType
    ) -> List[IntrospectiveModule]:
        """Get all modules of a specific type from all registered warehouses.

        Args:
            module_type (ModuleControlsType): The type of module to filter by.

        Returns:
            List[IntrospectiveModule]: List of modules matching the specified type.
        """
        modules = []
        warehouses = cls.get_registered_types()

        for warehouse_name, warehouse_cls in warehouses.items():
            if warehouse_cls:
                modules.extend(warehouse_cls.get_modules_by_type(module_type))
            else:
                cls.get_logger().warning(f'Warehouse class for {warehouse_name} is None')

        return modules

    @classmethod
    def filter_modules_by_type(
        cls,
        modules: Union[List[Module], HashList[Module]],
        module_type: ModuleControlsType
    ) -> List[IntrospectiveModule]:
        """Filter a list of modules by a specific type.

        Args:
            modules (List[IntrospectiveModule]): The list of modules to filter.
            module_type (ModuleControlsType): The type of module to filter by.

        Returns:
            List[IntrospectiveModule]: List of modules matching the specified type.
        """
        filtered = []
        for module in modules:
            if not module.introspective_module:
                cls.get_logger().warning(f'Module {module} has no introspective_module, skipping...')
                continue
            if module.introspective_module.controls_type != module_type:
                continue
            filtered.append(module.introspective_module)
        return filtered


class ModuleWarehouse(MetaFactory, metaclass=FactoryTypeMeta['ModuleWarehouse', ModuleWarehouseFactory]):
    """Class used to manage a collection of IntrospectiveModules.

    Can filter types, catalog numbers, etc.
    """

    supports_registering = False  # This class can't be used to match anything

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.supports_registering = True  # Subclasses can be used to match

    @classmethod
    def get_factory(cls) -> ModuleWarehouseFactory:
        return ModuleWarehouseFactory

    @classmethod
    def get_known_module_classes(cls) -> list[type[IntrospectiveModule]]:
        """Get all known module classes from this warehouse.

        Returns:
            list[type[IntrospectiveModule]]: List of IntrospectiveModule subclasses.
        """
        # This should return the actual IntrospectiveModule subclass types
        # that this warehouse knows about. You'll need to implement this
        # based on how your warehouses store their module types.
        classes = []
        for known in cls.get_registered_types().values():
            if issubclass(known, IntrospectiveModule):
                classes.append(known)
        return classes

    @classmethod
    def get_known_modules(cls) -> list[IntrospectiveModule]:
        """Get instances of all known modules from this warehouse."""
        module_classes = cls.get_known_module_classes()
        return [module_cls() for module_cls in module_classes]

    @classmethod
    def get_modules_by_type(
        cls,
        module_type: ModuleControlsType
    ) -> List[IntrospectiveModule]:
        """Get all modules of a specific type from this warehouse.

        Args:
            module_type (ModuleControlsType): The type of module to filter by.

        Returns:
            List[IntrospectiveModule]: List of modules matching the specified type.
        """
        modules = cls.get_known_modules()

        return [
            module for module in modules
            if module.module_type == module_type
        ]


class IntrospectiveModule(PyroxObject):
    """Introspective Module for a rockwell plc.
    This is a wrapper around the Module class to provide introspection capabilities.
    Such as, a Siemens G115Drive, or a Rockwell 1756-L85E controller.
    It is used to extend capabilities of known modules, or to provide a way to introspect unknown modules.
    """

    def __init__(
        self,
        module: Optional[Module] = None
    ) -> None:
        self._module = module

    @property
    def catalog_number(self) -> str:
        """The catalog number of the module."""
        raise NotImplementedError('This method should be implemented by the subclass.')

    @property
    def config_cxn_point(self) -> str:
        """The configuration connection point of the module."""
        return ''

    @property
    def config_size(self) -> str:
        """The configuration size of the module."""
        raise NotImplementedError('This method should be implemented by the subclass.')

    @property
    def controls_type(cls) -> ModuleControlsType:
        """The controls type of the module."""
        return ModuleControlsType.UNKNOWN

    @property
    def input_cxn_point(self) -> str:
        """The input connection point of the module."""
        raise NotImplementedError('This method should be implemented by the subclass.')

    @property
    def input_size(self) -> str:
        """The input size of the module."""
        raise NotImplementedError('This method should be implemented by the subclass.')

    @property
    def module(self) -> Optional[Module]:
        """The module being wrapped by the IntrospectiveModule."""
        return self._module

    @module.setter
    def module(self, value: Module) -> None:
        if not isinstance(value, Module):
            raise ValueError('Module must be an instance of Module.')
        self._module = value

    @property
    def output_cxn_point(self) -> str:
        """The output connection point of the module."""
        raise NotImplementedError('This method should be implemented by the subclass.')

    @property
    def output_size(self) -> str:
        """The output size of the module."""
        raise NotImplementedError('This method should be implemented by the subclass.')

    @property
    def type_(self) -> str:
        """Get the type of the module."""
        return self.__class__.__name__

    @classmethod
    def from_meta_data(
        cls,
        module: Module,
        lazy_match_catalog: Optional[bool] = False
    ) -> IntrospectiveModule:
        """Create an IntrospectiveModule from a Module instance.
        This method will attempt to match the module to a known IntrospectiveModule subclass

        Args:
            module (Module): The Module instance to wrap.
            lazy_match_catalog (bool, optional): If True, will attempt to match the catalog number
                using a substring match if an exact match is not found. Defaults to False.

        Returns:
            IntrospectiveModule: An instance of the matched IntrospectiveModule subclass,
                or a generic IntrospectiveModule if no match is found.

        Raises:
            ValueError: If the module is None.
        """
        if not module:
            raise ValueError('Module is required to create an IntrospectiveModule.')

        for m in ModuleWarehouseFactory.get_all_known_modules():
            mod = m(module)
            if lazy_match_catalog and module.catalog_number and module.catalog_number != 'ETHERNET-MODULE':
                if mod.catalog_number in module.catalog_number:
                    return mod
            if mod.catalog_number != module.catalog_number:
                continue
            if mod.input_cxn_point != module.input_connection_point:
                continue
            if mod.output_cxn_point != module.output_connection_point:
                continue
            if mod.config_cxn_point != module.config_connection_point:
                continue
            if mod.input_size != module.input_connection_size:
                continue
            if mod.output_size != module.output_connection_size:
                continue
            if mod.config_size != module.config_connection_size:
                continue
            return mod

        cls.log().warning(
            'No matching module type found for %s, enable debug for more info.',
            module.name
        )
        cls.log().debug('Module details: %s', {
            'ModuleName': module.name,
            'CatalogNumber': module.catalog_number,
            'InputCxnPoint': module.input_connection_point,
            'OutputCxnPoint': module.output_connection_point,
            'ConfigCxnPoint': module.config_connection_point,
            'InputSize': module.input_connection_size,
            'OutputSize': module.output_connection_size,
            'ConfigSize': module.config_connection_size,
        })
        return cls(module)

    @classmethod
    def get_controls_type(cls) -> ModuleControlsType:
        """Get the controls type of the module."""
        obj = cls()
        return obj.controls_type

    @classmethod
    def get_required_imports(cls) -> List[tuple[str, List[str]]]:
        """Get the required datatype imports for the module.

        Returns:
            list[tuple[str, str]]: List of tuples containing the module and class name to import.
        """
        return []

    def get_required_safety_rungs(
        self,
        **__,
    ) -> list[Rung]:
        """Get the required safety rungs for the module.

        Returns:
            list[Rung]: List of rungs.
        """
        return []

    def get_required_standard_rungs(
        self,
        **__,
    ) -> list[Rung]:
        """Get the required standard rungs for the module.

        Returns:
            list[Rung]: List of rungs.
        """
        return []

    def get_required_standard_to_safety_mapping(
        self,
        **__,
    ) -> tuple[str, str]:
        """Get the required standard to safety mapping for the module.

        Returns:
            dict[str, str]: Dictionary of standard to safety mapping.
        """
        return self.get_standard_input_tag_name(), self.get_safety_input_tag_name()

    @classmethod
    def get_required_tags(
        cls,
        **__,
    ) -> list[dict]:
        """Get the required tags for the module.

        Returns:
            list[dict]: List of tag dictionaries.
        """
        return []

    def get_safety_input_tag_name(self) -> str:
        """Get the safety tag name for the module.

        Returns:
            str: Safety tag name.
        """
        return ''

    def get_safety_output_tag_name(self) -> str:
        """Get the safety output tag name for the module.

        Returns:
            str: Safety output tag name.
        """
        return ''

    def get_standard_input_tag_name(self) -> str:
        """Get the standard tag name for the module.

        Returns:
            str: Standard tag name.
        """
        return ''

    def get_standard_output_tag_name(self) -> str:
        """Get the standard output tag name for the module.

        Returns:
            str: Standard output tag name.
        """
        return ''

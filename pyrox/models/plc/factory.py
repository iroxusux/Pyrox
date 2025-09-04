
from typing import List, Optional
from .mod import IntrospectiveModule, ModuleControlsType


class WarehouseMeta(type):
    """Metaclass for auto-registering Warehouse subclasses."""

    def __new__(cls, name, bases, attrs, **_):
        new_class = super().__new__(cls, name, bases, attrs)

        # Auto-register controller subclasses
        if (name != 'ModuleWarehouse' and
            issubclass(new_class, ModuleWarehouse) and
                hasattr(new_class, 'warehouse_type')):

            ModuleWarehouseFactory._warehouses[new_class.warehouse_type] = new_class

        return new_class


class ModuleWarehouse(metaclass=WarehouseMeta):
    """Class used to manage a collection of IntrospectiveModules.

    Can filter types, catalog numbers, etc.
    """

    warehouse_type: str = 'GenericWarehouse'

    @property
    def known_modules(self) -> List[IntrospectiveModule]:
        """List of known IntrospectiveModules in this warehouse."""
        raise NotImplementedError("Subclasses must implement this method")

    def get_modules_by_type(
        self,
        module_type: ModuleControlsType
    ) -> List[IntrospectiveModule]:
        """Get modules of a specific type from the warehouse.

        Args:
            module_type (ModuleControlsType): The type of module to filter by.

        Returns:
            List[IntrospectiveModule]: List of modules matching the specified type.
        """
        return [
            m for m in self.known_modules if isinstance(m, module_type)
        ]


class ModuleWarehouseFactory:
    """Factory for creating ModuleWarehouse instances."""

    _warehouses: dict[str, ModuleWarehouse] = {}

    @staticmethod
    def create_warehouse(warehouse_type: str) -> Optional[ModuleWarehouse]:
        """Create a ModuleWarehouse instance based on the warehouse type.

        Args:
            warehouse_type (str): The type of warehouse to create.

        Returns:
            Optional[ModuleWarehouse]: An instance of the requested warehouse type, or None if not found.
        """
        return ModuleWarehouseFactory._warehouses.get(warehouse_type, None)

    def get_all_warehouses() -> dict[str, ModuleWarehouse]:
        """Get all registered warehouses.

        Returns:
            dict: A copy of the dictionary of all registered warehouses.
        """
        return ModuleWarehouseFactory._warehouses.copy()

    @staticmethod
    def filter_modules_by_controls_type(
        modules: List[IntrospectiveModule],
        controls_type: ModuleControlsType
    ) -> List[IntrospectiveModule]:
        """Filter a list of IntrospectiveModules by their controls type.

        Args:
            modules (List[IntrospectiveModule]): The list of modules to filter.
            controls_type (ModuleControlsType): The controls type to filter by.

        Returns:
            List[IntrospectiveModule]: A list of modules matching the specified controls type.
        """
        return [
            m for m in modules if isinstance(m, controls_type)
        ]

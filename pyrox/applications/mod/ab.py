"""Allen Bradley specific PLC Modules.
"""
from __future__ import annotations
from pyrox.models.plc import IntrospectiveModule, ModuleWarehouse, ModuleControlsType


class AB_1732Es(IntrospectiveModule):
    """Allen Bradley 1732ES Safety Block Module.
    """
    @property
    def catalog_number(self) -> str:
        """The catalog number of the G115 drive module."""
        return '1732ES-IB'

    @property
    def controls_type(self) -> ModuleControlsType:
        """The controls type of the module."""
        return ModuleControlsType.SAFETY_BLOCK


class AB_1734IB8S(IntrospectiveModule):
    """Allen Bradley 1734-IB8S Module.

    This module represents an Allen Bradley 1734-IB8S input module.
    It is used to control and monitor the input operations in a PLC system.
    """
    @property
    def catalog_number(self) -> str:
        """The catalog number of the 1734-IB8S module."""
        return '1734-IB8S'

    @property
    def controls_type(self) -> ModuleControlsType:
        """The controls type of the module."""
        return ModuleControlsType.SAFETY_BLOCK


class AB_1791ES(IntrospectiveModule):
    """Allen Bradley 1791ES Safety Block Module.
    """
    @property
    def catalog_number(self) -> str:
        """The catalog number of the G115 drive module."""
        return '1791ES-IB'

    @property
    def controls_type(self) -> ModuleControlsType:
        """The controls type of the module."""
        return ModuleControlsType.SAFETY_BLOCK


class AllenBradleyWarehouse(ModuleWarehouse):
    """Warehouse for Allen Bradley specific modules."""

    warehouse_type: str = 'AllenBradleyWarehouse'

    @property
    def known_modules(self) -> list[IntrospectiveModule]:
        return [
            m for m in IntrospectiveModule.get_known_modules() if
            m.catalog_number.startswith('1732')
            or m.catalog_number.startswith('1734')
        ]

"""Red Lion specific PLC Modules.
"""
from __future__ import annotations
from pyrox.models.abc.factory import FactoryTypeMeta
from pyrox.models.plc import (
    IntrospectiveModule,
    ModuleControlsType,
    ModuleWarehouse
)


class RedLionModuleFactory(ModuleWarehouse):
    """Factory for creating Red Lion module instances."""


class RedLionModule(
        IntrospectiveModule,
        metaclass=FactoryTypeMeta['RedLionModule', RedLionModuleFactory]
):
    """Red Lion Module ABC.
    """
    supports_registering = False

    def __init_subclass__(cls, **kwargs):
        cls.supports_registering = True
        return super().__init_subclass__(**kwargs)

    @property
    def catalog_number(self) -> str:
        """The catalog number of the G115 drive module."""
        return 'ETHERNET-MODULE'

    @property
    def config_cxn_point(self) -> str:
        """The config connection point of the module."""
        return ''

    @classmethod
    def get_factory(cls):
        return RedLionModuleFactory


class NTron16PortSwitch(RedLionModule):
    @property
    def config_cxn_point(self) -> str:
        """The config connection point of the module."""
        return '103'

    @property
    def config_size(self) -> str:
        """The config connection size of the module."""
        return '0'

    @property
    def controls_type(self) -> ModuleControlsType:
        """The controls type of the module."""
        return ModuleControlsType.ETHERNET_SWITCH

    @property
    def input_cxn_point(self) -> str:
        """The input connection point of the module."""
        return '105'

    @property
    def input_size(self) -> str:
        """The input size of the module."""
        return '16'

    @property
    def output_cxn_point(self) -> str:
        """The output connection point of the module."""
        return '104'

    @property
    def output_size(self) -> str:
        """The output size of the module."""
        return '4'

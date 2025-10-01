"""Turck specific PLC Modules.
"""
from __future__ import annotations
from pyrox.models.abc.factory import FactoryTypeMeta
from pyrox.models.plc import (
    IntrospectiveModule,
    ModuleControlsType,
    ModuleWarehouse
)


class TurckModuleFactory(ModuleWarehouse):
    """Factory for creating Turck module instances."""


class TurckModule(
        IntrospectiveModule,
        metaclass=FactoryTypeMeta['TurckModule', TurckModuleFactory]
):
    """Turck Module ABC.
    """
    supports_registering = False  # Turck modules do not support registering directly

    def __init_subclass__(cls, **kwargs):
        cls.supports_registering = True  # Subclasses can support registering
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
        return TurckModuleFactory

    def get_standard_input_tag_name(self):
        return f'zz_Demo3D_{self.module.name}'


class TurckTBENG16ConfigBlock(TurckModule):
    @property
    def config_size(self) -> str:
        """The config connection size of the module."""
        return '0'

    @property
    def controls_type(self) -> ModuleControlsType:
        """The controls type of the module."""
        return ModuleControlsType.CONFIG_BLOCK

    @property
    def input_cxn_point(self) -> str:
        """The input connection point of the module."""
        return '103'

    @property
    def input_size(self) -> str:
        """The input size of the module."""
        return '10'

    @property
    def output_cxn_point(self) -> str:
        """The output connection point of the module."""
        return '104'

    @property
    def output_size(self) -> str:
        """The output size of the module."""
        return '4'


class TurckTBENG8In8OutBlock(TurckModule):
    @property
    def config_size(self) -> str:
        """The config connection size of the module."""
        return '16'

    @property
    def controls_type(self) -> ModuleControlsType:
        """The controls type of the module."""
        return ModuleControlsType.INPUT_OUTPUT_BLOCK

    @property
    def input_cxn_point(self) -> str:
        """The input connection point of the module."""
        return '103'

    @property
    def input_size(self) -> str:
        """The input size of the module."""
        return '8'

    @property
    def output_cxn_point(self) -> str:
        """The output connection point of the module."""
        return '104'

    @property
    def output_size(self) -> str:
        """The output size of the module."""
        return '4'


class TurckTBENL16InBlock(TurckModule):
    @property
    def config_size(self) -> str:
        """The config connection size of the module."""
        return '16'

    @property
    def controls_type(self) -> ModuleControlsType:
        """The controls type of the module."""
        return ModuleControlsType.INPUT_BLOCK

    @property
    def input_cxn_point(self) -> str:
        """The input connection point of the module."""
        return '103'

    @property
    def input_size(self) -> str:
        """The input size of the module."""
        return '8'

    @property
    def output_cxn_point(self) -> str:
        """The output connection point of the module."""
        return '104'

    @property
    def output_size(self) -> str:
        """The output size of the module."""
        return '2'

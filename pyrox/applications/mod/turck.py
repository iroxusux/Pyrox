"""Turck specific PLC Modules.
"""
from __future__ import annotations
from pyrox.models.plc import TurckModule, ModuleControlsType


class TurckTBENG16ConfigBlock(TurckModule):
    @property
    def catalog_number(self) -> str:
        """The catalog number of the G115 drive module."""
        return 'ETHERNET-MODULE'

    @property
    def controls_type(self) -> ModuleControlsType:
        """The controls type of the module."""
        return ModuleControlsType.BLOCK

    @property
    def input_cxn_point(self) -> str:
        """The input connection point of the module."""
        return '103'

    @property
    def input_size(self) -> str:
        """The input size of the module."""
        return '5'

    @property
    def output_cxn_point(self) -> str:
        """The output connection point of the module."""
        return '104'

    @property
    def output_size(self) -> str:
        """The output size of the module."""
        return '2'

    @classmethod
    def get_required_imports(cls) -> list[tuple[str, list[str]]]:
        """Get the required datatype imports for the module.

        Returns:
            list[tuple[str, str]]: List of tuples containing the module and class name to import.
        """
        return [
        ]

    def get_required_standard_rungs(self):
        rungs = []

        return rungs

    def get_required_tags(self) -> list[dict]:
        tags = []

        return tags

    def get_standard_input_tag_name(self):
        return f'zz_Demo3D_{self.module.name}'


class TurckTBENG8In8OutBlock(TurckModule):
    @property
    def catalog_number(self) -> str:
        """The catalog number of the G115 drive module."""
        return 'ETHERNET-MODULE'

    @property
    def config_cxn_point(self) -> str:
        """The config connection point of the module."""
        return ''

    @property
    def config_size(self) -> str:
        """The config connection size of the module."""
        return '16'

    @property
    def controls_type(self) -> ModuleControlsType:
        """The controls type of the module."""
        return ModuleControlsType.BLOCK

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

    @classmethod
    def get_required_imports(cls) -> list[tuple[str, list[str]]]:
        """Get the required datatype imports for the module.

        Returns:
            list[tuple[str, str]]: List of tuples containing the module and class name to import.
        """
        return []

    def get_required_standard_rungs(self):
        rungs = []

        return rungs

    def get_required_tags(self) -> list[dict]:
        tags = []

        return tags

    def get_standard_input_tag_name(self):
        return f'zz_Demo3D_{self.module.name}'


class TurckTBENL16InBlock(TurckModule):
    @property
    def catalog_number(self) -> str:
        """The catalog number of the G115 drive module."""
        return 'ETHERNET-MODULE'

    @property
    def config_cxn_point(self) -> str:
        """The config connection point of the module."""
        return ''

    @property
    def config_size(self) -> str:
        """The config connection size of the module."""
        return '16'

    @property
    def controls_type(self) -> ModuleControlsType:
        """The controls type of the module."""
        return ModuleControlsType.BLOCK

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

    @classmethod
    def get_required_imports(cls) -> list[tuple[str, list[str]]]:
        """Get the required datatype imports for the module.

        Returns:
            list[tuple[str, str]]: List of tuples containing the module and class name to import.
        """
        return []

    def get_required_standard_rungs(self):
        rungs = []

        return rungs

    def get_required_tags(self) -> list[dict]:
        tags = []

        return tags

    def get_standard_input_tag_name(self):
        return f'zz_Demo3D_{self.module.name}'

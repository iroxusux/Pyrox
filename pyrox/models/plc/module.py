"""Module model for pyrox Controller applications
"""
from enum import Enum
from typing import Optional, TYPE_CHECKING, Union
from pyrox.models.plc import meta as plc_meta

if TYPE_CHECKING:
    from pyrox.models.plc.controller import Controller
    from pyrox.models.plc.imodule import IntrospectiveModule


class ModuleControlsType(Enum):
    """Module controls type enumeration
    """
    UNKOWN = 'Unknown'
    PLC = 'PLC'
    RACK_COMM_CARD = 'RackCommCard'
    ETHERNET = 'Ethernet'
    ETHERNET_SWITCH = 'EthernetSwitch'
    SERIAL = 'Serial'
    BLOCK = 'Block'
    INPUT_BLOCK = 'InputBlock'
    OUTPUT_BLOCK = 'OutputBlock'
    INPUT_OUTPUT_BLOCK = 'InputOutputBlock'
    CONFIG_BLOCK = 'ConfigBlock'
    SAFETY_BLOCK = 'SafetyBlock'
    SAFETY_INPUT_BLOCK = 'SafetyInputBlock'
    SAFETY_OUTPUT_BLOCK = 'SafetyOutputBlock'
    SAFETY_INPUT_OUTPUT_BLOCK = 'SafetyInputOutputBlock'
    SAFETY_CONFIG_BLOCK = 'SafetyConfigBlock'
    DRIVE = 'Drive'
    POINT_IO = 'PointIO'

    @staticmethod
    def all_block_types() -> list['ModuleControlsType']:
        """Get all block types

        Returns:
            :class:`list[ModuleControlsType]`: list of all block types
        """
        return [
            ModuleControlsType.BLOCK,
            ModuleControlsType.INPUT_BLOCK,
            ModuleControlsType.OUTPUT_BLOCK,
            ModuleControlsType.INPUT_OUTPUT_BLOCK,
            ModuleControlsType.CONFIG_BLOCK,
            ModuleControlsType.SAFETY_BLOCK,
            ModuleControlsType.SAFETY_INPUT_BLOCK,
            ModuleControlsType.SAFETY_OUTPUT_BLOCK,
            ModuleControlsType.SAFETY_INPUT_OUTPUT_BLOCK,
            ModuleControlsType.SAFETY_CONFIG_BLOCK,
        ]


class ModuleConnectionTag(plc_meta.PlcObject):

    @property
    def config_size(self) -> str:
        return self['@ConfigSize']

    @property
    def data(self) -> list[dict]:
        if not self['Data']:
            return [{}]
        return self['Data']

    @property
    def data_decorated(self) -> dict:
        if not isinstance(self.data, list):
            datas = [self.data]
        else:
            datas = self.data
        return next((x for x in datas if x.get('@Format', '') == 'Decorated'), {})

    @property
    def data_decorated_structure(self) -> dict:
        return self.data_decorated.get('Structure', {})

    @property
    def data_decorated_structure_array_member(self) -> dict:
        return self.data_decorated_structure.get('ArrayMember', {})

    @property
    def data_decorated_stucture_datatype(self) -> str:
        return self.data_decorated_structure.get('@DataType', '')

    @property
    def data_decorated_stucture_size(self) -> str:
        return self.data_decorated_structure_array_member.get('@Dimensions', '')

    @property
    def data_l5x(self) -> dict:
        return next((x for x in self.data if x.get('@Format', '') == 'L5X'), {})

    def get_data_multiplier(self) -> int:
        """get the data multiplier for this tag

        Returns:
            :class:`int`: data multiplier
        """
        if not self.data_decorated_stucture_datatype:
            return 0

        match self.data_decorated_stucture_datatype:
            case 'SINT':
                return 1
            case 'INT':
                return 2
            case 'DINT' | 'REAL' | 'DWORD':
                return 4
            case 'LINT' | 'LREAL' | 'LWORD':
                return 8
            case _:
                raise ValueError(f"Unsupported datatype: {self.data_decorated_stucture_datatype}")

    def get_resolved_size(self) -> int:
        """get the resolved size for this tag

        Returns:
            :class:`int`: resolved size
        """
        if not self.data_decorated_stucture_size:
            return 0

        native_size = int(self.data_decorated_stucture_size)
        return native_size * self.get_data_multiplier()


class Module(plc_meta.NamedPlcObject):

    default_l5x_file_path = plc_meta.PLC_MOD_FILE
    default_l5x_asset_key = 'Module'

    def __init__(
        self,
        meta_data: Optional[dict] = None,
        controller: Optional['Controller'] = None
    ) -> None:

        super().__init__(meta_data=meta_data, controller=controller)
        self._introspective_module: 'IntrospectiveModule' = None
        self._config_tag: ModuleConnectionTag = None
        self._input_tag: ModuleConnectionTag = None
        self._output_tag: ModuleConnectionTag = None
        self._compile_from_meta_data()

    @property
    def address(self) -> str:
        return self.ports[0]['@Address'] if self.ports and len(self.ports) > 0 else ''

    @property
    def dict_key_order(self) -> list[str]:
        return [
            '@Name',
            '@CatalogNumber',
            '@Vendor',
            '@ProductType',
            '@ProductCode',
            '@Major',
            '@Minor',
            '@ParentModule',
            '@ParentModPortId',
            '@Inhibited',
            '@MajorFault',
            'Description',
            'EKey',
            'Ports',
            'Communications',
        ]

    @property
    def catalog_number(self) -> str:
        return self['@CatalogNumber']

    @catalog_number.setter
    def catalog_number(self, value: str):
        if not self.is_valid_module_string(value):
            raise self.InvalidNamingException

        self['@CatalogNumber'] = value

    @property
    def communications(self) -> dict:
        return self['Communications']

    @communications.setter
    def communications(self, value: dict):
        if not isinstance(value, dict):
            raise ValueError("Communications must be a dictionary!")

        self['Communications'] = value

    @property
    def connection(self) -> dict:
        return self.connections[0] if self.connections and len(self.connections) > 0 else {}

    @property
    def connections(self) -> list[dict]:
        """get the connections for this module

        Returns:
            :class:`dict`: connections for this module
        """
        if not self.communications:
            return {}
        if not self.communications.get('Connections', None):
            return {}

        if not isinstance(self.communications['Connections'], dict):
            self.communications['Connections'] = {'Connection': []}
        if not isinstance(self.communications['Connections'].get('Connection', []), list):
            self.communications['Connections']['Connection'] = [self.communications['Connections']['Connection']]
        return self.communications['Connections'].get('Connection', [])

    @property
    def config_connection_point(self) -> str:
        """get the config connection point for this module

        Returns:
            :class:`str`: config connection point
        """
        if not self.connections or len(self.connections) < 1:
            return ''
        return self.connections[0].get('@ConfigCxnPoint', '')

    @property
    def config_tag(self) -> ModuleConnectionTag:
        """get the config tag for this module

        Returns:
            :class:`str`: config tag
        """
        return self._config_tag

    @property
    def input_connection_point(self) -> str:
        """get the input connection point for this module

        Returns:
            :class:`str`: input connection point
        """
        if not self.connections or len(self.connections) < 1:
            return ''
        return self.connections[0].get('@InputCxnPoint', '')

    @property
    def input_tag(self) -> ModuleConnectionTag:
        """get the input tag for this module

        Returns:
            :class:`str`: input tag
        """
        return self._input_tag

    @property
    def output_connection_point(self) -> str:
        """get the output connection point for this module

        Returns:
            :class:`str`: output connection point
        """
        if not self.connections or len(self.connections) < 1:
            return ''
        return self.connections[0].get('@OutputCxnPoint', '')

    @property
    def output_tag(self) -> ModuleConnectionTag:
        """get the output tag for this module

        Returns:
            :class:`str`: output tag
        """
        return self._output_tag

    @property
    def config_connection_size(self) -> str:
        """get the config connection size for this module

        Returns:
            :class:`str`: config connection size
        """
        if not self.config_tag:
            return ''
        return self.config_tag.config_size

    @property
    def input_connection_size(self) -> str:
        """get the input connection size for this module

        Returns:
            :class:`str`: input connection size
        """
        if not self.connection:
            return ''
        return self.connection.get('@InputSize', '')

    @property
    def output_connection_size(self) -> str:
        """get the output connection size for this module

        Returns:
            :class:`str`: output connection size
        """
        if not self.connection:
            return ''
        return self.connection.get('@OutputSize', '')

    @property
    def vendor(self) -> str:
        return self['@Vendor']

    @vendor.setter
    def vendor(self, value: str):
        self._safe_set_integer_property('@Vendor', value)

    @property
    def product_type(self) -> str:
        return self['@ProductType']

    @product_type.setter
    def product_type(self, value: str):
        self._safe_set_integer_property('@ProductType', value)

    @property
    def product_code(self) -> str:
        return self['@ProductCode']

    @product_code.setter
    def product_code(self, value: str):
        self._safe_set_integer_property('@ProductCode', value)

    @property
    def major(self) -> str:
        return self['@Major']

    @major.setter
    def major(self, value: str):
        self._safe_set_integer_property('@Major', value)

    @property
    def minor(self) -> str:
        return self['@Minor']

    @minor.setter
    def minor(self, value: str):
        self._safe_set_integer_property('@Minor', value)

    @property
    def parent_module(self) -> str:
        return self['@ParentModule']

    @property
    def parent_mod_port_id(self) -> str:
        return self['@ParentModPortId']

    @property
    def inhibited(self) -> str:
        return self['@Inhibited']

    @inhibited.setter
    def inhibited(self, value: Union[str, bool]):
        if isinstance(value, bool):
            value = 'true' if value else 'false'

        if not self.is_valid_rockwell_bool(value):
            raise self.InvalidNamingException

        self['@Inhibited'] = value

    @property
    def introspective_module(self) -> 'IntrospectiveModule':
        """get the introspective module for this module

        Returns:
            :class:`IntrospectiveModule`: introspective module
        """
        return self._introspective_module

    @introspective_module.setter
    def introspective_module(self, value: 'IntrospectiveModule'):
        from pyrox.models.plc.imodule import IntrospectiveModule
        if not isinstance(value, IntrospectiveModule):
            raise ValueError("IntrospectiveModule must be an instance of IntrospectiveModule!")
        self._introspective_module = value

    @property
    def major_fault(self) -> str:
        return self['@MajorFault']

    @major_fault.setter
    def major_fault(self, value: Union[str, bool]):
        if isinstance(value, bool):
            value = 'true' if value else 'false'

        if not self.is_valid_rockwell_bool(value):
            raise self.InvalidNamingException

        self['@MajorFault'] = value

    @property
    def ekey(self) -> dict:
        return self['EKey']

    @property
    def ports(self) -> list[dict]:
        if not self['Ports']:
            return []

        if not isinstance(self['Ports']['Port'], list):
            return [self['Ports']['Port']]

        return self['Ports']['Port']

    @property
    def rpi(self) -> str:
        return self.connection.get('@RPI', '')

    @property
    def type_(self) -> str:
        """get the type of this module

        Returns:
            :class:`str`: type of this module
        """
        return self.introspective_module.type_ if self.introspective_module else 'Unknown'

    def _compile_from_meta_data(self):

        self._compile_tag_meta_data()
        from pyrox.models.plc.imodule import IntrospectiveModule
        self._introspective_module = IntrospectiveModule.from_meta_data(self, lazy_match_catalog=True)

    def _compile_tag_meta_data(self):
        if not self.communications:
            return

        config_tag_data = self.communications.get('ConfigTag', None)
        if config_tag_data:
            self._config_tag = ModuleConnectionTag(meta_data=config_tag_data, controller=self.controller)

        if not self.connections:
            return

        input_tag_data = self.connection.get('InputTag', None)
        output_tag_data = self.connection.get('OutputTag', None)

        if input_tag_data:
            self._input_tag = ModuleConnectionTag(meta_data=input_tag_data, controller=self.controller)
        if output_tag_data:
            self._output_tag = ModuleConnectionTag(meta_data=output_tag_data, controller=self.controller)

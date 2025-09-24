"""Tag module for plc Tag type
"""
from typing import Optional, Union, TYPE_CHECKING, Self
from pyrox.models.plc import meta as plc_meta
from pyrox.services.plc import l5x_dict_from_file
if TYPE_CHECKING:
    from .controller import Controller, Program, AddOnInstruction


class DataValueMember(plc_meta.NamedPlcObject):
    """type class for plc Tag DataValueMember

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """

    def __init__(self,
                 name: str = None,
                 l5x_meta_data: dict = None,
                 controller: 'Controller' = None,
                 parent: Union['Tag', Self] = None):

        if not l5x_meta_data:
            raise ValueError('Cannot have an empty DataValueMember!')

        if not parent:
            raise ValueError('Cannot have a datavalue member without a parent!')

        super().__init__(meta_data=l5x_meta_data,
                         controller=controller)

        self._parent = parent

        if name:
            self.name = name

    @property
    def parent(self) -> Union['Tag', Self]:
        return self._parent


class TagEndpoint(plc_meta.PlcObject):
    def __init__(self,
                 meta_data: str,
                 controller: 'Controller',
                 parent_tag: 'Tag'):
        super().__init__(meta_data=meta_data,
                         controller=controller)
        self._parent_tag: 'Tag' = parent_tag

    @property
    def name(self) -> str:
        """get the name of this tag endpoint

        Returns:
            :class:`str`: name of this tag endpoint
        """
        return self._meta_data


class Tag(plc_meta.NamedPlcObject):
    def __init__(self,
                 meta_data: Optional[dict] = None,
                 controller: Optional['Controller'] = None,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 class_: Optional[str] = None,
                 tag_type: Optional[str] = None,
                 datatype: Optional[str] = None,
                 dimensions: Optional[str] = None,
                 constant: Optional[bool] = None,
                 external_access: Optional[str] = None,
                 container: Union['Program', 'AddOnInstruction', 'Controller'] = None):
        """type class for plc Tag

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """
        if controller is None and container is not None:
            from pyrox.models.plc import Program, AddOnInstruction
            controller = container.controller if isinstance(container, (Program, AddOnInstruction)) else None

        container = container or controller
        super().__init__(
            controller=controller,
            meta_data=meta_data or l5x_dict_from_file(plc_meta.PLC_TAG_FILE)['Tag'],
            name=name,
            description=description
        )
        self._container = container
        if class_:
            self.class_ = class_
        if tag_type:
            self.tag_type = tag_type
        if datatype:
            self.datatype = datatype
        if dimensions:
            self.dimensions = dimensions
        if constant is not None:
            self.constant = constant
        if external_access:
            self.external_access = external_access

    @property
    def dict_key_order(self) -> list[str]:
        return [
            '@Name',
            '@Class',
            '@TagType',
            '@DataType',
            '@Dimensions',
            '@Radix',
            '@AliasFor',
            '@Constant',
            '@ExternalAccess',
            'ConsumeInfo',
            'ProduceInfo',
            'Description',
            'Data',
        ]

    @property
    def alias_for(self) -> str:
        return self._meta_data.get('@AliasFor', None)

    @property
    def alias_for_base_name(self) -> str:
        """get the base name of the aliased tag

        Returns:
            :class:`str`
        """
        if not self.alias_for:
            return None

        return self.alias_for.split('.')[0].split(':')[0]

    @property
    def class_(self) -> str:
        return self['@Class']

    @class_.setter
    def class_(self, value: str):
        if not isinstance(value, str):
            raise ValueError("Class must be a string!")

        if value not in ['Standard', 'Safety']:
            raise ValueError("Class must be one of: Standard, Safety!")

        self['@Class'] = value

    @property
    def constant(self) -> str:
        return self['@Constant']

    @constant.setter
    def constant(self, value: Union[str, bool]):
        if isinstance(value, bool):
            value = 'true' if value else 'false'

        if not self.is_valid_rockwell_bool(value):
            raise self.InvalidNamingException

        self['@Constant'] = value

    @property
    def container(self) -> Optional[Union['Program', 'AddOnInstruction', 'Controller']]:
        return self._container

    @property
    def data(self) -> list[dict]:
        if not isinstance(self['Data'], list):
            return [self['Data']]

        return self['Data']

    @property
    def datatype(self) -> str:
        return self['@DataType']

    @datatype.setter
    def datatype(self, value: str):
        if not self.is_valid_string(value) or not value:
            raise ValueError("Data type must be a valid string!")

        self['@DataType'] = value
        self['Data'] = []

    @property
    def datavalue_members(self) -> list[DataValueMember]:
        if not self.decorated_data:
            return []

        if not self.decorated_data.get('Structure', None):
            return []

        if not self.decorated_data['Structure'].get('DataValueMember', None):
            return []

        return [DataValueMember(l5x_meta_data=x,
                                controller=self.controller,
                                parent=self)
                for x in self.decorated_data['Structure']['DataValueMember']]

    @property
    def decorated_data(self) -> dict:
        return next((x for x in self.data if x and x['@Format'] == 'Decorated'), None)

    @property
    def dimensions(self) -> str:
        """get the dimensions of this tag

        Returns:
            :class:`str`: dimensions of this datatype
        """
        return self['@Dimensions']

    @dimensions.setter
    def dimensions(self, value: Union[str, int]):
        if isinstance(value, int):
            if value < 0:
                raise ValueError("Dimensions must be a positive integer!")
            value = str(value)

        if not isinstance(value, str):
            raise ValueError("Dimensions must be a string or an integer!")

        self['@Dimensions'] = value

    @property
    def endpoint_operands(self) -> list[str]:
        """get the endpoint operands for this tag

        Returns:
            :class:`list[str]`: list of endpoint operands
        """
        if not self.datatype:
            return []

        datatype = self.controller.datatypes.get(self.datatype, None)
        if not datatype:
            return []

        endpoints = datatype.endpoint_operands
        if not endpoints:
            return []

        return [TagEndpoint(meta_data=f'{self.name}{x}',
                            controller=self.controller,
                            parent_tag=self) for x in endpoints]

    @property
    def external_access(self) -> str:
        return self['@ExternalAccess']

    @external_access.setter
    def external_access(self, value: str):
        if not isinstance(value, str):
            raise ValueError("External access must be a string!")

        if value not in ['None', 'ReadOnly', 'Read/Write']:
            raise ValueError("External access must be one of: None, ReadOnly, Read/Write!")

        self['@ExternalAccess'] = value

    @property
    def l5k_data(self) -> dict:
        return next((x for x in self.data if x and x['@Format'] == 'L5K'), None)

    @property
    def opc_ua_access(self) -> str:
        return self['@OpcUaAccess']

    @property
    def scope(self) -> plc_meta.LogixTagScope:
        from pyrox.models.plc import Controller, Program, AddOnInstruction
        if isinstance(self.container, Controller):
            return plc_meta.LogixTagScope.CONTROLLER
        elif isinstance(self.container, Program) or isinstance(self.container, AddOnInstruction):
            return plc_meta.LogixTagScope.PROGRAM
        else:
            raise ValueError('Unknown tag scope!')

    @property
    def tag_type(self) -> str:
        return self['@TagType']

    @tag_type.setter
    def tag_type(self, value: str):
        if not isinstance(value, str):
            raise ValueError("Tag type must be a string!")

        if value not in ['Base', 'Structure', 'Array']:
            raise ValueError("Tag type must be one of: Atomic, Structure, Array!")

        self['@TagType'] = value

    def get_alias_string(self,
                         additional_elements: str = None) -> str:
        """get the alias string for this tag

        Returns:
            :class:`str`: alias string of this tag
        """
        if not additional_elements:
            additional_elements = ''

        if not self.alias_for:
            return f'{self.name}{additional_elements}'

        parent_tag = self.get_parent_tag(self)
        if not parent_tag:
            return f'{self.alias_for}{additional_elements}'

        alias_element_pointer = self.alias_for.find('.')
        if alias_element_pointer != -1:
            additional_elements = f'{self.alias_for[alias_element_pointer:]}{additional_elements}'

        return parent_tag.get_alias_string(additional_elements=additional_elements)

    def get_base_tag(self,
                     tracked_tag: Self = None):
        tag = self if not tracked_tag else tracked_tag

        if not tag.alias_for:
            return tag

        alias = tag.get_parent_tag(tag)

        if not alias:
            return tag

        if alias.alias_for:
            return self.get_base_tag(tracked_tag=alias)
        else:
            return alias

    @staticmethod
    def get_parent_tag(tag: Self):
        if not tag.alias_for:
            return None

        alias = None

        if tag.container:
            alias: Self = tag.container.tags.get(tag.alias_for_base_name, None)

        if not alias:
            alias: Self = tag.controller.tags.get(tag.alias_for_base_name, None)

        return alias

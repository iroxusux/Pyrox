"""Datatype for a rockwell plc
"""
from typing import TYPE_CHECKING
from pyrox.models.plc import meta as plc_meta
if TYPE_CHECKING:
    from pyrox.models.plc import Controller


class DatatypeMember(plc_meta.NamedPlcObject):
    def __init__(self,
                 l5x_meta_data: dict,
                 parent_datatype: 'Datatype',
                 controller: 'Controller'):
        """type class for plc Datatype Member

        Args:
            l5x_meta_data (str): meta data
            datatype (Datatype): parent datatype
            controller (Self): controller dictionary
        """
        super().__init__(
            meta_data=l5x_meta_data,
            controller=controller
        )
        self._parent_datatype = parent_datatype

    @property
    def datatype(self) -> str:
        """get the datatype of this member

        Returns:
            :class:`str`: datatype of this member
        """
        return self['@DataType']

    @property
    def dimension(self) -> str:
        return self['@Dimension']

    @property
    def hidden(self) -> str:
        return self['@Hidden']

    @property
    def is_atomic(self) -> bool:
        """check if this member is atomic

        Returns:
            :class:`bool`: True if atomic, False otherwise
        """
        return self.datatype in plc_meta.ATOMIC_DATATYPES

    @property
    def parent_datatype(self) -> 'Datatype':
        return self._parent_datatype


class Datatype(plc_meta.NamedPlcObject):
    """.. description::
        Datatype for a rockwell plc
        .. --------------------------------
        .. package::
        models.plc.plc
        .. --------------------------------
        .. attributes::
        :class:`list[str]` endpoint_operands:
            list of endpoint operands for this datatype
        """

    def __init__(
        self,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self._endpoint_operands: list[str] = []
        self._members: list[DatatypeMember] = []
        [self._members.append(DatatypeMember(l5x_meta_data=x, controller=self.controller, parent_datatype=self))
         for x in self.raw_members]

    @property
    def endpoint_operands(self) -> list[str]:
        """get the endpoint operands for this datatype
        for example, for a datatype with members like::
        .. code-block:: xml
        <Datatype Name="MyDatatype" ...>
            <Member Name="MyAtomicMember" @Datatype="BOOL" ... />
            <Member Name="MyMember" @Datatype="SomeOtherDatatype" ...>
                <Member Name"MyChildMember" @Datatype="BOOL" ... />
            </Member>
        </Datatype>

        the endpoint operands would be:
            ['.MyAtomicMember', '.MyMember.MyChildMember']

        Returns:
            list[str]: List of endpoint operands.
        """
        if self.is_atomic:
            return ['']
        if self._endpoint_operands:
            return self._endpoint_operands
        self._endpoint_operands = []
        for member in self.members:
            if member.hidden == 'true':
                continue
            if member.is_atomic:
                self._endpoint_operands.append(f'.{member.name}')
            else:
                datatype = self.controller.datatypes.get(member['@DataType'], None)
                if not datatype:
                    continue
                self._endpoint_operands.extend([f'.{member.name}{x}' for x in datatype.endpoint_operands])
        return self._endpoint_operands

    @property
    def dict_key_order(self) -> list[str]:
        return [
            '@Name',
            '@Family',
            '@Class',
            'Description',
            'Members',
        ]

    @property
    def family(self) -> str:
        return self['@Family']

    @property
    def is_atomic(self) -> bool:
        """check if this member is atomic

        Returns:
            :class:`bool`: True if atomic, False otherwise
        """
        return self.name in plc_meta.ATOMIC_DATATYPES

    @property
    def members(self) -> list[DatatypeMember]:
        return self._members

    @property
    def raw_members(self) -> list[dict]:
        return self._raw_list_asset('Members', 'Member')

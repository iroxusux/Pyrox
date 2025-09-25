"""Datatype for a rockwell plc
"""
from typing import Optional, TYPE_CHECKING
from pyrox.models.plc import meta as plc_meta
if TYPE_CHECKING:
    from pyrox.models.plc import Controller


class DataTypeMeta(plc_meta.NamedPlcObject):
    @property
    def is_atomic(self) -> bool:
        """check if this member is atomic

        Returns:
            :class:`bool`: True if atomic, False otherwise
        """
        if hasattr(self, 'datatype'):  # Datatype uses this member
            return self.datatype in plc_meta.ATOMIC_DATATYPES  # type: ignore
        elif hasattr(self, 'name'):
            return self.name in plc_meta.ATOMIC_DATATYPES
        return False


class DatatypeMember(DataTypeMeta):
    def __init__(
        self,
        meta_data: Optional[dict],
        controller: Optional['Controller'],
        parent_datatype: Optional['Datatype'],
    ) -> None:
        """type class for plc Datatype Member

        Args:
            meta_data (dict): meta data
            controller (Controller): controller
            parent_datatype (Datatype): parent datatype
        """
        super().__init__(
            meta_data=meta_data,
            controller=controller
        )
        self.parent_datatype = parent_datatype

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
    def parent_datatype(self) -> Optional['Datatype']:
        return self._parent_datatype

    @parent_datatype.setter
    def parent_datatype(self, value: Optional['Datatype']) -> None:
        if not isinstance(value, Datatype) and value is not None:
            raise TypeError('parent_datatype must be a Datatype or None')
        self._parent_datatype = value


class Datatype(DataTypeMeta):
    """Datatype Definition for a rockwell plc
    """

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
                if not self.controller:
                    continue
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
    def members(self) -> list[DatatypeMember]:
        return self._members

    @property
    def raw_members(self) -> list[dict]:
        return self._raw_list_asset('Members', 'Member')

    def _post_init(
        self,
        **_
    ) -> None:
        """Post initialization hook.
        This method is called after the object has been initialized.
        """
        self._members: list[DatatypeMember] = []
        self._endpoint_operands: list[str] = []
        for member in self.raw_members:
            self._members.append(DatatypeMember(
                meta_data=member,
                controller=self.controller,
                parent_datatype=self,
            ))

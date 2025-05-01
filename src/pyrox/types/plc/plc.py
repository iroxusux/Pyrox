"""plc type module
    """
from __future__ import annotations


from dataclasses import dataclass
from enum import Enum
import os
import re
from typing import Generic, get_args, Optional, Self, TypeVar, Tuple
import xml.etree.ElementTree as ET


import lxml.etree
import xmltodict


from ..abc.meta import EnforcesNaming, Loggable, SnowFlake


from ...utils import replace_strings_in_dict


__all__ = (
    'PlcObject',
    'AddOnInstruction',
    'ConnectionParameters',
    'Controller',
    'Datatype',
    'Module',
    'Program',
    'ProgramTag',
    'Routine',
    'Rung',
    'Tag',
)


T = TypeVar('T')

INST_RE_PATTERN: str = r'([A-Z]{3,4}\(\S+?\))'


def controller_dict_from_file(file_location: str) -> Optional[dict]:
    """get a controller dictionary from a provided .l5x file location

    Args:
        file_location (str): file location (must end in .l5x)

    Raises:
        ValueError: if provided file location is not .L5X

    Returns:
        dict: controller
    """
    if not file_location.endswith('.L5X'):
        raise ValueError('can only parse .L5X files!')

    if not os.path.exists(file_location):
        raise FileNotFoundError

    # use lxml and parse the .l5x xml into a dictionary
    try:
        parser = lxml.etree.XMLParser(strip_cdata=False)
        tree = lxml.etree.parse(file_location, parser)
        root = tree.getroot()
        xml_str = lxml.etree.tostring(root, encoding='utf-8').decode("utf-8")
    except FileNotFoundError:
        print(f"Error: File not found: {file_location}")
        return None
    except ET.ParseError:
        print(f"Error: Invalid XML format in {file_location}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

    if not xml_str:
        return None

    # update c_data sections to create comments from all comment data
    try:
        xml_str = xml_str.replace("<![CDATA[]]>", "<![CDATA[//]]>")
        return xmltodict.parse(xml_str)
    except KeyError:
        return None


class LogixInstruction:
    """Logix instruction
    """


class LogixElement(Enum):
    """logix element resolver enumeration
    """
    DEFAULT = 0
    TAG = 1
    DATATYPE = 2
    AOI = 3
    MODULE = 4
    PROGRAM = 5
    ROUTINE = 6
    PROGRAMTAG = 7
    RUNG = 8
    ALL = 9


class PlcObject(EnforcesNaming, SnowFlake):
    """base class for a l5x plc object
    """

    def __getitem__(self, key):
        return self._meta_data.get(key, None)

    def __setitem__(self, key, value):
        self._meta_data[key] = value

    def __init__(self,
                 l5x_meta_data: dict,
                 controller: 'Controller'):
        SnowFlake.__init__(self)

        if not l5x_meta_data:
            raise ValueError('Cannot create an object from nothing!')

        self._meta_data = l5x_meta_data
        self._controller = controller

    @property
    def config(self) -> 'ControllerConfiguration':
        if not self._controller:
            return None
        return self._controller._config

    @property
    def controller(self):
        """get this object's controller

        .. -------------------------------

        Returns
        ----------
            :class:`Controller`
        """
        return self._controller

    @property
    def name(self) -> str:
        """get this object's meta data name

        .. -------------------------------

        Returns
        ----------
            :class:`str`
        """
        return self['@Name']

    @name.setter
    def name(self, value: str):
        if not self.is_valid_string(value):
            raise self.InvalidNamingException

        self['@Name'] = value

    @property
    def description(self) -> str:
        """get this object's meta data description

        .. -------------------------------

        Returns
        ----------
            :class:`str`
        """
        return self['Description']

    @description.setter
    def description(self, value: str):
        self['Description'] = value

    @property
    def meta_data(self) -> dict:
        return self._meta_data


class SupportsMeta(Generic[T], PlcObject):
    """meta type for 'supports' structuring
    """

    @property
    def __key__(self) -> str:
        raise NotImplementedError()

    def __set__(self, value: T):
        if not isinstance(value, get_args(self.__orig_bases__[0])[0]):
            raise ValueError(f'Value must be of type {T}!')
        self[self.__key__] = value

    def __get__(self):
        return self[self.__key__]


class SupportsClass(SupportsMeta[str]):
    """This PLC Object supports the @Class property
    """

    @property
    def __key__(self) -> str:
        return '@Class'

    @property
    def class_(self) -> str:
        return super().__get__()

    @class_.setter
    def class_(self, value: str):
        super().__set__(value)


class SupportsExternalAccess(SupportsMeta[str]):
    """This PLC Object supports the @ExternalAccess property
    """
    @property
    def __key__(self) -> str:
        return '@ExternalAccess'

    @property
    def external_access(self) -> str:
        return super().__get__()

    @external_access.setter
    def external_access(self, value: str):
        super().__set__(value)


class SupportsRadix(SupportsMeta[str]):
    """This PLC Object supports the @Radix property
    """

    @property
    def __key__(self) -> str:
        return '@Radix'

    @property
    def radix(self) -> str:
        return super().__get__()

    @radix.setter
    def radix(self, value: str):
        super().__set__(value)


class AddOnInstruction(SupportsClass):
    def __init__(self,
                 l5x_meta_data: dict,
                 controller: 'Controller'):
        """type class for plc AddOn Instruction Definition

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """
        super().__init__(l5x_meta_data=l5x_meta_data,
                         controller=controller)

    @property
    def revision(self) -> str:
        return self['@Revision']

    @property
    def execute_prescan(self) -> str:
        return self['@ExecutePrescan']

    @property
    def execute_postscan(self) -> str:
        return self['@ExecutePostscan']

    @property
    def execute_enable_in_false(self) -> str:
        return self['@ExecuteEnableInFalse']

    @property
    def created_date(self) -> str:
        return self['@CreatedDate']

    @property
    def created_by(self) -> str:
        return self['@CreatedBy']

    @property
    def edited_date(self) -> str:
        return self['@EditedDate']

    @property
    def edited_by(self) -> str:
        return self['@EditedBy']

    @property
    def software_revision(self) -> str:
        return self['@SoftwareRevision']

    @property
    def revision_note(self) -> str:
        return self['RevisionNote']

    @property
    def parameters(self) -> list[dict]:
        if not self['Parameters']:
            return []

        if not isinstance(self['Parameters']['Parameter'], list):
            return [self['Parameters']['Parameter']]
        return self['Parameters']['Parameter']

    @property
    def local_tags(self) -> list[dict]:
        if not self['LocalTags']:
            return []

        if not isinstance(self['LocalTags']['LocalTag'], list):
            return [self['LocalTags']['LocalTag']]
        return self['LocalTags']['LocalTag']

    @property
    def routines(self) -> list[dict]:
        if not self['Routines']:
            return []

        if not isinstance(self['Routines']['Routine'], list):
            return [self['Routines']['Routine']]
        return self['Routines']['Routine']


class ConnectionParameters:
    """connection parameters for connecting to a plc
    """

    def __init__(self,
                 ip_address: str,
                 slot: int,
                 rpi: int = 50):
        # explicit type-casting to enform type protection for this class
        slot = int(slot)
        rpi = int(rpi)

        if len(ip_address.split('.')) != 4:
            raise ValueError('Ip addresses must be specified in groups of 4 - e.g. 192.168.1.2')

        self._ip_address: str = ip_address  # PLC IP Address
        self._slot: int = slot              # PLC Slot
        self._rpi: float = rpi              # PLC Requested Packet Interval

    @property
    def ip_address(self) -> str:
        return self._ip_address

    @property
    def rpi(self) -> int:
        return self._rpi

    @property
    def slot(self) -> int:
        return self._slot


class DatatypeMember(SupportsRadix, SupportsExternalAccess):
    def __init__(self,
                 l5x_meta_data: dict,
                 datatype: 'Datatype',
                 controller: Controller):
        """type class for plc Datatype Member

        Args:
            l5x_meta_data (str): meta data
            datatype (Datatype): parent datatype
            controller (Self): controller dictionary
        """
        super().__init__(l5x_meta_data=l5x_meta_data,
                         controller=controller)
        self._datatype = datatype

    @property
    def datatype(self) -> 'Datatype':
        return self._datatype

    @property
    def dimension(self) -> str:
        return self['@Dimension']

    @property
    def hidden(self) -> str:
        return self['@Hidden']


class Datatype(SupportsClass):
    def __init__(self,
                 l5x_meta_data: dict,
                 controller: Controller):
        """type class for plc Datatype

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """
        super().__init__(l5x_meta_data=l5x_meta_data,
                         controller=controller)
        self._members = [DatatypeMember(x['@Name'], self, self._controller) for x in self.raw_members]

    @property
    def family(self) -> str:
        return self['@Family']

    @property
    def members(self) -> list[DatatypeMember]:
        return self._members

    @property
    def raw_members(self) -> list[dict]:
        if not self['Members']:
            return []

        if not isinstance(self['Members']['Member'], list):
            return [self['Members']['Member']]
        else:
            return self['Members']['Member']


class Module(PlcObject):
    def __init__(self,
                 l5x_meta_data: dict,
                 controller: Controller):
        """type class for plc Module

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """
        super().__init__(l5x_meta_data=l5x_meta_data,
                         controller=controller)

    @property
    def catalog_number(self) -> str:
        return self['@CatalogNumber']

    @property
    def vendor(self) -> str:
        return self['@Vendor']

    @property
    def product_type(self) -> str:
        return self['@ProductType']

    @property
    def product_code(self) -> str:
        return self['@ProductCode']

    @property
    def major(self) -> str:
        return self['@Major']

    @property
    def minor(self) -> str:
        return self['@Minor']

    @property
    def parent_module(self) -> str:
        return self['@ParentModule']

    @property
    def parent_mod_port_id(self) -> str:
        return self['@ParentModPortId']

    @property
    def inhibited(self) -> str:
        return self['@Inhibited']

    @property
    def major_fault(self) -> str:
        return self['@MajorFault']

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
    def communications(self) -> dict:
        if not self['Communications']:
            return None

        return self['Communications']


class Program(SupportsClass):
    def __init__(self,
                 l5x_meta_data: dict,
                 controller: Controller):
        """type class for plc Program

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """
        super().__init__(l5x_meta_data=l5x_meta_data,
                         controller=controller)
        self._routines = [self.config.routine_type(l5x_meta_data=routine,
                                                   controller=self.controller,
                                                   program=self)
                          for routine in self.raw_routines]

    @property
    def test_edits(self) -> str:
        return self['@TestEdits']

    @property
    def main_routine_name(self) -> str:
        return self['@MainRoutineName']

    @property
    def disabled(self) -> str:
        return self['@Disabled']

    @property
    def use_as_folder(self) -> str:
        return self['@UseAsFolder']

    @property
    def tags(self) -> list[dict]:
        if not self['Tags']:
            return []

        if not isinstance(self['Tags']['Tag'], list):
            return [self['Tags']['Tag']]

        return self['Tags']['Tag']

    @property
    def routines(self) -> list[Routine]:
        return self._routines

    @property
    def raw_routines(self) -> list[dict]:
        if not self['Routines']:
            return []

        if not isinstance(self['Routines']['Routine'], list):
            return [self['Routines']['Routine']]

        return self['Routines']['Routine']


class ProgramTag(PlcObject):
    def __init__(self,
                 l5x_meta_data: dict,
                 controller: Controller,
                 program: Optional[Program] = None):
        """type class for plc Program Tag

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """
        super().__init__(l5x_meta_data=l5x_meta_data,
                         controller=controller)
        self._program: Optional[Program] = program

    @property
    def program(self) -> Optional[Program]:
        return self._program


class Routine(PlcObject):
    def __init__(self,
                 l5x_meta_data: dict,
                 controller: Controller,
                 program: Optional[Program] = None):
        """type class for plc Routine

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """
        super().__init__(l5x_meta_data=l5x_meta_data,
                         controller=controller)

        self._program: Optional[Program] = program
        self._rungs = [self.config.rung_type(l5x_meta_data=x,
                                             controller=self.controller,
                                             routine=self)
                       for x in self.raw_rungs]

    @property
    def program(self) -> Optional[Program]:
        return self._program

    @property
    def rungs(self) -> list[Rung]:
        return self._rungs

    @property
    def raw_rungs(self) -> list[dict]:
        if not self['RLLContent']:
            return []

        if not isinstance(self['RLLContent']['Rung'], list):
            return [self['RLLContent']['Rung']]

        return self['RLLContent']['Rung']


class Rung(PlcObject):
    def __init__(self,
                 l5x_meta_data: dict,
                 controller: Controller,
                 routine: Optional[Routine] = None):
        """type class for plc Rung

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """
        super().__init__(l5x_meta_data=l5x_meta_data,
                         controller=controller)
        self._routine: Optional[Routine] = routine

    def __repr__(self):
        return (
            f'Rung(number={self.number}, '
            f'routine={self.routine.name}, '
            f'type={self.type}, '
            f'comment={self.comment}, '
            f'text={self.text}),'
            f'instructions={self.instructions}),'
        )

    def __str__(self):
        return self.text

    @property
    def number(self) -> str:
        return self['@Number']

    @property
    def routine(self) -> Optional[Routine]:
        return self._routine

    @property
    def type(self) -> str:
        return self['@Type']

    @property
    def comment(self) -> str:
        return self['Comment']

    @property
    def text(self) -> str:
        return self['Text']

    @property
    def instructions(self) -> list[LogixInstruction]:
        return self._get_instructions()

    def _get_instructions(self):
        matches = re.findall(INST_RE_PATTERN, self.text)
        if not matches:
            return []

        return matches


class Tag(SupportsClass, SupportsExternalAccess):
    def __init__(self,
                 l5x_meta_data: dict,
                 controller: 'Controller'):
        """type class for plc Tag

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """
        super().__init__(l5x_meta_data=l5x_meta_data,
                         controller=controller)

    @property
    def tag_type(self) -> str:
        return self['@TagType']

    @property
    def datatype(self) -> str:
        return self['@DataType']

    @property
    def constant(self) -> str:
        return self['@Constant']

    @property
    def opc_ua_access(self) -> str:
        return self['@OpcUaAccess']

    @property
    def data(self) -> list[dict]:
        if not isinstance(self['Data'], list):
            return [self['Data']]

        return self['Data']


@dataclass
class ControllerConfiguration:
    aoi_type: type = AddOnInstruction
    datatype_type: type = Datatype
    module_type: type = Module
    program_type: type = Program
    routine_type: type = Routine
    rung_type: type = Rung
    tag_type: type = Tag


class Controller(PlcObject, Loggable):
    """Controller container for Allen Bradley L5X Files.
    .. ------------------------------------------------------------

    .. package:: emulation_preparation.types.plc

    .. ------------------------------------------------------------

    Arguments
    -----------
    root_meta_data: :class:`str`
        XML style data from .L5X data. Basically, the raw data.

    .. ------------------------------------------------------------

    Attributes
    -----------
    aois: list[:class:`dict`]
        `AddOnInstructionDefintion` list from L5X.

    comm_path: :type:`str`
        Communication path for physical controller.

    datatypes: list[:class:`dict`]
        `Datatypes` list from L5X.

    file_location: :type:`str`
        File location of the .L5X the `Controller` was loaded from.

    ip_address: :type:`str`
        IP Address of the physical controller.

    l5x_meta_data: :type:`dict`
        The dictionary object parsed from .L5X (xml) format.

    major_revision: :type:`int`
        Major revision of the parsed controller.

    minor_revision: :type:`int`
        Minor revision of the parsed controller.

    modules: list[:class:`dict`]
        `Modules` list from L5X.

    name: :type:`str`
        Name of the parsed controller.

    plc_module: :class:`dict`
        Module from `ModuleList` that describes the controller itself. (@Local)

    plc_module_icp_port: :class:`dict`
        ICP Port for the physical controller. Contains connection parameter information.

    plc_module_ports: list[:class:`dict`]
        Ports of the physical controller. Contains connection parameter information.

    programs: list[:class:`dict`]
        `Programs` list from L5X.

    root_meta_data: :type:`str`
        Absolute root from the .L5X file. Required for compression back into a .L5X file.

    slot: :type:`int`
        The physical chassis slot for the controller.

    tags: list[:class:`dict`]
        `Tags` list from L5X.

        """

    def __init__(self,
                 root_meta_data: str,
                 config: Optional[ControllerConfiguration] = ControllerConfiguration()):
        self._root_meta_data = root_meta_data
        self._file_location: str = ''
        self._ip_address: str = ''
        self._slot = 0
        self._config = config

        PlcObject.__init__(self, self.l5x_meta_data, self)
        Loggable.__init__(self)

        if not self.plc_module:
            raise ValueError('Could not find @Local in plc Modules!')

        try:
            self._assign_address(self.comm_path.split('\\')[-1])
            self._slot = int(self.plc_module_icp_port['@Address'])
        except (ValueError, TypeError) as e:
            self.logger.error('ip address assignment err -> %s', e)

        if not self._config:
            raise RuntimeError('Configuration must be supplied when creating a controller!')

        self._aois: list = [self._config.aoi_type(x, self) for x in self.raw_aois]
        self._datatypes: list = [self._config.datatype_type(x, self) for x in self.raw_datatypes]
        self._modules: list = [self._config.module_type(x, self) for x in self.raw_modules]
        self._programs: list = [self._config.program_type(x, self) for x in self.raw_programs]
        self._tags: list = [self._config.tag_type(x, self) for x in self.raw_tags]

    @property
    def aois(self) -> list[AddOnInstruction]:
        return self._aois

    @property
    def raw_aois(self) -> list[dict]:
        """`AddOnInstructionDefintion` list from L5X.

        .. ------------------------------------------------------------

        Returns
        ----------

            aois: list[:class:`dict`]

        """
        return self['AddOnInstructionDefinitions']['AddOnInstructionDefinition']

    @property
    def comm_path(self) -> str:
        """Communication path for physical controller.

        .. ------------------------------------------------------------

        Returns
        ----------

            comm_path: :type:`str`

        """
        return self['@CommPath']

    @property
    def datatypes(self) -> list[Datatype]:
        return self._datatypes

    @property
    def raw_datatypes(self) -> list[dict]:
        """`Datatypes` list from L5X.

        .. ------------------------------------------------------------

        Returns
        ----------

            datatypes: list[:class:`dict`]

        """
        return self['DataTypes']['DataType']

    @property
    def file_location(self) -> str:
        """File location of the .L5X the `Controller` was loaded from.        

        .. ------------------------------------------------------------

        Returns
        ----------

            aois: list[:class:`dict`]

        """
        return self._file_location

    @file_location.setter
    def file_location(self,
                      value: str):
        self._file_location = value

    @property
    def ip_address(self) -> str:
        """IP Address of the physical controller.        

        .. ------------------------------------------------------------

        Returns
        ----------

            ip_address: :type:`str`

        """
        return self._ip_address

    @ip_address.setter
    def ip_address(self,
                   value: str):
        self._assign_address(value)

    @property
    def l5x_meta_data(self) -> dict:
        """The dictionary object parsed from .L5X (xml) format.

        .. ------------------------------------------------------------

        Returns
        ----------

            l5x_meta_data: :type:`dict`

        """
        return self._root_meta_data['RSLogix5000Content']['Controller']

    @l5x_meta_data.setter
    def l5x_meta_data(self, value) -> None:
        self._root_meta_data['RSLogix5000Content']['Controller'] = value

    @property
    def major_revision(self) -> int:
        """Major revision of the parsed controller.

        .. ------------------------------------------------------------

        Returns
        ----------

            major_revision: :type:`int`

        """
        return int(self['@MajorRev'])

    @property
    def minor_revision(self) -> int:
        """Minor revision of the parsed controller.

        .. ------------------------------------------------------------

        Returns
        ----------

            minor_revision: :type:`int`

        """
        return int(self['@MinorRev'])

    @property
    def modules(self) -> list[Module]:
        return self._modules

    @property
    def raw_modules(self) -> list[dict]:
        """`Modules` list from L5X.

        .. ------------------------------------------------------------

        Returns
        ----------

            modules: list[:class:`dict`]

        """
        return self['Modules']['Module']

    @property
    def name(self) -> str:
        """Name of the parsed controller.

        .. ------------------------------------------------------------

        Returns
        ----------

            name: :type:`str`

        """
        return self['@Name']

    @property
    def plc_module(self) -> dict:
        """Module from `ModuleList` that describes the controller itself. (@Local)        

        .. ------------------------------------------------------------

        Returns
        ----------

            plc_module: :class:`dict`

        """
        return next((x for x in self.raw_modules if x['@Name'] == 'Local'), None)

    @property
    def plc_module_icp_port(self) -> dict:
        """ICP Port for the physical controller. Contains connection parameter information.        

        .. ------------------------------------------------------------

        Returns
        ----------

            plc_module_icp_port: :class:`dict`

        """
        return next((x for x in self.plc_module_ports if x['@Type'] == 'ICP' or x['@Type'] == '5069'), None)

    @property
    def plc_module_ports(self) -> list[dict]:
        """Ports of the physical controller. Contains connection parameter information.        

        .. ------------------------------------------------------------

        Returns
        ----------

            plc_module_ports: list[:class:`dict`]

        """
        return self.plc_module['Ports']['Port']

    @property
    def programs(self) -> list[Program]:
        return self._programs

    @property
    def raw_programs(self) -> list[dict]:
        """`Programs` list from L5X.

        .. ------------------------------------------------------------

        Returns
        ----------

            programs: list[:class:`dict`]

        """
        return self['Programs']['Program']

    @property
    def root_meta_data(self) -> dict:
        """Absolute root from the .L5X file. Required for compression back into a .L5X file.

        .. ------------------------------------------------------------

        Returns
        ----------

            root_meta_data: :type:`str`

        """
        return self._root_meta_data

    @property
    def slot(self) -> int:
        """The physical chassis slot for the controller.

        .. ------------------------------------------------------------

        Returns
        ----------

            slot: :type:`int`

        """
        return int(self._slot)

    @slot.setter
    def slot(self,
             value: int):
        self._slot = int(value)

    @property
    def tags(self) -> list[Tag]:
        return self._tags

    @property
    def raw_tags(self) -> list[dict]:
        """`Tags` list from L5X.

        .. ------------------------------------------------------------

        Returns
        ----------

            tags: list[:class:`dict`]

        """
        return self['Tags']['Tag']

    @classmethod
    def from_file(cls: Self,
                  file_location: str) -> Optional[Self]:
        """Get an assembled controller from a given file location

        .. ------------------------------------------------------------

        Arguments
        ----------
        file_location: :type:`str`
            File location to try to load a controller from.

        .. Must be a .L5X file!

        .. ------------------------------------------------------------

        Returns
        ----------
            :class:`Controller`

        """
        root_data = controller_dict_from_file(file_location)
        if not root_data:
            return None

        return cls(root_data)

    def _assign_address(self,
                        address: str):
        octets = address.split('.')
        if not octets or len(octets) != 4:
            raise ValueError('IP Octets invalid!')

        for _, v in enumerate(octets):
            if 0 > int(v) > 255:
                raise ValueError(f'IP address octet range ivalid: {v}')

        self._ip_address = address

    def rename_asset(self,
                     element_type: LogixElement,
                     name: str,
                     replace_name: str):
        """rename an asset of the controller

        Args:
            resolver (enums.Resolver): which asset(s) to rename
            name (str): name to rename
            replace_name (str): final name
        """
        if not element_type or not name or not replace_name:
            return

        match element_type:
            case LogixElement.TAG:
                self.raw_tags = replace_strings_in_dict(
                    self.raw_tags, name, replace_name)

            case LogixElement.ALL:
                self.l5x_meta_data = replace_strings_in_dict(
                    self.l5x_meta_data, name, replace_name)

            case _:
                return


class ModuleReportException(Exception):
    """Base exception for module reporting.
    """

    def __init__(self, msg='My default message', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


class DataTypeReportException(Exception):
    """Base exception for datatype reporting.
    """

    def __init__(self, msg='My default message', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


class AddOnInstructionReportException(Exception):
    """Base exception for addon instruction reporting.
    """

    def __init__(self, msg='My default message', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


class TagReportException(Exception):
    """Base exception for tag reporting.
    """

    def __init__(self, msg='My default message', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


class ProgramReportException(Exception):
    """Base exception for program reporting.
    """

    def __init__(self, msg='My default message', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


class ModuleInhibitedException(ModuleReportException):
    """Module is inhibited!
    """

    def __init__(self, msg='Module should not be inhibted!', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


class ModuleNoCatalogException(ModuleReportException):
    """Module has no catalog number!
    """

    def __init__(self, msg='Module has no catalog number!', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


class ModuleNoVendorException(ModuleReportException):
    """Module has no vendor number!
    """

    def __init__(self, msg='Module has no vendor number!', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


class DataTypeNoFamilyException(DataTypeReportException):
    """Datatype has no family type!
    """

    def __init__(self, msg='Datatype has no family type!', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


class DataTypeNoMembersException(DataTypeReportException):
    """Datatype has no members!
    """

    def __init__(self, msg='Datatype has no members!', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


class ControllerReport(Loggable):
    """Controller status report

    Get detailed information about a controller, showing problem areas, etc.
    """

    def __init__(self,
                 controller: Controller):
        super().__init__()
        self._controller: Controller = controller
        self._health_counter:    int = 0
        self._health_value:      int = 0

    @property
    def health(self) -> Tuple[int, int]:
        return (self._health_value, self._health_counter)

    def _log_health(self):
        _log_char = '█'
        _health = self.health
        _log_chart = _log_char * int((self._health_counter * (_health[0]/_health[1])))
        self.logger.info(f'Health -> {_log_chart}')

    def _tick_health(self, health_good: bool):
        """using boolean assignment, increment a health counter and health value.

        This allows for a rolling counter, while tracking how much of the health was actually good.

        In the end, is used to show health such as: 60/120, then be translated to a percentage (66% Healthy).
        """
        self._health_counter += 1
        if health_good:
            self._health_value += 1
        # self._log_health()

    def _check_aois(self):
        self.logger.info('Checking addon instructions...')

        for aoi in self._controller.aois:
            try:
                self.logger.info('AddOnInstruction: %s' % aoi.name)

                self.logger.info('ok...')

            except AddOnInstructionReportException as e:
                self.logger.error('error -> %s' % e)

    def _check_controller(self):
        self.logger.info('Checking controller...')

        # comm path
        self.logger.info('Comms path...')
        good = True if self._controller.comm_path != '' else False
        if good:
            self.logger.info('ok... -> %s' % str(self._controller.comm_path))
        else:
            self.logger.error('error!')
        self._tick_health(good)

        # ip address
        self.logger.info('IP Address...')
        good = True if self._controller.ip_address != '' else False
        if good:
            self.logger.info('ok... -> %s' % str(self._controller.ip_address))
        else:
            self.logger.error('error!')
        self._tick_health(good)

        # slot
        self.logger.info('Slot...')
        good = True if self._controller.slot is not None else False
        if good:
            self.logger.info('ok... -> %s' % str(self._controller.slot))
        else:
            self.logger.error('error!')
        self._tick_health(good)

        # plc module
        self.logger.info('PLC Module...')
        good = True if self._controller.plc_module else False
        if good:
            self.logger.info('ok... -> %s' % str(self._controller.plc_module['@Name']))
        else:
            self.logger.error('error!')
        self._tick_health(good)

    def _check_datatypes(self):
        self.logger.info('Checking datatypes...')
        for datatype in self._controller.datatypes:
            try:
                self.logger.info('Datatype: %s' % datatype.name)

                if datatype.family is None:
                    raise DataTypeNoFamilyException

                if datatype.members is None:
                    raise DataTypeNoMembersException

                self.logger.info('ok...')

            except DataTypeReportException as e:
                self.logger.error('error -> %s' % e)

    def _check_modules(self):
        self.logger.info('Checking modules...')
        for module in self._controller.modules:
            try:
                self.logger.info('Module: %s' % module.name)

                if module.catalog_number is None:
                    raise ModuleNoCatalogException

                if module.vendor is None:
                    raise ModuleNoVendorException

                self.logger.info('ok...')

            except ModuleReportException as e:
                self.logger.error('error -> %s' % e)

    def _check_programs(self):
        self.logger.info('Checking programs...')

        for program in self._controller.programs:
            try:
                self.logger.info('Program: %s' % program.name)

                self.logger.info('ok...')

            except ProgramReportException as e:
                self.logger.error('error -> %s' % e)

    def _check_tags(self):
        self.logger.info('Checking tags...')

        for tag in self._controller.tags:
            try:
                self.logger.info('Tag: %s' % tag.name)

                self.logger.info('ok...')

            except TagReportException as e:
                self.logger.error('error -> %s' % e)

    def run(self) -> Self:
        self.logger.info('Starting report...')
        self._check_controller()
        self._check_modules()
        self._check_datatypes()
        self._check_aois()
        self._check_tags()
        self._check_programs()
        self.logger.info('Finalizing report...')
        return self

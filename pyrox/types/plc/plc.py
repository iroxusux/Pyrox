"""plc type module
    """
from __future__ import annotations


from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import os
import re
from typing import Generic, get_args, Optional, Self, TypeVar, Union
import xml.etree.ElementTree as ET


import lxml.etree
import xmltodict


from ..abc.meta import EnforcesNaming, Loggable, SnowFlake


from ...services.plc_services import xml_dict_from_file
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

PLC_ROOT_FILE = r'docs\controls\root.L5X'
PLC_PROG_FILE = r'docs\controls\_program.L5X'
PLC_ROUT_FILE = r'docs\controls\_routine.L5X'
PLC_DT_FILE = r'docs\controls\_datatype.L5X'
PLC_AOI_FILE = r'docs\controls\_aoi.L5X'
PLC_MOD_FILE = r'docs\controls\_module.L5X'
PLC_RUNG_FILE = r'docs\controls\_rung.L5X'
PLC_TAG_FILE = r'docs\controls\_tag.L5X'
OTE_OPERAND_RE_PATTERN = r"(?:OTE\()(.*)(?:\))"


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
        return self._l5x_meta_data.get(key, None)

    def __setitem__(self, key, value):
        self._l5x_meta_data[key] = value

    def __init__(self,
                 l5x_meta_data: dict = defaultdict(None),
                 controller: 'Controller' = None):
        SnowFlake.__init__(self)

        self._l5x_meta_data = l5x_meta_data
        self._controller = controller

    @property
    def config(self) -> ControllerConfiguration:
        if not self._controller:
            return ControllerConfiguration()
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
        return self._l5x_meta_data

    def validate(self) -> 'ControllerReportItem':
        return ControllerReportItem(self,
                                    'N/A',
                                    False,
                                    'Testing to be implimented...')


class SupportsMeta(Generic[T], PlcObject):
    """meta type for 'supports' structuring
    """

    @property
    def __key__(self) -> str:
        raise NotImplementedError()

    def __set__(self, value: T):
        try:
            base = get_args(self.__orig_bases__[0])[0]
        except TypeError:
            base = get_args(self.__orig_bases__[0])
        if not isinstance(value, base):
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
                 name: str = None,
                 l5x_meta_data: dict = None,
                 controller: 'Controller' = None):
        """type class for plc AddOn Instruction Definition

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """

        if not l5x_meta_data:
            l5x_meta_data = xml_dict_from_file(PLC_AOI_FILE)['AddOnInstructionDefinition']

        super().__init__(l5x_meta_data=l5x_meta_data,
                         controller=controller)

        if name:
            self.name = name

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

    def validate(self):
        test_notes = []

        return ControllerReportItem(self,
                                    'Testing aoi attributes...',
                                    True,
                                    '\n'.join(test_notes))


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
                 name: str = None,
                 l5x_meta_data: dict = None,
                 controller: Controller = None):
        """type class for plc Datatype

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """
        if not l5x_meta_data:
            l5x_meta_data = xml_dict_from_file(PLC_DT_FILE)['DataType']

        super().__init__(l5x_meta_data=l5x_meta_data,
                         controller=controller)

        if name:
            self.name = name

    @property
    def family(self) -> str:
        return self['@Family']

    @property
    def members(self) -> list[DatatypeMember]:
        return [DatatypeMember(x['@Name'], self, self._controller) for x in self.raw_members]

    @property
    def raw_members(self) -> list[dict]:
        if not self['Members']:
            return []

        if not isinstance(self['Members']['Member'], list):
            return [self['Members']['Member']]
        else:
            return self['Members']['Member']

    def validate(self):
        test_notes = []

        return ControllerReportItem(self,
                                    'Testing datatype attributes...',
                                    True,
                                    '\n'.join(test_notes))


class Module(PlcObject):
    def __init__(self,
                 name: str = None,
                 l5x_meta_data: dict = None,
                 controller: Controller = None):
        """type class for plc Module

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """

        if not l5x_meta_data:
            l5x_meta_data = xml_dict_from_file(PLC_MOD_FILE)['Module']

        super().__init__(l5x_meta_data=l5x_meta_data,
                         controller=controller)

        if name:
            self.name = name

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

    def validate(self) -> ControllerReportItem:

        conns = None
        std_conn_ok = True
        safe_conn_ok = True
        test_notes = []

        while True:
            if self.communications is not None:
                if self.communications['Connections'] is not None:
                    conns = self.communications['Connections']['Connection']
                    if not isinstance(conns, list):
                        conns = [conns]

                if not conns:
                    break

                std_connection = next((x for x in conns if x['@Name'] == 'Standard'), None)
                safe_in_connection = next((x for x in conns if x['@Name'] == 'SafetyInput'), None)
                safe_out_connection = next((x for x in conns if x['@Name'] == 'SafetyOutput'), None)

                # ------------- check standard connection --------------- #
                if std_connection:
                    # check unicast operations for module
                    try:
                        if std_connection['@Unicast'] != 'true':
                            std_conn_ok = False
                            test_notes.append('Module standard tag not set for unicast!')
                    except KeyError:
                        test_notes.append('Module does not have @Unicast option...')

                    # check standard RPI (requested packet interval) settings for module
                    try:
                        if int(std_connection['@RPI']) > 50_000 or int(std_connection['@RPI']) < 10_000:
                            std_conn_ok = False
                            test_notes.append('Module RPI must be above 10ms and below 50ms! (ideally, about 20ms).')
                    except KeyError:
                        test_notes.append('Module does not support RPI setting...')

                # ------------- check safety input connection --------------- #
                if safe_in_connection:
                    # check unicast operations for module
                    if safe_in_connection['@InputConnectionType'] != 'Unicast':
                        safe_conn_ok = False
                        test_notes.append('Module Safety Input tag not set for unicast!')

                    # check standard RPI (requested packet interval) settings for module
                    # TODO -> Match the RPI of an input module to the RPI of the controller safety task
                    elif int(safe_in_connection['@RPI']) > 50_000 or int(safe_in_connection['@RPI']) < 10_000:
                        safe_conn_ok = False
                        test_notes.append('Module RPI must be above 10ms and below 50ms! (ideally, about 20ms).')

                # ------------- check safety output connection --------------- #
                if safe_out_connection:
                    # check unicast operations for module
                    if safe_out_connection['@InputConnectionType'] != 'Unicast':
                        safe_conn_ok = False
                        test_notes.append('Module Safety Input tag not set for unicast!')

                    # check standard RPI (requested packet interval) settings for module
                    # TODO -> Match the RPI of an input module to the RPI of the controller safety task
                    elif int(safe_out_connection['@RPI']) > 50_000 or int(safe_out_connection['@RPI']) < 10_000:
                        safe_conn_ok = False
                        test_notes.append('Module RPI must be above 10ms and below 50ms! (ideally, about 20ms).')

                break
            break

        return ControllerReportItem(self,
                                    'Testing module standard and safety i/o settings...',
                                    std_conn_ok and safe_conn_ok,
                                    '\n'.join(test_notes))


class Program(SupportsClass):
    def __init__(self,
                 name: str = None,
                 l5x_meta_data: dict = None,
                 controller: Controller = None):
        """type class for plc Program

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """
        if not l5x_meta_data:
            l5x_meta_data = xml_dict_from_file(PLC_PROG_FILE)['Program']

        super().__init__(l5x_meta_data=l5x_meta_data,
                         controller=controller)

        if name:
            self.name = name

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
        return [self.config.routine_type(l5x_meta_data=routine,
                                         controller=self.controller,
                                         program=self)
                for routine in self.raw_routines]

    @property
    def raw_routines(self) -> list[dict]:
        if not self['Routines']:
            return []

        if not isinstance(self['Routines']['Routine'], list):
            return [self['Routines']['Routine']]

        return self['Routines']['Routine']

    def validate(self):
        test_notes = []

        return ControllerReportItem(self,
                                    'Testing program attributes...',
                                    True,
                                    '\n'.join(test_notes))


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
                 name: str = None,
                 l5x_meta_data: dict = None,
                 controller: Controller = None,
                 program: Optional[Program] = None):
        """type class for plc Routine

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """
        if not l5x_meta_data:
            l5x_meta_data = xml_dict_from_file(PLC_ROUT_FILE)['Routine']

        super().__init__(l5x_meta_data=l5x_meta_data,
                         controller=controller)

        if name:
            self.name = name

        self._program: Optional[Program] = program

    @property
    def program(self) -> Optional[Program]:
        return self._program

    @property
    def rungs(self) -> list[Rung]:
        return [self.config.rung_type(l5x_meta_data=x,
                                      controller=self.controller,
                                      routine=self)
                for x in self.raw_rungs]

    @property
    def raw_rungs(self) -> list[dict]:
        if not self['RLLContent']:
            return []

        if not isinstance(self['RLLContent']['Rung'], list):
            return [self['RLLContent']['Rung']]

        return self['RLLContent']['Rung']


class Rung(PlcObject):
    def __init__(self,
                 l5x_meta_data: dict = None,
                 controller: Controller = None,
                 routine: Optional[Routine] = None):
        """type class for plc Rung

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """

        if not l5x_meta_data:
            l5x_meta_data = xml_dict_from_file(PLC_RUNG_FILE)['Rung']

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

    @routine.setter
    def routine(self, value: Routine):
        self._routine = value

    @property
    def type(self) -> str:
        return self['@Type']

    @property
    def comment(self) -> str:
        return self['Comment']

    @comment.setter
    def comment(self, value: str):
        self['Comment'] = value

    @property
    def text(self) -> str:
        return self['Text']

    @text.setter
    def text(self, value: str):
        self['Text'] = value

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
                 name: str = None,
                 l5x_meta_data: dict = None,
                 controller: 'Controller' = None):
        """type class for plc Tag

        Args:
            l5x_meta_data (str): meta data
            controller (Self): controller dictionary
        """

        if not l5x_meta_data:
            l5x_meta_data = xml_dict_from_file(PLC_TAG_FILE)['Tag']

        super().__init__(l5x_meta_data=l5x_meta_data,
                         controller=controller)

        if name:
            self.name = name

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

    def validate(self):
        test_notes = []

        return ControllerReportItem(self,
                                    'Testing tag attributes...',
                                    True,
                                    '\n'.join(test_notes))


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

        """

    def __init__(self,
                 root_meta_data: str = None,
                 config: Optional[ControllerConfiguration] = ControllerConfiguration()):

        self._root_meta_data: dict = root_meta_data if root_meta_data else controller_dict_from_file(PLC_ROOT_FILE)
        self._file_location, self._ip_address = '', ''
        self._slot = 0
        self._config = config

        PlcObject.__init__(self, self.l5x_meta_data, self)
        Loggable.__init__(self)

        if not self.plc_module:
            raise ValueError('Could not find @Local in plc Modules!')

        try:
            self._assign_address(self.comm_path.split('\\')[-1])
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error('ip address assignment err -> %s', e)

        if not self._config:
            raise RuntimeError('Configuration must be supplied when creating a controller!')

        self._aois: list = [self._config.aoi_type(x, self) for x in self.raw_aois]
        self._datatypes: list = [self._config.datatype_type(x, self) for x in self.raw_datatypes]
        self._modules: list = [self._config.module_type(l5x_meta_data=x, controller=self) for x in self.raw_modules]
        self._programs: list = [self._config.program_type(l5x_meta_data=x, controller=self) for x in self.raw_programs]
        self._tags: list = [self._config.tag_type(jl5x_meta_data=x, controller=self) for x in self.raw_tags]

    @property
    def aois(self) -> list[AddOnInstruction]:
        return self._aois

    @property
    def raw_aois(self) -> list[dict]:
        if not self['AddOnInstructionDefinitions']:
            return []
        if not isinstance(self['AddOnInstructionDefinitions']['AddOnInstructionDefinition'], list):
            return [self['AddOnInstructionDefinitions']['AddOnInstructionDefinition']]
        else:
            return self['AddOnInstructionDefinitions']['AddOnInstructionDefinition']

    @property
    def comm_path(self) -> str:

        return self['@CommPath']

    @property
    def datatypes(self) -> list[Datatype]:
        return self._datatypes

    @property
    def raw_datatypes(self) -> list[dict]:

        if not self['DataTypes']:
            return []
        if not isinstance(self['DataTypes']['DataType'], list):
            return [self['DataTypes']['DataType']]
        else:
            return self['DataTypes']['DataType']

    @property
    def file_location(self) -> str:

        return self._file_location

    @file_location.setter
    def file_location(self,
                      value: str):
        self._file_location = value

    @property
    def ip_address(self) -> str:

        return self._ip_address

    @ip_address.setter
    def ip_address(self,
                   value: str):
        self._assign_address(value)

    @property
    def l5x_meta_data(self) -> dict:

        return self._root_meta_data['RSLogix5000Content']['Controller']

    @l5x_meta_data.setter
    def l5x_meta_data(self, value) -> None:
        self._root_meta_data['RSLogix5000Content']['Controller'] = value

    @property
    def major_revision(self) -> int:
        return int(self['@MajorRev'])

    @property
    def minor_revision(self) -> int:
        return int(self['@MinorRev'])

    @property
    def modules(self) -> list[Module]:
        return self._modules

    @property
    def raw_modules(self) -> list[dict]:
        if not self['Modules']:
            return []
        if not isinstance(self['Modules']['Module'], list):
            return [self['Modules']['Module']]
        else:
            return self['Modules']['Module']

    @property
    def plc_module(self) -> dict:
        return next((x for x in self.raw_modules if x['@Name'] == 'Local'), None)

    @property
    def plc_module_icp_port(self) -> dict:
        return next((x for x in self.plc_module_ports if x['@Type'] == 'ICP' or x['@Type'] == '5069'), None)

    @property
    def plc_module_ports(self) -> list[dict]:
        if not self.plc_module:
            return []

        if not isinstance(self.plc_module['Ports']['Port'], list):
            return [self.plc_module['Ports']['Port']]
        return self.plc_module['Ports']['Port']

    @property
    def programs(self) -> list[Program]:
        return self._programs

    @property
    def raw_programs(self) -> list[dict]:
        if not self['Programs']:
            return []
        if not isinstance(self['Programs']['Program'], list):
            return [self['Programs']['Program']]
        else:
            return self['Programs']['Program']

    @property
    def root_meta_data(self) -> dict:
        return self._root_meta_data

    @property
    def slot(self) -> int:
        if not self.plc_module_icp_port:
            return None
        return int(self.plc_module_icp_port['@Address'])

    @slot.setter
    def slot(self,
             value: int):
        self._slot = int(value)

    @property
    def tags(self) -> list[Tag]:
        return self._tags

    @property
    def raw_tags(self) -> list[dict]:
        if not self._l5x_meta_data['Tags']:
            return []
        if not isinstance(self._l5x_meta_data['Tags'], dict):
            raise ValueError('Tags must be a dictionary!')
        if not isinstance(self._l5x_meta_data['Tags']['Tag'], list):
            return [self._l5x_meta_data['Tags']['Tag']]
        else:
            return self._l5x_meta_data['Tags']['Tag']

    @raw_tags.setter
    def raw_tags(self,
                 value: dict):
        if value is None:
            raise ValueError('Tags cannot be None!')
        if not isinstance(value, dict) and not isinstance(value, list):
            raise ValueError('Tags must be a dictionary or a list!')

        if isinstance(value, dict):
            self['Tags'] = value
        elif isinstance(value, list):
            self['Tags']['Tag'] = value

    @classmethod
    def from_file(cls: Self,
                  file_location: str) -> Optional[Self]:
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

    def _add_common(self,
                    plcobject: Union[PlcObject, str, dict],
                    target_list: list,
                    objecttype: type):

        if isinstance(plcobject, PlcObject):
            target_list.append(plcobject)

        elif isinstance(plcobject, dict):
            target_list.append(objecttype(l5x_meta_data=plcobject, controller=self))

        elif isinstance(plcobject, str):
            target_list.append(objecttype(name=plcobject, controller=self))

        else:
            raise TypeError('Invalid type for %s!' % objecttype.__name__)

    def _remove_common(self,
                       plcobject: PlcObject,
                       target_list: list):
        if plcobject in target_list:
            target_list.remove(plcobject)

    def add_aoi(self, aoi: Union[AddOnInstruction, dict, str]):
        self._add_common(aoi, self._aois, self._config.aoi_type)

    def add_datatype(self, datatype: Union[Program, dict, str]):
        self._add_common(datatype, self._datatypes, self._config.datatype_type)

    def add_module(self, module: Union[Module, dict, str]):
        self._add_common(module, self._modules, self._config.module_type)

    def add_program(self, program: Union[Program, dict, str]):
        self._add_common(program, self._programs, self._config.program_type)

    def add_tag(self, tag: Union[Tag, dict, str]):
        self._add_common(tag, self._tags, self._config.tag_type)

    def remove_aoi(self, aoi: AddOnInstruction):
        self._remove_common(aoi, self._aois)

    def remove_datatype(self, datatype: Datatype):
        self._remove_common(datatype, self._datatypes)

    def remove_module(self, module: Module):
        self._remove_common(module, self._modules)

    def remove_program(self, program: Program):
        self._remove_common(program, self._programs)

    def remove_tag(self, tag: Tag):
        self._remove_common(tag, self._tags)

    def find_diagnostic_rungs(self) -> list[Rung]:
        diagnostic_rungs = []

        for program in self.programs:
            for routine in program.routines:
                for rung in routine.rungs:
                    if rung.comment is not None and '<@DIAG>' in rung.comment:
                        diagnostic_rungs.append(rung)
                    else:
                        for instruction in rung.instructions:
                            if 'JSR' in instruction and 'zZ999_Diagnostics' in instruction:
                                diagnostic_rungs.append(rung)
                                break

        return diagnostic_rungs

    def find_redundant_otes(self,
                            include_all_coils=False):
        ote_operands = defaultdict(list)

        routines = []

        for program in self.programs:
            for routine in program.routines:
                routines.append((program.name, routine.name, routine))

        for program_name, routine_name, routine in routines:

            for rung_idx, rung in enumerate(routine.rungs, 1):
                ote_elements = [x for x in rung.instructions if 'OTE(' in x]

                for ote in ote_elements:
                    operand = re.findall(OTE_OPERAND_RE_PATTERN, ote)[0]

                    if operand:
                        location = {
                            'program': program_name,
                            'routine': routine_name,
                            'rung': rung_idx,
                            'operand': operand
                        }
                        ote_operands[operand].append(location)

        redundant_otes = {operand: locations for operand, locations in ote_operands.items() if len(locations) > 1}

        if include_all_coils is False:
            return redundant_otes
        else:
            return (redundant_otes, ote_operands)

    def rename_asset(self,
                     element_type: LogixElement,
                     name: str,
                     replace_name: str):
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

    def validate(self) -> 'ControllerReport':
        return ControllerReport(self).run()


class ControllerReportItem:
    def __init__(self,
                 plc_object: PlcObject,
                 test_description: str,
                 pass_fail: bool,
                 report_description: str):
        if plc_object is None or test_description is None or pass_fail is None or report_description is None:
            raise ValueError('Cannot leave any fields empty/None!')
        self._plc_object: PlcObject = plc_object
        self._test_description: str = test_description
        self._pass_fail: bool = pass_fail
        self._report_description: str = report_description

    def __repr__(self):
        return f'ControllerReportItem(plc_object={self._plc_object},)'\
            f'test_description={self._test_description}, '\
            f'pass_fail={self._pass_fail}, '\
            f'report_description={self._report_description})'

    @property
    def plc_object(self) -> PlcObject:
        return self._plc_object

    @property
    def test_description(self) -> str:
        return self._test_description

    @property
    def pass_fail(self) -> bool:
        return self._pass_fail

    @property
    def report_description(self) -> str:
        return self._report_description


class ControllerReport(Loggable):
    """Controller status report

    Get detailed information about a controller, showing problem areas, etc.
    """

    def __init__(self,
                 controller: Controller):
        super().__init__()
        self._controller: Controller = controller
        self._report_items: list[ControllerReportItem] = []

    @property
    def report_items(self) -> list[ControllerReportItem]:
        return self._report_items

    @property
    def categorized_items(self) -> dict[list[ControllerReportItem]]:
        return self._as_categorized()

    def _check_controller(self):
        self.logger.info('Checking controller...')

        # comm path
        self.logger.info('Comms path...')
        good = True if self._controller.comm_path != '' else False
        if good:
            self.logger.info('ok... -> %s' % str(self._controller.comm_path))
        else:
            self.logger.error('error!')

        # ip address
        self.logger.info('IP Address...')
        good = True if self._controller.ip_address != '' else False
        if good:
            self.logger.info('ok... -> %s' % str(self._controller.ip_address))
        else:
            self.logger.error('error!')

        # slot
        self.logger.info('Slot...')
        good = True if self._controller.slot is not None else False
        if good:
            self.logger.info('ok... -> %s' % str(self._controller.slot))
        else:
            self.logger.error('error!')

        # plc module
        self.logger.info('PLC Module...')
        good = True if self._controller.plc_module else False
        if good:
            self.logger.info('ok... -> %s' % str(self._controller.plc_module['@Name']))
        else:
            self.logger.error('error!')

    def _check_common(self, attr: list[PlcObject]):

        if not isinstance(attr, list):
            raise ValueError

        for x in attr:
            self.logger.info('analyzing "%s"...', x.name)
            self._report_items.append(x.validate())
            if self._report_items[-1].pass_fail is True:
                self.logger.info('validation ok...')
            else:
                self.logger.warning('validation error! -> %s', self._report_items[-1].report_description)

    def _as_categorized(self) -> dict[list[ControllerReportItem]]:
        categories = {}
        for report in self._report_items:
            if report.plc_object.__class__.__name__ not in categories:
                categories[report.plc_object.__class__.__name__] = []
            categories[report.plc_object.__class__.__name__].append(report)
        return categories

    def run(self) -> Self:
        self.logger.info('Starting report...')
        self._check_controller()
        self._check_common(self._controller.modules)
        self._check_common(self._controller.datatypes)
        self._check_common(self._controller.aois)
        self._check_common(self._controller.tags)
        self._check_common(self._controller.programs)
        self.logger.info('Finalizing report...')
        return self

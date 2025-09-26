"""PLC type module for Pyrox framework."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import (
    List,
    Optional,
    Self,
    Tuple,
    Type,
    Union
)
from pyrox.models.abc.factory import MetaFactory, FactoryTypeMeta
from pyrox.services.logging import log
from pyrox.models.abc.list import HashList

from . import meta as plc_meta
from .aoi import AddOnInstruction
from .datatype import Datatype
from .instruction import LogixInstruction
from .module import Module
from .program import Program
from .routine import Routine
from .rung import Rung
from .tag import Tag

from pyrox.services.plc import l5x_dict_from_file
from pyrox.utils import replace_strings_in_dict

__all__ = (
    'Controller',
    'ControllerFactory',
    'ControllerModificationSchema',
    'ControllerSafetyInfo',
)


class ControllerSafetyInfo(plc_meta.PlcObject):
    def __init__(self,
                 meta_data: str,
                 controller: 'Controller'):
        super().__init__(meta_data=meta_data,
                         controller=controller)

    @property
    def safety_locked(self) -> str:
        return self['@SafetyLocked']

    @safety_locked.setter
    def safety_locked(self, value: str):
        if not self.is_valid_rockwell_bool(value):
            raise ValueError("Safety locked must be a valid boolean string (true/false)!")

        self['@SafetyLocked'] = value

    @property
    def signature_runmode_protect(self) -> str:
        return self['@SignatureRunModeProtect']

    @signature_runmode_protect.setter
    def signature_runmode_protect(self, value: str):
        if not self.is_valid_rockwell_bool(value):
            raise ValueError("Signature run mode protect must be a valid boolean string (true/false)!")

        self['@SignatureRunModeProtect'] = value

    @property
    def configure_safety_io_always(self) -> str:
        return self['@ConfigureSafetyIOAlways']

    @configure_safety_io_always.setter
    def configure_safety_io_always(self, value: str):
        if not self.is_valid_rockwell_bool(value):
            raise ValueError("Configure safety IO always must be a valid boolean string (true/false)!")

        self['@ConfigureSafetyIOAlways'] = value

    @property
    def safety_level(self) -> str:
        return self['@SafetyLevel']

    @safety_level.setter
    def safety_level(self, value: str):
        if not isinstance(value, str):
            raise ValueError("Safety level must be a string!")

        if not any(x in value for x in ['SIL1', 'SIL2', 'SIL3', 'SIL4']):
            raise ValueError("Safety level must contain one of: SIL1, SIL2, SIL3, SIL4!")

        self['@SafetyLevel'] = value

    @property
    def safety_tag_map(self) -> str:
        if self['SafetyTagMap'] is None:
            return ''

        return self['SafetyTagMap']

    @safety_tag_map.setter
    def safety_tag_map(self, value: str):
        if not isinstance(value, str):
            raise ValueError("Safety tag map must be a string!")

        if not value:
            self['SafetyTagMap'] = None
            return

        # Validate format: should be "tag_name=safety_tag_name, ..."
        pairs = value.split(',')
        for pair in pairs:
            pair = pair.strip()
            if not pair:
                continue
            if '=' not in pair or len(pair.split('=')) != 2:
                raise ValueError("Safety tag map must be in the format 'tag_name=safety_tag_name, ...'")

        self['SafetyTagMap'] = value.strip()

    @property
    def safety_tag_map_dict_list(self) -> list[dict]:
        if not self.safety_tag_map:
            return []

        if not isinstance(self.safety_tag_map, str):
            raise ValueError("Safety tag map must be a string!")

        string_data = self.safety_tag_map.strip().split(',')
        if len(string_data) == 1 and string_data[0] == '':
            return []

        dict_list = []
        for pair in string_data:
            dict_list.append({
                '@Name': pair.split('=')[0].strip(),
                'TagName': pair.split('=')[0].strip(),
                'SafetyTagName': pair.split('=')[1].strip()
            })

        return dict_list

    def add_safety_tag_mapping(
        self,
        tag_name: str,
        safety_tag_name: str
    ) -> None:
        """Add a new safety tag mapping to the safety tag map.

        Args:
            tag_name (str): The standard tag name
            safety_tag_name (str): The corresponding safety tag name

        Raises:
            ValueError: If tag names are not strings
        """
        if not isinstance(tag_name, str) or not isinstance(safety_tag_name, str):
            raise ValueError("Tag names must be strings!")

        if not self.safety_tag_map:
            self.safety_tag_map = f"{tag_name}={safety_tag_name}"
            return

        self.safety_tag_map = self.safety_tag_map.strip()
        if f',{tag_name}={safety_tag_name}' in self.safety_tag_map:
            self.safety_tag_map = self.safety_tag_map.replace(f",{tag_name}={safety_tag_name}", '')
        elif f"{tag_name}={safety_tag_name}," in self.safety_tag_map:
            self.safety_tag_map = self.safety_tag_map.replace(f"{tag_name}={safety_tag_name},", '')
        self.safety_tag_map += f",{tag_name}={safety_tag_name}"

    def remove_safety_tag_mapping(
        self,
        tag_name: str,
        safety_tag_name: str
    ) -> None:
        """Remove a safety tag mapping from the safety tag map.

        Args:
            tag_name (str): The standard tag name
            safety_tag_name (str): The corresponding safety tag name
        Raises:
            ValueError: If tag names are not strings
        """
        if not isinstance(tag_name, str) or not isinstance(safety_tag_name, str):
            raise ValueError("Tag names must be strings!")

        if not self.safety_tag_map:
            return

        self.safety_tag_map = self.safety_tag_map.strip()
        if f",{tag_name}={safety_tag_name}" in self.safety_tag_map:
            self.safety_tag_map = self.safety_tag_map.replace(f",{tag_name}={safety_tag_name}", '')
        elif f"{tag_name}={safety_tag_name}," in self.safety_tag_map:
            self.safety_tag_map = self.safety_tag_map.replace(f"{tag_name}={safety_tag_name},", '')
        elif f"{tag_name}={safety_tag_name}" in self.safety_tag_map:
            self.safety_tag_map = self.safety_tag_map.replace(f"{tag_name}={safety_tag_name}", '')


class ControllerFactory(MetaFactory):
    """Controller factory with scoring-based matching."""

    @classmethod
    def get_best_match(
        cls,
        controller_data: dict,
        min_score: float = 0.3
    ) -> Optional[Type]:
        """Get the best matching controller type based on scoring."""
        if not controller_data:
            log(cls).warning("No controller data provided")
            return None

        scored_matches: List[Tuple[float, Type]] = []
        from .matcher import ControllerMatcherFactory

        for _, matcher in ControllerMatcherFactory.get_registered_types().items():
            score = matcher.calculate_score(controller_data)
            ctrl_class = matcher.get_controller_constructor()
            if score >= min_score:
                scored_matches.append((score, matcher.get_controller_constructor()))
                log(cls).info(
                    f"Matched {ctrl_class.__name__} with score {score:.2f}"
                )
            else:
                log(cls).info(
                    f"{ctrl_class.__name__} score {score:.2f} below min score {min_score}"
                )

        if not scored_matches:
            log(cls).info(f"No matches found above min score {min_score}")
            return None

        # Sort by score (highest first) and return the best match
        scored_matches.sort(key=lambda x: x[0], reverse=True)
        best_score, best_class = scored_matches[0]

        log(cls).info(f"Best match: {best_class} with score {best_score:.2f}")
        return best_class

    @classmethod
    def create_controller(
        cls,
        meta_data: dict,
        **kwargs
    ) -> object:
        """Create the best matching controller instance."""
        controller_class = cls.get_best_match(meta_data)
        if not controller_class:
            return None
        return controller_class(meta_data=meta_data, **kwargs)


class Controller(
    plc_meta.NamedPlcObject,
    metaclass=FactoryTypeMeta['Controller', ControllerFactory]
):
    """Controller for a PLC project.

    Args:
        meta_data (str, optional): The meta data for the controller. Defaults to None.
        file_location (str, optional): The file location of the controller project. Defaults to None.
    Raises:
        ValueError: If meta_data is not a dictionary
        \n\tor if required keys are missing
        \n\tor if file_location is not a string
    """

    generator_type = 'EmulationGenerator'

    def __getitem__(self, key):
        return self.controller_meta_data.get(key, None)

    def __setitem__(self, key, value):
        self.controller_meta_data[key] = value
        if key == '@MajorRev' or key == '@MinorRev':
            log(self).info('Changing revisions of processor...')
            self.content_meta_data['@SoftwareRevision'] = f'{self.major_revision}.{self.minor_revision}'
            if not self.plc_module:
                raise RuntimeError('No PLC module found in controller!')
            self.plc_module['@Major'] = self.major_revision
            self.plc_module['@Minor'] = self.minor_revision

    def __init__(
        self,
        meta_data: Optional[dict] = None,
        file_location: Optional[str] = None
    ) -> None:
        super().__init__(meta_data=meta_data)

        self._file_location, self._ip_address, self._slot = file_location, None, None
        self._config = ControllerConfiguration()

        self._aois: HashList[AddOnInstruction] = HashList('name')
        self._datatypes: HashList[Datatype] = HashList('name')
        self._modules: HashList[Module] = HashList('name')
        self._programs: HashList[Program] = HashList('name')
        self._tags: HashList[Tag] = HashList('name')
        self._safety_info: Optional[ControllerSafetyInfo] = None

    @property
    def aois(self) -> HashList[AddOnInstruction]:
        if not self._aois:
            self._compile_common_hashlist_from_meta_data(
                target_list=self._aois,
                target_meta_list=self.raw_aois,
                item_class=self.config.aoi_type,
            )
        return self._aois

    @property
    def raw_aois(self) -> list[dict]:
        return self._get_raw_l5x_asset_list(plc_meta.L5X_ASSET_ADDONINSTRUCTIONDEFINITIONS)

    @property
    def comm_path(self) -> Optional[str]:
        return self['@CommPath']

    @comm_path.setter
    def comm_path(self, value: str):
        if not isinstance(value, str):
            raise ValueError('CommPath must be a string!')
        self['@CommPath'] = value

    @property
    def content_meta_data(self) -> dict:
        if self.meta_data is None:
            raise RuntimeError('Meta data is not set!')
        return self.meta_data['RSLogix5000Content']

    @property
    def controller_meta_data(self) -> dict:
        return self.content_meta_data['Controller']

    @property
    def controller_type(self) -> str:
        return self.__class__.__name__

    @property
    def datatypes(self) -> HashList[Datatype]:
        if not self._datatypes:
            self._compile_common_hashlist_from_meta_data(
                target_list=self._datatypes,
                target_meta_list=self.raw_datatypes,
                item_class=self.config.datatype_type,
            )
        return self._datatypes

    @property
    def raw_datatypes(self) -> list[dict]:
        return self._get_raw_l5x_asset_list(plc_meta.L5X_ASSET_DATATYPES)

    @property
    def file_location(self) -> Optional[str]:
        return self._file_location

    @file_location.setter
    def file_location(
        self,
        value: str
    ):
        if not isinstance(value, str) and value is not None:
            raise ValueError('File location must be a string or None!')
        self._file_location = value

    @property
    def input_instructions(self) -> list[LogixInstruction]:
        instr = []
        [instr.extend(x.input_instructions) for x in self.programs]
        return instr

    @property
    def instructions(self) -> list[LogixInstruction]:
        """get the instructions in this controller

        Returns:
            :class:`list[LogixInstruction]`
        """
        instr = []
        [instr.extend(x.instructions) for x in self.programs]
        # [instr.extend(x.instructions) for x in self.aois]
        return instr

    @property
    def output_instructions(self) -> list[LogixInstruction]:
        instr = []
        [instr.extend(x.output_instructions) for x in self.programs]
        return instr

    @property
    def l5x_meta_data(self) -> dict:
        return self.content_meta_data['Controller']

    @l5x_meta_data.setter
    def l5x_meta_data(self, value) -> None:
        self.content_meta_data['Controller'] = value

    @property
    def major_revision(self) -> int:
        rev = self['@MajorRev']
        if not rev:
            raise RuntimeError('Major revision is not set!')
        return int(rev)

    @major_revision.setter
    def major_revision(self, value: int):
        self['@MajorRev'] = int(value)

    @property
    def meta_data(self) -> Optional[dict]:
        if not isinstance(self._meta_data, dict):
            raise RuntimeError('Meta data must be a dictionary!')
        return self._meta_data

    @meta_data.setter
    def meta_data(self, value: Optional[Union[dict, str]]) -> None:
        if not isinstance(value, dict):
            raise ValueError('Meta data must be a dictionary!')
        self._meta_data = value

    @property
    def minor_revision(self) -> int:
        rev = self['@MinorRev']
        if not rev:
            raise RuntimeError('Minor revision is not set!')
        return int(rev)

    @minor_revision.setter
    def minor_revision(self, value: int):
        self['@MinorRev'] = int(value)

    @property
    def modules(self) -> HashList[Module]:
        if not self._modules:
            self._compile_common_hashlist_from_meta_data(
                target_list=self._modules,
                target_meta_list=self.raw_modules,
                item_class=self.config.module_type,
            )
        return self._modules

    @property
    def raw_modules(self) -> list[dict]:
        return self._get_raw_l5x_asset_list(plc_meta.L5X_ASSET_MODULES)

    @property
    def plc_module(self) -> Optional[dict]:
        if not self.raw_modules:
            return None
        for module in self.raw_modules:
            if not isinstance(module, dict):
                continue
            if module['@Name'] == 'Local':
                return module
        return None

    @property
    def plc_module_icp_port(self) -> Optional[dict]:
        if not self.plc_module_ports:
            return None
        for port in self.plc_module_ports:
            if not isinstance(port, dict):
                continue
            if port['@Type'] == 'ICP' or port['@Type'] == '5069':
                return port
        return None

    @property
    def plc_module_ports(self) -> list[dict]:
        if not self.plc_module:
            return []

        if not isinstance(self.plc_module['Ports']['Port'], list):
            return [self.plc_module['Ports']['Port']]
        return self.plc_module['Ports']['Port']

    @property
    def programs(self) -> HashList[Program]:
        if not self._programs:
            self._compile_common_hashlist_from_meta_data(
                target_list=self._programs,
                target_meta_list=self.raw_programs,
                item_class=self.config.program_type,
            )
        return self._programs

    @property
    def raw_programs(self) -> list[dict]:
        return self._get_raw_l5x_asset_list(plc_meta.L5X_ASSET_PROGRAMS)

    @property
    def safety_info(self) -> Optional[ControllerSafetyInfo]:
        if not self._safety_info:
            self._compile_safety_info()
        return self._safety_info

    @property
    def safety_programs(self) -> list[Program]:
        val = [x for x in self.programs if x.class_ == 'Safety']
        val.sort(key=lambda x: x.name)
        return val

    @property
    def slot(self) -> Optional[int]:
        if not self.plc_module_icp_port:
            return None
        return int(self.plc_module_icp_port['@Address'])

    @slot.setter
    def slot(self,
             value: int):
        self._slot = int(value)

    @property
    def standard_programs(self) -> list[Program]:
        val = [x for x in self.programs if x.class_ == 'Standard']
        val.sort(key=lambda x: x.name)
        return val

    @property
    def tags(self) -> HashList[Tag]:
        if not self._tags:
            self._compile_common_hashlist_from_meta_data(
                target_list=self._tags,
                target_meta_list=self.raw_tags,
                item_class=self.config.tag_type,
                container=self
            )
        return self._tags

    @property
    def raw_tags(self) -> list[dict]:
        return self._get_raw_l5x_asset_list(plc_meta.L5X_ASSET_TAGS)

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
    def from_file(
        cls,
        file_location: str
    ) -> Optional['Controller']:
        """Create a Controller instance from an L5X file.

        Args:
            file_location (str): The file path to the L5X file.

        Returns:
            Optional[Controller]: The created Controller instance, or None if the file could not be read.
        """
        meta_data = l5x_dict_from_file(file_location)
        if meta_data is None:
            return None

        ctrl = ControllerFactory.create_controller(meta_data)
        if not ctrl:
            log(cls).warning('Could not determine controller type from file! Creating generic controller')
            ctrl = cls(
                meta_data=meta_data,
                file_location=file_location
            )

        if not isinstance(ctrl, Controller):
            raise RuntimeError('Incorrect object built from controller factory!')

        return ctrl

    @classmethod
    def from_meta_data(
        cls,
        meta_data: dict
    ) -> 'Controller':
        """Create a Controller instance from meta data.

        Args:
            meta_data (dict): The meta data dictionary to create the controller from.

        Returns:
            Controller: The created Controller instance.

        Raises:
            ValueError: If meta_data is None or not a dictionary
            \n\tor if required keys are missing
            \n\tor if config is not a ControllerConfiguration instance.
        """
        if not meta_data:
            raise ValueError('Meta data cannot be None!')
        if not isinstance(meta_data, dict):
            raise ValueError('Meta data must be a dictionary!')
        if 'RSLogix5000Content' not in meta_data:
            raise ValueError('Meta data must contain RSLogix5000Content!')
        if 'Controller' not in meta_data['RSLogix5000Content']:
            raise ValueError('Meta data must contain Controller!')
        ctrl = cls(meta_data=meta_data)
        return ctrl

    @classmethod
    def get_class(cls) -> Type[Self]:
        return cls

    @classmethod
    def get_factory(cls):
        return ControllerFactory

    def _compile_atomic_datatypes(self) -> None:
        """Compile atomic datatypes from the controller's datatypes."""
        self._datatypes.append(Datatype(meta_data={'@Name': 'BOOL'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'BIT'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'SINT'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'INT'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'DINT'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'LINT'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'USINT'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'UINT'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'UDINT'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'ULINT'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'REAL'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'LREAL'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'STRING'}, controller=self))
        self._datatypes.append(Datatype(meta_data={'@Name': 'TIMER',
                                                   'Members': {'Member': [
                                                       {'@Name': 'PRE'},
                                                       {'@Name': 'ACC'},
                                                       {'@Name': 'EN'},
                                                       {'@Name': 'TT'},
                                                       {'@Name': 'DN'}
                                                   ]}}, controller=self))

    def _compile_common_hashlist_from_meta_data(
        self,
        target_list: HashList,
        target_meta_list: list,
        item_class: type,
        **kwargs
    ) -> None:
        """Compile a common HashList from meta data.

        Args:
            target_list (HashList): The target HashList to populate.
            target_meta_list (list): The list of meta data dictionaries.
            item_class (type): The class type of the items to create.
        """
        if target_list is None:
            target_list = HashList('name')
        target_list.clear()
        for item in target_meta_list:
            if isinstance(item, dict):
                target_list.append(
                    item_class(
                        meta_data=item,
                        controller=self,
                        **kwargs
                    ))
            else:
                log(self).warning(f'Invalid item data: {item}. Skipping...')

    def _compile_from_meta_data(self):
        """Compile this controller from its meta data."""
        log(self).info('Compiling controller from meta data...')
        self._aois.clear()
        self._compile_common_hashlist_from_meta_data(
            target_list=self._aois,
            target_meta_list=self.raw_aois,
            item_class=self.config.aoi_type
        )

        self._datatypes.clear()
        self._compile_common_hashlist_from_meta_data(
            target_list=self._datatypes,
            target_meta_list=self.raw_datatypes,
            item_class=self.config.datatype_type
        )
        self._compile_atomic_datatypes()

        self._modules.clear()
        self._compile_common_hashlist_from_meta_data(
            target_list=self._modules,
            target_meta_list=self.raw_modules,
            item_class=self.config.module_type
        )

        self._programs.clear()
        self._compile_common_hashlist_from_meta_data(
            target_list=self._programs,
            target_meta_list=self.raw_programs,
            item_class=self.config.program_type
        )

        self._tags.clear()
        self._compile_common_hashlist_from_meta_data(
            target_list=self._tags,
            target_meta_list=self.raw_tags,
            item_class=self.config.tag_type,
            container=self
        )

        self._safety_info = None
        self._compile_safety_info()

    def _compile_safety_info(self) -> None:
        """Compile safety information from the controller's safety info."""
        log(self).debug('Compiling safety info from controller...')
        if self._safety_info is None:
            safety_info_data = self.content_meta_data['Controller'].get('SafetyInfo', None)
            if safety_info_data:
                self._safety_info = ControllerSafetyInfo(
                    meta_data=safety_info_data,
                    controller=self
                )
            else:
                log(self).warning('No SafetyInfo found in controller metadata.')

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
                    item: plc_meta.NamedPlcObject,
                    item_class: type,
                    target_list: HashList,
                    target_meta_list: list):

        if not isinstance(item, item_class):
            raise TypeError(f"{item.name} must be of type {item_class}!")

        if item.name in target_list:
            log(self).debug(f'{item.name} already exists in this collection. Updating...')
            meta_item = next((x for x in target_meta_list if x['@Name'] == item.name), None)
            if not meta_item:
                raise ValueError(f'{item.name} not found in target meta list!')
            target_meta_list.remove(meta_item)

        target_meta_list.append(item.meta_data)
        self._invalidate_list_cache(target_list)

    def _remove_common(
        self,
        item: plc_meta.PlcObject,
        target_list: HashList,
        target_meta_list: list
    ) -> None:
        """Remove an item from the controller's collection."""
        if not isinstance(item, plc_meta.PlcObject):
            raise TypeError(f"{item.name} must be of type PlcObject!")

        if item.name not in target_list:
            log(self).warning(f'{item.name} does not exist in this collection. Cannot remove.')
            return

        target_meta_list.remove(next((x for x in target_meta_list if x['@Name'] == item.name), None))
        self._invalidate_list_cache(target_list)

    def _invalidate_list_cache(
        self,
        target_list: HashList
    ) -> None:
        """Invalidate the cached list."""
        if target_list is self.aois:
            self._aois.clear()
        elif target_list is self.datatypes:
            self._datatypes.clear()
        elif target_list is self.modules:
            self._modules.clear()
        elif target_list is self.programs:
            self._programs.clear()
        elif target_list is self.tags:
            self._tags.clear()
        else:
            raise ValueError('Unknown target list!')

    def import_assets_from_file(
        self,
        file_location: str,
        asset_types: Optional[List[str]] = plc_meta.L5X_ASSETS
    ) -> None:
        """Import assets from an L5X file into this controller.
            .. -------------------------------
            .. arguments::
            :class:`str` file_location:
                the L5X file to import from
            :class:`list[str]` asset_types:
                the types of assets to import (e.g., ['DataTypes', 'Tags'])
            """
        l5x_dict = l5x_dict_from_file(file_location)
        if not l5x_dict:
            log(self).warning(f'No L5X dictionary could be read from file: {file_location}')
            return

        self.import_assets_from_l5x_dict(l5x_dict, asset_types=asset_types)

    def import_assets_from_l5x_dict(
        self,
        l5x_dict: dict,
        asset_types: Optional[List[str]] = plc_meta.L5X_ASSETS
    ) -> None:
        """Import assets from an L5X dictionary into this controller.
            .. -------------------------------
            .. arguments::
            :class:`dict` l5x_dict:
                the L5X dictionary to import from
            :class:`list[str]` asset_types:
                the types of assets to import (e.g., ['DataTypes', 'Tags'])
            """
        if not l5x_dict:
            log(self).warning('No L5X dictionary provided for import.')
            return

        if 'RSLogix5000Content' not in l5x_dict:
            log(self).warning('No RSLogix5000Content found in provided L5X dictionary.')
            return
        if 'Controller' not in l5x_dict['RSLogix5000Content']:
            log(self).warning('No Controller found in RSLogix5000Content in provided L5X dictionary.')
            return

        if not asset_types:
            log(self).warning('No asset types provided to import!')
            return

        controller_data = l5x_dict['RSLogix5000Content']['Controller']

        for asset_type in asset_types:
            if asset_type not in controller_data:
                log(self).warning(f'No {asset_type} found in Controller in provided L5X dictionary.')
                continue

            items = controller_data[asset_type]

            item_list = items.get(asset_type[:-1], [])
            if not isinstance(item_list, list):
                item_list = [item_list]

            for item in item_list:
                try:
                    match asset_type:
                        case 'DataTypes':
                            datatype = self.config.datatype_type(controller=self, meta_data=item)
                            self.add_datatype(datatype)
                            log(self).info(f'Datatype {datatype.name} imported successfully.')
                        case 'Tags':
                            tag = self.config.tag_type(controller=self, meta_data=item, container=self)
                            self.add_tag(tag)
                            log(self).info(f'Tag {tag.name} imported successfully.')
                        case 'Programs':
                            program = self.config.program_type(controller=self, meta_data=item)
                            self.add_program(program)
                            log(self).info(f'Program {program.name} imported successfully.')
                        case 'AddOnInstructionDefinitions':
                            aoi = self.config.aoi_type(controller=self, meta_data=item)
                            self.add_aoi(aoi)
                            log(self).info(f'AOI {aoi.name} imported successfully.')
                        case 'Modules':
                            module = self.config.module_type(controller=self, l5x_meta_data=item)
                            self.add_module(module)
                            log(self).info(f'Module {module.name} imported successfully.')
                        case _:
                            log(self).warning(f'Unknown asset type: {asset_type}. Skipping...')
                except ValueError as e:
                    log(self).warning(f'Failed to add {asset_type[:-1]}:\n{e}')
                    continue

    def add_aoi(
        self,
        aoi: AddOnInstruction
    ) -> None:
        """Add an AOI to this controller.
        .. -------------------------------
        .. arguments::
        :class:`AddOnInstruction` aoi:
            the AOI to add
        """
        self._add_common(aoi,
                         self.config.aoi_type,
                         self.aois,
                         self.raw_aois)

    def add_datatype(
        self,
        datatype: Datatype,
    ) -> None:
        """Add a datatype to this controller.
        .. -------------------------------
        .. arguments::
        :class:`Datatype` datatype:
            the datatype to add
        """
        self._add_common(datatype,
                         self.config.datatype_type,
                         self.datatypes,
                         self.raw_datatypes)

    def add_module(
        self,
        module: Module
    ) -> None:
        """Add a module to this controller.
        .. -------------------------------
        .. arguments::
        :class:`Module` module:
            the module to add
        """
        self._add_common(module,
                         self.config.module_type,
                         self.modules,
                         self.raw_modules)

    def add_program(
        self,
        program: Program
    ) -> None:
        """Add a program to this controller.
        .. -------------------------------
        .. arguments::
        :class:`Program` program:
            the program to add
        """
        self._add_common(program,
                         self.config.program_type,
                         self.programs,
                         self.raw_programs)

    def add_tag(
        self,
        tag: Tag
    ) -> None:
        """Add a tag to this controller.
        .. -------------------------------
        .. arguments::
        :class:`Tag` tag:
            the tag to add
        """
        self._add_common(
            tag,
            self.config.tag_type,
            self.tags,
            self.raw_tags
        )

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

    def find_unpaired_controller_inputs(self):
        log(self).info('Finding unpaired controller inputs...')
        inputs = defaultdict(list)
        outputs = set()

        # Collect all input and output operands
        for instr in self.input_instructions:
            for operand in instr.operands:
                inputs[operand.as_qualified].append(operand)
        for instr in self.output_instructions:
            for operand in instr.operands:
                outputs.add(operand.as_qualified)

        unpaired_inputs = {}

        for key, value in inputs.items():
            if key not in outputs:
                # Use set intersection for fast check
                qualified_parents = set(value[0].qualified_parents)
                if qualified_parents.isdisjoint(outputs):
                    unpaired_inputs[key] = [x.as_report_dict() for x in value]

        # Remove common hardware flags
        for key in ['S:FS', 'S:Fs', 'S:fs', 's:fs', 's:FS']:
            unpaired_inputs.pop(key, None)

        return unpaired_inputs

    def find_redundant_otes(self):
        log(self).info('Finding redundant OTEs...')
        outputs = defaultdict(list)

        for inst in [x for x in self.output_instructions if x.instruction_name == 'OTE']:
            outputs[inst.qualified_meta_data].append(inst.as_report_dict())

        shallow_outputs = outputs.copy()

        for key, value in shallow_outputs.items():
            if len(value) < 2:
                del outputs[key]

        return outputs

    def remove_aoi(self, aoi: AddOnInstruction):
        self._remove_common(aoi, self.aois, self.raw_aois)

    def remove_datatype(self, datatype: Datatype):
        self._remove_common(datatype, self.datatypes, self.raw_datatypes)

    def remove_module(self, module: Module):
        self._remove_common(module, self.modules, self.raw_modules)

    def remove_program(self, program: Program):
        self._remove_common(program, self.programs, self.raw_programs)

    def remove_tag(self, tag: Tag):
        self._remove_common(tag, self.tags, self.raw_tags)

    def rename_asset(self,
                     element_type: plc_meta.LogixAssetType,
                     name: str,
                     replace_name: str):
        if not element_type or not name or not replace_name:
            return

        match element_type:
            case plc_meta.LogixAssetType.TAG:
                self.raw_tags = replace_strings_in_dict(
                    self.raw_tags, name, replace_name)

            case plc_meta.LogixAssetType.ALL:
                self.l5x_meta_data = replace_strings_in_dict(
                    self.l5x_meta_data, name, replace_name)

            case _:
                return


@dataclass
class ControllerConfiguration:
    aoi_type: type = AddOnInstruction
    controller_type: type = Controller
    datatype_type: type = Datatype
    module_type: type = Module
    program_type: type = Program
    routine_type: type = Routine
    rung_type: type = Rung
    tag_type: type = Tag


class ControllerModificationSchema:
    """
    Defines a schema for modifying a controller, such as migrating assets between controllers,
    or importing assets from an L5X dictionary.
    """

    def __init__(
        self,
        source: Optional[Controller],
        destination: Optional[Controller]
    ) -> None:
        self.source = source
        self.destination = destination
        self.actions: list[dict] = []  # List of migration actions

    def _execute_add_controller_tag(
        self,
        action: dict
    ) -> None:
        tag_data = action.get('asset')
        if not tag_data:
            log(self).warning('No tag data provided for add_controller_tag action.')
            return

        destination = self._safe_get_destination_controller()
        config = self._safe_get_controller_config()

        tag = config.tag_type(
            meta_data=tag_data,
            controller=self.destination,
            container=self.destination
        )

        try:
            destination.add_tag(tag)
            log(self).info(f'Added tag {tag.name} to destination controller.')
        except ValueError as e:
            log(self).warning(f'Failed to add tag {tag.name}:\n{e}')

    def _execute_add_datatype(
        self,
        action: dict
    ) -> None:
        datatype_data = action.get('asset')
        if not datatype_data:
            log(self).warning('No datatype data provided for add_datatype action.')
            return

        config = self.destination.config

        datatype = config.datatype_type(
            meta_data=datatype_data,
            controller=self.destination
        )

        try:
            self.destination.add_datatype(datatype)
            log(self).info(f'Added datatype {datatype.name} to destination controller.')
        except ValueError as e:
            log(self).warning(f'Failed to add datatype {datatype.name}:\n{e}')

    def _execute_add_program_tag(
        self,
        action: dict
    ) -> None:
        program_name = action.get('program')
        tag_data = action.get('asset')
        if not program_name or not tag_data:
            log(self).warning('Program name or tag data missing for add_program_tag action.')
            return

        program: Program = self.destination.programs.get(program_name)
        if not program:
            log(self).warning(f'Program {program_name} not found in destination controller.')
            return

        config = self.destination.config

        tag = config.tag_type(
            meta_data=tag_data,
            controller=self.destination,
            container=program
        )

        try:
            program.add_tag(tag)
            log(self).info(f'Added tag {tag.name} to program {program_name}.')
        except ValueError as e:
            log(self).warning(f'Failed to add tag {tag.name} to program {program_name}:\n{e}')

    def _execute_add_routine(
        self,
        action: dict
    ) -> None:
        program_name = action.get('program')
        routine_data = action.get('routine')
        if not program_name or not routine_data:
            log(self).warning('Program name or routine data missing for add_routine action.')
            return

        program: Program = self.destination.programs.get(program_name)
        if not program:
            log(self).warning(f'Program {program_name} not found in destination controller.')
            return

        config = self.destination.config

        routine = config.routine_type(
            meta_data=routine_data,
            program=program
        )

        try:
            program.add_routine(routine)
            log(self).info(f'Added routine {routine.name} to program {program_name}.')
        except ValueError as e:
            log(self).warning(f'Failed to add routine {routine.name} to program {program_name}:\n{e}')

    def _execute_add_rung(
        self,
        action: dict
    ) -> None:
        program_name = action.get('program')
        routine_name = action.get('routine')
        rung_data = action.get('new_rung')
        rung_number = action.get('rung_number')
        if not program_name or not routine_name or not rung_data:
            log(self).warning('Program name, routine name, or rung data missing for add_rung action.')
            return

        program: Program = self.destination.programs.get(program_name)
        if not program:
            log(self).warning(f'Program {program_name} not found in destination controller.')
            return

        routine: Routine = program.routines.get(routine_name)
        if not routine:
            log(self).warning(f'Routine {routine_name} not found in program {program_name}.')
            return

        config = self.destination.config

        rung = config.rung_type(
            meta_data=rung_data,
            routine=routine,
            rung_number=rung_number
        )

        try:
            routine.add_rung(rung, index=rung_number)
            log(self).info(f'Added rung {rung.number} to routine {routine_name} in program {program_name}.')
        except ValueError as e:
            log(self).warning(f'Failed to add rung {rung.number} to routine {routine_name} in program {program_name}:\n{e}')

    def _execute_add_safety_tag_mapping(
        self,
        action: dict
    ) -> None:
        std_tag = action.get('standard')
        sfty_tag = action.get('safety')
        if not std_tag or not sfty_tag:
            log(self).warning('Standard or safety tag missing for add_safety_tag_mapping action.')
            return

        try:
            self.destination.safety_info.add_safety_tag_mapping(std_tag, sfty_tag)
            log(self).info(f'Added safety tag mapping: {std_tag} -> {sfty_tag}')
        except ValueError as e:
            log(self).warning(f'Failed to add safety tag mapping {std_tag} -> {sfty_tag}:\n{e}')

    def _execute_controller_tag_migration(
        self,
        action: dict
    ) -> None:
        tag_name = action.get('name')
        tag: Tag = self.source.tags.get(tag_name)
        if not tag:
            log(self).warning(f'Tag {tag_name} not found in source controller.')
            return

        try:
            self.destination.add_tag(tag)
            log(self).info(f'Migrated tag {tag_name} to destination controller.')
        except ValueError as e:
            log(self).warning(f'Failed to migrate tag {tag_name}:\n{e}')

    def _execute_datatype_migration(
        self,
        action: dict
    ) -> None:
        datatype_name = action.get('name')
        datatype: Datatype = self.source.datatypes.get(datatype_name)
        if not datatype:
            log(self).warning(f'Datatype {datatype_name} not found in source controller.')
            return

        try:
            self.destination.add_datatype(datatype)
            log(self).info(f'Migrated datatype {datatype_name} to destination controller.')
        except ValueError as e:
            log(self).warning(f'Failed to migrate datatype {datatype_name}:\n{e}')

    def _execute_import_assets_from_file(
        self,
        action: dict
    ) -> None:
        file_location = action.get('file')
        asset_types = action.get('asset_types', plc_meta.L5X_ASSETS)
        if not file_location:
            log(self).warning('No file location provided for import_datatypes_from_file action.')
            return

        try:
            self.destination.import_assets_from_file(file_location, asset_types)
            log(self).info(f'Imported assets from file {file_location} to destination controller.')
        except Exception as e:
            log(self).warning(f'Failed to import assets from file {file_location}:\n{e}')
            raise e

    def _execute_import_assets_from_l5x_dict(
        self,
        action: dict
    ) -> None:
        l5x_dict = action.get('l5x_dict')
        asset_types = action.get('asset_types', plc_meta.L5X_ASSETS)
        if not l5x_dict:
            log(self).warning('No L5X dictionary provided for import_assets_from_l5x_dict action.')
            return

        try:
            self.destination.import_assets_from_l5x_dict(l5x_dict, asset_types)
            log(self).info('Imported assets from L5X dictionary to destination controller.')
        except Exception as e:
            log(self).warning(f'Failed to import assets from L5X dictionary:\n{e}')
            raise e

    def _execute_remove_controller_tag(
        self,
        action: dict
    ) -> None:
        tag_name = action.get('name')
        tag: Tag = self.destination.tags.get(tag_name)
        if not tag:
            log(self).warning(f'Tag {tag_name} not found in destination controller.')
            return

        self.destination.remove_tag(tag)
        log(self).info(f'Removed tag {tag_name} from destination controller.')

    def _execute_remove_datatype(
        self,
        action: dict
    ) -> None:
        datatype_name = action.get('name')
        datatype: Datatype = self.destination.datatypes.get(datatype_name)
        if not datatype:
            log(self).warning(f'Datatype {datatype_name} not found in destination controller.')
            return

        self.destination.remove_datatype(datatype)
        log(self).info(f'Removed datatype {datatype_name} from destination controller.')

    def _execute_remove_program_tag(
        self,
        action: dict
    ) -> None:
        program_name = action.get('program')
        tag_name = action.get('name')

        program: Program = self.destination.programs.get(program_name)
        if not program:
            log(self).warning(f'Program {program_name} not found in destination controller.')
            return

        tag: Tag = program.tags.get(tag_name)
        if not tag:
            log(self).warning(f'Tag {tag_name} not found in program {program_name}.')
            return

        program.remove_tag(tag)
        log(self).info(f'Removed tag {tag_name} from program {program_name}.')

    def _execute_remove_routine(
        self,
        action: dict
    ) -> None:
        program_name = action.get('program')
        routine_name = action.get('name')

        program: Program = self.destination.programs.get(program_name)
        if not program:
            log(self).warning(f'Program {program_name} not found in destination controller.')
            return

        routine: Routine = program.routines.get(routine_name)
        if not routine:
            log(self).warning(f'Routine {routine_name} not found in program {program_name}.')
            return

        program.remove_routine(routine)
        log(self).info(f'Removed routine {routine_name} from program {program_name}.')
        log(self).debug('Searching for JSR instructions to %s...', routine_name)
        jsr = program.get_instructions('JSR', routine_name)
        if jsr:
            for op in jsr:
                rung: Rung = op.rung
                if not rung:
                    raise ValueError('JSR instruction has no parent rung!')
                jsr_routine: Routine = program.routines.get(rung.routine.name)
                log(self).debug('Found JSR in rung %s of routine %s. Removing rung...', rung.number, jsr_routine.name)
                jsr_routine.remove_rung(rung)

    def _execute_remove_safety_tag_mapping(
        self,
        action: dict
    ) -> None:
        std_tag = action.get('standard')
        sfty_tag = action.get('safety')
        log(self).debug(f'Removing safety tag mapping: {std_tag} -> {sfty_tag}')
        self.destination.safety_info.remove_safety_tag_mapping(std_tag, sfty_tag)

    def _execute_routine_migration(
        self,
        action: dict
    ) -> None:
        source_program_name = action.get('source_program')
        destination_program_name = action.get('destination_program')
        routine_name = action.get('routine')
        rung_updates = action.get('rung_updates', {})

        source_program: Program = self.source.programs.get(source_program_name)
        if not source_program:
            log(self).warning(f'Program {source_program_name} not found in source controller.')
            return

        source_routine: Routine = source_program.routines.get(routine_name)
        if not source_routine:
            log(self).warning(f'Routine {routine_name} not found in program {source_program_name}.')
            return

        destination_program: Program = self.destination.programs.get(destination_program_name)
        if not destination_program:
            log(self).warning(f'Program {destination_program_name} not found in destination controller.')
            return

        destination_program.add_routine(source_routine)
        log(self).info(f'Migrated routine {routine_name} from program {source_program_name} to program {destination_program_name}.')

        dest_routine = self.destination.programs.get(destination_program_name).routines.get(routine_name)
        for rung_num, new_rung in rung_updates.items():
            dest_routine.rungs[rung_num] = new_rung
            log(self).info(f'Updated rung {rung_num} in routine {routine_name} of program {destination_program_name}.')

    def _safe_get_controller_config(self) -> ControllerConfiguration:
        destination = self._safe_get_destination_controller()

        if not destination.config:
            raise ValueError('Destination controller configuration not set!')

        return destination.config

    def _safe_get_destination_controller(self) -> Controller:
        if not self.destination:
            raise ValueError('Destination controller not set!')

        return self.destination

    def _safe_register_action(
        self,
        action: dict
    ) -> None:
        if action not in self.actions:
            self.actions.append(action)
        else:
            log(self).debug('Action already registered, skipping duplicate.')

    def add_controller_tag(
        self,
        tag: Tag
    ) -> Tag:
        """Add an individual tag to import directly to the destination controller.

        Args:
            tag (Tag): The tag to add.

        Raises:
            ValueError: If the provided tag is not an instance of the Tag class.
        """
        if not isinstance(tag, Tag):
            raise ValueError('Tag must be an instance of Tag class.')

        self._safe_register_action({
            'type': 'add_controller_tag',
            'asset': tag.meta_data,
            'method': self._execute_add_controller_tag
        })

        return tag

    def add_controller_tag_migration(
        self,
        tag_name: str
    ) -> None:
        """Specify a tag to migrate from source to destination.

        Args:
            tag_name (str): The name of the tag to migrate.
        """
        self._safe_register_action({
            'type': 'migrate_controller_tag',
            'name': tag_name,
            'method': self._execute_controller_tag_migration
        })

    def add_datatype_migration(
        self,
        datatype_name: str
    ) -> None:
        """Specify a datatype to migrate from source to destination.

        Args:
            datatype_name (str): The name of the datatype to migrate.
        """
        self._safe_register_action({
            'type': 'migrate_datatype',
            'name': datatype_name,
            'method': self._execute_datatype_migration
        })

    def add_program_tag(
        self,
        program_name: str,
        tag: Tag
    ) -> Tag:
        """Add a tag to import directly to the destination controller within a specific program.

        Args:
            program_name (str): The name of the program to add the tag to.
            tag (Tag): The tag to add.

        Raises:
            ValueError: If the provided tag is not an instance of the Tag class.
        """
        if not isinstance(tag, Tag):
            raise ValueError('Tag must be an instance of Tag class.')

        self._safe_register_action({
            'type': 'add_program_tag',
            'program': program_name,
            'asset': tag.meta_data,
            'method': self._execute_add_program_tag
        })

        return tag

    def add_routine(
        self,
        program_name: str,
        routine: Routine
    ) -> Routine:
        """Add a routine to import directly to the destination controller.

        Args:
            program_name (str): The name of the program to add the routine to.
            routine (Routine): The routine to add.

        Raises:
            ValueError: If the provided routine is not an instance of the Routine class.
        """
        if not isinstance(routine, Routine):
            raise ValueError('Routine must be an instance of Routine class.')

        self._safe_register_action({
            'type': 'add_routine',
            'program': program_name,
            'routine': routine.meta_data,
            'method': self._execute_add_routine
        })

        return routine

    def add_routine_migration(
        self,
        source_program_name: str,
        routine_name: str,
        destination_program_name: str = None,
        rung_updates: dict = None
    ) -> None:
        """Specify a routine to migrate, with optional rung updates.

        Args:
            source_program_name (str): The name of the program containing the routine from the source controller.
            routine_name (str): The name of the routine to migrate.
            destination_program_name (str, optional): The name of the program to add the routine to in the destination controller.
                                                        \n\tIf None, uses the same program name as the source.
            rung_updates (dict, optional): A dictionary of rung updates to apply during migration.
        """
        self._safe_register_action({
            'type': 'migrate_routine',
            'source_program': source_program_name,
            'routine': routine_name,
            'destination_program': destination_program_name or source_program_name,
            'rung_updates': rung_updates or {},
            'method': self._execute_routine_migration
        })

    def add_rung(
        self,
        program_name: str,
        routine_name: str,
        rung: Rung,
        rung_number: Optional[int] = None
    ) -> Rung:
        """Add a rung to import directly to the destination controller.

        Args:
            program_name (str): The name of the program containing the routine.
            routine_name (str): The name of the routine to add the rung to.
            new_rung (Rung): The rung to add.
            rung_number (Optional[int]): The index at which to insert the new rung. If None, appends to the end.

        Raises:
            ValueError: If the provided rung is not an instance of the Rung class.
        """
        if not isinstance(rung, Rung):
            raise ValueError('Rung must be an instance of Rung class.')

        self._safe_register_action({
            'type': 'add_rung',
            'program': program_name,
            'routine': routine_name,
            'rung_number': rung_number,
            'new_rung': rung.meta_data,
            'method': self._execute_add_rung
        })

        return rung

    def add_import_from_l5x_dict(
        self,
        l5x_dict: dict,
        asset_types: list[str] = plc_meta.L5X_ASSETS
    ) -> None:
        """
        Add actions to import assets from an L5X dictionary.

        Args:
            l5x_dict (dict): The L5X data as a dictionary.
            asset_types (list[str], optional): List of asset types to import, e.g. ['DataTypes', 'Tags', 'Programs'].
                                                \n\tDefaults to all if None.
        """

        self._safe_register_action({
            'type': 'import_from_l5x_dict',
            'l5x_dict': l5x_dict,
            'asset_types': asset_types,
            'method': self._execute_import_assets_from_l5x_dict
        })

    def add_import_from_file(
        self,
        file_location: str,
        asset_types: list[str] = plc_meta.L5X_ASSETS
    ) -> None:
        """
        Add actions to import assets from an L5X file.

        Args:
            file_location (str): The path to the L5X file.
            asset_types (list[str], optional): List of asset types to import, e.g. ['DataTypes', 'Tags', 'Programs'].
                                                \n\tDefaults to all if None.

        Raises:
            ValueError: If no valid L5X data is found in the specified file.
        """

        self._safe_register_action({
            'type': 'import_from_file',
            'file': file_location,
            'asset_types': asset_types,
            'method': self._execute_import_assets_from_file
        })

    def add_safety_tag_mapping(
        self,
        std_tag: str,
        sfty_tag: str
    ) -> None:
        """Add a mapping for tags from standard to safety code space.

        Args:
            std_tag (str): The standard tag name.
            sfty_tag (str): The safety tag name.

        Raises:
            ValueError: If either tag name is not a string.
        """
        if not isinstance(std_tag, str) or not isinstance(sfty_tag, str):
            raise ValueError('Source and destination tags must be strings.')
        self._safe_register_action({
            'type': 'safety_tag_mapping',
            'standard': std_tag,
            'safety': sfty_tag,
            'method': self._execute_add_safety_tag_mapping
        })

    def remove_controller_tag(
        self,
        tag_name: str
    ) -> None:
        """Specify a tag to remove from the destination controller.

        Args:
            tag_name (str): The name of the tag to remove.
        """
        self._safe_register_action({
            'type': 'remove_controller_tag',
            'name': tag_name,
            'method': self._execute_remove_controller_tag
        })

    def remove_datatype(
        self,
        datatype_name: str
    ) -> None:
        """Specify a datatype to remove from the destination controller.

        Args:
            datatype_name (str): The name of the datatype to remove.
        """
        self._safe_register_action({
            'type': 'remove_datatype',
            'name': datatype_name,
            'method': self._execute_remove_datatype
        })

    def remove_program_tag(
        self,
        program_name: str,
        tag_name: str
    ) -> None:
        """Specify a tag to remove from a specific program in the destination controller.

        Args:
            program_name (str): The name of the program containing the tag.
            tag_name (str): The name of the tag to remove.
        """
        self._safe_register_action({
            'type': 'remove_program_tag',
            'program': program_name,
            'name': tag_name,
            'method': self._execute_remove_program_tag
        })

    def remove_routine(
        self,
        program_name: str,
        routine_name: str
    ) -> None:
        """Specify a routine to remove from a specific program in the destination controller.

        Args:
            program_name (str): The name of the program containing the routine.
            routine_name (str): The name of the routine to remove.
        """
        self._safe_register_action({
            'type': 'remove_routine',
            'program': program_name,
            'name': routine_name,
            'method': self._execute_remove_routine
        })

    def remove_safety_tag_mapping(
        self,
        std_tag: str,
        sfty_tag: str
    ) -> None:
        """Specify a safety tag mapping to remove from the destination controller.

        Args:
            std_tag (str): The standard tag name.
            sfty_tag (str): The safety tag name.
        """
        self._safe_register_action({
            'type': 'remove_safety_tag_mapping',
            'standard': std_tag,
            'safety': sfty_tag,
            'method': self._execute_remove_safety_tag_mapping
        })

    def execute(self):
        """Perform all migration and import actions."""
        log(self).info('Executing controller modification schema...')

        if not self.destination:
            raise ValueError('Destination controller is not set.')

        # call all action's methods
        for action in self.actions:
            method = action.get('method')
            if callable(method):
                method(action)
            else:
                log(self).warning(f"No method defined for action type: {action['type']}. Skipping...")

        # Compile after all imports
        self.destination.compile()

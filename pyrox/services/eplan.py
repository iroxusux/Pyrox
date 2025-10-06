"""EPlan PDF parsing services for extracting electrical schematic information.

This module provides functionality to parse EPlan-generated PDF files containing
electrical schematics for Controls Automation Systems and extract device information,
power structures, network configurations, and I/O mappings.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
import os
from pyrox.services.env import get_env
from pyrox.services.file import get_open_file
from pyrox.services.logging import log
from pyrox.models.eplan import project as proj

if TYPE_CHECKING:
    from pyrox.models import plc


__all__ = (
    'get_project',
    'import_eplan',
)


PACKAGE_NAME_RE: str = r"(?:PACKAGE )(.*)(?:DESCRIPTION: )(.*)"
SECTION_LETTER_RE: str = r"(?:SECTION\nLETTER:\n)(.*)"
SHEET_NUMBER_RE: str = r"(?:SHEET\nNUMBER:\n)(.*) (.*)(?:\nOF)"


def _debug_get_project_save_file(project: proj.EplanProject) -> str:
    controller = project.controller
    name = controller.name if controller else 'unknown_controller'

    save_dir = get_env('EPLAN_DUMP_PROJECT_DIR', './artifacts')
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir, exist_ok=True)
    if not os.path.isdir(save_dir):
        raise NotADirectoryError(f'Could not create directory: {save_dir}')
    return save_dir + f'/{name}_eplan_project.json'


def _debug_export_project_dict(project: proj.EplanProject) -> None:
    if not get_env('EPLAN_DUMP_PROJECT_DICT', False, cast_type=bool):
        return
    project.save_project_dict_to_file(_debug_get_project_save_file(project))


def _get_validator(
    controller: plc.Controller,
    project: proj.EplanProject
) -> proj.EplanControllerValidator:
    validator: Optional[type[proj.EplanControllerValidator]
                        ] = proj.EplanControllerValidatorFactory.get_registered_type_by_supporting_class(controller)
    if not validator:
        validator = proj.EplanControllerValidatorFactory.get_registered_type_by_supporting_class('Controller')
    if not isinstance(validator, type(proj.EplanControllerValidator)):
        raise ValueError('No valid validator found for this controller type!')
    return validator(controller=controller, project=project)


def _work_precheck(
    controller: plc.Controller,
    project: proj.EplanProject,
    validator: proj.EplanControllerValidator,
) -> None:
    if not controller:
        raise ValueError('No controller provided for eplan import operation.')
    if not project:
        raise ValueError('No project provided for eplan import operation.')
    if not validator:
        raise ValueError('No validator provided for eplan import operation.')


def get_epj_file() -> str:
    return get_open_file(
        title='Select EPlan Project',
        filetypes=[('.epj Files', '*.epj'), ('All Files', '*.*')],
    )


def get_project(
    controller: plc.Controller,
    file_location: str
) -> proj.EplanProject:
    project = (proj.EplanProjectFactory.get_registered_type_by_supporting_class(controller)
               or proj.EplanProjectFactory.get_registered_type_by_supporting_class('Controller'))
    if not isinstance(project, type(proj.EplanProject)):
        raise ValueError('No valid project found for this controller type!')

    file_location = file_location or get_epj_file()
    if not file_location or not os.path.isfile(file_location):
        raise FileNotFoundError('No valid EPlan project file selected!')

    return project(file_location=file_location)


def import_eplan(
    controller: plc.Controller
) -> None:
    file_location = get_epj_file()
    if not file_location or not os.path.isfile(file_location):
        log(__name__).error('No valid EPlan project file selected!')
        return

    project: proj.EplanProject = get_project(controller, file_location)
    validator: proj.EplanControllerValidator = _get_validator(controller, project)
    _work_precheck(controller, project, validator)
    project.parse()
    _debug_export_project_dict(project)
    validator.validate()

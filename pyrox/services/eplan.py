"""EPlan PDF parsing services for extracting electrical schematic information.

This module provides functionality to parse EPlan-generated PDF files containing
electrical schematics for Controls Automation Systems and extract device information,
power structures, network configurations, and I/O mappings.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import os
from pyrox.models import eplan

if TYPE_CHECKING:
    from pyrox.models import plc

PACKAGE_NAME_RE: str = r"(?:PACKAGE )(.*)(?:DESCRIPTION: )(.*)"
SECTION_LETTER_RE: str = r"(?:SECTION\nLETTER:\n)(.*)"
SHEET_NUMBER_RE: str = r"(?:SHEET\nNUMBER:\n)(.*) (.*)(?:\nOF)"


def _get_epj_file() -> str:
    from .file import get_open_file
    return get_open_file(
        title='Select EPlan Project',
        filetypes=[('.epj Files', '*.epj'), ('All Files', '*.*')],
    )


def _get_project(
    controller: plc.Controller,
    file_location: str
) -> eplan.EplanProject:
    project: eplan.EplanProject = eplan.EplanProjectFactory.get_registered_type_by_supporting_class(controller)
    if not project:
        project = eplan.EplanProjectFactory.get_registered_type_by_supporting_class('Controller')
    if not isinstance(project, type(eplan.EplanProject)):
        raise ValueError('No valid project found for this controller type!')
    return project(file_location=file_location)


def _get_validator(
    controller: plc.Controller,
    project: eplan.EplanProject
) -> eplan.EplanControllerValidator:
    validator: eplan.EplanControllerValidator = eplan.EplanControllerValidatorFactory.get_registered_type_by_supporting_class(controller)
    if not validator:
        validator = eplan.EplanControllerValidatorFactory.get_registered_type_by_supporting_class('Controller')
    if not isinstance(validator, type(eplan.EplanControllerValidator)):
        raise ValueError('No valid validator found for this controller type!')
    return validator(controller=controller, project=project)


def _work_precheck(
    controller: plc.Controller,
    project: eplan.EplanProject,
    validator: eplan.EplanControllerValidator,
) -> None:
    if not controller:
        raise ValueError('No controller provided for eplan import operation.')
    if not project:
        raise ValueError('No project provided for eplan import operation.')
    if not validator:
        raise ValueError('No validator provided for eplan import operation.')


def import_eplan(
    controller: plc.Controller
) -> None:
    """Injects emulation routine the current controller.

    Args:
        controller (plc.Controller): The controller to inject the emulation routine into.
    """
    file_location = _get_epj_file()
    if not file_location or not os.path.isfile(file_location):
        raise FileNotFoundError('No valid EPlan project file selected!')

    project: eplan.EplanProject = _get_project(controller, file_location)
    validator: eplan.EplanControllerValidator = _get_validator(controller, project)
    _work_precheck(controller, project, validator)
    project.parse()
    validator.validate()

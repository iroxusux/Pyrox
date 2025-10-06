"""Pyrox emulation services module.
"""
import importlib
from pyrox.models.plc import controller
from pyrox.models.plc import generator as gen
from pyrox.services import checklist, eplan
from pyrox.services.file import get_save_file, save_file

__all__ = (
    'inject_emulation_routine',
    'remove_emulation_routine',
)


def _get_generator(
    controller: controller.Controller
) -> gen.EmulationGenerator:
    generator = gen.EmulationGeneratorFactory.get_registered_type_by_supporting_class(controller)
    if not isinstance(generator, type(gen.EmulationGenerator)):
        raise ValueError('No valid generator found for this controller type!')
    return generator(controller)


def _work_precheck(
    controller: controller.Controller,
    generator: gen.EmulationGenerator,
) -> None:
    if not controller:
        raise ValueError('No controller provided for emulation routine operation.')
    if not generator:
        raise ValueError('No generator provided for emulation routine operation.')


def create_checklist_from_template(
    ctrl: controller.Controller
) -> None:
    importlib.reload(eplan)
    importlib.reload(checklist)
    project_checklist = checklist.compile_checklist_from_eplan_project(
        project=eplan.get_project(ctrl, ''),
        template=checklist.get_controls_template()
    )
    if not project_checklist:
        raise ValueError('Could not compile checklist from EPlan project and template!')
    if not ctrl.file_location:
        file_location = get_save_file([('.md', 'Markdown Files')])
    else:
        file_location = ctrl.file_location.replace('.L5X', '_Emulation_Checklist.md')
    if not file_location:
        raise ValueError('No valid location to save checklist file selected!')

    save_file(file_location, project_checklist['raw_content'])


def inject_emulation_routine(
    ctrl: controller.Controller
) -> None:
    """Injects emulation routine the current controller.

    Args:
        controller (plc.Controller): The controller to inject the emulation routine into.
    """
    generator = _get_generator(ctrl)
    _work_precheck(ctrl, generator)
    generator.generate_emulation_logic()


def remove_emulation_routine(
    controller: controller.Controller
) -> None:
    """Removes emulation routine from the current controller.

    Args:
        controller (plc.Controller): The controller to remove the emulation routine from.
    """
    generator = _get_generator(controller)
    _work_precheck(controller, generator)
    generator.remove_emulation_logic()

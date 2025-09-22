"""Pyrox emulation services module.
"""
from pyrox.models.plc import plc
from pyrox.models import emu

__all__ = (
    'inject_emulation_routine',
    'remove_emulation_routine',
)


def _get_generator(
    controller: plc.Controller
) -> emu.EmulationGenerator:
    generator: emu.EmulationGenerator = emu.EmulationGeneratorFactory.get_registered_type_by_supporting_class(controller)
    if not isinstance(generator, type(emu.EmulationGenerator)):
        raise ValueError('No valid generator found for this controller type!')
    return generator(controller)


def _work_precheck(
    controller: plc.Controller,
    generator: emu.EmulationGenerator,
) -> None:
    if not controller:
        raise ValueError('No controller provided for emulation routine operation.')
    if not generator:
        raise ValueError('No generator provided for emulation routine operation.')


def inject_emulation_routine(
    controller: plc.Controller
) -> None:
    """Injects emulation routine the current controller.

    Args:
        controller (plc.Controller): The controller to inject the emulation routine into.
    """
    generator = _get_generator(controller)
    _work_precheck(controller, generator)
    generator.generate_emulation_logic()


def remove_emulation_routine(
    controller: plc.Controller
) -> None:
    """Removes emulation routine from the current controller.

    Args:
        controller (plc.Controller): The controller to remove the emulation routine from.
    """
    generator = _get_generator(controller)
    _work_precheck(controller, generator)
    generator.remove_emulation_logic()

"""Ford Controller Validator Class
"""
import importlib
from pyrox.applications.ford.ford import FordController
from pyrox.applications import validator as base_validator
from pyrox.models.plc.module import ModuleControlsType
from pyrox.services.logging import log

importlib.reload(base_validator)


class FordControllerValidator(base_validator.BaseControllerValidator):
    """Validator for Ford controllers.
    """
    supporting_class = FordController

    @classmethod
    def _validate_mapped_in_module(
        cls,
        controller,
        module
    ) -> bool:
        gsv_instruction = controller.find_instruction('GSV', module.name)
        if gsv_instruction is None:
            log(cls).error(f'Module {module.name} is missing GSV instruction.')
            return False

        module_tag = controller.tags.get(module.name, None)
        if module_tag is None:
            log(cls).error(f'Module {module.name} tag not found in controller tags.')
            return False

        cop_in_instruction = controller.find_instruction('COP', module.name + ':I')
        if cop_in_instruction is None:
            log(cls).error(f'Module {module.name} is missing COP instruction for input.')
            return False

        fll_in_instruction = controller.find_instruction('FLL', module.name + ':I')
        if fll_in_instruction is None:
            log(cls).error(f'Module {module.name} is missing FLL instruction for input.')
            return False

        return True

    @classmethod
    def _validate_module_io_block(
        cls,
        controller,
        module,
    ) -> bool:
        log(cls).info(f'Validating Ford IO Block: {module.name}')
        any_failures = False
        any_failures = any_failures or not cls._validate_mapped_in_module(controller, module)
        return not any_failures

    @classmethod
    def _validate_module_safety_block(
        cls,
        controller,
        module
    ) -> bool:
        log(cls).info(f'Validating Ford Safety Block: {module.name}')
        any_failures = False
        any_failures = any_failures or not cls._validate_mapped_in_module(controller, module)
        return not any_failures

    @classmethod
    def validate_module(
        cls,
        controller,
        module
    ) -> bool:
        any_failures = not super().validate_module(controller, module)
        match module.introspective_module.controls_type:
            case ModuleControlsType.BLOCK:
                return cls._validate_module_io_block(controller, module)
            case ModuleControlsType.SAFETY_BLOCK:
                return cls._validate_module_safety_block(controller, module)
            case _:
                log(cls).warning(
                    f'No specific validation implemented for module type: {module.introspective_module.controls_type}'
                )
                return not any_failures

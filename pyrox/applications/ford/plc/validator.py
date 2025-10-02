"""Ford Controller Validator Class
"""
import importlib
from pyrox.applications import ford
from pyrox.applications import validator as base_validator
from pyrox.models.plc.controller import Controller
from pyrox.models.plc.datatype import Datatype
from pyrox.models.plc.module import ModuleControlsType
from pyrox.services.logging import log

importlib.reload(ford)
importlib.reload(base_validator)


class FordControllerValidator(base_validator.BaseControllerValidator):
    """Validator for Ford controllers.
    """
    supporting_class = ford.FordController

    @classmethod
    def validate_datatype(
        cls,
        controller: Controller,
        datatype: Datatype
    ) -> bool:
        if datatype.name.lower().startswith('fud'):
            return True
        if datatype.name.lower().startswith('rac_'):
            return True
        if datatype.name.lower().startswith('raudt_'):
            return True
        any_failures = not super().validate_datatype(controller, datatype)
        return not any_failures

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
    def _validate_module_tag_exists(
        cls,
        controller,
        module
    ) -> bool:
        if module.name not in controller.tags:
            log(cls).error(f'Module {module.name} does not have a corresponding tag in the controller.')
            return False
        return True

    @classmethod
    def _validate_module_io_block(
        cls,
        controller,
        module,
    ) -> bool:
        if module.introspective_module.controls_type in [
            ModuleControlsType.INPUT_BLOCK,
            ModuleControlsType.OUTPUT_BLOCK,
            ModuleControlsType.INPUT_OUTPUT_BLOCK
        ]:
            return cls._validate_standard_io_block(controller, module)
        elif module.introspective_module.controls_type in [
            ModuleControlsType.SAFETY_INPUT_BLOCK,
            ModuleControlsType.SAFETY_OUTPUT_BLOCK,
            ModuleControlsType.SAFETY_INPUT_OUTPUT_BLOCK
        ]:
            return cls._validate_safety_io_block(controller, module)
        else:
            log(cls).warning(
                f'No specific IO block validation implemented for module type: {module.introspective_module.controls_type}'
            )
            return False

    @classmethod
    def _validate_standard_io_block(
        cls,
        controller,
        module
    ) -> bool:
        log(cls).info(f'Validating Ford Standard IO Block: {module.name}')
        any_failures = False
        any_failures |= not cls._validate_mapped_in_module(controller, module)
        any_failures |= not cls._validate_module_tag_exists(controller, module)
        return not any_failures

    @classmethod
    def _validate_safety_io_block(
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

        if module.introspective_module.controls_type in ModuleControlsType.all_block_types():
            return cls._validate_module_io_block(controller, module)

        # No specific validation found
        log(cls).warning(
            f'No specific validation implemented for module type: {module.introspective_module.controls_type}'
        )
        return not any_failures

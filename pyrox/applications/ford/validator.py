"""Ford Controller Validator Class
"""
from pyrox.applications.ford.ford import FordController
from pyrox.applications.validator import BaseControllerValidator
from pyrox.models.plc.module import ModuleControlsType
from pyrox.services.logging import log


class FordControllerValidator(BaseControllerValidator):
    """Validator for Ford controllers.
    """
    supporting_class = FordController

    @classmethod
    def _validate_module_io_block(
        cls,
        controller,
        module,
    ) -> bool:
        log(cls).info(f'Validating Ford IO Block: {module.name}')
        return True

    @classmethod
    def validate_module(
        cls,
        controller,
        module
    ) -> bool:
        any_failures = not super().validate_module(controller, module)
        log(cls).info(f'Validating Ford module: {module}')
        match module.introspective_module.controls_type:
            case ModuleControlsType.BLOCK:
                return cls._validate_module_io_block(controller, module)
            case _:
                log(cls).warning(
                    f'No specific validation implemented for module type: {module.introspective_module.controls_type}'
                )
                return not any_failures

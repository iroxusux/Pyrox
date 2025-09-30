"""Indicon default application package implimentations.
This package contains the default controller, validator, and emulation generator
for Indicon PLCs.
"""
from pyrox.models import eplan, plc
from pyrox.services.logging import log, LOG_LEVEL_FAILURE, LOG_LEVEL_SUCCESS


class BaseControllerValidator(plc.ControllerValidator):
    """Validator for controllers."""
    supporting_class = plc.Controller

    @classmethod
    def _check_comms_path(
        cls,
        controller: plc.Controller
    ) -> bool:
        """Check if the controller has a valid comms path.

        Args:
            controller: The controller to check.
        Returns:
            True if the controller has a valid comms path, False otherwise.
        """
        message = 'Comms path...'
        if controller.comm_path != '':
            message += f' ok... -> {str(controller.comm_path)}'
        else:
            message += ' error!'
        if 'error' in message:
            log(cls).log(LOG_LEVEL_FAILURE, message)
            return False
        else:
            log(cls).log(LOG_LEVEL_SUCCESS, message)
            return True

    @classmethod
    def _check_internal_plc_module(
        cls,
        controller: plc.Controller
    ) -> bool:
        """Check if the controller has a valid internal PLC module.

        Args:
            controller: The controller to check.
        Returns:
            True if the controller has a valid internal PLC module, False otherwise.
        """
        message = 'Internal PLC module...'
        if controller.plc_module is not None:
            message += f' ok... -> {str(controller.plc_module["@Name"])}'
        else:
            message += ' error!'
        if 'error' in message:
            log(cls).log(LOG_LEVEL_FAILURE, message)
            return False
        else:
            log(cls).log(LOG_LEVEL_SUCCESS, message)
            return True

    @classmethod
    def _check_slot(
        cls,
        controller: plc.Controller
    ) -> bool:
        """Check if the controller has a valid slot.

        Args:
            controller: The controller to check.
        Returns:
            True if the controller has a valid slot, False otherwise.
        """
        message = 'Slot...'
        if controller.slot is not None:
            message += f' ok... -> {str(controller.slot)}'
        else:
            message += ' error!'
        if 'error' in message:
            log(cls).log(LOG_LEVEL_FAILURE, message)
            return False
        else:
            log(cls).log(LOG_LEVEL_SUCCESS, message)
            return True

    @classmethod
    def validate_all(
        cls,
        controller: plc.Controller
    ) -> None:
        log(cls).info('Starting report...')
        cls.validate_properties(controller)
        cls.validate_modules(controller)
        cls.validate_datatypes(controller)
        cls.validate_aois(controller)
        cls.validate_tags(controller)
        cls.validate_programs(controller)

    @classmethod
    def validate_properties(
        cls,
        controller: plc.Controller
    ) -> None:
        log(cls).info('Validating controller properties...')

        cls._check_comms_path(controller)
        cls._check_slot(controller)
        cls._check_internal_plc_module(controller)

    @classmethod
    def validate_datatypes(
        cls,
        controller: plc.Controller
    ) -> None:
        log(cls).info('Validating datatypes...')

    @classmethod
    def validate_aois(
        cls,
        controller: plc.Controller
    ) -> None:
        log(cls).info('Validating add on instructions...')

    @classmethod
    def validate_module(
        cls,
        controller: plc.Controller,
        module: plc.Module
    ) -> None:
        if not module.name or module.name == '':
            log(cls).log(LOG_LEVEL_FAILURE, f'Module {module.name} has no name!')
        else:
            log(cls).info(f'Validating module {module.name}...')

        if not module.catalog_number or module.catalog_number == '':
            log(cls).log(LOG_LEVEL_FAILURE, f'Module {module.name} has no catalog number!')
        else:
            log(cls).log(LOG_LEVEL_SUCCESS, f'Module {module.name} catalog number: {module.catalog_number}')

        if not module.address or module.address == '':
            log(cls).log(LOG_LEVEL_FAILURE, f'Module {module.name} has no address!')
        else:
            log(cls).log(LOG_LEVEL_SUCCESS, f'Module {module.name} address: {module.address}')

        if not module.rpi or module.rpi == '':
            log(cls).log(LOG_LEVEL_FAILURE, f'Module {module.name} has no RPI!')
        else:
            log(cls).log(LOG_LEVEL_SUCCESS, f'Module {module.name} RPI: {module.rpi}')

        if not module.ekey or module.ekey == '':
            log(cls).log(LOG_LEVEL_FAILURE, f'Module {module.name} has no EKey!')
        else:
            state = module.ekey['@State']
            if not state or state == '':
                log(cls).log(LOG_LEVEL_FAILURE, f'Module {module.name} EKey has no state!')
            else:
                log(cls).log(LOG_LEVEL_SUCCESS, f'Module {module.name} EKey state: {state}')

    @classmethod
    def validate_modules(
        cls,
        controller: plc.Controller
    ) -> None:
        log(cls).info('Validating modules...')
        for module in controller.modules:
            cls.validate_module(controller, module)

    @classmethod
    def validate_tags(
        cls,
        controller: plc.Controller
    ) -> None:
        log(cls).info('Validating tags...')

    @classmethod
    def validate_programs(
        cls,
        controller: plc.Controller
    ) -> None:
        log(cls).info('Validating programs...')


class BaseEplanProject(eplan.project.EplanProject):
    """Base class for Eplan project generation logic."""
    supporting_class = plc.Controller


class BaseEplanValidator(eplan.project.EplanControllerValidator):
    """Base class for Eplan project validation logic."""
    supporting_class = plc.Controller

    def _find_missing_devices_in_project(self):
        self.log().info('Checking for missing devices in Eplan project...')
        all_devices = [d for d in self.project.devices]
        for device in self.project.devices:
            if not device:
                continue
            matching_device = self.find_matching_device_in_controller(device.name)
            if matching_device:
                all_devices.remove(device)
                continue

            almost_matching_device = self.find_almost_matching_device_in_controller(device.name)
            if almost_matching_device:
                self.log().warning(
                    f'Device {device.name} in Eplan project almost matches module {almost_matching_device.name} in controller.'
                    'Check for configuration differences.'
                )
                all_devices.remove(device)
                continue

            log(self).error(f'Device {device.name} in Eplan project is missing from controller.')

    def _find_missing_modules_in_controller(self):
        self.log().info('Checking for missing modules in controller...')
        all_modules = [m for m in self.controller.modules]
        for module in self.controller.modules:
            matching_device = self.find_matching_module_in_project(module)
            if matching_device:
                all_modules.remove(module)
                continue

            almost_matching_device = self.find_almost_matching_module_in_project(module)
            if almost_matching_device:
                self.log().warning(
                    f'Module {module.name} in controller almost matches device {almost_matching_device.name} in Eplan project.'
                    'Check for configuration differences.'
                )
                all_modules.remove(module)

                continue

            self.log().error(f'Module {module.name} in controller is missing from Eplan project.')

    def _find_missing_devices(self):
        if len(self.project.devices) > len(self.controller.modules):
            self._find_missing_devices_in_project()
        else:
            self._find_missing_modules_in_controller()

    def _validate_controller_properties(self):
        log(self).info('Validating controller properties...')

    def _validate_modules(self):
        log(self).info('Validating controller modules...')
        if len(self.project.devices) != len(self.controller.modules):
            self._find_missing_devices()

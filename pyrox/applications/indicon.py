"""Indicon default application package implimentations.
This package contains the default controller, validator, and emulation generator
for Indicon PLCs.
"""
from pyrox.models import eplan, plc
from pyrox.services.logging import log


class BaseControllerValidator(plc.ControllerValidator):
    """Validator for controllers."""
    supporting_class = plc.Controller


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

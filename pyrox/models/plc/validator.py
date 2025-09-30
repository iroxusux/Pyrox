"""Plc Controller Validator Abstract Base Class and Factory.
"""
from pyrox.models.abc.meta import PyroxObject
from pyrox.models.abc.factory import FactoryTypeMeta, MetaFactory
from pyrox.services.logging import log
from .controller import Controller


class ControllerValidatorFactory(MetaFactory):
    """Controller validator factory."""

    @staticmethod
    def get_validator(
        controller: Controller
    ) -> 'ControllerValidator':
        """Get a validator for the given controller.

        Args:
            controller: The controller to get a validator for.
        Returns:
            A ControllerValidator instance if a matching validator is found, None otherwise.
        """
        validator_cls = ControllerValidatorFactory.get_registered_type_by_supporting_class(controller)
        if validator_cls and issubclass(validator_cls, ControllerValidator):
            return validator_cls(controller)
        raise ValueError(f'No validator found for controller type {controller.__class__.__name__}.')


class ControllerValidator(
        PyroxObject,
        metaclass=FactoryTypeMeta['ControllerValidator', ControllerValidatorFactory]
):
    """Abstract base class for controller validation strategies."""

    supporting_class = Controller
    supports_registering = False  # This class can't be used to match anything

    def __init__(
        self,
        controller: Controller
    ) -> None:
        """Initialize the controller validator.

        Args:
            controller: The controller to validate.
        """
        self.controller = controller

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.supports_registering = True  # Subclasses can be used to match

    @property
    def controller(self) -> Controller:
        """The controller to validate."""
        return self._controller

    @controller.setter
    def controller(self, value: Controller) -> None:
        if not isinstance(value, Controller):
            raise TypeError("controller must be a Controller instance")
        self._controller = value

    @classmethod
    def _check_comms_path(
        cls,
        controller: Controller
    ) -> bool:
        """Check if the controller has a valid comms path.

        Args:
            controller: The controller to check.
        Returns:
            True if the controller has a valid comms path, False otherwise.
        """
        raise NotImplementedError("Subclass must implement abstract method")

    @classmethod
    def _check_internal_plc_module(
        cls,
        controller: Controller
    ) -> bool:
        """Check if the controller has a valid internal PLC module.

        Args:
            controller: The controller to check.
        Returns:
            True if the controller has a valid internal PLC module, False otherwise.
        """
        raise NotImplementedError("Subclass must implement abstract method")

    @classmethod
    def _check_slot(
        cls,
        controller: Controller
    ) -> bool:
        """Check if the controller has a valid slot.

        Args:
            controller: The controller to check.
        Returns:
            True if the controller has a valid slot, False otherwise.
        """
        raise NotImplementedError("Subclass must implement abstract method")

    @classmethod
    def get_factory(cls):
        return ControllerValidatorFactory

    @classmethod
    def validate_all(
        cls,
        controller: Controller
    ) -> None:
        raise NotImplementedError("Subclass must implement abstract method")

    @classmethod
    def validate_properties(
        cls,
        controller: Controller
    ) -> None:
        log(cls).info('Validating controller properties...')

        raise NotImplementedError("Subclass must implement abstract method")

    @classmethod
    def validate_datatypes(
        cls,
        controller: Controller
    ) -> None:
        raise NotImplementedError("Subclass must implement abstract method")

    @classmethod
    def validate_aois(
        cls,
        controller: Controller
    ) -> None:
        raise NotImplementedError("Subclass must implement abstract method")

    @classmethod
    def validate_modules(
        cls,
        controller: Controller
    ) -> None:
        raise NotImplementedError("Subclass must implement abstract method")

    @classmethod
    def validate_tags(
        cls,
        controller: Controller
    ) -> None:
        raise NotImplementedError("Subclass must implement abstract method")

    @classmethod
    def validate_programs(
        cls,
        controller: Controller
    ) -> None:
        raise NotImplementedError("Subclass must implement abstract method")

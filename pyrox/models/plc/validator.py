from typing import Self

from pyrox.models.abc.meta import PyroxObject
from pyrox.models.abc.factory import FactoryTypeMeta, MetaFactory
from pyrox.models.abc.list import HashList
from .meta import PlcObject
from .controller import Controller


class ControllerValidatorFactory(MetaFactory):
    """Controller validator factory."""


class ControllerValidator(PyroxObject, metaclass=FactoryTypeMeta[Self, ControllerValidatorFactory]):
    """Abstract base class for controller validation strategies."""

    supporting_class = 'Controller'
    supports_registering = False  # This class can't be used to match anything

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.supports_registering = True  # Subclasses can be used to match

    @classmethod
    def get_factory(cls):
        return ControllerValidatorFactory

    @classmethod
    def validate_all(
        cls,
        controller: Controller
    ) -> Self:
        cls.logger.info('Starting report...')
        cls.validate_properties(controller)
        cls.validate_modules(controller)
        cls.validate_datatypes(controller)
        cls.validate_aois(controller)
        cls.validate_tags(controller)
        cls.validate_programs(controller)
        return cls

    @classmethod
    def validate_properties(
        cls,
        controller: Controller
    ) -> Self:
        cls.logger.info('Validating controller properties...')

    @classmethod
    def validate_datatypes(
        cls,
        controller: Controller
    ) -> Self:
        cls.logger.info('Validating datatypes...')

    @classmethod
    def validate_aois(
        cls,
        controller: Controller
    ) -> Self:
        cls.logger.info('Validating add on instructions...')

    @classmethod
    def validate_modules(
        cls,
        controller: Controller
    ) -> Self:
        cls.logger.info('Validating modules...')

    @classmethod
    def validate_tags(
        cls,
        controller: Controller
    ) -> Self:
        cls.logger.info('Validating tags...')

    @classmethod
    def validate_programs(
        cls,
        controller: Controller
    ) -> Self:
        cls.logger.info('Validating programs...')


class ControllerReportItem:
    def __init__(self,
                 plc_object: PlcObject,
                 test_description: str,
                 pass_fail: bool = True,
                 test_notes: list[str] = None):
        if plc_object is None or test_description is None:
            raise ValueError('Cannot leave any fields empty/None!')
        self._plc_object: PlcObject = plc_object
        self._test_description: str = test_description
        self._pass_fail: bool = pass_fail
        self._test_notes: list[str] = test_notes if test_notes is not None else []
        self._child_reports: list['ControllerReportItem'] = []

    @property
    def child_reports(self) -> list['ControllerReportItem']:
        return self._child_reports

    @child_reports.setter
    def child_reports(self, value: list['ControllerReportItem']):
        if not isinstance(value, list):
            raise ValueError('Child reports must be a list!')
        self._child_reports = value

    @property
    def plc_object(self) -> PlcObject:
        return self._plc_object

    @property
    def test_description(self) -> str:
        return self._test_description

    @test_description.setter
    def test_description(self, value: str):
        if not isinstance(value, str):
            raise ValueError('Test description must be a string!')
        self._test_description = value

    @property
    def pass_fail(self) -> bool:
        return self._pass_fail

    @pass_fail.setter
    def pass_fail(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError('Pass/Fail must be a boolean value!')
        self._pass_fail = value

    @property
    def test_notes(self) -> list[str]:
        return self._test_notes

    @test_notes.setter
    def test_notes(self, value: list[str]):
        if not isinstance(value, list):
            raise ValueError('Test notes must be a list!')
        self._test_notes = value

    def as_dictionary(self) -> dict:
        """Get the report item as a dictionary.

        Returns
        -------
            :class:`dict`
        """
        name = str(self.plc_object.name) if hasattr(self.plc_object, 'name') else str(self.plc_object.meta_data)
        name += ' [%s]' % self.plc_object.__class__.__name__

        return {
            'Name': name,
            'PLC Object': self.plc_object.meta_data,
            'Test Description': self.test_description,
            'Pass?': self.pass_fail,
            'Test Notes': self.test_notes,
            'Child Reports': [x.as_dictionary() for x in self.child_reports]
        }


class ControllerReport(PyroxObject):
    """Controller status report

    Get detailed information about a controller, showing problem areas, etc.
    """

    @property
    def report_items(self) -> list[ControllerReportItem]:
        return self._report_items

    @property
    def categorized_items(self) -> dict[list[ControllerReportItem]]:
        return self._as_categorized()

    def _check_controller(self):
        self.log().info('Checking controller...')

        # comm path
        self.log().info('Comms path...')
        good = True if self._controller.comm_path != '' else False
        if good:
            self.log().info('ok... -> %s' % str(self._controller.comm_path))
        else:
            self.log().error('error!')

        # slot
        self.log().info('Slot...')
        good = True if self._controller.slot is not None else False
        if good:
            self.log().info('ok... -> %s' % str(self._controller.slot))
        else:
            self.log().error('error!')

        # plc module
        self.log().info('PLC Module...')
        good = True if self._controller.plc_module else False
        if good:
            self.log().info('ok... -> %s' % str(self._controller.plc_module['@Name']))
        else:
            self.log().error('error!')

    @classmethod
    def _check_common(
        cls,
        plc_objects: list[PlcObject]
    ) -> list[ControllerReportItem]:
        cls.logger.info(f'Checking {plc_objects.__class__.__name__} objects...')

        if not isinstance(plc_objects, list) and not isinstance(plc_objects, HashList):
            raise ValueError

        items = [plc_object.validate() for plc_object in plc_objects]

        return items

    @classmethod
    def check_controller_properties(
        cls,
        controller: Controller,
    ) -> ControllerReportItem:
        raise NotImplementedError("Subclass must implement abstract method")

    @classmethod
    def check_module_properties(
        cls,
        modules: list[PlcObject],
    ) -> list[ControllerReportItem]:
        raise NotImplementedError("Subclass must implement abstract method")

    @classmethod
    def check_datatype_properties(
        cls,
        datatypes: list[PlcObject],
    ) -> list[ControllerReportItem]:
        raise NotImplementedError("Subclass must implement abstract method")

    @classmethod
    def check_aois_properties(
        cls,
        aois: list[PlcObject],
    ) -> list[ControllerReportItem]:
        raise NotImplementedError("Subclass must implement abstract method")

    @classmethod
    def check_tag_properties(
        cls,
        tags: list[PlcObject],
    ) -> list[ControllerReportItem]:
        raise NotImplementedError("Subclass must implement abstract method")

    @classmethod
    def check_program_properties(
        cls,
        programs: list[PlcObject],
    ) -> list[ControllerReportItem]:
        raise NotImplementedError("Subclass must implement abstract method")

    @classmethod
    def validate_controller(
        cls,
        controller: Controller
    ) -> Self:
        cls.logger.info('Starting report...')
        cls.logger.info('Checking modules...')
        cls._check_common(controller.modules)
        cls.logger.info('Checking datatypes...')
        cls._check_common(controller.datatypes)
        cls.logger.info('Checking add on instructions...')
        cls._check_common(controller.aois)
        cls.logger.info('Checking tags...')
        cls._check_common(controller.tags)
        cls.logger.info('Checking programs...')
        cls._check_common(controller.programs)
        cls.logger.info('Finalizing report...')
        return cls

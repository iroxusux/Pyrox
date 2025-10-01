"""Base PLC Controller Validator
"""
from pyrox.models import plc
from pyrox.models.plc import validator as plc_validator
from pyrox.services.factory import reload_factory_module_while_preserving_registered_types
from pyrox.services.logging import log, LOG_LEVEL_FAILURE, LOG_LEVEL_SUCCESS

reload_factory_module_while_preserving_registered_types(plc_validator.ControllerValidatorFactory)
print(f'Registered Controller Validators: {list(plc_validator.ControllerValidatorFactory._registered_types.keys())}')


class BaseControllerValidator(plc_validator.ControllerValidator):
    """Validator for controllers.
    """
    supporting_class = plc.Controller

    @classmethod
    def _check_common_has_description(
        cls,
        controller: plc.Controller,
        common_plc_object: plc.NamedPlcObject
    ) -> bool:
        """Check if a common PLC object has a description.

        Args:
            controller: The controller to check.
            common_plc_object: The common PLC object to check.

        Returns:
            True if the common PLC object has a description, False otherwise.
        """
        if not common_plc_object.description or common_plc_object.description == '':
            log(cls).log(LOG_LEVEL_FAILURE, f'{common_plc_object.__class__.__name__} {common_plc_object.name} has no description!')
            return False
        return True

    @classmethod
    def _check_common_has_name(
        cls,
        controller: plc.Controller,
        common_plc_object: plc.NamedPlcObject
    ) -> bool:
        """Check if a common PLC object has a name.

        Args:
            controller: The controller to check.
            common_plc_object: The common PLC object to check.

        Returns:
            True if the common PLC object has a name, False otherwise.
        """
        if not common_plc_object.name or common_plc_object.name == '':
            log(cls).log(LOG_LEVEL_FAILURE, f'{common_plc_object.__class__.__name__} has no name!')
            return False
        return True

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
    def _check_datatype_member_has_valid_datatype(
        cls,
        controller: plc.Controller,
        datatype: plc.Datatype,
        member: plc.DatatypeMember
    ) -> None:
        """Check if a datatype member has a valid datatype.

        Args:
            controller: The controller to check.
            datatype: The datatype the member belongs to.
            member: The datatype member to check.
        """
        if not member.datatype or member.datatype == '':
            log(cls).log(LOG_LEVEL_FAILURE,
                         f'Datatype member {member.name} in datatype {datatype.name} has no datatype!')

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
    def _check_routine_has_jsr(
        cls,
        controller: plc.Controller,
        program: plc.Program,
        routine: plc.Routine
    ) -> None:
        """Check that a routine has at least one JSR call to itself (is not an uncalled routine).

        Args:
            controller: The controller to check.
            program: The program the routine is in.
            routine: The routine to check.
        """
        if program.main_routine_name == routine.name:
            return

        if not program.check_routine_has_jsr(routine):
            log(cls).log(LOG_LEVEL_FAILURE, f'Routine {routine.name} in program {program.name} has no JSR calls to it!')

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
    def validate_aoi(
        cls,
        controller: plc.Controller,
        aoi: plc.AddOnInstruction
    ) -> None:
        cls._check_common_has_name(controller, aoi)
        cls._check_common_has_description(controller, aoi)

    @classmethod
    def validate_aois(
        cls,
        controller: plc.Controller
    ) -> None:
        log(cls).info('Validating add on instructions...')
        for aoi in controller.aois:
            cls.validate_aoi(controller, aoi)

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
    def validate_datatype(
        cls,
        controller: plc.Controller,
        datatype: plc.Datatype
    ) -> None:
        cls._check_common_has_name(controller, datatype)
        cls._check_common_has_description(controller, datatype)
        cls.validate_datatype_members(controller, datatype)

    @classmethod
    def validate_datatype_member(
        cls,
        controller: plc.Controller,
        datatype: plc.Datatype,
        member: plc.DatatypeMember
    ) -> None:
        cls._check_common_has_name(controller, member)
        cls._check_datatype_member_has_valid_datatype(controller, datatype, member)

    @classmethod
    def validate_datatype_members(
        cls,
        controller: plc.Controller,
        datatype: plc.Datatype
    ) -> None:
        for member in datatype.members:
            cls.validate_datatype_member(controller, datatype, member)

    @classmethod
    def validate_datatypes(
        cls,
        controller: plc.Controller
    ) -> None:
        for datatype in controller.datatypes:
            cls.validate_datatype(controller, datatype)

    @classmethod
    def validate_module(
        cls,
        controller: plc.Controller,
        module: plc.Module
    ) -> bool:
        any_failures = False
        any_failures = any_failures or not (cls._check_common_has_name(controller, module))
        any_failures = any_failures or not (cls._check_common_has_description(controller, module))

        if not module.catalog_number or module.catalog_number == '':
            any_failures = True
            log(cls).log(LOG_LEVEL_FAILURE, f'Module {module.name} has no catalog number!')

        if not module.address or module.address == '':
            any_failures = True
            log(cls).log(LOG_LEVEL_FAILURE, f'Module {module.name} has no address!')

        if not module.rpi or module.rpi == '':
            if module.name != 'Local':
                any_failures = True
                log(cls).log(LOG_LEVEL_FAILURE, f'Module {module.name} has no RPI!')

        if not module.ekey or module.ekey == '':
            any_failures = True
            log(cls).log(LOG_LEVEL_FAILURE, f'Module {module.name} has no EKey!')

        return not any_failures

    @classmethod
    def validate_modules(
        cls,
        controller: plc.Controller
    ) -> None:
        log(cls).info('Validating modules...')
        for module in controller.modules:
            if not cls.validate_module(controller, module):
                log(cls).log(LOG_LEVEL_FAILURE, f'Module validation failed! -> {module.name}')
            else:
                log(cls).log(LOG_LEVEL_SUCCESS, f'Module validation passed! -> {module.name}')

    @classmethod
    def validate_program(
        cls,
        controller: plc.Controller,
        program: plc.Program
    ) -> None:
        cls._check_common_has_name(controller, program)
        cls._check_common_has_description(controller, program)
        cls.validate_routines(controller, program)

    @classmethod
    def validate_programs(
        cls,
        controller: plc.Controller
    ) -> None:
        log(cls).info('Validating programs...')
        for program in controller.programs:
            cls.validate_program(controller, program)

    @classmethod
    def validate_routine(
        cls,
        controller: plc.Controller,
        program: plc.Program,
        routine: plc.Routine
    ) -> None:
        cls._check_common_has_name(controller, routine)
        cls._check_common_has_description(controller, routine)
        cls._check_routine_has_jsr(controller, program, routine)
        cls.validate_rungs(controller, program, routine)

    @classmethod
    def validate_routines(
        cls,
        controller: plc.Controller,
        program: plc.Program
    ) -> None:
        for routine in program.routines:
            cls.validate_routine(controller, program, routine)

    @classmethod
    def validate_rung(
        cls,
        controller: plc.Controller,
        program: plc.Program,
        routine: plc.Routine,
        rung: plc.Rung
    ) -> None:

        if not rung.number or rung.number == '':
            log(cls).log(LOG_LEVEL_FAILURE, f'Rung in routine {routine.name} in program {program.name} has no number!')

        if not rung.text or rung.text == '':
            log(cls).log(LOG_LEVEL_FAILURE, f'Rung {rung.number} in routine {routine.name} in program {program.name} has no text!')

    @classmethod
    def validate_rungs(
        cls,
        controller: plc.Controller,
        program: plc.Program,
        routine: plc.Routine
    ) -> None:
        for rung in routine.rungs:
            cls.validate_rung(controller, program, routine, rung)

    @classmethod
    def validate_tag(
        cls,
        controller: plc.Controller,
        tag: plc.Tag
    ) -> None:
        cls._check_common_has_name(controller, tag)
        cls._check_common_has_description(controller, tag)

        if not tag.datatype or tag.datatype == '':
            log(cls).log(LOG_LEVEL_FAILURE, f'Tag {tag.name} has no datatype!')

    @classmethod
    def validate_tags(
        cls,
        controller: plc.Controller
    ) -> None:
        log(cls).info('Validating tags...')
        for tag in controller.tags:
            cls.validate_tag(controller, tag)

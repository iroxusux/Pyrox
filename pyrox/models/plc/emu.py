"""Base emulation logic factory for PLC controllers."""
from abc import ABC, ABCMeta, abstractmethod
from typing import Dict, List, Optional, Type

from .. import abc, plc


class EmulationGeneratorMeta(ABCMeta):
    """Metaclass for emulation generator registration."""

    _generators: Dict[str, Type['BaseEmulationGenerator']] = {}

    def __new__(cls, name, bases, attrs, **kwargs):
        new_cls = super().__new__(cls, name, bases, attrs)

        # Register generator classes (skip the base class)
        if name != 'BaseEmulationGenerator' and hasattr(new_cls, 'controller_type'):
            cls._generators[new_cls.controller_type] = new_cls

        return new_cls

    @classmethod
    def get_generator(cls, controller_type: str) -> Optional[Type['BaseEmulationGenerator']]:
        """Get a registered generator for a controller type."""
        return cls._generators.get(controller_type)

    @classmethod
    def list_generators(cls) -> List[str]:
        """List all registered controller types."""
        return list(cls._generators.keys())


class BaseEmulationGenerator(abc.Loggable, ABC, metaclass=EmulationGeneratorMeta):
    """Base class for emulation logic generators."""

    controller_type: str = None  # Override in subclasses

    def __init__(self, controller: plc.Controller):
        super().__init__(name=f"{self.__class__.__name__}")
        self.controller = controller
        self.schema = plc.ControllerModificationSchema(
            source=None,
            destination=controller
        )

    @abstractmethod
    def generate_base_emulation(self) -> None:
        """Generate the base emulation logic common to all controllers."""
        pass

    @abstractmethod
    def generate_module_emulation(self) -> None:
        """Generate module-specific emulation logic."""
        pass

    @abstractmethod
    def remove_base_emulation(self) -> None:
        """Remove the base emulation logic common to all controllers."""
        pass

    @abstractmethod
    def remove_module_emulation(self) -> None:
        """Remove module-specific emulation logic."""
        pass

    @abstractmethod
    def validate_controller(self) -> bool:
        """Validate that the controller is compatible with this generator.

        Returns:
            bool: True if controller is valid for this generator type.

        Raises:
            ValueError: If controller validation fails.
        """
        pass

    def generate_custom_logic(self) -> None:
        """Generate custom emulation logic. Override in subclasses if needed."""
        pass

    def generate_emulation_logic(self) -> plc.ControllerModificationSchema:
        """Main entry point to generate emulation logic.

        Returns:
            ControllerModificationSchema: The modification schema with all changes.
        """
        self.logger.info(f"Starting emulation generation for {self.controller.name}")

        # Validate controller
        if not self.validate_controller():
            raise ValueError(f"Controller {self.controller.name} is not valid for {self.controller_type} emulation")

        # Generate emulation logic
        self.generate_base_emulation()
        self.generate_module_emulation()
        self.generate_custom_logic()

        # Execute the schema
        self.schema.execute()

        self.logger.info(f"Emulation generation completed for {self.controller.name}")
        return self.schema

    def remove_emulation_logic(self) -> plc.ControllerModificationSchema:
        """Remove previously added emulation logic.

        Returns:
            ControllerModificationSchema: The modification schema with all removals.
        """
        self.logger.info(f"Starting emulation removal for {self.controller.name}")

        # Remove emulation logic
        self.remove_base_emulation()
        self.remove_module_emulation()
        self.remove_custom_logic()

        # Execute the schema to remove added elements
        self.schema.execute()

        self.logger.info(f"Emulation removal completed for {self.controller.name}")
        return self.schema

    def add_emulation_routine(self,
                              program_name: str,
                              routine_name: str,
                              routine_description: str,
                              call_from_main: bool = True,
                              rung_position: int = -1) -> plc.Routine:
        """Helper method to add an emulation routine to a program.

        Args:
            program_name: Name of the program to add routine to
            routine_name: Name of the new routine
            routine_description: Description for the routine
            call_from_main: Whether to add JSR call from main routine
            rung_position: Position to insert JSR call (-1 for end)

        Returns:
            Routine: The created routine
        """
        self.logger.debug(f"Adding emulation routine '{routine_name}' to program '{program_name}'")

        # Create the routine
        routine = self.controller.config.routine_type(controller=self.controller)
        routine.name = routine_name
        routine.description = routine_description
        routine.clear_rungs()

        # Add routine to program
        self.schema.add_routine(
            program_name=program_name,
            routine=routine
        )

        # Add JSR call if requested
        if call_from_main:
            program = self.controller.programs.get(program_name)
            if program and program.main_routine:
                if program.main_routine.check_for_jsr(routine_name):
                    self.logger.debug(f"JSR to '{routine_name}' already exists in main routine of program '{program_name}'")
                else:
                    self.logger.debug(f"Adding JSR call to '{routine_name}' in main routine of program '{program_name}'")
                    jsr_rung = plc.Rung(
                        controller=self.controller,
                        text=f'JSR({routine_name},0);',
                        comment=f'Call the {routine_name} routine.'
                    )
                    self.schema.add_rung(
                        program_name=program_name,
                        routine_name=program.main_routine_name,
                        rung_number=rung_position,
                        new_rung=jsr_rung
                    )

        return routine

    def add_program_tag(
        self,
        program_name: str,
        tag_name: str,
        datatype: str,
        **kwargs
    ) -> plc.Tag:
        """Helper method to add a tag to a program.

        Args:
            program_name: Name of the program
            tag_name: Name of the tag
            datatype: Datatype of the tag
            **kwargs: Additional tag properties

        Returns:
            Tag: The created tag
        """
        self.logger.debug(f"Adding program tag: {tag_name} with datatype {datatype} to program {program_name}")

        tag = plc.Tag(
            controller=self.controller,
            name=tag_name,
            datatype=datatype,
            **kwargs
        )

        self.schema.add_program_tag(
            program_name=program_name,
            tag=tag
        )

        return tag

    def add_controller_tag(
        self,
        tag_name: str,
        datatype: str,
        description: str = "",
        **kwargs
    ) -> plc.Tag:
        """Helper method to add a controller-scoped tag.

        Args:
            tag_name: Name of the tag
            datatype: Datatype of the tag
            **kwargs: Additional tag properties

        Returns:
            Tag: The created tag
        """
        self.logger.debug(f"Adding controller tag: {tag_name} with datatype {datatype}")

        tag = self.controller.config.tag_type(
            controller=self.controller,
            name=tag_name,
            datatype=datatype,
            description=description,
            **kwargs
        )

        self.schema.add_controller_tag(tag)
        return tag

    def get_modules_by_type(self, module_type: str) -> List[plc.Module]:
        """Get all modules of a specific type.

        Args:
            module_type: The module type to filter by

        Returns:
            List[Module]: List of matching modules
        """
        self.logger.debug(f"Retrieving modules of type: {module_type}")

        return [module for module in self.controller.modules if module.type_ == module_type]

    def get_modules_by_description_pattern(self, pattern: str) -> List[plc.Module]:
        """Get modules matching a description pattern.

        Args:
            pattern: Pattern to match in module description

        Returns:
            List[Module]: List of matching modules
        """
        self.logger.debug(f"Retrieving modules with description pattern: {pattern}")

        return [module for module in self.controller.modules
                if module.description and pattern in module.description]

    def remove_custom_logic(self) -> None:
        """Remove custom emulation logic."""
        pass

    def remove_controller_tag(
        self,
        tag_name: str
    ) -> None:
        """Helper method to remove a controller-scoped tag.

        Args:
            tag_name: Name of the tag to remove
        """
        self.logger.debug(f"Removing controller tag '{tag_name}'")

        self.schema.remove_controller_tag(
            tag_name=tag_name
        )

    def remove_datatype(
        self,
        datatype_name: str
    ) -> None:
        """Helper method to remove a datatype from the controller.

        Args:
            datatype_name: Name of the datatype to remove
        """
        self.logger.debug(f"Removing datatype '{datatype_name}' from controller")

        self.schema.remove_datatype(
            datatype_name=datatype_name
        )

    def remove_program_tag(
        self,
        program_name: str,
        tag_name: str
    ) -> None:
        """Helper method to remove a tag from a program.

        Args:
            program_name: Name of the program
            tag_name: Name of the tag to remove
        """
        self.logger.debug(f"Removing tag '{tag_name}' from program '{program_name}'")

        self.schema.remove_program_tag(
            program_name=program_name,
            tag_name=tag_name
        )

    def remove_routine(
            self,
            program_name: str,
            routine_name: str
    ) -> None:
        """Helper method to remove a routine from the controller.

        Args:
            program_name: Name of the program containing the routine
            routine_name: Name of the routine to remove
        """
        self.logger.debug(f"Removing routine '{routine_name}' from controller")

        self.schema.remove_routine(
            program_name,
            routine_name
        )


class EmulationFactory:
    """Factory class for creating emulation generators."""

    @staticmethod
    def create_generator(controller: plc.Controller) -> BaseEmulationGenerator:
        """Create an appropriate emulation generator for a controller.

        Args:
            controller: The controller to generate emulation for

        Returns:
            BaseEmulationGenerator: The appropriate generator instance

        Raises:
            ValueError: If no suitable generator is found
        """
        # Try to determine controller type from controller class
        controller_type = controller.__class__.__name__

        # Look for a registered generator
        generator_class = EmulationGeneratorMeta.get_generator(controller_type)

        if generator_class:
            return generator_class(controller)

        # Fallback to base generator if no specific one found
        if hasattr(controller, 'controller_type'):
            generator_class = EmulationGeneratorMeta.get_generator(controller.controller_type)
            if generator_class:
                return generator_class(controller)

        raise ValueError(f"No emulation generator found for controller type: {controller_type}")

    @staticmethod
    def list_supported_types() -> List[str]:
        """List all supported controller types.

        Returns:
            List[str]: List of supported controller type names
        """
        return EmulationGeneratorMeta.list_generators()

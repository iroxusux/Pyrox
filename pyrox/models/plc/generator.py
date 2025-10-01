"""Emulation Generator module for pyrox applications.
"""
from typing import Optional, List

from . import controller, imodule, module, routine, rung, tag
from ..abc import meta, factory


class EmulationGeneratorFactory(factory.MetaFactory):
    """Factory for creating EmulationGenerator instances."""


class EmulationGenerator(
    meta.PyroxObject,
    metaclass=factory.FactoryTypeMeta[
        'EmulationGenerator',
        EmulationGeneratorFactory
    ]
):
    """Base class for emulation logic generators."""
    supporting_class: Optional[type] = None
    supports_registering: bool = False

    def __init__(
        self,
        ctrl: controller.Controller
    ) -> None:
        super().__init__()
        self.generator_object = ctrl
        self.schema = controller.ControllerModificationSchema(
            source=None,
            destination=self.generator_object
        )
        self._emulation_standard_routine = None
        self._emulation_safety_routine = None

    def __init_subclass__(cls, **kwargs):
        cls.supports_registering = True
        return super().__init_subclass__(**kwargs)

    @property
    def base_tags(self) -> list[tuple[str, str, str]]:
        """List of base tags common to all controllers.

        Returns:
            list[tuple[str, str, str]]: List of tuples (tag_name, datatype, description)
        """
        raise NotImplementedError("Subclasses must implement base_tags")

    @property
    def custom_tags(self) -> list[tuple[str, str, str, Optional[str]]]:
        """List of custom tags specific to the controller type.

        Returns:
            list[str]: List of tuples (tag_name, datatype, description, dimensions).
        """
        raise NotImplementedError("Subclasses must implement custom_tags")

    @property
    def emulation_safety_routine(self) -> Optional[routine.Routine]:
        """The safety emulation routine, if created.

        Returns:
            Optional[Routine]: The safety emulation routine or None
        """
        return self._emulation_safety_routine

    @emulation_safety_routine.setter
    def emulation_safety_routine(self, value: Optional[routine.Routine]):
        if value and not isinstance(value, controller.Routine):
            raise TypeError(f'Emulation safety routine must be of type Routine, got {type(value)} instead.')
        self._emulation_safety_routine = value

    @property
    def emulation_safety_routine_description(self) -> str:
        """Description for the safety routine to add emulation logic to.

        Returns:
            str: Description of the safety routine
        """
        return self.emulation_standard_routine_description

    @property
    def emulation_safety_routine_name(self) -> str:
        """Name of the safety routine to add emulation logic to.

        Returns:
            str: Name of the safety routine
        """
        raise NotImplementedError("Subclasses must implement emulation_safety_routine_name")

    @property
    def emulation_standard_routine(self) -> Optional[routine.Routine]:
        """The standard emulation routine, if created.

        Returns:
            Optional[Routine]: The standard emulation routine or None
        """
        return self._emulation_standard_routine

    @emulation_standard_routine.setter
    def emulation_standard_routine(self, value: Optional[routine.Routine]):
        if value and not isinstance(value, controller.Routine):
            raise TypeError(f'Emulation standard routine must be of type Routine, got {type(value)} instead.')
        self._emulation_standard_routine = value

    @property
    def emulation_standard_routine_description(self) -> str:
        """Description for the standard routine to add emulation logic to.

        Returns:
            str: Description of the standard routine
        """
        raise NotImplementedError("Subclasses must implement emulation_standard_routine_description")

    @property
    def emulation_standard_routine_name(self) -> str:
        """Name of the standard routine to add emulation logic to.

        Returns:
            str: Name of the standard routine
        """
        raise NotImplementedError("Subclasses must implement emulation_standard_routine_name")

    @property
    def generator_object(self) -> controller.Controller:
        return self._generator_object

    @generator_object.setter
    def generator_object(self, value: controller.Controller):
        if self.supporting_class is not None and not isinstance(value, self.supporting_class):
            raise TypeError(f'Controller must be of type {self.supporting_class}, got {type(value)} instead.')
        self._generator_object = value

    @property
    def inhibit_tag(self) -> str:
        """Name of the inhibit tag.

        Returns:
            str: Name of the inhibit tag
        """
        return self.base_tags[1][0]  # Inhibit tag name

    @property
    def local_mode_tag(self) -> str:
        """Name of the local mode tag.

        Returns:
            str: Name of the local mode tag
        """
        return self.base_tags[3][0]  # LocalMode tag name

    @property
    def target_safety_program_name(self) -> str:
        """Name of the safety program to add emulation logic to.

        Returns:
            str: Name of the safety program
        """
        raise NotImplementedError("Subclasses must implement target_safety_program_name")

    @property
    def target_standard_program_name(self) -> str:
        """Name of the standard program to add emulation logic to.

        Returns:
            str: Name of the standard program
        """
        raise NotImplementedError("Subclasses must implement target_standard_program_name")

    @property
    def test_mode_tag(self) -> str:
        """Name of the test mode tag.

        Returns:
            str: Name of the test mode tag
        """
        raise NotImplementedError("Subclasses must implement test_mode_tag")

    @property
    def toggle_inhibit_tag(self) -> str:
        """Name of the toggle inhibit tag.

        Returns:
            str: Name of the toggle inhibit tag
        """
        return self.base_tags[2][0]  # ToggleInhibit tag name

    @property
    def uninhibit_tag(self) -> str:
        """Name of the uninhibit tag.

        Returns:
            str: Name of the uninhibit tag
        """
        return self.base_tags[0][0]  # Uninhibit tag name

    @classmethod
    def get_factory(cls):
        return EmulationGeneratorFactory

    def _add_rung_common(
        self,
        rung: controller.Rung,
        program_name: str,
        routine_name: str
    ) -> None:
        """Helper to add a rung to a specified routine.

        Args:
            rung: The rung to add
            program_name: Name of the program
            routine_name: Name of the routine
        """
        self.schema.add_rung(
            program_name=program_name,
            routine_name=routine_name,
            rung=rung
        )

    def _generate_base_emulation(self) -> None:
        """Generate the base emulation logic common to all controllers."""
        self._generate_base_tags()
        self._generate_custom_tags()

        self._generate_base_standard_routine()
        self._generate_base_standard_rungs()

        self._generate_base_safety_routine()
        self._generate_base_safety_rungs()

        self._generate_base_module_emulation()

        self._generate_custom_standard_routines()
        self._generate_custom_standard_rungs()
        self._generate_custom_safety_routines()
        self._generate_custom_safety_rungs()

    def _generate_base_module_emulation(self) -> None:
        """Generate base module emulation logic common to all controllers."""
        self.log().info("Generating base module emulation...")
        for controller_type in module.ModuleControlsType:
            self._generate_builtin_common(controller_type)

    def _generate_base_safety_routine(self) -> None:
        """Generate a safety routine common to all controllers."""
        self.log().debug("Generating base safety routine...")
        self.emulation_safety_routine = self.add_routine(
            program_name=self.target_safety_program_name,
            routine_name=self.emulation_safety_routine_name,
            routine_description=self.emulation_safety_routine_description,
            call_from_main=True,
            rung_position=0
        )

    def _generate_base_safety_rungs(self) -> None:
        """Generate base rungs in the safety emulation routine."""
        self.log().info("Generating base safety rungs...")
        if not self.emulation_safety_routine:
            raise ValueError("Safety emulation routine has not been created yet.")

        self.emulation_safety_routine.clear_rungs()
        self.add_rung_to_safety_routine(
            controller.Rung(
                controller=self.generator_object,
                text='NOP();',
                comment='// Emulation Safety Logic Routine\n// Auto-generated by Indicon LLC\n// Do not modify.'
            ))

    def _generate_base_standard_routine(self) -> None:
        """Generate a standard base routine common to all controllers."""
        self.log().info("Generating base standard routine...")
        self.emulation_standard_routine = self.add_routine(
            program_name=self.target_standard_program_name,
            routine_name=self.emulation_standard_routine_name,
            routine_description=self.emulation_standard_routine_description,
            call_from_main=True,
            rung_position=0
        )

    def _generate_base_standard_rungs(self) -> None:
        """Generate base rungs in the standard emulation routine."""
        self.log().info("Generating base standard rungs...")
        if not self.emulation_standard_routine:
            raise ValueError("Emulation routine has not been created yet.")

        self.emulation_standard_routine.clear_rungs()
        self.add_rung_to_standard_routine(
            controller.Rung(
                text='NOP();',
                comment='// Emulation Logic Routine\n// Auto-generated by Indicon LLC\n// Do not modify.'
            ))

        # Setup Rung
        branch1 = f'XIC(S:FS)OTL({self.toggle_inhibit_tag})OTL({self.test_mode_tag})'
        branch2 = f'MOV(0,{self.uninhibit_tag})MOV(4,{self.inhibit_tag})'
        self.add_rung_to_standard_routine(
            controller.Rung(
                text=f'[{branch1},{branch2}];',
                comment='// This routine is auto-generated by Indicon LLC.\n// Do not modify.'
            ))

        # Inhibit Logic Rung
        branch1 = f'XIO({self.toggle_inhibit_tag})MOV({self.uninhibit_tag},{self.local_mode_tag})'
        branch2 = f'XIC({self.toggle_inhibit_tag})MOV({self.inhibit_tag},{self.local_mode_tag})'
        self.add_rung_to_standard_routine(
            controller.Rung(
                controller=self.generator_object,
                text=f'[{branch1},{branch2}];',
                comment='// Handle toggle inhibit.'
            ))

        self._generate_module_inhibit_rungs()

    def _generate_base_tags(self) -> None:
        """Generate base tags common to all controllers."""
        self.log().info("Generating base tags...")
        for tag_name, datatype, description in self.base_tags:
            self.add_controller_tag(tag_name, datatype, description=description)

    def _generate_builtin_common(
        self,
        generation_type: module.ModuleControlsType
    ) -> None:
        modules: list[imodule.IntrospectiveModule] = imodule.ModuleWarehouseFactory.filter_modules_by_type(
            self.generator_object.modules,
            generation_type
        )

        self.log().info("Generating built-in common emulation for %d modules of type %s...", len(modules), generation_type.value)

        for _, value in enumerate(modules):
            if not value:
                self.log().warning("Module has no introspective_module, skipping...")
                continue
            if not value.module:
                self.log().warning("IntrospectiveModule has no associated module, skipping...")
                continue
            self.log().info("Generating emulation for %s %s of class %s", generation_type.value, value.module.name, value.__class__.__name__)
            self.add_l5x_imports(value.get_required_imports())
            self.add_controller_tags(value.get_required_tags())
            self.add_safety_tag_mapping(*value.get_required_standard_to_safety_mapping())
            self.add_rungs(
                self.target_standard_program_name,
                self.emulation_standard_routine_name,
                value.get_required_standard_rungs()
            )
            self.add_rungs(
                self.target_safety_program_name,
                self.emulation_safety_routine_name,
                value.get_required_safety_rungs()
            )

    def _generate_custom_logic(self) -> None:
        """Generate custom emulation logic. Override in subclasses if needed."""
        pass

    def _generate_custom_module_emulation(self) -> None:
        """Generate module-specific emulation logic."""
        pass

    def _generate_custom_safety_routines(self) -> None:
        """Generate custom safety routines. Override in subclasses if needed."""
        pass

    def _generate_custom_safety_rungs(self) -> None:
        """Generate custom safety rungs. Override in subclasses if needed."""
        pass

    def _generate_custom_standard_routines(self) -> None:
        """Generate custom standard routines. Override in subclasses if needed."""
        pass

    def _generate_custom_standard_rungs(self) -> None:
        """Generate custom standard rungs. Override in subclasses if needed."""
        pass

    def _generate_custom_tags(self) -> None:
        """Generate custom tags. Override in subclasses if needed."""
        self.log().info("Generating custom tags...")
        for tag_name, datatype, description, dimensions in self.custom_tags:
            self.add_controller_tag(tag_name, datatype, description=description, dimensions=dimensions)

    def _generate_module_inhibit_rungs(self) -> None:
        """Generate inhibit logic for modules."""
        if not self.emulation_standard_routine:
            raise ValueError("Emulation routine has not been created yet.")

        if not self.generator_object.config:
            raise ValueError("Controller configuration is not set.")

        self.log().info("Generating module inhibit rungs...")

        for mod in self.generator_object.modules:
            if mod.name == 'Local':
                continue
            self.add_rung_to_standard_routine(
                self.generator_object.config.rung_type(
                    controller=self.generator_object,
                    text=f'SSV(Module,{mod.name},Mode,{self.local_mode_tag});',
                    comment=f'// Inhibit logic for module {mod.name}'
                ))

    def add_l5x_imports(
        self,
        imports: List[tuple[str, List[str]]]
    ) -> None:
        """Helper to schedule imports in the modification schema.

        Args:
            imports: List of tuples (file_location, [asset_types])
        """
        for file_location, asset_types in imports:
            self.log().debug(f"Scheduling import of {asset_types} from {file_location}")
            self.schema.add_import_from_file(
                file_location=file_location,
                asset_types=asset_types
            )

    def add_program_tag(
        self,
        program_name: str,
        tag_name: str,
        datatype: str,
        **kwargs
    ) -> controller.Tag:
        """Helper method to add a tag to a program.

        Args:
            program_name: Name of the program
            tag_name: Name of the tag
            datatype: Datatype of the tag
            **kwargs: Additional tag properties

        Returns:
            Tag: The created tag
        """
        self.log().debug(f"Adding program tag: {tag_name} with datatype {datatype} to program {program_name}")
        return self.schema.add_program_tag(
            program_name=program_name,
            tag=tag.Tag(
                controller=self.generator_object,
                name=tag_name,
                datatype=datatype,
                **kwargs
            ))

    def add_controller_tag(
        self,
        tag_name: str,
        datatype: str,
        description: str = "",
        constant: bool = False,
        external_access: str = "Read/Write",
        tag_type: str = 'Base',
        **kwargs
    ) -> controller.Tag:
        """Helper method to add a controller-scoped tag.

        Args:
            tag_name: Name of the tag
            datatype: Datatype of the tag
            **kwargs: Additional tag properties

        Returns:
            Tag: The created tag
        """
        self.log().debug(f"Scheduling controller tag: {tag_name} with datatype {datatype}.")
        return self.schema.add_controller_tag(
            tag.Tag(
                controller=self.generator_object,
                name=tag_name,
                datatype=datatype,
                description=description,
                constant=constant,
                external_access=external_access,
                tag_type=tag_type,
                **kwargs
            ))

    def add_controller_tags(
        self,
        tags: List[dict]
    ) -> None:
        """Helper method to add multiple controller-scoped tags.

        Args:
            tags: List of tag dictionaries with keys matching Tag properties
        """
        for tag_info in tags:
            self.add_controller_tag(**tag_info)

    def add_routine(
        self,
        program_name: str,
        routine_name: str,
        routine_description: str,
        call_from_main: bool = True,
        rung_position: int = -1
    ) -> routine.Routine:
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
        self.log().debug(f"Adding emulation routine '{routine_name}' to program '{program_name}' to schema.")
        if not self.generator_object.config:
            raise ValueError("Controller configuration is not set.")

        # Create the routine
        rout: routine.Routine = self.generator_object.config.routine_type(controller=self.generator_object)
        rout.name = routine_name
        rout.description = routine_description
        rout.clear_rungs()

        # Add routine to program
        self.schema.add_routine(
            program_name=program_name,
            routine=rout
        )

        # Add JSR call if requested
        if call_from_main:
            program: Optional[controller.Program] = self.generator_object.programs.get(program_name)
            if program and program.main_routine:
                if program.main_routine.check_for_jsr(routine_name):
                    self.log().debug(f"JSR to '{routine_name}' already exists in main routine of program '{program_name}'")
                else:
                    self.log().debug(f"Adding JSR call to '{routine_name}' in main routine of program '{program_name}'")
                    jsr_rung = rung.Rung(
                        controller=self.generator_object,
                        text=f'JSR({routine_name},0);',
                        comment=f'Call the {routine_name} routine.'
                    )
                    self.schema.add_rung(
                        program_name=program_name,
                        routine_name=program.main_routine_name,
                        rung_number=rung_position,
                        rung=jsr_rung
                    )

        return rout

    def add_rung(
        self,
        program_name: str,
        routine_name: str,
        new_rung: controller.Rung,
        rung_number: Optional[int] = None
    ) -> controller.Rung:
        """Helper method to add a rung to a routine.

        Args:
            program_name: Name of the program
            routine_name: Name of the routine
            new_rung: The rung to add
            rung_number: Position to insert the rung (-1 for end)
        """
        self.log().debug(
            f"Adding rung to routine '{routine_name}' in program '{program_name}' at rung {rung_number if rung_number is not None else 'end'}"
        )
        return self.schema.add_rung(
            program_name=program_name,
            routine_name=routine_name,
            rung_number=rung_number,
            rung=new_rung
        )

    def add_rung_to_safety_routine(self, rung: controller.Rung) -> None:
        """Helper to add a rung to the safety emulation routine."""
        if not self.emulation_safety_routine:
            raise ValueError("Safety emulation routine has not been created yet.")
        self._add_rung_common(
            rung=rung,
            program_name=self.target_safety_program_name,
            routine_name=self.emulation_safety_routine_name
        )

    def add_rung_to_standard_routine(self, rung: controller.Rung) -> None:
        """Helper to add a rung to the standard emulation routine."""
        if not self.emulation_standard_routine:
            raise ValueError("Emulation routine has not been created yet.")
        self._add_rung_common(
            rung=rung,
            program_name=self.target_standard_program_name,
            routine_name=self.emulation_standard_routine_name
        )

    def add_rungs(
        self,
        program_name: str,
        routine_name: str,
        new_rungs: List[controller.Rung],
        rung_number: Optional[int] = None
    ) -> None:
        """Helper method to add multiple rungs to a routine.

        Args:
            program_name: Name of the program
            routine_name: Name of the routine
            new_rungs: List of rungs to add
            rung_number: Position to insert the first rung (-1 for end)
        """
        for i, r in enumerate(new_rungs):
            position = rung_number + i if rung_number is not None and rung_number >= 0 else -1
            self.add_rung(
                program_name=program_name,
                routine_name=routine_name,
                new_rung=r,
                rung_number=position
            )

    def add_safety_tag_mapping(
        self,
        standard_tag: str,
        safety_tag: str,
    ) -> None:
        """Helper method to add a safety tag mapping.

        Args:
            standard_tag: Name of the standard tag
            safety_tag: Name of the safety tag
        """
        if not standard_tag or not safety_tag:
            return
        self.schema.add_safety_tag_mapping(
            std_tag=standard_tag,
            sfty_tag=safety_tag
        )

    def block_routine_jsr(
        self,
        program_name: str,
        routine_name: str
    ) -> None:
        """Helper method to block a JSR call to a routine.

        Args:
            program_name: Name of the program
            routine_name: Name of the routine
        """
        self.log().debug(f"Blocking JSR call to routine '{routine_name}' in program '{program_name}'")
        ...

    def generate_emulation_logic(self) -> controller.ControllerModificationSchema:
        """Main entry point to generate emulation logic.

        Returns:
            ControllerModificationSchema: The modification schema with all changes.
        """
        self.log().info(f"Starting emulation generation for {self.generator_object.name}")
        self._generate_base_emulation()
        self._generate_custom_module_emulation()
        self._generate_custom_logic()

        self.schema.execute()
        self.log().info(f"Emulation generation completed for {self.generator_object.name}")
        return self.schema

    def get_modules_by_type(self, module_type: str) -> List[controller.Module]:
        """Get all modules of a specific type.

        Args:
            module_type: The module type to filter by

        Returns:
            List[Module]: List of matching modules
        """
        mods = [module for module in self.generator_object.modules if module.type_ == module_type]
        self.log().info('Found %d modules of type %s...', len(mods), module_type)
        return mods

    def get_modules_by_description_pattern(self, pattern: str) -> List[controller.Module]:
        """Get modules matching a description pattern.

        Args:
            pattern: Pattern to match in module description

        Returns:
            List[Module]: List of matching modules
        """
        mods = [m for m in self.generator_object.modules if m.description and pattern in m.description]
        self.log().info('Found %d modules matching description pattern "%s"...', len(mods), pattern)
        return mods

    def remove_base_emulation(self) -> None:
        """Remove the base emulation logic common to all controllers."""
        pass

    def remove_module_emulation(self) -> None:
        """Remove module-specific emulation logic."""
        pass

    def remove_emulation_logic(self) -> controller.ControllerModificationSchema:
        """Remove previously added emulation logic.

        Returns:
            ControllerModificationSchema: The modification schema with all removals.
        """
        self.log().info(f"Starting emulation removal for {self.generator_object.name}")

        # Remove emulation logic
        self.remove_base_emulation()
        self.remove_module_emulation()
        self.remove_custom_logic()

        # Execute the schema to remove added elements
        self.schema.execute()

        self.log().info(f"Emulation removal completed for {self.generator_object.name}")
        return self.schema

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
        self.log().debug(f"Removing controller tag '{tag_name}'")

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
        self.log().debug(f"Removing datatype '{datatype_name}' from controller")

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
        self.log().debug(f"Removing tag '{tag_name}' from program '{program_name}'")

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
        self.log().debug(f"Removing routine '{routine_name}' from controller")

        self.schema.remove_routine(
            program_name,
            routine_name
        )

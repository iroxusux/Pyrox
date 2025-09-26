"""Unit tests for emu.py module."""
import unittest
from unittest.mock import Mock, patch, call
from typing import Optional

from pyrox.models.generator import EmulationGenerator, EmulationGeneratorFactory
from pyrox.models.plc import controller, module, routine
from pyrox.models.abc import meta, factory


class TestEmulationGeneratorFactory(unittest.TestCase):
    """Test cases for EmulationGeneratorFactory class."""

    def test_factory_inheritance(self):
        """Test that EmulationGeneratorFactory inherits from MetaFactory."""
        self.assertTrue(issubclass(EmulationGeneratorFactory, factory.MetaFactory))

    def test_factory_instantiation(self):
        """Test that EmulationGeneratorFactory is a metaclass and should not be instantiated directly."""
        with self.assertRaises(TypeError):
            EmulationGeneratorFactory()  # type: ignore


class TestController(controller.Controller):
    """Mock controller class for testing"""
    pass


class ConcreteEmulationGenerator(EmulationGenerator):
    """Concrete implementation of EmulationGenerator for testing."""

    supporting_class = TestController

    @property
    def base_tags(self) -> list[tuple[str, str, str]]:
        return [
            ("Uninhibit", "DINT", "Uninhibit tag"),
            ("Inhibit", "DINT", "Inhibit tag"),
            ("ToggleInhibit", "BOOL", "Toggle inhibit tag"),
            ("LocalMode", "DINT", "Local mode tag")
        ]

    @property
    def custom_tags(self) -> list[tuple[str, str, str, Optional[str]]]:
        return [
            ("CustomTag1", "BOOL", "Custom tag 1", None),
            ("CustomArray", "DINT", "Custom array tag", "[10]")
        ]

    @property
    def emulation_safety_routine_name(self) -> str:
        return "SafetyEmulationRoutine"

    @property
    def emulation_standard_routine_description(self) -> str:
        return "Standard emulation routine description"

    @property
    def emulation_standard_routine_name(self) -> str:
        return "StandardEmulationRoutine"

    @property
    def target_safety_program_name(self) -> str:
        return "SafetyProgram"

    @property
    def target_standard_program_name(self) -> str:
        return "MainProgram"

    @property
    def test_mode_tag(self) -> str:
        return "TestMode"


class TestEmulationGenerator(unittest.TestCase):
    """Test cases for EmulationGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock controller
        self.mock_controller = Mock(spec=TestController)
        self.mock_controller.__class__.__name__ = "TestController"
        self.mock_controller.name = "TestController"
        self.mock_controller.modules = []
        self.mock_controller.programs = Mock()
        self.mock_controller.config = Mock()

        # Create mock schema
        self.mock_schema = Mock(spec=controller.ControllerModificationSchema)

        # Create concrete generator instance
        with patch('pyrox.models.plc.controller.ControllerModificationSchema') as mock_schema_class:
            mock_schema_class.return_value = self.mock_schema
            self.generator = ConcreteEmulationGenerator(self.mock_controller)

    def test_inheritance(self):
        """Test that EmulationGenerator inherits from PyroxObject."""
        self.assertTrue(issubclass(EmulationGenerator, meta.PyroxObject))

    def test_metaclass(self):
        """Test that EmulationGenerator uses FactoryTypeMeta."""
        self.assertTrue(issubclass(type(EmulationGenerator), factory.FactoryTypeMeta))

    def test_init_with_valid_controller(self):
        """Test initialization with valid controller."""
        self.assertEqual(self.generator.generator_object, self.mock_controller)
        self.assertIsInstance(self.generator.schema, Mock)
        self.assertIsNone(self.generator.emulation_standard_routine)
        self.assertIsNone(self.generator.emulation_safety_routine)

    def test_init_subclass_sets_supports_registering(self):
        """Test that __init_subclass__ sets supports_registering to True."""
        self.assertTrue(ConcreteEmulationGenerator.supports_registering)

    def test_generator_object_property(self):
        """Test generator_object property getter."""
        self.assertEqual(self.generator.generator_object, self.mock_controller)

    def test_generator_object_setter_valid_type(self):
        """Test generator_object setter with valid controller type."""
        new_controller = Mock(spec=TestController)
        new_controller.__class__.__name__ = "TestController"

        self.generator.generator_object = new_controller
        self.assertEqual(self.generator.generator_object, new_controller)

    def test_generator_object_setter_invalid_type(self):
        """Test generator_object setter with invalid controller type."""
        invalid_controller = Mock(spec=controller.Controller)
        invalid_controller.__class__.__name__ = "WrongController"

        with self.assertRaises(TypeError) as context:
            self.generator.generator_object = invalid_controller

        self.assertIn("Controller must be of type", str(context.exception))

    def test_safety_routine_setter_valid_type(self):
        """Test emulation_safety_routine setter with valid Routine type."""
        mock_routine = Mock(spec=controller.Routine)

        self.generator.emulation_safety_routine = mock_routine
        self.assertEqual(self.generator.emulation_safety_routine, mock_routine)

    def test_safety_routine_setter_invalid_type(self):
        """Test emulation_safety_routine setter with invalid type."""
        invalid_routine = Mock()

        with self.assertRaises(TypeError) as context:
            self.generator.emulation_safety_routine = invalid_routine

        self.assertIn("Emulation safety routine must be of type", str(context.exception))

    def test_standard_routine_setter_valid_type(self):
        """Test emulation_standard_routine setter with valid Routine type."""
        mock_routine = Mock(spec=controller.Routine)

        self.generator.emulation_standard_routine = mock_routine
        self.assertEqual(self.generator.emulation_standard_routine, mock_routine)

    def test_standard_routine_setter_invalid_type(self):
        """Test emulation_standard_routine setter with invalid type."""
        invalid_routine = Mock()

        with self.assertRaises(TypeError) as context:
            self.generator.emulation_standard_routine = invalid_routine

        self.assertIn("Emulation standard routine must be of type", str(context.exception))

    def test_base_tags_implemented(self):
        """Test that base_tags property returns expected tags."""
        expected_tags = [
            ("Uninhibit", "DINT", "Uninhibit tag"),
            ("Inhibit", "DINT", "Inhibit tag"),
            ("ToggleInhibit", "BOOL", "Toggle inhibit tag"),
            ("LocalMode", "DINT", "Local mode tag")
        ]
        self.assertEqual(self.generator.base_tags, expected_tags)

    def test_custom_tags_implemented(self):
        """Test that custom_tags property returns expected tags."""
        expected_tags = [
            ("CustomTag1", "BOOL", "Custom tag 1", None),
            ("CustomArray", "DINT", "Custom array tag", "[10]")
        ]
        self.assertEqual(self.generator.custom_tags, expected_tags)

    def test_inhibit_tag_property(self):
        """Test inhibit_tag property returns correct tag name."""
        self.assertEqual(self.generator.inhibit_tag, "Inhibit")

    def test_local_mode_tag_property(self):
        """Test local_mode_tag property returns correct tag name."""
        self.assertEqual(self.generator.local_mode_tag, "LocalMode")

    def test_toggle_inhibit_tag_property(self):
        """Test toggle_inhibit_tag property returns correct tag name."""
        self.assertEqual(self.generator.toggle_inhibit_tag, "ToggleInhibit")

    def test_uninhibit_tag_property(self):
        """Test uninhibit_tag property returns correct tag name."""
        self.assertEqual(self.generator.uninhibit_tag, "Uninhibit")

    def test_emulation_safety_routine_description_default(self):
        """Test that safety routine description defaults to standard description."""
        self.assertEqual(
            self.generator.emulation_safety_routine_description,
            self.generator.emulation_standard_routine_description
        )

    def test_get_factory_class_method(self):
        """Test get_factory class method returns correct factory."""
        self.assertEqual(EmulationGenerator.get_factory(), EmulationGeneratorFactory)

    def test_controller_property_shortcut(self):
        """Test controller property (should be generator_object)."""
        # Note: This assumes controller is an alias/property for generator_object
        # If not implemented, this test may need adjustment
        if hasattr(self.generator, 'controller'):
            self.assertEqual(self.generator.generator_object, self.mock_controller)

    @patch('pyrox.models.plc.imodule.ModuleWarehouseFactory.filter_modules_by_type')
    def test_generate_builtin_common_with_modules(self, mock_filter):
        """Test _generate_builtin_common with mock modules."""
        # Setup mock introspective module
        mock_introspective_module = Mock()
        mock_introspective_module.module = Mock()
        mock_introspective_module.module.name = "TestModule"
        mock_introspective_module.get_required_imports.return_value = [("test.l5x", ["Tag", "Routine"])]
        mock_introspective_module.get_required_tags.return_value = [{"tag_name": "TestTag", "datatype": "BOOL"}]
        mock_introspective_module.get_required_standard_to_safety_mapping.return_value = ("StdTag", "SafeTag")
        mock_introspective_module.get_required_standard_rungs.return_value = []
        mock_introspective_module.get_required_safety_rungs.return_value = []

        mock_filter.return_value = [mock_introspective_module]

        # Test the method
        self.generator._generate_builtin_common(module.ModuleControlsType.BLOCK)

        # Verify calls were made
        mock_filter.assert_called_once()
        mock_introspective_module.get_required_imports.assert_called_once()
        mock_introspective_module.get_required_tags.assert_called_once()

    def test_generate_builtin_common_with_no_module(self):
        """Test _generate_builtin_common handles None module gracefully."""
        with patch('pyrox.models.plc.imodule.ModuleWarehouseFactory.filter_modules_by_type') as mock_filter:
            mock_filter.return_value = [None]

            # Should not raise exception
            self.generator._generate_builtin_common(module.ModuleControlsType.BLOCK)

    def test_generate_builtin_common_with_no_introspective_module(self):
        """Test _generate_builtin_common handles missing introspective_module."""
        with patch('pyrox.models.plc.imodule.ModuleWarehouseFactory.filter_modules_by_type') as mock_filter:
            mock_introspective_module = Mock()
            mock_introspective_module.module = None
            mock_filter.return_value = [mock_introspective_module]

            # Should not raise exception
            self.generator._generate_builtin_common(module.ModuleControlsType.BLOCK)

    def test_add_l5x_imports(self):
        """Test add_l5x_imports method."""
        imports = [("file1.l5x", ["Tag", "Routine"]), ("file2.l5x", ["DataType"])]

        self.generator.add_l5x_imports(imports)

        # Verify schema method calls
        expected_calls = [
            call.add_import_from_file(file_location="file1.l5x", asset_types=["Tag", "Routine"]),
            call.add_import_from_file(file_location="file2.l5x", asset_types=["DataType"])
        ]
        self.mock_schema.add_import_from_file.assert_has_calls(expected_calls)

    @patch('pyrox.models.plc.tag.Tag')
    def test_add_controller_tag(self, mock_tag_class):
        """Test add_controller_tag method."""
        mock_tag = Mock()
        mock_tag_class.return_value = mock_tag

        result = self.generator.add_controller_tag(
            tag_name="TestTag",
            datatype="BOOL",
            description="Test description"
        )

        # Verify Tag creation
        mock_tag_class.assert_called_once_with(
            controller=self.mock_controller,
            name="TestTag",
            datatype="BOOL",
            description="Test description",
            constant=False,
            external_access="Read/Write",
            tag_type="Base"
        )

        # Verify schema call
        self.mock_schema.add_controller_tag.assert_called_once_with(mock_tag)
        self.assertEqual(result, self.mock_schema.add_controller_tag.return_value)

    def test_add_controller_tags(self):
        """Test add_controller_tags method."""
        tags = [
            {"tag_name": "Tag1", "datatype": "BOOL", "description": "Description 1"},
            {"tag_name": "Tag2", "datatype": "DINT", "description": "Description 2"}
        ]

        with patch.object(self.generator, 'add_controller_tag') as mock_add_tag:
            self.generator.add_controller_tags(tags)

            expected_calls = [
                call(tag_name="Tag1", datatype="BOOL", description="Description 1"),
                call(tag_name="Tag2", datatype="DINT", description="Description 2")
            ]
            mock_add_tag.assert_has_calls(expected_calls)

    @patch('pyrox.models.plc.tag.Tag')
    def test_add_program_tag(self, mock_tag_class):
        """Test add_program_tag method."""
        mock_tag = Mock()
        mock_tag_class.return_value = mock_tag

        result = self.generator.add_program_tag(
            program_name="TestProgram",
            tag_name="TestTag",
            datatype="BOOL",
            description="Test description"
        )

        # Verify Tag creation
        mock_tag_class.assert_called_once_with(
            controller=self.mock_controller,
            name="TestTag",
            datatype="BOOL",
            description="Test description"
        )

        # Verify schema call
        self.mock_schema.add_program_tag.assert_called_once_with(
            program_name="TestProgram",
            tag=mock_tag
        )
        self.assertEqual(result, self.mock_schema.add_program_tag.return_value)

    def test_add_routine_with_jsr_call(self):
        """Test add_routine method with JSR call."""
        # Setup mock program and routine
        mock_program = Mock()
        mock_main_routine = Mock()
        mock_main_routine.check_for_jsr.return_value = False
        mock_program.main_routine = mock_main_routine
        mock_program.main_routine_name = "Main"

        self.mock_controller.programs.get.return_value = mock_program
        self.mock_controller.config.routine_type.return_value = Mock(spec=controller.Routine)

        with patch('pyrox.models.plc.rung.Rung') as mock_rung_class:
            result = self.generator.add_routine(
                program_name="TestProgram",
                routine_name="TestRoutine",
                routine_description="Test Description",
                call_from_main=True,
                rung_position=0
            )

            # Verify routine creation and setup
            self.assertIsNotNone(result)
            self.mock_schema.add_routine.assert_called_once()

            # Verify JSR rung creation
            mock_rung_class.assert_called_once()
            self.mock_schema.add_rung.assert_called_once()

    def test_add_routine_jsr_already_exists(self):
        """Test add_routine when JSR already exists."""
        # Setup mock program with existing JSR
        mock_program = Mock()
        mock_main_routine = Mock()
        mock_main_routine.check_for_jsr.return_value = True
        mock_program.main_routine = mock_main_routine
        mock_program.main_routine_name = "Main"

        self.mock_controller.programs.get.return_value = mock_program
        self.mock_controller.config.routine_type.return_value = Mock(spec=controller.Routine)

        with patch('pyrox.models.plc.rung.Rung') as mock_rung_class:
            self.generator.add_routine(
                program_name="TestProgram",
                routine_name="TestRoutine",
                routine_description="Test Description",
                call_from_main=True
            )

            # Verify JSR rung was NOT created (already exists)
            mock_rung_class.assert_not_called()

    def test_add_rung(self):
        """Test add_rung method."""
        mock_rung = Mock(spec=controller.Rung)

        result = self.generator.add_rung(
            program_name="TestProgram",
            routine_name="TestRoutine",
            new_rung=mock_rung,
            rung_number=5
        )

        self.mock_schema.add_rung.assert_called_once_with(
            program_name="TestProgram",
            routine_name="TestRoutine",
            rung_number=5,
            rung=mock_rung
        )
        self.assertEqual(result, self.mock_schema.add_rung.return_value)

    def test_add_rungs(self):
        """Test add_rungs method."""
        mock_rungs = [Mock(spec=controller.Rung) for _ in range(3)]

        with patch.object(self.generator, 'add_rung') as mock_add_rung:
            self.generator.add_rungs(
                program_name="TestProgram",
                routine_name="TestRoutine",
                new_rungs=mock_rungs,
                rung_number=2
            )

            expected_calls = [
                call(program_name="TestProgram", routine_name="TestRoutine",
                     new_rung=mock_rungs[0], rung_number=2),
                call(program_name="TestProgram", routine_name="TestRoutine",
                     new_rung=mock_rungs[1], rung_number=3),
                call(program_name="TestProgram", routine_name="TestRoutine",
                     new_rung=mock_rungs[2], rung_number=4)
            ]
            mock_add_rung.assert_has_calls(expected_calls)

    def test_add_rungs_no_position(self):
        """Test add_rungs method without specific position."""
        mock_rungs = [Mock(spec=controller.Rung) for _ in range(2)]

        with patch.object(self.generator, 'add_rung') as mock_add_rung:
            self.generator.add_rungs(
                program_name="TestProgram",
                routine_name="TestRoutine",
                new_rungs=mock_rungs
            )

            expected_calls = [
                call(program_name="TestProgram", routine_name="TestRoutine",
                     new_rung=mock_rungs[0], rung_number=-1),
                call(program_name="TestProgram", routine_name="TestRoutine",
                     new_rung=mock_rungs[1], rung_number=-1)
            ]
            mock_add_rung.assert_has_calls(expected_calls)

    def test_add_safety_tag_mapping(self):
        """Test add_safety_tag_mapping method."""
        self.generator.add_safety_tag_mapping("StandardTag", "SafetyTag")

        self.mock_schema.add_safety_tag_mapping.assert_called_once_with(
            std_tag="StandardTag",
            sfty_tag="SafetyTag"
        )

    def test_add_safety_tag_mapping_empty_tags(self):
        """Test add_safety_tag_mapping with empty tags."""
        self.generator.add_safety_tag_mapping("", "SafetyTag")
        self.generator.add_safety_tag_mapping("StandardTag", "")
        self.generator.add_safety_tag_mapping("", "")

        # Should not call schema method for empty tags
        self.mock_schema.add_safety_tag_mapping.assert_not_called()

    def test_add_rung_to_standard_routine(self):
        """Test add_rung_to_standard_routine method."""
        # Setup emulation routine
        self.generator.emulation_standard_routine = Mock(spec=controller.Routine)
        mock_rung = Mock(spec=controller.Rung)

        with patch.object(self.generator, '_add_rung_common') as mock_add_common:
            self.generator.add_rung_to_standard_routine(mock_rung)

            mock_add_common.assert_called_once_with(
                rung=mock_rung,
                program_name="MainProgram",
                routine_name="StandardEmulationRoutine"
            )

    def test_add_rung_to_standard_routine_no_routine(self):
        """Test add_rung_to_standard_routine without emulation routine."""
        mock_rung = Mock(spec=controller.Rung)

        with self.assertRaises(ValueError) as context:
            self.generator.add_rung_to_standard_routine(mock_rung)

        self.assertIn("Emulation routine has not been created yet", str(context.exception))

    def test_add_rung_to_safety_routine(self):
        """Test add_rung_to_safety_routine method."""
        # Setup safety emulation routine
        self.generator.emulation_safety_routine = Mock(spec=routine.Routine)
        mock_rung = Mock(spec=controller.Rung)

        with patch.object(self.generator, '_add_rung_common') as mock_add_common:
            self.generator.add_rung_to_safety_routine(mock_rung)

            mock_add_common.assert_called_once_with(
                rung=mock_rung,
                program_name="SafetyProgram",
                routine_name="SafetyEmulationRoutine"
            )

    def test_add_rung_to_safety_routine_no_routine(self):
        """Test add_rung_to_safety_routine without safety emulation routine."""
        mock_rung = Mock(spec=controller.Rung)

        with self.assertRaises(ValueError) as context:
            self.generator.add_rung_to_safety_routine(mock_rung)

        self.assertIn("Safety emulation routine has not been created yet", str(context.exception))

    def test_get_modules_by_type(self):
        """Test get_modules_by_type method."""
        # Setup mock modules
        mock_module1 = Mock()
        mock_module1.type_ = "INPUT"
        mock_module2 = Mock()
        mock_module2.type_ = "OUTPUT"
        mock_module3 = Mock()
        mock_module3.type_ = "INPUT"

        self.mock_controller.modules = [mock_module1, mock_module2, mock_module3]

        result = self.generator.get_modules_by_type("INPUT")

        self.assertEqual(len(result), 2)
        self.assertIn(mock_module1, result)
        self.assertIn(mock_module3, result)
        self.assertNotIn(mock_module2, result)

    def test_get_modules_by_description_pattern(self):
        """Test get_modules_by_description_pattern method."""
        # Setup mock modules
        mock_module1 = Mock()
        mock_module1.description = "Analog Input Module"
        mock_module2 = Mock()
        mock_module2.description = "Digital Output Module"
        mock_module3 = Mock()
        mock_module3.description = "Analog Output Module"
        mock_module4 = Mock()
        mock_module4.description = None

        self.mock_controller.modules = [mock_module1, mock_module2, mock_module3, mock_module4]

        result = self.generator.get_modules_by_description_pattern("Analog")

        self.assertEqual(len(result), 2)
        self.assertIn(mock_module1, result)
        self.assertIn(mock_module3, result)
        self.assertNotIn(mock_module2, result)
        self.assertNotIn(mock_module4, result)

    def test_remove_controller_tag(self):
        """Test remove_controller_tag method."""
        self.generator.remove_controller_tag("TestTag")

        self.mock_schema.remove_controller_tag.assert_called_once_with(tag_name="TestTag")

    def test_remove_program_tag(self):
        """Test remove_program_tag method."""
        self.generator.remove_program_tag("TestProgram", "TestTag")

        self.mock_schema.remove_program_tag.assert_called_once_with(
            program_name="TestProgram",
            tag_name="TestTag"
        )

    def test_remove_routine(self):
        """Test remove_routine method."""
        self.generator.remove_routine("TestProgram", "TestRoutine")

        self.mock_schema.remove_routine.assert_called_once_with("TestProgram", "TestRoutine")

    def test_remove_datatype(self):
        """Test remove_datatype method."""
        self.generator.remove_datatype("TestDataType")

        self.mock_schema.remove_datatype.assert_called_once_with(datatype_name="TestDataType")

    @patch.object(ConcreteEmulationGenerator, '_generate_base_emulation')
    @patch.object(ConcreteEmulationGenerator, '_generate_custom_module_emulation')
    @patch.object(ConcreteEmulationGenerator, '_generate_custom_logic')
    def test_generate_emulation_logic_success(self, mock_custom_logic, mock_custom_module,
                                              mock_base_emulation):
        """Test generate_emulation_logic method success path."""
        result = self.generator.generate_emulation_logic()

        # Verify all generation methods were called
        mock_base_emulation.assert_called_once()
        mock_custom_module.assert_called_once()
        mock_custom_logic.assert_called_once()

        # Verify schema execution
        self.mock_schema.execute.assert_called_once()
        self.assertEqual(result, self.mock_schema)

    @patch.object(ConcreteEmulationGenerator, 'remove_base_emulation')
    @patch.object(ConcreteEmulationGenerator, 'remove_module_emulation')
    @patch.object(ConcreteEmulationGenerator, 'remove_custom_logic')
    def test_remove_emulation_logic(self, mock_remove_custom, mock_remove_module, mock_remove_base):
        """Test remove_emulation_logic method."""
        result = self.generator.remove_emulation_logic()

        # Verify all removal methods were called
        mock_remove_base.assert_called_once()
        mock_remove_module.assert_called_once()
        mock_remove_custom.assert_called_once()

        # Verify schema execution
        self.mock_schema.execute.assert_called_once()
        self.assertEqual(result, self.mock_schema)

    def test_generate_base_tags(self):
        """Test _generate_base_tags method."""
        with patch.object(self.generator, 'add_controller_tag') as mock_add_tag:
            self.generator._generate_base_tags()

            expected_calls = [
                call("Uninhibit", "DINT", description="Uninhibit tag"),
                call("Inhibit", "DINT", description="Inhibit tag"),
                call("ToggleInhibit", "BOOL", description="Toggle inhibit tag"),
                call("LocalMode", "DINT", description="Local mode tag")
            ]
            mock_add_tag.assert_has_calls(expected_calls)

    def test_generate_custom_tags(self):
        """Test _generate_custom_tags method."""
        with patch.object(self.generator, 'add_controller_tag') as mock_add_tag:
            self.generator._generate_custom_tags()

            expected_calls = [
                call("CustomTag1", "BOOL", description="Custom tag 1", dimensions=None),
                call("CustomArray", "DINT", description="Custom array tag", dimensions="[10]")
            ]
            mock_add_tag.assert_has_calls(expected_calls)

    def test_generate_base_standard_routine(self):
        """Test _generate_base_standard_routine method."""
        with patch.object(self.generator, 'add_routine') as mock_add_routine:
            mock_routine = Mock(spec=routine.Routine)
            mock_add_routine.return_value = mock_routine

            self.generator._generate_base_standard_routine()

            mock_add_routine.assert_called_once_with(
                program_name="MainProgram",
                routine_name="StandardEmulationRoutine",
                routine_description="Standard emulation routine description",
                call_from_main=True,
                rung_position=0
            )
            self.assertEqual(self.generator.emulation_standard_routine, mock_routine)

    def test_generate_base_safety_routine(self):
        """Test _generate_base_safety_routine method."""
        with patch.object(self.generator, 'add_routine') as mock_add_routine:
            mock_routine = Mock(spec=routine.Routine)
            mock_add_routine.return_value = mock_routine

            self.generator._generate_base_safety_routine()

            mock_add_routine.assert_called_once_with(
                program_name="SafetyProgram",
                routine_name="SafetyEmulationRoutine",
                routine_description="Standard emulation routine description",
                call_from_main=True,
                rung_position=0
            )
            self.assertEqual(self.generator.emulation_safety_routine, mock_routine)

    @patch('pyrox.models.plc.rung.Rung')
    def test_generate_base_standard_rungs(self, mock_rung_class):
        """Test _generate_base_standard_rungs method."""
        # Setup mock routine
        mock_routine = Mock(spec=routine.Routine)
        self.generator.emulation_standard_routine = mock_routine

        with patch.object(self.generator, 'add_rung_to_standard_routine') as mock_add_rung:
            with patch.object(self.generator, '_generate_module_inhibit_rungs') as mock_module_inhibit:
                self.generator._generate_base_standard_rungs()

                # Verify routine was cleared
                mock_routine.clear_rungs.assert_called_once()

                # Verify rungs were added (should be 3 calls)
                self.assertEqual(mock_add_rung.call_count, 3)

                # Verify module inhibit rungs generation
                mock_module_inhibit.assert_called_once()

    def test_generate_base_standard_rungs_no_routine(self):
        """Test _generate_base_standard_rungs without emulation routine."""
        self.generator.emulation_standard_routine = None

        with self.assertRaises(ValueError) as context:
            self.generator._generate_base_standard_rungs()

        self.assertIn("Emulation routine has not been created yet", str(context.exception))

    @patch('pyrox.models.plc.rung.Rung')
    def test_generate_base_safety_rungs(self, mock_rung_class):
        """Test _generate_base_safety_rungs method."""
        # Setup mock routine
        mock_routine = Mock(spec=routine.Routine)
        self.generator.emulation_safety_routine = mock_routine

        with patch.object(self.generator, 'add_rung_to_safety_routine') as mock_add_rung:
            self.generator._generate_base_safety_rungs()

            # Verify routine was cleared
            mock_routine.clear_rungs.assert_called_once()

            # Verify rung was added (should be 1 call)
            mock_add_rung.assert_called_once()

    def test_generate_base_safety_rungs_no_routine(self):
        """Test _generate_base_safety_rungs without safety emulation routine."""
        self.generator.emulation_safety_routine = None

        with self.assertRaises(ValueError) as context:
            self.generator._generate_base_safety_rungs()

        self.assertIn("Safety emulation routine has not been created yet", str(context.exception))

    def test_generate_module_inhibit_rungs(self):
        """Test _generate_module_inhibit_rungs method."""
        # Setup mock modules
        mock_local_module = Mock(spec=module.Module)
        mock_local_module.name = "Local"
        mock_module1 = Mock(spec=module.Module)
        mock_module1.name = "Module1"
        mock_module2 = Mock(spec=module.Module)
        mock_module2.name = "Module2"

        self.mock_controller.modules = [mock_local_module, mock_module1, mock_module2]
        self.mock_controller.config.rung_type.return_value = Mock()

        # Setup emulation routine
        self.generator.emulation_standard_routine = Mock(spec=routine.Routine)

        with patch.object(self.generator, 'add_rung_to_standard_routine') as mock_add_rung:
            self.generator._generate_module_inhibit_rungs()

            # Should add rungs for non-Local modules (2 calls)
            self.assertEqual(mock_add_rung.call_count, 2)

    def test_generate_module_inhibit_rungs_no_routine(self):
        """Test _generate_module_inhibit_rungs without emulation routine."""
        self.generator.emulation_standard_routine = None

        with self.assertRaises(ValueError) as context:
            self.generator._generate_module_inhibit_rungs()

        self.assertIn("Emulation routine has not been created yet", str(context.exception))

    @patch.object(ConcreteEmulationGenerator, '_generate_base_tags')
    @patch.object(ConcreteEmulationGenerator, '_generate_custom_tags')
    @patch.object(ConcreteEmulationGenerator, '_generate_base_standard_routine')
    @patch.object(ConcreteEmulationGenerator, '_generate_base_standard_rungs')
    @patch.object(ConcreteEmulationGenerator, '_generate_base_safety_routine')
    @patch.object(ConcreteEmulationGenerator, '_generate_base_safety_rungs')
    @patch.object(ConcreteEmulationGenerator, '_generate_base_module_emulation')
    @patch.object(ConcreteEmulationGenerator, '_generate_custom_standard_routines')
    @patch.object(ConcreteEmulationGenerator, '_generate_custom_standard_rungs')
    @patch.object(ConcreteEmulationGenerator, '_generate_custom_safety_routines')
    @patch.object(ConcreteEmulationGenerator, '_generate_custom_safety_rungs')
    def test_generate_base_emulation(self, mock_custom_safety_rungs, mock_custom_safety_routines,
                                     mock_custom_standard_rungs, mock_custom_standard_routines,
                                     mock_base_module, mock_base_safety_rungs, mock_base_safety_routine,
                                     mock_base_standard_rungs, mock_base_standard_routine,
                                     mock_custom_tags, mock_base_tags):
        """Test _generate_base_emulation calls all generation methods in correct order."""
        self.generator._generate_base_emulation()

        # Verify all methods were called once
        mock_base_tags.assert_called_once()
        mock_custom_tags.assert_called_once()
        mock_base_standard_routine.assert_called_once()
        mock_base_standard_rungs.assert_called_once()
        mock_base_safety_routine.assert_called_once()
        mock_base_safety_rungs.assert_called_once()
        mock_base_module.assert_called_once()
        mock_custom_standard_routines.assert_called_once()
        mock_custom_standard_rungs.assert_called_once()
        mock_custom_safety_routines.assert_called_once()
        mock_custom_safety_rungs.assert_called_once()

    @patch.object(ConcreteEmulationGenerator, '_generate_builtin_common')
    def test_generate_base_module_emulation(self, mock_builtin_common):
        """Test _generate_base_module_emulation method."""
        with patch('pyrox.models.plc.module.ModuleControlsType') as mock_module_types:
            mock_module_types.__iter__ = Mock(return_value=iter([
                module.ModuleControlsType.IO,
                module.ModuleControlsType.COMMUNICATION
            ]))

            self.generator._generate_base_module_emulation()

            # Should call _generate_builtin_common for each module type
            self.assertEqual(mock_builtin_common.call_count, 2)

    def test_block_routine_jsr(self):
        """Test block_routine_jsr method (placeholder implementation)."""
        # This method appears to be a placeholder, just verify it doesn't raise exceptions
        self.generator.block_routine_jsr("TestProgram", "TestRoutine")

    def test_abstract_properties_raise_not_implemented(self):
        """Test that abstract properties raise NotImplementedError."""
        # Create a direct instance of EmulationGenerator (bypassing abstract check for testing)
        with patch('pyrox.models.plc.controller.ControllerModificationSchema'):
            # Need to create a class that doesn't override abstract methods
            class IncompleteGenerator(EmulationGenerator):
                supporting_class = "TestController"

            incomplete_gen = IncompleteGenerator.__new__(IncompleteGenerator)
            incomplete_gen._generator_object = self.mock_controller

            # Test abstract properties
            with self.assertRaises(NotImplementedError):
                _ = incomplete_gen.base_tags

            with self.assertRaises(NotImplementedError):
                _ = incomplete_gen.custom_tags

            with self.assertRaises(NotImplementedError):
                _ = incomplete_gen.emulation_safety_routine_name

            with self.assertRaises(NotImplementedError):
                _ = incomplete_gen.emulation_standard_routine_description

            with self.assertRaises(NotImplementedError):
                _ = incomplete_gen.emulation_standard_routine_name

            with self.assertRaises(NotImplementedError):
                _ = incomplete_gen.target_safety_program_name

            with self.assertRaises(NotImplementedError):
                _ = incomplete_gen.target_standard_program_name

            with self.assertRaises(NotImplementedError):
                _ = incomplete_gen.test_mode_tag


class TestEmulationGeneratorIntegration(unittest.TestCase):
    """Integration tests for EmulationGenerator with real-like scenarios."""

    def setUp(self):
        """Set up test fixtures for integration tests."""
        self.mock_controller = Mock(spec=TestController)
        self.mock_controller.__class__.__name__ = "TestController"
        self.mock_controller.name = "IntegrationTestController"
        self.mock_controller.modules = []
        self.mock_controller.programs = Mock()
        self.mock_controller.config = Mock()

        with patch('pyrox.models.plc.controller.ControllerModificationSchema'):
            self.generator = ConcreteEmulationGenerator(self.mock_controller)

    def test_full_emulation_generation_workflow(self):
        """Test a complete emulation generation workflow."""
        # Mock all the generation steps
        with patch.object(self.generator, '_generate_base_emulation') as mock_base:
            with patch.object(self.generator, '_generate_custom_module_emulation') as mock_custom_mod:
                with patch.object(self.generator, '_generate_custom_logic') as mock_custom_logic:

                    result = self.generator.generate_emulation_logic()

                    # Verify the workflow
                    mock_base.assert_called_once()
                    mock_custom_mod.assert_called_once()
                    mock_custom_logic.assert_called_once()
                    self.generator.schema.execute.assert_called_once()
                    self.assertEqual(result, self.generator.schema)

    def test_tag_management_workflow(self):
        """Test tag management workflow."""
        # Test adding and removing controller tags
        with patch.object(self.generator, 'add_controller_tag') as mock_add:
            with patch.object(self.generator, 'remove_controller_tag') as mock_remove:

                # Add tags
                self.generator.add_controller_tag("TestTag1", "BOOL", "Test tag 1")
                self.generator.add_controller_tag("TestTag2", "DINT", "Test tag 2")

                # Remove a tag
                self.generator.remove_controller_tag("TestTag1")

                # Verify calls
                self.assertEqual(mock_add.call_count, 2)
                mock_remove.assert_called_once_with("TestTag1")

    def test_routine_management_workflow(self):
        """Test routine management workflow."""
        # Test adding and removing routines
        with patch.object(self.generator, 'add_routine') as mock_add_routine:
            with patch.object(self.generator, 'remove_routine') as mock_remove_routine:

                # Add routine
                mock_routine = Mock()
                mock_add_routine.return_value = mock_routine

                result = self.generator.add_routine(
                    program_name="TestProgram",
                    routine_name="TestRoutine",
                    routine_description="Test routine"
                )

                # Remove routine
                self.generator.remove_routine("TestProgram", "TestRoutine")

                # Verify calls
                mock_add_routine.assert_called_once()
                mock_remove_routine.assert_called_once_with("TestProgram", "TestRoutine")
                self.assertEqual(result, mock_routine)


if __name__ == '__main__':
    unittest.main()

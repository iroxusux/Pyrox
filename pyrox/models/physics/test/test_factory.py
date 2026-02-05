"""Unit tests for factory.py module.

Tests the PhysicsSceneTemplate and PhysicsSceneFactory classes for
creating and managing physics body templates.
"""
import unittest
from typing import Optional

from pyrox.models.physics.factory import PhysicsSceneTemplate, PhysicsSceneFactory
from pyrox.models.physics.base import BasePhysicsBody
from pyrox.interfaces import (
    IBasePhysicsBody,
)
from pyrox.models.protocols.physics import Material


class MockPhysicsBody(BasePhysicsBody):
    """Mock physics body for testing."""

    def __init__(
        self,
        name: str = "Mock",
        x: float = 0.0,
        y: float = 0.0,
        mass: float = 1.0,
        test_attribute: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            name=name,
            x=x,
            y=y,
            mass=mass,
            **kwargs
        )
        self.test_attribute = test_attribute


def mock_factory_func(**kwargs) -> IBasePhysicsBody:
    """Mock factory function for testing custom factory logic."""
    return MockPhysicsBody(
        name=kwargs.get("name", "Custom Mock"),
        x=kwargs.get("x", 100.0),
        y=kwargs.get("y", 200.0),
        test_attribute="from_factory_func"
    )


class TestPhysicsSceneTemplate(unittest.TestCase):
    """Test cases for PhysicsSceneTemplate class."""

    def setUp(self):
        """Set up test fixtures."""
        self.simple_template = PhysicsSceneTemplate(
            name="Simple Template",
            body_class=MockPhysicsBody,
            description="A simple test template"
        )

        self.template_with_defaults = PhysicsSceneTemplate(
            name="Template With Defaults",
            body_class=MockPhysicsBody,
            description="Template with default kwargs",
            default_kwargs={
                "name": "Default Body",
                "x": 50.0,
                "y": 75.0,
                "mass": 5.0,
                "test_attribute": "default_value"
            }
        )

        self.template_with_factory_func = PhysicsSceneTemplate(
            name="Custom Factory Template",
            body_class=MockPhysicsBody,
            description="Template with custom factory function",
            factory_func=mock_factory_func
        )

        self.categorized_template = PhysicsSceneTemplate(
            name="Categorized Template",
            body_class=MockPhysicsBody,
            description="Template with category and icon",
            category="Test Category",
            icon="test_icon"
        )

    # ==================== Initialization Tests ====================

    def test_template_initialization_minimal(self):
        """Test template initialization with minimal arguments."""
        template = PhysicsSceneTemplate(
            name="Minimal",
            body_class=MockPhysicsBody
        )

        self.assertEqual(template.name, "Minimal")
        self.assertEqual(template.body_class, MockPhysicsBody)
        self.assertEqual(template.description, "")
        self.assertEqual(template.default_kwargs, {})
        self.assertIsNone(template.factory_func)
        self.assertEqual(template.icon, "")
        self.assertEqual(template.category, "General")

    def test_template_initialization_full(self):
        """Test template initialization with all arguments."""
        template = PhysicsSceneTemplate(
            name="Full Template",
            body_class=MockPhysicsBody,
            description="Full description",
            default_kwargs={"x": 10.0},
            factory_func=mock_factory_func,
            icon="test_icon",
            category="Test"
        )

        self.assertEqual(template.name, "Full Template")
        self.assertEqual(template.body_class, MockPhysicsBody)
        self.assertEqual(template.description, "Full description")
        self.assertEqual(template.default_kwargs, {"x": 10.0})
        self.assertEqual(template.factory_func, mock_factory_func)
        self.assertEqual(template.icon, "test_icon")
        self.assertEqual(template.category, "Test")

    def test_template_repr(self):
        """Test template string representation."""
        repr_str = repr(self.simple_template)
        self.assertIn("PhysicsBodyTemplate", repr_str)
        self.assertIn("Simple Template", repr_str)
        self.assertIn("MockPhysicsBody", repr_str)

    # ==================== Create Method Tests ====================

    def test_create_with_no_kwargs(self):
        """Test creating body from template without kwargs."""
        body = self.simple_template.create()

        self.assertIsInstance(body, MockPhysicsBody)
        self.assertEqual(body.name, "Mock")  # Default from MockPhysicsBody
        self.assertEqual(body.x, 0.0)
        self.assertEqual(body.y, 0.0)

    def test_create_with_override_kwargs(self):
        """Test creating body with override kwargs."""
        body = self.simple_template.create(
            name="Overridden",
            x=100.0,
            y=200.0,
            mass=10.0
        )

        self.assertIsInstance(body, MockPhysicsBody)
        self.assertEqual(body.name, "Overridden")
        self.assertEqual(body.x, 100.0)
        self.assertEqual(body.y, 200.0)
        self.assertEqual(body.mass, 10.0)

    def test_create_with_default_kwargs(self):
        """Test creating body from template with default kwargs."""
        body = self.template_with_defaults.create()

        self.assertEqual(body.name, "Default Body")
        self.assertEqual(body.x, 50.0)
        self.assertEqual(body.y, 75.0)
        self.assertEqual(body.mass, 5.0)
        self.assertEqual(body.test_attribute, "default_value")  # type: ignore

    def test_create_override_default_kwargs(self):
        """Test overriding default kwargs."""
        body = self.template_with_defaults.create(
            name="Override Name",
            x=999.0
        )

        self.assertEqual(body.name, "Override Name")  # Overridden
        self.assertEqual(body.x, 999.0)  # Overridden
        self.assertEqual(body.y, 75.0)  # From defaults
        self.assertEqual(body.mass, 5.0)  # From defaults

    def test_create_with_custom_factory_func(self):
        """Test creating body using custom factory function."""
        body = self.template_with_factory_func.create()

        self.assertIsInstance(body, MockPhysicsBody)
        self.assertEqual(body.name, "Custom Mock")
        self.assertEqual(body.x, 100.0)
        self.assertEqual(body.y, 200.0)
        self.assertEqual(body.test_attribute, "from_factory_func")  # type: ignore

    def test_create_custom_factory_func_with_overrides(self):
        """Test custom factory function with override kwargs."""
        body = self.template_with_factory_func.create(
            name="Overridden Factory",
            x=500.0
        )

        self.assertEqual(body.name, "Overridden Factory")
        self.assertEqual(body.x, 500.0)
        self.assertEqual(body.y, 200.0)  # Default from factory func

    def test_template_attributes(self):
        """Test template category and icon attributes."""
        self.assertEqual(self.categorized_template.category, "Test Category")
        self.assertEqual(self.categorized_template.icon, "test_icon")


class TestPhysicsSceneFactory(unittest.TestCase):
    """Test cases for PhysicsSceneFactory class."""

    def setUp(self):
        """Set up test fixtures."""
        # Save existing templates before each test
        self._saved_templates = PhysicsSceneFactory._templates.copy()
        
        # Clear templates for isolated test environment
        PhysicsSceneFactory._templates.clear()

        self.template_a = PhysicsSceneTemplate(
            name="Template A",
            body_class=MockPhysicsBody,
            description="First test template",
            category="CategoryA"
        )

        self.template_b = PhysicsSceneTemplate(
            name="Template B",
            body_class=MockPhysicsBody,
            description="Second test template",
            category="CategoryB"
        )

        self.template_c = PhysicsSceneTemplate(
            name="Template C",
            body_class=MockPhysicsBody,
            description="Third test template",
            category="CategoryA"  # Same category as A
        )

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original templates after each test
        PhysicsSceneFactory._templates.clear()
        PhysicsSceneFactory._templates.update(self._saved_templates)

    # ==================== Registration Tests ====================

    def test_register_template(self):
        """Test registering a template."""
        PhysicsSceneFactory.register_template("TestTemplate", self.template_a)

        templates = PhysicsSceneFactory.get_all_templates()
        self.assertIn("TestTemplate", templates)
        self.assertEqual(templates["TestTemplate"], self.template_a)

    def test_register_multiple_templates(self):
        """Test registering multiple templates."""
        PhysicsSceneFactory.register_template("TemplateA", self.template_a)
        PhysicsSceneFactory.register_template("TemplateB", self.template_b)

        templates = PhysicsSceneFactory.get_all_templates()
        self.assertEqual(len(templates), 2)
        self.assertIn("TemplateA", templates)
        self.assertIn("TemplateB", templates)

    def test_register_template_overwrite(self):
        """Test registering template with existing name overwrites."""
        PhysicsSceneFactory.register_template("Template", self.template_a)
        PhysicsSceneFactory.register_template("Template", self.template_b)

        templates = PhysicsSceneFactory.get_all_templates()
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates["Template"], self.template_b)  # Overwritten

    # ==================== Unregistration Tests ====================

    def test_unregister_template(self):
        """Test unregistering a template."""
        PhysicsSceneFactory.register_template("Template", self.template_a)
        result = PhysicsSceneFactory.unregister_template("Template")

        self.assertTrue(result)
        templates = PhysicsSceneFactory.get_all_templates()
        self.assertEqual(len(templates), 0)

    def test_unregister_nonexistent_template(self):
        """Test unregistering a template that doesn't exist."""
        result = PhysicsSceneFactory.unregister_template("NonExistent")
        self.assertFalse(result)

    def test_unregister_one_of_multiple(self):
        """Test unregistering one template when multiple exist."""
        PhysicsSceneFactory.register_template("TemplateA", self.template_a)
        PhysicsSceneFactory.register_template("TemplateB", self.template_b)

        result = PhysicsSceneFactory.unregister_template("TemplateA")

        self.assertTrue(result)
        templates = PhysicsSceneFactory.get_all_templates()
        self.assertEqual(len(templates), 1)
        self.assertIn("TemplateB", templates)
        self.assertNotIn("TemplateA", templates)

    # ==================== Get Template Tests ====================

    def test_get_template(self):
        """Test getting a registered template."""
        PhysicsSceneFactory.register_template("Template", self.template_a)

        template = PhysicsSceneFactory.get_template("Template")
        self.assertEqual(template, self.template_a)

    def test_get_nonexistent_template(self):
        """Test getting a template that doesn't exist."""
        template = PhysicsSceneFactory.get_template("NonExistent")
        self.assertIsNone(template)

    def test_get_all_templates_empty(self):
        """Test getting all templates when none registered."""
        templates = PhysicsSceneFactory.get_all_templates()
        self.assertEqual(len(templates), 0)
        self.assertIsInstance(templates, dict)

    def test_get_all_templates(self):
        """Test getting all registered templates."""
        PhysicsSceneFactory.register_template("TemplateA", self.template_a)
        PhysicsSceneFactory.register_template("TemplateB", self.template_b)
        PhysicsSceneFactory.register_template("TemplateC", self.template_c)

        templates = PhysicsSceneFactory.get_all_templates()
        self.assertEqual(len(templates), 3)
        self.assertIn("TemplateA", templates)
        self.assertIn("TemplateB", templates)
        self.assertIn("TemplateC", templates)

    def test_get_all_templates_returns_copy(self):
        """Test that get_all_templates returns a copy."""
        PhysicsSceneFactory.register_template("Template", self.template_a)

        templates1 = PhysicsSceneFactory.get_all_templates()
        templates2 = PhysicsSceneFactory.get_all_templates()

        # Modifying one shouldn't affect the other
        templates1["NewTemplate"] = self.template_b
        self.assertNotIn("NewTemplate", templates2)

    # ==================== Category Tests ====================

    def test_get_templates_by_category(self):
        """Test getting templates by category."""
        PhysicsSceneFactory.register_template("TemplateA", self.template_a)
        PhysicsSceneFactory.register_template("TemplateB", self.template_b)
        PhysicsSceneFactory.register_template("TemplateC", self.template_c)

        category_a_templates = PhysicsSceneFactory.get_templates_by_category("CategoryA")
        self.assertEqual(len(category_a_templates), 2)
        self.assertIn("TemplateA", category_a_templates)
        self.assertIn("TemplateC", category_a_templates)

        category_b_templates = PhysicsSceneFactory.get_templates_by_category("CategoryB")
        self.assertEqual(len(category_b_templates), 1)
        self.assertIn("TemplateB", category_b_templates)

    def test_get_templates_by_nonexistent_category(self):
        """Test getting templates from non-existent category."""
        PhysicsSceneFactory.register_template("Template", self.template_a)

        templates = PhysicsSceneFactory.get_templates_by_category("NonExistent")
        self.assertEqual(len(templates), 0)

    def test_get_categories(self):
        """Test getting all unique categories."""
        PhysicsSceneFactory.register_template("TemplateA", self.template_a)
        PhysicsSceneFactory.register_template("TemplateB", self.template_b)
        PhysicsSceneFactory.register_template("TemplateC", self.template_c)

        categories = PhysicsSceneFactory.get_categories()
        self.assertEqual(len(categories), 2)
        self.assertIn("CategoryA", categories)
        self.assertIn("CategoryB", categories)

    def test_get_categories_empty(self):
        """Test getting categories when no templates registered."""
        categories = PhysicsSceneFactory.get_categories()
        self.assertEqual(len(categories), 0)

    def test_get_categories_sorted(self):
        """Test that categories are returned sorted."""
        template_z = PhysicsSceneTemplate(
            name="Z Template",
            body_class=MockPhysicsBody,
            category="ZCategory"
        )
        template_a = PhysicsSceneTemplate(
            name="A Template",
            body_class=MockPhysicsBody,
            category="ACategory"
        )

        PhysicsSceneFactory.register_template("Z", template_z)
        PhysicsSceneFactory.register_template("A", template_a)

        categories = PhysicsSceneFactory.get_categories()
        self.assertEqual(categories, ["ACategory", "ZCategory"])

    # ==================== Create From Template Tests ====================

    def test_create_from_template_success(self):
        """Test creating a body from a registered template."""
        template = PhysicsSceneTemplate(
            name="Test",
            body_class=MockPhysicsBody,
            default_kwargs={"name": "Created Body", "x": 100.0}
        )
        PhysicsSceneFactory.register_template("Test", template)

        body = PhysicsSceneFactory.create_from_template("Test")

        self.assertIsInstance(body, MockPhysicsBody)
        self.assertEqual(body.name, "Created Body")  # type: ignore
        self.assertEqual(body.x, 100.0)  # type: ignore

    def test_create_from_template_with_overrides(self):
        """Test creating a body with override kwargs."""
        template = PhysicsSceneTemplate(
            name="Test",
            body_class=MockPhysicsBody,
            default_kwargs={"name": "Default", "x": 50.0}
        )
        PhysicsSceneFactory.register_template("Test", template)

        body = PhysicsSceneFactory.create_from_template(
            "Test",
            name="Overridden",
            y=200.0
        )

        self.assertEqual(body.name, "Overridden")  # type: ignore
        self.assertEqual(body.x, 50.0)  # From defaults  # type: ignore
        self.assertEqual(body.y, 200.0)  # Overridden  # type: ignore

    def test_create_from_nonexistent_template(self):
        """Test creating from a template that doesn't exist."""
        body = PhysicsSceneFactory.create_from_template("NonExistent")
        self.assertIsNone(body)

    def test_create_from_template_error_handling(self):
        """Test error handling when template creation fails."""
        def failing_factory(**kwargs):
            raise ValueError("Intentional error")

        template = PhysicsSceneTemplate(
            name="Failing",
            body_class=MockPhysicsBody,
            factory_func=failing_factory
        )
        PhysicsSceneFactory.register_template("Failing", template)

        body = PhysicsSceneFactory.create_from_template("Failing")
        self.assertIsNone(body)

    # ==================== Integration Tests ====================

    def test_workflow_register_create_unregister(self):
        """Test complete workflow: register, create, unregister."""
        # Register
        PhysicsSceneFactory.register_template("Workflow", self.template_a)
        self.assertIsNotNone(PhysicsSceneFactory.get_template("Workflow"))

        # Create
        body = PhysicsSceneFactory.create_from_template("Workflow", x=123.0)
        self.assertIsInstance(body, MockPhysicsBody)
        self.assertEqual(body.x, 123.0)  # type: ignore

        # Unregister
        result = PhysicsSceneFactory.unregister_template("Workflow")
        self.assertTrue(result)
        self.assertIsNone(PhysicsSceneFactory.get_template("Workflow"))

    def test_multiple_templates_different_categories(self):
        """Test managing multiple templates with different categories."""
        PhysicsSceneFactory.register_template("A1", self.template_a)
        PhysicsSceneFactory.register_template("A2", self.template_c)
        PhysicsSceneFactory.register_template("B1", self.template_b)

        # Test category filtering
        cat_a = PhysicsSceneFactory.get_templates_by_category("CategoryA")
        cat_b = PhysicsSceneFactory.get_templates_by_category("CategoryB")

        self.assertEqual(len(cat_a), 2)
        self.assertEqual(len(cat_b), 1)

        # Test all templates
        all_templates = PhysicsSceneFactory.get_all_templates()
        self.assertEqual(len(all_templates), 3)

        # Test categories list
        categories = PhysicsSceneFactory.get_categories()
        self.assertEqual(set(categories), {"CategoryA", "CategoryB"})


class TestPhysicsSceneFactoryWithRealBodies(unittest.TestCase):
    """Test factory with real physics body classes."""

    def setUp(self):
        """Set up test fixtures."""
        # Save existing templates before each test
        self._saved_templates = PhysicsSceneFactory._templates.copy()
        
        # Clear templates for isolated test environment
        PhysicsSceneFactory._templates.clear()

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original templates after each test
        PhysicsSceneFactory._templates.clear()
        PhysicsSceneFactory._templates.update(self._saved_templates)

    def test_create_base_physics_body(self):
        """Test creating a BasePhysicsBody from template."""
        template = PhysicsSceneTemplate(
            name="Base Body",
            body_class=BasePhysicsBody,
            default_kwargs={
                "name": "Test Base",
                "x": 100.0,
                "y": 200.0,
                "width": 50.0,
                "height": 30.0,
                "mass": 10.0,
            }
        )

        PhysicsSceneFactory.register_template("Base", template)
        body = PhysicsSceneFactory.create_from_template("Base")

        self.assertIsInstance(body, BasePhysicsBody)
        self.assertEqual(body.name, "Test Base")  # type: ignore
        self.assertEqual(body.x, 100.0)  # type: ignore
        self.assertEqual(body.y, 200.0)  # type: ignore
        self.assertEqual(body.width, 50.0)  # type: ignore
        self.assertEqual(body.height, 30.0)  # type: ignore
        self.assertEqual(body.mass, 10.0)  # type: ignore

    def test_create_with_material(self):
        """Test creating body with material properties."""
        material = Material(
            density=2.0,
            restitution=0.5,
            friction=0.8,
            drag=0.1
        )

        template = PhysicsSceneTemplate(
            name="Material Body",
            body_class=BasePhysicsBody,
            default_kwargs={
                "material": material,
                "mass": 5.0
            }
        )

        PhysicsSceneFactory.register_template("Material", template)
        body = PhysicsSceneFactory.create_from_template("Material")

        self.assertEqual(body.material.density, 2.0)  # type: ignore
        self.assertEqual(body.material.restitution, 0.5)  # type: ignore
        self.assertEqual(body.material.friction, 0.8)  # type: ignore
        self.assertEqual(body.material.drag, 0.1)  # type: ignore


if __name__ == '__main__':
    unittest.main()

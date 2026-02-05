"""Unit tests for ui_panel.py module.

Tests the UIPanelBody and UIButtonBody classes for creating
non-colliding interactive UI elements in the scene.
"""
import unittest

from pyrox.models.physics.ui_panel import UIPanelBody, UIButtonBody
from pyrox.models.physics.factory import PhysicsSceneFactory
from pyrox.interfaces import (
    BodyType,
    ColliderType,
    CollisionLayer,
)
from pyrox.models.protocols.physics import Material


class TestUIPanelBody(unittest.TestCase):
    """Test cases for UIPanelBody class."""

    def setUp(self):
        """Set up test fixtures."""
        self.default_panel = UIPanelBody()

        self.custom_panel = UIPanelBody(
            name="Control Panel",
            x=100.0,
            y=200.0,
            width=150.0,
            height=100.0,
            interactive=True,
            panel_type="control"
        )

        self.non_interactive_panel = UIPanelBody(
            name="Display Panel",
            interactive=False,
            panel_type="display"
        )

    # ==================== Initialization Tests ====================

    def test_default_initialization(self):
        """Test default initialization creates valid UI panel."""
        panel = UIPanelBody()

        self.assertEqual(panel.name, "UI Panel")
        self.assertEqual(panel.x, 0.0)
        self.assertEqual(panel.y, 0.0)
        self.assertEqual(panel.width, 100.0)
        self.assertEqual(panel.height, 50.0)
        self.assertTrue(panel.interactive)
        self.assertEqual(panel.panel_type, "panel")

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        self.assertEqual(self.custom_panel.name, "Control Panel")
        self.assertEqual(self.custom_panel.x, 100.0)
        self.assertEqual(self.custom_panel.y, 200.0)
        self.assertEqual(self.custom_panel.width, 150.0)
        self.assertEqual(self.custom_panel.height, 100.0)
        self.assertTrue(self.custom_panel.interactive)
        self.assertEqual(self.custom_panel.panel_type, "control")

    def test_initialization_with_custom_material(self):
        """Test initialization with custom material."""
        custom_material = Material(
            density=1.0,
            restitution=0.5,
            friction=0.8,
            drag=0.2
        )

        panel = UIPanelBody(
            name="Custom Material Panel",
            material=custom_material
        )

        self.assertEqual(panel.material.density, 1.0)
        self.assertEqual(panel.material.restitution, 0.5)
        self.assertEqual(panel.material.friction, 0.8)
        self.assertEqual(panel.material.drag, 0.2)

    def test_default_material_properties(self):
        """Test that default material has zero physics properties."""
        panel = UIPanelBody()

        self.assertEqual(panel.material.density, 0.0)
        self.assertEqual(panel.material.restitution, 0.0)
        self.assertEqual(panel.material.friction, 0.0)
        self.assertEqual(panel.material.drag, 0.0)

    # ==================== Physics Properties Tests ====================

    def test_body_type_is_static(self):
        """Test that UI panel is always STATIC."""
        self.assertEqual(self.default_panel.body_type, BodyType.STATIC)
        self.assertEqual(self.custom_panel.body_type, BodyType.STATIC)

    def test_collision_layer_is_ui(self):
        """Test that UI panel uses UI collision layer."""
        self.assertEqual(self.default_panel.collider.collision_layer, CollisionLayer.UI)
        self.assertEqual(self.custom_panel.collider.collision_layer, CollisionLayer.UI)

    def test_collision_mask_is_empty(self):
        """Test that UI panel has empty collision mask."""
        self.assertEqual(self.default_panel.collider.collision_mask, [])
        self.assertEqual(self.custom_panel.collider.collision_mask, [])

    def test_is_not_trigger(self):
        """Test that UI panel is not a trigger."""
        self.assertFalse(self.default_panel.collider.is_trigger)
        self.assertFalse(self.custom_panel.collider.is_trigger)

    def test_mass_is_zero(self):
        """Test that UI panel has zero mass."""
        self.assertEqual(self.default_panel.mass, 0.0)
        self.assertEqual(self.custom_panel.mass, 0.0)

    def test_collider_type_is_rectangle(self):
        """Test that UI panel uses rectangle collider."""
        self.assertEqual(self.default_panel.collider.collider_type, ColliderType.RECTANGLE)
        self.assertEqual(self.custom_panel.collider.collider_type, ColliderType.RECTANGLE)

    def test_is_enabled(self):
        """Test that UI panel is enabled by default."""
        self.assertTrue(self.default_panel.enabled)
        self.assertTrue(self.custom_panel.enabled)

    def test_not_sleeping(self):
        """Test that UI panel is not sleeping by default."""
        self.assertFalse(self.default_panel.sleeping)
        self.assertFalse(self.custom_panel.sleeping)

    # ==================== Tag Tests ====================

    def test_has_ui_tag(self):
        """Test that UI panel has 'ui' tag."""
        self.assertTrue(self.default_panel.has_tag("ui"))
        self.assertTrue(self.custom_panel.has_tag("ui"))

    def test_has_panel_type_tag(self):
        """Test that UI panel has panel_type tag."""
        self.assertTrue(self.default_panel.has_tag("panel"))
        self.assertTrue(self.custom_panel.has_tag("control"))
        self.assertTrue(self.non_interactive_panel.has_tag("display"))

    def test_tags_contain_both_ui_and_type(self):
        """Test that tags contain both 'ui' and panel_type."""
        tags = self.custom_panel.tags
        self.assertIn("ui", tags)
        self.assertIn("control", tags)
        self.assertEqual(len(tags), 2)

    # ==================== Interactive Tests ====================

    def test_is_interactive_default(self):
        """Test that panel is interactive by default."""
        self.assertTrue(self.default_panel.is_interactive())

    def test_is_interactive_custom(self):
        """Test custom interactive setting."""
        self.assertTrue(self.custom_panel.is_interactive())
        self.assertFalse(self.non_interactive_panel.is_interactive())

    def test_set_interactive_true(self):
        """Test setting panel to interactive."""
        panel = UIPanelBody(interactive=False)
        self.assertFalse(panel.is_interactive())

        panel.set_interactive(True)
        self.assertTrue(panel.is_interactive())

    def test_set_interactive_false(self):
        """Test setting panel to non-interactive."""
        panel = UIPanelBody(interactive=True)
        self.assertTrue(panel.is_interactive())

        panel.set_interactive(False)
        self.assertFalse(panel.is_interactive())

    def test_interactive_attribute_direct_access(self):
        """Test direct access to interactive attribute."""
        self.assertTrue(self.default_panel.interactive)
        self.assertFalse(self.non_interactive_panel.interactive)

    # ==================== Panel Type Tests ====================

    def test_panel_type_default(self):
        """Test default panel type."""
        self.assertEqual(self.default_panel.panel_type, "panel")

    def test_panel_type_custom(self):
        """Test custom panel types."""
        self.assertEqual(self.custom_panel.panel_type, "control")
        self.assertEqual(self.non_interactive_panel.panel_type, "display")

    def test_panel_type_attribute(self):
        """Test panel_type is accessible as attribute."""
        panel = UIPanelBody(panel_type="custom_type")
        self.assertEqual(panel.panel_type, "custom_type")

    # ==================== Position and Size Tests ====================

    def test_position_default(self):
        """Test default position."""
        self.assertEqual(self.default_panel.x, 0.0)
        self.assertEqual(self.default_panel.y, 0.0)

    def test_position_custom(self):
        """Test custom position."""
        self.assertEqual(self.custom_panel.x, 100.0)
        self.assertEqual(self.custom_panel.y, 200.0)

    def test_size_default(self):
        """Test default size."""
        self.assertEqual(self.default_panel.width, 100.0)
        self.assertEqual(self.default_panel.height, 50.0)

    def test_size_custom(self):
        """Test custom size."""
        self.assertEqual(self.custom_panel.width, 150.0)
        self.assertEqual(self.custom_panel.height, 100.0)


class TestUIButtonBody(unittest.TestCase):
    """Test cases for UIButtonBody class."""

    def setUp(self):
        """Set up test fixtures."""
        self.default_button = UIButtonBody()

        self.custom_button = UIButtonBody(
            name="Start Button",
            x=50.0,
            y=75.0,
            width=100.0,
            height=40.0,
            toggle=False,
            enabled=True
        )

        self.toggle_button = UIButtonBody(
            name="Power Button",
            toggle=True,
            enabled=True
        )

        self.disabled_button = UIButtonBody(
            name="Disabled Button",
            enabled=False
        )

    # ==================== Initialization Tests ====================

    def test_default_initialization(self):
        """Test default initialization creates valid button."""
        button = UIButtonBody()

        self.assertEqual(button.name, "UI Button")
        self.assertEqual(button.x, 0.0)
        self.assertEqual(button.y, 0.0)
        self.assertEqual(button.width, 80.0)
        self.assertEqual(button.height, 30.0)
        self.assertFalse(button._toggle)
        self.assertTrue(button._enabled)
        self.assertFalse(button._pressed)

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        self.assertEqual(self.custom_button.name, "Start Button")
        self.assertEqual(self.custom_button.x, 50.0)
        self.assertEqual(self.custom_button.y, 75.0)
        self.assertEqual(self.custom_button.width, 100.0)
        self.assertEqual(self.custom_button.height, 40.0)
        self.assertFalse(self.custom_button._toggle)
        self.assertTrue(self.custom_button._enabled)

    def test_toggle_button_initialization(self):
        """Test toggle button initialization."""
        self.assertTrue(self.toggle_button._toggle)
        self.assertTrue(self.toggle_button._enabled)
        self.assertFalse(self.toggle_button._pressed)

    def test_disabled_button_initialization(self):
        """Test disabled button initialization."""
        self.assertFalse(self.disabled_button._enabled)
        self.assertFalse(self.disabled_button.interactive)

    # ==================== Inheritance Tests ====================

    def test_inherits_from_ui_panel(self):
        """Test that button inherits from UIPanelBody."""
        self.assertIsInstance(self.default_button, UIPanelBody)

    def test_has_ui_panel_properties(self):
        """Test that button has UI panel properties."""
        self.assertEqual(self.default_button.body_type, BodyType.STATIC)
        self.assertEqual(self.default_button.collider.collision_layer, CollisionLayer.UI)
        self.assertEqual(self.default_button.collider.collision_mask, [])
        self.assertEqual(self.default_button.mass, 0.0)

    def test_panel_type_is_button(self):
        """Test that button panel_type is 'button'."""
        self.assertEqual(self.default_button.panel_type, "button")
        self.assertEqual(self.custom_button.panel_type, "button")
        self.assertEqual(self.toggle_button.panel_type, "button")

    def test_has_button_tag(self):
        """Test that button has 'button' tag."""
        self.assertTrue(self.default_button.has_tag("button"))
        self.assertTrue(self.default_button.has_tag("ui"))

    # ==================== Pressed State Tests ====================

    def test_pressed_property_default(self):
        """Test pressed property defaults to False."""
        self.assertFalse(self.default_button.pressed)

    def test_pressed_property_readonly(self):
        """Test that pressed property is read-only."""
        # Should use setter method, not direct assignment
        self.assertFalse(self.default_button.pressed)

    def test_set_pressed_true(self):
        """Test setting button to pressed."""
        button = UIButtonBody(enabled=True)
        button.set_pressed(True)
        self.assertTrue(button.pressed)

    def test_set_pressed_false(self):
        """Test setting button to released."""
        button = UIButtonBody(enabled=True)
        button.set_pressed(True)
        button.set_pressed(False)
        self.assertFalse(button.pressed)

    def test_set_pressed_when_disabled(self):
        """Test that disabled button cannot be pressed."""
        button = UIButtonBody(enabled=False)
        button.set_pressed(True)
        self.assertFalse(button.pressed)  # Should remain unpressed

    # ==================== Press/Release Tests ====================

    def test_press_momentary_button(self):
        """Test pressing a momentary button."""
        button = UIButtonBody(toggle=False, enabled=True)
        button.press()
        self.assertTrue(button.pressed)

    def test_release_momentary_button(self):
        """Test releasing a momentary button."""
        button = UIButtonBody(toggle=False, enabled=True)
        button.press()
        self.assertTrue(button.pressed)

        button.release()
        self.assertFalse(button.pressed)

    def test_press_toggle_button_first_time(self):
        """Test pressing toggle button first time."""
        button = UIButtonBody(toggle=True, enabled=True)
        self.assertFalse(button.pressed)

        button.press()
        self.assertTrue(button.pressed)

    def test_press_toggle_button_second_time(self):
        """Test pressing toggle button second time."""
        button = UIButtonBody(toggle=True, enabled=True)

        button.press()  # First press
        self.assertTrue(button.pressed)

        button.press()  # Second press
        self.assertFalse(button.pressed)

    def test_release_toggle_button_does_nothing(self):
        """Test that release() doesn't affect toggle buttons."""
        button = UIButtonBody(toggle=True, enabled=True)

        button.press()
        self.assertTrue(button.pressed)

        button.release()
        self.assertTrue(button.pressed)  # Should remain pressed

    def test_press_disabled_button(self):
        """Test pressing disabled button has no effect."""
        button = UIButtonBody(enabled=False)
        button.press()
        self.assertFalse(button.pressed)

    def test_release_disabled_button(self):
        """Test releasing disabled button has no effect."""
        button = UIButtonBody(enabled=False)
        button._pressed = True  # Manually set to test
        button.release()
        self.assertTrue(button._pressed)  # Should remain as is

    # ==================== Toggle Tests ====================

    def test_toggle_pressed_when_enabled_and_toggle_mode(self):
        """Test toggling when enabled and in toggle mode."""
        button = UIButtonBody(toggle=True, enabled=True)

        button.toggle_pressed()
        self.assertTrue(button.pressed)

        button.toggle_pressed()
        self.assertFalse(button.pressed)

    def test_toggle_pressed_when_not_toggle_mode(self):
        """Test toggle_pressed does nothing when not in toggle mode."""
        button = UIButtonBody(toggle=False, enabled=True)

        button.toggle_pressed()
        self.assertFalse(button.pressed)  # Should not change

    def test_toggle_pressed_when_disabled(self):
        """Test toggle_pressed does nothing when disabled."""
        button = UIButtonBody(toggle=True, enabled=False)

        button.toggle_pressed()
        self.assertFalse(button.pressed)  # Should not change

    def test_is_toggle_true(self):
        """Test is_toggle returns True for toggle buttons."""
        self.assertTrue(self.toggle_button.is_toggle())

    def test_is_toggle_false(self):
        """Test is_toggle returns False for momentary buttons."""
        self.assertFalse(self.custom_button.is_toggle())
        self.assertFalse(self.default_button.is_toggle())

    # ==================== Enable/Disable Tests ====================

    def test_is_enabled_default(self):
        """Test button is enabled by default."""
        self.assertTrue(self.default_button.is_enabled())

    def test_is_enabled_custom(self):
        """Test custom enabled state."""
        self.assertTrue(self.custom_button.is_enabled())
        self.assertFalse(self.disabled_button.is_enabled())

    def test_set_enabled_true(self):
        """Test enabling a button."""
        button = UIButtonBody(enabled=False)
        self.assertFalse(button.is_enabled())

        button.set_enabled(True)
        self.assertTrue(button.is_enabled())
        self.assertTrue(button.is_interactive())

    def test_set_enabled_false(self):
        """Test disabling a button."""
        button = UIButtonBody(enabled=True)
        self.assertTrue(button.is_enabled())

        button.set_enabled(False)
        self.assertFalse(button.is_enabled())
        self.assertFalse(button.is_interactive())

    def test_set_enabled_syncs_with_interactive(self):
        """Test that enabled state syncs with interactive."""
        button = UIButtonBody(enabled=True)

        button.set_enabled(False)
        self.assertFalse(button.is_interactive())

        button.set_enabled(True)
        self.assertTrue(button.is_interactive())

    def test_disabling_prevents_pressing(self):
        """Test that disabled button cannot be pressed."""
        button = UIButtonBody(enabled=True)
        button.set_enabled(False)

        button.press()
        self.assertFalse(button.pressed)

    def test_disabling_while_pressed(self):
        """Test disabling a button while it's pressed."""
        button = UIButtonBody(enabled=True)
        button.press()
        self.assertTrue(button.pressed)

        button.set_enabled(False)
        # Button remains pressed but can't be changed
        self.assertTrue(button.pressed)

        button.set_pressed(False)
        self.assertTrue(button.pressed)  # Can't change when disabled

    # ==================== Integration Tests ====================

    def test_momentary_button_workflow(self):
        """Test complete workflow for momentary button."""
        button = UIButtonBody(name="Test", toggle=False, enabled=True)

        # Initial state
        self.assertFalse(button.pressed)

        # Press
        button.press()
        self.assertTrue(button.pressed)

        # Release
        button.release()
        self.assertFalse(button.pressed)

        # Press again
        button.press()
        self.assertTrue(button.pressed)

    def test_toggle_button_workflow(self):
        """Test complete workflow for toggle button."""
        button = UIButtonBody(name="Power", toggle=True, enabled=True)

        # Initial state
        self.assertFalse(button.pressed)

        # First click
        button.press()
        self.assertTrue(button.pressed)

        # Second click
        button.press()
        self.assertFalse(button.pressed)

        # Third click
        button.press()
        self.assertTrue(button.pressed)

    def test_disable_enable_workflow(self):
        """Test disabling and re-enabling button."""
        button = UIButtonBody(enabled=True)

        # Press while enabled
        button.press()
        self.assertTrue(button.pressed)

        # Disable
        button.set_enabled(False)
        self.assertFalse(button.is_enabled())

        # Try to release while disabled
        button.release()
        self.assertTrue(button.pressed)  # Remains pressed

        # Re-enable
        button.set_enabled(True)

        # Now can release
        button.release()
        self.assertFalse(button.pressed)


class TestPhysicsSceneFactoryRegistration(unittest.TestCase):
    """Test that UI panel templates are registered in the factory."""

    def test_ui_panel_template_registered(self):
        """Test that UI Panel template is registered."""
        template = PhysicsSceneFactory.get_template("UI Panel")
        self.assertIsNotNone(template)
        self.assertEqual(template.name, "UI Panel")  # type: ignore
        self.assertEqual(template.body_class, UIPanelBody)  # type: ignore
        self.assertEqual(template.category, "UI")  # type: ignore

    def test_ui_button_template_registered(self):
        """Test that UI Button template is registered."""
        template = PhysicsSceneFactory.get_template("UI Button")
        self.assertIsNotNone(template)
        self.assertEqual(template.name, "UI Button")  # type: ignore
        self.assertEqual(template.body_class, UIButtonBody)  # type: ignore
        self.assertEqual(template.category, "UI")  # type: ignore

    def test_create_ui_panel_from_template(self):
        """Test creating UI panel from factory template."""
        panel = PhysicsSceneFactory.create_from_template(
            "UI Panel",
            name="Test Panel",
            x=100.0,
            y=200.0
        )

        self.assertIsInstance(panel, UIPanelBody)
        self.assertEqual(panel.name, "Test Panel")  # type: ignore
        self.assertEqual(panel.x, 100.0)  # type: ignore
        self.assertEqual(panel.y, 200.0)  # type: ignore
        self.assertEqual(panel.width, 100.0)  # From defaults  # type: ignore
        self.assertEqual(panel.height, 50.0)  # From defaults  # type: ignore

    def test_create_ui_button_from_template(self):
        """Test creating UI button from factory template."""
        button = PhysicsSceneFactory.create_from_template(
            "UI Button",
            name="Test Button",
            x=50.0,
            y=75.0
        )

        self.assertIsInstance(button, UIButtonBody)
        self.assertEqual(button.name, "Test Button")  # type: ignore
        self.assertEqual(button.x, 50.0)  # type: ignore
        self.assertEqual(button.y, 75.0)  # type: ignore
        self.assertEqual(button.width, 80.0)  # From defaults  # type: ignore
        self.assertEqual(button.height, 30.0)  # From defaults  # type: ignore
        self.assertFalse(button._toggle)  # From defaults  # type: ignore
        self.assertTrue(button._enabled)  # From defaults  # type: ignore

    def test_ui_templates_in_ui_category(self):
        """Test that UI templates are in UI category."""
        ui_templates = PhysicsSceneFactory.get_templates_by_category("UI")

        self.assertIn("UI Panel", ui_templates)
        self.assertIn("UI Button", ui_templates)

    def test_ui_category_exists(self):
        """Test that UI category exists in categories list."""
        categories = PhysicsSceneFactory.get_categories()
        self.assertIn("UI", categories)


if __name__ == '__main__':
    unittest.main()

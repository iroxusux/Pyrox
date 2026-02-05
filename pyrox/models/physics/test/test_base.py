"""Unit tests for base.py module.

Tests the BasePhysicsBody class and its functionality including
tag management, spatial queries, and physics body integration.
"""
import unittest

from pyrox.models.physics.base import BasePhysicsBody
from pyrox.models.protocols.physics import Material, PhysicsBody2D
from pyrox.interfaces import (
    BodyType,
    ColliderType,
    CollisionLayer,
    IPhysicsBody2D,
)


class TestBasePhysicsBody(unittest.TestCase):
    """Test cases for BasePhysicsBody class."""

    def setUp(self):
        """Set up test fixtures."""
        self.default_body = BasePhysicsBody()

        self.custom_body = BasePhysicsBody(
            name="Test Body",
            tags=["test", "physics"],
            x=100.0,
            y=200.0,
            width=50.0,
            height=30.0,
            mass=10.0,
            body_type=BodyType.DYNAMIC
        )

    def tearDown(self):
        """Clean up test fixtures."""
        # self.default_body = None
        # self.custom_body = None

    # ==================== Initialization Tests ====================

    def test_default_initialization(self):
        """Test default initialization creates valid body."""
        body = BasePhysicsBody()

        self.assertEqual(body.name, "")
        self.assertEqual(body.tags, [])
        self.assertEqual(body.body_type, BodyType.DYNAMIC)
        self.assertEqual(body.x, 0.0)
        self.assertEqual(body.y, 0.0)
        self.assertEqual(body.width, 10.0)
        self.assertEqual(body.height, 10.0)
        self.assertEqual(body.mass, 1.0)
        self.assertTrue(body.enabled)
        self.assertFalse(body.sleeping)

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        body = BasePhysicsBody(
            name="Custom Body",
            tags=["custom", "test"],
            x=150.0,
            y=250.0,
            width=100.0,
            height=75.0,
            mass=25.0,
            body_type=BodyType.STATIC,
            velocity_x=10.0,
            velocity_y=-5.0
        )

        self.assertEqual(body.name, "Custom Body")
        self.assertEqual(body.tags, ["custom", "test"])
        self.assertEqual(body.x, 150.0)
        self.assertEqual(body.y, 250.0)
        self.assertEqual(body.width, 100.0)
        self.assertEqual(body.height, 75.0)
        self.assertEqual(body.mass, 25.0)
        self.assertEqual(body.body_type, BodyType.STATIC)
        self.assertEqual(body.velocity_x, 10.0)
        self.assertEqual(body.velocity_y, -5.0)

    def test_initialization_with_material(self):
        """Test initialization with custom material."""
        material = Material(
            density=2.0,
            restitution=0.8,
            friction=0.3,
            drag=0.05
        )

        body = BasePhysicsBody(material=material)

        self.assertAlmostEqual(body.material.density, 2.0)
        self.assertAlmostEqual(body.material.restitution, 0.8)
        self.assertAlmostEqual(body.material.friction, 0.3)
        self.assertAlmostEqual(body.material.drag, 0.05)

    def test_initialization_with_collision_settings(self):
        """Test initialization with collision layer and mask."""
        collision_mask = [CollisionLayer.TERRAIN, CollisionLayer.PLAYER]

        body = BasePhysicsBody(
            collision_layer=CollisionLayer.ENEMY,
            collision_mask=collision_mask,
            collider_type=ColliderType.CIRCLE,
            is_trigger=True
        )

        self.assertEqual(body.collision_layer, CollisionLayer.ENEMY)
        self.assertEqual(body.collider.collision_mask, collision_mask)
        self.assertEqual(body.collider.collider_type, ColliderType.CIRCLE)
        self.assertTrue(body.collider.is_trigger)

    def test_inheritance_from_physics_body_2d(self):
        """Test that BasePhysicsBody properly inherits from PhysicsBody2D."""
        body = BasePhysicsBody()

        self.assertIsInstance(body, PhysicsBody2D)
        self.assertIsInstance(body, IPhysicsBody2D)

    # ==================== Tag Management Tests ====================

    def test_has_tag_with_existing_tag(self):
        """Test has_tag returns True for existing tags."""
        self.assertTrue(self.custom_body.has_tag("test"))
        self.assertTrue(self.custom_body.has_tag("physics"))

    def test_has_tag_with_nonexistent_tag(self):
        """Test has_tag returns False for nonexistent tags."""
        self.assertFalse(self.custom_body.has_tag("nonexistent"))
        self.assertFalse(self.custom_body.has_tag(""))

    def test_has_tag_on_empty_tags(self):
        """Test has_tag on body with no tags."""
        self.assertFalse(self.default_body.has_tag("any"))

    def test_add_tag_new_tag(self):
        """Test adding a new tag."""
        self.default_body.add_tag("new_tag")

        self.assertTrue(self.default_body.has_tag("new_tag"))
        self.assertIn("new_tag", self.default_body.tags)

    def test_add_tag_duplicate(self):
        """Test adding duplicate tag doesn't create duplicates."""
        self.custom_body.add_tag("test")

        tag_count = self.custom_body.tags.count("test")
        self.assertEqual(tag_count, 1)

    def test_add_multiple_tags(self):
        """Test adding multiple different tags."""
        body = BasePhysicsBody()

        body.add_tag("tag1")
        body.add_tag("tag2")
        body.add_tag("tag3")

        self.assertEqual(len(body.tags), 3)
        self.assertTrue(body.has_tag("tag1"))
        self.assertTrue(body.has_tag("tag2"))
        self.assertTrue(body.has_tag("tag3"))

    def test_remove_tag_existing(self):
        """Test removing an existing tag."""
        self.custom_body.remove_tag("test")

        self.assertFalse(self.custom_body.has_tag("test"))
        self.assertNotIn("test", self.custom_body.tags)

    def test_remove_tag_nonexistent(self):
        """Test removing nonexistent tag doesn't raise error."""
        try:
            self.custom_body.remove_tag("nonexistent")
        except Exception as e:
            self.fail(f"remove_tag raised exception: {e}")

    def test_remove_all_tags(self):
        """Test removing all tags."""
        self.custom_body.remove_tag("test")
        self.custom_body.remove_tag("physics")

        self.assertEqual(len(self.custom_body.tags), 0)

    # ==================== Spatial Query Tests ====================

    def test_is_on_top_of_true(self):
        """Test is_on_top_of returns True when body is on top."""
        # Body on top at y=100, height=20 (bottom at y=120)
        top_body = BasePhysicsBody(
            x=100.0,
            y=100.0,
            width=50.0,
            height=20.0
        )

        # Body below at y=120, height=20 (top at y=120)
        bottom_body = BasePhysicsBody(
            x=100.0,
            y=120.0,
            width=50.0,
            height=20.0
        )

        self.assertTrue(top_body.is_on_top_of(bottom_body))

    def test_is_on_top_of_false_no_horizontal_overlap(self):
        """Test is_on_top_of returns False when no horizontal overlap."""
        # Bodies at same height but no X overlap
        body1 = BasePhysicsBody(x=0.0, y=100.0, width=50.0, height=20.0)
        body2 = BasePhysicsBody(x=100.0, y=120.0, width=50.0, height=20.0)

        self.assertFalse(body1.is_on_top_of(body2))

    def test_is_on_top_of_false_too_far_vertically(self):
        """Test is_on_top_of returns False when vertically separated."""
        body1 = BasePhysicsBody(x=100.0, y=50.0, width=50.0, height=20.0)
        body2 = BasePhysicsBody(x=100.0, y=100.0, width=50.0, height=20.0)

        # body1 bottom is at y=70, body2 top is at y=100
        # Difference is 30, which is > tolerance
        self.assertFalse(body1.is_on_top_of(body2))

    def test_is_on_top_of_partial_horizontal_overlap(self):
        """Test is_on_top_of with partial horizontal overlap."""
        # Partial overlap in X direction
        top_body = BasePhysicsBody(x=100.0, y=100.0, width=50.0, height=20.0)
        bottom_body = BasePhysicsBody(x=125.0, y=120.0, width=50.0, height=20.0)

        # Should still detect "on top" if there's any X overlap
        self.assertTrue(top_body.is_on_top_of(bottom_body))

    def test_is_on_top_of_different_sizes(self):
        """Test is_on_top_of with different body sizes."""
        # Small body on large platform
        small_body = BasePhysicsBody(x=110.0, y=100.0, width=10.0, height=10.0)
        large_body = BasePhysicsBody(x=100.0, y=110.0, width=100.0, height=20.0)

        self.assertTrue(small_body.is_on_top_of(large_body))

    def test_is_on_top_of_edge_alignment(self):
        """Test is_on_top_of with exact edge alignment."""
        # Bodies aligned at their edges
        body1 = BasePhysicsBody(x=100.0, y=100.0, width=50.0, height=20.0)
        body2 = BasePhysicsBody(x=100.0, y=120.0, width=50.0, height=20.0)

        # Exact alignment should work
        self.assertTrue(body1.is_on_top_of(body2))

    # ==================== Integration Tests ====================

    def test_physics_properties_accessible(self):
        """Test that physics properties from parent class are accessible."""
        body = self.custom_body

        # Test position properties
        self.assertEqual(body.x, 100.0)
        self.assertEqual(body.y, 200.0)

        # Test size properties
        self.assertEqual(body.width, 50.0)
        self.assertEqual(body.height, 30.0)

        # Test physics properties
        self.assertEqual(body.mass, 10.0)
        self.assertEqual(body.body_type, BodyType.DYNAMIC)

    def test_get_bounds(self):
        """Test get_bounds returns correct bounding box."""
        body = BasePhysicsBody(x=100.0, y=200.0, width=50.0, height=30.0)

        min_x, min_y, max_x, max_y = body.get_bounds()

        self.assertEqual(min_x, 100.0)
        self.assertEqual(min_y, 200.0)
        self.assertEqual(max_x, 150.0)  # x + width
        self.assertEqual(max_y, 230.0)  # y + height

    def test_velocity_properties(self):
        """Test velocity can be set and retrieved."""
        body = BasePhysicsBody(velocity_x=10.0, velocity_y=-5.0)

        self.assertEqual(body.velocity_x, 10.0)
        self.assertEqual(body.velocity_y, -5.0)

        # Test setting velocity
        body.linear_velocity = (20.0, -10.0)
        self.assertEqual(body.velocity_x, 20.0)
        self.assertEqual(body.velocity_y, -10.0)

    def test_collision_callbacks_exist(self):
        """Test that collision callback methods exist."""
        body = BasePhysicsBody()

        self.assertTrue(hasattr(body, 'on_collision_enter'))
        self.assertTrue(hasattr(body, 'on_collision_stay'))
        self.assertTrue(hasattr(body, 'on_collision_exit'))
        self.assertTrue(hasattr(body, 'update'))

    def test_body_type_modification(self):
        """Test changing body type."""
        body = BasePhysicsBody(body_type=BodyType.DYNAMIC)
        self.assertEqual(body.body_type, BodyType.DYNAMIC)

        body.body_type = BodyType.STATIC
        self.assertEqual(body.body_type, BodyType.STATIC)

    def test_enabled_flag(self):
        """Test enabled flag controls physics simulation."""
        body = BasePhysicsBody(enabled=True)
        self.assertTrue(body.enabled)

        body.enabled = False
        self.assertFalse(body.enabled)

    def test_sleeping_flag(self):
        """Test sleeping flag for optimization."""
        body = BasePhysicsBody(sleeping=False)
        self.assertFalse(body.sleeping)

        body.sleeping = True
        self.assertTrue(body.sleeping)

    # ==================== String Representation Tests ====================

    def test_repr_with_name(self):
        """Test __repr__ includes name when set."""
        body = BasePhysicsBody(
            name="Named Body",
            x=10.0,
            y=20.0,
            width=30.0,
            height=40.0
        )

        repr_str = repr(body)

        self.assertIn("Named Body", repr_str)
        self.assertIn("BasePhysicsBody", repr_str)
        self.assertIn("10.0", repr_str)
        self.assertIn("20.0", repr_str)
        self.assertIn("30.0", repr_str)
        self.assertIn("40.0", repr_str)

    def test_repr_without_name(self):
        """Test __repr__ without name."""
        body = BasePhysicsBody(x=5.0, y=10.0, width=15.0, height=20.0)

        repr_str = repr(body)

        self.assertIn("BasePhysicsBody", repr_str)
        self.assertIn("5.0", repr_str)
        self.assertIn("10.0", repr_str)
        self.assertIn("15.0", repr_str)
        self.assertIn("20.0", repr_str)
        self.assertNotIn("''", repr_str)  # Empty name shouldn't show

    def test_repr_includes_body_type(self):
        """Test __repr__ includes body type."""
        dynamic_body = BasePhysicsBody(body_type=BodyType.DYNAMIC)
        static_body = BasePhysicsBody(body_type=BodyType.STATIC)

        self.assertIn("DYNAMIC", repr(dynamic_body))
        self.assertIn("STATIC", repr(static_body))

    # ==================== Edge Case Tests ====================

    def test_zero_size_body(self):
        """Test body with zero size."""
        body = BasePhysicsBody(width=0.0, height=0.0)

        self.assertEqual(body.width, 0.0)
        self.assertEqual(body.height, 0.0)

        min_x, min_y, max_x, max_y = body.get_bounds()
        self.assertEqual(min_x, max_x)
        self.assertEqual(min_y, max_y)

    def test_negative_position(self):
        """Test body at negative position."""
        body = BasePhysicsBody(x=-100.0, y=-200.0)

        self.assertEqual(body.x, -100.0)
        self.assertEqual(body.y, -200.0)

    def test_large_values(self):
        """Test body with very large values."""
        body = BasePhysicsBody(
            x=1_000_000.0,
            y=2_000_000.0,
            width=10_000.0,
            height=20_000.0,
            mass=100_000.0
        )

        self.assertEqual(body.x, 1_000_000.0)
        self.assertEqual(body.mass, 100_000.0)

    def test_empty_tag_list(self):
        """Test operations on empty tag list."""
        body = BasePhysicsBody()

        self.assertEqual(len(body.tags), 0)
        self.assertFalse(body.has_tag("any"))

        # Should not raise
        body.remove_tag("nonexistent")

    def test_many_tags(self):
        """Test body with many tags."""
        tags = [f"tag_{i}" for i in range(100)]
        body = BasePhysicsBody(tags=tags)

        self.assertEqual(len(body.tags), 100)
        self.assertTrue(body.has_tag("tag_50"))

        body.remove_tag("tag_50")
        self.assertFalse(body.has_tag("tag_50"))
        self.assertEqual(len(body.tags), 99)

    def test_special_characters_in_name(self):
        """Test name with special characters."""
        body = BasePhysicsBody(name="Body #1 (Test) - Special!")

        self.assertEqual(body.name, "Body #1 (Test) - Special!")
        self.assertIn("Body #1 (Test) - Special!", repr(body))

    def test_unicode_in_tags(self):
        """Test tags with unicode characters."""
        body = BasePhysicsBody(tags=["测试", "тест", "🚀"])

        self.assertTrue(body.has_tag("测试"))
        self.assertTrue(body.has_tag("тест"))
        self.assertTrue(body.has_tag("🚀"))


class TestBasePhysicsBodyFactory(unittest.TestCase):
    """Test the factory registration for BasePhysicsBody."""

    def test_factory_registration(self):
        """Test that BasePhysicsBody is registered in the factory."""
        from pyrox.models.physics.factory import PhysicsSceneFactory

        template = PhysicsSceneFactory.get_template("Base Physics Body")

        self.assertIsNotNone(template)
        self.assertEqual(template.name, "Base Physics Body")  # type: ignore
        self.assertEqual(template.body_class, BasePhysicsBody)  # type: ignore

    def test_create_from_factory(self):
        """Test creating BasePhysicsBody from factory."""
        from pyrox.models.physics.factory import PhysicsSceneFactory

        body = PhysicsSceneFactory.create_from_template(
            "Base Physics Body",
            x=50.0,
            y=75.0,
            name="Factory Body"
        )

        self.assertIsNotNone(body)
        self.assertIsInstance(body, BasePhysicsBody)
        self.assertEqual(body.x, 50.0)  # type: ignore
        self.assertEqual(body.y, 75.0)  # type: ignore
        self.assertEqual(body.name, "Factory Body")  # type: ignore


if __name__ == '__main__':
    unittest.main()

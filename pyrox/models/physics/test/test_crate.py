"""Unit tests for crate.py module.

Tests the CrateBody class and its functionality including
material types, factory methods, collision behavior, and moment of inertia calculations.
"""
import unittest
from unittest.mock import Mock

from pyrox.models.physics.crate import CrateBody
from pyrox.models.physics.base import BasePhysicsBody
from pyrox.models.protocols.physics import Material
from pyrox.interfaces import (
    BodyType,
    ColliderType,
    CollisionLayer,
    IPhysicsBody2D,
)


class TestCrateBody(unittest.TestCase):
    """Test cases for CrateBody class."""

    def setUp(self):
        """Set up test fixtures."""
        self.default_crate = CrateBody()

        self.custom_crate = CrateBody(
            name="Test Crate",
            x=100.0,
            y=200.0,
            width=30.0,
            height=40.0,
            mass=25.0,
            crate_type="metal"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.default_crate = None
        self.custom_crate = None

    # ==================== Initialization Tests ====================

    def test_default_initialization(self):
        """Test default initialization creates valid crate."""
        crate = CrateBody()

        self.assertEqual(crate.name, "Crate")
        self.assertEqual(crate.x, 0.0)
        self.assertEqual(crate.y, 0.0)
        self.assertEqual(crate.width, 20.0)
        self.assertEqual(crate.height, 20.0)
        self.assertEqual(crate.mass, 10.0)
        self.assertEqual(crate.crate_type, "wooden")
        self.assertEqual(crate.body_type, BodyType.DYNAMIC)

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        crate = CrateBody(
            name="Custom Crate",
            x=50.0,
            y=100.0,
            width=30.0,
            height=40.0,
            mass=25.0,
            crate_type="metal"
        )

        self.assertEqual(crate.name, "Custom Crate")
        self.assertEqual(crate.x, 50.0)
        self.assertEqual(crate.y, 100.0)
        self.assertEqual(crate.width, 30.0)
        self.assertEqual(crate.height, 40.0)
        self.assertEqual(crate.mass, 25.0)
        self.assertEqual(crate.crate_type, "metal")

    def test_initialization_with_custom_material(self):
        """Test initialization with custom material."""
        material = Material(
            density=1.5,
            restitution=0.8,
            friction=0.2,
            drag=0.05
        )

        crate = CrateBody(material=material)

        self.assertAlmostEqual(crate.material.density, 1.5)
        self.assertAlmostEqual(crate.material.restitution, 0.8)
        self.assertAlmostEqual(crate.material.friction, 0.2)
        self.assertAlmostEqual(crate.material.drag, 0.05)

    def test_dynamic_body_type(self):
        """Test that crates are always DYNAMIC bodies."""
        crate = CrateBody()

        self.assertEqual(crate.body_type, BodyType.DYNAMIC)

    def test_rectangle_collider_type(self):
        """Test that crates use RECTANGLE collider."""
        crate = CrateBody()

        self.assertEqual(crate.collider.collider_type, ColliderType.RECTANGLE)

    def test_default_collision_layer(self):
        """Test default collision layer is DEFAULT."""
        crate = CrateBody()

        self.assertEqual(crate.collider.collision_layer, CollisionLayer.DEFAULT)

    def test_default_collision_mask(self):
        """Test default collision mask includes common layers."""
        crate = CrateBody()

        mask = crate.collider.collision_mask
        self.assertIn(CollisionLayer.DEFAULT, mask)
        self.assertIn(CollisionLayer.TERRAIN, mask)
        self.assertIn(CollisionLayer.PLAYER, mask)
        self.assertIn(CollisionLayer.ENEMY, mask)

    def test_custom_collision_mask(self):
        """Test initialization with custom collision mask."""
        custom_mask = [CollisionLayer.PLAYER, CollisionLayer.PROJECTILE]
        crate = CrateBody(collision_mask=custom_mask)

        self.assertEqual(crate.collider.collision_mask, custom_mask)

    def test_custom_collision_layer(self):
        """Test initialization with custom collision layer."""
        crate = CrateBody(collision_layer=CollisionLayer.PLAYER)

        self.assertEqual(crate.collider.collision_layer, CollisionLayer.PLAYER)

    def test_not_trigger(self):
        """Test that crates are not triggers by default."""
        crate = CrateBody()

        self.assertFalse(crate.collider.is_trigger)

    def test_enabled_by_default(self):
        """Test that crates are enabled by default."""
        crate = CrateBody()

        self.assertTrue(crate.enabled)

    def test_not_sleeping_by_default(self):
        """Test that crates are not sleeping by default."""
        crate = CrateBody()

        self.assertFalse(crate.sleeping)

    def test_automatic_tags(self):
        """Test crate automatically has crate and type tags."""
        crate = CrateBody(crate_type="metal")

        self.assertTrue(crate.has_tag("crate"))
        self.assertTrue(crate.has_tag("metal"))

    def test_inheritance_from_base_physics_body(self):
        """Test that CrateBody inherits from BasePhysicsBody."""
        crate = CrateBody()

        self.assertIsInstance(crate, BasePhysicsBody)
        self.assertIsInstance(crate, IPhysicsBody2D)

    # ==================== Material Type Tests ====================

    def test_wooden_material_properties(self):
        """Test wooden crate has correct material properties."""
        crate = CrateBody(crate_type="wooden")

        self.assertAlmostEqual(crate.material.density, 0.6)
        self.assertAlmostEqual(crate.material.restitution, 0.3)
        self.assertAlmostEqual(crate.material.friction, 0.6)
        self.assertAlmostEqual(crate.material.drag, 0.1)

    def test_metal_material_properties(self):
        """Test metal crate has correct material properties."""
        crate = CrateBody(crate_type="metal")

        self.assertAlmostEqual(crate.material.density, 7.8)
        self.assertAlmostEqual(crate.material.restitution, 0.2)
        self.assertAlmostEqual(crate.material.friction, 0.4)
        self.assertAlmostEqual(crate.material.drag, 0.05)

    def test_cardboard_material_properties(self):
        """Test cardboard box has correct material properties."""
        crate = CrateBody(crate_type="cardboard")

        self.assertAlmostEqual(crate.material.density, 0.2)
        self.assertAlmostEqual(crate.material.restitution, 0.1)
        self.assertAlmostEqual(crate.material.friction, 0.7)
        self.assertAlmostEqual(crate.material.drag, 0.15)

    def test_plastic_material_properties(self):
        """Test plastic crate has correct material properties."""
        crate = CrateBody(crate_type="plastic")

        self.assertAlmostEqual(crate.material.density, 0.9)
        self.assertAlmostEqual(crate.material.restitution, 0.5)
        self.assertAlmostEqual(crate.material.friction, 0.3)
        self.assertAlmostEqual(crate.material.drag, 0.08)

    def test_unknown_type_defaults_to_wooden(self):
        """Test unknown crate type defaults to wooden material."""
        crate = CrateBody(crate_type="unknown_type")

        # Should default to wooden material
        self.assertAlmostEqual(crate.material.density, 0.6)
        self.assertAlmostEqual(crate.material.friction, 0.6)

    def test_material_ordering_by_density(self):
        """Test materials have expected density ordering."""
        cardboard = CrateBody(crate_type="cardboard")
        wooden = CrateBody(crate_type="wooden")
        plastic = CrateBody(crate_type="plastic")
        metal = CrateBody(crate_type="metal")

        # cardboard < wooden < plastic < metal
        self.assertLess(cardboard.material.density, wooden.material.density)
        self.assertLess(wooden.material.density, plastic.material.density)
        self.assertLess(plastic.material.density, metal.material.density)

    def test_material_affects_physics_behavior(self):
        """Test that different materials have different friction/restitution."""
        wooden = CrateBody(crate_type="wooden")
        metal = CrateBody(crate_type="metal")

        # Different materials should have different properties
        self.assertNotEqual(wooden.material.friction, metal.material.friction)
        self.assertNotEqual(wooden.material.restitution, metal.material.restitution)

    # ==================== Moment of Inertia Tests ====================

    def test_moment_of_inertia_calculation(self):
        """Test moment of inertia is calculated correctly."""
        crate = CrateBody(width=20.0, height=20.0, mass=10.0)

        # I = (1/12) * m * (w² + h²)
        expected = (1.0 / 12.0) * 10.0 * (20.0 * 20.0 + 20.0 * 20.0)

        self.assertAlmostEqual(crate.moment_of_inertia, expected, places=4)

    def test_moment_of_inertia_with_different_dimensions(self):
        """Test moment of inertia for non-square crate."""
        crate = CrateBody(width=30.0, height=40.0, mass=25.0)

        # I = (1/12) * m * (w² + h²)
        expected = (1.0 / 12.0) * 25.0 * (30.0 * 30.0 + 40.0 * 40.0)

        self.assertAlmostEqual(crate.moment_of_inertia, expected, places=4)

    def test_moment_of_inertia_increases_with_mass(self):
        """Test heavier crates have higher moment of inertia."""
        light = CrateBody(width=20.0, height=20.0, mass=5.0)
        heavy = CrateBody(width=20.0, height=20.0, mass=50.0)

        self.assertLess(light.moment_of_inertia, heavy.moment_of_inertia)

    def test_moment_of_inertia_increases_with_size(self):
        """Test larger crates have higher moment of inertia."""
        small = CrateBody(width=10.0, height=10.0, mass=10.0)
        large = CrateBody(width=40.0, height=40.0, mass=10.0)

        self.assertLess(small.moment_of_inertia, large.moment_of_inertia)

    def test_moment_of_inertia_zero_mass(self):
        """Test moment of inertia with zero mass."""
        crate = CrateBody(mass=0.0)

        self.assertEqual(crate.moment_of_inertia, 0.0)

    # ==================== Factory Method Tests ====================

    def test_create_wooden_factory_method(self):
        """Test create_wooden factory method."""
        crate = CrateBody.create_wooden()

        self.assertEqual(crate.name, "Wooden Crate")
        self.assertEqual(crate.crate_type, "wooden")
        self.assertEqual(crate.mass, 10.0)
        self.assertIsInstance(crate, CrateBody)

    def test_create_metal_factory_method(self):
        """Test create_metal factory method."""
        crate = CrateBody.create_metal()

        self.assertEqual(crate.name, "Metal Crate")
        self.assertEqual(crate.crate_type, "metal")
        self.assertEqual(crate.mass, 50.0)
        self.assertIsInstance(crate, CrateBody)

    def test_create_cardboard_factory_method(self):
        """Test create_cardboard factory method."""
        crate = CrateBody.create_cardboard()

        self.assertEqual(crate.name, "Cardboard Box")
        self.assertEqual(crate.crate_type, "cardboard")
        self.assertEqual(crate.mass, 2.0)
        self.assertIsInstance(crate, CrateBody)

    def test_factory_method_with_custom_name(self):
        """Test factory methods accept custom name."""
        crate = CrateBody.create_wooden(name="My Custom Box")

        self.assertEqual(crate.name, "My Custom Box")
        self.assertEqual(crate.crate_type, "wooden")

    def test_factory_method_with_kwargs(self):
        """Test factory methods accept additional kwargs."""
        crate = CrateBody.create_metal(
            name="Heavy Box",
            x=100.0,
            y=200.0,
            width=50.0,
            height=50.0
        )

        self.assertEqual(crate.name, "Heavy Box")
        self.assertEqual(crate.x, 100.0)
        self.assertEqual(crate.y, 200.0)
        self.assertEqual(crate.width, 50.0)
        self.assertEqual(crate.height, 50.0)
        self.assertEqual(crate.mass, 50.0)  # Default for metal

    def test_factory_methods_preserve_material_properties(self):
        """Test factory methods create crates with correct materials."""
        wooden = CrateBody.create_wooden()
        metal = CrateBody.create_metal()
        cardboard = CrateBody.create_cardboard()

        self.assertAlmostEqual(wooden.material.density, 0.6)
        self.assertAlmostEqual(metal.material.density, 7.8)
        self.assertAlmostEqual(cardboard.material.density, 0.2)

    def test_factory_methods_mass_ordering(self):
        """Test factory methods create crates with expected mass ordering."""
        cardboard = CrateBody.create_cardboard()
        wooden = CrateBody.create_wooden()
        metal = CrateBody.create_metal()

        # cardboard < wooden < metal
        self.assertLess(cardboard.mass, wooden.mass)
        self.assertLess(wooden.mass, metal.mass)

    # ==================== Collision Callback Tests ====================

    def test_on_collision_enter_does_not_error(self):
        """Test on_collision_enter can be called without error."""
        crate = CrateBody()
        mock_other = Mock(spec=IPhysicsBody2D)

        try:
            crate.on_collision_enter(mock_other)
        except Exception as e:
            self.fail(f"on_collision_enter raised exception: {e}")

    def test_on_collision_stay_does_not_error(self):
        """Test on_collision_stay can be called without error."""
        crate = CrateBody()
        mock_other = Mock(spec=IPhysicsBody2D)

        try:
            crate.on_collision_stay(mock_other)
        except Exception as e:
            self.fail(f"on_collision_stay raised exception: {e}")

    def test_on_collision_exit_does_not_error(self):
        """Test on_collision_exit can be called without error."""
        crate = CrateBody()
        mock_other = Mock(spec=IPhysicsBody2D)

        try:
            crate.on_collision_exit(mock_other)
        except Exception as e:
            self.fail(f"on_collision_exit raised exception: {e}")

    def test_collision_callbacks_with_multiple_calls(self):
        """Test collision callbacks can be called multiple times."""
        crate = CrateBody()
        mock_other = Mock(spec=IPhysicsBody2D)

        try:
            crate.on_collision_enter(mock_other)
            crate.on_collision_stay(mock_other)
            crate.on_collision_stay(mock_other)
            crate.on_collision_exit(mock_other)
        except Exception as e:
            self.fail(f"Collision callbacks raised exception: {e}")

    # ==================== Update Method Tests ====================

    def test_update_does_not_error(self):
        """Test update method can be called without error."""
        crate = CrateBody()

        try:
            crate.update(0.016)  # ~60 FPS
        except Exception as e:
            self.fail(f"update raised exception: {e}")

    def test_update_with_zero_dt(self):
        """Test update with zero delta time."""
        crate = CrateBody()

        try:
            crate.update(0.0)
        except Exception as e:
            self.fail(f"update raised exception: {e}")

    def test_update_with_large_dt(self):
        """Test update with large delta time."""
        crate = CrateBody()

        try:
            crate.update(1.0)
        except Exception as e:
            self.fail(f"update raised exception: {e}")

    def test_update_multiple_times(self):
        """Test update can be called multiple times."""
        crate = CrateBody()

        try:
            for _ in range(100):
                crate.update(0.016)
        except Exception as e:
            self.fail(f"Multiple updates raised exception: {e}")

    # ==================== String Representation Tests ====================

    def test_repr_contains_name(self):
        """Test __repr__ contains crate name."""
        crate = CrateBody(name="Test Box")

        repr_str = repr(crate)

        self.assertIn("Test Box", repr_str)

    def test_repr_contains_type(self):
        """Test __repr__ contains crate type."""
        crate = CrateBody(crate_type="metal")

        repr_str = repr(crate)

        self.assertIn("metal", repr_str)

    def test_repr_contains_mass(self):
        """Test __repr__ contains mass."""
        crate = CrateBody(mass=25.0)

        repr_str = repr(crate)

        self.assertIn("25.0", repr_str)
        self.assertIn("kg", repr_str)

    def test_repr_contains_position(self):
        """Test __repr__ contains position."""
        crate = CrateBody(x=100.0, y=200.0)

        repr_str = repr(crate)

        self.assertIn("100.0", repr_str)
        self.assertIn("200.0", repr_str)

    def test_repr_contains_size(self):
        """Test __repr__ contains size."""
        crate = CrateBody(width=30.0, height=40.0)

        repr_str = repr(crate)

        self.assertIn("30.0", repr_str)
        self.assertIn("40.0", repr_str)

    def test_repr_format(self):
        """Test __repr__ follows expected format."""
        crate = CrateBody(
            name="Box",
            crate_type="wooden",
            mass=10.0,
            x=50.0,
            y=100.0,
            width=20.0,
            height=20.0
        )

        repr_str = repr(crate)

        self.assertTrue(repr_str.startswith("<CrateBody"))
        self.assertTrue(repr_str.endswith(">"))

    # ==================== Edge Case Tests ====================

    def test_zero_mass_crate(self):
        """Test crate with zero mass."""
        crate = CrateBody(mass=0.0)

        self.assertEqual(crate.mass, 0.0)
        self.assertEqual(crate.moment_of_inertia, 0.0)

    def test_very_large_mass(self):
        """Test crate with very large mass."""
        crate = CrateBody(mass=10000.0)

        self.assertEqual(crate.mass, 10000.0)
        self.assertGreater(crate.moment_of_inertia, 0.0)

    def test_very_small_dimensions(self):
        """Test crate with very small dimensions."""
        crate = CrateBody(width=0.1, height=0.1)

        self.assertEqual(crate.width, 0.1)
        self.assertEqual(crate.height, 0.1)

    def test_very_large_dimensions(self):
        """Test crate with very large dimensions."""
        crate = CrateBody(width=1000.0, height=1000.0)

        self.assertEqual(crate.width, 1000.0)
        self.assertEqual(crate.height, 1000.0)

    def test_negative_position(self):
        """Test crate at negative position."""
        crate = CrateBody(x=-100.0, y=-200.0)

        self.assertEqual(crate.x, -100.0)
        self.assertEqual(crate.y, -200.0)

    def test_non_square_crate(self):
        """Test non-square crate dimensions."""
        crate = CrateBody(width=10.0, height=50.0)

        self.assertEqual(crate.width, 10.0)
        self.assertEqual(crate.height, 50.0)
        self.assertNotEqual(crate.width, crate.height)

    def test_empty_name(self):
        """Test crate with empty name."""
        crate = CrateBody(name="")

        self.assertEqual(crate.name, "")

    def test_long_name(self):
        """Test crate with very long name."""
        long_name = "A" * 1000
        crate = CrateBody(name=long_name)

        self.assertEqual(crate.name, long_name)

    def test_special_characters_in_name(self):
        """Test crate with special characters in name."""
        crate = CrateBody(name="Crate#1@Test!")

        self.assertEqual(crate.name, "Crate#1@Test!")

    def test_unicode_in_name(self):
        """Test crate with unicode characters in name."""
        crate = CrateBody(name="箱子")

        self.assertEqual(crate.name, "箱子")


class TestCrateBodyFactory(unittest.TestCase):
    """Test the factory registration for CrateBody."""

    def test_factory_registration(self):
        """Test that CrateBody is registered in the factory."""
        from pyrox.models.physics.factory import PhysicsSceneFactory

        template = PhysicsSceneFactory.get_template("Crate")

        self.assertIsNotNone(template)
        self.assertEqual(template.name, "Crate")  # type: ignore
        self.assertEqual(template.body_class, CrateBody)  # type: ignore
        self.assertEqual(template.category, "Objects")  # type: ignore

    def test_create_from_factory(self):
        """Test creating CrateBody from factory."""
        from pyrox.models.physics.factory import PhysicsSceneFactory

        crate = PhysicsSceneFactory.create_from_template(
            "Crate",
            x=150.0,
            y=250.0,
            name="Factory Crate"
        )

        self.assertIsNotNone(crate)
        self.assertIsInstance(crate, CrateBody)
        self.assertEqual(crate.x, 150.0)  # type: ignore
        self.assertEqual(crate.y, 250.0)  # type: ignore
        self.assertEqual(crate.name, "Factory Crate")  # type: ignore

    def test_factory_default_parameters(self):
        """Test factory template uses correct defaults."""
        from pyrox.models.physics.factory import PhysicsSceneFactory

        template = PhysicsSceneFactory.get_template("Crate")

        self.assertEqual(template.default_kwargs['width'], 20.0)  # type: ignore
        self.assertEqual(template.default_kwargs['height'], 20.0)  # type: ignore
        self.assertEqual(template.default_kwargs['mass'], 10.0)  # type: ignore
        self.assertEqual(template.default_kwargs['crate_type'], "wooden")  # type: ignore

    def test_factory_creates_wooden_by_default(self):
        """Test factory creates wooden crate by default."""
        from pyrox.models.physics.factory import PhysicsSceneFactory

        crate = PhysicsSceneFactory.create_from_template("Crate")

        self.assertEqual(crate.crate_type, "wooden")  # type: ignore

    def test_factory_override_crate_type(self):
        """Test factory can override crate type."""
        from pyrox.models.physics.factory import PhysicsSceneFactory

        crate = PhysicsSceneFactory.create_from_template(
            "Crate",
            crate_type="metal"
        )

        self.assertEqual(crate.crate_type, "metal")  # type: ignore


class TestCrateMaterialComparison(unittest.TestCase):
    """Test comparisons between different crate materials."""

    def test_metal_heavier_than_wooden(self):
        """Test metal crate is heavier than wooden."""
        wooden = CrateBody.create_wooden(width=20.0, height=20.0)
        metal = CrateBody.create_metal(width=20.0, height=20.0)

        self.assertGreater(metal.mass, wooden.mass)

    def test_cardboard_lighter_than_wooden(self):
        """Test cardboard box is lighter than wooden crate."""
        cardboard = CrateBody.create_cardboard(width=20.0, height=20.0)
        wooden = CrateBody.create_wooden(width=20.0, height=20.0)

        self.assertLess(cardboard.mass, wooden.mass)

    def test_plastic_more_bouncy_than_metal(self):
        """Test plastic has higher restitution than metal."""
        plastic = CrateBody(crate_type="plastic")
        metal = CrateBody(crate_type="metal")

        self.assertGreater(plastic.material.restitution, metal.material.restitution)

    def test_cardboard_highest_friction(self):
        """Test cardboard has highest friction."""
        cardboard = CrateBody(crate_type="cardboard")
        wooden = CrateBody(crate_type="wooden")
        metal = CrateBody(crate_type="metal")
        plastic = CrateBody(crate_type="plastic")

        self.assertGreater(cardboard.material.friction, wooden.material.friction)
        self.assertGreater(cardboard.material.friction, metal.material.friction)
        self.assertGreater(cardboard.material.friction, plastic.material.friction)

    def test_metal_lowest_drag(self):
        """Test metal has lowest drag."""
        metal = CrateBody(crate_type="metal")
        wooden = CrateBody(crate_type="wooden")
        cardboard = CrateBody(crate_type="cardboard")

        self.assertLess(metal.material.drag, wooden.material.drag)
        self.assertLess(metal.material.drag, cardboard.material.drag)


if __name__ == '__main__':
    unittest.main()

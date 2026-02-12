"""Unit tests for conveyor.py module.

Tests the ConveyorBody class and its functionality including
belt velocity, direction control, object tracking, and collision behavior.
"""
import unittest
from unittest.mock import Mock, patch

from pyrox.models.physics.conveyor import ConveyorBody, Direction
from pyrox.models.physics.base import BasePhysicsBody
from pyrox.models.protocols.physics import Material
from pyrox.interfaces import (
    BodyType,
    CollisionLayer,
    IPhysicsBody2D,
)


class TestDirection(unittest.TestCase):
    """Test cases for Direction enum."""

    def test_direction_enum_values(self):
        """Test Direction enum has correct values."""
        self.assertEqual(Direction.NORTH.value, "north")
        self.assertEqual(Direction.SOUTH.value, "south")
        self.assertEqual(Direction.EAST.value, "east")
        self.assertEqual(Direction.WEST.value, "west")

    def test_direction_from_str(self):
        """Test Direction.from_str converts strings correctly."""
        self.assertEqual(Direction.from_str("north"), Direction.NORTH)
        self.assertEqual(Direction.from_str("south"), Direction.SOUTH)
        self.assertEqual(Direction.from_str("east"), Direction.EAST)
        self.assertEqual(Direction.from_str("west"), Direction.WEST)

    def test_direction_from_str_case_insensitive(self):
        """Test Direction.from_str is case-insensitive."""
        self.assertEqual(Direction.from_str("NORTH"), Direction.NORTH)
        self.assertEqual(Direction.from_str("South"), Direction.SOUTH)
        self.assertEqual(Direction.from_str("EaSt"), Direction.EAST)

    def test_direction_from_str_invalid(self):
        """Test Direction.from_str raises error for invalid direction."""
        with self.assertRaises(ValueError):
            Direction.from_str("invalid")

    def test_direction_get_velocity_vector_north(self):
        """Test get_velocity_vector for NORTH."""
        vx, vy = Direction.NORTH.get_velocity_vector(50.0)
        self.assertEqual(vx, 0.0)
        self.assertEqual(vy, -50.0)

    def test_direction_get_velocity_vector_south(self):
        """Test get_velocity_vector for SOUTH."""
        vx, vy = Direction.SOUTH.get_velocity_vector(50.0)
        self.assertEqual(vx, 0.0)
        self.assertEqual(vy, 50.0)

    def test_direction_get_velocity_vector_east(self):
        """Test get_velocity_vector for EAST."""
        vx, vy = Direction.EAST.get_velocity_vector(50.0)
        self.assertEqual(vx, 50.0)
        self.assertEqual(vy, 0.0)

    def test_direction_get_velocity_vector_west(self):
        """Test get_velocity_vector for WEST."""
        vx, vy = Direction.WEST.get_velocity_vector(50.0)
        self.assertEqual(vx, -50.0)
        self.assertEqual(vy, 0.0)

    def test_direction_get_velocity_vector_with_zero_speed(self):
        """Test get_velocity_vector with zero speed."""
        vx, vy = Direction.EAST.get_velocity_vector(0.0)
        self.assertEqual(vx, 0.0)
        self.assertEqual(vy, 0.0)


class TestConveyorBody(unittest.TestCase):
    """Test cases for ConveyorBody class."""

    def setUp(self):
        """Set up test fixtures."""
        self.default_conveyor = ConveyorBody()

        self.custom_conveyor = ConveyorBody(
            name="Test Conveyor",
            x=100.0,
            y=200.0,
            width=300.0,
            height=25.0,
            direction=Direction.EAST,
            belt_speed=75.0,
            is_active=True
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.default_conveyor = None
        self.custom_conveyor = None

    # ==================== Initialization Tests ====================

    def test_default_initialization(self):
        """Test default initialization creates valid conveyor."""
        conveyor = ConveyorBody()

        self.assertEqual(conveyor.name, "Conveyor")
        self.assertEqual(conveyor.x, 0.0)
        self.assertEqual(conveyor.y, 0.0)
        self.assertEqual(conveyor.width, 100.0)
        self.assertEqual(conveyor.height, 20.0)
        self.assertEqual(conveyor.direction, Direction.EAST)
        self.assertEqual(conveyor.belt_speed, 50.0)
        self.assertTrue(conveyor.is_active)
        self.assertEqual(conveyor.body_type, BodyType.STATIC)

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        conveyor = ConveyorBody(
            name="Custom Belt",
            x=50.0,
            y=100.0,
            width=200.0,
            height=30.0,
            direction=Direction.WEST,
            belt_speed=100.0,
            is_active=False
        )

        self.assertEqual(conveyor.name, "Custom Belt")
        self.assertEqual(conveyor.x, 50.0)
        self.assertEqual(conveyor.y, 100.0)
        self.assertEqual(conveyor.width, 200.0)
        self.assertEqual(conveyor.height, 30.0)
        self.assertEqual(conveyor.direction, Direction.WEST)
        self.assertEqual(conveyor.belt_speed, 100.0)
        self.assertFalse(conveyor.is_active)

    def test_initialization_with_custom_material(self):
        """Test initialization with custom material."""
        material = Material(
            density=2.0,
            restitution=0.0,
            friction=1.0,
            drag=0.0
        )

        conveyor = ConveyorBody(material=material)

        self.assertAlmostEqual(conveyor.material.density, 2.0)
        self.assertAlmostEqual(conveyor.material.restitution, 0.0)
        self.assertAlmostEqual(conveyor.material.friction, 1.0)

    def test_default_material_properties(self):
        """Test default material has high friction for conveyors."""
        conveyor = ConveyorBody()

        # Should have high friction by default
        self.assertGreater(conveyor.material.friction, 0.8)
        # Should have low bounce
        self.assertLess(conveyor.material.restitution, 0.2)

    def test_default_collision_mask(self):
        """Test default collision mask includes common layers."""
        conveyor = ConveyorBody()

        mask = conveyor.collider.collision_mask
        self.assertIn(CollisionLayer.DEFAULT, mask)
        self.assertIn(CollisionLayer.PLAYER, mask)
        self.assertIn(CollisionLayer.ENEMY, mask)

    def test_custom_collision_mask(self):
        """Test initialization with custom collision mask."""
        custom_mask = [CollisionLayer.PLAYER, CollisionLayer.PROJECTILE]
        conveyor = ConveyorBody(collision_mask=custom_mask)

        self.assertEqual(conveyor.collider.collision_mask, custom_mask)

    def test_static_body_type_zero_mass(self):
        """Test that STATIC conveyors have zero mass."""
        conveyor = ConveyorBody(body_type=BodyType.STATIC)

        self.assertEqual(conveyor.mass, 0.0)

    def test_kinematic_body_type_has_mass(self):
        """Test that KINEMATIC conveyors have mass."""
        conveyor = ConveyorBody(body_type=BodyType.KINEMATIC)

        self.assertEqual(conveyor.mass, 100.0)

    def test_automatic_tags(self):
        """Test conveyor automatically has platform tags."""
        conveyor = ConveyorBody()

        self.assertTrue(conveyor.has_tag("conveyor"))
        self.assertTrue(conveyor.has_tag("platform"))

    def test_inheritance_from_base_physics_body(self):
        """Test that ConveyorBody inherits from BasePhysicsBody."""
        conveyor = ConveyorBody()

        self.assertIsInstance(conveyor, BasePhysicsBody)
        self.assertIsInstance(conveyor, IPhysicsBody2D)

    # ==================== Belt Velocity Tests ====================

    def test_belt_velocity_active_east(self):
        """Test belt_velocity when active and moving east."""
        conveyor = ConveyorBody(direction=Direction.EAST, belt_speed=50.0, is_active=True)

        vx, vy = conveyor.belt_velocity

        self.assertEqual(vx, 50.0)
        self.assertEqual(vy, 0.0)

    def test_belt_velocity_active_west(self):
        """Test belt_velocity when active and moving west."""
        conveyor = ConveyorBody(direction=Direction.WEST, belt_speed=50.0, is_active=True)

        vx, vy = conveyor.belt_velocity

        self.assertEqual(vx, -50.0)
        self.assertEqual(vy, 0.0)

    def test_belt_velocity_active_north(self):
        """Test belt_velocity when active and moving north."""
        conveyor = ConveyorBody(direction=Direction.NORTH, belt_speed=50.0, is_active=True)

        vx, vy = conveyor.belt_velocity

        self.assertEqual(vx, 0.0)
        self.assertEqual(vy, -50.0)

    def test_belt_velocity_active_south(self):
        """Test belt_velocity when active and moving south."""
        conveyor = ConveyorBody(direction=Direction.SOUTH, belt_speed=50.0, is_active=True)

        vx, vy = conveyor.belt_velocity

        self.assertEqual(vx, 0.0)
        self.assertEqual(vy, 50.0)

    def test_belt_velocity_inactive(self):
        """Test belt_velocity returns zero when inactive."""
        conveyor = ConveyorBody(belt_speed=100.0, is_active=False)

        vx, vy = conveyor.belt_velocity

        self.assertEqual(vx, 0.0)
        self.assertEqual(vy, 0.0)

    def test_belt_velocity_zero_speed(self):
        """Test belt_velocity with zero speed."""
        conveyor = ConveyorBody(belt_speed=0.0, is_active=True)

        vx, vy = conveyor.belt_velocity

        self.assertEqual(vx, 0.0)
        self.assertEqual(vy, 0.0)

    def test_belt_velocity_changes_with_speed(self):
        """Test belt_velocity updates when speed changes."""
        conveyor = ConveyorBody(direction=Direction.EAST, belt_speed=50.0, is_active=True)

        self.assertEqual(conveyor.belt_velocity[0], 50.0)

        conveyor.set_belt_speed(100.0)
        self.assertEqual(conveyor.belt_velocity[0], 100.0)

    def test_belt_velocity_changes_with_direction(self):
        """Test belt_velocity updates when direction changes."""
        conveyor = ConveyorBody(direction=Direction.EAST, belt_speed=50.0, is_active=True)

        self.assertEqual(conveyor.belt_velocity[0], 50.0)

        conveyor.set_direction(Direction.WEST)
        self.assertEqual(conveyor.belt_velocity[0], -50.0)

        conveyor.set_direction(Direction.NORTH)
        self.assertEqual(conveyor.belt_velocity[0], 0.0)
        self.assertEqual(conveyor.belt_velocity[1], -50.0)

    # ==================== Direction Control Tests ====================

    def test_set_direction_enum(self):
        """Test set_direction with Direction enum."""
        conveyor = ConveyorBody(direction=Direction.WEST)

        conveyor.set_direction(Direction.EAST)
        self.assertEqual(conveyor.direction, Direction.EAST)

        conveyor.set_direction(Direction.NORTH)
        self.assertEqual(conveyor.direction, Direction.NORTH)

    def test_set_direction_string(self):
        """Test set_direction with string values."""
        conveyor = ConveyorBody(direction=Direction.EAST)

        conveyor.set_direction("west")
        self.assertEqual(conveyor.direction, Direction.WEST)

        conveyor.set_direction("north")
        self.assertEqual(conveyor.direction, Direction.NORTH)

        conveyor.set_direction("south")
        self.assertEqual(conveyor.direction, Direction.SOUTH)

    def test_get_direction_returns_string(self):
        """Test get_direction returns string representation."""
        conveyor = ConveyorBody(direction=Direction.NORTH)

        self.assertEqual(conveyor.get_direction(), "north")

        conveyor.set_direction(Direction.WEST)
        self.assertEqual(conveyor.get_direction(), "west")

    def test_direction_string_case_insensitive(self):
        """Test direction accepts case-insensitive strings."""
        conveyor = ConveyorBody()

        conveyor.set_direction("NORTH")
        self.assertEqual(conveyor.direction, Direction.NORTH)

        conveyor.set_direction("SoUtH")
        self.assertEqual(conveyor.direction, Direction.SOUTH)

    # ==================== Speed Control Tests ====================

    def test_set_belt_speed_positive(self):
        """Test set_belt_speed with positive value."""
        conveyor = ConveyorBody(belt_speed=50.0)

        conveyor.set_belt_speed(100.0)
        self.assertEqual(conveyor.belt_speed, 100.0)

    def test_set_belt_speed_negative_becomes_positive(self):
        """Test set_belt_speed converts negative to positive."""
        conveyor = ConveyorBody(belt_speed=50.0)

        conveyor.set_belt_speed(-75.0)
        self.assertEqual(conveyor.belt_speed, 75.0)

    def test_set_belt_speed_zero(self):
        """Test set_belt_speed with zero."""
        conveyor = ConveyorBody(belt_speed=50.0)

        conveyor.set_belt_speed(0.0)
        self.assertEqual(conveyor.belt_speed, 0.0)

    def test_speed_always_positive(self):
        """Test speed is always stored as positive value."""
        conveyor = ConveyorBody()

        conveyor.set_belt_speed(-100.0)
        self.assertGreaterEqual(conveyor.belt_speed, 0.0)

    # ==================== Activation Control Tests ====================

    def test_toggle_from_active(self):
        """Test toggle switches from active to inactive."""
        conveyor = ConveyorBody(is_active=True)

        conveyor.toggle()
        self.assertFalse(conveyor.is_active)

    def test_toggle_from_inactive(self):
        """Test toggle switches from inactive to active."""
        conveyor = ConveyorBody(is_active=False)

        conveyor.toggle()
        self.assertTrue(conveyor.is_active)

    def test_toggle_multiple_times(self):
        """Test toggle switches state multiple times."""
        conveyor = ConveyorBody(is_active=True)

        conveyor.toggle()
        self.assertFalse(conveyor.is_active)

        conveyor.toggle()
        self.assertTrue(conveyor.is_active)

        conveyor.toggle()
        self.assertFalse(conveyor.is_active)

    def test_activate(self):
        """Test activate turns conveyor on."""
        conveyor = ConveyorBody(is_active=False)

        conveyor.activate()
        self.assertTrue(conveyor.is_active)

    def test_activate_when_already_active(self):
        """Test activate when already active."""
        conveyor = ConveyorBody(is_active=True)

        conveyor.activate()
        self.assertTrue(conveyor.is_active)

    def test_deactivate(self):
        """Test deactivate turns conveyor off."""
        conveyor = ConveyorBody(is_active=True)

        conveyor.deactivate()
        self.assertFalse(conveyor.is_active)

    def test_deactivate_when_already_inactive(self):
        """Test deactivate when already inactive."""
        conveyor = ConveyorBody(is_active=False)

        conveyor.deactivate()
        self.assertFalse(conveyor.is_active)

    # ==================== Object Tracking Tests ====================

    def test_initial_objects_on_belt_empty(self):
        """Test objects_on_belt is empty initially."""
        conveyor = ConveyorBody()

        objects = conveyor.get_objects_on_belt()

        self.assertEqual(len(objects), 0)
        self.assertIsInstance(objects, set)

    def test_get_objects_on_belt_returns_copy(self):
        """Test get_objects_on_belt returns a copy, not reference."""
        conveyor = ConveyorBody()

        objects1 = conveyor.get_objects_on_belt()
        objects2 = conveyor.get_objects_on_belt()

        self.assertIsNot(objects1, objects2)

    # ==================== Collision Callback Tests ====================

    def test_on_collision_enter_adds_object_on_top(self):
        """Test on_collision_enter adds object when on top."""
        conveyor = ConveyorBody(x=100.0, y=100.0, width=100.0, height=20.0)

        # Create mock object on top of conveyor
        mock_object = Mock(spec=IPhysicsBody2D)
        mock_object.body_type = BodyType.DYNAMIC
        mock_object.get_bounds.return_value = (110.0, 80.0, 130.0, 100.0)  # On top

        # Mock the is_on_top_of check
        with patch.object(conveyor, 'is_on_top_of', return_value=True):
            conveyor.on_collision_enter(mock_object)

        objects = conveyor.get_objects_on_belt()
        self.assertIn(mock_object, objects)

    def test_on_collision_stay_applies_velocity_when_active(self):
        """Test on_collision_stay applies belt velocity to dynamic object."""
        conveyor = ConveyorBody(
            x=100.0, y=100.0, width=100.0, height=20.0,
            direction=Direction.EAST, belt_speed=50.0, is_active=True
        )

        mock_object = Mock(spec=IPhysicsBody2D)
        mock_object.body_type = BodyType.DYNAMIC
        mock_object.linear_velocity = (0.0, -10.0)

        with patch.object(conveyor, 'is_on_top_of', return_value=True):
            conveyor.on_collision_stay(mock_object)

        # Should apply belt velocity (50.0, 0.0) but preserve Y velocity
        mock_object.set_linear_velocity.assert_called_once_with(50.0, -10.0)

    def test_on_collision_stay_does_nothing_when_inactive(self):
        """Test on_collision_stay doesn't apply velocity when inactive."""
        conveyor = ConveyorBody(is_active=False)

        mock_object = Mock(spec=IPhysicsBody2D)
        mock_object.body_type = BodyType.DYNAMIC

        conveyor.on_collision_stay(mock_object)

        # Should not call set_linear_velocity
        mock_object.set_linear_velocity.assert_not_called()

    def test_on_collision_stay_ignores_static_bodies(self):
        """Test on_collision_stay ignores static bodies."""
        conveyor = ConveyorBody(is_active=True)

        mock_object = Mock(spec=IPhysicsBody2D)
        mock_object.body_type = BodyType.STATIC

        conveyor.on_collision_stay(mock_object)

        mock_object.set_linear_velocity.assert_not_called()

    def test_on_collision_stay_ignores_kinematic_bodies(self):
        """Test on_collision_stay ignores kinematic bodies."""
        conveyor = ConveyorBody(is_active=True)

        mock_object = Mock(spec=IPhysicsBody2D)
        mock_object.body_type = BodyType.KINEMATIC

        conveyor.on_collision_stay(mock_object)

        mock_object.set_linear_velocity.assert_not_called()

    def test_on_collision_exit_removes_object(self):
        """Test on_collision_exit removes object from tracking."""
        conveyor = ConveyorBody()

        mock_object = Mock(spec=IPhysicsBody2D)

        # Add object first
        conveyor._objects_on_belt.add(mock_object)
        self.assertIn(mock_object, conveyor.get_objects_on_belt())

        # Exit collision
        conveyor.on_collision_exit(mock_object)

        objects = conveyor.get_objects_on_belt()
        self.assertNotIn(mock_object, objects)

    def test_on_collision_exit_handles_nonexistent_object(self):
        """Test on_collision_exit doesn't error if object not tracked."""
        conveyor = ConveyorBody()

        mock_object = Mock(spec=IPhysicsBody2D)

        # Try to remove object that was never added
        try:
            conveyor.on_collision_exit(mock_object)
        except Exception as e:
            self.fail(f"on_collision_exit raised exception: {e}")

    def test_multiple_objects_on_belt(self):
        """Test tracking multiple objects simultaneously."""
        conveyor = ConveyorBody(x=100.0, y=100.0, width=100.0, height=20.0)

        mock_obj1 = Mock(spec=IPhysicsBody2D)
        mock_obj2 = Mock(spec=IPhysicsBody2D)
        mock_obj3 = Mock(spec=IPhysicsBody2D)

        with patch.object(conveyor, 'is_on_top_of', return_value=True):
            conveyor.on_collision_enter(mock_obj1)
            conveyor.on_collision_enter(mock_obj2)
            conveyor.on_collision_enter(mock_obj3)

        objects = conveyor.get_objects_on_belt()
        self.assertEqual(len(objects), 3)

    # ==================== Update Method Tests ====================

    def test_update_does_not_error(self):
        """Test update method can be called without error."""
        conveyor = ConveyorBody()

        try:
            conveyor.update(0.016)  # ~60 FPS
        except Exception as e:
            self.fail(f"update raised exception: {e}")

    def test_update_with_zero_dt(self):
        """Test update with zero delta time."""
        conveyor = ConveyorBody()

        try:
            conveyor.update(0.0)
        except Exception as e:
            self.fail(f"update raised exception: {e}")

    def test_update_with_large_dt(self):
        """Test update with large delta time."""
        conveyor = ConveyorBody()

        try:
            conveyor.update(1.0)
        except Exception as e:
            self.fail(f"update raised exception: {e}")

    # ==================== String Representation Tests ====================

    def test_repr_active_east(self):
        """Test __repr__ for active conveyor moving east."""
        conveyor = ConveyorBody(
            name="Test Belt",
            x=50.0,
            y=100.0,
            width=200.0,
            height=30.0,
            direction=Direction.EAST,
            belt_speed=75.0,
            is_active=True
        )

        repr_str = repr(conveyor)

        self.assertIn("Test Belt", repr_str)
        self.assertIn("ACTIVE", repr_str)
        self.assertIn("→", repr_str)  # Right arrow
        self.assertIn("75.0", repr_str)
        self.assertIn("50.0", repr_str)
        self.assertIn("100.0", repr_str)

    def test_repr_inactive_west(self):
        """Test __repr__ for inactive conveyor moving west."""
        conveyor = ConveyorBody(
            name="Stopped Belt",
            direction=Direction.WEST,
            is_active=False
        )

        repr_str = repr(conveyor)

        self.assertIn("Stopped Belt", repr_str)
        self.assertIn("INACTIVE", repr_str)
        self.assertIn("←", repr_str)  # Left arrow

    def test_repr_north(self):
        """Test __repr__ for conveyor moving north."""
        conveyor = ConveyorBody(
            name="North Belt",
            direction=Direction.NORTH,
            is_active=True
        )

        repr_str = repr(conveyor)

        self.assertIn("North Belt", repr_str)
        self.assertIn("↑", repr_str)  # Up arrow

    def test_repr_south(self):
        """Test __repr__ for conveyor moving south."""
        conveyor = ConveyorBody(
            name="South Belt",
            direction=Direction.SOUTH,
            is_active=True
        )

        repr_str = repr(conveyor)

        self.assertIn("South Belt", repr_str)
        self.assertIn("↓", repr_str)  # Down arrow

    def test_repr_includes_object_count(self):
        """Test __repr__ includes number of objects on belt."""
        conveyor = ConveyorBody(name="Belt")

        # Add some mock objects
        for i in range(3):
            mock_obj = Mock(spec=IPhysicsBody2D)
            conveyor._objects_on_belt.add(mock_obj)

        repr_str = repr(conveyor)

        self.assertIn("objects=3", repr_str)

    def test_repr_zero_objects(self):
        """Test __repr__ with zero objects."""
        conveyor = ConveyorBody()

        repr_str = repr(conveyor)

        self.assertIn("objects=0", repr_str)

    # ==================== Edge Case Tests ====================

    def test_very_high_speed(self):
        """Test conveyor with very high speed."""
        conveyor = ConveyorBody(belt_speed=10000.0, is_active=True)

        vx, vy = conveyor.belt_velocity
        self.assertEqual(vx, 10000.0)

    def test_fractional_speed(self):
        """Test conveyor with fractional speed."""
        conveyor = ConveyorBody(belt_speed=0.5, is_active=True, direction=Direction.EAST)

        vx, vy = conveyor.belt_velocity
        self.assertEqual(vx, 0.5)

    def test_west_direction(self):
        """Test initialization with west direction."""
        conveyor = ConveyorBody(direction=Direction.WEST, belt_speed=50.0, is_active=True)

        vx, vy = conveyor.belt_velocity
        self.assertEqual(vx, -50.0)
        self.assertEqual(vy, 0.0)

    def test_collision_layer_terrain(self):
        """Test default collision layer is TERRAIN."""
        conveyor = ConveyorBody()

        self.assertEqual(conveyor.collider.collision_layer, CollisionLayer.TERRAIN)

    def test_custom_collision_layer(self):
        """Test custom collision layer."""
        conveyor = ConveyorBody(collision_layer=CollisionLayer.DEFAULT)

        self.assertEqual(conveyor.collider.collision_layer, CollisionLayer.DEFAULT)

    def test_collision_callbacks_preserve_y_velocity(self):
        """Test that conveyor preserves Y velocity when applying belt motion."""
        conveyor = ConveyorBody(
            x=100.0, y=100.0,
            direction=Direction.EAST, belt_speed=50.0, is_active=True
        )

        mock_object = Mock(spec=IPhysicsBody2D)
        mock_object.body_type = BodyType.DYNAMIC
        mock_object.linear_velocity = (10.0, -30.0)  # Falling

        with patch.object(conveyor, 'is_on_top_of', return_value=True):
            conveyor.on_collision_stay(mock_object)

        # Y velocity should be preserved
        mock_object.set_linear_velocity.assert_called_with(50.0, -30.0)

    def test_zero_size_conveyor(self):
        """Test conveyor with zero size."""
        conveyor = ConveyorBody(width=0.0, height=0.0)

        self.assertEqual(conveyor.width, 0.0)
        self.assertEqual(conveyor.height, 0.0)

    # ==================== Serialization Tests ====================

    def test_to_dict(self):
        """Test to_dict creates correct dictionary representation."""
        conveyor = ConveyorBody(
            name="Serialize Test",
            x=100.0,
            y=200.0,
            width=150.0,
            height=25.0,
            direction=Direction.NORTH,
            belt_speed=75.0,
            is_active=True
        )

        data = conveyor.to_dict()

        self.assertEqual(data["name"], "Serialize Test")
        self.assertEqual(data["x"], 100.0)
        self.assertEqual(data["y"], 200.0)
        self.assertEqual(data["width"], 150.0)
        self.assertEqual(data["height"], 25.0)
        self.assertEqual(data["direction"], "north")
        self.assertEqual(data["belt_speed"], 75.0)
        self.assertTrue(data["is_active"])

    def test_from_dict(self):
        """Test from_dict creates conveyor from dictionary."""
        data = {
            "name": "Deserialized Belt",
            "x": 50.0,
            "y": 75.0,
            "width": 200.0,
            "height": 30.0,
            "direction": "south",
            "belt_speed": 60.0,
            "is_active": False,
            "body_type": "STATIC",
            "collision_layer": "TERRAIN",
            "collider_type": "RECTANGLE",
            "enabled": True,
            "sleeping": False,
            "mass": 0.0,
        }

        conveyor = ConveyorBody.from_dict(data)

        self.assertEqual(conveyor.name, "Deserialized Belt")
        self.assertEqual(conveyor.x, 50.0)
        self.assertEqual(conveyor.y, 75.0)
        self.assertEqual(conveyor.width, 200.0)
        self.assertEqual(conveyor.height, 30.0)
        self.assertEqual(conveyor.direction, Direction.SOUTH)
        self.assertEqual(conveyor.belt_speed, 60.0)
        self.assertFalse(conveyor.is_active)

    def test_roundtrip_serialization(self):
        """Test serialization and deserialization produces identical object."""
        original = ConveyorBody(
            name="Original",
            x=123.45,
            y=678.90,
            width=175.0,
            height=35.0,
            direction=Direction.WEST,
            belt_speed=85.5,
            is_active=True
        )

        data = original.to_dict()
        restored = ConveyorBody.from_dict(data)

        self.assertEqual(original.name, restored.name)
        self.assertEqual(original.x, restored.x)
        self.assertEqual(original.y, restored.y)
        self.assertEqual(original.width, restored.width)
        self.assertEqual(original.height, restored.height)
        self.assertEqual(original.direction, restored.direction)
        self.assertEqual(original.belt_speed, restored.belt_speed)
        self.assertEqual(original.is_active, restored.is_active)

    def test_from_dict_direction_enum(self):
        """Test from_dict handles Direction enum directly."""
        data = {
            "name": "Test",
            "direction": Direction.EAST,
            "body_type": "STATIC",
            "collision_layer": "TERRAIN",
            "collider_type": "RECTANGLE",
        }

        conveyor = ConveyorBody.from_dict(data)

        self.assertEqual(conveyor.direction, Direction.EAST)

    # ==================== Editable Properties Tests ====================

    def test_get_editable_properties(self):
        """Test get_editable_properties returns correct structure."""
        conveyor = ConveyorBody()

        props = conveyor.get_properties()

        self.assertIn("direction", props)
        self.assertIn("belt_speed", props)
        self.assertIn("is_active", props)
        self.assertIn("x", props)  # From base class
        self.assertIn("y", props)  # From base class
        self.assertIn("width", props)  # From base class
        self.assertIn("height", props)  # From base class

    def test_editable_property_direction(self):
        """Test direction property value."""
        conveyor = ConveyorBody()

        props = conveyor.get_properties()
        direction_value = props["direction"]

        # Direction should be stored as string value
        self.assertEqual(direction_value, "east")  # Default

        # Test changing direction
        conveyor.set_direction("north")
        props = conveyor.get_properties()
        self.assertEqual(props["direction"], "north")

    def test_editable_property_belt_speed(self):
        """Test belt_speed property value."""
        conveyor = ConveyorBody(belt_speed=50.0)

        props = conveyor.get_properties()
        speed_value = props["belt_speed"]

        # Belt speed should be stored as float value
        self.assertEqual(speed_value, 50.0)

        # Test changing belt speed
        conveyor.set_belt_speed(100.0)
        props = conveyor.get_properties()
        self.assertEqual(props["belt_speed"], 100.0)

    def test_editable_property_is_active(self):
        """Test is_active property value."""
        conveyor = ConveyorBody(is_active=True)

        props = conveyor.get_properties()
        active_value = props["is_active"]

        # is_active should be stored as bool value
        self.assertTrue(active_value)

        # Test changing active state
        conveyor.deactivate()
        props = conveyor.get_properties()
        self.assertFalse(props["is_active"])


class TestConveyorBodyFactory(unittest.TestCase):
    """Test the factory registration for ConveyorBody."""

    def test_factory_registration(self):
        """Test that ConveyorBody is registered in the factory."""
        from pyrox.models.physics.factory import PhysicsSceneFactory

        template = PhysicsSceneFactory.get_template("Conveyor Belt")

        self.assertIsNotNone(template)
        self.assertEqual(template.name, "Conveyor Belt")  # type: ignore
        self.assertEqual(template.body_class, ConveyorBody)  # type: ignore
        self.assertEqual(template.category, "Platforms")  # type: ignore

    def test_create_from_factory(self):
        """Test creating ConveyorBody from factory."""
        from pyrox.models.physics.factory import PhysicsSceneFactory

        conveyor = PhysicsSceneFactory.create_from_template(
            "Conveyor Belt",
            x=150.0,
            y=250.0,
            name="Factory Conveyor"
        )

        self.assertIsNotNone(conveyor)
        self.assertIsInstance(conveyor, ConveyorBody)
        self.assertEqual(conveyor.x, 150.0)  # type: ignore
        self.assertEqual(conveyor.y, 250.0)  # type: ignore
        self.assertEqual(conveyor.name, "Factory Conveyor")  # type: ignore

    def test_factory_default_parameters(self):
        """Test factory template uses correct defaults."""
        from pyrox.models.physics.factory import PhysicsSceneFactory

        template = PhysicsSceneFactory.get_template("Conveyor Belt")

        self.assertEqual(template.default_kwargs['width'], 200.0)  # type: ignore
        self.assertEqual(template.default_kwargs['height'], 20.0)  # type: ignore
        self.assertEqual(template.default_kwargs['direction'], Direction.EAST)  # type: ignore
        self.assertEqual(template.default_kwargs['belt_speed'], 50.0)  # type: ignore
        self.assertTrue(template.default_kwargs['is_active'])  # type: ignore

    def test_top_down_factory_registration(self):
        """Test that Top-Down Conveyor Belt is registered in the factory."""
        from pyrox.models.physics.factory import PhysicsSceneFactory

        template = PhysicsSceneFactory.get_template("Top-Down Conveyor Belt")

        self.assertIsNotNone(template)
        self.assertEqual(template.name, "Top-Down Conveyor Belt")  # type: ignore
        self.assertEqual(template.body_class, ConveyorBody)  # type: ignore
        self.assertEqual(template.category, "Platforms")  # type: ignore

    def test_top_down_factory_default_parameters(self):
        """Test top-down factory template uses correct defaults."""
        from pyrox.models.physics.factory import PhysicsSceneFactory

        template = PhysicsSceneFactory.get_template("Top-Down Conveyor Belt")

        self.assertEqual(template.default_kwargs['width'], 200.0)  # type: ignore
        self.assertEqual(template.default_kwargs['height'], 20.0)  # type: ignore
        self.assertEqual(template.default_kwargs['direction'], Direction.NORTH)  # type: ignore
        self.assertEqual(template.default_kwargs['belt_speed'], 50.0)  # type: ignore
        self.assertTrue(template.default_kwargs['is_active'])  # type: ignore
        self.assertTrue(template.default_kwargs['is_trigger'])  # type: ignore

    def test_create_top_down_from_factory(self):
        """Test creating top-down ConveyorBody from factory."""
        from pyrox.models.physics.factory import PhysicsSceneFactory

        conveyor = PhysicsSceneFactory.create_from_template(
            "Top-Down Conveyor Belt",
            x=150.0,
            y=250.0,
            name="Top-Down Conveyor"
        )

        self.assertIsNotNone(conveyor)
        self.assertIsInstance(conveyor, ConveyorBody)
        self.assertEqual(conveyor.x, 150.0)  # type: ignore
        self.assertEqual(conveyor.y, 250.0)  # type: ignore
        self.assertEqual(conveyor.name, "Top-Down Conveyor")  # type: ignore
        self.assertEqual(conveyor.direction, Direction.NORTH)  # type: ignore
        self.assertTrue(conveyor.collider.is_trigger)  # type: ignore


if __name__ == '__main__':
    unittest.main()

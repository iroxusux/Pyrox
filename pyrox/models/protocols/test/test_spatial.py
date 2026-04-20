"""Unit tests for spatial.py protocols module."""

import unittest

from pyrox.interfaces import CardinalDirection, IDirectional2D, IRotatable
from pyrox.models.protocols.spatial import (
    Rotatable,
    Spatial2D,
    Zoomable,
)
from pyrox.models.protocols.coord import (
    Area2D,
)


class TestRotatable(unittest.TestCase):
    """Test cases for Rotatable class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        rot = Rotatable()
        self.assertEqual(rot.get_pitch(), 0.0)
        self.assertEqual(rot.get_yaw(), 0.0)
        self.assertEqual(rot.get_roll(), 0.0)

    def test_init_with_values(self):
        """Test initialization with provided values."""
        rot = Rotatable(roll=10.0, pitch=20.0, yaw=30.0)
        self.assertEqual(rot.get_pitch(), 20.0)
        self.assertEqual(rot.get_yaw(), 30.0)
        self.assertEqual(rot.get_roll(), 10.0)

    def test_get_pitch(self):
        """Test getting pitch rotation."""
        rot = Rotatable(pitch=45.0)
        self.assertEqual(rot.get_pitch(), 45.0)
        self.assertIsInstance(rot.get_pitch(), float)

    def test_set_pitch(self):
        """Test setting pitch rotation."""
        rot = Rotatable()
        rot.set_pitch(90.0)
        self.assertEqual(rot.get_pitch(), 90.0)

    def test_get_yaw(self):
        """Test getting yaw rotation."""
        rot = Rotatable(yaw=180.0)
        self.assertEqual(rot.get_yaw(), 180.0)
        self.assertIsInstance(rot.get_yaw(), float)

    def test_set_yaw(self):
        """Test setting yaw rotation."""
        rot = Rotatable()
        rot.set_yaw(270.0)
        self.assertEqual(rot.get_yaw(), 270.0)

    def test_get_roll(self):
        """Test getting roll rotation."""
        rot = Rotatable(roll=15.0)
        self.assertEqual(rot.get_roll(), 15.0)
        self.assertIsInstance(rot.get_roll(), float)

    def test_set_roll(self):
        """Test setting roll rotation."""
        rot = Rotatable()
        rot.set_roll(45.0)
        self.assertEqual(rot.get_roll(), 45.0)

    def test_pitch_property(self):
        """Test pitch property access."""
        rot = Rotatable(pitch=60.0)
        self.assertEqual(rot.pitch, 60.0)
        rot.pitch = 120.0
        self.assertEqual(rot.pitch, 120.0)

    def test_yaw_property(self):
        """Test yaw property access."""
        rot = Rotatable(yaw=90.0)
        self.assertEqual(rot.yaw, 90.0)
        rot.yaw = 180.0
        self.assertEqual(rot.yaw, 180.0)

    def test_roll_property(self):
        """Test roll property access."""
        rot = Rotatable(roll=30.0)
        self.assertEqual(rot.roll, 30.0)
        rot.roll = 60.0
        self.assertEqual(rot.roll, 60.0)

    def test_get_rotation(self):
        """Test get_rotation returns (pitch, yaw, roll) tuple."""
        rot = Rotatable(roll=10.0, pitch=20.0, yaw=30.0)
        rotation = rot.get_rotation()
        self.assertEqual(rotation, (20.0, 30.0, 10.0))  # (pitch, yaw, roll)
        self.assertIsInstance(rotation, tuple)
        self.assertEqual(len(rotation), 3)

    def test_set_rotation(self):
        """Test set_rotation with positional arguments."""
        rot = Rotatable()
        rot.set_rotation(45.0, 90.0, 135.0)  # pitch, yaw, roll
        self.assertEqual(rot.get_pitch(), 45.0)
        self.assertEqual(rot.get_yaw(), 90.0)
        self.assertEqual(rot.get_roll(), 135.0)

    def test_rotation_property(self):
        """Test rotation property returns (pitch, yaw, roll) tuple."""
        rot = Rotatable(roll=5.0, pitch=10.0, yaw=15.0)
        self.assertEqual(rot.rotation, (10.0, 15.0, 5.0))

    def test_set_rotation_updates_all(self):
        """Test that set_rotation updates all three axes."""
        rot = Rotatable(roll=1.0, pitch=2.0, yaw=3.0)
        rot.set_rotation(100.0, 200.0, 300.0)  # pitch, yaw, roll
        self.assertEqual(rot.get_pitch(), 100.0)
        self.assertEqual(rot.get_yaw(), 200.0)
        self.assertEqual(rot.get_roll(), 300.0)

    def test_negative_rotations(self):
        """Test negative rotation values."""
        rot = Rotatable(roll=-10.0, pitch=-20.0, yaw=-30.0)
        self.assertEqual(rot.get_pitch(), -20.0)
        self.assertEqual(rot.get_yaw(), -30.0)
        self.assertEqual(rot.get_roll(), -10.0)

    def test_large_rotation_values(self):
        """Test large rotation values (e.g., multiple revolutions)."""
        rot = Rotatable(roll=720.0, pitch=1080.0, yaw=1440.0)
        self.assertEqual(rot.get_roll(), 720.0)
        self.assertEqual(rot.get_pitch(), 1080.0)
        self.assertEqual(rot.get_yaw(), 1440.0)

    def test_rotation_independence(self):
        """Test that pitch, yaw, and roll are independent axes."""
        rot = Rotatable()
        rot.set_pitch(10.0)
        self.assertEqual(rot.get_pitch(), 10.0)
        self.assertEqual(rot.get_yaw(), 0.0)
        self.assertEqual(rot.get_roll(), 0.0)

        rot.set_yaw(20.0)
        self.assertEqual(rot.get_pitch(), 10.0)
        self.assertEqual(rot.get_yaw(), 20.0)
        self.assertEqual(rot.get_roll(), 0.0)

    def test_inherits_irotatable(self):
        """Test that Rotatable satisfies the IRotatable interface."""
        rot = Rotatable()
        self.assertIsInstance(rot, IRotatable)


class TestZoomable(unittest.TestCase):
    """Test cases for Zoomable class."""

    def test_init_default_zoom(self):
        """Test initialization with default zoom level."""
        z = Zoomable()
        self.assertEqual(z.get_zoom(), 1.0)

    def test_init_with_zoom(self):
        """Test initialization with a specific zoom level."""
        z = Zoomable(zoom=2.5)
        self.assertEqual(z.get_zoom(), 2.5)

    def test_set_zoom(self):
        """Test setting zoom level."""
        z = Zoomable()
        z.set_zoom(3.0)
        self.assertEqual(z.get_zoom(), 3.0)

    def test_zoom_property_getter(self):
        """Test zoom property getter."""
        z = Zoomable(zoom=0.5)
        self.assertEqual(z.zoom, 0.5)

    def test_zoom_property_setter(self):
        """Test zoom property setter."""
        z = Zoomable()
        z.zoom = 4.0
        self.assertEqual(z.zoom, 4.0)

    def test_zoom_fractional(self):
        """Test fractional zoom values."""
        z = Zoomable(zoom=0.25)
        self.assertEqual(z.get_zoom(), 0.25)

    def test_multiple_instances_independent(self):
        """Test that multiple Zoomable instances are independent."""
        z1 = Zoomable(zoom=1.0)
        z2 = Zoomable(zoom=2.0)
        z1.set_zoom(5.0)
        self.assertEqual(z1.get_zoom(), 5.0)
        self.assertEqual(z2.get_zoom(), 2.0)


class TestSpatial2D(unittest.TestCase):
    """Test cases for Spatial2D class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        spatial = Spatial2D()
        self.assertEqual(spatial.get_x(), 0.0)
        self.assertEqual(spatial.get_y(), 0.0)
        self.assertEqual(spatial.get_width(), 0.0)
        self.assertEqual(spatial.get_height(), 0.0)
        self.assertIsNone(spatial._direction)

    def test_init_with_position_values(self):
        """Test initialization with position values."""
        spatial = Spatial2D(x=10.0, y=20.0)
        self.assertEqual(spatial.get_x(), 10.0)
        self.assertEqual(spatial.get_y(), 20.0)

    def test_init_with_size_values(self):
        """Test initialization with size values."""
        spatial = Spatial2D(width=100.0, height=50.0)
        self.assertEqual(spatial.get_width(), 100.0)
        self.assertEqual(spatial.get_height(), 50.0)

    def test_init_with_direction(self):
        """Test initialization with a cardinal direction."""
        spatial = Spatial2D(direction=CardinalDirection.NORTH)
        self.assertEqual(spatial._direction, CardinalDirection.NORTH)

    def test_init_with_all_values(self):
        """Test initialization with all supported values."""
        spatial = Spatial2D(
            x=10.0, y=20.0,
            width=100.0, height=50.0,
            direction=CardinalDirection.EAST,
        )
        self.assertEqual(spatial.get_x(), 10.0)
        self.assertEqual(spatial.get_y(), 20.0)
        self.assertEqual(spatial.get_width(), 100.0)
        self.assertEqual(spatial.get_height(), 50.0)
        self.assertEqual(spatial._direction, CardinalDirection.EAST)

    def test_inheritance_from_area2d(self):
        """Test that Spatial2D inherits from Area2D."""
        spatial = Spatial2D()
        self.assertIsInstance(spatial, Area2D)

    def test_inherits_idirectional2d(self):
        """Test that Spatial2D satisfies the IDirectional2D interface."""
        spatial = Spatial2D()
        self.assertIsInstance(spatial, IDirectional2D)

    def test_area2d_methods_work(self):
        """Test that Area2D position/size methods work on Spatial2D."""
        spatial = Spatial2D()
        spatial.set_x(100.0)
        spatial.set_y(200.0)
        spatial.set_width(50.0)
        spatial.set_height(25.0)

        self.assertEqual(spatial.get_x(), 100.0)
        self.assertEqual(spatial.get_y(), 200.0)
        self.assertEqual(spatial.get_width(), 50.0)
        self.assertEqual(spatial.get_height(), 25.0)

    def test_position_property(self):
        """Test position property from Area2D."""
        spatial = Spatial2D(x=10.0, y=20.0)
        self.assertEqual(spatial.position, (10.0, 20.0))

    def test_size_property(self):
        """Test size property from Area2D."""
        spatial = Spatial2D(width=100.0, height=50.0)
        self.assertEqual(spatial.size, (100.0, 50.0))

    def test_center_calculation(self):
        """Test center calculation from Area2D."""
        spatial = Spatial2D(x=0.0, y=0.0, width=100.0, height=50.0)
        center = spatial.get_center()
        self.assertEqual(center, (50.0, 25.0))

    def test_set_position(self):
        """Test setting position via tuple."""
        spatial = Spatial2D()
        spatial.set_position((30.0, 40.0))
        self.assertEqual(spatial.get_x(), 30.0)
        self.assertEqual(spatial.get_y(), 40.0)

    def test_set_size(self):
        """Test setting size via tuple."""
        spatial = Spatial2D()
        spatial.set_size((200.0, 150.0))
        self.assertEqual(spatial.get_width(), 200.0)
        self.assertEqual(spatial.get_height(), 150.0)

    def test_get_direction_defaults_to_north(self):
        """Test that get_direction returns NORTH when no direction was set."""
        spatial = Spatial2D()
        self.assertIsNone(spatial._direction)
        self.assertEqual(spatial.get_direction(), CardinalDirection.NORTH)

    def test_set_direction(self):
        """Test setting direction explicitly."""
        spatial = Spatial2D()
        spatial.set_direction(CardinalDirection.EAST)
        self.assertEqual(spatial.get_direction(), CardinalDirection.EAST)

    def test_direction_property(self):
        """Test direction property getter and setter."""
        spatial = Spatial2D(direction=CardinalDirection.SOUTH)
        self.assertEqual(spatial.direction, CardinalDirection.SOUTH)
        spatial.direction = CardinalDirection.WEST
        self.assertEqual(spatial.direction, CardinalDirection.WEST)

    def test_set_direction_from_string(self):
        """Test setting direction using a string value."""
        spatial = Spatial2D()
        spatial.set_direction("EAST")
        self.assertEqual(spatial.get_direction(), CardinalDirection.EAST)

    def test_set_direction_none_clears_direction(self):
        """Test that setting direction to None clears it."""
        spatial = Spatial2D(direction=CardinalDirection.NORTH)
        spatial.set_direction(None)
        self.assertIsNone(spatial._direction)

    def test_rotate_area_swaps_dimensions(self):
        """Test that rotate_area swaps width and height."""
        spatial = Spatial2D(width=100.0, height=40.0)
        spatial.rotate_clockwise()  # Rotate to EAST (perpendicular)
        self.assertEqual(spatial.get_width(), 40.0)
        self.assertEqual(spatial.get_height(), 100.0)

    def test_rotate_clockwise(self):
        """Test rotating clockwise changes direction correctly."""
        spatial = Spatial2D(direction=CardinalDirection.NORTH, width=10.0, height=20.0)
        spatial.rotate_clockwise()
        self.assertEqual(spatial.get_direction(), CardinalDirection.EAST)

    def test_rotate_counterclockwise(self):
        """Test rotating counter-clockwise changes direction correctly."""
        spatial = Spatial2D(direction=CardinalDirection.NORTH, width=10.0, height=20.0)
        spatial.rotate_counterclockwise()
        self.assertEqual(spatial.get_direction(), CardinalDirection.WEST)

    def test_rotate_180(self):
        """Test rotating 180 degrees reaches the opposite direction."""
        # NORTH(4) → formula: ((4+1)%4)+1 = 2 = SOUTH
        spatial = Spatial2D(direction=CardinalDirection.NORTH)
        spatial.rotate_180()
        self.assertEqual(spatial.get_direction(), CardinalDirection.SOUTH)

    def test_rotate_to(self):
        """Test rotating to a specific direction."""
        spatial = Spatial2D(direction=CardinalDirection.NORTH)
        spatial.rotate_to(CardinalDirection.SOUTH)
        self.assertEqual(spatial.get_direction(), CardinalDirection.SOUTH)

    def test_perpendicular_rotation_swaps_area(self):
        """Test that rotating to a perpendicular direction swaps area dimensions."""
        spatial = Spatial2D(
            direction=CardinalDirection.NORTH,
            width=10.0,
            height=20.0,
        )
        spatial.rotate_clockwise()  # NORTH → EAST (perpendicular)
        self.assertEqual(spatial.get_width(), 20.0)
        self.assertEqual(spatial.get_height(), 10.0)

    def test_non_perpendicular_rotation_preserves_area(self):
        """Test that rotating to the same or opposite direction preserves area dimensions."""
        spatial = Spatial2D(
            direction=CardinalDirection.NORTH,
            width=10.0,
            height=20.0,
        )
        spatial.set_direction(CardinalDirection.SOUTH)  # NORTH → SOUTH (opposite, not perpendicular)
        self.assertEqual(spatial.get_width(), 10.0)
        self.assertEqual(spatial.get_height(), 20.0)


class TestSpatialIntegration(unittest.TestCase):
    """Integration tests for spatial classes."""

    def test_multiple_spatial_instances_independence(self):
        """Test that multiple Spatial2D instances are independent."""
        spatial1 = Spatial2D(x=10.0, y=20.0)
        spatial2 = Spatial2D(x=40.0, y=50.0)

        spatial1.set_x(100.0)

        self.assertEqual(spatial1.get_x(), 100.0)
        self.assertEqual(spatial2.get_x(), 40.0)

    def test_rotatable_instances_independence(self):
        """Test that Rotatable instances are independent."""
        rot1 = Rotatable(pitch=10.0, yaw=20.0, roll=30.0)
        rot2 = Rotatable(pitch=40.0, yaw=50.0, roll=60.0)

        rot1.set_pitch(100.0)

        self.assertEqual(rot1.get_pitch(), 100.0)
        self.assertEqual(rot2.get_pitch(), 40.0)

    def test_spatial_move(self):
        """Test moving a Spatial2D object."""
        spatial = Spatial2D(x=0.0, y=0.0)
        spatial.set_x(100.0)
        spatial.set_y(200.0)
        self.assertEqual(spatial.get_position(), (100.0, 200.0))

    def test_rotatable_pure_rotation(self):
        """Test Rotatable without any area (pure rotation object)."""
        rot = Rotatable(roll=30.0, pitch=60.0, yaw=90.0)
        self.assertEqual(rot.get_rotation(), (60.0, 90.0, 30.0))

        rot.set_rotation(120.0, 180.0, 240.0)  # pitch, yaw, roll
        self.assertEqual(rot.get_rotation(), (120.0, 180.0, 240.0))

    def test_zoomable_instances_independence(self):
        """Test that multiple Zoomable instances have independent state."""
        z1 = Zoomable(zoom=1.0)
        z2 = Zoomable(zoom=2.0)
        z1.zoom = 10.0
        self.assertEqual(z1.zoom, 10.0)
        self.assertEqual(z2.zoom, 2.0)

    def test_full_clockwise_rotation_cycle(self):
        """Test a full 4-step clockwise rotation returns to original dimensions."""
        spatial = Spatial2D(
            direction=CardinalDirection.NORTH,
            width=10.0,
            height=20.0,
        )
        # Each 90° clockwise step swaps dimensions (perpendicular each time)
        for _ in range(4):
            spatial.rotate_clockwise()
        # After 4 rotations we're back to NORTH with original dimensions
        self.assertEqual(spatial.get_direction(), CardinalDirection.NORTH)
        self.assertEqual(spatial.get_width(), 10.0)
        self.assertEqual(spatial.get_height(), 20.0)


if __name__ == '__main__':
    unittest.main()

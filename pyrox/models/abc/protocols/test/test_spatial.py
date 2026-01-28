"""Unit tests for spatial.py protocols module."""

import unittest

from pyrox.models.abc.protocols.spatial import (
    Rotatable,
    Spatial2D,
    Spatial3D,
)
from pyrox.models.abc.protocols.coord import (
    Area2D,
    Area3D,
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
        """Test getting rotation as tuple."""
        rot = Rotatable(roll=10.0, pitch=20.0, yaw=30.0)
        rotation = rot.get_rotation()
        self.assertEqual(rotation, (20.0, 30.0, 10.0))  # (pitch, yaw, roll)
        self.assertIsInstance(rotation, tuple)
        self.assertEqual(len(rotation), 3)

    def test_set_rotation(self):
        """Test setting rotation from individual values."""
        rot = Rotatable()
        rot.set_rotation(pitch=45.0, yaw=90.0, roll=135.0)
        self.assertEqual(rot.get_pitch(), 45.0)
        self.assertEqual(rot.get_yaw(), 90.0)
        self.assertEqual(rot.get_roll(), 135.0)

    def test_rotation_property(self):
        """Test rotation property access."""
        rot = Rotatable(roll=5.0, pitch=10.0, yaw=15.0)
        self.assertEqual(rot.rotation, (10.0, 15.0, 5.0))

    def test_set_rotation_updates_all(self):
        """Test that set_rotation updates all rotation values."""
        rot = Rotatable(roll=1.0, pitch=2.0, yaw=3.0)
        rot.set_rotation(pitch=100.0, yaw=200.0, roll=300.0)
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
        """Test that pitch, yaw, and roll are independent."""
        rot = Rotatable()
        rot.set_pitch(10.0)
        self.assertEqual(rot.get_pitch(), 10.0)
        self.assertEqual(rot.get_yaw(), 0.0)
        self.assertEqual(rot.get_roll(), 0.0)

        rot.set_yaw(20.0)
        self.assertEqual(rot.get_pitch(), 10.0)
        self.assertEqual(rot.get_yaw(), 20.0)
        self.assertEqual(rot.get_roll(), 0.0)


class TestSpatial2D(unittest.TestCase):
    """Test cases for Spatial2D class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        spatial = Spatial2D()
        self.assertEqual(spatial.get_x(), 0.0)
        self.assertEqual(spatial.get_y(), 0.0)
        self.assertEqual(spatial.get_width(), 0.0)
        self.assertEqual(spatial.get_height(), 0.0)
        self.assertEqual(spatial.get_pitch(), 0.0)
        self.assertEqual(spatial.get_yaw(), 0.0)
        self.assertEqual(spatial.get_roll(), 0.0)

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

    def test_init_with_rotation_values(self):
        """Test initialization with rotation values."""
        spatial = Spatial2D(roll=10.0, pitch=20.0, yaw=30.0)
        self.assertEqual(spatial.get_roll(), 10.0)
        self.assertEqual(spatial.get_pitch(), 20.0)
        self.assertEqual(spatial.get_yaw(), 30.0)

    def test_init_with_all_values(self):
        """Test initialization with all values."""
        spatial = Spatial2D(
            x=10.0, y=20.0,
            width=100.0, height=50.0,
            roll=15.0, pitch=25.0, yaw=35.0
        )
        self.assertEqual(spatial.get_x(), 10.0)
        self.assertEqual(spatial.get_y(), 20.0)
        self.assertEqual(spatial.get_width(), 100.0)
        self.assertEqual(spatial.get_height(), 50.0)
        self.assertEqual(spatial.get_roll(), 15.0)
        self.assertEqual(spatial.get_pitch(), 25.0)
        self.assertEqual(spatial.get_yaw(), 35.0)

    def test_inheritance_from_area2d(self):
        """Test that Spatial2D inherits from Area2D."""
        spatial = Spatial2D()
        self.assertIsInstance(spatial, Area2D)

    def test_inheritance_from_rotatable(self):
        """Test that Spatial2D inherits from Rotatable."""
        spatial = Spatial2D()
        self.assertIsInstance(spatial, Rotatable)

    def test_area2d_methods_work(self):
        """Test that Area2D methods work."""
        spatial = Spatial2D()
        spatial.set_x(100.0)
        spatial.set_y(200.0)
        spatial.set_width(50.0)
        spatial.set_height(25.0)

        self.assertEqual(spatial.get_x(), 100.0)
        self.assertEqual(spatial.get_y(), 200.0)
        self.assertEqual(spatial.get_width(), 50.0)
        self.assertEqual(spatial.get_height(), 25.0)

    def test_rotatable_methods_work(self):
        """Test that Rotatable methods work."""
        spatial = Spatial2D()
        spatial.set_roll(45.0)
        spatial.set_pitch(90.0)
        spatial.set_yaw(135.0)

        self.assertEqual(spatial.get_roll(), 45.0)
        self.assertEqual(spatial.get_pitch(), 90.0)
        self.assertEqual(spatial.get_yaw(), 135.0)

    def test_position_property(self):
        """Test position property from Area2D."""
        spatial = Spatial2D(x=10.0, y=20.0)
        self.assertEqual(spatial.position, (10.0, 20.0))

    def test_size_property(self):
        """Test size property from Area2D."""
        spatial = Spatial2D(width=100.0, height=50.0)
        self.assertEqual(spatial.size, (100.0, 50.0))

    def test_rotation_property(self):
        """Test rotation property from Rotatable."""
        spatial = Spatial2D(roll=10.0, pitch=20.0, yaw=30.0)
        self.assertEqual(spatial.rotation, (20.0, 30.0, 10.0))

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

    def test_set_rotation_method(self):
        """Test setting rotation via method."""
        spatial = Spatial2D()
        spatial.set_rotation(pitch=60.0, yaw=120.0, roll=180.0)
        self.assertEqual(spatial.get_pitch(), 60.0)
        self.assertEqual(spatial.get_yaw(), 120.0)
        self.assertEqual(spatial.get_roll(), 180.0)


class TestSpatial3D(unittest.TestCase):
    """Test cases for Spatial3D class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        spatial = Spatial3D()
        self.assertEqual(spatial.get_x(), 0.0)
        self.assertEqual(spatial.get_y(), 0.0)
        self.assertEqual(spatial.get_z(), 0.0)
        self.assertEqual(spatial.get_width(), 0.0)
        self.assertEqual(spatial.get_height(), 0.0)
        self.assertEqual(spatial.get_depth(), 0.0)
        self.assertEqual(spatial.get_pitch(), 0.0)
        self.assertEqual(spatial.get_yaw(), 0.0)
        self.assertEqual(spatial.get_roll(), 0.0)

    def test_init_with_position_values(self):
        """Test initialization with position values."""
        spatial = Spatial3D(x=10.0, y=20.0, z=30.0)
        self.assertEqual(spatial.get_x(), 10.0)
        self.assertEqual(spatial.get_y(), 20.0)
        self.assertEqual(spatial.get_z(), 30.0)

    def test_init_with_size_values(self):
        """Test initialization with size values."""
        spatial = Spatial3D(width=100.0, height=50.0, depth=75.0)
        self.assertEqual(spatial.get_width(), 100.0)
        self.assertEqual(spatial.get_height(), 50.0)
        self.assertEqual(spatial.get_depth(), 75.0)

    def test_init_with_rotation_values(self):
        """Test initialization with rotation values."""
        spatial = Spatial3D(roll=10.0, pitch=20.0, yaw=30.0)
        self.assertEqual(spatial.get_roll(), 10.0)
        self.assertEqual(spatial.get_pitch(), 20.0)
        self.assertEqual(spatial.get_yaw(), 30.0)

    def test_init_with_all_values(self):
        """Test initialization with all values."""
        spatial = Spatial3D(
            x=10.0, y=20.0, z=30.0,
            width=100.0, height=50.0, depth=75.0,
            roll=15.0, pitch=25.0, yaw=35.0
        )
        self.assertEqual(spatial.get_x(), 10.0)
        self.assertEqual(spatial.get_y(), 20.0)
        self.assertEqual(spatial.get_z(), 30.0)
        self.assertEqual(spatial.get_width(), 100.0)
        self.assertEqual(spatial.get_height(), 50.0)
        self.assertEqual(spatial.get_depth(), 75.0)
        self.assertEqual(spatial.get_roll(), 15.0)
        self.assertEqual(spatial.get_pitch(), 25.0)
        self.assertEqual(spatial.get_yaw(), 35.0)

    def test_inheritance_from_area3d(self):
        """Test that Spatial3D inherits from Area3D."""
        spatial = Spatial3D()
        self.assertIsInstance(spatial, Area3D)

    def test_inheritance_from_rotatable(self):
        """Test that Spatial3D inherits from Rotatable."""
        spatial = Spatial3D()
        self.assertIsInstance(spatial, Rotatable)

    def test_area3d_methods_work(self):
        """Test that Area3D methods work."""
        spatial = Spatial3D()
        spatial.set_x(100.0)
        spatial.set_y(200.0)
        spatial.set_z(300.0)
        spatial.set_width(50.0)
        spatial.set_height(25.0)
        spatial.set_depth(75.0)

        self.assertEqual(spatial.get_x(), 100.0)
        self.assertEqual(spatial.get_y(), 200.0)
        self.assertEqual(spatial.get_z(), 300.0)
        self.assertEqual(spatial.get_width(), 50.0)
        self.assertEqual(spatial.get_height(), 25.0)
        self.assertEqual(spatial.get_depth(), 75.0)

    def test_rotatable_methods_work(self):
        """Test that Rotatable methods work."""
        spatial = Spatial3D()
        spatial.set_roll(45.0)
        spatial.set_pitch(90.0)
        spatial.set_yaw(135.0)

        self.assertEqual(spatial.get_roll(), 45.0)
        self.assertEqual(spatial.get_pitch(), 90.0)
        self.assertEqual(spatial.get_yaw(), 135.0)

    def test_position_property(self):
        """Test 3D position property from Area3D."""
        spatial = Spatial3D(x=10.0, y=20.0, z=30.0)
        self.assertEqual(spatial.position, (10.0, 20.0, 30.0))

    def test_size_property(self):
        """Test 3D size property from Area3D."""
        spatial = Spatial3D(width=100.0, height=50.0, depth=75.0)
        self.assertEqual(spatial.size, (100.0, 50.0, 75.0))

    def test_rotation_property(self):
        """Test rotation property from Rotatable."""
        spatial = Spatial3D(roll=10.0, pitch=20.0, yaw=30.0)
        self.assertEqual(spatial.rotation, (20.0, 30.0, 10.0))

    def test_center_calculation(self):
        """Test 3D center calculation from Area3D."""
        spatial = Spatial3D(
            x=0.0, y=0.0, z=0.0,
            width=100.0, height=50.0, depth=80.0
        )
        center = spatial.get_center()
        self.assertEqual(center, (50.0, 25.0, 40.0))

    def test_set_position(self):
        """Test setting 3D position via tuple."""
        spatial = Spatial3D()
        spatial.set_position((30.0, 40.0, 50.0))
        self.assertEqual(spatial.get_x(), 30.0)
        self.assertEqual(spatial.get_y(), 40.0)
        self.assertEqual(spatial.get_z(), 50.0)

    def test_set_size(self):
        """Test setting 3D size via tuple."""
        spatial = Spatial3D()
        spatial.set_size((200.0, 150.0, 100.0))
        self.assertEqual(spatial.get_width(), 200.0)
        self.assertEqual(spatial.get_height(), 150.0)
        self.assertEqual(spatial.get_depth(), 100.0)

    def test_set_rotation_method(self):
        """Test setting rotation via method."""
        spatial = Spatial3D()
        spatial.set_rotation(pitch=60.0, yaw=120.0, roll=180.0)
        self.assertEqual(spatial.get_pitch(), 60.0)
        self.assertEqual(spatial.get_yaw(), 120.0)
        self.assertEqual(spatial.get_roll(), 180.0)

    def test_all_properties_together(self):
        """Test all properties working together."""
        spatial = Spatial3D(
            x=100.0, y=200.0, z=300.0,
            width=50.0, height=60.0, depth=70.0,
            roll=10.0, pitch=20.0, yaw=30.0
        )

        # Position
        self.assertEqual(spatial.get_position(), (100.0, 200.0, 300.0))

        # Size
        self.assertEqual(spatial.get_size(), (50.0, 60.0, 70.0))

        # Rotation
        self.assertEqual(spatial.get_rotation(), (20.0, 30.0, 10.0))

        # Center
        center = spatial.get_center()
        self.assertEqual(center[0], 125.0)  # 100 + 50/2
        self.assertEqual(center[1], 230.0)  # 200 + 60/2
        self.assertEqual(center[2], 335.0)  # 300 + 70/2


class TestSpatialIntegration(unittest.TestCase):
    """Integration tests for spatial classes."""

    def test_spatial2d_to_spatial3d_conversion(self):
        """Test converting 2D spatial to 3D spatial."""
        spatial2d = Spatial2D(
            x=10.0, y=20.0,
            width=100.0, height=50.0,
            roll=5.0, pitch=10.0, yaw=15.0
        )

        spatial3d = Spatial3D(
            x=spatial2d.get_x(),
            y=spatial2d.get_y(),
            z=30.0,
            width=spatial2d.get_width(),
            height=spatial2d.get_height(),
            depth=75.0,
            roll=spatial2d.get_roll(),
            pitch=spatial2d.get_pitch(),
            yaw=spatial2d.get_yaw()
        )

        self.assertEqual(spatial3d.get_x(), 10.0)
        self.assertEqual(spatial3d.get_y(), 20.0)
        self.assertEqual(spatial3d.get_z(), 30.0)
        self.assertEqual(spatial3d.get_width(), 100.0)
        self.assertEqual(spatial3d.get_height(), 50.0)
        self.assertEqual(spatial3d.get_depth(), 75.0)
        self.assertEqual(spatial3d.get_roll(), 5.0)
        self.assertEqual(spatial3d.get_pitch(), 10.0)
        self.assertEqual(spatial3d.get_yaw(), 15.0)

    def test_multiple_instances_independence(self):
        """Test that multiple instances are independent."""
        spatial1 = Spatial2D(x=10.0, y=20.0, roll=30.0)
        spatial2 = Spatial2D(x=40.0, y=50.0, roll=60.0)

        spatial1.set_x(100.0)
        spatial1.set_roll(90.0)

        self.assertEqual(spatial1.get_x(), 100.0)
        self.assertEqual(spatial1.get_roll(), 90.0)
        self.assertEqual(spatial2.get_x(), 40.0)
        self.assertEqual(spatial2.get_roll(), 60.0)

    def test_rotatable_independence(self):
        """Test that rotatable instances are independent."""
        rot1 = Rotatable(pitch=10.0, yaw=20.0, roll=30.0)
        rot2 = Rotatable(pitch=40.0, yaw=50.0, roll=60.0)

        rot1.set_pitch(100.0)

        self.assertEqual(rot1.get_pitch(), 100.0)
        self.assertEqual(rot2.get_pitch(), 40.0)

    def test_combined_operations(self):
        """Test combined position, size, and rotation operations."""
        spatial = Spatial3D()

        # Set all properties
        spatial.set_position((10.0, 20.0, 30.0))
        spatial.set_size((100.0, 50.0, 75.0))
        spatial.set_rotation(pitch=45.0, yaw=90.0, roll=135.0)

        # Verify all properties
        self.assertEqual(spatial.get_position(), (10.0, 20.0, 30.0))
        self.assertEqual(spatial.get_size(), (100.0, 50.0, 75.0))
        self.assertEqual(spatial.get_rotation(), (45.0, 90.0, 135.0))

    def test_spatial_transformations(self):
        """Test spatial transformations (move and rotate)."""
        spatial = Spatial2D(x=0.0, y=0.0, roll=0.0)

        # Move
        spatial.set_x(100.0)
        spatial.set_y(200.0)

        # Rotate
        spatial.set_roll(45.0)

        self.assertEqual(spatial.get_position(), (100.0, 200.0))
        self.assertEqual(spatial.get_roll(), 45.0)

    def test_zero_rotation_valid(self):
        """Test that zero rotation is valid and distinct from uninitialized."""
        spatial = Spatial2D(roll=0.0, pitch=0.0, yaw=0.0)

        self.assertEqual(spatial.get_roll(), 0.0)
        self.assertEqual(spatial.get_pitch(), 0.0)
        self.assertEqual(spatial.get_yaw(), 0.0)
        self.assertEqual(spatial.get_rotation(), (0.0, 0.0, 0.0))

    def test_rotatable_with_no_area(self):
        """Test rotatable without associated area (pure rotation)."""
        rot = Rotatable(roll=30.0, pitch=60.0, yaw=90.0)

        self.assertEqual(rot.get_rotation(), (60.0, 90.0, 30.0))

        # Modify rotation
        rot.set_rotation(pitch=120.0, yaw=180.0, roll=240.0)
        self.assertEqual(rot.get_rotation(), (120.0, 180.0, 240.0))


if __name__ == '__main__':
    unittest.main()

"""Unit tests for coord.py protocols module."""

import unittest

from pyrox.models.abc.protocols.coord import (
    Coord2D,
    Area2D,
    Coord3D,
    Area3D,
)


class TestCoord2D(unittest.TestCase):
    """Test cases for Coord2D class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        coord = Coord2D()
        self.assertEqual(coord.get_x(), 0.0)
        self.assertEqual(coord.get_y(), 0.0)

    def test_init_with_values(self):
        """Test initialization with provided values."""
        coord = Coord2D(x=10.5, y=20.3)
        self.assertEqual(coord.get_x(), 10.5)
        self.assertEqual(coord.get_y(), 20.3)

    def test_get_x(self):
        """Test getting X coordinate."""
        coord = Coord2D(x=42.0)
        self.assertEqual(coord.get_x(), 42.0)
        self.assertIsInstance(coord.get_x(), float)

    def test_set_x(self):
        """Test setting X coordinate."""
        coord = Coord2D()
        coord.set_x(15.7)
        self.assertEqual(coord.get_x(), 15.7)

    def test_get_y(self):
        """Test getting Y coordinate."""
        coord = Coord2D(y=33.3)
        self.assertEqual(coord.get_y(), 33.3)
        self.assertIsInstance(coord.get_y(), float)

    def test_set_y(self):
        """Test setting Y coordinate."""
        coord = Coord2D()
        coord.set_y(25.8)
        self.assertEqual(coord.get_y(), 25.8)

    def test_x_property(self):
        """Test X property access."""
        coord = Coord2D(x=100.0)
        self.assertEqual(coord.x, 100.0)
        coord.x = 200.0
        self.assertEqual(coord.x, 200.0)

    def test_y_property(self):
        """Test Y property access."""
        coord = Coord2D(y=150.0)
        self.assertEqual(coord.y, 150.0)
        coord.y = 250.0
        self.assertEqual(coord.y, 250.0)

    def test_get_position(self):
        """Test getting position as tuple."""
        coord = Coord2D(x=10.0, y=20.0)
        position = coord.get_position()
        self.assertEqual(position, (10.0, 20.0))
        self.assertIsInstance(position, tuple)
        self.assertEqual(len(position), 2)

    def test_set_position(self):
        """Test setting position from tuple."""
        coord = Coord2D()
        coord.set_position((30.0, 40.0))
        self.assertEqual(coord.get_x(), 30.0)
        self.assertEqual(coord.get_y(), 40.0)

    def test_position_property(self):
        """Test position property access."""
        coord = Coord2D(x=5.0, y=10.0)
        self.assertEqual(coord.position, (5.0, 10.0))

    def test_set_position_updates_both_coordinates(self):
        """Test that set_position updates both X and Y."""
        coord = Coord2D(x=1.0, y=2.0)
        coord.set_position((99.0, 88.0))
        self.assertEqual(coord.get_x(), 99.0)
        self.assertEqual(coord.get_y(), 88.0)

    def test_negative_coordinates(self):
        """Test negative coordinate values."""
        coord = Coord2D(x=-10.0, y=-20.0)
        self.assertEqual(coord.get_x(), -10.0)
        self.assertEqual(coord.get_y(), -20.0)

    def test_zero_coordinates(self):
        """Test zero coordinate values."""
        coord = Coord2D(x=0.0, y=0.0)
        self.assertEqual(coord.get_x(), 0.0)
        self.assertEqual(coord.get_y(), 0.0)


class TestArea2D(unittest.TestCase):
    """Test cases for Area2D class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        area = Area2D()
        self.assertEqual(area.get_x(), 0.0)
        self.assertEqual(area.get_y(), 0.0)
        self.assertEqual(area.get_width(), 0.0)
        self.assertEqual(area.get_height(), 0.0)

    def test_init_with_values(self):
        """Test initialization with provided values."""
        area = Area2D(x=10.0, y=20.0, width=100.0, height=50.0)
        self.assertEqual(area.get_x(), 10.0)
        self.assertEqual(area.get_y(), 20.0)
        self.assertEqual(area.get_width(), 100.0)
        self.assertEqual(area.get_height(), 50.0)

    def test_get_width(self):
        """Test getting width."""
        area = Area2D(width=75.0)
        self.assertEqual(area.get_width(), 75.0)
        self.assertIsInstance(area.get_width(), float)

    def test_set_width(self):
        """Test setting width."""
        area = Area2D()
        area.set_width(125.0)
        self.assertEqual(area.get_width(), 125.0)

    def test_get_height(self):
        """Test getting height."""
        area = Area2D(height=60.0)
        self.assertEqual(area.get_height(), 60.0)
        self.assertIsInstance(area.get_height(), float)

    def test_set_height(self):
        """Test setting height."""
        area = Area2D()
        area.set_height(80.0)
        self.assertEqual(area.get_height(), 80.0)

    def test_width_property(self):
        """Test width property access."""
        area = Area2D(width=200.0)
        self.assertEqual(area.width, 200.0)
        area.width = 300.0
        self.assertEqual(area.width, 300.0)

    def test_height_property(self):
        """Test height property access."""
        area = Area2D(height=150.0)
        self.assertEqual(area.height, 150.0)
        area.height = 250.0
        self.assertEqual(area.height, 250.0)

    def test_get_size(self):
        """Test getting size as tuple."""
        area = Area2D(width=100.0, height=50.0)
        size = area.get_size()
        self.assertEqual(size, (100.0, 50.0))
        self.assertIsInstance(size, tuple)
        self.assertEqual(len(size), 2)

    def test_set_size(self):
        """Test setting size from tuple."""
        area = Area2D()
        area.set_size((200.0, 150.0))
        self.assertEqual(area.get_width(), 200.0)
        self.assertEqual(area.get_height(), 150.0)

    def test_size_property(self):
        """Test size property access."""
        area = Area2D(width=80.0, height=60.0)
        self.assertEqual(area.size, (80.0, 60.0))

    def test_get_center_x(self):
        """Test getting center X coordinate."""
        area = Area2D(x=10.0, width=100.0)
        center_x = area.get_center_x()
        self.assertEqual(center_x, 60.0)  # 10 + 100/2

    def test_get_center_y(self):
        """Test getting center Y coordinate."""
        area = Area2D(y=20.0, height=80.0)
        center_y = area.get_center_y()
        self.assertEqual(center_y, 60.0)  # 20 + 80/2

    def test_get_center(self):
        """Test getting center as tuple."""
        area = Area2D(x=0.0, y=0.0, width=100.0, height=50.0)
        center = area.get_center()
        self.assertEqual(center, (50.0, 25.0))
        self.assertIsInstance(center, tuple)
        self.assertEqual(len(center), 2)

    def test_center_property(self):
        """Test center property access."""
        area = Area2D(x=10.0, y=10.0, width=20.0, height=20.0)
        self.assertEqual(area.center, (20.0, 20.0))

    def test_inheritance_from_coord2d(self):
        """Test that Area2D inherits from Coord2D."""
        area = Area2D(x=5.0, y=10.0)
        self.assertIsInstance(area, Coord2D)
        self.assertEqual(area.get_position(), (5.0, 10.0))

    def test_position_methods_work(self):
        """Test that inherited position methods work."""
        area = Area2D()
        area.set_position((15.0, 25.0))
        self.assertEqual(area.get_x(), 15.0)
        self.assertEqual(area.get_y(), 25.0)


class TestCoord3D(unittest.TestCase):
    """Test cases for Coord3D class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        coord = Coord3D()
        self.assertEqual(coord.get_x(), 0.0)
        self.assertEqual(coord.get_y(), 0.0)
        self.assertEqual(coord.get_z(), 0.0)

    def test_init_with_values(self):
        """Test initialization with provided values."""
        coord = Coord3D(x=10.0, y=20.0, z=30.0)
        self.assertEqual(coord.get_x(), 10.0)
        self.assertEqual(coord.get_y(), 20.0)
        self.assertEqual(coord.get_z(), 30.0)

    def test_get_z(self):
        """Test getting Z coordinate."""
        coord = Coord3D(z=42.0)
        self.assertEqual(coord.get_z(), 42.0)
        self.assertIsInstance(coord.get_z(), float)

    def test_set_z(self):
        """Test setting Z coordinate."""
        coord = Coord3D()
        coord.set_z(55.0)
        self.assertEqual(coord.get_z(), 55.0)

    def test_z_property(self):
        """Test Z property access."""
        coord = Coord3D(z=100.0)
        self.assertEqual(coord.z, 100.0)
        coord.z = 200.0
        self.assertEqual(coord.z, 200.0)

    def test_get_position(self):
        """Test getting 3D position as tuple."""
        coord = Coord3D(x=10.0, y=20.0, z=30.0)
        position = coord.get_position()
        self.assertEqual(position, (10.0, 20.0, 30.0))
        self.assertIsInstance(position, tuple)
        self.assertEqual(len(position), 3)

    def test_set_position(self):
        """Test setting 3D position from tuple."""
        coord = Coord3D()
        coord.set_position((40.0, 50.0, 60.0))
        self.assertEqual(coord.get_x(), 40.0)
        self.assertEqual(coord.get_y(), 50.0)
        self.assertEqual(coord.get_z(), 60.0)

    def test_position_property(self):
        """Test 3D position property access."""
        coord = Coord3D(x=5.0, y=10.0, z=15.0)
        self.assertEqual(coord.position, (5.0, 10.0, 15.0))

    def test_inheritance_from_coord2d(self):
        """Test that Coord3D inherits from Coord2D."""
        coord = Coord3D(x=1.0, y=2.0, z=3.0)
        self.assertIsInstance(coord, Coord2D)
        self.assertEqual(coord.get_x(), 1.0)
        self.assertEqual(coord.get_y(), 2.0)

    def test_2d_methods_still_work(self):
        """Test that 2D coordinate methods still work."""
        coord = Coord3D()
        coord.set_x(10.0)
        coord.set_y(20.0)
        self.assertEqual(coord.get_x(), 10.0)
        self.assertEqual(coord.get_y(), 20.0)

    def test_negative_z_coordinate(self):
        """Test negative Z coordinate value."""
        coord = Coord3D(z=-10.0)
        self.assertEqual(coord.get_z(), -10.0)


class TestArea3D(unittest.TestCase):
    """Test cases for Area3D class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        area = Area3D()
        self.assertEqual(area.get_x(), 0.0)
        self.assertEqual(area.get_y(), 0.0)
        self.assertEqual(area.get_z(), 0.0)
        self.assertEqual(area.get_width(), 0.0)
        self.assertEqual(area.get_height(), 0.0)
        self.assertEqual(area.get_depth(), 0.0)

    def test_init_with_values(self):
        """Test initialization with provided values."""
        area = Area3D(
            x=10.0, y=20.0, z=30.0,
            width=100.0, height=50.0, depth=75.0
        )
        self.assertEqual(area.get_x(), 10.0)
        self.assertEqual(area.get_y(), 20.0)
        self.assertEqual(area.get_z(), 30.0)
        self.assertEqual(area.get_width(), 100.0)
        self.assertEqual(area.get_height(), 50.0)
        self.assertEqual(area.get_depth(), 75.0)

    def test_get_depth(self):
        """Test getting depth."""
        area = Area3D(depth=90.0)
        self.assertEqual(area.get_depth(), 90.0)
        self.assertIsInstance(area.get_depth(), float)

    def test_set_depth(self):
        """Test setting depth."""
        area = Area3D()
        area.set_depth(120.0)
        self.assertEqual(area.get_depth(), 120.0)

    def test_depth_property(self):
        """Test depth property access."""
        area = Area3D(depth=150.0)
        self.assertEqual(area.depth, 150.0)

    def test_get_size(self):
        """Test getting 3D size as tuple."""
        area = Area3D(width=100.0, height=50.0, depth=75.0)
        size = area.get_size()
        self.assertEqual(size, (100.0, 50.0, 75.0))
        self.assertIsInstance(size, tuple)
        self.assertEqual(len(size), 3)

    def test_set_size(self):
        """Test setting 3D size from tuple."""
        area = Area3D()
        area.set_size((200.0, 150.0, 100.0))
        self.assertEqual(area.get_width(), 200.0)
        self.assertEqual(area.get_height(), 150.0)
        self.assertEqual(area.get_depth(), 100.0)

    def test_size_property(self):
        """Test 3D size property access."""
        area = Area3D(width=80.0, height=60.0, depth=40.0)
        self.assertEqual(area.size, (80.0, 60.0, 40.0))

    def test_get_center_z(self):
        """Test getting center Z coordinate."""
        area = Area3D(z=10.0, depth=80.0)
        center_z = area.get_center_z()
        self.assertEqual(center_z, 50.0)  # 10 + 80/2

    def test_get_center(self):
        """Test getting 3D center as tuple."""
        area = Area3D(
            x=0.0, y=0.0, z=0.0,
            width=100.0, height=50.0, depth=80.0
        )
        center = area.get_center()
        self.assertEqual(center, (50.0, 25.0, 40.0))
        self.assertIsInstance(center, tuple)
        self.assertEqual(len(center), 3)

    def test_center_property(self):
        """Test 3D center property access."""
        area = Area3D(
            x=10.0, y=10.0, z=10.0,
            width=20.0, height=20.0, depth=20.0
        )
        self.assertEqual(area.center, (20.0, 20.0, 20.0))

    def test_inheritance_from_coord3d(self):
        """Test that Area3D inherits from Coord3D."""
        area = Area3D(x=5.0, y=10.0, z=15.0)
        self.assertIsInstance(area, Coord3D)
        position = area.get_position()
        self.assertEqual(position, (5.0, 10.0, 15.0))

    def test_inheritance_from_area2d(self):
        """Test that Area3D inherits from Area2D."""
        area = Area3D(x=5.0, y=10.0, width=100.0, height=50.0)
        self.assertIsInstance(area, Area2D)
        self.assertEqual(area.get_width(), 100.0)
        self.assertEqual(area.get_height(), 50.0)

    def test_2d_methods_still_work(self):
        """Test that 2D area methods still work."""
        area = Area3D()
        area.set_width(100.0)
        area.set_height(50.0)
        self.assertEqual(area.get_width(), 100.0)
        self.assertEqual(area.get_height(), 50.0)

    def test_position_methods_work(self):
        """Test that 3D position methods work."""
        area = Area3D()
        area.set_position((15.0, 25.0, 35.0))
        self.assertEqual(area.get_x(), 15.0)
        self.assertEqual(area.get_y(), 25.0)
        self.assertEqual(area.get_z(), 35.0)

    def test_complex_area_calculation(self):
        """Test complex area with all values."""
        area = Area3D(
            x=100.0, y=200.0, z=300.0,
            width=50.0, height=60.0, depth=70.0
        )

        # Check position
        self.assertEqual(area.get_position(), (100.0, 200.0, 300.0))

        # Check size
        self.assertEqual(area.get_size(), (50.0, 60.0, 70.0))

        # Check center
        center = area.get_center()
        self.assertEqual(center[0], 125.0)  # 100 + 50/2
        self.assertEqual(center[1], 230.0)  # 200 + 60/2
        self.assertEqual(center[2], 335.0)  # 300 + 70/2


class TestCoordIntegration(unittest.TestCase):
    """Integration tests for coordinate classes."""

    def test_coord2d_to_coord3d_conversion(self):
        """Test converting 2D coordinates to 3D."""
        coord2d = Coord2D(x=10.0, y=20.0)
        coord3d = Coord3D(x=coord2d.get_x(), y=coord2d.get_y(), z=30.0)

        self.assertEqual(coord3d.get_x(), 10.0)
        self.assertEqual(coord3d.get_y(), 20.0)
        self.assertEqual(coord3d.get_z(), 30.0)

    def test_area2d_to_area3d_conversion(self):
        """Test converting 2D area to 3D area."""
        area2d = Area2D(x=5.0, y=10.0, width=100.0, height=50.0)
        area3d = Area3D(
            x=area2d.get_x(),
            y=area2d.get_y(),
            z=0.0,
            width=area2d.get_width(),
            height=area2d.get_height(),
            depth=75.0
        )

        self.assertEqual(area3d.get_x(), 5.0)
        self.assertEqual(area3d.get_y(), 10.0)
        self.assertEqual(area3d.get_width(), 100.0)
        self.assertEqual(area3d.get_height(), 50.0)
        self.assertEqual(area3d.get_depth(), 75.0)

    def test_multiple_instances_independence(self):
        """Test that multiple instances are independent."""
        coord1 = Coord2D(x=10.0, y=20.0)
        coord2 = Coord2D(x=30.0, y=40.0)

        coord1.set_x(100.0)

        self.assertEqual(coord1.get_x(), 100.0)
        self.assertEqual(coord2.get_x(), 30.0)  # Should remain unchanged

    def test_chaining_setters(self):
        """Test setting multiple values in sequence."""
        coord = Coord3D()
        coord.set_x(10.0)
        coord.set_y(20.0)
        coord.set_z(30.0)

        self.assertEqual(coord.get_position(), (10.0, 20.0, 30.0))

    def test_area_center_calculation_accuracy(self):
        """Test accuracy of center calculation for areas."""
        area = Area2D(x=0.0, y=0.0, width=10.0, height=10.0)
        center = area.get_center()

        self.assertAlmostEqual(center[0], 5.0, places=10)
        self.assertAlmostEqual(center[1], 5.0, places=10)


if __name__ == '__main__':
    unittest.main()

"""Unit tests for coord.py protocols module."""

import unittest

from pyrox.models.protocols.coord import (
    Coord2D,
    Area2D,
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


class TestCoordIntegration(unittest.TestCase):
    """Integration tests for coordinate classes."""

    def test_multiple_instances_independence(self):
        """Test that multiple instances are independent."""
        coord1 = Coord2D(x=10.0, y=20.0)
        coord2 = Coord2D(x=30.0, y=40.0)

        coord1.set_x(100.0)

        self.assertEqual(coord1.get_x(), 100.0)
        self.assertEqual(coord2.get_x(), 30.0)  # Should remain unchanged

    def test_area_center_calculation_accuracy(self):
        """Test accuracy of center calculation for areas."""
        area = Area2D(x=0.0, y=0.0, width=10.0, height=10.0)
        center = area.get_center()

        self.assertAlmostEqual(center[0], 5.0, places=10)
        self.assertAlmostEqual(center[1], 5.0, places=10)


if __name__ == '__main__':
    unittest.main()

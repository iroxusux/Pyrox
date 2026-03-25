"""Unit tests for kinematic.py protocols module."""

import unittest
import math
from pyrox.interfaces import IVelocity2D
from pyrox.models.protocols.kinematic import (
    AngularVelocity,
    Kinematic2D,
)


class TestAngularVelocity(unittest.TestCase):
    """Test cases for AngularVelocity class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        ang_vel = AngularVelocity()
        velocity = ang_vel.get_angular_velocity()
        self.assertEqual(velocity, (0.0, 0.0, 0.0))

    def test_get_angular_velocity(self):
        """Test getting angular velocity as tuple."""
        ang_vel = AngularVelocity()
        ang_vel.set_angular_velocity((10.0, 20.0, 30.0))
        velocity = ang_vel.get_angular_velocity()
        self.assertEqual(velocity, (10.0, 20.0, 30.0))
        self.assertIsInstance(velocity, tuple)
        self.assertEqual(len(velocity), 3)

    def test_set_angular_velocity(self):
        """Test setting angular velocity from tuple."""
        ang_vel = AngularVelocity()
        ang_vel.set_angular_velocity((45.0, 90.0, 135.0))
        velocity = ang_vel.get_angular_velocity()
        self.assertEqual(velocity[0], 45.0)
        self.assertEqual(velocity[1], 90.0)
        self.assertEqual(velocity[2], 135.0)

    def test_angular_velocity_property(self):
        """Test angular_velocity property access."""
        ang_vel = AngularVelocity()
        ang_vel.set_angular_velocity((15.0, 25.0, 35.0))
        self.assertEqual(ang_vel.angular_velocity, (15.0, 25.0, 35.0))

    def test_set_angular_velocity_updates_all_components(self):
        """Test that set_angular_velocity updates all components."""
        ang_vel = AngularVelocity()
        ang_vel.set_angular_velocity((1.0, 2.0, 3.0))
        ang_vel.set_angular_velocity((100.0, 200.0, 300.0))
        velocity = ang_vel.get_angular_velocity()
        self.assertEqual(velocity, (100.0, 200.0, 300.0))

    def test_negative_angular_velocity(self):
        """Test negative angular velocity values."""
        ang_vel = AngularVelocity()
        ang_vel.set_angular_velocity((-10.0, -20.0, -30.0))
        velocity = ang_vel.get_angular_velocity()
        self.assertEqual(velocity, (-10.0, -20.0, -30.0))

    def test_zero_angular_velocity(self):
        """Test zero angular velocity values."""
        ang_vel = AngularVelocity()
        ang_vel.set_angular_velocity((0.0, 0.0, 0.0))
        velocity = ang_vel.get_angular_velocity()
        self.assertEqual(velocity, (0.0, 0.0, 0.0))

    def test_mixed_angular_velocity(self):
        """Test mixed positive/negative angular velocity values."""
        ang_vel = AngularVelocity()
        ang_vel.set_angular_velocity((10.0, -20.0, 30.0))
        velocity = ang_vel.get_angular_velocity()
        self.assertEqual(velocity, (10.0, -20.0, 30.0))


class TestKinematic2D(unittest.TestCase):
    """Test cases for Kinematic2D class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        kin = Kinematic2D()
        self.assertEqual(kin.get_acceleration_x(), 0.0)
        self.assertEqual(kin.get_acceleration_y(), 0.0)
        self.assertEqual(kin.get_acceleration(), 0.0)

    def test_get_acceleration(self):
        """Test getting acceleration as tuple."""
        kin = Kinematic2D()
        kin.set_linear_acceleration(5.0, 10.0)
        self.assertEqual(kin.get_acceleration_x(), 5.0)
        self.assertEqual(kin.get_acceleration_y(), 10.0)
        self.assertGreater(kin.get_acceleration(), 0.0)

    def test_set_acceleration(self):
        """Test setting acceleration from tuple."""
        kin = Kinematic2D()
        kin.set_linear_acceleration(15.0, 25.0)
        self.assertEqual(kin.get_acceleration_x(), 15.0)
        self.assertEqual(kin.get_acceleration_y(), 25.0)
        kin.set_acceleration_x(35.0)
        kin.set_acceleration_y(45.0)
        self.assertEqual(kin.get_acceleration_x(), 35.0)
        self.assertEqual(kin.get_acceleration_y(), 45.0)

    def test_acceleration_property(self):
        """Test acceleration property access."""
        kin = Kinematic2D()
        kin.set_linear_acceleration(10.0, 20.0)
        self.assertEqual(int(kin.acceleration), 22)

    def test_linear_acceleration_property(self):
        """Test acceleration property access."""
        kin = Kinematic2D()
        kin.set_linear_acceleration(20.0, 30.0)
        self.assertEqual(kin.linear_acceleration, (20.0, 30.0))

    def test_inheritance_from_ivelocity2d(self):
        """Test that Kinematic2D inherits from Velocity2D."""
        kin = Kinematic2D()
        self.assertIsInstance(kin, IVelocity2D)
        kin.set_velocity_x(10.0)
        kin.set_velocity_y(20.0)
        self.assertEqual(kin.get_linear_velocity(), (10.0, 20.0))

    def test_velocity_and_acceleration_together(self):
        """Test velocity and acceleration working together."""
        kin = Kinematic2D()
        kin.set_velocity_x(10.0)
        kin.set_velocity_y(20.0)
        kin.set_linear_acceleration(5.0, 10.0)

        self.assertEqual(kin.get_linear_velocity(), (10.0, 20.0))
        self.assertEqual(kin.get_linear_acceleration(), (5.0, 10.0))

    def test_speed_calculation(self):
        """Test speed calculation with kinematic object."""
        kin = Kinematic2D()
        kin.set_velocity_x(3.0)
        kin.set_velocity_y(4.0)
        self.assertEqual(kin.get_speed(), 5.0)

    def test_negative_acceleration(self):
        """Test negative acceleration values (deceleration)."""
        kin = Kinematic2D()
        kin.set_linear_acceleration(-5.0, -10.0)
        self.assertEqual(kin.get_linear_acceleration(), (-5.0, -10.0))

    def test_zero_acceleration(self):
        """Test zero acceleration (constant velocity)."""
        kin = Kinematic2D()
        kin.set_velocity_x(10.0)
        kin.set_velocity_y(20.0)
        kin.set_linear_acceleration(0.0, 0.0)
        self.assertEqual(kin.get_linear_acceleration(), (0.0, 0.0))


class TestKinematicIntegration(unittest.TestCase):
    """Integration tests for kinematic classes."""

    def test_multiple_instances_independence(self):
        """Test that multiple instances are independent."""
        kin1 = Kinematic2D()
        kin2 = Kinematic2D()

        kin1.set_velocity_x(10.0)
        kin1.set_linear_acceleration(5.0, 10.0)

        # kin2 should remain unchanged
        self.assertEqual(kin2.get_velocity_x(), 0.0)
        self.assertEqual(kin2.get_linear_acceleration(), (0.0, 0.0))

    def test_velocity_without_acceleration(self):
        """Test velocity can exist without acceleration."""
        vel = Kinematic2D()
        vel.set_velocity_x(10.0)
        vel.set_velocity_y(20.0)
        self.assertEqual(vel.get_linear_velocity(), (10.0, 20.0))
        self.assertEqual(vel.get_speed(), math.sqrt(10**2 + 20**2))

    def test_motion_state_combinations(self):
        """Test various combinations of motion states."""
        # Stationary (no velocity, no acceleration)
        kin_stationary = Kinematic2D()
        self.assertEqual(kin_stationary.get_speed(), 0.0)
        self.assertEqual(kin_stationary.get_linear_acceleration(), (0.0, 0.0))

        # Constant velocity (velocity but no acceleration)
        kin_constant = Kinematic2D()
        kin_constant.set_velocity_x(10.0)
        kin_constant.set_velocity_y(10.0)
        self.assertGreater(kin_constant.get_speed(), 0.0)
        self.assertEqual(kin_constant.get_linear_acceleration(), (0.0, 0.0))

        # Accelerating (both velocity and acceleration)
        kin_accelerating = Kinematic2D()
        kin_accelerating.set_velocity_x(10.0)
        kin_accelerating.set_velocity_y(10.0)
        kin_accelerating.set_linear_acceleration(5.0, 5.0)
        self.assertGreater(kin_accelerating.get_speed(), 0.0)
        self.assertNotEqual(kin_accelerating.get_linear_acceleration(), (0.0, 0.0))


if __name__ == '__main__':
    unittest.main()

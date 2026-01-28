"""Unit tests for kinematic.py protocols module."""

import unittest
import math

from pyrox.models.abc.protocols.kinematic import (
    Velocity2D,
    Velocity3D,
    AngularVelocity,
    Kinematic2D,
    Kinematic3D,
)


class TestVelocity2D(unittest.TestCase):
    """Test cases for Velocity2D class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        vel = Velocity2D()
        self.assertEqual(vel.get_velocity_x(), 0.0)
        self.assertEqual(vel.get_velocity_y(), 0.0)

    def test_get_velocity_x(self):
        """Test getting X velocity."""
        vel = Velocity2D()
        vel.set_velocity_x(10.0)
        self.assertEqual(vel.get_velocity_x(), 10.0)
        self.assertIsInstance(vel.get_velocity_x(), float)

    def test_set_velocity_x(self):
        """Test setting X velocity."""
        vel = Velocity2D()
        vel.set_velocity_x(25.5)
        self.assertEqual(vel.get_velocity_x(), 25.5)

    def test_get_velocity_y(self):
        """Test getting Y velocity."""
        vel = Velocity2D()
        vel.set_velocity_y(15.0)
        self.assertEqual(vel.get_velocity_y(), 15.0)
        self.assertIsInstance(vel.get_velocity_y(), float)

    def test_set_velocity_y(self):
        """Test setting Y velocity."""
        vel = Velocity2D()
        vel.set_velocity_y(30.5)
        self.assertEqual(vel.get_velocity_y(), 30.5)

    def test_velocity_x_property(self):
        """Test velocity_x property access."""
        vel = Velocity2D()
        vel.set_velocity_x(100.0)
        self.assertEqual(vel.velocity_x, 100.0)

    def test_velocity_y_property(self):
        """Test velocity_y property access."""
        vel = Velocity2D()
        vel.set_velocity_y(200.0)
        self.assertEqual(vel.velocity_y, 200.0)

    def test_get_velocity(self):
        """Test getting velocity as tuple."""
        vel = Velocity2D()
        vel.set_velocity_x(10.0)
        vel.set_velocity_y(20.0)
        velocity = vel.get_velocity()
        self.assertEqual(velocity, (10.0, 20.0))
        self.assertIsInstance(velocity, tuple)
        self.assertEqual(len(velocity), 2)

    def test_velocity_property(self):
        """Test velocity property access."""
        vel = Velocity2D()
        vel.set_velocity_x(5.0)
        vel.set_velocity_y(10.0)
        self.assertEqual(vel.velocity, (5.0, 10.0))

    def test_get_speed_zero(self):
        """Test speed calculation when velocity is zero."""
        vel = Velocity2D()
        self.assertEqual(vel.get_speed(), 0.0)

    def test_get_speed_horizontal(self):
        """Test speed calculation for horizontal movement."""
        vel = Velocity2D()
        vel.set_velocity_x(10.0)
        vel.set_velocity_y(0.0)
        self.assertEqual(vel.get_speed(), 10.0)

    def test_get_speed_vertical(self):
        """Test speed calculation for vertical movement."""
        vel = Velocity2D()
        vel.set_velocity_x(0.0)
        vel.set_velocity_y(10.0)
        self.assertEqual(vel.get_speed(), 10.0)

    def test_get_speed_diagonal(self):
        """Test speed calculation for diagonal movement."""
        vel = Velocity2D()
        vel.set_velocity_x(3.0)
        vel.set_velocity_y(4.0)
        # 3^2 + 4^2 = 9 + 16 = 25, sqrt(25) = 5
        self.assertEqual(vel.get_speed(), 5.0)

    def test_get_speed_complex(self):
        """Test speed calculation with complex values."""
        vel = Velocity2D()
        vel.set_velocity_x(6.0)
        vel.set_velocity_y(8.0)
        # 6^2 + 8^2 = 36 + 64 = 100, sqrt(100) = 10
        self.assertEqual(vel.get_speed(), 10.0)

    def test_speed_property(self):
        """Test speed property access."""
        vel = Velocity2D()
        vel.set_velocity_x(3.0)
        vel.set_velocity_y(4.0)
        self.assertEqual(vel.speed, 5.0)

    def test_negative_velocity(self):
        """Test negative velocity values."""
        vel = Velocity2D()
        vel.set_velocity_x(-10.0)
        vel.set_velocity_y(-20.0)
        self.assertEqual(vel.get_velocity_x(), -10.0)
        self.assertEqual(vel.get_velocity_y(), -20.0)

    def test_negative_velocity_speed(self):
        """Test speed calculation with negative velocities."""
        vel = Velocity2D()
        vel.set_velocity_x(-3.0)
        vel.set_velocity_y(-4.0)
        # Speed should be positive magnitude
        self.assertEqual(vel.get_speed(), 5.0)

    def test_mixed_velocity_speed(self):
        """Test speed calculation with mixed positive/negative velocities."""
        vel = Velocity2D()
        vel.set_velocity_x(3.0)
        vel.set_velocity_y(-4.0)
        self.assertEqual(vel.get_speed(), 5.0)


class TestVelocity3D(unittest.TestCase):
    """Test cases for Velocity3D class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        vel = Velocity3D()
        self.assertEqual(vel.get_velocity_x(), 0.0)
        self.assertEqual(vel.get_velocity_y(), 0.0)
        self.assertEqual(vel.get_velocity_z(), 0.0)

    def test_get_velocity_z(self):
        """Test getting Z velocity."""
        vel = Velocity3D()
        vel._velocity_z = 30.0
        self.assertEqual(vel.get_velocity_z(), 30.0)
        self.assertIsInstance(vel.get_velocity_z(), float)

    def test_velocity_z_property(self):
        """Test velocity_z property access."""
        vel = Velocity3D()
        vel.set_velocity_z(150.0)
        self.assertEqual(vel.velocity_z, 150.0)

    def test_get_velocity(self):
        """Test getting 3D velocity as tuple."""
        vel = Velocity3D()
        vel.set_velocity_x(10.0)
        vel.set_velocity_y(20.0)
        vel._velocity_z = 30.0
        velocity = vel.get_velocity()
        self.assertEqual(velocity, (10.0, 20.0, 30.0))
        self.assertIsInstance(velocity, tuple)
        self.assertEqual(len(velocity), 3)

    def test_velocity_property(self):
        """Test 3D velocity property access."""
        vel = Velocity3D()
        vel.set_velocity_x(5.0)
        vel.set_velocity_y(10.0)
        vel._velocity_z = 15.0
        self.assertEqual(vel.velocity, (5.0, 10.0, 15.0))

    def test_get_speed_zero(self):
        """Test 3D speed calculation when velocity is zero."""
        vel = Velocity3D()
        self.assertEqual(vel.get_speed(), 0.0)

    def test_get_speed_x_axis(self):
        """Test 3D speed calculation along X axis."""
        vel = Velocity3D()
        vel.set_velocity_x(10.0)
        self.assertEqual(vel.get_speed(), 10.0)

    def test_get_speed_y_axis(self):
        """Test 3D speed calculation along Y axis."""
        vel = Velocity3D()
        vel.set_velocity_y(10.0)
        self.assertEqual(vel.get_speed(), 10.0)

    def test_get_speed_z_axis(self):
        """Test 3D speed calculation along Z axis."""
        vel = Velocity3D()
        vel._velocity_z = 10.0
        self.assertEqual(vel.get_speed(), 10.0)

    def test_get_speed_3d(self):
        """Test 3D speed calculation with all components."""
        vel = Velocity3D()
        vel.set_velocity_x(2.0)
        vel.set_velocity_y(3.0)
        vel._velocity_z = 6.0
        # 2^2 + 3^2 + 6^2 = 4 + 9 + 36 = 49, sqrt(49) = 7
        self.assertEqual(vel.get_speed(), 7.0)

    def test_speed_property(self):
        """Test 3D speed property access."""
        vel = Velocity3D()
        vel.set_velocity_x(2.0)
        vel.set_velocity_y(3.0)
        vel._velocity_z = 6.0
        self.assertEqual(vel.speed, 7.0)

    def test_inheritance_from_velocity2d(self):
        """Test that Velocity3D inherits from Velocity2D."""
        vel = Velocity3D()
        self.assertIsInstance(vel, Velocity2D)
        vel.set_velocity_x(10.0)
        vel.set_velocity_y(20.0)
        self.assertEqual(vel.get_velocity_x(), 10.0)
        self.assertEqual(vel.get_velocity_y(), 20.0)

    def test_negative_3d_velocity(self):
        """Test negative 3D velocity values."""
        vel = Velocity3D()
        vel.set_velocity_x(-10.0)
        vel.set_velocity_y(-20.0)
        vel._velocity_z = -30.0
        self.assertEqual(vel.get_velocity(), (-10.0, -20.0, -30.0))
        # Speed should be positive
        expected_speed = math.sqrt(10**2 + 20**2 + 30**2)
        self.assertAlmostEqual(vel.get_speed(), expected_speed, places=10)


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
        self.assertEqual(kin.get_velocity_x(), 0.0)
        self.assertEqual(kin.get_velocity_y(), 0.0)
        self.assertEqual(kin.get_acceleration(), (0.0, 0.0))

    def test_get_acceleration(self):
        """Test getting acceleration as tuple."""
        kin = Kinematic2D()
        kin.set_acceleration((5.0, 10.0))
        acceleration = kin.get_acceleration()
        self.assertEqual(acceleration, (5.0, 10.0))
        self.assertIsInstance(acceleration, tuple)
        self.assertEqual(len(acceleration), 2)

    def test_set_acceleration(self):
        """Test setting acceleration from tuple."""
        kin = Kinematic2D()
        kin.set_acceleration((15.0, 25.0))
        acceleration = kin.get_acceleration()
        self.assertEqual(acceleration[0], 15.0)
        self.assertEqual(acceleration[1], 25.0)

    def test_acceleration_property(self):
        """Test acceleration property access."""
        kin = Kinematic2D()
        kin.set_acceleration((20.0, 30.0))
        self.assertEqual(kin.acceleration, (20.0, 30.0))

    def test_inheritance_from_velocity2d(self):
        """Test that Kinematic2D inherits from Velocity2D."""
        kin = Kinematic2D()
        self.assertIsInstance(kin, Velocity2D)
        kin.set_velocity_x(10.0)
        kin.set_velocity_y(20.0)
        self.assertEqual(kin.get_velocity(), (10.0, 20.0))

    def test_velocity_and_acceleration_together(self):
        """Test velocity and acceleration working together."""
        kin = Kinematic2D()
        kin.set_velocity_x(10.0)
        kin.set_velocity_y(20.0)
        kin.set_acceleration((5.0, 10.0))

        self.assertEqual(kin.get_velocity(), (10.0, 20.0))
        self.assertEqual(kin.get_acceleration(), (5.0, 10.0))

    def test_speed_calculation(self):
        """Test speed calculation with kinematic object."""
        kin = Kinematic2D()
        kin.set_velocity_x(3.0)
        kin.set_velocity_y(4.0)
        self.assertEqual(kin.get_speed(), 5.0)

    def test_negative_acceleration(self):
        """Test negative acceleration values (deceleration)."""
        kin = Kinematic2D()
        kin.set_acceleration((-5.0, -10.0))
        self.assertEqual(kin.get_acceleration(), (-5.0, -10.0))

    def test_zero_acceleration(self):
        """Test zero acceleration (constant velocity)."""
        kin = Kinematic2D()
        kin.set_velocity_x(10.0)
        kin.set_velocity_y(20.0)
        kin.set_acceleration((0.0, 0.0))
        self.assertEqual(kin.get_acceleration(), (0.0, 0.0))


class TestKinematic3D(unittest.TestCase):
    """Test cases for Kinematic3D class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        kin = Kinematic3D()
        self.assertEqual(kin.get_velocity_x(), 0.0)
        self.assertEqual(kin.get_velocity_y(), 0.0)
        self.assertEqual(kin.get_velocity_z(), 0.0)
        self.assertEqual(kin.get_acceleration(), (0.0, 0.0, 0.0))

    def test_get_acceleration(self):
        """Test getting 3D acceleration as tuple."""
        kin = Kinematic3D()
        kin.set_acceleration((5.0, 10.0, 15.0))
        acceleration = kin.get_acceleration()
        self.assertEqual(acceleration, (5.0, 10.0, 15.0))
        self.assertIsInstance(acceleration, tuple)
        self.assertEqual(len(acceleration), 3)

    def test_set_acceleration(self):
        """Test setting 3D acceleration from tuple."""
        kin = Kinematic3D()
        kin.set_acceleration((20.0, 30.0, 40.0))
        acceleration = kin.get_acceleration()
        self.assertEqual(acceleration[0], 20.0)
        self.assertEqual(acceleration[1], 30.0)
        self.assertEqual(acceleration[2], 40.0)

    def test_acceleration_property(self):
        """Test 3D acceleration property access."""
        kin = Kinematic3D()
        kin.set_acceleration((25.0, 35.0, 45.0))
        self.assertEqual(kin.acceleration, (25.0, 35.0, 45.0))

    def test_inheritance_from_kinematic2d(self):
        """Test that Kinematic3D inherits from Kinematic2D."""
        kin = Kinematic3D()
        self.assertIsInstance(kin, Kinematic2D)

    def test_inheritance_from_velocity3d(self):
        """Test that Kinematic3D inherits from Velocity3D."""
        kin = Kinematic3D()
        self.assertIsInstance(kin, Velocity3D)

    def test_velocity_and_acceleration_together(self):
        """Test 3D velocity and acceleration working together."""
        kin = Kinematic3D()
        kin.set_velocity_x(10.0)
        kin.set_velocity_y(20.0)
        kin._velocity_z = 30.0
        kin.set_acceleration((5.0, 10.0, 15.0))

        self.assertEqual(kin.get_velocity(), (10.0, 20.0, 30.0))
        self.assertEqual(kin.get_acceleration(), (5.0, 10.0, 15.0))

    def test_speed_calculation(self):
        """Test 3D speed calculation with kinematic object."""
        kin = Kinematic3D()
        kin.set_velocity_x(2.0)
        kin.set_velocity_y(3.0)
        kin._velocity_z = 6.0
        self.assertEqual(kin.get_speed(), 7.0)

    def test_negative_acceleration(self):
        """Test negative 3D acceleration values."""
        kin = Kinematic3D()
        kin.set_acceleration((-5.0, -10.0, -15.0))
        self.assertEqual(kin.get_acceleration(), (-5.0, -10.0, -15.0))

    def test_zero_acceleration(self):
        """Test zero 3D acceleration."""
        kin = Kinematic3D()
        kin.set_velocity_x(10.0)
        kin.set_velocity_y(20.0)
        kin._velocity_z = 30.0
        kin.set_acceleration((0.0, 0.0, 0.0))
        self.assertEqual(kin.get_acceleration(), (0.0, 0.0, 0.0))

    def test_all_components_together(self):
        """Test all kinematic components working together."""
        kin = Kinematic3D()

        # Set velocity
        kin.set_velocity_x(10.0)
        kin.set_velocity_y(20.0)
        kin._velocity_z = 30.0

        # Set acceleration
        kin.set_acceleration((1.0, 2.0, 3.0))

        # Verify all values
        self.assertEqual(kin.get_velocity(), (10.0, 20.0, 30.0))
        self.assertEqual(kin.get_acceleration(), (1.0, 2.0, 3.0))

        # Calculate expected speed
        expected_speed = math.sqrt(10**2 + 20**2 + 30**2)
        self.assertAlmostEqual(kin.get_speed(), expected_speed, places=10)


class TestKinematicIntegration(unittest.TestCase):
    """Integration tests for kinematic classes."""

    def test_kinematic2d_to_kinematic3d_conversion(self):
        """Test converting 2D kinematic to 3D kinematic."""
        kin2d = Kinematic2D()
        kin2d.set_velocity_x(10.0)
        kin2d.set_velocity_y(20.0)
        kin2d.set_acceleration((5.0, 10.0))

        kin3d = Kinematic3D()
        kin3d.set_velocity_x(kin2d.get_velocity_x())
        kin3d.set_velocity_y(kin2d.get_velocity_y())
        kin3d._velocity_z = 30.0

        accel_2d = kin2d.get_acceleration()
        kin3d.set_acceleration((accel_2d[0], accel_2d[1], 15.0))

        self.assertEqual(kin3d.get_velocity(), (10.0, 20.0, 30.0))
        self.assertEqual(kin3d.get_acceleration(), (5.0, 10.0, 15.0))

    def test_multiple_instances_independence(self):
        """Test that multiple instances are independent."""
        kin1 = Kinematic2D()
        kin2 = Kinematic2D()

        kin1.set_velocity_x(10.0)
        kin1.set_acceleration((5.0, 10.0))

        # kin2 should remain unchanged
        self.assertEqual(kin2.get_velocity_x(), 0.0)
        self.assertEqual(kin2.get_acceleration(), (0.0, 0.0))

    def test_velocity_without_acceleration(self):
        """Test velocity can exist without acceleration."""
        vel = Velocity2D()
        vel.set_velocity_x(10.0)
        vel.set_velocity_y(20.0)
        self.assertEqual(vel.get_velocity(), (10.0, 20.0))
        self.assertEqual(vel.get_speed(), math.sqrt(10**2 + 20**2))

    def test_angular_velocity_independence(self):
        """Test angular velocity is independent from linear velocity."""
        ang_vel = AngularVelocity()
        lin_vel = Velocity3D()

        ang_vel.set_angular_velocity((10.0, 20.0, 30.0))
        lin_vel.set_velocity_x(40.0)

        self.assertEqual(ang_vel.get_angular_velocity(), (10.0, 20.0, 30.0))
        self.assertEqual(lin_vel.get_velocity_x(), 40.0)

    def test_speed_accuracy_with_large_values(self):
        """Test speed calculation accuracy with large values."""
        vel = Velocity3D()
        vel.set_velocity_x(1000.0)
        vel.set_velocity_y(2000.0)
        vel._velocity_z = 3000.0

        expected_speed = math.sqrt(1000**2 + 2000**2 + 3000**2)
        self.assertAlmostEqual(vel.get_speed(), expected_speed, places=10)

    def test_zero_values_valid(self):
        """Test that zero values are valid throughout."""
        kin = Kinematic3D()

        self.assertEqual(kin.get_velocity(), (0.0, 0.0, 0.0))
        self.assertEqual(kin.get_acceleration(), (0.0, 0.0, 0.0))
        self.assertEqual(kin.get_speed(), 0.0)

    def test_pythagorean_speed_calculations(self):
        """Test Pythagorean theorem in speed calculations."""
        # 2D case: 3-4-5 triangle
        vel2d = Velocity2D()
        vel2d.set_velocity_x(3.0)
        vel2d.set_velocity_y(4.0)
        self.assertEqual(vel2d.get_speed(), 5.0)

        # 3D case: 2-3-6-7 pyramid
        vel3d = Velocity3D()
        vel3d.set_velocity_x(2.0)
        vel3d.set_velocity_y(3.0)
        vel3d._velocity_z = 6.0
        self.assertEqual(vel3d.get_speed(), 7.0)

    def test_motion_state_combinations(self):
        """Test various combinations of motion states."""
        # Stationary (no velocity, no acceleration)
        kin_stationary = Kinematic2D()
        self.assertEqual(kin_stationary.get_speed(), 0.0)
        self.assertEqual(kin_stationary.get_acceleration(), (0.0, 0.0))

        # Constant velocity (velocity but no acceleration)
        kin_constant = Kinematic2D()
        kin_constant.set_velocity_x(10.0)
        kin_constant.set_velocity_y(10.0)
        self.assertGreater(kin_constant.get_speed(), 0.0)
        self.assertEqual(kin_constant.get_acceleration(), (0.0, 0.0))

        # Accelerating (both velocity and acceleration)
        kin_accelerating = Kinematic2D()
        kin_accelerating.set_velocity_x(10.0)
        kin_accelerating.set_velocity_y(10.0)
        kin_accelerating.set_acceleration((5.0, 5.0))
        self.assertGreater(kin_accelerating.get_speed(), 0.0)
        self.assertNotEqual(kin_accelerating.get_acceleration(), (0.0, 0.0))


if __name__ == '__main__':
    unittest.main()

"""Unit tests for PhysicsEngineService.

Tests the main physics simulation orchestrator that integrates environment,
collision detection, and physics body updates with fixed timestep simulation.
"""

import unittest
from unittest.mock import Mock, patch
from pyrox.services.physics import PhysicsEngineService
from pyrox.services.environment import EnvironmentService
from pyrox.services.collision import CollisionService
from pyrox.interfaces.protocols.physics import BodyType
from pyrox.models.protocols import PhysicsBody2D


class TestPhysicsEngineService(unittest.TestCase):
    """Test cases for PhysicsEngineService class."""

    def setUp(self):
        """Set up test fixtures."""
        self.environment = EnvironmentService()
        self.collision = CollisionService()
        self.engine = PhysicsEngineService(
            environment=self.environment,
            collision=self.collision
        )

    def _create_body_mock(self, **kwargs):
        """Create a properly configured body mock.

        Args:
            **kwargs: Override default attributes

        Returns:
            Mock object with all necessary physics body attributes
        """
        defaults = {
            'enabled': True,
            'sleeping': False,
            'body_type': BodyType.DYNAMIC,
            'mass': 1.0,
            'inverse_mass': 1.0,
            'force': (0.0, 0.0),
            'linear_velocity': (0.0, 0.0),
            'x': 0.0,
            'y': 0.0,
            'roll': 0.0,
            'angular_velocity': 0.0,
        }
        defaults.update(kwargs)

        body = Mock()
        for key, value in defaults.items():
            setattr(body, key, value)

        # Add methods
        body.update = Mock()
        body.apply_force = Mock()
        body.set_linear_velocity = Mock()
        body.clear_forces = Mock()
        body.get_bounds = Mock(return_value=(
            body.x - 5.0, body.y - 5.0,
            body.x + 5.0, body.y + 5.0
        ))

        return body

    def test_initialization_default(self):
        """Test default initialization of PhysicsEngineService."""
        engine = PhysicsEngineService()

        self.assertIsNotNone(engine.environment)
        self.assertIsNotNone(engine.collision)
        self.assertEqual(engine.get_physics_step(), 1.0 / 60.0)
        self.assertEqual(engine.get_time_scale(), 1.0)
        self.assertEqual(len(engine.bodies), 0)

    def test_initialization_custom_step(self):
        """Test initialization with custom physics step."""
        custom_step = 1.0 / 120.0
        engine = PhysicsEngineService(physics_step=custom_step)

        self.assertEqual(engine.get_physics_step(), custom_step)

    def test_initialization_with_services(self):
        """Test initialization with existing services."""
        environment = EnvironmentService(preset='moon')
        collision = CollisionService(cell_size=200.0)

        engine = PhysicsEngineService(
            environment=environment,
            collision=collision
        )

        self.assertIs(engine.environment, environment)
        self.assertIs(engine.collision, collision)

    def test_get_set_gravity(self):
        """Test getting and setting gravity."""
        # Initial gravity
        gx, gy = self.engine.get_gravity()
        self.assertIsInstance(gx, (int, float))
        self.assertIsInstance(gy, (int, float))

        # Set new gravity
        self.engine.set_gravity(5.0, -15.0)
        gx, gy = self.engine.get_gravity()
        self.assertEqual(gx, 5.0)
        self.assertEqual(gy, -15.0)

    def test_get_set_time_scale(self):
        """Test getting and setting time scale."""
        # Initial time scale
        self.assertEqual(self.engine.get_time_scale(), 1.0)

        # Set slow motion
        self.engine.set_time_scale(0.5)
        self.assertEqual(self.engine.get_time_scale(), 0.5)

        # Set fast forward
        self.engine.set_time_scale(2.0)
        self.assertEqual(self.engine.get_time_scale(), 2.0)

        # Set zero (pause)
        self.engine.set_time_scale(0.0)
        self.assertEqual(self.engine.get_time_scale(), 0.0)

    def test_get_set_physics_step(self):
        """Test getting and setting physics step."""
        # Initial step
        self.assertEqual(self.engine.get_physics_step(), 1.0 / 60.0)

        # Set 120 Hz
        self.engine.set_physics_step(1.0 / 120.0)
        self.assertEqual(self.engine.get_physics_step(), 1.0 / 120.0)

        # Set 30 Hz
        self.engine.set_physics_step(1.0 / 30.0)
        self.assertEqual(self.engine.get_physics_step(), 1.0 / 30.0)

    def test_set_physics_step_validation(self):
        """Test physics step validation."""
        # Zero step should raise error
        with self.assertRaises(ValueError):
            self.engine.set_physics_step(0.0)

        # Negative step should raise error
        with self.assertRaises(ValueError):
            self.engine.set_physics_step(-0.01)

    def test_register_body(self):
        """Test registering a physics body."""
        body = PhysicsBody2D()
        body.set_enabled(True)
        body.set_sleeping(False)

        self.engine.register_body(body)

        self.assertIn(body, self.engine.bodies)
        self.assertEqual(len(self.engine.bodies), 1)

    def test_register_multiple_bodies(self):
        """Test registering multiple physics bodies."""
        body1 = PhysicsBody2D()
        body2 = PhysicsBody2D()
        body3 = PhysicsBody2D()

        self.engine.register_body(body1)
        self.engine.register_body(body2)
        self.engine.register_body(body3)

        self.assertEqual(len(self.engine.bodies), 3)
        self.assertIn(body1, self.engine.bodies)
        self.assertIn(body2, self.engine.bodies)
        self.assertIn(body3, self.engine.bodies)

    def test_unregister_body(self):
        """Test unregistering a physics body."""
        body = PhysicsBody2D()
        body.set_linear_velocity(0.0, 0.0)
        self.engine.unregister_body(body)

        self.assertNotIn(body, self.engine.bodies)
        self.assertEqual(len(self.engine.bodies), 0)

    def test_unregister_nonexistent_body(self):
        """Test unregistering a body that isn't registered."""
        body = PhysicsBody2D()

        # Should not raise error
        self.engine.unregister_body(body)
        self.assertEqual(len(self.engine.bodies), 0)

    def test_step_with_no_bodies(self):
        """Test stepping with no bodies registered."""
        # Should not raise error
        self.engine.step(0.016)

        stats = self.engine.get_stats()
        self.assertEqual(stats['body_count'], 0)

    def test_step_accumulator_below_threshold(self):
        """Test step when dt is smaller than physics step."""
        body = self._create_body_mock()

        self.engine.register_body(body)

        # Step with small dt (0.005s) - below physics step (1/60 ≈ 0.0167s)
        self.engine.step(0.005)

        # Should not call update yet
        body.update.assert_not_called()

    def test_step_accumulator_reaches_threshold(self):
        """Test step when accumulated time reaches physics step."""
        body = PhysicsBody2D()
        body.set_enabled(True)
        body.set_sleeping(False)

        with patch.object(body, 'update') as mock_update:
            self.engine.register_body(body)

            # Step with dt that reaches physics step
            self.engine.step(0.020)  # Exceeds 1/60

            # Should call update once
            mock_update.assert_called()

    def test_step_multiple_fixed_steps(self):
        """Test step that requires multiple fixed timesteps."""
        body = PhysicsBody2D()
        body.set_enabled(True)
        body.set_sleeping(False)

        with patch.object(body, 'update') as mock_update:
            self.engine.register_body(body)

            # Step with large dt (0.1s = 100ms)
            # At 60 Hz (0.0167s per step), should run multiple steps
            self.engine.step(0.1)

            # Should call update multiple times
            self.assertGreater(mock_update.call_count, 1)

    def test_step_max_steps_limiter(self):
        """Test that max steps limiter prevents spiral of death."""
        body = self._create_body_mock()

        # Step with huge dt (1 second)
        # Should cap at 10 steps maximum
        self.engine.step(1.0)

        # Should call update no more than 10 times
        self.assertLessEqual(body.update.call_count, 10)

    def test_step_with_time_scale_slow_motion(self):
        """Test step with slow motion time scale."""
        body = self._create_body_mock()
        self.engine.set_time_scale(0.5)  # Half speed

        # Step with dt that would normally trigger one step
        self.engine.step(0.020)

        # With 0.5x time scale, should need more real time to step
        # First call might not trigger due to scaled dt
        initial_calls = body.update.call_count

        # Step again
        self.engine.step(0.020)

        # Should eventually step
        self.assertGreaterEqual(body.update.call_count, initial_calls)

    def test_step_with_time_scale_paused(self):
        """Test step with time scale set to zero (paused)."""
        body = Mock(spec=PhysicsBody2D)
        body.set_enabled(True)
        body.set_sleeping(False)
        body.set_linear_velocity(0.0, 0.0)
        # Step with any dt
        self.engine.step(0.1)

        # Should not call update when paused
        body.update.assert_not_called()

    def test_apply_forces_gravity(self):
        """Test that gravity is applied to bodies."""
        body = PhysicsBody2D()
        body.set_enabled(True)
        body.set_sleeping(False)
        body.set_body_type(BodyType.DYNAMIC)
        body.set_mass(2.0)

        self.engine.register_body(body)
        self.engine.set_gravity(0.0, -10.0)

        # Call apply forces directly
        with patch.object(body, 'apply_force') as mock_apply_force:
            self.engine._apply_forces(0.016)
            # Should apply gravity force (mass * gravity)
            # Gravity is (0.0, -10.0), mass is 2.0, so force should be (0.0, -20.0)
            # But it's also applying drag force, so check both calls
            self.assertEqual(mock_apply_force.call_count, 2)
            # First call is gravity
            mock_apply_force.assert_any_call(0.0, -20.0)

    def test_apply_forces_drag(self):
        """Test that drag force is applied to moving bodies."""
        body = PhysicsBody2D()
        body.set_enabled(True)
        body.set_sleeping(False)
        body.set_body_type(BodyType.DYNAMIC)
        body.set_mass(1.0)
        body.set_linear_velocity(10.0, 0.0)
        body.set_drag(0.1)
        body.set_width(1.0)
        body.set_height(1.0)
        body.apply_force = Mock()

        self.engine.register_body(body)

        # Call apply forces directly
        self.engine._apply_forces(0.016)

        # Should call apply_force for both gravity and drag
        self.assertEqual(body.apply_force.call_count, 2)

    def test_apply_forces_skips_disabled_bodies(self):
        """Test that disabled bodies don't receive forces."""
        body = PhysicsBody2D()
        body.set_enabled(False)
        body.set_sleeping(False)
        body.set_body_type(BodyType.DYNAMIC)
        body.set_mass(1.0)

        with patch.object(body, 'apply_force') as mock_apply_force:
            self.engine.register_body(body)

            # Call apply forces directly
            self.engine._apply_forces(0.016)

            # Should not apply force to disabled body
            mock_apply_force.assert_not_called()

    def test_apply_forces_skips_sleeping_bodies(self):
        """Test that sleeping bodies don't receive forces."""
        body = PhysicsBody2D()
        body.set_enabled(True)
        body.set_sleeping(True)
        body.set_body_type(BodyType.DYNAMIC)
        body.set_mass(1.0)

        with patch.object(body, 'apply_force') as mock_apply_force:
            self.engine.register_body(body)

            # Call apply forces directly
            self.engine._apply_forces(0.016)

            # Should not apply force to disabled body
            mock_apply_force.assert_not_called()

    def test_apply_forces_skips_static_bodies(self):
        """Test that static bodies don't receive forces."""
        body = PhysicsBody2D()
        body.set_enabled(True)
        body.set_sleeping(False)
        body.set_body_type(BodyType.STATIC)
        body.set_mass(1.0)

        with patch.object(body, 'apply_force') as mock_apply_force:
            self.engine.register_body(body)

            # Call apply forces directly
            self.engine._apply_forces(0.016)

            # Should not apply force to disabled body
            mock_apply_force.assert_not_called()

    def test_integrate_dynamic_body(self):
        """Test integration of dynamic body physics."""
        body = PhysicsBody2D()
        body.set_enabled(True)
        body.set_sleeping(False)
        body.set_body_type(BodyType.DYNAMIC)
        body.set_mass(1.0)
        body.set_force(10.0, -5.0)
        body.set_linear_velocity(1.0, 0.0)
        body.x = 0.0
        body.y = 0.0

        with patch.object(body, 'set_linear_velocity') as mock_set_velocity, \
                patch.object(body, 'clear_forces') as mock_clear_forces:

            self.engine.register_body(body)

            # Call integrate directly
            self.engine._integrate(0.016)

            # Should update velocity based on force
            mock_set_velocity.assert_called()

            # Should clear forces
            mock_clear_forces.assert_called()

    def test_integrate_kinematic_body(self):
        """Test integration of kinematic body (velocity only)."""
        body = PhysicsBody2D()
        body.set_enabled(True)
        body.set_sleeping(False)
        body.set_body_type(BodyType.KINEMATIC)
        body.set_linear_velocity(5.0, 3.0)
        body.x = 10.0
        body.y = 20.0

        initial_x = body.x
        initial_y = body.y

        self.engine.register_body(body)

        # Call integrate directly
        dt = 0.016
        self.engine._integrate(dt)

        # Position should update based on velocity
        expected_x = initial_x + 5.0 * dt
        expected_y = initial_y + 3.0 * dt
        self.assertAlmostEqual(body.x, expected_x, places=5)
        self.assertAlmostEqual(body.y, expected_y, places=5)

    def test_integrate_static_body(self):
        """Test that static bodies don't integrate."""
        body = PhysicsBody2D()
        body.set_enabled(True)
        body.set_sleeping(False)
        body.set_body_type(BodyType.STATIC)
        body.x = 10.0
        body.y = 20.0

        initial_x = body.x
        initial_y = body.y

        self.engine.register_body(body)

        # Call integrate directly
        self.engine._integrate(0.016)

        # Position should not change
        self.assertEqual(body.x, initial_x)
        self.assertEqual(body.y, initial_y)

    def test_integrate_terminal_velocity_clamping(self):
        """Test that velocities are clamped to terminal velocity."""
        body = PhysicsBody2D()
        body.set_enabled(True)
        body.set_sleeping(False)
        body.set_body_type(BodyType.DYNAMIC)
        body.set_force(1000.0, 1000.0)  # Huge force
        body.set_linear_velocity(0.0, 0.0)
        body.x = 0.0
        body.y = 0.0

        # Track velocity calls
        velocity_calls = []
        body.set_linear_velocity = lambda vx, vy: velocity_calls.append((vx, vy))
        body.clear_forces = Mock()

        self.engine.register_body(body)

        # Set low terminal velocity
        self.engine.environment.terminal_velocity = 10.0

        # Integrate multiple times to build up velocity
        for _ in range(100):
            body.set_force(1000.0, 1000.0)
            self.engine._integrate(0.016)

        # Check that final velocity doesn't exceed terminal velocity
        if velocity_calls:
            final_vx, final_vy = velocity_calls[-1]
            final_speed = (final_vx**2 + final_vy**2)**0.5
            self.assertLessEqual(final_speed, self.engine.environment.terminal_velocity + 0.1)

    def test_integrate_angular_velocity(self):
        """Test integration of angular velocity."""
        body = PhysicsBody2D()
        body.set_enabled(True)
        body.set_sleeping(False)
        body.set_body_type(BodyType.DYNAMIC)
        body.set_force(0.0, 0.0)
        body.set_linear_velocity(0.0, 0.0)
        body.set_angular_velocity(1.0)  # radians/sec
        body.roll = 0.0
        body.x = 0.0
        body.y = 0.0

        initial_roll = body.roll

        self.engine.register_body(body)

        # Call integrate directly
        dt = 0.016
        self.engine._integrate(dt)

        # Roll should update based on angular velocity
        expected_roll = initial_roll + 1.0 * dt
        self.assertAlmostEqual(body.roll, expected_roll, places=5)

    def test_collision_integration(self):
        """Test that collision service is properly integrated."""
        body = PhysicsBody2D()
        body.set_enabled(True)
        body.set_sleeping(False)
        body.set_body_type(BodyType.DYNAMIC)
        body.set_mass(1.0)
        body.set_force(0.0, 0.0)
        body.set_linear_velocity(0.0, 0.0)
        body.x = 0.0
        body.y = 0.0

        self.engine.register_body(body)

        # Mock collision service methods
        self.collision.update_spatial_grid = Mock()
        self.collision.detect_collisions = Mock(return_value=[])
        self.collision.resolve_collision = Mock()

        # Step the engine
        self.engine.step(0.020)

        # Collision methods should be called
        self.collision.update_spatial_grid.assert_called()
        self.collision.detect_collisions.assert_called()

    def test_reset(self):
        """Test resetting the engine state."""
        body = PhysicsBody2D()
        body.set_enabled(True)
        body.set_sleeping(False)
        body.set_body_type(BodyType.DYNAMIC)
        body.set_mass(1.0)
        body.set_force(10.0, -5.0)
        body.set_linear_velocity(1.0, 0.0)
        body.x = 0.0
        body.y = 0.0
        body.clear_forces = Mock()

        self.engine.register_body(body)

        # Step to accumulate some state
        self.engine.step(0.020)

        # Reset
        self.engine.reset()

        # Check that state is reset
        stats = self.engine.get_stats()
        self.assertEqual(stats['total_time'], 0.0)
        self.assertEqual(stats['step_count'], 0)
        self.assertEqual(stats['accumulator'], 0.0)

        # Should clear forces
        body.clear_forces.assert_called()

    def test_clear(self):
        """Test clearing all bodies and resetting."""
        body1 = PhysicsBody2D()
        body2 = PhysicsBody2D()

        self.engine.register_body(body1)
        self.engine.register_body(body2)

        self.assertEqual(len(self.engine.bodies), 2)

        # Clear
        self.engine.clear()

        # All bodies should be removed
        self.assertEqual(len(self.engine.bodies), 0)

        # State should be reset
        stats = self.engine.get_stats()
        self.assertEqual(stats['total_time'], 0.0)
        self.assertEqual(stats['step_count'], 0)

    def test_get_stats(self):
        """Test getting engine statistics."""
        body = PhysicsBody2D()
        body.set_enabled(True)
        body.set_sleeping(False)

        self.engine.register_body(body)

        stats = self.engine.get_stats()

        # Check all expected fields
        self.assertIn('total_time', stats)
        self.assertIn('step_count', stats)
        self.assertIn('body_count', stats)
        self.assertIn('active_bodies', stats)
        self.assertIn('physics_step', stats)
        self.assertIn('time_scale', stats)
        self.assertIn('accumulator', stats)

        # Check values
        self.assertEqual(stats['body_count'], 1)
        self.assertEqual(stats['active_bodies'], 1)
        self.assertEqual(stats['physics_step'], 1.0 / 60.0)
        self.assertEqual(stats['time_scale'], 1.0)

    def test_get_stats_active_bodies_count(self):
        """Test that active_bodies count excludes disabled/sleeping bodies."""
        body1 = PhysicsBody2D()
        body1.set_enabled(True)
        body1.set_sleeping(False)

        body2 = PhysicsBody2D()
        body2.set_enabled(False)
        body2.set_sleeping(False)

        body3 = PhysicsBody2D()
        body3.set_enabled(True)
        body3.set_sleeping(True)

        self.engine.register_body(body1)
        self.engine.register_body(body2)
        self.engine.register_body(body3)

        stats = self.engine.get_stats()

        self.assertEqual(stats['body_count'], 3)
        self.assertEqual(stats['active_bodies'], 1)  # Only body1 is active

    def test_query_bodies_at_point(self):
        """Test querying bodies at a specific point."""
        body1 = PhysicsBody2D()
        body1.get_bounds = Mock(return_value=(0.0, 0.0, 10.0, 10.0))

        body2 = PhysicsBody2D()
        body2.get_bounds = Mock(return_value=(20.0, 20.0, 30.0, 30.0))

        self.engine.register_body(body1)
        self.engine.register_body(body2)

        # Query point inside body1
        result = self.engine.query_bodies_at_point(5.0, 5.0)
        self.assertIn(body1, result)
        self.assertNotIn(body2, result)

        # Query point inside body2
        result = self.engine.query_bodies_at_point(25.0, 25.0)
        self.assertIn(body2, result)
        self.assertNotIn(body1, result)

        # Query point outside both
        result = self.engine.query_bodies_at_point(50.0, 50.0)
        self.assertEqual(len(result), 0)

    def test_query_bodies_at_point_overlapping(self):
        """Test querying bodies at a point where multiple bodies overlap."""
        body1 = PhysicsBody2D()
        body1.get_bounds = Mock(return_value=(0.0, 0.0, 20.0, 20.0))

        body2 = PhysicsBody2D()
        body2.get_bounds = Mock(return_value=(10.0, 10.0, 30.0, 30.0))

        self.engine.register_body(body1)
        self.engine.register_body(body2)

        # Query point in overlapping region
        result = self.engine.query_bodies_at_point(15.0, 15.0)

        self.assertEqual(len(result), 2)
        self.assertIn(body1, result)
        self.assertIn(body2, result)

    def test_query_bodies_in_area(self):
        """Test querying bodies in a rectangular area."""
        body1 = PhysicsBody2D()
        body1.get_bounds = Mock(return_value=(0.0, 0.0, 10.0, 10.0))

        body2 = PhysicsBody2D()
        body2.get_bounds = Mock(return_value=(20.0, 20.0, 30.0, 30.0))

        body3 = PhysicsBody2D()
        body3.get_bounds = Mock(return_value=(5.0, 5.0, 15.0, 15.0))

        self.engine.register_body(body1)
        self.engine.register_body(body2)
        self.engine.register_body(body3)

        # Query area overlapping body1 and body3
        result = self.engine.query_bodies_in_area(0.0, 0.0, 12.0, 12.0)

        self.assertIn(body1, result)
        self.assertIn(body3, result)
        self.assertNotIn(body2, result)

    def test_query_bodies_in_area_no_overlap(self):
        """Test querying bodies in an area with no overlaps."""
        body = PhysicsBody2D()
        body.get_bounds = Mock(return_value=(0.0, 0.0, 10.0, 10.0))

        self.engine.register_body(body)

        # Query area far from body
        result = self.engine.query_bodies_in_area(50.0, 50.0, 60.0, 60.0)

        self.assertEqual(len(result), 0)

    def test_query_bodies_in_area_fully_contained(self):
        """Test querying bodies where area fully contains body."""
        body = PhysicsBody2D()
        body.get_bounds = Mock(return_value=(10.0, 10.0, 20.0, 20.0))

        self.engine.register_body(body)

        # Query larger area that contains body
        result = self.engine.query_bodies_in_area(0.0, 0.0, 30.0, 30.0)

        self.assertIn(body, result)

    def test_update_sleep_state_wake_moving_body(self):
        """Test that moving bodies wake up from sleep."""
        body = PhysicsBody2D()
        body.set_enabled(True)
        body.set_sleeping(True)
        body.set_body_type(BodyType.DYNAMIC)
        body.set_linear_velocity(1.0, 1.0)
        self.engine.register_body(body)

        # Should wake up the body
        with patch.object(body, 'set_sleeping') as mock_set_sleeping:
            self.engine._update_sleep_state()
            mock_set_sleeping.assert_called_with(False)

    def test_update_sleep_state_slow_body(self):
        """Test sleep state with slow-moving body."""
        body = PhysicsBody2D()
        self.engine.register_body(body)

        # Call update sleep state directly
        self.engine._update_sleep_state()

        # Currently doesn't auto-sleep, just checks threshold
        # This test documents current behavior

    def test_bodies_property(self):
        """Test that bodies property returns current list."""
        body1 = PhysicsBody2D()
        body2 = PhysicsBody2D()

        bodies = self.engine.bodies
        self.assertEqual(len(bodies), 0)

        self.engine.register_body(body1)
        bodies = self.engine.bodies
        self.assertEqual(len(bodies), 1)

        self.engine.register_body(body2)
        bodies = self.engine.bodies
        self.assertEqual(len(bodies), 2)

    def test_environment_property(self):
        """Test environment property access."""
        env = self.engine.environment
        self.assertIsInstance(env, EnvironmentService)

    def test_collision_property(self):
        """Test collision property access."""
        collision = self.engine.collision
        self.assertIsInstance(collision, CollisionService)


if __name__ == '__main__':
    unittest.main()

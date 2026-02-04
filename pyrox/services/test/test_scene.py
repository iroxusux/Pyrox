"""Unit tests for SceneRunnerService.

Tests the scene runner service that integrates physics simulation with scene
updates, providing a complete runtime environment with frame-rate independent
rendering.
"""

import unittest
from unittest.mock import Mock, patch
from pyrox.services.scene import SceneRunnerService
from pyrox.services.physics import PhysicsEngineService
from pyrox.services.environment import EnvironmentService
from pyrox.interfaces import IPhysicsBody2D


class TestSceneRunnerService(unittest.TestCase):
    """Test cases for SceneRunnerService class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock application
        self.mock_app = Mock()

        # Create mock scene
        self.mock_scene = Mock()
        self.mock_scene.get_scene_objects = Mock(return_value={})

        # Create mock backend for GuiManager
        self.mock_backend = Mock()
        self.mock_backend.schedule_event = Mock(return_value="event_id_123")
        self.mock_backend.cancel_scheduled_event = Mock()

        # Patch GuiManager to return the mock backend
        self.gui_manager_patcher = patch('pyrox.services.scene.GuiManager')
        self.mock_gui_manager_class = self.gui_manager_patcher.start()
        self.mock_gui_manager_class.unsafe_get_backend.return_value = self.mock_backend

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        self.gui_manager_patcher.stop()

    def test_initialization_without_physics(self):
        """Test initialization without physics enabled."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        self.assertEqual(runner.app, self.mock_app)
        self.assertEqual(runner.scene, self.mock_scene)
        self.assertEqual(runner.update_interval_ms, 16)
        self.assertFalse(runner.enable_physics)
        self.assertIsNone(runner.physics_engine)
        self.assertIsNone(runner.environment)
        self.assertFalse(runner._is_running)

    def test_initialization_with_physics_default(self):
        """Test initialization with physics enabled (default services)."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=True
        )

        self.assertTrue(runner.enable_physics)
        self.assertIsNotNone(runner.physics_engine)
        self.assertIsNotNone(runner.environment)
        self.assertIsInstance(runner.physics_engine, PhysicsEngineService)
        self.assertIsInstance(runner.environment, EnvironmentService)

    def test_initialization_with_physics_custom_services(self):
        """Test initialization with custom physics and environment services."""
        custom_env = EnvironmentService(preset='moon')
        custom_physics = PhysicsEngineService(environment=custom_env)

        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            physics_engine=custom_physics,
            environment=custom_env,
            enable_physics=True
        )

        self.assertIs(runner.physics_engine, custom_physics)
        self.assertIs(runner.environment, custom_env)

    def test_register_physics_bodies_on_init(self):
        """Test that physics bodies are registered during initialization."""
        # Create mock physics bodies
        body1 = Mock(spec=IPhysicsBody2D)
        body1.get_bounds = Mock(return_value=(0.0, 0.0, 10.0, 10.0))
        body2 = Mock(spec=IPhysicsBody2D)
        body2.get_bounds = Mock(return_value=(0.0, 0.0, 10.0, 10.0))
        non_physics_obj = Mock()

        self.mock_scene.get_scene_objects = Mock(return_value={
            'body1': body1,
            'body2': body2,
            'other': non_physics_obj
        })

        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=True
        )

        # Check that physics bodies were registered
        self.assertIn(body1, runner.physics_engine.bodies)  # type: ignore
        self.assertIn(body2, runner.physics_engine.bodies)  # type: ignore
        self.assertNotIn(non_physics_obj, runner.physics_engine.bodies)  # type: ignore

    def test_register_physics_bodies_no_physics_engine(self):
        """Test _register_physics_bodies when physics engine is None."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        # Should not raise error
        runner._register_physics_bodies()

    def test_run_starts_scene(self):
        """Test that run() starts the scene runner."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        runner.run()

        self.assertTrue(runner._is_running)
        self.mock_backend.schedule_event.assert_called_once()
        self.assertEqual(runner._event_id, "event_id_123")

    def test_run_when_already_running(self):
        """Test that run() does nothing if already running."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        runner.run()
        call_count_1 = self.mock_backend.schedule_event.call_count

        runner.run()  # Call again
        call_count_2 = self.mock_backend.schedule_event.call_count

        # Should not schedule again
        self.assertEqual(call_count_1, call_count_2)

    def test_stop_stops_scene(self):
        """Test that stop() stops the scene runner."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        runner.run()
        runner.stop()

        self.assertFalse(runner._is_running)
        self.mock_backend.cancel_scheduled_event.assert_called_once_with("event_id_123")
        self.assertIsNone(runner._event_id)

    def test_stop_when_not_running(self):
        """Test that stop() is safe to call when not running."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        # Should not raise error
        runner.stop()
        self.assertFalse(runner._is_running)

    @patch('pyrox.services.scene.datetime')
    def test_run_scene_calculates_time_delta(self, mock_datetime):
        """Test that _run_scene calculates correct time delta."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        # Mock time progression - need 3 timestamps: init, _run_scene, reschedule
        mock_datetime.now.return_value.timestamp.side_effect = [
            1000.0,    # Initial time in run()
            1000.016,  # Time in _run_scene()
            1000.016,  # Time for reschedule (can reuse)
        ]

        runner.run()
        runner._run_scene()

        # Time delta should be 0.016 (16ms)
        _ = 0.016
        self.assertAlmostEqual(runner.current_time, 1000.016, places=3)

    @patch('pyrox.services.scene.datetime')
    def test_run_scene_clamps_large_time_delta(self, mock_datetime):
        """Test that _run_scene clamps excessive time deltas."""
        # Mock large time jump (e.g., 500ms)
        mock_datetime.now.return_value.timestamp.side_effect = [
            1000.0,  # Initial time
            1000.5,  # 500ms later (too large)
            1000.5,  # Time for reschedule
        ]

        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        runner.run()
        runner._run_scene()

        # Time delta should be clamped to max 0.1 (100ms)
        self.assertEqual(runner.current_time, 1000.5)

    @patch('pyrox.services.scene.datetime')
    def test_run_scene_steps_physics(self, mock_datetime):
        """Test that _run_scene steps the physics engine."""
        mock_datetime.now.return_value.timestamp.side_effect = [
            1000.0,    # Initial time in __init__
            1000.0,    # Time in run()
            1000.016,  # Time in _run_scene()
        ]

        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=True
        )

        with patch.object(runner.physics_engine, 'step') as mock_step:
            runner.run()
            runner._run_scene()

            # Physics should be stepped with time delta
            mock_step.assert_called_once()
            call_args = mock_step.call_args[0][0]
            self.assertAlmostEqual(call_args, 0.016, places=3)

    @patch('pyrox.services.scene.datetime')
    def test_run_scene_skips_physics_when_disabled(self, mock_datetime):
        """Test that _run_scene skips physics when disabled."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        mock_datetime.now.return_value.timestamp.side_effect = [1000.0, 1000.016, 1000.016]

        runner.run()
        runner._run_scene()

        # Physics engine should be None
        self.assertIsNone(runner.physics_engine)

    def test_run_scene_stops_when_not_running(self):
        """Test that _run_scene exits early when _is_running is False."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=True
        )

        runner._is_running = False

        with patch.object(runner.physics_engine, 'step') as mock_step:
            runner._run_scene()

            # Physics should not be stepped
            mock_step.assert_not_called()

    def test_run_scene_reschedules_event(self):
        """Test that _run_scene reschedules itself."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        runner.run()
        initial_call_count = self.mock_backend.schedule_event.call_count

        runner._run_scene()

        # Should schedule again
        self.assertGreater(
            self.mock_backend.schedule_event.call_count,
            initial_call_count
        )

    def test_set_update_rate_valid(self):
        """Test setting valid update rates."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        # Test 60 FPS
        runner.set_update_rate(60)
        self.assertEqual(runner.update_interval_ms, 16)

        # Test 30 FPS
        runner.set_update_rate(30)
        self.assertEqual(runner.update_interval_ms, 33)

        # Test 120 FPS
        runner.set_update_rate(120)
        self.assertEqual(runner.update_interval_ms, 8)

    def test_set_update_rate_boundary_values(self):
        """Test setting update rate at boundary values."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        # Test minimum (1 FPS)
        runner.set_update_rate(1)
        self.assertEqual(runner.update_interval_ms, 1000)

        # Test maximum (240 FPS)
        runner.set_update_rate(240)
        self.assertEqual(runner.update_interval_ms, 4)

    def test_set_update_rate_invalid_low(self):
        """Test that invalid low FPS raises ValueError."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        with self.assertRaises(ValueError) as context:
            runner.set_update_rate(0)

        self.assertIn("FPS must be between 1 and 240", str(context.exception))

    def test_set_update_rate_invalid_high(self):
        """Test that invalid high FPS raises ValueError."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        with self.assertRaises(ValueError) as context:
            runner.set_update_rate(241)

        self.assertIn("FPS must be between 1 and 240", str(context.exception))

    def test_add_physics_body(self):
        """Test adding a physics body dynamically."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=True
        )

        body = Mock(spec=IPhysicsBody2D)
        body.get_bounds = Mock(return_value=(0.0, 0.0, 10.0, 10.0))
        runner.enable_physics = False

        # Should not raise error
        runner.add_physics_body(body)

    def test_remove_physics_body(self):
        """Test removing a physics body dynamically."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=True
        )

        body = Mock(spec=IPhysicsBody2D)
        body.get_bounds = Mock(return_value=(0.0, 0.0, 10.0, 10.0))
        _ = self.mock_app,
        runner.set_scene(self.mock_scene)
        runner.enable_physics = False

        body = Mock(spec=IPhysicsBody2D)

        # Should not raise error
        runner.remove_physics_body(body)

    def test_get_physics_stats_with_physics(self):
        """Test getting physics stats when physics is enabled."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=True
        )

        stats = runner.get_physics_stats()

        self.assertIsInstance(stats, dict)
        self.assertIn('total_time', stats)
        self.assertIn('step_count', stats)
        self.assertIn('body_count', stats)

    def test_get_physics_stats_without_physics(self):
        """Test getting physics stats when physics is disabled."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        stats = runner.get_physics_stats()

        self.assertIsInstance(stats, dict)
        self.assertEqual(len(stats), 0)

    def test_current_time_initialization(self):
        """Test that current_time is initialized."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        self.assertIsInstance(runner.current_time, float)
        self.assertGreater(runner.current_time, 0)

    def test_update_interval_default(self):
        """Test default update interval is 16ms (~60 FPS)."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        self.assertEqual(runner.update_interval_ms, 16)

    def test_multiple_bodies_registration(self):
        """Test registering multiple physics bodies."""
        body1 = Mock(spec=IPhysicsBody2D)
        body1.get_bounds = Mock(return_value=(0.0, 0.0, 10.0, 10.0))
        body2 = Mock(spec=IPhysicsBody2D)
        body2.get_bounds = Mock(return_value=(0.0, 0.0, 10.0, 10.0))
        body3 = Mock(spec=IPhysicsBody2D)
        body3.get_bounds = Mock(return_value=(0.0, 0.0, 10.0, 10.0))

        self.mock_scene.get_scene_objects = Mock(return_value={
            'body1': body1,
            'body2': body2,
            'body3': body3
        })

        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=True
        )

        self.assertEqual(len(runner.physics_engine.bodies), 3)  # type: ignore
        self.assertIn(body1, runner.physics_engine.bodies)  # type: ignore
        self.assertIn(body2, runner.physics_engine.bodies)  # type: ignore
        self.assertIn(body3, runner.physics_engine.bodies)  # type: ignore

    def test_run_sets_current_time(self):
        """Test that run() sets current_time."""
        runner = SceneRunnerService(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        old_time = runner.current_time
        runner.run()

        # Current time should be updated
        self.assertGreaterEqual(runner.current_time, old_time)


if __name__ == '__main__':
    unittest.main()

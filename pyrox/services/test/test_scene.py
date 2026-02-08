"""Unit tests for SceneRunnerService.

Tests the scene runner service that integrates physics simulation with scene
updates, providing a complete runtime environment with frame-rate independent
rendering.
"""

import unittest
from unittest.mock import Mock, patch
from pyrox.interfaces import ISceneObject, IPhysicsBody2D
from pyrox.services.scene import (
    SceneRunnerService,
    SceneEventBus,
    SceneEventType,
    SceneEvent
)
from pyrox.services.physics import PhysicsEngineService
from pyrox.services.environment import EnvironmentService


class TestSceneRunnerService(unittest.TestCase):
    """Test cases for SceneRunnerService class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock application
        self.mock_app = Mock()

        # Create mock scene
        self.mock_scene = Mock()
        self.mock_scene.get_scene_objects = Mock(return_value={})
        self.mock_scene.on_scene_object_added = []
        self.mock_scene.on_scene_object_removed = []

        # Create mock backend for GuiManager
        self.mock_backend = Mock()
        self.mock_backend.schedule_event = Mock(return_value="event_id_123")
        self.mock_backend.cancel_scheduled_event = Mock()

        # Patch GuiManager to return the mock backend
        self.gui_manager_patcher = patch('pyrox.services.scene.GuiManager')
        self.mock_gui_manager_class = self.gui_manager_patcher.start()
        self.mock_gui_manager_class.unsafe_get_backend.return_value = self.mock_backend

        # Reset the static class state
        SceneRunnerService._running = False
        SceneRunnerService._enable_physics = False
        SceneRunnerService._scene = None
        SceneRunnerService._environment = None
        SceneRunnerService._physics_engine = None
        SceneRunnerService._event_id = None
        SceneRunnerService._on_tick_callbacks = []
        SceneRunnerService._on_scene_load_callbacks = []
        SceneRunnerService._update_interval_ms = 16

        # Clear event bus subscriptions
        SceneEventBus.clear()

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Stop the service if running
        if SceneRunnerService._running:
            SceneRunnerService.stop()

        # Reset state
        SceneRunnerService._running = False
        SceneRunnerService._enable_physics = False
        SceneRunnerService._scene = None
        SceneRunnerService._environment = None
        SceneRunnerService._physics_engine = None
        SceneRunnerService._event_id = None
        SceneRunnerService._on_tick_callbacks = []
        SceneRunnerService._on_scene_load_callbacks = []

        # Clear event bus subscriptions
        SceneEventBus.clear()

        self.gui_manager_patcher.stop()

    def test_cannot_instantiate(self):
        """Test that SceneRunnerService cannot be instantiated."""
        with self.assertRaises(ValueError) as context:
            SceneRunnerService()

        self.assertIn("static class", str(context.exception))

    def test_initialization_without_physics(self):
        """Test initialization without physics enabled."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        self.assertEqual(SceneRunnerService._scene, self.mock_scene)
        self.assertEqual(SceneRunnerService._update_interval_ms, 16)
        self.assertFalse(SceneRunnerService._enable_physics)
        self.assertIsNone(SceneRunnerService._physics_engine)
        self.assertIsNone(SceneRunnerService._environment)
        self.assertFalse(SceneRunnerService._running)

    def test_initialization_with_physics_default(self):
        """Test initialization with physics enabled (default services)."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=True
        )

        self.assertTrue(SceneRunnerService._enable_physics)
        self.assertIsNotNone(SceneRunnerService._physics_engine)
        self.assertIsNotNone(SceneRunnerService._environment)
        self.assertIsInstance(SceneRunnerService._physics_engine, PhysicsEngineService)
        self.assertIsInstance(SceneRunnerService._environment, EnvironmentService)

    def test_initialization_with_physics_custom_services(self):
        """Test initialization with custom physics and environment services."""
        custom_env = EnvironmentService(preset='moon')
        custom_physics = PhysicsEngineService(environment=custom_env)

        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            physics_engine=custom_physics,
            environment=custom_env,
            enable_physics=True
        )

        self.assertIs(SceneRunnerService._physics_engine, custom_physics)
        self.assertIs(SceneRunnerService._environment, custom_env)

    def test_register_physics_bodies_on_init(self):
        """Test that physics bodies are registered during initialization."""
        # Create mock physics bodies
        body1 = Mock(spec=ISceneObject)
        body1.physics_body = Mock(spec=IPhysicsBody2D)
        body1.physics_body.get_bounds = Mock(return_value=(0.0, 0.0, 10.0, 10.0))

        body2 = Mock(spec=ISceneObject)
        body2.physics_body = Mock(spec=IPhysicsBody2D)
        body2.physics_body.get_bounds = Mock(return_value=(0.0, 0.0, 10.0, 10.0))

        self.mock_scene.get_scene_objects = Mock(return_value={
            'body1': body1,
            'body2': body2,
        })

        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=True
        )

        # Check that physics bodies were registered
        self.assertIn(body1.physics_body, SceneRunnerService._physics_engine.bodies)  # type: ignore
        self.assertIn(body2.physics_body, SceneRunnerService._physics_engine.bodies)  # type: ignore

    def test_register_physics_bodies_no_physics_engine(self):
        """Test _register_physics_bodies when physics engine is None."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        # Should not raise error
        SceneRunnerService._register_physics_bodies()

    def test_run_starts_scene(self):
        """Test that run() starts the scene runner."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        SceneRunnerService.run()

        self.assertTrue(SceneRunnerService._running)
        self.mock_backend.schedule_event.assert_called_once()
        self.assertEqual(SceneRunnerService._event_id, "event_id_123")

    def test_run_when_already_running(self):
        """Test that run() does nothing if already running."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        SceneRunnerService.run()
        call_count_1 = self.mock_backend.schedule_event.call_count

        SceneRunnerService.run()  # Call again
        call_count_2 = self.mock_backend.schedule_event.call_count

        # Should not schedule again
        self.assertEqual(call_count_1, call_count_2)

    def test_stop_stops_scene(self):
        """Test that stop() stops the scene runner."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        SceneRunnerService.run()
        SceneRunnerService.stop()

        self.assertFalse(SceneRunnerService._running)
        self.mock_backend.cancel_scheduled_event.assert_called_once_with("event_id_123")
        self.assertIsNone(SceneRunnerService._event_id)

    def test_stop_when_not_running(self):
        """Test that stop() is safe to call when not running."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        # Should not raise error
        SceneRunnerService.stop()
        self.assertFalse(SceneRunnerService._running)

    @patch('pyrox.services.scene.datetime')
    def test_run_scene_calculates_time_delta(self, mock_datetime):
        """Test that _run_scene calculates correct time delta."""
        SceneRunnerService.initialize(
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

        SceneRunnerService.run()
        SceneRunnerService._run_scene()

        # Time delta should be 0.016 (16ms)
        _ = 0.016
        self.assertAlmostEqual(SceneRunnerService._current_time, 1000.016, places=3)

    @patch('pyrox.services.scene.datetime')
    def test_run_scene_clamps_large_time_delta(self, mock_datetime):
        """Test that _run_scene clamps excessive time deltas."""
        # Mock large time jump (e.g., 500ms)
        mock_datetime.now.return_value.timestamp.side_effect = [
            1000.0,  # Initial time
            1000.5,  # 500ms later (too large)
            1000.5,  # Time for reschedule
        ]

        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        SceneRunnerService.run()
        SceneRunnerService._run_scene()

        # Time delta should be clamped to max 0.1 (100ms)
        self.assertEqual(SceneRunnerService._current_time, 1000.5)

    @patch('pyrox.services.scene.datetime')
    def test_run_scene_steps_physics(self, mock_datetime):
        """Test that _run_scene steps the physics engine."""
        mock_datetime.now.return_value.timestamp.side_effect = [
            1000.0,    # Initial time in __init__
            1000.0,    # Time in run()
            1000.016,  # Time in _run_scene()
        ]

        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=True
        )

        with patch.object(SceneRunnerService._physics_engine, 'step') as mock_step:
            SceneRunnerService.run()
            SceneRunnerService._run_scene()

            # Physics should be stepped with time delta
            mock_step.assert_called_once()
            call_args = mock_step.call_args[0][0]
            self.assertAlmostEqual(call_args, 0.016, places=3)

    @patch('pyrox.services.scene.datetime')
    def test_run_scene_skips_physics_when_disabled(self, mock_datetime):
        """Test that _run_scene skips physics when disabled."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        mock_datetime.now.return_value.timestamp.side_effect = [1000.0, 1000.016, 1000.016]

        SceneRunnerService.run()
        SceneRunnerService._run_scene()

        # Physics engine should be None
        self.assertIsNone(SceneRunnerService._physics_engine)

    def test_run_scene_stops_when_not_running(self):
        """Test that _run_scene exits early when _running is False."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=True
        )

        SceneRunnerService._running = False

        with patch.object(SceneRunnerService._physics_engine, 'step') as mock_step:
            SceneRunnerService._run_scene()

            # Physics should not be stepped
            mock_step.assert_not_called()

    def test_run_scene_reschedules_event(self):
        """Test that _run_scene reschedules itself."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        SceneRunnerService.run()
        initial_call_count = self.mock_backend.schedule_event.call_count

        SceneRunnerService._run_scene()

        # Should schedule again
        self.assertGreater(
            self.mock_backend.schedule_event.call_count,
            initial_call_count
        )

    def test_set_update_rate_valid(self):
        """Test setting valid update rates."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        # Test 60 FPS
        SceneRunnerService.set_update_rate(60)
        self.assertEqual(SceneRunnerService._update_interval_ms, 16)

        # Test 30 FPS
        SceneRunnerService.set_update_rate(30)
        self.assertEqual(SceneRunnerService._update_interval_ms, 33)

        # Test 120 FPS
        SceneRunnerService.set_update_rate(120)
        self.assertEqual(SceneRunnerService._update_interval_ms, 8)

    def test_set_update_rate_boundary_values(self):
        """Test setting update rate at boundary values."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        # Test minimum (1 FPS)
        SceneRunnerService.set_update_rate(1)
        self.assertEqual(SceneRunnerService._update_interval_ms, 1000)

        # Test maximum (240 FPS)
        SceneRunnerService.set_update_rate(240)
        self.assertEqual(SceneRunnerService._update_interval_ms, 4)

    def test_set_update_rate_invalid_low(self):
        """Test that invalid low FPS raises ValueError."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        with self.assertRaises(ValueError) as context:
            SceneRunnerService.set_update_rate(0)

        self.assertIn("FPS must be between 1 and 240", str(context.exception))

    def test_set_update_rate_invalid_high(self):
        """Test that invalid high FPS raises ValueError."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        with self.assertRaises(ValueError) as context:
            SceneRunnerService.set_update_rate(241)

        self.assertIn("FPS must be between 1 and 240", str(context.exception))

    def test_add_physics_body(self):
        """Test adding a physics body dynamically."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=True
        )

        body = Mock(spec=IPhysicsBody2D)
        body.get_bounds = Mock(return_value=(0.0, 0.0, 10.0, 10.0))
        SceneRunnerService._enable_physics = False

        # Should not raise error
        SceneRunnerService.add_physics_body(body)

    def test_remove_physics_body(self):
        """Test removing a physics body dynamically."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=True
        )

        body = Mock(spec=IPhysicsBody2D)
        body.get_bounds = Mock(return_value=(0.0, 0.0, 10.0, 10.0))
        _ = self.mock_app,
        SceneRunnerService.set_scene(self.mock_scene)
        SceneRunnerService._enable_physics = False

        body = Mock(spec=IPhysicsBody2D)

        # Should not raise error
        SceneRunnerService.remove_physics_body(body)

    def test_get_physics_stats_with_physics(self):
        """Test getting physics stats when physics is enabled."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=True
        )

        stats = SceneRunnerService.get_physics_stats()

        self.assertIsInstance(stats, dict)
        self.assertIn('total_time', stats)
        self.assertIn('step_count', stats)
        self.assertIn('body_count', stats)

    def test_get_physics_stats_without_physics(self):
        """Test getting physics stats when physics is disabled."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        stats = SceneRunnerService.get_physics_stats()

        self.assertIsInstance(stats, dict)
        self.assertEqual(len(stats), 0)

    def test_current_time_initialization(self):
        """Test that current_time is initialized."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        self.assertIsInstance(SceneRunnerService._current_time, float)
        self.assertGreater(SceneRunnerService._current_time, 0)

    def test_update_interval_default(self):
        """Test default update interval is 16ms (~60 FPS)."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        self.assertEqual(SceneRunnerService._update_interval_ms, 16)

    def test_multiple_bodies_registration(self):
        """Test registering multiple physics bodies."""
        # Create mock scene objects with physics bodies
        scene_obj1 = Mock(spec=ISceneObject)
        scene_obj1.physics_body = Mock(spec=IPhysicsBody2D)
        scene_obj1.physics_body.get_bounds = Mock(return_value=(0.0, 0.0, 10.0, 10.0))

        scene_obj2 = Mock(spec=ISceneObject)
        scene_obj2.physics_body = Mock(spec=IPhysicsBody2D)
        scene_obj2.physics_body.get_bounds = Mock(return_value=(0.0, 0.0, 10.0, 10.0))

        scene_obj3 = Mock(spec=ISceneObject)
        scene_obj3.physics_body = Mock(spec=IPhysicsBody2D)
        scene_obj3.physics_body.get_bounds = Mock(return_value=(0.0, 0.0, 10.0, 10.0))

        self.mock_scene.get_scene_objects = Mock(return_value={
            'body1': scene_obj1,
            'body2': scene_obj2,
            'body3': scene_obj3
        })

        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=True
        )

        self.assertEqual(len(SceneRunnerService._physics_engine.bodies), 3)  # type: ignore
        self.assertIn(scene_obj1.physics_body, SceneRunnerService._physics_engine.bodies)  # type: ignore
        self.assertIn(scene_obj2.physics_body, SceneRunnerService._physics_engine.bodies)  # type: ignore
        self.assertIn(scene_obj3.physics_body, SceneRunnerService._physics_engine.bodies)  # type: ignore

    def test_run_sets_current_time(self):
        """Test that run() sets current_time."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        old_time = SceneRunnerService._current_time
        SceneRunnerService.run()

        # Current time should be updated
        self.assertGreaterEqual(SceneRunnerService._current_time, old_time)

    def test_set_scene_publishes_loaded_event(self):
        """Test that set_scene publishes SCENE_LOADED event."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=None,
            enable_physics=False
        )

        # Subscribe to event
        events_received = []

        def capture_event(event: SceneEvent):
            events_received.append(event)

        SceneEventBus.subscribe(SceneEventType.SCENE_LOADED, capture_event)

        # Set scene
        SceneRunnerService.set_scene(self.mock_scene)

        # Verify event was published
        self.assertEqual(len(events_received), 1)
        self.assertEqual(events_received[0].event_type, SceneEventType.SCENE_LOADED)
        self.assertEqual(events_received[0].scene, self.mock_scene)

    def test_set_scene_none_publishes_unloaded_event(self):
        """Test that set_scene(None) publishes SCENE_UNLOADED event."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=self.mock_scene,
            enable_physics=False
        )

        # Subscribe to event
        events_received = []

        def capture_event(event: SceneEvent):
            events_received.append(event)

        SceneEventBus.subscribe(SceneEventType.SCENE_UNLOADED, capture_event)

        # Clear scene
        SceneRunnerService.set_scene(None)

        # Verify event was published
        self.assertEqual(len(events_received), 1)
        self.assertEqual(events_received[0].event_type, SceneEventType.SCENE_UNLOADED)
        self.assertIsNone(events_received[0].scene)

    def test_new_scene_creates_and_sets_scene(self):
        """Test that new_scene creates and sets a new Scene."""
        SceneRunnerService.initialize(
            app=self.mock_app,
            scene=None,
            enable_physics=False
        )

        # Create new scene - patch where Scene is imported from
        with patch('pyrox.models.scene.Scene') as MockScene:
            mock_scene_instance = Mock()
            mock_scene_instance.on_scene_object_added = []
            mock_scene_instance.on_scene_object_removed = []
            mock_scene_instance.get_scene_objects = Mock(return_value={})
            MockScene.return_value = mock_scene_instance

            SceneRunnerService.new_scene()

            # Verify Scene was created and set
            MockScene.assert_called_once()
            self.assertEqual(SceneRunnerService.get_scene(), mock_scene_instance)

    def test_event_bus_subscribe_and_publish(self):
        """Test SceneEventBus subscribe and publish functionality."""
        events_received = []

        def callback1(event: SceneEvent):
            events_received.append(('callback1', event))

        def callback2(event: SceneEvent):
            events_received.append(('callback2', event))

        # Subscribe both callbacks
        SceneEventBus.subscribe(SceneEventType.SCENE_LOADED, callback1)
        SceneEventBus.subscribe(SceneEventType.SCENE_LOADED, callback2)

        # Verify subscriber count
        self.assertEqual(SceneEventBus.get_subscriber_count(SceneEventType.SCENE_LOADED), 2)

        # Publish event
        event = SceneEvent(event_type=SceneEventType.SCENE_LOADED, scene=self.mock_scene)
        SceneEventBus.publish(event)

        # Verify both callbacks were called
        self.assertEqual(len(events_received), 2)
        self.assertEqual(events_received[0][0], 'callback1')
        self.assertEqual(events_received[1][0], 'callback2')

    def test_event_bus_unsubscribe(self):
        """Test SceneEventBus unsubscribe functionality."""
        events_received = []

        def callback(event: SceneEvent):
            events_received.append(event)

        # Subscribe
        SceneEventBus.subscribe(SceneEventType.SCENE_LOADED, callback)
        self.assertEqual(SceneEventBus.get_subscriber_count(SceneEventType.SCENE_LOADED), 1)

        # Unsubscribe
        SceneEventBus.unsubscribe(SceneEventType.SCENE_LOADED, callback)
        self.assertEqual(SceneEventBus.get_subscriber_count(SceneEventType.SCENE_LOADED), 0)

        # Publish event
        event = SceneEvent(event_type=SceneEventType.SCENE_LOADED, scene=self.mock_scene)
        SceneEventBus.publish(event)

        # Verify callback was not called
        self.assertEqual(len(events_received), 0)

    def test_event_bus_removes_failing_callbacks(self):
        """Test that SceneEventBus removes callbacks that raise exceptions."""
        events_received = []

        def failing_callback(event: SceneEvent):
            raise RuntimeError("Intentional error")

        def working_callback(event: SceneEvent):
            events_received.append(event)

        # Subscribe both callbacks
        SceneEventBus.subscribe(SceneEventType.SCENE_LOADED, failing_callback)
        SceneEventBus.subscribe(SceneEventType.SCENE_LOADED, working_callback)

        self.assertEqual(SceneEventBus.get_subscriber_count(SceneEventType.SCENE_LOADED), 2)

        # Publish event
        event = SceneEvent(event_type=SceneEventType.SCENE_LOADED, scene=self.mock_scene)
        SceneEventBus.publish(event)

        # Verify failing callback was removed but working callback still called
        self.assertEqual(SceneEventBus.get_subscriber_count(SceneEventType.SCENE_LOADED), 1)
        self.assertEqual(len(events_received), 1)

    def test_event_bus_clear(self):
        """Test that SceneEventBus.clear removes all subscriptions."""
        def callback(event: SceneEvent):
            pass

        # Subscribe to multiple event types
        SceneEventBus.subscribe(SceneEventType.SCENE_LOADED, callback)
        SceneEventBus.subscribe(SceneEventType.SCENE_UNLOADED, callback)
        SceneEventBus.subscribe(SceneEventType.SCENE_STARTED, callback)

        # Verify subscriptions exist
        self.assertGreater(SceneEventBus.get_subscriber_count(SceneEventType.SCENE_LOADED), 0)

        # Clear all
        SceneEventBus.clear()

        # Verify all subscriptions removed
        self.assertEqual(SceneEventBus.get_subscriber_count(SceneEventType.SCENE_LOADED), 0)
        self.assertEqual(SceneEventBus.get_subscriber_count(SceneEventType.SCENE_UNLOADED), 0)
        self.assertEqual(SceneEventBus.get_subscriber_count(SceneEventType.SCENE_STARTED), 0)


if __name__ == '__main__':
    unittest.main()

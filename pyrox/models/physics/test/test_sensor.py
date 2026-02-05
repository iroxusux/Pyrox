"""Unit tests for sensor.py module.

Tests the ProximitySensorBody class including initialization,
detection tracking, state changes, callbacks, and factory methods.
"""
import unittest
from unittest.mock import Mock

from pyrox.models.physics.sensor import ProximitySensorBody
from pyrox.models.physics.base import BasePhysicsBody
from pyrox.interfaces import (
    BodyType,
    ColliderType,
    CollisionLayer,
    IPhysicsBody2D,
)


class TestProximitySensorBody(unittest.TestCase):
    """Test cases for ProximitySensorBody class."""

    def setUp(self):
        """Set up test fixtures."""
        self.default_sensor = ProximitySensorBody()

        self.custom_sensor = ProximitySensorBody(
            name="Test Sensor",
            x=100.0,
            y=200.0,
            width=15.0,
            height=12.0
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.default_sensor = None
        self.custom_sensor = None

    # ==================== Initialization Tests ====================

    def test_default_initialization(self):
        """Test default initialization creates valid sensor."""
        sensor = ProximitySensorBody()

        self.assertEqual(sensor.name, "ProximitySensor")
        self.assertEqual(sensor.x, 0.0)
        self.assertEqual(sensor.y, 0.0)
        self.assertEqual(sensor.width, 10.0)
        self.assertEqual(sensor.height, 10.0)
        self.assertEqual(sensor.body_type, BodyType.STATIC)
        self.assertTrue(sensor.collider.is_trigger)

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        sensor = ProximitySensorBody(
            name="Custom Sensor",
            x=50.0,
            y=100.0,
            width=30.0,
            height=40.0
        )

        self.assertEqual(sensor.name, "Custom Sensor")
        self.assertEqual(sensor.x, 50.0)
        self.assertEqual(sensor.y, 100.0)
        self.assertEqual(sensor.width, 30.0)
        self.assertEqual(sensor.height, 40.0)

    def test_static_body_type(self):
        """Test that sensors are always STATIC bodies."""
        sensor = ProximitySensorBody()

        self.assertEqual(sensor.body_type, BodyType.STATIC)

    def test_is_trigger(self):
        """Test that sensors are always triggers."""
        sensor = ProximitySensorBody()

        self.assertTrue(sensor.collider.is_trigger)

    def test_zero_mass(self):
        """Test that sensors have zero mass."""
        sensor = ProximitySensorBody()

        self.assertEqual(sensor.mass, 0.0)

    def test_rectangle_collider_type(self):
        """Test that sensors use RECTANGLE collider."""
        sensor = ProximitySensorBody()

        self.assertEqual(sensor.collider.collider_type, ColliderType.RECTANGLE)

    def test_default_collision_layer(self):
        """Test default collision layer is DEFAULT."""
        sensor = ProximitySensorBody()

        self.assertEqual(sensor.collider.collision_layer, CollisionLayer.DEFAULT)

    def test_default_collision_mask(self):
        """Test default collision mask includes common layers."""
        sensor = ProximitySensorBody()

        mask = sensor.collider.collision_mask
        self.assertIn(CollisionLayer.DEFAULT, mask)
        self.assertIn(CollisionLayer.PLAYER, mask)
        self.assertIn(CollisionLayer.ENEMY, mask)

    def test_custom_collision_mask(self):
        """Test initialization with custom collision mask."""
        custom_mask = [CollisionLayer.PLAYER, CollisionLayer.PROJECTILE]
        sensor = ProximitySensorBody(collision_mask=custom_mask)

        self.assertEqual(sensor.collider.collision_mask, custom_mask)

    def test_custom_collision_layer(self):
        """Test initialization with custom collision layer."""
        sensor = ProximitySensorBody(collision_layer=CollisionLayer.PLAYER)

        self.assertEqual(sensor.collider.collision_layer, CollisionLayer.PLAYER)

    def test_material_properties(self):
        """Test that sensor has zero material properties."""
        sensor = ProximitySensorBody()

        self.assertEqual(sensor.material.density, 0.0)
        self.assertEqual(sensor.material.restitution, 0.0)
        self.assertEqual(sensor.material.friction, 0.0)
        self.assertEqual(sensor.material.drag, 0.0)

    # ==================== Property Tests ====================

    def test_is_active_initially_false(self):
        """Test that sensor is not active initially."""
        sensor = ProximitySensorBody()

        self.assertFalse(sensor.is_active)

    def test_detected_objects_initially_empty(self):
        """Test that detected objects set is initially empty."""
        sensor = ProximitySensorBody()

        self.assertEqual(len(sensor.detected_objects), 0)
        self.assertIsInstance(sensor.detected_objects, set)

    def test_detection_count_initially_zero(self):
        """Test that detection count is initially zero."""
        sensor = ProximitySensorBody()

        self.assertEqual(sensor.detection_count, 0)

    def test_callback_lists_initialized(self):
        """Test that all callback lists are initialized."""
        sensor = ProximitySensorBody()

        self.assertIsInstance(sensor.on_activate_callbacks, list)
        self.assertIsInstance(sensor.on_deactivate_callbacks, list)
        self.assertIsInstance(sensor.on_object_enter_callbacks, list)
        self.assertIsInstance(sensor.on_object_exit_callbacks, list)

    def test_callback_lists_initially_empty(self):
        """Test that all callback lists start empty."""
        sensor = ProximitySensorBody()

        self.assertEqual(len(sensor.on_activate_callbacks), 0)
        self.assertEqual(len(sensor.on_deactivate_callbacks), 0)
        self.assertEqual(len(sensor.on_object_enter_callbacks), 0)
        self.assertEqual(len(sensor.on_object_exit_callbacks), 0)

    # ==================== Detection Tests ====================

    def test_on_collision_enter_adds_object(self):
        """Test on_collision_enter adds object to detected set."""
        sensor = ProximitySensorBody()
        mock_object = Mock(spec=IPhysicsBody2D)

        sensor.on_collision_enter(mock_object)

        self.assertIn(mock_object, sensor.detected_objects)
        self.assertEqual(sensor.detection_count, 1)

    def test_on_collision_enter_activates_sensor(self):
        """Test first object entering activates sensor."""
        sensor = ProximitySensorBody()
        mock_object = Mock(spec=IPhysicsBody2D)

        self.assertFalse(sensor.is_active)

        sensor.on_collision_enter(mock_object)

        self.assertTrue(sensor.is_active)

    def test_on_collision_enter_multiple_objects(self):
        """Test multiple objects entering sensor."""
        sensor = ProximitySensorBody()
        mock_obj1 = Mock(spec=IPhysicsBody2D)
        mock_obj2 = Mock(spec=IPhysicsBody2D)
        mock_obj3 = Mock(spec=IPhysicsBody2D)

        sensor.on_collision_enter(mock_obj1)
        sensor.on_collision_enter(mock_obj2)
        sensor.on_collision_enter(mock_obj3)

        self.assertEqual(sensor.detection_count, 3)
        self.assertIn(mock_obj1, sensor.detected_objects)
        self.assertIn(mock_obj2, sensor.detected_objects)
        self.assertIn(mock_obj3, sensor.detected_objects)

    def test_on_collision_enter_same_object_twice(self):
        """Test same object entering twice only counts once."""
        sensor = ProximitySensorBody()
        mock_object = Mock(spec=IPhysicsBody2D)

        sensor.on_collision_enter(mock_object)
        sensor.on_collision_enter(mock_object)

        self.assertEqual(sensor.detection_count, 1)

    def test_on_collision_exit_removes_object(self):
        """Test on_collision_exit removes object from detected set."""
        sensor = ProximitySensorBody()
        mock_object = Mock(spec=IPhysicsBody2D)

        sensor.on_collision_enter(mock_object)
        self.assertEqual(sensor.detection_count, 1)

        sensor.on_collision_exit(mock_object)

        self.assertNotIn(mock_object, sensor.detected_objects)
        self.assertEqual(sensor.detection_count, 0)

    def test_on_collision_exit_deactivates_sensor(self):
        """Test last object exiting deactivates sensor."""
        sensor = ProximitySensorBody()
        mock_object = Mock(spec=IPhysicsBody2D)

        sensor.on_collision_enter(mock_object)
        self.assertTrue(sensor.is_active)

        sensor.on_collision_exit(mock_object)

        self.assertFalse(sensor.is_active)

    def test_on_collision_exit_with_multiple_objects(self):
        """Test sensor stays active until all objects exit."""
        sensor = ProximitySensorBody()
        mock_obj1 = Mock(spec=IPhysicsBody2D)
        mock_obj2 = Mock(spec=IPhysicsBody2D)

        sensor.on_collision_enter(mock_obj1)
        sensor.on_collision_enter(mock_obj2)
        self.assertTrue(sensor.is_active)

        sensor.on_collision_exit(mock_obj1)
        self.assertTrue(sensor.is_active)  # Still active
        self.assertEqual(sensor.detection_count, 1)

        sensor.on_collision_exit(mock_obj2)
        self.assertFalse(sensor.is_active)  # Now deactivated
        self.assertEqual(sensor.detection_count, 0)

    def test_on_collision_exit_nonexistent_object(self):
        """Test exiting object that was never entered."""
        sensor = ProximitySensorBody()
        mock_object = Mock(spec=IPhysicsBody2D)

        # Should not raise error
        sensor.on_collision_exit(mock_object)

        self.assertEqual(sensor.detection_count, 0)
        self.assertFalse(sensor.is_active)

    # ==================== State Change Tests ====================

    def test_activate_sets_is_active(self):
        """Test _activate sets is_active to True."""
        sensor = ProximitySensorBody()

        sensor._activate()

        self.assertTrue(sensor.is_active)

    def test_deactivate_sets_is_active(self):
        """Test _deactivate sets is_active to False."""
        sensor = ProximitySensorBody()
        sensor._is_active = True

        sensor._deactivate()

        self.assertFalse(sensor.is_active)

    def test_activate_only_once(self):
        """Test _activate only changes state once."""
        sensor = ProximitySensorBody()
        callback = Mock()
        sensor.on_activate_callbacks.append(callback)

        sensor._activate()
        sensor._activate()  # Should not trigger again

        callback.assert_called_once()

    def test_deactivate_only_once(self):
        """Test _deactivate only changes state once."""
        sensor = ProximitySensorBody()
        sensor._is_active = True
        callback = Mock()
        sensor.on_deactivate_callbacks.append(callback)

        sensor._deactivate()
        sensor._deactivate()  # Should not trigger again

        callback.assert_called_once()

    # ==================== Callback Tests ====================

    def test_on_activate_callback_fired(self):
        """Test activate callback is fired when sensor activates."""
        sensor = ProximitySensorBody()
        callback = Mock()
        sensor.on_activate_callbacks.append(callback)

        mock_object = Mock(spec=IPhysicsBody2D)
        sensor.on_collision_enter(mock_object)

        callback.assert_called_once_with(sensor)

    def test_on_deactivate_callback_fired(self):
        """Test deactivate callback is fired when sensor deactivates."""
        sensor = ProximitySensorBody()
        callback = Mock()
        sensor.on_deactivate_callbacks.append(callback)

        mock_object = Mock(spec=IPhysicsBody2D)
        sensor.on_collision_enter(mock_object)
        sensor.on_collision_exit(mock_object)

        callback.assert_called_once_with(sensor)

    def test_on_object_enter_callback_fired(self):
        """Test object enter callback is fired for each entering object."""
        sensor = ProximitySensorBody()
        callback = Mock()
        sensor.on_object_enter_callbacks.append(callback)

        mock_obj1 = Mock(spec=IPhysicsBody2D)
        mock_obj2 = Mock(spec=IPhysicsBody2D)

        sensor.on_collision_enter(mock_obj1)
        sensor.on_collision_enter(mock_obj2)

        self.assertEqual(callback.call_count, 2)
        callback.assert_any_call(sensor, mock_obj1)
        callback.assert_any_call(sensor, mock_obj2)

    def test_on_object_exit_callback_fired(self):
        """Test object exit callback is fired for each exiting object."""
        sensor = ProximitySensorBody()
        callback = Mock()
        sensor.on_object_exit_callbacks.append(callback)

        mock_obj1 = Mock(spec=IPhysicsBody2D)
        mock_obj2 = Mock(spec=IPhysicsBody2D)

        sensor.on_collision_enter(mock_obj1)
        sensor.on_collision_enter(mock_obj2)
        sensor.on_collision_exit(mock_obj1)
        sensor.on_collision_exit(mock_obj2)

        self.assertEqual(callback.call_count, 2)
        callback.assert_any_call(sensor, mock_obj1)
        callback.assert_any_call(sensor, mock_obj2)

    def test_multiple_callbacks_all_fired(self):
        """Test multiple callbacks are all fired."""
        sensor = ProximitySensorBody()
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()

        sensor.on_activate_callbacks.extend([callback1, callback2, callback3])

        mock_object = Mock(spec=IPhysicsBody2D)
        sensor.on_collision_enter(mock_object)

        callback1.assert_called_once()
        callback2.assert_called_once()
        callback3.assert_called_once()

    def test_callback_exception_handled(self):
        """Test that callback exceptions don't crash sensor."""
        sensor = ProximitySensorBody()
        bad_callback = Mock(side_effect=Exception("Test error"))
        good_callback = Mock()

        sensor.on_activate_callbacks.extend([bad_callback, good_callback])

        mock_object = Mock(spec=IPhysicsBody2D)

        # Should not raise exception
        sensor.on_collision_enter(mock_object)

        # Good callback should still be called
        good_callback.assert_called_once()

    def test_activate_callback_not_fired_if_already_active(self):
        """Test activate callback not fired when already active."""
        sensor = ProximitySensorBody()
        callback = Mock()
        sensor.on_activate_callbacks.append(callback)

        mock_obj1 = Mock(spec=IPhysicsBody2D)
        mock_obj2 = Mock(spec=IPhysicsBody2D)

        sensor.on_collision_enter(mock_obj1)
        sensor.on_collision_enter(mock_obj2)  # Already active

        callback.assert_called_once()  # Only called once

    def test_deactivate_callback_not_fired_if_not_empty(self):
        """Test deactivate callback not fired if objects remain."""
        sensor = ProximitySensorBody()
        callback = Mock()
        sensor.on_deactivate_callbacks.append(callback)

        mock_obj1 = Mock(spec=IPhysicsBody2D)
        mock_obj2 = Mock(spec=IPhysicsBody2D)

        sensor.on_collision_enter(mock_obj1)
        sensor.on_collision_enter(mock_obj2)
        sensor.on_collision_exit(mock_obj1)  # Still has obj2

        callback.assert_not_called()

    # ==================== Utility Method Tests ====================

    def test_clear_detected_objects(self):
        """Test clear_detected_objects empties the set."""
        sensor = ProximitySensorBody()
        mock_obj1 = Mock(spec=IPhysicsBody2D)
        mock_obj2 = Mock(spec=IPhysicsBody2D)

        sensor.on_collision_enter(mock_obj1)
        sensor.on_collision_enter(mock_obj2)
        self.assertEqual(sensor.detection_count, 2)

        sensor.clear_detected_objects()

        self.assertEqual(sensor.detection_count, 0)
        self.assertEqual(len(sensor.detected_objects), 0)

    def test_clear_detected_objects_deactivates(self):
        """Test clear_detected_objects deactivates sensor."""
        sensor = ProximitySensorBody()
        mock_object = Mock(spec=IPhysicsBody2D)

        sensor.on_collision_enter(mock_object)
        self.assertTrue(sensor.is_active)

        sensor.clear_detected_objects()

        self.assertFalse(sensor.is_active)

    def test_clear_detected_objects_fires_deactivate_callback(self):
        """Test clear_detected_objects fires deactivate callback."""
        sensor = ProximitySensorBody()
        callback = Mock()
        sensor.on_deactivate_callbacks.append(callback)

        mock_object = Mock(spec=IPhysicsBody2D)
        sensor.on_collision_enter(mock_object)

        sensor.clear_detected_objects()

        callback.assert_called_once()

    def test_is_detecting_returns_true_for_detected_object(self):
        """Test is_detecting returns True for detected object."""
        sensor = ProximitySensorBody()
        mock_object = Mock(spec=IPhysicsBody2D)

        sensor.on_collision_enter(mock_object)

        self.assertTrue(sensor.is_detecting(mock_object))

    def test_is_detecting_returns_false_for_undetected_object(self):
        """Test is_detecting returns False for undetected object."""
        sensor = ProximitySensorBody()
        mock_obj1 = Mock(spec=IPhysicsBody2D)
        mock_obj2 = Mock(spec=IPhysicsBody2D)

        sensor.on_collision_enter(mock_obj1)

        self.assertFalse(sensor.is_detecting(mock_obj2))

    def test_detected_objects_returns_copy(self):
        """Test detected_objects property returns a copy."""
        sensor = ProximitySensorBody()
        mock_object = Mock(spec=IPhysicsBody2D)

        sensor.on_collision_enter(mock_object)
        detected = sensor.detected_objects

        # Modify returned set
        detected.clear()

        # Original should be unchanged
        self.assertEqual(sensor.detection_count, 1)

    # ==================== Factory Method Tests ====================

    def test_create_small_sensor(self):
        """Test create_small_sensor factory method."""
        sensor = ProximitySensorBody.create_small_sensor(
            name="SmallTest",
            x=50.0,
            y=100.0
        )

        self.assertEqual(sensor.name, "SmallTest")
        self.assertEqual(sensor.x, 50.0)
        self.assertEqual(sensor.y, 100.0)
        self.assertEqual(sensor.width, 5.0)
        self.assertEqual(sensor.height, 5.0)

    def test_create_small_sensor_default_name(self):
        """Test create_small_sensor with default name."""
        sensor = ProximitySensorBody.create_small_sensor()

        self.assertEqual(sensor.name, "SmallSensor")
        self.assertEqual(sensor.width, 5.0)
        self.assertEqual(sensor.height, 5.0)

    def test_create_checkpoint_sensor(self):
        """Test create_checkpoint_sensor factory method."""
        sensor = ProximitySensorBody.create_checkpoint_sensor(
            name="CheckpointTest",
            x=100.0,
            y=200.0,
            width=50.0
        )

        self.assertEqual(sensor.name, "CheckpointTest")
        self.assertEqual(sensor.x, 100.0)
        self.assertEqual(sensor.y, 200.0)
        self.assertEqual(sensor.width, 50.0)
        self.assertEqual(sensor.height, 5.0)

    def test_create_checkpoint_sensor_default_name(self):
        """Test create_checkpoint_sensor with default name."""
        sensor = ProximitySensorBody.create_checkpoint_sensor(width=30.0)

        self.assertEqual(sensor.name, "Checkpoint")
        self.assertEqual(sensor.width, 30.0)
        self.assertEqual(sensor.height, 5.0)

    def test_create_checkpoint_sensor_default_width(self):
        """Test create_checkpoint_sensor with default width."""
        sensor = ProximitySensorBody.create_checkpoint_sensor()

        self.assertEqual(sensor.width, 20.0)
        self.assertEqual(sensor.height, 5.0)

    # ==================== Integration Tests ====================

    def test_full_detection_cycle(self):
        """Test complete detection cycle with callbacks."""
        sensor = ProximitySensorBody()

        # Setup callbacks
        activate_calls = []
        deactivate_calls = []
        enter_calls = []
        exit_calls = []

        sensor.on_activate_callbacks.append(lambda s: activate_calls.append(s))
        sensor.on_deactivate_callbacks.append(lambda s: deactivate_calls.append(s))
        sensor.on_object_enter_callbacks.append(lambda s, o: enter_calls.append(o))
        sensor.on_object_exit_callbacks.append(lambda s, o: exit_calls.append(o))

        # Create mock objects
        mock_obj1 = Mock(spec=IPhysicsBody2D)
        mock_obj2 = Mock(spec=IPhysicsBody2D)

        # Object 1 enters (activate)
        sensor.on_collision_enter(mock_obj1)
        self.assertTrue(sensor.is_active)
        self.assertEqual(len(activate_calls), 1)
        self.assertEqual(len(enter_calls), 1)

        # Object 2 enters (stay active)
        sensor.on_collision_enter(mock_obj2)
        self.assertTrue(sensor.is_active)
        self.assertEqual(len(activate_calls), 1)  # Still 1
        self.assertEqual(len(enter_calls), 2)

        # Object 1 exits (stay active)
        sensor.on_collision_exit(mock_obj1)
        self.assertTrue(sensor.is_active)
        self.assertEqual(len(deactivate_calls), 0)
        self.assertEqual(len(exit_calls), 1)

        # Object 2 exits (deactivate)
        sensor.on_collision_exit(mock_obj2)
        self.assertFalse(sensor.is_active)
        self.assertEqual(len(deactivate_calls), 1)
        self.assertEqual(len(exit_calls), 2)

    def test_inheritance_from_base_physics_body(self):
        """Test that sensor inherits from BasePhysicsBody."""
        sensor = ProximitySensorBody()

        self.assertIsInstance(sensor, BasePhysicsBody)

    def test_has_required_collision_methods(self):
        """Test that sensor has required collision callback methods."""
        sensor = ProximitySensorBody()

        self.assertTrue(hasattr(sensor, 'on_collision_enter'))
        self.assertTrue(hasattr(sensor, 'on_collision_exit'))
        self.assertTrue(callable(sensor.on_collision_enter))
        self.assertTrue(callable(sensor.on_collision_exit))


if __name__ == '__main__':
    unittest.main()

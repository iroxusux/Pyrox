"""Unit tests for ConnectionRegistry class."""
import unittest
from pyrox.models.connection import ConnectionRegistry
from pyrox.interfaces import Connection


class TestConnectionRegistry(unittest.TestCase):
    """Test cases for ConnectionRegistry class."""

    def setUp(self):
        """Set up test fixtures."""
        self.registry = ConnectionRegistry()

        # Create mock objects with callbacks
        class MockSensor:
            def __init__(self, sensor_id: str):
                self.id = sensor_id
                self.on_activate_callbacks: list = []
                self.on_deactivate_callbacks: list = []

        class MockMotor:
            def __init__(self, motor_id: str):
                self.id = motor_id
                self.speed = 0.0
                self.start_called = False
                self.stop_called = False

            def start(self):
                self.start_called = True
                self.speed = 100.0

            def stop(self):
                self.stop_called = True
                self.speed = 0.0

            def set_speed(self, speed: float):
                self.speed = speed

        self.MockSensor = MockSensor
        self.MockMotor = MockMotor

    def test_init(self):
        """Test ConnectionRegistry initialization."""
        registry = ConnectionRegistry()
        self.assertIsInstance(registry._connections, list)
        self.assertIsInstance(registry._objects, dict)
        self.assertEqual(len(registry._connections), 0)
        self.assertEqual(len(registry._objects), 0)

    def test_register_object(self):
        """Test registering an object."""
        sensor = self.MockSensor("sensor_001")
        self.registry.register_object("sensor_001", sensor)

        self.assertIn("sensor_001", self.registry._objects)
        self.assertIs(self.registry._objects["sensor_001"], sensor)

    def test_register_multiple_objects(self):
        """Test registering multiple objects."""
        sensor1 = self.MockSensor("sensor_001")
        sensor2 = self.MockSensor("sensor_002")
        motor = self.MockMotor("motor_001")

        self.registry.register_object("sensor_001", sensor1)
        self.registry.register_object("sensor_002", sensor2)
        self.registry.register_object("motor_001", motor)

        self.assertEqual(len(self.registry._objects), 3)
        self.assertIn("sensor_001", self.registry._objects)
        self.assertIn("sensor_002", self.registry._objects)
        self.assertIn("motor_001", self.registry._objects)

    def test_register_object_overwrites_existing(self):
        """Test that registering same ID overwrites previous object."""
        sensor1 = self.MockSensor("sensor_001")
        sensor2 = self.MockSensor("sensor_001")

        self.registry.register_object("sensor_001", sensor1)
        self.registry.register_object("sensor_001", sensor2)

        self.assertEqual(len(self.registry._objects), 1)
        self.assertIs(self.registry._objects["sensor_001"], sensor2)

    def test_connect_creates_connection(self):
        """Test that connect creates a Connection."""
        sensor = self.MockSensor("sensor_001")
        motor = self.MockMotor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        conn = self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )

        self.assertIsInstance(conn, Connection)
        self.assertEqual(conn.source_id, "sensor_001")
        self.assertEqual(conn.source_output, "on_activate_callbacks")
        self.assertEqual(conn.target_id, "motor_001")
        self.assertEqual(conn.target_input, "start")

    def test_connect_adds_to_connections_list(self):
        """Test that connect adds connection to internal list."""
        sensor = self.MockSensor("sensor_001")
        motor = self.MockMotor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        self.assertEqual(len(self.registry._connections), 0)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )

        self.assertEqual(len(self.registry._connections), 1)

    def test_connect_wires_callback(self):
        """Test that connect actually wires the callback."""
        sensor = self.MockSensor("sensor_001")
        motor = self.MockMotor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )

        # Verify callback was added to sensor's callback list
        self.assertEqual(len(sensor.on_activate_callbacks), 1)
        # Check the callback is bound to the correct method
        callback = sensor.on_activate_callbacks[0]
        self.assertEqual(callback.__name__, "start")
        self.assertIs(callback.__self__, motor)

    def test_connect_callback_is_functional(self):
        """Test that the wired callback actually works."""
        sensor = self.MockSensor("sensor_001")
        motor = self.MockMotor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )

        # Trigger the callback
        self.assertFalse(motor.start_called)
        sensor.on_activate_callbacks[0]()
        self.assertTrue(motor.start_called)
        self.assertEqual(motor.speed, 100.0)

    def test_connect_multiple_connections(self):
        """Test creating multiple connections."""
        sensor1 = self.MockSensor("sensor_001")
        sensor2 = self.MockSensor("sensor_002")
        motor1 = self.MockMotor("motor_001")
        motor2 = self.MockMotor("motor_002")

        self.registry.register_object("sensor_001", sensor1)
        self.registry.register_object("sensor_002", sensor2)
        self.registry.register_object("motor_001", motor1)
        self.registry.register_object("motor_002", motor2)

        conn1 = self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )
        conn2 = self.registry.connect(
            "sensor_002", "on_deactivate_callbacks",
            "motor_002", "stop"
        )

        self.assertEqual(len(self.registry._connections), 2)
        self.assertIn(conn1, self.registry._connections)
        self.assertIn(conn2, self.registry._connections)

    def test_connect_one_to_many(self):
        """Test connecting one source to multiple targets."""
        sensor = self.MockSensor("sensor_001")
        motor1 = self.MockMotor("motor_001")
        motor2 = self.MockMotor("motor_002")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor1)
        self.registry.register_object("motor_002", motor2)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )
        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_002", "start"
        )

        self.assertEqual(len(self.registry._connections), 2)
        self.assertEqual(len(sensor.on_activate_callbacks), 2)

        # Both motors should be triggered
        for callback in sensor.on_activate_callbacks:
            callback()

        self.assertTrue(motor1.start_called)
        self.assertTrue(motor2.start_called)

    def test_connect_with_unregistered_source_raises_error(self):
        """Test that connecting unregistered source raises KeyError."""
        motor = self.MockMotor("motor_001")
        self.registry.register_object("motor_001", motor)

        with self.assertRaises(KeyError):
            self.registry.connect(
                "nonexistent", "on_activate_callbacks",
                "motor_001", "start"
            )

    def test_connect_with_unregistered_target_raises_error(self):
        """Test that connecting unregistered target raises KeyError."""
        sensor = self.MockSensor("sensor_001")
        self.registry.register_object("sensor_001", sensor)

        with self.assertRaises(KeyError):
            self.registry.connect(
                "sensor_001", "on_activate_callbacks",
                "nonexistent", "start"
            )

    def test_connect_with_invalid_output_raises_error(self):
        """Test that connecting invalid output attribute raises AttributeError."""
        sensor = self.MockSensor("sensor_001")
        motor = self.MockMotor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        with self.assertRaises(AttributeError):
            self.registry.connect(
                "sensor_001", "nonexistent_output",
                "motor_001", "start"
            )

    def test_connect_with_invalid_input_raises_error(self):
        """Test that connecting invalid input attribute raises AttributeError."""
        sensor = self.MockSensor("sensor_001")
        motor = self.MockMotor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        with self.assertRaises(AttributeError):
            self.registry.connect(
                "sensor_001", "on_activate_callbacks",
                "motor_001", "nonexistent_input"
            )

    def test_serialize_empty_registry(self):
        """Test serializing empty registry."""
        result = self.registry.serialize()

        self.assertIsInstance(result, dict)
        self.assertIn("connections", result)
        self.assertIsInstance(result["connections"], list)
        self.assertEqual(len(result["connections"]), 0)

    def test_serialize_single_connection(self):
        """Test serializing registry with one connection."""
        sensor = self.MockSensor("sensor_001")
        motor = self.MockMotor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )

        result = self.registry.serialize()

        self.assertEqual(len(result["connections"]), 1)
        conn_data = result["connections"][0]

        self.assertEqual(conn_data["source"], "sensor_001")
        self.assertEqual(conn_data["output"], "on_activate_callbacks")
        self.assertEqual(conn_data["target"], "motor_001")
        self.assertEqual(conn_data["input"], "start")
        self.assertIn("enabled", conn_data)

    def test_serialize_multiple_connections(self):
        """Test serializing registry with multiple connections."""
        sensor1 = self.MockSensor("sensor_001")
        sensor2 = self.MockSensor("sensor_002")
        motor1 = self.MockMotor("motor_001")
        motor2 = self.MockMotor("motor_002")

        self.registry.register_object("sensor_001", sensor1)
        self.registry.register_object("sensor_002", sensor2)
        self.registry.register_object("motor_001", motor1)
        self.registry.register_object("motor_002", motor2)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )
        self.registry.connect(
            "sensor_002", "on_deactivate_callbacks",
            "motor_002", "stop"
        )

        result = self.registry.serialize()

        self.assertEqual(len(result["connections"]), 2)

        # Check first connection
        conn1 = result["connections"][0]
        self.assertEqual(conn1["source"], "sensor_001")
        self.assertEqual(conn1["output"], "on_activate_callbacks")
        self.assertEqual(conn1["target"], "motor_001")
        self.assertEqual(conn1["input"], "start")

        # Check second connection
        conn2 = result["connections"][1]
        self.assertEqual(conn2["source"], "sensor_002")
        self.assertEqual(conn2["output"], "on_deactivate_callbacks")
        self.assertEqual(conn2["target"], "motor_002")
        self.assertEqual(conn2["input"], "stop")

    def test_serialize_preserves_connection_order(self):
        """Test that serialize preserves connection order."""
        sensor = self.MockSensor("sensor_001")
        motor1 = self.MockMotor("motor_001")
        motor2 = self.MockMotor("motor_002")
        motor3 = self.MockMotor("motor_003")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor1)
        self.registry.register_object("motor_002", motor2)
        self.registry.register_object("motor_003", motor3)

        self.registry.connect("sensor_001", "on_activate_callbacks", "motor_001", "start")
        self.registry.connect("sensor_001", "on_activate_callbacks", "motor_002", "start")
        self.registry.connect("sensor_001", "on_activate_callbacks", "motor_003", "start")

        result = self.registry.serialize()

        self.assertEqual(result["connections"][0]["target"], "motor_001")
        self.assertEqual(result["connections"][1]["target"], "motor_002")
        self.assertEqual(result["connections"][2]["target"], "motor_003")

    def test_connection_enabled_in_serialization(self):
        """Test that enabled field is included in serialization."""
        sensor = self.MockSensor("sensor_001")
        motor = self.MockMotor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )

        result = self.registry.serialize()
        conn_data = result["connections"][0]

        self.assertIn("enabled", conn_data)
        self.assertIsInstance(conn_data["enabled"], bool)

    def test_integration_sensor_motor_workflow(self):
        """Integration test: sensor triggers motor through connection."""
        sensor = self.MockSensor("checkpoint_001")
        motor = self.MockMotor("conveyor_motor_001")

        # Register objects
        self.registry.register_object("checkpoint_001", sensor)
        self.registry.register_object("conveyor_motor_001", motor)

        # Create connection
        self.registry.connect(
            "checkpoint_001", "on_activate_callbacks",
            "conveyor_motor_001", "start"
        )

        # Simulate sensor activation
        self.assertFalse(motor.start_called)
        self.assertEqual(motor.speed, 0.0)

        # Trigger all callbacks on sensor activation
        for callback in sensor.on_activate_callbacks:
            callback()

        # Verify motor started
        self.assertTrue(motor.start_called)
        self.assertEqual(motor.speed, 100.0)

    def test_integration_bidirectional_connections(self):
        """Integration test: bidirectional connections between sensors and motors."""
        sensor = self.MockSensor("sensor_001")
        motor = self.MockMotor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        # Connect activate -> start
        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )

        # Connect deactivate -> stop
        self.registry.connect(
            "sensor_001", "on_deactivate_callbacks",
            "motor_001", "stop"
        )

        # Test activation
        sensor.on_activate_callbacks[0]()
        self.assertTrue(motor.start_called)
        self.assertEqual(motor.speed, 100.0)

        # Test deactivation
        sensor.on_deactivate_callbacks[0]()
        self.assertTrue(motor.stop_called)
        self.assertEqual(motor.speed, 0.0)

    def test_unregister_object_removes_connections(self):
        """Test that unregistering an object removes its connections."""
        sensor = self.MockSensor("sensor_001")
        motor = self.MockMotor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )

        self.assertEqual(len(self.registry._connections), 1)

        # Unregister sensor
        self.registry.unregister_object("sensor_001")

        self.assertEqual(len(self.registry._connections), 0)
        self.assertNotIn("sensor_001", self.registry._objects)

    def test_unregister_object_not_registered(self):
        """Test that unregistering a non-registered object does not raise error."""
        try:
            self.registry.unregister_object("nonexistent")
        except Exception as e:
            self.fail(f"unregister_object raised an exception unexpectedly: {e}")

    def test_unregister_object_removes_multiple_connections(self):
        """Test that unregistering an object removes all its connections."""
        sensor1 = self.MockSensor("sensor_001")
        sensor2 = self.MockSensor("sensor_002")
        motor = self.MockMotor("motor_001")

        self.registry.register_object("sensor_001", sensor1)
        self.registry.register_object("sensor_002", sensor2)
        self.registry.register_object("motor_001", motor)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )
        self.registry.connect(
            "sensor_002", "on_deactivate_callbacks",
            "motor_001", "stop"
        )

        self.assertEqual(len(self.registry._connections), 2)

        # Unregister motor
        self.registry.unregister_object("motor_001")

        self.assertEqual(len(self.registry._connections), 0)
        self.assertNotIn("motor_001", self.registry._objects)


if __name__ == '__main__':
    unittest.main()

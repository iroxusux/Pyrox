"""Unit tests for connection.py protocols module.

Tests the Connectable class and Connection dataclass for
managing connections between objects in the scene.
"""
import unittest

from pyrox.interfaces import Connection
from pyrox.models.protocols.connection import Connectable


class TestConnection(unittest.TestCase):
    """Test cases for Connection dataclass."""

    def test_connection_initialization_all_fields(self):
        """Test initialization with all fields."""
        conn = Connection(
            source_id="sensor_1",
            source_output="on_activate_callbacks",
            target_id="conveyor_1",
            target_input="activate",
            enabled=True
        )

        self.assertEqual(conn.source_id, "sensor_1")
        self.assertEqual(conn.source_output, "on_activate_callbacks")
        self.assertEqual(conn.target_id, "conveyor_1")
        self.assertEqual(conn.target_input, "activate")
        self.assertTrue(conn.enabled)

    def test_connection_initialization_default_enabled(self):
        """Test initialization with default enabled=True."""
        conn = Connection(
            source_id="obj_1",
            source_output="output_1",
            target_id="obj_2",
            target_input="input_1"
        )

        self.assertTrue(conn.enabled)

    def test_connection_initialization_disabled(self):
        """Test initialization with enabled=False."""
        conn = Connection(
            source_id="obj_1",
            source_output="output_1",
            target_id="obj_2",
            target_input="input_1",
            enabled=False
        )

        self.assertFalse(conn.enabled)

    def test_connection_equality(self):
        """Test that two connections with same data are equal."""
        conn1 = Connection(
            source_id="s1",
            source_output="out1",
            target_id="t1",
            target_input="in1",
            enabled=True
        )
        conn2 = Connection(
            source_id="s1",
            source_output="out1",
            target_id="t1",
            target_input="in1",
            enabled=True
        )

        self.assertEqual(conn1, conn2)

    def test_connection_inequality_different_source(self):
        """Test that connections with different sources are not equal."""
        conn1 = Connection("s1", "out1", "t1", "in1")
        conn2 = Connection("s2", "out1", "t1", "in1")

        self.assertNotEqual(conn1, conn2)

    def test_connection_inequality_different_output(self):
        """Test that connections with different outputs are not equal."""
        conn1 = Connection("s1", "out1", "t1", "in1")
        conn2 = Connection("s1", "out2", "t1", "in1")

        self.assertNotEqual(conn1, conn2)

    def test_connection_inequality_different_target(self):
        """Test that connections with different targets are not equal."""
        conn1 = Connection("s1", "out1", "t1", "in1")
        conn2 = Connection("s1", "out1", "t2", "in1")

        self.assertNotEqual(conn1, conn2)

    def test_connection_inequality_different_input(self):
        """Test that connections with different inputs are not equal."""
        conn1 = Connection("s1", "out1", "t1", "in1")
        conn2 = Connection("s1", "out1", "t1", "in2")

        self.assertNotEqual(conn1, conn2)

    def test_connection_inequality_different_enabled(self):
        """Test that connections with different enabled states are not equal."""
        conn1 = Connection("s1", "out1", "t1", "in1", enabled=True)
        conn2 = Connection("s1", "out1", "t1", "in1", enabled=False)

        self.assertNotEqual(conn1, conn2)

    def test_connection_is_dataclass(self):
        """Test that Connection is a dataclass."""
        conn = Connection("s1", "out1", "t1", "in1")

        # Dataclasses have __dataclass_fields__
        self.assertTrue(hasattr(conn, '__dataclass_fields__'))

    def test_connection_repr(self):
        """Test string representation of Connection."""
        conn = Connection("sensor_1", "on_activate", "conveyor_1", "start")

        repr_str = repr(conn)
        self.assertIn("Connection", repr_str)
        self.assertIn("sensor_1", repr_str)
        self.assertIn("on_activate", repr_str)
        self.assertIn("conveyor_1", repr_str)
        self.assertIn("start", repr_str)

    def test_connection_field_mutation(self):
        """Test that connection fields can be mutated."""
        conn = Connection("s1", "out1", "t1", "in1", enabled=True)

        conn.enabled = False
        self.assertFalse(conn.enabled)

        conn.source_id = "new_source"
        self.assertEqual(conn.source_id, "new_source")


class TestConnectable(unittest.TestCase):
    """Test cases for Connectable class."""

    def test_initialization_with_id(self):
        """Test initialization with ID."""
        obj = Connectable(id="test_obj_1")

        self.assertEqual(obj.id, "test_obj_1")

    def test_initialization_creates_empty_connections(self):
        """Test that initialization creates empty connections list."""
        obj = Connectable(id="obj_1")

        connections = obj.get_connections()
        self.assertIsInstance(connections, list)
        self.assertEqual(len(connections), 0)

    def test_get_connections_returns_list(self):
        """Test get_connections returns a list."""
        obj = Connectable(id="obj_1")

        connections = obj.get_connections()
        self.assertIsInstance(connections, list)

    def test_set_connections_single(self):
        """Test setting a single connection."""
        obj = Connectable(id="obj_1")
        conn = Connection("obj_1", "output", "obj_2", "input")

        obj.set_connections([conn])

        connections = obj.get_connections()
        self.assertEqual(len(connections), 1)
        self.assertEqual(connections[0], conn)

    def test_set_connections_multiple(self):
        """Test setting multiple connections."""
        obj = Connectable(id="obj_1")
        conn1 = Connection("obj_1", "out1", "obj_2", "in1")
        conn2 = Connection("obj_1", "out2", "obj_3", "in2")
        conn3 = Connection("obj_1", "out3", "obj_4", "in3")

        obj.set_connections([conn1, conn2, conn3])

        connections = obj.get_connections()
        self.assertEqual(len(connections), 3)
        self.assertIn(conn1, connections)
        self.assertIn(conn2, connections)
        self.assertIn(conn3, connections)

    def test_set_connections_replaces_existing(self):
        """Test that set_connections replaces existing connections."""
        obj = Connectable(id="obj_1")
        conn1 = Connection("obj_1", "out1", "obj_2", "in1")
        conn2 = Connection("obj_1", "out2", "obj_3", "in2")

        obj.set_connections([conn1])
        self.assertEqual(len(obj.get_connections()), 1)

        obj.set_connections([conn2])
        connections = obj.get_connections()
        self.assertEqual(len(connections), 1)
        self.assertEqual(connections[0], conn2)
        self.assertNotIn(conn1, connections)

    def test_set_connections_empty_list(self):
        """Test setting empty connections list."""
        obj = Connectable(id="obj_1")
        conn = Connection("obj_1", "output", "obj_2", "input")

        obj.set_connections([conn])
        self.assertEqual(len(obj.get_connections()), 1)

        obj.set_connections([])
        self.assertEqual(len(obj.get_connections()), 0)

    def test_connections_list_is_mutable(self):
        """Test that connections list is mutable."""
        obj = Connectable(id="obj_1")
        conn1 = Connection("obj_1", "out1", "obj_2", "in1")
        conn2 = Connection("obj_1", "out2", "obj_3", "in2")

        obj.set_connections([conn1])
        connections = obj.get_connections()
        connections.append(conn2)

        # The returned list should be the same reference
        obj.set_connections(connections)
        self.assertEqual(len(obj.get_connections()), 2)

    def test_inherits_from_hasid(self):
        """Test that Connectable inherits from HasId."""
        obj = Connectable(id="test_id")

        # Should have id property from HasId
        self.assertTrue(hasattr(obj, 'id'))
        self.assertEqual(obj.id, "test_id")

    def test_get_id_method(self):
        """Test get_id method from IHasId interface."""
        obj = Connectable(id="my_object_123")

        self.assertEqual(obj.get_id(), "my_object_123")

    def test_multiple_instances_independent(self):
        """Test that multiple instances have independent connection lists."""
        obj1 = Connectable(id="obj_1")
        obj2 = Connectable(id="obj_2")

        conn1 = Connection("obj_1", "out", "obj_2", "in")
        conn2 = Connection("obj_2", "out", "obj_3", "in")

        obj1.set_connections([conn1])
        obj2.set_connections([conn2])

        self.assertEqual(len(obj1.get_connections()), 1)
        self.assertEqual(len(obj2.get_connections()), 1)
        self.assertEqual(obj1.get_connections()[0], conn1)
        self.assertEqual(obj2.get_connections()[0], conn2)


class TestConnectableIntegration(unittest.TestCase):
    """Integration tests for Connectable with Connection."""

    def test_connection_workflow(self):
        """Test complete connection workflow."""
        source = Connectable(id="sensor_1")
        target = Connectable(id="conveyor_1")

        # Create connection
        conn = Connection(
            source_id=source.id,
            source_output="on_activate_callbacks",
            target_id=target.id,
            target_input="activate"
        )

        # Add to source
        source.set_connections([conn])

        # Verify
        connections = source.get_connections()
        self.assertEqual(len(connections), 1)
        self.assertEqual(connections[0].source_id, "sensor_1")
        self.assertEqual(connections[0].target_id, "conveyor_1")

    def test_bidirectional_connections(self):
        """Test bidirectional connections between two objects."""
        obj1 = Connectable(id="obj_1")
        obj2 = Connectable(id="obj_2")

        # Connection from obj1 to obj2
        conn1_to_2 = Connection(
            source_id="obj_1",
            source_output="output_signal",
            target_id="obj_2",
            target_input="input_receiver"
        )

        # Connection from obj2 to obj1
        conn2_to_1 = Connection(
            source_id="obj_2",
            source_output="feedback_signal",
            target_id="obj_1",
            target_input="feedback_receiver"
        )

        obj1.set_connections([conn1_to_2])
        obj2.set_connections([conn2_to_1])

        self.assertEqual(len(obj1.get_connections()), 1)
        self.assertEqual(len(obj2.get_connections()), 1)
        self.assertEqual(obj1.get_connections()[0].target_id, "obj_2")
        self.assertEqual(obj2.get_connections()[0].target_id, "obj_1")

    def test_disabled_connection(self):
        """Test creating and managing disabled connections."""
        obj = Connectable(id="obj_1")

        active_conn = Connection("obj_1", "out1", "obj_2", "in1", enabled=True)
        disabled_conn = Connection("obj_1", "out2", "obj_3", "in2", enabled=False)

        obj.set_connections([active_conn, disabled_conn])

        connections = obj.get_connections()
        active_connections = [c for c in connections if c.enabled]
        disabled_connections = [c for c in connections if not c.enabled]

        self.assertEqual(len(active_connections), 1)
        self.assertEqual(len(disabled_connections), 1)

    def test_connection_graph_scenario(self):
        """Test a more complex connection graph."""
        sensor = Connectable(id="proximity_sensor")
        conveyor = Connectable(id="main_conveyor")
        light = Connectable(id="status_light")
        plc = Connectable(id="plc_controller")

        # Sensor -> Conveyor
        sensor.set_connections([
            Connection("proximity_sensor", "on_activate", "main_conveyor", "start")
        ])

        # Conveyor -> Light and PLC
        conveyor.set_connections([
            Connection("main_conveyor", "on_start", "status_light", "turn_green"),
            Connection("main_conveyor", "on_error", "plc_controller", "handle_error")
        ])

        self.assertEqual(len(sensor.get_connections()), 1)
        self.assertEqual(len(conveyor.get_connections()), 2)
        self.assertEqual(len(light.get_connections()), 0)
        self.assertEqual(len(plc.get_connections()), 0)


if __name__ == '__main__':
    unittest.main()

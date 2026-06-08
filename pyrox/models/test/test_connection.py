"""Unit tests for ConnectionRegistry class."""
import pytest
from typing import Any
from pyrox.models.connection import ConnectionRegistry, Connectable
from pyrox.interfaces import Connection, IConnectable


class _Sensor(IConnectable):
    def __init__(self, id_: str):
        super().__init__()
        self._id = id_
        self.on_activate_callbacks: list = []
        self.on_deactivate_callbacks: list = []

    def get_id(self) -> str:
        return self._id

    def set_id(self, id_: str) -> None:
        self._id = id_

    @property
    def id_(self) -> str:
        return self.get_id()

    def get_inputs(self) -> dict[str, Any]:
        return {}

    def get_outputs(self) -> dict[str, Any]:
        return {
            "on_activate_callbacks": self.on_activate_callbacks,
            "on_deactivate_callbacks": self.on_deactivate_callbacks,
        }


class _Motor(IConnectable):
    def __init__(self, id_: str):
        super().__init__()
        self._id = id_
        self.speed = 0.0
        self.start_called = False
        self.stop_called = False

    def get_id(self) -> str:
        return self._id

    def set_id(self, id_: str) -> None:
        self._id = id_

    @property
    def id_(self) -> str:
        return self.get_id()

    def start(self):
        self.start_called = True
        self.speed = 100.0

    def stop(self):
        self.stop_called = True
        self.speed = 0.0

    def set_speed(self, speed: float):
        self.speed = speed

    def get_inputs(self) -> dict[str, Any]:
        return {
            "start": self.start,
            "stop": self.stop,
            "set_speed": self.set_speed,
        }

    def get_outputs(self) -> dict[str, Any]:
        return {}


class TestConnectionRegistry:
    """Test cases for ConnectionRegistry class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.registry = ConnectionRegistry()  # pylint: disable=attribute-defined-outside-init
        self.sensor = _Sensor("sensor_001")  # pylint: disable=attribute-defined-outside-init
        self.motor = _Motor("motor_001")  # pylint: disable=attribute-defined-outside-init

    def test_init(self):
        """Test ConnectionRegistry initialization."""
        assert isinstance(self.registry, ConnectionRegistry)
        assert isinstance(self.registry.connections, list)
        assert isinstance(self.registry.objects, dict)
        assert len(self.registry.connections) == 0
        assert len(self.registry.objects) == 0

    def test_register_object(self):
        """Test registering an object."""
        self.registry.register_object("sensor_001", self.sensor)
        assert len(self.registry.objects) == 1
        assert 'sensor_001' in self.registry.objects
        assert self.registry.objects['sensor_001'] is self.sensor

    def test_register_multiple_objects(self):
        """Test registering multiple objects."""
        sensor1 = _Sensor("sensor_001")
        sensor2 = _Sensor("sensor_002")
        motor = _Motor("motor_001")

        self.registry.register_object("sensor_001", sensor1)
        self.registry.register_object("sensor_002", sensor2)
        self.registry.register_object("motor_001", motor)

        assert len(self.registry.objects) == 3
        assert 'sensor_001' in self.registry.objects
        assert 'sensor_002' in self.registry.objects
        assert 'motor_001' in self.registry.objects
        assert self.registry.objects['sensor_001'] is sensor1
        assert self.registry.objects['sensor_002'] is sensor2
        assert self.registry.objects['motor_001'] is motor

    def test_register_object_overwrites_existing(self):
        """Test that registering same ID overwrites previous object."""
        sensor1 = _Sensor("sensor_001")
        sensor2 = _Sensor("sensor_001")

        self.registry.register_object("sensor_001", sensor1)
        self.registry.register_object("sensor_001", sensor2)

        assert len(self.registry.objects) == 1
        assert 'sensor_001' in self.registry.objects
        assert self.registry.objects['sensor_001'] is sensor2

    def test_connect_creates_connection(self):
        """Test that connect creates a Connection."""
        sensor = _Sensor("sensor_001")
        motor = _Motor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        conn = self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )

        assert isinstance(conn, Connection)
        assert conn.source_id == "sensor_001"
        assert conn.source_output == "on_activate_callbacks"
        assert conn.target_id == "motor_001"
        assert conn.target_input == "start"
        assert conn.enabled is True

    def test_connect_adds_to_connections_list(self):
        """Test that connect adds connection to internal list."""
        sensor = _Sensor("sensor_001")
        motor = _Motor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        assert len(self.registry.connections) == 0
        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )

        assert len(self.registry.connections) == 1
        conn = self.registry.connections[0]
        assert conn.source_id == "sensor_001"
        assert conn.source_output == "on_activate_callbacks"
        assert conn.target_id == "motor_001"
        assert conn.target_input == "start"
        assert conn.enabled is True

    def test_connect_wires_callback(self):
        """Test that connect actually wires the callback."""
        sensor = _Sensor("sensor_001")
        motor = _Motor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )

        # Verify callback was added to sensor's callback list
        assert len(sensor.on_activate_callbacks) == 1
        # Check the callback is bound to the correct method
        callback = sensor.on_activate_callbacks[0]
        assert callable(callback)
        assert hasattr(callback, "__name__")
        assert hasattr(callback, "__self__")
        assert callback.__name__ == "start"
        assert callback.__self__ is motor  # type: ignore

    def test_connect_callback_is_functional(self):
        """Test that the wired callback actually works."""
        sensor = _Sensor("sensor_001")
        motor = _Motor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )

        # Trigger the callback
        assert not motor.start_called
        sensor.on_activate_callbacks[0]()
        assert motor.start_called
        assert motor.speed == 100.0

    def test_connect_multiple_connections(self):
        """Test creating multiple connections."""
        sensor1 = _Sensor("sensor_001")
        sensor2 = _Sensor("sensor_002")
        motor1 = _Motor("motor_001")
        motor2 = _Motor("motor_002")

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

        assert len(self.registry.connections) == 2
        assert conn1 in self.registry.connections
        assert conn2 in self.registry.connections

    def test_connect_one_to_many(self):
        """Test connecting one source to multiple targets."""
        sensor = _Sensor("sensor_001")
        motor1 = _Motor("motor_001")
        motor2 = _Motor("motor_002")

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

        assert len(self.registry.connections) == 2
        assert len(sensor.on_activate_callbacks) == 2

        for callback in sensor.on_activate_callbacks:
            callback()

        assert motor1.start_called
        assert motor2.start_called

    def test_connect_with_unregistered_source_raises_error(self):
        """Test that connecting unregistered source raises KeyError."""
        motor = _Motor("motor_001")
        self.registry.register_object("motor_001", motor)

        with pytest.raises(KeyError):
            self.registry.connect(
                "nonexistent", "on_activate_callbacks",
                "motor_001", "start"
            )

    def test_connect_with_unregistered_target_raises_error(self):
        """Test that connecting unregistered target raises KeyError."""
        sensor = _Sensor("sensor_001")
        self.registry.register_object("sensor_001", sensor)

        with pytest.raises(KeyError):
            self.registry.connect(
                "sensor_001", "on_activate_callbacks",
                "nonexistent", "start"
            )

    def test_connect_with_invalid_output_raises_error(self):
        """Test that connecting invalid output attribute raises AttributeError."""
        sensor = _Sensor("sensor_001")
        motor = _Motor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        with pytest.raises(AttributeError):
            self.registry.connect(
                "sensor_001", "nonexistent_output",
                "motor_001", "start"
            )

    def test_connect_with_invalid_input_raises_error(self):
        """Test that connecting invalid input attribute raises AttributeError."""
        sensor = _Sensor("sensor_001")
        motor = _Motor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        with pytest.raises(AttributeError):
            self.registry.connect(
                "sensor_001", "on_activate_callbacks",
                "motor_001", "nonexistent_input"
            )

    def test_serialize_empty_registry(self):
        """Test serializing empty registry."""
        result = self.registry.serialize()
        assert isinstance(result, dict)
        assert "connections" in result
        assert isinstance(result["connections"], list)
        assert len(result["connections"]) == 0

    def test_serialize_single_connection(self):
        """Test serializing registry with one connection."""
        sensor = _Sensor("sensor_001")
        motor = _Motor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )

        result = self.registry.serialize()

        assert len(result["connections"]) == 1
        conn_data = result["connections"][0]
        assert conn_data["source"] == "sensor_001"
        assert conn_data["output"] == "on_activate_callbacks"
        assert conn_data["target"] == "motor_001"
        assert conn_data["input"] == "start"
        assert "enabled" in conn_data

    def test_serialize_multiple_connections(self):
        """Test serializing registry with multiple connections."""
        sensor1 = _Sensor("sensor_001")
        sensor2 = _Sensor("sensor_002")
        motor1 = _Motor("motor_001")
        motor2 = _Motor("motor_002")

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

        assert len(result["connections"]) == 2

        # Check first connection
        conn1 = result["connections"][0]
        assert conn1["source"] == "sensor_001"
        assert conn1["output"] == "on_activate_callbacks"
        assert conn1["target"] == "motor_001"
        assert conn1["input"] == "start"

        # Check second connection
        conn2 = result["connections"][1]
        assert conn2["source"] == "sensor_002"
        assert conn2["output"] == "on_deactivate_callbacks"
        assert conn2["target"] == "motor_002"
        assert conn2["input"] == "stop"

    def test_serialize_preserves_connection_order(self):
        """Test that serialize preserves connection order."""
        sensor = _Sensor("sensor_001")
        motor1 = _Motor("motor_001")
        motor2 = _Motor("motor_002")
        motor3 = _Motor("motor_003")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor1)
        self.registry.register_object("motor_002", motor2)
        self.registry.register_object("motor_003", motor3)

        self.registry.connect("sensor_001", "on_activate_callbacks", "motor_001", "start")
        self.registry.connect("sensor_001", "on_activate_callbacks", "motor_002", "start")
        self.registry.connect("sensor_001", "on_activate_callbacks", "motor_003", "start")

        result = self.registry.serialize()

        assert result["connections"][0]["target"] == "motor_001"
        assert result["connections"][1]["target"] == "motor_002"
        assert result["connections"][2]["target"] == "motor_003"

    def test_connection_enabled_in_serialization(self):
        """Test that enabled field is included in serialization."""
        sensor = _Sensor("sensor_001")
        motor = _Motor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )

        result = self.registry.serialize()
        conn_data = result["connections"][0]

        assert 'enabled' in conn_data
        assert isinstance(conn_data['enabled'], bool)

    def test_integration_sensor_motor_workflow(self):
        """Integration test: sensor triggers motor through connection."""
        sensor = _Sensor("checkpoint_001")
        motor = _Motor("conveyor_motor_001")

        # Register objects
        self.registry.register_object("checkpoint_001", sensor)
        self.registry.register_object("conveyor_motor_001", motor)

        # Create connection
        self.registry.connect(
            "checkpoint_001", "on_activate_callbacks",
            "conveyor_motor_001", "start"
        )

        # Simulate sensor activation\
        assert not motor.start_called
        assert motor.speed == 0.0

        # Trigger all callbacks on sensor activation
        for callback in sensor.on_activate_callbacks:
            callback()

        # Verify motor started
        assert motor.start_called
        assert motor.speed == 100.0

    def test_integration_bidirectional_connections(self):
        """Integration test: bidirectional connections between sensors and motors."""
        sensor = _Sensor("sensor_001")
        motor = _Motor("motor_001")

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
        assert motor.start_called
        assert motor.speed == 100.0

        # Test deactivation
        sensor.on_deactivate_callbacks[0]()
        assert motor.stop_called
        assert motor.speed == 0.0

    def test_unregister_object_removes_connections(self):
        """Test that unregistering an object removes its connections."""
        sensor = _Sensor("sensor_001")
        motor = _Motor("motor_001")

        self.registry.register_object("sensor_001", sensor)
        self.registry.register_object("motor_001", motor)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start"
        )

        assert len(self.registry.connections) == 1

        # Unregister sensor
        self.registry.unregister_object("sensor_001")

        assert len(self.registry.connections) == 0
        assert 'sensor_001' not in self.registry.objects
        assert not sensor.on_activate_callbacks  # Callbacks should be unwired

    def test_unregister_object_not_registered(self):
        """Test that unregistering a non-registered object does not raise error."""
        assert len(self.registry.objects) == 0
        self.registry.unregister_object("nonexistent")  # Should not raise
        assert len(self.registry.objects) == 0

    def test_unregister_object_removes_multiple_connections(self):
        """Test that unregistering an object removes all its connections."""
        sensor1 = _Sensor("sensor_001")
        sensor2 = _Sensor("sensor_002")
        motor = _Motor("motor_001")

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

        assert len(self.registry.connections) == 2

        # Unregister motor
        self.registry.unregister_object("motor_001")

        assert len(self.registry.connections) == 0
        assert 'motor_001' not in self.registry.objects

    # ------------------------------------------------------------------
    # get_object
    # ------------------------------------------------------------------

    def test_get_object_returns_registered_object(self):
        """Test that get_object returns the object registered under that ID."""
        self.registry.register_object("sensor_001", self.sensor)
        assert self.registry.get_object("sensor_001") is self.sensor

    def test_get_object_returns_none_for_unknown_id(self):
        """Test that get_object returns None when the ID is not registered."""
        assert self.registry.get_object("nonexistent") is None

    # ------------------------------------------------------------------
    # connect(enabled=False)
    # ------------------------------------------------------------------

    def test_connect_disabled_records_connection(self):
        """Test that a disabled connection is still recorded in the list."""
        self.registry.register_object("sensor_001", self.sensor)
        self.registry.register_object("motor_001", self.motor)

        conn = self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
            enabled=False,
        )

        assert len(self.registry.connections) == 1
        assert conn.enabled is False

    def test_connect_disabled_does_not_wire_callback(self):
        """Test that a disabled connection does not append to the callback list."""
        self.registry.register_object("sensor_001", self.sensor)
        self.registry.register_object("motor_001", self.motor)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
            enabled=False,
        )

        assert len(self.sensor.on_activate_callbacks) == 0

    def test_connect_disabled_does_not_fire_target(self):
        """Test that firing callbacks on the source does not call the target."""
        self.registry.register_object("sensor_001", self.sensor)
        self.registry.register_object("motor_001", self.motor)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
            enabled=False,
        )

        for cb in self.sensor.on_activate_callbacks:
            cb()

        assert not self.motor.start_called

    # ------------------------------------------------------------------
    # duplicate connect
    # ------------------------------------------------------------------

    def test_connect_duplicate_raises(self):
        """Test that connecting the same source/output/target/input pair twice raises ValueError."""
        self.registry.register_object("sensor_001", self.sensor)
        self.registry.register_object("motor_001", self.motor)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
        )

        with pytest.raises(ValueError):
            self.registry.connect(
                "sensor_001", "on_activate_callbacks",
                "motor_001", "start",
            )

    def test_connect_duplicate_does_not_add_second_record(self):
        """Test that a failed duplicate connect leaves the registry unchanged."""
        self.registry.register_object("sensor_001", self.sensor)
        self.registry.register_object("motor_001", self.motor)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
        )

        with pytest.raises(ValueError):
            self.registry.connect(
                "sensor_001", "on_activate_callbacks",
                "motor_001", "start",
            )

        assert len(self.registry.connections) == 1
        assert len(self.sensor.on_activate_callbacks) == 1

    # ------------------------------------------------------------------
    # disconnect
    # ------------------------------------------------------------------

    def test_disconnect_returns_true_when_found(self):
        """Test that disconnect returns True when the connection exists."""
        self.registry.register_object("sensor_001", self.sensor)
        self.registry.register_object("motor_001", self.motor)
        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
        )

        result = self.registry.disconnect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
        )

        assert result is True

    def test_disconnect_returns_false_when_not_found(self):
        """Test that disconnect returns False when no matching connection exists."""
        result = self.registry.disconnect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
        )
        assert result is False

    def test_disconnect_removes_connection_record(self):
        """Test that disconnect removes the connection from the internal list."""
        self.registry.register_object("sensor_001", self.sensor)
        self.registry.register_object("motor_001", self.motor)
        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
        )

        assert len(self.registry.connections) == 1
        self.registry.disconnect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
        )
        assert len(self.registry.connections) == 0

    def test_disconnect_unwires_callback(self):
        """Test that disconnect removes the bound method from the source callback list."""
        self.registry.register_object("sensor_001", self.sensor)
        self.registry.register_object("motor_001", self.motor)
        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
        )

        assert len(self.sensor.on_activate_callbacks) == 1
        self.registry.disconnect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
        )
        assert len(self.sensor.on_activate_callbacks) == 0

    def test_disconnect_callback_no_longer_fires(self):
        """Test that after disconnect the target method is no longer called."""
        self.registry.register_object("sensor_001", self.sensor)
        self.registry.register_object("motor_001", self.motor)
        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
        )
        self.registry.disconnect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
        )

        for cb in self.sensor.on_activate_callbacks:
            cb()

        assert not self.motor.start_called

    def test_disconnect_only_removes_matching_connection(self):
        """Test that disconnect leaves other connections intact."""
        motor2 = _Motor("motor_002")
        self.registry.register_object("sensor_001", self.sensor)
        self.registry.register_object("motor_001", self.motor)
        self.registry.register_object("motor_002", motor2)
        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
        )
        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_002", "start",
        )

        self.registry.disconnect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
        )

        assert len(self.registry.connections) == 1
        assert self.registry.connections[0].target_id == "motor_002"
        assert len(self.sensor.on_activate_callbacks) == 1

    def test_connect_disabled_allows_later_enabled_connect_after_disconnect(self):
        """Test that a disabled connection can be removed and re-added enabled."""
        self.registry.register_object("sensor_001", self.sensor)
        self.registry.register_object("motor_001", self.motor)

        self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
            enabled=False,
        )
        self.registry.disconnect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
        )
        conn = self.registry.connect(
            "sensor_001", "on_activate_callbacks",
            "motor_001", "start",
            enabled=True,
        )

        assert conn.enabled is True
        assert len(self.sensor.on_activate_callbacks) == 1


class TestConnection:
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
        assert conn.source_id == "sensor_1"
        assert conn.source_output == "on_activate_callbacks"
        assert conn.target_id == "conveyor_1"
        assert conn.target_input == "activate"
        assert conn.enabled is True

    def test_connection_initialization_default_enabled(self):
        """Test initialization with default enabled=True."""
        conn = Connection(
            source_id="obj_1",
            source_output="output_1",
            target_id="obj_2",
            target_input="input_1"
        )
        assert conn.enabled is True

    def test_connection_initialization_disabled(self):
        """Test initialization with enabled=False."""
        conn = Connection(
            source_id="obj_1",
            source_output="output_1",
            target_id="obj_2",
            target_input="input_1",
            enabled=False
        )
        assert conn.enabled is False

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
        assert conn1 == conn2

    def test_connection_inequality_different_source(self):
        """Test that connections with different sources are not equal."""
        conn1 = Connection("s1", "out1", "t1", "in1")
        conn2 = Connection("s2", "out1", "t1", "in1")
        assert conn1 != conn2

    def test_connection_inequality_different_output(self):
        """Test that connections with different outputs are not equal."""
        conn1 = Connection("s1", "out1", "t1", "in1")
        conn2 = Connection("s1", "out2", "t1", "in1")
        assert conn1 != conn2

    def test_connection_inequality_different_target(self):
        """Test that connections with different targets are not equal."""
        conn1 = Connection("s1", "out1", "t1", "in1")
        conn2 = Connection("s1", "out1", "t2", "in1")
        assert conn1 != conn2

    def test_connection_inequality_different_input(self):
        """Test that connections with different inputs are not equal."""
        conn1 = Connection("s1", "out1", "t1", "in1")
        conn2 = Connection("s1", "out1", "t1", "in2")
        assert conn1 != conn2

    def test_connection_inequality_different_enabled(self):
        """Test that connections with different enabled states are not equal."""
        conn1 = Connection("s1", "out1", "t1", "in1", enabled=True)
        conn2 = Connection("s1", "out1", "t1", "in1", enabled=False)
        assert conn1 != conn2

    def test_connection_is_dataclass(self):
        """Test that Connection is a dataclass."""
        conn = Connection("s1", "out1", "t1", "in1")
        assert hasattr(conn, '__dataclass_fields__'), "Connection should be a dataclass"

    def test_connection_repr(self):
        """Test string representation of Connection."""
        conn = Connection("sensor_1", "on_activate", "conveyor_1", "start")

        repr_str = repr(conn)
        assert 'Connection(' in repr_str
        assert "source_id='sensor_1'" in repr_str
        assert "source_output='on_activate'" in repr_str
        assert "target_id='conveyor_1'" in repr_str
        assert "target_input='start'" in repr_str

    def test_connection_field_mutation(self):
        """Test that connection fields can be mutated."""
        conn = Connection("s1", "out1", "t1", "in1", enabled=True)

        conn.enabled = False
        assert not conn.enabled
        conn.source_id = "new_source"
        assert conn.source_id == 'new_source'


class TestConnectable:
    """Test cases for Connectable class."""

    def test_initialization_with_id(self):
        """Test initialization with ID."""
        obj = Connectable(id_="test_obj_1")
        assert obj.id_ == "test_obj_1"

    def test_inherits_from_hasid(self):
        """Test that Connectable inherits from HasId."""
        obj = Connectable(id_="test_id")

        assert hasattr(obj, 'get_id')
        assert obj.get_id() == "test_id"

    def test_get_id_method(self):
        """Test get_id method from IHasId interface."""
        obj = Connectable(id_="my_object_123")
        assert obj.get_id() == "my_object_123"

    def test_get_inputs_outputs_empty(self):
        """Test that get_inputs and get_outputs return empty dict by default."""
        obj = Connectable(id_="test_obj")
        assert isinstance(obj.get_inputs(), dict)
        assert isinstance(obj.get_outputs(), dict)
        assert len(obj.get_inputs()) == 0
        assert len(obj.get_outputs()) == 0

    def test_get_inputs_outputs_override(self):
        """Test that get_inputs and get_outputs can be overridden."""
        class CustomConnectable(Connectable):
            def get_inputs(self) -> dict[str, Any]:
                return {"input1": lambda x: x}

            def get_outputs(self) -> dict[str, Any]:
                return {"output1": []}

        obj = CustomConnectable(id_="custom_obj")
        assert 'input1' in obj.get_inputs()
        assert 'output1' in obj.get_outputs()


if __name__ == '__main__':
    pytest.main()

"""Comprehensive unit tests for connection.py module."""
import unittest
from unittest.mock import Mock, patch
from enum import Enum

from pyrox.models.plc.connection import (
    ConnectionParameters,
    ConnectionCommand,
    ConnectionCommandType,
    ControllerConnection
)
from pyrox.models.abc.network import Ipv4Address
from pyrox.services.timer import TimerService
from pylogix.lgx_response import Response


class TestConnectionParameters(unittest.TestCase):
    """Test cases for ConnectionParameters class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_ip = Ipv4Address("192.168.1.10")
        self.test_slot = 1
        self.test_rpi = 500

    def test_init_with_required_parameters(self):
        """Test initialization with required parameters only."""
        params = ConnectionParameters(self.test_ip, self.test_slot)

        self.assertEqual(params.ip_address, self.test_ip)
        self.assertEqual(params.slot, self.test_slot)
        self.assertEqual(params.rpi, 250)  # Default value

    def test_init_with_all_parameters(self):
        """Test initialization with all parameters."""
        params = ConnectionParameters(self.test_ip, self.test_slot, self.test_rpi)

        self.assertEqual(params.ip_address, self.test_ip)
        self.assertEqual(params.slot, self.test_slot)
        self.assertEqual(params.rpi, self.test_rpi)

    def test_rpi_property_getter(self):
        """Test RPI property getter."""
        params = ConnectionParameters(self.test_ip, self.test_slot, 123.5)  # type: ignore

        self.assertEqual(params.rpi, 123.5)
        self.assertIsInstance(params.rpi, float)

    def test_rpi_property_setter_valid_values(self):
        """Test RPI property setter with valid values."""
        params = ConnectionParameters(self.test_ip, self.test_slot)

        # Test integer value
        params.rpi = 100
        self.assertEqual(params.rpi, 100.0)
        self.assertIsInstance(params.rpi, float)

        # Test float value
        params.rpi = 250.5
        self.assertEqual(params.rpi, 250.5)

        # Test minimum valid value
        params.rpi = 1
        self.assertEqual(params.rpi, 1.0)

    def test_rpi_property_setter_invalid_type(self):
        """Test RPI property setter with invalid types."""
        params = ConnectionParameters(self.test_ip, self.test_slot)

        with self.assertRaises(TypeError) as context:
            params.rpi = "250"  # type: ignore

        self.assertIn("rpi must be a number", str(context.exception))

        with self.assertRaises(TypeError) as context:
            params.rpi = None  # type: ignore

        self.assertIn("rpi must be a number", str(context.exception))

    def test_rpi_property_setter_invalid_value(self):
        """Test RPI property setter with invalid values."""
        params = ConnectionParameters(self.test_ip, self.test_slot)

        with self.assertRaises(ValueError) as context:
            params.rpi = 0

        self.assertIn("rpi must be a positive number", str(context.exception))

        with self.assertRaises(ValueError) as context:
            params.rpi = -100

        self.assertIn("rpi must be a positive number", str(context.exception))

    def test_slot_property_getter(self):
        """Test slot property getter."""
        params = ConnectionParameters(self.test_ip, 5)

        self.assertEqual(params.slot, 5)
        self.assertIsInstance(params.slot, int)

    def test_slot_property_setter_valid_values(self):
        """Test slot property setter with valid values."""
        params = ConnectionParameters(self.test_ip, self.test_slot)

        # Test minimum value
        params.slot = 0
        self.assertEqual(params.slot, 0)

        # Test maximum value
        params.slot = 16
        self.assertEqual(params.slot, 16)

        # Test middle value
        params.slot = 8
        self.assertEqual(params.slot, 8)

    def test_slot_property_setter_invalid_type(self):
        """Test slot property setter with invalid types."""
        params = ConnectionParameters(self.test_ip, self.test_slot)

        with self.assertRaises(TypeError) as context:
            params.slot = 5.5  # type: ignore

        self.assertIn("slot must be an integer", str(context.exception))

    def test_slot_property_setter_invalid_value(self):
        """Test slot property setter with invalid values."""
        params = ConnectionParameters(self.test_ip, self.test_slot)

        with self.assertRaises(ValueError) as context:
            params.slot = -1

        self.assertIn("slot must be a non-negative integer", str(context.exception))

        with self.assertRaises(ValueError) as context:
            params.slot = 17

        self.assertIn("slot must be between 0 and 16", str(context.exception))


class TestConnectionCommandType(unittest.TestCase):
    """Test cases for ConnectionCommandType enum."""

    def test_enum_values(self):
        """Test that enum has correct values."""
        self.assertEqual(ConnectionCommandType.NA.value, 0)
        self.assertEqual(ConnectionCommandType.READ.value, 1)
        self.assertEqual(ConnectionCommandType.WRITE.value, 2)

    def test_enum_inheritance(self):
        """Test that ConnectionCommandType inherits from Enum."""
        self.assertTrue(issubclass(ConnectionCommandType, Enum))

    def test_enum_members(self):
        """Test that enum has all expected members."""
        expected_members = ['NA', 'READ', 'WRITE']
        actual_members = [member.name for member in ConnectionCommandType]

        self.assertEqual(set(actual_members), set(expected_members))


class TestConnectionCommand(unittest.TestCase):
    """Test cases for ConnectionCommand class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_callback = Mock()
        self.test_command = ConnectionCommand(
            type=ConnectionCommandType.READ,
            tag_name="TestTag",
            tag_value=42,
            data_type=1,
            response_cb=self.mock_callback
        )

    def test_init(self):
        """Test ConnectionCommand initialization."""
        self.assertEqual(self.test_command.type, ConnectionCommandType.READ)
        self.assertEqual(self.test_command.tag_name, "TestTag")
        self.assertEqual(self.test_command.tag_value, 42)
        self.assertEqual(self.test_command.data_type, 1)
        self.assertEqual(self.test_command.response_cb, self.mock_callback)

    def test_init_with_different_types(self):
        """Test initialization with different command types."""
        read_cmd = ConnectionCommand(
            ConnectionCommandType.READ, "ReadTag", 0, 1, self.mock_callback
        )
        self.assertEqual(read_cmd.type, ConnectionCommandType.READ)

        write_cmd = ConnectionCommand(
            ConnectionCommandType.WRITE, "WriteTag", 100, 2, self.mock_callback
        )
        self.assertEqual(write_cmd.type, ConnectionCommandType.WRITE)

        na_cmd = ConnectionCommand(
            ConnectionCommandType.NA, "NoAction", 0, 0, self.mock_callback
        )
        self.assertEqual(na_cmd.type, ConnectionCommandType.NA)

    def test_callback_is_callable(self):
        """Test that response callback is callable."""
        self.assertTrue(callable(self.test_command.response_cb))

    def test_attributes_assignment(self):
        """Test that all attributes can be assigned and retrieved."""
        cmd = ConnectionCommand(
            type=ConnectionCommandType.WRITE,
            tag_name="NewTag",
            tag_value="StringValue",  # type: ignore
            data_type=3,
            response_cb=lambda x: None
        )

        self.assertEqual(cmd.type, ConnectionCommandType.WRITE)
        self.assertEqual(cmd.tag_name, "NewTag")
        self.assertEqual(cmd.tag_value, "StringValue")
        self.assertEqual(cmd.data_type, 3)
        self.assertTrue(callable(cmd.response_cb))


class TestControllerConnection(unittest.TestCase):
    """Test cases for ControllerConnection class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_ip = Ipv4Address("192.168.1.100")
        self.test_params = ConnectionParameters(self.test_ip, 1, 250)
        self.mock_callback = Mock()

        self.test_commands = [
            ConnectionCommand(
                ConnectionCommandType.READ,
                "TestTag1",
                0,
                1,
                self.mock_callback
            ),
            ConnectionCommand(
                ConnectionCommandType.WRITE,
                "TestTag2",
                42,
                1,
                self.mock_callback
            )
        ]

    def tearDown(self):
        """Clean up after tests."""
        # Ensure timer service is properly shutdown
        if hasattr(self, 'connection'):
            self.connection._timer_service.shutdown()  # type: ignore

    def test_init_with_parameters_only(self):
        """Test initialization with parameters only."""
        connection = ControllerConnection(self.test_params)

        self.assertEqual(connection.parameters, self.test_params)
        self.assertEqual(connection.commands, [])
        self.assertFalse(connection.is_connected)
        self.assertEqual(connection._commands, [])
        self.assertEqual(connection._subscribers, [])
        self.assertIsInstance(connection._timer_service, TimerService)

    def test_init_with_parameters_and_commands(self):
        """Test initialization with parameters and commands."""
        connection = ControllerConnection(self.test_params, self.test_commands)

        self.assertEqual(connection.parameters, self.test_params)
        self.assertEqual(connection.commands, self.test_commands)
        self.assertFalse(connection.is_connected)

    def test_subscribe_to_ticks_valid_callback(self):
        """Test subscribing to tick events with valid callback."""
        connection = ControllerConnection(self.test_params)
        callback = Mock()

        connection.subscribe_to_ticks(callback)

        self.assertIn(callback, connection._subscribers)

    def test_subscribe_to_ticks_invalid_callback(self):
        """Test subscribing to tick events with invalid callback."""
        connection = ControllerConnection(self.test_params)

        with self.assertRaises(ValueError) as context:
            connection.subscribe_to_ticks("not_callable")  # type: ignore

        self.assertIn("Callback must be callable", str(context.exception))

    def test_unsubscribe_from_ticks_existing_callback(self):
        """Test unsubscribing existing callback from tick events."""
        connection = ControllerConnection(self.test_params)
        callback = Mock()

        # Subscribe first
        connection.subscribe_to_ticks(callback)
        self.assertIn(callback, connection._subscribers)

        # Unsubscribe
        connection.unsubscribe_from_ticks(callback)
        self.assertNotIn(callback, connection._subscribers)

    def test_unsubscribe_from_ticks_nonexistent_callback(self):
        """Test unsubscribing non-existent callback from tick events."""
        connection = ControllerConnection(self.test_params)
        callback = Mock()

        # Should not raise an exception
        connection.unsubscribe_from_ticks(callback)
        self.assertNotIn(callback, connection._subscribers)

    def test_tick_calls_all_subscribers(self):
        """Test that _tick calls all subscribed callbacks."""
        connection = ControllerConnection(self.test_params)
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()

        connection.subscribe_to_ticks(callback1)
        connection.subscribe_to_ticks(callback2)
        connection.subscribe_to_ticks(callback3)

        connection._tick()

        callback1.assert_called_once()
        callback2.assert_called_once()
        callback3.assert_called_once()

    def test_tick_with_no_subscribers(self):
        """Test that _tick works with no subscribers."""
        connection = ControllerConnection(self.test_params)

        # Should not raise an exception
        connection._tick()

    @patch('pyrox.models.plc.connection.PLC')
    def test_strobe_plc(self, mock_plc_class):
        """Test _strobe_plc method."""
        mock_plc_instance = Mock()
        mock_plc_class.return_value.__enter__.return_value = mock_plc_instance
        mock_response = Mock()
        mock_plc_instance.GetPLCTime.return_value = mock_response

        connection = ControllerConnection(self.test_params)
        result = connection._strobe_plc()

        mock_plc_class.assert_called_once_with(
            ip_address=str(self.test_params.ip_address),
            slot=self.test_params.slot
        )
        mock_plc_instance.GetPLCTime.assert_called_once()
        self.assertEqual(result, False)

    @patch('pyrox.models.plc.connection.PLC')
    def test_run_commands_read_success(self, mock_plc_class):
        """Test _run_commands_read with successful read operations."""
        mock_plc_instance = Mock()
        mock_plc_class.return_value.__enter__.return_value = mock_plc_instance
        mock_response = Mock()
        mock_plc_instance.Read.return_value = mock_response

        connection = ControllerConnection(self.test_params)
        connection.is_connected = True

        read_command = ConnectionCommand(
            ConnectionCommandType.READ,
            "TestReadTag",
            0,
            1,
            Mock()
        )
        connection._commands = [read_command]

        connection._run_commands_read(mock_plc_instance)

        mock_plc_instance.Read.assert_called_once_with("TestReadTag", datatype=1)
        read_command.response_cb.assert_called_once_with(mock_response)  # type: ignore

    @patch('pyrox.models.plc.connection.PLC')
    def test_run_commands_read_with_error(self, mock_plc_class):
        """Test _run_commands_read with KeyError exception."""
        mock_plc_instance = Mock()
        mock_plc_class.return_value.__enter__.return_value = mock_plc_instance
        mock_plc_instance.Read.side_effect = KeyError("Tag not found")

        connection = ControllerConnection(self.test_params)
        connection.is_connected = True

        read_command = ConnectionCommand(
            ConnectionCommandType.READ,
            "NonExistentTag",
            0,
            1,
            Mock()
        )
        connection._commands = [read_command]

        connection._run_commands_read(mock_plc_instance)

        # Should call callback with error response
        read_command.response_cb.assert_called_once()  # type: ignore
        args = read_command.response_cb.call_args[0]  # type: ignore
        self.assertIsInstance(args[0], Response)
        self.assertEqual(args[0].TagName, "NonExistentTag")
        self.assertIsNone(args[0].Value)
        self.assertEqual(args[0].Status, 'Error')

    @patch('pyrox.models.plc.connection.PLC')
    def test_run_commands_write_success(self, mock_plc_class):
        """Test _run_commands_write with successful write operations."""
        mock_plc_instance = Mock()
        mock_plc_class.return_value.__enter__.return_value = mock_plc_instance
        mock_response = Mock()
        mock_plc_instance.Write.return_value = mock_response

        connection = ControllerConnection(self.test_params)
        connection.is_connected = True

        write_command = ConnectionCommand(
            ConnectionCommandType.WRITE,
            "TestWriteTag",
            42,
            1,
            Mock()
        )
        connection._commands = [write_command]

        connection._run_commands_write(mock_plc_instance)

        mock_plc_instance.Write.assert_called_once_with("TestWriteTag", 42, datatype=1)
        write_command.response_cb.assert_called_once_with(mock_response)  # type: ignore

    @patch('pyrox.models.plc.connection.PLC')
    def test_run_commands_write_with_string_value(self, mock_plc_class):
        """Test _run_commands_write with string value that can't be converted to int."""
        mock_plc_instance = Mock()
        mock_plc_class.return_value.__enter__.return_value = mock_plc_instance
        mock_response = Mock()
        mock_plc_instance.Write.return_value = mock_response

        connection = ControllerConnection(self.test_params)
        connection.is_connected = True

        write_command = ConnectionCommand(
            ConnectionCommandType.WRITE,
            "TestStringTag",
            "Hello",  # type: ignore
            2,
            Mock()
        )
        connection._commands = [write_command]

        connection._run_commands_write(mock_plc_instance)

        mock_plc_instance.Write.assert_called_once_with("TestStringTag", "Hello", datatype=2)
        write_command.response_cb.assert_called_once_with(mock_response)  # type: ignore

    @patch('pyrox.models.plc.connection.PLC')
    def test_run_commands_write_with_error(self, mock_plc_class):
        """Test _run_commands_write with KeyError exception."""
        mock_plc_instance = Mock()
        mock_plc_class.return_value.__enter__.return_value = mock_plc_instance
        mock_plc_instance.Write.side_effect = KeyError("Tag not found")

        connection = ControllerConnection(self.test_params)
        connection.is_connected = True

        write_command = ConnectionCommand(
            ConnectionCommandType.WRITE,
            "NonExistentTag",
            100,
            1,
            Mock()
        )
        connection._commands = [write_command]

        connection._run_commands_write(mock_plc_instance)

        # Should call callback with error response
        write_command.response_cb.assert_called_once()  # type: ignore
        args = write_command.response_cb.call_args[0]  # type: ignore
        self.assertIsInstance(args[0], Response)
        self.assertEqual(args[0].TagName, "NonExistentTag")
        self.assertIsNone(args[0].Value)
        self.assertEqual(args[0].Status, 'Error')

    @patch('pyrox.models.plc.connection.PLC')
    def test_run_commands_mixed_types(self, mock_plc_class):
        """Test _run_commands with mixed read and write commands."""
        mock_plc_instance = Mock()
        mock_plc_class.return_value.__enter__.return_value = mock_plc_instance
        mock_read_response = Mock()
        mock_write_response = Mock()
        mock_plc_instance.Read.return_value = mock_read_response
        mock_plc_instance.Write.return_value = mock_write_response

        connection = ControllerConnection(self.test_params)
        connection.is_connected = True

        read_cmd = ConnectionCommand(ConnectionCommandType.READ, "ReadTag", 0, 1, Mock())
        write_cmd = ConnectionCommand(ConnectionCommandType.WRITE, "WriteTag", 123, 1, Mock())
        na_cmd = ConnectionCommand(ConnectionCommandType.NA, "NoActionTag", 0, 1, Mock())

        connection._commands = [read_cmd, write_cmd, na_cmd]

        with patch.object(connection, '_run_commands_read') as mock_read:
            with patch.object(connection, '_run_commands_write') as mock_write:
                connection._run_commands()

        mock_read.assert_called_once_with(mock_plc_instance)
        mock_write.assert_called_once_with(mock_plc_instance)

        # Commands should be cleared after execution
        self.assertEqual(connection._commands, [])

    def test_run_commands_when_disconnected(self):
        """Test _run_commands when connection is disconnected."""
        connection = ControllerConnection(self.test_params)
        connection.is_connected = False

        # Add some commands
        connection._commands = [Mock(), Mock()]

        with patch('pyrox.models.plc.connection.PLC') as mock_plc:
            connection._run_commands()

        # PLC should not be instantiated
        mock_plc.assert_not_called()

        # Commands should remain in buffer
        self.assertEqual(len(connection._commands), 2)

    @patch('pyrox.models.plc.connection.PLC')
    def test_schedule_when_connected(self, mock_plc_class):
        """Test _schedule when connection is active."""
        connection = ControllerConnection(self.test_params)
        connection.is_connected = True

        with patch.object(connection._timer_service, 'schedule_task') as mock_schedule:
            connection._schedule()

        mock_schedule.assert_called_once_with(connection._connection_loop, self.test_params.rpi)

    def test_schedule_when_disconnected(self):
        """Test _schedule when connection is inactive."""
        connection = ControllerConnection(self.test_params)
        connection.is_connected = False

        with patch.object(connection._timer_service, 'schedule_task') as mock_schedule:
            connection._schedule()

        mock_schedule.assert_not_called()

    def test_connect_delegates_to_private_connect(self):
        """Test that public connect method delegates to _connect."""
        connection = ControllerConnection(self.test_params)
        new_params = ConnectionParameters(Ipv4Address("10.0.0.1"), 2)

        with patch.object(connection, '_connect') as mock_connect:
            connection.connect(new_params)

        mock_connect.assert_called_once_with(new_params)

    def test_connect_without_parameters(self):
        """Test connect method without parameters."""
        connection = ControllerConnection(self.test_params)

        with patch.object(connection, '_connect') as mock_connect:
            connection.connect()

        mock_connect.assert_called_once_with(None)

    @patch.object(ControllerConnection, '_connection_loop')
    def test_private_connect_when_not_connected(self, mock_loop):
        """Test _connect when not already connected."""
        connection = ControllerConnection(self.test_params)
        connection.is_connected = False

        new_params = ConnectionParameters(Ipv4Address("10.0.0.1"), 2)
        connection._connect(new_params)

        self.assertEqual(connection.parameters, new_params)
        mock_loop.assert_called_once()

    @patch.object(ControllerConnection, '_connection_loop')
    def test_private_connect_when_already_connected(self, mock_loop):
        """Test _connect when already connected."""
        connection = ControllerConnection(self.test_params)
        connection.is_connected = True

        connection._connect()

        mock_loop.assert_not_called()

    @patch.object(ControllerConnection, '_connection_loop')
    def test_private_connect_without_new_parameters(self, mock_loop):
        """Test _connect without new parameters."""
        connection = ControllerConnection(self.test_params)
        connection.is_connected = False
        original_params = connection.parameters

        connection._connect()

        self.assertEqual(connection.parameters, original_params)
        mock_loop.assert_called_once()

    def test_connection_loop_when_disconnected(self):
        """Test _connection_loop when not connected."""
        connection = ControllerConnection(self.test_params)
        connection.is_connected = False

        with patch.object(connection, '_strobe_plc') as mock_strobe:
            with patch.object(connection, '_tick') as mock_tick:
                with patch.object(connection, '_run_commands') as mock_commands:
                    with patch.object(connection, '_schedule') as mock_schedule:
                        mock_strobe.return_value = False
                        connection._connection_loop()

        mock_strobe.assert_called_once()
        mock_tick.assert_not_called()
        mock_commands.assert_not_called()
        mock_schedule.assert_not_called()

    @patch('pyrox.models.plc.connection.PLC')
    def test_connection_loop_strobe_failure(self, mock_plc_class):
        """Test _connection_loop when strobe fails."""
        mock_plc_instance = Mock()
        mock_plc_class.return_value.__enter__.return_value = mock_plc_instance
        mock_plc_instance.GetPLCTime.return_value = False

        connection = ControllerConnection(self.test_params)
        connection.is_connected = True

        with patch.object(connection, '_strobe_plc', return_value=False):
            with patch.object(connection, '_tick') as mock_tick:
                with patch.object(connection, '_run_commands') as mock_commands:
                    with patch.object(connection, '_schedule') as mock_schedule:
                        connection._connection_loop()

        self.assertFalse(connection.is_connected)
        mock_tick.assert_not_called()
        mock_commands.assert_not_called()
        mock_schedule.assert_not_called()

    def test_connection_loop_exception_handling(self):
        """Test _connection_loop exception handling."""
        connection = ControllerConnection(self.test_params)
        connection.is_connected = True

        with patch.object(connection, '_strobe_plc', side_effect=Exception("Test error")):
            connection._connection_loop()

        self.assertFalse(connection.is_connected)

    @patch('pyrox.models.plc.connection.PLC')
    def test_connection_loop_success(self, mock_plc_class):
        """Test successful _connection_loop execution."""
        mock_plc_instance = Mock()
        mock_plc_class.return_value.__enter__.return_value = mock_plc_instance
        mock_plc_instance.GetPLCTime.return_value = True

        connection = ControllerConnection(self.test_params)
        connection.is_connected = True

        with patch.object(connection, '_strobe_plc', return_value=True):
            with patch.object(connection, '_tick') as mock_tick:
                with patch.object(connection, '_run_commands') as mock_commands:
                    with patch.object(connection, '_schedule') as mock_schedule:
                        connection._connection_loop()

        self.assertTrue(connection.is_connected)
        mock_tick.assert_called_once()
        mock_commands.assert_called_once()
        mock_schedule.assert_called_once()

    def test_multiple_subscribers_management(self):
        """Test managing multiple subscribers."""
        connection = ControllerConnection(self.test_params)
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()

        # Subscribe multiple callbacks
        connection.subscribe_to_ticks(callback1)
        connection.subscribe_to_ticks(callback2)
        connection.subscribe_to_ticks(callback3)

        self.assertEqual(len(connection._subscribers), 3)

        # Unsubscribe one
        connection.unsubscribe_from_ticks(callback2)

        self.assertEqual(len(connection._subscribers), 2)
        self.assertIn(callback1, connection._subscribers)
        self.assertNotIn(callback2, connection._subscribers)
        self.assertIn(callback3, connection._subscribers)

        # Test tick calls remaining subscribers
        connection._tick()

        callback1.assert_called_once()
        callback2.assert_not_called()
        callback3.assert_called_once()

    def test_timer_service_integration(self):
        """Test integration with TimerService."""
        connection = ControllerConnection(self.test_params)

        self.assertIsInstance(connection._timer_service, TimerService)

        # Test that timer service can be used
        callback = Mock()
        task_id = connection._timer_service.schedule_task(callback, 0.1)

        self.assertIsInstance(task_id, str)

        # Clean up
        connection._timer_service.shutdown()


if __name__ == '__main__':
    unittest.main()

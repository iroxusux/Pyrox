"""Unit tests for logging.py module."""

import io
import logging
import sys
import unittest
from unittest.mock import patch

from pyrox.services.logging import (
    LoggingManager,
    StreamCapture,
    log
)


class TestConstants(unittest.TestCase):
    """Test module constants."""

    def test_default_formatter(self):
        """Test default formatter string."""
        from pyrox.services.env import get_default_formatter
        expected = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
        self.assertEqual(get_default_formatter(), expected)

    def test_default_date_format(self):
        """Test default date format string."""
        from pyrox.services.env import get_default_date_format
        expected = "%Y-%m-%d %H:%M:%S"
        self.assertEqual(get_default_date_format(), expected)

    def test_formatter_contains_required_fields(self):
        """Test that formatter contains all required logging fields."""
        from pyrox.services.env import get_default_formatter
        required_fields = ['%(asctime)s', '%(name)s', '%(levelname)s', '%(message)s']

        for field in required_fields:
            with self.subTest(field=field):
                self.assertIn(field, get_default_formatter())


class TestStreamCapture(unittest.TestCase):
    """Test cases for StreamCapture class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_stream = io.StringIO()
        self.callback_called = False
        self.callback_data = None

    def test_init_without_original_stream(self):
        """Test StreamCapture initialization without original stream."""
        capture = StreamCapture()

        self.assertIsNone(capture.original_stream)
        self.assertEqual(capture._lines, [])
        self.assertEqual(capture._callbacks, [])

    def test_init_with_original_stream(self):
        """Test StreamCapture initialization with original stream."""
        capture = StreamCapture(self.mock_stream)

        self.assertEqual(capture.original_stream, self.mock_stream)
        self.assertEqual(capture._lines, [])
        self.assertEqual(capture._callbacks, [])

    def test_write_to_capture_only(self):
        """Test writing to capture without original stream."""
        capture = StreamCapture()

        result = capture.write("test message")

        self.assertEqual(result, 12)  # Length of "test message"
        self.assertEqual(capture.getvalue(), "test message")

    def test_write_to_capture_and_original(self):
        """Test writing to both capture and original stream."""
        capture = StreamCapture(self.mock_stream)

        result = capture.write("test message")

        self.assertEqual(result, 12)
        self.assertEqual(capture.getvalue(), "test message")
        self.assertEqual(self.mock_stream.getvalue(), "test message")

    def test_write_with_newlines_stores_lines(self):
        """Test that writing with newlines stores lines correctly."""
        capture = StreamCapture()

        capture.write("line1\nline2\nline3")

        lines = capture.get_lines()
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], "line1\n")
        self.assertEqual(lines[1], "line2\n")
        self.assertEqual(lines[2], "line3")

    def test_write_calls_callbacks(self):
        """Test that writing calls registered callbacks."""
        capture = StreamCapture()

        def test_callback(data, **kwargs):
            self.callback_called = True
            self.callback_data = data

        capture.register_callback(test_callback)
        capture.write("test data")

        self.assertTrue(self.callback_called)
        self.assertEqual(self.callback_data, "test data")

    def test_write_ignores_callback_errors(self):
        """Test that callback errors don't break write operations."""
        capture = StreamCapture()

        def failing_callback(data):
            raise Exception("Callback error")

        capture.register_callback(failing_callback)

        # Should not raise an exception
        result = capture.write("test")
        self.assertEqual(result, 4)
        self.assertEqual(capture.getvalue(), "test")

    def test_flush_with_original_stream(self):
        """Test flushing with original stream."""
        capture = StreamCapture(self.mock_stream)

        capture.write("test")
        capture.flush()

        # Should not raise any exceptions
        self.assertEqual(capture.getvalue(), "test")

    def test_flush_handles_closed_stream(self):
        """Test flush handles closed original stream gracefully."""
        mock_stream = io.StringIO()
        mock_stream.close()

        capture = StreamCapture(mock_stream)

        # Should not raise an exception
        capture.flush()

    def test_get_lines(self):
        """Test getting captured lines."""
        capture = StreamCapture()

        capture.write("line1\n")
        capture.write("line2\n")

        lines = capture.get_lines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "line1\n")
        self.assertEqual(lines[1], "line2\n")

    def test_clear_lines(self):
        """Test clearing captured lines."""
        capture = StreamCapture()

        capture.write("line1\nline2\n")
        self.assertEqual(len(capture.get_lines()), 2)

        capture.clear_lines()
        self.assertEqual(len(capture.get_lines()), 0)

    def test_readable(self):
        """Test readable property."""
        capture = StreamCapture()
        self.assertTrue(capture.readable())

    def test_seekable(self):
        """Test seekable property."""
        capture = StreamCapture()
        self.assertTrue(capture.seekable())

    def test_register_callback_with_callable(self):
        """Test registering a valid callback."""
        capture = StreamCapture()

        def valid_callback(data):
            pass

        capture.register_callback(valid_callback)
        self.assertIn(valid_callback, capture._callbacks)

    def test_register_callback_ignores_non_callable(self):
        """Test that non-callable objects are ignored."""
        capture = StreamCapture()
        original_count = len(capture._callbacks)

        capture.register_callback("not callable")

        self.assertEqual(len(capture._callbacks), original_count)

    def test_yield_lines(self):
        """Test yielding lines one by one."""
        capture = StreamCapture()

        capture.write("line1\nline2\nline3\n")

        lines = list(capture.yield_lines())
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], "line1\n")
        self.assertEqual(lines[1], "line2\n")
        self.assertEqual(lines[2], "line3\n")


class TestLoggingManager(unittest.TestCase):
    """Test cases for LoggingManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Store original state
        self.original_loggers = LoggingManager._curr_loggers.copy()
        self.original_level = LoggingManager.curr_logging_level

        # Clear loggers for clean tests
        LoggingManager._curr_loggers.clear()

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original state
        LoggingManager._curr_loggers = self.original_loggers
        LoggingManager.curr_logging_level = self.original_level

        # Restore streams to avoid affecting other tests
        LoggingManager.restore_system_streams()

    def test_capture_system_streams(self):
        """Test capturing system streams."""
        # Store original streams
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        try:
            stdout_capture, stderr_capture = LoggingManager.capture_system_streams()

            self.assertIsInstance(stdout_capture, StreamCapture)
            self.assertIsInstance(stderr_capture, StreamCapture)
            self.assertTrue(LoggingManager._streams_captured)

            # Verify that returned captures match the stored ones
            self.assertEqual(stdout_capture, LoggingManager._captured_stdout)
            self.assertEqual(stderr_capture, LoggingManager._captured_stderr)

            # Verify original streams are stored
            self.assertEqual(LoggingManager._original_stdout, original_stdout)
            self.assertEqual(LoggingManager._original_stderr, original_stderr)
        finally:
            LoggingManager.restore_system_streams()

    def test_capture_system_streams_idempotent(self):
        """Test that capturing streams twice returns same instances."""
        try:
            stdout1, stderr1 = LoggingManager.capture_system_streams()
            stdout2, stderr2 = LoggingManager.capture_system_streams()

            self.assertEqual(stdout1, stdout2)
            self.assertEqual(stderr1, stderr2)
        finally:
            LoggingManager.restore_system_streams()

    def test_restore_system_streams(self):
        """Test restoring original system streams."""
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        # Capture streams first
        LoggingManager.capture_system_streams()
        self.assertTrue(LoggingManager._streams_captured)

        # Restore streams
        LoggingManager.restore_system_streams()

        self.assertFalse(LoggingManager._streams_captured)
        self.assertEqual(sys.stdout, original_stdout)
        self.assertEqual(sys.stderr, original_stderr)

    def test_restore_system_streams_when_not_captured(self):
        """Test restoring streams when they weren't captured."""
        # Should not raise an exception
        LoggingManager.restore_system_streams()
        self.assertFalse(LoggingManager._streams_captured)

    def test_get_captured_stdout(self):
        """Test getting captured stdout stream."""
        try:
            LoggingManager.capture_system_streams()

            stdout_capture = LoggingManager.get_captured_stdout()

            self.assertIsInstance(stdout_capture, StreamCapture)
            self.assertEqual(stdout_capture, sys.stdout)
        finally:
            LoggingManager.restore_system_streams()

    def test_get_captured_stderr(self):
        """Test getting captured stderr stream."""
        try:
            LoggingManager.capture_system_streams()

            stderr_capture = LoggingManager.get_captured_stderr()

            self.assertIsInstance(stderr_capture, StreamCapture)
            self.assertEqual(stderr_capture, sys.stderr)
        finally:
            LoggingManager.restore_system_streams()

    def test_get_captured_streams(self):
        """Test getting both captured streams."""
        try:
            LoggingManager.capture_system_streams()

            streams = LoggingManager.get_captured_streams()

            self.assertEqual(len(streams), 2)
            self.assertIsInstance(streams[0], StreamCapture)  # stdout
            self.assertIsInstance(streams[1], StreamCapture)  # stderr
        finally:
            LoggingManager.restore_system_streams()

    def test_register_callback_to_captured_streams(self):
        """Test registering callback to captured streams."""
        callback_called = False
        callback_data = None

        def test_callback(data):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = data

        try:
            LoggingManager.capture_system_streams()
            LoggingManager.register_callback_to_captured_streams(test_callback)

            sys.stdout.write("test message")

            self.assertTrue(callback_called)
            self.assertEqual(callback_data, "test message")
        finally:
            LoggingManager.restore_system_streams()

    def test_register_callback_when_streams_not_captured(self):
        """Test registering callback when streams aren't captured."""
        def test_callback(data):
            pass

        # Should not raise an exception
        LoggingManager.register_callback_to_captured_streams(test_callback)

    def test_initial_class_attributes(self):
        """Test initial class attributes."""
        self.assertIsNotNone(LoggingManager.curr_logging_level)
        self.assertIsInstance(LoggingManager._curr_loggers, dict)

    def test_create_logger_basic(self):
        """Test creating a basic logger."""
        logger_name = "test_logger"

        logger = LoggingManager._create_logger(logger_name)

        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, logger_name)
        self.assertIn(logger_name, LoggingManager._curr_loggers)
        self.assertEqual(LoggingManager._curr_loggers[logger_name], logger)

    def test_create_logger_default_name(self):
        """Test creating logger with default name."""
        logger = LoggingManager._create_logger()

        self.assertIsInstance(logger, logging.Logger)
        self.assertIn(logger.name, LoggingManager._curr_loggers)

    def test_create_logger_configuration(self):
        """Test that created logger has correct configuration."""
        logger_name = "config_test"

        logger = LoggingManager._create_logger(logger_name)

        self.assertEqual(logger.level, LoggingManager.curr_logging_level)
        self.assertFalse(logger.propagate)
        self.assertEqual(len(logger.handlers), 1)

        handler = logger.handlers[0]
        self.assertIsInstance(handler, logging.StreamHandler)

        # Test that handler uses captured stderr if streams are captured
        if isinstance(handler, logging.StreamHandler):
            if LoggingManager._streams_captured:
                self.assertEqual(handler.stream, LoggingManager._captured_stderr)
            else:
                # In test environment, stderr might be wrapped/redirected
                self.assertIsNotNone(handler.stream)

    def test_create_logger_none_name(self):
        """Test creating logger with None as name."""
        logger = LoggingManager._create_logger(None)  # type: ignore

        self.assertIsInstance(logger, logging.Logger)
        self.assertIn(logger.name, LoggingManager._curr_loggers)

    def test_get_or_create_logger_new_logger(self):
        """Test getting or creating a new logger."""
        logger_name = "new_logger"

        logger = LoggingManager._get_or_create_logger(logger_name)

        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, logger_name)
        self.assertIn(logger_name, LoggingManager._curr_loggers)

    def test_get_or_create_logger_existing_logger(self):
        """Test getting existing logger."""
        logger_name = "existing_logger"

        # Create logger first time
        logger1 = LoggingManager._get_or_create_logger(logger_name)

        # Get same logger second time
        logger2 = LoggingManager._get_or_create_logger(logger_name)

        self.assertIs(logger1, logger2)
        self.assertEqual(len(LoggingManager._curr_loggers), 1)

    def test_get_or_create_logger_public_method(self):
        """Test public get_or_create_logger method."""
        logger_name = "public_test"

        logger = LoggingManager.get_or_create_logger(logger_name)

        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, logger_name)

    def test_get_standard_handler_default_stream(self):
        """Test getting standard handler with default stream."""
        handler = LoggingManager._get_standard_handler(sys.stderr)

        self.assertIsInstance(handler, logging.StreamHandler)
        if isinstance(handler, logging.StreamHandler):
            self.assertEqual(handler.stream, sys.stderr)
        self.assertEqual(handler.level, LoggingManager.curr_logging_level)

        from pyrox.services.env import get_default_formatter, get_default_date_format

        # Test formatter
        formatter = handler.formatter
        self.assertIsInstance(formatter, logging.Formatter)
        self.assertEqual(formatter._fmt, get_default_formatter())  # type: ignore
        self.assertEqual(formatter.datefmt, get_default_date_format())  # type: ignore

    def test_get_standard_handler_custom_stream(self):
        """Test getting standard handler with custom stream."""
        custom_stream = io.StringIO()

        handler = LoggingManager._get_standard_handler(custom_stream)

        if isinstance(handler, logging.StreamHandler):
            self.assertEqual(handler.stream, custom_stream)

    def test_setup_standard_logger(self):
        """Test setting up standard logger."""
        logger_name = "standard_test"

        logger = LoggingManager._setup_standard_logger(logger_name)

        self.assertEqual(logger.name, logger_name)
        self.assertEqual(logger.level, LoggingManager.curr_logging_level)
        self.assertFalse(logger.propagate)
        self.assertEqual(len(logger.handlers), 1)

        handler = logger.handlers[0]
        self.assertIsInstance(handler, logging.StreamHandler)

    def test_setup_standard_logger_removes_existing_handlers(self):
        """Test that setup removes existing handlers."""
        logger_name = "handler_test"

        # Get logger and add custom handler
        logger = logging.getLogger(logger_name)
        custom_handler = logging.StreamHandler()
        logger.addHandler(custom_handler)

        initial_handler_count = len(logger.handlers)
        self.assertGreater(initial_handler_count, 0)

        # Setup standard logger
        result_logger = LoggingManager._setup_standard_logger(logger_name)

        # Should be same logger but with only one handler
        self.assertIs(result_logger, logger)
        self.assertEqual(len(logger.handlers), 1)
        self.assertNotIn(custom_handler, logger.handlers)

    def test_remove_all_handlers(self):
        """Test removing all handlers from logger."""
        logger = logging.getLogger("handler_removal_test")

        # Add multiple handlers
        handler1 = logging.StreamHandler()
        handler2 = logging.StreamHandler()
        handler3 = logging.StreamHandler()

        logger.addHandler(handler1)
        logger.addHandler(handler2)
        logger.addHandler(handler3)

        self.assertEqual(len(logger.handlers), 3)

        # Remove all handlers
        LoggingManager._remove_all_handlers(logger)

        self.assertEqual(len(logger.handlers), 0)

    def test_remove_all_handlers_empty_logger(self):
        """Test removing handlers from logger with no handlers."""
        logger = logging.getLogger("empty_handler_test")

        # Ensure no handlers initially
        logger.handlers.clear()
        self.assertEqual(len(logger.handlers), 0)

        # Should not raise error
        LoggingManager._remove_all_handlers(logger)

        self.assertEqual(len(logger.handlers), 0)

    def test_set_logging_level_updates_class_variable(self):
        """Test setting logging level updates class variable."""
        original_level = LoggingManager.curr_logging_level
        new_level = logging.WARNING

        try:
            LoggingManager.set_logging_level(new_level)

            self.assertEqual(LoggingManager.curr_logging_level, new_level)
        finally:
            LoggingManager.curr_logging_level = original_level

    def test_set_logging_level_updates_existing_loggers(self):
        """Test setting logging level updates all existing loggers."""
        # Create some loggers
        logger1 = LoggingManager._create_logger("level_test_1")
        logger2 = LoggingManager._create_logger("level_test_2")

        original_level = LoggingManager.curr_logging_level
        new_level = logging.ERROR

        try:
            LoggingManager.set_logging_level(new_level)

            # Check loggers were updated
            self.assertEqual(logger1.level, new_level)
            self.assertEqual(logger2.level, new_level)

            # Check handlers were updated
            for handler in logger1.handlers:
                self.assertEqual(handler.level, new_level)
            for handler in logger2.handlers:
                self.assertEqual(handler.level, new_level)
        finally:
            LoggingManager.curr_logging_level = original_level

    def test_set_logging_level_default_parameter(self):
        """Test setting logging level with default parameter."""
        original_level = LoggingManager.curr_logging_level

        try:
            LoggingManager.set_logging_level()  # Default is INFO

            self.assertEqual(LoggingManager.curr_logging_level, logging.INFO)
        finally:
            LoggingManager.curr_logging_level = original_level

    def test_debug_loggers_output(self):
        """Test debug_loggers method output."""
        # Create a test logger
        LoggingManager._create_logger("debug_test")

        with patch('builtins.print') as mock_print:
            LoggingManager.debug_loggers()

            mock_print.assert_called()

            # Check that debug information was printed
            print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
            debug_output = '\n'.join(print_calls)

            self.assertIn("=== Current Loggers ===", debug_output)
            self.assertIn("debug_test", debug_output)
            self.assertIn("Level:", debug_output)
            self.assertIn("Propagate:", debug_output)
            self.assertIn("Handlers:", debug_output)

    def test_debug_loggers_empty(self):
        """Test debug_loggers with no loggers."""
        # Ensure no loggers
        LoggingManager._curr_loggers.clear()

        with patch('builtins.print') as mock_print:
            LoggingManager.debug_loggers()

            mock_print.assert_called_once_with("=== Current Loggers ===")

    def test_force_all_loggers_to_stderr(self):
        """Test forcing all loggers to stderr."""
        # Create some test loggers with custom handlers
        logger1_name = "stderr_test_1"
        logger2_name = "stderr_test_2"

        LoggingManager._create_logger(logger1_name)
        LoggingManager._create_logger(logger2_name)

        # Add a custom logger to the global logger dict
        custom_logger = logging.getLogger("custom_global")
        custom_handler = logging.StreamHandler(io.StringIO())
        custom_logger.addHandler(custom_handler)

        with patch.object(LoggingManager, '_setup_standard_logger') as mock_setup:
            LoggingManager.force_all_loggers_to_captured_stderr()

            # Should be called for root logger + each logger in manager dict
            # + each existing logger in the global logger dict
            self.assertGreater(mock_setup.call_count, 2)

    def test_multiple_loggers_independence(self):
        """Test that multiple loggers operate independently."""
        logger1 = LoggingManager._create_logger("independent_1")
        logger2 = LoggingManager._create_logger("independent_2")

        # They should be different instances
        self.assertIsNot(logger1, logger2)
        self.assertNotEqual(logger1.name, logger2.name)

        # But have similar configuration
        self.assertEqual(logger1.level, logger2.level)
        self.assertEqual(logger1.propagate, logger2.propagate)

    def test_logger_functionality_integration(self):
        """Test that created loggers actually work for logging."""
        prev_logging_level = LoggingManager.curr_logging_level
        LoggingManager.set_logging_level(logging.INFO)

        logger = LoggingManager._create_logger("functional_test")

        # Create a StringIO to capture output
        fake_stderr = io.StringIO()

        # Get the logger's handler and temporarily replace its stream
        handler = logger.handlers[0]
        if isinstance(handler, logging.StreamHandler):
            original_stream = handler.stream

            try:
                # Replace the handler's stream with our StringIO
                handler.stream = fake_stderr

                logger.info("Test message")

                output = fake_stderr.getvalue()
                self.assertIn("Test message", output)
                self.assertIn("functional_test", output)
                self.assertIn("INFO", output)

            finally:
                # Restore the original stream
                handler.stream = original_stream
        else:
            self.fail("Handler is not a StreamHandler")

        # Restore original logging level
        LoggingManager.curr_logging_level = prev_logging_level

    def test_concurrent_logger_creation(self):
        """Test creating multiple loggers with same name."""
        logger1 = LoggingManager._get_or_create_logger("concurrent_test")
        logger2 = LoggingManager._get_or_create_logger("concurrent_test")

        # Should return same instance
        self.assertIs(logger1, logger2)

        # Should only be one entry in the manager
        concurrent_loggers = [name for name in LoggingManager._curr_loggers.keys()
                              if name == "concurrent_test"]
        self.assertEqual(len(concurrent_loggers), 1)

    def test_initialize_logging_level_from_env(self):
        """Test initializing logging level from environment variable."""
        with patch('pyrox.services.env.EnvManager.get') as mock_get:
            # Test with string level
            mock_get.return_value = 'WARNING'
            LoggingManager.initialize_logging_level_from_env()
            self.assertEqual(LoggingManager.curr_logging_level, logging.WARNING)

            # Test with invalid level
            mock_get.return_value = 'INVALID_LEVEL'
            LoggingManager.initialize_logging_level_from_env()
            self.assertEqual(LoggingManager.curr_logging_level, logging.DEBUG)

            # Test with numeric level
            mock_get.return_value = '30'  # Equivalent to WARNING
            LoggingManager.initialize_logging_level_from_env()
            self.assertEqual(LoggingManager.curr_logging_level, logging.WARNING)


class TestIntegration(unittest.TestCase):
    """Integration tests for logging module components."""

    def setUp(self):
        """Set up test fixtures."""
        # Store original state
        self.original_loggers = LoggingManager._curr_loggers.copy()
        self.original_level = LoggingManager.curr_logging_level

        # Clear for clean tests
        LoggingManager._curr_loggers.clear()

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original state
        LoggingManager._curr_loggers = self.original_loggers
        LoggingManager.curr_logging_level = self.original_level

    def test_loggable_with_logging_manager_integration(self):
        """Test Loggable integration with LoggingManager."""

        integrated_logger = LoggingManager.get_or_create_logger("IntegratedLoggable")

        # Logger should be managed by LoggingManager
        self.assertIn('IntegratedLoggable', LoggingManager._curr_loggers)

        # Setting logging level should affect Loggable logger
        original_level = LoggingManager.curr_logging_level
        try:
            LoggingManager.set_logging_level(logging.WARNING)

            self.assertEqual(integrated_logger.level, logging.WARNING)
        finally:
            LoggingManager.curr_logging_level = original_level

    def test_multiple_loggable_classes_level_management(self):
        """Test managing logging levels across multiple Loggable classes."""
        first_logger = LoggingManager.get_or_create_logger("FirstLoggable")
        second_logger = LoggingManager.get_or_create_logger("SecondLoggable")

        original_level = LoggingManager.curr_logging_level
        try:
            # Change logging level
            LoggingManager.set_logging_level(logging.ERROR)

            # All loggers should be updated
            self.assertEqual(first_logger.level, logging.ERROR)
            self.assertEqual(second_logger.level, logging.ERROR)
        finally:
            LoggingManager.curr_logging_level = original_level

    def test_real_world_logging_scenario(self):
        """Test realistic logging scenario."""
        original_level = LoggingManager.curr_logging_level
        LoggingManager.set_logging_level(logging.DEBUG)

        class ApplicationComponent:
            def __init__(self, name):
                self.name = name

            def start(self):
                log(self.name).info(f"{self.name} component starting")
                return True

            def process(self, data):
                log(self.name).debug(f"{self.name} processing: {data}")
                if not data:
                    log(self.name).warning(f"{self.name} received empty data")
                    return False
                return True

            def stop(self):
                log(self.name).info(f"{self.name} component stopping")

        component = ApplicationComponent("TestComponent")

        component.start()
        component.process("test_data")
        component.process("")  # Empty data to trigger warning
        component.stop()

        output = ' '.join(LoggingManager.get_stderr_lines())

        # Check all expected log messages
        self.assertIn("TestComponent component starting", output)
        self.assertIn("TestComponent processing: test_data", output)
        self.assertIn("TestComponent received empty data", output)
        self.assertIn("TestComponent component stopping", output)

        # Check log levels
        self.assertIn("INFO", output)
        self.assertIn("DEBUG", output)
        self.assertIn("WARNING", output)

        # Restore original logging level
        LoggingManager.curr_logging_level = original_level

    def test_logger_configuration_persistence(self):
        """Test that logger configurations persist across operations."""
        pers_logger = LoggingManager.get_or_create_logger("PersistentLoggable")

        original_propagate = pers_logger.propagate
        original_handler_count = len(pers_logger.handlers)

        # Change logging level through manager
        LoggingManager.set_logging_level(logging.CRITICAL)

        # Verify changes persisted
        self.assertEqual(pers_logger.level, logging.CRITICAL)
        self.assertEqual(pers_logger.propagate, original_propagate)
        self.assertEqual(len(pers_logger.handlers), original_handler_count)

    def test_error_handling_in_logging(self):
        """Test error handling in logging operations."""
        original_level = LoggingManager.curr_logging_level
        LoggingManager.set_logging_level(logging.ERROR)

        class ErrorLoggable:
            def risky_operation(self):
                try:
                    raise ValueError("Simulated error")
                except Exception as e:
                    log(self).error(f"Error in risky_operation: {e}")
                    return False
                return True

        error_obj = ErrorLoggable()

        result = error_obj.risky_operation()

        self.assertFalse(result)
        output = ' '.join(LoggingManager.get_stderr_lines())
        self.assertIn("Error in risky_operation: Simulated error", output)
        self.assertIn("ERROR", output)
        # Restore original logging level
        LoggingManager.curr_logging_level = original_level

    def test_concurrent_logging_safety(self):
        """Test logging safety with multiple classes and instances."""
        original_level = LoggingManager.curr_logging_level
        LoggingManager.set_logging_level(logging.INFO)

        class ConcurrentLoggable:
            def __init__(self, instance_id):
                self.instance_id = instance_id

            def log_message(self):
                log(self).info(f"Message from instance {self.instance_id}")

        # Create multiple instances
        instances = [ConcurrentLoggable(i) for i in range(5)]

        for instance in instances:
            instance.log_message()

        output = ' '.join(LoggingManager.get_stderr_lines())

        # All instances should use same logger (class-level)
        for i in range(5):
            self.assertIn(f"Message from instance {i}", output)

        # But all should have same logger name
        self.assertIn("ConcurrentLoggable", output)
        # Restore original logging level
        LoggingManager.curr_logging_level = original_level

    def test_formatter_consistency(self):
        """Test that all loggers use consistent formatting."""
        formatted_logger = LoggingManager.get_or_create_logger("FormattedLoggable")

        # Manually create another logger through manager
        manual_logger = LoggingManager.get_or_create_logger("manual_test")

        # Both should have handlers with same formatter format
        formatted_handler = formatted_logger.handlers[0]
        manual_handler = manual_logger.handlers[0]

        from pyrox.services.env import get_default_formatter, get_default_date_format

        self.assertEqual(formatted_handler.formatter._fmt, get_default_formatter())  # type: ignore
        self.assertEqual(manual_handler.formatter._fmt, get_default_formatter())  # type: ignore
        self.assertEqual(formatted_handler.formatter.datefmt, get_default_date_format())  # type: ignore
        self.assertEqual(manual_handler.formatter.datefmt, get_default_date_format())  # type: ignore

    def test_complex_inheritance_with_logging(self):
        """Test complex inheritance scenarios with logging."""
        class BaseService:
            def __init__(self):
                self.status = "initialized"
                log(self).info(f"{self.__class__.__name__} initialized")

        class WebService(BaseService):
            def start_server(self):
                log(self).info("Web server starting")
                self.status = "running"

        class DatabaseService(BaseService):
            def connect(self):
                log(self).info("Database connection established")
                self.status = "connected"

        web = WebService()
        db = DatabaseService()

        web.start_server()
        db.connect()

        output = ' '.join(LoggingManager.get_stderr_lines())

        # Should see different logger names
        self.assertIn("WebService", output)
        self.assertIn("DatabaseService", output)

        # Should see initialization and specific operations
        self.assertIn("Web server starting", output)
        self.assertIn("Database connection established", output)


class TestCustomLoggingLevels(unittest.TestCase):
    """Test custom logging levels if any are defined."""

    def test_custom_logging_levels_exist(self):
        """Test that custom logging levels are defined."""
        # Assuming custom levels are defined in LoggingManager
        from pyrox.services import logging as pyrox_logging
        pyrox_logging.LoggingManager.initialize_additional_logging_levels()
        from logging import getLevelNamesMapping
        logging_levels = getLevelNamesMapping()

        for level_value, level_name in pyrox_logging.CUSTOM_LOGGING_LEVELS:
            level_value = int(level_value)
            self.assertTrue(level_name in logging_levels)
            self.assertEqual(logging_levels.get(level_name), level_value)


if __name__ == '__main__':
    unittest.main(verbosity=2)

"""Unit tests for logging.py module."""

import io
import logging
import sys
import unittest
from unittest.mock import patch

from pyrox.services.logging import (
    LoggingManager,
    Loggable,
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

    def test_initial_class_attributes(self):
        """Test initial class attributes."""
        self.assertEqual(LoggingManager.curr_logging_level, logging.DEBUG)
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

        # Test that handler uses the appropriate stream
        expected_stream = (LoggingManager._captured_stderr
                           if LoggingManager._streams_captured
                           else sys.stderr)
        self.assertEqual(handler.stream, expected_stream)

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
        logger = LoggingManager._create_logger("functional_test")

        # Create a StringIO to capture output
        fake_stderr = io.StringIO()

        # Get the logger's handler and temporarily replace its stream
        handler = logger.handlers[0]
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


class TestLoggable(unittest.TestCase):
    """Test cases for Loggable class."""

    def setUp(self):
        """Set up test fixtures."""
        # Store original state
        self.original_loggers = LoggingManager._curr_loggers.copy()

        # Clear for clean tests
        LoggingManager._curr_loggers.clear()

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original state
        LoggingManager._curr_loggers = self.original_loggers

    def test_loggable_class_has_logger_attribute(self):
        """Test that Loggable class has logger attribute."""
        self.assertTrue(hasattr(Loggable, 'log'))
        self.assertIsInstance(Loggable.log(), logging.Logger)

    def test_loggable_logger_name(self):
        """Test that Loggable logger has correct name."""
        self.assertEqual(Loggable.log().__class__.__name__, 'Logger')

    def test_init_subclass_creates_logger(self):
        """Test that subclassing Loggable creates logger with class name."""
        class TestLoggableSubclass(Loggable):
            pass

        self.assertTrue(hasattr(TestLoggableSubclass, 'log'))
        self.assertIsInstance(TestLoggableSubclass.log(), logging.Logger)

    def test_multiple_subclasses_have_different_loggers(self):
        """Test that different subclasses have different loggers."""
        class FirstSubclass(Loggable):
            pass

        class SecondSubclass(Loggable):
            pass

        self.assertIsNot(FirstSubclass.log(), SecondSubclass.log())
        self.assertEqual(FirstSubclass.log().name, 'FirstSubclass')
        self.assertEqual(SecondSubclass.log().name, 'SecondSubclass')

    def test_nested_subclass_inheritance(self):
        """Test nested subclass inheritance."""
        class ParentLoggable(Loggable):
            pass

        class ChildLoggable(ParentLoggable):
            pass

        # Each should have its own logger
        self.assertIsNot(ParentLoggable.log(), ChildLoggable.log())
        self.assertEqual(ParentLoggable.log().name, 'ParentLoggable')
        self.assertEqual(ChildLoggable.log().name, 'ChildLoggable')

    def test_subclass_logger_functionality(self):
        """Test that subclass loggers actually work."""
        class FunctionalLoggable(Loggable):
            def log_test_message(self):
                self.log().info("Functional test message")

        obj = FunctionalLoggable()

        obj.log_test_message()

        output = ' '.join(LoggingManager.get_stderr_lines())
        self.assertIn("Functional test message", output)
        self.assertIn("FunctionalLoggable", output)

    def test_instance_access_to_class_logger(self):
        """Test that instances can access the class logger."""
        class InstanceLoggable(Loggable):
            pass

        obj = InstanceLoggable()

        # Instance should access same logger as class
        self.assertIs(obj.log(), InstanceLoggable.log())

    def test_loggable_subclass_customization(self):
        """Test Loggable subclass with custom attributes and methods."""
        class CustomizedLoggable(Loggable):
            custom_setting = "configured"

            def get_logger_info(self):
                return {
                    'name': self.log().name,
                    'level': self.log().level,
                    'custom_setting': self.custom_setting
                }

        obj = CustomizedLoggable()
        info = obj.get_logger_info()

        self.assertEqual(info['name'], 'CustomizedLoggable')
        self.assertEqual(info['custom_setting'], 'configured')
        self.assertEqual(obj.log().name, 'CustomizedLoggable')

    def test_loggable_mixin_behavior(self):
        """Test Loggable as a mixin with other classes."""
        class BaseClass:
            def __init__(self):
                self.base_attr = "base"

        class MixinLoggable(BaseClass, Loggable):
            def __init__(self):
                super().__init__()
                self.mixin_attr = "mixin"

        obj = MixinLoggable()

        self.assertEqual(obj.base_attr, "base")
        self.assertEqual(obj.mixin_attr, "mixin")
        self.assertIsInstance(obj.log(), logging.Logger)
        self.assertEqual(obj.log().name, 'MixinLoggable')

    def test_loggable_subclass_logger_registered(self):
        """Test that subclass loggers are registered in LoggingManager."""
        class RegisteredLoggable(Loggable):
            pass

        # Logger should be in the manager's dictionary
        self.assertIn('RegisteredLoggable', LoggingManager._curr_loggers)
        self.assertIs(LoggingManager._curr_loggers['RegisteredLoggable'],
                      RegisteredLoggable.log())

    def test_dynamic_subclass_creation(self):
        """Test dynamic subclass creation."""
        # Create subclass dynamically
        DynamicLoggable = type('DynamicLoggable', (Loggable,), {})

        self.assertTrue(hasattr(DynamicLoggable, 'log'))
        self.assertEqual(DynamicLoggable.log().name, 'DynamicLoggable')

    def test_loggable_inheritance_chain(self):
        """Test complex inheritance chain with Loggable."""
        class Level1(Loggable):
            pass

        class Level2(Level1):
            pass

        class Level3(Level2):
            pass

        # Each level should have its own logger
        self.assertEqual(Level1.log().name, 'Level1')
        self.assertEqual(Level2.log().name, 'Level2')
        self.assertEqual(Level3.log().name, 'Level3')

        # All should be different instances
        loggers = [Level1.log(), Level2.log(), Level3.log()]
        self.assertEqual(len(set(loggers)), 3)


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
        class IntegratedLoggable(Loggable):
            pass

        # Logger should be managed by LoggingManager
        self.assertIn('IntegratedLoggable', LoggingManager._curr_loggers)

        # Setting logging level should affect Loggable logger
        original_level = LoggingManager.curr_logging_level
        try:
            LoggingManager.set_logging_level(logging.WARNING)

            self.assertEqual(IntegratedLoggable.log().level, logging.WARNING)
        finally:
            LoggingManager.curr_logging_level = original_level

    def test_multiple_loggable_classes_level_management(self):
        """Test managing logging levels across multiple Loggable classes."""
        class FirstLoggable(Loggable):
            pass

        class SecondLoggable(Loggable):
            pass

        original_level = LoggingManager.curr_logging_level
        try:
            # Change logging level
            LoggingManager.set_logging_level(logging.ERROR)

            # All loggers should be updated
            self.assertEqual(FirstLoggable.log().level, logging.ERROR)
            self.assertEqual(SecondLoggable.log().level, logging.ERROR)
        finally:
            LoggingManager.curr_logging_level = original_level

    def test_real_world_logging_scenario(self):
        """Test realistic logging scenario."""
        class ApplicationComponent(Loggable):
            def __init__(self, name):
                self.name = name

            def start(self):
                self.log().info(f"{self.name} component starting")
                return True

            def process(self, data):
                self.log().debug(f"{self.name} processing: {data}")
                if not data:
                    self.log().warning(f"{self.name} received empty data")
                    return False
                return True

            def stop(self):
                self.log().info(f"{self.name} component stopping")

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

    def test_logger_configuration_persistence(self):
        """Test that logger configurations persist across operations."""
        class PersistentLoggable(Loggable):
            pass

        original_propagate = PersistentLoggable.log().propagate
        original_handler_count = len(PersistentLoggable.log().handlers)

        # Change logging level through manager
        LoggingManager.set_logging_level(logging.CRITICAL)

        # Verify changes persisted
        self.assertEqual(PersistentLoggable.log().level, logging.CRITICAL)
        self.assertEqual(PersistentLoggable.log().propagate, original_propagate)
        self.assertEqual(len(PersistentLoggable.log().handlers), original_handler_count)

    def test_error_handling_in_logging(self):
        """Test error handling in logging operations."""
        class ErrorLoggable(Loggable):
            def risky_operation(self):
                try:
                    raise ValueError("Simulated error")
                except Exception as e:
                    self.log().error(f"Error in risky_operation: {e}")
                    return False
                return True

        error_obj = ErrorLoggable()

        result = error_obj.risky_operation()

        self.assertFalse(result)
        output = ' '.join(LoggingManager.get_stderr_lines())
        self.assertIn("Error in risky_operation: Simulated error", output)
        self.assertIn("ERROR", output)

    def test_concurrent_logging_safety(self):
        """Test logging safety with multiple classes and instances."""
        class ConcurrentLoggable(Loggable):
            def __init__(self, instance_id):
                self.instance_id = instance_id

            def log_message(self):
                self.log().info(f"Message from instance {self.instance_id}")

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

    def test_formatter_consistency(self):
        """Test that all loggers use consistent formatting."""
        class FormattedLoggable(Loggable):
            pass

        # Manually create another logger through manager
        manual_logger = LoggingManager.get_or_create_logger("manual_test")

        # Both should have handlers with same formatter format
        formatted_handler = FormattedLoggable.log().handlers[0]
        manual_handler = manual_logger.handlers[0]

        from pyrox.services.env import get_default_formatter, get_default_date_format

        self.assertEqual(formatted_handler.formatter._fmt, get_default_formatter())  # type: ignore
        self.assertEqual(manual_handler.formatter._fmt, get_default_formatter())  # type: ignore
        self.assertEqual(formatted_handler.formatter.datefmt, get_default_date_format())  # type: ignore
        self.assertEqual(manual_handler.formatter.datefmt, get_default_date_format())  # type: ignore

    def test_complex_inheritance_with_logging(self):
        """Test complex inheritance scenarios with logging."""
        class BaseService(Loggable):
            def __init__(self):
                self.status = "initialized"
                self.log().info(f"{self.__class__.__name__} initialized")

        class WebService(BaseService):
            def start_server(self):
                self.log().info("Web server starting")
                self.status = "running"

        class DatabaseService(BaseService):
            def connect(self):
                self.log().info("Database connection established")
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

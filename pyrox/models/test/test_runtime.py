"""Unit tests for runtime.py module."""

import unittest
from unittest.mock import MagicMock

from pyrox.models.protocols import Buildable, Runnable
from pyrox.models.runtime import RuntimeDict


class TestBuildable(unittest.TestCase):
    """Test cases for Buildable class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        obj = Buildable()

        self.assertFalse(obj.built)

    def test_built_property_initial_state(self):
        """Test built property initial state."""
        obj = Buildable()

        self.assertFalse(obj.built)
        self.assertIsInstance(obj.built, bool)

    def test_build_method_sets_built_flag(self):
        """Test that build method sets built flag to True."""
        obj = Buildable()

        self.assertFalse(obj.built)

        obj.build()

        self.assertTrue(obj.built)

    def test_build_method_multiple_calls(self):
        """Test calling build method multiple times."""
        obj = Buildable()

        obj.build()
        self.assertTrue(obj.built)

        obj.build()  # Call again
        self.assertTrue(obj.built)  # Should still be True

    def test_refresh_method_no_op(self):
        """Test refresh method (should be no-op)."""
        obj = Buildable()

        # Should not raise any errors
        obj.refresh()

        # Built state should not change
        self.assertFalse(obj.built)

        obj.build()
        obj.refresh()

        # Built state should remain True
        self.assertTrue(obj.built)

    def test_refresh_method_can_be_overridden(self):
        """Test that refresh method can be overridden in subclasses."""
        class TestBuildable(Buildable):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.refresh_count = 0

            def refresh(self):
                self.refresh_count += 1

        obj = TestBuildable()

        obj.refresh()
        self.assertEqual(obj.refresh_count, 1)

        obj.refresh()
        self.assertEqual(obj.refresh_count, 2)

    def test_build_lifecycle(self):
        """Test complete build lifecycle."""
        obj = Buildable()

        # Initial state
        self.assertFalse(obj.built)

        # Build
        obj.build()
        self.assertTrue(obj.built)

        # Refresh (should not affect built state)
        obj.refresh()
        self.assertTrue(obj.built)

    def test_inheritance_compatibility(self):
        """Test inheritance from Buildable."""
        class CustomBuildable(Buildable):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.custom_property = "custom"

            def build(self):
                super().build()
                self.custom_property = "built"

        obj = CustomBuildable()

        self.assertEqual(obj.custom_property, "custom")
        self.assertFalse(obj.built)

        obj.build()

        self.assertEqual(obj.custom_property, "built")
        self.assertTrue(obj.built)


class TestRunnable(unittest.TestCase):
    """Test cases for Runnable class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        obj = Runnable()

        self.assertFalse(obj.running)

    def test_running_property_initial_state(self):
        """Test running property initial state."""
        obj = Runnable()

        self.assertFalse(obj.running)
        self.assertIsInstance(obj.running, bool)

    def test_run_method_multiple_calls(self):
        """Test calling start method multiple times."""
        obj = Runnable()

        obj.run()
        self.assertTrue(obj.running)

        obj.run()  # Call again
        self.assertTrue(obj.running)

    def test_stop_method(self):
        """Test stop method."""
        obj = Runnable()
        obj.run()

        self.assertTrue(obj.running)

        obj.stop()

        self.assertFalse(obj.running)

    def test_stop_method_when_not_running(self):
        """Test stop method when not running."""
        obj = Runnable()

        self.assertFalse(obj.running)

        obj.stop()  # Should not raise error

        self.assertFalse(obj.running)

    def test_stop_method_multiple_calls(self):
        """Test calling stop method multiple times."""
        obj = Runnable()
        obj.run()

        obj.stop()
        self.assertFalse(obj.running)

        obj.stop()  # Call again
        self.assertFalse(obj.running)

    def test_start_stop_cycle(self):
        """Test multiple start/stop cycles."""
        obj = Runnable()

        # First cycle
        obj.run()
        self.assertTrue(obj.running)

        obj.stop()
        self.assertFalse(obj.running)

        # Second cycle (should not rebuild)
        obj.run()
        self.assertTrue(obj.running)

        obj.stop()
        self.assertFalse(obj.running)

    def test_inheritance_and_overriding(self):
        """Test inheritance from Runnable with method overriding."""
        class CustomRunnable(Runnable):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.start_count = 0
                self.stop_count = 0
                self.build_count = 0

            def run(self, stop_code: int = 0):
                self.start_count += 1
                super().run()
                return 0

            def stop(self, stop_code: int = 0):
                self.stop_count += 1
                super().stop()

        obj = CustomRunnable()

        # Test start
        obj.run()
        self.assertEqual(obj.start_count, 1)
        self.assertTrue(obj.running)

        # Test stop
        obj.stop()
        self.assertEqual(obj.stop_count, 1)
        self.assertFalse(obj.running)

    def test_complete_lifecycle(self):
        """Test complete Runnable lifecycle."""
        obj = Runnable()

        # Initial state
        self.assertFalse(obj.running)

        # Start (auto-builds)
        obj.run()
        self.assertTrue(obj.running)

        # Stop
        obj.stop()
        self.assertFalse(obj.running)

        # Restart
        obj.run()
        self.assertTrue(obj.running)


class TestRuntimeDict(unittest.TestCase):
    """Test cases for RuntimeDict class."""

    def test_init_with_valid_callback(self):
        """Test initialization with valid callback."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        self.assertEqual(rd.callback, callback)
        self.assertEqual(rd.data, {})
        self.assertFalse(rd.inhibit_callback)

    def test_init_with_none_callback_raises_error(self):
        """Test initialization with None callback raises ValueError."""
        with self.assertRaises(ValueError) as context:
            RuntimeDict(None)  # type: ignore

        self.assertEqual(str(context.exception),
                         'A valid callback function must be provided to RuntimeDict.')

    def test_init_with_non_callable_raises_error(self):
        """Test initialization with non-callable raises TypeError."""
        with self.assertRaises(TypeError) as context:
            RuntimeDict("not callable")  # type: ignore

        self.assertEqual(str(context.exception), 'Callback must be a callable function.')

    def test_init_with_various_invalid_callbacks(self):
        """Test initialization with various invalid callbacks."""
        invalid_callbacks = [123, [], {}, "string", object()]

        for invalid_callback in invalid_callbacks:
            with self.subTest(callback=invalid_callback):
                with self.assertRaises(TypeError):
                    RuntimeDict(invalid_callback)

    def test_setitem_triggers_callback(self):
        """Test that setting item triggers callback."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        rd['key'] = 'value'

        callback.assert_called_once()
        self.assertEqual(rd['key'], 'value')

    def test_setitem_multiple_items(self):
        """Test setting multiple items."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        rd['key1'] = 'value1'
        rd['key2'] = 'value2'
        rd['key3'] = 'value3'

        self.assertEqual(callback.call_count, 3)
        self.assertEqual(rd['key1'], 'value1')
        self.assertEqual(rd['key2'], 'value2')
        self.assertEqual(rd['key3'], 'value3')

    def test_delitem_triggers_callback(self):
        """Test that deleting item triggers callback."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        rd['key'] = 'value'
        callback.reset_mock()

        del rd['key']

        callback.assert_called_once()
        self.assertIsNone(rd['key'])  # Should return None for missing keys

    def test_delitem_nonexistent_key_raises_keyerror(self):
        """Test deleting non-existent key raises KeyError."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        with self.assertRaises(KeyError):
            del rd['nonexistent']

    def test_getitem_existing_key(self):
        """Test getting existing key."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        rd['key'] = 'value'

        result = rd['key']
        self.assertEqual(result, 'value')

    def test_getitem_nonexistent_key_returns_none(self):
        """Test getting non-existent key returns None."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        result = rd['nonexistent']
        self.assertIsNone(result)

    def test_contains_method(self):
        """Test __contains__ method."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        rd['existing'] = 'value'

        self.assertIn('existing', rd)
        self.assertNotIn('nonexistent', rd)

    def test_callback_property_getter(self):
        """Test callback property getter."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        self.assertEqual(rd.callback, callback)

    def test_callback_property_setter_valid(self):
        """Test callback property setter with valid callback."""
        callback1 = MagicMock()
        callback2 = MagicMock()
        rd = RuntimeDict(callback1)

        rd.callback = callback2

        self.assertEqual(rd.callback, callback2)

    def test_callback_property_setter_none_raises_error(self):
        """Test callback property setter with None raises ValueError."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        with self.assertRaises(ValueError):
            rd.callback = None  # type: ignore

    def test_callback_property_setter_non_callable_raises_error(self):
        """Test callback property setter with non-callable raises ValueError."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        with self.assertRaises(ValueError):
            rd.callback = "not callable"  # type: ignore

    def test_data_property_getter(self):
        """Test data property getter."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        rd['key'] = 'value'

        data = rd.data
        self.assertEqual(data, {'key': 'value'})
        self.assertIsInstance(data, dict)

    def test_data_property_setter_valid(self):
        """Test data property setter with valid dictionary."""
        callback = MagicMock()
        rd = RuntimeDict(callback)
        new_data = {'new_key': 'new_value', 'another_key': 123}

        rd.data = new_data

        self.assertEqual(rd.data, new_data)
        callback.assert_called()  # Should trigger callback

    def test_data_property_setter_non_dict_raises_error(self):
        """Test data property setter with non-dict raises TypeError."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        invalid_data_types = ["string", 123, [], None]

        for invalid_data in invalid_data_types:
            with self.subTest(data_type=type(invalid_data).__name__):
                with self.assertRaises(TypeError) as context:
                    rd.data = invalid_data

                self.assertEqual(str(context.exception),
                                 'Runtime data must be a dictionary.')

    def test_inhibit_callback_property_getter(self):
        """Test inhibit_callback property getter."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        self.assertFalse(rd.inhibit_callback)

    def test_inhibit_callback_property_setter_valid(self):
        """Test inhibit_callback property setter with valid boolean."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        rd.inhibit_callback = True

        self.assertTrue(rd.inhibit_callback)
        callback.assert_not_called()  # Setting property should trigger callback

        rd.inhibit_callback = False

        self.assertFalse(rd.inhibit_callback)
        callback.assert_called_once()  # Setting property should trigger callback

    def test_inhibit_callback_property_setter_non_bool_raises_error(self):
        """Test inhibit_callback setter with non-boolean raises TypeError."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        invalid_types = ["string", 123, [], {}, None]

        for invalid_type in invalid_types:
            with self.subTest(type_name=type(invalid_type).__name__):
                with self.assertRaises(TypeError) as context:
                    rd.inhibit_callback = invalid_type

                self.assertEqual(str(context.exception),
                                 'Inhibit callback must be a boolean value.')

    def test_inhibit_method(self):
        """Test inhibit method."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        rd.inhibit()

        self.assertTrue(rd.inhibit_callback)

    def test_uninhibit_method(self):
        """Test uninhibit method."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        rd.inhibit()
        callback.reset_mock()

        rd.uninhibit()

        self.assertFalse(rd.inhibit_callback)
        callback.assert_called_once()  # Should trigger callback

    def test_callback_inhibition(self):
        """Test that inhibiting prevents callback execution."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        rd.inhibit()
        callback.reset_mock()

        rd['key'] = 'value'

        callback.assert_not_called()

    def test_callback_uninhibition_triggers_callback(self):
        """Test that uninhibiting triggers callback."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        rd.inhibit()
        rd['key'] = 'value'  # Should not trigger callback
        callback.reset_mock()

        rd.uninhibit()

        callback.assert_called_once()

    def test_clear_method(self):
        """Test clear method."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        rd['key1'] = 'value1'
        rd['key2'] = 'value2'
        callback.reset_mock()

        rd.clear()

        callback.assert_called_once()
        self.assertEqual(len(rd.data), 0)
        self.assertNotIn('key1', rd)
        self.assertNotIn('key2', rd)

    def test_get_method(self):
        """Test get method."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        rd['existing'] = 'value'

        # Test existing key
        result = rd.get('existing')
        self.assertEqual(result, 'value')

        # Test non-existent key with default None
        result = rd.get('nonexistent')
        self.assertIsNone(result)

        # Test non-existent key with custom default
        result = rd.get('nonexistent', 'default_value')
        self.assertEqual(result, 'default_value')

    def test_update_method(self):
        """Test update method."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        rd['existing'] = 'old_value'
        callback.reset_mock()

        update_data = {'existing': 'new_value', 'new_key': 'new_value'}
        rd.update(update_data)

        callback.assert_called_once()
        self.assertEqual(rd['existing'], 'new_value')
        self.assertEqual(rd['new_key'], 'new_value')

    def test_update_method_with_kwargs(self):
        """Test update method with keyword arguments."""
        callback = MagicMock()
        rd = RuntimeDict(callback)
        callback.reset_mock()

        rd.update(key1='value1', key2='value2')

        callback.assert_called_once()
        self.assertEqual(rd['key1'], 'value1')
        self.assertEqual(rd['key2'], 'value2')

    def test_update_method_mixed_args(self):
        """Test update method with both dict and kwargs."""
        callback = MagicMock()
        rd = RuntimeDict(callback)
        callback.reset_mock()

        rd.update({'dict_key': 'dict_value'}, kwarg_key='kwarg_value')

        callback.assert_called_once()
        self.assertEqual(rd['dict_key'], 'dict_value')
        self.assertEqual(rd['kwarg_key'], 'kwarg_value')

    def test_call_method_with_invalid_callback(self):
        """Test _call method when callback becomes invalid."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        # Make callback invalid
        rd._callback = "not callable"  # type: ignore

        with self.assertRaises(TypeError) as context:
            rd._call()

        self.assertEqual(str(context.exception), 'Callback must be a callable function.')

    def test_slots_attribute(self):
        """Test that __slots__ is properly defined."""
        self.assertTrue(hasattr(RuntimeDict, '__slots__'))
        self.assertEqual(RuntimeDict.__slots__, ('_callback', '_data', '_inhibit_callback'))

    def test_complex_data_operations(self):
        """Test complex operations with various data types."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        # Test various data types
        rd['string'] = 'text'
        rd['integer'] = 42
        rd['float'] = 3.14
        rd['list'] = [1, 2, 3]
        rd['dict'] = {'nested': 'value'}
        rd['boolean'] = True
        rd['none'] = None

        # Verify all data is stored correctly
        self.assertEqual(rd['string'], 'text')
        self.assertEqual(rd['integer'], 42)
        self.assertEqual(rd['float'], 3.14)
        self.assertEqual(rd['list'], [1, 2, 3])
        self.assertEqual(rd['dict'], {'nested': 'value'})
        self.assertEqual(rd['boolean'], True)
        self.assertIsNone(rd['none'])

        # Verify callback was called for each operation
        self.assertEqual(callback.call_count, 7)

    def test_callback_exception_handling(self):
        """Test behavior when callback raises exception."""
        def error_callback():
            raise ValueError("Callback error")

        rd = RuntimeDict(error_callback)

        # Should not prevent the operation, but callback error propagates
        with self.assertRaises(ValueError) as context:
            rd['key'] = 'value'

        self.assertEqual(str(context.exception), "Callback error")

        # Data should still be set
        self.assertEqual(rd['key'], 'value')

    def test_lifecycle_operations(self):
        """Test complete lifecycle of RuntimeDict operations."""
        callback_calls = []

        def tracking_callback():
            callback_calls.append("called")

        rd = RuntimeDict(tracking_callback)

        # Add items
        rd['item1'] = 'value1'
        rd['item2'] = 'value2'

        # Update items
        rd.update({'item3': 'value3'})

        # Delete item
        del rd['item1']

        # Clear all
        rd.clear()

        # Verify callback was called for each operation
        self.assertEqual(len(callback_calls), 5)

        # Verify final state
        self.assertEqual(len(rd.data), 0)

    def test_inhibition_workflow(self):
        """Test complete inhibition workflow."""
        callback = MagicMock()
        rd = RuntimeDict(callback)

        # Normal operation
        rd['key1'] = 'value1'
        self.assertEqual(callback.call_count, 1)

        # Inhibit callbacks
        rd.inhibit()
        callback.reset_mock()

        # Operations during inhibition
        rd['key2'] = 'value2'
        rd['key3'] = 'value3'
        del rd['key1']

        # No callbacks should have been triggered
        callback.assert_not_called()

        # Uninhibit - should trigger callback
        rd.uninhibit()
        callback.assert_called_once()

        # Normal operation resumes
        rd['key4'] = 'value4'
        self.assertEqual(callback.call_count, 2)


class TestIntegration(unittest.TestCase):
    """Integration tests for runtime classes."""

    def test_runtime_dict_with_buildable_integration(self):
        """Test RuntimeDict used with Buildable objects."""
        class ConfigurableBuildable(Buildable):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.config = RuntimeDict(self._on_config_change)
                self.config_change_count = 0

            def _on_config_change(self):
                self.config_change_count += 1
                if self.built and 'auto_refresh' in self.config and self.config['auto_refresh']:
                    self.refresh()

        obj = ConfigurableBuildable()

        # Set initial config
        obj.config['setting1'] = 'value1'
        obj.config['auto_refresh'] = True

        self.assertEqual(obj.config_change_count, 2)

        # Build object
        obj.build()

        # Change config after building (should trigger refresh)
        obj.config['setting2'] = 'value2'

        self.assertEqual(obj.config_change_count, 3)

    def test_runtime_dict_with_runnable_integration(self):
        """Test RuntimeDict used with Runnable objects."""
        class ConfigurableRunnable(Runnable):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.settings = RuntimeDict(self._on_settings_change)
                self.auto_restarts = 0

            def _on_settings_change(self):
                # Auto-restart if running and restart_on_change is enabled
                if (self.running and
                    'restart_on_change' in self.settings and
                        self.settings['restart_on_change']):
                    self.stop()
                    self.run()
                    self.auto_restarts += 1

        obj = ConfigurableRunnable()

        # Configure for auto-restart
        obj.settings['restart_on_change'] = True

        # Start the object
        obj.run()
        self.assertTrue(obj.running)
        self.assertEqual(obj.auto_restarts, 0)

        # Change settings (should trigger restart)
        obj.settings['new_setting'] = 'new_value'

        self.assertTrue(obj.running)
        self.assertEqual(obj.auto_restarts, 1)

    def test_complex_inheritance_scenario(self):
        """Test complex inheritance scenario with all classes."""
        class ComplexObject(Runnable):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.runtime_data = RuntimeDict(self._on_data_change)
                self.status_log = []

            def _on_data_change(self):
                self.status_log.append(f"Data changed while running: {self.running}")

            def run(self, stop_code: int = 0) -> int:
                super().run()
                self.status_log.append("Object started")
                return 0

            def stop(self, stop_code: int = 0):
                super().stop()
                self.status_log.append("Object stopped")

            def refresh(self):
                self.status_log.append("Object refreshed")

        obj = ComplexObject()

        # Test complete lifecycle
        obj.runtime_data['config'] = 'initial'  # Data change while not running
        obj.run()  # Should build and start
        obj.runtime_data['config'] = 'updated'  # Data change while running
        obj.refresh()
        obj.stop()

        expected_log = [
            "Data changed while running: False",  # Initial data change
            "Object started",                     # Start
            "Data changed while running: True",   # Data change while running
            "Object refreshed",                   # Manual refresh
            "Object stopped"                      # Stop
        ]

        self.assertEqual(obj.status_log, expected_log)

    def test_multiple_runtime_dicts(self):
        """Test object with multiple RuntimeDict instances."""
        class MultiConfigObject(Buildable):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.user_config = RuntimeDict(lambda: self._log_change("user"))
                self.system_config = RuntimeDict(lambda: self._log_change("system"))
                self.change_log = []

            def _log_change(self, config_type):
                self.change_log.append(f"{config_type}_config_changed")

        obj = MultiConfigObject()

        # Test both configs
        obj.user_config['theme'] = 'dark'
        obj.system_config['debug'] = True
        obj.user_config['language'] = 'en'

        expected_log = [
            "user_config_changed",
            "system_config_changed",
            "user_config_changed"
        ]

        self.assertEqual(obj.change_log, expected_log)

    def test_error_recovery_integration(self):
        """Test error recovery in integrated scenarios."""
        class ErrorProneObject(Runnable):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.should_fail = False
                self.config = RuntimeDict(self._handle_config_change)
                self.error_count = 0

            def _handle_config_change(self):
                if self.should_fail:
                    self.error_count += 1
                    raise RuntimeError("Simulated config error")

            def run(self, stop_code: int = 0) -> int:
                super().run()
                if 'fail_on_start' in self.config and self.config['fail_on_start']:
                    raise RuntimeError("Start failed")
                return 0

        obj = ErrorProneObject()

        # Normal operation
        obj.config['normal_setting'] = 'value'

        # Enable failure mode
        obj.should_fail = True

        # This should raise error but not break the object
        with self.assertRaises(RuntimeError):
            obj.config['failing_setting'] = 'value'

        self.assertEqual(obj.error_count, 1)

        # Disable failure mode and continue
        obj.should_fail = False
        obj.config['recovery_setting'] = 'value'

        # Object should still be functional
        obj.run()
        self.assertTrue(obj.running)


if __name__ == '__main__':
    unittest.main(verbosity=2)

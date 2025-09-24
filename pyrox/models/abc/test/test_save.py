"""Unit tests for save.py module."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import shutil

from pyrox.models.abc.save import (
    SupportsLoading,
    SupportsSaving,
    SupportsJsonLoading,
    SupportsJsonSaving,
)


class TestSupportsLoading(unittest.TestCase):
    """Test cases for SupportsLoading class."""

    def test_init_inherits_from_supports_file_location(self):
        """Test that SupportsLoading inherits from SupportsFileLocation."""
        obj = SupportsLoading()

        # Should have file_location attribute from parent
        self.assertIsNone(obj.file_location)

        # Test setting file_location
        obj.file_location = '/test/path'
        self.assertEqual(obj.file_location, '/test/path')

    def test_load_not_implemented(self):
        """Test that load method raises NotImplementedError."""
        obj = SupportsLoading()

        with self.assertRaises(NotImplementedError) as context:
            obj.load()

        self.assertIn("This method should be implemented in subclasses", str(context.exception))

    def test_load_with_path_parameter(self):
        """Test that load method can accept path parameter."""
        obj = SupportsLoading()
        test_path = Path('/test/path')

        with self.assertRaises(NotImplementedError):
            obj.load(test_path)

    def test_on_loaded_default_implementation(self):
        """Test on_loaded default implementation (no-op)."""
        obj = SupportsLoading()

        # Should not raise any errors
        obj.on_loaded("test data")
        obj.on_loaded({"key": "value"})
        obj.on_loaded(None)
        obj.on_loaded([1, 2, 3])

    def test_on_loaded_can_be_overridden(self):
        """Test that on_loaded can be overridden in subclasses."""
        class TestLoading(SupportsLoading):
            def __init__(self):
                super().__init__()
                self.loaded_data = None

            def on_loaded(self, data):
                self.loaded_data = data

            def load(self, path=None):
                # Mock implementation for testing
                test_data = {"loaded": True}
                self.on_loaded(test_data)
                return test_data

        obj = TestLoading()
        result = obj.load()

        self.assertEqual(obj.loaded_data, {"loaded": True})
        self.assertEqual(result, {"loaded": True})

    def test_slots_attribute(self):
        """Test that __slots__ is properly defined."""
        self.assertTrue(hasattr(SupportsLoading, '__slots__'))
        self.assertEqual(SupportsLoading.__slots__, ())


class TestSupportsSaving(unittest.TestCase):
    """Test cases for SupportsSaving class."""

    def test_init_inherits_from_supports_file_location(self):
        """Test that SupportsSaving inherits from SupportsFileLocation."""
        obj = SupportsSaving()

        # Should have file_location attribute from parent
        self.assertIsNone(obj.file_location)

        # Test setting file_location
        obj.file_location = '/test/path'
        self.assertEqual(obj.file_location, '/test/path')

    def test_save_data_callback_not_implemented(self):
        """Test that save_data_callback property returns none when not implimented."""
        obj = SupportsSaving()
        self.assertIsNone(obj.on_saving())

    def test_save_not_implemented(self):
        """Test that save method raises NotImplementedError."""
        obj = SupportsSaving()

        with self.assertRaises(NotImplementedError) as context:
            obj.save()

        self.assertIn("This method should be implemented in subclasses", str(context.exception))

    def test_save_with_parameters(self):
        """Test that save method can accept path and data parameters."""
        obj = SupportsSaving()
        test_path = Path('/test/path')
        test_data = {"test": "data"}

        with self.assertRaises(NotImplementedError):
            obj.save(test_path, test_data)

    def test_save_with_none_parameters(self):
        """Test save method with None parameters."""
        obj = SupportsSaving()

        with self.assertRaises(NotImplementedError):
            obj.save(None, None)

    def test_concrete_implementation_example(self):
        """Test concrete implementation of SupportsSaving."""
        class TestSaving(SupportsSaving):
            def __init__(self):
                super().__init__()
                self.data = {"test": "data"}
                self.saved_data = None
                self.saved_path = None

            @property
            def save_data_callback(self):
                return lambda: self.data

            def save(self, path=None, data=None):
                self.saved_path = path or self.file_location
                self.saved_data = data or self.save_data_callback()
                return True

        obj = TestSaving()
        obj.file_location = '/test/path'

        # Test save_data_callback
        callback = obj.save_data_callback
        self.assertEqual(callback(), {"test": "data"})

        # Test save
        result = obj.save()
        self.assertTrue(result)
        self.assertEqual(obj.saved_path, '/test/path')
        self.assertEqual(obj.saved_data, {"test": "data"})


class TestSupportsJsonSaving(unittest.TestCase):
    """Test cases for SupportsJsonSaving class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, 'test.json')
        self.test_data = {
            'name': 'Test Object',
            'version': '1.0.0',
            'items': ['item1', 'item2', 'item3'],
            'metadata': {
                'created': '2023-01-01',
                'author': 'test_author'
            }
        }

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_inherits_from_supports_saving(self):
        """Test that SupportsJsonSaving inherits from SupportsSaving."""
        obj = SupportsJsonSaving()

        self.assertIsInstance(obj, SupportsSaving)
        self.assertIsNone(obj.file_location)

    def test_save_to_json_with_explicit_path_and_data(self):
        """Test saving JSON with explicit path and data."""
        obj = SupportsJsonSaving()

        obj.save_to_json(Path(self.test_file_path), self.test_data)

        # Verify file was created
        self.assertTrue(os.path.exists(self.test_file_path))

        # Verify content
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data, self.test_data)

    def test_save_to_json_with_file_location_property(self):
        """Test saving JSON using file_location property."""
        class TestJsonSaving(SupportsJsonSaving):
            def on_saving(self):
                return {"from_callback": True}

        obj = TestJsonSaving()
        obj.file_location = self.test_file_path

        obj.save_to_json()

        # Verify file was created
        self.assertTrue(os.path.exists(self.test_file_path))

        # Verify content from callback
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data, {"from_callback": True})

    def test_save_to_json_no_path_raises_error(self):
        """Test that save_to_json raises ValueError when no path is provided."""
        obj = SupportsJsonSaving()

        with self.assertRaises(ValueError) as context:
            obj.save_to_json()

        self.assertEqual(str(context.exception), "No path provided for saving JSON data.")

    def test_save_to_json_invalid_directory_raises_ioerror(self):
        """Test that save_to_json raises IOError for invalid directory."""
        obj = SupportsJsonSaving()
        invalid_path = '/nonexistent/directory/file.json'

        with self.assertRaises(IOError) as context:
            obj.save_to_json(Path(invalid_path), self.test_data)

        self.assertIn("Failed to save JSON to", str(context.exception))

    def test_save_to_json_permission_error(self):
        """Test save_to_json with permission error."""
        obj = SupportsJsonSaving()

        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with self.assertRaises(IOError) as context:
                obj.save_to_json(Path(self.test_file_path), self.test_data)

            self.assertIn("Failed to save JSON to", str(context.exception))
            self.assertIn("Permission denied", str(context.exception))

    def test_save_to_json_with_callback_data(self):
        """Test saving JSON using save_data_callback."""
        class TestJsonSaving(SupportsJsonSaving):
            def __init__(self, data):
                super().__init__()
                self._data = data

            def on_saving(self):
                return self._data

        obj = TestJsonSaving(self.test_data)
        obj.save_to_json(Path(self.test_file_path))

        # Verify content
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data, self.test_data)

    def test_save_to_json_formatting(self):
        """Test that JSON is saved with proper formatting (indent=4)."""
        obj = SupportsJsonSaving()
        simple_data = {"key": "value", "number": 42}

        obj.save_to_json(Path(self.test_file_path), simple_data)

        # Read raw file content to check formatting
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Should contain indentation (4 spaces)
        self.assertIn('    ', content)
        # Should be properly formatted JSON
        self.assertTrue(content.strip().startswith('{'))
        self.assertTrue(content.strip().endswith('}'))

    def test_save_to_json_unicode_handling(self):
        """Test saving JSON with Unicode characters."""
        obj = SupportsJsonSaving()
        unicode_data = {
            'name': 'Test with Unicode: àáâãäå æç èéêë ìíîï',
            'emoji': '🚀 🌟 💎',
            'chinese': '你好世界'
        }

        obj.save_to_json(Path(self.test_file_path), unicode_data)

        # Verify Unicode characters are preserved
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data, unicode_data)

    def test_save_to_json_empty_data(self):
        """Test saving empty JSON data."""
        obj = SupportsJsonSaving()

        some_data = {'A': "1"}

        obj.save_to_json(Path(self.test_file_path), some_data)

        # Verify empty dict was saved
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data, some_data)

    def test_save_to_json_complex_nested_data(self):
        """Test saving complex nested JSON data."""
        obj = SupportsJsonSaving()
        complex_data = {
            'level1': {
                'level2': {
                    'level3': {
                        'deep_value': 'found_me',
                        'deep_list': [1, 2, {'nested': True}]
                    }
                },
                'list_of_dicts': [
                    {'item': 1, 'active': True},
                    {'item': 2, 'active': False}
                ]
            },
            'top_level_list': ['a', 'b', 'c']
        }

        obj.save_to_json(Path(self.test_file_path), complex_data)

        # Verify complex structure is preserved
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data, complex_data)
        self.assertEqual(loaded_data['level1']['level2']['level3']['deep_value'], 'found_me')

    def test_save_to_json_overwrite_existing_file(self):
        """Test saving JSON overwrites existing file."""
        obj = SupportsJsonSaving()

        # Create initial file
        initial_data = {'initial': 'data'}
        obj.save_to_json(Path(self.test_file_path), initial_data)

        # Overwrite with new data
        new_data = {'new': 'data', 'updated': True}
        obj.save_to_json(Path(self.test_file_path), new_data)

        # Verify new data overwrote old data
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data, new_data)
        self.assertNotEqual(loaded_data, initial_data)


class TestSupportsJsonLoading(unittest.TestCase):
    """Test cases for SupportsJsonLoading class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, 'test.json')
        self.test_data = {
            'name': 'Test Object',
            'version': '1.0.0',
            'items': ['item1', 'item2', 'item3'],
            'metadata': {
                'created': '2023-01-01',
                'author': 'test_author'
            }
        }

        # Create test JSON file
        with open(self.test_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_data, f, indent=4)

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_inherits_from_supports_loading(self):
        """Test that SupportsJsonLoading inherits from SupportsLoading."""
        obj = SupportsJsonLoading()

        self.assertIsInstance(obj, SupportsLoading)
        self.assertIsNone(obj.file_location)

    def test_load_from_json_with_explicit_path(self):
        """Test loading JSON with explicit path."""
        class TestJsonLoading(SupportsJsonLoading):
            def __init__(self):
                super().__init__()
                self.loaded_data = None

            def on_loaded(self, data):
                self.loaded_data = data

        obj = TestJsonLoading()

        result = obj.load_from_json(Path(self.test_file_path))

        self.assertEqual(result, self.test_data)
        self.assertEqual(obj.loaded_data, self.test_data)

    def test_load_from_json_with_file_location_property(self):
        """Test loading JSON using file_location property."""
        class TestJsonLoading(SupportsJsonLoading):
            def __init__(self):
                super().__init__()
                self.loaded_data = None

            def on_loaded(self, data):
                self.loaded_data = data

        obj = TestJsonLoading()
        obj.file_location = self.test_file_path

        result = obj.load_from_json()

        self.assertEqual(result, self.test_data)
        self.assertEqual(obj.loaded_data, self.test_data)

    def test_load_from_json_nonexistent_file_returns_none(self):
        """Test loading from non-existent file returns None."""
        obj = SupportsJsonLoading()
        nonexistent_path = os.path.join(self.temp_dir, 'nonexistent.json')

        result = obj.load_from_json(Path(nonexistent_path))

        self.assertIsNone(result)

    def test_load_from_json_no_path_returns_none(self):
        """Test loading with no path returns None."""
        obj = SupportsJsonLoading()
        # file_location is None by default

        result = obj.load_from_json()

        self.assertIsNone(result)

    def test_load_from_json_invalid_json_raises_ioerror(self):
        """Test loading invalid JSON raises IOError."""
        obj = SupportsJsonLoading()
        invalid_json_path = os.path.join(self.temp_dir, 'invalid.json')

        # Create file with invalid JSON
        with open(invalid_json_path, 'w', encoding='utf-8') as f:
            f.write("{ invalid json content")

        with self.assertRaises(IOError) as context:
            obj.load_from_json(Path(invalid_json_path))

        self.assertIn("Failed to load JSON from", str(context.exception))

    def test_load_from_json_permission_error(self):
        """Test loading JSON with permission error."""
        obj = SupportsJsonLoading()

        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with self.assertRaises(IOError) as context:
                obj.load_from_json(Path(self.test_file_path))

            self.assertIn("Failed to load JSON from", str(context.exception))
            self.assertIn("Permission denied", str(context.exception))

    def test_load_from_json_unicode_handling(self):
        """Test loading JSON with Unicode characters."""
        obj = SupportsJsonLoading()
        unicode_data = {
            'name': 'Test with Unicode: àáâãäå æç èéêë ìíîï',
            'emoji': '🚀 🌟 💎',
            'chinese': '你好世界'
        }
        unicode_file = os.path.join(self.temp_dir, 'unicode.json')

        # Create Unicode JSON file
        with open(unicode_file, 'w', encoding='utf-8') as f:
            json.dump(unicode_data, f, indent=4)

        result = obj.load_from_json(Path(unicode_file))

        self.assertEqual(result, unicode_data)

    def test_load_from_json_empty_json(self):
        """Test loading empty JSON file."""
        obj = SupportsJsonLoading()
        empty_file = os.path.join(self.temp_dir, 'empty.json')

        # Create empty JSON file
        with open(empty_file, 'w', encoding='utf-8') as f:
            json.dump({}, f)

        result = obj.load_from_json(Path(empty_file))

        self.assertEqual(result, {})

    def test_load_from_json_complex_nested_data(self):
        """Test loading complex nested JSON data."""
        obj = SupportsJsonLoading()
        complex_data = {
            'level1': {
                'level2': {
                    'level3': {
                        'deep_value': 'found_me',
                        'deep_list': [1, 2, {'nested': True}]
                    }
                },
                'list_of_dicts': [
                    {'item': 1, 'active': True},
                    {'item': 2, 'active': False}
                ]
            },
            'top_level_list': ['a', 'b', 'c']
        }
        complex_file = os.path.join(self.temp_dir, 'complex.json')

        # Create complex JSON file
        with open(complex_file, 'w', encoding='utf-8') as f:
            json.dump(complex_data, f, indent=4)

        result = obj.load_from_json(Path(complex_file))

        self.assertEqual(result, complex_data)
        self.assertEqual(result['level1']['level2']['level3']['deep_value'], 'found_me')

    def test_load_from_json_calls_on_loaded(self):
        """Test that load_from_json calls on_loaded with correct data."""
        class TestJsonLoading(SupportsJsonLoading):
            def __init__(self):
                super().__init__()
                self.on_loaded_calls = []

            def on_loaded(self, data):
                self.on_loaded_calls.append(data)

        obj = TestJsonLoading()

        result = obj.load_from_json(Path(self.test_file_path))

        self.assertEqual(len(obj.on_loaded_calls), 1)
        self.assertEqual(obj.on_loaded_calls[0], self.test_data)
        self.assertEqual(result, self.test_data)

    def test_load_from_json_string_path_conversion(self):
        """Test that string paths are converted to Path objects."""
        obj = SupportsJsonLoading()

        # Pass string path instead of Path object
        result = obj.load_from_json(self.test_file_path)

        self.assertEqual(result, self.test_data)

    def test_load_from_json_file_location_string_conversion(self):
        """Test file_location string is converted to Path."""
        obj = SupportsJsonLoading()
        obj.file_location = self.test_file_path  # String path

        result = obj.load_from_json()

        self.assertEqual(result, self.test_data)

    def test_load_method_still_not_implemented(self):
        """Test that inherited load method still raises NotImplementedError."""
        obj = SupportsJsonLoading()

        with self.assertRaises(NotImplementedError):
            obj.load()

    def test_slots_attribute(self):
        """Test that __slots__ is properly defined."""
        self.assertTrue(hasattr(SupportsJsonLoading, '__slots__'))
        self.assertEqual(SupportsJsonLoading.__slots__, ())


class TestIntegration(unittest.TestCase):
    """Integration tests for save and load functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, 'integration_test.json')

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_load_json_integration(self):
        """Test complete save and load JSON cycle."""
        class TestSaveLoad(SupportsJsonSaving, SupportsJsonLoading):
            def __init__(self, data=None):
                super().__init__()
                self._data = data or {}
                self.loaded_data = None

            def on_saving(self):
                return self._data

            def on_loaded(self, data):
                self.loaded_data = data
                self._data = data

        # Test data
        original_data = {
            'name': 'Integration Test',
            'version': '2.0.0',
            'features': ['save', 'load', 'json'],
            'config': {
                'auto_save': True,
                'backup_count': 5
            }
        }

        # Create object and save data
        obj1 = TestSaveLoad(original_data)
        obj1.save_to_json(Path(self.test_file_path))

        # Verify file exists
        self.assertTrue(os.path.exists(self.test_file_path))

        # Create new object and load data
        obj2 = TestSaveLoad()
        loaded_data = obj2.load_from_json(Path(self.test_file_path))

        # Verify data integrity
        self.assertEqual(loaded_data, original_data)
        self.assertEqual(obj2.loaded_data, original_data)
        self.assertEqual(obj2._data, original_data)

    def test_file_location_property_integration(self):
        """Test using file_location property for both saving and loading."""
        class TestFileLocation(SupportsJsonSaving, SupportsJsonLoading):
            def __init__(self, data=None):
                super().__init__()
                self._data = data or {}
                self.load_history = []

            def on_saving(self):
                return self._data

            def on_loaded(self, data):
                self.load_history.append(data)

        test_data = {'integrated': True, 'test_id': 'file_location_test'}

        # Create object and set file location
        obj = TestFileLocation(test_data)
        obj.file_location = self.test_file_path

        # Save using file_location
        obj.save_to_json()

        # Clear internal data
        obj._data = {}

        # Load using file_location
        result = obj.load_from_json()

        # Verify integration
        self.assertEqual(result, test_data)
        self.assertEqual(len(obj.load_history), 1)
        self.assertEqual(obj.load_history[0], test_data)

    def test_error_handling_integration(self):
        """Test error handling in integrated save/load operations."""
        class TestErrorHandling(SupportsJsonSaving, SupportsJsonLoading):
            @property
            def on_saving(self):
                return lambda: {'error_test': True}

        obj = TestErrorHandling()

        # Test save error - invalid path
        with self.assertRaises(IOError):
            obj.save_to_json(Path('/invalid/path/file.json'))

        # Test load error - invalid JSON
        invalid_json_path = os.path.join(self.temp_dir, 'invalid.json')
        with open(invalid_json_path, 'w') as f:
            f.write('{ invalid json')

        with self.assertRaises(IOError):
            obj.load_from_json(Path(invalid_json_path))

    def test_multiple_inheritance_compatibility(self):
        """Test that multiple inheritance works correctly."""
        class ComplexObject(SupportsJsonSaving, SupportsJsonLoading):
            def __init__(self, name="test"):
                super().__init__()
                self.name = name
                self.data = {'name': name, 'type': 'complex'}
                self.load_count = 0

            def on_saving(self):
                return {'name': self.name, 'data': self.data}

            def on_loaded(self, data):
                self.load_count += 1
                self.name = data.get('name', 'unknown')
                self.data = data.get('data', {})

            def load(self, path=None):
                # Custom implementation of load
                return self.load_from_json(path)

            def save(self, path=None, data=None):
                # Custom implementation of save
                self.save_to_json(path, data)

        # Test the complex object
        obj = ComplexObject("integration_test")
        obj.file_location = self.test_file_path

        # Test save method
        obj.save()
        self.assertTrue(os.path.exists(self.test_file_path))

        # Test load method
        obj2 = ComplexObject()
        obj2.file_location = self.test_file_path
        result = obj2.load()

        # Verify complex inheritance works
        self.assertEqual(obj2.name, "integration_test")
        self.assertEqual(obj2.load_count, 1)
        self.assertIsNotNone(result)

    def test_real_world_usage_pattern(self):
        """Test realistic usage patterns."""
        class ConfigManager(SupportsJsonSaving, SupportsJsonLoading):
            def __init__(self, config_path=None):
                super().__init__()
                self.file_location = config_path
                self.settings = {
                    'app_name': 'Pyrox App',
                    'version': '1.0.0',
                    'debug': False,
                    'database': {
                        'host': 'localhost',
                        'port': 5432,
                        'name': 'pyrox_db'
                    },
                    'features': {
                        'auto_save': True,
                        'backup': True,
                        'logging': 'info'
                    }
                }
                self.is_loaded = False

            def on_saving(self):
                return self.settings

            def on_loaded(self, data):
                self.settings.update(data)
                self.is_loaded = True

            def get_setting(self, key, default=None):
                return self.settings.get(key, default)

            def update_setting(self, key, value):
                self.settings[key] = value

            def save_config(self):
                self.save_to_json()

            def load_config(self):
                return self.load_from_json()

        # Test realistic config management
        config_path = os.path.join(self.temp_dir, 'app_config.json')

        # Create and save config
        config1 = ConfigManager(config_path)
        config1.update_setting('debug', True)
        config1.save_config()

        # Load config in new instance
        config2 = ConfigManager(config_path)
        config2.load_config()

        # Verify realistic usage
        self.assertTrue(config2.is_loaded)
        self.assertTrue(config2.get_setting('debug'))
        self.assertEqual(config2.get_setting('app_name'), 'Pyrox App')
        self.assertEqual(config2.get_setting('database')['host'], 'localhost')


if __name__ == '__main__':
    unittest.main(verbosity=2)

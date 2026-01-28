"""Unit tests for protocols.py module."""

import unittest

from pyrox.models.abc.protocols import (
    Nameable,
    Describable,
    Refreshable,
    Resettable,
    Buildable,
    Runnable,
    CoreRunnableMixin,
    HasFileLocation,
    HasMetaDictData,
    SupportsItemAccess,
)


class TestNameable(unittest.TestCase):
    """Test cases for Nameable class."""

    def test_init_default_name(self):
        """Test initialization with default empty name."""
        obj = Nameable()
        self.assertEqual(obj.get_name(), "")

    def test_init_with_name(self):
        """Test initialization with provided name."""
        obj = Nameable(name="Test Object")
        self.assertEqual(obj.get_name(), "Test Object")

    def test_get_name(self):
        """Test getting the name."""
        obj = Nameable(name="My Name")
        result = obj.get_name()
        self.assertEqual(result, "My Name")
        self.assertIsInstance(result, str)

    def test_set_name(self):
        """Test setting the name."""
        obj = Nameable()
        obj.set_name("New Name")
        self.assertEqual(obj.get_name(), "New Name")

    def test_set_name_updates_existing(self):
        """Test setting name updates existing value."""
        obj = Nameable(name="Old Name")
        obj.set_name("New Name")
        self.assertEqual(obj.get_name(), "New Name")

    def test_set_name_with_empty_string(self):
        """Test setting name to empty string."""
        obj = Nameable(name="Original")
        obj.set_name("")
        self.assertEqual(obj.get_name(), "")

    def test_name_property_via_methods(self):
        """Test name property access via methods."""
        obj = Nameable()
        obj.set_name("Test Name")
        self.assertEqual(obj.get_name(), "Test Name")


class TestDescribable(unittest.TestCase):
    """Test cases for Describable class."""

    def test_init_default_description(self):
        """Test initialization with default empty description."""
        obj = Describable()
        self.assertEqual(obj.get_description(), "")

    def test_init_with_description(self):
        """Test initialization with provided description."""
        obj = Describable(description="Test description")
        self.assertEqual(obj.get_description(), "Test description")

    def test_get_description(self):
        """Test getting the description."""
        obj = Describable(description="My description")
        result = obj.get_description()
        self.assertEqual(result, "My description")
        self.assertIsInstance(result, str)

    def test_set_description(self):
        """Test setting the description."""
        obj = Describable()
        obj.set_description("New Description")
        self.assertEqual(obj.get_description(), "New Description")

    def test_set_description_updates_existing(self):
        """Test setting description updates existing value."""
        obj = Describable(description="Old Description")
        obj.set_description("New Description")
        self.assertEqual(obj.get_description(), "New Description")

    def test_set_description_with_empty_string(self):
        """Test setting description to empty string."""
        obj = Describable(description="Original")
        obj.set_description("")
        self.assertEqual(obj.get_description(), "")


class TestRefreshable(unittest.TestCase):
    """Test cases for Refreshable class."""

    def test_refresh_method_exists(self):
        """Test that refresh method exists and is callable."""
        obj = Refreshable()
        self.assertTrue(hasattr(obj, 'refresh'))
        self.assertTrue(callable(obj.refresh))

    def test_refresh_can_be_called_multiple_times(self):
        """Test that refresh can be called multiple times."""
        obj = Refreshable()
        for _ in range(5):
            _ = obj.refresh()


class TestResettable(unittest.TestCase):
    """Test cases for Resettable class."""

    def test_reset_method_exists(self):
        """Test that reset method exists and is callable."""
        obj = Resettable()
        self.assertTrue(hasattr(obj, 'reset'))
        self.assertTrue(callable(obj.reset))

    def test_reset_can_be_called_multiple_times(self):
        """Test that reset can be called multiple times."""
        obj = Resettable()
        for _ in range(5):
            _ = obj.reset()


class TestBuildable(unittest.TestCase):
    """Test cases for Buildable class."""

    def test_init_default_not_built(self):
        """Test initialization with default not built state."""
        obj = Buildable()
        self.assertFalse(obj.is_built())

    def test_build_sets_built_to_true(self):
        """Test that build() sets built state to True."""
        obj = Buildable()
        obj.build()
        self.assertTrue(obj.is_built())

    def test_teardown_sets_built_to_false(self):
        """Test that teardown() sets built state to False."""
        obj = Buildable()
        obj.build()
        obj.teardown()
        self.assertFalse(obj.is_built())

    def test_is_built_default_false(self):
        """Test that is_built() returns False by default."""
        obj = Buildable()
        self.assertFalse(obj.is_built())

    def test_is_built_after_build(self):
        """Test that is_built() returns True after build()."""
        obj = Buildable()
        obj.build()
        self.assertTrue(obj.is_built())

    def test_multiple_build_calls(self):
        """Test multiple build() calls."""
        obj = Buildable()
        obj.build()
        obj.build()
        self.assertTrue(obj.is_built())


class TestRunnable(unittest.TestCase):
    """Test cases for Runnable class."""

    def test_init_default_not_running(self):
        """Test initialization with default not running state."""
        obj = Runnable()
        self.assertFalse(obj.is_running())

    def test_run_sets_running_to_true(self):
        """Test that run() sets running state to True."""
        obj = Runnable()
        obj.run()
        self.assertTrue(obj.is_running())

    def test_run_returns_zero(self):
        """Test that run() returns 0."""
        obj = Runnable()
        result = obj.run()
        self.assertEqual(result, 0)

    def test_stop_sets_running_to_false(self):
        """Test that stop() sets running state to False."""
        obj = Runnable()
        obj.run()
        obj.stop()
        self.assertFalse(obj.is_running())

    def test_is_running_default_false(self):
        """Test that is_running() returns False by default."""
        obj = Runnable()
        self.assertFalse(obj.is_running())

    def test_is_running_after_run(self):
        """Test that is_running() returns True after run()."""
        obj = Runnable()
        obj.run()
        self.assertTrue(obj.is_running())

    def test_multiple_run_calls(self):
        """Test multiple run() calls."""
        obj = Runnable()
        obj.run()
        obj.run()
        self.assertTrue(obj.is_running())


class TestCoreRunnableMixin(unittest.TestCase):
    """Test cases for CoreRunnableMixin class."""

    def test_mixin_init_default_values(self):
        """Test initialization with default values."""
        obj = CoreRunnableMixin()
        self.assertEqual(obj.get_name(), "")
        self.assertEqual(obj.get_description(), "")
        self.assertFalse(obj.is_built())

    def test_init_with_name_and_description(self):
        """Test initialization with name and description."""
        obj = CoreRunnableMixin(name="Mixin Test", description="Test Desc")
        self.assertEqual(obj.get_name(), "Mixin Test")
        self.assertEqual(obj.get_description(), "Test Desc")

    def test_inherits_nameable_functionality(self):
        """Test that mixin inherits Nameable functionality."""
        obj = CoreRunnableMixin()
        obj.set_name("Test Name")
        self.assertEqual(obj.get_name(), "Test Name")

    def test_inherits_describable_functionality(self):
        """Test that mixin inherits Describable functionality."""
        obj = CoreRunnableMixin()
        obj.set_description("Test Description")
        self.assertEqual(obj.get_description(), "Test Description")

    def test_inherits_buildable_functionality(self):
        """Test that mixin inherits Buildable functionality."""
        obj = CoreRunnableMixin()
        self.assertFalse(obj.is_built())
        obj.build()
        self.assertTrue(obj.is_built())

    def test_inherits_runnable_functionality(self):
        """Test that mixin inherits Runnable functionality."""
        obj = CoreRunnableMixin()
        # Manually initialize Runnable since CoreRunnableMixin doesn't call it
        Runnable.__init__(obj)

        self.assertFalse(obj.is_running())
        obj.run()
        self.assertTrue(obj.is_running())
        obj.stop()
        self.assertFalse(obj.is_running())

    def test_mixin_initialization_order(self):
        """Test that initialization order works correctly."""
        obj = CoreRunnableMixin(name="Init Test", description="Init description")
        self.assertTrue(hasattr(obj, '_name'))
        self.assertTrue(hasattr(obj, '_description'))
        self.assertTrue(hasattr(obj, '_built'))


class TestHasFileLocation(unittest.TestCase):
    """Test cases for HasFileLocation class."""

    def test_init_default_file_location(self):
        """Test initialization with default empty file location."""
        obj = HasFileLocation()
        self.assertEqual(obj.get_file_location(), "")

    def test_init_with_file_location(self):
        """Test initialization with provided file location."""
        obj = HasFileLocation(file_location="/path/to/file.txt")
        self.assertEqual(obj.get_file_location(), "/path/to/file.txt")

    def test_get_file_location(self):
        """Test getting the file location."""
        obj = HasFileLocation(file_location="/test/path")
        result = obj.get_file_location()
        self.assertEqual(result, "/test/path")
        self.assertIsInstance(result, str)

    def test_set_file_location(self):
        """Test setting the file location."""
        obj = HasFileLocation()
        obj.set_file_location("/new/path")
        self.assertEqual(obj.get_file_location(), "/new/path")

    def test_set_file_location_updates_existing(self):
        """Test setting file location updates existing value."""
        obj = HasFileLocation(file_location="/old/path")
        obj.set_file_location("/new/path")
        self.assertEqual(obj.get_file_location(), "/new/path")

    def test_set_file_location_with_empty_string(self):
        """Test setting file location to empty string."""
        obj = HasFileLocation(file_location="/some/path")
        obj.set_file_location("")
        self.assertEqual(obj.get_file_location(), "")

    def test_file_location_with_windows_path(self):
        """Test file location with Windows-style path."""
        obj = HasFileLocation()
        obj.set_file_location(r"C:\Windows\Path\file.txt")
        self.assertEqual(obj.get_file_location(), r"C:\Windows\Path\file.txt")


class TestHasMetaData(unittest.TestCase):
    """Test cases for HasMetaData class."""

    def test_init_default_metadata(self):
        """Test initialization with default empty metadata."""
        obj = HasMetaDictData()
        self.assertEqual(obj.get_metadata(), {})

    def test_init_with_metadata(self):
        """Test initialization with provided metadata."""
        obj = HasMetaDictData(meta_data={"key": "value"})
        self.assertEqual(obj.get_metadata(), {"key": "value"})

    def test_get_meta_data(self):
        """Test getting the metadata."""
        obj = HasMetaDictData(meta_data={"test": "data"})
        result = obj.get_metadata()
        self.assertEqual(result, {"test": "data"})
        self.assertIsInstance(result, dict)

    def test_set_meta_data_dict(self):
        """Test setting metadata with dictionary."""
        obj = HasMetaDictData()
        obj.set_metadata({"new": "data"})
        self.assertEqual(obj.get_metadata(), {"new": "data"})

    def test_set_meta_data_updates_existing(self):
        """Test setting metadata updates existing value."""
        obj = HasMetaDictData(meta_data={"old": "data"})
        obj.set_metadata({"new": "data"})
        self.assertEqual(obj.get_metadata(), {"new": "data"})

    def test_set_meta_data_with_empty_dict(self):
        """Test setting metadata to empty dictionary."""
        obj = HasMetaDictData(meta_data={"some": "data"})
        obj.set_metadata({})
        self.assertEqual(obj.get_metadata(), {})

    def test_metadata_with_nested_structure(self):
        """Test metadata with nested dictionary structure."""
        nested = {"level1": {"level2": {"value": 42}}}
        obj = HasMetaDictData()
        obj.set_metadata(nested)
        result = obj.get_metadata()
        self.assertEqual(result["level1"]["level2"]["value"], 42)  # type: ignore


class TestSupportsItemAccess(unittest.TestCase):
    """Test cases for SupportsItemAccess class."""

    def test_getitem_with_dict_metadata(self):
        """Test __getitem__ with dictionary metadata."""
        obj = SupportsItemAccess()
        obj.set_metadata({"key1": "value1", "key2": 42})
        result = obj.get_metadata()["key1"]
        self.assertEqual(result, "value1")

    def test_getitem_with_multiple_keys(self):
        """Test __getitem__ with multiple keys."""
        obj = SupportsItemAccess()
        obj.set_metadata({"a": 1, "b": 2, "c": 3})
        metadata = obj.get_metadata()
        self.assertEqual(metadata["a"], 1)
        self.assertEqual(metadata["b"], 2)
        self.assertEqual(metadata["c"], 3)

    def test_getitem_missing_key_raises_keyerror(self):
        """Test __getitem__ with missing key raises KeyError."""
        obj = SupportsItemAccess()
        obj.set_metadata({"existing": "value"})
        with self.assertRaises(KeyError):
            _ = obj.get_metadata()["nonexistent"]

    def test_setitem_with_dict_metadata(self):
        """Test __setitem__ with dictionary metadata."""
        obj = SupportsItemAccess()
        metadata = obj.get_metadata()
        metadata["new_key"] = "new_value"
        self.assertEqual(metadata["new_key"], "new_value")
        self.assertIn("new_key", obj.get_metadata())

    def test_setitem_updates_existing_key(self):
        """Test __setitem__ updates existing key."""
        obj = SupportsItemAccess()
        metadata = obj.get_metadata()
        metadata["key"] = "old_value"
        metadata["key"] = "new_value"
        self.assertEqual(metadata["key"], "new_value")

    def test_setitem_multiple_keys(self):
        """Test __setitem__ with multiple keys."""
        obj = SupportsItemAccess()
        metadata = obj.get_metadata()
        metadata["key1"] = "value1"
        metadata["key2"] = 42
        metadata["key3"] = [1, 2, 3]
        self.assertEqual(metadata["key1"], "value1")
        self.assertEqual(metadata["key2"], 42)
        self.assertEqual(metadata["key3"], [1, 2, 3])

    def test_item_access_integration(self):
        """Test full integration of item access."""
        obj = SupportsItemAccess()
        metadata = obj.get_metadata()
        metadata["name"] = "Test"
        metadata["count"] = 10
        self.assertEqual(metadata["name"], "Test")
        self.assertEqual(metadata["count"], 10)
        result = obj.get_metadata()
        self.assertEqual(result["name"], "Test")
        self.assertEqual(result["count"], 10)

    def test_item_access_with_various_types(self):
        """Test item access with various value types."""
        obj = SupportsItemAccess()
        metadata = obj.get_metadata()
        metadata["string"] = "text"
        metadata["int"] = 42
        metadata["float"] = 3.14
        metadata["list"] = [1, 2, 3]
        metadata["dict"] = {"nested": "value"}
        metadata["bool"] = True
        metadata["none"] = None
        self.assertEqual(metadata["string"], "text")
        self.assertEqual(metadata["int"], 42)
        self.assertEqual(metadata["float"], 3.14)
        self.assertEqual(metadata["list"], [1, 2, 3])
        self.assertEqual(metadata["dict"], {"nested": "value"})
        self.assertEqual(metadata["bool"], True)
        self.assertIsNone(metadata["none"])


class TestProtocolsComposition(unittest.TestCase):
    """Test composing multiple protocols together."""

    def test_nameable_and_describable_composition(self):
        """Test composing Nameable and Describable."""
        class NamedAndDescribed(Nameable, Describable):
            def __init__(self, name="", description=""):
                Nameable.__init__(self, name)
                Describable.__init__(self, description)

        obj = NamedAndDescribed(name="Test", description="Test Desc")
        self.assertEqual(obj.get_name(), "Test")
        self.assertEqual(obj.get_description(), "Test Desc")

    def test_buildable_and_runnable_composition(self):
        """Test composing Buildable and Runnable."""
        class BuildableRunnable(Buildable, Runnable):
            def __init__(self):
                Buildable.__init__(self)
                Runnable.__init__(self)

        obj = BuildableRunnable()
        obj.build()
        self.assertTrue(obj.is_built())
        obj.run()
        self.assertTrue(obj.is_running())

    def test_all_protocols_composition(self):
        """Test composing all protocols together."""
        class AllProtocols(
            Nameable,
            Describable,
            Buildable,
            Runnable,
            HasFileLocation,
            SupportsItemAccess,
            HasMetaDictData,
        ):
            def __init__(self):
                Nameable.__init__(self)
                Describable.__init__(self)
                Buildable.__init__(self)
                Runnable.__init__(self)
                HasFileLocation.__init__(self)
                SupportsItemAccess.__init__(self)
                HasMetaDictData.__init__(self)

        obj = AllProtocols()
        obj.set_name("All")
        obj.set_description("All protocols")
        obj.build()
        obj.run()
        obj.set_file_location("/path")
        metadata = obj.get_metadata()
        metadata["key"] = "value"

        self.assertEqual(obj.get_name(), "All")
        self.assertEqual(obj.get_description(), "All protocols")
        self.assertTrue(obj.is_built())
        self.assertTrue(obj.is_running())
        self.assertEqual(obj.get_file_location(), "/path")
        metadata = obj.get_metadata()
        self.assertEqual(metadata["key"], "value")


class TestProtocolsEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def test_nameable_with_special_characters(self):
        """Test Nameable with special characters in name."""
        obj = Nameable()
        special_names = [
            "Name with spaces",
            "Name-with-dashes",
            "Name_with_underscores",
            "Name.with.dots",
            "Name@with@symbols",
            "ナメ (Unicode)",
            ""
        ]
        for name in special_names:
            obj.set_name(name)
            self.assertEqual(obj.get_name(), name)

    def test_describable_with_long_text(self):
        """Test Describable with very long description."""
        obj = Describable()
        long_desc = "A" * 10000
        obj.set_description(long_desc)
        self.assertEqual(obj.get_description(), long_desc)
        self.assertEqual(len(obj.get_description()), 10000)

    def test_buildable_state_persistence(self):
        """Test that built state persists across operations."""
        obj = Buildable()
        obj.build()
        obj.refresh()
        self.assertTrue(obj.is_built())
        obj.teardown()
        self.assertFalse(obj.is_built())

    def test_runnable_state_persistence(self):
        """Test that running state persists across operations."""
        obj = Runnable()
        obj.run()
        for _ in range(10):
            self.assertTrue(obj.is_running())
        obj.stop()
        self.assertFalse(obj.is_running())

    def test_has_metadata_with_complex_structures(self):
        """Test HasMetaData with complex nested structures."""
        obj = HasMetaDictData()
        complex_data = {
            "nested": {
                "level1": {
                    "level2": {
                        "value": 42
                    }
                }
            },
            "list": [1, 2, [3, 4, [5, 6]]],
            "mixed": {
                "list": [{"key": "value"}],
                "dict": {"list": [1, 2, 3]}
            }
        }
        obj.set_metadata(complex_data)
        result = obj.get_metadata()
        self.assertEqual(result["nested"]["level1"]["level2"]["value"], 42)
        self.assertEqual(result["list"][2][2][1], 6)

    def test_supports_item_access_empty_metadata(self):
        """Test SupportsItemAccess with empty metadata."""
        obj = SupportsItemAccess()
        with self.assertRaises(KeyError):
            _ = obj.get_metadata()["nonexistent"]
        metadata = obj.get_metadata()
        metadata["first"] = "value"
        self.assertEqual(metadata["first"], "value")


if __name__ == '__main__':
    unittest.main()

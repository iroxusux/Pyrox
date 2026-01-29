"""Unit tests for meta.py protocols module."""

import unittest

from pyrox.models.protocols.meta import (
    Configurable,
    Authored,
    Versioned,
    HasId,
    Nameable,
    Describable,
    Refreshable,
    Resettable,
    Buildable,
    Runnable,
    CoreMixin,
    CoreRunnableMixin,
    HasFileLocation,
    HasMetaDictData,
    SupportsItemAccess,
)


class TestConfigurable(unittest.TestCase):
    """Test cases for Configurable class."""

    def test_init_default_config(self):
        """Test initialization with default empty config."""
        obj = Configurable()
        self.assertEqual(obj.get_config(), {})

    def test_init_with_config(self):
        """Test initialization with provided config."""
        config = {"key1": "value1", "key2": 42}
        obj = Configurable(config=config)
        self.assertEqual(obj.get_config(), config)

    def test_get_config(self):
        """Test getting the configuration."""
        config = {"setting": "value"}
        obj = Configurable(config=config)
        result = obj.get_config()
        self.assertEqual(result, config)
        self.assertIsInstance(result, dict)

    def test_set_config(self):
        """Test setting the configuration."""
        obj = Configurable()
        new_config = {"new_key": "new_value"}
        obj.set_config(new_config)
        self.assertEqual(obj.get_config(), new_config)

    def test_set_config_updates_existing(self):
        """Test setting config updates existing value."""
        obj = Configurable(config={"old": "config"})
        new_config = {"new": "config"}
        obj.set_config(new_config)
        self.assertEqual(obj.get_config(), new_config)

    def test_configure_method_exists(self):
        """Test that configure method exists and is callable."""
        obj = Configurable()
        self.assertTrue(hasattr(obj, 'configure'))
        self.assertTrue(callable(obj.configure))

    def test_config_property(self):
        """Test config property access."""
        config = {"test": "data"}
        obj = Configurable(config=config)
        self.assertEqual(obj.config, config)


class TestAuthored(unittest.TestCase):
    """Test cases for Authored class."""

    def test_init_default_author(self):
        """Test initialization with default empty author."""
        obj = Authored()
        self.assertEqual(obj.get_author(), "")

    def test_init_with_author(self):
        """Test initialization with provided author."""
        obj = Authored(author="John Doe")
        self.assertEqual(obj.get_author(), "John Doe")

    def test_get_author(self):
        """Test getting the author."""
        obj = Authored(author="Jane Smith")
        result = obj.get_author()
        self.assertEqual(result, "Jane Smith")
        self.assertIsInstance(result, str)

    def test_set_author(self):
        """Test setting the author."""
        obj = Authored()
        obj.set_author("New Author")
        self.assertEqual(obj.get_author(), "New Author")

    def test_set_author_updates_existing(self):
        """Test setting author updates existing value."""
        obj = Authored(author="Old Author")
        obj.set_author("New Author")
        self.assertEqual(obj.get_author(), "New Author")

    def test_author_property(self):
        """Test author property access."""
        obj = Authored(author="Test Author")
        self.assertEqual(obj.author, "Test Author")


class TestVersioned(unittest.TestCase):
    """Test cases for Versioned class."""

    def test_init_default_version(self):
        """Test initialization with default empty version."""
        obj = Versioned()
        self.assertEqual(obj.get_version(), "")

    def test_init_with_version(self):
        """Test initialization with provided version."""
        obj = Versioned(version="1.0.0")
        self.assertEqual(obj.get_version(), "1.0.0")

    def test_get_version(self):
        """Test getting the version."""
        obj = Versioned(version="2.3.1")
        result = obj.get_version()
        self.assertEqual(result, "2.3.1")
        self.assertIsInstance(result, str)

    def test_set_version(self):
        """Test setting the version."""
        obj = Versioned()
        obj.set_version("3.0.0")
        self.assertEqual(obj.get_version(), "3.0.0")

    def test_set_version_updates_existing(self):
        """Test setting version updates existing value."""
        obj = Versioned(version="1.0.0")
        obj.set_version("2.0.0")
        self.assertEqual(obj.get_version(), "2.0.0")

    def test_version_property(self):
        """Test version property access."""
        obj = Versioned(version="4.5.6")
        self.assertEqual(obj.version, "4.5.6")


class TestHasId(unittest.TestCase):
    """Test cases for HasId class."""

    def test_init_default_id(self):
        """Test initialization with default empty id."""
        obj = HasId()
        self.assertEqual(obj.get_id(), "")

    def test_init_with_id(self):
        """Test initialization with provided id."""
        obj = HasId(id="test-id-123")
        self.assertEqual(obj.get_id(), "test-id-123")

    def test_get_id(self):
        """Test getting the id."""
        obj = HasId(id="unique-id")
        result = obj.get_id()
        self.assertEqual(result, "unique-id")
        self.assertIsInstance(result, str)

    def test_set_id(self):
        """Test setting the id."""
        obj = HasId()
        obj.set_id("new-id")
        self.assertEqual(obj.get_id(), "new-id")

    def test_set_id_updates_existing(self):
        """Test setting id updates existing value."""
        obj = HasId(id="old-id")
        obj.set_id("new-id")
        self.assertEqual(obj.get_id(), "new-id")

    def test_id_property(self):
        """Test id property access."""
        obj = HasId(id="property-id")
        self.assertEqual(obj.id, "property-id")


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

    def test_name_property(self):
        """Test name property access."""
        obj = Nameable(name="Test Name")
        self.assertEqual(obj.name, "Test Name")


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

    def test_description_property(self):
        """Test description property access."""
        obj = Describable(description="Test Description")
        self.assertEqual(obj.description, "Test Description")


class TestRefreshable(unittest.TestCase):
    """Test cases for Refreshable class."""

    def test_refresh_method_exists(self):
        """Test that refresh method exists and is callable."""
        obj = Refreshable()
        self.assertTrue(hasattr(obj, 'refresh'))
        self.assertTrue(callable(obj.refresh))

    def test_refresh_can_be_called(self):
        """Test that refresh can be called without error."""
        obj = Refreshable()
        obj.refresh()  # Should not raise

    def test_refresh_can_be_called_multiple_times(self):
        """Test that refresh can be called multiple times."""
        obj = Refreshable()
        for _ in range(5):
            obj.refresh()


class TestResettable(unittest.TestCase):
    """Test cases for Resettable class."""

    def test_reset_method_exists(self):
        """Test that reset method exists and is callable."""
        obj = Resettable()
        self.assertTrue(hasattr(obj, 'reset'))
        self.assertTrue(callable(obj.reset))

    def test_reset_can_be_called(self):
        """Test that reset can be called without error."""
        obj = Resettable()
        obj.reset()  # Should not raise

    def test_reset_can_be_called_multiple_times(self):
        """Test that reset can be called multiple times."""
        obj = Resettable()
        for _ in range(5):
            obj.reset()


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

    def test_refresh_method_exists(self):
        """Test that refresh method exists."""
        obj = Buildable()
        self.assertTrue(hasattr(obj, 'refresh'))
        self.assertTrue(callable(obj.refresh))

    def test_build_teardown_cycle(self):
        """Test multiple build/teardown cycles."""
        obj = Buildable()
        for _ in range(3):
            self.assertFalse(obj.is_built())
            obj.build()
            self.assertTrue(obj.is_built())
            obj.teardown()
            self.assertFalse(obj.is_built())


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

    def test_stop_default_code(self):
        """Test stop() with default stop code."""
        obj = Runnable()
        obj.run()
        obj.stop()  # Default stop_code=0
        self.assertFalse(obj.is_running())

    def test_stop_with_custom_code(self):
        """Test stop() with custom stop code."""
        obj = Runnable()
        obj.run()
        obj.stop(stop_code=1)
        self.assertFalse(obj.is_running())

    def test_is_running_default_false(self):
        """Test that is_running() returns False by default."""
        obj = Runnable()
        self.assertFalse(obj.is_running())

    def test_multiple_run_calls(self):
        """Test multiple run() calls."""
        obj = Runnable()
        obj.run()
        obj.run()
        self.assertTrue(obj.is_running())

    def test_run_stop_cycle(self):
        """Test multiple run/stop cycles."""
        obj = Runnable()
        for _ in range(3):
            self.assertFalse(obj.is_running())
            obj.run()
            self.assertTrue(obj.is_running())
            obj.stop()
            self.assertFalse(obj.is_running())


class TestCoreMixin(unittest.TestCase):
    """Test cases for CoreMixin class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        obj = CoreMixin()
        self.assertEqual(obj.get_id(), "")
        self.assertEqual(obj.get_name(), "")
        self.assertEqual(obj.get_description(), "")

    def test_init_with_all_values(self):
        """Test initialization with all values provided."""
        obj = CoreMixin(
            id="test-id",
            name="Test Name",
            description="Test Description"
        )
        self.assertEqual(obj.get_id(), "test-id")
        self.assertEqual(obj.get_name(), "Test Name")
        self.assertEqual(obj.get_description(), "Test Description")

    def test_init_with_partial_values(self):
        """Test initialization with partial values."""
        obj = CoreMixin(name="Just Name")
        self.assertEqual(obj.get_id(), "")
        self.assertEqual(obj.get_name(), "Just Name")
        self.assertEqual(obj.get_description(), "")

    def test_set_all_attributes(self):
        """Test setting all attributes."""
        obj = CoreMixin()
        obj.set_id("new-id")
        obj.set_name("New Name")
        obj.set_description("New Description")
        self.assertEqual(obj.get_id(), "new-id")
        self.assertEqual(obj.get_name(), "New Name")
        self.assertEqual(obj.get_description(), "New Description")

    def test_properties_access(self):
        """Test property access."""
        obj = CoreMixin(
            id="prop-id",
            name="Prop Name",
            description="Prop Desc"
        )
        self.assertEqual(obj.id, "prop-id")
        self.assertEqual(obj.name, "Prop Name")
        self.assertEqual(obj.description, "Prop Desc")


class TestCoreRunnableMixin(unittest.TestCase):
    """Test cases for CoreRunnableMixin class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        obj = CoreRunnableMixin()
        self.assertEqual(obj.get_name(), "")
        self.assertEqual(obj.get_description(), "")
        self.assertFalse(obj.is_built())
        self.assertFalse(obj.is_running())

    def test_init_with_values(self):
        """Test initialization with provided values."""
        obj = CoreRunnableMixin(
            name="Runnable Name",
            description="Runnable Description"
        )
        self.assertEqual(obj.get_name(), "Runnable Name")
        self.assertEqual(obj.get_description(), "Runnable Description")

    def test_buildable_functionality(self):
        """Test Buildable functionality."""
        obj = CoreRunnableMixin()
        self.assertFalse(obj.is_built())
        obj.build()
        self.assertTrue(obj.is_built())
        obj.teardown()
        self.assertFalse(obj.is_built())

    def test_runnable_functionality(self):
        """Test Runnable functionality."""
        obj = CoreRunnableMixin()
        self.assertFalse(obj.is_running())
        result = obj.run()
        self.assertTrue(obj.is_running())
        self.assertEqual(result, 0)
        obj.stop()
        self.assertFalse(obj.is_running())

    def test_nameable_functionality(self):
        """Test Nameable functionality."""
        obj = CoreRunnableMixin()
        obj.set_name("Test Name")
        self.assertEqual(obj.get_name(), "Test Name")

    def test_describable_functionality(self):
        """Test Describable functionality."""
        obj = CoreRunnableMixin()
        obj.set_description("Test Description")
        self.assertEqual(obj.get_description(), "Test Description")

    def test_combined_lifecycle(self):
        """Test combined lifecycle operations."""
        obj = CoreRunnableMixin(name="Lifecycle Test")

        # Build
        obj.build()
        self.assertTrue(obj.is_built())

        # Run
        obj.run()
        self.assertTrue(obj.is_running())

        # Stop
        obj.stop()
        self.assertFalse(obj.is_running())

        # Teardown
        obj.teardown()
        self.assertFalse(obj.is_built())


class TestHasFileLocation(unittest.TestCase):
    """Test cases for HasFileLocation class."""

    def test_init_default_location(self):
        """Test initialization with default empty location."""
        obj = HasFileLocation()
        self.assertEqual(obj.get_file_location(), "")

    def test_init_with_location(self):
        """Test initialization with provided location."""
        obj = HasFileLocation(file_location="/path/to/file.txt")
        self.assertEqual(obj.get_file_location(), "/path/to/file.txt")

    def test_get_file_location(self):
        """Test getting the file location."""
        obj = HasFileLocation(file_location="C:\\Users\\test.py")
        result = obj.get_file_location()
        self.assertEqual(result, "C:\\Users\\test.py")
        self.assertIsInstance(result, str)

    def test_set_file_location(self):
        """Test setting the file location."""
        obj = HasFileLocation()
        obj.set_file_location("/new/path/file.py")
        self.assertEqual(obj.get_file_location(), "/new/path/file.py")

    def test_set_file_location_updates_existing(self):
        """Test setting location updates existing value."""
        obj = HasFileLocation(file_location="/old/path")
        obj.set_file_location("/new/path")
        self.assertEqual(obj.get_file_location(), "/new/path")

    def test_file_location_property(self):
        """Test file_location property access."""
        obj = HasFileLocation(file_location="/test/location")
        self.assertEqual(obj.file_location, "/test/location")


class TestHasMetaDictData(unittest.TestCase):
    """Test cases for HasMetaDictData class."""

    def test_init_default_metadata(self):
        """Test initialization with default empty metadata."""
        obj = HasMetaDictData()
        self.assertEqual(obj.get_metadata(), {})

    def test_init_with_metadata(self):
        """Test initialization with provided metadata."""
        metadata = {"key1": "value1", "key2": 42}
        obj = HasMetaDictData(meta_data=metadata)
        self.assertEqual(obj.get_metadata(), metadata)

    def test_get_metadata(self):
        """Test getting the metadata."""
        metadata = {"setting": "value"}
        obj = HasMetaDictData(meta_data=metadata)
        result = obj.get_metadata()
        self.assertEqual(result, metadata)
        self.assertIsInstance(result, dict)

    def test_set_metadata(self):
        """Test setting the metadata."""
        obj = HasMetaDictData()
        new_metadata = {"new_key": "new_value"}
        obj.set_metadata(new_metadata)
        self.assertEqual(obj.get_metadata(), new_metadata)

    def test_set_metadata_updates_existing(self):
        """Test setting metadata updates existing value."""
        obj = HasMetaDictData(meta_data={"old": "data"})
        new_metadata = {"new": "data"}
        obj.set_metadata(new_metadata)
        self.assertEqual(obj.get_metadata(), new_metadata)

    def test_metadata_property(self):
        """Test metadata property access."""
        metadata = {"test": "data"}
        obj = HasMetaDictData(meta_data=metadata)
        self.assertEqual(obj.metadata, metadata)

    def test_metadata_mutation(self):
        """Test that metadata dictionary can be mutated."""
        obj = HasMetaDictData()
        obj.get_metadata()["new_key"] = "new_value"
        self.assertEqual(obj.get_metadata()["new_key"], "new_value")


class TestSupportsItemAccess(unittest.TestCase):
    """Test cases for SupportsItemAccess class."""

    def test_init_default_metadata(self):
        """Test initialization with default empty metadata."""
        obj = SupportsItemAccess()
        self.assertEqual(obj.get_metadata(), {})

    def test_init_with_metadata(self):
        """Test initialization with provided metadata."""
        metadata = {"key1": "value1", "key2": 42}
        obj = SupportsItemAccess(meta_data=metadata)
        self.assertEqual(obj.get_metadata(), metadata)

    def test_getitem(self):
        """Test getting item by key using indexing."""
        metadata = {"name": "test", "count": 5}
        obj = SupportsItemAccess(meta_data=metadata)
        self.assertEqual(obj["name"], "test")
        self.assertEqual(obj["count"], 5)

    def test_setitem(self):
        """Test setting item by key using indexing."""
        obj = SupportsItemAccess()
        obj["key1"] = "value1"
        self.assertEqual(obj["key1"], "value1")
        self.assertEqual(obj.metadata["key1"], "value1")

    def test_setitem_updates_existing(self):
        """Test setting item updates existing value."""
        metadata = {"key": "old_value"}
        obj = SupportsItemAccess(meta_data=metadata)
        obj["key"] = "new_value"
        self.assertEqual(obj["key"], "new_value")

    def test_setitem_adds_new_key(self):
        """Test setting item adds new key."""
        obj = SupportsItemAccess(meta_data={"existing": "value"})
        obj["new_key"] = "new_value"
        self.assertEqual(obj["new_key"], "new_value")
        self.assertIn("existing", obj.metadata)
        self.assertIn("new_key", obj.metadata)

    def test_mixed_item_access(self):
        """Test mixed get/set item access."""
        obj = SupportsItemAccess()
        obj["key1"] = 100
        obj["key2"] = "text"
        obj["key3"] = [1, 2, 3]

        self.assertEqual(obj["key1"], 100)
        self.assertEqual(obj["key2"], "text")
        self.assertEqual(obj["key3"], [1, 2, 3])

    def test_getitem_nonexistent_key_raises(self):
        """Test getting nonexistent key raises KeyError."""
        obj = SupportsItemAccess()
        with self.assertRaises(KeyError):
            _ = obj["nonexistent"]

    def test_inheritance_from_has_meta_dict_data(self):
        """Test that SupportsItemAccess inherits from HasMetaDictData."""
        obj = SupportsItemAccess()
        self.assertIsInstance(obj, HasMetaDictData)
        self.assertTrue(hasattr(obj, 'get_metadata'))
        self.assertTrue(hasattr(obj, 'set_metadata'))


if __name__ == '__main__':
    unittest.main()

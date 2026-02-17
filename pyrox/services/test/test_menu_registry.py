"""Unit tests for menu_registry.py module."""

import unittest
from unittest.mock import Mock, MagicMock

from pyrox.services.menu_registry import MenuItemDescriptor, MenuRegistry


class TestMenuItemDescriptor(unittest.TestCase):
    """Test cases for MenuItemDescriptor dataclass."""

    def test_descriptor_creation(self):
        """Test creating a menu item descriptor."""
        mock_menu = Mock()
        callback = Mock()

        descriptor = MenuItemDescriptor(
            menu_id="test.item",
            menu_path="Test/Item",
            menu_widget=mock_menu,
            menu_index=0,
            owner="TestOwner",
            command=callback,
            enabled=True,
            metadata={"key": "value"}
        )

        self.assertEqual(descriptor.menu_id, "test.item")
        self.assertEqual(descriptor.menu_path, "Test/Item")
        self.assertEqual(descriptor.menu_widget, mock_menu)
        self.assertEqual(descriptor.menu_index, 0)
        self.assertEqual(descriptor.owner, "TestOwner")
        self.assertEqual(descriptor.command, callback)
        self.assertTrue(descriptor.enabled)
        self.assertEqual(descriptor.metadata, {"key": "value"})

    def test_descriptor_default_values(self):
        """Test descriptor creation with default values."""
        mock_menu = Mock()

        descriptor = MenuItemDescriptor(
            menu_id="test.item",
            menu_path="Test/Item",
            menu_widget=mock_menu,
            menu_index=0,
            owner="TestOwner"
        )

        self.assertIsNone(descriptor.command)
        self.assertTrue(descriptor.enabled)
        self.assertEqual(descriptor.metadata, {})


class TestMenuRegistry(unittest.TestCase):
    """Test cases for MenuRegistry class."""

    def setUp(self):
        """Set up test fixtures."""
        MenuRegistry.clear()
        self.mock_menu = MagicMock()
        self.mock_callback = Mock()

    def tearDown(self):
        """Clean up after tests."""
        MenuRegistry.clear()

    def test_register_item(self):
        """Test registering a menu item."""
        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask",
            command=self.mock_callback
        )

        descriptor = MenuRegistry.get_item("file.save")
        self.assertIsNotNone(descriptor)
        self.assertEqual(descriptor.menu_id, "file.save")  # type: ignore
        self.assertEqual(descriptor.menu_path, "File/Save")  # type: ignore
        self.assertEqual(descriptor.menu_widget, self.mock_menu)  # type: ignore
        self.assertEqual(descriptor.menu_index, 0)  # type: ignore
        self.assertEqual(descriptor.owner, "TestTask")  # type: ignore
        self.assertEqual(descriptor.command, self.mock_callback)  # type: ignore
        self.assertTrue(descriptor.enabled)  # type: ignore

    def test_register_item_with_metadata(self):
        """Test registering a menu item with additional metadata."""
        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask",
            shortcut="Ctrl+S",
            accelerator="Ctrl+S"
        )

        descriptor = MenuRegistry.get_item("file.save")
        self.assertEqual(descriptor.metadata["shortcut"], "Ctrl+S")  # type: ignore
        self.assertEqual(descriptor.metadata["accelerator"], "Ctrl+S")  # type: ignore

    def test_register_multiple_items(self):
        """Test registering multiple menu items."""
        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        MenuRegistry.register_item(
            menu_id="file.open",
            menu_path="File/Open",
            menu_widget=self.mock_menu,
            menu_index=1,
            owner="TestTask"
        )

        self.assertEqual(len(MenuRegistry.get_all_items()), 2)
        self.assertIsNotNone(MenuRegistry.get_item("file.save"))
        self.assertIsNotNone(MenuRegistry.get_item("file.open"))

    def test_unregister_item(self):
        """Test unregistering a menu item."""
        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        self.assertIsNotNone(MenuRegistry.get_item("file.save"))

        MenuRegistry.unregister_item("file.save")

        self.assertIsNone(MenuRegistry.get_item("file.save"))
        self.assertEqual(len(MenuRegistry.get_all_items()), 0)

    def test_unregister_nonexistent_item(self):
        """Test unregistering a non-existent menu item (should not raise error)."""
        MenuRegistry.unregister_item("nonexistent.item")
        # Should complete without error

    def test_get_item_not_found(self):
        """Test getting a menu item that doesn't exist."""
        result = MenuRegistry.get_item("nonexistent.item")
        self.assertIsNone(result)

    def test_enable_item(self):
        """Test enabling a menu item."""
        self.mock_menu.type.return_value = "command"

        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        result = MenuRegistry.enable_item("file.save")

        self.assertTrue(result)
        self.mock_menu.entryconfig.assert_called_with(0, state='normal')
        descriptor = MenuRegistry.get_item("file.save")
        self.assertTrue(descriptor.enabled)  # type: ignore

    def test_enable_item_not_found(self):
        """Test enabling a non-existent menu item."""
        result = MenuRegistry.enable_item("nonexistent.item")
        self.assertFalse(result)

    def test_enable_item_separator(self):
        """Test enabling a separator (should be skipped and return False)."""
        self.mock_menu.type.return_value = "separator"

        MenuRegistry.register_item(
            menu_id="separator.1",
            menu_path="File/-",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        result = MenuRegistry.enable_item("separator.1")

        # Separator items return False since they can't be enabled
        self.assertFalse(result)
        # entryconfig should not be called for separators
        self.mock_menu.entryconfig.assert_not_called()

    def test_enable_item_with_exception(self):
        """Test enabling a menu item that raises an exception."""
        self.mock_menu.type.side_effect = Exception("Test error")

        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        result = MenuRegistry.enable_item("file.save")

        self.assertFalse(result)

    def test_disable_item(self):
        """Test disabling a menu item."""
        self.mock_menu.type.return_value = "command"

        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        result = MenuRegistry.disable_item("file.save")

        self.assertTrue(result)
        self.mock_menu.entryconfig.assert_called_with(0, state='disabled')
        descriptor = MenuRegistry.get_item("file.save")
        self.assertFalse(descriptor.enabled)  # type: ignore

    def test_disable_item_not_found(self):
        """Test disabling a non-existent menu item."""
        result = MenuRegistry.disable_item("nonexistent.item")
        self.assertFalse(result)

    def test_disable_item_separator(self):
        """Test disabling a separator (should be skipped and return False)."""
        self.mock_menu.type.return_value = "separator"

        MenuRegistry.register_item(
            menu_id="separator.1",
            menu_path="File/-",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        result = MenuRegistry.disable_item("separator.1")

        # Separator items return False since they can't be disabled
        self.assertFalse(result)
        # entryconfig should not be called for separators
        self.mock_menu.entryconfig.assert_not_called()

    def test_disable_item_with_exception(self):
        """Test disabling a menu item that raises an exception."""
        self.mock_menu.type.side_effect = Exception("Test error")

        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        result = MenuRegistry.disable_item("file.save")

        self.assertFalse(result)

    def test_set_command(self):
        """Test setting a command for a menu item."""
        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        new_callback = Mock()
        result = MenuRegistry.set_command("file.save", new_callback)

        self.assertTrue(result)
        self.mock_menu.entryconfig.assert_called_with(0, command=new_callback)
        descriptor = MenuRegistry.get_item("file.save")
        self.assertEqual(descriptor.command, new_callback)  # type: ignore

    def test_set_command_not_found(self):
        """Test setting command for a non-existent menu item."""
        result = MenuRegistry.set_command("nonexistent.item", Mock())
        self.assertFalse(result)

    def test_set_command_with_exception(self):
        """Test setting a command that raises an exception."""
        self.mock_menu.entryconfig.side_effect = Exception("Test error")

        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        result = MenuRegistry.set_command("file.save", Mock())

        self.assertFalse(result)

    def test_enable_items_by_owner(self):
        """Test enabling all items owned by a specific component."""
        self.mock_menu.type.return_value = "command"

        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        MenuRegistry.register_item(
            menu_id="file.open",
            menu_path="File/Open",
            menu_widget=self.mock_menu,
            menu_index=1,
            owner="TestTask"
        )

        MenuRegistry.register_item(
            menu_id="edit.copy",
            menu_path="Edit/Copy",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="OtherTask"
        )

        count = MenuRegistry.enable_items_by_owner("TestTask")

        self.assertEqual(count, 2)
        self.assertEqual(self.mock_menu.entryconfig.call_count, 2)

    def test_enable_items_by_owner_no_items(self):
        """Test enabling items for an owner with no registered items."""
        count = MenuRegistry.enable_items_by_owner("NonexistentOwner")
        self.assertEqual(count, 0)

    def test_disable_items_by_owner(self):
        """Test disabling all items owned by a specific component."""
        self.mock_menu.type.return_value = "command"

        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        MenuRegistry.register_item(
            menu_id="file.open",
            menu_path="File/Open",
            menu_widget=self.mock_menu,
            menu_index=1,
            owner="TestTask"
        )

        MenuRegistry.register_item(
            menu_id="edit.copy",
            menu_path="Edit/Copy",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="OtherTask"
        )

        count = MenuRegistry.disable_items_by_owner("TestTask")

        self.assertEqual(count, 2)
        self.assertEqual(self.mock_menu.entryconfig.call_count, 2)

    def test_disable_items_by_owner_no_items(self):
        """Test disabling items for an owner with no registered items."""
        count = MenuRegistry.disable_items_by_owner("NonexistentOwner")
        self.assertEqual(count, 0)

    def test_get_items_by_owner(self):
        """Test getting all items owned by a specific component."""
        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        MenuRegistry.register_item(
            menu_id="file.open",
            menu_path="File/Open",
            menu_widget=self.mock_menu,
            menu_index=1,
            owner="TestTask"
        )

        MenuRegistry.register_item(
            menu_id="edit.copy",
            menu_path="Edit/Copy",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="OtherTask"
        )

        items = MenuRegistry.get_items_by_owner("TestTask")

        self.assertEqual(len(items), 2)
        self.assertIn(items[0].menu_id, ["file.save", "file.open"])
        self.assertIn(items[1].menu_id, ["file.save", "file.open"])

    def test_get_items_by_owner_no_items(self):
        """Test getting items for an owner with no registered items."""
        items = MenuRegistry.get_items_by_owner("NonexistentOwner")
        self.assertEqual(len(items), 0)

    def test_clear(self):
        """Test clearing the entire registry."""
        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        MenuRegistry.register_item(
            menu_id="file.open",
            menu_path="File/Open",
            menu_widget=self.mock_menu,
            menu_index=1,
            owner="TestTask"
        )

        self.assertEqual(len(MenuRegistry.get_all_items()), 2)

        MenuRegistry.clear()

        self.assertEqual(len(MenuRegistry.get_all_items()), 0)
        self.assertEqual(len(MenuRegistry._owner_index), 0)

    def test_get_all_items(self):
        """Test getting all registered menu items."""
        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        MenuRegistry.register_item(
            menu_id="file.open",
            menu_path="File/Open",
            menu_widget=self.mock_menu,
            menu_index=1,
            owner="TestTask"
        )

        all_items = MenuRegistry.get_all_items()

        self.assertEqual(len(all_items), 2)
        self.assertIn("file.save", all_items)
        self.assertIn("file.open", all_items)
        self.assertIsInstance(all_items, dict)

    def test_get_all_items_returns_copy(self):
        """Test that get_all_items returns a copy, not the original registry."""
        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        all_items = MenuRegistry.get_all_items()
        all_items["fake.item"] = None  # type: ignore

        # Original registry should not be modified
        self.assertNotIn("fake.item", MenuRegistry._registry)

    def test_owner_index_updates(self):
        """Test that owner index is properly maintained."""
        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        self.assertIn("TestTask", MenuRegistry._owner_index)
        self.assertIn("file.save", MenuRegistry._owner_index["TestTask"])

        MenuRegistry.unregister_item("file.save")

        self.assertNotIn("TestTask", MenuRegistry._owner_index)

    def test_multiple_items_same_owner(self):
        """Test registering multiple items with the same owner."""
        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        MenuRegistry.register_item(
            menu_id="file.open",
            menu_path="File/Open",
            menu_widget=self.mock_menu,
            menu_index=1,
            owner="TestTask"
        )

        MenuRegistry.register_item(
            menu_id="file.close",
            menu_path="File/Close",
            menu_widget=self.mock_menu,
            menu_index=2,
            owner="TestTask"
        )

        self.assertEqual(len(MenuRegistry._owner_index["TestTask"]), 3)
        self.assertEqual(len(MenuRegistry.get_items_by_owner("TestTask")), 3)

    def test_unregister_preserves_other_owner_items(self):
        """Test that unregistering an item doesn't affect other owner's items."""
        MenuRegistry.register_item(
            menu_id="file.save",
            menu_path="File/Save",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
        )

        MenuRegistry.register_item(
            menu_id="file.open",
            menu_path="File/Open",
            menu_widget=self.mock_menu,
            menu_index=1,
            owner="TestTask"
        )

        MenuRegistry.unregister_item("file.save")

        # TestTask should still have one item
        self.assertIn("TestTask", MenuRegistry._owner_index)
        self.assertEqual(len(MenuRegistry._owner_index["TestTask"]), 1)
        self.assertIn("file.open", MenuRegistry._owner_index["TestTask"])

    def test_enable_item_with_category_match(self):
        """Test enabling a menu item with matching category."""
        self.mock_menu.type.return_value = "command"

        MenuRegistry.register_item(
            menu_id="view.properties",
            menu_path="View/Properties",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask",
            category="scene"
        )

        result = MenuRegistry.enable_item("view.properties", category="scene")

        self.assertTrue(result)
        self.mock_menu.entryconfig.assert_called_with(0, state='normal')
        descriptor = MenuRegistry.get_item("view.properties")
        self.assertTrue(descriptor.enabled)  # type: ignore

    def test_enable_item_with_category_mismatch(self):
        """Test enabling a menu item with non-matching category."""
        self.mock_menu.type.return_value = "command"

        MenuRegistry.register_item(
            menu_id="view.properties",
            menu_path="View/Properties",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask",
            category="scene"
        )

        result = MenuRegistry.enable_item("view.properties", category="different")

        self.assertFalse(result)
        self.mock_menu.entryconfig.assert_not_called()

    def test_enable_item_with_subcategory_match(self):
        """Test enabling a menu item with matching subcategory."""
        self.mock_menu.type.return_value = "command"

        MenuRegistry.register_item(
            menu_id="view.properties",
            menu_path="View/Properties",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask",
            subcategory="panel"
        )

        result = MenuRegistry.enable_item("view.properties", subcategory="panel")

        self.assertTrue(result)
        self.mock_menu.entryconfig.assert_called_with(0, state='normal')
        descriptor = MenuRegistry.get_item("view.properties")
        self.assertTrue(descriptor.enabled)  # type: ignore

    def test_enable_item_with_subcategory_mismatch(self):
        """Test enabling a menu item with non-matching subcategory."""
        self.mock_menu.type.return_value = "command"

        MenuRegistry.register_item(
            menu_id="view.properties",
            menu_path="View/Properties",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask",
            subcategory="panel"
        )

        result = MenuRegistry.enable_item("view.properties", subcategory="different")

        self.assertFalse(result)
        self.mock_menu.entryconfig.assert_not_called()

    def test_enable_item_with_both_category_and_subcategory_match(self):
        """Test enabling a menu item with both category and subcategory matching."""
        self.mock_menu.type.return_value = "command"

        MenuRegistry.register_item(
            menu_id="view.properties",
            menu_path="View/Properties",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask",
            category="scene",
            subcategory="panel"
        )

        result = MenuRegistry.enable_item(
            "view.properties",
            category="scene",
            subcategory="panel"
        )

        self.assertTrue(result)
        self.mock_menu.entryconfig.assert_called_with(0, state='normal')
        descriptor = MenuRegistry.get_item("view.properties")
        self.assertTrue(descriptor.enabled)  # type: ignore

    def test_enable_item_with_category_match_subcategory_mismatch(self):
        """Test enabling with matching category but mismatched subcategory."""
        self.mock_menu.type.return_value = "command"

        MenuRegistry.register_item(
            menu_id="view.properties",
            menu_path="View/Properties",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask",
            category="scene",
            subcategory="panel"
        )

        result = MenuRegistry.enable_item(
            "view.properties",
            category="scene",
            subcategory="different"
        )

        self.assertFalse(result)
        self.mock_menu.entryconfig.assert_not_called()

    def test_enable_item_without_category_filter(self):
        """Test enabling item with metadata but no category filter."""
        self.mock_menu.type.return_value = "command"

        MenuRegistry.register_item(
            menu_id="view.properties",
            menu_path="View/Properties",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask",
            category="scene"
        )

        result = MenuRegistry.enable_item("view.properties")

        self.assertTrue(result)
        self.mock_menu.entryconfig.assert_called_with(0, state='normal')

    def test_enable_items_by_owner_with_category(self):
        """Test enabling items by owner with category filter."""
        self.mock_menu.type.return_value = "command"

        MenuRegistry.register_item(
            menu_id="view.properties",
            menu_path="View/Properties",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask",
            category="scene"
        )

        MenuRegistry.register_item(
            menu_id="view.settings",
            menu_path="View/Settings",
            menu_widget=self.mock_menu,
            menu_index=1,
            owner="TestTask",
            category="config"
        )

        MenuRegistry.register_item(
            menu_id="view.details",
            menu_path="View/Details",
            menu_widget=self.mock_menu,
            menu_index=2,
            owner="TestTask",
            category="scene"
        )

        count = MenuRegistry.enable_items_by_owner("TestTask", category="scene")

        self.assertEqual(count, 2)
        # Only the two items with category="scene" should be enabled
        self.assertEqual(self.mock_menu.entryconfig.call_count, 2)

    def test_enable_items_by_owner_with_subcategory(self):
        """Test enabling items by owner with subcategory filter."""
        self.mock_menu.type.return_value = "command"

        MenuRegistry.register_item(
            menu_id="view.properties",
            menu_path="View/Properties",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask",
            subcategory="panel"
        )

        MenuRegistry.register_item(
            menu_id="view.settings",
            menu_path="View/Settings",
            menu_widget=self.mock_menu,
            menu_index=1,
            owner="TestTask",
            subcategory="dialog"
        )

        MenuRegistry.register_item(
            menu_id="view.details",
            menu_path="View/Details",
            menu_widget=self.mock_menu,
            menu_index=2,
            owner="TestTask",
            subcategory="panel"
        )

        count = MenuRegistry.enable_items_by_owner("TestTask", subcategory="panel")

        self.assertEqual(count, 2)
        # Only the two items with subcategory="panel" should be enabled
        self.assertEqual(self.mock_menu.entryconfig.call_count, 2)

    def test_enable_items_by_owner_with_both_filters(self):
        """Test enabling items by owner with both category and subcategory filters."""
        self.mock_menu.type.return_value = "command"

        MenuRegistry.register_item(
            menu_id="view.properties",
            menu_path="View/Properties",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask",
            category="scene",
            subcategory="panel"
        )

        MenuRegistry.register_item(
            menu_id="view.settings",
            menu_path="View/Settings",
            menu_widget=self.mock_menu,
            menu_index=1,
            owner="TestTask",
            category="scene",
            subcategory="dialog"
        )

        MenuRegistry.register_item(
            menu_id="view.details",
            menu_path="View/Details",
            menu_widget=self.mock_menu,
            menu_index=2,
            owner="TestTask",
            category="config",
            subcategory="panel"
        )

        MenuRegistry.register_item(
            menu_id="view.info",
            menu_path="View/Info",
            menu_widget=self.mock_menu,
            menu_index=3,
            owner="TestTask",
            category="scene",
            subcategory="panel"
        )

        count = MenuRegistry.enable_items_by_owner(
            "TestTask",
            category="scene",
            subcategory="panel"
        )

        self.assertEqual(count, 2)
        # Only items with both category="scene" AND subcategory="panel"
        self.assertEqual(self.mock_menu.entryconfig.call_count, 2)

    def test_enable_items_by_owner_no_match_for_filters(self):
        """Test enabling items by owner when no items match the filters."""
        self.mock_menu.type.return_value = "command"

        MenuRegistry.register_item(
            menu_id="view.properties",
            menu_path="View/Properties",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask",
            category="scene"
        )

        MenuRegistry.register_item(
            menu_id="view.settings",
            menu_path="View/Settings",
            menu_widget=self.mock_menu,
            menu_index=1,
            owner="TestTask",
            category="config"
        )

        count = MenuRegistry.enable_items_by_owner("TestTask", category="nonexistent")

        self.assertEqual(count, 0)
        self.mock_menu.entryconfig.assert_not_called()

    def test_enable_items_by_owner_without_filters(self):
        """Test enabling items by owner without any filters (original behavior)."""
        self.mock_menu.type.return_value = "command"

        MenuRegistry.register_item(
            menu_id="view.properties",
            menu_path="View/Properties",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask",
            category="scene"
        )

        MenuRegistry.register_item(
            menu_id="view.settings",
            menu_path="View/Settings",
            menu_widget=self.mock_menu,
            menu_index=1,
            owner="TestTask",
            category="config"
        )

        count = MenuRegistry.enable_items_by_owner("TestTask")

        self.assertEqual(count, 2)
        # All items should be enabled regardless of category
        self.assertEqual(self.mock_menu.entryconfig.call_count, 2)

    def test_category_filter_with_missing_metadata(self):
        """Test category filter on items without category metadata."""
        self.mock_menu.type.return_value = "command"

        MenuRegistry.register_item(
            menu_id="view.properties",
            menu_path="View/Properties",
            menu_widget=self.mock_menu,
            menu_index=0,
            owner="TestTask"
            # No category metadata
        )

        result = MenuRegistry.enable_item("view.properties", category="scene")

        self.assertFalse(result)
        self.mock_menu.entryconfig.assert_not_called()


if __name__ == '__main__':
    unittest.main()

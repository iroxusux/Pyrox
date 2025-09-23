"""Test suite for dictionary services."""
from pyrox.services.dict import (
    insert_key_at_index,
    key_index,
    remove_none_values_inplace,
    rename_keys,
)


class TestDictServices:
    """Test class for dictionary services."""

    def test_insert_key_at_index_beginning(self):
        """Test inserting key at the beginning of dictionary."""
        d = {"b": 2, "c": 3}
        insert_key_at_index(d, "a", 0, 1)

        keys = list(d.keys())
        assert keys[0] == "a"
        assert d["a"] == 1
        assert len(d) == 3

    def test_insert_key_at_index_middle(self):
        """Test inserting key in the middle of dictionary."""
        d = {"a": 1, "c": 3}
        insert_key_at_index(d, "b", 1, 2)

        keys = list(d.keys())
        assert keys == ["a", "b", "c"]
        assert d["b"] == 2

    def test_insert_key_at_index_end(self):
        """Test inserting key at the end of dictionary."""
        d = {"a": 1, "b": 2}
        insert_key_at_index(d, "c", 2, 3)

        keys = list(d.keys())
        assert keys[-1] == "c"
        assert d["c"] == 3

    def test_insert_key_at_index_empty_dict(self):
        """Test inserting key into empty dictionary."""
        d = {}
        insert_key_at_index(d, "a", 0, 1)

        assert len(d) == 1
        assert d["a"] == 1

    def test_insert_key_at_index_default_value(self):
        """Test inserting key with default None value."""
        d = {"a": 1}
        insert_key_at_index(d, "b", 1)

        assert d["b"] is None

    def test_insert_key_at_index_negative_index(self):
        """Test inserting key with negative index."""
        d = {"a": 1, "b": 2, "c": 3}
        insert_key_at_index(d, "d", -1, 4)

        keys = list(d.keys())
        assert "d" in keys

    def test_insert_key_at_index_out_of_bounds(self):
        """Test inserting key with index beyond length."""
        d = {"a": 1}
        insert_key_at_index(d, "b", 10, 2)

        keys = list(d.keys())
        assert "b" in keys

    def test_insert_key_at_index_existing_key(self):
        """Test inserting existing key updates value and position."""
        d = {"a": 1, "b": 2, "c": 3}
        original_id = id(d)
        insert_key_at_index(d, "a", 2, 10)

        assert id(d) == original_id  # Same object
        assert d["a"] == 10
        keys = list(d.keys())
        assert keys.index("a") == 2

    def test_key_index_existing_key(self):
        """Test finding index of existing key."""
        d = {"a": 1, "b": 2, "c": 3}

        assert key_index(d, "a") == 0
        assert key_index(d, "b") == 1
        assert key_index(d, "c") == 2

    def test_key_index_non_existing_key(self):
        """Test finding index of non-existing key returns -1."""
        d = {"a": 1, "b": 2}

        assert key_index(d, "z") == -1
        assert key_index(d, "missing") == -1

    def test_key_index_empty_dict(self):
        """Test finding index in empty dictionary."""
        d = {}

        assert key_index(d, "a") == -1

    def test_remove_none_values_inplace_simple(self):
        """Test removing None values from simple dictionary."""
        d = {"a": 1, "b": None, "c": 3}
        original_id = id(d)

        remove_none_values_inplace(d)

        assert id(d) == original_id  # Same object
        assert "b" not in d
        assert d == {"a": 1, "c": 3}

    def test_remove_none_values_inplace_nested_dict(self):
        """Test removing None values from nested dictionaries."""
        d = {
            "a": 1,
            "b": None,
            "c": {
                "d": 2,
                "e": None,
                "f": {"g": None, "h": 3}
            }
        }

        remove_none_values_inplace(d)

        expected = {
            "a": 1,
            "c": {
                "d": 2,
                "f": {"h": 3}
            }
        }
        assert d == expected

    def test_remove_none_values_inplace_list_with_dicts(self):
        """Test removing None values from dictionaries within lists."""
        d = {
            "a": 1,
            "b": [
                {"c": 2, "d": None},
                {"e": None, "f": 3},
                "string_item",
                {"g": None}
            ]
        }

        remove_none_values_inplace(d)

        expected = {
            "a": 1,
            "b": [
                {"c": 2},
                {"f": 3},
                "string_item",
                {}
            ]
        }
        assert d == expected

    def test_remove_none_values_inplace_all_none(self):
        """Test removing None values when all values are None."""
        d = {"a": None, "b": None, "c": None}

        remove_none_values_inplace(d)

        assert d == {}

    def test_remove_none_values_inplace_no_none_values(self):
        """Test removing None values when no None values exist."""
        d = {"a": 1, "b": 2, "c": {"d": 3, "e": [{"f": 4}]}}
        original = d.copy()

        remove_none_values_inplace(d)

        assert d == original

    def test_remove_none_values_inplace_empty_dict(self):
        """Test removing None values from empty dictionary."""
        d = {}

        remove_none_values_inplace(d)

        assert d == {}

    def test_remove_none_values_inplace_complex_nesting(self):
        """Test removing None values from complex nested structure."""
        d = {
            "level1": {
                "level2": {
                    "level3": None,
                    "keep": "value"
                },
                "list": [
                    {"item1": None, "item2": "keep"},
                    {"item3": None}
                ],
                "remove": None
            },
            "keep_top": "value"
        }

        remove_none_values_inplace(d)

        expected = {
            "level1": {
                "level2": {
                    "keep": "value"
                },
                "list": [
                    {"item2": "keep"},
                    {}
                ]
            },
            "keep_top": "value"
        }
        assert d == expected

    def test_rename_keys_simple(self):
        """Test renaming keys in simple dictionary."""
        d = {"old_key1": 1, "old_key2": 2, "keep": 3}
        key_map = {"old_key1": "new_key1", "old_key2": "new_key2"}

        rename_keys(d, key_map)

        expected = {"new_key1": 1, "new_key2": 2, "keep": 3}
        assert d == expected

    def test_rename_keys_nested_dict(self):
        """Test renaming keys in nested dictionaries."""
        d = {
            "old_key1": 1,
            "nested": {
                "old_key2": 2,
                "old_key1": 3
            }
        }
        key_map = {"old_key1": "new_key1", "old_key2": "new_key2"}

        rename_keys(d, key_map)

        expected = {
            "new_key1": 1,
            "nested": {
                "new_key2": 2,
                "new_key1": 3
            }
        }
        assert d == expected

    def test_rename_keys_list_with_dicts(self):
        """Test renaming keys in dictionaries within lists."""
        d = {
            "list_data": [
                {"old_key": "value1"},
                {"old_key": "value2", "other": "keep"},
                "string_item"
            ]
        }
        key_map = {"old_key": "new_key"}

        rename_keys(d, key_map)

        expected = {
            "list_data": [
                {"new_key": "value1"},
                {"new_key": "value2", "other": "keep"},
                "string_item"
            ]
        }
        assert d == expected

    def test_rename_keys_non_existing_keys(self):
        """Test renaming keys that don't exist in dictionary."""
        d = {"existing": 1, "other": 2}
        original = d.copy()
        key_map = {"non_existing": "new_name"}

        rename_keys(d, key_map)

        assert d == original  # No changes

    def test_rename_keys_empty_dict(self):
        """Test renaming keys in empty dictionary."""
        d = {}
        key_map = {"old": "new"}

        rename_keys(d, key_map)

        assert d == {}

    def test_rename_keys_empty_key_map(self):
        """Test renaming keys with empty key map."""
        d = {"key1": 1, "key2": 2}
        original = d.copy()
        key_map = {}

        rename_keys(d, key_map)

        assert d == original

    def test_rename_keys_non_dict_input(self):
        """Test rename_keys with non-dictionary input."""
        non_dict = "not a dict"
        key_map = {"old": "new"}

        # Should not raise an error, just return early
        rename_keys(non_dict, key_map)

        assert non_dict == "not a dict"  # Unchanged

    def test_rename_keys_complex_nesting(self):
        """Test renaming keys in complex nested structure."""
        d = {
            "old_root": {
                "old_nested": {
                    "old_deep": "value1"
                },
                "list_with_dicts": [
                    {"old_item": "value2"},
                    {"old_nested": "value3", "old_item": "value4"}
                ]
            },
            "old_simple": "value5"
        }
        key_map = {
            "old_root": "new_root",
            "old_nested": "new_nested",
            "old_deep": "new_deep",
            "old_item": "new_item",
            "old_simple": "new_simple"
        }

        rename_keys(d, key_map)

        expected = {
            "new_root": {
                "new_nested": {
                    "new_deep": "value1"
                },
                "list_with_dicts": [
                    {"new_item": "value2"},
                    {"new_nested": "value3", "new_item": "value4"}
                ]
            },
            "new_simple": "value5"
        }
        assert d == expected

    def test_rename_keys_overwrites_existing(self):
        """Test that renaming can overwrite existing keys."""
        d = {"old_key": "old_value", "new_key": "existing_value"}
        key_map = {"old_key": "new_key"}

        rename_keys(d, key_map)

        # The renamed key should overwrite the existing one
        assert d == {"new_key": "old_value"}
        assert "old_key" not in d

    def test_rename_keys_circular_rename(self):
        """Test renaming keys in a circular fashion."""
        d = {"a": 1, "b": 2}
        key_map = {"a": "c", "b": "d"}

        rename_keys(d, key_map)

        # Due to the order of operations, this might not work as expected
        # The test documents the current behavior
        assert len(d) == 2
        assert 1 in d.values()
        assert 2 in d.values()

    def test_rename_keys_preserves_order(self):
        """Test that renaming keys preserves dictionary order."""
        d = {"first": 1, "second": 2, "third": 3}
        key_map = {"second": "middle"}

        rename_keys(d, key_map)

        keys = list(d.keys())
        assert keys == ["first", "middle", "third"]

    def test_rename_keys_with_none_values(self):
        """Test renaming keys when values are None."""
        d = {"old_key": None, "other": "value"}
        key_map = {"old_key": "new_key"}

        rename_keys(d, key_map)

        expected = {"new_key": None, "other": "value"}
        assert d == expected

    def test_all_functions_preserve_object_identity(self):
        """Test that all in-place functions preserve object identity."""
        d = {"a": 1, "b": None, "c": {"old": "value"}}
        original_id = id(d)

        # Test insert_key_at_index
        insert_key_at_index(d, "new", 1, "value")
        assert id(d) == original_id

        # Test remove_none_values_inplace
        remove_none_values_inplace(d)
        assert id(d) == original_id

        # Test rename_keys
        rename_keys(d, {"old": "new_name"})
        assert id(d) == original_id

    def test_edge_case_mixed_data_types(self):
        """Test functions with mixed data types in dictionary."""
        d = {
            "string_key": "string_value",
            1: "numeric_key",
            "list": [1, 2, {"nested": None}],
            "tuple": (1, 2, 3),
            "none": None,
            "bool": True
        }

        # Test remove_none_values_inplace
        remove_none_values_inplace(d)
        assert "none" not in d
        assert d["list"][2] == {}  # nested None removed

        # Test rename_keys with numeric keys
        key_map = {1: "one", "string_key": "str_key"}
        rename_keys(d, key_map)
        assert "one" in d
        assert "str_key" in d
        assert 1 not in d
        assert "string_key" not in d

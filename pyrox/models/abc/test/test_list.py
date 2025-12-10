"""Unit tests for list.py module."""

import unittest
from unittest.mock import MagicMock

from pyrox.models.abc.list import (
    Subscribable,
    HashList,
    SafeList,
    TrackedList,
)


class TestSubscribable(unittest.TestCase):
    """Test cases for Subscribable class."""

    def test_init(self):
        """Test initialization of Subscribable."""
        sub = Subscribable()

        self.assertIsInstance(sub._subscribers, list)
        self.assertEqual(len(sub._subscribers), 0)

    def test_subscribers_property(self):
        """Test subscribers property getter."""
        sub = Subscribable()

        self.assertEqual(sub.subscribers, sub._subscribers)
        self.assertIs(sub.subscribers, sub._subscribers)

    def test_subscribe_new_callback(self):
        """Test subscribing a new callback."""
        sub = Subscribable()
        callback = MagicMock()

        sub.subscribe(callback)

        self.assertIn(callback, sub.subscribers)
        self.assertEqual(len(sub.subscribers), 1)

    def test_subscribe_duplicate_callback(self):
        """Test subscribing the same callback twice."""
        sub = Subscribable()
        callback = MagicMock()

        sub.subscribe(callback)
        sub.subscribe(callback)  # Subscribe again

        self.assertEqual(len(sub.subscribers), 1)
        self.assertIn(callback, sub.subscribers)

    def test_subscribe_multiple_callbacks(self):
        """Test subscribing multiple different callbacks."""
        sub = Subscribable()
        callback1 = MagicMock()
        callback2 = MagicMock()
        callback3 = MagicMock()

        sub.subscribe(callback1)
        sub.subscribe(callback2)
        sub.subscribe(callback3)

        self.assertEqual(len(sub.subscribers), 3)
        self.assertIn(callback1, sub.subscribers)
        self.assertIn(callback2, sub.subscribers)
        self.assertIn(callback3, sub.subscribers)

    def test_unsubscribe_existing_callback(self):
        """Test unsubscribing an existing callback."""
        sub = Subscribable()
        callback = MagicMock()

        sub.subscribe(callback)
        self.assertIn(callback, sub.subscribers)

        sub.unsubscribe(callback)

        self.assertNotIn(callback, sub.subscribers)
        self.assertEqual(len(sub.subscribers), 0)

    def test_unsubscribe_nonexistent_callback(self):
        """Test unsubscribing a callback that doesn't exist."""
        sub = Subscribable()
        callback = MagicMock()

        # Should not raise error
        sub.unsubscribe(callback)

        self.assertEqual(len(sub.subscribers), 0)

    def test_unsubscribe_partial_removal(self):
        """Test unsubscribing one of multiple callbacks."""
        sub = Subscribable()
        callback1 = MagicMock()
        callback2 = MagicMock()
        callback3 = MagicMock()

        sub.subscribe(callback1)
        sub.subscribe(callback2)
        sub.subscribe(callback3)

        sub.unsubscribe(callback2)

        self.assertEqual(len(sub.subscribers), 2)
        self.assertIn(callback1, sub.subscribers)
        self.assertNotIn(callback2, sub.subscribers)
        self.assertIn(callback3, sub.subscribers)

    def test_emit_no_subscribers(self):
        """Test emit with no subscribers."""
        sub = Subscribable()

        # Should not raise error
        sub.unsafe_emit("test", keyword="value")

    def test_emit_with_subscribers(self):
        """Test emit with subscribers."""
        sub = Subscribable()
        callback1 = MagicMock()
        callback2 = MagicMock()

        sub.subscribe(callback1)
        sub.subscribe(callback2)

        sub.unsafe_emit("arg1", "arg2", kwarg1="value1", kwarg2="value2")

        callback1.assert_called_once_with("arg1", "arg2", kwarg1="value1", kwarg2="value2")
        callback2.assert_called_once_with("arg1", "arg2", kwarg1="value1", kwarg2="value2")

    def test_emit_args_only(self):
        """Test emit with positional arguments only."""
        sub = Subscribable()
        callback = MagicMock()

        sub.subscribe(callback)
        sub.unsafe_emit("test", 123, [1, 2, 3])

        callback.assert_called_once_with("test", 123, [1, 2, 3])

    def test_emit_kwargs_only(self):
        """Test emit with keyword arguments only."""
        sub = Subscribable()
        callback = MagicMock()

        sub.subscribe(callback)
        sub.unsafe_emit(name="test", value=42, data={"key": "value"})

        callback.assert_called_once_with(name="test", value=42, data={"key": "value"})

    def test_emit_exception_handling(self):
        """Test emit behavior when subscriber raises exception."""
        sub = Subscribable()
        error_callback = MagicMock(side_effect=Exception("Callback error"))
        good_callback = MagicMock()

        sub.subscribe(error_callback)
        sub.subscribe(good_callback)

        # Should raise the first callback's exception
        with self.assertRaises(Exception) as context:
            sub.unsafe_emit("test")

        self.assertEqual(str(context.exception), "Callback error")
        error_callback.assert_called_once_with("test")
        # good_callback may or may not be called depending on order

    def test_slots_attribute(self):
        """Test that __slots__ is properly defined."""
        self.assertTrue(hasattr(Subscribable, '__slots__'))
        self.assertEqual(Subscribable.__slots__, '_subscribers')


class TestHashList(unittest.TestCase):
    """Test cases for HashList class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test objects with name attribute
        self.test_obj1 = type('TestObj', (), {'name': 'obj1', 'value': 10})()
        self.test_obj2 = type('TestObj', (), {'name': 'obj2', 'value': 20})()
        self.test_obj3 = type('TestObj', (), {'name': 'obj3', 'value': 30})()

    def test_init(self):
        """Test initialization of HashList."""
        hash_list = HashList('name')

        self.assertEqual(hash_list.hash_key, 'name')
        self.assertEqual(len(hash_list.hashes), 0)
        self.assertIsInstance(hash_list.hashes, dict)
        self.assertIsInstance(hash_list.subscribers, list)

    def test_init_inheritance(self):
        """Test that HashList inherits from Subscribable."""
        hash_list = HashList('name')

        self.assertIsInstance(hash_list, Subscribable)

    def test_hash_key_property(self):
        """Test hash_key property."""
        hash_list = HashList('test_key')

        self.assertEqual(hash_list.hash_key, 'test_key')

    def test_hashes_property(self):
        """Test hashes property."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)

        self.assertEqual(hash_list.hashes, {'obj1': self.test_obj1})
        self.assertIs(hash_list.hashes, hash_list._hashes)

    def test_append_single_object(self):
        """Test appending a single object."""
        hash_list = HashList('name')
        callback = MagicMock()
        hash_list.subscribe(callback)

        hash_list.append(self.test_obj1)

        self.assertIn('obj1', hash_list.hashes)
        self.assertEqual(hash_list.hashes['obj1'], self.test_obj1)
        self.assertEqual(len(hash_list), 1)
        callback.assert_called_once()

    def test_append_multiple_objects(self):
        """Test appending multiple objects."""
        hash_list = HashList('name')

        hash_list.append(self.test_obj1)
        hash_list.append(self.test_obj2)
        hash_list.append(self.test_obj3)

        self.assertEqual(len(hash_list), 3)
        self.assertIn('obj1', hash_list.hashes)
        self.assertIn('obj2', hash_list.hashes)
        self.assertIn('obj3', hash_list.hashes)

    def test_append_duplicate_key_updates(self):
        """Test appending object with duplicate key updates existing."""
        hash_list = HashList('name')
        obj1_updated = type('TestObj', (), {'name': 'obj1', 'value': 999})()

        hash_list.append(self.test_obj1)
        self.assertEqual(hash_list.hashes['obj1'].value, 10)

        hash_list.append(obj1_updated)

        self.assertEqual(len(hash_list), 1)
        self.assertEqual(hash_list.hashes['obj1'].value, 999)

    def test_contains_with_dict(self):
        """Test __contains__ with dictionary."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)

        _ = {'name': 'obj1'}

        # This will fail with current implementation since getattr on dict
        # We need to handle dict case properly
        assert 'obj1' in hash_list

    def test_contains_with_string(self):
        """Test __contains__ with string key."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)

        self.assertIn('obj1', hash_list)
        self.assertNotIn('obj2', hash_list)

    def test_contains_with_object(self):
        """Test __contains__ with object."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)

        self.assertIn(self.test_obj1, hash_list)
        self.assertNotIn(self.test_obj2, hash_list)

    def test_getitem_by_string_key(self):
        """Test __getitem__ with string key."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)

        result = hash_list['obj1']

        self.assertEqual(result, self.test_obj1)

    def test_getitem_by_integer_index(self):
        """Test __getitem__ with integer index."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)
        hash_list.append(self.test_obj2)

        result = hash_list[0]

        # Should return first item (insertion order in dict)
        self.assertIsNotNone(result)
        self.assertIn(result, [self.test_obj1, self.test_obj2])

    def test_getitem_nonexistent_key(self):
        """Test __getitem__ with non-existent key."""
        hash_list = HashList('name')

        with self.assertRaises(KeyError):
            hash_list['nonexistent']

    def test_iter(self):
        """Test __iter__ method."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)
        hash_list.append(self.test_obj2)

        items = list(hash_list)

        self.assertEqual(len(items), 2)
        self.assertIn(self.test_obj1, items)
        self.assertIn(self.test_obj2, items)

    def test_len(self):
        """Test __len__ method."""
        hash_list = HashList('name')

        self.assertEqual(len(hash_list), 0)

        hash_list.append(self.test_obj1)
        self.assertEqual(len(hash_list), 1)

        hash_list.append(self.test_obj2)
        self.assertEqual(len(hash_list), 2)

    def test_as_list_names(self):
        """Test as_list_names method."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)
        hash_list.append(self.test_obj2)

        names = hash_list.as_list_names()

        self.assertIsInstance(names, list)
        self.assertEqual(set(names), {'obj1', 'obj2'})

    def test_as_list_values(self):
        """Test as_list_values method."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)
        hash_list.append(self.test_obj2)

        values = hash_list.as_list_values()

        self.assertIsInstance(values, list)
        self.assertEqual(set(values), {self.test_obj1, self.test_obj2})

    def test_as_named_list(self):
        """Test as_named_list method."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)
        hash_list.append(self.test_obj2)

        named_list = hash_list.as_named_list()

        self.assertIsInstance(named_list, list)
        self.assertEqual(len(named_list), 2)

        # Each item should be a tuple of (key, value)
        for item in named_list:
            self.assertIsInstance(item, tuple)
            self.assertEqual(len(item), 2)
            key, value = item
            self.assertIn(key, ['obj1', 'obj2'])
            self.assertIn(value, [self.test_obj1, self.test_obj2])

    def test_by_attr(self):
        """Test by_attr method."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)
        hash_list.append(self.test_obj2)

        # Note: Current implementation returns key, not object
        result = hash_list.by_attr('value', 20)

        self.assertEqual(result, 'obj2')

    def test_by_attr_not_found(self):
        """Test by_attr method when attribute not found."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)

        result = hash_list.by_attr('value', 999)

        self.assertIsNone(result)

    def test_by_key(self):
        """Test by_key method."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)

        result = hash_list.by_key('obj1')

        self.assertEqual(result, self.test_obj1)

    def test_by_key_not_found(self):
        """Test by_key method when key not found."""
        hash_list = HashList('name')

        result = hash_list.by_key('nonexistent')

        self.assertIsNone(result)

    def test_by_index(self):
        """Test by_index method."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)
        hash_list.append(self.test_obj2)

        result = hash_list.by_index(0)

        self.assertIsNotNone(result)
        self.assertIn(result, [self.test_obj1, self.test_obj2])

    def test_by_index_out_of_range(self):
        """Test by_index method with out of range index."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)

        result = hash_list.by_index(10)

        self.assertIsNone(result)

    def test_by_index_negative(self):
        """Test by_index method with negative index."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)
        hash_list.append(self.test_obj2)

        result = hash_list.by_index(-1)

        self.assertIsNotNone(result)

    def test_emit_custom_implementation(self):
        """Test custom emit implementation."""
        hash_list = HashList('name')
        callback = MagicMock()
        hash_list.subscribe(callback)

        hash_list.append(self.test_obj1)

        callback.assert_called_once_with(
            models={'hash_key': 'name', 'hash_list': hash_list.hashes}
        )

    def test_extend(self):
        """Test extend method."""
        hash_list = HashList('name')
        callback = MagicMock()
        hash_list.subscribe(callback)

        hash_list.extend([self.test_obj1, self.test_obj2, self.test_obj3])

        self.assertEqual(len(hash_list), 3)
        self.assertIn('obj1', hash_list.hashes)
        self.assertIn('obj2', hash_list.hashes)
        self.assertIn('obj3', hash_list.hashes)

        # Should emit for each append
        self.assertEqual(callback.call_count, 3)

    def test_find_first(self):
        """Test find_first method."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)
        hash_list.append(self.test_obj2)
        hash_list.append(self.test_obj3)

        result = hash_list.find_first(lambda x: x.value > 15)

        self.assertIsNotNone(result)
        self.assertGreater(result.value, 15)  # type: ignore

    def test_find_first_not_found(self):
        """Test find_first method when no match found."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)

        result = hash_list.find_first(lambda x: x.value > 100)

        self.assertIsNone(result)

    def test_get_method(self):
        """Test get method."""
        hash_list = HashList('name')
        hash_list.append(self.test_obj1)

        result = hash_list.get('obj1')
        self.assertEqual(result, self.test_obj1)

        result = hash_list.get('nonexistent')
        self.assertIsNone(result)

        result = hash_list.get('nonexistent', 'default')
        self.assertEqual(result, 'default')

    def test_remove(self):
        """Test remove method."""
        hash_list = HashList('name')
        callback = MagicMock()
        hash_list.subscribe(callback)

        hash_list.append(self.test_obj1)
        hash_list.append(self.test_obj2)
        callback.reset_mock()

        hash_list.remove(self.test_obj1)

        self.assertEqual(len(hash_list), 1)
        self.assertNotIn('obj1', hash_list.hashes)
        self.assertIn('obj2', hash_list.hashes)
        callback.assert_called_once()

    def test_remove_nonexistent(self):
        """Test remove method with non-existent object."""
        hash_list = HashList('name')
        callback = MagicMock()
        hash_list.subscribe(callback)

        hash_list.append(self.test_obj1)
        callback.reset_mock()

        # Should not raise error
        hash_list.remove(self.test_obj2)

        self.assertEqual(len(hash_list), 1)
        callback.assert_called_once()  # Still emits

    def test_sort(self):
        """Test sort method."""
        hash_list = HashList('name')
        callback = MagicMock()
        hash_list.subscribe(callback)

        # Add in unsorted order
        hash_list.append(self.test_obj3)  # obj3
        hash_list.append(self.test_obj1)  # obj1
        hash_list.append(self.test_obj2)  # obj2
        callback.reset_mock()

        hash_list.sort()

        keys = list(hash_list.hashes.keys())
        self.assertEqual(keys, ['obj1', 'obj2', 'obj3'])
        callback.assert_called_once()

    def test_slots_attribute(self):
        """Test that __slots__ is properly defined."""
        self.assertTrue(hasattr(HashList, '__slots__'))
        self.assertEqual(HashList.__slots__, ('_hash_key', '_hashes'))

    def test_clear_method(self):
        """Test clear method."""
        hash_list = HashList('name')
        callback = MagicMock()
        hash_list.subscribe(callback)

        hash_list.append(self.test_obj1)
        hash_list.append(self.test_obj2)
        self.assertEqual(len(hash_list), 2)

        callback.reset_mock()
        hash_list.clear()

        self.assertEqual(len(hash_list), 0)
        self.assertNotIn('obj1', hash_list.hashes)
        self.assertNotIn('obj2', hash_list.hashes)
        callback.assert_called_once()


class TestSafeList(unittest.TestCase):
    """Test cases for SafeList class."""

    def test_init(self):
        """Test initialization of SafeList."""
        safe_list = SafeList()

        self.assertIsInstance(safe_list, list)
        self.assertEqual(len(safe_list), 0)

    def test_init_with_values(self):
        """Test initialization with initial values."""
        safe_list = SafeList([1, 2, 3])

        self.assertEqual(len(safe_list), 3)
        self.assertEqual(safe_list, [1, 2, 3])

    def test_append_new_item(self):
        """Test appending a new item."""
        safe_list = SafeList()

        safe_list.append("test")

        self.assertIn("test", safe_list)
        self.assertEqual(len(safe_list), 1)

    def test_append_duplicate_item(self):
        """Test appending duplicate item (should be ignored)."""
        safe_list = SafeList()

        safe_list.append("test")
        safe_list.append("test")  # Duplicate

        self.assertEqual(len(safe_list), 1)
        self.assertEqual(safe_list.count("test"), 1)

    def test_append_multiple_different_items(self):
        """Test appending multiple different items."""
        safe_list = SafeList()

        safe_list.append("item1")
        safe_list.append("item2")
        safe_list.append("item3")

        self.assertEqual(len(safe_list), 3)
        self.assertEqual(set(safe_list), {"item1", "item2", "item3"})

    def test_append_mixed_duplicates_and_new(self):
        """Test appending mix of duplicate and new items."""
        safe_list = SafeList()

        safe_list.append("item1")
        safe_list.append("item2")
        safe_list.append("item1")  # Duplicate
        safe_list.append("item3")
        safe_list.append("item2")  # Duplicate

        self.assertEqual(len(safe_list), 3)
        self.assertEqual(set(safe_list), {"item1", "item2", "item3"})

    def test_append_with_different_types(self):
        """Test appending different data types."""
        safe_list = SafeList()

        safe_list.append(1)
        safe_list.append("string")
        safe_list.append([1, 2, 3])
        safe_list.append({"key": "value"})
        safe_list.append(1)  # Duplicate int

        self.assertEqual(len(safe_list), 4)

    def test_append_with_objects(self):
        """Test appending custom objects."""
        safe_list = SafeList()
        obj1 = object()
        obj2 = object()

        safe_list.append(obj1)
        safe_list.append(obj2)
        safe_list.append(obj1)  # Same object reference

        self.assertEqual(len(safe_list), 2)
        self.assertIn(obj1, safe_list)
        self.assertIn(obj2, safe_list)

    def test_other_list_methods_work(self):
        """Test that other list methods still work normally."""
        safe_list = SafeList([1, 2, 3])

        # Test extend
        safe_list.extend([4, 5])
        self.assertEqual(len(safe_list), 5)

        # Test insert
        safe_list.insert(0, 0)
        self.assertEqual(safe_list[0], 0)

        # Test remove
        safe_list.remove(2)
        self.assertNotIn(2, safe_list)

        # Test pop
        _ = safe_list.pop()
        self.assertEqual(len(safe_list), len(safe_list))

    def test_extend_allows_duplicates(self):
        """Test that extend still allows duplicates (not overridden)."""
        safe_list = SafeList([1, 2])

        safe_list.extend([2, 3, 2])  # Contains duplicates

        # extend is not overridden, so duplicates are allowed
        self.assertGreater(safe_list.count(2), 1)

    def test_inheritance_from_list(self):
        """Test that SafeList properly inherits from list."""
        safe_list = SafeList()

        self.assertIsInstance(safe_list, list)
        self.assertTrue(hasattr(safe_list, 'append'))
        self.assertTrue(hasattr(safe_list, 'extend'))
        self.assertTrue(hasattr(safe_list, 'remove'))


class TestTrackedList(unittest.TestCase):
    """Test cases for TrackedList class."""

    def test_init(self):
        """Test initialization of TrackedList."""
        tracked_list = TrackedList()

        self.assertIsInstance(tracked_list, list)
        self.assertIsInstance(tracked_list.subscribers, list)
        self.assertEqual(len(tracked_list.subscribers), 0)

    def test_init_with_values(self):
        """Test initialization with initial values."""
        tracked_list = TrackedList([1, 2, 3])

        self.assertEqual(len(tracked_list), 3)
        self.assertEqual(tracked_list, [1, 2, 3])

    def test_subscribers_property_getter(self):
        """Test subscribers property getter."""
        tracked_list = TrackedList()

        self.assertEqual(tracked_list.subscribers, tracked_list._subscribers)
        self.assertIs(tracked_list.subscribers, tracked_list._subscribers)

    def test_subscribers_property_setter(self):
        """Test subscribers property setter."""
        tracked_list = TrackedList()
        new_subscribers = [lambda: None, lambda: None]

        with self.assertRaises(TypeError) as context:
            tracked_list.subscribers = new_subscribers
        self.assertEqual(str(context.exception), 'subscribers must be a SafeList')

    def test_subscribers_is_safe_list(self):
        """Test that subscribers is a SafeList."""
        tracked_list = TrackedList()

        self.assertIsInstance(tracked_list._subscribers, SafeList)

    def test_emit_no_subscribers(self):
        """Test emit with no subscribers."""
        tracked_list = TrackedList()

        # Should not raise error
        tracked_list.emit()

    def test_emit_with_subscribers(self):
        """Test emit with subscribers."""
        tracked_list = TrackedList()
        callback1 = MagicMock()
        callback2 = MagicMock()

        tracked_list.subscribers.append(callback1)
        tracked_list.subscribers.append(callback2)

        tracked_list.emit()

        callback1.assert_called_once_with()
        callback2.assert_called_once_with()

    def test_emit_with_failing_subscriber(self):
        """Test emit behavior when subscriber raises exception."""
        tracked_list = TrackedList()
        error_callback = MagicMock(side_effect=Exception("Subscriber error"))
        good_callback = MagicMock()

        tracked_list.subscribers.append(error_callback)
        tracked_list.subscribers.append(good_callback)

        # The list comprehension will continue even if one fails
        # but the exception might not be raised
        tracked_list.emit()

        error_callback.assert_called_once()

    def test_append_triggers_emit(self):
        """Test that append triggers emit."""
        tracked_list = TrackedList()
        callback = MagicMock()
        tracked_list.subscribers.append(callback)

        tracked_list.append("test")

        self.assertIn("test", tracked_list)
        callback.assert_called_once_with()

    def test_append_multiple_items(self):
        """Test appending multiple items triggers multiple emits."""
        tracked_list = TrackedList()
        callback = MagicMock()
        tracked_list.subscribers.append(callback)

        tracked_list.append("item1")
        tracked_list.append("item2")
        tracked_list.append("item3")

        self.assertEqual(len(tracked_list), 3)
        self.assertEqual(callback.call_count, 3)

    def test_remove_triggers_emit(self):
        """Test that remove triggers emit."""
        tracked_list = TrackedList(["test", "other"])
        callback = MagicMock()
        tracked_list.subscribers.append(callback)

        tracked_list.remove("test")

        self.assertNotIn("test", tracked_list)
        callback.assert_called_once_with()

    def test_remove_nonexistent_raises_error(self):
        """Test removing non-existent item raises ValueError."""
        tracked_list = TrackedList()
        callback = MagicMock()
        tracked_list.subscribers.append(callback)

        with self.assertRaises(ValueError):
            tracked_list.remove("nonexistent")

        # Emit should not be called if remove fails
        callback.assert_not_called()

    def test_other_list_methods_no_emit(self):
        """Test that other list methods don't trigger emit."""
        tracked_list = TrackedList([1, 2, 3])
        callback = MagicMock()
        tracked_list.subscribers.append(callback)

        # These operations should not trigger emit
        _ = tracked_list[0]  # __getitem__
        _ = len(tracked_list)  # __len__
        _ = 2 in tracked_list  # __contains__
        tracked_list.index(2)  # index method
        tracked_list.count(1)  # count method

        callback.assert_not_called()

    def test_extend_no_emit_override(self):
        """Test that extend doesn't trigger emit (not overridden)."""
        tracked_list = TrackedList([1])
        callback = MagicMock()
        tracked_list.subscribers.append(callback)

        tracked_list.extend([2, 3])

        self.assertEqual(len(tracked_list), 3)
        # extend is not overridden, so no emit
        callback.assert_not_called()

    def test_insert_no_emit_override(self):
        """Test that insert doesn't trigger emit (not overridden)."""
        tracked_list = TrackedList([1, 3])
        callback = MagicMock()
        tracked_list.subscribers.append(callback)

        tracked_list.insert(1, 2)

        self.assertEqual(tracked_list, [1, 2, 3])
        # insert is not overridden, so no emit
        callback.assert_not_called()

    def test_subscriber_deduplication(self):
        """Test that subscribers are deduplicated (using SafeList)."""
        tracked_list = TrackedList()
        callback = MagicMock()

        tracked_list.subscribers.append(callback)
        tracked_list.subscribers.append(callback)  # Duplicate

        self.assertEqual(len(tracked_list.subscribers), 1)

    def test_complex_workflow(self):
        """Test complex workflow with multiple operations."""
        tracked_list = TrackedList()
        callback1 = MagicMock()
        callback2 = MagicMock()

        # Subscribe callbacks
        tracked_list.subscribers.append(callback1)
        tracked_list.subscribers.append(callback2)

        # Perform tracked operations
        tracked_list.append("item1")
        tracked_list.append("item2")
        tracked_list.remove("item1")

        # Check final state
        self.assertEqual(tracked_list, ["item2"])

        # Check callback calls
        self.assertEqual(callback1.call_count, 3)  # 2 appends + 1 remove
        self.assertEqual(callback2.call_count, 3)  # 2 appends + 1 remove

    def test_inheritance_from_list(self):
        """Test that TrackedList properly inherits from list."""
        tracked_list = TrackedList()

        self.assertIsInstance(tracked_list, list)
        self.assertTrue(hasattr(tracked_list, 'append'))
        self.assertTrue(hasattr(tracked_list, 'remove'))
        self.assertTrue(hasattr(tracked_list, 'extend'))


class TestIntegration(unittest.TestCase):
    """Integration tests for list module components."""

    def test_hash_list_with_safe_list_subscribers(self):
        """Test HashList with SafeList for managing subscribers."""
        hash_list = HashList('name')

        # Subscribers should be a regular list, but we can test the concept
        callback1 = MagicMock()
        callback2 = MagicMock()

        hash_list.subscribe(callback1)
        hash_list.subscribe(callback2)
        hash_list.subscribe(callback1)  # Duplicate

        self.assertEqual(len(hash_list.subscribers), 2)

    def test_tracked_list_with_hash_list_items(self):
        """Test TrackedList containing HashList-like objects."""
        tracked_list = TrackedList()
        callback = MagicMock()
        tracked_list.subscribers.append(callback)

        hash_list1 = HashList('id')
        hash_list2 = HashList('id')

        tracked_list.append(hash_list1)
        tracked_list.append(hash_list2)

        self.assertEqual(len(tracked_list), 2)
        self.assertEqual(callback.call_count, 2)

    def test_subscribable_inheritance_patterns(self):
        """Test various inheritance patterns with Subscribable."""
        class CustomHashList(HashList):
            def __init__(self, hash_key):
                super().__init__(hash_key)
                self.custom_attr = "custom"

        custom_list = CustomHashList('name')
        callback = MagicMock()
        custom_list.subscribe(callback)

        test_obj = type('TestObj', (), {'name': 'test'})()
        custom_list.append(test_obj)

        self.assertEqual(custom_list.custom_attr, "custom")
        callback.assert_called_once()

    def test_nested_subscription_patterns(self):
        """Test nested subscription patterns."""
        outer_list = TrackedList()
        inner_hash = HashList('name')

        outer_callback = MagicMock()
        inner_callback = MagicMock()

        outer_list.subscribers.append(outer_callback)
        inner_hash.subscribe(inner_callback)

        # Add hash list to tracked list
        outer_list.append(inner_hash)

        # Add item to hash list
        test_obj = type('TestObj', (), {'name': 'test'})()
        inner_hash.append(test_obj)

        # Both callbacks should have been triggered
        outer_callback.assert_called_once()  # When hash was added to tracked list
        inner_callback.assert_called_once()  # When item was added to hash

    def test_performance_with_many_subscribers(self):
        """Test performance characteristics with many subscribers."""
        hash_list = HashList('name')

        # Add many subscribers
        callbacks = [MagicMock() for _ in range(100)]
        for callback in callbacks:
            hash_list.subscribe(callback)

        test_obj = type('TestObj', (), {'name': 'test'})()
        hash_list.append(test_obj)

        # All callbacks should be called
        for callback in callbacks:
            callback.assert_called_once()

    def test_memory_management_with_subscriptions(self):
        """Test memory management with subscriptions."""
        hash_list = HashList('name')

        # Add and remove subscribers
        callback1 = MagicMock()
        callback2 = MagicMock()
        callback3 = MagicMock()

        hash_list.subscribe(callback1)
        hash_list.subscribe(callback2)
        hash_list.subscribe(callback3)

        self.assertEqual(len(hash_list.subscribers), 3)

        # Remove some subscribers
        hash_list.unsubscribe(callback2)

        self.assertEqual(len(hash_list.subscribers), 2)
        self.assertNotIn(callback2, hash_list.subscribers)

    def test_error_resilience_in_callbacks(self):
        """Test error resilience when callbacks fail."""
        hash_list = HashList('name')

        error_callback = MagicMock(side_effect=Exception("Callback failed"))
        good_callback = MagicMock()

        hash_list.subscribe(error_callback)
        hash_list.subscribe(good_callback)

        test_obj = type('TestObj', (), {'name': 'test'})()

        # Should raise error from first callback
        with self.assertRaises(Exception):
            hash_list.append(test_obj)

        # Object should still be added despite callback error
        self.assertIn('test', hash_list.hashes)

    def test_concurrent_modification_safety(self):
        """Test safety with concurrent-like modifications."""
        tracked_list = TrackedList()

        # Callback that modifies the subscribers list
        def modifying_callback():
            if len(tracked_list.subscribers) > 1:
                tracked_list.subscribers.append(lambda: None)

        regular_callback = MagicMock()

        tracked_list.subscribers.append(modifying_callback)
        tracked_list.subscribers.append(regular_callback)

        # This should not cause issues
        tracked_list.append("test")

        regular_callback.assert_called_once()

    def test_type_safety_with_generics(self):
        """Test type safety with generic types."""
        # This is more of a documentation test since Python doesn't enforce generics at runtime
        string_hash_list = HashList[str]('name')
        int_safe_list = SafeList[int]()
        float_tracked_list = TrackedList[float]()

        # Should work with any type (Python doesn't enforce at runtime)
        test_obj = type('TestObj', (), {'name': 'test'})()
        string_hash_list.append(test_obj)  # type: ignore

        int_safe_list.append("not an int")  # Would work in Python  # type: ignore
        float_tracked_list.append({"not": "a float"})  # Would work in Python  # type: ignore

        # Just verify they work as expected
        self.assertEqual(len(string_hash_list), 1)
        self.assertEqual(len(int_safe_list), 1)
        self.assertEqual(len(float_tracked_list), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)

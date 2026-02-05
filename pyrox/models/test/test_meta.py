"""Unit tests for the meta module."""

import pytest


from pyrox.models.meta import (
    PyroxObject,
    SliceableInt,
    SnowFlake,
)
from pyrox.services import IdGeneratorService


class TestSliceableInt:
    """Test the SliceableInt class."""

    def test_initialization(self):
        """Test SliceableInt initialization."""
        si = SliceableInt()
        assert si._value == 0
        assert int(si) == 0

        si2 = SliceableInt(42)
        assert si2._value == 42
        assert int(si2) == 42

    def test_arithmetic_operations(self):
        """Test arithmetic operations."""
        si = SliceableInt(10)

        assert si + 5 == 15
        assert 5 + si == 15  # Test __radd__
        assert si - 3 == 7

        # Test equality
        assert si == 10
        assert si != 5

    def test_string_representation(self):
        """Test string representation."""
        si = SliceableInt(42)
        assert repr(si) == "42"
        assert str(si) == "42"

    def test_bit_operations(self):
        """Test bit manipulation operations."""
        si = SliceableInt(0b10101010)  # 170
        print(f'Initial value: {si._value:08b}')
        print(f'Bit 0: {si.read_bit(0)}')

        # Test read_bit
        assert si.read_bit(0) == False  # noqa: E712 - Bit 0 is 0
        assert si.read_bit(1) == True   # noqa: E712 - Bit 1 is 1
        assert si.read_bit(7) == True   # noqa: E712 - MSB is 1

        # Test set_bit
        original_value = si._value
        si.set_bit(0)
        assert si._value == original_value | 1
        assert si.read_bit(0) == True  # noqa: E712 - Bit 0 should now be 1

        # Test clear_bit
        si.clear_bit(1)
        assert si.read_bit(1) == False  # noqa: E712 - Bit 1 should now be 0

    def test_clear_and_set_value(self):
        """Test clear and set_value methods."""
        si = SliceableInt(42)
        si.clear()
        assert si._value == 0

        si.set_value(100)
        assert si._value == 100
        assert isinstance(si, SliceableInt)  # Type should be preserved

    def test_index_and_int_conversion(self):
        """Test __index__ and __int__ methods."""
        si = SliceableInt(42)
        assert si.__index__() == 42
        assert int(si) == 42

        # Test that it can be used in contexts requiring an index
        test_list = [1, 2, 3, 4, 5]
        si_index = SliceableInt(2)
        assert test_list[si_index] == 3


class TestSnowFlake:
    """Test the SnowFlake class."""

    def setup_method(self):
        """Reset the ID generator before each test."""
        IdGeneratorService._ctr = 0

    def test_unique_ids(self):
        """Test that each SnowFlake gets a unique ID."""
        sf1 = SnowFlake()
        sf2 = SnowFlake()
        sf3 = SnowFlake()

        assert sf1.id == 1
        assert sf2.id == 2
        assert sf3.id == 3

        # All IDs should be different
        assert sf1.id != sf2.id
        assert sf2.id != sf3.id

    def test_equality(self):
        """Test SnowFlake equality comparison."""
        sf1 = SnowFlake()
        sf2 = SnowFlake()

        # Same object should be equal to itself
        assert sf1 == sf1

        # Different objects should not be equal
        assert sf1 != sf2

        # Test with different types
        assert sf1 != "not a snowflake"
        assert sf1 != 42

    def test_hash(self):
        """Test SnowFlake hashing."""
        sf1 = SnowFlake()
        sf2 = SnowFlake()

        # Hash should be based on ID
        assert hash(sf1) == hash(sf1.id)
        assert hash(sf1) != hash(sf2)

        # Should be usable in sets and dicts
        snowflake_set = {sf1, sf2}
        assert len(snowflake_set) == 2

    def test_string_representation(self):
        """Test SnowFlake string representation."""
        sf = SnowFlake()
        assert str(sf) == str(sf.id)


class TestPyroxObject:
    """Test the PyroxObject class."""

    def setup_method(self):
        """Reset the ID generator before each test."""
        IdGeneratorService._ctr = 0

    def test_inheritance(self):
        """Test PyroxObject inheritance."""
        obj = PyroxObject()

        # Should inherit from SnowFlake
        assert hasattr(obj, 'id')
        assert obj.id == 1

    def test_repr(self):
        """Test PyroxObject string representation."""
        obj = PyroxObject()
        assert repr(obj) == "PyroxObject"


class TestBitOperations:
    """Test bit operations in SliceableInt."""

    def test_bit_operations(self):
        """test bit operations perform correctly
        """

        my_value = SliceableInt(0)

        my_value.set_bit(0)

        assert my_value == 1
        assert my_value.read_bit(0)

        my_value.set_bit(1)

        assert my_value == 3
        assert my_value.read_bit(0)
        assert my_value.read_bit(1)

        my_value.clear_bit(0)

        assert my_value == 2
        assert not my_value.read_bit(0)
        assert my_value.read_bit(1)

        assert isinstance(my_value, SliceableInt)

        my_value.set_value(8)

        assert my_value == 8
        assert not my_value.read_bit(0)
        assert not my_value.read_bit(1)
        assert not my_value.read_bit(2)
        assert my_value.read_bit(3)

        my_value.clear()

        assert my_value == 0

        assert isinstance(my_value, SliceableInt)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

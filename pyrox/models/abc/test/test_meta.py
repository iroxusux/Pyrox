"""Unit tests for the meta module."""

import pytest
import re
from pathlib import Path


from pyrox.models.abc.meta import (
    _IdGenerator,
    ALLOWED_CHARS,
    ALLOWED_REV_CHARS,
    ALLOWED_MOD_CHARS,
    DEF_ICON,
    EnforcesNaming,
    NamedPyroxObject,
    PyroxObject,
    SliceableInt,
    SnowFlake,
    SupportsFileLocation,
    SupportsItemAccess,
    SupportsMetaData,
    TK_CURSORS,
)


class TestConstants:
    """Test constants defined in the meta module."""

    def test_default_constants(self):
        """Test that default constants are properly defined."""
        assert isinstance(DEF_ICON, Path)
        assert DEF_ICON.name == '_def.ico'

    def test_regex_patterns(self):
        """Test that regex patterns are compiled correctly."""
        assert isinstance(ALLOWED_CHARS, re.Pattern)
        assert isinstance(ALLOWED_REV_CHARS, re.Pattern)
        assert isinstance(ALLOWED_MOD_CHARS, re.Pattern)

        # Test what characters are allowed/disallowed
        assert ALLOWED_CHARS.search('invalid!@#') is not None
        assert ALLOWED_CHARS.search('valid_name123[]') is None

        assert ALLOWED_REV_CHARS.search('1.2.3') is None
        assert ALLOWED_REV_CHARS.search('1.2.3a') is not None

        assert ALLOWED_MOD_CHARS.search('module_name-1.0') is None
        assert ALLOWED_MOD_CHARS.search('module@name') is not None


class TestTKCursors:
    """Test the TK_CURSORS enum."""

    def test_cursor_enum_values(self):
        """Test that cursor enum has expected values."""
        assert TK_CURSORS.ARROW.value == "arrow"
        assert TK_CURSORS.CIRCLE.value == "circle"
        assert TK_CURSORS.CLOCK.value == "clock"
        assert TK_CURSORS.CROSS.value == "cross"
        assert TK_CURSORS.DEFAULT.value == ""
        assert TK_CURSORS.DOTBOX.value == "dotbox"
        assert TK_CURSORS.EXCHANGE.value == "exchange"
        assert TK_CURSORS.FLEUR.value == "fleur"
        assert TK_CURSORS.HEART.value == "heart"
        assert TK_CURSORS.MAN.value == "man"
        assert TK_CURSORS.MOUSE.value == "mouse"
        assert TK_CURSORS.PIRATE.value == "pirate"
        assert TK_CURSORS.PLUS.value == "plus"
        assert TK_CURSORS.SHUTTLE.value == "shuttle"
        assert TK_CURSORS.SIZING.value == "sizing"
        assert TK_CURSORS.SPIDER.value == "spider"
        assert TK_CURSORS.SPRAYCAN.value == "spraycan"
        assert TK_CURSORS.STAR.value == "star"
        assert TK_CURSORS.TARGET.value == "target"
        assert TK_CURSORS.TCROSS.value == "tcross"
        assert TK_CURSORS.TREK.value == "trek"
        assert TK_CURSORS.WAIT.value == "wait"

    def test_cursor_enum_membership(self):
        """Test cursor enum membership."""
        assert TK_CURSORS.ARROW in TK_CURSORS
        assert len(list(TK_CURSORS)) == 22


class TestIdGenerator:
    """Test the _IdGenerator class."""

    def setup_method(self):
        """Reset the counter before each test."""
        _IdGenerator._ctr = 0

    def test_get_id_increments(self):
        """Test that get_id returns incremental values."""
        first_id = _IdGenerator.get_id()
        second_id = _IdGenerator.get_id()
        third_id = _IdGenerator.get_id()

        assert first_id == 1
        assert second_id == 2
        assert third_id == 3

    def test_curr_value(self):
        """Test curr_value returns current counter value."""
        assert _IdGenerator.curr_value() == 0
        _IdGenerator.get_id()
        assert _IdGenerator.curr_value() == 1
        _IdGenerator.get_id()
        assert _IdGenerator.curr_value() == 2

    def test_thread_safety_simulation(self):
        """Test that multiple calls return unique values."""
        ids = [_IdGenerator.get_id() for _ in range(100)]
        assert len(set(ids)) == 100  # All IDs should be unique


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


class TestEnforcesNaming:
    """Test the EnforcesNaming class."""

    def test_is_valid_string(self):
        """Test string validation."""
        # Valid strings
        assert EnforcesNaming.is_valid_string("validName123") is True
        assert EnforcesNaming.is_valid_string("valid_name") is True
        assert EnforcesNaming.is_valid_string("name[0]") is True
        assert EnforcesNaming.is_valid_string("array[index]") is True

        # Invalid strings
        assert EnforcesNaming.is_valid_string("invalid!name") is False
        assert EnforcesNaming.is_valid_string("name@symbol") is False
        assert EnforcesNaming.is_valid_string("name with spaces") is False

    def test_is_valid_rockwell_bool(self):
        """Test Rockwell boolean validation."""
        assert EnforcesNaming.is_valid_rockwell_bool("true") is True
        assert EnforcesNaming.is_valid_rockwell_bool("false") is True

        assert EnforcesNaming.is_valid_rockwell_bool("True") is False
        assert EnforcesNaming.is_valid_rockwell_bool("FALSE") is False
        assert EnforcesNaming.is_valid_rockwell_bool("1") is False
        assert EnforcesNaming.is_valid_rockwell_bool("0") is False
        assert EnforcesNaming.is_valid_rockwell_bool("") is False
        assert EnforcesNaming.is_valid_rockwell_bool("yes") is False

    def test_is_valid_module_string(self):
        """Test module string validation."""
        # Valid module names
        assert EnforcesNaming.is_valid_module_string("module_name") is True
        assert EnforcesNaming.is_valid_module_string("module-1.0") is True
        assert EnforcesNaming.is_valid_module_string("Module123.dll") is True

        # Invalid module names
        assert EnforcesNaming.is_valid_module_string("module@name") is False
        assert EnforcesNaming.is_valid_module_string("module name") is False
        assert EnforcesNaming.is_valid_module_string("module!name") is False

    def test_is_valid_revision_string(self):
        """Test revision string validation."""
        # Valid revision strings
        assert EnforcesNaming.is_valid_revision_string("1.2.3") is True
        assert EnforcesNaming.is_valid_revision_string("10.25") is True
        assert EnforcesNaming.is_valid_revision_string("1") is True

        # Invalid revision strings
        assert EnforcesNaming.is_valid_revision_string("1.2.3a") is False
        assert EnforcesNaming.is_valid_revision_string("v1.2.3") is False
        assert EnforcesNaming.is_valid_revision_string("1-2-3") is False

    def test_invalid_naming_exception(self):
        """Test InvalidNamingException."""
        exception = EnforcesNaming.InvalidNamingException()
        assert "Invalid naming scheme!" in exception.message

        custom_exception = EnforcesNaming.InvalidNamingException("Custom message: ")
        assert "Custom message:" in custom_exception.message


class TestSnowFlake:
    """Test the SnowFlake class."""

    def setup_method(self):
        """Reset the ID generator before each test."""
        _IdGenerator._ctr = 0

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
        _IdGenerator._ctr = 0

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


class TestSupportsItemAccess:
    """Test the SupportsItemAccess class."""

    def test_item_access_with_meta_data(self):
        """Test item access when meta_data exists."""

        class TestClass(SupportsItemAccess):
            def __init__(self):
                self.meta_data = {'key1': 'value1', 'key2': 'value2'}

        obj = TestClass()

        # Test getting items
        assert obj['key1'] == 'value1'
        assert obj['key2'] == 'value2'
        assert obj['nonexistent'] is None

        # Test setting items
        obj['key3'] = 'value3'
        assert obj['key3'] == 'value3'
        assert obj.meta_data['key3'] == 'value3'

    def test_item_access_without_meta_data(self):
        """Test item access when no meta_data exists."""

        class TestClass(SupportsItemAccess):
            pass

        obj = TestClass()

        # Should return None when no indexed_attribute
        with pytest.raises(TypeError, match="Cannot set item on a non-dict indexed attribute!"):
            obj['key'] = 'value'

    def test_set_item_non_dict_error(self):
        """Test setting item on non-dict indexed attribute."""

        class TestClass(SupportsItemAccess):
            def __init__(self):
                self.meta_data = "not a dict"

        obj = TestClass()

        with pytest.raises(TypeError, match="Cannot set item on a non-dict"):
            obj['key'] = 'value'


class TestSupportsMetaData:
    """Test the SupportsMetaData class."""

    def setup_method(self):
        """Reset the ID generator before each test."""
        _IdGenerator._ctr = 0

    def test_initialization_default(self):
        """Test initialization with default values."""
        obj = SupportsMetaData()
        assert obj.meta_data == {}

    def test_initialization_with_dict(self):
        """Test initialization with dictionary meta data."""
        test_data = {'key': 'value', 'number': 42}
        obj = SupportsMetaData(meta_data=test_data)
        assert obj.meta_data == test_data

    def test_initialization_with_string(self):
        """Test initialization with string meta data."""
        test_string = "test meta data"
        obj = SupportsMetaData(meta_data=test_string)
        assert obj.meta_data == test_string

    def test_meta_data_setter_valid(self):
        """Test setting valid meta data."""
        obj = SupportsMetaData()

        # Test dict
        test_dict = {'new': 'data'}
        obj.meta_data = test_dict
        assert obj.meta_data == test_dict

        # Test string
        test_string = "new string data"
        obj.meta_data = test_string
        assert obj.meta_data == test_string

        # Test None
        obj.meta_data = ''
        assert not obj.meta_data

    def test_meta_data_setter_invalid(self):
        """Test setting invalid meta data types."""
        obj = SupportsMetaData()

        with pytest.raises(TypeError, match="Meta data must be a dictionary or string."):
            obj.meta_data = 42  # type: ignore

        with pytest.raises(TypeError, match="Meta data must be a dictionary or string."):
            obj.meta_data = ['list', 'not', 'allowed']  # type: ignore

    def test_item_access_inheritance(self):
        """Test that item access works with meta data."""
        obj = SupportsMetaData(meta_data={'test': 'value'})
        assert obj['test'] == 'value'

        obj['new_key'] = 'new_value'
        assert obj.meta_data['new_key'] == 'new_value'  # type: ignore

    def test_generic_typing(self):
        """Test SupportsMetaData with generic typing."""

        class GenericMetaData(SupportsMetaData[str]):
            pass

        obj = GenericMetaData(meta_data="generic string")
        assert obj.meta_data == "generic string"

        obj.meta_data = "another string"
        assert obj.meta_data == "another string"


class TestNamedPyroxObject:
    """Test the NamedPyroxObject class."""

    def setup_method(self):
        """Reset the ID generator before each test."""
        _IdGenerator._ctr = 0

    def test_initialization_default(self):
        """Test initialization with default values."""
        obj = NamedPyroxObject()
        assert obj.name == "NamedPyroxObject"
        assert obj.description == ""

    def test_initialization_with_values(self):
        """Test initialization with custom values."""
        obj = NamedPyroxObject(name="TestObject", description="Test description")
        assert obj.name == "TestObject"
        assert obj.description == "Test description"

    def test_name_setter_valid(self):
        """Test setting valid names."""
        obj = NamedPyroxObject()

        obj.name = "valid_name123"
        assert obj.name == "valid_name123"

        obj.name = "array[0]"
        assert obj.name == "array[0]"

    def test_name_setter_invalid(self):
        """Test setting invalid names."""
        obj = NamedPyroxObject()

        with pytest.raises(EnforcesNaming.InvalidNamingException):
            obj.name = "invalid!name"

        with pytest.raises(EnforcesNaming.InvalidNamingException):
            obj.name = "name with spaces"

    def test_description_setter_valid(self):
        """Test setting valid descriptions."""
        obj = NamedPyroxObject()

        obj.description = "This is a valid description"
        assert obj.description == "This is a valid description"

        obj.description = ""
        assert obj.description == ""

    def test_description_setter_invalid(self):
        """Test setting invalid descriptions."""
        obj = NamedPyroxObject()

        with pytest.raises(TypeError, match="Description must be a string"):
            obj.description = 42  # type: ignore

        with pytest.raises(TypeError, match="Description must be a string"):
            obj.description = None  # type: ignore

    def test_string_representations(self):
        """Test string representations."""
        obj = NamedPyroxObject(name="TestObject")

        assert str(obj) == "TestObject"
        assert repr(obj) == "TestObject"

    def test_inheritance(self):
        """Test that NamedPyroxObject inherits from PyroxObject."""
        obj = NamedPyroxObject()

        # Should have ID from SnowFlake
        assert hasattr(obj, 'id')
        assert obj.id == 1


class TestSupportsFileLocation:
    """Test the SupportsFileLocation class."""

    def setup_method(self):
        """Reset the ID generator before each test."""
        _IdGenerator._ctr = 0

    def test_initialization_default(self):
        """Test initialization with default values."""
        obj = SupportsFileLocation()
        assert obj.file_location is None

    def test_initialization_with_location(self):
        """Test initialization with file location."""
        location = "/path/to/file.txt"
        obj = SupportsFileLocation(file_location=location)
        assert obj.file_location == location

    def test_file_location_setter_valid(self):
        """Test setting valid file locations."""
        obj = SupportsFileLocation()

        # Test string path
        obj.file_location = "/valid/path/file.txt"
        assert obj.file_location == "/valid/path/file.txt"

        # Test None
        obj.file_location = None
        assert obj.file_location is None

        # Test empty string
        obj.file_location = ""
        assert obj.file_location == ""

    def test_file_location_setter_invalid(self):
        """Test setting invalid file locations."""
        obj = SupportsFileLocation()

        with pytest.raises(TypeError, match="File location must be a string or None"):
            obj.file_location = 42  # type: ignore

        with pytest.raises(TypeError, match="File location must be a string or None"):
            obj.file_location = ['path', 'list']  # type: ignore


class TestIntegration:
    """Integration tests for multiple classes working together."""

    def setup_method(self):
        """Reset the ID generator before each test."""
        _IdGenerator._ctr = 0

    def test_multiple_inheritance_combination(self):
        """Test a class that combines multiple base classes."""

        class CombinedClass(SupportsMetaData, SupportsFileLocation, NamedPyroxObject):
            pass

        obj = CombinedClass(
            name="combined_object",
            description="A combined test object",
            meta_data={'type': 'test', 'version': 1.0},
            file_location="/path/to/object.xml"
        )

        # Test all inherited functionality
        assert obj.name == "combined_object"
        assert obj.description == "A combined test object"
        assert obj.meta_data == {'type': 'test', 'version': 1.0}
        assert obj.file_location == "/path/to/object.xml"

        # Test item access from SupportsMetaData
        assert obj['type'] == 'test'
        assert obj['version'] == 1.0

        # Test unique ID
        assert obj.id == 1

    def test_sliceable_int_in_data_structure(self):
        """Test SliceableInt working within other data structures."""
        si1 = SliceableInt(0b11110000)
        si2 = SliceableInt(0b00001111)

        obj = SupportsMetaData(meta_data={
            'value1': si1,
            'value2': si2,
            'combined': si1 + si2
        })

        assert obj['value1'] == 240  # 0b11110000
        assert obj['value2'] == 15   # 0b00001111
        assert obj['combined'] == 255  # 240 + 15

    def test_error_propagation(self):
        """Test that errors propagate correctly through inheritance."""
        obj = NamedPyroxObject()

        # Test that naming validation works
        with pytest.raises(EnforcesNaming.InvalidNamingException):
            obj.name = "invalid name with spaces"

        # Test that other setters work
        obj.description = "Valid description"
        assert obj.description == "Valid description"


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

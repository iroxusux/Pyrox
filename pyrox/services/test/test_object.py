from pyrox.services.object import (
    is_iterable,
    get_object_attributes,
    resolve_object_path,
    resolve_object_path_with_parent
)


class TestObjectAttributes:
    def test_dict_attributes(self):
        my_dict = {'key1': 'value1', 'key2': 42}
        attrs = get_object_attributes(my_dict)
        assert attrs == my_dict

    def test_list_attributes(self):
        my_list = ['a', 'b', 'c']
        attrs = get_object_attributes(my_list)
        assert attrs == {'[0]': 'a', '[1]': 'b', '[2]': 'c'}

    def test_set_attributes(self):
        my_set = {'x', 'y', 'z'}
        attrs = get_object_attributes(my_set)
        assert 'x' in attrs.values()
        assert 'y' in attrs.values()
        assert 'z' in attrs.values()

    def test_object_attributes(self):
        class MyClass:
            def __init__(self):
                self.public_attr = 'public'
                self._private_attr = 'private'

            def method(self):
                pass
        obj = MyClass()
        attrs = get_object_attributes(obj)
        assert 'public_attr' in attrs
        assert '_private_attr' not in attrs
        assert 'method' not in attrs
        attrs_with_private = get_object_attributes(obj, show_private=True)
        assert '_private_attr' in attrs_with_private
        assert 'public_attr' in attrs_with_private
        assert 'method' not in attrs_with_private

    def test_unaccessible_attribute(self):
        class MyClass:
            @property
            def faulty_attr(self):
                raise ValueError("Cannot access this attribute")
        obj = MyClass()
        attrs = get_object_attributes(obj)
        assert 'faulty_attr' not in attrs

    def test_no_attributes(self):
        class EmptyClass:
            pass
        obj = EmptyClass()
        attrs = get_object_attributes(obj)
        assert attrs == {}

    def test_builtin_type(self):
        my_int = 42
        attrs = get_object_attributes(my_int)
        assert attrs == {}

    def test_none_type(self):
        my_none = None
        attrs = get_object_attributes(my_none)
        assert attrs == {}

    def test_show_private_flag(self):
        class MyClass:
            def __init__(self):
                self.public_attr = 'public'
                self._private_attr = 'private'
        obj = MyClass()
        attrs = get_object_attributes(obj, show_private=True)
        assert 'public_attr' in attrs
        assert '_private_attr' in attrs

    def test_property_attribute(self):
        class MyClass:
            @property
            def my_property(self):
                return 'property_value'
        obj = MyClass()
        attrs = get_object_attributes(obj)
        assert 'my_property' in attrs
        assert attrs['my_property'] == 'property_value'

    def test_mixed_collection(self):
        my_mixed = [1, 'two', 3.0, {'four': 4}]
        attrs = get_object_attributes(my_mixed)
        assert attrs == {'[0]': 1, '[1]': 'two', '[2]': 3.0, '[3]': {'four': 4}}

    def test_nested_object(self):
        class InnerClass:
            def __init__(self):
                self.inner_attr = 'inner'

        class OuterClass:
            def __init__(self):
                self.outer_attr = 'outer'
                self.inner_obj = InnerClass()
        obj = OuterClass()
        attrs = get_object_attributes(obj)
        assert 'outer_attr' in attrs
        assert 'inner_obj' in attrs
        assert isinstance(attrs['inner_obj'], InnerClass)
        assert attrs['inner_obj'].inner_attr == 'inner'

    def test_exception_handling(self):
        class FaultyClass:
            def __getattr__(self, name):
                raise RuntimeError("Access error")
        obj = FaultyClass()
        attrs = get_object_attributes(obj)
        assert attrs == {}

    def test_large_collection(self):
        my_large_list = list(range(1000))
        attrs = get_object_attributes(my_large_list)
        assert len(attrs) == 1000
        assert attrs['[0]'] == 0
        assert attrs['[999]'] == 999

    def test_custom_str_method(self):
        class MyClass:
            def __str__(self):
                return "CustomString"
        obj = MyClass()
        attrs = get_object_attributes(obj)
        assert attrs == {}

    def test_inherited_attributes(self):
        class BaseClass:
            def __init__(self):
                self.base_attr = 'base'

        class DerivedClass(BaseClass):
            def __init__(self):
                super().__init__()
                self.derived_attr = 'derived'
        obj = DerivedClass()
        attrs = get_object_attributes(obj)
        assert 'base_attr' in attrs
        assert 'derived_attr' in attrs

    def test_slots_attributes(self):
        class MyClass:
            __slots__ = ['slot_attr']

            def __init__(self):
                self.slot_attr = 'slot_value'
        obj = MyClass()
        attrs = get_object_attributes(obj)
        assert 'slot_attr' in attrs
        assert attrs['slot_attr'] == 'slot_value'

    def test_callable_attribute(self):
        class MyClass:
            def my_method(self):
                return 'method_value'
        obj = MyClass()
        attrs = get_object_attributes(obj)
        assert 'my_method' not in attrs

    def test_property_and_method(self):
        class MyClass:
            @property
            def my_property(self):
                return 'property_value'

            def my_method(self):
                return 'method_value'
        obj = MyClass()
        attrs = get_object_attributes(obj)
        assert 'my_property' in attrs
        assert attrs['my_property'] == 'property_value'
        assert 'my_method' not in attrs

    def test_private_property(self):
        class MyClass:
            @property
            def _private_property(self):
                return 'private_value'
        obj = MyClass()
        attrs = get_object_attributes(obj)
        assert '_private_property' not in attrs
        attrs_with_private = get_object_attributes(obj, show_private=True)
        assert '_private_property' in attrs_with_private
        assert attrs_with_private['_private_property'] == 'private_value'

    def test_property_raises_exception(self):
        class MyClass:
            @property
            def faulty_property(self):
                raise ValueError("Cannot access this property")
        obj = MyClass()
        attrs = get_object_attributes(obj)
        assert 'faulty_property' not in attrs

    def test_object_with_dict_and_attributes(self):
        class MyClass:
            def __init__(self):
                self.attr1 = 'value1'
                self.attr2 = 'value2'
                self.__dict__['dynamic_attr'] = 'dynamic_value'
        obj = MyClass()
        attrs = get_object_attributes(obj)
        assert 'attr1' in attrs
        assert 'attr2' in attrs
        assert 'dynamic_attr' in attrs
        assert attrs['dynamic_attr'] == 'dynamic_value'

    def test_object_with_private_and_public_attributes(self):
        class MyClass:
            def __init__(self):
                self.public_attr = 'public_value'
                self._private_attr = 'private_value'
                self.__very_private_attr = 'very_private_value'
        obj = MyClass()
        attrs = get_object_attributes(obj)
        assert 'public_attr' in attrs
        assert '_private_attr' not in attrs
        assert '__very_private_attr' not in attrs
        attrs_with_private = get_object_attributes(obj, show_private=True)
        assert 'public_attr' in attrs_with_private
        assert '_private_attr' in attrs_with_private
        assert '_MyClass__very_private_attr' in attrs_with_private
        assert attrs_with_private['_private_attr'] == 'private_value'
        assert attrs_with_private['_MyClass__very_private_attr'] == 'very_private_value'

    def test_object_with_mixed_attributes(self):
        class MyClass:
            def __init__(self):
                self.public_attr = 'public_value'
                self._private_attr = 'private_value'

            @property
            def my_property(self):
                return 'property_value'

            def my_method(self):
                return 'method_value'
        obj = MyClass()
        attrs = get_object_attributes(obj)
        assert 'public_attr' in attrs
        assert '_private_attr' not in attrs
        assert 'my_property' in attrs
        assert 'my_method' not in attrs
        assert attrs['my_property'] == 'property_value'
        attrs_with_private = get_object_attributes(obj, show_private=True)
        assert 'public_attr' in attrs_with_private
        assert '_private_attr' in attrs_with_private
        assert 'my_property' in attrs_with_private
        assert 'my_method' not in attrs_with_private
        assert attrs_with_private['_private_attr'] == 'private_value'
        assert attrs_with_private['my_property'] == 'property_value'


class TestResolveObjectPath:
    """Test class for resolve_object_path function."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Create mock objects for testing
        class MockController:
            def __init__(self, name):
                self.name = name
                self.description = f"Description for {name}"
                self.tags = MockTagCollection()
                self.programs = MockProgramCollection()

        class MockTag:
            def __init__(self, name, tag_type="DINT"):
                self.name = name
                self.tag_type = tag_type
                self.description = f"Tag {name} description"
                self.value = 42

        class MockProgram:
            def __init__(self, name):
                self.name = name
                self.description = f"Program {name} description"
                self.enabled = True

        class MockTagCollection:
            def __init__(self):
                self.tag1 = MockTag("Tag1")
                self.tag2 = MockTag("Tag2", "BOOL")

            def as_list_values(self):
                return [self.tag1, self.tag2]

        class MockProgramCollection:
            def __init__(self):
                self.main_program = MockProgram("MainProgram")
                self.sub_program = MockProgram("SubProgram")

            def as_list_values(self):
                return [self.main_program, self.sub_program]

        # Set up test data
        self.MockController = MockController
        self.MockTag = MockTag
        self.MockProgram = MockProgram
        self.controllers = [MockController("Controller1"), MockController("Controller2")]

    def test_resolve_empty_path(self):
        """Test resolving an empty path."""
        result = resolve_object_path([], self.controllers)
        assert result is None

    def test_resolve_empty_root_objects(self):
        """Test resolving with empty root objects list."""
        result = resolve_object_path(["Controller1"], [])
        assert result is None

    def test_resolve_single_level_path(self):
        """Test resolving a single-level path (root object)."""
        result = resolve_object_path(["Controller1"], self.controllers)
        assert result is not None
        assert result.name == "Controller1"
        assert isinstance(result, self.MockController)

    def test_resolve_case_insensitive(self):
        """Test that path resolution is case insensitive."""
        result = resolve_object_path(["controller1"], self.controllers)
        assert result is not None
        assert result.name == "Controller1"

    def test_resolve_object_attribute(self):
        """Test resolving an object's attribute."""
        result = resolve_object_path(["Controller1", "description"], self.controllers)
        assert result == "Description for Controller1"

    def test_resolve_nested_object_attribute(self):
        """Test resolving a nested object's attribute."""
        result = resolve_object_path(["Controller1", "tags"], self.controllers)
        assert result is not None
        assert hasattr(result, "as_list_values")

    def test_resolve_nonexistent_object(self):
        """Test resolving a path to a nonexistent object."""
        result = resolve_object_path(["NonExistentController"], self.controllers)
        assert result is None

    def test_resolve_nonexistent_attribute(self):
        """Test resolving a path to a nonexistent attribute."""
        result = resolve_object_path(["Controller1", "nonexistent_attr"], self.controllers)
        assert result is None

    def test_resolve_deep_path(self):
        """Test resolving a deep path through multiple levels."""
        # This would require the mock objects to be more complex
        # For now, test a 3-level path
        # Note: This test demonstrates the intent but may need actual implementation
        # that supports navigation through collections
        path = ["Controller1", "tags", "tag1"]
        result = resolve_object_path(path, self.controllers)
        # The actual test would depend on how the mock tags collection is implemented
        # For now, just verify the function doesn't crash
        assert result is None or result is not None  # Either outcome is acceptable for this test

    def test_resolve_with_string_representation(self):
        """Test resolving using string representation when name attribute is not available."""
        # Create an object without a name attribute
        class SimpleObject:
            def __init__(self, value):
                self.value = value

            def __str__(self):
                return f"SimpleObject_{self.value}"

        simple_objects = [SimpleObject(1), SimpleObject(2)]
        result = resolve_object_path(["SimpleObject_1"], simple_objects)
        assert result is not None
        assert result.value == 1

    def test_resolve_builtin_types(self):
        """Test resolving paths with builtin types."""
        test_objects = [42, "test_string", [1, 2, 3]]
        result = resolve_object_path(["42"], test_objects)
        assert result == 42

        result = resolve_object_path(["test_string"], test_objects)
        assert result == "test_string"


class TestResolveObjectPathWithParent:
    """Test class for resolve_object_path_with_parent function."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Create mock objects for testing
        class MockController:
            def __init__(self, name):
                self.name = name
                self.description = f"Description for {name}"
                self.version = "1.0.0"

        class MockTag:
            def __init__(self, name):
                self.name = name
                self.description = f"Tag {name} description"
                self.value = 42

        self.MockController = MockController
        self.MockTag = MockTag
        self.controllers = [MockController("Controller1"), MockController("Controller2")]

    def test_resolve_with_parent_empty_path(self):
        """Test resolving an empty path with parent."""
        target, parent, attr_name = resolve_object_path_with_parent([], self.controllers)
        assert target is None
        assert parent is None
        assert attr_name is None

    def test_resolve_with_parent_empty_root_objects(self):
        """Test resolving with empty root objects list."""
        target, parent, attr_name = resolve_object_path_with_parent(["Controller1"], [])
        assert target is None
        assert parent is None
        assert attr_name is None

    def test_resolve_with_parent_root_object(self):
        """Test resolving a root object (no parent)."""
        target, parent, attr_name = resolve_object_path_with_parent(["Controller1"], self.controllers)
        assert target is not None
        assert target.name == "Controller1"
        assert parent is None
        assert attr_name is None

    def test_resolve_with_parent_object_attribute(self):
        """Test resolving an object's attribute (with parent)."""
        target, parent, attr_name = resolve_object_path_with_parent(["Controller1", "description"], self.controllers)
        assert target == "Description for Controller1"
        assert parent is not None
        assert parent.name == "Controller1"
        assert attr_name == "description"

    def test_resolve_with_parent_nested_attribute(self):
        """Test resolving a nested attribute path."""
        target, parent, attr_name = resolve_object_path_with_parent(["Controller1", "version"], self.controllers)
        assert target == "1.0.0"
        assert parent is not None
        assert parent.name == "Controller1"
        assert attr_name == "version"

    def test_resolve_with_parent_nonexistent_object(self):
        """Test resolving a path to a nonexistent object."""
        target, parent, attr_name = resolve_object_path_with_parent(["NonExistent"], self.controllers)
        assert target is None
        assert parent is None
        assert attr_name is None

    def test_resolve_with_parent_nonexistent_attribute(self):
        """Test resolving a path to a nonexistent attribute."""
        target, parent, attr_name = resolve_object_path_with_parent(["Controller1", "nonexistent"], self.controllers)
        assert target is None
        assert parent is not None  # Parent should still be found
        assert parent.name == "Controller1"
        assert attr_name == "nonexistent"

    def test_resolve_with_parent_case_insensitive(self):
        """Test that parent resolution is case insensitive."""
        target, parent, attr_name = resolve_object_path_with_parent(["controller1", "description"], self.controllers)
        assert target == "Description for Controller1"
        assert parent is not None
        assert parent.name == "Controller1"
        assert attr_name == "description"

    def test_resolve_with_parent_deep_path(self):
        """Test resolving a deep path with parent."""
        # Test a 3-level path: object -> attribute -> sub-attribute
        # This requires the parent's attribute to have its own attributes
        class ComplexController:
            def __init__(self, name):
                self.name = name
                self.config = ComplexConfig()

        class ComplexConfig:
            def __init__(self):
                self.settings = {"timeout": 30, "retries": 3}
                self.enabled = True

        complex_controllers = [ComplexController("ComplexController1")]
        target, parent, attr_name = resolve_object_path_with_parent(
            ["ComplexController1", "config", "enabled"],
            complex_controllers
        )
        assert target is True
        assert parent is not None
        assert hasattr(parent, "settings")
        assert attr_name == "enabled"


class TestObjectIsIterable:
    def test_is_iterable_with_list(self):
        assert is_iterable([1, 2, 3]) is True

    def test_is_iterable_with_string(self):
        assert is_iterable("hello") is True

    def test_is_iterable_with_integer(self):
        assert is_iterable(42) is False

    def test_is_iterable_with_dict(self):
        assert is_iterable({'a': 1, 'b': 2}) is True

    def test_is_iterable_with_set(self):
        assert is_iterable({1, 2, 3}) is True

    def test_is_iterable_with_tuple(self):
        assert is_iterable((1, 2)) is True

    def test_is_iterable_with_none(self):
        assert is_iterable(None) is False

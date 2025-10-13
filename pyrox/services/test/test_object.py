from pyrox.services.object import get_object_attributes


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

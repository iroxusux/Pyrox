import pytest
from pyrox.core.validators import unsafe_assert_is_type


class TestUnsafeAssertIsType:

    def test_expected_values_pass(self):
        unsafe_assert_is_type('string', str)
        unsafe_assert_is_type(0, int)
        unsafe_assert_is_type(0.0, float)
        unsafe_assert_is_type(object(), object)

    def test_custom_classes_pass(self):
        class TestClass:
            def __init__(self) -> None:
                self.a = 1

        unsafe_assert_is_type(TestClass(), TestClass)

    def test_child_classes_all_pass(self):
        class TestClass:
            def __init__(self) -> None:
                self.a = 1

        class ChildClass(TestClass):
            pass

        unsafe_assert_is_type(TestClass(), TestClass)
        unsafe_assert_is_type(ChildClass(), ChildClass)
        unsafe_assert_is_type(ChildClass(), TestClass)

    def test_incorrect_value_raises_value_error_with_message(self):
        with pytest.raises(ValueError) as context:
            unsafe_assert_is_type('string', int)
        assert context.exconly() == f'ValueError: Expected type {str(int)}, but got {str(str)}!'

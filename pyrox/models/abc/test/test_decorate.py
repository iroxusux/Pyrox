"""Unit tests for decorate.py module."""

import unittest
import warnings
import functools
from typing import Callable

from pyrox.models.abc.decorate import deprecated


class TestDeprecatedDecorator(unittest.TestCase):
    """Test cases for deprecated decorator."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear any existing warnings
        warnings.resetwarnings()
        # Ensure warnings are always shown during tests
        warnings.simplefilter("always")

    def tearDown(self):
        """Clean up test fixtures."""
        # Reset warnings to default behavior
        warnings.resetwarnings()

    def test_decorator_basic_usage(self):
        """Test basic usage of deprecated decorator."""
        @deprecated()
        def test_function():
            return "test_result"

        # Test that function still works
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = test_function()

            self.assertEqual(result, "test_result")
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, DeprecationWarning))
            self.assertIn("test_function is deprecated", str(w[0].message))

    def test_decorator_with_reason(self):
        """Test deprecated decorator with reason parameter."""
        reason = "Use new_function instead"

        @deprecated(reason=reason)
        def test_function():
            return "test_result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            test_function()

            self.assertEqual(len(w), 1)
            self.assertIn("test_function is deprecated", str(w[0].message))
            self.assertIn(reason, str(w[0].message))

    def test_decorator_with_version(self):
        """Test deprecated decorator with version parameter."""
        version = "2.0"

        @deprecated(version=version)
        def test_function():
            return "test_result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            test_function()

            self.assertEqual(len(w), 1)
            self.assertIn("test_function is deprecated", str(w[0].message))
            self.assertIn(f"will be removed in version {version}", str(w[0].message))

    def test_decorator_with_reason_and_version(self):
        """Test deprecated decorator with both reason and version."""
        reason = "Use new_function instead"
        version = "2.0"

        @deprecated(reason=reason, version=version)
        def test_function():
            return "test_result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            test_function()

            self.assertEqual(len(w), 1)
            message = str(w[0].message)
            self.assertIn("test_function is deprecated", message)
            self.assertIn(reason, message)
            self.assertIn(f"will be removed in version {version}", message)

    def test_decorator_empty_reason(self):
        """Test deprecated decorator with empty reason."""
        @deprecated(reason="")
        def test_function():
            return "test_result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            test_function()

            self.assertEqual(len(w), 1)
            message = str(w[0].message)
            self.assertEqual(message, "test_function is deprecated")

    def test_decorator_none_reason(self):
        """Test deprecated decorator with None reason."""
        @deprecated(reason=None)
        def test_function():
            return "test_result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            test_function()

            self.assertEqual(len(w), 1)
            message = str(w[0].message)
            self.assertEqual(message, "test_function is deprecated")

    def test_decorator_empty_version(self):
        """Test deprecated decorator with empty version."""
        @deprecated(version="")
        def test_function():
            return "test_result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            test_function()

            self.assertEqual(len(w), 1)
            message = str(w[0].message)
            self.assertEqual(message, "test_function is deprecated: This function is deprecated")

    def test_decorator_none_version(self):
        """Test deprecated decorator with None version."""
        @deprecated(version=None)
        def test_function():
            return "test_result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            test_function()

            self.assertEqual(len(w), 1)
            message = str(w[0].message)
            self.assertEqual(message, "test_function is deprecated: This function is deprecated")

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""
        def original_function():
            """Original function docstring."""
            return "test_result"

        decorated_function = deprecated()(original_function)

        self.assertEqual(decorated_function.__name__, original_function.__name__)
        self.assertEqual(decorated_function.__doc__, original_function.__doc__)
        self.assertEqual(decorated_function.__module__, original_function.__module__)
        self.assertTrue(hasattr(decorated_function, '__wrapped__'))
        self.assertIs(decorated_function.__wrapped__, original_function)

    def test_decorator_with_arguments(self):
        """Test deprecated decorator on function with arguments."""
        @deprecated("Use new_add instead")
        def add_numbers(a, b):
            return a + b

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = add_numbers(2, 3)

            self.assertEqual(result, 5)
            self.assertEqual(len(w), 1)
            self.assertIn("add_numbers is deprecated", str(w[0].message))

    def test_decorator_with_kwargs(self):
        """Test deprecated decorator on function with keyword arguments."""
        @deprecated("Use new_concat instead")
        def concat_strings(*args, separator=" "):
            return separator.join(args)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = concat_strings("hello", "world", separator="-")

            self.assertEqual(result, "hello-world")
            self.assertEqual(len(w), 1)
            self.assertIn("concat_strings is deprecated", str(w[0].message))

    def test_decorator_multiple_calls(self):
        """Test that deprecated warning is issued on each call."""
        @deprecated("Use new_function instead")
        def test_function():
            return "test_result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            test_function()
            test_function()
            test_function()

            self.assertEqual(len(w), 3)
            for warning in w:
                self.assertTrue(issubclass(warning.category, DeprecationWarning))
                self.assertIn("test_function is deprecated", str(warning.message))

    def test_decorator_on_method(self):
        """Test deprecated decorator on class method."""
        class TestClass:
            @deprecated("Use new_method instead")
            def test_method(self):
                return "method_result"

        instance = TestClass()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = instance.test_method()

            self.assertEqual(result, "method_result")
            self.assertEqual(len(w), 1)
            self.assertIn("test_method is deprecated", str(w[0].message))

    def test_decorator_on_static_method(self):
        """Test deprecated decorator on static method."""
        class TestClass:
            @staticmethod
            @deprecated("Use new_static_method instead")
            def test_static_method():
                return "static_result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = TestClass.test_static_method()

            self.assertEqual(result, "static_result")
            self.assertEqual(len(w), 1)
            self.assertIn("test_static_method is deprecated", str(w[0].message))

    def test_decorator_on_class_method(self):
        """Test deprecated decorator on class method."""
        class TestClass:
            @classmethod
            @deprecated("Use new_class_method instead")
            def test_class_method(cls):
                return "class_result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = TestClass.test_class_method()

            self.assertEqual(result, "class_result")
            self.assertEqual(len(w), 1)
            self.assertIn("test_class_method is deprecated", str(w[0].message))

    def test_decorator_with_exception(self):
        """Test deprecated decorator when decorated function raises exception."""
        @deprecated("This function will be removed")
        def failing_function():
            raise ValueError("Test exception")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            with self.assertRaises(ValueError) as context:
                failing_function()

            self.assertEqual(str(context.exception), "Test exception")
            self.assertEqual(len(w), 1)
            self.assertIn("failing_function is deprecated", str(w[0].message))

    def test_decorator_warning_category(self):
        """Test that correct warning category is used."""
        @deprecated()
        def test_function():
            return "test"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            test_function()

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, DeprecationWarning))
            self.assertEqual(w[0].category, DeprecationWarning)

    def test_decorator_with_lambda(self):
        """Test deprecated decorator on lambda function."""
        deprecated_lambda = deprecated("Lambda is deprecated")(lambda x: x * 2)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = deprecated_lambda(5)

            self.assertEqual(result, 10)
            self.assertEqual(len(w), 1)
            self.assertIn("<lambda> is deprecated", str(w[0].message))

    def test_decorator_nested_calls(self):
        """Test deprecated decorator with nested function calls."""
        @deprecated("Outer function is deprecated")
        def outer_function():
            return inner_function()

        @deprecated("Inner function is deprecated")
        def inner_function():
            return "nested_result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = outer_function()

            self.assertEqual(result, "nested_result")
            self.assertEqual(len(w), 2)  # Both functions should warn

            messages = [str(warning.message) for warning in w]
            self.assertTrue(any("outer_function is deprecated" in msg for msg in messages))
            self.assertTrue(any("inner_function is deprecated" in msg for msg in messages))

    def test_decorator_return_type(self):
        """Test that decorator returns callable."""
        def test_function():
            return "test"

        decorated: Callable = deprecated()(test_function)

        self.assertTrue(callable(decorated))
        self.assertIsInstance(decorated, Callable)  # type: ignore

    def test_decorator_factory_return_type(self):
        """Test that decorator factory returns decorator."""
        decorator = deprecated("Test reason", "1.0")

        self.assertTrue(callable(decorator))

        def test_function():
            return "test"

        decorated = decorator(test_function)
        self.assertTrue(callable(decorated))

    def test_message_formatting(self):
        """Test various message formatting scenarios."""
        test_cases = [
            # (reason, version, expected_parts)
            ("Use new_func", "2.0", ["is deprecated", "Use new_func", "version 2.0"]),
            ("Use new_func", None, ["is deprecated", "Use new_func"]),
            (None, "2.0", ["is deprecated", "version 2.0"]),
            ("", "", ["is deprecated"]),
            ("", "2.0", ["is deprecated", "version 2.0"]),
            ("Use new_func", "", ["is deprecated", "Use new_func"]),
        ]

        for reason, version, expected_parts in test_cases:
            with self.subTest(reason=reason, version=version):
                @deprecated(reason=reason, version=version)
                def test_func():
                    pass

                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    test_func()

                    self.assertEqual(len(w), 1)
                    message = str(w[0].message)

                    for part in expected_parts:
                        self.assertIn(part, message)

    def test_decorator_with_complex_function_signature(self):
        """Test decorator on function with complex signature."""
        @deprecated("Complex function is deprecated")
        def complex_function(a, b=None, *args, c=42, **kwargs):
            return {
                'a': a,
                'b': b,
                'args': args,
                'c': c,
                'kwargs': kwargs
            }

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = complex_function(1, 2, 3, 4, c=99, extra="value")

            expected = {
                'a': 1,
                'b': 2,
                'args': (3, 4),
                'c': 99,
                'kwargs': {'extra': 'value'}
            }

            self.assertEqual(result, expected)
            self.assertEqual(len(w), 1)
            self.assertIn("complex_function is deprecated", str(w[0].message))

    def test_warnings_integration(self):
        """Test integration with warnings module features."""
        @deprecated("Test warning integration")
        def test_function():
            return "result"

        # Test with warnings filtered
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            result = test_function()

            # Function should still work even with warnings filtered
            self.assertEqual(result, "result")

    def test_functools_wraps_integration(self):
        """Test proper integration with functools.wraps."""
        def original_function(x, y=10):
            """Original function docstring.

            Args:
                x: First parameter
                y: Second parameter with default

            Returns:
                Sum of x and y
            """
            return x + y

        decorated = deprecated("Test functools integration")(original_function)

        # Test that functools.wraps preserved all metadata
        self.assertEqual(decorated.__name__, "original_function")
        self.assertEqual(decorated.__doc__, original_function.__doc__)
        self.assertEqual(decorated.__module__, original_function.__module__)
        self.assertEqual(decorated.__qualname__, original_function.__qualname__)
        self.assertEqual(decorated.__annotations__, original_function.__annotations__)

        # Test that __wrapped__ is properly set
        self.assertTrue(hasattr(decorated, '__wrapped__'))
        self.assertIs(decorated.__wrapped__, original_function)

    def test_decorator_on_generator_function(self):
        """Test deprecated decorator on generator function."""
        @deprecated("Generator is deprecated")
        def test_generator():
            yield 1
            yield 2
            yield 3

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            gen = test_generator()

            # Warning should be issued when function is called, not when generator is consumed
            self.assertEqual(len(w), 1)
            self.assertIn("test_generator is deprecated", str(w[0].message))

            # Generator should work normally
            result = list(gen)
            self.assertEqual(result, [1, 2, 3])

    def test_decorator_on_async_function(self):
        """Test deprecated decorator on async function."""
        import asyncio

        @deprecated("Async function is deprecated")
        async def async_test_function():
            await asyncio.sleep(0)  # Minimal async operation
            return "async_result"

        async def run_test():
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = await async_test_function()

                self.assertEqual(result, "async_result")
                self.assertEqual(len(w), 1)
                self.assertIn("async_test_function is deprecated", str(w[0].message))

        # Run the async test
        asyncio.run(run_test())

    def test_multiple_decorators_compatibility(self):
        """Test compatibility with other decorators."""
        def another_decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                return f"decorated_{result}"
            return wrapper

        @another_decorator
        @deprecated("Function with multiple decorators is deprecated")
        def test_function():
            return "result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = test_function()

            self.assertEqual(result, "decorated_result")
            self.assertEqual(len(w), 1)
            self.assertIn("test_function is deprecated", str(w[0].message))

    def test_edge_case_special_characters_in_messages(self):
        """Test edge cases with special characters in messages."""
        special_reason = "Use new_func() instead: it's better! @deprecated #legacy"
        special_version = "2.0-beta.1"

        @deprecated(reason=special_reason, version=special_version)
        def test_function():
            return "result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            test_function()

            self.assertEqual(len(w), 1)
            message = str(w[0].message)
            self.assertIn(special_reason, message)
            self.assertIn(special_version, message)


class TestDeprecatedDecoratorEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for deprecated decorator."""

    def setUp(self):
        """Set up test fixtures."""
        warnings.resetwarnings()
        warnings.simplefilter("always")

    def tearDown(self):
        """Clean up test fixtures."""
        warnings.resetwarnings()

    def test_decorator_with_non_string_reason(self):
        """Test deprecated decorator with non-string reason."""
        # The decorator should handle non-string reasons gracefully
        @deprecated(reason=123)
        def test_function():
            return "result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = test_function()

            self.assertEqual(result, "result")
            self.assertEqual(len(w), 1)
            message = str(w[0].message)
            self.assertIn("test_function is deprecated", message)
            self.assertIn("123", message)

    def test_decorator_with_non_string_version(self):
        """Test deprecated decorator with non-string version."""
        @deprecated(version=2.0)
        def test_function():
            return "result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = test_function()

            self.assertEqual(result, "result")
            self.assertEqual(len(w), 1)
            message = str(w[0].message)
            self.assertIn("test_function is deprecated", message)
            self.assertIn("2.0", message)

    def test_warnings_with_custom_formatwarning(self):
        """Test deprecated decorator with custom warning formatting."""
        original_formatwarning = warnings.formatwarning

        def custom_formatwarning(message, category, filename, lineno, line=None):
            return f"CUSTOM: {message}\n"

        try:
            warnings.formatwarning = custom_formatwarning

            @deprecated("Custom format test")
            def test_function():
                return "result"

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                test_function()

                self.assertEqual(len(w), 1)
                self.assertIn("test_function is deprecated", str(w[0].message))

        finally:
            warnings.formatwarning = original_formatwarning


if __name__ == '__main__':
    unittest.main(verbosity=2)

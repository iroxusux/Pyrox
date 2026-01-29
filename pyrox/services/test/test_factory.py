"""Unit tests for the factory service module.

This module contains comprehensive tests for the factory service functions,
ensuring proper functionality for factory module reloading and type preservation.
"""

import sys
import unittest
from unittest.mock import patch
import types

from pyrox.services.factory import reload_factory_module_while_preserving_registered_types
from pyrox.models.factory import MetaFactory


class TestReloadFactoryWhilePreservingRegisteredTypes(unittest.TestCase):
    """Test cases for the reload_factory_while_preserving_registered_types function."""

    def setUp(self):
        """Set up test environment."""
        # Create a mock factory class using MetaFactory
        class MockFactory(MetaFactory):
            pass

        self.MockFactory = MockFactory
        self.MockFactory.__module__ = 'test_module'

        # Create mock registered types
        self.mock_types = {
            'TestType1': str,
            'TestType2': int,
            'CustomClass': type('CustomClass', (), {})
        }
        self.MockFactory._registered_types = self.mock_types.copy()

    def tearDown(self):
        """Clean up test environment."""
        # Clean up any modules we might have added during testing
        modules_to_remove = [mod for mod in sys.modules.keys() if mod.startswith('test_module')]
        for mod in modules_to_remove:
            if mod in sys.modules:
                del sys.modules[mod]

    def test_successful_reload_preserves_types(self):
        """Test that successful reload preserves registered types."""
        # Create a mock module and add it to sys.modules
        mock_module = types.ModuleType('test_module')
        # Add the MockFactory to the module so it can be found after reload
        setattr(mock_module, 'MockFactory', self.MockFactory)
        sys.modules['test_module'] = mock_module

        with patch('importlib.reload') as mock_reload:
            mock_reload.return_value = mock_module

            # Call the function
            reloaded_factory = reload_factory_module_while_preserving_registered_types(self.MockFactory)

            # Verify importlib.reload was called
            mock_reload.assert_called_once_with(mock_module)

            # Verify registered types were preserved
            self.assertEqual(reloaded_factory._registered_types, self.mock_types)

    def test_module_not_in_sys_modules_raises_import_error(self):
        """Test that missing module in sys.modules raises ImportError."""
        # Ensure the module is not in sys.modules
        module_name = 'nonexistent_module'
        self.MockFactory.__module__ = module_name

        if module_name in sys.modules:
            del sys.modules[module_name]

        with self.assertRaises(ImportError) as context:
            reload_factory_module_while_preserving_registered_types(self.MockFactory)

        self.assertIn(f"Module {module_name} not found in sys.modules", str(context.exception))

    def test_reload_failure_propagates_exception(self):
        """Test that importlib.reload failure propagates the exception."""
        # Create a mock module and add it to sys.modules
        mock_module = types.ModuleType('test_module')
        sys.modules['test_module'] = mock_module

        with patch('importlib.reload') as mock_reload:
            mock_reload.side_effect = ImportError("Reload failed")

            with self.assertRaises(ImportError) as context:
                reload_factory_module_while_preserving_registered_types(self.MockFactory)

            self.assertIn("Reload failed", str(context.exception))

    def test_registered_types_copied_before_reload(self):
        """Test that registered types are properly copied before reload."""
        # Create a mock module and add it to sys.modules
        mock_module = types.ModuleType('test_module')
        # Add the MockFactory to the module so it can be found after reload
        setattr(mock_module, 'MockFactory', self.MockFactory)
        sys.modules['test_module'] = mock_module

        original_types = self.MockFactory._registered_types
        original_id = id(original_types)

        with patch('importlib.reload') as mock_reload:
            mock_reload.return_value = mock_module

            # Modify registered types during reload simulation
            def side_effect(module):
                # Simulate module reload clearing the factory's types
                self.MockFactory._registered_types = {}
                return module

            mock_reload.side_effect = side_effect

            # Call the function
            reloaded_factory = reload_factory_module_while_preserving_registered_types(self.MockFactory)

            # Verify that types were restored (not the same object, but same content)
            self.assertEqual(reloaded_factory._registered_types, self.mock_types)
            self.assertNotEqual(id(reloaded_factory._registered_types), original_id)

    def test_empty_registered_types_handled_correctly(self):
        """Test that empty registered types dictionary is handled correctly."""
        # Set empty registered types
        self.MockFactory._registered_types = {}

        # Create a mock module and add it to sys.modules
        mock_module = types.ModuleType('test_module')
        # Add the MockFactory to the module so it can be found after reload
        setattr(mock_module, 'MockFactory', self.MockFactory)
        sys.modules['test_module'] = mock_module

        with patch('importlib.reload') as mock_reload:
            mock_reload.return_value = mock_module

            # Call the function
            reloaded_factory = reload_factory_module_while_preserving_registered_types(self.MockFactory)

            # Verify empty dict was preserved
            self.assertEqual(reloaded_factory._registered_types, {})
            mock_reload.assert_called_once()

    def test_factory_with_none_module_name(self):
        """Test behavior when factory __module__ is None."""
        self.MockFactory.__module__ = None  # type: ignore

        # This should trigger an ImportError since None won't be in sys.modules
        with self.assertRaises(ImportError) as context:
            reload_factory_module_while_preserving_registered_types(self.MockFactory)

        self.assertIn("Module None not found in sys.modules", str(context.exception))

    @patch('importlib.reload')
    def test_multiple_calls_preserve_latest_types(self, mock_reload):
        """Test that multiple calls preserve the latest registered types."""
        # Setup mock module
        mock_module = types.ModuleType('test_module')
        # Add the MockFactory to the module so it can be found after reload
        setattr(mock_module, 'MockFactory', self.MockFactory)
        sys.modules['test_module'] = mock_module
        mock_reload.return_value = mock_module

        # First call
        reloaded_factory = reload_factory_module_while_preserving_registered_types(self.MockFactory)
        self.assertEqual(reloaded_factory._registered_types, self.mock_types)

        # Modify registered types
        new_types = {'NewType': type('NewType', (), {})}
        reloaded_factory._registered_types = new_types

        # Second call
        reloaded_factory2 = reload_factory_module_while_preserving_registered_types(reloaded_factory)
        self.assertEqual(reloaded_factory2._registered_types, new_types)

        # Verify reload was called twice
        self.assertEqual(mock_reload.call_count, 2)

    def test_factory_subclass_behavior(self):
        """Test behavior with factory subclasses."""
        # Use the existing MockFactory but rename it for this test
        SubclassFactory = self.MockFactory
        SubclassFactory.__module__ = 'custom_module'
        custom_types = {'CustomType': type('CustomType', (), {})}
        SubclassFactory._registered_types = custom_types

        # Create mock module
        mock_module = types.ModuleType('custom_module')
        # Add the SubclassFactory to the module so it can be found after reload
        setattr(mock_module, 'MockFactory', SubclassFactory)  # Use the same class name as setUp
        sys.modules['custom_module'] = mock_module

        with patch('importlib.reload') as mock_reload:
            mock_reload.return_value = mock_module

            reloaded_factory = reload_factory_module_while_preserving_registered_types(SubclassFactory)

            self.assertEqual(reloaded_factory._registered_types, custom_types)

    def test_registered_types_mutation_during_reload(self):
        """Test that modifications to registered types during reload are handled."""
        mock_module = types.ModuleType('test_module')
        # Add the MockFactory to the module so it can be found after reload
        setattr(mock_module, 'MockFactory', self.MockFactory)
        sys.modules['test_module'] = mock_module

        # Store reference to original types
        original_types_ref = self.MockFactory._registered_types

        def reload_side_effect(module):
            # Simulate external modification of registered types during reload
            original_types_ref.clear()
            original_types_ref.update({'ModifiedType': str})
            return module

        with patch('importlib.reload', side_effect=reload_side_effect):
            reloaded_factory = reload_factory_module_while_preserving_registered_types(self.MockFactory)

            # Original types should be restored, overwriting modifications
            self.assertEqual(reloaded_factory._registered_types, self.mock_types)

    def test_sys_modules_modification_during_execution(self):
        """Test behavior when sys.modules is modified during execution."""
        mock_module = types.ModuleType('test_module')
        # Add the MockFactory to the module so it can be found after reload
        setattr(mock_module, 'MockFactory', self.MockFactory)
        sys.modules['test_module'] = mock_module

        def reload_side_effect(module):
            # Remove module from sys.modules during reload
            if 'test_module' in sys.modules:
                del sys.modules['test_module']
            return module

        with patch('importlib.reload', side_effect=reload_side_effect):
            # Should still work as we already have the module reference
            reloaded_factory = reload_factory_module_while_preserving_registered_types(self.MockFactory)

            self.assertEqual(reloaded_factory._registered_types, self.mock_types)


class TestFactoryServicesEdgeCases(unittest.TestCase):
    """Edge case tests for factory services."""

    def setUp(self):
        """Set up edge case test environment."""
        self.test_module_name = 'edge_case_test_module'

    def tearDown(self):
        """Clean up edge case test environment."""
        if self.test_module_name in sys.modules:
            del sys.modules[self.test_module_name]

    def test_factory_missing_registered_types_attribute(self):
        """Test edge case where _registered_types attribute is missing."""
        class TestFactory(metaclass=MetaFactory):
            pass

        # MetaFactory should automatically create _registered_types, but let's test the edge case
        # where it somehow doesn't exist by removing it
        if hasattr(TestFactory, '_registered_types'):
            original_types = TestFactory._registered_types
            delattr(TestFactory, '_registered_types')

        TestFactory.__module__ = self.test_module_name

        # Should raise AttributeError when trying to access _registered_types
        with self.assertRaises(AttributeError):
            reload_factory_module_while_preserving_registered_types(TestFactory)

        # Restore for cleanup
        if 'original_types' in locals():
            TestFactory._registered_types = original_types  # type: ignore

    def test_factory_without_registered_types(self):
        """Test behavior when factory doesn't have _registered_types attribute."""
        class FactoryWithoutTypes(metaclass=MetaFactory):
            pass

        # Remove the _registered_types attribute if it exists
        if hasattr(FactoryWithoutTypes, '_registered_types'):
            delattr(FactoryWithoutTypes, '_registered_types')

        FactoryWithoutTypes.__module__ = self.test_module_name

        mock_module = types.ModuleType(self.test_module_name)
        sys.modules[self.test_module_name] = mock_module

        # Should raise AttributeError when trying to access _registered_types
        with self.assertRaises(AttributeError):
            reload_factory_module_while_preserving_registered_types(FactoryWithoutTypes)

    def test_invalid_factory_parameters(self):
        """Test behavior with invalid factory parameter types."""
        # Test with None - should raise AttributeError when accessing __module__
        with self.assertRaises(AttributeError):
            reload_factory_module_while_preserving_registered_types(None)  # type: ignore

        # Test with string - should raise AttributeError when accessing __module__
        with self.assertRaises(AttributeError):
            reload_factory_module_while_preserving_registered_types("not a factory")  # type: ignore

        # Test with int - should raise AttributeError when accessing __module__
        with self.assertRaises(AttributeError):
            reload_factory_module_while_preserving_registered_types(42)  # type: ignore

    def test_large_registered_types_dict(self):
        """Test performance with large registered types dictionary."""
        class LargeFactory(MetaFactory):
            pass

        # Create a large dictionary of types
        large_types = {f'Type{i}': type(f'Type{i}', (), {}) for i in range(100)}
        LargeFactory._registered_types = large_types.copy()
        LargeFactory.__module__ = self.test_module_name

        # Create mock module and add the factory class to it
        mock_module = types.ModuleType(self.test_module_name)
        setattr(mock_module, 'LargeFactory', LargeFactory)  # Add factory to mock module
        sys.modules[self.test_module_name] = mock_module

        with patch('importlib.reload') as mock_reload:
            mock_reload.return_value = mock_module

            # Should handle large dictionaries efficiently
            reloaded_factory = reload_factory_module_while_preserving_registered_types(LargeFactory)

            # Verify all types were preserved
            self.assertEqual(len(reloaded_factory._registered_types), 100)
            self.assertEqual(reloaded_factory._registered_types, large_types)
            # Ensure every class object is the same as before reload
            for key in large_types:
                self.assertIs(reloaded_factory._registered_types[key], large_types[key], f"Type {key} was not preserved after reload")

    def test_nested_type_objects(self):
        """Test with complex nested type objects."""
        class ComplexFactory(MetaFactory):
            pass

        # Create nested complex types
        class OuterClass:
            class InnerClass:
                pass

        complex_types = {
            'OuterClass': OuterClass,
            'InnerClass': OuterClass.InnerClass,
            'GenericType': type('GenericType', (object,), {'attr': 'value'})
        }

        ComplexFactory._registered_types = complex_types
        ComplexFactory.__module__ = self.test_module_name

        mock_module = types.ModuleType(self.test_module_name)
        setattr(mock_module, 'ComplexFactory', ComplexFactory)  # Add factory to mock module
        sys.modules[self.test_module_name] = mock_module

        with patch('importlib.reload') as mock_reload:
            mock_reload.return_value = mock_module

            reloaded_factory = reload_factory_module_while_preserving_registered_types(ComplexFactory)

            # Verify complex types were preserved correctly
            self.assertEqual(reloaded_factory._registered_types, complex_types)
            self.assertIs(reloaded_factory._registered_types['OuterClass'], OuterClass)
            self.assertIs(reloaded_factory._registered_types['InnerClass'], OuterClass.InnerClass)


if __name__ == '__main__':
    unittest.main(verbosity=2)

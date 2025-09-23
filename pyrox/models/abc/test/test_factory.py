"""Unit tests for factory.py module."""
import sys
import unittest
from unittest.mock import MagicMock, patch

from pyrox.models.abc.factory import (
    FactoryTypeMeta,
    MetaFactory,
)
from pyrox.models.abc.logging import Loggable


class TestMetaFactory(unittest.TestCase):
    """Test cases for MetaFactory class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a test factory class for each test
        class TestFactory(MetaFactory):
            pass

        self.TestFactory = TestFactory
        # Clear any registered types
        self.TestFactory._registered_types = {}

    def tearDown(self):
        """Clean up test fixtures."""
        # Clear registered types after each test
        if hasattr(self.TestFactory, '_registered_types'):
            self.TestFactory._registered_types.clear()

    def test_inheritance(self):
        """Test that MetaFactory inherits from ABCMeta and Loggable."""
        from abc import ABCMeta

        self.assertTrue(issubclass(MetaFactory, ABCMeta))
        self.assertTrue(issubclass(MetaFactory, Loggable))

    def test_init_subclass_initializes_registered_types(self):
        """Test that __init_subclass__ initializes _registered_types."""
        class NewFactory(MetaFactory):
            pass

        self.assertTrue(hasattr(NewFactory, '_registered_types'))
        self.assertIsInstance(NewFactory._registered_types, dict)
        self.assertEqual(len(NewFactory._registered_types), 0)

    def test_get_class_from_module_direct_lookup(self):
        """Test _get_class_from_module with direct class lookup."""
        # Create a mock module with a test class
        mock_module = MagicMock()
        mock_module.TestClass = str  # Use str as a test class

        result = self.TestFactory._get_class_from_module(mock_module, 'TestClass')

        self.assertEqual(result, str)

    def test_get_class_from_module_not_found(self):
        """Test _get_class_from_module when class is not found."""
        mock_module = MagicMock()
        mock_module.configure_mock(**{'hasattr.return_value': False})

        # Remove the NonexistentClass attribute to simulate it not existing
        del mock_module.NonexistentClass

        result = self.TestFactory._get_class_from_module(mock_module, 'NonexistentClass')

        self.assertIsNone(result)

    def test_reload_class_module_success(self):
        """Test _reload_class_module with successful reload."""
        # Create a test class
        class TestClass:
            __name__ = 'TestClass'
            __module__ = 'test_module'

        with patch('importlib.reload') as mock_reload:
            with patch.object(self.TestFactory, '_get_class_from_module') as mock_get_class:
                with patch.object(self.TestFactory, 'register_type') as mock_register:
                    # Create a real module-like object
                    import types
                    mock_module = types.ModuleType('test_module')

                    with patch.object(sys, 'modules', {'test_module': mock_module}):
                        mock_get_class.return_value = TestClass

                        result = self.TestFactory._reload_class_module(TestClass)

                        mock_reload.assert_called_once_with(mock_module)
                        mock_get_class.assert_called_once_with(mock_module, 'TestClass')
                        mock_register.assert_called_once_with(TestClass)
                        self.assertEqual(result, TestClass)

    def test_reload_class_module_class_not_found_after_reload(self):
        """Test _reload_class_module when class not found after reload."""
        class TestClass:
            __name__ = 'TestClass'
            __module__ = 'test_module'

        # Create a real module-like object
        import types
        mock_module = types.ModuleType('test_module')

        with patch.object(sys, 'modules', {'test_module': mock_module}):
            with patch('pyrox.models.abc.factory.importlib.reload') as mock_reload:  # Patch in the specific module
                with patch.object(self.TestFactory, '_get_class_from_module', return_value=None):

                    with self.assertRaises(ImportError) as context:
                        self.TestFactory._reload_class_module(TestClass)

                    self.assertIn('Class TestClass not found', str(context.exception))
                    mock_reload.assert_called_once_with(mock_module)

    def test_reload_class_module_reload_fails(self):
        """Test _reload_class_module when reload raises exception."""
        class TestClass:
            __name__ = 'TestClass'
            __module__ = 'test_module'

        with patch.object(sys, 'modules', {'test_module': MagicMock()}):
            with patch('importlib.reload', side_effect=Exception("Reload failed")):

                with self.assertRaises(ImportError) as context:
                    self.TestFactory._reload_class_module(TestClass)

                self.assertIn('Failed to reload module test_module', str(context.exception))

    def test_reload_class_module_not_in_sys_modules(self):
        """Test _reload_class_module when module not in sys.modules."""
        class TestClass:
            __name__ = 'TestClass'
            __module__ = 'test_module'

        with patch.object(sys, 'modules', {}):
            result = self.TestFactory._reload_class_module(TestClass)

            self.assertEqual(result, TestClass)

    def test_create_instance_success(self):
        """Test create_instance with registered type."""
        class TestType:
            def __init__(self, value):
                self.value = value

        self.TestFactory._registered_types['TestType'] = TestType

        instance = self.TestFactory.create_instance('TestType', 'test_value')

        self.assertIsInstance(instance, TestType)
        self.assertEqual(instance.value, 'test_value')

    def test_create_instance_with_kwargs(self):
        """Test create_instance with keyword arguments."""
        class TestType:
            def __init__(self, value, name=None):
                self.value = value
                self.name = name

        self.TestFactory._registered_types['TestType'] = TestType

        instance = self.TestFactory.create_instance('TestType', 'test_value', name='test_name')

        self.assertIsInstance(instance, TestType)
        self.assertEqual(instance.value, 'test_value')
        self.assertEqual(instance.name, 'test_name')

    def test_create_instance_type_not_found(self):
        """Test create_instance when type is not registered."""
        instance = self.TestFactory.create_instance('NonexistentType')

        self.assertIsNone(instance)

    def test_get_available_types(self):
        """Test get_available_types method."""
        class Type1:
            pass

        class Type2:
            pass

        self.TestFactory._registered_types = {
            'Type1': Type1,
            'Type2': Type2
        }

        types = self.TestFactory.get_available_types()

        self.assertEqual(set(types), {'Type1', 'Type2'})

    def test_get_available_types_empty(self):
        """Test get_available_types when no types registered."""
        types = self.TestFactory.get_available_types()

        self.assertEqual(types, [])

    def test_get_registered_type_with_string(self):
        """Test get_registered_type with string parameter."""
        class TestType:
            pass

        self.TestFactory._registered_types['TestType'] = TestType

        result = self.TestFactory.get_registered_type('TestType')

        self.assertEqual(result, TestType)

    def test_get_registered_type_with_object(self):
        """Test get_registered_type with object parameter."""
        class TestType:
            pass

        self.TestFactory._registered_types['TestType'] = TestType
        test_instance = TestType()

        result = self.TestFactory.get_registered_type(test_instance)

        self.assertEqual(result, TestType)

    def test_get_registered_type_not_found(self):
        """Test get_registered_type when type not found."""
        result = self.TestFactory.get_registered_type('NonexistentType')

        self.assertIsNone(result)

    def test_get_registered_type_by_supporting_class_with_object(self):
        """Test get_registered_type_by_supporting_class with object."""
        class SupportedClass:
            pass

        class TestType:
            supporting_class = 'SupportedClass'

        self.TestFactory._registered_types['SupportedClass'] = TestType
        supported_instance = SupportedClass()

        with patch.object(self.TestFactory, '_reload_class_module', return_value=TestType) as mock_reload:
            result = self.TestFactory.get_registered_type_by_supporting_class(supported_instance)

            self.assertEqual(result, TestType)
            mock_reload.assert_called_once_with(TestType)

    def test_get_registered_type_by_supporting_class_with_type(self):
        """Test get_registered_type_by_supporting_class with type."""
        class SupportedClass:
            pass

        class TestType:
            supporting_class = 'SupportedClass'

        # Register by the supporting_class name, not the class name
        self.TestFactory._registered_types['SupportedClass'] = TestType

        with patch.object(self.TestFactory, '_reload_class_module', return_value=TestType):
            result = self.TestFactory.get_registered_type_by_supporting_class(SupportedClass)

            self.assertEqual(result, TestType)

    def test_get_registered_type_by_supporting_class_with_string(self):
        """Test get_registered_type_by_supporting_class with string."""
        class TestType:
            supporting_class = 'SupportedClass'

        self.TestFactory._registered_types['TestType'] = TestType

        with patch.object(self.TestFactory, '_reload_class_module', return_value=TestType):
            result = self.TestFactory.get_registered_type_by_supporting_class('SupportedClass')

            self.assertEqual(result, TestType)

    def test_get_registered_type_by_supporting_class_not_found(self):
        """Test get_registered_type_by_supporting_class when not found."""
        class TestType:
            supporting_class = 'DifferentClass'

        self.TestFactory._registered_types['TestType'] = TestType

        result = self.TestFactory.get_registered_type_by_supporting_class('SupportedClass')

        self.assertIsNone(result)

    def test_get_registered_type_by_supporting_class_no_supporting_class_attr(self):
        """Test get_registered_type_by_supporting_class when class has no supporting_class."""
        class TestType:
            pass  # No supporting_class attribute

        self.TestFactory._registered_types['TestType'] = TestType

        result = self.TestFactory.get_registered_type_by_supporting_class('SupportedClass')

        self.assertIsNone(result)

    def test_get_registered_type_by_supporting_class_invalid_parameter(self):
        """Test get_registered_type_by_supporting_class with invalid parameter."""
        with self.assertRaises(ValueError) as context:
            self.TestFactory.get_registered_type_by_supporting_class(123)

        self.assertIn('supporting_class must be a string, type, or an object instance', str(context.exception))

    def test_get_registered_types(self):
        """Test get_registered_types method."""
        class Type1:
            pass

        class Type2:
            pass

        expected_types = {'Type1': Type1, 'Type2': Type2}
        self.TestFactory._registered_types = expected_types

        result = self.TestFactory.get_registered_types()

        self.assertEqual(result, expected_types)

    def test_get_registered_types_no_attribute(self):
        """Test get_registered_types when _registered_types doesn't exist."""
        delattr(self.TestFactory, '_registered_types')

        result = self.TestFactory.get_registered_types()

        self.assertEqual(result, {})

    def test_register_type_success(self):
        """Test register_type with valid type."""
        class TestType:
            __name__ = 'TestType'

        self.TestFactory.register_type(TestType)

        self.assertIn('TestType', self.TestFactory._registered_types)
        self.assertEqual(self.TestFactory._registered_types['TestType'], TestType)

    def test_register_type_with_supporting_class(self):
        """Test register_type with type that has supporting_class."""
        class TestType:
            __name__ = 'TestType'
            supporting_class = 'SupportedClass'

        self.TestFactory.register_type(TestType)

        self.assertIn('SupportedClass', self.TestFactory._registered_types)
        self.assertEqual(self.TestFactory._registered_types['SupportedClass'], TestType)

    def test_register_type_supporting_class_empty(self):
        """Test register_type when supporting_class is empty."""
        class TestType:
            __name__ = 'TestType'
            supporting_class = ''

        self.TestFactory.register_type(TestType)

        # Should fall back to __name__
        self.assertIn('TestType', self.TestFactory._registered_types)
        self.assertEqual(self.TestFactory._registered_types['TestType'], TestType)

    def test_register_type_supporting_class_none(self):
        """Test register_type when supporting_class is None."""
        class TestType:
            __name__ = 'TestType'
            supporting_class = None

        self.TestFactory.register_type(TestType)

        # Should fall back to __name__
        self.assertIn('TestType', self.TestFactory._registered_types)
        self.assertEqual(self.TestFactory._registered_types['TestType'], TestType)

    def test_register_type_no_registered_types_attribute(self):
        """Test register_type when _registered_types doesn't exist."""
        delattr(self.TestFactory, '_registered_types')

        class TestType:
            pass

        with self.assertRaises(RuntimeError) as context:
            self.TestFactory.register_type(TestType)

        self.assertIn('Factory TestFactory is not properly initialized', str(context.exception))

    def test_multiple_factories_independence(self):
        """Test that multiple factory classes are independent."""
        class Factory1(MetaFactory):
            pass

        class Factory2(MetaFactory):
            pass

        class Type1:
            pass

        class Type2:
            pass

        Factory1.register_type(Type1)
        Factory2.register_type(Type2)

        self.assertIn('Type1', Factory1.get_registered_types())
        self.assertNotIn('Type1', Factory2.get_registered_types())
        self.assertIn('Type2', Factory2.get_registered_types())
        self.assertNotIn('Type2', Factory1.get_registered_types())

    def test_logger_integration(self):
        """Test that MetaFactory properly integrates with logging."""
        self.assertTrue(hasattr(self.TestFactory, 'logger'))
        self.assertIsNotNone(self.TestFactory.logger)


class TestFactoryTypeMeta(unittest.TestCase):
    """Test cases for FactoryTypeMeta class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a test factory
        class TestFactory(MetaFactory):
            pass

        self.TestFactory = TestFactory
        self.TestFactory._registered_types = {}

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up any registered types
        if hasattr(self.TestFactory, '_registered_types'):
            self.TestFactory._registered_types.clear()

    def test_inheritance(self):
        """Test that FactoryTypeMeta inherits from ABCMeta and Loggable."""
        from abc import ABCMeta
        from typing import Generic

        self.assertTrue(issubclass(FactoryTypeMeta, ABCMeta))
        self.assertTrue(issubclass(FactoryTypeMeta, Loggable))
        self.assertTrue(issubclass(FactoryTypeMeta, Generic))

    def test_class_attributes(self):
        """Test default class attributes."""
        self.assertIsNone(FactoryTypeMeta.supporting_class)
        self.assertTrue(FactoryTypeMeta.supports_registering)

    def test_new_with_registration_disabled(self):
        """Test __new__ when supports_registering is False."""
        class TestType(metaclass=FactoryTypeMeta):
            supports_registering = False

            @classmethod
            def get_factory(cls):
                return self.TestFactory

        # Should not be registered
        self.assertEqual(len(self.TestFactory.get_registered_types()), 0)

    def test_new_with_no_factory(self):
        """Test __new__ when get_factory returns None."""
        class TestType(metaclass=FactoryTypeMeta):
            @classmethod
            def get_factory(cls):
                return None

        # Should not be registered
        self.assertEqual(len(self.TestFactory.get_registered_types()), 0)

    def test_new_with_successful_registration(self):
        """Test __new__ with successful registration."""
        class TestType(metaclass=FactoryTypeMeta):
            @classmethod
            def get_factory(cls):
                return self.TestFactory

        # Should be registered
        self.assertIn('TestType', self.TestFactory.get_registered_types())
        self.assertEqual(self.TestFactory.get_registered_types()['TestType'], TestType)

    def test_get_factory_not_implemented(self):
        """Test that get_factory raises NotImplementedError."""
        with self.assertRaises(NotImplementedError) as context:
            FactoryTypeMeta.get_factory()

        self.assertIn('Subclasses must implement get_factory', str(context.exception))

    def test_init_method(self):
        """Test __init__ method."""
        # This is mostly about ensuring the method exists and calls super()
        # The actual functionality is tested through class creation

        class TestType(metaclass=FactoryTypeMeta):
            test_attr = 'test'

            @classmethod
            def get_factory(cls):
                return self.TestFactory

        self.assertEqual(TestType.test_attr, 'test')

    def test_logger_integration(self):
        """Test that FactoryTypeMeta properly integrates with logging."""
        self.assertTrue(hasattr(FactoryTypeMeta, 'logger'))
        self.assertIsNotNone(FactoryTypeMeta.logger)

    def test_supporting_class_inheritance(self):
        """Test supporting_class attribute inheritance."""
        class BaseType(metaclass=FactoryTypeMeta):
            supporting_class = str

            @classmethod
            def get_factory(cls):
                return self.TestFactory

        class DerivedType(BaseType):
            pass

        self.assertEqual(BaseType.supporting_class, str)
        self.assertEqual(DerivedType.supporting_class, str)

    def test_supports_registering_inheritance(self):
        """Test supports_registering attribute inheritance."""
        class BaseType(metaclass=FactoryTypeMeta):
            supports_registering = False

            @classmethod
            def get_factory(cls):
                return self.TestFactory

        class DerivedType(BaseType):
            pass

        self.assertFalse(BaseType.supports_registering)
        self.assertFalse(DerivedType.supports_registering)


class TestIntegration(unittest.TestCase):
    """Integration tests for factory module components."""

    def setUp(self):
        """Set up test fixtures."""
        class TestFactory(MetaFactory):
            pass

        self.TestFactory = TestFactory
        self.TestFactory._registered_types = {}

    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self.TestFactory, '_registered_types'):
            self.TestFactory._registered_types.clear()

    def test_complete_factory_workflow(self):
        """Test complete workflow from registration to instance creation."""
        # Define a type with FactoryTypeMeta
        class TestWidget(metaclass=FactoryTypeMeta):
            def __init__(self, name, value=None):
                self.name = name
                self.value = value

            @classmethod
            def get_factory(cls):
                return self.TestFactory

        # Verify registration
        self.assertIn('TestWidget', self.TestFactory.get_registered_types())

        # Create instance through factory
        instance = self.TestFactory.create_instance('TestWidget', 'test_widget', value=42)

        self.assertIsInstance(instance, TestWidget)
        self.assertEqual(instance.name, 'test_widget')
        self.assertEqual(instance.value, 42)

    def test_supporting_class_workflow(self):
        """Test workflow with supporting_class attribute."""
        class Controller:
            pass

        class WidgetController(metaclass=FactoryTypeMeta):
            supporting_class = Controller

            def __init__(self, name):
                self.name = name

            @classmethod
            def get_factory(cls):
                return self.TestFactory

        registered_types = self.TestFactory.get_registered_types()

        # Should be registered by Controller name, not class name
        self.assertIn(Controller, registered_types)
        self.assertNotIn(WidgetController, registered_types)
        self.assertEqual(registered_types[Controller], WidgetController)

        # Test retrieval by supporting class
        controller_instance = Controller()  # Create instance of Controller, not WidgetController
        with patch.object(self.TestFactory, '_reload_class_module', return_value=WidgetController):
            result = self.TestFactory.get_registered_type_by_supporting_class(controller_instance)
            self.assertEqual(result, WidgetController)

        # Also test with the Controller class directly
        with patch.object(self.TestFactory, '_reload_class_module', return_value=WidgetController):
            result = self.TestFactory.get_registered_type_by_supporting_class(Controller)
            self.assertEqual(result, WidgetController)

    def test_multiple_types_same_factory(self):
        """Test multiple types registered to same factory."""
        class Widget1(metaclass=FactoryTypeMeta):
            @classmethod
            def get_factory(cls):
                return self.TestFactory

        class Widget2(metaclass=FactoryTypeMeta):
            @classmethod
            def get_factory(cls):
                return self.TestFactory

        class Widget3(metaclass=FactoryTypeMeta):
            @classmethod
            def get_factory(cls):
                return self.TestFactory

        registered_types = self.TestFactory.get_registered_types()

        self.assertEqual(len(registered_types), 3)
        self.assertIn('Widget1', registered_types)
        self.assertIn('Widget2', registered_types)
        self.assertIn('Widget3', registered_types)

    def test_inheritance_with_factory_types(self):
        """Test inheritance patterns with factory types."""
        class BaseWidget(metaclass=FactoryTypeMeta):
            def __init__(self, name):
                self.name = name

            @classmethod
            def get_factory(cls):
                return self.TestFactory

        class SpecialWidget(BaseWidget):
            def __init__(self, name, special_value):
                super().__init__(name)
                self.special_value = special_value

        # Both should be registered
        registered_types = self.TestFactory.get_registered_types()
        self.assertIn('BaseWidget', registered_types)
        self.assertIn('SpecialWidget', registered_types)

        # Create instances
        base_instance = self.TestFactory.create_instance('BaseWidget', 'base')
        special_instance = self.TestFactory.create_instance('SpecialWidget', 'special', 'special_val')

        self.assertIsInstance(base_instance, BaseWidget)
        self.assertIsInstance(special_instance, SpecialWidget)
        self.assertEqual(special_instance.special_value, 'special_val')

    def test_factory_type_discovery(self):
        """Test discovering available factory types."""
        class Type1(metaclass=FactoryTypeMeta):
            @classmethod
            def get_factory(cls):
                return self.TestFactory

        class Type2(metaclass=FactoryTypeMeta):
            @classmethod
            def get_factory(cls):
                return self.TestFactory

        class Type3(metaclass=FactoryTypeMeta):
            supports_registering = False  # This shouldn't appear

            @classmethod
            def get_factory(cls):
                return self.TestFactory

        available_types = self.TestFactory.get_available_types()

        self.assertEqual(set(available_types), {'Type1', 'Type2'})
        self.assertNotIn('Type3', available_types)

    def test_error_handling_in_registration(self):
        """Test error handling during type registration."""
        # Test with a factory that doesn't have _registered_types
        class BadFactory(MetaFactory):
            pass

        delattr(BadFactory, '_registered_types')

        with self.assertRaises(RuntimeError):
            class BadType(metaclass=FactoryTypeMeta):
                @classmethod
                def get_factory(cls):
                    return BadFactory

    def test_module_reloading_integration(self):
        """Test module reloading functionality."""
        # Create a mock type with module info
        class TestType:
            __name__ = 'TestType'
            __module__ = 'test_module'
            supporting_class = 'TestClass'

        # Register it
        self.TestFactory.register_type(TestType)

        # Create a real module-like object and add the TestType to it
        import types
        mock_module = types.ModuleType('test_module')
        mock_module.TestType = TestType

        with patch.object(sys, 'modules', {'test_module': mock_module}):
            with patch('pyrox.models.abc.factory.importlib.reload') as mock_reload:
                # Test getting by supporting class (which triggers reload)
                result = self.TestFactory.get_registered_type_by_supporting_class('TestClass')

                mock_reload.assert_called_once_with(mock_module)
                self.assertEqual(result, TestType)

    def test_complex_type_hierarchy(self):
        """Test complex type hierarchy with factory registration."""
        class BaseController(metaclass=FactoryTypeMeta):
            supporting_class = 'Controller'

            @classmethod
            def get_factory(cls):
                return self.TestFactory

        class DatabaseController(BaseController):
            supporting_class = 'DatabaseController'

        class APIController(BaseController):
            supporting_class = 'APIController'

        class SpecialAPIController(APIController):
            supporting_class = 'SpecialAPIController'

        registered_types = self.TestFactory.get_registered_types()

        # All should be registered by their supporting_class names
        self.assertIn('Controller', registered_types)
        self.assertIn('DatabaseController', registered_types)
        self.assertIn('APIController', registered_types)
        self.assertIn('SpecialAPIController', registered_types)

        # Test instance creation
        api_instance = self.TestFactory.create_instance('APIController')
        self.assertIsInstance(api_instance, APIController)

    def test_logging_integration_during_registration(self):
        """Test logging integration during type registration."""
        with patch.object(FactoryTypeMeta, 'logger') as mock_logger:
            class LoggedType(metaclass=FactoryTypeMeta):
                @classmethod
                def get_factory(cls):
                    return self.TestFactory

            # Should log debug message about registration
            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args[0][0]
            self.assertIn('Registering class LoggedType', call_args)

    def test_generic_type_support(self):
        """Test that generic types work with the factory system."""
        from typing import Generic, TypeVar

        T = TypeVar('T')

        class GenericWidget(Generic[T], metaclass=FactoryTypeMeta):
            def __init__(self, item: T):
                self.item = item

            @classmethod
            def get_factory(cls):
                return self.TestFactory

        # Should be registered
        self.assertIn('GenericWidget', self.TestFactory.get_registered_types())

        # Create instance (Python doesn't enforce generic types at runtime)
        instance = self.TestFactory.create_instance('GenericWidget', "test_string")
        self.assertIsInstance(instance, GenericWidget)
        self.assertEqual(instance.item, "test_string")

    def test_factory_isolation(self):
        """Test that different factories are properly isolated."""
        class Factory1(MetaFactory):
            pass

        class Factory2(MetaFactory):
            pass

        class Type1(metaclass=FactoryTypeMeta):
            @classmethod
            def get_factory(cls):
                return Factory1

        class Type2(metaclass=FactoryTypeMeta):
            @classmethod
            def get_factory(cls):
                return Factory2

        # Each factory should only have its own types
        self.assertIn('Type1', Factory1.get_registered_types())
        self.assertNotIn('Type2', Factory1.get_registered_types())

        self.assertIn('Type2', Factory2.get_registered_types())
        self.assertNotIn('Type1', Factory2.get_registered_types())

        # Instance creation should work correctly
        instance1 = Factory1.create_instance('Type1')
        instance2 = Factory2.create_instance('Type2')

        self.assertIsInstance(instance1, Type1)
        self.assertIsInstance(instance2, Type2)

        # Cross-factory creation should fail
        self.assertIsNone(Factory1.create_instance('Type2'))
        self.assertIsNone(Factory2.create_instance('Type1'))


if __name__ == '__main__':
    unittest.main(verbosity=2)

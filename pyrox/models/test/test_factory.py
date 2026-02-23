"""Unit tests for factory.py module."""
import sys
import types
import unittest
from abc import abstractmethod
from typing import Generic, TypeVar
from unittest.mock import MagicMock, patch

from pyrox.interfaces.protocols.meta import IFactoryMixinProtocolMeta
from pyrox.models.factory import (
    FactoryTypeMeta,
    MetaFactory,
)


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
        if hasattr(self.TestFactory, '_registered_types'):
            self.TestFactory._registered_types.clear()
        if hasattr(self.TestFactory, '_base_type'):
            del self.TestFactory._base_type

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

        # Create a real module-like object
        import types
        mock_module = types.ModuleType('test_module')
        mock_module.TestClass = TestClass  # Add the class to the module  # type: ignore
        self.TestFactory._registered_types['TestClass'] = TestClass

        with patch.object(sys, 'modules', {'test_module': mock_module}):
            with patch('pyrox.models.factory.importlib.reload') as mock_reload:
                with patch.object(self.TestFactory, 'register_type') as mock_register:
                    # Mock reload to return the module (this is what importlib.reload actually does)
                    mock_reload.return_value = mock_module

                    result = self.TestFactory._reload_class_module(TestClass)

                    mock_reload.assert_called_once_with(mock_module)
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
            with patch('pyrox.models.factory.importlib.reload') as mock_reload:  # Patch in the specific module
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
            with self.assertRaises(ImportError) as context:
                _ = self.TestFactory._reload_class_module(TestClass)
            self.assertIn('Module test_module not found in sys.modules', str(context.exception))

    def test_create_instance_success(self):
        """Test create_instance with registered type."""
        class TestType:
            def __init__(self, value):
                self.value = value

        self.TestFactory._registered_types['TestType'] = TestType

        instance = self.TestFactory.create_instance('TestType', 'test_value')

        self.assertIsInstance(instance, TestType)
        self.assertEqual(instance.value, 'test_value')  # type: ignore

    def test_create_instance_with_kwargs(self):
        """Test create_instance with keyword arguments."""
        class TestType:
            def __init__(self, value, name=None):
                self.value = value
                self.name = name

        self.TestFactory._registered_types['TestType'] = TestType

        instance = self.TestFactory.create_instance('TestType', 'test_value', name='test_name')

        self.assertIsInstance(instance, TestType)
        self.assertEqual(instance.value, 'test_value')  # type: ignore
        self.assertEqual(instance.name, 'test_name')  # type: ignore

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
            supporting_class = SupportedClass

        self.TestFactory._registered_types['SupportedClass'] = TestType
        supported_instance = SupportedClass()

        with patch.object(self.TestFactory, '_reload_class_module', return_value=TestType) as mock_reload:
            result = self.TestFactory.get_registered_type_by_supporting_class(supported_instance, True)

            self.assertEqual(result, TestType)
            mock_reload.assert_called_once_with(TestType)

    def test_get_registered_type_by_supporting_class_with_type(self):
        """Test get_registered_type_by_supporting_class with type."""
        class SupportedClass:
            pass

        class TestType:
            supporting_class = SupportedClass

        # Register by the supporting_class name, not the class name
        self.TestFactory._registered_types['SupportedClass'] = TestType

        with patch.object(self.TestFactory, '_reload_class_module', return_value=TestType):
            result = self.TestFactory.get_registered_type_by_supporting_class(SupportedClass, True)

            self.assertEqual(result, TestType)

    def test_get_registered_type_by_supporting_class_with_string(self):
        """Test get_registered_type_by_supporting_class with string."""
        class TestType:
            supporting_class = 'SupportedClass'

        self.TestFactory._registered_types['TestType'] = TestType

        with patch.object(self.TestFactory, '_reload_class_module', return_value=TestType):
            result = self.TestFactory.get_registered_type_by_supporting_class('SupportedClass')

            self.assertIsNone(result)  # Because supporting_class is a string, not a type

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

        self.assertIn('TestType', self.TestFactory._registered_types)
        self.assertEqual(self.TestFactory._registered_types['TestType'], TestType)

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

    # ------------------------------------------------------------------
    # _base_type enforcement
    # ------------------------------------------------------------------

    def test_register_type_accepts_subclass_when_base_type_set(self):
        """register_type accepts a subclass of _base_type."""
        class Base:
            pass

        class Sub(Base):
            pass

        self.TestFactory._base_type = Base
        self.TestFactory.register_type(Sub)

        self.assertIn('Sub', self.TestFactory._registered_types)

    def test_register_type_rejects_non_subclass_when_base_type_set(self):
        """register_type raises TypeError when type is not a subclass of _base_type."""
        class Base:
            pass

        class Unrelated:
            pass

        self.TestFactory._base_type = Base

        with self.assertRaises(TypeError) as ctx:
            self.TestFactory.register_type(Unrelated)

        self.assertIn('subclass', str(ctx.exception))

    def test_register_type_accepts_base_type_itself(self):
        """register_type accepts _base_type itself (issubclass(X, X) is True)."""
        class Base:
            pass

        self.TestFactory._base_type = Base
        self.TestFactory.register_type(Base)

        self.assertIn('Base', self.TestFactory._registered_types)

    def test_register_type_no_base_type_accepts_anything(self):
        """When _base_type is not set, any type can be registered."""
        class Anything:
            pass

        self.TestFactory.register_type(Anything)
        self.assertIn('Anything', self.TestFactory._registered_types)


class TestFactoryTypeMeta(unittest.TestCase):
    """Test cases for FactoryTypeMeta class."""

    def setUp(self):
        class TestFactory(MetaFactory):
            pass
        self.TestFactory = TestFactory

    def tearDown(self):
        if hasattr(self.TestFactory, '_registered_types'):
            self.TestFactory._registered_types.clear()
        if hasattr(self.TestFactory, '_base_type'):
            del self.TestFactory._base_type

    # ------------------------------------------------------------------
    # Metaclass structure
    # ------------------------------------------------------------------

    def test_inherits_from_IFactoryMixinProtocolMeta(self):
        """FactoryTypeMeta must be a subclass of IFactoryMixinProtocolMeta to
        resolve the Protocol / ABCMeta diamond when bases use Protocol."""
        self.assertTrue(issubclass(FactoryTypeMeta, IFactoryMixinProtocolMeta))

    def test_bound_factory_is_none_by_default(self):
        """Bare FactoryTypeMeta carries no factory binding."""
        self.assertIsNone(FactoryTypeMeta._bound_factory)

    # ------------------------------------------------------------------
    # __class_getitem__
    # ------------------------------------------------------------------

    def test_class_getitem_returns_metaclass_subclass(self):
        """FactoryTypeMeta[F] returns a subclass of FactoryTypeMeta."""
        BoundMeta = FactoryTypeMeta[self.TestFactory]
        self.assertTrue(issubclass(BoundMeta, FactoryTypeMeta))

    def test_class_getitem_binds_factory(self):
        """The returned metaclass carries the specified factory."""
        BoundMeta = FactoryTypeMeta[self.TestFactory]
        self.assertIs(BoundMeta._bound_factory, self.TestFactory)

    def test_class_getitem_rejects_non_type(self):
        with self.assertRaises(TypeError):
            FactoryTypeMeta['not_a_type']  # type: ignore

    def test_each_parameterisation_is_independent(self):
        """Two FactoryTypeMeta[F] calls with different factories are independent."""
        class Factory1(MetaFactory):
            pass

        class Factory2(MetaFactory):
            pass

        Meta1 = FactoryTypeMeta[Factory1]
        Meta2 = FactoryTypeMeta[Factory2]

        self.assertIs(Meta1._bound_factory, Factory1)
        self.assertIs(Meta2._bound_factory, Factory2)

    # ------------------------------------------------------------------
    # No bound factory → nothing registered
    # ------------------------------------------------------------------

    def test_no_bound_factory_class_not_registered(self):
        """A class using bare FactoryTypeMeta is not added to any factory."""
        class UnboundType(metaclass=FactoryTypeMeta):
            pass

        self.assertEqual(len(self.TestFactory.get_registered_types()), 0)

    # ------------------------------------------------------------------
    # Abstract vs concrete registration
    # ------------------------------------------------------------------

    def test_abstract_base_not_registered_but_anchors_base_type(self):
        """The abstract base sets _base_type but is not itself registered."""
        BoundMeta = FactoryTypeMeta[self.TestFactory]

        class AbstractBase(metaclass=BoundMeta):
            @abstractmethod
            def run(self): ...

        self.assertNotIn('AbstractBase', self.TestFactory.get_registered_types())
        self.assertIs(self.TestFactory._base_type, AbstractBase)

    def test_concrete_subclass_auto_registered(self):
        """A concrete subclass is automatically registered on class definition."""
        BoundMeta = FactoryTypeMeta[self.TestFactory]

        class AbstractBase(metaclass=BoundMeta):
            @abstractmethod
            def run(self): ...

        class ConcreteImpl(AbstractBase):
            def run(self): pass

        self.assertIn('ConcreteImpl', self.TestFactory.get_registered_types())
        self.assertIs(self.TestFactory.get_registered_types()['ConcreteImpl'], ConcreteImpl)

    def test_concrete_base_registered_and_anchors_base_type(self):
        """A concrete first class is registered and anchors _base_type."""
        BoundMeta = FactoryTypeMeta[self.TestFactory]

        class ConcreteBase(metaclass=BoundMeta):
            pass

        self.assertIn('ConcreteBase', self.TestFactory.get_registered_types())
        self.assertIs(self.TestFactory._base_type, ConcreteBase)

    def test_multiple_concrete_subclasses_all_registered(self):
        """Every concrete subclass of the abstract base is registered."""
        BoundMeta = FactoryTypeMeta[self.TestFactory]

        class AbstractBase(metaclass=BoundMeta):
            @abstractmethod
            def run(self): ...

        class Impl1(AbstractBase):
            def run(self): pass

        class Impl2(AbstractBase):
            def run(self): pass

        class Impl3(AbstractBase):
            def run(self): pass

        registered = self.TestFactory.get_registered_types()
        self.assertIn('Impl1', registered)
        self.assertIn('Impl2', registered)
        self.assertIn('Impl3', registered)
        self.assertEqual(len(registered), 3)

    # ------------------------------------------------------------------
    # Type enforcement
    # ------------------------------------------------------------------

    def test_unrelated_type_rejected_by_register_type(self):
        """Manually registering an unrelated type after _base_type is anchored raises TypeError."""
        BoundMeta = FactoryTypeMeta[self.TestFactory]

        class AbstractBase(metaclass=BoundMeta):
            @abstractmethod
            def run(self): ...

        class Intruder:
            pass

        with self.assertRaises(TypeError):
            self.TestFactory.register_type(Intruder)


class TestIntegration(unittest.TestCase):
    """Integration tests for factory module components."""

    # Each test creates its own factory to avoid _base_type state bleed.
    def _make_factory(self):
        class F(MetaFactory):
            pass
        return F

    # ------------------------------------------------------------------
    # Basic workflow
    # ------------------------------------------------------------------

    def test_complete_workflow(self):
        """Registration → lookup → instantiation using a bound metaclass."""
        F = self._make_factory()
        BoundMeta = FactoryTypeMeta[F]

        class Widget(metaclass=BoundMeta):
            @abstractmethod
            def render(self): ...

        class ButtonWidget(Widget):
            def __init__(self, label: str):
                self.label = label

            def render(self): pass

        self.assertIn('ButtonWidget', F.get_registered_types())
        instance = F.create_instance('ButtonWidget', 'OK')
        self.assertIsInstance(instance, ButtonWidget)
        self.assertEqual(instance.label, 'OK')  # type: ignore

    # ------------------------------------------------------------------
    # Inheritance
    # ------------------------------------------------------------------

    def test_concrete_base_and_subclass_both_registered(self):
        """When the base is concrete, both it and its subclass register."""
        F = self._make_factory()
        BoundMeta = FactoryTypeMeta[F]

        class BaseWidget(metaclass=BoundMeta):
            def __init__(self, name: str):
                self.name = name

        class SpecialWidget(BaseWidget):
            def __init__(self, name: str, value: int):
                super().__init__(name)
                self.value = value

        registered = F.get_registered_types()
        self.assertIn('BaseWidget', registered)
        self.assertIn('SpecialWidget', registered)

        special = F.create_instance('SpecialWidget', 'special', 99)
        self.assertIsInstance(special, SpecialWidget)
        self.assertEqual(special.value, 99)  # type: ignore

    def test_deep_inheritance_chain(self):
        """Concrete classes at every level of a deep hierarchy are registered."""
        F = self._make_factory()
        BoundMeta = FactoryTypeMeta[F]

        class Base(metaclass=BoundMeta):
            @abstractmethod
            def run(self): ...

        class Mid(Base):
            def run(self): pass

        class Leaf(Mid):
            pass

        registered = F.get_registered_types()
        self.assertNotIn('Base', registered)
        self.assertIn('Mid', registered)
        self.assertIn('Leaf', registered)

    def test_abstract_intermediate_not_registered(self):
        """An intermediate abstract class is skipped."""
        F = self._make_factory()
        BoundMeta = FactoryTypeMeta[F]

        class Root(metaclass=BoundMeta):
            @abstractmethod
            def run(self): ...

        class AbstractMid(Root):
            @abstractmethod
            def extra(self): ...

        class Concrete(AbstractMid):
            def run(self): pass
            def extra(self): pass

        registered = F.get_registered_types()
        self.assertNotIn('Root', registered)
        self.assertNotIn('AbstractMid', registered)
        self.assertIn('Concrete', registered)

    def test_multiple_concrete_subclasses_same_factory(self):
        """Multiple concrete subclasses all register into the same factory."""
        F = self._make_factory()
        BoundMeta = FactoryTypeMeta[F]

        class Base(metaclass=BoundMeta):
            @abstractmethod
            def run(self): ...

        class Task1(Base):
            def run(self): pass

        class Task2(Base):
            def run(self): pass

        class Task3(Base):
            def run(self): pass

        registered = F.get_registered_types()
        self.assertEqual(len(registered), 3)
        self.assertIn('Task1', registered)
        self.assertIn('Task2', registered)
        self.assertIn('Task3', registered)

    # ------------------------------------------------------------------
    # Factory isolation
    # ------------------------------------------------------------------

    def test_two_factories_are_isolated(self):
        """Types wired to different factories are kept separate."""
        F1 = self._make_factory()
        F2 = self._make_factory()
        Meta1 = FactoryTypeMeta[F1]
        Meta2 = FactoryTypeMeta[F2]

        class Base1(metaclass=Meta1):
            @abstractmethod
            def run(self): ...

        class Type1(Base1):
            def run(self): pass

        class Base2(metaclass=Meta2):
            @abstractmethod
            def run(self): ...

        class Type2(Base2):
            def run(self): pass

        self.assertIn('Type1', F1.get_registered_types())
        self.assertNotIn('Type2', F1.get_registered_types())
        self.assertIn('Type2', F2.get_registered_types())
        self.assertNotIn('Type1', F2.get_registered_types())

        self.assertIsNone(F1.create_instance('Type2'))
        self.assertIsNone(F2.create_instance('Type1'))

    # ------------------------------------------------------------------
    # Type enforcement
    # ------------------------------------------------------------------

    def test_unrelated_type_rejected_at_registration(self):
        """Manually registering a type unrelated to _base_type raises TypeError."""
        F = self._make_factory()
        BoundMeta = FactoryTypeMeta[F]

        class Base(metaclass=BoundMeta):
            @abstractmethod
            def run(self): ...

        class Outsider:
            pass

        with self.assertRaises(TypeError):
            F.register_type(Outsider)

    def test_uninitialised_factory_raises_on_registration(self):
        """A factory whose _registered_types was deleted raises RuntimeError."""
        F = self._make_factory()
        delattr(F, '_registered_types')

        class SomeType:
            pass

        with self.assertRaises(RuntimeError):
            F.register_type(SomeType)

    # ------------------------------------------------------------------
    # supporting_class lookup
    # ------------------------------------------------------------------

    def test_supporting_class_lookup(self):
        """Types can be retrieved by their supporting_class attribute."""
        F = self._make_factory()
        BoundMeta = FactoryTypeMeta[F]

        class Controller:
            pass

        class Base(metaclass=BoundMeta):
            @abstractmethod
            def run(self): ...

        class ControllerAdapter(Base):
            supporting_class = Controller
            def run(self): pass

        self.assertIs(F.get_registered_type_by_supporting_class(Controller), ControllerAdapter)
        self.assertIs(F.get_registered_type_by_supporting_class(Controller()), ControllerAdapter)

    # ------------------------------------------------------------------
    # Generic types
    # ------------------------------------------------------------------

    def test_generic_class_registered(self):
        """Generic[T] subclasses integrate transparently with the factory."""
        T = TypeVar('T')
        F = self._make_factory()
        BoundMeta = FactoryTypeMeta[F]

        class Base(metaclass=BoundMeta):
            @abstractmethod
            def process(self): ...

        class Container(Base, Generic[T]):
            def __init__(self, item: T):
                self.item = item

            def process(self): pass

        self.assertIn('Container', F.get_registered_types())
        instance = F.create_instance('Container', 'hello')
        self.assertEqual(instance.item, 'hello')  # type: ignore

    # ------------------------------------------------------------------
    # Module reloading
    # ------------------------------------------------------------------

    def test_module_reloading_integration(self):
        """_reload_class_module re-registers the refreshed class."""
        F = self._make_factory()

        class Controller:
            pass

        class MyAdapter:
            supporting_class = Controller

        MyAdapter.__module__ = 'test_module'  # needed so _reload_class_module can locate it
        F.register_type(MyAdapter)

        mock_module = types.ModuleType('test_module')
        mock_module.MyAdapter = MyAdapter  # type: ignore

        with patch.object(sys, 'modules', {'test_module': mock_module}):
            with patch('pyrox.models.factory.importlib.reload') as mock_reload:
                mock_reload.return_value = mock_module
                result = F.get_registered_type_by_supporting_class(Controller, reload_class=True)
                mock_reload.assert_called_once_with(mock_module)
                self.assertIs(result, MyAdapter)


if __name__ == '__main__':
    unittest.main(verbosity=2)

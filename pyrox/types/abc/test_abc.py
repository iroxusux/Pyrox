"""testing module for abc classes
    """
import copy
from tkinter import Tk, Toplevel, Frame, LabelFrame, Menu, TclError
from typing import Callable
import unittest


from .application import (
    PartialApplicationTask,
    BaseMenu,
    PartialApplication,
    PartialApplicationConfiguration
)


from .factory import Factory

from .list import (
    HashList,
    SafeList,
    TrackedList
)


from .meta import (
    _IdGenerator,
    Buildable,
    ConsolePanelHandler,
    EnforcesNaming,
    ExceptionContextManager,
    Loggable,
    LoggableUnitTest,
    PartialViewConfiguration,
    PartialViewType,
    Runnable,
    SnowFlake,
    PartialView,
    DEF_WIN_TITLE
)


from .model import PartialModel


__all__ = (
    'TestMeta',
)


class TestMeta(unittest.TestCase):
    """test class for meta module
    """

    def test_id_generator(self):
        """test id generator generates unique ids
        """
        curr_value = _IdGenerator.curr_value()
        self.assertIsInstance(_IdGenerator.curr_value(), int)
        self.assertEqual(_IdGenerator.curr_value(), curr_value)

        x = _IdGenerator.get_id()
        self.assertEqual(_IdGenerator.curr_value(), curr_value+1)
        y = _IdGenerator.get_id()
        self.assertEqual(_IdGenerator.curr_value(), curr_value+2)

        # check that new objects get new values
        self.assertNotEqual(x, y)

    def test_snowflake(self):
        """test snowflakes generate with unique ids
        """
        x = SnowFlake()
        self.assertIsInstance(x.id, int)
        y = SnowFlake()
        self.assertIsInstance(y.id, int)

        self.assertNotEqual(x.id, y.id)

        # create list for testing
        my_list = [x]

        # check __hash__ function by checking if obj in list
        # check second obj not in list
        self.assertTrue(x in my_list)
        self.assertFalse(y in my_list)

        z = copy.copy(x)

        # check eq and neq
        self.assertTrue(x is not z)
        self.assertTrue(x == z)
        self.assertTrue(x is not y)
        self.assertTrue(x != y)
        self.assertTrue(y is not z)
        self.assertTrue(y != z)

        # add second obj
        my_list.append(y)

        # check again
        self.assertTrue(x in my_list)
        self.assertTrue(y in my_list)
        self.assertTrue(z in my_list)  # check the copy is attributed to the list

    def test_partial_view_builds(self):
        """test partial view builds
        """

        # test root build
        x = PartialView(config=PartialViewConfiguration(view_type=PartialViewType.ROOT))
        self.assertTrue(x.parent.winfo_exists())
        self.assertNotEqual(x.parent.children, {})

        # check all attrs
        self.assertIsInstance(x.name, str)
        self.assertIsInstance(x.parent, (Tk, Toplevel, Frame, LabelFrame))
        self.assertIsInstance(x.frame, Frame)
        self.assertIsInstance(x.config, PartialViewConfiguration)
        self.assertEqual(x.name, x.parent.title())

        x.close()
        self.assertEqual(x.parent.children, {})

        # validate the second attempt to close throws the expected err
        with self.assertRaises(TclError) as context:
            x.close()
        self.assertTrue(isinstance(context.exception, TclError))

        # test top level build
        x = PartialView(config=PartialViewConfiguration(view_type=PartialViewType.TOPLEVEL))
        self.assertTrue(x.parent.winfo_exists())
        self.assertNotEqual(x.parent.children, {})

        # check all attrs
        self.assertIsInstance(x.name, str)
        self.assertIsInstance(x.parent, (Tk, Toplevel, Frame, LabelFrame))
        self.assertIsInstance(x.frame, Frame)
        self.assertIsInstance(x.config, PartialViewConfiguration)

        # add some children to the view's frame
        a = Frame(x.frame)
        b = Frame(x.frame)
        c = Frame(x.frame)

        a.pack()
        b.pack()
        c.pack()

        self.assertTrue(len(x.frame.children) == 3)
        x.clear()
        self.assertTrue(len(x.frame.children) == 3)

        x.close()
        self.assertEqual(x.parent.children, {})

        # test an invalid view type can't be built
        with self.assertRaises(ValueError) as context:
            x = PartialView(config=PartialViewConfiguration(view_type=PartialViewType.NA))
        self.assertTrue(isinstance(context.exception, ValueError))

        # test a non-dict object can't be passed for config
        with self.assertRaises(AttributeError) as context:
            PartialView(config=None)
        self.assertTrue(isinstance(context.exception, AttributeError))

    def test_enforces_naming(self):
        '''test enforces naming class
        '''
        x = EnforcesNaming()

        self.assertTrue(x.is_valid_string('This_is_a_valid_string'))
        self.assertFalse(x.is_valid_string('This-is_not_a_valid_string'))
        self.assertFalse(x.is_valid_string('This_is_not_a_valid_string!'))

    def test_hash_list(self):
        """test hash works as intended
        """
        class TestClass:
            """test class for unit testing"""

            def __init__(self, name: str, value: int):
                self.name = name
                self.value = value
        val1 = TestClass('value1', 1)
        val2 = TestClass('value2', 2)
        val3 = TestClass('value3', 3)
        val4 = TestClass('value4', 4)

        my_list = HashList('name')
        my_list.append(val1)
        self.assertTrue(len(my_list) == 1)
        my_list.append(val2)
        self.assertTrue(len(my_list) == 2)
        my_list.append(val3)
        self.assertTrue(len(my_list) == 3)
        my_list.append(val3)
        self.assertTrue(len(my_list) == 3)
        my_list.remove(val3)
        self.assertTrue(len(my_list) == 2)
        my_list.remove(val4)
        self.assertTrue(len(my_list) == 2)
        my_list.append(val3)
        self.assertTrue(len(my_list) == 3)
        self.assertIsNotNone(my_list.by_key('value1'))
        self.assertIsNotNone(my_list.by_key('value2'))
        self.assertIsNotNone(my_list.by_key('value3'))
        self.assertIsNone(my_list.by_key('value4'))

        # test iterable
        self.assertIsNotNone(iter(my_list))

        # test contains
        self.assertTrue(val1 in my_list)
        self.assertTrue(val2 in my_list)
        self.assertTrue(val3 in my_list)
        self.assertFalse(val4 in my_list)

        # test slots / instances
        self.assertIsInstance(my_list.hash_key, str)
        self.assertIsInstance(my_list.hashes, dict)
        self.assertIsInstance(my_list.subscribers, list)

    def test_loggable(self):
        """test loggable class
        """
        class TestLog(Loggable):
            """test class for unit testing
            """

        # test logger inherits class name for naming
        x = TestLog()
        self.assertEqual(x.logger.name, TestLog.__name__)

        # test logger uses supplied name for naming
        name = 'TestLog_CustomName1'
        x = TestLog(name)
        self.assertEqual(x.logger.name, name)

        # test logger uses console panel handler correctly
        setattr(self, 'console_panel_handler_passed', False)

        def callback(*_, **__):
            setattr(self, 'console_panel_handler_passed', True)

        y = ConsolePanelHandler(callback)
        x.add_handler(y)
        x.info('abc')
        self.assertTrue(getattr(self, 'console_panel_handler_passed'))

        def new_callback(*_, **__):
            pass

        self.assertIsInstance(y._callback, Callable)  # pylint: disable=protected-access
        y.set_callback(new_callback)
        self.assertIsInstance(y._callback, Callable)  # pylint: disable=protected-access
        self.assertEqual(new_callback, y._callback)  # pylint: disable=protected-access

    def test_loggable_unittest(self):
        """test loggable unittest class
        """
        x = LoggableUnitTest()
        self.assertEqual(x.logger.name, 'LoggableUnitTest')

        class _MyTestLogger(LoggableUnitTest):
            ...

        y = _MyTestLogger()

        self.assertEqual(y.logger.name, '_MyTestLogger')

    def test_buildable(self):
        """test buildable class
        """
        class _TestClass(Buildable):

            def __init__(self):
                super().__init__()
                self.build_good = False
                self.refresh_good = False

            def build(self):
                self.build_good = True

            def refresh(self):
                self.refresh_good = True

        x = _TestClass()

        self.assertFalse(x.build_good)
        self.assertFalse(x.refresh_good)
        x.build()
        self.assertTrue(x.build_good)
        self.assertFalse(x.refresh_good)
        x.refresh()
        self.assertTrue(x.build_good)
        self.assertTrue(x.refresh_good)

    def test_runnable(self):
        """test runnable
        """
        x = Runnable()

        self.assertFalse(x.running)
        x.start()
        self.assertTrue(x.running)
        x.stop()
        self.assertFalse(x.running)

    def test_safelist(self):
        """test safelist
        """
        my_list: SafeList[int] = SafeList()
        self.assertTrue(len(my_list) == 0)
        my_list.append(1)
        self.assertTrue(len(my_list) == 1)
        my_list.append(2)
        self.assertTrue(len(my_list) == 2)
        my_list.append(3)
        self.assertTrue(len(my_list) == 3)
        my_list.append(3)
        self.assertTrue(len(my_list) == 3)

    def test_tracked_list(self):
        """test tracked list
        """
        setattr(self, 'tracked_list_passed', False)

        def cb(*_, **__):
            setattr(self, 'tracked_list_passed', True)

        my_list = TrackedList()
        my_list.subscribers.append(cb)

        my_list.append('anything')

        self.assertTrue(getattr(self, 'tracked_list_passed'))

    def test_exception_cm(self):
        """test exception context manager
        """
        _log: list[list[str]] = []

        cm = ExceptionContextManager(_log)

        with cm as manager:
            raise ValueError('This is a value error')

        self.assertEqual(_log[0], 'This is a value error')


class TestApplication(unittest.TestCase):
    """test class for application module
    """

    def test_app_configuration(self):
        """test application configurations
        """
        config = PartialApplicationConfiguration()

        self.assertIsNotNone(config)
        self.assertIsInstance(config, PartialApplicationConfiguration)
        self.assertIsInstance(config.headless, bool)
        self.assertIsInstance(config.inc_log_window, bool)
        self.assertIsInstance(config.tasks, list)
        self.assertIsInstance(config.view_config, PartialViewConfiguration)

        root = PartialApplicationConfiguration.root()
        self.assertEqual(root.view_config.view_type, PartialViewType.ROOT)
        self.assertEqual(DEF_WIN_TITLE, root.view_config.name)

        toplevel = PartialApplicationConfiguration.toplevel()
        self.assertEqual(toplevel.view_config.view_type, PartialViewType.TOPLEVEL)
        self.assertEqual(DEF_WIN_TITLE, root.view_config.name)

    def test_application(self):
        """test application
        """
        # build a good app
        model = PartialModel()
        app = PartialApplication(model,
                                 PartialApplicationConfiguration.root())
        self.assertIsNotNone(app)

        # check attributes
        self.assertIsInstance(app.main_model, PartialModel)
        self.assertIsInstance(app.config, PartialApplicationConfiguration)
        self.assertIsInstance(app.model_hash, HashList)
        self.assertFalse(app.running)

        # test bad add model
        with self.assertRaises(TypeError) as context:
            app.add_model(None)
        self.assertIsInstance(context.exception, TypeError)

        # test add good model
        self.assertIsInstance(app.add_model(PartialModel()), PartialModel)

        # test bad set model
        with self.assertRaises(TypeError) as context:
            app.set_model(None)
        self.assertIsInstance(context.exception, TypeError)

        # test good set model
        my_mdl = app.add_model(PartialModel())
        app.set_model(my_mdl)
        self.assertEqual(app.main_model, my_mdl)

        # build bad app with None as dict
        with self.assertRaises(ValueError) as context:
            PartialApplication(config=None)
        self.assertTrue(isinstance(context.exception, ValueError))

        # build a bad app with invalid view type
        with self.assertRaises(ValueError) as context:
            config = PartialApplicationConfiguration.root()
            config.view_config.view_type = PartialViewType.NA
            PartialApplication(None,
                               config)
        self.assertTrue(isinstance(context.exception, ValueError))

        # close the first app before continuing
        app.close()

        # build a root app and toplevel app with generic configs
        app = PartialApplication(config=PartialApplicationConfiguration.root())
        ext = PartialApplication(config=PartialApplicationConfiguration.toplevel())

        # then close in proper order
        ext.close()
        app.close()

    def test_application_task(self):
        """test application task builds
        """
        model = PartialModel()
        app = PartialApplication(model, PartialApplicationConfiguration.root())
        task = PartialApplicationTask(app, model)
        self.assertIsNotNone(task)

        self.assertTrue(isinstance(task.application, PartialApplication))
        self.assertTrue(isinstance(task.model, PartialModel))

        self.assertFalse(task.running)
        task.start()
        self.assertTrue(task.running)
        task.stop()
        self.assertFalse(task.running)

        app.close()

    def test_base_menu(self):
        """test base menu builds
        """
        app = PartialApplication(None, PartialApplicationConfiguration.root())
        menu = BaseMenu(app.parent)
        self.assertIsNotNone(menu)

        self.assertIsInstance(menu.root, (Tk, Toplevel))
        self.assertIsInstance(menu.menu, Menu)

        app.close()


class TestFactory(unittest.TestCase):
    """test factory functions
    """

    def test_factory(self):
        """test factory functions with generic method
        """
        class MyFactory(Factory[str]):
            """testing factory class"""
            test_str = 'Test!'

            @staticmethod
            def generic() -> str:
                return MyFactory.test_str

        x = MyFactory()
        self.assertEqual(x.generic(), MyFactory.test_str)

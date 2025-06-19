import unittest
import logging
import os
from tkinter import Frame, Tk, Menu, Toplevel
from ttkthemes import ThemedTk
from typing import Union


from .application import (
    BaseMenu,
    PartialApplication,
    PartialApplicationTask,
    PartialApplicationConfiguration
)


from .list import (
    HashList,
    Subscribable,
    SafeList,
    TrackedList,
)


from .meta import (
    _IdGenerator,
    EnforcesNaming,
    SnowFlake,
    ConsolePanelHandler,
    Loggable,
    LoggableUnitTest,
    Buildable,
    Runnable,
    ViewType,
    PartialViewConfiguration,
    PartialView,
    ExceptionContextManager,
)


from .model import (
    PartialModel,
)


from .viewmodel import (
    PartialViewModel,
)


from .meta import (
    DEF_ICON,
    DEF_THEME,
    DEF_WIN_SIZE,
    DEF_WIN_TITLE
)


class TestIdGenerator(unittest.TestCase):
    def test_get_id(self):
        initial_id = _IdGenerator.curr_value()
        new_id = _IdGenerator.get_id()
        self.assertEqual(new_id, initial_id + 1)

    def test_curr_value(self):
        current_value = _IdGenerator.curr_value()
        id = _IdGenerator.get_id()  # Increment the counter
        self.assertEqual(current_value+1, id)  # Assuming this is the second call


class TestEnforcesNaming(unittest.TestCase):
    def test_is_valid_string(self):
        valid_string = "ValidName123"
        invalid_string = "Invalid Name!"
        self.assertTrue(EnforcesNaming.is_valid_string(valid_string))
        self.assertFalse(EnforcesNaming.is_valid_string(invalid_string))

    def test_invalid_naming_exception(self):
        with self.assertRaises(EnforcesNaming.InvalidNamingException):
            raise EnforcesNaming.InvalidNamingException()


class TestSnowFlake(unittest.TestCase):
    def test_snowflake_id(self):
        snowflake = SnowFlake()
        self.assertEqual(snowflake.id, _IdGenerator.curr_value())

    def test_snowflake_equality(self):
        snowflake1 = SnowFlake()
        snowflake2 = SnowFlake()
        self.assertNotEqual(snowflake1, snowflake2)
        self.assertEqual(snowflake1, snowflake1)

    def test_snowflake_hash(self):
        snowflake = SnowFlake()
        self.assertEqual(hash(snowflake), hash(snowflake.id))


class TestConsolePanelHandler(unittest.TestCase):
    def test_emit(self):
        messages = []
        handler = ConsolePanelHandler(callback=messages.append)
        logger = logging.getLogger('test_logger')
        logger.addHandler(handler)
        logger.error('Test error message')
        self.assertIn('Test error message', messages[0])

    def test_set_callback(self):
        messages = []
        handler = ConsolePanelHandler(callback=None)
        handler.set_callback(messages.append)
        logger = logging.getLogger('test_logger')
        logger.addHandler(handler)
        logger.error('Test error message')
        self.assertIn('Test error message', messages[0])


class TestLoggable(unittest.TestCase):
    def test_logger_initialization(self):
        loggable = Loggable()
        self.assertIsInstance(loggable.logger, logging.Logger)
        self.assertIsInstance(loggable.log_handler, ConsolePanelHandler)

    def test_add_handler(self):
        loggable = Loggable()
        handler = logging.StreamHandler()
        loggable.add_handler(handler)
        self.assertIn(handler, loggable.logger.handlers)

    def test_logging_methods(self):
        messages = []
        handler = ConsolePanelHandler(callback=messages.append)
        loggable = Loggable()
        loggable.add_handler(handler)
        loggable.info('Info message')
        loggable.warning('Warning message')
        loggable.error('Error message')
        self.assertIn('Info message', messages[0])
        self.assertIn('Warning message', messages[1])
        self.assertIn('Error message', messages[2])


class TestLoggableUnitTest(unittest.TestCase):
    def test_loggable_unittest_initialization(self):
        test_case = LoggableUnitTest()
        self.assertIsInstance(test_case.logger, logging.Logger)
        self.assertIsInstance(test_case.log_handler, ConsolePanelHandler)


class TestBuildable(unittest.TestCase):
    def test_initial_built_state(self):
        buildable = Buildable()
        self.assertFalse(buildable.built)

    def test_build_method(self):
        buildable = Buildable()
        buildable.build()
        self.assertTrue(buildable.built)

    def test_refresh_method(self):
        buildable = Buildable()
        buildable.refresh()
        self.assertFalse(buildable.built)  # Refresh should not change the built state


class TestRunnable(unittest.TestCase):
    def test_initial_running_state(self):
        runnable = Runnable()
        self.assertFalse(runnable.running)

    def test_start_method(self):
        runnable = Runnable()
        runnable.start()
        self.assertTrue(runnable.running)
        self.assertTrue(runnable.built)  # Start should also build the object

    def test_stop_method(self):
        runnable = Runnable()
        runnable.start()
        runnable.stop()
        self.assertFalse(runnable.running)

    def test_run_method(self):
        runnable = Runnable()
        runnable.run()
        self.assertFalse(runnable.running)  # Run method does not change running state


class TestViewType(unittest.TestCase):
    def test_enum_values(self):
        self.assertEqual(ViewType.NA.value, 0)
        self.assertEqual(ViewType.ROOT.value, 1)
        self.assertEqual(ViewType.TOPLEVEL.value, 2)
        self.assertEqual(ViewType.EMBED.value, 3)


class TestPartialViewConfiguration(unittest.TestCase):
    def test_default_values(self):
        config = PartialViewConfiguration()
        self.assertEqual(config.title, 'Pyrox Default Frame')
        self.assertEqual(config.icon, f'{os.path.dirname(os.path.abspath(__file__))}\\..\\..\\ui\\icons\\_def.ico')
        self.assertEqual(config.size_, '1024x768')
        self.assertIsNone(config.parent)


class TestPartialView(unittest.TestCase):
    def test_initialization(self):
        view = PartialView()
        self.assertIsInstance(view.frame, Frame)
        self.assertIsNone(view.parent)


class TestExceptionContextManager(unittest.TestCase):
    def test_log_exception(self):
        report_items = []
        with ExceptionContextManager(report_items) as manager:  # noqa: F841
            raise ValueError("Test exception")
        self.assertIn("Test exception", report_items)

    def test_log_method(self):
        report_items = []
        manager = ExceptionContextManager(report_items)
        manager.log("Test log message")
        self.assertIn("Test log message", report_items)


class TestBaseMenu(unittest.TestCase):
    def test_initialization(self):
        root = Tk()
        base_menu = BaseMenu(root)
        self.assertEqual(base_menu.root, root)
        self.assertIsInstance(base_menu.menu, Menu)
        root.quit()

    def test_menu_property(self):
        root = Tk()
        base_menu = BaseMenu(root)
        self.assertIsInstance(base_menu.menu, Menu)
        root.quit()

    def test_root_property(self):
        root = Tk()
        base_menu = BaseMenu(root)
        self.assertEqual(base_menu.root, root)
        root.quit()


class TestPartialApplicationTask(unittest.TestCase):
    def test_initialization(self):
        application = PartialApplication(PartialApplicationConfiguration())
        model = PartialModel()
        task = PartialApplicationTask(application=application, model=model)
        self.assertEqual(task.application, application)
        self.assertEqual(task.model, model)
        application.stop()

    def test_model_property(self):
        application = PartialApplication(PartialApplicationConfiguration())
        model = PartialModel()
        task = PartialApplicationTask(application=application, model=model)
        new_model = PartialModel()
        task.model = new_model
        self.assertEqual(task.model, new_model)
        application.stop()


class TestPartialApplicationConfiguration(unittest.TestCase):
    def test_default_values(self):
        config = PartialApplicationConfiguration()
        self.assertFalse(config.headless)
        self.assertFalse(config.inc_log_window)
        self.assertIsInstance(config.title, str)
        self.assertIsInstance(config.theme, str)
        self.assertIsInstance(config.type_, ViewType)
        self.assertIsInstance(config.icon, str)
        self.assertIsInstance(config.size_, str)
        self.assertEqual(config.tasks, [])
        self.assertIsInstance(config.view_config, PartialViewConfiguration)
        self.assertIsNone(config.application)

    def test_common_assembly(self):
        config = PartialApplicationConfiguration._common_assembly(application=Tk(),
                                                                  headless=False,
                                                                  inc_log_window=False,
                                                                  inc_organizer=False,
                                                                  inc_workspace=False,
                                                                  tasks=[],
                                                                  title=DEF_WIN_TITLE,
                                                                  theme=DEF_THEME,
                                                                  type_=ViewType.ROOT,
                                                                  icon=DEF_ICON,
                                                                  size_=DEF_WIN_SIZE,
                                                                  view_config=None)
        self.assertIsInstance(config.application, Tk)
        self.assertFalse(config.headless)
        self.assertFalse(config.inc_log_window)
        self.assertEqual(config.tasks, [])
        self.assertEqual(config.title, DEF_WIN_TITLE)
        self.assertEqual(config.theme, DEF_THEME)
        self.assertEqual(config.type_, ViewType.ROOT)
        self.assertEqual(config.icon, DEF_ICON)
        self.assertEqual(config.size_, DEF_WIN_SIZE)
        self.assertIsNone(config.view_config)

    def test_toplevel_method(self):
        config = PartialApplicationConfiguration.toplevel()
        self.assertEqual(config.application, Toplevel)
        self.assertFalse(config.headless)
        self.assertFalse(config.inc_log_window)
        self.assertEqual(config.tasks, [])
        self.assertEqual(config.title, DEF_WIN_TITLE)
        self.assertEqual(config.theme, DEF_THEME)
        self.assertEqual(config.type_, ViewType.TOPLEVEL)
        self.assertEqual(config.icon, DEF_ICON)
        self.assertEqual(config.size_, DEF_WIN_SIZE)
        self.assertIsInstance(config.view_config, PartialViewConfiguration)

    def test_root_method(self):
        config = PartialApplicationConfiguration.root()
        self.assertEqual(config.application, ThemedTk)
        self.assertFalse(config.headless)
        self.assertTrue(config.inc_log_window)
        self.assertEqual(config.tasks, [])
        self.assertEqual(config.title, DEF_WIN_TITLE)
        self.assertEqual(config.theme, DEF_THEME)
        self.assertEqual(config.type_, ViewType.ROOT)
        self.assertEqual(config.icon, DEF_ICON)
        self.assertEqual(config.size_, DEF_WIN_SIZE)
        self.assertIsInstance(config.view_config, PartialViewConfiguration)


class TestPartialApplication(unittest.TestCase):
    def test_initialization(self):
        config = PartialApplicationConfiguration()
        application = PartialApplication(config=config)
        self.assertEqual(application.config, config)


class TestSubscribable(unittest.TestCase):
    def test_initial_subscribers(self):
        subscribable = Subscribable()
        self.assertEqual(subscribable.subscribers, [])

    def test_subscribe_method(self):
        subscribable = Subscribable()
        def callback(x): return x
        subscribable.subscribe(callback)
        self.assertIn(callback, subscribable.subscribers)

    def test_unsubscribe_method(self):
        subscribable = Subscribable()
        def callback(x): return x
        subscribable.subscribe(callback)
        subscribable.unsubscribe(callback)
        self.assertNotIn(callback, subscribable.subscribers)

    def test_emit_method(self):
        subscribable = Subscribable()
        messages = []
        def callback(x): return messages.append(x)
        subscribable.subscribe(callback)
        subscribable.emit("Test message")
        self.assertIn("Test message", messages)


class MockItem:
    def __init__(self, id, name):
        self.id = id
        self.name = name


class TestHashList(unittest.TestCase):
    def test_initialization(self):
        hash_list = HashList(hash_key='id')
        self.assertEqual(hash_list.hash_key, 'id')
        self.assertEqual(hash_list.hashes, {})

    def test_append_method(self):
        hash_list = HashList(hash_key='id')
        item = MockItem(id=1, name='Item 1')
        hash_list.append(item)
        self.assertIn(1, hash_list.hashes)
        self.assertEqual(hash_list.hashes[1], item)

    def test_by_attr_method(self):
        hash_list = HashList(hash_key='id')
        item = MockItem(id=1, name='Item 1')
        hash_list.append(item)
        result = hash_list.by_attr('name', 'Item 1')
        self.assertEqual(result, 1)

    def test_by_key_method(self):
        hash_list = HashList(hash_key='id')
        item = MockItem(id=1, name='Item 1')
        hash_list.append(item)
        result = hash_list.by_key(1)
        self.assertEqual(result, item)

    def test_remove_method(self):
        hash_list = HashList(hash_key='id')
        item = MockItem(id=1, name='Item 1')
        hash_list.append(item)
        hash_list.remove(item)
        self.assertNotIn(1, hash_list.hashes)

    def test_emit_method(self):
        hash_list = HashList(hash_key='id')
        messages = []

        def callback(*args, **kwargs):
            messages.append(kwargs['models'])
        hash_list.subscribe(callback)
        item = MockItem(id=1, name='Item 1')
        hash_list.append(item)
        self.assertIn('hash_list', messages[0])
        self.assertIn(1, messages[0]['hash_list'])


class TestSafeList(unittest.TestCase):
    def test_append_no_duplicates(self):
        safe_list = SafeList()
        safe_list.append(1)
        safe_list.append(1)
        self.assertEqual(len(safe_list), 1)
        self.assertEqual(safe_list[0], 1)

    def test_append_unique_values(self):
        safe_list = SafeList[int]()
        safe_list.append(1)
        safe_list.append(2)
        self.assertEqual(len(safe_list), 2)
        self.assertEqual(safe_list[0], 1)
        self.assertEqual(safe_list[1], 2)


class TestTrackedList(unittest.TestCase):
    def test_initial_subscribers(self):
        tracked_list = TrackedList()
        self.assertEqual(tracked_list.subscribers, [])

    def test_append_method(self):
        tracked_list = TrackedList()
        messages = []
        def callback(): return messages.append("Updated")
        tracked_list.subscribers.append(callback)
        tracked_list.append(1)
        self.assertIn("Updated", messages)
        self.assertEqual(tracked_list[0], 1)

    def test_remove_method(self):
        tracked_list = TrackedList()
        messages = []
        def callback(): return messages.append("Updated")
        tracked_list.subscribers.append(callback)
        tracked_list.append(1)
        tracked_list.remove(1)
        self.assertIn("Updated", messages)
        self.assertEqual(len(tracked_list), 0)

    def test_emit_method(self):
        tracked_list = TrackedList()
        messages = []
        def callback(): return messages.append("Updated")
        tracked_list.subscribers.append(callback)
        tracked_list.emit()
        self.assertIn("Updated", messages)


class TestPartialModel(unittest.TestCase):
    def test_initialization(self):
        application = PartialApplication(PartialApplicationConfiguration())
        view_model = PartialViewModel()
        model = PartialModel(application=application, view_model=view_model)
        self.assertEqual(model.application, application)
        self.assertEqual(model.view_model, view_model)

    def test_initialization_with_view_model_class(self):
        application = PartialApplication(PartialApplicationConfiguration())
        model = PartialModel(application=application, view_model=PartialViewModel)
        self.assertEqual(model.application, application)
        self.assertIsInstance(model.view_model, PartialViewModel)

    def test_initialization_with_invalid_view_model(self):
        with self.assertRaises(ValueError):
            PartialModel(view_model="invalid_view_model")

    def test_str_method(self):
        model = PartialModel()
        self.assertEqual(str(model), "PartialModel")

    def test_set_application(self):
        application = PartialApplication(PartialApplicationConfiguration())
        model = PartialModel()
        result = model.set_application(application)
        self.assertTrue(result)
        self.assertEqual(model.application, application)
        application.stop()

    def test_set_application_already_set(self):
        application = PartialApplication(PartialApplicationConfiguration())
        model = PartialModel(application=application)
        result = model.set_application(application)
        self.assertFalse(result)
        application.stop()

    def test_view_model_deleter(self):
        view_model = PartialViewModel()
        model = PartialModel(view_model=view_model)
        del model.view_model
        self.assertIsNone(model.view_model)


class TestPartialViewModel(unittest.TestCase):
    def test_initialization(self):
        model = PartialModel()
        view = PartialView()
        view_model = PartialViewModel(model=model, view=view)
        self.assertEqual(view_model.model, model)
        self.assertEqual(view_model.view, view)

    def test_initialization_with_view_class(self):
        model = PartialModel()
        view_model = PartialViewModel(model=model, view=PartialView)
        self.assertEqual(view_model.model, model)
        self.assertIsInstance(view_model.view, PartialView)

    def test_initialization_with_invalid_view(self):
        with self.assertRaises(ValueError):
            PartialViewModel(view="invalid_view")

    def test_model_property(self):
        model = PartialModel()
        view_model = PartialViewModel(model=model)
        self.assertEqual(view_model.model, model)

    def test_view_property(self):
        view = PartialView()
        view_model = PartialViewModel(view=view)
        self.assertEqual(view_model.view, view)

    def test_view_deleter(self):
        view = PartialView()
        view_model = PartialViewModel(view=view)
        del view_model.view
        self.assertIsNone(view_model.view)


if __name__ == '__main__':
    unittest.main()

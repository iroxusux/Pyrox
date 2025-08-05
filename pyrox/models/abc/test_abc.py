"""test abcs module
    """
import json
import logging
from unittest.mock import MagicMock
import os
import tempfile
from tkinter import Tk, Menu
import unittest


from .application import (
    BaseMenu,
    Application,
    ApplicationConfiguration,
    ApplicationDirectoryService,
    ApplicationRuntimeInfo,
    ApplicationTask,
    ApplicationTkType,
)


from .list import (
    HashList,
    Subscribable,
    SafeList,
    TrackedList,
)


from .meta import (
    _IdGenerator,
    Buildable,
    EnforcesNaming,
    Loggable,
    NamedPyroxObject,
    PyroxObject,
    Runnable,
    RuntimeDict,
    SnowFlake,
    SupportsJsonLoading,
    SupportsJsonSaving,
    SupportsLoading,
    SupportSaving,
)


from .model import (
    Model,
)


from .meta import (
    DEF_APP_NAME,
    DEF_AUTHOR_NAME,
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

    def test_valid_rockwell_bool(self):
        valid_bool = 'true'
        invalid_bool = "True"
        self.assertTrue(EnforcesNaming.is_valid_rockwell_bool(valid_bool))
        self.assertFalse(EnforcesNaming.is_valid_rockwell_bool(invalid_bool))

    def test_valid_module_string(self):
        valid_module = "valid_module-name"
        invalid_module = "Invalid Module Name"
        self.assertTrue(EnforcesNaming.is_valid_module_string(valid_module))
        self.assertFalse(EnforcesNaming.is_valid_module_string(invalid_module))

    def test_valid_revision_string(self):
        valid_revision = "1.0.0"
        invalid_revision = "1point0"
        self.assertTrue(EnforcesNaming.is_valid_revision_string(valid_revision))
        self.assertFalse(EnforcesNaming.is_valid_revision_string(invalid_revision))


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

    def test_snowflake_string(self):
        snowflake = SnowFlake()
        self.assertIsInstance(str(snowflake), str)
        self.assertIn(str(snowflake.id), str(snowflake))


class TestRuntimeDict(unittest.TestCase):
    def setUp(self):
        self.callback_called = False

        def callback():
            self.callback_called = True
        self.runtime_dict = RuntimeDict(callback=callback)

    def test_set_and_get_item(self):
        self.runtime_dict['key'] = 'value'
        self.assertEqual(self.runtime_dict['key'], 'value')
        self.assertTrue(self.callback_called)

    def test_del_item(self):
        self.runtime_dict['key'] = 'value'
        self.callback_called = False
        del self.runtime_dict['key']
        self.assertIsNone(self.runtime_dict['key'])
        self.assertTrue(self.callback_called)

    def test_contains(self):
        self.runtime_dict['key'] = 'value'
        self.assertIn('key', self.runtime_dict)
        self.assertNotIn('missing', self.runtime_dict)

    def test_data_property(self):
        data = {'a': 1, 'b': 2}
        self.runtime_dict.data = data
        self.assertEqual(self.runtime_dict.data, data)
        self.assertTrue(self.callback_called)

    def test_inhibit_and_uninhibit(self):
        self.runtime_dict.inhibit()
        self.callback_called = False
        self.runtime_dict['key'] = 'value'
        self.assertFalse(self.callback_called)
        self.runtime_dict.uninhibit()
        self.assertTrue(self.callback_called)

    def test_clear(self):
        self.runtime_dict['key'] = 'value'
        self.callback_called = False
        self.runtime_dict.clear()
        self.assertEqual(self.runtime_dict.data, {})
        self.assertTrue(self.callback_called)

    def test_update(self):
        self.callback_called = False
        self.runtime_dict.update({'x': 10, 'y': 20})
        self.assertEqual(self.runtime_dict['x'], 10)
        self.assertEqual(self.runtime_dict['y'], 20)
        self.assertTrue(self.callback_called)

    def test_get_method(self):
        self.runtime_dict['foo'] = 'bar'
        self.assertEqual(self.runtime_dict.get('foo'), 'bar')
        self.assertEqual(self.runtime_dict.get('missing', 'default'), 'default')

    def test_callback_setter(self):
        def new_callback():
            self.callback_called = 'new'
        self.runtime_dict.callback = new_callback
        self.runtime_dict['key'] = 'value'
        self.assertEqual(self.callback_called, 'new')

    def test_inhibit_callback_setter(self):
        self.runtime_dict.inhibit_callback = True
        self.callback_called = False
        self.runtime_dict['key'] = 'value'
        self.assertFalse(self.callback_called)
        self.runtime_dict.inhibit_callback = False
        self.assertTrue(self.callback_called)

    def test_data_setter_type_error(self):
        with self.assertRaises(TypeError):
            self.runtime_dict.data = 'not_a_dict'

    def test_callback_setter_value_error(self):
        with self.assertRaises(ValueError):
            self.runtime_dict.callback = None

    def test_inhibit_callback_setter_type_error(self):
        with self.assertRaises(TypeError):
            self.runtime_dict.inhibit_callback = 'not_a_bool'


class TestPyroxObject(unittest.TestCase):
    def test_inheritance_from_snowflake(self):
        obj = PyroxObject()
        self.assertIsInstance(obj, SnowFlake)
        self.assertIsInstance(obj.id, int)

    def test_repr_returns_class_name(self):
        obj = PyroxObject()
        self.assertEqual(repr(obj), 'PyroxObject')


class TestNamedPyroxObject(unittest.TestCase):
    def test_inheritance_from_pyroxobject(self):
        obj = NamedPyroxObject()
        self.assertIsInstance(obj, PyroxObject)
        self.assertIsInstance(obj.id, int)

    def test_default_name_and_description(self):
        obj = NamedPyroxObject()
        self.assertEqual(obj.name, 'NamedPyroxObject')
        self.assertEqual(obj.description, '')

    def test_custom_name_and_description(self):
        obj = NamedPyroxObject(name='CustomName', description='CustomDesc')
        self.assertEqual(obj.name, 'CustomName')
        self.assertEqual(obj.description, 'CustomDesc')

    def test_name_setter_valid(self):
        obj = NamedPyroxObject()
        obj.name = 'ValidName123'
        self.assertEqual(obj.name, 'ValidName123')

    def test_name_setter_invalid(self):
        obj = NamedPyroxObject()
        with self.assertRaises(EnforcesNaming.InvalidNamingException):
            obj.name = 'Invalid Name!'

    def test_description_setter_valid(self):
        obj = NamedPyroxObject()
        obj.description = 'A description'
        self.assertEqual(obj.description, 'A description')

    def test_description_setter_invalid(self):
        obj = NamedPyroxObject()
        with self.assertRaises(TypeError):
            obj.description = 12345


class TestSupportsLoading(unittest.TestCase):
    def test_inheritance_from_pyroxobject(self):
        class DummyLoader(SupportsLoading):
            @property
            def load_path(self):
                return None

            def load(self, path=None):
                return "loaded"

            def on_loaded(self, data):
                self.loaded_data = data

        obj = DummyLoader()
        self.assertIsInstance(obj, PyroxObject)
        self.assertIsInstance(obj.id, int)

    def test_not_implemented_load_path(self):
        obj = SupportsLoading()
        with self.assertRaises(NotImplementedError):
            _ = obj.load_path

    def test_not_implemented_load_method(self):
        obj = SupportsLoading()
        with self.assertRaises(NotImplementedError):
            obj.load()

    def test_on_loaded_override(self):
        class DummyLoader(SupportsLoading):
            def on_loaded(self, data):
                self.loaded_data = data

        obj = DummyLoader()
        obj.on_loaded("test_data")
        self.assertEqual(obj.loaded_data, "test_data")


class TestSupportsSaving(unittest.TestCase):
    def test_inheritance_from_pyroxobject(self):
        class DummySaver(SupportSaving):
            @property
            def save_path(self):
                return None

            @property
            def save_data_callback(self):
                return lambda: {"data": 123}

            def save(self, path=None, data=None):
                self.saved = True

        obj = DummySaver()
        self.assertIsInstance(obj, PyroxObject)
        self.assertIsInstance(obj.id, int)

    def test_not_implemented_save_path(self):
        obj = SupportSaving()
        with self.assertRaises(NotImplementedError):
            _ = obj.save_path

    def test_not_implemented_save_data_callback(self):
        obj = SupportSaving()
        with self.assertRaises(NotImplementedError):
            _ = obj.save_data_callback

    def test_not_implemented_save_method(self):
        obj = SupportSaving()
        with self.assertRaises(NotImplementedError):
            obj.save()

    def test_save_override(self):
        class DummySaver(SupportSaving):
            def save(self, path=None, data=None):
                self.saved = (path, data)
        obj = DummySaver()
        obj.save(path="test_path", data={"x": 1})
        self.assertEqual(obj.saved, ("test_path", {"x": 1}))


class TestSupportsJsonSaving(unittest.TestCase):
    def test_inheritance_from_supportsaving(self):
        class DummyJsonSaver(SupportsJsonSaving):
            @property
            def save_path(self):
                return None

            @property
            def save_data_callback(self):
                return lambda: {"data": 123}
        obj = DummyJsonSaver()
        self.assertIsInstance(obj, SupportSaving)
        self.assertIsInstance(obj.id, int)

    def test_save_to_json_success(self):
        class DummyJsonSaver(SupportsJsonSaving):
            @property
            def save_path(self):
                return self._path

            @property
            def save_data_callback(self):
                return lambda: {"data": 456}
        obj = DummyJsonSaver()
        with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.json') as tmp:
            obj._path = tmp.name
            obj.save_to_json()
            tmp.seek(0)
            saved_data = json.load(tmp)
        self.assertEqual(saved_data, {"data": 456})
        os.remove(tmp.name)

    def test_save_to_json_no_path(self):
        class DummyJsonSaver(SupportsJsonSaving):
            @property
            def save_path(self):
                return None

            @property
            def save_data_callback(self):
                return lambda: {"data": 789}
        obj = DummyJsonSaver()
        with self.assertRaises(ValueError):
            obj.save_to_json()


class TestSupportsJsonLoading(unittest.TestCase):
    def test_inheritance_from_supportsloading(self):
        class DummyJsonLoader(SupportsJsonLoading):
            @property
            def load_path(self):
                return None

            def on_loaded(self, data):
                self.loaded_data = data
        obj = DummyJsonLoader()
        self.assertIsInstance(obj, SupportsLoading)
        self.assertIsInstance(obj.id, int)

    def test_load_from_json_success(self):
        class DummyJsonLoader(SupportsJsonLoading):
            @property
            def load_path(self):
                return self._path

            def on_loaded(self, data):
                self.loaded_data = data
        obj = DummyJsonLoader()
        test_data = {"foo": "bar"}
        with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.json') as tmp:
            json.dump(test_data, tmp)
            tmp.close()
            obj._path = tmp.name
            obj.load_from_json()
        self.assertEqual(obj.loaded_data, test_data)
        os.remove(tmp.name)

    def test_load_from_json_file_not_found(self):
        class DummyJsonLoader(SupportsJsonLoading):
            @property
            def load_path(self):
                return "non_existent_file.json"

            def on_loaded(self, data):
                self.loaded_data = data
        obj = DummyJsonLoader()
        result = obj.load_from_json()
        self.assertIsNone(result)


class TestLoggable(unittest.TestCase):
    def test_logger_initialization(self):
        loggable = Loggable()
        self.assertIsInstance(loggable.logger, logging.Logger)
        # self.assertIsInstance(loggable.log_handler, ConsolePanelHandler)


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


class TestBaseMenu(unittest.TestCase):
    def test_initialization(self):
        root = Tk()
        base_menu = BaseMenu(root)
        self.assertEqual(base_menu.root, root)
        self.assertIsInstance(base_menu.menu, Menu)
        root.quit()

    def test_menu_property(self):
        root = MagicMock()
        base_menu = BaseMenu(root)
        self.assertIsInstance(base_menu.menu, Menu)
        root.quit()

    def test_root_property(self):
        root = MagicMock()
        base_menu = BaseMenu(root)
        self.assertEqual(base_menu.root, root)
        root.quit()


class TestApplicationTask(unittest.TestCase):
    def test_initialization(self):
        application = Application(ApplicationConfiguration())
        task = ApplicationTask(application=application)
        self.assertEqual(task.application, application)


class TestApplicationConfiguration(unittest.TestCase):
    def test_default_values(self):
        config = ApplicationConfiguration()
        self.assertFalse(config.headless)
        self.assertIsInstance(config.title, str)
        self.assertIsInstance(config.theme, str)
        self.assertIsInstance(config.type_, ApplicationTkType)
        self.assertEqual(config.icon, DEF_ICON)
        self.assertIsInstance(config.size_, str)
        self.assertEqual(config.tasks, [])

    def test_common_assembly(self):
        config = ApplicationConfiguration._common_assembly(application_name=DEF_APP_NAME,
                                                           author_name=DEF_AUTHOR_NAME,
                                                           headless=False,
                                                           tasks=[],
                                                           title=DEF_WIN_TITLE,
                                                           theme=DEF_THEME,
                                                           type_=ApplicationTkType.ROOT,
                                                           icon=DEF_ICON,
                                                           size_=DEF_WIN_SIZE)
        self.assertFalse(config.headless)
        self.assertEqual(config.tasks, [])
        self.assertEqual(config.title, DEF_WIN_TITLE)
        self.assertEqual(config.theme, DEF_THEME)
        self.assertEqual(config.type_, ApplicationTkType.ROOT)
        self.assertEqual(config.icon, DEF_ICON)
        self.assertEqual(config.size_, DEF_WIN_SIZE)

    def test_toplevel_method(self):
        config = ApplicationConfiguration.toplevel()
        self.assertFalse(config.headless)
        self.assertEqual(config.tasks, [])
        self.assertEqual(config.title, DEF_WIN_TITLE)
        self.assertEqual(config.theme, DEF_THEME)
        self.assertEqual(config.type_, ApplicationTkType.TOPLEVEL)
        self.assertEqual(config.icon, DEF_ICON)
        self.assertEqual(config.size_, DEF_WIN_SIZE)

    def test_root_method(self):
        config = ApplicationConfiguration.root()
        self.assertFalse(config.headless)
        self.assertEqual(config.tasks, [])
        self.assertEqual(config.title, DEF_WIN_TITLE)
        self.assertEqual(config.theme, DEF_THEME)
        self.assertEqual(config.type_, ApplicationTkType.ROOT)
        self.assertEqual(config.icon, DEF_ICON)
        self.assertEqual(config.size_, DEF_WIN_SIZE)


class TestApplicationDirectoryService(unittest.TestCase):
    def setUp(self):
        self.author_name = "TestAuthor"
        self.app_name = "TestApp"
        self.ads = ApplicationDirectoryService(author_name=self.author_name, app_name=self.app_name)

    def test_app_name_property(self):
        self.assertEqual(self.ads.app_name, self.app_name)

    def test_author_name_property(self):
        self.assertEqual(self.ads.author_name, self.author_name)

    def test_all_directories_property(self):
        dirs = self.ads.all_directories
        self.assertIsInstance(dirs, dict)
        self.assertIn('user_cache', dirs)
        self.assertIn('user_config', dirs)
        self.assertIn('user_data', dirs)
        self.assertIn('user_log', dirs)

    def test_user_cache_property(self):
        self.assertTrue(os.path.isdir(self.ads.user_cache))

    def test_user_config_property(self):
        self.assertTrue(os.path.isdir(self.ads.user_config))

    def test_user_data_property(self):
        self.assertTrue(os.path.isdir(self.ads.user_data))

    def test_user_documents_property(self):
        self.assertTrue(isinstance(self.ads.user_documents, str))

    def test_user_downloads_property(self):
        self.assertTrue(isinstance(self.ads.user_downloads, str))

    def test_user_log_property(self):
        self.assertTrue(isinstance(self.ads.user_log, str))

    def test_user_log_file_property(self):
        self.assertTrue(self.ads.user_log_file.endswith('.log'))

    def test_app_runtime_info_file_property(self):
        self.assertTrue(self.ads.app_runtime_info_file.endswith('_runtime_info.json'))

    def test_build_directory_refresh(self):
        # Should not raise
        self.ads.build_directory(as_refresh=True)


class TestApplicationRuntimeInfo(unittest.TestCase):
    def setUp(self):
        class DummyApp:
            def __init__(self):
                self.directory_service = ApplicationDirectoryService(author_name="TestAuthor", app_name="TestApp")
                self.logger = type("Logger", (), {"warning": lambda self, msg: None})()
        self.app = DummyApp()
        self.ari = ApplicationRuntimeInfo(application=self.app)

    def test_application_property(self):
        self.assertIs(self.ari.application, self.app)

    def test_application_runtime_info_file_property(self):
        path = self.ari.application_runtime_info_file
        self.assertTrue(path.endswith("_runtime_info.json"))
        self.assertIn(self.app.directory_service.app_name, path)

    def test_data_property(self):
        self.assertIsInstance(self.ari.data, RuntimeDict)
        self.ari.data['test_key'] = 'test_value'
        self.assertEqual(self.ari.data['test_key'], 'test_value')

    def test_data_setter(self):
        new_data = {'foo': 'bar'}
        self.ari.data = new_data
        self.assertEqual(self.ari.data['foo'], 'bar')

    def test_load_path_and_save_path(self):
        self.assertEqual(self.ari.load_path, self.ari.application_runtime_info_file)
        self.assertEqual(self.ari.save_path, self.ari.application_runtime_info_file)

    def test_save_data_callback(self):
        cb = self.ari.save_data_callback
        self.assertTrue(callable(cb))
        self.ari.data['abc'] = 123
        self.assertEqual(cb()['abc'], 123)

    def test_get_and_set(self):
        self.ari.set('hello', 'world')
        self.assertEqual(self.ari.get('hello'), 'world')
        self.assertEqual(self.ari.get('notfound', 'default'), 'default')

    def test_on_loaded(self):
        # Should not raise for dict
        self.ari.on_loaded({'x': 1})
        self.assertEqual(self.ari.data['x'], 1)
        # Should re-init for None
        self.ari.on_loaded(None)
        self.assertIsInstance(self.ari.data, RuntimeDict)
        # Should raise for non-dict
        with self.assertRaises(TypeError):
            self.ari.on_loaded("notadict")


class TestApplication(unittest.TestCase):
    def setUp(self):
        # Minimal config for headless test
        self.config = ApplicationConfiguration(
            headless=True,
            application_name="TestApp",
            author_name="TestAuthor",
            title="Test Title",
            theme="default",
            type_=ApplicationTkType.ROOT,
            icon="",
            size_="800x600",
            tasks=[]
        )
        self.app = Application(config=self.config)

    def test_config_property(self):
        self.assertIs(self.app.config, self.config)

    def test_directory_service_property(self):
        self.assertIsInstance(self.app.directory_service, ApplicationDirectoryService)
        self.assertEqual(self.app.directory_service.app_name, "TestApp")
        self.assertEqual(self.app.directory_service.author_name, "TestAuthor")

    def test_runtime_info_property(self):
        self.app._runtime_info = ApplicationRuntimeInfo(application=self.app)
        self.assertIsInstance(self.app.runtime_info, ApplicationRuntimeInfo)

    def test_tasks_property(self):
        self.app._tasks = HashList('name')
        self.assertIsInstance(self.app.tasks, HashList)

    def test_log_and_clear_log_file(self):
        self.app.log("Test log entry")
        self.app.clear_log_file()
        # Should not raise

    def test_add_task_and_add_tasks(self):
        class DummyTask(ApplicationTask):
            def inject(self): return self
        self.app._tasks = HashList('name')
        task = DummyTask(application=self.app)
        self.app.add_task(task)
        self.assertIn(task, self.app.tasks)
        self.app.add_tasks([DummyTask(application=self.app)])
        self.assertTrue(any(isinstance(t, DummyTask) for t in self.app.tasks))

    def test_toggle_fullscreen(self):
        # Should not raise, even if tk_app is None
        self.app._runtime_info = ApplicationRuntimeInfo(application=self.app)
        self.app._tk_app = type("TkApp", (), {"attributes": lambda self, k, v=None: None})()
        self.app.toggle_fullscreen(True)
        self.app.toggle_fullscreen(False)
        self.app.toggle_fullscreen(None)

    def test_center_method(self):
        # Should not raise, even if tk_app is None
        self.app._tk_app = type("TkApp", (), {
            "winfo_screenwidth": lambda self: 1920,
            "winfo_reqwidth": lambda self: 800,
            "winfo_screenheight": lambda self: 1080,
            "winfo_reqheight": lambda self: 600,
            "geometry": lambda self, s: None
        })()
        self.app.center()

    def test_close_method(self):
        # Should not raise, even if tk_app is None
        self.app._tk_app = type("TkApp", (), {
            "quit": lambda self: None,
            "destroy": lambda self: None
        })()
        self.app.close()

    def test_on_pre_run_and_stop(self):
        # Should not raise
        self.app.on_pre_run()
        self.app.stop()


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


class TestModel(unittest.TestCase):
    def setUp(self):
        class DummyApplication:
            pass
        self.app = DummyApplication()
        self.model = Model(application=self.app)

    def test_application_property(self):
        self.assertIs(self.model.application, self.app)

    def test_application_setter(self):
        new_app = object()
        self.model.application = new_app
        self.assertIs(self.model.application, new_app)

    def test_init_with_none(self):
        model_none = Model()
        self.assertIsNone(model_none.application)


if __name__ == '__main__':
    unittest.main()

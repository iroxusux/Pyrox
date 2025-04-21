"""types test suite
    """
from __future__ import annotations


from tkinter import Tk
import unittest


from .abc import (
    PartialModel,
)


from .application import (
    Application,
    ApplicationTask,
    PartialApplicationConfiguration
)

from .loggable import (ConsolePanelHandler, Loggable)
from .model import Model
from .progress_bar import ProgressBar
from .abc.list import (
    HashList,
    SafeList,
    TrackedList
)
from .view import View
from .viewmodel import ViewModel


__all__ = (
    'TestTypes',
)


class TestTypes(unittest.TestCase):
    """Testing class for types
    """

    def test_main_application_menu(self):
        """test main application menu
        """
        class TestTask(ApplicationTask):
            """testing class for menu
            """

            def inject(self):
                """test injecting into menu
                """
                self.application.menu.file.add_command(label='Test1', command=lambda: print('this is a test...'))
                self.application.menu.file.add_command(label='Test2', command=lambda: print('this is a test...'))
                self.application.menu.file.add_command(label='Test3', command=lambda: print('this is a test...'))

        app = Application(None, PartialApplicationConfiguration.generic_root())

        task = TestTask(app, None)
        task.inject()

        cmds = app.menu.get_menu_commands(app.menu.file)

        self.assertIsNotNone(cmds.get('Test1', None))
        self.assertIsNotNone(cmds.get('Test2', None))
        self.assertIsNotNone(cmds.get('Test3', None))

        app.close()

    def test_application(self):
        """test application builds
        """
        # test generic build with no model
        app = Application(None, PartialApplicationConfiguration.generic_root())
        self.assertIsNotNone(app)
        self.assertIsNotNone(app.logger)
        self.assertTrue(isinstance(app.parent, Tk))
        app.close()

        # test generic build with basic model
        model = PartialModel()
        app = Application(model, PartialApplicationConfiguration.generic_root())
        self.assertIsNotNone(app)
        self.assertTrue(isinstance(app.parent, Tk))
        self.assertEqual(model, app.main_model)

        # check menu is built
        self.assertIsNotNone(app.menu)
        self.assertIsNotNone(app.menu.file)
        self.assertIsNotNone(app.menu.edit)
        self.assertIsNotNone(app.menu.tools)
        self.assertIsNotNone(app.menu.view)
        self.assertIsNotNone(app.menu.help)

        # can set a good model
        new_model = PartialModel()
        app.set_model(new_model)
        self.assertEqual(new_model, app.main_model)

        # can't set a bad model
        with self.assertRaises(TypeError) as context:
            app.set_model(1)
        self.assertTrue(isinstance(context.exception, TypeError))

        app.close()

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

        my_list = HashList('name')
        my_list.append(val1)
        self.assertTrue(len(my_list) == 1)
        my_list.append(val2)
        self.assertTrue(len(my_list) == 2)
        my_list.append(val3)
        self.assertTrue(len(my_list) == 3)
        my_list.append(val3)
        self.assertTrue(len(my_list) == 3)
        self.assertIsNotNone(my_list.by_key('value1'))
        self.assertIsNotNone(my_list.by_key('value2'))
        self.assertIsNotNone(my_list.by_key('value3'))

    def test_loggable(self):
        """test loggable class
        """
        class TestLog(Loggable):
            """test class for unit testing
            """

            def _log(self,
                     _: str) -> None:
                ...

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

    def test_model(self):
        """test model
        """
        model = Model(None, None)
        self.assertIsNone(model.application)
        self.assertIsNone(model.view_model)
        self.assertIsNotNone(model.id)
        self.assertIsNotNone(model.logger)

        app = Application(None, PartialApplicationConfiguration.generic_root())

        asmbl_mdl = Model.as_assembled(app,
                                       ViewModel,
                                       View)

        app.set_model(asmbl_mdl)

        self.assertIsNotNone(asmbl_mdl)
        self.assertIsNotNone(asmbl_mdl.application)
        self.assertIsNotNone(asmbl_mdl.view_model)
        self.assertIsNotNone(asmbl_mdl.view_model.view)

        self.assertEqual(asmbl_mdl.application, app)
        self.assertEqual(asmbl_mdl.application.main_model, asmbl_mdl)
        self.assertEqual(asmbl_mdl, asmbl_mdl.view_model.model)
        self.assertEqual(asmbl_mdl.view_model, asmbl_mdl.view_model.view.view_model)
        self.assertEqual(asmbl_mdl.view_model.view.parent, asmbl_mdl.application.frame)

    def test_progressbar(self):
        """test progress-bar
        """
        pbar = ProgressBar('Test Title', 'Test Header')
        self.assertIsNotNone(pbar)

        pbar.update('Some Extra Text', 50)

        pbar.close()

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

    def test_view(self):
        """test view
        """
        view = View(None)
        self.assertIsNotNone(view)
        self.assertIsNotNone(view.name)
        self.assertIsNotNone(view.view_type)
        self.assertIsNone(view.view_model)
        self.assertIsNotNone(view.logger)

    def test_view_model(self):
        """test view model
        """
        view_model = ViewModel(None, None)
        self.assertIsNotNone(view_model)
        self.assertIsNone(view_model.model)
        self.assertIsNone(view_model.view)
        self.assertIsNotNone(view_model.logger)

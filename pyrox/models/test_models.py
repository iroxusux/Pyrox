"""types test suite
    """
from __future__ import annotations


from tkinter import Tk
from ttkthemes import ThemedTk
import unittest


from .application import (
    Application,
    ApplicationTask,
    PartialApplicationConfiguration
)

from .model import Model
from .utkinter.progress_bar import ProgressBar
from .view import View
from .viewmodel import ViewModel


__all__ = (
    'TestModels',
)


class TestModels(unittest.TestCase):
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

        app = Application(config=PartialApplicationConfiguration.root())
        app.build()

        task = TestTask(app, None)
        task.inject()

        cmds = app.menu.get_menu_commands(app.menu.file)

        self.assertIsNotNone(cmds.get('Test1', None))
        self.assertIsNotNone(cmds.get('Test2', None))
        self.assertIsNotNone(cmds.get('Test3', None))

        app.stop()

    def test_application(self):
        """test application builds
        """
        # test generic build with no model
        app = Application(PartialApplicationConfiguration.root())
        self.assertIsNotNone(app)
        self.assertIsNotNone(app.logger)
        self.assertEqual(app.config.application, ThemedTk)

        app.build()

        # check menu is built
        self.assertIsNotNone(app.menu)
        self.assertIsNotNone(app.menu.file)
        self.assertIsNotNone(app.menu.edit)
        self.assertIsNotNone(app.menu.tools)
        self.assertIsNotNone(app.menu.view)
        self.assertIsNotNone(app.menu.help)
        self.assertIsNotNone(app.menu.active_models)

        # can insert a task by type
        app.add_task(ApplicationTask)

        # can insert a task already built
        task = ApplicationTask(app, None)
        app.add_task(task)

        app.stop()

    def test_model(self):
        """test model
        """
        model = Model(None, None)
        self.assertIsNone(model.application)
        self.assertIsNone(model.view_model)
        self.assertIsNotNone(model.id)
        self.assertIsNotNone(model.logger)

    def test_progressbar(self):
        """test progress-bar
        """
        return  # this needs to be fixed
        pbar = ProgressBar('Test Title', 'Test Header')
        self.assertIsNotNone(pbar)
        pbar.update('Some Extra Text', 50)
        pbar.stop()

    def test_view(self):
        """test view
        """
        view = View()
        self.assertIsNotNone(view)
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

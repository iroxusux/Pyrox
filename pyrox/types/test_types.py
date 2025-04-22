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


from .model import Model
from .utkinter.progress_bar import ProgressBar
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

        # can insert a task by type
        app.add_task(ApplicationTask)

        # can insert a task already built
        task = ApplicationTask(app, None)
        app.add_task(task)

        app.close()

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

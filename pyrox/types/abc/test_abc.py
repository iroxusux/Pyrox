from tkinter import Tk, Toplevel, Frame, LabelFrame, Menu, TclError
import unittest


from .application import (
    ApplicationTask,
    BaseMenu,
    PartialApplication,
    PartialApplicationConfiguration
)


from .factory import Factory


from .meta import (
    _IdGenerator,
    SnowFlake,
    PartialView
)


from .model import Model


__all__ = (
    'TestMeta',
)


class TestMeta(unittest.TestCase):
    """test class for meta module
    """

    def test_id_generator(self):
        """test id generator generates unique ids
        """
        val = _IdGenerator.curr_value
        self.assertTrue(isinstance(val, int))

        x = _IdGenerator.get_id()
        y = _IdGenerator.get_id()

        # check that value incremented
        self.assertEqual(val+1, x)

        # check that new objects get new values
        self.assertNotEqual(x, y)

    def test_snowflake_generation(self):
        """test snowflakes generate with unique ids
        """
        x = SnowFlake()
        y = SnowFlake()

        self.assertTrue(isinstance(x.id, int))

        self.assertNotEqual(x.id, y.id)

        # create list for testing
        my_list = [x]

        # check __hash__ function by checking if obj in list
        # check second obj not in list
        self.assertTrue(x in my_list)
        self.assertFalse(y in my_list)

        # add second obj
        my_list.append(y)

        # check again
        self.assertTrue(x in my_list)
        self.assertTrue(y in my_list)

    def test_partial_view_builds(self):
        """test partial view builds
        """

        # test root build
        x = PartialView('', 1)
        self.assertTrue(x.parent.winfo_exists())
        self.assertNotEqual(x.parent.children, {})

        # check all attrs
        self.assertTrue(isinstance(x.name, str))
        self.assertTrue(isinstance(x.parent, (Tk, Toplevel, Frame, LabelFrame)))
        self.assertTrue(isinstance(x.frame, Frame))
        self.assertTrue(isinstance(x.view_type, int))

        x.close()
        self.assertEqual(x.parent.children, {})

        # validate the second attempt to close throws the expected err
        with self.assertRaises(TclError) as context:
            x.close()
        self.assertTrue(isinstance(context.exception, TclError))

        # test top level build
        x = PartialView('', 2)
        self.assertTrue(x.parent.winfo_exists())
        self.assertNotEqual(x.parent.children, {})

        # check all attrs
        self.assertTrue(isinstance(x.name, str))
        self.assertTrue(isinstance(x.parent, (Tk, Toplevel, Frame, LabelFrame)))
        self.assertTrue(isinstance(x.frame, Frame))
        self.assertTrue(isinstance(x.view_type, int))

        x.close()
        self.assertEqual(x.parent.children, {})

        # test an invalid view type can't be built
        with self.assertRaises(ValueError) as context:
            PartialView(None, 3)
        self.assertTrue(isinstance(context.exception, ValueError))

        # test a non-dict object can't be passed for config
        with self.assertRaises(TypeError) as context:
            PartialView(None, None)
        self.assertTrue(isinstance(context.exception, TypeError))


class TestApplication(unittest.TestCase):
    """test class for application module
    """

    def test_app_configuration(self):
        """test application configurations
        """
        config = PartialApplicationConfiguration({
            'icon': 'icon.bmp',
            'theme': 'black',
            'title': 'Test Application',
            'type': 1,
            'win_size': '400x400',
        })

        self.assertIsNotNone(config)

        self.assertTrue(isinstance(config, dict))

    def test_application_builds(self):
        """test application builds
        """
        # build a good app
        model = Model()
        app = PartialApplication(model,
                                 PartialApplicationConfiguration.generic_root())
        self.assertIsNotNone(app)

        self.assertTrue(isinstance(app.model, Model))
        self.assertTrue(isinstance(app.config, dict))

        app.close()

        # build bad app with shit dict
        with self.assertRaises(KeyError) as context:
            PartialApplication(None, {})

        self.assertTrue(isinstance(context.exception, KeyError))

        # build bad app with None as dict
        with self.assertRaises(TypeError) as context:
            PartialApplication(None, None)

        self.assertTrue(isinstance(context.exception, TypeError))

        # build a bad app with invalid view type
        with self.assertRaises(ValueError) as context:
            config = PartialApplicationConfiguration.generic_root()
            config['type'] = 3
            PartialApplication(None,
                               config)
        self.assertTrue(isinstance(context.exception, ValueError))

        # build a root app and toplevel app with generic configs
        app = PartialApplication(None, PartialApplicationConfiguration.generic_root())
        ext = PartialApplication(None, PartialApplicationConfiguration.generic_toplevel())

        # then close in proper order
        ext.close()
        app.close()

    def test_application_task(self):
        """test application task builds
        """
        model = Model()
        app = PartialApplication(model, PartialApplicationConfiguration.generic_root())
        task = ApplicationTask(app, model)
        self.assertIsNotNone(task)

        self.assertTrue(isinstance(task.application, PartialApplication))
        self.assertTrue(isinstance(task.model, Model))

        app.close()

    def test_base_menu(self):
        """test base menu builds
        """
        app = PartialApplication(None, PartialApplicationConfiguration.generic_root())
        menu = BaseMenu(app.parent)
        self.assertIsNotNone(menu)

        self.assertTrue(isinstance(menu.root, (Tk, Toplevel)))
        self.assertTrue(isinstance(menu.menu, Menu))

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

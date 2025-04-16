"""types test suite
    """
from __future__ import annotations


from tkinter import Tk
import unittest


from .abc import (
    Model,
)


from .application import (
    Application,
    PartialApplicationConfiguration
)

from .hashlist import HashList
from .safelist import SafeList


__all__ = (
    'TestTypes',
)


class TestTypes(unittest.TestCase):
    """Testing class for types
    """

    def test_application(self):
        """test application builds
        """
        # test generic build with on model
        app = Application(None, PartialApplicationConfiguration.generic_root())
        self.assertIsNotNone(app)
        self.assertTrue(isinstance(app.parent, Tk))
        app.close()

        # test generic build with basic model
        model = Model()
        app = Application(model, PartialApplicationConfiguration.generic_root())
        self.assertIsNotNone(app)
        self.assertTrue(isinstance(app.parent, Tk))
        self.assertEqual(model, app.model)

        # check menu is built
        self.assertIsNotNone(app.menu)
        self.assertIsNotNone(app.menu.file)
        self.assertIsNotNone(app.menu.edit)
        self.assertIsNotNone(app.menu.tools)
        self.assertIsNotNone(app.menu.view)
        self.assertIsNotNone(app.menu.help)

        # can set a good model
        new_model = Model()
        app.set_model(new_model)
        self.assertEqual(new_model, app.model)

        # can't set a bad model
        with self.assertRaises(TypeError) as context:
            app.set_model(1)
        self.assertTrue(isinstance(context.exception, TypeError))

        app.close()

    def test_hash(self):
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
        self.assertIsNotNone(my_list.by_name('value1'))
        self.assertIsNotNone(my_list.by_name('value2'))
        self.assertIsNotNone(my_list.by_name('value3'))

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

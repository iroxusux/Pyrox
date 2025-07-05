"""types test suite
    """
from __future__ import annotations


from tkinter import Listbox
import unittest


from ..abc import PyroxObject
from .pyroxguiobject import PyroxGuiObject
from .listbox import UserListbox


class TestPyroxOGuibject(unittest.TestCase):
    """Unit tests for the PyroxOGuibject class."""

    def test_name(self):
        obj = PyroxGuiObject(PyroxObject())
        self.assertEqual(obj.name, 'PyroxGuiObject')

    def test_description(self):
        obj = PyroxGuiObject(PyroxObject())
        self.assertEqual(obj.description, '')

    def test_public_attributes(self):
        obj = PyroxGuiObject(PyroxObject())
        attrs = obj.public_attributes()
        self.assertIn('id', attrs)
        self.assertIn('logger', attrs)
        self.assertNotIn('_logger', attrs)  # Private attribute should not be included


class TestTypes(unittest.TestCase):
    """Testing class for types
    """

    def test_userlistbox(self):
        """test userlistbox
        """

        lb = UserListbox()
        self.assertIsInstance(lb, Listbox)
        my_data = [
            'one',
            'two',
            'three',
        ]

        self.assertTrue(len(lb) == 0)

        lb.fill(my_data)
        self.assertTrue(len(lb) == 3)

        # test refreshing the data and validate length is equal
        length = len(lb)
        lb.fill(my_data)
        self.assertEqual(len(lb), length)

        lb.clear()
        self.assertTrue(len(lb) == 0)

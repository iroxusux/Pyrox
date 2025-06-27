"""types test suite
    """
from __future__ import annotations


from tkinter import Listbox
import unittest


from .listbox import UserListbox


__all__ = (
    'TestTypes',
)


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

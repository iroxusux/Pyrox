"""types test suite
    """
from __future__ import annotations


import unittest


from . import utils


__all__ = (
    'TestUtils',
)


class TestUtils(unittest.TestCase):
    """Testing class for utilities
    """

    def test_bit_operations(self):
        """test bit operations perform correctly
        """

        my_value = utils.SliceableInt(0)

        my_value.set_bit(0)

        self.assertEqual(my_value, 1)
        self.assertTrue(my_value.read_bit(0))

        my_value.set_bit(1)

        self.assertEqual(my_value, 3)
        self.assertTrue(my_value.read_bit(1))

        my_value.clear_bit(0)

        self.assertEqual(my_value, 2)
        self.assertFalse(my_value.read_bit(0))
        self.assertTrue(my_value.read_bit(1))

        self.assertIsInstance(my_value, utils.SliceableInt)

        my_value.set_value(8)

        self.assertFalse(my_value.read_bit(0))
        self.assertFalse(my_value.read_bit(1))
        self.assertFalse(my_value.read_bit(2))
        self.assertTrue(my_value.read_bit(3))

        my_value.clear()

        self.assertEqual(my_value, 0)

        self.assertIsInstance(my_value, utils.SliceableInt)

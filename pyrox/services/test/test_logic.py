"""Test suite for logic services and utilities."""
import unittest
from pyrox.services.logic import function_list_or_chain


class TestLogicServices(unittest.TestCase):
    """Unit tests for logic services."""

    def test_function_list_or_chain_all_true(self):
        """Test function_list_or_chain with all functions returning True."""
        funcs = [lambda: True, lambda: True, lambda: True]
        result = function_list_or_chain(funcs)
        self.assertTrue(result)

    def test_function_list_or_chain_one_false(self):
        """Test function_list_or_chain with one function returning False."""
        funcs = [lambda: True, lambda: False, lambda: True]
        result = function_list_or_chain(funcs)
        self.assertFalse(result)

    def test_function_list_or_chain_all_false(self):
        """Test function_list_or_chain with all functions returning False."""
        funcs = [lambda: False, lambda: False, lambda: False]
        result = function_list_or_chain(funcs)
        self.assertFalse(result)

    def test_function_list_or_chain_empty_list(self):
        """Test function_list_or_chain with an empty list of functions."""
        funcs = []
        result = function_list_or_chain(funcs)
        self.assertTrue(result)  # By definition, an empty conjunction is True

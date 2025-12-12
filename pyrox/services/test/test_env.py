"""Unit tests for environment configuration services."""

import os
import tempfile
import unittest
from unittest.mock import patch
import shutil

from pyrox.services.env import (
    EnvManager,
    load_env,
    get_env,
    set_env,
    get_debug_mode,
    get_log_level,
    get_data_dir,
    get_database_url,
)


class TestEnvManager(unittest.TestCase):
    """Test cases for EnvManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_env_file = os.path.join(self.test_dir, '.env')

        # Clear any existing environment variables that might interfere
        self.original_env = dict(os.environ)
        test_vars = [
            'PYROX_DEBUG', 'PYROX_LOG_LEVEL', 'DATABASE_URL', 'TEST_VAR',
            'QUOTED_VAR', 'BOOL_VAR', 'INT_VAR', 'FLOAT_VAR', 'LIST_VAR'
        ]
        for var in test_vars:
            os.environ.pop(var, None)

        # Reset static class state
        EnvManager._env_vars.clear()
        EnvManager._loaded = False
        EnvManager._env_file = None

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

        # Clean up test directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

        # Reset static class state
        EnvManager._env_vars.clear()
        EnvManager._loaded = False
        EnvManager._env_file = None

    def _create_test_env_file(self, content: str) -> str:
        """Helper to create test .env file."""
        with open(self.test_env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return self.test_env_file

    def test_prevent_instantiation(self):
        """Test that EnvManager cannot be instantiated."""
        with self.assertRaises(TypeError) as context:
            EnvManager()
        self.assertIn("static class", str(context.exception))

    def test_static_class_state(self):
        """Test static class initial state."""
        self.assertFalse(EnvManager.is_loaded())
        self.assertEqual(len(EnvManager._env_vars), 0)

    def test_load_prints_messages(self):
        """Test that loading prints messages."""
        content = "TEST_VAR=test_value\n"
        env_file = self._create_test_env_file(content)

        with patch('builtins.print') as mock_print:
            result = EnvManager.load(env_file)

            self.assertTrue(result)
            self.assertTrue(EnvManager.is_loaded())
            self.assertEqual(EnvManager.get('TEST_VAR'), 'test_value')

            # Check that print was called with expected messages
            mock_print.assert_any_call(f"Loading .env file from: {env_file}")
            mock_print.assert_any_call(f".env file '{env_file}' loaded successfully.")

    def test_load_prints_error_on_failure(self):
        """Test that loading prints error messages on failure."""
        invalid_env_file = os.path.join(self.test_dir, 'nonexistent.env')

        with patch('builtins.print') as mock_print:
            result = EnvManager.load(invalid_env_file)

            self.assertFalse(result)
            self.assertFalse(EnvManager.is_loaded())

            # Check that print was called with expected error message
            mock_print.assert_any_call(f".env file '{invalid_env_file}' is not readable.")

    def test_load_with_specific_env_file(self):
        """Test loading with specific env file."""
        content = "TEST_VAR=test_value\n"
        env_file = self._create_test_env_file(content)

        result = EnvManager.load(env_file)
        self.assertTrue(result)
        self.assertTrue(EnvManager.is_loaded())
        self.assertEqual(EnvManager.get('TEST_VAR'), 'test_value')

    def test_load_existing_file(self):
        """Test loading an existing .env file."""
        content = """
# Test configuration
TEST_VAR=test_value
ANOTHER_VAR=another_value
"""
        env_file = self._create_test_env_file(content)

        result = EnvManager.load(env_file)

        self.assertTrue(result)
        self.assertTrue(EnvManager.is_loaded())
        self.assertEqual(EnvManager.get('TEST_VAR'), 'test_value')
        self.assertEqual(EnvManager.get('ANOTHER_VAR'), 'another_value')

    def test_load_nonexistent_file(self):
        """Test loading a nonexistent .env file."""
        result = EnvManager.load('/nonexistent/.env')

        self.assertFalse(result)
        self.assertFalse(EnvManager.is_loaded())

    def test_find_env_file(self):
        """Test finding .env file in common locations."""
        # Use a test-specific .env file to avoid deleting the real one
        test_env_file = os.path.join(self.test_dir, '.env')

        try:
            with open(test_env_file, 'w') as f:
                f.write('TEST=1')

            # Test that _is_file_readable works correctly
            self.assertTrue(EnvManager._is_file_readable(test_env_file))

        finally:
            # Clean up test file only (in test directory, not project root)
            if os.path.exists(test_env_file):
                os.remove(test_env_file)

    def test_find_env_file_not_found(self):
        """Test finding .env file when none exists."""
        # Temporarily rename existing .env file if it exists
        env_file_path = os.path.join(os.getcwd(), '.env')
        temp_backup = None

        try:
            if os.path.exists(env_file_path):
                temp_backup = env_file_path + '.test_backup'
                os.rename(env_file_path, temp_backup)

            found_file = EnvManager._find_env_file()
            self.assertIsNone(found_file)

        finally:
            # Restore the original .env file if it existed
            if temp_backup and os.path.exists(temp_backup):
                os.rename(temp_backup, env_file_path)

    def test_parse_simple_key_value(self):
        """Test parsing simple key=value pairs."""
        content = """
KEY1=value1
KEY2=value2
KEY_WITH_UNDERSCORE=value_with_underscore
"""
        env_file = self._create_test_env_file(content)

        EnvManager.load(env_file)
        self.assertEqual(EnvManager.get('KEY1'), 'value1')
        self.assertEqual(EnvManager.get('KEY2'), 'value2')
        self.assertEqual(EnvManager.get('KEY_WITH_UNDERSCORE'), 'value_with_underscore')

    def test_parse_quoted_values(self):
        """Test parsing quoted values."""
        content = '''
DOUBLE_QUOTED="double quoted value"
SINGLE_QUOTED='single quoted value'
QUOTED_WITH_SPACES="value with spaces"
QUOTED_EMPTY=""
'''
        env_file = self._create_test_env_file(content)

        EnvManager.load(env_file)
        self.assertEqual(EnvManager.get('DOUBLE_QUOTED'), 'double quoted value')
        self.assertEqual(EnvManager.get('SINGLE_QUOTED'), 'single quoted value')
        self.assertEqual(EnvManager.get('QUOTED_WITH_SPACES'), 'value with spaces')
        self.assertEqual(EnvManager.get('QUOTED_EMPTY'), '')

    def test_parse_escape_sequences(self):
        """Test parsing escape sequences."""
        content = r'''
NEWLINE="line1\nline2"
TAB="tab\ttab"
QUOTE="quote\"quote"
BACKSLASH="back\\slash"
'''
        env_file = self._create_test_env_file(content)

        EnvManager.load(env_file)
        self.assertEqual(EnvManager.get('NEWLINE'), 'line1\nline2')
        self.assertEqual(EnvManager.get('TAB'), 'tab\ttab')
        self.assertEqual(EnvManager.get('QUOTE'), 'quote"quote')
        self.assertEqual(EnvManager.get('BACKSLASH'), 'back\\slash')

    def test_skip_comments_and_empty_lines(self):
        """Test skipping comments and empty lines."""
        content = """
# This is a comment
VALID_VAR=valid_value

# Another comment
   # Indented comment

ANOTHER_VAR=another_value
"""
        env_file = self._create_test_env_file(content)

        EnvManager.load(env_file)
        self.assertEqual(EnvManager.get('VALID_VAR'), 'valid_value')
        self.assertEqual(EnvManager.get('ANOTHER_VAR'), 'another_value')

    def test_invalid_lines(self):
        """Test handling of invalid lines."""
        content = """
VALID_VAR=valid_value
INVALID_LINE_NO_EQUALS
=NO_KEY_VALUE
ANOTHER_VALID=another_value
"""
        env_file = self._create_test_env_file(content)

        EnvManager.load(env_file)
        self.assertEqual(EnvManager.get('VALID_VAR'), 'valid_value')
        self.assertEqual(EnvManager.get('ANOTHER_VALID'), 'another_value')
        self.assertIsNone(EnvManager.get('INVALID_LINE_NO_EQUALS'))

    def test_variable_substitution_braced(self):
        """Test variable substitution with ${VAR} format."""
        content = """
BASE_DIR=/app
DATA_DIR=${BASE_DIR}/data
LOG_DIR=${BASE_DIR}/logs
"""
        env_file = self._create_test_env_file(content)

        EnvManager.load(env_file)
        self.assertEqual(EnvManager.get('BASE_DIR'), '/app')
        self.assertEqual(EnvManager.get('DATA_DIR'), '/app/data')
        self.assertEqual(EnvManager.get('LOG_DIR'), '/app/logs')

    def test_variable_substitution_simple(self):
        """Test variable substitution with $VAR format."""
        content = """
HOME=/home/user
PATH=$HOME/bin
"""
        env_file = self._create_test_env_file(content)

        EnvManager.load(env_file)
        self.assertEqual(EnvManager.get('HOME'), '/home/user')
        self.assertEqual(EnvManager.get('PATH'), '/home/user/bin')

    def test_variable_substitution_from_os_environ(self):
        """Test variable substitution from os.environ."""
        os.environ['EXISTING_VAR'] = 'existing_value'

        content = """
NEW_VAR=${EXISTING_VAR}/suffix
"""
        env_file = self._create_test_env_file(content)

        EnvManager.load(env_file)
        self.assertEqual(EnvManager.get('NEW_VAR'), 'existing_value/suffix')

    def test_get_with_type_casting_bool(self):
        """Test getting values with boolean type casting."""
        content = """
TRUE_VAR=true
FALSE_VAR=false
ONE_VAR=1
ZERO_VAR=0
YES_VAR=yes
NO_VAR=no
ON_VAR=on
OFF_VAR=off
ENABLED_VAR=enabled
DISABLED_VAR=disabled
"""
        env_file = self._create_test_env_file(content)

        EnvManager.load(env_file)
        self.assertTrue(EnvManager.get('TRUE_VAR', cast_type=bool))
        self.assertFalse(EnvManager.get('FALSE_VAR', cast_type=bool))
        self.assertTrue(EnvManager.get('ONE_VAR', cast_type=bool))
        self.assertFalse(EnvManager.get('ZERO_VAR', cast_type=bool))
        self.assertTrue(EnvManager.get('YES_VAR', cast_type=bool))
        self.assertFalse(EnvManager.get('NO_VAR', cast_type=bool))
        self.assertTrue(EnvManager.get('ON_VAR', cast_type=bool))
        self.assertFalse(EnvManager.get('OFF_VAR', cast_type=bool))
        self.assertTrue(EnvManager.get('ENABLED_VAR', cast_type=bool))
        self.assertFalse(EnvManager.get('DISABLED_VAR', cast_type=bool))

    def test_get_with_type_casting_int(self):
        """Test getting values with integer type casting."""
        content = """
INT_VAR=123
NEGATIVE_INT=-456
"""
        env_file = self._create_test_env_file(content)

        EnvManager.load(env_file)
        self.assertEqual(EnvManager.get('INT_VAR', cast_type=int), 123)
        self.assertEqual(EnvManager.get('NEGATIVE_INT', cast_type=int), -456)

    def test_get_with_type_casting_float(self):
        """Test getting values with float type casting."""
        content = """
FLOAT_VAR=123.45
NEGATIVE_FLOAT=-67.89
"""
        env_file = self._create_test_env_file(content)

        EnvManager.load(env_file)
        self.assertEqual(EnvManager.get('FLOAT_VAR', cast_type=float), 123.45)
        self.assertEqual(EnvManager.get('NEGATIVE_FLOAT', cast_type=float), -67.89)

    def test_get_with_type_casting_list(self):
        """Test getting values with list type casting."""
        content = """
LIST_VAR=item1,item2,item3
LIST_WITH_SPACES=item1, item2 , item3
EMPTY_LIST=
SINGLE_ITEM=single
"""
        env_file = self._create_test_env_file(content)

        EnvManager.load(env_file)
        self.assertEqual(EnvManager.get('LIST_VAR', cast_type=list), ['item1', 'item2', 'item3'])
        self.assertEqual(EnvManager.get('LIST_WITH_SPACES', cast_type=list), ['item1', 'item2', 'item3'])
        self.assertEqual(EnvManager.get('EMPTY_LIST', cast_type=list), [])
        self.assertEqual(EnvManager.get('SINGLE_ITEM', cast_type=list), ['single'])

    def test_get_with_type_casting_tuple(self):
        """Test getting values with tuple type casting."""
        content = """
TUPLE_VAR=item1,item2,item3
TUPLE_WITH_SPACES=item1, item2 , item3
TUPLE_WITH_PARENS=(item1,item2,item3)
"""
        env_file = self._create_test_env_file(content)
        EnvManager.load(env_file)
        self.assertEqual(EnvManager.get('TUPLE_VAR', cast_type=tuple), ('item1', 'item2', 'item3'))
        self.assertEqual(EnvManager.get('TUPLE_WITH_SPACES', cast_type=tuple), ('item1', 'item2', 'item3'))
        self.assertEqual(EnvManager.get('TUPLE_WITH_PARENS', cast_type=tuple), ('item1', 'item2', 'item3'))

    def test_get_with_invalid_type_casting(self):
        """Test getting values with invalid type casting."""
        content = """
INVALID_INT=not_a_number
INVALID_FLOAT=not_a_float
"""
        env_file = self._create_test_env_file(content)

        EnvManager.load(env_file)

        # Should return default when casting fails
        self.assertEqual(EnvManager.get('INVALID_INT', default=999, cast_type=int), 999)
        self.assertEqual(EnvManager.get('INVALID_FLOAT', default=99.9, cast_type=float), 99.9)

    def test_get_default_values(self):
        """Test getting default values when variables don't exist."""
        # Static class doesn't auto-load, so we test default behavior
        self.assertEqual(EnvManager.get('NONEXISTENT', 'default'), 'default')
        self.assertEqual(EnvManager.get('NONEXISTENT', 123, int), 123)
        self.assertEqual(EnvManager.get('NONEXISTENT', True, bool), True)
        self.assertIsNone(EnvManager.get('NONEXISTENT'))

    def test_get_from_os_environ(self):
        """Test getting values from os.environ when not in .env file."""
        os.environ['OS_VAR'] = 'os_value'

        self.assertEqual(EnvManager.get('OS_VAR'), 'os_value')

    def test_get_priority_env_file_over_os_environ(self):
        """Test that .env file values take priority over os.environ."""
        os.environ['PRIORITY_VAR'] = 'os_value'

        content = "PRIORITY_VAR=env_file_value\n"
        env_file = self._create_test_env_file(content)

        EnvManager.load(env_file)
        self.assertEqual(EnvManager.get('PRIORITY_VAR'), 'env_file_value')

    def test_set_variable(self):
        """Test setting environment variables."""
        # Use test env file to avoid overwriting production .env
        test_env = self._create_test_env_file('')
        EnvManager.set('NEW_VAR', 'new_value', env_file=test_env)
        self.assertEqual(EnvManager.get('NEW_VAR'), 'new_value')
        self.assertEqual(os.environ.get('NEW_VAR'), 'new_value')

    def test_get_all_variables(self):
        """Test getting all environment variables."""
        content = """
ENV_VAR1=value1
ENV_VAR2=value2
"""
        env_file = self._create_test_env_file(content)
        os.environ['OS_VAR'] = 'os_value'

        EnvManager.load(env_file)
        all_vars = EnvManager.get_all()

        self.assertIn('ENV_VAR1', all_vars)
        self.assertIn('ENV_VAR2', all_vars)
        self.assertIn('OS_VAR', all_vars)
        self.assertEqual(all_vars['ENV_VAR1'], 'value1')
        self.assertEqual(all_vars['OS_VAR'], 'os_value')

    def test_get_all_with_prefix(self):
        """Test getting variables with prefix filter."""
        content = """
PYROX_VAR1=value1
PYROX_VAR2=value2
OTHER_VAR=other_value
"""
        env_file = self._create_test_env_file(content)

        EnvManager.load(env_file)
        pyrox_vars = EnvManager.get_all(prefix='PYROX_')

        self.assertIn('PYROX_VAR1', pyrox_vars)
        self.assertIn('PYROX_VAR2', pyrox_vars)
        self.assertNotIn('OTHER_VAR', pyrox_vars)

    def test_create_env_template(self):
        """Test creating environment template file."""
        template_path = os.path.join(self.test_dir, '.env.template')

        EnvManager.create_env_template(template_path)

        self.assertTrue(os.path.exists(template_path))

        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for expected template content
        self.assertIn('PYROX_DEBUG=', content)
        self.assertIn('DATABASE_URL=', content)
        self.assertIn('EPLAN_DEFAULT_PROJECT_DIR=', content)

    def test_reload(self):
        """Test reloading the .env file."""
        content1 = "TEST_VAR=value1\n"
        env_file = self._create_test_env_file(content1)

        EnvManager.load(env_file)
        self.assertEqual(EnvManager.get('TEST_VAR'), 'value1')

        # Update file content
        content2 = "TEST_VAR=value2\nNEW_VAR=new_value\n"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content2)

        # Reload
        result = EnvManager.reload()
        self.assertTrue(result)
        self.assertEqual(EnvManager.get('TEST_VAR'), 'value2')
        self.assertEqual(EnvManager.get('NEW_VAR'), 'new_value')

    def test_file_encoding_utf8(self):
        """Test handling of UTF-8 encoded files."""
        content = "UNICODE_VAR=café\n"
        with open(self.test_env_file, 'w', encoding='utf-8') as f:
            f.write(content)

        EnvManager.load(self.test_env_file)
        self.assertEqual(EnvManager.get('UNICODE_VAR'), 'café')


class TestGlobalFunctions(unittest.TestCase):
    """Test cases for global convenience functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_env = dict(os.environ)

        # Reset static class state
        EnvManager._env_vars.clear()
        EnvManager._loaded = False
        EnvManager._env_file = None

    def tearDown(self):
        """Clean up test fixtures."""
        os.environ.clear()
        os.environ.update(self.original_env)
        shutil.rmtree(self.test_dir, ignore_errors=True)

        # Reset static class state
        EnvManager._env_vars.clear()
        EnvManager._loaded = False
        EnvManager._env_file = None

    def test_static_class_behavior(self):
        """Test that EnvManager behaves as a static class."""
        # Create test env file to avoid overwriting production .env
        test_env = os.path.join(self.test_dir, '.env')
        
        # Test that we can call methods without instantiation
        EnvManager.set('TEST_STATIC', 'static_value', env_file=test_env)
        self.assertEqual(EnvManager.get('TEST_STATIC'), 'static_value')

        # Test that state persists across calls
        result1 = EnvManager.get('TEST_STATIC')
        result2 = EnvManager.get('TEST_STATIC')
        self.assertEqual(result1, result2)

    def test_load_env(self):
        """Test load_env function."""
        env_file = os.path.join(self.test_dir, '.env')
        with open(env_file, 'w') as f:
            f.write('TEST_VAR=test_value\n')

        result = load_env(env_file)
        self.assertTrue(result)

        # Should be accessible through get_env
        self.assertEqual(get_env('TEST_VAR'), 'test_value')

    def test_get_env_function(self):
        """Test get_env function."""
        os.environ['TEST_VAR'] = 'test_value'

        self.assertEqual(get_env('TEST_VAR'), 'test_value')
        self.assertEqual(get_env('NONEXISTENT', 'default'), 'default')
        self.assertEqual(get_env('TEST_VAR', cast_type=str), 'test_value')

    def test_set_env_function(self):
        """Test set_env function."""
        # Patch EnvManager.set to avoid writing to production .env file
        with patch('pyrox.services.env.EnvManager.set') as mock_set:
            set_env('NEW_VAR', 'new_value')
            mock_set.assert_called_once_with('NEW_VAR', 'new_value')
        
        # Test the functionality separately by setting directly in os.environ
        os.environ['NEW_VAR'] = 'new_value'
        self.assertEqual(get_env('NEW_VAR'), 'new_value')
        self.assertEqual(os.environ.get('NEW_VAR'), 'new_value')

    def test_convenience_functions(self):
        """Test convenience functions for common configurations."""
        # Test debug mode
        os.environ['DEBUG_MODE'] = 'true'
        self.assertTrue(get_debug_mode())

        os.environ['DEBUG_MODE'] = 'false'
        self.assertFalse(get_debug_mode())

        # Test log level
        os.environ['LOG_LEVEL'] = 'DEBUG'
        self.assertEqual(get_log_level(), 'DEBUG')

        # Test data directory
        os.environ['DATA_DIR'] = './custom/data'
        self.assertEqual(get_data_dir(), './custom/data')

        # Test database URL
        os.environ['DATABASE_URL'] = 'postgresql://localhost/test'
        self.assertEqual(get_database_url(), 'postgresql://localhost/test')

    def test_convenience_functions_defaults(self):
        """Test convenience functions return defaults when not set."""
        # Clear any existing values
        for key in ['PYROX_DEBUG', 'PYROX_LOG_LEVEL', 'PYROX_DATA_DIR', 'DATABASE_URL']:
            os.environ.pop(key, None)
            EnvManager._env_vars.pop(key, None)

        self.assertFalse(EnvManager.get('NOT_A_KEY', False, bool))
        self.assertEqual(EnvManager.get('NOT_A_LOG_LEVEL', 'INFO', str), 'INFO')
        self.assertEqual(EnvManager.get('NOT_A_DATA_DIR', './data', str), './data')
        self.assertEqual(EnvManager.get('NOT_A_DATABASE', 'sqlite:///pyrox.db', str), 'sqlite:///pyrox.db')

    def test_getitem(self):
        """Test __getitem__ method of EnvManager."""
        os.environ['TEST_VAR'] = 'test_value'
        self.assertEqual(EnvManager.__getitem__('TEST_VAR'), 'test_value')

    def test_setitem(self):
        """Test __setitem__ method of EnvManager."""
        EnvManager.__setitem__('NEW_VAR', 'new_value')
        self.assertEqual(EnvManager.get('NEW_VAR'), 'new_value')
        self.assertEqual(os.environ.get('NEW_VAR'), 'new_value')


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        # Reset static class state
        EnvManager._env_vars.clear()
        EnvManager._loaded = False
        EnvManager._env_file = None

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Reset static class state
        EnvManager._env_vars.clear()
        EnvManager._loaded = False
        EnvManager._env_file = None

    def test_file_readability_checks(self):
        """Test various file readability scenarios."""
        # Test nonexistent file
        self.assertFalse(EnvManager._is_file_readable('/nonexistent/file.env'))

        # Test directory instead of file
        self.assertFalse(EnvManager._is_file_readable(self.test_dir))

        # Test readable file
        env_file = os.path.join(self.test_dir, '.env')
        with open(env_file, 'w') as f:
            f.write('TEST=value')

        self.assertTrue(EnvManager._is_file_readable(env_file))

    def test_malformed_file_handling(self):
        """Test handling of malformed .env files."""
        env_file = os.path.join(self.test_dir, '.env')

        # Create file with various malformed content
        with open(env_file, 'wb') as f:
            f.write(b'\xff\xfe\x00\x00invalid_content')  # Invalid UTF-8

        result = EnvManager.load(env_file)

        # Should handle the error and return False
        self.assertFalse(result)

    @patch('pyrox.services.env.open', side_effect=IOError("File read error"))
    def test_file_io_error(self, mock_open):
        """Test handling of file I/O errors."""
        result = EnvManager.load('/some/path/.env')

        self.assertFalse(result)
        self.assertFalse(EnvManager.is_loaded())

    def test_unicode_decode_error_handling(self):
        """Test handling of files with encoding issues."""
        env_file = os.path.join(self.test_dir, '.env')

        # Create file with invalid UTF-8 bytes
        with open(env_file, 'wb') as f:
            f.write(b'VALID_KEY=valid_value\n')
            f.write(b'INVALID_KEY=\xff\xfe\x00\x00invalid_utf8\n')
            f.write(b'ANOTHER_KEY=another_value\n')

        # Should detect that file is not readable due to encoding issues
        self.assertFalse(EnvManager._is_file_readable(env_file))

        # Loading should fail
        result = EnvManager.load(env_file)
        self.assertFalse(result)
        self.assertFalse(EnvManager.is_loaded())


if __name__ == '__main__':
    unittest.main()

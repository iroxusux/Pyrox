"""Unit tests for environment configuration services."""

import os
import tempfile
import unittest
from unittest.mock import patch
import shutil

from pyrox.services.env import (
    EnvManager,
    get_env_manager,
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

        # Reset global manager
        global _env_manager
        _env_manager = None

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

        # Clean up test directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

        # Reset global manager
        global _env_manager
        _env_manager = None

    def _create_test_env_file(self, content: str) -> str:
        """Helper to create test .env file."""
        with open(self.test_env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return self.test_env_file

    def test_init_with_auto_load_disabled(self):
        """Test EnvManager initialization with auto_load=False."""
        manager = EnvManager(auto_load=False)
        self.assertFalse(manager.is_loaded())
        self.assertEqual(len(manager._env_vars), 0)

    def test_init_with_specific_env_file(self):
        """Test EnvManager initialization with specific env file."""
        content = "TEST_VAR=test_value\n"
        env_file = self._create_test_env_file(content)

        manager = EnvManager(env_file=env_file)
        self.assertTrue(manager.is_loaded())
        self.assertEqual(manager.get('TEST_VAR'), 'test_value')

    def test_load_existing_file(self):
        """Test loading an existing .env file."""
        content = """
# Test configuration
TEST_VAR=test_value
ANOTHER_VAR=another_value
"""
        env_file = self._create_test_env_file(content)

        manager = EnvManager(auto_load=False)
        result = manager.load(env_file)

        self.assertTrue(result)
        self.assertTrue(manager.is_loaded())
        self.assertEqual(manager.get('TEST_VAR'), 'test_value')
        self.assertEqual(manager.get('ANOTHER_VAR'), 'another_value')

    def test_load_nonexistent_file(self):
        """Test loading a nonexistent .env file."""
        manager = EnvManager(auto_load=False)
        result = manager.load('/nonexistent/.env')

        self.assertFalse(result)
        self.assertFalse(manager.is_loaded())

    def test_find_env_file(self):
        """Test finding .env file in common locations."""
        # Create .env file in current directory
        cwd_env = os.path.join(os.getcwd(), '.env')

        try:
            with open(cwd_env, 'w') as f:
                f.write('TEST=1')

            manager = EnvManager(auto_load=False)
            found_file = manager._find_env_file()

            self.assertEqual(found_file, cwd_env)

        finally:
            # Clean up
            if os.path.exists(cwd_env):
                os.remove(cwd_env)

    def test_find_env_file_not_found(self):
        """Test finding .env file when none exists."""
        manager = EnvManager(auto_load=False)
        found_file = manager._find_env_file()
        self.assertIsNone(found_file)

    def test_parse_simple_key_value(self):
        """Test parsing simple key=value pairs."""
        content = """
KEY1=value1
KEY2=value2
KEY_WITH_UNDERSCORE=value_with_underscore
"""
        env_file = self._create_test_env_file(content)

        manager = EnvManager(env_file=env_file)
        self.assertEqual(manager.get('KEY1'), 'value1')
        self.assertEqual(manager.get('KEY2'), 'value2')
        self.assertEqual(manager.get('KEY_WITH_UNDERSCORE'), 'value_with_underscore')

    def test_parse_quoted_values(self):
        """Test parsing quoted values."""
        content = '''
DOUBLE_QUOTED="double quoted value"
SINGLE_QUOTED='single quoted value'
QUOTED_WITH_SPACES="value with spaces"
QUOTED_EMPTY=""
'''
        env_file = self._create_test_env_file(content)

        manager = EnvManager(env_file=env_file)
        self.assertEqual(manager.get('DOUBLE_QUOTED'), 'double quoted value')
        self.assertEqual(manager.get('SINGLE_QUOTED'), 'single quoted value')
        self.assertEqual(manager.get('QUOTED_WITH_SPACES'), 'value with spaces')
        self.assertEqual(manager.get('QUOTED_EMPTY'), '')

    def test_parse_escape_sequences(self):
        """Test parsing escape sequences."""
        content = r'''
NEWLINE="line1\nline2"
TAB="tab\ttab"
QUOTE="quote\"quote"
BACKSLASH="back\\slash"
'''
        env_file = self._create_test_env_file(content)

        manager = EnvManager(env_file=env_file)
        self.assertEqual(manager.get('NEWLINE'), 'line1\nline2')
        self.assertEqual(manager.get('TAB'), 'tab\ttab')
        self.assertEqual(manager.get('QUOTE'), 'quote"quote')
        self.assertEqual(manager.get('BACKSLASH'), 'back\\slash')

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

        manager = EnvManager(env_file=env_file)
        self.assertEqual(manager.get('VALID_VAR'), 'valid_value')
        self.assertEqual(manager.get('ANOTHER_VAR'), 'another_value')

    def test_invalid_lines(self):
        """Test handling of invalid lines."""
        content = """
VALID_VAR=valid_value
INVALID_LINE_NO_EQUALS
=NO_KEY_VALUE
ANOTHER_VALID=another_value
"""
        env_file = self._create_test_env_file(content)

        manager = EnvManager(env_file=env_file)
        self.assertEqual(manager.get('VALID_VAR'), 'valid_value')
        self.assertEqual(manager.get('ANOTHER_VALID'), 'another_value')
        self.assertIsNone(manager.get('INVALID_LINE_NO_EQUALS'))

    def test_variable_substitution_braced(self):
        """Test variable substitution with ${VAR} format."""
        content = """
BASE_DIR=/app
DATA_DIR=${BASE_DIR}/data
LOG_DIR=${BASE_DIR}/logs
"""
        env_file = self._create_test_env_file(content)

        manager = EnvManager(env_file=env_file)
        self.assertEqual(manager.get('BASE_DIR'), '/app')
        self.assertEqual(manager.get('DATA_DIR'), '/app/data')
        self.assertEqual(manager.get('LOG_DIR'), '/app/logs')

    def test_variable_substitution_simple(self):
        """Test variable substitution with $VAR format."""
        content = """
HOME=/home/user
PATH=$HOME/bin
"""
        env_file = self._create_test_env_file(content)

        manager = EnvManager(env_file=env_file)
        self.assertEqual(manager.get('HOME'), '/home/user')
        self.assertEqual(manager.get('PATH'), '/home/user/bin')

    def test_variable_substitution_from_os_environ(self):
        """Test variable substitution from os.environ."""
        os.environ['EXISTING_VAR'] = 'existing_value'

        content = """
NEW_VAR=${EXISTING_VAR}/suffix
"""
        env_file = self._create_test_env_file(content)

        manager = EnvManager(env_file=env_file)
        self.assertEqual(manager.get('NEW_VAR'), 'existing_value/suffix')

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

        manager = EnvManager(env_file=env_file)
        self.assertTrue(manager.get('TRUE_VAR', cast_type=bool))
        self.assertFalse(manager.get('FALSE_VAR', cast_type=bool))
        self.assertTrue(manager.get('ONE_VAR', cast_type=bool))
        self.assertFalse(manager.get('ZERO_VAR', cast_type=bool))
        self.assertTrue(manager.get('YES_VAR', cast_type=bool))
        self.assertFalse(manager.get('NO_VAR', cast_type=bool))
        self.assertTrue(manager.get('ON_VAR', cast_type=bool))
        self.assertFalse(manager.get('OFF_VAR', cast_type=bool))
        self.assertTrue(manager.get('ENABLED_VAR', cast_type=bool))
        self.assertFalse(manager.get('DISABLED_VAR', cast_type=bool))

    def test_get_with_type_casting_int(self):
        """Test getting values with integer type casting."""
        content = """
INT_VAR=123
NEGATIVE_INT=-456
"""
        env_file = self._create_test_env_file(content)

        manager = EnvManager(env_file=env_file)
        self.assertEqual(manager.get('INT_VAR', cast_type=int), 123)
        self.assertEqual(manager.get('NEGATIVE_INT', cast_type=int), -456)

    def test_get_with_type_casting_float(self):
        """Test getting values with float type casting."""
        content = """
FLOAT_VAR=123.45
NEGATIVE_FLOAT=-67.89
"""
        env_file = self._create_test_env_file(content)

        manager = EnvManager(env_file=env_file)
        self.assertEqual(manager.get('FLOAT_VAR', cast_type=float), 123.45)
        self.assertEqual(manager.get('NEGATIVE_FLOAT', cast_type=float), -67.89)

    def test_get_with_type_casting_list(self):
        """Test getting values with list type casting."""
        content = """
LIST_VAR=item1,item2,item3
LIST_WITH_SPACES=item1, item2 , item3
EMPTY_LIST=
SINGLE_ITEM=single
"""
        env_file = self._create_test_env_file(content)

        manager = EnvManager(env_file=env_file)
        self.assertEqual(manager.get('LIST_VAR', cast_type=list), ['item1', 'item2', 'item3'])
        self.assertEqual(manager.get('LIST_WITH_SPACES', cast_type=list), ['item1', 'item2', 'item3'])
        self.assertEqual(manager.get('EMPTY_LIST', cast_type=list), [])
        self.assertEqual(manager.get('SINGLE_ITEM', cast_type=list), ['single'])

    def test_get_with_invalid_type_casting(self):
        """Test getting values with invalid type casting."""
        content = """
INVALID_INT=not_a_number
INVALID_FLOAT=not_a_float
"""
        env_file = self._create_test_env_file(content)

        manager = EnvManager(env_file=env_file)

        # Should return default when casting fails
        self.assertEqual(manager.get('INVALID_INT', default=999, cast_type=int), 999)
        self.assertEqual(manager.get('INVALID_FLOAT', default=99.9, cast_type=float), 99.9)

    def test_get_default_values(self):
        """Test getting default values when variables don't exist."""
        manager = EnvManager(auto_load=False)

        self.assertEqual(manager.get('NONEXISTENT', 'default'), 'default')
        self.assertEqual(manager.get('NONEXISTENT', 123, int), 123)
        self.assertEqual(manager.get('NONEXISTENT', True, bool), True)
        self.assertIsNone(manager.get('NONEXISTENT'))

    def test_get_from_os_environ(self):
        """Test getting values from os.environ when not in .env file."""
        os.environ['OS_VAR'] = 'os_value'

        manager = EnvManager(auto_load=False)
        self.assertEqual(manager.get('OS_VAR'), 'os_value')

    def test_get_priority_env_file_over_os_environ(self):
        """Test that .env file values take priority over os.environ."""
        os.environ['PRIORITY_VAR'] = 'os_value'

        content = "PRIORITY_VAR=env_file_value\n"
        env_file = self._create_test_env_file(content)

        manager = EnvManager(env_file=env_file)
        self.assertEqual(manager.get('PRIORITY_VAR'), 'env_file_value')

    def test_set_variable(self):
        """Test setting environment variables."""
        manager = EnvManager(auto_load=False)

        manager.set('NEW_VAR', 'new_value')
        self.assertEqual(manager.get('NEW_VAR'), 'new_value')
        self.assertEqual(os.environ.get('NEW_VAR'), 'new_value')

    def test_set_variable_without_updating_os_environ(self):
        """Test setting variables without updating os.environ."""
        manager = EnvManager(auto_load=False)

        manager.set('NEW_VAR', 'new_value', update_os_environ=False)
        self.assertEqual(manager.get('NEW_VAR'), 'new_value')
        self.assertIsNone(os.environ.get('NEW_VAR'))

    def test_get_all_variables(self):
        """Test getting all environment variables."""
        content = """
ENV_VAR1=value1
ENV_VAR2=value2
"""
        env_file = self._create_test_env_file(content)
        os.environ['OS_VAR'] = 'os_value'

        manager = EnvManager(env_file=env_file)
        all_vars = manager.get_all()

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

        manager = EnvManager(env_file=env_file)
        pyrox_vars = manager.get_all(prefix='PYROX_')

        self.assertIn('PYROX_VAR1', pyrox_vars)
        self.assertIn('PYROX_VAR2', pyrox_vars)
        self.assertNotIn('OTHER_VAR', pyrox_vars)

    def test_create_env_template(self):
        """Test creating environment template file."""
        template_path = os.path.join(self.test_dir, '.env.template')

        manager = EnvManager(auto_load=False)
        manager.create_env_template(template_path)

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

        manager = EnvManager(env_file=env_file)
        self.assertEqual(manager.get('TEST_VAR'), 'value1')

        # Update file content
        content2 = "TEST_VAR=value2\nNEW_VAR=new_value\n"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content2)

        # Reload
        result = manager.reload()
        self.assertTrue(result)
        self.assertEqual(manager.get('TEST_VAR'), 'value2')
        self.assertEqual(manager.get('NEW_VAR'), 'new_value')

    def test_file_encoding_utf8(self):
        """Test handling of UTF-8 encoded files."""
        content = "UNICODE_VAR=café\n"
        with open(self.test_env_file, 'w', encoding='utf-8') as f:
            f.write(content)

        manager = EnvManager(env_file=self.test_env_file)
        self.assertEqual(manager.get('UNICODE_VAR'), 'café')


class TestGlobalFunctions(unittest.TestCase):
    """Test cases for global convenience functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_env = dict(os.environ)

        # Reset global manager
        global _env_manager
        _env_manager = None

    def tearDown(self):
        """Clean up test fixtures."""
        os.environ.clear()
        os.environ.update(self.original_env)
        shutil.rmtree(self.test_dir, ignore_errors=True)

        # Reset global manager
        global _env_manager
        _env_manager = None

    def test_get_env_manager_singleton(self):
        """Test that get_env_manager returns the same instance."""
        manager1 = get_env_manager()
        manager2 = get_env_manager()
        self.assertIs(manager1, manager2)

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
        set_env('NEW_VAR', 'new_value')

        self.assertEqual(get_env('NEW_VAR'), 'new_value')
        self.assertEqual(os.environ.get('NEW_VAR'), 'new_value')

    def test_convenience_functions(self):
        """Test convenience functions for common configurations."""
        # Test debug mode
        os.environ['PYROX_DEBUG'] = 'true'
        self.assertTrue(get_debug_mode())

        os.environ['PYROX_DEBUG'] = 'false'
        self.assertFalse(get_debug_mode())

        # Test log level
        os.environ['PYROX_LOG_LEVEL'] = 'DEBUG'
        self.assertEqual(get_log_level(), 'DEBUG')

        # Test data directory
        os.environ['PYROX_DATA_DIR'] = '/custom/data'
        self.assertEqual(get_data_dir(), '/custom/data')

        # Test database URL
        os.environ['DATABASE_URL'] = 'postgresql://localhost/test'
        self.assertEqual(get_database_url(), 'postgresql://localhost/test')

    def test_convenience_functions_defaults(self):
        """Test convenience functions return defaults when not set."""
        # Clear any existing values
        for key in ['PYROX_DEBUG', 'PYROX_LOG_LEVEL', 'PYROX_DATA_DIR', 'DATABASE_URL']:
            os.environ.pop(key, None)

        self.assertFalse(get_debug_mode())
        self.assertEqual(get_log_level(), 'INFO')
        self.assertEqual(get_data_dir(), './data')
        self.assertEqual(get_database_url(), 'sqlite:///pyrox.db')

    def test_getitem(self):
        """Test __getitem__ method of EnvManager."""
        os.environ['TEST_VAR'] = 'test_value'
        manager = get_env_manager()
        self.assertEqual(manager['TEST_VAR'], 'test_value')

    def test_setitem(self):
        """Test __setitem__ method of EnvManager."""
        manager = get_env_manager()
        manager['NEW_VAR'] = 'new_value'
        self.assertEqual(manager.get('NEW_VAR'), 'new_value')
        self.assertEqual(os.environ.get('NEW_VAR'), 'new_value')


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        global _env_manager
        _env_manager = None

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        global _env_manager
        _env_manager = None

    def test_file_readability_checks(self):
        """Test various file readability scenarios."""
        manager = EnvManager(auto_load=False)

        # Test nonexistent file
        self.assertFalse(manager._is_file_readable('/nonexistent/file.env'))

        # Test directory instead of file
        self.assertFalse(manager._is_file_readable(self.test_dir))

        # Test readable file
        env_file = os.path.join(self.test_dir, '.env')
        with open(env_file, 'w') as f:
            f.write('TEST=value')

        self.assertTrue(manager._is_file_readable(env_file))

    def test_malformed_file_handling(self):
        """Test handling of malformed .env files."""
        env_file = os.path.join(self.test_dir, '.env')

        # Create file with various malformed content
        with open(env_file, 'wb') as f:
            f.write(b'\xff\xfe\x00\x00invalid_content')  # Invalid UTF-8

        manager = EnvManager(auto_load=False)
        result = manager.load(env_file)

        # Should handle the error and return False
        self.assertFalse(result)

    @patch('pyrox.services.env.open', side_effect=IOError("File read error"))
    def test_file_io_error(self, mock_open):
        """Test handling of file I/O errors."""
        manager = EnvManager(auto_load=False)
        result = manager.load('/some/path/.env')

        self.assertFalse(result)
        self.assertFalse(manager.is_loaded())

    def test_unicode_decode_error_handling(self):
        """Test handling of files with encoding issues."""
        env_file = os.path.join(self.test_dir, '.env')

        # Create file with invalid UTF-8 bytes
        with open(env_file, 'wb') as f:
            f.write(b'VALID_KEY=valid_value\n')
            f.write(b'INVALID_KEY=\xff\xfe\x00\x00invalid_utf8\n')
            f.write(b'ANOTHER_KEY=another_value\n')

        manager = EnvManager(auto_load=False)

        # Should detect that file is not readable due to encoding issues
        self.assertFalse(manager._is_file_readable(env_file))

        # Loading should fail
        result = manager.load(env_file)
        self.assertFalse(result)
        self.assertFalse(manager.is_loaded())


if __name__ == '__main__':
    unittest.main()

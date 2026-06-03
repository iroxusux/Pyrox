"""Unit tests for environment configuration services."""

import os
import tempfile
import shutil
from unittest.mock import patch

import pytest

from pyrox.services.env import (
    EnvManager,
    load_env,
    get_env,
    set_env,
    get_debug_mode,
    get_log_level,
    get_data_dir,
)


# ── Shared fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_env_manager():
    """Reset EnvManager static state and os.environ around every test."""
    original_env = dict(os.environ)
    for var in [
        'PYROX_DEBUG', 'PYROX_LOG_LEVEL', 'DATABASE_URL', 'TEST_VAR',
        'QUOTED_VAR', 'BOOL_VAR', 'INT_VAR', 'FLOAT_VAR', 'LIST_VAR',
    ]:
        os.environ.pop(var, None)
    EnvManager.reset()

    yield

    os.environ.clear()
    os.environ.update(original_env)
    EnvManager.reset()


@pytest.fixture()
def test_dir():
    """Provide a temporary directory, cleaned up after the test."""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture()
def test_env_file(test_dir):  # pylint: disable=redefined-outer-name
    """Provide the path for a `.env` file inside the temp directory."""
    return os.path.join(test_dir, '.env')


@pytest.fixture()
def make_env_file(test_env_file):  # pylint: disable=redefined-outer-name
    """Factory fixture: write content to the temp .env file and return its path."""
    def _make(content: str) -> str:
        with open(test_env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return test_env_file
    return _make


# ── TestEnvManager ─────────────────────────────────────────────────────────────

class TestEnvManager:
    """Test cases for EnvManager class."""

    def test_prevent_instantiation(self):
        with pytest.raises(TypeError, match="static class"):
            EnvManager()

    def test_static_class_state(self):
        assert not EnvManager.is_loaded()
        assert EnvManager.count() == 0

    def test_load_with_specific_env_file(self, make_env_file):  # pylint: disable=redefined-outer-name
        env_file = make_env_file("TEST_VAR=test_value\n")
        assert EnvManager.load(env_file)
        assert EnvManager.is_loaded()
        assert EnvManager.get('TEST_VAR') == 'test_value'

    def test_load_existing_file(self, make_env_file):  # pylint: disable=redefined-outer-name
        env_file = make_env_file("""
# Test configuration
TEST_VAR=test_value
ANOTHER_VAR=another_value
""")
        assert EnvManager.load(env_file)
        assert EnvManager.is_loaded()
        assert EnvManager.get('TEST_VAR') == 'test_value'
        assert EnvManager.get('ANOTHER_VAR') == 'another_value'

    def test_load_nonexistent_file(self):
        EnvManager.load('/nonexistent/.env')
        assert not EnvManager.is_loaded()

    def test_find_env_file_not_found(self):
        env_file_path = os.path.join(os.getcwd(), '.env')
        temp_backup = None
        try:
            if os.path.exists(env_file_path):
                temp_backup = env_file_path + '.test_backup'
                os.rename(env_file_path, temp_backup)
            assert EnvManager._find_env_file() is None
        finally:
            if temp_backup and os.path.exists(temp_backup):
                os.rename(temp_backup, env_file_path)

    def test_parse_simple_key_value(self, make_env_file):
        env_file = make_env_file("""
KEY1=value1
KEY2=value2
KEY_WITH_UNDERSCORE=value_with_underscore
""")
        EnvManager.load(env_file)
        assert EnvManager.get('KEY1') == 'value1'
        assert EnvManager.get('KEY2') == 'value2'
        assert EnvManager.get('KEY_WITH_UNDERSCORE') == 'value_with_underscore'

    def test_parse_quoted_values(self, make_env_file):
        env_file = make_env_file('''
DOUBLE_QUOTED="double quoted value"
SINGLE_QUOTED='single quoted value'
QUOTED_WITH_SPACES="value with spaces"
QUOTED_EMPTY=""
''')
        EnvManager.load(env_file)
        assert EnvManager.get('DOUBLE_QUOTED') == 'double quoted value'
        assert EnvManager.get('SINGLE_QUOTED') == 'single quoted value'
        assert EnvManager.get('QUOTED_WITH_SPACES') == 'value with spaces'
        assert EnvManager.get('QUOTED_EMPTY') == ''

    def test_parse_escape_sequences(self, make_env_file):
        env_file = make_env_file(r'''
NEWLINE="line1\nline2"
TAB="tab\ttab"
QUOTE="quote\"quote"
BACKSLASH="back\\slash"
''')
        EnvManager.load(env_file)
        assert EnvManager.get('NEWLINE') == 'line1\nline2'
        assert EnvManager.get('TAB') == 'tab\ttab'
        assert EnvManager.get('QUOTE') == 'quote"quote'
        assert EnvManager.get('BACKSLASH') == 'back\\slash'

    def test_skip_comments_and_empty_lines(self, make_env_file):
        env_file = make_env_file("""
# This is a comment
VALID_VAR=valid_value

# Another comment
   # Indented comment

ANOTHER_VAR=another_value
""")
        EnvManager.load(env_file)
        assert EnvManager.get('VALID_VAR') == 'valid_value'
        assert EnvManager.get('ANOTHER_VAR') == 'another_value'

    def test_invalid_lines(self, make_env_file):
        env_file = make_env_file("""
VALID_VAR=valid_value
INVALID_LINE_NO_EQUALS
=NO_KEY_VALUE
ANOTHER_VALID=another_value
""")
        EnvManager.load(env_file)
        assert EnvManager.get('VALID_VAR') == 'valid_value'
        assert EnvManager.get('ANOTHER_VALID') == 'another_value'
        assert EnvManager.get('INVALID_LINE_NO_EQUALS') is None

    def test_variable_substitution_braced(self, make_env_file):
        env_file = make_env_file("""
BASE_DIR=/app
DATA_DIR=${BASE_DIR}/data
LOG_DIR=${BASE_DIR}/logs
""")
        EnvManager.load(env_file)
        assert EnvManager.get('BASE_DIR') == '/app'
        assert EnvManager.get('DATA_DIR') == '/app/data'
        assert EnvManager.get('LOG_DIR') == '/app/logs'

    def test_variable_substitution_simple(self, make_env_file):
        env_file = make_env_file("""
HOME=/home/user
PATH=$HOME/bin
""")
        EnvManager.load(env_file)
        assert EnvManager.get('HOME') == '/home/user'
        assert EnvManager.get('PATH') == '/home/user/bin'

    def test_variable_substitution_from_os_environ(self, make_env_file):
        os.environ['EXISTING_VAR'] = 'existing_value'
        env_file = make_env_file("NEW_VAR=${EXISTING_VAR}/suffix\n")
        EnvManager.load(env_file)
        assert EnvManager.get('NEW_VAR') == 'existing_value/suffix'

    def test_get_with_type_casting_bool(self, make_env_file):
        env_file = make_env_file("""
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
""")
        EnvManager.load(env_file)
        assert EnvManager.get('TRUE_VAR', cast_type=bool)
        assert not EnvManager.get('FALSE_VAR', cast_type=bool)
        assert EnvManager.get('ONE_VAR', cast_type=bool)
        assert not EnvManager.get('ZERO_VAR', cast_type=bool)
        assert EnvManager.get('YES_VAR', cast_type=bool)
        assert not EnvManager.get('NO_VAR', cast_type=bool)
        assert EnvManager.get('ON_VAR', cast_type=bool)
        assert not EnvManager.get('OFF_VAR', cast_type=bool)
        assert EnvManager.get('ENABLED_VAR', cast_type=bool)
        assert not EnvManager.get('DISABLED_VAR', cast_type=bool)

    def test_get_with_type_casting_int(self, make_env_file):
        env_file = make_env_file("""
INT_VAR=123
NEGATIVE_INT=-456
""")
        EnvManager.load(env_file)
        assert EnvManager.get('INT_VAR', cast_type=int) == 123
        assert EnvManager.get('NEGATIVE_INT', cast_type=int) == -456

    def test_get_with_type_casting_float(self, make_env_file):
        env_file = make_env_file("""
FLOAT_VAR=123.45
NEGATIVE_FLOAT=-67.89
""")
        EnvManager.load(env_file)
        assert EnvManager.get('FLOAT_VAR', cast_type=float) == 123.45
        assert EnvManager.get('NEGATIVE_FLOAT', cast_type=float) == -67.89

    def test_get_with_type_casting_list(self, make_env_file):
        env_file = make_env_file("""
LIST_VAR=item1,item2,item3
LIST_WITH_SPACES=item1, item2 , item3
EMPTY_LIST=
SINGLE_ITEM=single
""")
        EnvManager.load(env_file)
        assert EnvManager.get('LIST_VAR', cast_type=list) == ['item1', 'item2', 'item3']
        assert EnvManager.get('LIST_WITH_SPACES', cast_type=list) == ['item1', 'item2', 'item3']
        assert EnvManager.get('EMPTY_LIST', cast_type=list) == []
        assert EnvManager.get('SINGLE_ITEM', cast_type=list) == ['single']

    def test_get_with_type_casting_tuple(self, make_env_file):
        env_file = make_env_file("""
TUPLE_VAR=item1,item2,item3
TUPLE_WITH_SPACES=item1, item2 , item3
TUPLE_WITH_PARENS=(item1,item2,item3)
""")
        EnvManager.load(env_file)
        assert EnvManager.get('TUPLE_VAR', cast_type=tuple) == ('item1', 'item2', 'item3')
        assert EnvManager.get('TUPLE_WITH_SPACES', cast_type=tuple) == ('item1', 'item2', 'item3')
        assert EnvManager.get('TUPLE_WITH_PARENS', cast_type=tuple) == ('item1', 'item2', 'item3')

    def test_get_with_invalid_type_casting(self, make_env_file):
        env_file = make_env_file("""
INVALID_INT=not_a_number
INVALID_FLOAT=not_a_float
""")
        EnvManager.load(env_file)
        assert EnvManager.get('INVALID_INT', default=999, cast_type=int) == 999
        assert EnvManager.get('INVALID_FLOAT', default=99.9, cast_type=float) == 99.9

    def test_get_default_values(self):
        assert EnvManager.get('NONEXISTENT', 'default') == 'default'
        assert EnvManager.get('NONEXISTENT', 123, int) == 123
        assert EnvManager.get('NONEXISTENT', True, bool) is True
        assert EnvManager.get('NONEXISTENT') is None

    def test_get_from_os_environ(self):
        os.environ['OS_VAR'] = 'os_value'
        assert EnvManager.get('OS_VAR') == 'os_value'

    def test_get_priority_env_file_over_os_environ(self, make_env_file):
        os.environ['PRIORITY_VAR'] = 'os_value'
        env_file = make_env_file("PRIORITY_VAR=env_file_value\n")
        EnvManager.load(env_file)
        assert EnvManager.get('PRIORITY_VAR') == 'env_file_value'

    def test_set_variable(self, make_env_file):
        test_env = make_env_file('')
        EnvManager.set('NEW_VAR', 'new_value', env_file=test_env)
        assert EnvManager.get('NEW_VAR') == 'new_value'
        assert os.environ.get('NEW_VAR') == 'new_value'

    def test_get_all_variables(self, make_env_file):
        env_file = make_env_file("""
ENV_VAR1=value1
ENV_VAR2=value2
""")
        os.environ['OS_VAR'] = 'os_value'
        EnvManager.load(env_file)
        all_vars = EnvManager.get_all()
        assert 'ENV_VAR1' in all_vars
        assert 'ENV_VAR2' in all_vars
        assert 'OS_VAR' in all_vars
        assert all_vars['ENV_VAR1'] == 'value1'
        assert all_vars['OS_VAR'] == 'os_value'

    def test_get_all_with_prefix(self, make_env_file):
        env_file = make_env_file("""
PYROX_VAR1=value1
PYROX_VAR2=value2
OTHER_VAR=other_value
""")
        EnvManager.load(env_file)
        pyrox_vars = EnvManager.get_all(prefix='PYROX_')
        assert 'PYROX_VAR1' in pyrox_vars
        assert 'PYROX_VAR2' in pyrox_vars
        assert 'OTHER_VAR' not in pyrox_vars

    def test_create_env_template(self, test_dir):
        template_path = os.path.join(test_dir, '.env.template')
        EnvManager.create_env_template(template_path)
        assert os.path.exists(template_path)
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'PYROX_DEBUG=' in content
        assert 'DATABASE_URL=' in content
        assert 'EPLAN_DEFAULT_PROJECT_DIR=' in content

    def test_reload(self, make_env_file):
        env_file = make_env_file("TEST_VAR=value1\n")
        EnvManager.load(env_file)
        assert EnvManager.get('TEST_VAR') == 'value1'
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("TEST_VAR=value2\nNEW_VAR=new_value\n")
        assert EnvManager.reload()
        assert EnvManager.get('TEST_VAR') == 'value2'
        assert EnvManager.get('NEW_VAR') == 'new_value'

    def test_file_encoding_utf8(self, test_env_file):
        with open(test_env_file, 'w', encoding='utf-8') as f:
            f.write('UNICODE_VAR=café\n')
        EnvManager.load(test_env_file)
        assert EnvManager.get('UNICODE_VAR') == 'café'


# ── TestGlobalFunctions ───────────────────────────────────────────────────────────

class TestGlobalFunctions:
    """Test cases for global convenience functions."""

    def test_static_class_behavior(self, test_dir):
        test_env = os.path.join(test_dir, '.env')
        EnvManager.set('TEST_STATIC', 'static_value', env_file=test_env)
        assert EnvManager.get('TEST_STATIC') == 'static_value'
        assert EnvManager.get('TEST_STATIC') == EnvManager.get('TEST_STATIC')

    def test_load_env(self, test_dir):
        env_file = os.path.join(test_dir, '.env')
        with open(env_file, 'w') as f:
            f.write('TEST_VAR=test_value\n')
        assert load_env(env_file)
        assert get_env('TEST_VAR') == 'test_value'

    def test_get_env_function(self):
        os.environ['TEST_VAR'] = 'test_value'
        assert get_env('TEST_VAR') == 'test_value'
        assert get_env('NONEXISTENT', 'default') == 'default'
        assert get_env('TEST_VAR', cast_type=str) == 'test_value'

    def test_set_env_function(self):
        with patch('pyrox.services.env.EnvManager.set') as mock_set:
            set_env('NEW_VAR', 'new_value')
            mock_set.assert_called_once_with('NEW_VAR', 'new_value')
        os.environ['NEW_VAR'] = 'new_value'
        assert get_env('NEW_VAR') == 'new_value'
        assert os.environ.get('NEW_VAR') == 'new_value'

    def test_convenience_functions(self):
        os.environ['APP_DEBUG_MODE'] = 'true'
        assert get_debug_mode()
        os.environ['APP_DEBUG_MODE'] = 'false'
        assert not get_debug_mode()
        os.environ['LOG_LEVEL'] = 'DEBUG'
        assert get_log_level() == 'DEBUG'
        os.environ['DIR_DATA'] = './custom/data'
        assert get_data_dir() == './custom/data'

    def test_convenience_functions_defaults(self):
        for key in ['PYROX_DEBUG', 'PYROX_LOG_LEVEL', 'PYROX_DATA_DIR', 'DATABASE_URL']:
            os.environ.pop(key, None)
            EnvManager._env_vars.pop(key, None)
        assert not EnvManager.get('NOT_A_KEY', False, bool)
        assert EnvManager.get('NOT_A_LOG_LEVEL', 'INFO', str) == 'INFO'
        assert EnvManager.get('NOT_A_DATA_DIR', './data', str) == './data'
        assert EnvManager.get('NOT_A_DATABASE', 'sqlite:///pyrox.db', str) == 'sqlite:///pyrox.db'

    def test_getitem(self):
        os.environ['TEST_VAR'] = 'test_value'
        assert EnvManager.__getitem__('TEST_VAR') == 'test_value'

    def test_setitem(self):
        with patch('pyrox.services.env.EnvManager.set') as mock_set:
            EnvManager.__setitem__('NEW_VAR', 'new_value')
            mock_set.assert_called_once_with('NEW_VAR', 'new_value')
        os.environ['NEW_VAR'] = 'new_value'
        assert EnvManager.get('NEW_VAR') == 'new_value'
        assert os.environ.get('NEW_VAR') == 'new_value'


# ── TestErrorHandling ───────────────────────────────────────────────────────────

class TestErrorHandling:
    """Test cases for error handling scenarios."""

    def test_malformed_file_handling(self, test_dir):
        env_file = os.path.join(test_dir, '.env')
        with open(env_file, 'wb') as f:
            f.write(b'\xff\xfe\x00\x00invalid_content')
        EnvManager.load(env_file)
        assert not EnvManager.is_loaded()

    @patch('pyrox.services.env.open', side_effect=IOError("File read error"))
    def test_file_io_error(self, mock_open):
        EnvManager.load('/some/path/.env')
        assert not EnvManager.is_loaded()

    def test_unicode_decode_error_handling(self, test_dir):
        env_file = os.path.join(test_dir, '.env')
        with open(env_file, 'wb') as f:
            f.write(b'VALID_KEY=valid_value\n')
            f.write(b'INVALID_KEY=\xff\xfe\x00\x00invalid_utf8\n')
            f.write(b'ANOTHER_KEY=another_value\n')
        EnvManager.load(env_file)
        assert not EnvManager.is_loaded()

"""Environment configuration services for Pyrox.

This module provides functionality to load and manage environment variables
from .env files and system environment.
"""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Union

from dotenv import load_dotenv, set_key


class EnvManager:
    """Static manager for environment variables and .env files."""

    # Class-level storage for environment variables
    _env_vars: Dict[str, str] = {}
    _env_file: Optional[str] = None
    _loaded: bool = False

    def __init__(self):
        """Prevent instantiation of static class."""
        raise TypeError("EnvManager is a static class and cannot be instantiated")

    @classmethod
    def __getitem__(cls, key: str) -> Any:
        return cls.get(key)

    @classmethod
    def __setitem__(cls, key: str, value: Any) -> None:
        cls.set(key, value)

    @classmethod
    def load(
        cls,
        env_file: Optional[Union[Path, str]] = None
    ) -> bool:
        """Load environment variables from .env file.

        Args:
            env_file: Path to .env file. If None, uses class default or searches

        Returns:
            True if file was loaded successfully
        """
        if isinstance(env_file, Path):
            env_file = str(env_file)

        if env_file:
            cls._env_file = env_file

        if not cls._env_file:
            cls._env_file = cls._find_env_file()

        if not cls._env_file:
            print(".env file not found.")
            return False

        print(f"Loading .env file from: {cls._env_file}")

        if not cls._is_file_readable(cls._env_file):
            print(f".env file '{cls._env_file}' is not readable.")
            return False

        try:
            cls._load_from_file(cls._env_file)
            cls._loaded = True
            print(f".env file '{cls._env_file}' loaded successfully.")
            return True

        except Exception as e:
            print(f"Error loading .env file '{cls._env_file}': {e}")
            return False

    @classmethod
    def _is_file_readable(cls, file_path: str) -> bool:
        """Check if file exists and is readable.

        Args:
            file_path: Path to the file to check

        Returns:
            True if file exists and is readable, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False

            # Check if it's actually a file (not a directory)
            if not os.path.isfile(file_path):
                return False

            # Check read permissions using os.access
            if not os.access(file_path, os.R_OK):
                return False

            # Try to actually open and read a small portion to verify readability
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read(1)  # Try to read just one character
                return True
            except (IOError, OSError, PermissionError, UnicodeDecodeError):
                return False

        except Exception:
            return False

    @classmethod
    def _find_env_file(cls) -> Optional[str]:
        """Search for .env file in common locations."""
        search_paths = [
            os.getcwd(),  # Current working directory
            Path(__file__).parent.parent.parent,  # Project root (3 levels up from services)
            os.path.expanduser("~"),  # Home directory
        ]

        for search_path in search_paths:
            env_path = os.path.join(search_path, '.env')
            if cls._is_file_readable(env_path):
                return env_path

        return None

    @classmethod
    def _load_from_file(cls, file_path: str) -> None:
        """Load variables from .env file."""

        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Parse key=value pairs
                if '=' not in line:
                    continue

                key, value = cls._parse_line(line, line_num, file_path)
                if key:
                    cls._env_vars[key] = value
                    # Also set in os.environ if not already set
                    if key not in os.environ:
                        os.environ[key] = value

    @classmethod
    def _parse_line(
        cls,
        line: str,
        line_num: int,
        file_path: str
    ) -> tuple[str, str]:
        """Parse a single line from .env file."""
        try:
            # Handle different quote styles and escaping
            match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$', line)
            if not match:
                return "", ""

            key, value = match.groups()

            # Handle quoted values
            value = cls._process_value(value)

            return key, value

        except Exception:
            return "", ""

    @classmethod
    def _process_value(cls, value: str) -> str:
        """Process and clean up the value from .env file."""
        value = value.strip()

        # Handle quoted strings
        if len(value) >= 2:
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]

        # Handle escape sequences
        value = value.replace('\\n', '\n')
        value = value.replace('\\t', '\t')
        value = value.replace('\\r', '\r')
        value = value.replace('\\"', '"')
        value = value.replace("\\'", "'")
        value = value.replace('\\\\', '\\')

        # Handle variable substitution ${VAR} or $VAR
        value = cls._substitute_variables(value)

        return value

    @classmethod
    def _substitute_variables(cls, value: str) -> str:
        """Substitute environment variables in the value."""
        # Handle ${VAR} format
        def replace_braced(match):
            var_name = match.group(1)
            return cls.get(var_name, os.environ.get(var_name, match.group(0)))

        value = re.sub(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}', replace_braced, value)

        # Handle $VAR format
        def replace_simple(match):
            var_name = match.group(1)
            return cls.get(var_name, os.environ.get(var_name, match.group(0)))

        value = re.sub(r'\$([A-Za-z_][A-Za-z0-9_]*)', replace_simple, value)

        return value

    @classmethod
    def get(
        cls,
        key: str,
        default=None,
        cast_type: type = str
    ) -> Any:
        """Get environment variable with optional type casting."""
        load_dotenv(cls._env_file)  # Load from .env file
        if key in cls._env_vars:
            value = cls._env_vars[key]
        else:
            value = os.environ.get(key, None)

        if value is None:
            return default

        if cast_type == str:
            return value

        if cast_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on', 'enabled')

        if cast_type == list:
            return [item.strip() for item in value.split(',') if item.strip()]

        if cast_type == tuple:
            value = value.replace('(', '').replace(')', '')  # Remove parentheses if present from tuple-like strings
            return tuple(item.strip() for item in value.split(',') if item.strip())

        try:
            return cast_type(value)
        except (ValueError, TypeError):
            return default

    @classmethod
    def set(cls, key: str, value: str, env_file: str = '.env') -> None:
        """Set environment variable both in memory and in .env file."""
        # Update in-memory environment
        os.environ[key] = value

        # Update .env file using python-dotenv
        set_key(env_file, key, value)

    @classmethod
    def get_all(cls, prefix: Optional[str] = None) -> Dict[str, str]:
        """Get all environment variables, optionally filtered by prefix.

        Args:
            prefix: Optional prefix to filter variables

        Returns:
            Dictionary of environment variables
        """
        all_vars = {**cls._env_vars, **dict(os.environ)}

        if prefix:
            return {k: v for k, v in all_vars.items() if k.startswith(prefix)}

        return all_vars

    @classmethod
    def create_env_template(cls, file_path: str = '.env.template') -> None:
        """Create a template .env file with common Pyrox variables.

        Args:
            file_path: Path where to create the template file
        """
        template_content = '''# Pyrox Environment Configuration
# Copy this file to .env and customize the values

# Application Configuration
PYROX_DEBUG=false
PYROX_LOG_LEVEL=INFO
PYROX_LOG_FILE=pyrox.log

# Database Configuration
DATABASE_URL=sqlite:///pyrox.db
DATABASE_DEBUG=false

# File Paths
PYROX_DATA_DIR=./data
PYROX_TEMP_DIR=./temp
PYROX_BACKUP_DIR=./backups

# EPLAN Configuration
EPLAN_DEFAULT_PROJECT_DIR=./projects
EPLAN_IMPORT_TIMEOUT=300
EPLAN_SUPPORTED_FORMATS=.elk,.eox,.eod

# PLC Configuration
PLC_DEFAULT_CONTROLLER_TYPE=CompactLogix
PLC_COMMUNICATION_TIMEOUT=5000
PLC_RETRY_ATTEMPTS=3

# UI Configuration
UI_THEME=default
UI_WINDOW_SIZE=1200x800
UI_AUTO_SAVE=true

# Security (if applicable)
SECRET_KEY=your-secret-key-here
ENCRYPTION_ALGORITHM=AES256

# External Services
# API_BASE_URL=https://api.example.com
# API_KEY=your-api-key
# API_TIMEOUT=30
'''

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
        except (IOError, OSError, PermissionError):
            raise

    @classmethod
    def is_loaded(cls) -> bool:
        """Check if .env file has been loaded."""
        return cls._loaded

    @classmethod
    def reload(cls) -> bool:
        """Reload the .env file."""
        cls._env_vars.clear()
        cls._loaded = False
        return cls.load()


EnvManager.load()


def load_env(env_file: Optional[str] = None) -> bool:
    """Load environment variables from .env file.

    Args:
        env_file: Path to .env file

    Returns:
        True if loaded successfully
    """
    return EnvManager.load(env_file)


def get_env(
    key: str,
    default: Any = None,
    cast_type: type = str
) -> Any:
    """Get environment variable value.

    Args:
        key: Environment variable name
        default: Default value if not found
        cast_type: Type to cast the value to

    Returns:
        Environment variable value
    """
    return EnvManager.get(key, default, cast_type)


def set_env(key: str, value: str) -> None:
    """Set environment variable.

    Args:
        key: Environment variable name
        value: Environment variable value
    """
    EnvManager.set(key, value)


def get_debug_mode() -> bool:
    """Get debug mode setting."""
    return EnvManager.get('DEBUG_MODE', False, bool)


def get_log_level() -> str:
    """Get log level setting."""
    return EnvManager.get('LOG_LEVEL', 'INFO', str)


def get_data_dir() -> str:
    """Get data directory path."""
    return EnvManager.get('DATA_DIR', './data', str)


def get_database_url() -> str:
    """Get database URL."""
    return EnvManager.get('DATABASE_URL', 'sqlite:///pyrox.db', str)


def get_default_date_format() -> str:
    """Get default log date format string."""
    date_format = EnvManager.get('LOG_DATE_FORMAT', '%Y-%m-%d %H:%M:%S', str)
    if not isinstance(date_format, str) or not date_format.strip():
        raise ValueError("Invalid log date format string from .env file!")
    return date_format


def get_default_formatter() -> str:
    """Get default log formatter string."""
    formatter = EnvManager.get('LOG_FORMAT', '%(asctime)s | %(name)s | %(levelname)s | %(message)s', str)
    if not isinstance(formatter, str) or not formatter.strip():
        raise ValueError("Invalid log formatter string from .env file!")
    return formatter

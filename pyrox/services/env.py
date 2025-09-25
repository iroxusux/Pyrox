"""Environment configuration services for Pyrox.

This module provides functionality to load and manage environment variables
from .env files and system environment.
"""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

from pyrox.models.abc.logging import Loggable


class EnvManager(Loggable):
    """Manager for environment variables and .env files."""

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __init__(
        self,
        env_file: Optional[str] = None,
        auto_load: bool = True
    ) -> None:
        """Initialize the environment manager.

        Args:
            env_file: Path to .env file. If None, searches for .env in common locations
            auto_load: Whether to automatically load the .env file on initialization
        """
        super().__init__()
        self._env_vars: Dict[str, str] = {}
        self._env_file = env_file
        self._loaded = False

        if auto_load:
            self.load()

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def load(
        self,
        env_file: Optional[str] = None
    ) -> bool:
        """Load environment variables from .env file.

        Args:
            env_file: Path to .env file. If None, uses instance default or searches

        Returns:
            True if file was loaded successfully
        """
        if env_file:
            self._env_file = env_file

        # Find .env file if not specified
        if not self._env_file:
            self._env_file = self._find_env_file()

        if not self._env_file:
            self.logger.warning("No .env file found")
            return False

        # Check if file exists and is readable
        if not self._is_file_readable(self._env_file):
            self.logger.warning(f"File is not readable: {self._env_file}")
            return False

        try:
            self._load_from_file(self._env_file)
            self.logger.info(f"Loaded environment variables from: {self._env_file}")
            self._loaded = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to load .env file {self._env_file}: {e}")
            return False

    def _is_file_readable(self, file_path: str) -> bool:
        """Check if file exists and is readable.

        Args:
            file_path: Path to the file to check

        Returns:
            True if file exists and is readable, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                self.logger.debug(f"File does not exist: {file_path}")
                return False

            # Check if it's actually a file (not a directory)
            if not os.path.isfile(file_path):
                self.logger.debug(f"Path is not a file: {file_path}")
                return False

            # Check read permissions using os.access
            if not os.access(file_path, os.R_OK):
                self.logger.debug(f"File is not readable (permissions): {file_path}")
                return False

            # Try to actually open and read a small portion to verify readability
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read(1)  # Try to read just one character
                return True
            except (IOError, OSError, PermissionError, UnicodeDecodeError) as e:
                self.logger.debug(f"File cannot be read: {file_path}, error: {e}")
                return False

        except Exception as e:
            self.logger.debug(f"Error checking file readability for {file_path}: {e}")
            return False

    def _find_env_file(self) -> Optional[str]:
        """Search for .env file in common locations."""
        search_paths = [
            os.getcwd(),  # Current working directory
            Path(__file__).parent.parent.parent,  # Project root (3 levels up from services)
            os.path.expanduser("~"),  # Home directory
        ]

        for search_path in search_paths:
            env_path = os.path.join(search_path, '.env')
            if self._is_file_readable(env_path):
                self.logger.debug(f"Found readable .env file at: {env_path}")
                return env_path

        return None

    def _load_from_file(self, file_path: str) -> None:
        """Load variables from .env file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue

                    # Parse key=value pairs
                    if '=' not in line:
                        self.logger.warning(f"Invalid line {line_num} in {file_path}: {line}")
                        continue

                    key, value = self._parse_line(line, line_num, file_path)
                    if key:
                        self._env_vars[key] = value
                        # Also set in os.environ if not already set
                        if key not in os.environ:
                            os.environ[key] = value
        except (IOError, OSError, PermissionError) as e:
            self.logger.error(f"IO error reading file {file_path}: {e}")
            raise
        except UnicodeDecodeError as e:
            self.logger.error(f"Encoding error reading file {file_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error reading file {file_path}: {e}")
            raise

    def _parse_line(
        self,
        line: str,
        line_num: int,
        file_path: str
    ) -> tuple[str, str]:
        """Parse a single line from .env file."""
        try:
            # Handle different quote styles and escaping
            match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$', line)
            if not match:
                self.logger.warning(f"Invalid format at line {line_num} in {file_path}")
                return "", ""

            key, value = match.groups()

            # Handle quoted values
            value = self._process_value(value)

            return key, value

        except Exception as e:
            self.logger.error(f"Error parsing line {line_num} in {file_path}: {e}")
            return "", ""

    def _process_value(self, value: str) -> str:
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
        value = self._substitute_variables(value)

        return value

    def _substitute_variables(self, value: str) -> str:
        """Substitute environment variables in the value."""
        # Handle ${VAR} format
        def replace_braced(match):
            var_name = match.group(1)
            return self.get(var_name, os.environ.get(var_name, match.group(0)))

        value = re.sub(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}', replace_braced, value)

        # Handle $VAR format
        def replace_simple(match):
            var_name = match.group(1)
            return self.get(var_name, os.environ.get(var_name, match.group(0)))

        value = re.sub(r'\$([A-Za-z_][A-Za-z0-9_]*)', replace_simple, value)

        return value

    def get(self, key: str, default: Any = None, cast_type: type = str) -> Any:
        """Get environment variable value with type casting.

        Args:
            key: Environment variable name
            default: Default value if not found
            cast_type: Type to cast the value to

        Returns:
            Environment variable value cast to specified type
        """
        # Check .env vars first, then os.environ
        value = self._env_vars.get(key, os.environ.get(key))

        if value is None:
            return default

        # Type casting
        try:
            if cast_type == bool:
                return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
            elif cast_type == int:
                return int(value)
            elif cast_type == float:
                return float(value)
            elif cast_type == list:
                # Split by comma and strip whitespace
                return [item.strip() for item in value.split(',') if item.strip()]
            else:
                return cast_type(value)
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Failed to cast {key}={value} to {cast_type.__name__}: {e}")
            return default

    def set(self, key: str, value: str, update_os_environ: bool = True) -> None:
        """Set environment variable.

        Args:
            key: Environment variable name
            value: Environment variable value
            update_os_environ: Whether to also update os.environ
        """
        self._env_vars[key] = str(value)
        if update_os_environ:
            os.environ[key] = str(value)
        self.logger.debug(f"Set environment variable: {key}={value}")

    def get_all(self, prefix: Optional[str] = None) -> Dict[str, str]:
        """Get all environment variables, optionally filtered by prefix.

        Args:
            prefix: Optional prefix to filter variables

        Returns:
            Dictionary of environment variables
        """
        all_vars = {**self._env_vars, **dict(os.environ)}

        if prefix:
            return {k: v for k, v in all_vars.items() if k.startswith(prefix)}

        return all_vars

    def create_env_template(self, file_path: str = '.env.template') -> None:
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
            self.logger.info(f"Created .env template at: {file_path}")
        except (IOError, OSError, PermissionError) as e:
            self.logger.error(f"Failed to create template file {file_path}: {e}")
            raise

    def is_loaded(self) -> bool:
        """Check if .env file has been loaded."""
        return self._loaded

    def reload(self) -> bool:
        """Reload the .env file."""
        self._env_vars.clear()
        self._loaded = False
        return self.load()


# Global instance for easy access
_env_manager: Optional[EnvManager] = None


def get_env_manager() -> EnvManager:
    """Get the global environment manager instance."""
    global _env_manager
    if _env_manager is None:
        _env_manager = EnvManager()
    return _env_manager


def load_env(env_file: Optional[str] = None) -> bool:
    """Load environment variables from .env file.

    Args:
        env_file: Path to .env file

    Returns:
        True if loaded successfully
    """
    return get_env_manager().load(env_file)


def get_env(key: str, default: Any = None, cast_type: type = str) -> Any:
    """Get environment variable value.

    Args:
        key: Environment variable name
        default: Default value if not found
        cast_type: Type to cast the value to

    Returns:
        Environment variable value
    """
    return get_env_manager().get(key, default, cast_type)


def set_env(key: str, value: str) -> None:
    """Set environment variable.

    Args:
        key: Environment variable name
        value: Environment variable value
    """
    get_env_manager().set(key, value)


# Convenience functions for common configurations
def get_debug_mode() -> bool:
    """Get debug mode setting."""
    return get_env('PYROX_DEBUG', False, bool)


def get_log_level() -> str:
    """Get log level setting."""
    return get_env('PYROX_LOG_LEVEL', 'INFO', str)


def get_data_dir() -> str:
    """Get data directory path."""
    return get_env('PYROX_DATA_DIR', './data', str)


def get_database_url() -> str:
    """Get database URL."""
    return get_env('DATABASE_URL', 'sqlite:///pyrox.db', str)

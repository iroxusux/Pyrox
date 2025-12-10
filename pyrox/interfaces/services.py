"""Service interface abstractions for Pyrox framework.

These interfaces define the contracts for core services such as environment
management, logging, theming, and configuration without any implementation
dependencies, enabling clean separation of concerns.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TextIO


class IEnvironmentManager(ABC):
    """Interface for environment variable management.

    Provides functionality for loading, getting, and setting environment
    variables from various sources including .env files and system environment.
    """

    @abstractmethod
    def load(self, env_file: Optional[str] = None) -> bool:
        """Load environment variables from a file.

        Args:
            env_file: Path to environment file. If None, searches for .env.

        Returns:
            bool: True if loaded successfully.
        """
        pass

    @abstractmethod
    def get(self, key: str, default: Any = None, cast_type: type = str) -> Any:
        """Get an environment variable with optional type casting.

        Args:
            key: Environment variable name.
            default: Default value if not found.
            cast_type: Type to cast the value to.

        Returns:
            Any: The environment variable value.
        """
        pass

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        """Set an environment variable.

        Args:
            key: Environment variable name.
            value: Environment variable value.
        """
        pass

    @abstractmethod
    def get_all(self, prefix: Optional[str] = None) -> Dict[str, str]:
        """Get all environment variables, optionally filtered by prefix.

        Args:
            prefix: Optional prefix to filter variables.

        Returns:
            Dict[str, str]: Dictionary of environment variables.
        """
        pass

    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if environment file has been loaded.

        Returns:
            bool: True if loaded, False otherwise.
        """
        pass


class ILogger(ABC):
    """Interface for individual logger instances.

    Provides the standard logging methods that individual loggers should support.
    """

    @abstractmethod
    def debug(self, message: str, *args, **kwargs) -> None:
        """Log a debug message.

        Args:
            message: The message to log.
            *args: Message formatting arguments.
            **kwargs: Additional logging parameters.
        """
        pass

    @abstractmethod
    def info(self, message: str, *args, **kwargs) -> None:
        """Log an info message.

        Args:
            message: The message to log.
            *args: Message formatting arguments.
            **kwargs: Additional logging parameters.
        """
        pass

    @abstractmethod
    def warning(self, message: str, *args, **kwargs) -> None:
        """Log a warning message.

        Args:
            message: The message to log.
            *args: Message formatting arguments.
            **kwargs: Additional logging parameters.
        """
        pass

    @abstractmethod
    def error(self, message: str, *args, **kwargs) -> None:
        """Log an error message.

        Args:
            message: The message to log.
            *args: Message formatting arguments.
            **kwargs: Additional logging parameters.
        """
        pass

    @abstractmethod
    def critical(self, message: str, *args, **kwargs) -> None:
        """Log a critical message.

        Args:
            message: The message to log.
            *args: Message formatting arguments.
            **kwargs: Additional logging parameters.
        """
        pass

    @abstractmethod
    def success(self, message: str, *args, **kwargs) -> None:
        """Log a success message (custom level).

        Args:
            message: The message to log.
            *args: Message formatting arguments.
            **kwargs: Additional logging parameters.
        """
        pass

    @abstractmethod
    def failure(self, message: str, *args, **kwargs) -> None:
        """Log a failure message (custom level).

        Args:
            message: The message to log.
            *args: Message formatting arguments.
            **kwargs: Additional logging parameters.
        """
        pass

    @abstractmethod
    def notice(self, message: str, *args, **kwargs) -> None:
        """Log a notice message (custom level).

        Args:
            message: The message to log.
            *args: Message formatting arguments.
            **kwargs: Additional logging parameters.
        """
        pass


class ILoggingManager(ABC):
    """Interface for logging system management.

    Provides functionality for creating, configuring, and managing loggers
    throughout the application.
    """

    @abstractmethod
    def get_logger(self, name: str) -> ILogger:
        """Get or create a logger by name.

        Args:
            name: Logger name, typically module name.

        Returns:
            ILogger: The logger instance.
        """
        pass

    @abstractmethod
    def set_level(self, level: str) -> None:
        """Set the global logging level.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        """
        pass

    @abstractmethod
    def add_handler(self, handler: Any) -> None:
        """Add a logging handler.

        Args:
            handler: The logging handler to add.
        """
        pass

    @abstractmethod
    def remove_handler(self, handler: Any) -> None:
        """Remove a logging handler.

        Args:
            handler: The logging handler to remove.
        """
        pass

    @abstractmethod
    def add_stream(self, stream: TextIO) -> None:
        """Add a stream for log output.

        Args:
            stream: The stream to add.
        """
        pass

    @abstractmethod
    def capture_stdout(self, capture: bool = True) -> None:
        """Enable or disable stdout capture.

        Args:
            capture: True to capture stdout, False to restore normal output.
        """
        pass

    @abstractmethod
    def capture_stderr(self, capture: bool = True) -> None:
        """Enable or disable stderr capture.

        Args:
            capture: True to capture stderr, False to restore normal output.
        """
        pass


class IThemeManager(ABC):
    """Interface for theme management.

    Provides functionality for managing application themes, styles,
    and visual appearance across different GUI frameworks.
    """

    @abstractmethod
    def load_theme(self, theme_name: str) -> bool:
        """Load a theme by name.

        Args:
            theme_name: Name of the theme to load.

        Returns:
            bool: True if theme was loaded successfully.
        """
        pass

    @abstractmethod
    def get_current_theme(self) -> str:
        """Get the name of the currently active theme.

        Returns:
            str: Current theme name.
        """
        pass

    @abstractmethod
    def get_available_themes(self) -> List[str]:
        """Get list of available theme names.

        Returns:
            List[str]: List of available theme names.
        """
        pass

    @abstractmethod
    def register_theme(self, name: str, theme_data: Dict[str, Any]) -> None:
        """Register a new theme.

        Args:
            name: Theme name.
            theme_data: Theme configuration data.
        """
        pass

    @abstractmethod
    def apply_to_component(self, component: Any, style_name: Optional[str] = None) -> None:
        """Apply theme styling to a GUI component.

        Args:
            component: The GUI component to style.
            style_name: Optional specific style name to apply.
        """
        pass


class IConfigurationManager(ABC):
    """Interface for configuration management.

    Provides functionality for loading, saving, and managing application
    configuration from various sources and formats.
    """

    @abstractmethod
    def load_config(self, config_path: str) -> bool:
        """Load configuration from a file.

        Args:
            config_path: Path to the configuration file.

        Returns:
            bool: True if loaded successfully.
        """
        pass

    @abstractmethod
    def save_config(self, config_path: str) -> bool:
        """Save configuration to a file.

        Args:
            config_path: Path to save the configuration.

        Returns:
            bool: True if saved successfully.
        """
        pass

    @abstractmethod
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (supports dot notation for nested values).
            default: Default value if key not found.

        Returns:
            Any: The configuration value.
        """
        pass

    @abstractmethod
    def set_value(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key (supports dot notation for nested values).
            value: The value to set.
        """
        pass

    @abstractmethod
    def has_key(self, key: str) -> bool:
        """Check if a configuration key exists.

        Args:
            key: The key to check.

        Returns:
            bool: True if key exists, False otherwise.
        """
        pass

    @abstractmethod
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get all values from a configuration section.

        Args:
            section: Section name.

        Returns:
            Dict[str, Any]: Section configuration values.
        """
        pass


__all__ = (
    'IEnvironmentManager',
    'ILogger',
    'ILoggingManager',
    'IThemeManager',
    'IConfigurationManager',
)

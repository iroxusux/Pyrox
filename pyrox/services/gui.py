"""GUI framework management services for Pyrox.

This module provides functionality to manage GUI frameworks and backends
based on environment configuration. It supports multiple GUI frameworks
and provides a unified interface for GUI operations.
"""

from __future__ import annotations
from typing import Any, Dict, Optional, Type, Union
from pyrox.services import EnvManager, log
from pyrox.interfaces import EnvironmentKeys, IGuiBackend, GuiFramework


class GuiManager:
    """Static manager for GUI framework selection and operations."""

    # Class-level storage
    _current_backend: Optional[IGuiBackend] = None
    _framework: GuiFramework
    _backends: Dict[GuiFramework, Type[IGuiBackend]] = {}
    _initialized: bool = False
    _root_window: Any = None

    def __init__(self):
        """Prevent instantiation of static class."""
        raise TypeError("GuiManager is a static class and cannot be instantiated")

    @classmethod
    def _get_framework_name(
        cls,
        framework: Optional[Union[GuiFramework, str]]
    ) -> str:
        value = 'tkinter'  # Default

        if not framework:
            log(cls).debug("Setting GUI framework from environment variable.")
            return EnvManager.get(
                EnvironmentKeys.ui.UI_FRAMEWORK,
                default='tkinter'
            )

        if isinstance(framework, str):
            try:
                value = GuiFramework(framework.lower()).value
            except ValueError:
                log(cls).warning(f"Invalid GUI framework specified: {framework}. Using 'tkinter'.")
        else:
            value = framework.value

        return value

    @classmethod
    def _set_backend(cls) -> None:
        """Set the current GUI backend based on the selected framework."""
        backend_class = cls._backends.get(cls._framework)
        if not backend_class:
            raise KeyError(f"No backend registered for framework: {cls._framework.value}")

        cls._current_backend = backend_class()
        if not cls._current_backend.is_available():
            raise RuntimeError(f"Backend for framework {cls._framework.value} is not available.")
        cls._initialized = cls._current_backend.initialize()

    @classmethod
    def _set_framework(
        cls,
        framework_name: str
    ) -> None:
        """Set the current GUI framework.

        Args:
            framework_name: The name of the GUI framework to set.
        """
        try:
            cls._framework = GuiFramework(framework_name.lower())
        except ValueError:
            log(cls).error(f"Invalid GUI framework specified: {framework_name}.")
            cls._framework = GuiFramework.TKINTER

    @classmethod
    def get_available_frameworks(cls) -> list[GuiFramework]:
        """Get list of available GUI frameworks on this system."""
        available = []
        for framework, backend_class in cls._backends.items():
            backend = backend_class()
            if backend.is_available():
                available.append(framework)
        return available

    @classmethod
    def get_backend(cls) -> Optional[IGuiBackend]:
        """Get the current GUI backend."""
        if not cls._initialized:
            cls.initialize()
        return cls._current_backend

    @classmethod
    def get_framework(cls) -> GuiFramework:
        """Get the current GUI framework."""
        if not cls._initialized:
            cls.initialize()
        return cls._framework

    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        """Get information about the current GUI configuration."""
        if not cls._initialized:
            cls.initialize()

        return {
            'framework': cls._framework.value if cls._framework else None,
            'backend_name': cls._current_backend.framework_name if cls._current_backend else None,
            'initialized': cls._initialized,
            'gui_available': cls.is_gui_available(),
            'has_root_window': cls._root_window is not None,
            'available_frameworks': [f.value for f in cls.get_available_frameworks()],
        }

    @classmethod
    def initialize(
        cls,
        framework: Optional[Union[GuiFramework, str]] = None
    ) -> bool:
        """Initialize the GUI manager with specified or environment framework.

        Args:
            framework: GUI framework to use. If None, reads from environment.

        Returns:
            True if initialization was successful.
        """
        if cls._initialized:
            return True

        log(cls).debug("Initializing GUI Manager...")
        cls._set_framework(cls._get_framework_name(framework))
        cls._set_backend()

        return cls._initialized

    @classmethod
    def is_gui_available(cls) -> bool:
        """Check if GUI is available (not console mode)."""
        if not cls._initialized:
            cls.initialize()
        return cls._framework != GuiFramework.CONSOLE

    @classmethod
    def quit_application(cls) -> None:
        """Quit the GUI application."""
        if cls._current_backend:
            cls._current_backend.quit_application()

    @classmethod
    def register_backend(cls, framework: GuiFramework, backend_class: Type[IGuiBackend]) -> None:
        """Register a custom GUI backend.

        Args:
            framework: The framework enum value.
            backend_class: The backend class to register.
        """
        cls._backends[framework] = backend_class

    @classmethod
    def run_main_loop(cls, root_window: Any = None) -> None:
        """Run the GUI main loop."""
        if not cls._initialized:
            cls.initialize()

        if cls._current_backend:
            window = root_window or cls._root_window
            cls._current_backend.run_main_loop(window)

    @classmethod
    def unsafe_get_backend(cls) -> IGuiBackend:
        """Get the current GUI backend, initializing if necessary.
        Will raise an exception, haulting execution, if unable to initialize the backend.
        """
        if not cls._initialized:
            cls.initialize()
        if not cls._current_backend:
            raise RuntimeError("No GUI backend available!")
        return cls._current_backend

    @classmethod
    def switch_framework(cls, framework: Union[GuiFramework, str]) -> bool:
        """Switch to a different GUI framework.

        Args:
            framework: The framework to switch to.

        Returns:
            True if switch was successful.
        """
        if isinstance(framework, str):
            try:
                framework = GuiFramework(framework.lower())
            except ValueError:
                return False

        # Reset state
        cls._initialized = False
        cls._current_backend = None
        cls._root_window = None

        # Initialize with new framework
        return cls.initialize(framework)


# Convenience functions for common operations
def initialize_gui(
    framework: Optional[Union[GuiFramework, str]] = None
) -> bool:
    """Initialize the GUI system.

    Args:
        framework: Optional framework to use. Defaults to environment variable.

    Returns:
        True if initialization successful.
    """
    return GuiManager.initialize(framework)


def register_backend(
    framework: GuiFramework,
    backend_class: Type[IGuiBackend]
) -> None:
    """Register a custom GUI backend.

    Args:
        framework: The framework enum value.
        backend_class: The backend class to register.
    """
    GuiManager.register_backend(framework, backend_class)


def run_gui(window: Any = None) -> None:
    """Run the GUI main loop.

    Args:
        window: Optional window to run. Uses root window if None.
    """
    GuiManager.run_main_loop(window)


def quit_gui() -> None:
    """Quit the GUI application."""
    GuiManager.quit_application()


def get_gui_info() -> Dict[str, Any]:
    """Get information about the current GUI configuration."""
    return GuiManager.get_info()


def is_gui_mode() -> bool:
    """Check if running in GUI mode (not console)."""
    return GuiManager.is_gui_available()


__all__ = (
    'GuiManager',
    'GuiFramework',
    'initialize_gui',
    'run_gui',
    'quit_gui',
    'get_gui_info',
    'is_gui_mode',
)

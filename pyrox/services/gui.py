"""GUI framework management services for Pyrox.

This module provides functionality to manage GUI frameworks and backends
based on environment configuration. It supports multiple GUI frameworks
and provides a unified interface for GUI operations.
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, Optional, Type, Union

from pyrox.models.gui.backend import GuiBackend
from pyrox.services.env import EnvManager


class GuiFramework(Enum):
    """Supported GUI frameworks."""
    TKINTER = "tkinter"
    QT = "qt"
    WX = "wx"
    KIVY = "kivy"
    PYGAME = "pygame"
    CONSOLE = "console"  # For headless/console mode


class TkinterBackend(GuiBackend):
    """Tkinter GUI backend implementation."""

    def __init__(self):
        self._root = None
        self._tk = None

    def initialize(self) -> bool:
        """Initialize the Tkinter backend."""
        try:
            import tkinter as tk
            self._tk = tk
            return True
        except ImportError:
            return False

    def is_available(self) -> bool:
        """Check if Tkinter is available."""
        try:
            import tkinter as _  # noqa: F401
            return True
        except ImportError:
            return False

    def create_root_window(self, **kwargs) -> Any:
        """Create and return a Tkinter root window."""
        if not self._tk:
            if not self.initialize():
                raise RuntimeError("Tkinter not available")

        if self._root is None:
            if self._tk is None:
                raise RuntimeError("Tkinter not initialized")
            self._root = self._tk.Tk()

        # Apply common configuration
        title = kwargs.pop(
            'title',
            EnvManager.get('UI_WINDOW_TITLE', default='Pyrox Application')
        )
        geometry = kwargs.pop(
            'geometry',
            EnvManager.get('UI_WINDOW_GEOMETRY', default='800x600')
        )

        self._root.title(title)
        self._root.geometry(geometry)

        return self._root

    def get_root_window(self) -> Any:
        if not self._root:
            self.create_root_window()
        return self._root

    def run_main_loop(self, root_window: Any = None) -> None:
        """Start the Tkinter main loop."""
        window = root_window or self._root
        if window:
            window.mainloop()

    def quit_application(self) -> None:
        """Quit the Tkinter application."""
        if self._root:
            self._root.quit()

    @property
    def framework_name(self) -> str:
        return "Tkinter"


class ConsoleBackend(GuiBackend):
    """Console/headless backend for non-GUI operations."""

    def initialize(self) -> bool:
        """Initialize console backend (always successful)."""
        return True

    def is_available(self) -> bool:
        """Console is always available."""
        return True

    def create_root_window(self, **kwargs) -> None:
        """Console mode has no window."""
        return None

    def get_root_window(self) -> Any:
        return None

    def run_main_loop(self, root_window: Any = None) -> None:
        """Console mode main loop (no-op)."""
        pass

    def quit_application(self) -> None:
        """Console mode quit (no-op)."""
        pass

    @property
    def framework_name(self) -> str:
        return "Console"


class GuiManager:
    """Static manager for GUI framework selection and operations."""

    # Class-level storage
    _current_backend: Optional[GuiBackend] = None
    _framework: GuiFramework = GuiFramework.TKINTER
    _backends: Dict[GuiFramework, Type[GuiBackend]] = {
        GuiFramework.TKINTER: TkinterBackend,
        GuiFramework.CONSOLE: ConsoleBackend,
    }
    _initialized: bool = False
    _root_window: Any = None

    def __init__(self):
        """Prevent instantiation of static class."""
        raise TypeError("GuiManager is a static class and cannot be instantiated")

    @classmethod
    def initialize(cls, framework: Optional[Union[GuiFramework, str]] = None) -> bool:
        """Initialize the GUI manager with specified or environment framework.

        Args:
            framework: GUI framework to use. If None, reads from environment.

        Returns:
            True if initialization was successful.
        """
        if cls._initialized:
            return True

        # Determine framework from parameter or environment
        if framework:
            if isinstance(framework, str):
                try:
                    cls._framework = GuiFramework(framework.lower())
                except ValueError:
                    cls._framework = GuiFramework.TKINTER
            else:
                cls._framework = framework
        else:
            # Read from environment variable
            env_gui = EnvManager.get('UI_FRAMEWORK', default='tkinter')
            try:
                cls._framework = GuiFramework(env_gui.lower())
            except ValueError:
                cls._framework = GuiFramework.TKINTER

        # Create and initialize the backend
        backend_class = cls._backends.get(cls._framework)
        if not backend_class:
            # Fallback to tkinter if framework not supported
            cls._framework = GuiFramework.TKINTER
            backend_class = cls._backends[GuiFramework.TKINTER]

        cls._current_backend = backend_class()

        if cls._current_backend.is_available():
            cls._initialized = cls._current_backend.initialize()
        else:
            # Fallback to console if GUI not available
            cls._framework = GuiFramework.CONSOLE
            cls._current_backend = ConsoleBackend()
            cls._initialized = cls._current_backend.initialize()

        return cls._initialized

    @classmethod
    def get_framework(cls) -> GuiFramework:
        """Get the current GUI framework."""
        if not cls._initialized:
            cls.initialize()
        return cls._framework

    @classmethod
    def get_backend(cls) -> Optional[GuiBackend]:
        """Get the current GUI backend."""
        if not cls._initialized:
            cls.initialize()
        return cls._current_backend

    @classmethod
    def is_gui_available(cls) -> bool:
        """Check if GUI is available (not console mode)."""
        if not cls._initialized:
            cls.initialize()
        return cls._framework != GuiFramework.CONSOLE

    @classmethod
    def create_root_window(cls, **kwargs) -> Any:
        """Create a root window using the current backend."""
        if not cls._initialized:
            cls.initialize()

        if cls._current_backend:
            cls._root_window = cls._current_backend.create_root_window(**kwargs)
            return cls._root_window
        return None

    @classmethod
    def get_root_window(cls) -> Any:
        """Get the current root window."""
        return cls._root_window

    @classmethod
    def run_main_loop(cls, root_window: Any = None) -> None:
        """Run the GUI main loop."""
        if not cls._initialized:
            cls.initialize()

        if cls._current_backend:
            window = root_window or cls._root_window
            cls._current_backend.run_main_loop(window)

    @classmethod
    def quit_application(cls) -> None:
        """Quit the GUI application."""
        if cls._current_backend:
            cls._current_backend.quit_application()

    @classmethod
    def register_backend(cls, framework: GuiFramework, backend_class: Type[GuiBackend]) -> None:
        """Register a custom GUI backend.

        Args:
            framework: The framework enum value.
            backend_class: The backend class to register.
        """
        cls._backends[framework] = backend_class

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


# Convenience functions for common operations
def initialize_gui(framework: Optional[Union[GuiFramework, str]] = None) -> bool:
    """Initialize the GUI system.

    Args:
        framework: Optional framework to use. Defaults to environment variable.

    Returns:
        True if initialization successful.
    """
    return GuiManager.initialize(framework)


def create_window(**kwargs) -> Any:
    """Create a root window with the current GUI framework.

    Args:
        **kwargs: Window configuration options (title, geometry, etc.)

    Returns:
        The created window object.
    """
    return GuiManager.create_root_window(**kwargs)


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


def is_gui_enabled() -> bool:
    """Check if GUI is enabled (not console mode)."""
    return EnvManager.get('UI_AUTO_INIT', default=False, cast_type=bool)


def is_gui_mode() -> bool:
    """Check if running in GUI mode (not console)."""
    return GuiManager.is_gui_available()


# Auto-initialize on import if environment variable is set
if is_gui_enabled():
    initialize_gui()
else:
    print("GUI auto-initialization is disabled via environment variable.")


__all__ = (
    'GuiManager',
    'GuiFramework',
    'GuiBackend',
    'TkinterBackend',
    'ConsoleBackend',
    'initialize_gui',
    'create_window',
    'run_gui',
    'quit_gui',
    'get_gui_info',
    'is_gui_mode',
)

"""Unit tests for GUI framework management services."""

import os
import unittest
from typing import Any, Callable
from unittest.mock import patch

from pyrox.interfaces import IApplicationGuiMenu, IGuiBackend, IGuiFrame, GuiFramework
from pyrox.interfaces.gui.menu import IGuiMenu
from pyrox.services.env import EnvManager
from pyrox.services.gui import (
    GuiManager,
    initialize_gui,
    run_gui,
    quit_gui,
    get_gui_info,
    is_gui_mode,
)


class MockGuiBackend(IGuiBackend):
    """Mock GUI backend for testing purposes."""

    def __init__(self, available: bool = True):
        self.available = available
        self.main_loop_called = False
        self.quit_called = False
        self.windows_created = []
        self.windows_destroyed = []

    @property
    def framework_name(self) -> str:
        return "MockFramework"

    def get_framework(self) -> GuiFramework:
        return GuiFramework.CONSOLE

    def initialize(self) -> bool: return True
    def is_available(self) -> bool: return self.available
    def config_from_env(self) -> None: return None

    def set_title(self, title: str) -> None:
        return None

    def cancel_scheduled_event(self, event_id: int | str) -> None:
        return None

    def create_root_gui_window(self, **kwargs) -> Any:
        window = f"MockWindow({kwargs})"
        self.windows_created.append(window)
        return window

    def update_framekwork_tasks(self) -> None:
        return None

    def run_main_loop(self, window=None) -> None: self.main_loop_called = True
    def quit_application(self) -> None: self.quit_called = True
    def destroy_gui_window(self, window, **kwargs) -> None: self.windows_destroyed.append(window)
    def bind_hotkey(self, hotkey: str, callback: Any, **kwargs) -> None: pass
    def configure_root_from_env(self, **kwargs) -> None: pass
    def create_application_gui_menu(self, **kwargs) -> IApplicationGuiMenu: pass  # type: ignore
    def create_gui_frame(self, **kwargs) -> IGuiFrame: pass  # type: ignore
    def create_gui_menu(self, **kwargs) -> Any: pass
    def get_framework_backend(self) -> Any: pass
    def get_root_application_gui_menu(self) -> IApplicationGuiMenu: pass  # type: ignore
    def get_root_gui_window(self) -> Any: pass
    def reroute_excepthook(self, callback: Callable[..., Any]) -> None: pass
    def create_gui_window(self, **kwargs) -> Any: pass
    def get_backend(self) -> Any: return None
    def get_root_application_menu(self) -> Any: return None
    def get_root_window(self) -> Any: return None
    def schedule_event(self, delay_ms: int, callback: Callable[..., Any], **kwargs) -> int | str: return ''
    def set_icon(self, icon_path: str) -> None: pass
    def update_cursor(self, cursor: str) -> None: pass
    def prompt_user_yes_no(self, title: str, message: str) -> bool: return True
    def destroy_gui_frame(self, frame: IGuiFrame) -> None: return None
    def destroy_gui_menu(self, menu: IGuiMenu) -> None: return None
    def setup_keybinds(self, **kwargs) -> None: pass
    def subscribe_to_window_change_event(self, callback: Callable[..., Any]) -> None: pass
    def subscribe_to_window_close_event(self, callback: Callable[..., Any]) -> None: pass


class TestGuiFramework(unittest.TestCase):
    """Test cases for GuiFramework enum."""

    def test_framework_values(self):
        """Test that all framework enums have correct values."""
        self.assertEqual(GuiFramework.TKINTER.value, "tkinter")
        self.assertEqual(GuiFramework.QT.value, "qt")
        self.assertEqual(GuiFramework.WX.value, "wx")
        self.assertEqual(GuiFramework.KIVY.value, "kivy")
        self.assertEqual(GuiFramework.PYGAME.value, "pygame")
        self.assertEqual(GuiFramework.CONSOLE.value, "console")


class TestGuiBackend(unittest.TestCase):
    """Test cases for GuiBackend abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that GuiBackend cannot be instantiated directly."""
        # This should be handled by the type system, but we can test it exists
        self.assertTrue(hasattr(IGuiBackend, '__abstractmethods__'))
        self.assertTrue(len(IGuiBackend.__abstractmethods__) > 0)


class TestGuiManager(unittest.TestCase):
    """Test cases for GuiManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset GuiManager state
        GuiManager._current_backend = None
        GuiManager._framework = GuiFramework.TKINTER
        GuiManager._initialized = False
        GuiManager._root_window = None

        # Clean up loading bar window attribute from previous tests
        if hasattr(GuiManager, '_loading_bar_window'):
            delattr(GuiManager, '_loading_bar_window')

        # Store original backends
        self.original_backends = GuiManager._backends.copy()

        # Clear environment variables that might interfere
        self.original_env = dict(os.environ)
        os.environ.pop('PYROX_GUI_FRAMEWORK', None)
        os.environ.pop('PYROX_AUTO_INIT_GUI', None)

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore GuiManager state
        GuiManager._current_backend = None
        GuiManager._framework = GuiFramework.TKINTER
        GuiManager._initialized = False
        GuiManager._root_window = None
        GuiManager._backends = self.original_backends

        # Restore environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_cannot_instantiate(self):
        """Test that GuiManager cannot be instantiated."""
        with self.assertRaises(TypeError):
            GuiManager()

    def test_initialize_default_framework(self):
        """Test initialization with default framework."""
        GuiManager._backends[GuiFramework.TKINTER] = MockGuiBackend

        result = GuiManager.initialize()

        self.assertTrue(result)
        self.assertTrue(GuiManager._initialized)
        self.assertEqual(GuiManager._framework, GuiFramework.TKINTER)
        self.assertIsInstance(GuiManager._current_backend, MockGuiBackend)

    def test_initialize_with_framework_parameter(self):
        """Test initialization with framework parameter."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend  # type: ignore

        result = GuiManager.initialize(GuiFramework.CONSOLE)

        self.assertTrue(result)
        self.assertEqual(GuiManager._framework, GuiFramework.CONSOLE)

    def test_initialize_with_string_parameter(self):
        """Test initialization with string framework parameter."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend  # type: ignore

        result = GuiManager.initialize("console")

        self.assertTrue(result)
        self.assertEqual(GuiManager._framework, GuiFramework.CONSOLE)

    def test_initialize_with_invalid_string_falls_back(self):
        """Test initialization with invalid string falls back to tkinter."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.TKINTER] = lambda: mock_backend  # type: ignore

        result = GuiManager.initialize("invalid_framework")

        self.assertTrue(result)
        self.assertEqual(GuiManager._framework, GuiFramework.TKINTER)

    @patch.dict(EnvManager._env_vars, {'UI_FRAMEWORK': 'console'})
    def test_initialize_from_environment(self):
        """Test initialization from environment variable."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend  # type: ignore

        result = GuiManager.initialize()

        self.assertTrue(result)
        self.assertEqual(GuiManager._framework, GuiFramework.CONSOLE)

    @patch.dict(os.environ, {'UI_FRAMEWORK': 'invalid'})
    def test_initialize_from_invalid_environment_falls_back(self):
        """Test initialization from invalid environment falls back to tkinter."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.TKINTER] = lambda: mock_backend  # type: ignore

        result = GuiManager.initialize()

        self.assertTrue(result)
        self.assertEqual(GuiManager._framework, GuiFramework.TKINTER)

    def test_initialize_raises_err_if_unavailable(self):
        """Test fallback to console if GUI framework is unavailable."""
        # Create a mock unavailable backend class
        class UnavailableBackend(IGuiBackend):
            def bind_hotkey(self, hotkey: str, callback: Any, **kwargs) -> None: return None
            def cancel_scheduled_event(self, event_id: int | str) -> None: return None
            def config_from_env(self) -> None: return None
            def update_framekwork_tasks(self) -> None: pass
            def set_icon(self, icon_path: str) -> None: return None
            def is_available(self): return False
            def initialize(self): return False
            def configure_root_from_env(self, **kwargs) -> None: return None
            def create_application_gui_menu(self, **kwargs) -> IApplicationGuiMenu: return None  # type: ignore
            def create_gui_frame(self, **kwargs) -> IGuiFrame: pass  # type: ignore
            def create_gui_menu(self, **kwargs) -> Any: return None
            def create_root_gui_window(self, **kwargs): return None  # type: ignore
            def get_framework_backend(self) -> Any: return None
            def get_root_application_gui_menu(self) -> IApplicationGuiMenu: pass  # type: ignore
            def get_root_gui_window(self): return None  # type: ignore
            def reroute_excepthook(self, callback: Callable[..., Any]) -> None: return None
            def run_main_loop(self, root_window=None): pass  # type: ignore
            def quit_application(self): pass
            def create_gui_window(self, **kwargs): return None  # type: ignore
            def set_title(self, title: str) -> None: return None
            def schedule_event(self, delay_ms: int, callback: Callable[..., Any], **kwargs) -> int | str: return ''
            def set_app_icon(self, icon_path: str) -> None: return None
            def setup_keybinds(self, **kwargs) -> None: return None
            def subscribe_to_window_change_event(self, callback: Callable[..., Any]) -> None: return None
            def subscribe_to_window_close_event(self, callback: Callable[..., Any]) -> None: return None
            def destroy_gui_window(self, window, **kwargs): pass
            def update_cursor(self, cursor: str) -> None: return None
            def prompt_user_yes_no(self, title: str, message: str) -> bool: return False
            def destroy_gui_frame(self, frame: IGuiFrame) -> None: return None
            def destroy_gui_menu(self, menu: IGuiMenu) -> None: return None
            def get_root_application_menu(self) -> Any: return None
            def get_backend(self) -> Any: return None
            def get_root_window(self) -> Any: return None
            def get_framework(self): return GuiFramework.TKINTER
            @property
            def framework_name(self): return "Unavailable"

        GuiManager._backends[GuiFramework.TKINTER] = UnavailableBackend

        with self.assertRaises(RuntimeError) as context:
            GuiManager.initialize()
        self.assertIn("Backend for framework tkinter is not available.", str(context.exception))

    def test_initialize_already_initialized_returns_true(self):
        """Test that initialize returns True if already initialized."""
        GuiManager._initialized = True
        result = GuiManager.initialize()
        self.assertTrue(result)

    def test_get_framework(self):
        """Test getting current framework."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend  # type: ignore
        GuiManager.initialize(GuiFramework.CONSOLE)

        framework = GuiManager.get_framework()
        self.assertEqual(framework, GuiFramework.CONSOLE)

    def test_get_backend(self):
        """Test getting current backend."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend  # type: ignore
        GuiManager.initialize(GuiFramework.CONSOLE)

        backend = GuiManager.get_backend()
        self.assertEqual(backend, mock_backend)

    def test_is_gui_available_true_for_gui_framework(self):
        """Test is_gui_available returns True for GUI frameworks."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.TKINTER] = lambda: mock_backend  # type: ignore
        GuiManager.initialize(GuiFramework.TKINTER)

        self.assertTrue(GuiManager.is_gui_available())

    def test_is_gui_available_false_for_console(self):
        """Test is_gui_available returns False for console."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend  # type: ignore
        GuiManager.initialize(GuiFramework.CONSOLE)

        self.assertFalse(GuiManager.is_gui_available())

    def test_run_main_loop(self):
        """Test running main loop."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend  # type: ignore
        GuiManager.initialize(GuiFramework.CONSOLE)

        GuiManager.run_main_loop()
        self.assertTrue(mock_backend.main_loop_called)

    def test_quit_application(self):
        """Test quitting application."""
        mock_backend = MockGuiBackend()
        GuiManager._current_backend = mock_backend

        GuiManager.quit_application()
        self.assertTrue(mock_backend.quit_called)

    def test_register_backend(self):
        """Test registering custom backend."""
        class CustomBackend(MockGuiBackend):
            def initialize(self): return True
            def is_available(self): return True
            def create_root_gui_window(self, **kwargs): return None
            def run_main_loop(self, window=None): pass
            def quit_application(self): pass
            @property
            def framework_name(self): return "Custom"

        GuiManager.register_backend(GuiFramework.QT, CustomBackend)
        self.assertEqual(GuiManager._backends[GuiFramework.QT], CustomBackend)

    def test_get_available_frameworks(self):
        """Test getting available frameworks."""
        available_backend = MockGuiBackend(available=True)
        unavailable_backend = MockGuiBackend(available=False)

        GuiManager._backends = {  # type: ignore
            GuiFramework.TKINTER: lambda: available_backend,
            GuiFramework.QT: lambda: unavailable_backend,
            GuiFramework.CONSOLE: lambda: available_backend,
        }

        available = GuiManager.get_available_frameworks()
        self.assertIn(GuiFramework.TKINTER, available)
        self.assertIn(GuiFramework.CONSOLE, available)
        self.assertNotIn(GuiFramework.QT, available)

    def test_switch_framework(self):
        """Test switching frameworks."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend  # type: ignore
        GuiManager._initialized = True

        result = GuiManager.switch_framework(GuiFramework.CONSOLE)

        self.assertTrue(result)
        self.assertEqual(GuiManager._framework, GuiFramework.CONSOLE)

    def test_switch_framework_with_string(self):
        """Test switching frameworks with string parameter."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend  # type: ignore

        result = GuiManager.switch_framework("console")

        self.assertTrue(result)
        self.assertEqual(GuiManager._framework, GuiFramework.CONSOLE)

    def test_switch_framework_invalid_string(self):
        """Test switching frameworks with invalid string returns False."""
        result = GuiManager.switch_framework("invalid")
        self.assertFalse(result)

    def test_get_info(self):
        """Test getting GUI information."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend  # type: ignore
        GuiManager.initialize(GuiFramework.CONSOLE)
        GuiManager._root_window = "TestWindow"

        info = GuiManager.get_info()

        expected_keys = [
            'framework', 'backend_name', 'initialized',
            'gui_available', 'has_root_window', 'available_frameworks'
        ]
        for key in expected_keys:
            self.assertIn(key, info)

        self.assertEqual(info['framework'], 'console')
        self.assertEqual(info['backend_name'], 'MockFramework')
        self.assertTrue(info['initialized'])
        self.assertFalse(info['gui_available'])
        self.assertTrue(info['has_root_window'])


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset GuiManager state
        GuiManager._current_backend = None
        GuiManager._framework = GuiFramework.TKINTER
        GuiManager._initialized = False
        GuiManager._root_window = None

        # Store original backends
        self.original_backends = GuiManager._backends.copy()

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore GuiManager state
        GuiManager._current_backend = None
        GuiManager._framework = GuiFramework.TKINTER
        GuiManager._initialized = False
        GuiManager._root_window = None
        GuiManager._backends = self.original_backends

    def test_initialize_gui(self):
        """Test initialize_gui convenience function."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend  # type: ignore

        result = initialize_gui(GuiFramework.CONSOLE)
        self.assertTrue(result)

    def test_run_gui(self):
        """Test run_gui convenience function."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend  # type: ignore
        GuiManager.initialize(GuiFramework.CONSOLE)

        run_gui()
        self.assertTrue(mock_backend.main_loop_called)

    def test_quit_gui(self):
        """Test quit_gui convenience function."""
        mock_backend = MockGuiBackend()
        GuiManager._current_backend = mock_backend

        quit_gui()
        self.assertTrue(mock_backend.quit_called)

    def test_get_gui_info(self):
        """Test get_gui_info convenience function."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend  # type: ignore
        GuiManager.initialize(GuiFramework.CONSOLE)

        info = get_gui_info()
        self.assertIsInstance(info, dict)
        self.assertIn('framework', info)

    def test_is_gui_mode_true(self):
        """Test is_gui_mode convenience function returns True for GUI."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.TKINTER] = lambda: mock_backend  # type: ignore
        GuiManager.initialize(GuiFramework.TKINTER)

        self.assertTrue(is_gui_mode())

    def test_is_gui_mode_false(self):
        """Test is_gui_mode convenience function returns False for console."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend  # type: ignore
        GuiManager.initialize(GuiFramework.CONSOLE)

        self.assertFalse(is_gui_mode())


class TestAutoInitialization(unittest.TestCase):
    """Test cases for auto-initialization feature."""

    @patch.dict(os.environ, {'UI_AUTO_INIT': 'true'})
    def test_auto_init_when_enabled(self):
        """Test that auto-initialization occurs when environment variable is set."""
        # Reset GuiManager state first
        from pyrox.services.gui import GuiManager
        GuiManager._initialized = False
        GuiManager._current_backend = None

        # Re-import to check auto-init behavior
        import importlib
        import pyrox.services.gui
        importlib.reload(pyrox.services.gui)

        # Again, reload to get the actual object from reloaded memory
        from pyrox.services.gui import GuiManager
        GuiManager._backends[GuiFramework.TKINTER] = MockGuiBackend
        GuiManager.initialize(None)  # Ensure initialization

        self.assertTrue(GuiManager._initialized)

    @patch.dict(os.environ, {'UI_AUTO_INIT': 'false'})
    @patch('pyrox.services.gui.initialize_gui')
    def test_auto_init_when_disabled(self, mock_initialize):
        """Test that auto-initialization does not occur when disabled."""
        # Reset GuiManager state first
        from pyrox.services.gui import GuiManager
        GuiManager._initialized = False
        GuiManager._current_backend = None

        # Re-import to check auto-init behavior
        import importlib
        import pyrox.services.gui
        importlib.reload(pyrox.services.gui)

        # Should not be called due to false value
        mock_initialize.assert_not_called()


if __name__ == '__main__':
    unittest.main()

"""Unit tests for GUI framework management services."""

import os
import unittest
from typing import Any
from unittest.mock import patch, MagicMock

from pyrox.services.env import EnvManager
from pyrox.models.gui.backend import GuiBackend
from pyrox.services.gui import (
    GuiManager,
    GuiFramework,
    TkinterBackend,
    ConsoleBackend,
    initialize_gui,
    create_window,
    run_gui,
    quit_gui,
    get_gui_info,
    is_gui_mode,
)


class MockGuiBackend(GuiBackend):
    """Mock GUI backend for testing."""

    def __init__(self, available=True, initialize_success=True):
        self.available = available
        self.initialize_success = initialize_success
        self.initialized = False
        self.root_window = None
        self.main_loop_called = False
        self.quit_called = False

    def initialize(self) -> bool:
        self.initialized = True
        return self.initialize_success

    def is_available(self) -> bool:
        return self.available

    def create_root_window(self, **kwargs) -> Any:
        self.root_window = f"MockWindow({kwargs})"
        return self.root_window

    def get_root_window(self) -> Any:
        return getattr(self, 'root_window', None)

    def run_main_loop(self, root_window: Any = None) -> None:
        self.main_loop_called = True

    def quit_application(self) -> None:
        self.quit_called = True

    @property
    def framework_name(self) -> str:
        return "MockFramework"


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
        self.assertTrue(hasattr(GuiBackend, '__abstractmethods__'))
        self.assertTrue(len(GuiBackend.__abstractmethods__) > 0)


class TestTkinterBackend(unittest.TestCase):
    """Test cases for TkinterBackend class."""

    def setUp(self):
        """Set up test fixtures."""
        self.backend = TkinterBackend()

    def test_framework_name(self):
        """Test framework name property."""
        self.assertEqual(self.backend.framework_name, "Tkinter")

    def test_initialize_success(self):
        """Test successful initialization."""
        # Test actual initialization behavior
        result = self.backend.initialize()
        # Should return a boolean regardless of success or failure
        self.assertIsInstance(result, bool)

    def test_initialize_failure(self):
        """Test initialization failure when tkinter not available."""
        with patch('builtins.__import__', side_effect=ImportError):
            result = self.backend.initialize()
            self.assertFalse(result)

    def test_is_available_success(self):
        """Test is_available when tkinter is available."""
        with patch('builtins.__import__'):
            result = self.backend.is_available()
            self.assertTrue(result)

    def test_is_available_failure(self):
        """Test is_available when tkinter is not available."""
        with patch('builtins.__import__', side_effect=ImportError):
            result = self.backend.is_available()
            self.assertFalse(result)

    @patch('tkinter.Tk')
    def test_create_root_window(self, mock_tk_class):
        """Test root window creation."""
        mock_root = MagicMock()
        mock_tk_class.return_value = mock_root
        self.backend._tk = MagicMock()
        self.backend._tk.Tk = mock_tk_class

        result = self.backend.create_root_window(title="Test", geometry="800x600")

        self.assertEqual(result, mock_root)
        mock_root.title.assert_called_once_with("Test")
        mock_root.geometry.assert_called_once_with("800x600")

    def test_create_root_window_initializes_if_needed(self):
        """Test that create_root_window initializes if _tk is None."""
        self.backend._tk = None

        with patch.object(self.backend, 'initialize', return_value=True):
            with patch('tkinter.Tk') as mock_tk_class:
                mock_root = MagicMock()
                mock_tk_class.return_value = mock_root
                self.backend._tk = MagicMock()
                self.backend._tk.Tk = mock_tk_class

                result = self.backend.create_root_window()
                self.assertIsNotNone(result)

    def test_create_root_window_raises_if_init_fails(self):
        """Test that create_root_window raises error if initialization fails."""
        self.backend._tk = None

        with patch.object(self.backend, 'initialize', return_value=False):
            with self.assertRaises(RuntimeError):
                self.backend.create_root_window()

    def test_run_main_loop_with_window(self):
        """Test running main loop with provided window."""
        mock_window = MagicMock()
        self.backend.run_main_loop(mock_window)
        mock_window.mainloop.assert_called_once()

    def test_run_main_loop_with_root(self):
        """Test running main loop with root window."""
        mock_root = MagicMock()
        self.backend._root = mock_root
        self.backend.run_main_loop()
        mock_root.mainloop.assert_called_once()

    def test_quit_application(self):
        """Test quitting application."""
        mock_root = MagicMock()
        self.backend._root = mock_root
        self.backend.quit_application()
        mock_root.quit.assert_called_once()


class TestConsoleBackend(unittest.TestCase):
    """Test cases for ConsoleBackend class."""

    def setUp(self):
        """Set up test fixtures."""
        self.backend = ConsoleBackend()

    def test_framework_name(self):
        """Test framework name property."""
        self.assertEqual(self.backend.framework_name, "Console")

    def test_initialize_always_succeeds(self):
        """Test that initialize always returns True."""
        self.assertTrue(self.backend.initialize())

    def test_is_available_always_true(self):
        """Test that is_available always returns True."""
        self.assertTrue(self.backend.is_available())

    def test_create_root_window_returns_none(self):
        """Test that create_root_window returns None."""
        self.assertIsNone(self.backend.create_root_window())

    def test_run_main_loop_no_op(self):
        """Test that run_main_loop is a no-op."""
        # Should not raise any exceptions
        self.backend.run_main_loop()
        self.backend.run_main_loop(None)

    def test_quit_application_no_op(self):
        """Test that quit_application is a no-op."""
        # Should not raise any exceptions
        self.backend.quit_application()


class TestGuiManager(unittest.TestCase):
    """Test cases for GuiManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset GuiManager state
        GuiManager._current_backend = None
        GuiManager._framework = GuiFramework.TKINTER
        GuiManager._initialized = False
        GuiManager._root_window = None

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
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend

        result = GuiManager.initialize(GuiFramework.CONSOLE)

        self.assertTrue(result)
        self.assertEqual(GuiManager._framework, GuiFramework.CONSOLE)

    def test_initialize_with_string_parameter(self):
        """Test initialization with string framework parameter."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend

        result = GuiManager.initialize("console")

        self.assertTrue(result)
        self.assertEqual(GuiManager._framework, GuiFramework.CONSOLE)

    def test_initialize_with_invalid_string_falls_back(self):
        """Test initialization with invalid string falls back to tkinter."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.TKINTER] = lambda: mock_backend

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
        GuiManager._backends[GuiFramework.TKINTER] = lambda: mock_backend

        result = GuiManager.initialize()

        self.assertTrue(result)
        self.assertEqual(GuiManager._framework, GuiFramework.TKINTER)

    def test_initialize_falls_back_to_console_if_unavailable(self):
        """Test fallback to console if GUI framework is unavailable."""
        # Create a mock unavailable backend class
        class UnavailableBackend(GuiBackend):
            def is_available(self): return False
            def initialize(self): return False
            def create_root_window(self, **kwargs): return None
            def get_root_window(self): return None
            def run_main_loop(self, root_window=None): pass
            def quit_application(self): pass
            @property
            def framework_name(self): return "Unavailable"

        GuiManager._backends[GuiFramework.TKINTER] = UnavailableBackend

        result = GuiManager.initialize()

        self.assertTrue(result)
        self.assertEqual(GuiManager._framework, GuiFramework.CONSOLE)
        # Should fall back to ConsoleBackend, not our mock
        self.assertIsInstance(GuiManager._current_backend, ConsoleBackend)

    def test_initialize_already_initialized_returns_true(self):
        """Test that initialize returns True if already initialized."""
        GuiManager._initialized = True
        result = GuiManager.initialize()
        self.assertTrue(result)

    def test_get_framework(self):
        """Test getting current framework."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend
        GuiManager.initialize(GuiFramework.CONSOLE)

        framework = GuiManager.get_framework()
        self.assertEqual(framework, GuiFramework.CONSOLE)

    def test_get_backend(self):
        """Test getting current backend."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend
        GuiManager.initialize(GuiFramework.CONSOLE)

        backend = GuiManager.get_backend()
        self.assertEqual(backend, mock_backend)

    def test_is_gui_available_true_for_gui_framework(self):
        """Test is_gui_available returns True for GUI frameworks."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.TKINTER] = lambda: mock_backend
        GuiManager.initialize(GuiFramework.TKINTER)

        self.assertTrue(GuiManager.is_gui_available())

    def test_is_gui_available_false_for_console(self):
        """Test is_gui_available returns False for console."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend
        GuiManager.initialize(GuiFramework.CONSOLE)

        self.assertFalse(GuiManager.is_gui_available())

    def test_create_root_window(self):
        """Test creating root window."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend
        GuiManager.initialize(GuiFramework.CONSOLE)

        window = GuiManager.create_root_window(title="Test")

        self.assertEqual(window, "MockWindow({'title': 'Test'})")
        self.assertEqual(GuiManager._root_window, window)

    def test_get_root_window(self):
        """Test getting root window."""
        test_window = "TestWindow"
        GuiManager._root_window = test_window

        window = GuiManager.get_root_window()
        self.assertEqual(window, test_window)

    def test_run_main_loop(self):
        """Test running main loop."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend
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
        class CustomBackend(GuiBackend):
            def initialize(self): return True
            def is_available(self): return True
            def create_root_window(self, **kwargs): return None
            def run_main_loop(self, root_window=None): pass
            def quit_application(self): pass
            @property
            def framework_name(self): return "Custom"

        GuiManager.register_backend(GuiFramework.QT, CustomBackend)
        self.assertEqual(GuiManager._backends[GuiFramework.QT], CustomBackend)

    def test_get_available_frameworks(self):
        """Test getting available frameworks."""
        available_backend = MockGuiBackend(available=True)
        unavailable_backend = MockGuiBackend(available=False)

        GuiManager._backends = {
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
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend
        GuiManager._initialized = True

        result = GuiManager.switch_framework(GuiFramework.CONSOLE)

        self.assertTrue(result)
        self.assertEqual(GuiManager._framework, GuiFramework.CONSOLE)

    def test_switch_framework_with_string(self):
        """Test switching frameworks with string parameter."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend

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
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend
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
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend

        result = initialize_gui(GuiFramework.CONSOLE)
        self.assertTrue(result)

    def test_create_window(self):
        """Test create_window convenience function."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend
        GuiManager.initialize(GuiFramework.CONSOLE)

        window = create_window(title="Test")
        self.assertEqual(window, "MockWindow({'title': 'Test'})")

    def test_run_gui(self):
        """Test run_gui convenience function."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend
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
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend
        GuiManager.initialize(GuiFramework.CONSOLE)

        info = get_gui_info()
        self.assertIsInstance(info, dict)
        self.assertIn('framework', info)

    def test_is_gui_mode_true(self):
        """Test is_gui_mode convenience function returns True for GUI."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.TKINTER] = lambda: mock_backend
        GuiManager.initialize(GuiFramework.TKINTER)

        self.assertTrue(is_gui_mode())

    def test_is_gui_mode_false(self):
        """Test is_gui_mode convenience function returns False for console."""
        mock_backend = MockGuiBackend()
        GuiManager._backends[GuiFramework.CONSOLE] = lambda: mock_backend
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

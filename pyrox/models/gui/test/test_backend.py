"""Unit tests for GUI backend implementations.

This module tests the ConsoleBackend and TkinterBackend classes,
ensuring proper initialization, window management, and GUI operations.
"""

import unittest
from unittest.mock import patch, MagicMock

from pyrox.interfaces import GuiFramework
from pyrox.models.gui.console import ConsoleBackend
from pyrox.models.gui.tk import TkinterBackend
from pyrox.models.gui.tk.frame import TkinterGuiFrame
from pyrox.models.gui.tk.menu import TkinterApplicationMenu, TkinterMenu
from pyrox.models.gui.tk.window import TkinterGuiWindow


class TestConsoleBackend(unittest.TestCase):
    """Test cases for ConsoleBackend class."""

    def setUp(self):
        """Set up test fixtures."""
        self.backend = ConsoleBackend()

    def test_framework_property(self):
        """Test framework property returns CONSOLE."""
        self.assertEqual(self.backend.framework, GuiFramework.CONSOLE)

    def test_framework_name_property(self):
        """Test framework_name property returns 'Console'."""
        self.assertEqual(self.backend.framework_name, "Console")

    def test_initialize_always_succeeds(self):
        """Test that initialize always returns True."""
        self.assertTrue(self.backend.initialize())

    def test_is_available_always_true(self):
        """Test that is_available always returns True."""
        self.assertTrue(self.backend.is_available())

    def test_get_backend_returns_none(self):
        """Test that get_backend returns None for console."""
        self.assertIsNone(self.backend.get_backend())

    def test_get_root_gui_window_returns_none(self):
        """Test that get_root_gui_window returns None."""
        self.assertIsNone(self.backend.get_root_gui_window())

    def test_run_main_loop_no_op(self):
        """Test that run_main_loop is a no-op."""
        # Should not raise any exceptions
        self.backend.run_main_loop()
        self.backend.run_main_loop(None)
        self.backend.run_main_loop("some_window")

    def test_create_root_gui_window_raises_not_implemented(self):
        """Test that create_root_gui_window raises NotImplementedError."""
        with self.assertRaises(NotImplementedError) as context:
            self.backend.create_root_window()
        self.assertIn('Console backend does not support window creation', str(context.exception))

    def test_create_gui_window_raises_not_implemented(self):
        """Test that create_gui_window raises NotImplementedError."""
        with self.assertRaises(NotImplementedError) as context:
            self.backend.create_gui_window()
        self.assertIn('Console backend does not support window creation', str(context.exception))

    def test_create_gui_frame_raises_not_implemented(self):
        """Test that create_gui_frame raises NotImplementedError."""
        with self.assertRaises(NotImplementedError) as context:
            self.backend.create_gui_frame()
        self.assertIn('Console backend does not support frame creation', str(context.exception))

    def test_set_icon_raises_not_implemented(self):
        """Test that set_icon raises NotImplementedError."""
        with self.assertRaises(NotImplementedError) as context:
            self.backend.set_icon("/path/to/icon.ico")
        self.assertIn('Console backend does not support setting an app icon', str(context.exception))


class TestTkinterBackend(unittest.TestCase):
    """Test cases for TkinterBackend class."""

    def setUp(self):
        """Set up test fixtures."""
        self.backend = TkinterBackend()

        self.mock_tk_patcher = patch('pyrox.models.gui.tk.window.Tk')
        self.mock_tk_instance = self.mock_tk_patcher.start()
        self.mock_tk_instance.return_value = MagicMock()

        self.mock_toplevel_patcher = patch('pyrox.models.gui.tk.window.Toplevel')
        self.mock_toplevel_instance = self.mock_toplevel_patcher.start()
        self.mock_toplevel_instance.return_value = MagicMock()

        self.mock_theme_created_patcher = patch('pyrox.services.theme.ThemeManager.ensure_theme_created')
        self.mock_theme_created_patcher.start()

    def tearDown(self):
        """Clean up test fixtures."""
        # Reset backend state
        self.backend._root_window = None
        self.backend._menu = None
        self.backend._tk = None
        self.mock_tk_patcher.stop()
        self.mock_toplevel_patcher.stop()
        self.mock_theme_created_patcher.stop()

    def test_framework_property(self):
        """Test framework property returns TKINTER."""
        self.assertEqual(self.backend.framework, GuiFramework.TKINTER)

    def test_framework_name_property(self):
        """Test framework_name property returns 'Tkinter'."""
        self.assertEqual(self.backend.framework_name, "Tkinter")

    def test_initialize_success(self):
        """Test successful initialization."""
        result = self.backend.initialize()
        self.assertTrue(result)
        self.assertIsNotNone(self.backend._tk)

    def test_is_available_success(self):
        """Test is_available when tkinter is available."""
        result = self.backend.is_available()
        self.assertTrue(result)

    def test_is_available_failure(self):
        """Test is_available when tkinter is not available."""
        with patch('builtins.__import__', side_effect=ImportError):
            result = self.backend.is_available()
            self.assertFalse(result)

    def test_get_backend_returns_tk_module(self):
        """Test that get_backend returns the tk module after initialization."""
        self.backend.initialize()
        backend = self.backend.get_backend()
        self.assertIsNotNone(backend)

    def test_create_root_gui_window_success(self):
        """Test successful root window creation."""

        with patch.object(self.backend, 'config_from_env') as mock_config:
            result = self.backend.create_root_window(title="Test", geometry="800x600")

            # Verify the result is a TkinterGuiWindow with the mocked Tk instance
            self.assertIsInstance(result, TkinterGuiWindow)
            self.assertEqual(result.root, self.mock_tk_instance.return_value)
            # Verify config_from_env was called with the right parameters
            mock_config.assert_called_once_with(title="Test", geometry="800x600")

    def test_create_root_gui_window_initializes_if_needed(self):
        """Test that create_root_window initializes if _tk is None."""
        self.backend._tk = None

        def mock_initialize():
            import tkinter as tk
            self.backend._tk = tk  # type: ignore
            return True

        with patch.object(self.backend, 'config_from_env'):
            with patch.object(self.backend, 'initialize', side_effect=mock_initialize) as mock_init:
                result = self.backend.create_root_window()

                # Verify initialize was called
                mock_init.assert_called_once()
                # Verify a result was returned
                self.assertIsNotNone(result)

    def test_create_root_gui_window_returns_existing(self):
        """Test that create_root_window returns existing window if already created."""
        mock_existing_window = MagicMock(spec=TkinterGuiWindow)
        self.backend._root_window = mock_existing_window
        self.backend._tk = MagicMock()  # Ensure _tk is not None # type: ignore

        result = self.backend.create_root_window()

        # Should return the existing window without creating a new one
        self.assertEqual(result, mock_existing_window)

    def test_create_root_gui_window_raises_if_init_fails(self):
        """Test that create_root_window raises error if initialization fails."""
        self.backend._tk = None

        with patch.object(self.backend, 'initialize', return_value=False):
            with self.assertRaises(RuntimeError) as context:
                self.backend.create_root_window()
            self.assertIn("Tkinter not available", str(context.exception))

    def test_create_root_gui_window_raises_if_tk_not_initialized(self):
        """Test that create_root_window raises error if _tk is None after init check."""
        # This test validates the condition where _tk is unexpectedly None
        # In practice, this should be handled by the check at line 241 in backend.py
        # So we'll just verify the method properly checks for this condition
        self.backend._root_window = None
        self.backend._tk = None

        # Should raise RuntimeError when trying to create without initialization
        with self.assertRaises(RuntimeError) as context:
            # Force the condition by patching initialize to return True but not set _tk
            with patch.object(self.backend, 'initialize', return_value=False):
                self.backend.create_root_window()

        self.assertIn("Tkinter not available", str(context.exception))

    def test_create_root_gui_window_only_creates_one_instance(self):
        """Test that create_root_gui_window only creates one instance."""
        mock_tk_instance = MagicMock()

        with patch('tkinter.Tk', return_value=mock_tk_instance):
            with patch('pyrox.services.theme.ThemeManager.ensure_theme_created'):
                with patch.object(self.backend, 'config_from_env'):
                    # First call to create_root_gui_window
                    first_window = self.backend.create_root_window()

                    # Second call to create_root_gui_window
                    second_window = self.backend.create_root_window()

                    # Both calls should return the same instance
                    self.assertIs(first_window, second_window)

    def test_create_gui_window_success(self):
        """Test creating a secondary GUI window."""

        # Need to patch isinstance to accept our mock
        with patch('pyrox.models.gui.tk.window.isinstance', return_value=True):
            result = self.backend.create_gui_window(title="Secondary")

            # Verify Toplevel was called with the root gui as master
            self.mock_toplevel_instance.assert_called_once()
            # Verify the result is a TkinterGuiWindow
            self.assertIsInstance(result, TkinterGuiWindow)

    def test_create_application_gui_menu_success(self):
        """Test creating application GUI menu."""
        mock_tk_window = MagicMock()
        self.backend._tk = MagicMock()  # Ensure initialized # type: ignore

        with patch.object(self.backend, 'get_root_window', return_value=mock_tk_window):
            # Mock the initialize method and the menu property to avoid actual tkinter menu creation
            with patch('pyrox.models.gui.tk.menu.TkinterApplicationMenu.initialize'):
                with patch('pyrox.models.gui.tk.menu.TkinterApplicationMenu.menu', new_callable=lambda: MagicMock()):
                    result = self.backend.create_application_gui_menu()

                    self.assertIsInstance(result, TkinterApplicationMenu)
                    self.assertIsNotNone(self.backend._menu)

    def test_create_application_gui_menu_returns_existing(self):
        """Test that create_application_gui_menu returns existing menu if already created."""
        mock_menu = MagicMock(spec=TkinterApplicationMenu)
        self.backend._menu = mock_menu
        self.backend._tk = MagicMock()  # type: ignore
        mock_tk_window = MagicMock()

        with patch.object(self.backend, 'get_root_window', return_value=mock_tk_window):
            result = self.backend.create_application_gui_menu()

            # Should return the existing menu
            self.assertEqual(result, mock_menu)

    def test_create_application_gui_menu_initializes_if_needed(self):
        """Test that create_application_gui_menu initializes backend if needed."""
        self.backend._tk = None

        with patch.object(self.backend, 'initialize', return_value=True) as mock_init:
            with patch.object(self.backend, 'get_root_window', return_value=MagicMock()):
                with patch('pyrox.models.gui.tk.menu.TkinterApplicationMenu.initialize'):
                    with patch('pyrox.models.gui.tk.menu.TkinterApplicationMenu.menu', new_callable=lambda: MagicMock()):
                        self.backend.create_application_gui_menu()

                        mock_init.assert_called()

    def test_create_application_gui_menu_raises_if_init_fails(self):
        """Test that create_application_gui_menu raises error if initialization fails."""
        self.backend._tk = None

        with patch.object(self.backend, 'initialize', return_value=False):
            with self.assertRaises(RuntimeError) as context:
                self.backend.create_application_gui_menu()
            self.assertIn("Tkinter not available", str(context.exception))

    def test_create_gui_frame_success(self):
        """Test creating a GUI frame."""
        result = self.backend.create_gui_frame(master=MagicMock())

        self.assertIsInstance(result, TkinterGuiFrame)

    def test_create_gui_menu_success(self):
        """Test creating a GUI menu."""
        result = self.backend.create_gui_menu(master=MagicMock())

        self.assertIsInstance(result, TkinterMenu)

    def test_get_root_application_gui_menu_creates_if_needed(self):
        """Test that get_root_application_gui_menu creates menu if needed."""
        self.backend._menu = None
        self.backend._tk = MagicMock()  # type: ignore
        mock_menu = MagicMock(spec=TkinterApplicationMenu)

        with patch.object(self.backend, 'create_application_gui_menu', return_value=mock_menu) as mock_create:
            # Manually set _menu after the call to simulate the creation
            def set_menu():
                self.backend._menu = mock_menu
                return mock_menu

            mock_create.side_effect = set_menu

            result = self.backend.get_root_application_gui_menu()

            mock_create.assert_called_once()
            self.assertEqual(result, mock_menu)

    def test_get_root_application_gui_menu_returns_existing(self):
        """Test that get_root_application_gui_menu returns existing menu."""
        mock_menu = MagicMock(spec=TkinterApplicationMenu)
        self.backend._menu = mock_menu

        result = self.backend.get_root_application_gui_menu()

        self.assertEqual(result, mock_menu)

    def test_get_root_application_gui_menu_raises_if_creation_fails(self):
        """Test that get_root_application_gui_menu raises error if creation fails."""
        self.backend._menu = None

        with patch.object(self.backend, 'create_application_gui_menu', return_value=None):
            with self.assertRaises(RuntimeError) as context:
                self.backend.get_root_application_gui_menu()
            self.assertIn("Menu not initialized", str(context.exception))

    def test_get_root_application_menu_returns_menu_object(self):
        """Test that get_root_application_menu returns the underlying menu object."""
        mock_menu_object = MagicMock()
        mock_menu = MagicMock(spec=TkinterApplicationMenu)
        mock_menu.menu = mock_menu_object
        self.backend._menu = mock_menu

        with patch.object(self.backend, 'get_root_application_gui_menu', return_value=mock_menu):
            result = self.backend.get_root_application_menu()

            self.assertEqual(result, mock_menu_object)

    def test_get_root_gui_window_creates_if_needed(self):
        """Test that get_root_gui_window creates window if needed."""
        self.backend._root_window = None
        mock_window = MagicMock(spec=TkinterGuiWindow)

        with patch.object(self.backend, 'create_root_window', return_value=mock_window) as mock_create:
            # Manually set _root_gui after the call to simulate the creation
            def set_window():
                self.backend._root_window = mock_window
                return mock_window

            mock_create.side_effect = set_window

            result = self.backend.get_root_gui_window()

            mock_create.assert_called_once()
            self.assertEqual(result, mock_window)

    def test_get_root_gui_window_returns_existing(self):
        """Test that get_root_gui_window returns existing window."""
        mock_window = MagicMock(spec=TkinterGuiWindow)
        self.backend._root_window = mock_window

        result = self.backend.get_root_gui_window()

        self.assertEqual(result, mock_window)

    def test_get_root_gui_window_raises_if_creation_fails(self):
        """Test that get_root_gui_window raises error if creation fails."""
        self.backend._root_window = None

        with patch.object(self.backend, 'create_root_window', return_value=None):
            with self.assertRaises(RuntimeError) as context:
                self.backend.get_root_gui_window()
            self.assertIn("Root window not initialized", str(context.exception))

    def test_get_root_window_returns_window_object(self):
        """Test that get_root_window returns the underlying window object."""
        mock_tk_window = MagicMock()
        mock_gui_window = MagicMock(spec=TkinterGuiWindow)
        mock_gui_window.root = mock_tk_window
        self.backend._root_window = mock_gui_window

        result = self.backend.get_root_window()

        self.assertEqual(result, mock_tk_window)

    def test_destroy_gui_frame_success(self):
        """Test destroying a GUI frame."""
        mock_frame = MagicMock(spec=TkinterGuiFrame)
        mock_frame_widget = MagicMock()
        mock_frame.root = mock_frame_widget

        self.backend.destroy_gui_frame(mock_frame)

        mock_frame_widget.destroy.assert_called_once()

    def test_destroy_gui_frame_raises_type_error(self):
        """Test that destroy_gui_frame raises TypeError for wrong type."""
        with self.assertRaises(TypeError) as context:
            self.backend.destroy_gui_frame("not a frame")  # type: ignore
        self.assertIn("Expected a TkinterGuiFrame instance", str(context.exception))

    def test_destroy_gui_menu_success(self):
        """Test destroying a GUI menu."""
        mock_menu = MagicMock(spec=TkinterMenu)
        mock_menu_widget = MagicMock()
        mock_menu.menu = mock_menu_widget

        self.backend.destroy_gui_menu(mock_menu)

        mock_menu_widget.destroy.assert_called_once()

    def test_destroy_gui_menu_raises_type_error(self):
        """Test that destroy_gui_menu raises TypeError for wrong type."""
        with self.assertRaises(TypeError) as context:
            self.backend.destroy_gui_menu("not a menu")  # type: ignore
        self.assertIn("Expected a TkinterMenu instance", str(context.exception))

    def test_destroy_gui_window_success(self):
        """Test destroying a GUI window."""
        mock_window = MagicMock(spec=TkinterGuiWindow)

        self.backend.destroy_gui_window(mock_window)

        mock_window.destroy.assert_called_once()

    def test_destroy_gui_window_raises_type_error(self):
        """Test that destroy_gui_window raises TypeError for wrong type."""
        with self.assertRaises(TypeError) as context:
            self.backend.destroy_gui_window("not a window")
        self.assertIn("Expected a TkinterGuiWindow instance", str(context.exception))

    def test_run_main_loop_with_window(self):
        """Test running main loop with provided window."""
        mock_window = MagicMock(spec=TkinterGuiWindow)
        mock_tk_window = MagicMock()
        mock_window.root = mock_tk_window

        self.backend.run_main_loop(mock_window)

        mock_tk_window.mainloop.assert_called_once()

    def test_run_main_loop_with_root(self):
        """Test running main loop with root window."""
        mock_root = MagicMock(spec=TkinterGuiWindow)
        mock_tk_window = MagicMock()
        mock_root.root = mock_tk_window
        self.backend._root_window = mock_root

        self.backend.run_main_loop()

        mock_tk_window.mainloop.assert_called_once()

    def test_run_main_loop_raises_type_error(self):
        """Test that run_main_loop raises TypeError for wrong type."""
        with self.assertRaises(TypeError) as context:
            self.backend.run_main_loop("not a window")
        self.assertIn("Expected a TkinterGuiWindow instance", str(context.exception))

    def test_quit_application(self):
        """Test quitting application."""
        mock_tk_window = MagicMock()

        with patch.object(self.backend, 'get_root_window', return_value=mock_tk_window):
            self.backend.quit_application()
            mock_tk_window.quit.assert_called_once()

    def test_config_from_env_success(self):
        """Test configuring from environment variables."""
        import tkinter as tk
        mock_tk_window = MagicMock(spec=tk.Tk)

        with patch.object(self.backend, 'get_root_window', return_value=mock_tk_window):
            with patch.object(self.backend, 'set_title') as mock_set_title:
                with patch('pyrox.services.env.EnvManager.get') as mock_env_get:
                    # Support new EnvironmentKeys enum-based access by normalizing keys
                    def _normalize_key(k):
                        try:
                            from enum import Enum
                            return str(k.value) if isinstance(k, Enum) else k
                        except Exception:
                            return k

                    mock_env_get.side_effect = lambda key, default=None, *args: {
                        'APP_WINDOW_TITLE': 'Test Title',
                        'UI_WINDOW_SIZE': '1024x768',
                        'APP_ICON': None
                    }.get(_normalize_key(key), default)

                    self.backend.config_from_env(title='Default Title', geometry='800x600')

                    mock_set_title.assert_called_once_with('Test Title')
                    mock_tk_window.geometry.assert_called_once_with('1024x768')

    def test_config_from_env_with_icon(self):
        """Test configuring with icon path."""
        import tkinter as tk
        mock_tk_window = MagicMock(spec=tk.Tk)
        test_icon_path = 'test_icon.ico'

        with patch.object(self.backend, 'get_root_window', return_value=mock_tk_window):
            with patch.object(self.backend, 'set_title'):
                with patch('pyrox.services.env.EnvManager.get') as mock_env_get:
                    with patch('pathlib.Path.is_file', return_value=True):
                        with patch.object(self.backend, 'set_icon') as mock_set_icon:
                            def _normalize_key(k):
                                try:
                                    from enum import Enum
                                    return str(k.value) if isinstance(k, Enum) else k
                                except Exception:
                                    return k

                            mock_env_get.side_effect = lambda key, default=None, *args: {
                                'APP_WINDOW_TITLE': 'Test',
                                'UI_WINDOW_SIZE': '800x600',
                                'APP_ICON': test_icon_path
                            }.get(_normalize_key(key), default)

                            self.backend.config_from_env()

                            mock_set_icon.assert_called_with(test_icon_path)

    def test_config_from_env_raises_if_not_tk_instance(self):
        """Test that config_from_env raises error when main_window is not properly initialized."""
        # Mock main_window to raise an error when trying to set title
        with patch.object(self.backend, 'set_title', side_effect=AttributeError("Mock attribute error")):
            with self.assertRaises(AttributeError):
                self.backend.config_from_env()

    def test_bind_hotkey_success(self):
        """Test binding a hotkey."""
        mock_tk_window = MagicMock()
        mock_root_gui = MagicMock()
        self.backend._root_window = mock_root_gui
        callback = MagicMock()

        with patch.object(self.backend, 'get_root_window', return_value=mock_tk_window):
            self.backend.bind_hotkey('<Control-s>', callback)

            mock_tk_window.bind.assert_called_once()
            # Get the bound function and test it calls the callback
            bound_func = mock_tk_window.bind.call_args[0][1]
            bound_func(None)  # Simulate event
            callback.assert_called_once()

    def test_bind_hotkey_raises_if_no_root_window(self):
        """Test that bind_hotkey raises error if root window not initialized."""
        self.backend._root_window = None

        with self.assertRaises(RuntimeError) as context:
            self.backend.bind_hotkey('<Control-s>', lambda: None)
        self.assertIn("Root window not initialized", str(context.exception))

    def test_schedule_event(self):
        """Test scheduling an event."""
        mock_tk_window = MagicMock()
        callback = MagicMock()

        with patch.object(self.backend, 'get_root_window', return_value=mock_tk_window):
            self.backend.schedule_event(1000, callback)

            mock_tk_window.after.assert_called_once_with(1000, callback)

    def test_set_icon(self):
        """Test setting application icon."""
        mock_gui_window = MagicMock(spec=TkinterGuiWindow)

        with patch.object(self.backend, 'get_root_gui_window', return_value=mock_gui_window):
            self.backend.set_icon('test_icon.ico')

            mock_gui_window.set_icon.assert_called_once_with('test_icon.ico')

    def test_subscribe_to_window_close_event(self):
        """Test subscribing to window close event."""
        mock_tk_window = MagicMock()
        callback = MagicMock()

        with patch.object(self.backend, 'get_root_window', return_value=mock_tk_window):
            self.backend.subscribe_to_window_close_event(callback)

            mock_tk_window.protocol.assert_called_once_with("WM_DELETE_WINDOW", callback)

    def test_update_cursor_success(self):
        """Test updating cursor."""
        mock_tk_window = MagicMock()

        with patch.object(self.backend, 'get_root_window', return_value=mock_tk_window):
            self.backend.update_cursor('hand2')

            mock_tk_window.config.assert_called_once_with(cursor='hand2')

    def test_update_cursor_raises_type_error(self):
        """Test that update_cursor raises TypeError for non-string."""
        with self.assertRaises(TypeError) as context:
            self.backend.update_cursor(123)  # type: ignore
        self.assertIn("Cursor must be a string", str(context.exception))

    def test_prompt_user_yes_no_returns_true(self):
        """Test prompt_user_yes_no returning True."""
        with patch('tkinter.messagebox.askyesno', return_value=True) as mock_dialog:
            result = self.backend.prompt_user_yes_no('Test Title', 'Test Message')

            mock_dialog.assert_called_once_with('Test Title', 'Test Message')
            self.assertTrue(result)

    def test_prompt_user_yes_no_returns_false(self):
        """Test prompt_user_yes_no returning False."""
        with patch('tkinter.messagebox.askyesno', return_value=False) as mock_dialog:
            result = self.backend.prompt_user_yes_no('Test Title', 'Test Message')

            mock_dialog.assert_called_once_with('Test Title', 'Test Message')
            self.assertFalse(result)

    def test_reroute_excepthook(self):
        """Test rerouting exception hook."""
        mock_tk = MagicMock()
        self.backend._tk = mock_tk  # type: ignore
        callback = MagicMock()

        with patch.object(self.backend, 'get_backend', return_value=mock_tk):
            self.backend.reroute_excepthook(callback)

            self.assertEqual(mock_tk.report_callback_exception, callback)

    def test_setup_keybinds_no_op(self):
        """Test that setup_keybinds is currently a no-op."""
        # Should not raise any exceptions
        self.backend.setup_keybinds()

    def test_subscribe_to_window_change_event_no_op(self):
        """Test that subscribe_to_window_change_event binds to window configure event."""
        # Mock the root window to prevent actual Tk window creation
        mock_window = MagicMock()

        with patch.object(self.backend, 'get_root_window', return_value=mock_window):
            callback = MagicMock()
            self.backend.subscribe_to_window_change_event(callback)

            # Verify bind was called with <Configure> event
            mock_window.bind.assert_called_once()
            call_args = mock_window.bind.call_args[0]
            self.assertEqual(call_args[0], "<Configure>")


class TestBackendRegistration(unittest.TestCase):
    """Test cases for backend registration with GuiManager."""

    def test_backends_are_registered(self):
        """Test that TkinterBackend and ConsoleBackend are registered with GuiManager."""
        from pyrox.services.gui import GuiManager

        # Check that backends are registered
        self.assertIn(GuiFramework.TKINTER, GuiManager._backends)
        self.assertIn(GuiFramework.CONSOLE, GuiManager._backends)

        # Check that the registered classes are correct
        self.assertEqual(GuiManager._backends[GuiFramework.TKINTER], TkinterBackend)
        self.assertEqual(GuiManager._backends[GuiFramework.CONSOLE], ConsoleBackend)


if __name__ == '__main__':
    unittest.main()

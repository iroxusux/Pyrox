"""Unit tests for application.py module."""

import unittest
from unittest.mock import MagicMock, Mock, patch, mock_open
from tkinter import Frame, TclError, Tk

from pyrox.models.application import Application
from pyrox.models.abc import stream
from pyrox.services.file import PlatformDirectoryService
from pyrox.models.menu import MainApplicationMenu


class TestApplication(unittest.TestCase):
    """Test cases for Application class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock objects
        self.mock_tk = Mock(spec=Tk)
        self.mock_frame = Mock(spec=Frame)
        self.mock_menu = Mock(spec=MainApplicationMenu)
        self.mock_directory_service = Mock(spec=PlatformDirectoryService)
        self.mock_multi_stream = Mock(spec=stream.MultiStream)

        # Set up mock attributes
        self.mock_tk.winfo_screenwidth.return_value = 1920
        self.mock_tk.winfo_screenheight.return_value = 1080
        self.mock_tk.winfo_reqwidth.return_value = 800
        self.mock_tk.winfo_reqheight.return_value = 600
        self.mock_tk.winfo_width.return_value = 800
        self.mock_tk.winfo_height.return_value = 600
        self.mock_tk.winfo_x.return_value = 100
        self.mock_tk.winfo_y.return_value = 100
        self.mock_tk.state.return_value = 'normal'
        self.mock_tk.attributes.return_value = False

        # Mock directory service
        self.mock_directory_service.user_log_file = '/tmp/test.log'
        self.mock_directory_service.get_log_file_stream.return_value = MagicMock()

    def tearDown(self):
        """Clean up test fixtures."""
        pass

    def test_init_sets_excepthook(self):
        """Test that initialization sets sys.excepthook."""
        with patch('pyrox.models.application.PlatformDirectoryService') as mock_service_class:
            mock_service_class.return_value = self.mock_directory_service
            with patch('pyrox.models.application.sys') as mock_sys:
                app = Application()
                mock_sys.excepthook = app._excepthook

    def test_init_creates_directory_service(self):
        """Test that initialization creates directory service."""
        with patch('pyrox.models.application.PlatformDirectoryService') as mock_service_class:
            mock_service_class.return_value = self.mock_directory_service
            app = Application()
            self.assertEqual(app.directory_service, self.mock_directory_service)

    def test_tk_app_property_getter(self):
        """Test tk_app property getter."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._tk_app = self.mock_tk
            result = app.tk_app
            self.assertEqual(result, self.mock_tk)

    def test_tk_app_property_not_tk_raises_error(self):
        """Test tk_app property raises error when not Tk instance."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._tk_app = "not_a_tk"
            with self.assertRaises(RuntimeError) as context:
                _ = app.tk_app
            self.assertIn("Applications only support Tk class functionality", str(context.exception))

    def test_directory_service_property(self):
        """Test directory_service property getter."""
        with patch('pyrox.models.application.PlatformDirectoryService') as mock_service_class:
            mock_service_class.return_value = self.mock_directory_service
            app = Application()
            self.assertEqual(app.directory_service, self.mock_directory_service)

    def test_frame_property(self):
        """Test frame property getter."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._frame = self.mock_frame
            result = app.frame
            self.assertEqual(result, self.mock_frame)

    def test_menu_property(self):
        """Test menu property getter."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._menu = self.mock_menu
            result = app.menu
            self.assertEqual(result, self.mock_menu)

    def test_multi_stream_property(self):
        """Test multi_stream property getter."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._multi_stream = self.mock_multi_stream
            result = app.multi_stream
            self.assertEqual(result, self.mock_multi_stream)

    @patch('pyrox.models.application.EnvManager')
    @patch('pyrox.models.application.Path')
    def test_build_app_icon_existing_file(self, mock_path_class, mock_env):
        """Test _build_app_icon with existing icon file."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_icon_path = MagicMock()
            mock_icon_path.exists.return_value = True
            mock_path_class.return_value = mock_icon_path
            mock_env.get.return_value = '/path/to/icon.ico'

            app = Application()
            app._tk_app = self.mock_tk

            app._build_app_icon()

            self.mock_tk.iconbitmap.assert_called_with(default=mock_icon_path)

    @patch('pyrox.models.application.EnvManager')
    @patch('pyrox.models.application.Path')
    def test_build_app_icon_missing_file(self, mock_path_class, mock_env):
        """Test _build_app_icon with missing icon file."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_icon_path = MagicMock()
            mock_icon_path.exists.return_value = False
            mock_path_class.return_value = mock_icon_path
            mock_env.get.return_value = '/path/to/nonexistent.ico'

            app = Application()
            app._tk_app = self.mock_tk

            with patch.object(app, 'log') as mock_log:
                mock_logger = MagicMock()
                mock_log.return_value = mock_logger

                app._build_app_icon()

                mock_logger.warning.assert_called_once()

    @patch('pyrox.models.application.EnvManager')
    def test_build_env_not_loaded_raises_error(self, mock_env):
        """Test _build_env when environment is not loaded."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_env.is_loaded.return_value = False

            app = Application()

            with self.assertRaises(RuntimeError) as context:
                app._build_env()

            self.assertIn("Environment variables have not been loaded", str(context.exception))

    @patch('pyrox.models.application.EnvManager')
    def test_build_env_sets_logging_level(self, mock_env):
        """Test _build_env sets logging level."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_env.is_loaded.return_value = True
            mock_env.get.return_value = 'DEBUG'

            app = Application()

            with patch.object(app, 'set_logging_level') as mock_set_level:
                app._build_env()

                mock_set_level.assert_called_once_with('DEBUG')

    @patch('pyrox.models.application.Frame')
    def test_build_frame(self, mock_frame_class):
        """Test _build_frame method."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_frame_class.return_value = self.mock_frame

            app = Application()
            app._tk_app = self.mock_tk

            app._build_frame()

            mock_frame_class.assert_called_once_with(master=self.mock_tk, background='#2b2b2b')
            self.mock_frame.pack.assert_called_once_with(fill='both', expand=True)
            self.assertEqual(app._frame, self.mock_frame)

    @patch('pyrox.models.application.MainApplicationMenu')
    def test_build_menu(self, mock_menu_class):
        """Test _build_menu method."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_menu_class.return_value = self.mock_menu

            app = Application()
            app._tk_app = self.mock_tk

            app._build_menu()

            mock_menu_class.assert_called_once_with(self.mock_tk)
            self.assertEqual(app._menu, self.mock_menu)

    @patch('pyrox.models.application.stream')
    @patch('pyrox.models.application.LoggingManager')
    def test_build_multi_stream_success(self, mock_logging_manager, mock_stream):
        """Test _build_multi_stream method success."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_multistream = MagicMock()
            mock_stream.MultiStream.return_value = mock_multistream
            mock_stream.SimpleStream.return_value = MagicMock()

            app = Application()
            app._directory_service = self.mock_directory_service

            with patch.object(app, 'log') as mock_log:
                mock_logger = MagicMock()
                mock_log.return_value = mock_logger

                app._build_multi_stream()

                self.assertEqual(app._multi_stream, mock_multistream)
                mock_logging_manager.register_callback_to_captured_streams.assert_called_once()

    @patch('pyrox.models.application.stream')
    def test_build_multi_stream_already_exists(self, mock_stream):
        """Test _build_multi_stream when already set up."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._multi_stream = self.mock_multi_stream

            with self.assertRaises(RuntimeError) as context:
                app._build_multi_stream()

            self.assertIn("MultiStream has already been set up", str(context.exception))

    @patch('pyrox.models.application.stream')
    def test_build_multi_stream_exception(self, mock_stream):
        """Test _build_multi_stream method handles exceptions."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_stream.MultiStream.side_effect = Exception("Stream error")

            app = Application()
            app._directory_service = self.mock_directory_service

            with self.assertRaises(RuntimeError) as context:
                app._build_multi_stream()

            self.assertIn("Failed to set up MultiStream", str(context.exception))

    @patch('pyrox.models.application.Tk')
    def test_build_tk_app_instance(self, mock_tk_class):
        """Test _build_tk_app_instance method."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_tk_class.return_value = self.mock_tk

            app = Application()

            app._build_tk_app_instance()

            mock_tk_class.assert_called_once()
            self.mock_tk.bind.assert_any_call('<Configure>', app._on_tk_configure)
            self.assertEqual(app._tk_app, self.mock_tk)

    @patch('pyrox.models.application.EnvManager')
    def test_connect_tk_attributes(self, mock_env):
        """Test _connect_tk_attributes method."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_env.get.return_value = 'Test Window'

            app = Application()
            app._tk_app = self.mock_tk

            app._connect_tk_attributes()

            self.assertEqual(self.mock_tk.report_callback_exception, app._excepthook)
            self.mock_tk.protocol.assert_called_once_with('WM_DELETE_WINDOW', app.close)
            self.mock_tk.title.assert_called_once_with('Test Window')

    def test_excepthook_keyboard_interrupt(self):
        """Test _excepthook with KeyboardInterrupt."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()

            # Should return None for KeyboardInterrupt
            result = app._excepthook(KeyboardInterrupt, KeyboardInterrupt(), None)
            self.assertIsNone(result)

    def test_excepthook_other_exception(self):
        """Test _excepthook with other exceptions."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()

            with patch.object(app, 'log') as mock_log:
                mock_logger = MagicMock()
                mock_log.return_value = mock_logger

                app._excepthook(ValueError, ValueError("test error"), None)

                mock_logger.error.assert_called_once()

    def test_on_tk_configure_wrong_widget(self):
        """Test _on_tk_configure with wrong widget."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._tk_app = self.mock_tk

            mock_event = MagicMock()
            mock_event.widget = MagicMock()  # Not a Tk instance

            # Should return early without doing anything
            with patch.object(app, '_set_geometry_env') as mock_set_geom:
                app._on_tk_configure(mock_event)
                mock_set_geom.assert_not_called()

    def test_on_tk_configure_correct_widget(self):
        """Test _on_tk_configure with correct widget."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._tk_app = self.mock_tk

            mock_event = MagicMock()
            mock_event.widget = self.mock_tk

            with patch.object(app, '_set_geometry_env') as mock_set_geom:
                app._on_tk_configure(mock_event)
                mock_set_geom.assert_called_once()

    @patch('pyrox.models.application.EnvManager')
    def test_restore_fullscreen_true(self, mock_env):
        """Test _restore_fullscreen with True value."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_env.get.return_value = True

            app = Application()

            with patch.object(app, 'toggle_fullscreen') as mock_toggle:
                app._restore_fullscreen()
                mock_toggle.assert_called_once_with(True)

    @patch('pyrox.models.application.EnvManager')
    def test_restore_fullscreen_invalid_type(self, mock_env):
        """Test _restore_fullscreen with invalid type."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_env.get.return_value = "not_a_bool"

            app = Application()

            with self.assertRaises(ValueError) as context:
                app._restore_fullscreen()
            self.assertIn("must be a boolean value", str(context.exception))

    @patch('pyrox.models.application.EnvManager')
    def test_restore_window_position_valid(self, mock_env):
        """Test _restore_window_position with valid position."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_env.get.return_value = (100, 200)

            app = Application()
            app._tk_app = self.mock_tk

            app._restore_window_position()

            self.mock_tk.geometry.assert_called_once_with('+100+200')

    @patch('pyrox.models.application.EnvManager')
    def test_restore_window_position_none(self, mock_env):
        """Test _restore_window_position with None value."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_env.get.return_value = None

            app = Application()
            app._tk_app = self.mock_tk

            app._restore_window_position()

            self.mock_tk.geometry.assert_not_called()

    @patch('pyrox.models.application.EnvManager')
    def test_restore_window_position_tcl_error(self, mock_env):
        """Test _restore_window_position handles TclError."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_env.get.return_value = (100, 200)

            app = Application()
            app._tk_app = self.mock_tk
            self.mock_tk.geometry.side_effect = TclError("Tcl error")

            with patch.object(app, 'log') as mock_log:
                mock_logger = MagicMock()
                mock_log.return_value = mock_logger

                app._restore_window_position()

                mock_logger.error.assert_called_once()

    @patch('pyrox.models.application.EnvManager')
    def test_restore_window_size_valid(self, mock_env):
        """Test _restore_window_size with valid size."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_env.get.return_value = '800x600'

            app = Application()
            app._tk_app = self.mock_tk

            app._restore_window_size()

            self.mock_tk.geometry.assert_called_once_with('800x600')

    @patch('pyrox.models.application.EnvManager')
    def test_restore_window_state_valid(self, mock_env):
        """Test _restore_window_state with valid state."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_env.get.return_value = 'maximized'

            app = Application()
            app._tk_app = self.mock_tk

            app._restore_window_state()

            self.mock_tk.state.assert_called_once_with('maximized')

    def test_restore_geometry_env_calls_all_methods(self):
        """Test _restore_geometry_env calls all restore methods."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()

            with patch.object(app, '_restore_fullscreen') as mock_full, \
                    patch.object(app, '_restore_window_size') as mock_size, \
                    patch.object(app, '_restore_window_state') as mock_state, \
                    patch.object(app, '_restore_window_position') as mock_pos:

                app._restore_geometry_env()

                mock_full.assert_called_once()
                mock_size.assert_called_once()
                mock_state.assert_called_once()
                mock_pos.assert_called_once()

    @patch('pyrox.models.application.EnvManager')
    def test_set_fullscreen_env_valid(self, mock_env):
        """Test _set_fullscreen_env with valid boolean."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()

            app._set_fullscreen_env(True)

            mock_env.set.assert_called_once_with('UI_FULLSCREEN', 'True')

    def test_set_fullscreen_env_invalid_type(self):
        """Test _set_fullscreen_env with invalid type."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()

            with self.assertRaises(TypeError) as context:
                app._set_fullscreen_env("not_a_bool")
            self.assertIn("must be a boolean value", str(context.exception))

    @patch('pyrox.models.application.EnvManager')
    def test_set_window_position_env_valid(self, mock_env):
        """Test _set_window_position_env with valid tuple."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()

            app._set_window_position_env((100, 200))

            mock_env.set.assert_called_once_with('UI_WINDOW_POSITION', '(100, 200)')

    def test_set_window_position_env_invalid_type(self):
        """Test _set_window_position_env with invalid type."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()

            with self.assertRaises(ValueError) as context:
                app._set_window_position_env("not_a_tuple")
            self.assertIn("must be a tuple", str(context.exception))

    def test_set_window_position_env_invalid_length(self):
        """Test _set_window_position_env with invalid tuple length."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()

            with self.assertRaises(ValueError) as context:
                app._set_window_position_env((100,))  # Only one element
            self.assertIn("must be a tuple", str(context.exception))

    @patch('pyrox.models.application.EnvManager')
    def test_set_window_size_env_valid(self, mock_env):
        """Test _set_window_size_env with valid string."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()

            app._set_window_size_env('800x600')

            mock_env.set.assert_called_once_with('UI_WINDOW_SIZE', '800x600')

    def test_set_window_size_env_invalid_type(self):
        """Test _set_window_size_env with invalid type."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()

            with self.assertRaises(TypeError) as context:
                app._set_window_size_env(123)
            self.assertIn("must be a string value", str(context.exception))

    @patch('pyrox.models.application.EnvManager')
    def test_set_window_state_env_valid(self, mock_env):
        """Test _set_window_state_env with valid string."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()

            app._set_window_state_env('maximized')

            mock_env.set.assert_called_once_with('UI_WINDOW_STATE', 'maximized')

    def test_set_window_state_env_invalid_type(self):
        """Test _set_window_state_env with invalid type."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()

            with self.assertRaises(TypeError) as context:
                app._set_window_state_env(123)
            self.assertIn("must be a string value", str(context.exception))

    def test_set_geometry_env_all_parameters(self):
        """Test _set_geometry_env with all parameters."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()

            with patch.object(app, '_set_window_size_env') as mock_size, \
                    patch.object(app, '_set_window_position_env') as mock_pos, \
                    patch.object(app, '_set_window_state_env') as mock_state, \
                    patch.object(app, '_set_fullscreen_env') as mock_full:

                app._set_geometry_env('800x600', (100, 200), 'maximized', True)

                mock_size.assert_called_once_with('800x600')
                mock_pos.assert_called_once_with((100, 200))
                mock_state.assert_called_once_with('maximized')
                mock_full.assert_called_once_with(True)

    def test_application_log_method(self):
        """Test application_log method (should be overridden)."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()

            # Should not raise an error, just do nothing
            result = app.application_log("test message")
            self.assertIsNone(result)

    def test_build_method_calls_all_build_steps(self):
        """Test build method calls all build steps."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()

            with patch.object(app, '_build_env') as mock_env, \
                    patch.object(app, '_build_multi_stream') as mock_stream, \
                    patch.object(app, '_build_tk_app_instance') as mock_tk, \
                    patch.object(app, '_connect_tk_attributes') as mock_connect, \
                    patch.object(app, '_build_app_icon') as mock_icon, \
                    patch.object(app, '_build_frame') as mock_frame, \
                    patch.object(app, '_build_menu') as mock_menu, \
                    patch.object(app, '_restore_geometry_env') as mock_restore, \
                    patch('pyrox.models.application.Runnable.build') as mock_super_build:

                app._directory_service = self.mock_directory_service

                app.build()

                mock_env.assert_called_once()
                mock_stream.assert_called_once()
                mock_tk.assert_called_once()
                mock_connect.assert_called_once()
                mock_icon.assert_called_once()
                mock_frame.assert_called_once()
                mock_menu.assert_called_once()
                self.mock_directory_service.build_directory.assert_called_once()
                mock_restore.assert_called_once()
                mock_super_build.assert_called_once()

    def test_center_method(self):
        """Test center method."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._tk_app = self.mock_tk

            app.center()

            expected_x = (1920 - 800) // 2
            expected_y = (1080 - 600) // 2
            self.mock_tk.geometry.assert_called_once_with(f'+{expected_x}+{expected_y}')

    def test_clear_log_file_success(self):
        """Test clear_log_file method success."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._directory_service = self.mock_directory_service

            with patch('builtins.open', mock_open()) as mock_file:
                app.clear_log_file()

                mock_file.assert_called_once_with('/tmp/test.log', 'w', encoding='utf-8')
                mock_file().write.assert_called_once_with('')

    def test_clear_log_file_io_error(self):
        """Test clear_log_file method handles IOError."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._directory_service = self.mock_directory_service

            with patch('builtins.open', side_effect=IOError("File error")), \
                    patch('builtins.print') as mock_print:

                app.clear_log_file()

                mock_print.assert_called_once()

    @patch('pyrox.models.application.gc')
    def test_close_method_tk_instance(self, mock_gc):
        """Test close method with Tk instance."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._tk_app = self.mock_tk

            with patch.object(app, 'log') as mock_log, \
                    patch.object(app, 'stop') as mock_stop:
                mock_logger = MagicMock()
                mock_log.return_value = mock_logger

                app.close()

                mock_logger.info.assert_called_once_with('Closing application...')
                mock_stop.assert_called_once()
                self.mock_tk.quit.assert_called_once()
                self.mock_tk.destroy.assert_called_once()
                mock_gc.collect.assert_called_once()

    @patch('pyrox.models.application.gc')
    def test_close_method_not_tk_instance(self, mock_gc):
        """Test close method with non-Tk instance."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._tk_app = "not_a_tk"  # This will cause the tk_app property to raise error

            with patch.object(app, 'log') as mock_log, \
                    patch.object(app, 'stop'):
                mock_logger = MagicMock()
                mock_log.return_value = mock_logger

                # Should handle the error gracefully
                with self.assertRaises(RuntimeError):
                    app.close()

    @patch('pyrox.models.application.gc')
    def test_close_method_tcl_error(self, mock_gc):
        """Test close method handles TclError."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._tk_app = self.mock_tk
            self.mock_tk.quit.side_effect = TclError("Tcl error")

            with patch.object(app, 'log') as mock_log, \
                    patch.object(app, 'stop'):
                mock_logger = MagicMock()
                mock_log.return_value = mock_logger

                app.close()

                mock_logger.error.assert_called_once()
                mock_gc.collect.assert_called_once()

    @patch('pyrox.models.application.meta')
    def test_set_app_state_busy(self, mock_meta):
        """Test set_app_state_busy method."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()

            with patch.object(app, 'update_cursor') as mock_update:
                app.set_app_state_busy()

                mock_update.assert_called_once_with(mock_meta.TK_CURSORS.WAIT)

    @patch('pyrox.models.application.meta')
    def test_set_app_state_normal(self, mock_meta):
        """Test set_app_state_normal method."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()

            with patch.object(app, 'update_cursor') as mock_update:
                app.set_app_state_normal()

                mock_update.assert_called_once_with(mock_meta.TK_CURSORS.DEFAULT)

    @patch('pyrox.models.application.getLevelNamesMapping')
    @patch('pyrox.models.application.getLevelName')
    @patch('pyrox.models.application.LoggingManager')
    @patch('pyrox.models.application.EnvManager')
    def test_set_logging_level_string(self, mock_env, mock_logging, mock_get_name, mock_mapping):
        """Test set_logging_level with string level."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_mapping.return_value = {'DEBUG': 10, 'INFO': 20}
            mock_get_name.return_value = 'DEBUG'

            app = Application()

            with patch.object(app, 'log') as mock_log:
                mock_logger = MagicMock()
                mock_log.return_value = mock_logger

                app.set_logging_level('DEBUG')

                mock_logging.set_logging_level.assert_called_once_with(10)
                mock_env.set.assert_called_once_with('PYROX_LOG_LEVEL', 'DEBUG')

    @patch('pyrox.models.application.getLevelName')
    @patch('pyrox.models.application.LoggingManager')
    @patch('pyrox.models.application.EnvManager')
    def test_set_logging_level_integer(self, mock_env, mock_logging, mock_get_name):
        """Test set_logging_level with integer level."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_get_name.return_value = 'INFO'

            app = Application()

            with patch.object(app, 'log') as mock_log:
                mock_logger = MagicMock()
                mock_log.return_value = mock_logger

                app.set_logging_level(20)

                mock_logging.set_logging_level.assert_called_once_with(20)
                mock_env.set.assert_called_once_with('PYROX_LOG_LEVEL', 'INFO')

    @patch('pyrox.models.application.getLevelNamesMapping')
    def test_set_logging_level_invalid_string(self, mock_mapping):
        """Test set_logging_level with invalid string."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_mapping.return_value = {'DEBUG': 10, 'INFO': 20}

            app = Application()

            with self.assertRaises(ValueError) as context:
                app.set_logging_level('INVALID_LEVEL')

            self.assertIn("Invalid logging level string", str(context.exception))

    def test_set_logging_level_invalid_type(self):
        """Test set_logging_level with invalid type."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()

            with self.assertRaises(TypeError) as context:
                app.set_logging_level(['not', 'a', 'valid', 'type'])

            self.assertIn("must be an integer", str(context.exception))

    @patch('pyrox.models.application.getLevelName')
    def test_set_logging_level_invalid_integer(self, mock_get_name):
        """Test set_logging_level with invalid integer."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            mock_get_name.return_value = 'Level 999'  # Invalid level format

            app = Application()

            with self.assertRaises(ValueError) as context:
                app.set_logging_level(999)

            self.assertIn("Invalid logging level integer", str(context.exception))

    def test_start_method(self):
        """Test start method."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._tk_app = self.mock_tk

            with patch('pyrox.models.application.Runnable.start') as mock_super_start:
                app.start()

                mock_super_start.assert_called_once()
                self.mock_tk.after.assert_called_once()
                self.mock_tk.focus.assert_called_once()
                self.mock_tk.mainloop.assert_called_once()

    def test_toggle_fullscreen_explicit_true(self):
        """Test toggle_fullscreen with explicit True."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._tk_app = self.mock_tk

            app.toggle_fullscreen(True)

            self.mock_tk.attributes.assert_called_with('-fullscreen', True)

    def test_toggle_fullscreen_explicit_false(self):
        """Test toggle_fullscreen with explicit False."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._tk_app = self.mock_tk

            app.toggle_fullscreen(False)

            self.mock_tk.attributes.assert_called_with('-fullscreen', False)

    def test_toggle_fullscreen_none_toggles_state(self):
        """Test toggle_fullscreen with None toggles current state."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._tk_app = self.mock_tk
            app._runtime_info = {'full_screen': False}

            app.toggle_fullscreen(None)

            self.mock_tk.attributes.assert_called_with('-fullscreen', True)

    def test_update_cursor_with_enum(self):
        """Test update_cursor with TK_CURSORS enum."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            # Mock isinstance to return True for our mock cursor
            with patch('pyrox.models.application.isinstance') as mock_isinstance:
                mock_isinstance.return_value = True

                mock_cursor = MagicMock()
                mock_cursor.value = 'wait'

                app = Application()
                app._tk_app = self.mock_tk

                app.update_cursor(mock_cursor)

                self.mock_tk.config.assert_called_once_with(cursor='wait')
                self.mock_tk.update_idletasks.assert_called_once()

    def test_update_cursor_with_string(self):
        """Test update_cursor with string."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._tk_app = self.mock_tk

            app.update_cursor('arrow')

            self.mock_tk.config.assert_called_once_with(cursor='arrow')
            self.mock_tk.update_idletasks.assert_called_once()

    def test_update_cursor_invalid_type(self):
        """Test update_cursor with invalid type."""
        with patch('pyrox.models.application.PlatformDirectoryService'):
            app = Application()
            app._tk_app = self.mock_tk

            with self.assertRaises(TypeError) as context:
                app.update_cursor(123)  # type: ignore

            self.assertIn("must be a string", str(context.exception))


if __name__ == '__main__':
    unittest.main()

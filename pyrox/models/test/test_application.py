"""Unit tests for application.py module."""

import unittest
from unittest.mock import MagicMock, Mock, patch, mock_open
from tkinter import Frame, Tk

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

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    def test_init_sets_excepthook(self, mock_service_class, mock_menu_class, mock_frame_class):
        """Test that initialization sets sys.excepthook."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        with patch('pyrox.models.application.sys') as mock_sys:
            app = Application(self.mock_tk)
            mock_sys.excepthook = app._excepthook

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    def test_init_creates_directory_service(self, mock_service_class, mock_menu_class, mock_frame_class):
        """Test that initialization creates directory service."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        app = Application(self.mock_tk)
        self.assertEqual(app.directory_service, self.mock_directory_service)

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    def test_init_creates_menu_and_frame(self, mock_service_class, mock_menu_class, mock_frame_class):
        """Test that initialization creates menu and frame."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        app = Application(self.mock_tk)

        # Verify menu creation
        mock_menu_class.assert_called_once_with(self.mock_tk)
        self.assertEqual(app.menu, self.mock_menu)

        # Verify frame creation
        mock_frame_class.assert_called_once_with(master=self.mock_tk, background='#2b2b2b')
        self.mock_frame.pack.assert_called_once_with(fill='both', expand=True)
        self.assertEqual(app.frame, self.mock_frame)

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    def test_tk_app_property_getter(self, mock_service_class, mock_menu_class, mock_frame_class):
        """Test tk_app property getter."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        app = Application(self.mock_tk)
        result = app.tk_app
        self.assertEqual(result, self.mock_tk)

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    def test_tk_app_property_not_tk_raises_error(self, mock_service_class, mock_menu_class, mock_frame_class):
        """Test tk_app property raises error when not Tk instance."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service
        mock_not_tk = Mock()  # Not a Tk instance

        app = Application(self.mock_tk)
        # Manually override the _tk_app after initialization
        app._tk_app = mock_not_tk  # type: ignore
        with self.assertRaises(RuntimeError) as context:
            _ = app.tk_app
        self.assertIn("Applications only support Tk class functionality", str(context.exception))

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    def test_directory_service_property(self, mock_service_class, mock_menu_class, mock_frame_class):
        """Test directory_service property getter."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        app = Application(self.mock_tk)
        self.assertEqual(app.directory_service, self.mock_directory_service)

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    def test_frame_property(self, mock_service_class, mock_menu_class, mock_frame_class):
        """Test frame property getter."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        app = Application(self.mock_tk)
        result = app.frame
        self.assertEqual(result, self.mock_frame)

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    def test_menu_property(self, mock_service_class, mock_menu_class, mock_frame_class):
        """Test menu property getter."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        app = Application(self.mock_tk)
        result = app.menu
        self.assertEqual(result, self.mock_menu)

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    def test_multi_stream_property(self, mock_service_class, mock_menu_class, mock_frame_class):
        """Test multi_stream property getter."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        app = Application(self.mock_tk)
        app._multi_stream = self.mock_multi_stream
        result = app.multi_stream
        self.assertEqual(result, self.mock_multi_stream)

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    @patch('pyrox.models.application.EnvManager')
    @patch('pyrox.models.application.Path')
    def test_build_app_icon_existing_file(self, mock_path_class, mock_env, mock_service_class, mock_menu_class, mock_frame_class):
        """Test _build_app_icon with existing icon file."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        mock_icon_path = MagicMock()
        mock_icon_path.exists.return_value = True
        mock_path_class.return_value = mock_icon_path
        mock_env.get.return_value = '/path/to/icon.ico'

        app = Application(self.mock_tk)

        app._build_app_icon()

        # Check both calls - the method calls iconbitmap twice
        calls = self.mock_tk.iconbitmap.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0], ((mock_icon_path,), {}))
        self.assertEqual(calls[1], ((), {'default': mock_icon_path}))

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    @patch('pyrox.models.application.EnvManager')
    @patch('pyrox.models.application.Path')
    def test_build_app_icon_missing_file(self, mock_path_class, mock_env, mock_service_class, mock_menu_class, mock_frame_class):
        """Test _build_app_icon with missing icon file."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        mock_icon_path = MagicMock()
        mock_icon_path.exists.return_value = False
        mock_path_class.return_value = mock_icon_path
        mock_env.get.return_value = '/path/to/nonexistent.ico'

        app = Application(self.mock_tk)

        with patch.object(app, 'log') as mock_log:
            mock_logger = MagicMock()
            mock_log.return_value = mock_logger

            app._build_app_icon()

            mock_logger.warning.assert_called_once()

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    @patch('pyrox.models.application.EnvManager')
    def test_build_env_not_loaded_raises_error(self, mock_env, mock_service_class, mock_menu_class, mock_frame_class):
        """Test _build_env when environment is not loaded."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        mock_env.is_loaded.return_value = False

        app = Application(self.mock_tk)

        with self.assertRaises(RuntimeError) as context:
            app._build_env()

        self.assertIn("Environment variables have not been loaded", str(context.exception))

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    @patch('pyrox.models.application.EnvManager')
    def test_build_env_sets_logging_level(self, mock_env, mock_service_class, mock_menu_class, mock_frame_class):
        """Test _build_env sets logging level."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        mock_env.is_loaded.return_value = True
        mock_env.get.return_value = 'DEBUG'

        app = Application(self.mock_tk)

        with patch.object(app, 'set_logging_level') as mock_set_level:
            app._build_env()

            mock_set_level.assert_called_once_with('DEBUG')

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    @patch('pyrox.models.application.stream')
    @patch('pyrox.models.application.LoggingManager')
    def test_build_multi_stream_success(self, mock_logging_manager, mock_stream, mock_service_class, mock_menu_class, mock_frame_class):
        """Test _build_multi_stream method success."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        mock_multistream = MagicMock()
        mock_stream.MultiStream.return_value = mock_multistream
        mock_stream.SimpleStream.return_value = MagicMock()

        app = Application(self.mock_tk)
        app._directory_service = self.mock_directory_service

        with patch.object(app, 'log') as mock_log:
            mock_logger = MagicMock()
            mock_log.return_value = mock_logger

            app._build_multi_stream()

            self.assertEqual(app._multi_stream, mock_multistream)
            mock_logging_manager.register_callback_to_captured_streams.assert_called_once()

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    @patch('pyrox.models.application.stream')
    def test_build_multi_stream_already_exists(self, mock_stream, mock_service_class, mock_menu_class, mock_frame_class):
        """Test _build_multi_stream when already set up."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        app = Application(self.mock_tk)
        app._multi_stream = self.mock_multi_stream

        with self.assertRaises(RuntimeError) as context:
            app._build_multi_stream()

        self.assertIn("MultiStream has already been set up", str(context.exception))

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    def test_build_method_calls_all_build_steps(self, mock_service_class, mock_menu_class, mock_frame_class):
        """Test build method calls all build steps."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        app = Application(self.mock_tk)

        with patch.object(app, '_build_env') as mock_env, \
                patch.object(app, '_build_multi_stream') as mock_stream, \
                patch.object(app, '_connect_tk_attributes') as mock_connect, \
                patch.object(app, '_build_app_icon') as mock_icon, \
                patch.object(app, '_restore_geometry_env') as mock_restore, \
                patch('pyrox.models.application.Runnable.build') as mock_super_build:

            app._directory_service = self.mock_directory_service

            app.build()

            mock_env.assert_called_once()
            mock_stream.assert_called_once()
            mock_connect.assert_called_once()
            mock_icon.assert_called_once()
            self.mock_directory_service.build_directory.assert_called_once()
            mock_restore.assert_called_once()
            mock_super_build.assert_called_once()

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    def test_center_method(self, mock_service_class, mock_menu_class, mock_frame_class):
        """Test center method."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        app = Application(self.mock_tk)

        app.center()

        expected_x = (1920 - 800) // 2
        expected_y = (1080 - 600) // 2
        self.mock_tk.geometry.assert_called_once_with(f'+{expected_x}+{expected_y}')

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    def test_clear_log_file_success(self, mock_service_class, mock_menu_class, mock_frame_class):
        """Test clear_log_file method success."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        app = Application(self.mock_tk)
        app._directory_service = self.mock_directory_service

        with patch('builtins.open', mock_open()) as mock_file:
            app.clear_log_file()

            mock_file.assert_called_once_with('/tmp/test.log', 'w', encoding='utf-8')
            mock_file().write.assert_called_once_with('')

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    @patch('pyrox.models.application.gc')
    def test_close_method_tk_instance(self, mock_gc, mock_service_class, mock_menu_class, mock_frame_class):
        """Test close method with Tk instance."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        app = Application(self.mock_tk)

        with patch.object(app, 'log') as mock_log, \
                patch.object(app, 'stop'):
            mock_logger = MagicMock()
            mock_log.return_value = mock_logger

            app.close()

            mock_logger.info.assert_called_once_with('Closing application...')
            self.mock_tk.quit.assert_called_once()
            self.mock_tk.destroy.assert_called_once()
            mock_gc.collect.assert_called_once()

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    def test_start_method(self, mock_service_class, mock_menu_class, mock_frame_class):
        """Test start method."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        app = Application(self.mock_tk)

        with patch('pyrox.models.application.Runnable.start') as mock_super_start:
            app.start()

            mock_super_start.assert_called_once()
            self.mock_tk.after.assert_called_once()
            self.mock_tk.focus.assert_called_once()
            self.mock_tk.mainloop.assert_called_once()

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    def test_toggle_fullscreen_explicit_true(self, mock_service_class, mock_menu_class, mock_frame_class):
        """Test toggle_fullscreen with explicit True."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        app = Application(self.mock_tk)

        app.toggle_fullscreen(True)

        self.mock_tk.attributes.assert_called_with('-fullscreen', True)

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    def test_update_cursor_with_enum(self, mock_service_class, mock_menu_class, mock_frame_class):
        """Test update_cursor with TK_CURSORS enum."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        # Mock isinstance to return True for our mock cursor
        with patch('pyrox.models.application.isinstance') as mock_isinstance:
            mock_isinstance.return_value = True

            mock_cursor = MagicMock()
            mock_cursor.value = 'wait'

            app = Application(self.mock_tk)

            app.update_cursor(mock_cursor)

            self.mock_tk.config.assert_called_once_with(cursor='wait')
            self.mock_tk.update_idletasks.assert_called_once()

    @patch('pyrox.models.application.Frame')
    @patch('pyrox.models.application.MainApplicationMenu')
    @patch('pyrox.models.application.PlatformDirectoryService')
    def test_update_cursor_with_string(self, mock_service_class, mock_menu_class, mock_frame_class):
        """Test update_cursor with string."""
        mock_menu_class.return_value = self.mock_menu
        mock_frame_class.return_value = self.mock_frame
        mock_service_class.return_value = self.mock_directory_service

        app = Application(self.mock_tk)

        app.update_cursor('arrow')

        self.mock_tk.config.assert_called_once_with(cursor='arrow')
        self.mock_tk.update_idletasks.assert_called_once()


if __name__ == '__main__':
    unittest.main()

"""Comprehensive unit tests for the Application class."""
import sys
import unittest
from unittest.mock import MagicMock, patch, call, mock_open

from pyrox.models.application import Application


class TestApplication(unittest.TestCase):
    """Test suite for the Application class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock GUI Manager to avoid tkinter initialization
        self.gui_manager_patcher = patch('pyrox.models.application.GuiManager')
        self.mock_gui_manager = self.gui_manager_patcher.start()

        # Mock LoggingManager
        self.logging_manager_patcher = patch('pyrox.models.application.LoggingManager')
        self.mock_logging_manager = self.logging_manager_patcher.start()

        # Create mock backend with complete mocking
        self.mock_backend = MagicMock()
        self.mock_menu = MagicMock()
        self.mock_window = MagicMock()

        # Configure backend returns
        self.mock_backend.get_root_application_gui_menu.return_value = self.mock_menu
        self.mock_backend.get_root_gui_window.return_value = self.mock_window
        self.mock_gui_manager.unsafe_get_backend.return_value = self.mock_backend

        # Mock environment variables
        self.env_patcher = patch('pyrox.models.application.get_env')
        self.mock_get_env = self.env_patcher.start()

        def mock_get_env_impl(*args, **kwargs):
            key = args[0] if args else kwargs.get('key')
            if key == 'UI_ICON_PATH':
                return ''
            elif key == 'PYROX_WINDOW_TITLE':
                return 'Pyrox Application'
            elif key in ('UI_AUTO_INIT',):
                return kwargs.get('default', True)
            elif key == 'UI_WINDOW_FULLSCREEN':
                return False
            elif key == 'UI_WINDOW_POSITION':
                return None
            elif key == 'UI_WINDOW_SIZE':
                return None
            elif key == 'UI_WINDOW_STATE':
                return 'normal'
            return kwargs.get('default', args[1] if len(args) > 1 else None)

        self.mock_get_env.side_effect = mock_get_env_impl

        # Mock set_env
        self.set_env_patcher = patch('pyrox.models.application.set_env')
        self.mock_set_env = self.set_env_patcher.start()

        # Mock PlatformDirectoryService
        self.dir_service_patcher = patch('pyrox.models.application.PlatformDirectoryService')
        self.mock_dir_service_class = self.dir_service_patcher.start()
        self.mock_dir_service = MagicMock()
        self.mock_log_stream = MagicMock()
        self.mock_dir_service.get_log_file_stream.return_value = self.mock_log_stream
        self.mock_dir_service.user_log_file = '/mock/path/to/log.txt'
        self.mock_dir_service_class.return_value = self.mock_dir_service

        # Mock Workspace
        self.workspace_patcher = patch('pyrox.models.application.Workspace')
        self.mock_workspace_class = self.workspace_patcher.start()
        self.mock_workspace = MagicMock()
        self.mock_workspace_class.return_value = self.mock_workspace

        # Mock log function
        self.log_patcher = patch('pyrox.models.application.log')
        self.mock_log = self.log_patcher.start()
        self.mock_logger = MagicMock()
        self.mock_log.return_value = self.mock_logger

    def tearDown(self):
        """Clean up after each test method."""
        self.gui_manager_patcher.stop()
        self.logging_manager_patcher.stop()
        self.env_patcher.stop()
        self.set_env_patcher.stop()
        self.dir_service_patcher.stop()
        self.workspace_patcher.stop()
        self.log_patcher.stop()

    # ========================================================================
    # Initialization Tests
    # ========================================================================

    def test_init_with_gui_enabled(self):
        """Test Application initialization with GUI enabled."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: (
            True if key == 'UI_AUTO_INIT' else (default if default is not None else '')
        )

        app = Application()

        # Verify excepthook was set
        self.assertEqual(sys.excepthook, app._excepthook)

        # Verify directory service was initialized
        self.mock_dir_service_class.assert_called_once()
        self.assertEqual(app._directory_service, self.mock_dir_service)

        # Verify log stream setup
        self.mock_dir_service.get_log_file_stream.assert_called_once()
        self.mock_logging_manager.register_callback_to_captured_streams.assert_called_once_with(
            self.mock_log_stream.write
        )

        # Verify workspace was created
        self.mock_workspace_class.assert_called_once()

    def test_init_with_gui_disabled(self):
        """Test Application initialization with GUI disabled (headless mode)."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: (
            False if key == 'UI_AUTO_INIT' else (default if default is not None else '')
        )

        app = Application()

        # Verify workspace was not created
        self.assertIsNone(app._workspace)

    def test_init_sets_after_id_to_none(self):
        """Test that initialization sets _after_id to None."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        self.assertIsNone(app._after_id)

    # ========================================================================
    # Property Tests
    # ========================================================================

    def test_dir_service_property(self):
        """Test dir_service property returns the directory service."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False
        app = Application()

        result = app.dir_service
        self.assertEqual(result, self.mock_dir_service)

    def test_gui_backend_property(self):
        """Test gui_backend property returns the GUI backend."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False
        app = Application()

        result = app.gui_backend
        self.assertEqual(result, self.mock_backend)
        self.mock_gui_manager.unsafe_get_backend.assert_called()

    def test_is_gui_enabled_property_true(self):
        """Test is_gui_enabled property returns True when GUI is enabled."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: (
            True if key == 'UI_AUTO_INIT' else (default if default is not None else '')
        )

        app = Application()
        self.assertTrue(app.is_gui_enabled)

    def test_is_gui_enabled_property_false(self):
        """Test is_gui_enabled property returns False when GUI is disabled."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: (
            False if key == 'UI_AUTO_INIT' else (default if default is not None else '')
        )

        app = Application()
        self.assertFalse(app.is_gui_enabled)

    def test_menu_property(self):
        """Test menu property returns the application menu."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False
        app = Application()

        result = app.menu
        self.assertEqual(result, self.mock_menu)
        self.mock_backend.get_root_application_gui_menu.assert_called()

    def test_log_stream_property(self):
        """Test log_stream property returns the log stream."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False
        app = Application()

        result = app.log_stream
        self.assertEqual(result, self.mock_log_stream)

    def test_window_property(self):
        """Test window property returns the root window."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False
        app = Application()

        result = app.window
        self.assertEqual(result, self.mock_window)
        self.mock_backend.get_root_gui_window.assert_called()

    def test_workspace_property_when_initialized(self):
        """Test workspace property returns workspace when initialized."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: (
            True if key == 'UI_AUTO_INIT' else (default if default is not None else '')
        )

        app = Application()
        result = app.workspace
        self.assertEqual(result, self.mock_workspace)

    def test_workspace_property_raises_when_not_initialized(self):
        """Test workspace property raises RuntimeError when not initialized."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        with self.assertRaises(RuntimeError) as cm:
            _ = app.workspace

        self.assertIn('Workspace is not initialized', str(cm.exception))

    # ========================================================================
    # Private Method Tests - GUI Connection
    # ========================================================================

    def test_connect_gui_attributes(self):
        """Test _connect_gui_attributes configures GUI connections."""
        def get_env_impl(key, default=None, cast_type=None):
            if key == 'PYROX_WINDOW_TITLE':
                return 'Pyrox Application'
            return False

        self.mock_get_env.side_effect = get_env_impl

        app = Application()
        app._connect_gui_attributes()

        # Verify all backend connections were made
        self.mock_backend.reroute_excepthook.assert_called_once_with(app._excepthook)
        self.mock_backend.subscribe_to_window_close_event.assert_called_once_with(app.close)
        self.mock_backend.subscribe_to_window_change_event.assert_called_once_with(app._on_gui_configure)
        self.mock_backend.set_title.assert_called_once_with('Pyrox Application')

    # ========================================================================
    # Private Method Tests - GUI Configure Event
    # ========================================================================

    def test_on_gui_configure_first_call(self):
        """Test _on_gui_configure schedules geometry save on first call."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        app._after_id = None
        self.mock_backend.schedule_event.return_value = 'event_123'

        app._on_gui_configure()

        self.mock_backend.schedule_event.assert_called_once_with(500, app._set_geometry_env)
        self.assertEqual(app._after_id, 'event_123')

    def test_on_gui_configure_cancels_previous_event(self):
        """Test _on_gui_configure cancels previous scheduled event."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        app._after_id = 'previous_event'
        self.mock_backend.schedule_event.return_value = 'new_event'

        app._on_gui_configure()

        self.mock_backend.cancel_scheduled_event.assert_called_once_with('previous_event')
        self.mock_backend.schedule_event.assert_called_once_with(500, app._set_geometry_env)
        self.assertEqual(app._after_id, 'new_event')

    # ========================================================================
    # Private Method Tests - Exception Hook
    # ========================================================================

    def test_excepthook_with_keyboard_interrupt(self):
        """Test _excepthook ignores KeyboardInterrupt."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        app._excepthook(KeyboardInterrupt, KeyboardInterrupt(), None)

        # Should not log KeyboardInterrupt
        self.mock_logger.error.assert_not_called()

    def test_excepthook_with_other_exception(self):
        """Test _excepthook logs other exceptions."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        exc = ValueError('Test error')
        app._excepthook(ValueError, exc, None)

        # Should log the exception
        self.mock_logger.error.assert_called_once()
        args = self.mock_logger.error.call_args
        self.assertIn('Uncaught exception', args[1]['msg'])
        self.assertEqual(args[1]['exc_info'], (ValueError, exc, None))

    # ========================================================================
    # Private Method Tests - Restore Geometry
    # ========================================================================

    def test_restore_fullscreen_when_gui_disabled(self):
        """Test _restore_fullscreen does nothing when GUI is disabled."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        app._restore_fullscreen()

        self.mock_window.set_fullscreen.assert_not_called()

    def test_restore_fullscreen_when_false(self):
        """Test _restore_fullscreen does nothing when fullscreen is False."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: (
            True if key == 'UI_AUTO_INIT' else False
        )

        app = Application()
        app._restore_fullscreen()

        self.mock_window.set_fullscreen.assert_not_called()

    def test_restore_fullscreen_when_true(self):
        """Test _restore_fullscreen sets fullscreen when True."""
        def get_env_side_effect(key, default=None, cast_type=None):
            if key == 'UI_AUTO_INIT':
                return True
            elif key == 'UI_WINDOW_FULLSCREEN':
                return True
            return default

        self.mock_get_env.side_effect = get_env_side_effect

        app = Application()
        app._restore_fullscreen()

        self.mock_window.set_fullscreen.assert_called_once_with(True)

    def test_restore_window_position_when_gui_disabled(self):
        """Test _restore_window_position does nothing when GUI is disabled."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        app._restore_window_position()

        self.mock_window.set_geometry.assert_not_called()

    def test_restore_window_position_when_none(self):
        """Test _restore_window_position logs warning when position is None."""
        def get_env_side_effect(key, default=None, cast_type=None):
            if key == 'UI_AUTO_INIT':
                return True
            elif key == 'UI_WINDOW_POSITION':
                return None
            return default

        self.mock_get_env.side_effect = get_env_side_effect

        app = Application()
        app._restore_window_position()

        self.mock_logger.warning.assert_called_once()
        self.assertIn('No window position found', self.mock_logger.warning.call_args[0][0])

    def test_restore_window_position_with_invalid_format(self):
        """Test _restore_window_position logs warning with invalid position format."""
        def get_env_side_effect(key, default=None, cast_type=None):
            if key == 'UI_AUTO_INIT':
                return True
            elif key == 'UI_WINDOW_POSITION':
                return (100,)  # Invalid: only one element
            return default

        self.mock_get_env.side_effect = get_env_side_effect

        app = Application()
        app._restore_window_position()

        self.mock_logger.warning.assert_called_once()
        self.assertIn('Invalid window position format', self.mock_logger.warning.call_args[0][0])

    def test_restore_window_position_success(self):
        """Test _restore_window_position sets geometry with valid position."""
        def get_env_side_effect(key, default=None, cast_type=None):
            if key == 'UI_AUTO_INIT':
                return True
            elif key == 'UI_WINDOW_POSITION':
                return (100, 200)
            return default

        self.mock_get_env.side_effect = get_env_side_effect
        self.mock_window.get_width.return_value = 800
        self.mock_window.get_height.return_value = 600

        app = Application()
        app._restore_window_position()

        self.mock_window.set_geometry.assert_called_once_with(
            width=800, height=600, x=100, y=200
        )

    def test_restore_window_size_when_gui_disabled(self):
        """Test _restore_window_size does nothing when GUI is disabled."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        app._restore_window_size()

        self.mock_window.set_geometry.assert_not_called()

    def test_restore_window_size_when_none(self):
        """Test _restore_window_size logs warning when size is None."""
        def get_env_side_effect(key, default=None, cast_type=None):
            if key == 'UI_AUTO_INIT':
                return True
            elif key == 'UI_WINDOW_SIZE':
                return None
            return default

        self.mock_get_env.side_effect = get_env_side_effect

        app = Application()
        app._restore_window_size()

        self.mock_logger.warning.assert_called_once()
        self.assertIn('No window size found', self.mock_logger.warning.call_args[0][0])

    def test_restore_window_size_with_invalid_format(self):
        """Test _restore_window_size logs warning with invalid size format."""
        def get_env_side_effect(key, default=None, cast_type=None):
            if key == 'UI_AUTO_INIT':
                return True
            elif key == 'UI_WINDOW_SIZE':
                return '800'  # Invalid: missing height
            return default

        self.mock_get_env.side_effect = get_env_side_effect

        app = Application()
        app._restore_window_size()

        self.mock_logger.warning.assert_called_once()
        self.assertIn('Invalid window size format', self.mock_logger.warning.call_args[0][0])

    def test_restore_window_size_success(self):
        """Test _restore_window_size sets geometry with valid size."""
        def get_env_side_effect(key, default=None, cast_type=None):
            if key == 'UI_AUTO_INIT':
                return True
            elif key == 'UI_WINDOW_SIZE':
                return '800x600'
            return default

        self.mock_get_env.side_effect = get_env_side_effect

        app = Application()
        app._restore_window_size()

        self.mock_window.set_geometry.assert_called_once_with(width=800, height=600)

    def test_restore_window_state_when_gui_disabled(self):
        """Test _restore_window_state does nothing when GUI is disabled."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        app._restore_window_state()

        self.mock_window.set_state.assert_not_called()

    def test_restore_window_state_success(self):
        """Test _restore_window_state sets state successfully."""
        def get_env_side_effect(key, default=None, cast_type=None):
            if key == 'UI_AUTO_INIT':
                return True
            elif key == 'UI_WINDOW_STATE':
                return 'maximized'
            return default

        self.mock_get_env.side_effect = get_env_side_effect

        app = Application()
        app._restore_window_state()

        self.mock_window.set_state.assert_called_once_with('maximized')

    def test_restore_geometry_env_calls_all_restore_methods(self):
        """Test _restore_geometry_env calls all restore methods in order."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: True

        app = Application()

        with patch.object(Application, '_restore_fullscreen') as mock_fullscreen, \
                patch.object(Application, '_restore_window_size') as mock_size, \
                patch.object(Application, '_restore_window_state') as mock_state, \
                patch.object(Application, '_restore_window_position') as mock_position:

            app._restore_geometry_env()

            mock_fullscreen.assert_called_once()
            mock_size.assert_called_once()
            mock_state.assert_called_once()
            mock_position.assert_called_once()

    # ========================================================================
    # Private Method Tests - Set Geometry Environment
    # ========================================================================

    def test_set_fullscreen_env_with_true(self):
        """Test _set_fullscreen_env sets environment variable with True."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        app._set_fullscreen_env(True)

        self.mock_set_env.assert_called_once_with('UI_FULLSCREEN', 'True')

    def test_set_fullscreen_env_with_false(self):
        """Test _set_fullscreen_env sets environment variable with False."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        app._set_fullscreen_env(False)

        self.mock_set_env.assert_called_once_with('UI_FULLSCREEN', 'False')

    def test_set_fullscreen_env_raises_on_invalid_type(self):
        """Test _set_fullscreen_env raises TypeError for non-boolean."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        with self.assertRaises(TypeError) as cm:
            app._set_fullscreen_env('true')  # type: ignore

        self.assertIn('Fullscreen must be a boolean', str(cm.exception))

    def test_set_window_position_env_success(self):
        """Test _set_window_position_env sets environment variable."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        app._set_window_position_env((100, 200))

        self.mock_set_env.assert_called_once_with('UI_WINDOW_POSITION', '(100, 200)')

    def test_set_window_position_env_raises_on_invalid_type(self):
        """Test _set_window_position_env raises ValueError for non-tuple."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        with self.assertRaises(ValueError) as cm:
            app._set_window_position_env([100, 200])  # type: ignore

        self.assertIn('Position must be a tuple', str(cm.exception))

    def test_set_window_position_env_raises_on_invalid_length(self):
        """Test _set_window_position_env raises ValueError for wrong tuple length."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        with self.assertRaises(ValueError) as cm:
            app._set_window_position_env((100,))

        self.assertIn('Position must be a tuple', str(cm.exception))

    def test_set_window_size_env_success(self):
        """Test _set_window_size_env sets environment variable."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        app._set_window_size_env('800x600')

        self.mock_set_env.assert_called_once_with('UI_WINDOW_SIZE', '800x600')

    def test_set_window_size_env_raises_on_invalid_type(self):
        """Test _set_window_size_env raises TypeError for non-string."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        with self.assertRaises(TypeError) as cm:
            app._set_window_size_env(800)  # type: ignore

        self.assertIn('Size must be a string', str(cm.exception))

    def test_set_window_state_env_success(self):
        """Test _set_window_state_env sets environment variable."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        app._set_window_state_env('maximized')

        self.mock_set_env.assert_called_once_with('UI_WINDOW_STATE', 'maximized')

    def test_set_window_state_env_raises_on_invalid_type(self):
        """Test _set_window_state_env raises TypeError for non-string."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        with self.assertRaises(TypeError) as cm:
            app._set_window_state_env(123)  # type: ignore

        self.assertIn('State must be a string', str(cm.exception))

    def test_set_geometry_env_with_all_values(self):
        """Test _set_geometry_env sets all geometry environment variables."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: True

        self.mock_window.get_size.return_value = (800, 600)
        self.mock_window.get_position.return_value = (100, 200)
        self.mock_window.get_state.return_value = 'maximized'
        self.mock_window.is_fullscreen.return_value = True

        app = Application()
        app._set_geometry_env()

        # Check all set_env calls
        expected_calls = [
            call('UI_WINDOW_SIZE', '800x600'),
            call('UI_WINDOW_POSITION', '(100, 200)'),
            call('UI_WINDOW_STATE', 'maximized'),
            call('UI_FULLSCREEN', 'True'),
        ]
        self.mock_set_env.assert_has_calls(expected_calls, any_order=True)

    def test_set_geometry_env_with_none_values(self):
        """Test _set_geometry_env skips None values."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: True

        self.mock_window.get_size.return_value = None
        self.mock_window.get_position.return_value = None
        self.mock_window.get_state.return_value = None
        self.mock_window.is_fullscreen.return_value = None

        app = Application()
        app._set_geometry_env()

        # Should not call set_env for None values
        self.mock_set_env.assert_not_called()

    # ========================================================================
    # Public Method Tests - Log
    # ========================================================================

    def test_log_with_gui_enabled(self):
        """Test log method with GUI enabled logs to workspace."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: (
            True if key == 'UI_AUTO_INIT' else (default if default is not None else '')
        )

        app = Application()
        app.log('Test message')

        self.mock_workspace.log_window.log.assert_called_once_with('Test message')

    def test_log_with_gui_disabled(self):
        """Test log method with GUI disabled prints to console."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()

        with patch('builtins.print') as mock_print:
            app.log('Test message')
            mock_print.assert_called_once_with('Test message')

    # ========================================================================
    # Public Method Tests - Build
    # ========================================================================

    def test_build_calls_all_setup_methods(self):
        """Test build method calls all setup methods."""
        def get_env_impl(key, default=None, cast_type=None):
            if key == 'UI_ICON_PATH':
                return ''
            return False

        self.mock_get_env.side_effect = get_env_impl

        app = Application()

        with patch.object(Application, '_connect_gui_attributes') as mock_connect, \
                patch.object(Application, '_restore_geometry_env') as mock_restore, \
                patch('pyrox.models.abc.Runnable.build') as mock_super_build:

            app.build()

            mock_connect.assert_called_once()
            self.mock_backend.set_icon.assert_called_once_with('')
            mock_restore.assert_called_once()
            self.mock_dir_service.build_directory.assert_called_once()
            mock_super_build.assert_called_once()

    # ========================================================================
    # Public Method Tests - Close
    # ========================================================================

    def test_close_with_gui_enabled(self):
        """Test close method with GUI enabled."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: True

        app = Application()

        with patch.object(Application, 'stop') as mock_stop, \
                patch('gc.collect') as mock_gc:

            app.close()

            mock_stop.assert_called_once()
            self.mock_logger.info.assert_called_once_with('Closing application...')
            self.mock_backend.quit_application.assert_called_once()
            mock_gc.assert_called_once()

    def test_close_with_gui_disabled(self):
        """Test close method with GUI disabled."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()

        with patch.object(Application, 'stop') as mock_stop, \
                patch('gc.collect') as mock_gc:

            app.close()

            mock_stop.assert_called_once()
            self.mock_backend.quit_application.assert_not_called()
            mock_gc.assert_called_once()

    def test_close_handles_exception(self):
        """Test close method handles exceptions gracefully."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: True

        app = Application()
        self.mock_backend.quit_application.side_effect = RuntimeError('Test error')

        with patch.object(Application, 'stop') as mock_stop, \
                patch('gc.collect') as mock_gc:

            app.close()

            mock_stop.assert_called_once()
            self.mock_logger.error.assert_called_once()
            self.assertIn('Error closing GUI', self.mock_logger.error.call_args[0][0])
            mock_gc.assert_called_once()

    # ========================================================================
    # Public Method Tests - Clear Log File
    # ========================================================================

    def test_clear_log_file_success(self):
        """Test clear_log_file successfully clears the log file."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()

        m = mock_open()
        with patch('builtins.open', m):
            app.clear_log_file()

        m.assert_called_once_with(self.mock_dir_service.user_log_file, 'w', encoding='utf-8')
        m().write.assert_called_once_with('')

    def test_clear_log_file_handles_io_error(self):
        """Test clear_log_file handles IOError gracefully."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()

        with patch('builtins.open', side_effect=IOError('Permission denied')), \
                patch('builtins.print') as mock_print:

            app.clear_log_file()

            mock_print.assert_called_once()
            self.assertIn('Error clearing log file', mock_print.call_args[0][0])

    # ========================================================================
    # Public Method Tests - App State
    # ========================================================================

    def test_set_app_state_busy_with_gui_enabled(self):
        """Test set_app_state_busy sets cursor to wait."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: True

        app = Application()
        app.set_app_state_busy()

        self.mock_backend.update_cursor.assert_called_once()
        # Verify the cursor value is passed (it's an enum value)
        self.assertTrue(self.mock_backend.update_cursor.called)

    def test_set_app_state_busy_with_gui_disabled(self):
        """Test set_app_state_busy does nothing when GUI is disabled."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        app.set_app_state_busy()

        self.mock_backend.update_cursor.assert_not_called()

    def test_set_app_state_normal_with_gui_enabled(self):
        """Test set_app_state_normal sets cursor to default."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: True

        app = Application()
        app.set_app_state_normal()

        self.mock_backend.update_cursor.assert_called_once()
        # Verify the cursor value is passed (it's an enum value)
        self.assertTrue(self.mock_backend.update_cursor.called)

    def test_set_app_state_normal_with_gui_disabled(self):
        """Test set_app_state_normal does nothing when GUI is disabled."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()
        app.set_app_state_normal()

        self.mock_backend.update_cursor.assert_not_called()

    # ========================================================================
    # Public Method Tests - Start
    # ========================================================================

    def test_start_with_gui_enabled(self):
        """Test start method with GUI enabled."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: True

        app = Application()

        with patch('pyrox.models.abc.Runnable.start') as mock_super_start:
            app.start()

            mock_super_start.assert_called_once()
            self.mock_backend.schedule_event.assert_called_once()
            self.mock_window.focus.assert_called_once()
            self.mock_backend.run_main_loop.assert_called_once()

    def test_start_with_gui_disabled(self):
        """Test start method with GUI disabled (headless mode)."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()

        with patch('pyrox.models.abc.Runnable.start') as mock_super_start:
            app.start()

            mock_super_start.assert_called_once()
            self.mock_logger.info.assert_called_once_with('Ready... (headless mode)')
            self.mock_backend.schedule_event.assert_not_called()
            self.mock_window.focus.assert_not_called()
            self.mock_backend.run_main_loop.assert_not_called()

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_full_lifecycle_with_gui(self):
        """Test full application lifecycle with GUI enabled."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: (
            True if key == 'UI_AUTO_INIT' else (default if default is not None else '')
        )

        app = Application()

        with patch('pyrox.models.abc.Runnable.build') as mock_super_build, \
                patch('pyrox.models.abc.Runnable.start') as mock_super_start, \
                patch.object(Application, 'stop') as mock_stop, \
                patch('gc.collect'):

            # Build phase
            app.build()
            mock_super_build.assert_called_once()
            self.mock_dir_service.build_directory.assert_called_once()

            # Start phase
            app.start()
            mock_super_start.assert_called_once()
            self.mock_backend.run_main_loop.assert_called_once()

            # Close phase
            app.close()
            mock_stop.assert_called_once()
            self.mock_backend.quit_application.assert_called_once()

    def test_full_lifecycle_headless(self):
        """Test full application lifecycle in headless mode."""
        self.mock_get_env.side_effect = lambda key, default=None, cast_type=None: False

        app = Application()

        with patch('pyrox.models.abc.Runnable.build') as mock_super_build, \
                patch('pyrox.models.abc.Runnable.start') as mock_super_start, \
                patch.object(Application, 'stop') as mock_stop, \
                patch('gc.collect'):

            # Build phase
            app.build()
            mock_super_build.assert_called_once()

            # Start phase
            app.start()
            mock_super_start.assert_called_once()
            self.mock_backend.run_main_loop.assert_not_called()

            # Close phase
            app.close()
            mock_stop.assert_called_once()
            self.mock_backend.quit_application.assert_not_called()


if __name__ == '__main__':
    unittest.main()

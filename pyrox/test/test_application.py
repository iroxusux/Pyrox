"""Comprehensive unit tests for the refactored Application class."""
import sys
import unittest
from io import TextIOWrapper
from unittest.mock import MagicMock, patch, mock_open

from pyrox.application import Application
from pyrox.interfaces import IApplicationTask
from pyrox.services import GuiManager, LoggingManager, EnvManager, PlatformDirectoryService


class TestApplicationBootstrap(unittest.TestCase):
    """Test cases for application bootstraping in init."""

    def setUp(self) -> None:
        self.gui_manager_patcher = patch('pyrox.models.services.GuiManager')
        self.logging_manager_patcher = patch('pyrox.models.services.LoggingManager')
        self.env_manager_patcher = patch('pyrox.models.services.EnvManager')
        self.workspace_patcher = patch('pyrox.application.Workspace')
        self.platform_dir_patcher = patch('pyrox.models.services.PlatformDirectoryService')

        self.mock_gui_manager = self.gui_manager_patcher.start()
        self.mock_logging_manager = self.logging_manager_patcher.start()
        self.mock_env_manager = self.env_manager_patcher.start()
        self.mock_workspace = self.workspace_patcher.start()
        self.mock_platform_dir = self.platform_dir_patcher.start()

        self.mock_backend = MagicMock()
        self.mock_gui_manager.unsafe_get_backend.return_value = self.mock_backend
        self.mock_log_stream = MagicMock(spec=TextIOWrapper)
        self.mock_platform_dir.get_log_file_stream.return_value = self.mock_log_stream

    def tearDown(self):
        """Clean up after tests."""
        self.gui_manager_patcher.stop()
        self.logging_manager_patcher.stop()
        self.env_manager_patcher.stop()
        self.workspace_patcher.stop()
        self.platform_dir_patcher.stop()

    def test_bootstrap_executes_without_error(self):
        """Test that _bootstrap function runs without error."""
        try:
            Application()
        except Exception as e:
            self.fail(f"_bootstrap raised an exception: {e}")


class TestApplicationInitialization(unittest.TestCase):
    """Test cases for Application initialization."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock all the service classes
        self.gui_manager_patcher = patch('pyrox.models.services.GuiManager')
        self.logging_manager_patcher = patch('pyrox.models.services.LoggingManager')
        self.env_manager_patcher = patch('pyrox.models.services.EnvManager')
        self.workspace_patcher = patch('pyrox.application.Workspace')
        self.platform_dir_patcher = patch('pyrox.models.services.PlatformDirectoryService')

        self.mock_gui_manager = self.gui_manager_patcher.start()
        self.mock_logging_manager = self.logging_manager_patcher.start()
        self.mock_env_manager = self.env_manager_patcher.start()
        self.mock_workspace = self.workspace_patcher.start()
        self.mock_platform_dir = self.platform_dir_patcher.start()

        # Create mock backend
        self.mock_backend = MagicMock()
        self.mock_gui_manager.unsafe_get_backend.return_value = self.mock_backend

        # Mock log stream
        self.mock_log_stream = MagicMock(spec=TextIOWrapper)
        self.mock_platform_dir.get_log_file_stream.return_value = self.mock_log_stream

    def tearDown(self):
        """Clean up after tests."""
        self.gui_manager_patcher.stop()
        self.logging_manager_patcher.stop()
        self.env_manager_patcher.stop()
        self.workspace_patcher.stop()
        self.platform_dir_patcher.stop()

    def test_application_initializes_with_default_parameters(self):
        """Test Application initializes with proper defaults."""
        app = Application()

        self.assertIsNotNone(app)
        self.assertIsInstance(app, Application)
        self.assertIsInstance(app.tasks, list)

    def test_application_sets_sys_excepthook(self):
        """Test that Application sets sys.excepthook to its except_hook method."""
        app = Application()

        self.assertEqual(sys.excepthook, app.except_hook)

    def test_application_registers_logging_callback(self):
        """Test that Application registers logging callback to log stream."""
        _ = Application()

        self.mock_logging_manager.register_callback_to_captured_streams.assert_called_once()
        call_args = self.mock_logging_manager.register_callback_to_captured_streams.call_args
        # Verify the write method of log_stream was passed
        self.assertIsNotNone(call_args)

    def test_application_creates_root_window_on_init(self):
        """Test that Application creates root window during initialization."""
        _ = Application()

        self.mock_backend.create_root_window.assert_called_once()

    def test_application_creates_gui_menu_on_init(self):
        """Test that Application creates GUI menu during initialization."""
        _ = Application()

        self.mock_backend.create_application_gui_menu.assert_called_once()

    def test_application_restores_window_geometry_on_init(self):
        """Test that Application restores window geometry during initialization."""
        _ = Application()

        self.mock_backend.restore_window_geometry.assert_called_once()

    def test_application_subscribes_to_window_change_event(self):
        """Test that Application subscribes to window change events."""
        _ = Application()

        self.mock_backend.subscribe_to_window_change_event.assert_called_once()

    def test_application_creates_workspace(self):
        """Test that Application creates a workspace instance."""
        _ = Application()

        self.mock_workspace.assert_called_once()

    def test_application_initializes_log_stream(self):
        """Test that Application initializes log stream correctly."""
        app = Application()

        self.assertEqual(app.log_stream, self.mock_log_stream)

    def test_application_initializes_tasks(self):
        """Test that Application initializes ApplicationTaskFactory."""
        app = Application()

        self.assertIsNotNone(app.tasks)


class TestApplicationProperties(unittest.TestCase):
    """Test cases for Application properties."""

    def setUp(self):
        """Set up test fixtures."""
        self.gui_manager_patcher = patch('pyrox.models.services.GuiManager')
        self.logging_manager_patcher = patch('pyrox.models.services.LoggingManager')
        self.env_manager_patcher = patch('pyrox.models.services.EnvManager')
        self.workspace_patcher = patch('pyrox.application.Workspace')
        self.platform_dir_patcher = patch('pyrox.models.services.PlatformDirectoryService')

        self.mock_gui_manager = self.gui_manager_patcher.start()
        self.mock_logging_manager = self.logging_manager_patcher.start()
        self.mock_env_manager = self.env_manager_patcher.start()
        self.mock_workspace = self.workspace_patcher.start()
        self.mock_platform_dir = self.platform_dir_patcher.start()

        self.mock_backend = MagicMock()
        self.mock_gui_manager.unsafe_get_backend.return_value = self.mock_backend
        self.mock_log_stream = MagicMock(spec=TextIOWrapper)
        self.mock_platform_dir.get_log_file_stream.return_value = self.mock_log_stream

        self.app = Application()

    def tearDown(self):
        """Clean up after tests."""
        self.gui_manager_patcher.stop()
        self.logging_manager_patcher.stop()
        self.env_manager_patcher.stop()
        self.workspace_patcher.stop()
        self.platform_dir_patcher.stop()

    def test_env_property_returns_env_manager_class(self):
        """Test that env property returns EnvManager class."""
        result = self.app.env

        self.assertEqual(result, self.mock_env_manager)

    def test_gui_property_returns_backend_instance(self):
        """Test that gui property returns GUI backend instance."""
        result = self.app.gui_backend

        self.assertEqual(result, self.mock_backend)
        self.mock_gui_manager.unsafe_get_backend.assert_called()

    def test_gui_mgr_property_returns_gui_manager_class(self):
        """Test that gui_mgr property returns GuiManager class."""
        result = self.app.gui

        self.assertEqual(result, self.mock_gui_manager)

    def test_logging_property_returns_logging_manager_class(self):
        """Test that logging property returns LoggingManager class."""
        result = self.app.logging

        self.assertEqual(result, self.mock_logging_manager)

    def test_directory_property_returns_platform_directory_service_class(self):
        """Test that directory property returns PlatformDirectoryService class."""
        result = self.app.directory

        self.assertEqual(result, self.mock_platform_dir)

    def test_log_stream_property_returns_log_file_stream(self):
        """Test that log_stream property returns log file stream."""
        result = self.app.log_stream

        self.assertEqual(result, self.mock_log_stream)
        self.mock_platform_dir.get_log_file_stream.assert_called()

    def test_workspace_property_returns_workspace_instance(self):
        """Test that workspace property returns workspace instance."""
        result = self.app.workspace

        self.assertIsNotNone(result)

    def test_application_built_property(self):
        """Test that application_built property works correctly."""
        self.assertFalse(self.app.built)

        # Simulate building the application
        self.app.build()

        self.assertTrue(self.app.built)


class TestApplicationMethods(unittest.TestCase):
    """Test cases for Application methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.gui_manager_patcher = patch('pyrox.models.services.GuiManager')
        self.logging_manager_patcher = patch('pyrox.models.services.LoggingManager')
        self.env_manager_patcher = patch('pyrox.models.services.EnvManager')
        self.workspace_patcher = patch('pyrox.application.Workspace')
        self.platform_dir_patcher = patch('pyrox.models.services.PlatformDirectoryService')
        self.log_patcher = patch('pyrox.models.services.LoggingManager')

        self.mock_gui_manager = self.gui_manager_patcher.start()
        self.mock_logging_manager = self.logging_manager_patcher.start()
        self.mock_env_manager = self.env_manager_patcher.start()
        self.mock_workspace_class = self.workspace_patcher.start()
        self.mock_platform_dir = self.platform_dir_patcher.start()
        self.mock_log = self.log_patcher.start()

        self.mock_backend = MagicMock()
        self.mock_gui_manager.unsafe_get_backend.return_value = self.mock_backend
        self.mock_log_stream = MagicMock(spec=TextIOWrapper)
        self.mock_platform_dir.get_log_file_stream.return_value = self.mock_log_stream

        # Create mock workspace instance
        self.mock_workspace = MagicMock()
        self.mock_workspace_class.return_value = self.mock_workspace

        self.app = Application()

    def tearDown(self):
        """Clean up after tests."""
        self.gui_manager_patcher.stop()
        self.logging_manager_patcher.stop()
        self.env_manager_patcher.stop()
        self.workspace_patcher.stop()
        self.platform_dir_patcher.stop()
        self.log_patcher.stop()

    def test_get_author_returns_author_from_environment(self):
        """Test that get_author returns author from environment."""
        self.mock_env_manager.get.return_value = 'Test Author'

        result = self.app.get_author()

        self.assertEqual(result, 'Test Author')
        self.mock_env_manager.get.assert_called()

    def test_get_author_returns_default_when_not_set(self):
        """Test that get_author returns default when not set."""
        self.mock_env_manager.get.return_value = 'Unknown Author'

        result = self.app.get_author()

        self.assertEqual(result, 'Unknown Author')

    def test_get_version_returns_version_string(self):
        """Test that get_version returns version string."""
        result = self.app.get_version()

        self.assertEqual(result, '1.0.0')

    def test_hook_to_gui_reroutes_excepthook(self):
        """Test that hook_to_gui reroutes exception hook."""
        self.app.hook_to_gui()

        self.mock_backend.reroute_excepthook.assert_called_once_with(self.app.except_hook)

    def test_hook_to_gui_subscribes_to_close_event(self):
        """Test that hook_to_gui subscribes to window close event."""
        self.app.hook_to_gui()

        self.mock_backend.subscribe_to_window_close_event.assert_called_once_with(self.app.on_close)

    def test_hook_to_gui_sets_window_title(self):
        """Test that hook_to_gui sets window title from environment."""
        self.mock_env_manager.get.return_value = 'Test Application'

        self.app.hook_to_gui()

        self.mock_backend.set_title.assert_called()

    def test_hook_to_gui_sets_window_icon(self):
        """Test that hook_to_gui sets window icon from environment."""
        self.mock_env_manager.get.return_value = '/path/to/icon.png'

        self.app.hook_to_gui()

        self.mock_backend.set_icon.assert_called()

    def test_except_hook_ignores_keyboard_interrupt(self):
        """Test that except_hook ignores KeyboardInterrupt."""
        mock_logger = MagicMock()
        self.mock_log.return_value = mock_logger

        self.app.except_hook(KeyboardInterrupt, KeyboardInterrupt(), None)  # type: ignore

        mock_logger.error.assert_not_called()

    def test_on_close_calls_garbage_collection(self):
        """Test that on_close calls garbage collection."""
        with patch('pyrox.application.gc.collect') as mock_gc:
            with patch.object(self.app, 'stop'):
                self.app.on_close()

        mock_gc.assert_called_once()

    def test_build_method_builds_workspace(self):
        """Test build method builds workspace."""
        self.app.build()

        self.mock_workspace.build.assert_called_once()

    def test_build_method_sets_building_status(self):
        """Test build method sets building status."""
        self.app.build()

        # Check that set_status was called with 'Building...'
        status_calls = [call[0][0] for call in self.mock_workspace.set_status.call_args_list]
        self.assertIn('Building...', status_calls)

    def test_build_method_sets_ready_status(self):
        """Test build method sets ready status at the end."""
        self.app.build()

        # Check that final call was 'Ready.'
        final_call = self.mock_workspace.set_status.call_args_list[-1][0][0]
        self.assertEqual(final_call, 'Ready.')

    def test_build_method_hooks_to_gui(self):
        """Test build method hooks to GUI."""
        with patch.object(self.app, 'hook_to_gui') as mock_hook:
            self.app.build()

        mock_hook.assert_called_once()

    def test_clear_log_file_clears_file_content(self):
        """Test clear_log_file clears log file content."""
        self.mock_platform_dir.get_user_log_file.return_value = '/path/to/log.txt'

        with patch('builtins.open', mock_open()) as mock_file:
            self.app.clear_log_file()

        mock_file.assert_called_once_with('/path/to/log.txt', 'w', encoding='utf-8')
        mock_file().write.assert_called_once_with('')

    def test_clear_log_file_handles_io_error(self):
        """Test clear_log_file handles IOError gracefully."""
        self.mock_platform_dir.get_user_log_file.return_value = '/path/to/log.txt'

        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with patch('builtins.print') as mock_print:
                self.app.clear_log_file()

        mock_print.assert_called_once()
        self.assertIn('Error clearing log file', mock_print.call_args[0][0])

    def test_set_app_state_busy_updates_cursor(self):
        """Test set_app_state_busy updates cursor to wait."""
        self.app.set_app_state_busy()

        self.mock_backend.update_cursor.assert_called_once()

    def test_set_app_state_normal_updates_cursor(self):
        """Test set_app_state_normal updates cursor to default."""
        self.app.set_app_state_normal()

        self.mock_backend.update_cursor.assert_called_once()

    def test_run_method_schedules_ready_event(self):
        """Test run method schedules ready log event."""
        with patch.object(self.app, 'run', wraps=self.app.run):
            self.mock_backend.run_main_loop.return_value = None

            _ = self.app.run()

        self.mock_backend.schedule_event.assert_called()

    def test_run_method_focuses_main_window(self):
        """Test run method focuses main window."""
        self.mock_backend.run_main_loop.return_value = None

        result = self.app.run()

        self.mock_backend.focus_main_window.assert_called_once()

    def test_run_method_runs_main_loop(self):
        """Test run method runs GUI main loop."""
        self.mock_backend.run_main_loop.return_value = None

        result = self.app.run()

        self.mock_backend.run_main_loop.assert_called_once()

    def test_run_method_returns_zero(self):
        """Test run method returns 0 on success."""
        self.mock_backend.run_main_loop.return_value = None

        result = self.app.run()

        self.assertEqual(result, 0)


class TestApplicationIntegration(unittest.TestCase):
    """Integration tests for Application class."""

    def setUp(self):
        """Set up test fixtures."""
        self.gui_manager_patcher = patch('pyrox.models.services.GuiManager')
        self.logging_manager_patcher = patch('pyrox.models.services.LoggingManager')
        self.env_manager_patcher = patch('pyrox.models.services.EnvManager')
        self.workspace_patcher = patch('pyrox.application.Workspace')
        self.platform_dir_patcher = patch('pyrox.models.services.PlatformDirectoryService')
        self.log_patcher = patch('pyrox.models.services.LoggingManager')

        self.mock_gui_manager = self.gui_manager_patcher.start()
        self.mock_logging_manager = self.logging_manager_patcher.start()
        self.mock_env_manager = self.env_manager_patcher.start()
        self.mock_workspace_class = self.workspace_patcher.start()
        self.mock_platform_dir = self.platform_dir_patcher.start()

        self.mock_backend = MagicMock()
        self.mock_gui_manager.unsafe_get_backend.return_value = self.mock_backend
        self.mock_log_stream = MagicMock(spec=TextIOWrapper)
        self.mock_platform_dir.get_log_file_stream.return_value = self.mock_log_stream

        self.mock_workspace = MagicMock()
        self.mock_workspace_class.return_value = self.mock_workspace

    def tearDown(self):
        """Clean up after tests."""
        self.gui_manager_patcher.stop()
        self.logging_manager_patcher.stop()
        self.env_manager_patcher.stop()
        self.workspace_patcher.stop()
        self.platform_dir_patcher.stop()

    def test_application_full_lifecycle(self):
        """Test complete application lifecycle: init -> build -> run -> close."""
        app = Application()

        # Build
        app.build()
        self.mock_workspace.build.assert_called_once()

        # Run
        result = app.run()
        self.assertEqual(result, 0)

        # Close
        with patch.object(app, 'stop'):
            app.on_close()
        self.mock_gui_manager.quit_application.assert_called()

    def test_application_service_properties_access(self):
        """Test that all service properties are accessible."""
        app = Application()

        # Test all property accessors
        self.assertIsNotNone(app.env)
        self.assertIsNotNone(app.gui)
        self.assertIsNotNone(app.gui_backend)
        self.assertIsNotNone(app.logging)
        self.assertIsNotNone(app.directory)
        self.assertIsNotNone(app.log_stream)
        self.assertIsNotNone(app.workspace)


if __name__ == '__main__':
    unittest.main(verbosity=2)

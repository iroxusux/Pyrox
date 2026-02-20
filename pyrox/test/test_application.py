"""Comprehensive unit tests for the refactored Application class."""
import sys
import unittest
from io import TextIOWrapper
from unittest.mock import MagicMock, patch

from pyrox.application import Application


class TestApplicationInitialization(unittest.TestCase):
    """Test cases for Application initialization."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock all the service classes
        self.gui_manager_patcher = patch('pyrox.application.TkGuiManager')
        self.task_factory_patcher = patch('pyrox.application.ApplicationTaskFactory')
        self.logging_manager_patcher = patch('pyrox.models.services.LoggingManager')
        self.env_manager_patcher = patch('pyrox.models.services.EnvManager')
        self.workspace_patcher = patch('pyrox.application.TkWorkspace')
        self.platform_dir_patcher = patch('pyrox.models.services.PlatformDirectoryService')

        self.mock_gui_manager = self.gui_manager_patcher.start()
        self.mock_task_factory = self.task_factory_patcher.start()
        self.mock_logging_manager = self.logging_manager_patcher.start()
        self.mock_env_manager = self.env_manager_patcher.start()
        self.mock_workspace = self.workspace_patcher.start()
        self.mock_platform_dir = self.platform_dir_patcher.start()

        self.mock_task_factory.build_tasks = MagicMock()

        # Mock log stream
        self.mock_log_stream = MagicMock(spec=TextIOWrapper)
        self.mock_platform_dir.get_log_file_stream.return_value = self.mock_log_stream

    def tearDown(self):
        """Clean up after tests."""
        self.gui_manager_patcher.stop()
        self.task_factory_patcher.stop()
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

    def test_application_creates_root_on_init(self):
        """Test that Application creates root during initialization."""
        _ = Application()

        self.mock_gui_manager.create_root.assert_called_once()

    def test_application_config_from_env_on_init(self):
        """Test that Application config_from_env during initialization."""
        _ = Application()

        self.mock_gui_manager.config_from_env.assert_called_once()

    def test_application_subscribes_to_window_change_event(self):
        """Test that Application subscribes to window change events."""
        _ = Application()

        self.mock_gui_manager.subscribe_to_window_change_event.assert_called_once()

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

    def test_application_reroutes_excepthook_on_init(self):
        """Test that Application reroutes exception hook during initialization."""
        app = Application()

        self.mock_gui_manager.reroute_excepthook.assert_called_once_with(app.except_hook)

    def test_application_subscribes_to_close_event_on_init(self):
        """Test that Application subscribes to window close event during initialization."""
        app = Application()

        self.mock_gui_manager.subscribe_to_window_close_event.assert_called_once_with(app.on_close)


class TestApplicationProperties(unittest.TestCase):
    """Test cases for Application properties."""

    def setUp(self):
        """Set up test fixtures."""
        # Both namespaces must be patched: pyrox.application for direct calls in
        # Application.__init__, and pyrox.models.services for self.gui property access.
        self.gui_manager_app_patcher = patch('pyrox.application.TkGuiManager')
        self.gui_manager_patcher = patch('pyrox.models.services.TkGuiManager')
        self.task_factory_patcher = patch('pyrox.application.ApplicationTaskFactory')
        self.logging_manager_patcher = patch('pyrox.models.services.LoggingManager')
        self.env_manager_patcher = patch('pyrox.models.services.EnvManager')
        self.workspace_patcher = patch('pyrox.application.TkWorkspace')
        self.platform_dir_patcher = patch('pyrox.models.services.PlatformDirectoryService')

        self.gui_manager_app_patcher.start()
        self.mock_gui_manager = self.gui_manager_patcher.start()
        self.mock_task_factory = self.task_factory_patcher.start()
        self.mock_logging_manager = self.logging_manager_patcher.start()
        self.mock_env_manager = self.env_manager_patcher.start()
        self.mock_workspace = self.workspace_patcher.start()
        self.mock_platform_dir = self.platform_dir_patcher.start()

        self.mock_task_factory.build_tasks = MagicMock()

        self.mock_log_stream = MagicMock(spec=TextIOWrapper)
        self.mock_platform_dir.get_log_file_stream.return_value = self.mock_log_stream

        self.app = Application()

    def tearDown(self):
        """Clean up after tests."""
        self.gui_manager_app_patcher.stop()
        self.gui_manager_patcher.stop()
        self.task_factory_patcher.stop()
        self.logging_manager_patcher.stop()
        self.env_manager_patcher.stop()
        self.workspace_patcher.stop()
        self.platform_dir_patcher.stop()

    def test_env_property_returns_env_manager_class(self):
        """Test that env property returns EnvManager class."""
        result = self.app.env

        self.assertEqual(result, self.mock_env_manager)

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
        # Both namespaces must be patched: pyrox.application for direct calls in
        # Application.__init__, and pyrox.models.services for self.gui property access.
        self.gui_manager_app_patcher = patch('pyrox.application.TkGuiManager')
        self.gui_manager_patcher = patch('pyrox.models.services.TkGuiManager')
        self.task_factory_patcher = patch('pyrox.application.ApplicationTaskFactory')
        self.logging_manager_patcher = patch('pyrox.models.services.LoggingManager')
        self.env_manager_patcher = patch('pyrox.models.services.EnvManager')
        self.workspace_patcher = patch('pyrox.application.TkWorkspace')
        self.platform_dir_patcher = patch('pyrox.models.services.PlatformDirectoryService')
        self.log_patcher = patch('pyrox.models.services.LoggingManager')

        self.gui_manager_app_patcher.start()
        self.mock_gui_manager = self.gui_manager_patcher.start()
        self.mock_task_factory = self.task_factory_patcher.start()
        self.mock_logging_manager = self.logging_manager_patcher.start()
        self.mock_env_manager = self.env_manager_patcher.start()
        self.mock_workspace_class = self.workspace_patcher.start()
        self.mock_platform_dir = self.platform_dir_patcher.start()
        self.mock_log = self.log_patcher.start()

        self.mock_task_factory.build_tasks = MagicMock()
        self.mock_log_stream = MagicMock(spec=TextIOWrapper)
        self.mock_platform_dir.get_log_file_stream.return_value = self.mock_log_stream

        # Create mock workspace instance
        self.mock_workspace = MagicMock()
        self.mock_workspace_class.return_value = self.mock_workspace

        self.app = Application()

    def tearDown(self):
        """Clean up after tests."""
        self.gui_manager_app_patcher.stop()
        self.gui_manager_patcher.stop()
        self.task_factory_patcher.stop()
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

    def test_except_hook_ignores_keyboard_interrupt(self):
        """Test that except_hook ignores KeyboardInterrupt."""
        mock_logger = MagicMock()
        self.mock_log.return_value = mock_logger

        self.app.except_hook(KeyboardInterrupt, KeyboardInterrupt(), None)  # type: ignore

        mock_logger.error.assert_not_called()

    def test_on_close_calls_stop_and_quit(self):
        """Test that on_close calls stop and quit_application."""
        with patch.object(self.app, 'stop') as mock_stop:
            self.app.on_close()

        mock_stop.assert_called_once()
        self.mock_gui_manager.quit_application.assert_called_once()

    def test_run_method_schedules_ready_event(self):
        """Test run method schedules ready log event."""
        with patch.object(self.app, 'run', wraps=self.app.run):
            self.mock_gui_manager.run_main_loop.return_value = None

            _ = self.app.run()

        self.mock_gui_manager.schedule_event.assert_called()

    def test_run_method_focuses_root(self):
        """Test run method focuses main window."""
        self.mock_gui_manager.run_main_loop.return_value = None

        _ = self.app.run()

        self.mock_gui_manager.focus_root.assert_called_once()

    def test_run_method_runs_main_loop(self):
        """Test run method runs GUI main loop."""
        self.mock_gui_manager.run_main_loop.return_value = None

        _ = self.app.run()

        self.mock_gui_manager.run_main_loop.assert_called_once()

    def test_run_method_returns_zero(self):
        """Test run method returns 0 on success."""
        self.mock_gui_manager.run_main_loop.return_value = None

        result = self.app.run()

        self.assertEqual(result, 0)


class TestApplicationIntegration(unittest.TestCase):
    """Integration tests for Application class."""

    def setUp(self):
        """Set up test fixtures."""
        # Both namespaces must be patched: pyrox.application for direct calls in
        # Application.__init__, and pyrox.models.services for self.gui property access.
        self.gui_manager_app_patcher = patch('pyrox.application.TkGuiManager')
        self.gui_manager_patcher = patch('pyrox.models.services.TkGuiManager')
        self.task_factory_patcher = patch('pyrox.application.ApplicationTaskFactory')
        self.logging_manager_patcher = patch('pyrox.models.services.LoggingManager')
        self.env_manager_patcher = patch('pyrox.models.services.EnvManager')
        self.workspace_patcher = patch('pyrox.application.TkWorkspace')
        self.platform_dir_patcher = patch('pyrox.models.services.PlatformDirectoryService')

        self.gui_manager_app_patcher.start()
        self.mock_gui_manager = self.gui_manager_patcher.start()
        self.mock_task_factory = self.task_factory_patcher.start()
        self.mock_logging_manager = self.logging_manager_patcher.start()
        self.mock_env_manager = self.env_manager_patcher.start()
        self.mock_workspace_class = self.workspace_patcher.start()
        self.mock_platform_dir = self.platform_dir_patcher.start()

        self.mock_task_factory.build_tasks = MagicMock()
        self.mock_log_stream = MagicMock(spec=TextIOWrapper)
        self.mock_platform_dir.get_log_file_stream.return_value = self.mock_log_stream

        self.mock_workspace = MagicMock()
        self.mock_workspace_class.return_value = self.mock_workspace

    def tearDown(self):
        """Clean up after tests."""
        self.gui_manager_app_patcher.stop()
        self.gui_manager_patcher.stop()
        self.task_factory_patcher.stop()
        self.logging_manager_patcher.stop()
        self.env_manager_patcher.stop()
        self.workspace_patcher.stop()
        self.platform_dir_patcher.stop()

    def test_application_full_lifecycle(self):
        """Test complete application lifecycle: init -> run -> close."""
        app = Application()

        # Verify workspace was created during init
        self.mock_workspace_class.assert_called_once()

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
        self.assertIsNotNone(app.logging)
        self.assertIsNotNone(app.directory)
        self.assertIsNotNone(app.log_stream)
        self.assertIsNotNone(app.workspace)


if __name__ == '__main__':
    unittest.main(verbosity=2)

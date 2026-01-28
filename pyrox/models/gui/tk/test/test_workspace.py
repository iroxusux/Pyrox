"""Unit tests for workspace.py module."""

from pyrox.models.gui.default.frame import TaskFrame
from pyrox.models.gui.tk.workspace import TkWorkspace
import unittest
from unittest.mock import MagicMock, patch


class TestWorkspaceInitialization(unittest.TestCase):
    """Test cases for Workspace initialization."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Set up patchers
        self.mock_tk_patcher = patch('pyrox.models.gui.tk.workspace.tk')
        self.mock_backend_patcher = patch('pyrox.models.services.GuiManager')

        # Start patchers
        self.mock_tk = self.mock_tk_patcher.start()
        self.mock_backend = self.mock_backend_patcher.start()

        self.mock_root = MagicMock()
        self.mock_backend.get_root_window.return_value = self.mock_root

        self.mock_frame = MagicMock()
        self.mock_backend.create_gui_frame.return_value = self.mock_frame

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Stop patchers
        self.mock_tk_patcher.stop()
        self.mock_backend_patcher.stop()

    def test_init_creates_required_components(self):
        """Test that initialization creates all required components."""
        # Setup mocks
        workspace = TkWorkspace()

        # Verify initialization
        self.assertEqual(workspace.get_name(), "pyroxWorkspace")
        self.assertIsNotNone(workspace._root)
        self.assertIsNone(workspace._main_paned_window)
        self.assertIsNone(workspace._sidebar_organizer)
        self.assertIsNone(workspace._workspace_area)
        self.assertIsNone(workspace._status_bar)

    def test_init_creates_empty_tracking_dicts(self):
        """Test that initialization creates empty tracking dictionaries."""
        workspace = TkWorkspace()

        self.assertEqual(len(workspace._mounted_widgets), 0)
        self.assertEqual(len(workspace._sidebar_tabs), 0)
        self.assertEqual(len(workspace._workspace_frames), 0)

    def test_init_sets_callbacks_to_none(self):
        """Test that initialization sets all callbacks to None."""
        workspace = TkWorkspace()

        self.assertIsNone(workspace.on_sidebar_toggle)
        self.assertIsNone(workspace.on_task_frame_mounted)
        self.assertIsNone(workspace.on_task_frame_unmounted)
        self.assertIsNone(workspace.on_sidebar_widget_mounted)
        self.assertIsNone(workspace.on_sidebar_widget_unmounted)
        self.assertIsNone(workspace.on_workspace_changed)


class TestWorkspaceProperties(unittest.TestCase):
    """Test cases for Workspace properties."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Set up patchers
        self.mock_tk_patcher = patch('pyrox.models.gui.tk.workspace.tk')
        self.mock_backend_patcher = patch('pyrox.models.services.GuiManager')

        # Start patchers
        self.mock_tk = self.mock_tk_patcher.start()
        self.mock_backend = self.mock_backend_patcher.start()

        self.mock_root = MagicMock()
        self.mock_backend.get_root_window.return_value = self.mock_root

        self.mock_frame = MagicMock()
        self.mock_backend.create_gui_frame.return_value = self.mock_frame

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Stop patchers
        self.mock_tk_patcher.stop()
        self.mock_backend_patcher.stop()

    def test_window_property_returns_window(self):
        """Test that window property returns the window."""
        workspace = TkWorkspace()

        self.assertIsNotNone(workspace.window)

    def test_main_paned_window_raises_when_not_initialized(self):
        """Test that main_paned_window raises error when not initialized."""
        workspace = TkWorkspace()

        with self.assertRaises(RuntimeError) as context:
            _ = workspace.main_paned_window
        self.assertIn("Main paned window not initialized", str(context.exception))

    def test_sidebar_organizer_raises_when_not_initialized(self):
        """Test that sidebar_organizer raises error when not initialized."""
        workspace = TkWorkspace()

        with self.assertRaises(RuntimeError) as context:
            _ = workspace.sidebar_organizer
        self.assertIn("Sidebar organizer not initialized", str(context.exception))

    def test_workspace_area_raises_when_not_initialized(self):
        """Test that workspace_area raises error when not initialized."""
        workspace = TkWorkspace()

        with self.assertRaises(RuntimeError) as context:
            _ = workspace.workspace_area
        self.assertIn("Workspace area not initialized", str(context.exception))

    def test_status_bar_raises_when_not_initialized(self):
        """Test that status_bar raises error when not initialized."""
        workspace = TkWorkspace()

        with self.assertRaises(RuntimeError) as context:
            _ = workspace.status_bar
        self.assertIn("Status bar not initialized", str(context.exception))


class TestWorkspaceStatusManagement(unittest.TestCase):
    """Test cases for Workspace status management."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Set up patchers
        self.mock_tk_patcher = patch('pyrox.models.gui.tk.workspace.tk')
        self.mock_backend_patcher = patch('pyrox.models.services.GuiManager')

        # Start patchers
        self.mock_tk = self.mock_tk_patcher.start()
        self.mock_backend = self.mock_backend_patcher.start()

        self.mock_root = MagicMock()
        self.mock_backend.get_root_window.return_value = self.mock_root

        self.mock_frame = MagicMock()
        self.mock_backend.create_gui_frame.return_value = self.mock_frame

        # Create a mock StringVar that actually stores values
        class MockStringVar:
            def __init__(self, value=""):
                self._value = value

            def set(self, value):
                self._value = value

            def get(self):
                return self._value

        # Configure the mock to return our MockStringVar
        self.mock_tk.StringVar.return_value = MockStringVar()

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Stop patchers
        self.mock_tk_patcher.stop()
        self.mock_backend_patcher.stop()

    def test_set_status_updates_status_text(self):
        """Test that set_status updates the status text."""

        workspace = TkWorkspace()
        workspace.set_status("Test status message")
        self.assertEqual(workspace.get_status(), "Test status message")

    def test_get_status_returns_current_status(self):
        """Test that get_status returns current status."""
        workspace = TkWorkspace()
        workspace.set_status("Initial status")
        result = workspace.get_status()
        self.assertEqual(result, "Initial status")

    def test_set_status_multiple_times(self):
        """Test setting status multiple times."""
        workspace = TkWorkspace()

        workspace.set_status("Status 1")
        workspace.set_status("Status 2")
        workspace.set_status("Status 3")

        self.assertEqual(workspace.get_status(), "Status 3")


class TestWorkspaceWidgetManagement(unittest.TestCase):
    """Test cases for Workspace widget management."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Set up patchers
        self.mock_tk_patcher = patch('pyrox.models.gui.tk.workspace.tk')
        self.mock_backend_patcher = patch('pyrox.models.services.GuiManager')

        # Start patchers
        self.mock_tk = self.mock_tk_patcher.start()
        self.mock_backend = self.mock_backend_patcher.start()

        self.mock_root = MagicMock()
        self.mock_backend.get_root_window.return_value = self.mock_root

        self.mock_frame = MagicMock()
        self.mock_backend.create_gui_frame.return_value = self.mock_frame

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Stop patchers
        self.mock_tk_patcher.stop()
        self.mock_backend_patcher.stop()

    def test_add_workspace_task_frame_raises_when_none(self):
        """Test that add_workspace_task_frame raises error when task_frame is None."""
        workspace = TkWorkspace()

        with self.assertRaises(ValueError) as context:
            workspace.add_workspace_task_frame(None)  # type: ignore
        self.assertIn("task_frame must be provided", str(context.exception))

    def test_get_widget_returns_none_when_not_found(self):
        """Test that get_widget returns None for non-existent widget."""
        workspace = TkWorkspace()

        result = workspace.get_widget("nonexistent_id")

        self.assertIsNone(result)

    def test_get_all_widget_ids_returns_organized_dict(self):
        """Test that get_all_widget_ids returns organized dictionary."""
        workspace = TkWorkspace()

        result = workspace.get_all_widget_ids()

        self.assertIn('sidebar', result)
        self.assertIn('workspace', result)
        self.assertIsInstance(result['sidebar'], list)
        self.assertIsInstance(result['workspace'], list)

    def test_remove_widget_returns_false_for_nonexistent(self):
        """Test that remove_widget returns False for non-existent widget."""
        workspace = TkWorkspace()

        result = workspace.remove_widget("nonexistent_id")

        self.assertFalse(result)


class TestWorkspaceSidebarManagement(unittest.TestCase):
    """Test cases for Workspace sidebar management."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Set up patchers
        self.mock_tk_patcher = patch('pyrox.models.gui.tk.workspace.tk')
        self.mock_backend_patcher = patch('pyrox.models.services.GuiManager')

        # Start patchers
        self.mock_tk = self.mock_tk_patcher.start()
        self.mock_backend = self.mock_backend_patcher.start()

        self.mock_root = MagicMock()
        self.mock_backend.get_root_window.return_value = self.mock_root

        self.mock_frame = MagicMock()
        self.mock_backend.create_gui_frame.return_value = self.mock_frame

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Stop patchers
        self.mock_tk_patcher.stop()
        self.mock_backend_patcher.stop()

    def test_add_sidebar_widget_raises_when_duplicate_id(self):
        """Test that add_sidebar_widget raises error for duplicate widget ID."""
        workspace = TkWorkspace()
        workspace._sidebar_organizer = MagicMock()

        # Add first widget
        mock_widget = MagicMock()
        workspace._mounted_widgets["test_id"] = mock_widget

        # Try to add duplicate
        with self.assertRaises(ValueError) as context:
            workspace.add_sidebar_widget(mock_widget, "Test Tab", widget_id="test_id")
        self.assertIn("already exists", str(context.exception))

    def test_add_sidebar_widget_generates_id_when_none(self):
        """Test that add_sidebar_widget generates ID when not provided."""
        workspace = TkWorkspace()
        workspace._sidebar_organizer = MagicMock()
        workspace._sidebar_organizer.add_frame_tab.return_value = ("tab_1", MagicMock())
        mock_frame_container = MagicMock()
        mock_frame_container.frame.root.winfo_children.return_value = []
        workspace._sidebar_organizer.get_tab_frame.return_value = mock_frame_container

        mock_widget = MagicMock()
        widget_id = workspace.add_sidebar_widget(mock_widget, "Test Tab")

        self.assertIsNotNone(widget_id)
        self.assertIn("sidebar_widget_", widget_id)

    def test_add_sidebar_widget_with_icon(self):
        """Test adding sidebar widget with icon."""
        workspace = TkWorkspace()
        workspace._sidebar_organizer = MagicMock()
        workspace._sidebar_organizer.add_frame_tab.return_value = ("tab_1", MagicMock())
        mock_frame_container = MagicMock()
        mock_frame_container.frame.root.winfo_children.return_value = []
        workspace._sidebar_organizer.get_tab_frame.return_value = mock_frame_container

        mock_widget = MagicMock()
        widget_id = workspace.add_sidebar_widget(mock_widget, "Test Tab", icon="📁")

        self.assertIsNotNone(widget_id)
        # Verify icon was included in display name
        call_args = workspace._sidebar_organizer.add_frame_tab.call_args[0]
        self.assertIn("📁", call_args[0])


class TestWorkspaceSashManagement(unittest.TestCase):
    """Test cases for Workspace sash management."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Set up patchers
        self.mock_tk_patcher = patch('pyrox.models.gui.tk.workspace.tk')
        self.mock_backend_patcher = patch('pyrox.models.services.GuiManager')

        # Start patchers
        self.mock_tk = self.mock_tk_patcher.start()
        self.mock_backend = self.mock_backend_patcher.start()

        self.mock_root = MagicMock()
        self.mock_backend.get_root_window.return_value = self.mock_root

        self.mock_frame = MagicMock()
        self.mock_backend.create_gui_frame.return_value = self.mock_frame

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Stop patchers
        self.mock_tk_patcher.stop()
        self.mock_backend_patcher.stop()

    def test_set_sidebar_width_raises_when_not_initialized(self):
        """Test that set_sidebar_width raises error when not initialized."""
        workspace = TkWorkspace()

        with self.assertRaises(RuntimeError) as context:
            workspace.set_sidebar_width(0.3)
        self.assertIn("Main paned window not initialized", str(context.exception))

    def test_set_log_window_height_raises_when_not_initialized(self):
        """Test that set_log_window_height raises error when not initialized."""
        workspace = TkWorkspace()

        with self.assertRaises(RuntimeError) as context:
            workspace.set_log_window_height(0.3)
        self.assertIn("Log paned window not initialized", str(context.exception))

    def test_subscribe_to_sash_movement_events(self):
        """Test subscribing to sash movement events."""
        workspace = TkWorkspace()

        callback = MagicMock()
        workspace.subscribe_to_sash_movement_events(callback)

        self.assertIn(callback, workspace._sash_callbacks)

    def test_on_log_sash_moved_calls_callbacks(self):
        """Test that on_log_sash_moved calls registered callbacks."""
        workspace = TkWorkspace()
        workspace._log_paned_window = MagicMock()

        callback1 = MagicMock()
        callback2 = MagicMock()
        workspace.subscribe_to_sash_movement_events(callback1)
        workspace.subscribe_to_sash_movement_events(callback2)

        mock_event = MagicMock()
        workspace.on_log_sash_moved(mock_event)

        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_on_main_sash_moved_calls_callbacks(self):
        """Test that on_main_sash_moved calls registered callbacks."""
        workspace = TkWorkspace()
        workspace._main_paned_window = MagicMock()

        callback1 = MagicMock()
        callback2 = MagicMock()
        workspace.subscribe_to_sash_movement_events(callback1)
        workspace.subscribe_to_sash_movement_events(callback2)

        mock_event = MagicMock()
        workspace.on_main_sash_moved(mock_event)

        callback1.assert_called_once()
        callback2.assert_called_once()


class TestWorkspaceClearOperations(unittest.TestCase):
    """Test cases for Workspace clear operations."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Set up patchers
        self.mock_tk_patcher = patch('pyrox.models.gui.tk.workspace.tk')
        self.mock_backend_patcher = patch('pyrox.models.services.GuiManager')

        # Start patchers
        self.mock_tk = self.mock_tk_patcher.start()
        self.mock_backend = self.mock_backend_patcher.start()

        self.mock_root = MagicMock()
        self.mock_backend.get_root_window.return_value = self.mock_root

        self.mock_frame = MagicMock()
        self.mock_backend.create_gui_frame.return_value = self.mock_frame

        # Create a mock StringVar that actually stores values
        class MockStringVar:
            def __init__(self, value=""):
                self._value = value

            def set(self, value):
                self._value = value

            def get(self):
                return self._value

        # Configure the mock to return our MockStringVar
        self.mock_tk.StringVar.return_value = MockStringVar()

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Stop patchers
        self.mock_tk_patcher.stop()
        self.mock_backend_patcher.stop()

    def test_clear_workspace_removes_all_workspace_widgets(self):
        """Test that clear_workspace removes all workspace widgets."""
        workspace = TkWorkspace()

        # Add mock widgets
        mock_frame1 = MagicMock(spec=TaskFrame)
        mock_frame1.name = "frame1"
        mock_frame1.shown = False
        workspace._workspace_frames["frame1"] = mock_frame1

        workspace.clear_workspace()

        self.assertEqual(len(workspace._workspace_frames), 0)

    def test_clear_sidebar_removes_all_sidebar_widgets(self):
        """Test that clear_sidebar removes all sidebar widgets."""
        workspace = TkWorkspace()
        workspace._sidebar_organizer = MagicMock()

        # Add mock widgets
        workspace._mounted_widgets["widget1"] = MagicMock()
        workspace._sidebar_tabs["widget1"] = "tab1"

        workspace.clear_sidebar()

        # Should attempt to remove widgets
        self.assertLessEqual(len(workspace._mounted_widgets), 1)

    def test_clear_all_clears_both_areas(self):
        """Test that clear_all clears both workspace and sidebar."""
        workspace = TkWorkspace()
        workspace._sidebar_organizer = MagicMock()

        # Add mock widgets to both areas
        mock_frame = MagicMock(spec=TaskFrame)
        mock_frame.name = "frame1"
        mock_frame.shown = False
        workspace._workspace_frames["frame1"] = mock_frame
        workspace._mounted_widgets["widget1"] = MagicMock()

        workspace.clear_all()

        # Verify status message
        self.assertIn("cleared", workspace.get_status().lower())


class TestWorkspacePanelManagement(unittest.TestCase):
    """Test cases for Workspace panel management."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Set up patchers
        self.mock_tk_patcher = patch('pyrox.models.gui.tk.workspace.tk')
        self.mock_backend_patcher = patch('pyrox.models.services.GuiManager')

        # Start patchers
        self.mock_tk = self.mock_tk_patcher.start()
        self.mock_backend = self.mock_backend_patcher.start()

        self.mock_root = MagicMock()
        self.mock_backend.get_root_window.return_value = self.mock_root

        self.mock_frame = MagicMock()
        self.mock_backend.create_gui_frame.return_value = self.mock_frame

        # Create a mock StringVar that actually stores values
        class MockStringVar:
            def __init__(self, value=""):
                self._value = value

            def set(self, value):
                self._value = value

            def get(self):
                return self._value

        # Configure the mock to return our MockStringVar
        self.mock_tk.StringVar.return_value = MockStringVar()

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Stop patchers
        self.mock_tk_patcher.stop()
        self.mock_backend_patcher.stop()

    def test_add_panel_left_position(self):
        """Test adding panel to left position."""
        workspace = TkWorkspace()
        workspace._main_paned_window = MagicMock()

        mock_panel = MagicMock()
        workspace.add_panel(mock_panel, 'left')

        workspace._main_paned_window.insert.assert_called_once_with(0, mock_panel)

    def test_add_panel_right_position(self):
        """Test adding panel to right position."""
        workspace = TkWorkspace()
        workspace._main_paned_window = MagicMock()

        mock_panel = MagicMock()
        workspace.add_panel(mock_panel, 'right')

        workspace._main_paned_window.add.assert_called_once_with(mock_panel)

    def test_add_panel_invalid_position_raises_error(self):
        """Test that adding panel with invalid position raises error."""
        workspace = TkWorkspace()
        workspace._main_paned_window = MagicMock()

        mock_panel = MagicMock()
        with self.assertRaises(ValueError) as context:
            workspace.add_panel(mock_panel, 'top')
        self.assertIn("must be 'left' or 'right'", str(context.exception))

    def test_remove_panel(self):
        """Test removing panel."""
        workspace = TkWorkspace()
        workspace._main_paned_window = MagicMock()

        mock_panel = MagicMock()
        workspace.remove_panel(mock_panel)

        workspace._main_paned_window.forget.assert_called_once_with(mock_panel)

    def test_get_panels(self):
        """Test getting all panels."""
        workspace = TkWorkspace()
        workspace._main_paned_window = MagicMock()
        mock_panes = [MagicMock(), MagicMock()]
        workspace._main_paned_window.panes.return_value = mock_panes

        result = workspace.get_panels()

        self.assertEqual(result, mock_panes)


class TestWorkspaceInfo(unittest.TestCase):
    """Test cases for Workspace information retrieval."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Set up patchers
        self.mock_tk_patcher = patch('pyrox.models.gui.tk.workspace.tk')
        self.mock_backend_patcher = patch('pyrox.models.services.GuiManager')

        # Start patchers
        self.mock_tk = self.mock_tk_patcher.start()
        self.mock_backend = self.mock_backend_patcher.start()

        self.mock_root = MagicMock()
        self.mock_backend.get_root_window.return_value = self.mock_root

        self.mock_frame = MagicMock()
        self.mock_backend.create_gui_frame.return_value = self.mock_frame

        # Create a mock StringVar that actually stores values
        class MockStringVar:
            def __init__(self, value=""):
                self._value = value

            def set(self, value):
                self._value = value

            def get(self):
                return self._value

        # Configure the mock to return our MockStringVar
        self.mock_tk.StringVar.return_value = MockStringVar()

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Stop patchers
        self.mock_tk_patcher.stop()
        self.mock_backend_patcher.stop()

    def test_get_workspace_info_returns_comprehensive_dict(self):
        """Test that get_workspace_info returns comprehensive information."""
        workspace = TkWorkspace()
        workspace._sidebar_organizer = MagicMock()
        workspace._sidebar_organizer.get_tab_count.return_value = 2
        workspace._workspace_area = MagicMock()
        workspace._workspace_area.frame.root.winfo_width.return_value = 800
        workspace._workspace_area.frame.root.winfo_height.return_value = 600

        result = workspace.get_workspace_info()

        self.assertIn('sidebar', result)
        self.assertIn('workspace', result)
        self.assertIn('status', result)
        self.assertIn('widgets', result)
        self.assertIsInstance(result['sidebar'], dict)
        self.assertIsInstance(result['workspace'], dict)

    def test_get_workspace_info_includes_widget_counts(self):
        """Test that workspace info includes widget counts."""
        workspace = TkWorkspace()
        workspace._sidebar_organizer = MagicMock()
        workspace._sidebar_organizer.get_tab_count.return_value = 3
        workspace._workspace_area = MagicMock()
        workspace._workspace_area.frame.root.winfo_width.return_value = 800
        workspace._workspace_area.frame.root.winfo_height.return_value = 600

        # Add some widgets
        workspace._mounted_widgets["w1"] = MagicMock()
        workspace._mounted_widgets["w2"] = MagicMock()
        mock_frame = MagicMock(spec=TaskFrame)
        mock_frame.name = "f1"
        workspace._workspace_frames["f1"] = mock_frame

        result = workspace.get_workspace_info()

        self.assertEqual(result['sidebar']['widget_count'], 2)
        self.assertEqual(result['workspace']['widget_count'], 1)


class TestWorkspaceCallbacks(unittest.TestCase):
    """Test cases for Workspace callback functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Set up patchers
        self.mock_tk_patcher = patch('pyrox.models.gui.tk.workspace.tk')
        self.mock_backend_patcher = patch('pyrox.models.services.GuiManager')

        # Start patchers
        self.mock_tk = self.mock_tk_patcher.start()
        self.mock_backend = self.mock_backend_patcher.start()

        self.mock_root = MagicMock()
        self.mock_backend.get_root_window.return_value = self.mock_root

        self.mock_frame = MagicMock()
        self.mock_backend.create_gui_frame.return_value = self.mock_frame

        # Create a mock StringVar that actually stores values
        class MockStringVar:
            def __init__(self, value=""):
                self._value = value

            def set(self, value):
                self._value = value

            def get(self):
                return self._value

        # Configure the mock to return our MockStringVar
        self.mock_tk.StringVar.return_value = MockStringVar()

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Stop patchers
        self.mock_tk_patcher.stop()
        self.mock_backend_patcher.stop()

    def test_on_sidebar_toggle_callback_called_on_show(self):
        """Test that on_sidebar_toggle callback is called when showing sidebar."""
        workspace = TkWorkspace()
        workspace._main_paned_window = MagicMock()
        workspace._sidebar_organizer = MagicMock()
        workspace.sidebar_visible = False

        callback = MagicMock()
        workspace.on_sidebar_toggle = callback

        workspace.show_sidebar()

        callback.assert_called_once_with(True)

    def test_on_sidebar_toggle_callback_called_on_hide(self):
        """Test that on_sidebar_toggle callback is called when hiding sidebar."""
        workspace = TkWorkspace()
        workspace._main_paned_window = MagicMock()
        workspace._sidebar_organizer = MagicMock()
        workspace.sidebar_visible = True

        callback = MagicMock()
        workspace.on_sidebar_toggle = callback

        workspace.hide_sidebar()

        callback.assert_called_once_with(False)

    def test_callback_error_handling(self):
        """Test that callback errors are handled gracefully."""
        workspace = TkWorkspace()
        workspace._main_paned_window = MagicMock()
        workspace._sidebar_organizer = MagicMock()
        workspace.sidebar_visible = False

        # Set callback that raises exception
        def error_callback(visible):
            raise Exception("Test error")

        workspace.on_sidebar_toggle = error_callback

        # Should not raise exception
        try:
            workspace.show_sidebar()
        except Exception:
            self.fail("Exception should have been caught")


class TestWorkspaceToggleSidebar(unittest.TestCase):
    """Test cases for Workspace sidebar toggle functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Set up patchers
        self.mock_tk_patcher = patch('pyrox.models.gui.tk.workspace.tk')
        self.mock_backend_patcher = patch('pyrox.models.services.GuiManager')

        # Start patchers
        self.mock_tk = self.mock_tk_patcher.start()
        self.mock_backend = self.mock_backend_patcher.start()

        self.mock_root = MagicMock()
        self.mock_backend.get_root_window.return_value = self.mock_root

        self.mock_frame = MagicMock()
        self.mock_backend.create_gui_frame.return_value = self.mock_frame

        # Create a mock StringVar that actually stores values
        class MockStringVar:
            def __init__(self, value=""):
                self._value = value

            def set(self, value):
                self._value = value

            def get(self):
                return self._value

        # Configure the mock to return our MockStringVar
        self.mock_tk.StringVar.return_value = MockStringVar()

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Stop patchers
        self.mock_tk_patcher.stop()
        self.mock_backend_patcher.stop()

    def test_toggle_sidebar_shows_when_hidden(self):
        """Test that toggle_sidebar shows sidebar when hidden."""
        workspace = TkWorkspace()
        workspace._main_paned_window = MagicMock()
        workspace._sidebar_organizer = MagicMock()
        workspace.sidebar_visible = False

        result = workspace.toggle_sidebar()

        self.assertTrue(result)
        self.assertTrue(workspace.sidebar_visible)

    def test_toggle_sidebar_hides_when_shown(self):
        """Test that toggle_sidebar hides sidebar when shown."""
        workspace = TkWorkspace()
        workspace._main_paned_window = MagicMock()
        workspace._sidebar_organizer = MagicMock()
        workspace.sidebar_visible = True

        result = workspace.toggle_sidebar()

        self.assertFalse(result)
        self.assertFalse(workspace.sidebar_visible)

    def test_toggle_sidebar_returns_new_state(self):
        """Test that toggle_sidebar returns the new visibility state."""
        workspace = TkWorkspace()
        workspace._main_paned_window = MagicMock()
        workspace._sidebar_organizer = MagicMock()
        workspace.sidebar_visible = False

        result1 = workspace.toggle_sidebar()
        result2 = workspace.toggle_sidebar()

        self.assertTrue(result1)
        self.assertFalse(result2)


class TestWorkspaceFrameOperations(unittest.TestCase):
    """Test cases for Workspace frame operations."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Set up patchers
        self.mock_tk_patcher = patch('pyrox.models.gui.tk.workspace.tk')
        self.mock_backend_patcher = patch('pyrox.models.services.GuiManager')

        # Start patchers
        self.mock_tk = self.mock_tk_patcher.start()
        self.mock_backend = self.mock_backend_patcher.start()

        self.mock_root = MagicMock()
        self.mock_backend.get_root_window.return_value = self.mock_root

        self.mock_frame = MagicMock()
        self.mock_backend.create_gui_frame.return_value = self.mock_frame

        # Create a mock StringVar that actually stores values
        class MockStringVar:
            def __init__(self, value=""):
                self._value = value

            def set(self, value):
                self._value = value

            def get(self):
                return self._value

        # Configure the mock to return our MockStringVar
        self.mock_tk.StringVar.return_value = MockStringVar()

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Stop patchers
        self.mock_tk_patcher.stop()
        self.mock_backend_patcher.stop()

    def test_raise_frame_raises_when_workspace_not_initialized(self):
        """Test that _raise_frame raises error when workspace not initialized."""
        workspace = TkWorkspace()

        mock_frame = MagicMock(spec=TaskFrame)
        mock_frame.name = "test_frame"

        with self.assertRaises(ValueError) as context:
            workspace._raise_frame(mock_frame)
        self.assertIn("Frame is not registered in the workspace", str(context.exception))

    def test_raise_frame_raises_when_frame_none(self):
        """Test that _raise_frame raises error when frame is None."""
        workspace = TkWorkspace()
        workspace._workspace_area = MagicMock()

        with self.assertRaises(ValueError) as context:
            workspace._raise_frame(None)  # type: ignore
        self.assertIn("must be a valid existing widget", str(context.exception))

    def test_raise_frame_raises_when_frame_not_registered(self):
        """Test that _raise_frame raises error when frame not registered."""
        workspace = TkWorkspace()
        workspace._workspace_area = MagicMock()

        mock_frame = MagicMock(spec=TaskFrame)
        mock_frame.name = "test_frame"

        with self.assertRaises(ValueError) as context:
            workspace._raise_frame(mock_frame)
        self.assertIn("not registered in the workspace", str(context.exception))

    def test_pack_frame_raises_when_workspace_not_initialized(self):
        """Test that _pack_frame_into_workspace raises error when not initialized."""
        workspace = TkWorkspace()

        mock_frame = MagicMock(spec=TaskFrame)

        with self.assertRaises(ValueError) as context:
            workspace._pack_frame_into_workspace(mock_frame)
        self.assertIn("Frame is not registered in the workspace", str(context.exception))

    def test_hide_frames_raises_when_workspace_not_initialized(self):
        """Test that _hide_frames raises error when workspace not initialized."""
        workspace = TkWorkspace()

        with self.assertRaises(RuntimeError) as context:
            workspace._hide_frames()
        self.assertIn("Workspace area not initialized", str(context.exception))


if __name__ == '__main__':
    unittest.main()

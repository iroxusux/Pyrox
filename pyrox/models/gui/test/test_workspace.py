"""Testcase for Workspace and _SidebarTabWidget"""
import sys
import unittest
from unittest.mock import Mock, patch

from PyQt6.QtWidgets import QApplication, QWidget

_app = QApplication.instance() or QApplication(sys.argv)

from pyrox.models.gui.workspace import _SidebarTabWidget, Workspace  # noqa: E402
from pyrox.models.gui.frame import TaskFrame  # noqa: E402


class TestSidebarTabWidget(unittest.TestCase):
    """Tests for _SidebarTabWidget callback-driven tab management."""

    def setUp(self) -> None:
        self.sidebar = _SidebarTabWidget()

    def tearDown(self) -> None:
        self.sidebar.deleteLater()

    def _add_widget(self, label: str = "Tab") -> tuple[QWidget, str]:
        widget = QWidget()
        tab_id = self.sidebar.add_tab_widget(widget, label)
        return widget, tab_id

    def test_initial_state(self):
        """Callbacks start as None and tab count is zero."""
        self.assertEqual(self.sidebar.get_tab_count(), 0)
        self.assertIsNone(self.sidebar.on_tab_selected)
        self.assertIsNone(self.sidebar.on_tab_added)
        self.assertIsNone(self.sidebar.on_tab_removed)

    def test_add_tab_widget_returns_tab_id(self):
        """add_tab_widget returns a string starting with 'tab_'."""
        _, tab_id = self._add_widget()
        self.assertIsInstance(tab_id, str)
        self.assertTrue(tab_id.startswith("tab_"))

    def test_add_tab_widget_increments_count(self):
        """Adding two widgets increases the tab count to 2."""
        self._add_widget("A")
        self._add_widget("B")
        self.assertEqual(self.sidebar.get_tab_count(), 2)

    def test_add_tab_widget_calls_on_tab_added(self):
        """on_tab_added is called with (tab_id, widget) after adding."""
        callback = Mock()
        self.sidebar.on_tab_added = callback
        widget = QWidget()
        tab_id = self.sidebar.add_tab_widget(widget, "Label")
        callback.assert_called_once_with(tab_id, widget)

    def test_add_tab_widget_swallows_callback_exception(self):
        """An exception raised in on_tab_added does not propagate."""
        self.sidebar.on_tab_added = Mock(side_effect=RuntimeError("boom"))
        tab_id = self.sidebar.add_tab_widget(QWidget(), "Tab")
        self.assertIsInstance(tab_id, str)

    def test_remove_tab_by_id_returns_true(self):
        """remove_tab_by_id returns True when the tab exists and is removed."""
        _, tab_id = self._add_widget()
        self.assertTrue(self.sidebar.remove_tab_by_id(tab_id))

    def test_remove_tab_by_id_decrements_count(self):
        """Tab count drops to zero after removing the only tab."""
        _, tab_id = self._add_widget()
        self.sidebar.remove_tab_by_id(tab_id)
        self.assertEqual(self.sidebar.get_tab_count(), 0)

    def test_remove_tab_by_id_unknown_returns_false(self):
        """remove_tab_by_id returns False for an unrecognised tab_id."""
        self.assertFalse(self.sidebar.remove_tab_by_id("tab_nonexistent"))

    def test_get_tab_frame_returns_widget(self):
        """get_tab_frame returns the widget added for the given tab_id."""
        widget = QWidget()
        tab_id = self.sidebar.add_tab_widget(widget, "Tab")
        self.assertIs(self.sidebar.get_tab_frame(tab_id), widget)

    def test_get_tab_frame_unknown_returns_none(self):
        """get_tab_frame returns None for an unrecognised tab_id."""
        self.assertIsNone(self.sidebar.get_tab_frame("tab_unknown"))

    def test_on_current_changed_fires_on_tab_selected(self):
        """_on_current_changed calls on_tab_selected with (tab_id, widget)."""
        widget, tab_id = self._add_widget()
        callback = Mock()
        self.sidebar.on_tab_selected = callback
        self.sidebar._on_current_changed(0)
        callback.assert_called_once_with(tab_id, widget)

    def test_on_current_changed_negative_index_is_noop(self):
        """_on_current_changed does nothing when index is -1."""
        callback = Mock()
        self.sidebar.on_tab_selected = callback
        self.sidebar._on_current_changed(-1)
        callback.assert_not_called()

    def test_on_current_changed_swallows_callback_exception(self):
        """An exception in on_tab_selected does not propagate."""
        self._add_widget()
        self.sidebar.on_tab_selected = Mock(side_effect=ValueError("err"))
        self.sidebar._on_current_changed(0)  # should not raise

    def test_on_tab_close_requested_removes_tab(self):
        """_on_tab_close_requested removes the tab at the given index."""
        self._add_widget()
        self.sidebar._on_tab_close_requested(0)
        self.assertEqual(self.sidebar.get_tab_count(), 0)

    def test_on_tab_close_requested_calls_on_tab_removed(self):
        """_on_tab_close_requested fires on_tab_removed with the tab_id."""
        _, tab_id = self._add_widget()
        callback = Mock()
        self.sidebar.on_tab_removed = callback
        self.sidebar._on_tab_close_requested(0)
        callback.assert_called_once_with(tab_id)


class TestWorkspace(unittest.TestCase):
    """Tests for the Workspace widget's public interface."""

    def setUp(self) -> None:
        self._patches = [
            patch('pyrox.models.gui.workspace.GuiStateService'),
            patch('pyrox.models.gui.workspace.LoggingManager'),
            patch('pyrox.models.gui.workspace.MenuRegistry'),
            patch('pyrox.models.gui.workspace.LogFrame'),
        ]
        self.MockGuiStateService = self._patches[0].start()
        self.MockLoggingManager = self._patches[1].start()
        self.MockMenuRegistry = self._patches[2].start()
        self.MockLogFrame = self._patches[3].start()
        for p in self._patches:
            self.addCleanup(p.stop)

        self.MockGuiStateService.get_geometry_state.return_value = {}
        self.MockLoggingManager.log.return_value = Mock()
        self.MockLogFrame.return_value = QWidget()

        self.workspace = Workspace()

    def tearDown(self) -> None:
        self.workspace.deleteLater()

    def _make_frame(self, name: str = "TestFrame") -> TaskFrame:
        """Return a TaskFrame with a real QWidget root suitable for workspace tests."""
        with patch('pyrox.models.gui.frame.QWidget'), \
             patch('pyrox.models.gui.frame.QPushButton'), \
             patch('pyrox.models.gui.frame.QLabel'), \
             patch('pyrox.models.gui.frame.QHBoxLayout'), \
             patch('pyrox.models.gui.frame.QVBoxLayout'):
            frame = TaskFrame(name=name, parent=None)
        frame._root = QWidget()
        return frame

    # ---- status bar ----

    def test_initial_status(self):
        """Status bar shows 'Workspace Ready' after construction."""
        self.assertEqual(self.workspace.get_status(), "Workspace Ready")

    def test_set_get_status(self):
        """set_status stores the message; get_status retrieves it."""
        self.workspace.set_status("Testing")
        self.assertEqual(self.workspace.get_status(), "Testing")

    # ---- widget ids ----

    def test_get_all_widget_ids_initially_empty(self):
        """Both sidebar and workspace id lists are empty on a fresh workspace."""
        self.assertEqual(self.workspace.get_all_widget_ids(), {'sidebar': [], 'workspace': []})

    def test_get_workspace_info_structure(self):
        """get_workspace_info returns a dict with sidebar, workspace, status, and widgets keys."""
        info = self.workspace.get_workspace_info()
        for key in ('sidebar', 'workspace', 'status', 'widgets'):
            self.assertIn(key, info)

    # ---- sash callbacks ----

    def test_subscribe_to_sash_movement_events(self):
        """Registered sash callbacks are stored in _sash_callbacks."""
        cb = Mock()
        self.workspace.subscribe_to_sash_movement_events(cb)
        self.assertIn(cb, self.workspace._sash_callbacks)

    def test_sash_callback_receives_main_event(self):
        """Sash callbacks receive ('main', ...) when the main sash moves."""
        cb = Mock()
        self.workspace.subscribe_to_sash_movement_events(cb)
        self.workspace.on_main_sash_moved()
        cb.assert_called_once()
        self.assertEqual(cb.call_args[0][0], 'main')

    def test_sash_callback_receives_log_event(self):
        """Sash callbacks receive ('log', ...) when the log sash moves."""
        cb = Mock()
        self.workspace.subscribe_to_sash_movement_events(cb)
        self.workspace.on_log_sash_moved()
        cb.assert_called_once()
        self.assertEqual(cb.call_args[0][0], 'log')

    # ---- sidebar visibility ----

    def test_sidebar_visible_by_default(self):
        """Sidebar is visible immediately after construction."""
        self.assertTrue(self.workspace._sidebar_visible)

    def test_toggle_sidebar_hides(self):
        """toggle_sidebar returns False and hides the sidebar when it is visible."""
        result = self.workspace.toggle_sidebar()
        self.assertFalse(result)
        self.assertFalse(self.workspace._sidebar_visible)

    def test_toggle_sidebar_shows(self):
        """toggle_sidebar returns True and shows the sidebar when it is hidden."""
        self.workspace.hide_sidebar()
        result = self.workspace.toggle_sidebar()
        self.assertTrue(result)
        self.assertTrue(self.workspace._sidebar_visible)

    def test_hide_sidebar_fires_callback(self):
        """hide_sidebar invokes on_sidebar_toggle with False."""
        cb = Mock()
        self.workspace.on_sidebar_toggle = cb
        self.workspace.hide_sidebar()
        cb.assert_called_once_with(False)

    def test_show_sidebar_fires_callback(self):
        """show_sidebar invokes on_sidebar_toggle with True."""
        self.workspace.hide_sidebar()
        cb = Mock()
        self.workspace.on_sidebar_toggle = cb
        self.workspace.show_sidebar()
        cb.assert_called_once_with(True)

    # ---- sidebar widgets ----

    def test_add_sidebar_widget_returns_given_id(self):
        """add_sidebar_widget returns the explicit widget_id when provided."""
        wid = self.workspace.add_sidebar_widget(QWidget(), "Panel", widget_id="explicit_id")
        self.assertEqual(wid, "explicit_id")

    def test_add_sidebar_widget_auto_generates_id(self):
        """add_sidebar_widget generates an id starting with 'sidebar_widget_' when none is given."""
        wid = self.workspace.add_sidebar_widget(QWidget(), "Panel")
        self.assertTrue(wid.startswith("sidebar_widget_"))

    def test_add_sidebar_widget_duplicate_raises(self):
        """Adding a widget with a duplicate widget_id raises ValueError."""
        self.workspace.add_sidebar_widget(QWidget(), "A", widget_id="dup")
        with self.assertRaises(ValueError):
            self.workspace.add_sidebar_widget(QWidget(), "B", widget_id="dup")

    def test_add_sidebar_widget_appears_in_ids(self):
        """widget_id appears in the sidebar section of get_all_widget_ids."""
        wid = self.workspace.add_sidebar_widget(QWidget(), "Panel", widget_id="p1")
        self.assertIn(wid, self.workspace.get_all_widget_ids()['sidebar'])

    def test_add_sidebar_widget_fires_mounted_callback(self):
        """on_sidebar_widget_mounted is called with (widget, 'sidebar') when a widget is added."""
        cb = Mock()
        self.workspace.on_sidebar_widget_mounted = cb
        widget = QWidget()
        self.workspace.add_sidebar_widget(widget, "Panel", widget_id="cb_test")
        cb.assert_called_once_with(widget, "sidebar")

    def test_remove_widget_sidebar_returns_true(self):
        """remove_widget returns True when a sidebar widget is successfully removed."""
        wid = self.workspace.add_sidebar_widget(QWidget(), "Panel", widget_id="rm_me")
        self.assertTrue(self.workspace.remove_widget(wid))

    def test_remove_widget_sidebar_cleans_up_id(self):
        """After removal the widget_id no longer appears in the sidebar ids."""
        wid = self.workspace.add_sidebar_widget(QWidget(), "Panel", widget_id="gone")
        self.workspace.remove_widget(wid)
        self.assertNotIn(wid, self.workspace.get_all_widget_ids()['sidebar'])

    def test_remove_widget_unknown_returns_false(self):
        """remove_widget returns False for an unrecognised widget_id."""
        self.assertFalse(self.workspace.remove_widget("no_such_id"))

    def test_get_widget_sidebar(self):
        """get_widget returns the original widget for a sidebar widget_id."""
        widget = QWidget()
        wid = self.workspace.add_sidebar_widget(widget, "Panel", widget_id="gw_test")
        self.assertIs(self.workspace.get_widget(wid), widget)

    def test_get_widget_unknown_returns_none(self):
        """get_widget returns None for an unrecognised widget_id."""
        self.assertIsNone(self.workspace.get_widget("unknown"))

    # ---- task frames ----

    def test_register_frame_non_taskframe_raises(self):
        """register_frame raises ValueError for non-TaskFrame arguments."""
        with self.assertRaises(ValueError):
            self.workspace.register_frame(Mock())  # type: ignore[arg-type]

    def test_unregister_frame_non_taskframe_raises(self):
        """unregister_frame raises ValueError for non-TaskFrame arguments."""
        with self.assertRaises(ValueError):
            self.workspace.unregister_frame(Mock())  # type: ignore[arg-type]

    def test_get_frame_not_found_returns_none(self):
        """get_frame returns None when no frame with the given name is registered."""
        self.assertIsNone(self.workspace.get_frame("no_such_frame"))

    def test_get_frames_initially_empty(self):
        """get_frames returns an empty list when no frames are registered."""
        self.assertEqual(self.workspace.get_frames(), [])

    def test_register_frame_duplicate_raises(self):
        """Registering a frame whose name is already taken raises ValueError."""
        frame_a = self._make_frame("Dup")
        frame_b = self._make_frame("Dup")
        self.workspace.register_frame(frame_a, raise_frame=True)
        with self.assertRaises(ValueError):
            self.workspace.register_frame(frame_b, raise_frame=False)

    def test_register_frame_appears_in_ids(self):
        """Frame name appears in the workspace section of get_all_widget_ids."""
        frame = self._make_frame("RegFrame")
        self.workspace.register_frame(frame, raise_frame=True)
        self.assertIn("RegFrame", self.workspace.get_all_widget_ids()['workspace'])

    def test_get_frame_returns_registered_frame(self):
        """get_frame returns the registered TaskFrame when the name matches."""
        frame = self._make_frame("FindMe")
        self.workspace.register_frame(frame, raise_frame=False)
        self.assertIs(self.workspace.get_frame("FindMe"), frame)

    def test_get_frames_returns_all(self):
        """get_frames returns all registered task frames."""
        fa = self._make_frame("FrameA")
        fb = self._make_frame("FrameB")
        self.workspace.register_frame(fa, raise_frame=False)
        self.workspace.register_frame(fb, raise_frame=False)
        frames = self.workspace.get_frames()
        self.assertIn(fa, frames)
        self.assertIn(fb, frames)

    def test_add_workspace_task_frame_registers_frame(self):
        """add_workspace_task_frame adds the frame to the workspace."""
        frame = self._make_frame("WsFrame")
        self.workspace.add_workspace_task_frame(frame, raise_frame=True)
        self.assertIn("WsFrame", self.workspace.get_all_widget_ids()['workspace'])

    def test_add_workspace_task_frame_duplicate_raises(self):
        """add_workspace_task_frame raises ValueError on a duplicate frame name."""
        fa = self._make_frame("DupWs")
        fb = self._make_frame("DupWs")
        self.workspace.add_workspace_task_frame(fa, raise_frame=True)
        with self.assertRaises(ValueError):
            self.workspace.add_workspace_task_frame(fb, raise_frame=False)

    def test_clear_workspace_removes_frames(self):
        """clear_workspace leaves the workspace frame list empty."""
        frame = self._make_frame("ClearMe")
        self.workspace.register_frame(frame, raise_frame=False)
        self.workspace.clear_workspace()
        self.assertEqual(self.workspace.get_frames(), [])

    # ---- panels ----

    def test_add_panel_invalid_position_raises(self):
        """add_panel raises ValueError for a position other than 'left' or 'right'."""
        with self.assertRaises(ValueError):
            self.workspace.add_panel(QWidget(), position='center')

    def test_get_panels_returns_list(self):
        """get_panels returns a list instance."""
        self.assertIsInstance(self.workspace.get_panels(), list)

    # ---- toolbar ----

    def test_get_toolbar_is_not_none(self):
        """get_toolbar returns the toolbar after construction."""
        self.assertIsNotNone(self.workspace.get_toolbar())

    def test_add_toolbar_separator_returns_int(self):
        """add_toolbar_separator returns an integer (action count)."""
        count = self.workspace.add_toolbar_separator()
        self.assertIsInstance(count, int)

    # ---- properties ----

    def test_property_main_paned_window(self):
        """main_paned_window returns the horizontal QSplitter."""
        from PyQt6.QtWidgets import QSplitter
        self.assertIsInstance(self.workspace.main_paned_window, QSplitter)

    def test_property_log_paned_window(self):
        """log_paned_window returns the vertical QSplitter."""
        from PyQt6.QtWidgets import QSplitter
        self.assertIsInstance(self.workspace.log_paned_window, QSplitter)

    def test_property_status_bar(self):
        """status_bar returns the QStatusBar."""
        from PyQt6.QtWidgets import QStatusBar
        self.assertIsInstance(self.workspace.status_bar, QStatusBar)

    def test_property_toolbar_bar(self):
        """toolbar_bar returns the QToolBar."""
        from PyQt6.QtWidgets import QToolBar
        self.assertIsInstance(self.workspace.toolbar_bar, QToolBar)

    def test_property_workspace_area(self):
        """workspace_area returns the main content QFrame."""
        from PyQt6.QtWidgets import QFrame
        self.assertIsInstance(self.workspace.workspace_area, QFrame)

    def test_property_sidebar_organizer(self):
        """sidebar_organizer returns a _SidebarTabWidget."""
        self.assertIsInstance(self.workspace.sidebar_organizer, _SidebarTabWidget)

    def test_get_workspace_area(self):
        """get_workspace_area returns a QFrame."""
        from PyQt6.QtWidgets import QFrame
        self.assertIsInstance(self.workspace.get_workspace_area(), QFrame)

    def test_get_workspace_paned_window(self):
        """get_workspace_paned_window returns the log QSplitter."""
        from PyQt6.QtWidgets import QSplitter
        self.assertIsInstance(self.workspace.get_workspace_paned_window(), QSplitter)

    def test_get_sidebar_organizer(self):
        """get_sidebar_organizer returns a _SidebarTabWidget."""
        self.assertIsInstance(self.workspace.get_sidebar_organizer(), _SidebarTabWidget)


if __name__ == "__main__":
    unittest.main()

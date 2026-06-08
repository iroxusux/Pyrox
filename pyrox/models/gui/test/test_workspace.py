"""Tests for Workspace and _SidebarTabWidget"""
import sys
import pytest
from unittest.mock import Mock, patch

from PyQt6.QtWidgets import QApplication, QWidget

from pyrox.models.gui.workspace import _SidebarTabWidget, Workspace
from pyrox.models.gui.frame import TaskFrame


@pytest.fixture(scope='module')
def qapp():
    return QApplication.instance() or QApplication(sys.argv)


class TestSidebarTabWidget:

    @pytest.fixture(autouse=True)
    def setup(self, qapp):
        self.sidebar = _SidebarTabWidget()
        yield
        self.sidebar.deleteLater()

    def _add_widget(self, label: str = "Tab") -> tuple[QWidget, str]:
        widget = QWidget()
        tab_id = self.sidebar.add_tab_widget(widget, label)
        return widget, tab_id

    def test_initial_state(self):
        assert self.sidebar.get_tab_count() == 0
        assert self.sidebar.on_tab_selected is None
        assert self.sidebar.on_tab_added is None
        assert self.sidebar.on_tab_removed is None

    def test_add_tab_widget_returns_tab_id(self):
        _, tab_id = self._add_widget()
        assert isinstance(tab_id, str)
        assert tab_id.startswith("tab_")

    def test_add_tab_widget_increments_count(self):
        self._add_widget("A")
        self._add_widget("B")
        assert self.sidebar.get_tab_count() == 2

    def test_add_tab_widget_calls_on_tab_added(self):
        callback = Mock()
        self.sidebar.on_tab_added = callback
        widget = QWidget()
        tab_id = self.sidebar.add_tab_widget(widget, "Label")
        callback.assert_called_once_with(tab_id, widget)

    def test_add_tab_widget_swallows_callback_exception(self):
        self.sidebar.on_tab_added = Mock(side_effect=RuntimeError("boom"))
        tab_id = self.sidebar.add_tab_widget(QWidget(), "Tab")
        assert isinstance(tab_id, str)

    def test_remove_tab_by_id_returns_true(self):
        _, tab_id = self._add_widget()
        assert self.sidebar.remove_tab_by_id(tab_id)

    def test_remove_tab_by_id_decrements_count(self):
        _, tab_id = self._add_widget()
        self.sidebar.remove_tab_by_id(tab_id)
        assert self.sidebar.get_tab_count() == 0

    def test_remove_tab_by_id_unknown_returns_false(self):
        assert not self.sidebar.remove_tab_by_id("tab_nonexistent")

    def test_get_tab_frame_returns_widget(self):
        widget = QWidget()
        tab_id = self.sidebar.add_tab_widget(widget, "Tab")
        assert self.sidebar.get_tab_frame(tab_id) is widget

    def test_get_tab_frame_unknown_returns_none(self):
        assert self.sidebar.get_tab_frame("tab_unknown") is None

    def test_on_current_changed_fires_on_tab_selected(self):
        widget, tab_id = self._add_widget()
        callback = Mock()
        self.sidebar.on_tab_selected = callback
        self.sidebar._on_current_changed(0)
        callback.assert_called_once_with(tab_id, widget)

    def test_on_current_changed_negative_index_is_noop(self):
        callback = Mock()
        self.sidebar.on_tab_selected = callback
        self.sidebar._on_current_changed(-1)
        callback.assert_not_called()

    def test_on_current_changed_swallows_callback_exception(self):
        self._add_widget()
        self.sidebar.on_tab_selected = Mock(side_effect=ValueError("err"))
        self.sidebar._on_current_changed(0)  # should not raise

    def test_on_tab_close_requested_removes_tab(self):
        self._add_widget()
        self.sidebar._on_tab_close_requested(0)
        assert self.sidebar.get_tab_count() == 0

    def test_on_tab_close_requested_calls_on_tab_removed(self):
        _, tab_id = self._add_widget()
        callback = Mock()
        self.sidebar.on_tab_removed = callback
        self.sidebar._on_tab_close_requested(0)
        callback.assert_called_once_with(tab_id)


class TestWorkspace:

    @pytest.fixture(autouse=True)
    def setup(self, qapp):
        # LogFrame.side_effect creates the widget with its intended parent,
        # avoiding a parentless top-level QWidget that can flash on screen.
        with patch('pyrox.models.gui.workspace.GuiStateService') as mock_gui_state, \
                patch('pyrox.models.gui.workspace.LoggingManager') as mock_logging, \
                patch('pyrox.models.gui.workspace.MenuRegistry'), \
                patch('pyrox.models.gui.workspace.LogFrame') as mock_log_frame:
            mock_gui_state.get_geometry_state.return_value = {}
            mock_logging.log.return_value = Mock()
            mock_log_frame.side_effect = lambda parent=None: QWidget(parent)
            self.workspace = Workspace()
            yield
            self.workspace.deleteLater()

    def _make_frame(self, name: str = "TestFrame") -> TaskFrame:
        # Bypass TaskFrame.__init__ so no real Qt widget tree is built.
        # _root is parented to workspace_area so _pack_frame_into_workspace
        # never needs to call setParent on a top-level window.
        frame = TaskFrame.__new__(TaskFrame)
        frame._name = name
        frame._shown = False
        frame._on_destroy = []
        frame._root = QWidget(self.workspace._workspace_area)
        return frame

    # ---- status bar ----

    def test_initial_status(self):
        assert self.workspace.get_status() == "Workspace Ready"

    def test_set_get_status(self):
        self.workspace.set_status("Testing")
        assert self.workspace.get_status() == "Testing"

    # ---- widget ids ----

    def test_get_all_widget_ids_initially_empty(self):
        assert self.workspace.get_all_widget_ids() == {'sidebar': [], 'workspace': []}

    def test_get_workspace_info_structure(self):
        info = self.workspace.get_workspace_info()
        for key in ('sidebar', 'workspace', 'status', 'widgets'):
            assert key in info

    # ---- sash callbacks ----

    def test_subscribe_to_sash_movement_events(self):
        cb = Mock()
        self.workspace.subscribe_to_sash_movement_events(cb)
        assert cb in self.workspace._sash_callbacks

    def test_sash_callback_receives_main_event(self):
        cb = Mock()
        self.workspace.subscribe_to_sash_movement_events(cb)
        self.workspace.on_main_sash_moved()
        cb.assert_called_once()
        assert cb.call_args[0][0] == 'main'

    def test_sash_callback_receives_log_event(self):
        cb = Mock()
        self.workspace.subscribe_to_sash_movement_events(cb)
        self.workspace.on_log_sash_moved()
        cb.assert_called_once()
        assert cb.call_args[0][0] == 'log'

    # ---- sidebar visibility ----

    def test_sidebar_visible_by_default(self):
        assert self.workspace._sidebar_visible

    def test_toggle_sidebar_hides(self):
        result = self.workspace.toggle_sidebar()
        assert not result
        assert not self.workspace._sidebar_visible

    def test_toggle_sidebar_shows(self):
        self.workspace.hide_sidebar()
        result = self.workspace.toggle_sidebar()
        assert result
        assert self.workspace._sidebar_visible

    def test_hide_sidebar_fires_callback(self):
        cb = Mock()
        self.workspace.on_sidebar_toggle = cb
        self.workspace.hide_sidebar()
        cb.assert_called_once_with(False)

    def test_show_sidebar_fires_callback(self):
        self.workspace.hide_sidebar()
        cb = Mock()
        self.workspace.on_sidebar_toggle = cb
        self.workspace.show_sidebar()
        cb.assert_called_once_with(True)

    # ---- sidebar widgets ----

    def test_add_sidebar_widget_returns_given_id(self):
        wid = self.workspace.add_sidebar_widget(QWidget(), "Panel", widget_id="explicit_id")
        assert wid == "explicit_id"

    def test_add_sidebar_widget_auto_generates_id(self):
        wid = self.workspace.add_sidebar_widget(QWidget(), "Panel")
        assert wid.startswith("sidebar_widget_")

    def test_add_sidebar_widget_duplicate_raises(self):
        self.workspace.add_sidebar_widget(QWidget(), "A", widget_id="dup")
        with pytest.raises(ValueError):
            self.workspace.add_sidebar_widget(QWidget(), "B", widget_id="dup")

    def test_add_sidebar_widget_appears_in_ids(self):
        wid = self.workspace.add_sidebar_widget(QWidget(), "Panel", widget_id="p1")
        assert wid in self.workspace.get_all_widget_ids()['sidebar']

    def test_add_sidebar_widget_fires_mounted_callback(self):
        cb = Mock()
        self.workspace.on_sidebar_widget_mounted = cb
        widget = QWidget()
        self.workspace.add_sidebar_widget(widget, "Panel", widget_id="cb_test")
        cb.assert_called_once_with(widget, "sidebar")

    def test_remove_widget_sidebar_returns_true(self):
        wid = self.workspace.add_sidebar_widget(QWidget(), "Panel", widget_id="rm_me")
        assert self.workspace.remove_widget(wid)

    def test_remove_widget_sidebar_cleans_up_id(self):
        wid = self.workspace.add_sidebar_widget(QWidget(), "Panel", widget_id="gone")
        self.workspace.remove_widget(wid)
        assert wid not in self.workspace.get_all_widget_ids()['sidebar']

    def test_remove_widget_unknown_returns_false(self):
        assert not self.workspace.remove_widget("no_such_id")

    def test_get_widget_sidebar(self):
        widget = QWidget()
        wid = self.workspace.add_sidebar_widget(widget, "Panel", widget_id="gw_test")
        assert self.workspace.get_widget(wid) is widget

    def test_get_widget_unknown_returns_none(self):
        assert self.workspace.get_widget("unknown") is None

    # ---- task frames ----

    def test_register_frame_non_taskframe_raises(self):
        with pytest.raises(ValueError):
            self.workspace.register_frame(Mock())  # type: ignore[arg-type]

    def test_unregister_frame_non_taskframe_raises(self):
        with pytest.raises(ValueError):
            self.workspace.unregister_frame(Mock())  # type: ignore[arg-type]

    def test_get_frame_not_found_returns_none(self):
        assert self.workspace.get_frame("no_such_frame") is None

    def test_get_frames_initially_empty(self):
        assert self.workspace.get_frames() == []

    def test_register_frame_duplicate_raises(self):
        frame_a = self._make_frame("Dup")
        frame_b = self._make_frame("Dup")
        self.workspace.register_frame(frame_a, raise_frame=True)
        with pytest.raises(ValueError):
            self.workspace.register_frame(frame_b, raise_frame=False)

    def test_register_frame_appears_in_ids(self):
        frame = self._make_frame("RegFrame")
        self.workspace.register_frame(frame, raise_frame=True)
        assert "RegFrame" in self.workspace.get_all_widget_ids()['workspace']

    def test_get_frame_returns_registered_frame(self):
        frame = self._make_frame("FindMe")
        self.workspace.register_frame(frame, raise_frame=False)
        assert self.workspace.get_frame("FindMe") is frame

    def test_get_frames_returns_all(self):
        fa = self._make_frame("FrameA")
        fb = self._make_frame("FrameB")
        self.workspace.register_frame(fa, raise_frame=False)
        self.workspace.register_frame(fb, raise_frame=False)
        frames = self.workspace.get_frames()
        assert fa in frames
        assert fb in frames

    def test_add_workspace_task_frame_registers_frame(self):
        frame = self._make_frame("WsFrame")
        self.workspace.add_workspace_task_frame(frame, raise_frame=True)
        assert "WsFrame" in self.workspace.get_all_widget_ids()['workspace']

    def test_add_workspace_task_frame_duplicate_raises(self):
        fa = self._make_frame("DupWs")
        fb = self._make_frame("DupWs")
        self.workspace.add_workspace_task_frame(fa, raise_frame=True)
        with pytest.raises(ValueError):
            self.workspace.add_workspace_task_frame(fb, raise_frame=False)

    def test_clear_workspace_removes_frames(self):
        frame = self._make_frame("ClearMe")
        self.workspace.register_frame(frame, raise_frame=False)
        self.workspace.clear_workspace()
        assert self.workspace.get_frames() == []

    # ---- panels ----

    def test_add_panel_invalid_position_raises(self):
        with pytest.raises(ValueError):
            self.workspace.add_panel(QWidget(), position='center')

    def test_get_panels_returns_list(self):
        assert isinstance(self.workspace.get_panels(), list)

    # ---- toolbar ----

    def test_get_toolbar_is_not_none(self):
        assert self.workspace.get_toolbar() is not None

    def test_add_toolbar_separator_returns_int(self):
        count = self.workspace.add_toolbar_separator()
        assert isinstance(count, int)

    # ---- properties ----

    def test_property_main_paned_window(self):
        from PyQt6.QtWidgets import QSplitter
        assert isinstance(self.workspace.main_paned_window, QSplitter)

    def test_property_log_paned_window(self):
        from PyQt6.QtWidgets import QSplitter
        assert isinstance(self.workspace.log_paned_window, QSplitter)

    def test_property_status_bar(self):
        from PyQt6.QtWidgets import QStatusBar
        assert isinstance(self.workspace.status_bar, QStatusBar)

    def test_property_toolbar_bar(self):
        from PyQt6.QtWidgets import QToolBar
        assert isinstance(self.workspace.toolbar_bar, QToolBar)

    def test_property_workspace_area(self):
        from PyQt6.QtWidgets import QFrame
        assert isinstance(self.workspace.workspace_area, QFrame)

    def test_property_sidebar_organizer(self):
        assert isinstance(self.workspace.sidebar_organizer, _SidebarTabWidget)

    def test_get_workspace_area(self):
        from PyQt6.QtWidgets import QFrame
        assert isinstance(self.workspace.get_workspace_area(), QFrame)

    def test_get_workspace_paned_window(self):
        from PyQt6.QtWidgets import QSplitter
        assert isinstance(self.workspace.get_workspace_paned_window(), QSplitter)

    def test_get_sidebar_organizer(self):
        assert isinstance(self.workspace.get_sidebar_organizer(), _SidebarTabWidget)

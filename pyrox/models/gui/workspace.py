"""
Workspace Widget for Pyrox applications with VSCode-like layout (PyQt6 implementation).

This module provides a workspace widget that mimics the VSCode interface with:
- Left sidebar organizer (QTabWidget) for navigation and tools
- Main workspace area for content
- Resizable panes with QSplitter
- Dynamic widget mounting and management
- Configurable sidebar visibility and positioning
"""
from __future__ import annotations

from typing import Optional, Callable, Any

from PyQt6.QtCore import Qt, QTimer, QSize, QRect, QPoint

from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QStyle,
    QStyleOptionTab,
    QStylePainter,
    QTabBar,
    QTabWidget,
    QToolBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from pyrox.interfaces import EnvironmentKeys
from pyrox.models.gui.commandbar import CommandButton
from pyrox.models.gui import LogFrame, TaskFrame
from pyrox.services import EnvManager, LoggingManager

# ---- Display map to help visualize what the layout should look like ----
# +-----------------------------------------------------+
# |                    Tool Bar                         |
# +----------------------+------------------------------+
# |      Sidebar         |        Workspace Area        |
# |   (QTabWidget)       |   (Dynamic TaskFrames)       |
# |                      |                              |
# |                      +------------------------------+
# |                      |        Log Window            |
# +----------------------+------------------------------+
# |                   Status Bar                        |
# +-----------------------------------------------------+


class _VerticalTabBar(QTabBar):
    """A QTabBar that renders tab labels rotated 90° for a VSCode-style vertical sidebar."""

    TAB_WIDTH = 55
    TAB_HEIGHT = 55

    def tabSizeHint(self, index: int) -> QSize:
        return QSize(self.TAB_WIDTH, self.TAB_HEIGHT)

    def minimumTabSizeHint(self, index: int) -> QSize:
        return QSize(self.TAB_WIDTH, self.TAB_HEIGHT)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QStylePainter(self)
        opt = QStyleOptionTab()
        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QStyle.ControlElement.CE_TabBarTabShape, opt)
            painter.save()
            s = opt.rect.size()
            s.transpose()
            r = QRect(QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r
            c = self.tabRect(i).center()
            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(QStyle.ControlElement.CE_TabBarTabLabel, opt)
            painter.restore()


class _SidebarTabWidget(QTabWidget):
    """Internal QTabWidget used as the sidebar organizer.

    Provides a thin wrapper around QTabWidget that mirrors the callback-driven
    API of the Pyrox PyroxNotebook used in the tkinter workspace.
    Tabs are displayed vertically on the left edge, VSCode-style.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setTabBar(_VerticalTabBar(self))
        self.setTabPosition(QTabWidget.TabPosition.West)
        self.setTabsClosable(False)
        self.setMovable(True)
        self.setDocumentMode(False)

        self.on_tab_selected: Optional[Callable[[str, QWidget], None]] = None
        self.on_tab_added: Optional[Callable[[str, QWidget], None]] = None
        self.on_tab_removed: Optional[Callable[[str], None]] = None

        self.currentChanged.connect(self._on_current_changed)
        self.tabCloseRequested.connect(self._on_tab_close_requested)

    # ---- internal helpers ----

    @staticmethod
    def _tab_id(widget: QWidget) -> str:
        return widget.property("_pyrox_tab_id") or ""

    # ---- public API ----

    def add_tab_widget(
        self,
        widget: QWidget,
        label: str,
        closeable: bool = True,
    ) -> str:
        """Add *widget* as a new tab and return its opaque tab_id string."""
        tab_id = f"tab_{id(widget)}"
        widget.setProperty("_pyrox_tab_id", tab_id)
        index = self.addTab(widget, label)

        if not closeable:
            # Hide the per-tab close button by replacing it with an empty widget.
            tab_bar = self.tabBar()
            if tab_bar is not None:
                tab_bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, QWidget())

        if self.on_tab_added:
            try:
                self.on_tab_added(tab_id, widget)
            except Exception as e:
                print(f"Error in on_tab_added callback: {e}")

        return tab_id

    def remove_tab_by_id(self, tab_id: str) -> bool:
        """Remove the tab whose tab_id matches *tab_id*. Returns True on success."""
        for i in range(self.count()):
            widget = self.widget(i)
            if widget and self._tab_id(widget) == tab_id:
                self.removeTab(i)
                return True
        return False

    def get_tab_frame(self, tab_id: str) -> Optional[QWidget]:
        """Return the container widget for *tab_id*, or None if not found."""
        for i in range(self.count()):
            widget = self.widget(i)
            if widget and self._tab_id(widget) == tab_id:
                return widget
        return None

    def get_tab_count(self) -> int:
        return self.count()

    # ---- Qt signal handlers ----

    def _on_current_changed(self, index: int) -> None:
        if index < 0 or not self.on_tab_selected:
            return
        widget = self.widget(index)
        if widget:
            try:
                self.on_tab_selected(self._tab_id(widget), widget)
            except Exception as e:
                print(f"Error in on_tab_selected callback: {e}")

    def _on_tab_close_requested(self, index: int) -> None:
        widget = self.widget(index)
        tab_id = self._tab_id(widget) if widget else ""
        self.removeTab(index)
        if tab_id and self.on_tab_removed:
            try:
                self.on_tab_removed(tab_id)
            except Exception as e:
                print(f"Error in on_tab_removed callback: {e}")


class Workspace(QWidget):
    """
    A VSCode-like workspace widget (PyQt6 implementation).

    Features:
    - Left sidebar with QTabWidget organizer
    - Resizable main workspace area via QSplitter
    - Dynamic widget mounting/unmounting
    - Sidebar visibility toggle
    - Multiple workspace layouts
    - Event callbacks for workspace operations
    - Built-in status bar and toolbar support
    - Configurable splitter positions
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ) -> None:
        QWidget.__init__(self, parent)

        self._main_splitter: Optional[QSplitter] = None
        self._log_splitter: Optional[QSplitter] = None
        self._sidebar_organizer: Optional[_SidebarTabWidget] = None
        self._workspace_area: Optional[QFrame] = None
        self._workspace_layout: Optional[QVBoxLayout] = None
        self._status_bar: Optional[QStatusBar] = None
        self._toolbar: Optional[QToolBar] = None
        self._sidebar_visible: bool = True

        # Widget tracking
        self._mounted_widgets: dict[str, QWidget] = {}
        self._sidebar_tabs: dict[str, str] = {}       # widget_id -> tab_id
        self._workspace_frames: dict[str, TaskFrame] = {}

        # Event callbacks
        self.on_sidebar_toggle: Optional[Callable[[bool], None]] = None
        self.on_task_frame_mounted: Optional[Callable[[TaskFrame, str], None]] = None
        self.on_task_frame_unmounted: Optional[Callable[[TaskFrame], None]] = None
        self.on_sidebar_widget_mounted: Optional[Callable[[QWidget, str], None]] = None
        self.on_sidebar_widget_unmounted: Optional[Callable[[str], None]] = None
        self.on_workspace_changed: Optional[Callable[[str], None]] = None

        # Status text
        self._status_text: str = ""

        # Sash callbacks and geometry-save debounce timer
        self._sash_callbacks: list[Callable] = []
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._store_workspace_geometry)

        self._create_layout()
        self._setup_bindings()

        self.set_status("Workspace Ready")
        # Restore geometry once the widget has been shown and sized
        QTimer.singleShot(50, self.restore_workspace_geometry)

    # ---- internal log helper (avoids pulling in the full ServicesRunnableMixin) ----

    def _log(self):
        return LoggingManager.log(caller=self)

    # ------- Layout creation --------

    def _create_layout(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._create_toolbar(outer)
        self._create_main_splitter(outer)
        self._create_status_bar(outer)

    def _create_toolbar(self, layout: QVBoxLayout) -> None:
        self._log().debug("Creating toolbar")
        self._toolbar = QToolBar(self)
        self._toolbar.setMovable(False)
        self._toolbar.setFloatable(False)
        layout.addWidget(self._toolbar)

        sep = QFrame(self)
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

    def _create_main_splitter(self, layout: QVBoxLayout) -> None:
        self._log().debug("Creating main splitter")
        self._main_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._main_splitter.setChildrenCollapsible(False)
        layout.addWidget(self._main_splitter, stretch=1)

        self._create_sidebar_organizer()
        self._create_log_splitter()

    def _create_sidebar_organizer(self) -> None:
        self._log().debug("Creating sidebar organizer")
        assert self._main_splitter is not None
        self._sidebar_organizer = _SidebarTabWidget(self._main_splitter)
        self._main_splitter.addWidget(self._sidebar_organizer)
        QTimer.singleShot(100, self._set_initial_sidebar_width)

    def _create_log_splitter(self) -> None:
        self._log().debug("Creating log splitter")
        assert self._main_splitter is not None
        self._log_splitter = QSplitter(Qt.Orientation.Vertical, self._main_splitter)
        self._log_splitter.setChildrenCollapsible(False)
        self._main_splitter.addWidget(self._log_splitter)

        self._create_workspace_area()
        self._create_log_window()

    def _create_workspace_area(self) -> None:
        self._log().debug("Creating workspace area")
        assert self._log_splitter is not None
        self._workspace_area = QFrame(self._log_splitter)
        self._workspace_area.setFrameShape(QFrame.Shape.NoFrame)
        self._workspace_layout = QVBoxLayout(self._workspace_area)
        self._workspace_layout.setContentsMargins(0, 0, 0, 0)
        self._workspace_layout.setSpacing(0)
        self._log_splitter.addWidget(self._workspace_area)

    def _create_log_window(self) -> None:
        self._log().debug("Creating log window")
        assert self._log_splitter is not None
        self.log_window = LogFrame(self._log_splitter)
        self._log_splitter.addWidget(self.log_window)
        QTimer.singleShot(10, self._set_initial_log_window_height)

    def _create_status_bar(self, layout: QVBoxLayout) -> None:
        self._log().debug("Creating status bar")
        self._status_bar = QStatusBar(self)
        info_btn = QPushButton("ⓘ", self._status_bar)
        info_btn.setFixedWidth(30)
        info_btn.setFlat(True)
        info_btn.setToolTip("Workspace Information")
        info_btn.clicked.connect(self._show_workspace_info)
        self._status_bar.addPermanentWidget(info_btn)
        layout.addWidget(self._status_bar)

    def _setup_bindings(self) -> None:
        """Connect internal signals to workspace callbacks."""
        assert self._sidebar_organizer is not None
        assert self._main_splitter is not None
        assert self._log_splitter is not None
        self._sidebar_organizer.on_tab_selected = self._on_sidebar_tab_selected
        self._sidebar_organizer.on_tab_added = self._on_sidebar_tab_added
        self._sidebar_organizer.on_tab_removed = self._on_sidebar_tab_removed

        self._main_splitter.splitterMoved.connect(self._on_main_sash_moved)
        self._log_splitter.splitterMoved.connect(self._on_log_sash_moved)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self.save_workspace_geometry()

    # -------- Geometry management --------

    def _store_workspace_geometry(self) -> None:
        """Persist the current splitter positions to the environment store."""
        sidebar_width = self.get_sidebar_width()
        log_height = self.get_log_window_height()

        if sidebar_width is not None and self._sidebar_visible:
            EnvManager.set(EnvironmentKeys.ui.UI_SIDEBAR_WIDTH, str(sidebar_width))
        if log_height is not None:
            EnvManager.set(EnvironmentKeys.ui.UI_LOG_WINDOW_HEIGHT, str(log_height))

    def save_workspace_geometry(self) -> None:
        """Debounce-triggered save of workspace geometry."""
        self._save_timer.start(500)

    def restore_workspace_geometry(self) -> None:
        """Restore splitter positions from the environment store."""
        self._set_initial_sidebar_width()
        self._set_initial_log_window_height()

    # -------- Workspace management --------

    def _show_workspace_info(self) -> None:
        """Show a modal dialog with workspace statistics."""
        info = self.get_workspace_info()
        info_text = (
            "Workspace Information:\n\n"
            "Sidebar:\n"
            f"  \u2022 Widgets: {info['sidebar']['widget_count']}\n"
            f"  \u2022 Tabs: {info['sidebar']['tab_count']}\n\n"
            "Main Area:\n"
            f"  \u2022 Widgets: {info['workspace']['widget_count']}\n"
            f"  \u2022 Size: {info['workspace']['area_size'][0]}\u00d7"
            f"{info['workspace']['area_size'][1]}px\n\n"
            f"Status: {info['status']['current_message']}\n"
        )

        dlg = QDialog(self)
        dlg.setWindowTitle("Workspace Information")
        dlg.resize(400, 300)
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)

        dlg_layout = QVBoxLayout(dlg)
        text_edit = QTextEdit(dlg)
        text_edit.setReadOnly(True)
        text_edit.setPlainText(info_text)
        dlg_layout.addWidget(text_edit)

        close_btn = QPushButton("Close", dlg)
        close_btn.clicked.connect(dlg.accept)
        dlg_layout.addWidget(close_btn)

        dlg.exec()

    def clear_workspace(self) -> None:
        """Clear all task frames from the workspace area."""
        for frame in list(self._workspace_frames.values()):
            self._unregister_workspace_frame(frame)
        self.set_status("Workspace cleared")

    def clear_all(self) -> None:
        """Clear all widgets from both the workspace area and sidebar."""
        self.clear_workspace()
        self.clear_sidebar()
        self.set_status("All widgets cleared")

    def get_workspace_info(self) -> dict[str, Any]:
        """Return a dict of current workspace statistics."""
        area = self._workspace_area
        size = (area.width(), area.height()) if area else (0, 0)
        return {
            'sidebar': {
                'widget_count': len(self._mounted_widgets),
                'tab_count': self._sidebar_organizer.get_tab_count() if self._sidebar_organizer else 0,
            },
            'workspace': {
                'widget_count': len(self._workspace_frames),
                'area_size': size,
            },
            'status': {
                'current_message': self.get_status(),
            },
            'widgets': self.get_all_widget_ids(),
        }

    def subscribe_to_sash_movement_events(self, callback: Callable) -> None:
        """Register *callback* to be called whenever a splitter sash is moved.

        The callback receives ``(sash_id: str, position: float | None)`` where
        *sash_id* is ``'main'`` for the sidebar splitter or ``'log'`` for the
        log-window splitter, and *position* is the fraction of total size.
        """
        self._sash_callbacks.append(callback)

    def get_workspace_area(self) -> Optional[QFrame]:
        """Return the main workspace content frame."""
        return self._workspace_area

    def get_workspace_paned_window(self) -> Optional[QSplitter]:
        """Return the log-area QSplitter (vertical, containing workspace + log)."""
        return self._log_splitter

    # -------- Frames management --------

    def _unregister_frame_from_view_menu(self, frame: TaskFrame) -> None:
        # Qt applications own their menus separately.
        # The host application should connect to on_task_frame_unmounted to
        # update its View menu when a frame is removed.
        pass

    def _unregister_workspace_frame(self, frame: TaskFrame) -> None:
        if frame.shown:
            self._hide_frames()

        self._workspace_frames.pop(frame.name, None)
        self._unregister_frame_from_view_menu(frame)
        self.set_status(f"Removed workspace frame: {frame.name}")

        if self.on_task_frame_unmounted:
            try:
                self.on_task_frame_unmounted(frame)
            except Exception as e:
                print(f"Error in on_task_frame_unmounted callback: {e}")

        if not self._get_shown_frame():
            self._raise_next_available_frame()

    def _unset_frames_selected(self) -> None:
        for frame in self._workspace_frames.values():
            frame.set_shown(False)

    def _hide_frames(self) -> None:
        """Hide all task-frame root widgets in the workspace area."""
        for frame in self._workspace_frames.values():
            root = frame.root
            if root is not None:
                root.setVisible(False)

    def _pack_frame_into_workspace(self, frame: TaskFrame) -> None:
        """Reparent *frame.root* into the workspace area and show it."""
        if frame.name not in self._workspace_frames:
            raise ValueError("Frame is not registered in the workspace")

        root: QWidget = frame.root
        if root is None:
            raise ValueError("Frame root widget is None")

        if root.parent() is not self._workspace_area:
            root.setParent(self._workspace_area)
            assert root.parent() is self._workspace_area, "Failed to reparent frame root to workspace area"

        assert self._workspace_layout is not None
        if self._workspace_layout.indexOf(root) == -1:
            self._workspace_layout.addWidget(root)
        root.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        root.setVisible(True)
        self.set_status(f"Packed frame into workspace: {frame.name}")

    def _raise_frame(self, frame: TaskFrame) -> None:
        """Bring *frame* to the front of the workspace area."""
        if frame.name not in self._workspace_frames:
            raise ValueError("Frame is not registered in the workspace")

        self._hide_frames()
        self._select_frame(frame)
        self._pack_frame_into_workspace(frame)
        self.set_status(f"Raised frame: {frame.name}")

    def _raise_next_available_frame(self) -> None:
        """Raise the first available registered frame."""
        for frame in self._workspace_frames.values():
            if frame.root is not None:
                self._raise_frame(frame)
                return

    def _register_frame_to_view_menu(self, frame: TaskFrame) -> None:
        # Qt applications own their menus separately.
        # The host application should connect to on_task_frame_mounted to
        # update its View menu when a new frame is registered.
        pass

    def _register_workspace_frame(
        self,
        frame: TaskFrame,
        raise_frame: bool = False,
    ) -> None:
        if frame is None:
            raise ValueError("frame must be provided")

        if frame.name in self._workspace_frames:
            raise ValueError(f"Widget ID '{frame.name}' already exists")

        self._workspace_frames[frame.name] = frame

        def _destroy_func(f: TaskFrame) -> None:
            self._unregister_workspace_frame(f)

        if _destroy_func not in frame.on_destroy():
            frame.on_destroy().append(lambda f: _destroy_func(f))

        self._register_frame_to_view_menu(frame)

        if self.on_task_frame_mounted:
            try:
                self.on_task_frame_mounted(frame, "workspace")
            except Exception as e:
                print(f"Error in on_task_frame_mounted callback: {e}")

        self.set_status(f"Added workspace widget: {frame.name}")

        if raise_frame:
            self._raise_frame(frame)

    def _select_frame(self, frame: TaskFrame) -> None:
        self._unset_frames_selected()
        frame.set_shown(True)

    def _get_shown_frame(self) -> Optional[TaskFrame]:
        for frame in self._workspace_frames.values():
            if frame.shown:
                return frame
        return None

    def register_frame(self, frame: TaskFrame, raise_frame: bool = True) -> None:
        """Register *frame* with the workspace.

        Args:
            frame: The ITaskFrame to register.
            raise_frame: Whether to bring the frame to the front immediately.
        """
        if not isinstance(frame, TaskFrame):
            raise ValueError("Only ITaskFrame instances can be registered in the workspace")
        self._register_workspace_frame(frame, raise_frame)

    def unregister_frame(self, frame: TaskFrame) -> None:
        """Remove *frame* from the workspace."""
        if not isinstance(frame, TaskFrame):
            raise ValueError("Only ITaskFrame instances can be unregistered from the workspace")
        self._unregister_workspace_frame(frame)

    def get_frame(self, frame_name: str) -> Optional[TaskFrame]:
        """Return the registered frame with name *frame_name*, or None."""
        return self._workspace_frames.get(frame_name)

    def get_frames(self) -> list[TaskFrame]:
        """Return all registered task frames."""
        return list(self._workspace_frames.values())

    def set_frames(self, frames: list[TaskFrame]) -> None:
        """Replace all workspace frames with *frames*."""
        self.clear_workspace()
        for frame in frames:
            self._register_workspace_frame(frame, raise_frame=False)

    def raise_frame(self, frame: TaskFrame) -> None:
        """Bring a registered *frame* to the front of the workspace."""
        if not isinstance(frame, TaskFrame):
            raise ValueError("Only ITaskFrame instances can be raised in the workspace")
        self._raise_frame(frame)

    # -------- Sidebar management --------

    def _on_sidebar_tab_selected(self, tab_id: str, frame: QWidget) -> None:
        widget_id = next(
            (wid for wid, tid in self._sidebar_tabs.items() if tid == tab_id),
            None,
        )
        if widget_id:
            self.set_status(f"Selected sidebar widget: {widget_id}")
            if self.on_workspace_changed:
                try:
                    self.on_workspace_changed(widget_id)
                except Exception as e:
                    print(f"Error in on_workspace_changed callback: {e}")

    def _on_sidebar_tab_added(self, tab_id: str, frame: QWidget) -> None:
        self.set_status("New sidebar tab added")

    def _on_sidebar_tab_removed(self, tab_id: str) -> None:
        widget_id = next(
            (wid for wid, tid in self._sidebar_tabs.items() if tid == tab_id),
            None,
        )
        if widget_id:
            self._mounted_widgets.pop(widget_id, None)
            self._sidebar_tabs.pop(widget_id, None)
            self.set_status(f"Removed sidebar widget: {widget_id}")

    def _set_initial_sidebar_width(self) -> None:
        self._log().debug("Setting initial sidebar width")
        width = EnvManager.get(EnvironmentKeys.ui.UI_SIDEBAR_WIDTH, 0.33, float)
        self.set_sidebar_width(width)

    def get_sidebar_width(self) -> Optional[float]:
        """Return the sidebar width as a fraction of the total workspace width."""
        if not self._main_splitter:
            return None
        total = self._main_splitter.width()
        if total <= 0:
            return None
        sizes = self._main_splitter.sizes()
        return sizes[0] / total if sizes else None

    def set_sidebar_width(self, perc_of_window: float) -> None:
        """Set the sidebar width to *perc_of_window* fraction of the total width."""
        if not self._main_splitter:
            raise RuntimeError("Main splitter not initialized")
        total = self._main_splitter.width()
        if total <= 0:
            return
        sidebar_px = int(total * perc_of_window)
        self._main_splitter.setSizes([sidebar_px, total - sidebar_px])
        EnvManager.set(EnvironmentKeys.ui.UI_SIDEBAR_WIDTH, str(perc_of_window))

    def _on_main_sash_moved(self, pos: int, index: int) -> None:
        width = self.get_sidebar_width()
        for cb in self._sash_callbacks:
            cb('main', width)

    def on_main_sash_moved(self, event=None) -> None:
        """Public hook for the main splitter sash movement."""
        self._on_main_sash_moved(0, 0)

    def get_sidebar_organizer(self) -> Optional[_SidebarTabWidget]:
        """Return the sidebar QTabWidget."""
        return self._sidebar_organizer

    # -------- Sidebar tab management --------

    def show_sidebar(self) -> None:
        """Show the sidebar panel."""
        if self._sidebar_visible or not self._main_splitter or not self._sidebar_organizer:
            return
        original_width = EnvManager.get(EnvironmentKeys.ui.UI_SIDEBAR_WIDTH, 0.33, float)
        self._sidebar_organizer.setVisible(True)
        self._sidebar_visible = True
        self.set_sidebar_width(original_width)
        self.set_status("Sidebar shown")
        if self.on_sidebar_toggle:
            try:
                self.on_sidebar_toggle(True)
            except Exception as e:
                print(f"Error in on_sidebar_toggle callback: {e}")

    def hide_sidebar(self) -> None:
        """Hide the sidebar panel."""
        if not self._sidebar_visible or not self._main_splitter:
            return
        # Persist current width before hiding so it can be restored accurately.
        sidebar_width = self.get_sidebar_width()
        if sidebar_width is not None:
            EnvManager.set(EnvironmentKeys.ui.UI_SIDEBAR_WIDTH, str(sidebar_width))
        if self._sidebar_organizer is not None:
            self._sidebar_organizer.setVisible(False)
        self._sidebar_visible = False
        self.set_status("Sidebar hidden")
        if self.on_sidebar_toggle:
            try:
                self.on_sidebar_toggle(False)
            except Exception as e:
                print(f"Error in on_sidebar_toggle callback: {e}")

    def toggle_sidebar(self) -> bool:
        """Toggle sidebar visibility. Returns the new visibility state."""
        if self._sidebar_visible:
            self.hide_sidebar()
        else:
            self.show_sidebar()
        return self._sidebar_visible

    # -------- Sidebar panel management --------

    def add_panel(self, panel: QWidget, position: str = 'left') -> None:
        """Add *panel* to the workspace splitter at *position* ('left' or 'right')."""
        if not self._log_splitter:
            raise RuntimeError("Log splitter not initialized")
        if position == 'left':
            self._log_splitter.insertWidget(0, panel)
        elif position == 'right':
            self._log_splitter.addWidget(panel)
        else:
            raise ValueError("Position must be 'left' or 'right'")

    def remove_panel(self, panel: QWidget) -> None:
        """Detach *panel* from the workspace splitter."""
        panel.setParent(None)

    def get_panels(self) -> list[QWidget]:
        """Return all current panels in the log splitter."""
        if not self._log_splitter:
            return []
        widgets = [self._log_splitter.widget(i) for i in range(self._log_splitter.count())]
        return [w for w in widgets if w is not None]

    def clear_panels(self) -> None:
        """Remove all panels from the log splitter."""
        if not self._log_splitter:
            return
        while self._log_splitter.count():
            widget = self._log_splitter.widget(0)
            if widget:
                widget.setParent(None)

    def set_panel_height(self, panel_id: str, height: int) -> None:
        """Set the last panel in the log splitter to *height* pixels."""
        if not self._log_splitter:
            raise RuntimeError("Log splitter not initialized")
        total = self._log_splitter.height()
        if total <= 0:
            return
        sizes = list(self._log_splitter.sizes())
        if len(sizes) >= 2:
            sizes[-1] = height
            sizes[-2] = total - height
            self._log_splitter.setSizes(sizes)

    def get_panel_height(self, panel_id: str) -> int:
        """Return the height of the last panel in the log splitter in pixels."""
        if not self._log_splitter:
            return 0
        sizes = self._log_splitter.sizes()
        return sizes[-1] if sizes else 0

    # -------- Sidebar widget management --------

    def add_sidebar_widget(
        self,
        widget: QWidget,
        tab_name: str,
        widget_id: Optional[str] = None,
        icon: Optional[str] = None,
        closeable: bool = True,
    ) -> str:
        """Add *widget* to the sidebar as a new tab.

        Args:
            widget: The QWidget to embed.
            tab_name: Label displayed on the tab.
            widget_id: Opaque ID for later retrieval. Auto-generated if None.
            icon: Optional Unicode glyph prepended to the tab label.
            closeable: Whether the tab shows a close button.

        Returns:
            The widget_id string.

        Raises:
            ValueError: If *widget_id* already exists.
        """
        if widget_id is None:
            widget_id = f"sidebar_widget_{len(self._mounted_widgets) + 1}"

        if widget_id in self._mounted_widgets:
            raise ValueError(f"Widget ID '{widget_id}' already exists")

        assert self._sidebar_organizer is not None, "Sidebar organizer not initialized"

        display_name = f"{icon} {tab_name}" if icon else tab_name

        # Wrap in a container so the sidebar organizer fully owns the lifetime.
        container = QWidget(self._sidebar_organizer)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        widget.setParent(container)
        container_layout.addWidget(widget)

        tab_id = self._sidebar_organizer.add_tab_widget(container, display_name, closeable)

        self._mounted_widgets[widget_id] = widget
        self._sidebar_tabs[widget_id] = tab_id

        self.set_status(f"Added sidebar widget: {tab_name}")

        if self.on_sidebar_widget_mounted:
            try:
                self.on_sidebar_widget_mounted(widget, "sidebar")
            except Exception as e:
                print(f"Error in on_sidebar_widget_mounted callback: {e}")

        return widget_id

    def add_workspace_task_frame(
        self,
        task_frame: TaskFrame,
        raise_frame: bool = True,
    ) -> str:
        """Add *task_frame* to the main workspace area.

        Args:
            task_frame: The ITaskFrame to add.
            raise_frame: Whether to bring the frame to the front immediately.

        Returns:
            The frame name used as its widget ID.

        Raises:
            ValueError: If task_frame is None or its name already exists.
        """
        if task_frame is None:
            raise ValueError("task_frame must be provided")
        if task_frame.name in self._workspace_frames:
            raise ValueError(f"Widget ID '{task_frame.name}' already exists")
        self._register_workspace_frame(task_frame, raise_frame)
        return task_frame.name

    def clear_sidebar(self) -> None:
        """Remove all sidebar widgets."""
        for widget_id in list(self._mounted_widgets.keys()):
            self.remove_widget(widget_id)
        self.set_status("Sidebar cleared")

    def remove_widget(self, widget_id: str) -> bool:
        """Remove the widget (sidebar or workspace) identified by *widget_id*.

        Returns:
            True if the widget was found and removed; False otherwise.
        """
        removed = False

        if widget_id in self._mounted_widgets:
            tab_id = self._sidebar_tabs.get(widget_id)
            if tab_id and self._sidebar_organizer:
                if self._sidebar_organizer.remove_tab_by_id(tab_id):
                    self._mounted_widgets.pop(widget_id, None)
                    self._sidebar_tabs.pop(widget_id, None)
                    removed = True

        elif widget_id in self._workspace_frames:
            frame = self._workspace_frames.pop(widget_id)
            frame.destroy()
            removed = True

        if removed:
            self.set_status(f"Removed widget: {widget_id}")
            if self.on_sidebar_widget_unmounted:
                try:
                    self.on_sidebar_widget_unmounted(widget_id)
                except Exception as e:
                    print(f"Error in on_sidebar_widget_unmounted callback: {e}")

        return removed

    def get_widget(self, widget_id: str) -> Optional[QWidget | TaskFrame]:
        """Return the widget or task frame for *widget_id*, or None."""
        return self._mounted_widgets.get(widget_id) or self._workspace_frames.get(widget_id)

    def get_all_widget_ids(self) -> dict[str, list[str]]:
        """Return all widget IDs grouped by location."""
        return {
            'sidebar': list(self._mounted_widgets.keys()),
            'workspace': list(self._workspace_frames.keys()),
        }

    # -------- Log window management --------

    def _set_initial_log_window_height(self) -> None:
        self._log().debug("Setting initial log window height")
        height = EnvManager.get(EnvironmentKeys.ui.UI_LOG_WINDOW_HEIGHT, 0.33, float)
        self.set_log_window_height(height)

    def get_log_window_height(self) -> Optional[float]:
        """Return the log window height as a fraction of the total splitter height."""
        if not self._log_splitter:
            return None
        total = self._log_splitter.height()
        if total <= 0:
            return None
        sizes = self._log_splitter.sizes()
        return sizes[-1] / total if sizes else None

    def set_log_window_height(self, perc_of_window: float) -> None:
        """Set the log window height to *perc_of_window* fraction of total height."""
        if not self._log_splitter:
            raise RuntimeError("Log splitter not initialized")
        total = self._log_splitter.height()
        if total <= 0:
            return
        log_px = int(total * perc_of_window)
        self._log_splitter.setSizes([total - log_px, log_px])
        EnvManager.set(EnvironmentKeys.ui.UI_LOG_WINDOW_HEIGHT, str(perc_of_window))

    def _on_log_sash_moved(self, pos: int, index: int) -> None:
        height = self.get_log_window_height()
        for cb in self._sash_callbacks:
            cb('log', height)

    def on_log_sash_moved(self, event=None) -> None:
        """Public hook for the log splitter sash movement."""
        self._on_log_sash_moved(0, 0)

    # -------- Status bar management --------

    def set_status(self, status: str) -> None:
        """Update the status bar message to *status*."""
        self._status_text = status
        if self._status_bar:
            self._status_bar.showMessage(status)

    def get_status(self) -> str:
        """Return the current status bar message."""
        return self._status_text

    # -------- Toolbar management --------

    def add_toolbar_button(self, button_config: CommandButton) -> None:
        """Add a button described by *button_config* to the toolbar."""
        if not self._toolbar:
            raise RuntimeError("Toolbar not initialized")
        label = button_config.icon or button_config.text or ""
        btn = QPushButton(label)
        if button_config.tooltip:
            btn.setToolTip(button_config.tooltip)
        if button_config.command:
            btn.clicked.connect(button_config.command)
        btn.setProperty("_pyrox_button_id", button_config.id)
        self._toolbar.addWidget(btn)

    def remove_toolbar_button(self, button_id: str) -> None:
        """Remove the toolbar button whose ID is *button_id*."""
        if not self._toolbar:
            return
        for action in self._toolbar.actions():
            widget = self._toolbar.widgetForAction(action)
            if widget and widget.property("_pyrox_button_id") == button_id:
                self._toolbar.removeAction(action)
                return

    def add_toolbar_separator(self) -> int:
        """Add a vertical separator to the toolbar. Returns the action count after insertion."""
        if not self._toolbar:
            raise RuntimeError("Toolbar not initialized")
        self._toolbar.addSeparator()
        return len(self._toolbar.actions())

    def get_toolbar(self) -> Optional[QToolBar]:
        """Return the underlying QToolBar, or None if not yet initialized."""
        return self._toolbar

    # ------- Properties --------

    @property
    def main_paned_window(self) -> QSplitter:
        """The horizontal QSplitter containing the sidebar and workspace/log area."""
        if not self._main_splitter:
            raise RuntimeError("Main splitter not initialized")
        return self._main_splitter

    @property
    def log_paned_window(self) -> QSplitter:
        """The vertical QSplitter containing the workspace area and log window."""
        if not self._log_splitter:
            raise RuntimeError("Log splitter not initialized")
        return self._log_splitter

    @property
    def status_bar(self) -> QStatusBar:
        """The QStatusBar at the bottom of the workspace."""
        if not self._status_bar:
            raise RuntimeError("Status bar not initialized")
        return self._status_bar

    @property
    def toolbar_bar(self) -> QToolBar:
        """The QToolBar at the top of the workspace."""
        if not self._toolbar:
            raise RuntimeError("Toolbar not initialized")
        return self._toolbar

    @property
    def workspace_area(self) -> QFrame:
        """The QFrame used as the main content area for task frames."""
        if not self._workspace_area:
            raise RuntimeError("Workspace area not initialized")
        return self._workspace_area

    @property
    def sidebar_organizer(self) -> _SidebarTabWidget:
        """The sidebar QTabWidget."""
        if not self._sidebar_organizer:
            raise RuntimeError("Sidebar organizer not initialized")
        return self._sidebar_organizer


# ---------------------------------------------------------------------------
# Stand-alone demo
# ---------------------------------------------------------------------------

def create_demo_window():  # -> QMainWindow
    """Create a self-contained QMainWindow that showcases the Workspace widget.

    Demonstrates:
    - Sidebar tabs with arbitrary QWidget content
    - Multiple task frames switchable via toolbar buttons
    - Toolbar buttons and separators
    - Status bar updates
    - Log window appending
    - Sidebar toggle button
    - Splitter geometry (sidebar width / log height)

    Usage::

        python pyrox/models/gui/workspace.py
    """
    from PyQt6.QtWidgets import (
        QMainWindow, QLabel, QListWidget,
        QTreeWidget, QTreeWidgetItem, QTextEdit,
    )
    from PyQt6.QtCore import Qt

    # ------------------------------------------------------------------ #
    # Minimal stub that satisfies ITaskFrame just enough for the demo     #
    # ------------------------------------------------------------------ #
    class _DemoFrame(TaskFrame):
        """Lightweight stand-in for a real ITaskFrame."""

        def __init__(self, title: str, color: str) -> None:
            self._name = title
            self._shown = False
            self._on_destroy: list = []
            self._root = QFrame()
            self._root.setFrameShape(QFrame.Shape.StyledPanel)
            self._root.setStyleSheet(f"background:{color};")

            lbl = QLabel(title, self._root)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color:#ffffff; font-size:18px; font-weight:bold;")
            lay = QVBoxLayout(self._root)
            lay.addWidget(lbl)

        # INameable ---------------------------------------------------- #
        def get_name(self) -> str:
            return self._name

        def set_name(self, name: str) -> None:
            self._name = name

        # IGuiComponent ------------------------------------------------ #
        def get_root(self):
            return self._root

        def set_root(self, root) -> None:
            self._root = root

        def get_parent(self):
            return self._root.parent()

        def set_parent(self, parent) -> None:
            pass

        def config(self, *args, **kwargs) -> None:
            pass

        def focus(self) -> None:
            self._root.setFocus()

        def initialize(self, **kwargs) -> bool:
            return True

        def is_visible(self) -> bool:
            return self._root.isVisible()

        def set_visible(self, visible: bool) -> None:
            self._root.setVisible(visible)

        def update(self) -> None:
            self._root.update()

        def get_height(self) -> int:
            return self._root.height()

        def get_width(self) -> int:
            return self._root.width()

        def get_x(self) -> int:
            return self._root.x()

        def get_y(self) -> int:
            return self._root.y()

        # IGuiWidget --------------------------------------------------- #
        def disable(self) -> None:
            self._root.setEnabled(False)

        def enable(self) -> None:
            self._root.setEnabled(True)

        def pack(self, **kwargs) -> None:
            pass

        def pack_propagate(self, propagate: bool) -> None:
            pass

        def pack_forget(self) -> None:
            self._root.setVisible(False)

        def update_idletasks(self) -> None:
            pass

        # IGuiFrame ---------------------------------------------------- #
        def add_child(self, child) -> None:
            pass

        def clear_children(self) -> None:
            pass

        def get_children(self) -> list:
            return []

        def remove_child(self, child) -> None:
            pass

        # ITaskFrame --------------------------------------------------- #
        def get_shown(self) -> bool:
            return self._shown

        def set_shown(self, value: bool) -> None:
            self._shown = value

        def on_destroy(self) -> list:
            return self._on_destroy

        def build(self) -> None:
            pass

        def destroy(self) -> None:
            self._root.deleteLater()

    # ------------------------------------------------------------------ #
    # Build the window                                                    #
    # ------------------------------------------------------------------ #
    window = QMainWindow()
    window.setWindowTitle("Pyrox Workspace Demo")
    window.resize(1280, 800)

    workspace = Workspace(window)
    window.setCentralWidget(workspace)

    # -- Sidebar panels ------------------------------------------------- #
    # 1. A simple tree / file-explorer panel
    tree = QTreeWidget()
    tree.setHeaderLabel("Project")
    tree.setStyleSheet("background:#1e1e1e; color:#cccccc;")
    root_item = QTreeWidgetItem(tree, ["my_project/"])
    for folder in ("models", "services", "interfaces", "tasks"):
        folder_item = QTreeWidgetItem(root_item, [f"{folder}/"])
        for i in range(1, 4):
            QTreeWidgetItem(folder_item, [f"{folder}_{i}.py"])
    tree.expandAll()
    workspace.add_sidebar_widget(tree, "Explorer", widget_id="explorer", icon="📁", closeable=False)

    # 2. A property-list panel
    prop_list = QListWidget()
    prop_list.setStyleSheet("background:#1e1e1e; color:#cccccc;")
    props = [
        "Name: my_application",
        "Version: 1.0.0",
        "Author: Pyrox",
        "Backend: PyQt6",
        "Python: 3.13",
        "Platform: Windows",
    ]
    for p in props:
        prop_list.addItem(p)
    workspace.add_sidebar_widget(prop_list, "Properties", widget_id="properties", icon="⚙")

    # 3. A plain text notes panel
    notes = QTextEdit()
    notes.setStyleSheet("background:#1e1e1e; color:#cccccc;")
    notes.setPlaceholderText("Type notes here...")
    workspace.add_sidebar_widget(notes, "Notes", widget_id="notes", icon="📝")

    # -- Task frames ---------------------------------------------------- #
    frames = [
        _DemoFrame("Dashboard",  "#2b4a6b"),
        _DemoFrame("Editor",     "#3a2b6b"),
        _DemoFrame("Simulation", "#2b6b3a"),
        _DemoFrame("Reports",    "#6b4a2b"),
    ]
    for frame in frames:
        workspace.register_frame(frame, raise_frame=False)  # type: ignore[arg-type]

    # Raise the first frame by default
    workspace.raise_frame(frames[0])  # type: ignore[arg-type]

    # -- Toolbar: one button per task frame + separator + sidebar toggle - #
    for frame in frames:
        def _make_show_cmd(f):
            def _cmd():
                workspace.raise_frame(f)  # type: ignore[arg-type]
                workspace.set_status(f"Showing {f.name}")
            return _cmd
        workspace.add_toolbar_button(CommandButton(
            id=f"show_{frame.name.lower()}",
            text=frame.name,
            tooltip=f"Switch to {frame.name} view",
            command=_make_show_cmd(frame),
        ))

    workspace.add_toolbar_separator()

    workspace.add_toolbar_button(CommandButton(
        id="toggle_sidebar",
        text="⇄ Sidebar",
        tooltip="Toggle sidebar visibility",
        command=lambda: workspace.toggle_sidebar() or None,  # type: ignore[arg-type]
    ))

    workspace.add_toolbar_button(CommandButton(
        id="log_demo",
        text="📋 Log",
        tooltip="Append a demo message to the log window",
        command=lambda: workspace.log_window.append(
            "Demo log message — click 📋 Log again to add more."
        ),
    ))

    # -- Event callbacks ------------------------------------------------ #
    workspace.on_sidebar_toggle = lambda visible: workspace.set_status(
        f"Sidebar {'shown' if visible else 'hidden'}"
    )
    workspace.on_task_frame_mounted = lambda frame, loc: workspace.set_status(
        f"Frame registered: {frame.name} ({loc})"
    )
    workspace.on_workspace_changed = lambda wid: workspace.set_status(
        f"Sidebar selection changed: {wid}"
    )

    workspace.set_status("Workspace demo ready  —  use the toolbar to switch views")
    return window


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = create_demo_window()
    window.show()
    sys.exit(app.exec())

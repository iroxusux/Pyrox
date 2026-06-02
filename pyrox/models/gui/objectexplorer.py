"""Object Explorer panel for the Scene Viewer.

Provides a PyQt6-based side panel that lists every object currently
present in the loaded scene, with optional search filtering, type-based
grouping, and a callback to notify the host (e.g. ``SceneViewerFrame``)
when the user changes selection.

``ObjectExplorer`` is a :class:`~pyrox.models.gui.frame.TaskFrame`
and therefore ships with a title bar and built-in close button.  Mount it
inside a ``QSplitter`` exactly as the property and bridge panels are
mounted in :mod:`pyrox.models.gui.sceneviewer`.

Example Usage:
    ```python
    explorer = ObjectExplorer(
        parent=splitter,
        title="Object Explorer",
        on_selection_changed=lambda obj_id: viewer.select_objects([obj_id]),
    )

    # Populate / refresh when the scene changes
    explorer.set_scene(my_scene)

    # Add to the splitter
    splitter.addWidget(explorer.root)
    ```
"""
from __future__ import annotations

import sys
from typing import Callable, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from pyrox.models.gui.frame import TaskFrame
from pyrox.services.logging import log


class ObjectExplorer(TaskFrame):
    """A resizable side panel that lists all scene objects.

    Objects are grouped by their ``_scene_object_type`` under collapsible
    tree nodes.  A live search bar lets the user filter by name.  Clicking
    a row triggers ``on_selection_changed`` with the selected object's ID
    so the host viewer can synchronise its own selection state.

    Features:
        - Tree view grouped by object type
        - Live name search / filter
        - Refresh button to re-sync with the scene
        - Selection callback consumed by the host viewer

    Attributes:
        scene:                The scene currently being browsed.
        on_selection_changed: Optional callback ``(obj_id: str) -> None``
                              invoked when the user selects a tree row.
    """

    def __init__(
        self,
        parent: QWidget,
        title: str = "Object Explorer",
        width: int = 230,
        on_selection_changed: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Initialise the ObjectExplorer.

        Args:
            parent:               Parent widget (typically a ``QSplitter``).
            title:                Title displayed in the panel's title bar.
            width:                Preferred panel width in pixels.
            on_selection_changed: Optional callback invoked with the selected
                                  object's ID when the tree selection changes.
        """
        super().__init__(name=title, parent=parent)
        self.root.setMinimumWidth(width)

        # self._scene: Optional[IScene] = None
        self._on_selection_changed = on_selection_changed

        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    # def set_scene(self, scene: Optional[IScene]) -> None:
    #     """Bind the explorer to a new (or cleared) scene.

    #     Args:
    #         scene: The scene to explore, or ``None`` to show an empty state.
    #     """
    #     self._scene = scene
    #     self.refresh()

    def refresh(self) -> None:
        """Re-populate the tree from the current scene.

        Safe to call at any time; clears the existing tree and rebuilds it
        from scratch.
        """
        self._tree.clear()

        # if self._scene is None:
        #     self._status_label.setText("No scene loaded")
        #     return

        objects: dict[str, object] = self._scene.scene_objects  # type: ignore[assignment]
        if not objects:
            self._status_label.setText("Scene is empty")
            return

        filter_text = self._search_edit.text().lower().strip()

        # Group by type -------------------------------------------------------
        groups: dict[str, list[object]] = {}
        for obj in objects.values():
            obj_type = getattr(obj, '_scene_object_type', 'Unknown')
            groups.setdefault(obj_type, []).append(obj)

        bold_font = QFont()
        bold_font.setBold(True)

        total = 0
        for group_name, members in sorted(groups.items()):
            matching = [
                obj for obj in members
                if not filter_text or filter_text in obj.get_name().lower()
            ]
            if not matching:
                continue

            group_item = QTreeWidgetItem(self._tree)
            group_item.setText(0, f"{group_name}  ({len(matching)})")
            group_item.setFont(0, bold_font)
            group_item.setData(0, Qt.ItemDataRole.UserRole, None)  # marks as group
            group_item.setExpanded(True)

            for obj in sorted(matching, key=lambda o: o.get_name().lower()):
                obj_id = getattr(obj, 'id', '') or getattr(obj, 'get_id', lambda: '')()
                leaf = QTreeWidgetItem(group_item)
                leaf.setText(0, obj.get_name())
                leaf.setData(0, Qt.ItemDataRole.UserRole, obj_id)
                total += 1

        self._status_label.setText(f"{total} object{'s' if total != 1 else ''}")
        log(self).debug(f"Object explorer refreshed: {total} objects")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the panel's widget hierarchy."""
        content_layout = self.content_frame.layout()
        content_layout.setContentsMargins(6, 6, 6, 4)  # type: ignore[union-attr]
        content_layout.setSpacing(4)  # type: ignore[union-attr]

        # -- Toolbar (search + refresh) ------------------------------------
        toolbar = QWidget(self.content_frame)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(2)

        search_icon = QLabel("🔍", toolbar)
        toolbar_layout.addWidget(search_icon)

        self._search_edit = QLineEdit(toolbar)
        self._search_edit.setPlaceholderText("Search...")
        self._search_edit.textChanged.connect(self._on_search_changed)
        toolbar_layout.addWidget(self._search_edit, 1)

        refresh_btn = QPushButton("↺", toolbar)
        refresh_btn.setFixedWidth(28)
        refresh_btn.setToolTip("Refresh object list")
        refresh_btn.clicked.connect(self.refresh)
        toolbar_layout.addWidget(refresh_btn)

        content_layout.addWidget(toolbar)  # type: ignore[union-attr]

        # -- Tree ------------------------------------------------------
        self._tree = QTreeWidget(self.content_frame)
        self._tree.setHeaderHidden(True)
        self._tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self._tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._tree.itemSelectionChanged.connect(self._on_tree_select)
        self._tree.itemDoubleClicked.connect(self._on_tree_double_click)
        content_layout.addWidget(self._tree, 1)  # type: ignore[union-attr]

        # -- Status bar ------------------------------------------------
        separator = QFrame(self.content_frame)
        separator.setFrameShape(QFrame.Shape.HLine)
        content_layout.addWidget(separator)  # type: ignore[union-attr]

        self._status_label = QLabel("No scene loaded", self.content_frame)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        content_layout.addWidget(self._status_label)  # type: ignore[union-attr]

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_search_changed(self) -> None:
        """Re-filter the tree whenever the search text changes."""
        self.refresh()

    def _on_tree_select(self) -> None:
        """Fire the selection callback when the user clicks a leaf row.

        Group header rows (where UserRole data is None) are ignored.
        """
        selected = self._tree.selectedItems()
        if not selected:
            return

        item = selected[0]
        obj_id = item.data(0, Qt.ItemDataRole.UserRole)
        if obj_id is None:
            return  # group header — ignore

        if self._on_selection_changed is not None:
            self._on_selection_changed(obj_id)

    def _on_tree_double_click(self, item: QTreeWidgetItem) -> None:
        """Collapse/expand group nodes on double-click; no-op for leaf rows."""
        if item.data(0, Qt.ItemDataRole.UserRole) is None:
            item.setExpanded(not item.isExpanded())


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def create_demo_window() -> QWidget:
    """Create a standalone demo window for :class:`ObjectExplorer`.

    Builds a realistic mock scene with objects in several categories so every
    feature of the panel (grouping, search, selection callback, empty / loaded
    states) can be exercised without depending on a live scene engine.

    Returns:
        QWidget: The configured root window.
    """
    # ------------------------------------------------------------------
    # Lightweight stand-ins for IScene / ISceneObject
    # ------------------------------------------------------------------

    class _MockObject:
        def __init__(self, obj_id: str, name: str, obj_type: str) -> None:
            self.id = obj_id
            self._name = name
            self._scene_object_type = obj_type

        def get_name(self) -> str:
            return self._name

    class _MockScene:
        def __init__(self, objects: list[_MockObject]) -> None:
            self.scene_objects: dict[str, _MockObject] = {o.id: o for o in objects}

    # ------------------------------------------------------------------
    # Sample scene data
    # ------------------------------------------------------------------

    _CONVEYOR_OBJECTS = [
        _MockObject('conv_001', 'Main Infeed Conveyor', 'Conveyor'),
        _MockObject('conv_002', 'Accumulation Lane A', 'Conveyor'),
        _MockObject('conv_003', 'Transfer Belt 1', 'Conveyor'),
        _MockObject('conv_004', 'Exit Spiral', 'Conveyor'),
    ]

    _SENSOR_OBJECTS = [
        _MockObject('sens_001', 'Photo Eye PE-01', 'Sensor'),
        _MockObject('sens_002', 'Photo Eye PE-02', 'Sensor'),
        _MockObject('sens_003', 'Proximity PX-01', 'Sensor'),
        _MockObject('sens_004', 'Light Curtain LC-01', 'Sensor'),
        _MockObject('sens_005', 'Barcode Scanner BC-01', 'Sensor'),
    ]

    _MOTOR_OBJECTS = [
        _MockObject('mtr_001', 'Drive M1 — Infeed', 'Motor'),
        _MockObject('mtr_002', 'Drive M2 — Accumulation', 'Motor'),
        _MockObject('mtr_003', 'Drive M3 — Exit', 'Motor'),
    ]

    _ROBOT_OBJECTS = [
        _MockObject('rob_001', 'Pick & Place Robot A', 'Robot'),
        _MockObject('rob_002', 'Pick & Place Robot B', 'Robot'),
    ]

    _FULL_SCENE = _MockScene(
        _CONVEYOR_OBJECTS + _SENSOR_OBJECTS + _MOTOR_OBJECTS + _ROBOT_OBJECTS
    )

    _SMALL_SCENE = _MockScene(_CONVEYOR_OBJECTS[:2] + _SENSOR_OBJECTS[:2])
    _EMPTY_SCENE = _MockScene([])

    # ------------------------------------------------------------------
    # Root window
    # ------------------------------------------------------------------

    window = QWidget()
    window.setWindowTitle("ObjectExplorer — Demo")
    window.resize(750, 520)

    main_layout = QVBoxLayout(window)
    main_layout.setContentsMargins(8, 8, 8, 0)
    main_layout.setSpacing(4)

    # ------------------------------------------------------------------
    # Top: scene controls
    # ------------------------------------------------------------------

    toolbar = QWidget(window)
    toolbar_layout = QHBoxLayout(toolbar)
    toolbar_layout.setContentsMargins(0, 0, 0, 0)
    toolbar_layout.setSpacing(4)
    toolbar_layout.addWidget(QLabel("Load scene:"))

    status_label = QLabel("No object selected yet.")

    def _on_selection(obj_id: str) -> None:
        status_label.setText(f"Selected object ID: {obj_id}")

    explorer = ObjectExplorer(
        parent=window,
        title="Object Explorer",
        on_selection_changed=_on_selection,
    )

    for btn_text, scene in [
        ("Full scene (14 objects)", _FULL_SCENE),
        ("Small scene (4 objects)", _SMALL_SCENE),
        ("Empty scene", _EMPTY_SCENE),
        ("Clear (no scene)", None),
    ]:
        btn = QPushButton(btn_text, toolbar)
        btn.clicked.connect(lambda checked, s=scene: explorer.set_scene(s))  # type: ignore[arg-type]
        toolbar_layout.addWidget(btn)

    toolbar_layout.addStretch()
    main_layout.addWidget(toolbar)

    # ------------------------------------------------------------------
    # Explorer panel
    # ------------------------------------------------------------------

    main_layout.addWidget(explorer.root, 1)
    explorer.set_scene(_FULL_SCENE)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------

    separator = QFrame(window)
    separator.setFrameShape(QFrame.Shape.HLine)
    main_layout.addWidget(separator)
    main_layout.addWidget(status_label)

    return window


if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo_window = create_demo_window()
    demo_window.show()
    sys.exit(app.exec())

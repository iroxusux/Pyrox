"""Object Explorer panel for the Scene Viewer.

Provides a Tkinter-based side panel that lists every object currently
present in the loaded scene, with optional search filtering, type-based
grouping, and a callback to notify the host (e.g. ``SceneViewerFrame``)
when the user changes selection.

``TkObjectExplorer`` is a :class:`~pyrox.models.gui.tk.frame.TkinterTaskFrame`
and therefore ships with a title bar and built-in close button.  Mount it
inside a ``ttk.PanedWindow`` exactly as the property and bridge panels are
mounted in :mod:`pyrox.models.gui.sceneviewer`.

Example Usage:
    ```python
    explorer = TkObjectExplorer(
        parent=paned_window,
        title="Object Explorer",
        on_selection_changed=lambda obj_ids: viewer.select_objects(obj_ids),
    )

    # Populate / refresh when the scene changes
    explorer.set_scene(my_scene)

    # Add to the paned window
    paned_window.add(explorer.root, weight=0)
    ```
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from pyrox.interfaces import IScene, ISceneObject
from pyrox.models.gui.tk.frame import TkinterTaskFrame
from pyrox.services.logging import log


class TkObjectExplorer(TkinterTaskFrame):
    """A resizable side panel that lists all scene objects.

    Objects are grouped by their ``scene_object_type`` under collapsible
    tree nodes.  A live search bar lets the user filter by name.  Clicking
    a row triggers ``on_selection_changed`` with the selected object's ID
    so the host viewer can synchronise its own selection state.

    Features:
        - Tree view grouped by object type
        - Live name search / filter
        - Refresh button to re-sync with the scene
        - Selection callback consumed by the host viewer
        - Follows the same ``TkinterTaskFrame`` conventions as
          ``TkPropertyPanel`` and ``SceneBridgeDialog``

    Attributes:
        scene:                The scene currently being browsed.
        on_selection_changed: Optional callback ``(obj_id: str) -> None``
                              invoked when the user selects a tree row.
    """

    def __init__(
        self,
        parent: tk.Widget | tk.Misc,
        title: str = "object explorer",
        width: int = 230,
        on_selection_changed: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Initialise the TkObjectExplorer.

        Args:
            parent:               Parent widget (typically a ``ttk.PanedWindow``).
            title:                Title displayed in the panel's title bar.
            width:                Preferred panel width in pixels.
            on_selection_changed: Optional callback invoked with the selected
                                  object's ID when the tree selection changes.
        """
        TkinterTaskFrame.__init__(self, name=title, parent=parent)  # type: ignore[arg-type]
        self.root.configure(width=width)

        self._title = title
        self._scene: Optional[IScene] = None
        self._on_selection_changed = on_selection_changed
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search_changed)

        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_scene(self, scene: Optional[IScene]) -> None:
        """Bind the explorer to a new (or cleared) scene.

        Args:
            scene: The scene to explore, or ``None`` to show an empty state.
        """
        self._scene = scene
        self.refresh()

    def refresh(self) -> None:
        """Re-populate the tree from the current scene.

        Safe to call at any time; clears the existing tree and rebuilds it
        from scratch.
        """
        self._tree.delete(*self._tree.get_children())

        if self._scene is None:
            self._status_label.config(text="No scene loaded")
            return

        objects: dict[str, ISceneObject] = self._scene.scene_objects  # type: ignore[assignment]
        if not objects:
            self._status_label.config(text="Scene is empty")
            return

        filter_text = self._search_var.get().lower().strip()

        # Group by type -------------------------------------------------------
        groups: dict[str, list[ISceneObject]] = {}
        for obj in objects.values():
            obj_type = getattr(obj, '_scene_object_type', 'Unknown')
            groups.setdefault(obj_type, []).append(obj)

        total = 0
        for group_name, members in sorted(groups.items()):
            matching = [
                obj for obj in members
                if not filter_text or filter_text in obj.get_name().lower()
            ]
            if not matching:
                continue

            group_node = self._tree.insert(
                '',
                tk.END,
                text=f"{group_name}  ({len(matching)})",
                open=True,
                tags=('group',),
            )

            for obj in sorted(matching, key=lambda o: o.get_name().lower()):
                obj_id = getattr(obj, 'id', '') or getattr(obj, 'get_id', lambda: '')()
                self._tree.insert(
                    group_node,
                    tk.END,
                    iid=obj_id,
                    text=obj.get_name(),
                    values=(obj_id, group_name),
                    tags=('object',),
                )
                total += 1

        self._status_label.config(text=f"{total} object{'s' if total != 1 else ''}")
        log(self).debug(f"Object explorer refreshed: {total} objects")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the panel's widget hierarchy."""
        # -- Toolbar (search + refresh) ------------------------------------
        toolbar = ttk.Frame(self.content_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=6, pady=(6, 2))

        ttk.Label(toolbar, text="🔍", width=2).pack(side=tk.LEFT)

        search_entry = ttk.Entry(toolbar, textvariable=self._search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        refresh_btn = ttk.Button(toolbar, text="↺", width=3, command=self.refresh)
        refresh_btn.pack(side=tk.RIGHT, padx=2)
        self._create_tooltip(refresh_btn, "Refresh object list")

        # -- Tree with scrollbar -------------------------------------------
        tree_frame = ttk.Frame(self.content_frame)
        tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6, pady=4)

        self._tree = ttk.Treeview(
            tree_frame,
            columns=('id', 'type'),
            show='tree',
            selectmode='browse',
        )
        self._tree.column('#0', width=160, stretch=True)
        self._tree.column('id', width=0, stretch=False)
        self._tree.column('type', width=0, stretch=False)

        # Visual distinction between group headers and leaf rows
        self._tree.tag_configure('group', font=('', 9, 'bold'))
        self._tree.tag_configure('object', font=('', 9))

        yscroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=yscroll.set)

        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._tree.bind('<<TreeviewSelect>>', self._on_tree_select)
        self._tree.bind('<Double-1>', self._on_tree_double_click)

        # -- Status bar ----------------------------------------------------
        self._status_label = ttk.Label(
            self.content_frame,
            text="No scene loaded",
            anchor=tk.W,
        )
        self._status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=(0, 4))

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_search_changed(self, *_) -> None:
        """Re-filter the tree whenever the search text changes."""
        self.refresh()

    def _on_tree_select(self, event) -> None:  # noqa: ANN001
        """Fire the selection callback when the user clicks a leaf row.

        Group header rows are ignored.
        """
        selected = self._tree.selection()
        if not selected:
            return

        item_id = selected[0]
        tags = self._tree.item(item_id, 'tags')
        if 'group' in tags:
            return  # Don't propagate group-header clicks

        if self._on_selection_changed is not None:
            self._on_selection_changed(item_id)

    def _on_tree_double_click(self, event) -> None:  # noqa: ANN001
        """Collapse/expand group nodes on double-click; no-op for leaf rows."""
        item_id = self._tree.identify_row(event.y)
        if not item_id:
            return
        tags = self._tree.item(item_id, 'tags')
        if 'group' in tags:
            currently_open = self._tree.item(item_id, 'open')
            self._tree.item(item_id, open=not currently_open)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_tooltip(self, widget: tk.Widget, text: str) -> None:
        """Attach a lightweight tooltip to *widget*.

        Args:
            widget: Target widget.
            text:   Tooltip text.
        """
        def _show(event):  # noqa: ANN001
            tip = tk.Toplevel()
            tip.wm_overrideredirect(True)
            tip.wm_geometry(f"+{event.x_root + 12}+{event.y_root + 10}")
            tk.Label(
                tip,
                text=text,
                background="#ffffe0",
                relief=tk.SOLID,
                borderwidth=1,
                padx=4,
                pady=2,
            ).pack()
            widget._tooltip = tip  # type: ignore[attr-defined]

        def _hide(event):  # noqa: ANN001
            if hasattr(widget, '_tooltip'):
                widget._tooltip.destroy()  # type: ignore[attr-defined]
                del widget._tooltip  # type: ignore[attr-defined]

        widget.bind('<Enter>', _show)
        widget.bind('<Leave>', _hide)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def create_demo_window() -> tk.Tk:
    """Create a standalone demo window for :class:`TkObjectExplorer`.

    Builds a realistic mock scene with objects in several categories so every
    feature of the panel (grouping, search, selection callback, empty / loaded
    states) can be exercised without depending on a live scene engine.

    Returns:
        tk.Tk: The configured root window (caller must call ``mainloop()``).
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

    root = tk.Tk()
    root.title("TkObjectExplorer — Demo")
    root.geometry("750x520")

    # ------------------------------------------------------------------
    # Top: selection feedback + scene controls
    # ------------------------------------------------------------------

    toolbar = ttk.Frame(root)
    toolbar.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(8, 0))

    ttk.Label(toolbar, text="Load scene:").pack(side=tk.LEFT, padx=(0, 4))

    status_var = tk.StringVar(value="No object selected yet.")

    def _on_selection(obj_id: str) -> None:
        status_var.set(f"Selected object ID: {obj_id}")

    explorer = TkObjectExplorer(
        parent=root,
        title="Object Explorer",
        on_selection_changed=_on_selection,
    )

    ttk.Button(
        toolbar,
        text="Full scene (14 objects)",
        command=lambda: explorer.set_scene(_FULL_SCENE),  # type: ignore[arg-type]
    ).pack(side=tk.LEFT, padx=2)

    ttk.Button(
        toolbar,
        text="Small scene (4 objects)",
        command=lambda: explorer.set_scene(_SMALL_SCENE),  # type: ignore[arg-type]
    ).pack(side=tk.LEFT, padx=2)

    ttk.Button(
        toolbar,
        text="Empty scene",
        command=lambda: explorer.set_scene(_EMPTY_SCENE),  # type: ignore[arg-type]
    ).pack(side=tk.LEFT, padx=2)

    ttk.Button(
        toolbar,
        text="Clear (no scene)",
        command=lambda: explorer.set_scene(None),
    ).pack(side=tk.LEFT, padx=2)

    # ------------------------------------------------------------------
    # Explorer panel (fills remaining space)
    # ------------------------------------------------------------------

    explorer.root.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    # Kick off with the full scene so there is something to see immediately
    explorer.set_scene(_FULL_SCENE)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------

    ttk.Separator(root, orient=tk.HORIZONTAL).pack(fill=tk.X)
    ttk.Label(
        root,
        textvariable=status_var,
        relief=tk.SUNKEN,
        anchor=tk.W,
        padding=(6, 2),
    ).pack(fill=tk.X, side=tk.BOTTOM)

    return root


if __name__ == "__main__":
    demo_window = create_demo_window()
    demo_window.mainloop()

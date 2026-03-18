"""Object explorer panel management.
This module defines the _SceneViewerObjectExplorerPanel class, which manages the embedded object explorer widget within the scene viewer.
"""
from __future__ import annotations

from typing import Any, Callable
from PyQt6.QtWidgets import QSplitter

from pyrox.interfaces import IScene
from pyrox.models.gui.objectexplorer import ObjectExplorer


class _SceneViewerObjectExplorerPanel:
    """Manages the object explorer panel widget and its visibility state."""

    def __init__(
        self,
        parent: QSplitter,
        on_selection_changed: Callable[[str], None],
    ) -> None:
        self._parent = parent
        self._explorer: ObjectExplorer | None = None
        self._visible: bool = False

        # Public callback wired by SceneViewerFrame
        self.on_selection_changed = on_selection_changed

    # ---- properties ----

    @property
    def visible(self) -> bool:
        return self._visible

    @property
    def explorer(self) -> ObjectExplorer | None:
        return self._explorer

    # ---- lifecycle ----

    def build(self, scene: IScene | None = None) -> '_SceneViewerObjectExplorerPanel':
        """Build and attach the ObjectExplorer widget to the parent splitter."""
        self._explorer = ObjectExplorer(
            parent=self._parent,
            title="object explorer",
            width=230,
            on_selection_changed=self.on_selection_changed,
        )
        self._explorer.set_scene(scene)

        def _on_closed(_frame: Any) -> None:
            self._explorer = None
            self._visible = False

        self._explorer.on_destroy().append(_on_closed)
        self._parent.addWidget(self._explorer.root)
        self._explorer.root.hide()
        return self

    # ---- visibility ----

    def show(self, scene: IScene | None = None) -> None:
        if self._explorer is None:
            self.build(scene=scene)
        if self._explorer is not None:
            self._explorer.root.show()
            if scene is not None:
                self._explorer.set_scene(scene)
            self._visible = True

    def hide(self) -> None:
        if self._explorer is not None:
            self._explorer.root.hide()
        self._visible = False

    def toggle(self, scene: IScene | None = None) -> None:
        self._visible = not self._visible
        if self._visible:
            self.show(scene=scene)
        else:
            self.hide()

    # ---- scene ----

    def set_scene(self, scene: IScene | None) -> None:
        """Propagate a scene change to the explorer widget if it exists."""
        if self._explorer is not None:
            self._explorer.set_scene(scene)


__all__ = [
    '_SceneViewerObjectExplorerPanel',
]

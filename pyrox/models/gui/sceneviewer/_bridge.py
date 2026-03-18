"""Scene viewer bridge panel management. 
This module defines the _SceneViewerBridgePanel class, which manages the embedded scene bridge dialog within the scene viewer.

"""
from __future__ import annotations

from typing import Any
from PyQt6.QtWidgets import QSplitter

from pyrox.interfaces import IScene, ISceneBridge
from pyrox.models.gui.scenebridge import SceneBridgeDialog
from pyrox.services import log, SceneBridgeService


class _SceneViewerBridgePanel:
    """Manages the scene bridge panel widget, its visibility state, and bridge reference."""

    def __init__(self, parent: QSplitter) -> None:
        self._parent = parent
        self._panel: SceneBridgeDialog | None = None
        self._visible: bool = False

    # ---- properties ----

    @property
    def visible(self) -> bool:
        return self._visible

    @property
    def panel(self) -> SceneBridgeDialog | None:
        return self._panel

    # ---- lifecycle ----

    def build(self, scene: IScene | None = None) -> bool:
        """Build the SceneBridgeDialog.  Returns *False* if no bridge is available."""
        bridge = SceneBridgeService.get_bridge()
        if bridge is None:
            log(self).warning("Cannot open bridge panel: no scene bridge is available")
            return False

        self._panel = SceneBridgeDialog(
            parent=self._parent,
            bridge=bridge,
            scene=scene,
        )

        def _on_closed(_frame: Any) -> None:
            self._panel = None
            self._visible = False

        self._panel.on_destroy().append(_on_closed)
        self._parent.addWidget(self._panel.root)
        self._panel.root.hide()
        return True

    # ---- visibility ----

    def show(self, scene: IScene | None = None) -> None:
        if self._panel is None:
            if not self.build(scene=scene):
                self._visible = False
                return
        if self._panel is not None:
            self._panel.root.show()
            self._visible = True

    def hide(self) -> None:
        if self._panel is not None:
            self._panel.root.hide()
        self._visible = False

    def toggle(self, scene: IScene | None = None) -> None:
        self._visible = not self._visible
        if self._visible:
            self.show(scene=scene)
        else:
            self.hide()

    # ---- scene/bridge update ----

    def update_scene(self, scene: IScene | None, bridge: ISceneBridge | None) -> None:
        """Update the embedded dialog when the active scene or bridge changes."""
        if self._panel is not None:
            if bridge is not None:
                self._panel.bridge = bridge
            self._panel.scene = scene


__all__ = [
    '_SceneViewerBridgePanel',
]

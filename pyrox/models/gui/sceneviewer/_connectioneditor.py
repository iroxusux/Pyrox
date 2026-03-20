"""Scene viewer connection editor panel management.

This module defines the _SceneViewerConnectionEditorPanel class, which manages
the embedded connection editor within the scene viewer.
"""
from PyQt6.QtWidgets import QSplitter

from pyrox.interfaces import IScene
from pyrox.models.gui.connectioneditor import ConnectionEditor
from pyrox.services import log


class _SceneViewerConnectionEditorPanel:
    """Manages the connection editor widget, its visibility state, and scene reference."""

    def __init__(self, parent: QSplitter) -> None:
        self._parent = parent
        self._panel: ConnectionEditor | None = None
        self._visible: bool = False

    # ---- properties ----

    @property
    def visible(self) -> bool:
        return self._visible

    @property
    def panel(self) -> ConnectionEditor | None:
        return self._panel

    # ---- lifecycle ----

    def build(self, scene: IScene | None = None) -> bool:
        """Build the ConnectionEditor widget.  Returns *False* if no scene is available."""
        if scene is None:
            log(self).warning("Cannot open connection editor: no scene is available")
            return False

        self._panel = ConnectionEditor(
            parent=self._parent,
            scene=scene,
        )
        self._parent.addWidget(self._panel)
        self._panel.hide()
        return True

    # ---- visibility ----

    def show(self, scene: IScene | None = None) -> None:
        if self._panel is None:
            if not self.build(scene=scene):
                self._visible = False
                return
        if self._panel is not None:
            self._panel.show()
            self._visible = True

    def hide(self) -> None:
        if self._panel is not None:
            self._panel.hide()
        self._visible = False

    def toggle(self, scene: IScene | None = None) -> None:
        self._visible = not self._visible
        if self._visible:
            self.show(scene=scene)
        else:
            self.hide()

    # ---- scene update ----

    def update_scene(self, scene: IScene | None) -> None:
        """Reload the editor when the active scene changes."""
        if self._panel is not None and scene is not None:
            self._panel.load_scene(scene)


__all__ = [
    '_SceneViewerConnectionEditorPanel',
]

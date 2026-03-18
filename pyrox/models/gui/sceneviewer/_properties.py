"""Properties panel management.
This module defines the _SceneViewerPropertiesPanel class, which manages the embedded properties panel widget within the scene viewer.
"""
from __future__ import annotations

from typing import Any, Callable

from PyQt6.QtWidgets import QSplitter

from pyrox.interfaces import IScene
from pyrox.models.gui import PropertyPanel


class _SceneViewerPropertiesPanel:
    """Manages the properties panel widget, visibility state, and selection-driven refresh."""

    def __init__(
        self,
        parent: QSplitter,
        on_property_changed: Callable[[str, Any], None],
    ) -> None:
        self._parent = parent
        self._panel: PropertyPanel | None = None
        self._visible: bool = False
        self._current_object_id: str | None = None
        self._previous_selection: set[str] = set()

        # Public callback wired by SceneViewerFrame
        self.on_property_changed = on_property_changed

    # ---- properties ----

    @property
    def visible(self) -> bool:
        return self._visible

    @property
    def panel(self) -> PropertyPanel | None:
        return self._panel

    # ---- lifecycle ----

    def build(self) -> '_SceneViewerPropertiesPanel':
        """Build and attach the PropertyPanel widget to the parent splitter."""
        self._panel = PropertyPanel(
            parent=self._parent,
            title="Object Properties",
            width=250,
            on_property_changed=self.on_property_changed,
        )

        def _on_closed(_frame: Any) -> None:
            self._panel = None
            self._visible = False
            self._current_object_id = None

        self._panel.on_destroy().append(_on_closed)
        self._parent.addWidget(self._panel.root)
        self._panel.root.hide()
        return self

    # ---- visibility ----

    def show(self) -> None:
        if self._panel is None:
            self.build()
        if self._panel is not None:
            self._panel.root.show()
            self._visible = True

    def hide(self) -> None:
        if self._panel is not None:
            self._panel.root.hide()
        self._visible = False

    def toggle(self) -> None:
        self._visible = not self._visible
        if self._visible:
            self.show()
        else:
            self.hide()

    # ---- content ----

    def refresh(
        self,
        selected_ids: set[str],
        scene: IScene | None,
        force_refresh: bool = False,
    ) -> None:
        """Update the panel to reflect the current selection from *scene*."""
        if not self._panel:
            return

        if not selected_ids:
            if self._current_object_id is not None:
                self._panel.set_object(None)
                self._current_object_id = None
            return

        if len(selected_ids) > 1:
            if self._current_object_id != 'MULTIPLE':
                self._panel.set_title(f"Properties ({len(selected_ids)} selected)")
                self._panel.set_object(None)
                self._current_object_id = 'MULTIPLE'
            return

        if not scene:
            return

        obj_id = next(iter(selected_ids))
        scene_obj = scene.get_scene_object(obj_id)
        if not scene_obj:
            return

        if obj_id != self._current_object_id or force_refresh:
            self._panel.set_title(f"Properties: {scene_obj.name}")
            readonly_props = {"id", "type", "scene_object_type"}
            all_props = scene_obj.get_properties()
            physics_keys = set(scene_obj.physics_body.get_properties().keys())
            scene_obj_props = {k: v for k, v in all_props.items() if k not in physics_keys}
            physics_props = {k: v for k, v in all_props.items() if k in physics_keys}
            self._panel.set_sections(
                {"Scene Object": scene_obj_props, "Physics Body": physics_props},
                readonly_properties=readonly_props,
                section_objects={
                    "Scene Object": scene_obj,
                    "Physics Body": scene_obj,  # SceneObject.set_property delegates to physics_body
                },
            )
            self._current_object_id = obj_id
        else:
            self._panel.update_values()

    def refresh_if_selection_changed(
        self,
        current_selection: set[str],
        scene: IScene | None,
    ) -> None:
        """Call *refresh* only when the selection set has changed since last time."""
        if current_selection != self._previous_selection:
            self.refresh(current_selection, scene, force_refresh=True)
            self._previous_selection = current_selection.copy()


__all__ = [
    '_SceneViewerPropertiesPanel',
]

"""Panel helper classes for SceneViewerFrame.

Each class owns the UI widget for a single side-panel, its visibility state,
and any logic that belongs exclusively to that panel.  The owning
SceneViewerFrame wires up public callbacks after instantiation, following the
same pattern as _SceneViewerToolbar and _SceneViewerUserMode.
"""
from __future__ import annotations

from typing import Any, Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from pyrox.interfaces import IScene, ISceneBridge
from pyrox.models.gui import PropertyPanel
from pyrox.models.gui.objectexplorer import ObjectExplorer
from pyrox.models.gui.scenebridge import SceneBridgeDialog
from pyrox.models.physics import PhysicsSceneFactory
from pyrox.models.scene import SceneObjectFactory
from pyrox.services import log, SceneBridgeService


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
                    "Physics Body": scene_obj.physics_body,
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


class _SceneViewerObjectPalettePanel:
    """Manages the floating object palette window and template selection state."""

    def __init__(
        self,
        content_frame: QWidget,
        on_template_selected: Callable[[str, bool], None],
    ) -> None:
        self._content_frame = content_frame
        self._frame: QWidget | None = None
        self._visible: bool = False
        self._positioned: bool = False
        self._current_template: str | None = None
        self._current_template_is_scene_object: bool = False
        self._palette_content_widget: QWidget | None = None
        self._palette_content_layout: QVBoxLayout | None = None
        self._templates: dict = {}
        self._scene_object_templates: dict = {}

        # Public callback wired by SceneViewerFrame
        self.on_template_selected = on_template_selected

    # ---- properties ----

    @property
    def visible(self) -> bool:
        return self._visible

    @property
    def templates(self) -> dict:
        return self._templates

    @property
    def scene_object_templates(self) -> dict:
        return self._scene_object_templates

    def get_selected_template(self) -> tuple[str | None, bool]:
        """Return ``(template_name, is_scene_object)`` for the pending placement."""
        return self._current_template, self._current_template_is_scene_object

    def clear_template(self) -> None:
        """Clear the pending template selection after placement."""
        self._current_template = None
        self._current_template_is_scene_object = False

    # ---- lifecycle ----

    def build(self) -> '_SceneViewerObjectPalettePanel':
        """Build the floating palette tool window."""
        self._frame = QWidget(
            None,
            Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint,
        )
        self._frame.setWindowTitle("Object Palette")
        self._frame.setMinimumSize(200, 300)
        self._frame.resize(220, 500)

        palette_layout = QVBoxLayout(self._frame)
        palette_layout.setContentsMargins(4, 4, 4, 4)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        palette_layout.addWidget(scroll_area)

        self._palette_content_widget = QWidget()
        self._palette_content_layout = QVBoxLayout(self._palette_content_widget)
        self._palette_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(self._palette_content_widget)

        self._frame.hide()
        return self

    # ---- visibility ----

    def show(self) -> None:
        if not self._frame:
            return
        if not self._positioned:
            global_top_left = self._content_frame.mapToGlobal(
                self._content_frame.rect().topLeft()
            )
            self._frame.move(global_top_left.x() + 10, global_top_left.y() + 40)
            self._positioned = True
        self._frame.show()
        self._frame.raise_()
        self._visible = True

    def hide(self) -> None:
        if self._frame:
            self._frame.hide()
        self._visible = False

    def toggle(self) -> None:
        self._visible = not self._visible
        if self._visible:
            self.show()
        else:
            self.hide()

    # ---- templates ----

    def initialize_templates(self) -> None:
        """Fetch all registered templates and populate the palette buttons."""
        if self._palette_content_layout is None or self._palette_content_widget is None:
            return

        self._templates = PhysicsSceneFactory.get_all_templates()
        self._scene_object_templates = SceneObjectFactory.get_all_templates()

        # Clear any previously built buttons
        while self._palette_content_layout.count():
            item = self._palette_content_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()  # type: ignore[union-attr]

        if self._templates:
            physics_label = QLabel("Physics Objects")
            physics_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            self._palette_content_layout.addWidget(physics_label)

            for template_name in self._templates:
                btn = QPushButton(text=template_name, parent=self._palette_content_widget)
                btn.clicked.connect(
                    lambda _checked, name=template_name: self._on_template_button_clicked(name, False)
                )
                self._palette_content_layout.addWidget(btn)

        if self._scene_object_templates:
            scene_label = QLabel("Scene Objects")
            scene_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            self._palette_content_layout.addWidget(scene_label)

            for template_name in self._scene_object_templates:
                btn = QPushButton(text=template_name, parent=self._palette_content_widget)
                btn.clicked.connect(
                    lambda _checked, name=template_name: self._on_template_button_clicked(name, True)
                )
                self._palette_content_layout.addWidget(btn)

    def _on_template_button_clicked(self, template_name: str, is_scene_object: bool) -> None:
        self._current_template = template_name
        self._current_template_is_scene_object = is_scene_object
        if callable(self.on_template_selected):
            self.on_template_selected(template_name, is_scene_object)


__all__ = [
    '_SceneViewerPropertiesPanel',
    '_SceneViewerObjectExplorerPanel',
    '_SceneViewerBridgePanel',
    '_SceneViewerObjectPalettePanel',
]

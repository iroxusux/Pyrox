"""2D Scene Viewer Frame for Pyrox.

This module provides a PyQt6-based graphics view frame for viewing and interacting
with 2D scenes containing sprites and simple shapes. Supports panning, zooming,
and integrates with the Scene workflow.
"""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Callable
from PyQt6.QtCore import Qt, QRectF, QLineF, QTimer, QPointF
from PyQt6.QtGui import (
    QBrush, QColor, QPen, QFont, QCursor, QContextMenuEvent,
    QKeyEvent, QMouseEvent, QWheelEvent, QResizeEvent,
)
from PyQt6.QtWidgets import (
    QGraphicsEllipseItem, QGraphicsLineItem,
    QGraphicsRectItem, QGraphicsScene, QGraphicsSimpleTextItem,
    QGraphicsView, QLabel, QPushButton,
    QScrollArea, QSplitter, QVBoxLayout, QWidget,
    QApplication, QMainWindow
)
from pyrox.interfaces import (
    IScene,
    ISceneBridge,
    ISceneObject,
    ISceneRunnerService,
    IViewport
)
from pyrox.models.physics.base import BasePhysicsBody
from pyrox.models.gui.frame import TaskFrame
from pyrox.models.gui import PropertyPanel
from pyrox.models.gui.contextmenu import PyroxContextMenu, MenuItem
from pyrox.models.gui.connectioneditor import ConnectionEditor
from pyrox.models.gui.objectexplorer import ObjectExplorer
from pyrox.models.gui.scenebridge import SceneBridgeDialog
from pyrox.models.physics import PhysicsSceneFactory
from pyrox.models.scene import Scene, SceneGroup, SceneObject
from pyrox.services import (
    log,
    SceneBridgeService,
    CanvasObjectManagmenentService,
    ViewportHostingService,
    MenuRegistry,
    SceneEventType,
    SceneEventBus,
)
from pyrox.services.viewport import ViewportEventBus, ViewportEvent, ViewportEventType
from pyrox.models.gui.sceneviewer._toolbar import _SceneViewerToolbar
from pyrox.models.gui.sceneviewer._user_mode import _SceneViewerUserMode, UserMode


class _SceneCanvasView(QGraphicsView):
    """Internal QGraphicsView subclass that routes Qt events into SceneViewerFrame."""

    def __init__(
        self,
        scene: QGraphicsScene,
        frame: 'SceneViewerFrame',
        parent: QWidget | None = None,
    ):
        super().__init__(scene, parent)
        self._frame = frame
        self._is_panning = False
        self._pan_start_x: float = 0.0
        self._pan_start_y: float = 0.0
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # ---- mouse ----

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return
        btn = event.button()
        if btn == Qt.MouseButton.LeftButton:
            pos = event.position()
            if self._frame._mode == UserMode.INSERT:
                sx = (pos.x() - self._frame.viewport.x) / self._frame.viewport.zoom
                sy = (pos.y() - self._frame.viewport.y) / self._frame.viewport.zoom
                self._frame._place_object_from_template(sx, sy)
            elif self._frame._mode == UserMode.SELECT:
                self._frame._on_select_click_qt(event)
        elif btn == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._pan_start_x = event.position().x()
            self._pan_start_y = event.position().y()
            self.setCursor(Qt.CursorShape.SizeAllCursor)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return
        buttons = event.buttons()
        if buttons & Qt.MouseButton.LeftButton:
            if self._frame._mode == UserMode.SELECT:
                self._frame._on_drag_object_qt(event)
        elif buttons & Qt.MouseButton.MiddleButton and self._is_panning:
            pos = event.position()
            dx = pos.x() - self._pan_start_x
            dy = pos.y() - self._pan_start_y
            self._frame.viewport.x += dx
            self._frame.viewport.y += dy
            self._pan_start_x = pos.x()
            self._pan_start_y = pos.y()
            ViewportEventBus.publish(ViewportEvent(event_type=ViewportEventType.PAN))
            self._frame._mark_dirty()

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return
        btn = event.button()
        if btn == Qt.MouseButton.LeftButton:
            if self._frame._mode == UserMode.SELECT:
                self._frame._on_drag_end_qt(event)
        elif btn == Qt.MouseButton.MiddleButton:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def wheelEvent(self, event: QWheelEvent | None) -> None:
        if event is None:
            return
        x = event.position().x()
        y = event.position().y()
        if event.angleDelta().y() > 0:
            self._frame._viewport_service.zoom.zoom_in(center_x=x, center_y=y)
        else:
            self._frame._viewport_service.zoom.zoom_out(center_x=x, center_y=y)
        self._frame._mark_dirty()

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if event is None:
            return
        key = event.key()
        mods = event.modifiers()
        ctrl = Qt.KeyboardModifier.ControlModifier
        ctrl_shift = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
        ctrl_alt = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier
        if key == Qt.Key.Key_Delete:
            self._frame.delete_selected_objects()
        elif key == Qt.Key.Key_Escape:
            self._frame.clear_selection()
        elif key == Qt.Key.Key_L and mods == ctrl:
            self._frame.toggle_entity_names()
        elif key == Qt.Key.Key_BracketRight and mods == ctrl:
            self._frame._context_layer_up()
        elif key == Qt.Key.Key_BracketLeft and mods == ctrl:
            self._frame._context_layer_down()
        elif key == Qt.Key.Key_BracketRight and mods == ctrl_shift:
            self._frame._context_bring_to_front()
        elif key == Qt.Key.Key_BracketLeft and mods == ctrl_shift:
            self._frame._context_send_to_back()
        elif key == Qt.Key.Key_G and mods == ctrl_alt:
            self._frame._context_group_selected()
        elif key == Qt.Key.Key_U and mods == ctrl_alt:
            self._frame._context_ungroup_selected()
        else:
            super().keyPressEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent | None) -> None:
        if event is not None:
            self._frame._on_right_click_qt(event)

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        w = max(self.width(), 2000)
        h = max(self.height(), 2000)
        sc = self.scene()
        if sc is not None:
            sc.setSceneRect(0, 0, w, h)
        super().resizeEvent(event)
        # Keep the view anchored at scene origin so manual pan/zoom item
        # positioning is 1:1 with view pixels (QGraphicsView centres by default).
        self.horizontalScrollBar().setValue(0)
        self.verticalScrollBar().setValue(0)
        self._frame._mark_dirty()


class SceneViewerFrame(TaskFrame):
    """A 2D scene viewer with pan and zoom support built on QGraphicsView.

    This frame provides a visual canvas for rendering scene objects with
    interactive pan and zoom controls. Integrates with the Scene and
    SceneObject interfaces for managing displayed content.

    Features:
        - QGraphicsScene/View-based 2D rendering
        - Mouse-based panning (middle mouse drag)
        - Zoom in/out with mouse wheel
        - Customizable toolbar
        - Scene integration

    Attributes:
        scene: The currently loaded scene
        viewport: Current viewport state (zoom, pan offsets)
    """

    _application_menu_built: bool = False

    # ==================== Initialization ====================

    def __init__(
        self,
        parent: QWidget,
        name: str = "scene viewer",
        runner: type[ISceneRunnerService] | None = None,
        scene: IScene | None = None
    ):
        """Initialize the SceneViewerFrame.

        Args:
            parent: Parent widget
            name: Name of the frame displayed in title bar
            scene: Optional scene to load initially
        """
        super().__init__(
            name=name,
            parent=parent
        )
        self._scene = scene
        self._runner = runner
        self._canvas_object_management_service = CanvasObjectManagmenentService()
        self._viewport_service = ViewportHostingService(canvas_parent=self._content_frame)

        # Graphics items dict: obj_id -> list[QGraphicsItem] (shape and optional label)
        self._gfx_items: dict[str, list] = {}

        # Properties panel state
        self._properties_panel_visible: bool = False
        self._properties_panel: PropertyPanel | None = None
        self._properties_panel_current_object_id: str | None = None
        self._previous_selection: set[str] = set()

        # Bridge panel state
        self._bridge_panel_visible: bool = False
        self._bridge_panel: SceneBridgeDialog | None = None
        self._bridge: ISceneBridge | None = None

        # Object explorer state
        self._object_explorer_visible: bool = False
        self._object_explorer: ObjectExplorer | None = None

        # Drawing and manipulation state
        self._draw_start_x: float | None = None
        self._draw_start_y: float | None = None
        self._drag_start_x: float | None = None
        self._drag_start_y: float | None = None
        self._is_dragging: bool = False
        self._object_counter: int = 0

        # Callbacks for scene events
        self._scene_loaded_callback = lambda event: self.set_scene(event.scene)
        self._scene_unloaded_callback = lambda event: self.set_scene(event.scene)
        self._object_palette_visible: bool = False
        self._object_palette_frame: QWidget | None = None
        self._current_object_template: str | None = None

        # Clipboard
        self._clipboard_data: list[dict] = []

        # Rendering: dirty flag pattern
        self._needs_render: bool = False
        self._render_timer: QTimer | None = None
        self._render_interval_ms: int = 33  # ~30 FPS

        # TODO: remove these following properties and abstract with services
        self._entity_names_visible: bool = True

        # Build the UI
        self._toolbar = _SceneViewerToolbar(self.content_frame).build_toolbar()
        self._build_canvas()
        self._mode = _SceneViewerUserMode(self, self._canvas_view)
        self._build_properties_panel()
        self._build_object_explorer()
        self._build_object_palette()
        self._build_context_menus()
        self._bind()
        self._initialize_object_templates()

        # Start render loop
        self._start_render_loop()

    # ==================== Properties ====================

    @property
    def canvas(self) -> QGraphicsScene:
        """Get the main graphics scene."""
        return self._gfx_scene

    @property
    def canvas_view(self) -> _SceneCanvasView:
        """Get the graphics view widget."""
        return self._canvas_view

    @property
    def properties_panel(self) -> PropertyPanel:
        """Get the properties panel, rebuilding it if it was previously closed."""
        if self._properties_panel is None:
            self._build_properties_panel()
        return self._properties_panel  # type: ignore[return-value]

    @property
    def scene(self) -> IScene | None:
        """Get the current scene."""
        return self._scene

    @property
    def viewport(self) -> IViewport:
        """Get the current viewport state."""
        return self._viewport_service.viewport

    # ==================== Scene Management ====================

    def set_scene(self, scene: IScene | None) -> None:
        """Set the scene to be displayed.

        Args:
            scene: Scene object to display
        """
        if scene is self._scene:
            return  # No change

        # Unsubscribe from old scene updates
        if self._scene:
            # Remove position sync callback
            if self._sync_object_positions in self._scene.get_on_scene_updated():
                self._scene.get_on_scene_updated().remove(self._sync_object_positions)

        # Subscribe to new scene updates
        if scene:
            # Lightweight position sync for physics (check before adding)
            # Only add if physics is enabled - check if runner has physics engine
            should_sync_positions = False
            if self._runner:
                try:
                    physics_engine = self._runner.get_physics_engine()
                    should_sync_positions = physics_engine is not None
                except (AttributeError, RuntimeError):
                    should_sync_positions = False

            if should_sync_positions:
                if self._sync_object_positions not in scene.get_on_scene_updated():
                    scene.get_on_scene_updated().append(self._sync_object_positions)

        self._scene = scene
        self._canvas_object_management_service.set_scene(scene)
        self._canvas_object_management_service.clear()
        self._viewport_service.reset_view()

        # Refresh bridge reference from SceneBridgeService.
        # The service manages scene changes automatically via SceneEventBus.
        self._bridge = SceneBridgeService.get_bridge()
        if self._bridge_panel is not None:
            if self._bridge is not None:
                self._bridge_panel.bridge = self._bridge
            self._bridge_panel.scene = scene
        if self._object_explorer is not None:
            self._object_explorer.set_scene(scene)
        self._enable_menu_entries(enable=scene is not None)
        self.render_scene()

    def get_scene(self) -> IScene | None:
        """Get the currently displayed scene.

        Returns:
            The current scene, or None if no scene is loaded
        """
        return self._scene

    def _load_from_scene_class(self, filepath: Path) -> None:
        """Load a scene from a file using the scene's class method.

        Args:
            filepath: Path to the scene file
        """
        # Create factory and register object types
        # Load scene
        loaded_scene = Scene.load(Path(filepath))
        self.set_scene(loaded_scene)
        log(self).info(f"Scene loaded from: {filepath}")

    def clear_scene(self) -> None:
        """Clear all scene objects from the viewer."""
        self.clear_canvas()
        if self._scene:
            self._scene.set_scene_objects({})

    # ==================== Object Management ====================

    def add_scene_object(self, scene_obj: ISceneObject) -> None:
        """Add a scene object to the current scene and render it.

        Args:
            scene_obj: Scene object to add
        """
        if not self._scene:
            log(self).warning("Cannot add scene object: no scene loaded")
            return

        self._scene.add_scene_object(scene_obj)
        self._render_scene_object(scene_obj.id, scene_obj)

    def remove_scene_object(self, obj_id: str) -> None:
        """Remove a scene object from the scene and canvas.

        Args:
            obj_id: ID of the scene object to remove
        """
        if not self._scene:
            return

        # Remove graphics items
        for item in self._gfx_items.pop(obj_id, []):
            if item.scene() == self._gfx_scene:
                self._gfx_scene.removeItem(item)

        # Remove from scene
        self._scene.remove_scene_object(obj_id)

    def delete_selected_objects(self) -> None:
        """Delete all currently selected objects from the scene."""
        if not self._scene:
            log(self).warning("Cannot delete objects: no scene loaded")
            return

        if not self._canvas_object_management_service.selected_objects:
            log(self).info("No objects selected to delete")
            return

        # Get list before clearing
        to_delete = list(self._canvas_object_management_service.selected_objects)

        # Remove from scene — for groups, also remove all their members
        for obj_id in to_delete:
            scene_obj = self._scene.scene_objects.get(obj_id)
            if isinstance(scene_obj, SceneGroup):
                for member_id in scene_obj.get_member_ids():
                    self._scene.remove_scene_object(member_id)
            self._scene.remove_scene_object(obj_id)

        # Clear selection
        self._canvas_object_management_service.clear_selection()

        # Redraw
        self.render_scene()

        log(self).info(f"Deleted {len(to_delete)} object(s)")

    # ==================== Selection Management ====================

    def select_object(
        self,
        obj_id: str,
        clear_previous: bool = False
    ) -> None:
        """Select a scene object.

        Args:
            obj_id: ID of the object to select
            clear_previous: Whether to clear previous selection
        """
        # Save currently selected objects before modifying selection
        previously_selected = list(self._canvas_object_management_service.selected_objects) if clear_previous else []

        self._canvas_object_management_service.select_object(obj_id, clear_previous)
        self._update_selection_display()

        # Update appearance of previously selected objects (now deselected)
        for prev_obj_id in previously_selected:
            if prev_obj_id != obj_id:  # Don't update the newly selected object twice
                self._update_object_appearance(prev_obj_id)

        # Update appearance of newly selected object
        self._update_object_appearance(obj_id)

    def deselect_object(self, obj_id: str) -> None:
        """Deselect a scene object.

        Args:
            obj_id: ID of the object to deselect
        """
        self._canvas_object_management_service.deselect_object(obj_id)
        self._update_selection_display()
        self._update_object_appearance(obj_id)

    def toggle_selection(self, obj_id: str) -> None:
        """Toggle selection state of a scene object.

        Args:
            obj_id: ID of the object to toggle
        """
        self._canvas_object_management_service.toggle_selection(obj_id)
        self._update_selection_display()
        self._update_object_appearance(obj_id)

    def clear_selection(self) -> None:
        """Clear all selected objects."""
        selected = list(self._canvas_object_management_service.selected_objects)
        self._canvas_object_management_service.clear_selection()
        self._update_selection_display()
        # Update appearance of previously selected objects
        for obj_id in selected:
            self._update_object_appearance(obj_id)

    # ==================== View Management ====================

    def toggle_object_palette(self) -> None:
        """Toggle the object palette visibility."""
        self._object_palette_visible = not self._object_palette_visible

        if self._object_palette_frame:
            if self._object_palette_visible:
                self._object_palette_frame.show()
            else:
                self._object_palette_frame.hide()

    def toggle_properties_panel(self) -> None:
        """Toggle the visibility of the properties panel."""
        self._properties_panel_visible = not self._properties_panel_visible

        if self._properties_panel_visible:
            if self._properties_panel is None:
                self._build_properties_panel()
            if self._properties_panel is not None:
                self._properties_panel.root.show()
                self._update_properties_panel()
        else:
            if self._properties_panel is not None:
                self._properties_panel.root.hide()

    def toggle_object_explorer(self) -> None:
        """Toggle the visibility of the object explorer panel."""
        self._object_explorer_visible = not self._object_explorer_visible

        if self._object_explorer_visible:
            if self._object_explorer is None:
                self._build_object_explorer()
            if self._object_explorer is not None:
                self._object_explorer.root.show()
                self._object_explorer.set_scene(self._scene)
        else:
            if self._object_explorer is not None:
                self._object_explorer.root.hide()

    def toggle_bridge_panel(self) -> None:
        """Toggle the visibility of the scene bridge panel."""
        self._bridge_panel_visible = not self._bridge_panel_visible

        if self._bridge_panel_visible:
            if self._bridge_panel is None:
                self._build_bridge_panel()
            if self._bridge_panel is None:
                self._bridge_panel_visible = False
                return
            self._bridge_panel.root.show()
        else:
            if self._bridge_panel is not None:
                self._bridge_panel.root.hide()

    def toggle_entity_names(self) -> None:
        """Toggle entity name labels visibility on the canvas."""
        self._entity_names_visible = not self._entity_names_visible

        # Re-render the scene to show/hide labels
        self.render_scene()

        # Update menu entry if registered
        self._enable_entry(
            "scene.view.entity_names",
            enable=self._entity_names_visible
        )

        log(self).info(f"Entity names {'shown' if self._entity_names_visible else 'hidden'}")

    def open_connection_editor(self) -> None:
        """Open the connection editor in a new window."""
        if not self._scene:
            log().warning("No scene loaded. Cannot open connection editor.")
            return

        editor_window = QWidget()
        editor_window.setWindowTitle("Connection Editor")
        editor_window.resize(1200, 800)
        editor_window.setWindowFlag(Qt.WindowType.Window)

        layout = QVBoxLayout(editor_window)
        layout.setContentsMargins(0, 0, 0, 0)

        connection_registry = self._scene.get_connection_registry()
        editor = ConnectionEditor(
            parent=editor_window,
            scene=self._scene,
            connection_registry=connection_registry  # type: ignore[arg-type]
        )
        layout.addWidget(editor)
        editor_window.show()
        editor_window.raise_()

    def clear_canvas(self) -> None:
        """Clear all items from the canvas without affecting the scene."""
        self._clear_scene_objects()

    # ==================== Coordinate Conversion ====================

    def world_to_canvas(self, world_x: float, world_y: float) -> tuple[float, float]:
        """Convert world coordinates to canvas coordinates.

        Args:
            world_x: X coordinate in world space
            world_y: Y coordinate in world space

        Returns:
            Tuple of (canvas_x, canvas_y)
        """
        canvas_x = world_x * self.viewport.zoom + self.viewport.x
        canvas_y = world_y * self.viewport.zoom + self.viewport.y
        return (canvas_x, canvas_y)

    def canvas_to_world(self, canvas_x: float, canvas_y: float) -> tuple[float, float]:
        """Convert canvas coordinates to world coordinates.

        Args:
            canvas_x: X coordinate on canvas
            canvas_y: Y coordinate on canvas

        Returns:
            Tuple of (world_x, world_y)
        """
        world_x = (canvas_x - self.viewport.x) / self.viewport.zoom
        world_y = (canvas_y - self.viewport.y) / self.viewport.zoom
        return (world_x, world_y)

    # ==================== Rendering Methods ====================

    def render_scene(
        self,
        *_,
    ) -> None:
        """Render the current scene to the graphics scene."""
        if not self._scene:
            return

        self._clear_scene_objects()
        self._render_grid()
        self.render_scene_objects()
        self._viewport_service.sync_viewport()
        # TODO: Add scene background rendering

    def render_scene_objects(self) -> None:
        """Render all scene objects with viewport culling and layer ordering."""
        if not self._scene:
            return

        # Get visible canvas bounds for culling
        canvas_width = self._canvas_view.width()
        canvas_height = self._canvas_view.height()

        # Convert canvas bounds to scene coordinates with margin for objects partially visible
        margin = 100  # Extra pixels around viewport to avoid pop-in
        min_scene_x = (-self.viewport.x - margin) / self.viewport.zoom
        min_scene_y = (-self.viewport.y - margin) / self.viewport.zoom
        max_scene_x = (canvas_width - self.viewport.x + margin) / self.viewport.zoom
        max_scene_y = (canvas_height - self.viewport.y + margin) / self.viewport.zoom

        # Sort objects by layer (z-order) before rendering
        # Lower layer values render first (background), higher values render last (foreground)
        sorted_objects = sorted(
            self._scene.scene_objects.items(),
            key=lambda item: item[1].get_layer()
        )

        # Only render objects within or near viewport (viewport culling)
        rendered_count = 0
        for obj_id, scene_obj in sorted_objects:
            # Check if object is in visible region
            if (scene_obj.x + scene_obj.width >= min_scene_x and
                    scene_obj.x <= max_scene_x and
                    scene_obj.y + scene_obj.height >= min_scene_y and
                    scene_obj.y <= max_scene_y):
                self._render_scene_object(obj_id, scene_obj)
                rendered_count += 1

        # Log culling stats for debugging (can remove after verification)
        total_objects = len(self._scene.scene_objects)
        if total_objects > 0:
            culled = total_objects - rendered_count
            if culled > 0:
                log(self).debug(f"Viewport culling: rendered {rendered_count}/{total_objects} objects ({culled} culled)")

    def _render_scene_group(
        self,
        obj_id: str,
        group: "SceneGroup"
    ) -> None:
        """Render a SceneGroup as a dashed bounding-box overlay.

        Groups have no fill — they show a labelled dashed border that encloses
        all their member objects.  When selected the border switches to the
        standard selection colour.

        Args:
            obj_id: Scene-registered ID of the group anchor
            group:  The SceneGroup instance to render
        """
        canvas_x = group.x * self.viewport.zoom + self.viewport.x
        canvas_y = group.y * self.viewport.zoom + self.viewport.y
        canvas_w = group.width * self.viewport.zoom
        canvas_h = group.height * self.viewport.zoom

        is_selected = obj_id in self._canvas_object_management_service.selected_objects
        outline_color = self._canvas_object_management_service._selection_color if is_selected else "#ffaa00"
        outline_width = self._canvas_object_management_service._selection_width if is_selected else 1

        pen = QPen(QColor(outline_color), outline_width)
        pen.setDashPattern([6, 4])
        rect_item = QGraphicsRectItem(QRectF(0, 0, canvas_w, canvas_h))
        rect_item.setPen(pen)
        rect_item.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        rect_item.setPos(canvas_x, canvas_y)
        rect_item.setData(0, obj_id)
        rect_item.setData(1, "scene_object")
        rect_item.setZValue(group.get_layer())
        self._gfx_scene.addItem(rect_item)

        items: list = [rect_item]

        if self._entity_names_visible:
            label_item = QGraphicsSimpleTextItem(group.name)
            font_size = max(8, int(10 * self.viewport.zoom))
            label_item.setFont(QFont("Arial", font_size))
            label_item.setBrush(QBrush(QColor("#ffaa00")))
            lw = label_item.boundingRect().width()
            label_item.setPos(
                canvas_x + canvas_w / 2 - lw / 2,
                canvas_y - 10 * self.viewport.zoom
            )
            label_item.setData(0, obj_id)
            label_item.setData(1, "scene_object_label")
            label_item.setZValue(group.get_layer() + 0.1)
            self._gfx_scene.addItem(label_item)
            items.append(label_item)

        self._gfx_items[obj_id] = items

    def _render_scene_object(
        self,
        obj_id: str,
        scene_obj: ISceneObject
    ) -> None:
        """Render a single scene object to the graphics scene.

        Args:
            obj_id: Unique identifier for the scene object
            scene_obj: The scene object to render
        """
        if isinstance(scene_obj, SceneGroup):
            self._render_scene_group(obj_id, scene_obj)
            return

        props = scene_obj.properties
        color = props.get("color", "#4a9eff")
        shape = props.get("shape", "rectangle")

        canvas_x = scene_obj.x * self.viewport.zoom + self.viewport.x
        canvas_y = scene_obj.y * self.viewport.zoom + self.viewport.y
        canvas_width = scene_obj.width * self.viewport.zoom
        canvas_height = scene_obj.height * self.viewport.zoom

        is_selected = obj_id in self._canvas_object_management_service.selected_objects
        outline_color = self._canvas_object_management_service._selection_color if is_selected else "white"
        outline_width = self._canvas_object_management_service._selection_width if is_selected else 2

        shape_item = None

        if shape == "rectangle":
            shape_item = QGraphicsRectItem(QRectF(0, 0, canvas_width, canvas_height))
            shape_item.setPen(QPen(QColor(outline_color), outline_width))
            shape_item.setBrush(QBrush(QColor(color)))
            shape_item.setPos(canvas_x, canvas_y)
        elif shape in ("circle", "oval"):
            shape_item = QGraphicsEllipseItem(QRectF(0, 0, canvas_width, canvas_height))
            shape_item.setPen(QPen(QColor(outline_color), outline_width))
            shape_item.setBrush(QBrush(QColor(color)))
            shape_item.setPos(canvas_x, canvas_y)
        elif shape == "line":
            x2 = props.get("x2", scene_obj.x + scene_obj.width)
            y2 = props.get("y2", scene_obj.y + scene_obj.height)
            canvas_x2 = x2 * self.viewport.zoom + self.viewport.x
            canvas_y2 = y2 * self.viewport.zoom + self.viewport.y
            line_color = outline_color if is_selected else color
            line_width = max(outline_width if is_selected else 2, int(2 * self.viewport.zoom))
            shape_item = QGraphicsLineItem(
                QLineF(0, 0, canvas_x2 - canvas_x, canvas_y2 - canvas_y)
            )
            shape_item.setPen(QPen(QColor(line_color), line_width))
            shape_item.setPos(canvas_x, canvas_y)
        # TODO: Add support for more shapes (polygon, text, image/sprite)

        if shape_item is not None:
            shape_item.setData(0, obj_id)
            shape_item.setData(1, "scene_object")
            shape_item.setZValue(scene_obj.get_layer())
            self._gfx_scene.addItem(shape_item)

            items: list = [shape_item]

            if self._entity_names_visible:
                font_size = max(8, int(10 * self.viewport.zoom))
                label_item = QGraphicsSimpleTextItem(scene_obj.name)
                label_item.setFont(QFont("Arial", font_size))
                label_item.setBrush(QBrush(QColor("white")))
                lw = label_item.boundingRect().width()
                label_item.setPos(
                    canvas_x + canvas_width / 2 - lw / 2,
                    canvas_y - 10 * self.viewport.zoom
                )
                label_item.setData(0, obj_id)
                label_item.setData(1, "scene_object_label")
                label_item.setZValue(scene_obj.get_layer() + 0.1)
                self._gfx_scene.addItem(label_item)
                items.append(label_item)

            self._gfx_items[obj_id] = items

    def _render_grid(self) -> None:
        """Render the grid overlay directly using QGraphicsScene."""
        # Clear existing grid items
        for item in list(self._gfx_scene.items()):
            if item.data(1) == "grid":
                self._gfx_scene.removeItem(item)

        grid_service = self._viewport_service.grid
        if not grid_service.is_enabled():
            return

        view_w = self._canvas_view.width()
        view_h = self._canvas_view.height()
        if view_w <= 1 or view_h <= 1:
            return

        grid_spacing = grid_service.get_grid_size() * self.viewport.zoom
        if grid_spacing < grid_service.get_min_spacing_pixels():
            return

        pen = QPen(QColor(grid_service.get_grid_color()), grid_service.get_grid_line_width())

        start_x = self.viewport.x % grid_spacing
        start_y = self.viewport.y % grid_spacing

        x = start_x
        while x < view_w:
            line = QGraphicsLineItem(x, 0, x, view_h)
            line.setPen(pen)
            line.setData(1, "grid")
            line.setZValue(-1)
            self._gfx_scene.addItem(line)
            x += grid_spacing

        y = start_y
        while y < view_h:
            line = QGraphicsLineItem(0, y, view_w, y)
            line.setPen(pen)
            line.setData(1, "grid")
            line.setZValue(-1)
            self._gfx_scene.addItem(line)
            y += grid_spacing

    def _clear_scene_objects(self) -> None:
        """Remove all non-grid graphics items from the scene."""
        for item in list(self._gfx_scene.items()):
            if item.data(1) in ("scene_object", "scene_object_label"):
                self._gfx_scene.removeItem(item)
        self._gfx_items.clear()

    def _start_render_loop(self) -> None:
        """Start the render loop at a controlled frame rate."""
        if self._render_timer is not None:
            self._render_timer.stop()
            self._render_timer = None

        QTimer.singleShot(100, self._mark_dirty)  # Initial render after short delay

        self._render_timer = QTimer()
        self._render_timer.timeout.connect(self._render_loop)
        self._render_timer.start(self._render_interval_ms)

    def _render_loop(self) -> None:
        """Render loop that checks dirty flag and renders if needed."""
        if self._needs_render or self._viewport_service.needs_render():
            self.render_scene()
            self._needs_render = False

        if self._properties_panel_visible and self._canvas_object_management_service.selected_objects:
            self._update_properties_panel()

    def _mark_dirty(self, *_) -> None:
        """Mark scene as needing re-render.

        Called by scene updates, viewport changes, etc.
        Actual render happens at controlled frame rate.
        """
        self._needs_render = True

    def _reset_view(self) -> None:
        """Reset viewport to default position/zoom and mark scene dirty."""
        self._viewport_service.reset_view()
        self._mark_dirty()

    def _zoom_in(self) -> None:
        """Zoom in by a fixed factor and mark scene dirty."""
        self._viewport_service.zoom.zoom_in(factor=1.25)
        self._mark_dirty()

    def _zoom_out(self) -> None:
        """Zoom out by a fixed factor and mark scene dirty."""
        self._viewport_service.zoom.zoom_out(factor=1.25)
        self._mark_dirty()

    def _sync_object_positions(self, *_) -> None:
        """Lightweight position sync for physics updates.

        Updates graphics item positions based on scene object positions
        without full re-render. Used during continuous physics simulation.

        NOTE: This is called at scene update rate (~60 FPS). Keep operations minimal.
        """
        if not self._scene or not self._gfx_items:
            return

        for obj_id, items in self._gfx_items.items():
            if not items:
                continue
            scene_obj = self._scene.scene_objects.get(obj_id)
            if not scene_obj:
                continue

            new_canvas_x = scene_obj.x * self.viewport.zoom + self.viewport.x
            new_canvas_y = scene_obj.y * self.viewport.zoom + self.viewport.y

            shape_item = items[0]
            current_pos = shape_item.pos()
            dx = new_canvas_x - current_pos.x()
            dy = new_canvas_y - current_pos.y()

            if abs(dx) > 0.5 or abs(dy) > 0.5:
                for item in items:
                    item.moveBy(dx, dy)

    # ==================== UI Building Methods ====================

    def _build_canvas(self) -> None:
        """Build the main graphics view for rendering."""
        content_layout = self.content_frame.layout()
        if not isinstance(content_layout, QVBoxLayout):
            content_layout = QVBoxLayout(self.content_frame)

        # Splitter for resizable split between canvas and side panels
        self._paned_window = QSplitter(Qt.Orientation.Horizontal, self.content_frame)
        content_layout.addWidget(self._paned_window)

        # Canvas container inside the splitter
        self._canvas_container = QWidget()
        canvas_container_layout = QVBoxLayout(self._canvas_container)
        canvas_container_layout.setContentsMargins(0, 0, 0, 0)
        self._paned_window.addWidget(self._canvas_container)

        # Graphics scene + view
        self._gfx_scene = QGraphicsScene()
        self._gfx_scene.setSceneRect(0, 0, 4000, 3000)
        self._canvas_view = _SceneCanvasView(self._gfx_scene, self, self._canvas_container)
        self._canvas_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._canvas_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._canvas_view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._canvas_view.setBackgroundBrush(QBrush(QColor("#727272")))
        self._canvas_view.setFrameShape(self._canvas_view.frameShape().NoFrame)
        # Anchor at scene origin so manual pan/zoom item positions map 1:1 to
        # view pixels (QGraphicsView centres on the scene rect by default).
        self._canvas_view.horizontalScrollBar().setValue(0)
        self._canvas_view.verticalScrollBar().setValue(0)
        canvas_container_layout.addWidget(self._canvas_view)

        # TODO: Add ruler/coordinate display

    def _build_properties_panel(self) -> None:
        """Build the properties panel for selected objects."""
        self._properties_panel = PropertyPanel(
            parent=self._paned_window,
            title="Object Properties",
            width=250,
            on_property_changed=self._on_property_changed
        )

        def _on_properties_panel_closed(frame):
            self._properties_panel = None
            self._properties_panel_visible = False
            self._properties_panel_current_object_id = None

        self._properties_panel.on_destroy().append(_on_properties_panel_closed)
        self._paned_window.addWidget(self._properties_panel.root)
        self._properties_panel.root.hide()

    def _build_object_explorer(self) -> None:
        """Build the object explorer side panel."""
        self._object_explorer = ObjectExplorer(
            parent=self._paned_window,
            title="object explorer",
            width=230,
            on_selection_changed=self._on_object_explorer_selection,
        )
        self._object_explorer.set_scene(self._scene)

        def _on_explorer_closed(frame):
            self._object_explorer = None
            self._object_explorer_visible = False

        self._object_explorer.on_destroy().append(_on_explorer_closed)
        self._paned_window.addWidget(self._object_explorer.root)
        self._object_explorer.root.hide()

    def _build_bridge_panel(self) -> None:
        """Build the scene bridge panel."""
        self._bridge = SceneBridgeService.get_bridge()
        if self._bridge is None:
            log(self).warning("Cannot open bridge panel: no scene is currently loaded")
            return
        self._bridge_panel = SceneBridgeDialog(
            parent=self._paned_window,
            bridge=self._bridge,
            scene=self._scene,
        )

        def _on_bridge_panel_closed(frame):
            self._bridge_panel = None
            self._bridge_panel_visible = False

        self._bridge_panel.on_destroy().append(_on_bridge_panel_closed)
        self._paned_window.addWidget(self._bridge_panel.root)
        self._bridge_panel.root.hide()

    def _build_object_palette(self) -> None:
        """Build the object palette for design mode."""
        self._object_palette_frame = QWidget(self._canvas_container)
        self._object_palette_frame.setFixedWidth(200)
        palette_layout = QVBoxLayout(self._object_palette_frame)
        palette_layout.setContentsMargins(4, 4, 4, 4)

        title_label = QLabel("Object Palette")
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        palette_layout.addWidget(title_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        palette_layout.addWidget(scroll_area)

        self._palette_content_widget = QWidget()
        self._palette_content_layout = QVBoxLayout(self._palette_content_widget)
        self._palette_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(self._palette_content_widget)

        # Insert BEFORE the canvas view in the canvas container layout
        canvas_container_layout = self._canvas_container.layout()
        if isinstance(canvas_container_layout, QVBoxLayout):
            canvas_container_layout.insertWidget(0, self._object_palette_frame)
        self._object_palette_frame.hide()

    def _build_context_menus(self) -> None:
        """Build context menus for different contexts."""
        self._canvas_context_menu = PyroxContextMenu(self._canvas_view)
        self._object_context_menu = PyroxContextMenu(self._canvas_view)

        # Populate canvas context menu
        self._canvas_context_menu.add_item(MenuItem(
            id="paste",
            label="Paste",
            command=self._context_paste,
            accelerator="Ctrl+V",
            icon="\ud83d\udccb"
        ))
        self._canvas_context_menu.add_item(MenuItem(
            id="zoom_in",
            label="Zoom In",
            command=self._zoom_in,
            accelerator="Ctrl++",
            icon="\ud83d\udd0d\u2795",
            separator_before=True
        ))
        self._canvas_context_menu.add_item(MenuItem(
            id="zoom_out",
            label="Zoom Out",
            command=self._zoom_out,
            accelerator="Ctrl+-",
            icon="\ud83d\udd0d\u2796"
        ))
        self._canvas_context_menu.add_item(MenuItem(
            id="reset_view",
            label="Reset View",
            command=self._reset_view,
            icon="\ud83d\udd04",
            separator_before=True
        ))
        self._canvas_context_menu.add_item(MenuItem(
            id="toggle_grid",
            label="Toggle Grid",
            command=self._viewport_service.grid.toggle,
            icon="⊞"
        ))
        self._canvas_context_menu.add_item(MenuItem(
            id="toggle_snap",
            label="Toggle Snap to Grid",
            command=self._viewport_service.grid.toggle_snap,
            icon="🧲"
        ))
        self._canvas_context_menu.add_item(MenuItem(
            id="toggle_entity_names",
            label="Toggle Entity Names",
            command=self.toggle_entity_names,
            icon="🏷️"
        ))
        self._canvas_context_menu.add_item(MenuItem(
            id="toggle_properties_panel",
            label="Toggle Properties Panel",
            command=self.toggle_properties_panel,
            icon="📋",
            separator_before=True
        ))
        self._canvas_context_menu.add_item(MenuItem(
            id="toggle_object_explorer",
            label="Toggle Object Explorer",
            command=self.toggle_object_explorer,
            icon="🗂️"
        ))
        self._canvas_context_menu.add_item(MenuItem(
            id="toggle_bridge_panel",
            label="Toggle Bridge Panel",
            command=self.toggle_bridge_panel,
            icon="🔗"
        ))

        # Populate object context menu
        self._object_context_menu.add_item(MenuItem(
            id="copy",
            label="Copy",
            command=self._context_copy,
            accelerator="Ctrl+C",
            icon="📄"
        ))
        self._object_context_menu.add_item(MenuItem(
            id="cut",
            label="Cut",
            command=self._context_cut,
            accelerator="Ctrl+X",
            icon="✂️"
        ))
        self._object_context_menu.add_item(MenuItem(
            id="duplicate",
            label="Duplicate",
            command=self._context_duplicate,
            accelerator="Ctrl+D",
            icon="⎘",
            separator_after=True
        ))
        self._object_context_menu.add_item(MenuItem(
            id="delete",
            label="Delete",
            command=self.delete_selected_objects,
            accelerator="Del",
            icon="🗑️"
        ))
        self._object_context_menu.add_item(MenuItem(
            id="group_selected",
            label="Group Selected",
            command=self._context_group_selected,
            accelerator="Ctrl+Alt+G",
            icon="🗂️",
            separator_before=True
        ))
        self._object_context_menu.add_item(MenuItem(
            id="ungroup_selected",
            label="Ungroup",
            command=self._context_ungroup_selected,
            accelerator="Ctrl+Alt+U",
            icon="📂"
        ))
        self._object_context_menu.add_item(MenuItem(
            id="properties",
            label="Properties",
            command=self._context_show_properties,
            icon="⚙️",
            separator_before=True
        ))

        # Layer ordering submenu
        self._object_context_menu.add_item(MenuItem(
            id="layer_up",
            label="Move Layer Up",
            command=self._context_layer_up,
            accelerator="Ctrl+]",
            icon="⬆️",
            separator_before=True
        ))
        self._object_context_menu.add_item(MenuItem(
            id="layer_down",
            label="Move Layer Down",
            command=self._context_layer_down,
            accelerator="Ctrl+[",
            icon="⬇️"
        ))
        self._object_context_menu.add_item(MenuItem(
            id="bring_to_front",
            label="Bring to Front",
            command=self._context_bring_to_front,
            accelerator="Ctrl+Shift+]",
            icon="⏫"
        ))
        self._object_context_menu.add_item(MenuItem(
            id="send_to_back",
            label="Send to Back",
            command=self._context_send_to_back,
            accelerator="Ctrl+Shift+[",
            icon="⏬"
        ))

    # ==================== Event Binding ====================

    def _bind_toolbar(self) -> None:
        """Bind toolbar buttons to their respective commands."""
        self._toolbar.on_toggle_bridge_panel = self.toggle_bridge_panel
        self._toolbar.on_toggle_object_explorer = self.toggle_object_explorer
        self._toolbar.on_toggle_properties_panel = self.toggle_properties_panel
        self._toolbar.on_toggle_object_palette = self.toggle_object_palette
        self._toolbar.on_toggle_entity_names = self.toggle_entity_names

    def _bind(self, *_) -> None:
        """Wire up events and service integrations."""
        self._mode.on_mode_change = self._viewport_service._viewport_status_service.set_current_tool

        self._bind_toolbar()

        SceneEventBus.subscribe(SceneEventType.SCENE_LOADED, self._scene_loaded_callback)
        SceneEventBus.subscribe(SceneEventType.SCENE_UNLOADED, self._scene_unloaded_callback)

        self.on_destroy().append(self._unbind_events)

        if self._scene:
            self._scene.get_on_scene_updated().append(self._sync_object_positions)

    def _unbind_events(
            self,
            *_,
    ) -> None:
        """Unbind events that are necessary when the frame is closed, such as the SceneEventBus subscriptions.

        This method properly cleans up all callbacks to prevent memory leaks and runtime errors
        from stale references after the frame is destroyed.
        """
        # Stop the render timer
        if self._render_timer:
            self._render_timer.stop()
            self._render_timer = None

        # Unsubscribe from SceneEventBus using the exact callback references
        SceneEventBus.unsubscribe(
            SceneEventType.SCENE_LOADED,
            self._scene_loaded_callback
        )
        SceneEventBus.unsubscribe(
            SceneEventType.SCENE_UNLOADED,
            self._scene_unloaded_callback
        )

        # Remove scene update callback if scene exists
        if self._scene:
            try:
                self._scene.get_on_scene_updated().remove(self._sync_object_positions)
            except (ValueError, AttributeError):
                pass  # Callback might already be removed or scene might be None

    def _enable_entry(
        self,
        menu_id: str,
        command: Callable | None = None,
        enable: bool = True
    ) -> None:
        """Enable or disable a menu entry by ID.

        Args:
            menu_id: The ID of the menu item to enable/disable
            command: Optional command to set when enabling
            enable: True to enable, False to disable
        """
        descriptor = MenuRegistry.get_item(menu_id)
        if not descriptor:
            log(self).warning(f"Menu item with ID '{menu_id}' not found in registry.")
            return

        if enable:
            MenuRegistry.enable_item(menu_id)
            if command:
                MenuRegistry.set_command(menu_id, command)
        else:
            MenuRegistry.disable_item(menu_id)
            MenuRegistry.set_command(menu_id, None)

    def _enable_menu_entries(
        self,
        enable: bool
    ) -> None:
        """Enable or disable all SceneViewer-related menu entries.
        Args:
            enable: True to enable, False to disable.
        """
        if enable:
            MenuRegistry.enable_items_by_owner("SceneviewerApplicationTask")
        else:
            MenuRegistry.disable_items_by_owner("SceneviewerApplicationTask")

        # Edit commands
        self._enable_entry(
            menu_id="scene.edit.delete_selected",
            command=self.delete_selected_objects,
            enable=enable
        )
        self._enable_entry(
            menu_id="scene.edit.group",
            command=self._context_group_selected,
            enable=enable
        )
        self._enable_entry(
            menu_id="scene.edit.ungroup",
            command=self._context_ungroup_selected,
            enable=enable
        )

        self._viewport_service.set_menu_registry_items_enabled(enable)

        # Design mode commands
        self._enable_entry(
            menu_id="scene.view.object_palette",
            command=self.toggle_object_palette,
            enable=enable
        )
        self._enable_entry(
            menu_id="scene.view.properties_panel",
            command=self.toggle_properties_panel,
            enable=enable
        )
        self._enable_entry(
            menu_id="scene.view.bridge_panel",
            command=self.toggle_bridge_panel,
            enable=enable
        )

        # Connection editor command
        self._enable_entry(
            menu_id="scene.view.connection_editor",
            command=self.open_connection_editor,
            enable=enable
        )

        # Entity names toggle
        self._enable_entry(
            menu_id="scene.view.entity_names",
            command=self.toggle_entity_names,
            enable=enable
        )

    # ==================== Mouse Event Handlers ====================

    def _on_left_click_qt(self, event: QMouseEvent) -> None:
        """Handle left mouse button press (called from _SceneCanvasView)."""
        if self._mode == UserMode.INSERT:
            scene_pos = self._canvas_view.mapToScene(int(event.position().x()), int(event.position().y()))
            scene_x = (scene_pos.x() - self.viewport.x) / self.viewport.zoom
            scene_y = (scene_pos.y() - self.viewport.y) / self.viewport.zoom
            self._place_object_from_template(scene_x, scene_y)
        elif self._mode == UserMode.SELECT:
            self._on_select_click_qt(event)

    def _on_left_drag_qt(self, event: QMouseEvent) -> None:
        """Handle left mouse drag (called from _SceneCanvasView)."""
        if self._mode == UserMode.SELECT:
            self._on_drag_object_qt(event)

    def _on_left_release_qt(self, event: QMouseEvent) -> None:
        """Handle left mouse button release (called from _SceneCanvasView)."""
        if self._mode == UserMode.SELECT:
            self._on_drag_end_qt(event)

    def _on_select_click_qt(self, event: QMouseEvent) -> None:
        """Handle selection click in Qt scene."""
        pos = event.position()
        scene_pos = self._canvas_view.mapToScene(int(pos.x()), int(pos.y()))
        items = self._gfx_scene.items(QPointF(scene_pos))
        non_grid = [i for i in items if i.data(1) not in ("grid", "scene_object_label")]

        if not non_grid:
            if not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                self.clear_selection()
            return

        clicked_obj_id = non_grid[0].data(0)

        if clicked_obj_id:
            if self._scene:
                clicked_scene_obj = self._scene.scene_objects.get(clicked_obj_id)
                if clicked_scene_obj:
                    group_id = clicked_scene_obj.get_group_id()
                    if group_id and group_id in self._scene.scene_objects:
                        clicked_obj_id = group_id

            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self.toggle_selection(clicked_obj_id)
            else:
                self.select_object(clicked_obj_id, clear_previous=True)

            self._drag_start_x = pos.x()
            self._drag_start_y = pos.y()

    def _on_drag_object_qt(self, event: QMouseEvent) -> None:
        """Handle dragging selected objects in Qt scene."""
        if not self._canvas_object_management_service.selected_objects:
            return
        if self._drag_start_x is None or self._drag_start_y is None:
            return

        pos = event.position()
        dx = pos.x() - self._drag_start_x
        dy = pos.y() - self._drag_start_y

        if not self._is_dragging and (abs(dx) < 3 and abs(dy) < 3):
            return

        self._is_dragging = True

        scene_dx = dx / self.viewport.zoom
        scene_dy = dy / self.viewport.zoom

        for obj_id in self._canvas_object_management_service.selected_objects:
            for item in self._gfx_items.get(obj_id, []):
                item.moveBy(dx, dy)

            if self._scene:
                scene_obj = self._scene.scene_objects.get(obj_id)
                if scene_obj:
                    if isinstance(scene_obj, SceneGroup):
                        for member_id in scene_obj.get_member_ids():
                            for item in self._gfx_items.get(member_id, []):
                                item.moveBy(dx, dy)
                        snapped_x, snapped_y = self._viewport_service.grid.snap_to_grid(
                            scene_obj.x + scene_dx, scene_obj.y + scene_dy
                        )
                        scene_obj.move_delta(snapped_x - scene_obj.x, snapped_y - scene_obj.y)
                    else:
                        new_x = scene_obj.x + scene_dx
                        new_y = scene_obj.y + scene_dy
                        new_x, new_y = self._viewport_service.grid.snap_to_grid(new_x, new_y)
                        scene_obj.physics_body.set_x(new_x)
                        scene_obj.physics_body.set_y(new_y)
                        props = scene_obj.properties
                        if props.get("shape") == "line":
                            actual_dx = new_x - scene_obj.x
                            actual_dy = new_y - scene_obj.y
                            props["x2"] = props.get("x2", 0) + actual_dx
                            props["y2"] = props.get("y2", 0) + actual_dy

        self._drag_start_x = pos.x()
        self._drag_start_y = pos.y()

    def _on_drag_end_qt(self, event: QMouseEvent) -> None:
        """Handle end of drag operation (called from _SceneCanvasView)."""
        self._is_dragging = False
        self._drag_start_x = None
        self._drag_start_y = None

    # ==================== Object Templates & Design Mode ====================

    def _initialize_object_templates(self) -> None:
        """Initialize object templates and populate palette."""
        self._templates = PhysicsSceneFactory.get_all_templates()

        for template_name in self._templates.keys():
            btn = QPushButton(text=template_name, parent=self._palette_content_widget)
            btn.clicked.connect(lambda checked, name=template_name: self._select_object_template(name))
            self._palette_content_layout.addWidget(btn)

    def _select_object_template(self, template_name: str) -> None:
        """Select an object template for placement.

        Args:
            template_name: Name of the template to select
        """
        self._current_object_template = template_name
        # Switch to placement mode
        self._mode.set_mode(UserMode.INSERT)
        log(self).info(f"Selected template: {template_name}. Click on canvas to place.")

    def _place_object_from_template(self, scene_x: float, scene_y: float) -> None:
        """Place an object from the current template at the given position.

        Args:
            scene_x: X coordinate in scene space
            scene_y: Y coordinate in scene space
        """
        try:
            if not self._current_object_template or not self._scene:
                return

            template = self._templates.get(self._current_object_template)
            if not template:
                return

            # Apply snap to grid if enabled
            scene_x, scene_y = self._viewport_service.grid.snap_to_grid(scene_x, scene_y)

            # Create kwargs for object creation (don't mutate template)
            creation_kwargs = template.default_kwargs.copy()
            creation_kwargs['x'] = scene_x
            creation_kwargs['y'] = scene_y

            # Generate unique ID
            self._object_counter += 1
            obj_id = f"{template.name.lower().replace(' ', '_')}_{self._object_counter:03d}"

            # Create physics object from template
            # Use self._current_object_template (the registry key) instead of template.name
            # to ensure we get the correct template
            physics_obj = PhysicsSceneFactory.create_from_template(
                self._current_object_template,
                **creation_kwargs
            )
            if not physics_obj:
                raise RuntimeError(f"Failed to create object from template: {self._current_object_template}")

            scene_obj = SceneObject(
                name=template.name,
                scene_object_type=template.body_class.__name__,
                description='',
                physics_body=physics_obj,
            )

            # Add to scene
            self._scene.add_scene_object(scene_obj)

            # Redraw
            self.render_scene()

            # Select the new object
            self._canvas_object_management_service.clear_selection()
            self._canvas_object_management_service.select_object(obj_id)
            self._update_selection_display()
            self._update_properties_panel()

            log(self).info(f"Placed {template.name} at ({scene_x:.1f}, {scene_y:.1f})")
        finally:
            # Reset to selection mode after placement
            self._mode.set_mode(UserMode.SELECT)
            self._current_object_template = None

    # ==================== Context Menu Handlers ====================

    def _on_right_click_qt(self, event: QContextMenuEvent) -> None:
        """Handle right-click to show context menu (called from _SceneCanvasView)."""
        pos = event.pos()
        scene_pos = self._canvas_view.mapToScene(pos)
        items = self._gfx_scene.items(QPointF(scene_pos))
        non_grid = [i for i in items if i.data(1) not in ("grid", "scene_object_label")]

        clicked_obj_id = non_grid[0].data(0) if non_grid else None

        if clicked_obj_id:
            if self._scene:
                clicked_scene_obj = self._scene.scene_objects.get(clicked_obj_id)
                if clicked_scene_obj:
                    group_id = clicked_scene_obj.get_group_id()
                    if group_id and group_id in self._scene.scene_objects:
                        clicked_obj_id = group_id

            if clicked_obj_id not in self._canvas_object_management_service.selected_objects:
                self.select_object(clicked_obj_id, clear_previous=True)

            global_pos = event.globalPos()
            self._object_context_menu.show_at(global_pos.x(), global_pos.y())
        else:
            global_pos = event.globalPos()
            self._canvas_context_menu.show_at(global_pos.x(), global_pos.y())

    def _context_copy(self) -> None:
        """Copy selected objects to clipboard."""
        if not self._scene:
            log(self).warning("No scene loaded to copy from")
            return

        if not self._canvas_object_management_service.selected_objects:
            log(self).warning("No objects selected to copy")
            return

        # Store selected object data for paste.
        # For SceneGroups the clipboard entry is augmented with the serialised
        # member objects so the paste path can reconstruct the group from scratch
        # without relying on the original member IDs still being in the scene.
        self._clipboard_data = []
        for obj_id in self._canvas_object_management_service.selected_objects:
            obj = self._scene.get_scene_object(obj_id)
            if obj:
                obj_dict = obj.to_dict()
                if isinstance(obj, SceneGroup):
                    obj_dict['_member_dicts'] = [
                        m.to_dict() for m in obj.get_members().values()
                    ]
                self._clipboard_data.append(obj_dict)

        log(self).info(f"Copied {len(self._clipboard_data)} object(s)")

    def _context_cut(self) -> None:
        """Cut selected objects to clipboard."""
        self._context_copy()
        self.delete_selected_objects()

    def _context_paste(self) -> None:
        """Paste objects from clipboard."""
        if not hasattr(self, '_clipboard_data') or not self._clipboard_data:
            log(self).warning("Nothing to paste")
            return

        # Get mouse position relative to the canvas view
        global_cursor = QCursor.pos()
        local_pos = self._canvas_view.mapFromGlobal(global_cursor)
        mouse_x = local_pos.x()
        mouse_y = local_pos.y()
        scene_x = (mouse_x - self.viewport.x) / self.viewport.zoom
        scene_y = (mouse_y - self.viewport.y) / self.viewport.zoom

        # Calculate offset from first object
        if self._clipboard_data:
            first_obj_x = self._clipboard_data[0]['body']['x']
            first_obj_y = self._clipboard_data[0]['body']['y']
            offset_x = scene_x - first_obj_x
            offset_y = scene_y - first_obj_y

            # Paste objects with offset
            for obj_data in self._clipboard_data:
                obj_data['body']['x'] += offset_x
                obj_data['body']['y'] += offset_y
                self._paste_object_data(obj_data)

        log(self).info(f"Pasted {len(self._clipboard_data)} object(s)")

    def _context_duplicate(self) -> None:
        """Duplicate selected objects."""
        if not self._scene:
            log(self).warning("No scene loaded to duplicate from")
            return

        if not self._canvas_object_management_service.selected_objects:
            log(self).warning("No objects selected to duplicate")
            return

        objects_to_duplicate = list(self._canvas_object_management_service.selected_objects)
        self.clear_selection()

        for obj_id in objects_to_duplicate:
            obj = self._scene.get_scene_object(obj_id)
            if obj:
                obj_data = obj.to_dict()
                # Offset the duplicate slightly
                obj_data['body']['x'] += 20
                obj_data['body']['y'] += 20
                if isinstance(obj, SceneGroup):
                    # Also embed member dicts (with matching offset) so
                    # _paste_object_data can rebuild the group correctly.
                    member_dicts = []
                    for m in obj.get_members().values():
                        md = m.to_dict()
                        md['body']['x'] += 20
                        md['body']['y'] += 20
                        member_dicts.append(md)
                    obj_data['_member_dicts'] = member_dicts
                new_obj = self._paste_object_data(obj_data)
                if new_obj:
                    self.select_object(new_obj.id, clear_previous=False)

        log(self).info(f"Duplicated {len(objects_to_duplicate)} object(s)")

    def _context_group_selected(self) -> None:
        """Group all currently selected objects into a SceneGroup."""
        if not self._scene:
            log(self).warning("No scene loaded to group from")
            return

        selected = list(self._canvas_object_management_service.selected_objects)
        if len(selected) < 2:
            log(self).warning("Need at least 2 objects selected to form a group")
            return

        group = self._scene.group_objects(selected)
        self.render_scene()
        self.select_object(group.id, clear_previous=True)
        log(self).info(f"Grouped {len(selected)} object(s) into group '{group.id}'")

    def _context_ungroup_selected(self) -> None:
        """Ungroup any selected SceneGroup objects, returning their members to the scene."""
        if not self._scene:
            log(self).warning("No scene loaded to ungroup from")
            return

        if not self._canvas_object_management_service.selected_objects:
            log(self).warning("No objects selected to ungroup")
            return

        ungrouped_count = 0
        released_member_ids: list[str] = []

        for obj_id in list(self._canvas_object_management_service.selected_objects):
            obj = self._scene.get_scene_object(obj_id)
            if obj and isinstance(obj, SceneGroup):
                member_ids = obj.get_member_ids()
                self._scene.ungroup(obj_id)
                released_member_ids.extend(member_ids)
                ungrouped_count += 1

        if ungrouped_count == 0:
            log(self).warning("No groups found in selection to ungroup")
            return

        self.render_scene()

        # Re-select the formerly-grouped members
        self.clear_selection()
        for mid in released_member_ids:
            self.select_object(mid, clear_previous=False)

        log(self).info(f"Ungrouped {ungrouped_count} group(s), released {len(released_member_ids)} object(s)")

    def _context_show_properties(self) -> None:
        """Show properties panel for selected object."""
        if not self._properties_panel_visible:
            self.toggle_properties_panel()

    def _context_layer_up(self) -> None:
        """Move selected objects one layer up (toward foreground)."""
        if not self._scene or not self._canvas_object_management_service.selected_objects:
            return

        for obj_id in self._canvas_object_management_service.selected_objects:
            obj = self._scene.get_scene_object(obj_id)
            if obj:
                obj.move_layer_up()

        self.render_scene()
        log(self).info(f"Moved {len(self._canvas_object_management_service.selected_objects)} object(s) layer up")

    def _context_layer_down(self) -> None:
        """Move selected objects one layer down (toward background)."""
        if not self._scene or not self._canvas_object_management_service.selected_objects:
            return

        for obj_id in self._canvas_object_management_service.selected_objects:
            obj = self._scene.get_scene_object(obj_id)
            if obj:
                obj.move_layer_down()

        self.render_scene()
        log(self).info(f"Moved {len(self._canvas_object_management_service.selected_objects)} object(s) layer down")

    def _context_bring_to_front(self) -> None:
        """Bring selected objects to front (highest layer)."""
        if not self._scene or not self._canvas_object_management_service.selected_objects:
            return

        for obj_id in self._canvas_object_management_service.selected_objects:
            obj = self._scene.get_scene_object(obj_id)
            if obj:
                obj.bring_to_front()

        self.render_scene()
        log(self).info(f"Brought {len(self._canvas_object_management_service.selected_objects)} object(s) to front")

    def _context_send_to_back(self) -> None:
        """Send selected objects to back (lowest layer)."""
        if not self._scene or not self._canvas_object_management_service.selected_objects:
            return

        for obj_id in self._canvas_object_management_service.selected_objects:
            obj = self._scene.get_scene_object(obj_id)
            if obj:
                obj.send_to_back()

        self.render_scene()
        log(self).info(f"Sent {len(self._canvas_object_management_service.selected_objects)} object(s) to back")

    def _paste_object_data(self, obj_data: dict) -> ISceneObject | None:
        """Helper to paste object data into scene.

        Args:
            obj_data: Dictionary containing object data

        Returns:
            Created scene object or None
        """
        if not self._scene:
            log(self).warning("Cannot paste object: no scene loaded")
            return None

        try:
            # --- SceneGroup: reconstruct with fresh IDs for anchor + all members ---
            if obj_data.get('scene_object_type') == 'group':
                return self._paste_group_data(obj_data)

            # Clear the body's id so BasePhysicsBody.__init__ generates a fresh one.
            # (The SceneObject's own .id is proxied to physics_body.id via __getattribute__,
            # so replacing only the top-level obj_data['id'] has no effect — the body id
            # is what actually gets reused and collides with the original object.)
            if 'body' in obj_data:
                obj_data['body'].pop('id', None)

            # Create object from data
            new_obj = SceneObject.from_dict(obj_data)
            self._scene.add_scene_object(new_obj)

            return new_obj
        except Exception as e:
            log(self).error(f"Failed to paste object: {e}")
            return None

    def _paste_group_data(self, group_data: dict) -> SceneGroup | None:
        """Reconstruct a SceneGroup from a clipboard/duplicate payload.

        The payload must contain a ``_member_dicts`` key with the serialised
        member objects (added by ``_context_copy`` / ``_context_duplicate``).
        Every object — anchor and all members — is given a fresh ID so the
        new group is fully independent of the original.

        Args:
            group_data: The group\'s ``to_dict()`` output augmented with
                        a ``_member_dicts`` list.

        Returns:
            The newly created SceneGroup, or None on failure.
        """
        if not self._scene:
            return None

        try:
            from pyrox.models.scene.scenegroup import SceneGroup

            member_dicts: list[dict] = group_data.get('_member_dicts', [])
            if not member_dicts:
                log(self).warning(
                    "Group clipboard entry has no '_member_dicts'; "
                    "cannot reconstruct members."
                )
                return None

            # Create each member with a fresh physics-body ID.
            new_members: list[SceneObject] = []
            for md in member_dicts:
                import copy
                md = copy.deepcopy(md)
                md['body'].pop('id', None)     # force fresh UUID
                md.pop('group_id', None)        # clear old group affiliation
                member = SceneObject.from_dict(md)
                self._scene.add_scene_object(member)
                new_members.append(member)  # type: ignore[arg-type]

            # Create the group anchor with a fresh ID.
            anchor_data = {k: v for k, v in group_data.items()
                           if k not in ('member_ids', '_member_dicts')}
            anchor_data['body'] = {k: v for k, v in group_data['body'].items()}
            anchor_data['body'].pop('id', None)  # force fresh UUID

            new_group = SceneGroup.from_dict(anchor_data)
            for m in new_members:
                new_group.add_member(m)

            self._scene.add_scene_object(new_group)
            self.render_scene()
            return new_group

        except Exception as e:
            log(self).error(f"Failed to paste group: {e}")
            return None

    # ==================== Helper & Update Methods ====================

    def _update_selection_display(self) -> None:
        """Update the selection info display in toolbar."""
        self._toolbar._selection_label.setText(self._canvas_object_management_service.selected_objects_display)

        # Only force refresh properties panel if selection actually changed
        if self._properties_panel_visible:
            current_selection = set(self._canvas_object_management_service.selected_objects)
            if current_selection != self._previous_selection:
                self._update_properties_panel(force_refresh=True)
                self._previous_selection = current_selection.copy()

    def _update_object_appearance(self, obj_id: str) -> None:
        """Update visual appearance of an object based on selection state."""
        items = self._gfx_items.get(obj_id)
        if not items:
            return

        shape_item = items[0]
        is_selected = obj_id in self._canvas_object_management_service.selected_objects
        selection_color = self._canvas_object_management_service._selection_color
        selection_width = self._canvas_object_management_service._selection_width

        if is_selected:
            pen = QPen(QColor(selection_color), selection_width)
        else:
            pen = QPen(QColor("white"), 2)
            if self._scene:
                scene_obj = self._scene.scene_objects.get(obj_id)
                if scene_obj:
                    color = scene_obj.properties.get("color", "#4a9eff")
                    shape = scene_obj.properties.get("shape", "rect")
                    if shape == "line":
                        pen = QPen(QColor(color), 2)
                    else:
                        pen = QPen(QColor("white"), 2)

        if isinstance(shape_item, (QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsLineItem)):
            shape_item.setPen(pen)

    def _update_properties_panel(self, force_refresh: bool = False) -> None:
        """Update the properties panel with selected object information.

        Args:
            force_refresh: If True, forces a full rebuild. Otherwise uses efficient update.
        """
        if not self._properties_panel:
            return

        if not self._canvas_object_management_service.selected_objects:
            # No selection
            if self._properties_panel_current_object_id is not None:
                self._properties_panel.set_object(None)
                self._properties_panel_current_object_id = None
            return

        if len(self._canvas_object_management_service.selected_objects) > 1:
            # Multiple selection - show count
            if self._properties_panel_current_object_id != 'MULTIPLE':
                self._properties_panel.set_title(f"Properties ({len(self._canvas_object_management_service.selected_objects)} selected)")
                self._properties_panel.set_object(None)
                self._properties_panel_current_object_id = 'MULTIPLE'
            return

        # Single object selected
        if not self._scene:
            return

        obj_id = next(iter(self._canvas_object_management_service.selected_objects))
        scene_obj = self._scene.get_scene_object(obj_id)

        if not scene_obj:
            return

        # Check if this is a new object or force refresh
        if obj_id != self._properties_panel_current_object_id or force_refresh:
            # New object selected - do full rebuild
            self._properties_panel.set_title(f"Properties: {obj_id}")

            # Define which properties should be read-only
            readonly_props = {"id", "type"}  # ID and type are typically read-only

            # Set the object to display (full rebuild)
            self._properties_panel.set_object(scene_obj, readonly_properties=readonly_props)
            self._properties_panel_current_object_id = obj_id
        else:
            # Same object - just update values efficiently without rebuilding
            self._properties_panel.update_values()

    def _on_property_changed(self, property_name: str, new_value) -> None:
        """Handle property changes from the properties panel."""
        if property_name == 'layer':
            self.render_scene()
            log(self).debug(f"Layer changed to {new_value}, re-rendering scene")
            return

        if self._canvas_object_management_service.selected_objects:
            for obj_id in self._canvas_object_management_service.selected_objects:
                self._update_object_appearance(obj_id)

                if property_name in ('x', 'y', 'width', 'height', 'radius', 'name', 'color'):
                    if self._scene:
                        scene_obj = self._scene.scene_objects.get(obj_id)
                        if scene_obj:
                            for item in self._gfx_items.pop(obj_id, []):
                                if item.scene() == self._gfx_scene:
                                    self._gfx_scene.removeItem(item)
                            self._render_scene_object(obj_id, scene_obj)

        log(self).debug(f"Property '{property_name}' changed to: {new_value}")

    def _on_object_explorer_selection(self, obj_id: str) -> None:
        """Handle object selection triggered by the object explorer.

        Selects the chosen object in the canvas (clearing any previous
        selection) and updates the properties panel to match.

        Args:
            obj_id: ID of the scene object the user clicked in the explorer.
        """
        if not self._scene:
            return
        if obj_id not in self._scene.scene_objects:
            return
        self.select_object(obj_id, clear_previous=True)
        self._update_properties_panel()


# ---------------------------------------------------------------------------
# Scene helpers
# ---------------------------------------------------------------------------

def _obj(name: str, x: float, y: float, w: float, h: float,
         color: str = "#4a9eff", shape: str = "rectangle") -> SceneObject:
    """Create a simple SceneObject backed by a BasePhysicsBody."""
    body = BasePhysicsBody(name=name, x=x, y=y, width=w, height=h)
    obj = SceneObject(
        name=name,
        scene_object_type="BasePhysicsBody",
        physics_body=body,
    )
    obj.properties["color"] = color
    obj.properties["shape"] = shape
    return obj


def _build_demo_scene() -> Scene:
    """Return a Scene populated with demo objects."""
    scene = Scene(name="Demo Scene", description="Sceneviewer QA demo")

    # A row of coloured rectangles
    colors = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#3498db", "#9b59b6"]
    for i, color in enumerate(colors):
        scene.add_scene_object(_obj(f"Box_{i+1}", 40 + i * 80, 60, 60, 40, color))

    # A circle
    circle_body = BasePhysicsBody(name="Circle", x=80, y=180, width=60, height=60)
    circle_obj = SceneObject(name="Circle", scene_object_type="BasePhysicsBody",
                             physics_body=circle_body)
    circle_obj.properties["color"] = "#1abc9c"
    circle_obj.properties["shape"] = "circle"
    scene.add_scene_object(circle_obj)

    # A line
    line_body = BasePhysicsBody(name="Line", x=200, y=200, width=120, height=0)
    line_obj = SceneObject(name="Line", scene_object_type="BasePhysicsBody",
                           physics_body=line_body)
    line_obj.properties["color"] = "#ecf0f1"
    line_obj.properties["shape"] = "line"
    line_obj.properties["x2"] = 320.0
    line_obj.properties["y2"] = 260.0
    scene.add_scene_object(line_obj)

    # A group containing two members
    m1 = _obj("GroupMember_A", 350, 180, 50, 35, "#e74c3c")
    m2 = _obj("GroupMember_B", 420, 180, 50, 35, "#9b59b6")
    scene.add_scene_object(m1)
    scene.add_scene_object(m2)
    # Build the group anchor manually (no scene.group_objects helper)
    anchor_body = BasePhysicsBody(name="DemoGroup", x=350, y=180, width=120, height=35)
    group = SceneGroup(name="DemoGroup", physics_body=anchor_body)
    group.add_member(m1)
    group.add_member(m2)
    scene.add_scene_object(group)

    return scene


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class DemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SceneViewerFrame — PyQt6 Demo")
        self.resize(1200, 700)

        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        scene = _build_demo_scene()
        self._viewer = SceneViewerFrame(parent=central, name="Demo Viewer", scene=scene)
        layout.addWidget(self._viewer.root)

        # Load the scene so the render loop picks it up
        self._viewer.set_scene(scene)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = DemoWindow()
    window.show()

    sys.exit(app.exec())


__all__ = ['SceneViewerFrame']

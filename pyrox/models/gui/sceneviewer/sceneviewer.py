"""2D Scene Viewer Frame for Pyrox.

This module provides a PyQt6-based graphics view frame for viewing and interacting
with 2D scenes containing sprites and simple shapes. Supports panning, zooming,
and integrates with the Scene workflow.
"""
import time
from pathlib import Path
from typing import Callable
from PyQt6.QtCore import Qt, QRectF, QLineF, QTimer, QPointF
from PyQt6.QtGui import (
    QBrush, QColor, QPen, QFont, QCursor, QContextMenuEvent,
    QKeyEvent, QMouseEvent, QWheelEvent, QResizeEvent,
    QPainter, QPixmap,
)
from PyQt6.QtWidgets import (
    QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPixmapItem,
    QGraphicsRectItem, QGraphicsScene, QGraphicsSimpleTextItem,
    QGraphicsView, QSplitter, QVBoxLayout, QWidget,
)
from pyrox.interfaces import (
    IScene,
    ISceneObject,
    ISceneRunnerService,
    IViewport
)
from pyrox.models.gui.frame import TaskFrame
from pyrox.models.gui import PropertyPanel
from pyrox.models.gui.contextmenu import PyroxContextMenu, MenuItem
from pyrox.models.physics import PhysicsSceneFactory
from pyrox.models.scene import Scene, SceneGroup, SceneObject, SceneObjectFactory, CompositeSceneObject
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
from pyrox.models.gui.sceneviewer._bridge import _SceneViewerBridgePanel
from pyrox.models.gui.sceneviewer._connectioneditor import _SceneViewerConnectionEditorPanel
from pyrox.models.gui.sceneviewer._explorer import _SceneViewerObjectExplorerPanel
from pyrox.models.gui.sceneviewer._objectpallet import _SceneViewerObjectPalettePanel
from pyrox.models.gui.sceneviewer._properties import _SceneViewerPropertiesPanel
from pyrox.models.gui.sceneviewer._toolbar import _SceneViewerToolbar
from pyrox.models.gui.sceneviewer._user_mode import _SceneViewerUserMode, UserMode


class _SceneCanvasView(QGraphicsView):
    """Internal QGraphicsView subclass that routes Qt events into SceneViewerFrame."""

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:  # type: ignore[override]
        """Paint the grid background directly via QPainter.

        Qt calls this automatically on every repaint, so the grid always
        reflects the current pan/zoom state without needing any scene items
        or dirty-flag bookkeeping.
        """
        super().drawBackground(painter, rect)
        grid = self._frame._viewport_service.grid
        if not grid.is_enabled():
            return
        view_w = self.width()
        view_h = self.height()
        if view_w <= 1 or view_h <= 1:
            return
        zoom = self._frame.viewport.zoom
        spacing = grid.get_grid_size() * zoom
        if spacing < grid.get_min_spacing_pixels():
            return
        pen = QPen(QColor(grid.get_grid_color()), grid.get_grid_line_width())
        painter.setPen(pen)
        vx = self._frame.viewport.x
        vy = self._frame.viewport.y
        x = vx % spacing
        while x < view_w:
            painter.drawLine(QLineF(x, 0.0, x, float(view_h)))
            x += spacing
        y = vy % spacing
        while y < view_h:
            painter.drawLine(QLineF(0.0, y, float(view_w), y))
            y += spacing

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
        self.horizontalScrollBar().setValue(0)  # type: ignore[union-attr]
        self.verticalScrollBar().setValue(0)  # type: ignore[union-attr]


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

        # Drawing and manipulation state
        self._drag_start_x: float | None = None
        self._drag_start_y: float | None = None
        self._is_dragging: bool = False
        self._object_counter: int = 0

        # Callbacks for scene events
        self._scene_loaded_callback = lambda event: self.set_scene(event.scene)
        self._scene_unloaded_callback = lambda event: self.set_scene(event.scene)

        # Clipboard
        self._clipboard_data: list[dict] = []

        # Rendering state
        self._needs_full_render: bool = False   # structural change → full clear+redraw
        self._render_timer: QTimer | None = None
        self._render_interval_ms: int = 16  # ~60 FPS

        # Sprite pixmap cache: "path:w:h" -> QPixmap
        # Invalidated when zoom changes to avoid stale scaled copies.
        self._sprite_cache: dict[str, QPixmap] = {}
        self._sprite_cache_zoom: float = -1.0  # sentinel → forces first fill

        # Animation tick timing
        self._last_tick_time: float = time.monotonic()

        # TODO: remove these following properties and abstract with services
        self._entity_names_visible: bool = True

        self._toolbar = _SceneViewerToolbar(self.content_frame).build_toolbar()
        self._build_canvas()
        self._mode = _SceneViewerUserMode(self, self._canvas_view)

        # Panel managers — each owns its widget, visibility state, and build logic.
        self._properties_panel = _SceneViewerPropertiesPanel(
            self._paned_window, self._on_property_changed
        ).build()
        self._object_explorer = _SceneViewerObjectExplorerPanel(
            self._paned_window, self._on_object_explorer_selection
        ).build(scene=self._scene)
        self._bridge_panel = _SceneViewerBridgePanel(self._paned_window)
        self._connection_editor_panel = _SceneViewerConnectionEditorPanel(self._paned_window)
        self._object_palette = _SceneViewerObjectPalettePanel(
            self.content_frame, self._on_palette_template_selected
        ).build()

        self._build_context_menus()
        self._bind()
        self._object_palette.initialize_templates()

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
        if self._properties_panel.panel is None:
            self._properties_panel.build()
        return self._properties_panel.panel  # type: ignore[return-value]

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

        # Propagate the new scene to panels.
        self._bridge_panel.update_scene(scene, SceneBridgeService.get_bridge())
        self._connection_editor_panel.update_scene(scene)
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
        self._object_palette.toggle()

    def toggle_properties_panel(self) -> None:
        """Toggle the visibility of the properties panel."""
        self._properties_panel.toggle()
        if self._properties_panel.visible:
            self._properties_panel.refresh(
                self._canvas_object_management_service.selected_objects,
                self._scene,
            )

    def toggle_object_explorer(self) -> None:
        """Toggle the visibility of the object explorer panel."""
        self._object_explorer.toggle(scene=self._scene)

    def toggle_bridge_panel(self) -> None:
        """Toggle the visibility of the scene bridge panel."""
        self._bridge_panel.toggle(scene=self._scene)

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

    def toggle_connection_editor(self) -> None:
        """Toggle the connection editor panel."""
        self._connection_editor_panel.toggle(scene=self._scene)

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
        self.render_scene_objects()
        self._viewport_service.sync_viewport()
        # TODO: Add scene background rendering

    def render_scene_objects(self) -> None:
        """Render all scene objects with viewport culling and layer ordering."""
        if not self._scene:
            return

        # Compute viewport bounds with margin to avoid pop-in at edges
        min_scene_x, min_scene_y, max_scene_x, max_scene_y = self._compute_viewport_bounds()

        # Sort objects by layer (z-order): lower values rendered first (background)
        sorted_objects = sorted(
            self._scene.scene_objects.items(),
            key=lambda item: item[1].get_layer()
        )

        rendered_count = 0
        for obj_id, scene_obj in sorted_objects:
            if self._is_in_viewport(scene_obj, min_scene_x, min_scene_y, max_scene_x, max_scene_y):
                self._render_scene_object(obj_id, scene_obj)
                rendered_count += 1

        if log(self).isEnabledFor(10):  # DEBUG
            total = len(self._scene.scene_objects)
            culled = total - rendered_count
            if culled > 0:
                log(self).debug(f"Viewport culling: {rendered_count}/{total} rendered ({culled} culled)")

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

    def _render_composite_scene_object(
        self,
        obj_id: str,
        composite: CompositeSceneObject,
    ) -> None:
        """Render a CompositeSceneObject by drawing each child component.

        The composite bounding box itself has no fill; only its components are
        drawn at their world-space positions::

            world_x = composite.x + offset_x
            world_y = composite.y + offset_y

        All component graphics items are stored under ``obj_id`` so that
        selection, hit-testing, and deletion continue to operate on the
        composite as a whole.  When the composite is selected a dashed
        bounding-box outline is drawn around the full composite extent.

        Args:
            obj_id:    Scene-registered ID of the composite.
            composite: The CompositeSceneObject to render.
        """
        is_selected = obj_id in self._canvas_object_management_service.selected_objects
        outline_color = self._canvas_object_management_service._selection_color if is_selected else "white"
        outline_width = self._canvas_object_management_service._selection_width if is_selected else 2

        # ----------------------------------------------------------
        # Bounding-box anchor item — always items[0].
        #
        # _fast_update_item computes the per-frame pan/zoom delta by
        # comparing composite.x/y against items[0].pos().  Component
        # items are intentionally offset from the composite origin, so
        # if a component were items[0] the delta would be wrong and all
        # items would drift every frame, causing a visual "dip" when
        # animation restores correct positions.  Placing the bounding
        # box first anchors items[0] at (composite.x, composite.y) so
        # the delta calculation is always correct.
        # ----------------------------------------------------------
        comp_canvas_x = composite.x * self.viewport.zoom + self.viewport.x
        comp_canvas_y = composite.y * self.viewport.zoom + self.viewport.y
        comp_canvas_w = composite.width * self.viewport.zoom
        comp_canvas_h = composite.height * self.viewport.zoom
        if is_selected:
            bbox_pen = QPen(
                QColor(self._canvas_object_management_service._selection_color),
                self._canvas_object_management_service._selection_width,
            )
            bbox_pen.setDashPattern([6, 4])
        else:
            bbox_pen = QPen(Qt.PenStyle.NoPen)
        bbox_item = QGraphicsRectItem(QRectF(0, 0, comp_canvas_w, comp_canvas_h))
        bbox_item.setPen(bbox_pen)
        bbox_item.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        bbox_item.setPos(comp_canvas_x, comp_canvas_y)
        bbox_item.setData(0, obj_id)
        bbox_item.setData(1, "scene_object")
        bbox_item.setZValue(composite.get_layer() + 0.2)
        self._gfx_scene.addItem(bbox_item)

        all_items: list = [bbox_item]

        for _comp_name, comp_obj in composite.get_components().items():
            world_x = composite.x + comp_obj._parent_offset_x
            world_y = composite.y + comp_obj._parent_offset_y

            props = comp_obj.properties
            sprite_path: str | None = props.get("sprite_path")
            bg_color: str = props.get("bg_color", props.get("color", "#4a9eff"))
            shape: str = props.get("shape", "rectangle")

            canvas_x = world_x * self.viewport.zoom + self.viewport.x
            canvas_y = world_y * self.viewport.zoom + self.viewport.y
            canvas_width = comp_obj.width * self.viewport.zoom
            canvas_height = comp_obj.height * self.viewport.zoom
            yaw: float = getattr(comp_obj, "yaw", 0.0)

            # ----------------------------------------------------------
            # Sprite path
            # ----------------------------------------------------------
            if sprite_path:
                pixmap = self._get_sprite_pixmap(sprite_path, int(canvas_width), int(canvas_height))
                if pixmap is not None:
                    sprite_item = QGraphicsPixmapItem(pixmap)
                    sprite_item.setPos(canvas_x, canvas_y)
                    sprite_item.setData(0, obj_id)
                    sprite_item.setData(1, "scene_object")
                    sprite_item.setZValue(comp_obj.get_layer())
                    if yaw:
                        sprite_item.setTransformOriginPoint(canvas_width / 2, canvas_height / 2)
                        sprite_item.setRotation(yaw)
                    self._gfx_scene.addItem(sprite_item)
                    all_items.append(sprite_item)

                    sel_pen = (
                        QPen(QColor(outline_color), outline_width)
                        if is_selected else QPen(Qt.PenStyle.NoPen)
                    )
                    sel_rect = QGraphicsRectItem(QRectF(0, 0, canvas_width, canvas_height))
                    sel_rect.setPen(sel_pen)
                    sel_rect.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                    sel_rect.setPos(canvas_x, canvas_y)
                    sel_rect.setData(0, obj_id)
                    sel_rect.setData(1, "scene_object")
                    sel_rect.setZValue(comp_obj.get_layer() + 0.05)
                    if yaw:
                        sel_rect.setTransformOriginPoint(canvas_width / 2, canvas_height / 2)
                        sel_rect.setRotation(yaw)
                    self._gfx_scene.addItem(sel_rect)
                    all_items.append(sel_rect)
                    continue  # skip colour fallback for this component
                else:
                    sprite_path = None  # fall back to colour fill

            # ----------------------------------------------------------
            # Colour fill fallback
            # ----------------------------------------------------------
            shape_item = None
            if shape == "rectangle":
                shape_item = QGraphicsRectItem(QRectF(0, 0, canvas_width, canvas_height))
                shape_item.setPen(QPen(QColor(outline_color), outline_width))
                shape_item.setBrush(QBrush(QColor(bg_color)))
                shape_item.setPos(canvas_x, canvas_y)
            elif shape in ("circle", "oval"):
                shape_item = QGraphicsEllipseItem(QRectF(0, 0, canvas_width, canvas_height))
                shape_item.setPen(QPen(QColor(outline_color), outline_width))
                shape_item.setBrush(QBrush(QColor(bg_color)))
                shape_item.setPos(canvas_x, canvas_y)
            elif shape == "line":
                x2 = props.get("x2", world_x + comp_obj.width)
                y2 = props.get("y2", world_y + comp_obj.height)
                canvas_x2 = x2 * self.viewport.zoom + self.viewport.x
                canvas_y2 = y2 * self.viewport.zoom + self.viewport.y
                line_color = outline_color if is_selected else bg_color
                line_width = max(outline_width if is_selected else 2, int(2 * self.viewport.zoom))
                shape_item = QGraphicsLineItem(
                    QLineF(0, 0, canvas_x2 - canvas_x, canvas_y2 - canvas_y)
                )
                shape_item.setPen(QPen(QColor(line_color), line_width))
                shape_item.setPos(canvas_x, canvas_y)

            if shape_item is not None:
                if yaw and shape != "line":
                    shape_item.setTransformOriginPoint(canvas_width / 2, canvas_height / 2)
                    shape_item.setRotation(yaw)
                shape_item.setData(0, obj_id)
                shape_item.setData(1, "scene_object")
                shape_item.setZValue(comp_obj.get_layer())
                self._gfx_scene.addItem(shape_item)
                all_items.append(shape_item)

        if all_items:
            self._gfx_items[obj_id] = all_items

    def _render_scene_object(
        self,
        obj_id: str,
        scene_obj: ISceneObject
    ) -> None:
        """Render a single scene object to the graphics scene.

        Rendering priority:
        1. If ``sprite_path`` is set and the file can be loaded → pixmap item.
        2. Otherwise → solid-colour shape (rectangle / circle / line).

        Rotation (``yaw``) is applied to all item types via
        ``setTransformOriginPoint`` + ``setRotation``.

        Args:
            obj_id:    Unique identifier for the scene object.
            scene_obj: The scene object to render.
        """
        if isinstance(scene_obj, SceneGroup):
            self._render_scene_group(obj_id, scene_obj)
            return

        if isinstance(scene_obj, CompositeSceneObject):
            self._render_composite_scene_object(obj_id, scene_obj)
            return

        props = scene_obj.properties
        sprite_path: str | None = props.get("sprite_path")
        bg_color: str = props.get("bg_color", props.get("color", "#4a9eff"))
        shape: str = props.get("shape", "rectangle")

        canvas_x = scene_obj.x * self.viewport.zoom + self.viewport.x
        canvas_y = scene_obj.y * self.viewport.zoom + self.viewport.y
        canvas_width = scene_obj.width * self.viewport.zoom
        canvas_height = scene_obj.height * self.viewport.zoom
        yaw: float = getattr(scene_obj, 'yaw', 0.0)

        is_selected = obj_id in self._canvas_object_management_service.selected_objects
        outline_color = self._canvas_object_management_service._selection_color if is_selected else "white"
        outline_width = self._canvas_object_management_service._selection_width if is_selected else 2

        items: list = []

        # ----------------------------------------------------------------
        # Sprite path: use a QGraphicsPixmapItem + invisible selection rect
        # ----------------------------------------------------------------
        if sprite_path:
            pixmap = self._get_sprite_pixmap(sprite_path, int(canvas_width), int(canvas_height))
            if pixmap is not None:
                sprite_item = QGraphicsPixmapItem(pixmap)
                sprite_item.setPos(canvas_x, canvas_y)
                sprite_item.setData(0, obj_id)
                sprite_item.setData(1, "scene_object")
                sprite_item.setZValue(scene_obj.get_layer())
                if yaw:
                    sprite_item.setTransformOriginPoint(canvas_width / 2, canvas_height / 2)
                    sprite_item.setRotation(yaw)
                self._gfx_scene.addItem(sprite_item)
                items.append(sprite_item)

                # Selection border overlay (always present, pen toggled on select)
                sel_pen = (
                    QPen(QColor(outline_color), outline_width)
                    if is_selected else QPen(Qt.PenStyle.NoPen)
                )
                sel_rect = QGraphicsRectItem(QRectF(0, 0, canvas_width, canvas_height))
                sel_rect.setPen(sel_pen)
                sel_rect.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                sel_rect.setPos(canvas_x, canvas_y)
                sel_rect.setData(0, obj_id)
                sel_rect.setData(1, "scene_object")
                sel_rect.setZValue(scene_obj.get_layer() + 0.05)
                if yaw:
                    sel_rect.setTransformOriginPoint(canvas_width / 2, canvas_height / 2)
                    sel_rect.setRotation(yaw)
                self._gfx_scene.addItem(sel_rect)
                items.append(sel_rect)
            else:
                sprite_path = None  # Fall back to colour fill if load failed

        # ----------------------------------------------------------------
        # Colour fill fallback
        # ----------------------------------------------------------------
        if not sprite_path:
            shape_item = None

            if shape == "rectangle":
                shape_item = QGraphicsRectItem(QRectF(0, 0, canvas_width, canvas_height))
                shape_item.setPen(QPen(QColor(outline_color), outline_width))
                shape_item.setBrush(QBrush(QColor(bg_color)))
                shape_item.setPos(canvas_x, canvas_y)
            elif shape in ("circle", "oval"):
                shape_item = QGraphicsEllipseItem(QRectF(0, 0, canvas_width, canvas_height))
                shape_item.setPen(QPen(QColor(outline_color), outline_width))
                shape_item.setBrush(QBrush(QColor(bg_color)))
                shape_item.setPos(canvas_x, canvas_y)
            elif shape == "line":
                x2 = props.get("x2", scene_obj.x + scene_obj.width)
                y2 = props.get("y2", scene_obj.y + scene_obj.height)
                canvas_x2 = x2 * self.viewport.zoom + self.viewport.x
                canvas_y2 = y2 * self.viewport.zoom + self.viewport.y
                line_color = outline_color if is_selected else bg_color
                line_width = max(outline_width if is_selected else 2, int(2 * self.viewport.zoom))
                shape_item = QGraphicsLineItem(
                    QLineF(0, 0, canvas_x2 - canvas_x, canvas_y2 - canvas_y)
                )
                shape_item.setPen(QPen(QColor(line_color), line_width))
                shape_item.setPos(canvas_x, canvas_y)

            if shape_item is not None:
                if yaw and shape != "line":
                    shape_item.setTransformOriginPoint(canvas_width / 2, canvas_height / 2)
                    shape_item.setRotation(yaw)
                shape_item.setData(0, obj_id)
                shape_item.setData(1, "scene_object")
                shape_item.setZValue(scene_obj.get_layer())
                self._gfx_scene.addItem(shape_item)
                items.append(shape_item)

        # ----------------------------------------------------------------
        # Entity name label
        # ----------------------------------------------------------------
        if items and self._entity_names_visible:
            font_size = max(8, int(10 * self.viewport.zoom))
            label_item = QGraphicsSimpleTextItem(scene_obj.name)
            label_item.setFont(QFont("Arial", font_size))
            label_item.setBrush(QBrush(QColor("white")))
            lw = label_item.boundingRect().width()
            label_item.setPos(
                canvas_x + canvas_width / 2 - lw / 2,
                canvas_y - 10 * self.viewport.zoom,
            )
            label_item.setData(0, obj_id)
            label_item.setData(1, "scene_object_label")
            label_item.setZValue(scene_obj.get_layer() + 0.1)
            self._gfx_scene.addItem(label_item)
            items.append(label_item)

        if items:
            self._gfx_items[obj_id] = items

    def _get_sprite_pixmap(self, path: str, w: int, h: int) -> QPixmap | None:
        """Return a cached, scaled :class:`QPixmap` for *path* at *w* × *h* pixels.

        The cache is keyed by ``"path:w:h"`` and flushed whenever the viewport
        zoom factor changes by more than 1 %, so stale scaled copies never
        accumulate across zoom levels.

        Args:
            path: Filesystem path to the image file.
            w:    Target width in canvas pixels.
            h:    Target height in canvas pixels.

        Returns:
            A valid :class:`QPixmap`, or ``None`` if the file could not be loaded.
        """
        if w <= 0 or h <= 0:
            return None

        # Invalidate cache on zoom change
        if abs(self.viewport.zoom - self._sprite_cache_zoom) > 0.01:
            self._sprite_cache.clear()
            self._sprite_cache_zoom = self.viewport.zoom

        cache_key = f"{path}:{w}:{h}"
        cached = self._sprite_cache.get(cache_key)
        if cached is not None:
            return cached if not cached.isNull() else None

        raw = QPixmap(path)
        if raw.isNull():
            self._sprite_cache[cache_key] = QPixmap()  # null sentinel
            return None

        scaled = raw.scaled(
            w, h,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._sprite_cache[cache_key] = scaled
        return scaled if not scaled.isNull() else None

    def _clear_scene_objects(self) -> None:
        """Remove all scene-object graphics items from the scene."""
        for item in list(self._gfx_scene.items()):
            if item.data(1) in ("scene_object", "scene_object_label"):
                self._gfx_scene.removeItem(item)
        self._gfx_items.clear()

    def _start_render_loop(self) -> None:
        """Start the continuous render loop at the target frame rate."""
        if self._render_timer is not None:
            self._render_timer.stop()
            self._render_timer = None

        self._render_timer = QTimer()
        self._render_timer.timeout.connect(self._render_loop)
        self._render_timer.start(self._render_interval_ms)

    def _render_loop(self) -> None:
        """Per-frame render loop.

        Every frame:
        1. Tick all animating objects (dt-based).
        2. If a structural change is pending (viewport transform, add/remove,
           scene load) perform a full clear-and-redraw.
        3. Otherwise perform a fast in-place update: move existing graphics
           items to reflect updated world positions, handle culling re-entry
           (add items for objects that entered the viewport, remove items for
           objects that left), and refresh animated sprite frames.
        """
        now = time.monotonic()
        dt = now - self._last_tick_time
        self._last_tick_time = now

        if self._scene:
            for obj in self._scene.scene_objects.values():
                obj.update(dt)

        if self._needs_full_render or self._viewport_service.needs_render():
            self.render_scene()
            self._needs_full_render = False
        elif self._scene:
            self._update_scene_objects_fast()

        if self._properties_panel.visible and self._canvas_object_management_service.selected_objects:
            self._properties_panel.refresh(
                self._canvas_object_management_service.selected_objects,
                self._scene,
            )

    def _mark_dirty(self, *_) -> None:
        """Request a full structural re-render on the next frame.

        Only call this when item *sizes* need to be recomputed — i.e. on zoom
        (canvas_w = world_w * zoom changes) or when the full scene must be
        rebuilt (explicit reload).  Pan, resize, and animation/physics updates
        do NOT need this: the continuous fast-update loop repositions items
        every frame, and the grid is repainted automatically by
        ``drawBackground``.
        """
        self._needs_full_render = True

    # ------------------------------------------------------------------
    # Fast per-frame update (no full clear)
    # ------------------------------------------------------------------

    def _compute_viewport_bounds(self, margin: float = 100.0) -> tuple[float, float, float, float]:
        """Return (min_x, min_y, max_x, max_y) in scene-space for viewport culling."""
        cw = self._canvas_view.width()
        ch = self._canvas_view.height()
        z = self.viewport.zoom
        vx = self.viewport.x
        vy = self.viewport.y
        return (
            (-vx - margin) / z,
            (-vy - margin) / z,
            (cw - vx + margin) / z,
            (ch - vy + margin) / z,
        )

    def _is_in_viewport(
        self,
        scene_obj,
        min_x: float, min_y: float,
        max_x: float, max_y: float,
    ) -> bool:
        """Return True if *scene_obj* intersects the given viewport bounds."""
        return (
            scene_obj.x + scene_obj.width >= min_x and
            scene_obj.x <= max_x and
            scene_obj.y + scene_obj.height >= min_y and
            scene_obj.y <= max_y
        )

    def _update_scene_objects_fast(self) -> None:
        """In-place per-frame update without a full scene clear.

        For each scene object:
        - If it is in the viewport and already has graphics items, move them
          to the current canvas position and refresh sprite frames if animating.
        - If it is in the viewport but has NO graphics items (culled re-entry),
          render it fresh.
        - If it is outside the viewport AND has graphics items, remove them
          (cull it out).
        """
        if not self._scene:
            return

        bounds = self._compute_viewport_bounds()
        min_x, min_y, max_x, max_y = bounds

        for obj_id, scene_obj in self._scene.scene_objects.items():
            in_view = self._is_in_viewport(scene_obj, min_x, min_y, max_x, max_y)
            has_items = obj_id in self._gfx_items and bool(self._gfx_items[obj_id])

            if in_view and has_items:
                self._fast_update_item(obj_id, scene_obj)
            elif in_view and not has_items:
                # Object entered the viewport — render it
                self._render_scene_object(obj_id, scene_obj)
            elif not in_view and has_items:
                # Object left the viewport — cull its graphics items
                for item in self._gfx_items.pop(obj_id):
                    if item.scene() == self._gfx_scene:
                        self._gfx_scene.removeItem(item)

    def _fast_update_item(self, obj_id: str, scene_obj) -> None:
        """Move existing graphics items for *scene_obj* to their current canvas
        position and update sprite pixmaps if the object has an active animator.

        This avoids the cost of removing and re-creating QGraphicsItems every
        frame.  Rotation (yaw) changes are also applied in-place.
        """
        items = self._gfx_items.get(obj_id)
        if not items:
            return

        # For composite objects (e.g. pistons), animations change *component
        # offsets* rather than the composite's own x/y.  A simple moveBy won't
        # reflect those offset changes, so clear the stale items and re-render
        # the composite from scratch whenever any component is animating.
        #
        # Two mechanisms signal that a composite needs per-frame re-render:
        #   1. animator.is_playing  — a SceneAnimator clip is active (piston, gate, etc.)
        #   2. scene_obj.is_animating — composite overrides this property to True,
        #      used by assets whose update() mutates component offsets directly
        #      without going through the SceneAnimator system (e.g. conveyor belt
        #      stripes).  New composite assets that do custom per-frame position
        #      updates must override is_animating to avoid this rendering gap.
        if isinstance(scene_obj, CompositeSceneObject):
            composite_animator = getattr(scene_obj, 'animator', None)
            has_animating_component = (
                getattr(scene_obj, 'is_animating', False)
                or (composite_animator is not None and composite_animator.is_playing)
                or any(
                    getattr(comp, 'animator', None) is not None
                    and getattr(comp, 'animator').is_playing
                    for comp in scene_obj.get_components().values()
                )
            )
            if has_animating_component:
                for item in self._gfx_items.pop(obj_id, []):
                    if item.scene() == self._gfx_scene:
                        self._gfx_scene.removeItem(item)
                self._render_composite_scene_object(obj_id, scene_obj)
                return

        new_canvas_x = scene_obj.x * self.viewport.zoom + self.viewport.x
        new_canvas_y = scene_obj.y * self.viewport.zoom + self.viewport.y

        shape_item = items[0]
        current_pos = shape_item.pos()
        dx = new_canvas_x - current_pos.x()
        dy = new_canvas_y - current_pos.y()

        if abs(dx) > 0.05 or abs(dy) > 0.05:
            for item in items:
                item.moveBy(dx, dy)

        # Refresh sprite frame if the object has an active animator
        animator = getattr(scene_obj, 'animator', None)
        if animator is not None and animator.is_playing:
            props = scene_obj.properties
            sprite_path: str | None = props.get('sprite_path')
            if sprite_path:
                canvas_w = int(scene_obj.width * self.viewport.zoom)
                canvas_h = int(scene_obj.height * self.viewport.zoom)
                pixmap = self._get_sprite_pixmap(sprite_path, canvas_w, canvas_h)
                if pixmap is not None:
                    for item in items:
                        if isinstance(item, QGraphicsPixmapItem):
                            item.setPixmap(pixmap)
                            break

        # Apply rotation in-place
        yaw: float = getattr(scene_obj, 'yaw', 0.0)
        if yaw:
            canvas_w = scene_obj.width * self.viewport.zoom
            canvas_h = scene_obj.height * self.viewport.zoom
            for item in items:
                item.setTransformOriginPoint(canvas_w / 2, canvas_h / 2)
                item.setRotation(yaw)

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
        """Physics callback: mark the frame dirty so the continuous render loop
        picks up the updated positions on the very next tick.

        Previously this method moved items directly, but that conflicted with
        viewport culling (items that were culled have no graphics items to move)
        and with the continuous animation loop.  Delegating to the render loop
        keeps all position/culling logic in one place.
        """
        # The render loop runs at ~60 FPS and calls _update_scene_objects_fast
        # every frame, so no explicit dirty flag is needed here.  We do nothing
        # beyond ensuring the loop is running (it always is while the frame is
        # alive) so that physics-driven motion is picked up immediately.
        pass

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
        self._canvas_view.horizontalScrollBar().setValue(0)  # type: ignore[union-attr]
        self._canvas_view.verticalScrollBar().setValue(0)  # type: ignore[union-attr]
        canvas_container_layout.addWidget(self._canvas_view)

        # Add status bar below the canvas view
        status_bar = self._viewport_service.status.get_status_bar()
        if status_bar:
            canvas_container_layout.addWidget(status_bar)

        self._viewport_service.set_canvas(self._canvas_view)

        # TODO: Add ruler/coordinate display

    def _build_context_menus(self) -> None:
        """Build context menus for different contexts."""
        self._build_canvas_context_menu()
        self._build_object_context_menu()

    def _build_canvas_context_menu(self) -> None:
        self._canvas_context_menu = PyroxContextMenu(self._canvas_view)

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
        self._canvas_context_menu.add_item(MenuItem(
            id="toggle_connection_editor",
            label="Toggle Connection Editor",
            command=self.toggle_connection_editor,
            icon="🔌"
        ))

    def _build_object_context_menu(self) -> None:
        self._object_context_menu = PyroxContextMenu(self._canvas_view)
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
        self._object_context_menu.add_item(MenuItem(
            id="rotate_cw",
            label="Rotate Clockwise",
            command=self._context_rotate_cw,
            accelerator="Ctrl+R",
            icon="🔄"
        ))
        self._object_context_menu.add_item(MenuItem(
            id="rotate_ccw",
            label="Rotate Counter-Clockwise",
            command=self._context_rotate_ccw,
            accelerator="Ctrl+Shift+R",
            icon="🔄"
        ))

    # ==================== Event Binding ====================

    def _bind_toolbar(self) -> None:
        """Bind toolbar buttons to their respective commands."""
        self._toolbar.on_toggle_bridge_panel = self.toggle_bridge_panel
        self._toolbar.on_toggle_object_explorer = self.toggle_object_explorer
        self._toolbar.on_toggle_properties_panel = self.toggle_properties_panel
        self._toolbar.on_toggle_object_palette = self.toggle_object_palette
        self._toolbar.on_toggle_entity_names = self.toggle_entity_names

    def _bind_menu_registry(self) -> None:
        """Bind menu registry items to their respective commands."""
        # Edit commands
        MenuRegistry.set_command("scene.edit.delete_selected", self.delete_selected_objects)
        MenuRegistry.set_command("scene.edit.group", self._context_group_selected)
        MenuRegistry.set_command("scene.edit.ungroup", self._context_ungroup_selected)

        # Zoom commands
        MenuRegistry.set_command("scene.view.zoom_in", self._zoom_in)
        MenuRegistry.set_command("scene.view.zoom_out", self._zoom_out)
        MenuRegistry.set_command("scene.view.reset_view", self._reset_view)

        # Grid commands
        MenuRegistry.set_command("scene.view.show_grid", self._viewport_service.grid.toggle)
        MenuRegistry.set_command("scene.view.snap_to_grid", self._viewport_service.grid.toggle_snap)

        # Design mode commands
        MenuRegistry.set_command("scene.view.object_palette", self.toggle_object_palette)
        MenuRegistry.set_command("scene.view.properties_panel", self.toggle_properties_panel)
        MenuRegistry.set_command("scene.view.bridge_panel", self.toggle_bridge_panel)
        MenuRegistry.set_command("scene.view.connection_editor", self.toggle_connection_editor)
        MenuRegistry.set_command("scene.view.entity_names", self.toggle_entity_names)

    def _bind(self, *_) -> None:
        """Wire up events and service integrations."""
        self._mode.on_mode_change = self._viewport_service._viewport_status_service.set_current_tool

        self._bind_toolbar()
        self._bind_menu_registry()

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

        # Unsubscribe viewport services from ViewportEventBus before the Qt
        # widgets are deleted.  Without this, stale bound-method references
        # remain in the bus and raise 'wrapped C/C++ object has been deleted'
        # errors the next time a pan/zoom event fires.
        self._viewport_service.destroy()

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
            command=self.toggle_connection_editor,
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
        """Fetch all registered templates and populate the object palette."""
        self._object_palette.initialize_templates()

    def _on_palette_template_selected(self, template_name: str, is_scene_object: bool) -> None:
        """Handle a template button click in the object palette."""
        self._mode.set_mode(UserMode.INSERT)
        log(self).info(f"Selected template: {template_name}. Click on canvas to place.")

    def _place_object_from_template(self, scene_x: float, scene_y: float) -> None:
        """Place an object from the current template at the given position.

        Handles both :class:`PhysicsSceneFactory` templates (physics body wrapped
        in a generic :class:`SceneObject`) and :class:`SceneObjectFactory`
        templates (custom :class:`SceneObject` subclass created directly).

        Args:
            scene_x: X coordinate in scene space
            scene_y: Y coordinate in scene space
        """
        try:
            template_name, is_scene_object = self._object_palette.get_selected_template()
            if not template_name or not self._scene:
                return

            # Apply snap to grid if enabled
            scene_x, scene_y = self._viewport_service.grid.snap_to_grid(scene_x, scene_y)

            if is_scene_object:
                self._place_scene_object_from_template(scene_x, scene_y, template_name)
            else:
                self._place_physics_object_from_template(scene_x, scene_y, template_name)
        finally:
            # Reset to selection mode after placement
            self._mode.set_mode(UserMode.SELECT)
            self._object_palette.clear_template()

    def _place_physics_object_from_template(self, scene_x: float, scene_y: float, template_name: str) -> None:
        """Place a physics-body-based object at the given scene-space position.

        Creates a physics body from the current :class:`PhysicsSceneFactory`
        template and wraps it in a generic :class:`SceneObject`.

        Args:
            scene_x: X coordinate in scene space
            scene_y: Y coordinate in scene space
            template_name: Name of the PhysicsSceneFactory template to instantiate
        """
        template = self._object_palette.templates.get(template_name)  # type: ignore[arg-type]
        if not template:
            return

        # Create kwargs for object creation (don't mutate template)
        creation_kwargs = template.default_kwargs.copy()
        creation_kwargs['x'] = scene_x
        creation_kwargs['y'] = scene_y

        physics_obj = PhysicsSceneFactory.create_from_template(
            template_name,  # type: ignore[arg-type]
            **creation_kwargs
        )
        if not physics_obj:
            raise RuntimeError(f"Failed to create physics object from template: {template_name}")

        scene_obj = SceneObject(
            name=template.name,
            description='',
            physics_body=physics_obj,
        )

        self._scene.add_scene_object(scene_obj)  # type: ignore[union-attr]
        self.render_scene()
        self._canvas_object_management_service.clear_selection()
        self._canvas_object_management_service.select_object(scene_obj.id)
        self._update_selection_display()
        self._properties_panel.refresh(
            self._canvas_object_management_service.selected_objects, self._scene
        )
        log(self).info(f"Placed physics object '{template.name}' at ({scene_x:.1f}, {scene_y:.1f})")

    def _place_scene_object_from_template(self, scene_x: float, scene_y: float, template_name: str) -> None:
        """Place a custom scene object at the given scene-space position.

        Creates the object directly from the current :class:`SceneObjectFactory`
        template — no physics-body wrapping step is needed.

        Args:
            scene_x: X coordinate in scene space
            scene_y: Y coordinate in scene space
            template_name: Name of the SceneObjectFactory template to instantiate
        """
        template = self._object_palette.scene_object_templates.get(template_name)
        if not template:
            return

        creation_kwargs = template.default_kwargs.copy()

        scene_obj = SceneObjectFactory.create_from_template(
            template_name,  # type: ignore[arg-type]
            **creation_kwargs
        )
        if not scene_obj:
            raise RuntimeError(f"Failed to create scene object from template: {template_name}")

        # SceneObjectFactory templates must produce a SceneObject (or subclass)
        assert isinstance(scene_obj, SceneObject), (
            f"SceneObjectTemplate '{template_name}' must produce a SceneObject instance"
        )
        scene_obj.x = scene_x
        scene_obj.y = scene_y

        self._scene.add_scene_object(scene_obj)  # type: ignore[union-attr]
        self.render_scene()
        self._canvas_object_management_service.clear_selection()
        self._canvas_object_management_service.select_object(scene_obj.id)
        self._update_selection_display()
        self._properties_panel.refresh(
            self._canvas_object_management_service.selected_objects, self._scene
        )
        log(self).info(f"Placed scene object '{template.name}' at ({scene_x:.1f}, {scene_y:.1f})")

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
        if not self._properties_panel.visible:
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

    def _context_rotate_cw(self) -> None:
        """Rotate selected objects 90 degrees clockwise."""
        if not self._scene or not self._canvas_object_management_service.selected_objects:
            return

        for obj_id in self._canvas_object_management_service.selected_objects:
            obj = self._scene.get_scene_object(obj_id)
            if obj:
                obj.rotate_clockwise()
        self._mark_dirty()
        log(self).info(f"Rotated {len(self._canvas_object_management_service.selected_objects)} object(s) 90° clockwise")

    def _context_rotate_ccw(self) -> None:
        """Rotate selected objects 90 degrees counter-clockwise."""
        if not self._scene or not self._canvas_object_management_service.selected_objects:
            return

        for obj_id in self._canvas_object_management_service.selected_objects:
            obj = self._scene.get_scene_object(obj_id)
            if obj:
                obj.rotate_counterclockwise()

        self._mark_dirty()
        log(self).info(f"Rotated {len(self._canvas_object_management_service.selected_objects)} object(s) 90° counter-clockwise")

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

        if self._properties_panel.visible:
            current_selection = set(self._canvas_object_management_service.selected_objects)
            self._properties_panel.refresh_if_selection_changed(current_selection, self._scene)

    def _update_object_appearance(self, obj_id: str) -> None:
        """Update visual appearance of an object based on selection state."""
        items = self._gfx_items.get(obj_id)
        if not items:
            return

        shape_item = items[0]
        is_selected = obj_id in self._canvas_object_management_service.selected_objects
        selection_color = self._canvas_object_management_service._selection_color
        selection_width = self._canvas_object_management_service._selection_width

        # --- Sprite items: toggle the selection-border overlay (items[1]) ---
        if isinstance(shape_item, QGraphicsPixmapItem):
            if len(items) > 1 and isinstance(items[1], QGraphicsRectItem):
                sel_border = items[1]
                if is_selected:
                    sel_border.setPen(QPen(QColor(selection_color), selection_width))
                else:
                    sel_border.setPen(QPen(Qt.PenStyle.NoPen))
            return

        # --- Colour-fill items: update pen directly ---
        if is_selected:
            pen = QPen(QColor(selection_color), selection_width)
        else:
            pen = QPen(QColor("white"), 2)
            if self._scene:
                scene_obj = self._scene.scene_objects.get(obj_id)
                if scene_obj:
                    color = scene_obj.properties.get("bg_color", scene_obj.properties.get("color", "#4a9eff"))
                    shape = scene_obj.properties.get("shape", "rect")
                    if shape == "line":
                        pen = QPen(QColor(color), 2)
                    else:
                        pen = QPen(QColor("white"), 2)

        if isinstance(shape_item, (QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsLineItem)):
            shape_item.setPen(pen)

    def _on_property_changed(self, property_name: str, new_value) -> None:
        """Handle property changes from the properties panel."""
        if property_name == 'layer':
            self.render_scene()
            log(self).debug(f"Layer changed to {new_value}, re-rendering scene")
            return

        if self._canvas_object_management_service.selected_objects:
            for obj_id in self._canvas_object_management_service.selected_objects:
                self._update_object_appearance(obj_id)

                # For certain properties (e.g. color, shape) we need to re-render the object to reflect the change.
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
        self._properties_panel.refresh(
            self._canvas_object_management_service.selected_objects,
            self._scene,
            force_refresh=True,
        )


__all__ = ['SceneViewerFrame']

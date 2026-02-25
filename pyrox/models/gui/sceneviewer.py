"""2D Scene Viewer Frame for Pyrox.

This module provides a Tkinter-based canvas frame for viewing and interacting
with 2D scenes containing sprites and simple shapes. Supports panning, zooming,
and integrates with the Scene workflow.
"""
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Tuple
from pyrox.interfaces import (
    IScene,
    ISceneBridge,
    ISceneObject,
    ISceneRunnerService,
    IViewport
)
from pyrox.models.gui.tk.frame import TkinterTaskFrame
from pyrox.models.gui import TkPropertyPanel
from pyrox.models.gui.contextmenu import PyroxContextMenu, MenuItem
from pyrox.models.gui.connectioneditor import ConnectionEditor
from pyrox.models.gui.objectexplorer import TkObjectExplorer
from pyrox.models.gui.scenebridge import SceneBridgeDialog
from pyrox.services.scene import SceneBridgeService
from pyrox.models.physics import PhysicsSceneFactory
from pyrox.models.scene import Scene, SceneGroup, SceneObject
from pyrox.services import (
    log,
    CanvasObjectManagmenentService,
    ViewportHostingService,
    MenuRegistry,
    SceneEventType,
    SceneEventBus
)


class SceneViewerFrame(TkinterTaskFrame):
    """A 2D canvas-based scene viewer with pan and zoom support.

    This frame provides a visual canvas for rendering scene objects with
    interactive pan and zoom controls. Integrates with the Scene and
    SceneObject interfaces for managing displayed content.

    Features:
        - Canvas-based 2D rendering
        - Mouse-based panning (middle mouse drag)
        - Zoom in/out with mouse wheel
        - Customizable toolbar
        - Scene integration

    Attributes:
        canvas: The main Tkinter canvas for rendering
        scene: The currently loaded scene
        viewport_x: Viewport X offset for panning
        viewport_y: Viewport Y offset for panning
        zoom_level: Current zoom level (1.0 = 100%)
    """

    _application_menu_built: bool = False

    # ==================== Initialization ====================

    def __init__(
        self,
        parent,
        name: str = "scene viewer",
        runner: Optional[type[ISceneRunnerService]] = None,
        scene: Optional[IScene] = None
    ):
        """Initialize the SceneViewerFrame.

        Args:
            parent: Parent widget
            name: Name of the frame displayed in title bar
            scene: Optional scene to load initially
            **kwargs: Additional arguments passed to TaskFrame
        """
        super().__init__(
            name=name,
            parent=parent
        )

        # Scene and rendering state
        self._scene: Optional[IScene] = scene
        self._runner: Optional[ISceneRunnerService] = runner

        # Canvas services
        self._canvas_object_management_service = CanvasObjectManagmenentService()

        # Viewport services
        self._viewport_service = ViewportHostingService(canvas_parent=self.content_frame)

        # Viewport state for panning and zooming
        self._last_culling_viewport_x: float = 0.0
        self._last_culling_viewport_y: float = 0.0
        self._culling_threshold: int = 50  # Pixels movement before re-culling

        # Selection state
        self._selection_color: str = "#ffaa00"  # Orange highlight for selection
        self._selection_width: int = 3

        # Properties panel state
        self._properties_panel_visible: bool = False
        self._properties_panel: Optional[TkPropertyPanel] = None  # type: ignore[assignment]
        self._properties_panel_current_object_id: Optional[str] = None  # Track displayed object
        self._previous_selection: set[str] = set()  # Track previous selection to detect changes

        # Bridge panel state
        self._bridge_panel_visible: bool = False
        self._bridge_panel: Optional[SceneBridgeDialog] = None
        self._bridge: Optional[ISceneBridge] = None

        # Object explorer state
        self._object_explorer_visible: bool = False
        self._object_explorer: Optional[TkObjectExplorer] = None
        self._object_explorer_var: tk.BooleanVar = tk.BooleanVar()

        # Drawing and manipulation state
        self._current_tool: str = "select"  # Current tool: select, rectangle, circle, line
        self._draw_start_x: Optional[float] = None
        self._draw_start_y: Optional[float] = None
        self._temp_draw_id: Optional[int] = None  # Temporary canvas ID for drawing preview
        self._drag_start_x: Optional[float] = None
        self._drag_start_y: Optional[float] = None
        self._is_dragging: bool = False
        self._object_counter: int = 0  # Counter for generating unique object IDs

        # Design mode state
        self._design_mode: bool = False

        # Store callback references for proper cleanup
        self._scene_loaded_callback = lambda event: self.set_scene(event.scene)
        self._scene_unloaded_callback = lambda event: self.set_scene(event.scene)
        self._object_palette_visible: bool = False
        self._object_palette_frame: Optional[ttk.Frame] = None
        self._current_object_template: Optional[str] = None  # Selected object template

        # Clipboard for copy/paste
        self._clipboard_data: list[dict] = []

        # Rendering optimization: dirty flag pattern
        self._needs_render: bool = False
        self._render_timer_id: Optional[str] = None
        self._render_interval_ms: int = 33  # ~30 FPS for rendering (decoupled from 60 Hz updates)

        # TODO: remove these following properties and abstract with services
        self._design_mode_var: tk.BooleanVar = tk.BooleanVar()
        self._object_palette_var: tk.BooleanVar = tk.BooleanVar()
        self._properties_var: tk.BooleanVar = tk.BooleanVar()
        self._bridge_var: tk.BooleanVar = tk.BooleanVar()
        self._entity_names_var: tk.BooleanVar = tk.BooleanVar(value=True)
        self._entity_names_visible: bool = True

        # Build the UI
        self._build_toolbar()
        self._build_canvas()
        self._build_properties_panel()
        self._build_object_explorer()
        self._build_object_palette()
        self._build_context_menus()
        self._bind_events()
        self._initialize_object_templates()

        # Start render loop (decoupled from scene update rate)
        self._start_render_loop()

    # ==================== Properties ====================

    @property
    def canvas(self) -> tk.Canvas:
        """Get the main canvas widget."""
        return self._canvas

    @property
    def properties_panel(self) -> TkPropertyPanel:
        """Get the properties panel, rebuilding it if it was previously closed."""
        if self._properties_panel is None:
            self._build_properties_panel()
        return self._properties_panel  # type: ignore[return-value]

    @property
    def scene(self) -> Optional[IScene]:
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

    def get_scene(self) -> Optional[IScene]:
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

        # Remove from canvas (both shape and label by tag)
        if obj_id in self._canvas_object_management_service.objects:
            # Delete by tag to remove both the shape and associated label
            self._canvas.delete(obj_id)
            del self._canvas_object_management_service.objects[obj_id]

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

    def toggle_design_mode(self) -> None:
        """Toggle design mode on/off."""
        self._design_mode = not self._design_mode
        self._design_mode_var.set(self._design_mode)

        if self._design_mode:
            # Enable design features
            self._design_mode_btn.config(text="🎨✓")  # Show checkmark when active
            log(self).info("Design mode enabled")
        else:
            # Disable design features
            self._design_mode_btn.config(text="🎨")
            self._object_palette_visible = False
            self._object_palette_var.set(False)
            if self._object_palette_frame:
                self._object_palette_frame.pack_forget()
            self._current_object_template = None
            if self._current_tool == "place_object":
                self._current_tool = "select"
                self._canvas.config(cursor="")
            log(self).info("Design mode disabled")

    def toggle_object_palette(self) -> None:
        """Toggle the object palette visibility."""
        self._object_palette_visible = not self._object_palette_visible
        self._object_palette_var.set(self._object_palette_visible)

        if self._object_palette_visible and self._object_palette_frame:
            self._object_palette_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5, before=self._canvas)
        elif self._object_palette_frame:
            self._object_palette_frame.pack_forget()

    def toggle_properties_panel(self) -> None:
        """Toggle the visibility of the properties panel."""
        self._properties_panel_visible = not self._properties_panel_visible
        self._properties_var.set(self._properties_panel_visible)
        panes = list(self._paned_window.panes())

        if self._properties_panel_visible:
            # Rebuild if the panel was previously closed via its X button
            if self._properties_panel is None:
                self._build_properties_panel()
            if self._properties_panel is not None and str(self._properties_panel.root) not in panes:
                self._properties_panel.root.master = self._paned_window
                self._paned_window.add(self._properties_panel.root, weight=0)
            self._update_properties_panel()
        else:
            if self._properties_panel is not None and str(self._properties_panel.root) in panes:
                self._properties_panel.root.pack_forget()
                self._paned_window.remove(self._properties_panel.root)

    def toggle_object_explorer(self) -> None:
        """Toggle the visibility of the object explorer panel."""
        self._object_explorer_visible = not self._object_explorer_visible
        self._object_explorer_var.set(self._object_explorer_visible)
        panes = list(self._paned_window.panes())

        if self._object_explorer_visible:
            if self._object_explorer is None:
                self._build_object_explorer()
            if self._object_explorer is not None:
                if str(self._object_explorer.root) not in panes:
                    self._object_explorer.root.master = self._paned_window
                    self._paned_window.add(self._object_explorer.root, weight=0)
                self._object_explorer.set_scene(self._scene)
        else:
            if self._object_explorer is not None and str(self._object_explorer.root) in panes:
                self._object_explorer.root.pack_forget()
                self._paned_window.remove(self._object_explorer.root)

    def toggle_bridge_panel(self) -> None:
        """Toggle the visibility of the scene bridge panel."""
        self._bridge_panel_visible = not self._bridge_panel_visible
        self._bridge_var.set(self._bridge_panel_visible)
        panes = list(self._paned_window.panes())

        if self._bridge_panel_visible:
            # Rebuild if the panel was previously closed via its X button
            if self._bridge_panel is None:
                self._build_bridge_panel()
            # If the build failed (no scene loaded yet), roll back visible state
            if self._bridge_panel is None:
                self._bridge_panel_visible = False
                self._bridge_var.set(False)
                return
            if str(self._bridge_panel.root) not in panes:
                self._bridge_panel.root.master = self._paned_window
                self._paned_window.add(self._bridge_panel.root, weight=0)
        else:
            if self._bridge_panel is not None and str(self._bridge_panel.root) in panes:
                self._bridge_panel.root.pack_forget()
                self._paned_window.remove(self._bridge_panel.root)

    def toggle_entity_names(self) -> None:
        """Toggle entity name labels visibility on the canvas."""
        self._entity_names_visible = not self._entity_names_visible
        self._entity_names_var.set(self._entity_names_visible)

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

        # Create a new top-level window
        editor_window = tk.Toplevel()
        editor_window.title("Connection Editor")
        editor_window.geometry("1200x800")

        # Get the connection registry from the scene
        connection_registry = self._scene.get_connection_registry()

        # Create the connection editor
        # Note: connection_registry is IConnectionRegistry, but ConnectionRegistry implements it
        editor = ConnectionEditor(
            master=editor_window,
            scene=self._scene,
            connection_registry=connection_registry  # type: ignore[arg-type]
        )
        editor.pack(fill=tk.BOTH, expand=True)

        # Set window icon if available (optional)
        try:
            editor_window.iconbitmap(default=str(Path(__file__).parent.parent / "ui" / "icons" / "pyrox.ico"))
        except Exception:
            pass  # Icon not found, continue without it

    def clear_canvas(self) -> None:
        """Clear all items from the canvas without affecting the scene."""
        self._canvas_object_management_service.clear()

    # ==================== Coordinate Conversion ====================

    def world_to_canvas(self, world_x: float, world_y: float) -> Tuple[float, float]:
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

    def canvas_to_world(self, canvas_x: float, canvas_y: float) -> Tuple[float, float]:
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
        """Render the current scene to the canvas."""
        if not self._scene:
            return

        self._canvas_object_management_service.clear()
        self._viewport_service.grid.render()
        self.render_scene_objects()

        # Sync viewport state immediately after render
        self._viewport_service.sync_viewport()
        # NOTE: Do not call update_idletasks() here — it forces a redundant layout pass
        # every render cycle (~30 Hz) and can cause nested event re-entry on Windows.
        # TODO: Add scene background rendering

    def render_scene_objects(self) -> None:
        """Render all scene objects to the canvas with viewport culling and layer ordering."""
        if not self._scene:
            return

        # Track viewport position for culling optimization
        self._last_culling_viewport_x = self.viewport.x
        self._last_culling_viewport_y = self.viewport.y

        # Get visible canvas bounds for culling
        canvas_width = self._canvas.winfo_width()
        canvas_height = self._canvas.winfo_height()

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
        outline_color = self._selection_color if is_selected else "#ffaa00"
        outline_width = self._selection_width if is_selected else 1

        canvas_id = self._canvas.create_rectangle(
            canvas_x,
            canvas_y,
            canvas_x + canvas_w,
            canvas_y + canvas_h,
            fill="",
            outline=outline_color,
            width=outline_width,
            dash=(6, 4),
            tags=("scene_object", obj_id)
        )
        self._canvas_object_management_service.set_object(obj_id, canvas_id)

        if self._entity_names_visible:
            font_size = max(8, int(10 * self.viewport.zoom))
            self._canvas.create_text(
                canvas_x + canvas_w / 2,
                canvas_y - 10 * self.viewport.zoom,
                text=group.name,
                fill=outline_color,
                font=("Arial", font_size),
                tags=("scene_object_label", obj_id)
            )

    def _render_scene_object(
        self,
        obj_id: str,
        scene_obj: ISceneObject
    ) -> None:
        """Render a single scene object to the canvas.

        Args:
            obj_id: Unique identifier for the scene object
            scene_obj: The scene object to render
        """
        # Groups get a dedicated dashed-outline renderer — not a filled shape.
        if isinstance(scene_obj, SceneGroup):
            self._render_scene_group(obj_id, scene_obj)
            return

        # Get properties with defaults
        props = scene_obj.properties
        color = props.get("color", "#4a9eff")
        shape = props.get("shape", "rectangle")

        # Apply viewport transformation to render in canvas space
        canvas_x = scene_obj.x * self.viewport.zoom + self.viewport.x
        canvas_y = scene_obj.y * self.viewport.zoom + self.viewport.y
        canvas_width = scene_obj.width * self.viewport.zoom
        canvas_height = scene_obj.height * self.viewport.zoom

        # Render based on shape type
        canvas_id = None
        is_selected = obj_id in self._canvas_object_management_service.selected_objects
        outline_color = self._selection_color if is_selected else "white"
        outline_width = self._selection_width if is_selected else 2

        if shape == "rectangle":
            canvas_id = self._canvas.create_rectangle(
                canvas_x,
                canvas_y,
                canvas_x + canvas_width,
                canvas_y + canvas_height,
                fill=color,
                outline=outline_color,
                width=outline_width,
                tags=("scene_object", obj_id)
            )
        elif shape == "circle" or shape == "oval":
            canvas_id = self._canvas.create_oval(
                canvas_x,
                canvas_y,
                canvas_x + canvas_width,
                canvas_y + canvas_height,
                fill=color,
                outline=outline_color,
                width=outline_width,
                tags=("scene_object", obj_id)
            )
        elif shape == "line":
            x2 = props.get("x2", scene_obj.x + scene_obj.width)
            y2 = props.get("y2", scene_obj.y + scene_obj.height)
            canvas_x2 = x2 * self.viewport.zoom + self.viewport.x
            canvas_y2 = y2 * self.viewport.zoom + self.viewport.y
            canvas_id = self._canvas.create_line(
                canvas_x,
                canvas_y,
                canvas_x2,
                canvas_y2,
                fill=outline_color if is_selected else color,
                width=max(outline_width if is_selected else 2, int(2 * self.viewport.zoom)),
                tags=("scene_object", obj_id)
            )
        # TODO: Add support for more shapes (polygon, text, image/sprite)

        # Add label for the object
        if canvas_id:
            self._canvas_object_management_service.set_object(obj_id, canvas_id)

            # Draw name label (only if entity names are visible)
            if self._entity_names_visible:
                font_size = max(8, int(10 * self.viewport.zoom))
                _ = self._canvas.create_text(
                    canvas_x + canvas_width / 2,
                    canvas_y - 10 * self.viewport.zoom,
                    text=scene_obj.name,
                    fill="white",
                    font=("Arial", font_size),
                    tags=("scene_object_label", obj_id)
                )

    def _start_render_loop(self) -> None:
        """Start the render loop at controlled frame rate."""
        # Prevent multiple render loops from running simultaneously
        if self._render_timer_id is not None:
            try:
                self._canvas.after_cancel(self._render_timer_id)
            except (tk.TclError, AttributeError):
                pass
            self._render_timer_id = None

        self.gui.schedule_event(100, self._mark_dirty)  # Initial render after short delay
        self._render_loop()

    def _render_loop(self) -> None:
        """Render loop that checks dirty flag and renders if needed."""
        if self._needs_render or self._viewport_service.needs_render():
            self.render_scene()
            self._needs_render = False

        # Update properties panel if visible and there's a selection
        # This ensures the panel shows live updates during object movement
        if self._properties_panel_visible and self._canvas_object_management_service.selected_objects:
            self._update_properties_panel()

        # Schedule next render check
        if self._canvas and self._canvas.winfo_exists():
            self._render_timer_id = self._canvas.after(self._render_interval_ms, self._render_loop)

    def _mark_dirty(self, *_) -> None:
        """Mark scene as needing re-render.

        Called by scene updates, viewport changes, etc.
        Actual render happens at controlled frame rate.
        """
        self._needs_render = True

    def _sync_object_positions(self, *_) -> None:
        """Lightweight position sync for physics updates.

        Updates canvas item positions based on scene object positions
        without full re-render. Used during continuous physics simulation.

        NOTE: This is called at scene update rate (~60 FPS). Keep operations minimal.
        """
        if not self._scene or not self._canvas:
            return

        # Quick early exit if no objects
        objects_dict = self._canvas_object_management_service.objects
        if not objects_dict:
            return

        # Batch update - iterate through objects and update positions
        for obj_id, canvas_id in objects_dict.items():
            scene_obj = self._scene.scene_objects.get(obj_id)
            if not scene_obj:
                continue

            # Calculate new canvas position
            new_canvas_x = scene_obj.x * self.viewport.zoom + self.viewport.x
            new_canvas_y = scene_obj.y * self.viewport.zoom + self.viewport.y

            # Get current canvas position
            try:
                coords = self._canvas.coords(canvas_id)
                if not coords or len(coords) < 2:
                    continue
            except tk.TclError:
                continue

            current_canvas_x = coords[0]
            current_canvas_y = coords[1]

            # Calculate delta
            dx = new_canvas_x - current_canvas_x
            dy = new_canvas_y - current_canvas_y

            # Only update if meaningful change (threshold increased from 0.01 to 0.5 pixels)
            # This significantly reduces unnecessary canvas operations when objects are stationary
            if abs(dx) > 0.5 or abs(dy) > 0.5:
                # Move all items with this obj_id tag (shape + label) in one batch
                # Note: find_withtag is still expensive, but only called when movement detected
                for item in self._canvas.find_withtag(obj_id):
                    self._canvas.move(item, dx, dy)

    # ==================== UI Building Methods ====================

    def _build_toolbar(self) -> None:
        """Build the toolbar with viewer controls."""
        self._toolbar = ttk.Frame(self.content_frame)
        self._toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Design Mode Toggle Button (with icon)
        self._design_mode_btn = ttk.Button(
            self._toolbar,
            text="🎨",  # Design/paint palette emoji
            width=3,
            command=self.toggle_design_mode
        )
        self._design_mode_btn.pack(side=tk.LEFT, padx=2)
        self._create_tooltip(self._design_mode_btn, "Toggle Design Mode")

        # Object Palette Toggle Button
        self._object_palette_btn = ttk.Button(
            self._toolbar,
            text="🧰",  # Toolbox emoji
            width=3,
            command=self.toggle_object_palette
        )
        self._object_palette_btn.pack(side=tk.LEFT, padx=2)
        self._create_tooltip(self._object_palette_btn, "Toggle Object Palette")

        # Properties Panel Toggle Button
        self._properties_panel_btn = ttk.Button(
            self._toolbar,
            text="📋",  # Clipboard emoji
            width=3,
            command=self.toggle_properties_panel
        )
        self._properties_panel_btn.pack(side=tk.LEFT, padx=2)
        self._create_tooltip(self._properties_panel_btn, "Toggle Properties Panel")

        # Scene Bridge Panel Toggle Button
        self._bridge_panel_btn = ttk.Button(
            self._toolbar,
            text="🔗",  # Link emoji
            width=3,
            command=self.toggle_bridge_panel
        )
        self._bridge_panel_btn.pack(side=tk.LEFT, padx=2)
        self._create_tooltip(self._bridge_panel_btn, "Toggle Scene Bridge Panel")

        # Object Explorer Toggle Button
        self._object_explorer_btn = ttk.Button(
            self._toolbar,
            text="🗂️",  # File cabinet emoji
            width=3,
            command=self.toggle_object_explorer
        )
        self._object_explorer_btn.pack(side=tk.LEFT, padx=2)
        self._create_tooltip(self._object_explorer_btn, "Toggle Object Explorer")

        # Separator
        ttk.Separator(self._toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Entity Names Toggle Button
        self._entity_names_btn = ttk.Button(
            self._toolbar,
            text="🏷️",  # Label emoji
            width=3,
            command=self.toggle_entity_names
        )
        self._entity_names_btn.pack(side=tk.LEFT, padx=2)
        self._create_tooltip(self._entity_names_btn, "Toggle Entity Names")

        # Separator
        ttk.Separator(self._toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Selection info
        self._selection_label = ttk.Label(
            self._toolbar,
            text="No selection"
        )
        self._selection_label.pack(side=tk.LEFT, padx=5)

        # Separator
        ttk.Separator(self._toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

    def _create_tooltip(self, widget, text: str) -> None:
        """Create a simple tooltip for a widget.

        Args:
            widget: The widget to attach the tooltip to
            text: The tooltip text to display
        """
        def on_enter(event):
            # Create tooltip window
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)  # Remove window decorations
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

            label = tk.Label(
                tooltip,
                text=text,
                background="#ffffe0",
                relief=tk.SOLID,
                borderwidth=1,
                padx=5,
                pady=2
            )
            label.pack()

            # Store reference to destroy later
            widget._tooltip = tooltip

        def on_leave(event):
            if hasattr(widget, '_tooltip'):
                widget._tooltip.destroy()
                delattr(widget, '_tooltip')

        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

    def _build_canvas(self) -> None:
        """Build the main canvas for rendering."""
        # Use PanedWindow for resizable split between canvas and properties panel
        self._paned_window = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        self._paned_window.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Canvas container
        self._canvas_container = ttk.Frame(self._paned_window)
        self._paned_window.add(self._canvas_container, weight=1)

        # Create canvas
        self._canvas = tk.Canvas(
            self._canvas_container,
            bg="#727272",
            highlightthickness=0
        )
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._viewport_service.set_canvas(self._canvas)

        # TODO: Add scrollbars for large scenes
        # TODO: Add ruler/coordinate display

    def _build_properties_panel(self) -> None:
        """Build the properties panel for selected objects."""
        self._properties_panel = TkPropertyPanel(
            parent=self._paned_window,
            title="Object Properties",
            width=250,
            on_property_changed=self._on_property_changed
        )

        def _on_properties_panel_closed(frame):
            """Reset state when the properties panel's X button destroys the frame."""
            self._properties_panel = None
            self._properties_panel_visible = False
            self._properties_var.set(False)
            self._properties_panel_current_object_id = None

        self._properties_panel.on_destroy().append(_on_properties_panel_closed)
        # Panel is initially hidden, will be added to paned window when toggled

    def _build_object_explorer(self) -> None:
        """Build the object explorer side panel."""
        self._object_explorer = TkObjectExplorer(
            parent=self._paned_window,
            title="object explorer",
            width=230,
            on_selection_changed=self._on_object_explorer_selection,
        )
        self._object_explorer.set_scene(self._scene)

        def _on_explorer_closed(frame):
            """Reset state when the explorer's X button destroys the frame."""
            self._object_explorer = None
            self._object_explorer_visible = False
            self._object_explorer_var.set(False)

        self._object_explorer.on_destroy().append(_on_explorer_closed)
        # Panel is initially hidden; added to PanedWindow when toggled

    def _build_bridge_panel(self) -> None:
        """Build the scene bridge panel."""
        # Bridge is owned by SceneBridgeService; the viewer only holds a reference.
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
            """Reset state when the bridge panel's X button destroys the frame."""
            self._bridge_panel = None
            self._bridge_panel_visible = False
            self._bridge_var.set(False)

        self._bridge_panel.on_destroy().append(_on_bridge_panel_closed)
        # Panel is initially hidden, will be added to paned window when toggled

    def _build_object_palette(self) -> None:
        """Build the object palette for design mode."""
        # Palette frame (initially hidden, shown on left side of canvas)
        self._object_palette_frame = ttk.Frame(self._canvas_container, width=200)
        # Don't pack it yet - will be shown when toggled

        # Palette title
        title_label = ttk.Label(
            self._object_palette_frame,
            text="Object Palette",
            font=("Arial", 10, "bold")
        )
        title_label.pack(side=tk.TOP, pady=5)

        # Scrollable frame for object buttons
        canvas_scroll = tk.Canvas(self._object_palette_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            self._object_palette_frame,
            orient=tk.VERTICAL,
            command=canvas_scroll.yview
        )
        canvas_scroll.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        palette_content = ttk.Frame(canvas_scroll)
        canvas_scroll.create_window((0, 0), window=palette_content, anchor=tk.NW)

        # Object template buttons will be populated in _initialize_object_templates
        self._palette_content_frame = palette_content

        def _configure_scroll(event):
            canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))

        palette_content.bind("<Configure>", _configure_scroll)

    def _build_context_menus(self) -> None:
        """Build context menus for different contexts."""
        # Context menu for empty canvas space
        self._canvas_context_menu = PyroxContextMenu(self._canvas)

        # Context menu for selected objects
        self._object_context_menu = PyroxContextMenu(self._canvas)

        # Populate canvas context menu
        self._canvas_context_menu.add_item(MenuItem(
            id="paste",
            label="Paste",
            command=self._context_paste,
            accelerator="Ctrl+V",
            icon="📋"
        ))
        self._canvas_context_menu.add_item(MenuItem(
            id="zoom_in",
            label="Zoom In",
            command=lambda: self._viewport_service.zoom.zoom_in(factor=1.25),
            accelerator="Ctrl++",
            icon="🔍➕",
            separator_before=True
        ))
        self._canvas_context_menu.add_item(MenuItem(
            id="zoom_out",
            label="Zoom Out",
            command=lambda: self._viewport_service.zoom.zoom_out(factor=1.25),
            accelerator="Ctrl+-",
            icon="🔍➖"
        ))
        self._canvas_context_menu.add_item(MenuItem(
            id="reset_view",
            label="Reset View",
            command=self._viewport_service.reset_view,
            icon="🔄",
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

    def _bind_events(
        self,
        *_,
    ) -> None:
        """Bind mouse and keyboard events for interaction."""
        self._canvas.update_idletasks()
        self._canvas_object_management_service.set_canvas(self._canvas)
        self._viewport_service.set_canvas(self._canvas)

        # Left mouse button - context-dependent (select, draw, or drag)
        self._canvas.bind("<ButtonPress-1>", self._on_left_click)
        self._canvas.bind("<B1-Motion>", self._on_left_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_left_release)

        # Right mouse button - context menu
        self._canvas.bind("<ButtonPress-3>", self._on_right_click)

        # Delete key to remove selected objects
        self._canvas.bind("<Delete>", lambda e: self.delete_selected_objects())

        # Deselect with Escape key
        self._canvas.bind("<Escape>", lambda e: self.clear_selection())

        # Toggle entity names with Ctrl+L
        self._canvas.bind("<Control-l>", lambda e: self.toggle_entity_names())

        # Layer ordering shortcuts
        self._canvas.bind("<Control-bracketright>", lambda e: self._context_layer_up())  # Ctrl+]
        self._canvas.bind("<Control-bracketleft>", lambda e: self._context_layer_down())  # Ctrl+[
        self._canvas.bind("<Control-Shift-bracketright>", lambda e: self._context_bring_to_front())  # Ctrl+Shift+]
        self._canvas.bind("<Control-Shift-bracketleft>", lambda e: self._context_send_to_back())  # Ctrl+Shift+[

        # Grouping shortcuts
        self._canvas.bind("<Control-Alt-g>", lambda e: self._context_group_selected())   # Ctrl+Alt+G
        self._canvas.bind("<Control-Alt-u>", lambda e: self._context_ungroup_selected())  # Ctrl+Alt+U

        # Subscribe to scene events using stored callback references
        SceneEventBus.subscribe(
            SceneEventType.SCENE_LOADED,
            self._scene_loaded_callback
        )
        SceneEventBus.subscribe(
            SceneEventType.SCENE_UNLOADED,
            self._scene_unloaded_callback
        )

        # Register the unbind for when the frame is closed to prevent memory leaks
        self.on_destroy().append(self._unbind_events)

        self._canvas.update_idletasks()  # Final update to ensure canvas is ready before rendering

        # Use dirty flag pattern instead of direct render on every update
        # For physics updates, use lightweight position sync instead of full render
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
        command: Optional[Callable] = None,
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
            menu_id="scene.view.design_mode",
            command=self.toggle_design_mode,
            enable=enable
        )
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

    def _on_left_click(self, event: tk.Event) -> None:
        """Handle left mouse button press - context dependent on current tool.

        Args:
            event: Mouse click event
        """
        if self._current_tool == "place_object":
            # Design mode - place object from template
            scene_x = (event.x - self.viewport.x) / self.viewport.zoom
            scene_y = (event.y - self.viewport.y) / self.viewport.zoom
            self._place_object_from_template(scene_x, scene_y)
        elif self._current_tool == "select":
            self._on_select_click(event)

    def _on_left_drag(self, event: tk.Event) -> None:
        """Handle left mouse drag - drawing or object manipulation.

        Args:
            event: Mouse drag event
        """
        if self._current_tool == "select":
            self._on_drag_object(event)
        else:
            # Drawing mode - show preview
            self._on_draw_preview(event)

    def _on_left_release(self, event: tk.Event) -> None:
        """Handle left mouse button release.

        Args:
            event: Mouse release event
        """
        if self._current_tool == "select":
            self._on_drag_end(event)
        else:
            # Drawing mode - finalize
            self._on_draw_complete(event)

    def _on_select_click(self, event: tk.Event) -> None:
        """Handle selection click events.

        Args:
            event: Mouse click event
        """
        canvas_items = self._canvas_object_management_service.get_non_grid_objects(event)

        if not canvas_items:
            # Click on empty space - clear selection unless Ctrl is held
            if not (event.state & 0x0004):  # Check if Ctrl key is not pressed  # type: ignore
                self.clear_selection()
            return

        # Find which scene object was clicked
        clicked_obj_id = self._canvas_object_management_service.get_from_canvas_id(canvas_items[-1])  # Get topmost item

        if clicked_obj_id:
            # If the clicked object is a member of a group, redirect to the group anchor
            if self._scene:
                clicked_scene_obj = self._scene.scene_objects.get(clicked_obj_id)
                if clicked_scene_obj and hasattr(clicked_scene_obj, 'get_group_id'):
                    group_id = clicked_scene_obj.get_group_id()
                    if group_id and group_id in self._scene.scene_objects:
                        clicked_obj_id = group_id

            # Check if Ctrl key is pressed for multi-select
            if event.state & 0x0004:  # Ctrl key  # type: ignore
                self.toggle_selection(clicked_obj_id)
            else:
                # Single select (clear previous selection)
                self.select_object(clicked_obj_id, clear_previous=True)

            # Prepare for potential drag
            self._drag_start_x = event.x
            self._drag_start_y = event.y

    def _on_drag_object(self, event: tk.Event) -> None:
        """Handle dragging selected objects.

        Args:
            event: Mouse drag event
        """
        if not self._canvas_object_management_service.selected_objects:
            return

        if self._drag_start_x is None or self._drag_start_y is None:
            return

        # Calculate drag delta in canvas coordinates
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y

        # Only start dragging if moved more than 3 pixels (avoid accidental drags)
        if not self._is_dragging and (abs(dx) < 3 and abs(dy) < 3):
            return

        self._is_dragging = True

        # Convert to scene coordinates
        scene_dx = dx / self.viewport.zoom
        scene_dy = dy / self.viewport.zoom

        # Move canvas items directly for smooth dragging (no full redraw!)
        for obj_id in self._canvas_object_management_service.selected_objects:
            # Move the canvas shape and label by delta
            for item in self._canvas.find_withtag(obj_id):
                self._canvas.move(item, dx, dy)

            # Update underlying scene object position
            if self._scene:
                scene_obj = self._scene.scene_objects.get(obj_id)
                if scene_obj:
                    if isinstance(scene_obj, SceneGroup):
                        # Also move all member canvas items so they follow the anchor
                        for member_id in scene_obj.get_member_ids():
                            for item in self._canvas.find_withtag(member_id):
                                self._canvas.move(item, dx, dy)

                        # Update ALL positions (anchor + members) via move_delta
                        snapped_x, snapped_y = self._viewport_service.grid.snap_to_grid(
                            scene_obj.x + scene_dx, scene_obj.y + scene_dy
                        )
                        scene_obj.move_delta(snapped_x - scene_obj.x, snapped_y - scene_obj.y)
                    else:
                        # Calculate new position
                        new_x = scene_obj.x + scene_dx
                        new_y = scene_obj.y + scene_dy

                        # Apply snap to grid if enabled
                        new_x, new_y = self._viewport_service.grid.snap_to_grid(new_x, new_y)

                        # Update object position
                        scene_obj.physics_body.set_x(new_x)
                        scene_obj.physics_body.set_y(new_y)

                        props = scene_obj.properties
                        # For line objects, also update x2, y2
                        if props.get("shape") == "line":
                            # Calculate line endpoint delta based on snapped position
                            actual_dx = new_x - scene_obj.x
                            actual_dy = new_y - scene_obj.y
                            props["x2"] = props.get("x2", 0) + actual_dx
                            props["y2"] = props.get("y2", 0) + actual_dy

        # Update drag start position
        self._drag_start_x = event.x
        self._drag_start_y = event.y

        # No render_scene() call - just moved canvas items directly!

    def _on_drag_end(self, event: tk.Event) -> None:
        """Handle end of drag operation.

        Args:
            event: Mouse release event
        """
        self._is_dragging = False
        self._drag_start_x = None
        self._drag_start_y = None

    # ==================== Drawing & Placement Event Handlers ====================

    def _on_draw_start(self, event: tk.Event) -> None:
        """Handle start of drawing operation.

        Args:
            event: Mouse press event
        """
        # Convert canvas coordinates to scene coordinates
        self._draw_start_x = (event.x - self.viewport.x) / self.viewport.zoom
        self._draw_start_y = (event.y - self.viewport.y) / self.viewport.zoom

    def _on_draw_preview(self, event: tk.Event) -> None:
        """Show preview of shape being drawn.

        Args:
            event: Mouse drag event
        """
        if self._draw_start_x is None or self._draw_start_y is None:
            return

        # Remove previous preview
        if self._temp_draw_id:
            self._canvas.delete(self._temp_draw_id)

        # Convert current position to scene coordinates
        end_x = (event.x - self.viewport.x) / self.viewport.zoom
        end_y = (event.y - self.viewport.y) / self.viewport.zoom

        # Draw preview in canvas coordinates
        canvas_x1 = self._draw_start_x * self.viewport.zoom + self.viewport.x
        canvas_y1 = self._draw_start_y * self.viewport.zoom + self.viewport.y
        canvas_x2 = end_x * self.viewport.zoom + self.viewport.x
        canvas_y2 = end_y * self.viewport.zoom + self.viewport.y

        # Draw preview based on tool
        if self._current_tool == "rectangle":
            self._temp_draw_id = self._canvas.create_rectangle(
                canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                outline="yellow", width=2, dash=(4, 4), tags="preview"
            )
        elif self._current_tool == "circle":
            self._temp_draw_id = self._canvas.create_oval(
                canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                outline="yellow", width=2, dash=(4, 4), tags="preview"
            )
        elif self._current_tool == "line":
            self._temp_draw_id = self._canvas.create_line(
                canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                fill="yellow", width=2, dash=(4, 4), tags="preview"
            )

    def _on_draw_complete(self, event: tk.Event) -> None:
        """Complete drawing operation and create scene object.

        Args:
            event: Mouse release event
        """
        if self._draw_start_x is None or self._draw_start_y is None:
            return

        # Remove preview
        if self._temp_draw_id:
            self._canvas.delete(self._temp_draw_id)
            self._temp_draw_id = None

        # Convert end position to scene coordinates
        end_x = (event.x - self.viewport.x) / self.viewport.zoom
        end_y = (event.y - self.viewport.y) / self.viewport.zoom

        # Calculate dimensions
        x = min(self._draw_start_x, end_x)
        y = min(self._draw_start_y, end_y)
        width = abs(end_x - self._draw_start_x)
        height = abs(end_y - self._draw_start_y)

        # Ignore very small shapes (likely accidental clicks)
        if width < 5 and height < 5:
            self._draw_start_x = None
            self._draw_start_y = None
            return

        # Create new scene object
        # NOTE: This creates a basic dict - you may need to extend ISceneObject
        # to properly handle object creation from the UI
        self._create_scene_object(
            shape=self._current_tool,
            x=x, y=y,
            width=width, height=height,
            x2=end_x if self._current_tool == "line" else None,
            y2=end_y if self._current_tool == "line" else None
        )

        # Reset drawing state
        self._draw_start_x = None
        self._draw_start_y = None

    def _create_scene_object(
        self,
        shape: str,
        x: float,
        y: float,
        width: float,
        height: float,
        x2: Optional[float] = None,
        y2: Optional[float] = None
    ) -> None:
        """Create a new scene object and add it to the scene.

        Args:
            shape: Shape type (rectangle, circle, line)
            x: X position in scene coordinates
            y: Y position in scene coordinates
            width: Width in scene coordinates
            height: Height in scene coordinates
            x2: End X for line objects
            y2: End Y for line objects

        Note:
            This method creates a basic object. You may need to extend your
            ISceneObject implementation to support dynamic object creation.
        """
        if not self.scene:
            log(self).warning("Cannot create object: no scene loaded")
            return

        factory = self.scene.get_scene_object_factory()
        if not factory:
            log(self).error(
                "Cannot create scene object: SceneObject factory not found. "
                "You need to implement get_scene_object_factory() in your IScene."
            )
            return

        # Generate unique ID
        self._object_counter += 1
        obj_id = f"{shape}_{self._object_counter}"

        # Create properties dict
        props = {
            "id": obj_id,
            "name": obj_id,
            "scene_object_type": 'Cube',
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "color": "#4a9eff",
            "shape": shape
        }

        if shape == "line" and x2 is not None and y2 is not None:
            props["x2"] = x2
            props["y2"] = y2

        # Create a basic scene object wrapper
        # NOTE: You'll need to implement a factory method or extend ISceneObject
        # This is a placeholder that assumes your scene can handle dict-like objects
        try:
            scene_obj = factory.create_scene_object(
                data=props
            )
            if not isinstance(scene_obj, ISceneObject):
                raise TypeError("Factory did not return a valid ISceneObject")

            self.scene.add_scene_object(scene_obj)
            self.render_scene()

            log(self).info(f"Created {shape} object: {obj_id}")
        except Exception as e:
            log(self).error(f"Failed to create scene object: {e}")

    # ==================== Object Templates & Design Mode ====================

    def _initialize_object_templates(self) -> None:
        """Initialize object templates and populate palette."""
        # Define object templates
        self._templates = PhysicsSceneFactory.get_all_templates()

        # Populate palette with buttons
        for template_name in self._templates.keys():
            btn = ttk.Button(
                self._palette_content_frame,
                text=template_name,
                command=lambda name=template_name: self._select_object_template(name)
            )
            btn.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

    def _select_object_template(self, template_name: str) -> None:
        """Select an object template for placement.

        Args:
            template_name: Name of the template to select
        """
        self._current_object_template = template_name
        # Switch to placement mode
        self._current_tool = "place_object"
        self._canvas.config(cursor="crosshair")
        log(self).info(f"Selected template: {template_name}. Click on canvas to place.")

    def _place_object_from_template(self, scene_x: float, scene_y: float) -> None:
        """Place an object from the current template at the given position.

        Args:
            scene_x: X coordinate in scene space
            scene_y: Y coordinate in scene space
        """
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

    # ==================== Context Menu Handlers ====================

    def _on_right_click(self, event: tk.Event) -> None:
        """Handle right-click to show context menu.

        Args:
            event: Mouse click event
        """
        # Find what was clicked (excluding grid items)
        canvas_items = self._canvas_object_management_service.get_non_grid_objects(event)

        # Check if we clicked on a scene object
        clicked_obj_id = self._canvas_object_management_service.get_from_canvas_id(canvas_items[-1]) if canvas_items else None

        if clicked_obj_id:
            # If the clicked object is a member of a group, redirect to the group anchor
            if self._scene:
                clicked_scene_obj = self._scene.scene_objects.get(clicked_obj_id)
                if clicked_scene_obj and hasattr(clicked_scene_obj, 'get_group_id'):
                    group_id = clicked_scene_obj.get_group_id()
                    if group_id and group_id in self._scene.scene_objects:
                        clicked_obj_id = group_id

            # Clicked on an object - ensure it's selected
            if clicked_obj_id not in self._canvas_object_management_service.selected_objects:
                self.select_object(clicked_obj_id, clear_previous=True)

            # Show object context menu
            self._object_context_menu.post(event.x_root, event.y_root)
        else:
            # Clicked on empty space - show canvas context menu
            self._canvas_context_menu.post(event.x_root, event.y_root)

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

        # Get mouse position relative to viewport for paste location
        mouse_x = self._canvas.winfo_pointerx() - self._canvas.winfo_rootx()
        mouse_y = self._canvas.winfo_pointery() - self._canvas.winfo_rooty()
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

    def _paste_object_data(self, obj_data: dict) -> Optional[ISceneObject]:
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

    def _paste_group_data(self, group_data: dict) -> Optional["SceneGroup"]:
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
        self._selection_label.config(text=self._canvas_object_management_service.selected_objects_display)

        # Only force refresh properties panel if selection actually changed
        if self._properties_panel_visible:
            current_selection = set(self._canvas_object_management_service.selected_objects)
            if current_selection != self._previous_selection:
                self._update_properties_panel(force_refresh=True)
                self._previous_selection = current_selection.copy()

    def _update_object_appearance(self, obj_id: str) -> None:
        """Update visual appearance of an object based on selection state.

        Args:
            obj_id: ID of the object to update
        """
        if obj_id not in self._canvas_object_management_service.objects:
            return

        canvas_id = self._canvas_object_management_service.objects[obj_id]
        is_selected = obj_id in self._canvas_object_management_service.selected_objects

        # Update outline color and width
        outline_color = self._selection_color if is_selected else "white"
        outline_width = self._selection_width if is_selected else 2

        try:
            self._canvas.itemconfig(canvas_id, outline=outline_color, width=outline_width)
        except tk.TclError:
            # Handle line objects which use 'fill' instead of 'outline'
            try:
                if is_selected:
                    self._canvas.itemconfig(canvas_id, fill=outline_color, width=outline_width)
                else:
                    # Restore original color from scene object
                    if self._scene:
                        scene_obj = self._scene.scene_objects.get(obj_id)
                        if scene_obj:
                            color = scene_obj.properties.get("color", "#4a9eff")
                            self._canvas.itemconfig(canvas_id, fill=color, width=2)
            except tk.TclError:
                pass

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
        """Handle property changes from the properties panel.

        Args:
            property_name: Name of the property that changed
            new_value: New value for the property
        """
        # If layer changed, need to re-render entire scene for correct z-order
        if property_name == 'layer':
            self.render_scene()
            log(self).debug(f"Layer changed to {new_value}, re-rendering scene")
            return

        # Only re-render the affected object(s), not the entire scene
        if self._canvas_object_management_service.selected_objects:
            for obj_id in self._canvas_object_management_service.selected_objects:
                # Update the specific canvas item appearance
                self._update_object_appearance(obj_id)

                # If position changed, need to re-render that object
                if property_name in ('x', 'y', 'width', 'height', 'radius', 'name', 'color'):
                    if self._scene:
                        scene_obj = self._scene.scene_objects.get(obj_id)
                        if scene_obj:
                            # Delete old rendering
                            self._canvas.delete(obj_id)
                            # Re-render just this object
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


__all__ = ['SceneViewerFrame']

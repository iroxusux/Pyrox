"""2D Scene Viewer Frame for Pyrox.

This module provides a Tkinter-based canvas frame for viewing and interacting
with 2D scenes containing sprites and simple shapes. Supports panning, zooming,
and integrates with the Scene workflow.
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, Tuple
from pyrox.interfaces import (
    IScene,
    ISceneObject,
    IViewport
)
from pyrox.models.gui.tk.frame import TkinterTaskFrame
from pyrox.models.gui import TkPropertyPanel
from pyrox.models.protocols import Area2D, Zoomable
from pyrox.services import (
    log,
    ViewportPanningService,
    ViewportZoomingService,
    ViewportGriddingService
)


class SceneViewerViewPort(
    IViewport,
    Area2D,
    Zoomable
):
    """Viewport state for the SceneViewerFrame.

    Attributes:
        x: X offset of the viewport
        y: Y offset of the viewport
        zoom: Zoom level of the viewport
    """

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        zoom: float = 1.0,
        max_zoom: float = 10.0,
        min_zoom: float = 0.1
    ):
        Area2D.__init__(self, x, y)
        Zoomable.__init__(self, zoom)
        self.max_zoom = max_zoom
        self.min_zoom = min_zoom

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, SceneViewerViewPort):
            return False
        return (
            self.x == value.x and
            self.y == value.y and
            self.zoom == value.zoom
        )

    def get_delta(
        self,
        other: IViewport,
    ) -> Tuple[float, float, float]:
        """Get the delta between this viewport and another.

        Args:
            viewport: Viewport to compare against
        Returns:
            Tuple of (delta_x, delta_y, delta_zoom)
        """
        delta_x = other.x - self.x
        delta_y = other.y - self.y
        delta_zoom = other.zoom - self.zoom
        return (delta_x, delta_y, delta_zoom)

    def reset(
        self
    ) -> None:
        """Reset the viewport to default state."""
        self.x = 0.0
        self.y = 0.0
        self.zoom = 1.0

    def update(
        self,
        other: IViewport
    ) -> None:
        self.x = other.x
        self.y = other.y
        self.zoom = other.zoom


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

    def __init__(
        self,
        parent,
        name: str = "Scene Viewer",
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
        self._canvas_objects: Dict[str, int] = {}  # scene_object_id -> canvas_id

        # Viewport state for panning and zooming
        self._viewport = SceneViewerViewPort()
        self._last_viewport = SceneViewerViewPort()

        # Mouse interaction state
        self._viewport_panning_service = ViewportPanningService(
            canvas=None,
            viewport=self._viewport
        )
        self._viewport_panning_service.on_pan_callbacks.append(self._update_viewport)
        self._viewport_zooming_service = ViewportZoomingService(
            canvas=None,
            viewport=self._viewport
        )
        self._viewport_zooming_service.on_zoom_callbacks.append(self._update_viewport)
        self._viewport_gridding_service = ViewportGriddingService(
            canvas=None,
            viewport=self._viewport
        )

        # Selection state
        self._selected_objects: set[str] = set()  # Set of selected object IDs
        self._selection_color: str = "#ffaa00"  # Orange highlight for selection
        self._selection_width: int = 3

        # Properties panel state
        self._properties_panel_visible: bool = False
        self._properties_panel: Optional[TkPropertyPanel] = None

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
        self._object_palette_visible: bool = False
        self._object_palette_frame: Optional[ttk.Frame] = None
        self._current_object_template: Optional[str] = None  # Selected object template
        self._snap_to_grid: bool = False

        # Build the UI
        self._build_toolbar()
        self._build_canvas()
        self._build_properties_panel()
        self._build_object_palette()
        self._bind_events()
        self._initialize_object_templates()
        self.render_scene()

    def _build_toolbar(self) -> None:
        """Build the toolbar with viewer controls."""
        self._toolbar = ttk.Frame(self.content_frame)
        self._toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Zoom controls
        ttk.Label(self._toolbar, text="Zoom:").pack(side=tk.LEFT, padx=5)

        self._zoom_in_btn = ttk.Button(
            self._toolbar,
            text="+",
            width=3,
            command=self._viewport_zooming_service.zoom_in
        )
        self._zoom_in_btn.pack(side=tk.LEFT, padx=2)

        self._zoom_out_btn = ttk.Button(
            self._toolbar,
            text="-",
            width=3,
            command=self._viewport_zooming_service.zoom_out
        )
        self._zoom_out_btn.pack(side=tk.LEFT, padx=2)

        self._reset_view_btn = ttk.Button(
            self._toolbar,
            text="Reset View",
            command=self.reset_view
        )
        self._reset_view_btn.pack(side=tk.LEFT, padx=5)

        # Zoom level display
        self._zoom_label = ttk.Label(
            self._toolbar,
            text=f"{int(self.viewport.zoom * 100)}%"
        )
        self._zoom_label.pack(side=tk.LEFT, padx=5)

        # Separator
        ttk.Separator(self._toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Grid toggle
        self._grid_var = tk.BooleanVar(value=self._viewport_gridding_service.enabled)
        self._grid_toggle = ttk.Checkbutton(
            self._toolbar,
            text="Show Grid",
            variable=self._grid_var,
            command=self.toggle_grid
        )
        self._grid_toggle.pack(side=tk.LEFT, padx=5)

        # Separator
        ttk.Separator(self._toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Selection info
        self._selection_label = ttk.Label(
            self._toolbar,
            text="No selection"
        )
        self._selection_label.pack(side=tk.LEFT, padx=5)

        # Separator
        ttk.Separator(self._toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Drawing tools
        ttk.Label(self._toolbar, text="Tool:").pack(side=tk.LEFT, padx=5)

        self._tool_var = tk.StringVar(value=self._current_tool)

        tools_frame = ttk.Frame(self._toolbar)
        tools_frame.pack(side=tk.LEFT, padx=2)

        ttk.Radiobutton(
            tools_frame,
            text="Select",
            variable=self._tool_var,
            value="select",
            command=self._on_tool_change
        ).pack(side=tk.LEFT, padx=2)

        ttk.Radiobutton(
            tools_frame,
            text="Rectangle",
            variable=self._tool_var,
            value="rectangle",
            command=self._on_tool_change
        ).pack(side=tk.LEFT, padx=2)

        ttk.Radiobutton(
            tools_frame,
            text="Circle",
            variable=self._tool_var,
            value="circle",
            command=self._on_tool_change
        ).pack(side=tk.LEFT, padx=2)

        ttk.Radiobutton(
            tools_frame,
            text="Line",
            variable=self._tool_var,
            value="line",
            command=self._on_tool_change
        ).pack(side=tk.LEFT, padx=2)

        # Separator
        ttk.Separator(self._toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Delete button
        self._delete_btn = ttk.Button(
            self._toolbar,
            text="Delete Selected",
            command=self.delete_selected_objects
        )
        self._delete_btn.pack(side=tk.LEFT, padx=5)

        # Separator
        ttk.Separator(self._toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Design Mode toggle
        self._design_mode_var = tk.BooleanVar(value=self._design_mode)
        self._design_mode_toggle = ttk.Checkbutton(
            self._toolbar,
            text="Design Mode",
            variable=self._design_mode_var,
            command=self.toggle_design_mode
        )
        self._design_mode_toggle.pack(side=tk.LEFT, padx=5)

        # Object Palette toggle (only visible in design mode)
        self._object_palette_var = tk.BooleanVar(value=self._object_palette_visible)
        self._object_palette_toggle = ttk.Checkbutton(
            self._toolbar,
            text="Object Palette",
            variable=self._object_palette_var,
            command=self.toggle_object_palette,
            state=tk.DISABLED  # Enabled when design mode is on
        )
        self._object_palette_toggle.pack(side=tk.LEFT, padx=5)

        # Snap to grid
        self._snap_var = tk.BooleanVar(value=self._snap_to_grid)
        self._snap_toggle = ttk.Checkbutton(
            self._toolbar,
            text="Snap to Grid",
            variable=self._snap_var,
            command=self.toggle_snap_to_grid
        )
        self._snap_toggle.pack(side=tk.LEFT, padx=5)

        # Separator
        ttk.Separator(self._toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Save/Load Scene buttons
        self._save_scene_btn = ttk.Button(
            self._toolbar,
            text="Save Scene",
            command=self.save_scene_dialog
        )
        self._save_scene_btn.pack(side=tk.LEFT, padx=2)

        self._load_scene_btn = ttk.Button(
            self._toolbar,
            text="Load Scene",
            command=self.load_scene_dialog
        )
        self._load_scene_btn.pack(side=tk.LEFT, padx=2)

        # Separator
        ttk.Separator(self._toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Properties panel toggle
        self._properties_var = tk.BooleanVar(value=self._properties_panel_visible)
        self._properties_toggle = ttk.Checkbutton(
            self._toolbar,
            text="Properties Panel",
            variable=self._properties_var,
            command=self.toggle_properties_panel
        )
        self._properties_toggle.pack(side=tk.LEFT, padx=5)

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
        # Panel is initially hidden, will be added to paned window when toggled

    def _bind_events(self) -> None:
        """Bind mouse and keyboard events for interaction."""
        self._viewport_panning_service.set_canvas(self._canvas)
        self._viewport_zooming_service.set_canvas(self._canvas)
        self._viewport_gridding_service.set_canvas(self._canvas)

        # Left mouse button - context-dependent (select, draw, or drag)
        self._canvas.bind("<ButtonPress-1>", self._on_left_click)
        self._canvas.bind("<B1-Motion>", self._on_left_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_left_release)

        # Delete key to remove selected objects
        self._canvas.bind("<Delete>", lambda e: self.delete_selected_objects())

        # Deselect with Escape key
        self._canvas.bind("<Escape>", lambda e: self.clear_selection())

        # TODO: Add keyboard shortcuts (Ctrl+Z undo, Ctrl+D duplicate, etc.)

    def _on_tool_change(self) -> None:
        """Handle tool selection change."""
        self._current_tool = self._tool_var.get()
        # Clear selection when switching to drawing tools
        if self._current_tool != "select":
            self.clear_selection()

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
        else:
            # Drawing mode
            self._on_draw_start(event)

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
        # Find canvas item at click position
        canvas_items = self._canvas.find_overlapping(
            event.x - 2, event.y - 2,
            event.x + 2, event.y + 2
        )

        # Filter out grid items
        canvas_items = [item for item in canvas_items if "grid" not in self._canvas.gettags(item)]

        if not canvas_items:
            # Click on empty space - clear selection unless Ctrl is held
            if not (event.state & 0x0004):  # Check if Ctrl key is not pressed  # type: ignore
                self.clear_selection()
            return

        # Find which scene object was clicked
        clicked_obj_id = None
        for obj_id, canvas_id in self._canvas_objects.items():
            if canvas_id in canvas_items:
                clicked_obj_id = obj_id
                break

        if clicked_obj_id:
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
        if not self._selected_objects or self._drag_start_x is None or self._drag_start_y is None:
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

        # Move all selected objects
        if self._scene:
            for obj_id in self._selected_objects:
                scene_obj = self._scene.scene_objects.get(obj_id)
                if scene_obj:
                    # Update object position
                    scene_obj.set_x(scene_obj.x + scene_dx)
                    scene_obj.set_y(scene_obj.y + scene_dy)

                    props = scene_obj.properties
                    # For line objects, also update x2, y2
                    if props.get("shape") == "line":
                        props["x2"] = props.get("x2", 0) + scene_dx
                        props["y2"] = props.get("y2", 0) + scene_dy

        # Update drag start position
        self._drag_start_x = event.x
        self._drag_start_y = event.y

        # Redraw scene
        self.render_scene()

    def _on_drag_end(self, event: tk.Event) -> None:
        """Handle end of drag operation.

        Args:
            event: Mouse release event
        """
        self._is_dragging = False
        self._drag_start_x = None
        self._drag_start_y = None

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

    def delete_selected_objects(self) -> None:
        """Delete all currently selected objects from the scene."""
        if not self._selected_objects:
            log(self).info("No objects selected to delete")
            return

        if not self._scene:
            log(self).warning("Cannot delete objects: no scene loaded")
            return

        # Get list before clearing
        to_delete = list(self._selected_objects)

        # Remove from scene
        for obj_id in to_delete:
            try:
                # Assuming scene has remove_scene_object method
                if hasattr(self._scene, 'remove_scene_object'):
                    self._scene.remove_scene_object(obj_id)
                elif hasattr(self._scene, 'scene_objects'):
                    # Fallback: directly manipulate scene_objects dict
                    self._scene.scene_objects.pop(obj_id, None)
                else:
                    log(self).error(
                        f"Cannot remove object {obj_id}: scene lacks removal method. "
                        "You need to implement remove_scene_object() in your IScene."
                    )
            except Exception as e:
                log(self).error(f"Failed to delete object {obj_id}: {e}")

        # Clear selection
        self.clear_selection()

        # Redraw
        self.render_scene()

        log(self).info(f"Deleted {len(to_delete)} object(s)")

    def reset_view(self) -> None:
        """Reset viewport to default position and zoom."""
        self.viewport.reset()
        self.last_viewport.reset()
        self._zoom_label.config(text="100%")
        self.render_scene()

    def _update_viewport(self) -> None:
        """Update all canvas objects to reflect viewport changes.

        Optimized implementation that transforms existing canvas items
        instead of redrawing everything.
        """
        # Get all canvas items
        all_items = self._canvas.find_all()

        if not all_items:
            # No items to transform, nothing to do
            return

        # Calculate pan delta
        dx, dy, zoom_ratio = self._last_viewport.get_delta(self._viewport)

        # Calculate zoom ratio
        zoom_ratio = self.viewport.zoom / self.last_viewport.zoom if self.last_viewport.zoom != 0 else 1.0

        # Apply transformations to all canvas items
        if zoom_ratio != 1.0:
            # Zooming: scale all items around the viewport origin (0, 0)
            # Note: Canvas scale uses (0,0) as origin, so we scale then adjust position
            for item in all_items:
                self._canvas.scale(item, 0, 0, zoom_ratio, zoom_ratio)

            # After scaling, adjust viewport position for the zoom
            self.last_viewport.x *= zoom_ratio
            self.last_viewport.y *= zoom_ratio
            dx, dy, zoom_ratio = self._last_viewport.get_delta(self._viewport)

        # Apply panning if there's any delta
        if dx != 0 or dy != 0:
            for item in all_items:
                self._canvas.move(item, dx, dy)

        # Update previous state
        self.last_viewport.update(self.viewport)

        # TODO: Implement viewport culling for large scenes

    def set_scene(self, scene: IScene) -> None:
        """Set the scene to be displayed.

        Args:
            scene: Scene object to display
        """
        self._scene = scene
        self._canvas_objects.clear()
        # Reset viewport state when setting new scene
        self.last_viewport.update(self.viewport)
        self.render_scene()

    def get_scene(self) -> Optional[IScene]:
        """Get the currently displayed scene.

        Returns:
            The current scene, or None if no scene is loaded
        """
        return self._scene

    def render_scene(self) -> None:
        """Render the current scene to the canvas."""
        if not self._scene:
            return

        self.clear_canvas()
        self._viewport_gridding_service.render()
        # self.render_grid()
        self.render_scene_objects()

        # Update property panel values (if visible) without rebuilding widgets
        if self._properties_panel_visible and self._properties_panel:
            self.properties_panel.update_values()

        # Initialize previous state to current after initial render
        self.last_viewport.update(self.viewport)

        # TODO: Add rendering order/layering support
        # TODO: Add scene background rendering

    def render_scene_objects(self) -> None:
        """Render all scene objects to the canvas."""
        if not self._scene:
            return

        for obj_id, scene_obj in self._scene.scene_objects.items():
            self._render_scene_object(obj_id, scene_obj)

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
        # Get properties with defaults
        props = scene_obj.properties
        color = props.get("color", "#4a9eff")
        shape = props.get("shape", "rectangle")

        # Apply viewport transformation
        canvas_x = scene_obj.x * self.viewport.zoom + self.viewport.x
        canvas_y = scene_obj.y * self.viewport.zoom + self.viewport.y
        canvas_width = scene_obj.width * self.viewport.zoom
        canvas_height = scene_obj.height * self.viewport.zoom

        # Render based on shape type
        canvas_id = None
        is_selected = obj_id in self._selected_objects
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
            self._canvas_objects[obj_id] = canvas_id

            # Draw name label
            _ = self._canvas.create_text(
                canvas_x + canvas_width / 2,
                canvas_y - 10 * self.viewport.zoom,
                text=scene_obj.name,
                fill="white",
                font=("Arial", max(8, int(10 * self.viewport.zoom))),
                tags=("scene_object_label", obj_id)
            )

    def toggle_grid(self) -> None:
        """Toggle grid visibility."""
        self._viewport_gridding_service.toggle()
        self.render_scene()

    def set_grid_size(self, size: int) -> None:
        """Set the grid spacing size.

        Args:
            size: Grid spacing in scene units
        """
        if size <= 0:
            log(self).warning(f"Invalid grid size: {size}. Must be positive.")
            return

        self._grid_size = size
        if self.render_scene:
            self.render_scene()

    def select_object(self, obj_id: str, clear_previous: bool = False) -> None:
        """Select a scene object.

        Args:
            obj_id: ID of the object to select
            clear_previous: Whether to clear previous selection
        """
        if clear_previous:
            self._selected_objects.clear()

        if obj_id not in self._canvas_objects:
            log(self).warning(f"Cannot select object {obj_id}: not found")
            return

        self._selected_objects.add(obj_id)
        self._update_selection_display()
        self._update_object_appearance(obj_id)

    def deselect_object(self, obj_id: str) -> None:
        """Deselect a scene object.

        Args:
            obj_id: ID of the object to deselect
        """
        if obj_id in self._selected_objects:
            self._selected_objects.discard(obj_id)
            self._update_selection_display()
            self._update_object_appearance(obj_id)

    def toggle_selection(self, obj_id: str) -> None:
        """Toggle selection state of a scene object.

        Args:
            obj_id: ID of the object to toggle
        """
        if obj_id in self._selected_objects:
            self.deselect_object(obj_id)
        else:
            self.select_object(obj_id, clear_previous=False)

    def clear_selection(self) -> None:
        """Clear all selected objects."""
        selected = list(self._selected_objects)
        self._selected_objects.clear()
        self._update_selection_display()

        # Update appearance of previously selected objects
        for obj_id in selected:
            self._update_object_appearance(obj_id)

    def get_selected_objects(self) -> list[str]:
        """Get list of currently selected object IDs.

        Returns:
            List of selected object IDs
        """
        return list(self._selected_objects)

    def _update_selection_display(self) -> None:
        """Update the selection info display in toolbar."""
        count = len(self._selected_objects)
        if count == 0:
            self._selection_label.config(text="No selection")
        elif count == 1:
            obj_id = list(self._selected_objects)[0]
            self._selection_label.config(text=f"Selected: {obj_id}")
        else:
            self._selection_label.config(text=f"Selected: {count} objects")

        # Update properties panel if visible
        if self._properties_panel_visible:
            self._update_properties_panel()

    def _update_object_appearance(self, obj_id: str) -> None:
        """Update visual appearance of an object based on selection state.

        Args:
            obj_id: ID of the object to update
        """
        if obj_id not in self._canvas_objects:
            return

        canvas_id = self._canvas_objects[obj_id]
        is_selected = obj_id in self._selected_objects

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

        # Remove from canvas
        if obj_id in self._canvas_objects:
            canvas_id = self._canvas_objects[obj_id]
            self._canvas.delete(canvas_id)
            del self._canvas_objects[obj_id]

        # Remove from scene
        self._scene.remove_scene_object(obj_id)

    def clear_canvas(self) -> None:
        """Clear all items from the canvas without affecting the scene."""
        self._canvas.delete("all")
        self._canvas_objects.clear()

    def clear_scene(self) -> None:
        """Clear all scene objects from the viewer."""
        self.clear_canvas()
        if self._scene:
            self._scene.set_scene_objects({})

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

    # Properties

    @property
    def canvas(self) -> tk.Canvas:
        """Get the main canvas widget."""
        return self._canvas

    @property
    def properties_panel(self) -> TkPropertyPanel:
        """Get the properties panel."""
        if not self._properties_panel:
            raise RuntimeError("Properties panel not initialized")
        return self._properties_panel

    @property
    def scene(self) -> Optional[IScene]:
        """Get the current scene."""
        return self._scene

    @property
    def viewport(self) -> SceneViewerViewPort:
        """Get the current viewport state."""
        return self._viewport

    @property
    def last_viewport(self) -> SceneViewerViewPort:
        """Get the last viewport state."""
        return self._last_viewport

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

    def _initialize_object_templates(self) -> None:
        """Initialize object templates and populate palette."""
        # Define object templates
        self._object_templates = {
            "Static Collider": {
                "scene_object_type": "PhysicsSceneObject",
                "name": "Static Collider",
                "description": "Static collision object",
                "properties": {
                    "shape": "rectangle",
                    "fill": "gray",
                    "outline": "black",
                    "body_type": "static",
                    "collider_type": "rectangle"
                },
                "width": 100.0,
                "height": 20.0
            },
            "Conveyor Belt": {
                "scene_object_type": "PhysicsSceneObject",
                "name": "Conveyor",
                "description": "Conveyor belt with surface velocity",
                "properties": {
                    "shape": "rectangle",
                    "fill": "#4a90e2",
                    "outline": "#2c5aa0",
                    "body_type": "static",
                    "collider_type": "rectangle",
                    "is_conveyor": True,
                    "surface_velocity": 50.0
                },
                "width": 200.0,
                "height": 30.0
            },
            "Wall": {
                "scene_object_type": "PhysicsSceneObject",
                "name": "Wall",
                "description": "Static wall",
                "properties": {
                    "shape": "rectangle",
                    "fill": "#8b4513",
                    "outline": "#654321",
                    "body_type": "static",
                    "collider_type": "rectangle"
                },
                "width": 20.0,
                "height": 200.0
            },
            "Dynamic Box": {
                "scene_object_type": "PhysicsSceneObject",
                "name": "Box",
                "description": "Dynamic physics box",
                "properties": {
                    "shape": "rectangle",
                    "fill": "#ff6b6b",
                    "outline": "#c92a2a",
                    "body_type": "dynamic",
                    "collider_type": "rectangle",
                    "mass": 1.0
                },
                "width": 50.0,
                "height": 50.0
            },
            "Actor/Sprite": {
                "scene_object_type": "SceneObject",
                "name": "Actor",
                "description": "Sprite or actor object",
                "properties": {
                    "shape": "circle",
                    "fill": "#51cf66",
                    "outline": "#2f9e44",
                    "actor_type": "player"
                },
                "width": 40.0,
                "height": 40.0
            },
            "Spawner": {
                "scene_object_type": "SceneObject",
                "name": "Spawner",
                "description": "Object spawner",
                "properties": {
                    "shape": "circle",
                    "fill": "#ffd43b",
                    "outline": "#fab005",
                    "spawn_rate": 2.0,
                    "spawn_object_type": "Box",
                    "spawner": True
                },
                "width": 30.0,
                "height": 30.0
            },
            "Trigger Zone": {
                "scene_object_type": "PhysicsSceneObject",
                "name": "Trigger",
                "description": "Trigger zone for events",
                "properties": {
                    "shape": "rectangle",
                    "fill": "",
                    "outline": "#e599f7",
                    "body_type": "static",
                    "collider_type": "rectangle",
                    "is_trigger": True
                },
                "width": 100.0,
                "height": 100.0
            }
        }

        # Populate palette with buttons
        for template_name in self._object_templates.keys():
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

        template = self._object_templates.get(self._current_object_template)
        if not template:
            return

        # Apply snap to grid if enabled
        if self._snap_to_grid:
            scene_x = round(scene_x / self._grid_size) * self._grid_size
            scene_y = round(scene_y / self._grid_size) * self._grid_size

        # Generate unique ID
        self._object_counter += 1
        obj_id = f"{template['name'].lower().replace(' ', '_')}_{self._object_counter:03d}"

        # Create object from template
        from pyrox.models.scene import SceneObject, PhysicsSceneObject

        obj_type = template.get("scene_object_type", "SceneObject")
        properties = template.get("properties", {}).copy()

        if obj_type == "PhysicsSceneObject":
            scene_obj = PhysicsSceneObject(
                id=obj_id,
                name=template["name"],
                scene_object_type=obj_type,
                description=template.get("description", ""),
                properties=properties,
                x=scene_x,
                y=scene_y,
                width=template.get("width", 50.0),
                height=template.get("height", 50.0)
            )
        else:
            scene_obj = SceneObject(
                id=obj_id,
                name=template["name"],
                scene_object_type=obj_type,
                description=template.get("description", ""),
                properties=properties,
                x=scene_x,
                y=scene_y,
                width=template.get("width", 50.0),
                height=template.get("height", 50.0)
            )

        # Add to scene
        self._scene.add_scene_object(scene_obj)

        # Redraw
        self.render_scene()

        # Select the new object
        self.clear_selection()
        self._selected_objects.add(obj_id)
        self._update_selection_display()
        self._update_properties_panel()

        log(self).info(f"Placed {template['name']} at ({scene_x:.1f}, {scene_y:.1f})")

    def toggle_design_mode(self) -> None:
        """Toggle design mode on/off."""
        self._design_mode = self._design_mode_var.get()

        if self._design_mode:
            # Enable design features
            self._object_palette_toggle.config(state=tk.NORMAL)
            log(self).info("Design mode enabled")
        else:
            # Disable design features
            self._object_palette_toggle.config(state=tk.DISABLED)
            self._object_palette_visible = False
            self._object_palette_var.set(False)
            if self._object_palette_frame:
                self._object_palette_frame.pack_forget()
            self._current_object_template = None
            if self._current_tool == "place_object":
                self._current_tool = "select"
                self._tool_var.set("select")
                self._canvas.config(cursor="")
            log(self).info("Design mode disabled")

    def toggle_object_palette(self) -> None:
        """Toggle the object palette visibility."""
        self._object_palette_visible = self._object_palette_var.get()

        if self._object_palette_visible and self._object_palette_frame:
            self._object_palette_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5, before=self._canvas)
        elif self._object_palette_frame:
            self._object_palette_frame.pack_forget()

    def toggle_snap_to_grid(self) -> None:
        """Toggle snap to grid on/off."""
        self._snap_to_grid = self._snap_var.get()
        log(self).info(f"Snap to grid: {'ON' if self._snap_to_grid else 'OFF'}")

    def save_scene_dialog(self) -> None:
        """Open file dialog to save the current scene."""
        if not self._scene:
            log(self).warning("No scene to save")
            return

        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            title="Save Scene",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filepath:
            try:
                from pathlib import Path
                self._scene.save(Path(filepath))
                log(self).info(f"Scene saved to: {filepath}")
            except Exception as e:
                log(self).error(f"Failed to save scene: {e}")

    def load_scene_dialog(self) -> None:
        """Open file dialog to load a scene."""
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            title="Load Scene",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filepath:
            try:
                from pathlib import Path
                from pyrox.models.scene import Scene, SceneObjectFactory, SceneObject, PhysicsSceneObject

                # Create factory and register object types
                factory = SceneObjectFactory()
                factory.register("SceneObject", SceneObject)
                factory.register("PhysicsSceneObject", PhysicsSceneObject)

                # Load scene
                loaded_scene = Scene.load(Path(filepath), factory=factory)
                self.set_scene(loaded_scene)
                log(self).info(f"Scene loaded from: {filepath}")
            except Exception as e:
                log(self).error(f"Failed to load scene: {e}")

    def toggle_properties_panel(self) -> None:
        """Toggle the visibility of the properties panel."""
        self._properties_panel_visible = self._properties_var.get()
        panes = list(self._paned_window.panes())

        if self._properties_panel_visible:
            # Show properties panel in the paned window
            # Check if it's already added to avoid errors
            if str(self.properties_panel) not in panes:
                self.properties_panel.master = self._paned_window
                self._paned_window.add(self.properties_panel, weight=0)
            self._update_properties_panel()
        else:
            # Hide properties panel by removing from paned window
            if str(self.properties_panel) in panes:
                self.properties_panel.pack_forget()
                self._paned_window.remove(self.properties_panel)

    def _update_properties_panel(self) -> None:
        """Update the properties panel with selected object information."""
        if not self._properties_panel:
            return

        if not self._selected_objects:
            # No selection
            self._properties_panel.set_object(None)
            return

        if len(self._selected_objects) > 1:
            # Multiple selection - show count
            self._properties_panel.set_title(f"Properties ({len(self._selected_objects)} selected)")
            self._properties_panel.set_object(None)
            return

        # Single object selected
        if not self._scene:
            return

        obj_id = next(iter(self._selected_objects))
        scene_obj = self._scene.get_scene_object(obj_id)

        if not scene_obj:
            return

        # Set title with object ID
        self._properties_panel.set_title(f"Properties: {obj_id}")

        # Define which properties should be read-only
        # For now, make specific properties editable based on your needs
        readonly_props = {"id", "type"}  # ID and type are typically read-only

        # Set the object to display
        self._properties_panel.set_object(scene_obj, readonly_properties=readonly_props)

    def _on_property_changed(self, property_name: str, new_value) -> None:
        """Handle property changes from the properties panel.

        Args:
            property_name: Name of the property that changed
            new_value: New value for the property
        """
        # Redraw the scene to reflect the property change
        self.render_scene()
        log(self).info(f"Property '{property_name}' changed to: {new_value}")


__all__ = ['SceneViewerFrame']

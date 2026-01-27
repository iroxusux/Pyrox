"""2D Scene Viewer Frame for Pyrox.

This module provides a Tkinter-based canvas frame for viewing and interacting
with 2D scenes containing sprites and simple shapes. Supports panning, zooming,
and integrates with the Scene workflow.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, Tuple, TYPE_CHECKING
from pyrox.models.gui.tk.frame import TkinterTaskFrame
from pyrox.services import log

if TYPE_CHECKING:
    from pyrox.interfaces import IScene, ISceneObject


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
        self._viewport_x: float = 0.0
        self._viewport_y: float = 0.0
        self._zoom_level: float = 1.0
        self._min_zoom: float = 0.1
        self._max_zoom: float = 10.0

        # Mouse interaction state
        self._pan_start_x: Optional[int] = None
        self._pan_start_y: Optional[int] = None
        self._is_panning: bool = False

        # Build the UI
        self._build_toolbar()
        self._build_canvas()
        self._bind_events()

        # Initial render if scene provided
        if self._scene:
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
            command=self.zoom_in
        )
        self._zoom_in_btn.pack(side=tk.LEFT, padx=2)

        self._zoom_out_btn = ttk.Button(
            self._toolbar,
            text="-",
            width=3,
            command=self.zoom_out
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
            text=f"{int(self._zoom_level * 100)}%"
        )
        self._zoom_label.pack(side=tk.LEFT, padx=5)

        # TODO: Add toolbar buttons for:
        # - Grid toggle
        # - Snap to grid
        # - Selection mode
        # - Drawing tools
        # - Scene object properties panel toggle

    def _build_canvas(self) -> None:
        """Build the main canvas for rendering."""
        # Canvas container with scrollbars
        canvas_frame = ttk.Frame(self.content_frame)
        canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Create canvas
        self._canvas = tk.Canvas(
            canvas_frame,
            bg="#2b2b2b",
            highlightthickness=0
        )
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # TODO: Add scrollbars for large scenes
        # TODO: Add grid overlay option
        # TODO: Add ruler/coordinate display

    def _bind_events(self) -> None:
        """Bind mouse and keyboard events for interaction."""
        # Pan with middle mouse button
        self._canvas.bind("<ButtonPress-2>", self._on_pan_start)
        self._canvas.bind("<B2-Motion>", self._on_pan_drag)
        self._canvas.bind("<ButtonRelease-2>", self._on_pan_end)

        # Zoom with mouse wheel
        self._canvas.bind("<MouseWheel>", self._on_mouse_wheel)

        # TODO: Add keyboard shortcuts
        # TODO: Add selection events (click, drag)
        # TODO: Add context menu on right-click

    def _on_pan_start(self, event: tk.Event) -> None:
        """Handle pan gesture start."""
        self._is_panning = True
        self._pan_start_x = event.x
        self._pan_start_y = event.y
        self._canvas.config(cursor="fleur")

    def _on_pan_drag(self, event: tk.Event) -> None:
        """Handle pan gesture dragging."""
        if not self._is_panning or self._pan_start_x is None or self._pan_start_y is None:
            return

        dx = event.x - self._pan_start_x
        dy = event.y - self._pan_start_y

        self._viewport_x += dx
        self._viewport_y += dy

        self._pan_start_x = event.x
        self._pan_start_y = event.y

        self._update_viewport()

    def _on_pan_end(self, event: tk.Event) -> None:
        """Handle pan gesture end."""
        self._is_panning = False
        self._pan_start_x = None
        self._pan_start_y = None
        self._canvas.config(cursor="")

    def _on_mouse_wheel(self, event: tk.Event) -> None:
        """Handle mouse wheel for zooming."""
        # Get mouse position for zoom center
        mouse_x = event.x
        mouse_y = event.y

        # Determine zoom direction
        if event.delta > 0:
            self.zoom_in(center_x=mouse_x, center_y=mouse_y)
        else:
            self.zoom_out(center_x=mouse_x, center_y=mouse_y)

    def zoom_in(
        self,
        factor: float = 1.2,
        center_x: Optional[int] = None,
        center_y: Optional[int] = None
    ) -> None:
        """Zoom in on the canvas.

        Args:
            factor: Zoom multiplication factor
            center_x: X coordinate to zoom toward (canvas coordinates)
            center_y: Y coordinate to zoom toward (canvas coordinates)
        """
        new_zoom = min(self._zoom_level * factor, self._max_zoom)
        self._apply_zoom(new_zoom, center_x, center_y)

    def zoom_out(
        self,
        factor: float = 1.2,
        center_x: Optional[int] = None,
        center_y: Optional[int] = None
    ) -> None:
        """Zoom out on the canvas.

        Args:
            factor: Zoom division factor
            center_x: X coordinate to zoom from (canvas coordinates)
            center_y: Y coordinate to zoom from (canvas coordinates)
        """
        new_zoom = max(self._zoom_level / factor, self._min_zoom)
        self._apply_zoom(new_zoom, center_x, center_y)

    def _apply_zoom(
        self,
        new_zoom: float,
        center_x: Optional[int] = None,
        center_y: Optional[int] = None
    ) -> None:
        """Apply zoom level change.

        Args:
            new_zoom: New zoom level
            center_x: X coordinate for zoom center
            center_y: Y coordinate for zoom center
        """
        if new_zoom == self._zoom_level:
            return

        # If no center specified, use canvas center
        if center_x is None or center_y is None:
            center_x = self._canvas.winfo_width() // 2
            center_y = self._canvas.winfo_height() // 2

        # Adjust viewport to zoom toward the center point
        zoom_ratio = new_zoom / self._zoom_level
        self._viewport_x = center_x - (center_x - self._viewport_x) * zoom_ratio
        self._viewport_y = center_y - (center_y - self._viewport_y) * zoom_ratio

        self._zoom_level = new_zoom
        self._zoom_label.config(text=f"{int(self._zoom_level * 100)}%")

        self._update_viewport()

    def reset_view(self) -> None:
        """Reset viewport to default position and zoom."""
        self._viewport_x = 0.0
        self._viewport_y = 0.0
        self._zoom_level = 1.0
        self._zoom_label.config(text="100%")
        self._update_viewport()

    def _update_viewport(self) -> None:
        """Update all canvas objects to reflect viewport changes."""
        # Move all canvas items based on viewport
        self._canvas.delete("all")  # Simple approach: redraw everything
        self.render_scene()

        # TODO: Optimize by transforming existing canvas items instead of redrawing
        # TODO: Implement viewport culling for large scenes

    def set_scene(self, scene: IScene) -> None:
        """Set the scene to be displayed.

        Args:
            scene: Scene object to display
        """
        self._scene = scene
        self._canvas_objects.clear()
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

        self._canvas.delete("all")
        self._canvas_objects.clear()

        # Render each scene object
        for obj_id, scene_obj in self._scene.scene_objects.items():
            self._render_scene_object(obj_id, scene_obj)

        # TODO: Add rendering order/layering support
        # TODO: Add scene background rendering

    def _render_scene_object(self, obj_id: str, scene_obj: ISceneObject) -> None:
        """Render a single scene object to the canvas.

        Args:
            obj_id: Unique identifier for the scene object
            scene_obj: The scene object to render
        """
        # Get properties with defaults
        props = scene_obj.properties
        x = props.get("x", 0)
        y = props.get("y", 0)
        width = props.get("width", 50)
        height = props.get("height", 50)
        color = props.get("color", "#4a9eff")
        shape = props.get("shape", "rectangle")

        # Apply viewport transformation
        canvas_x = x * self._zoom_level + self._viewport_x
        canvas_y = y * self._zoom_level + self._viewport_y
        canvas_width = width * self._zoom_level
        canvas_height = height * self._zoom_level

        # Render based on shape type
        canvas_id = None
        if shape == "rectangle":
            canvas_id = self._canvas.create_rectangle(
                canvas_x,
                canvas_y,
                canvas_x + canvas_width,
                canvas_y + canvas_height,
                fill=color,
                outline="white",
                width=2
            )
        elif shape == "circle" or shape == "oval":
            canvas_id = self._canvas.create_oval(
                canvas_x,
                canvas_y,
                canvas_x + canvas_width,
                canvas_y + canvas_height,
                fill=color,
                outline="white",
                width=2
            )
        elif shape == "line":
            x2 = props.get("x2", x + width)
            y2 = props.get("y2", y + height)
            canvas_x2 = x2 * self._zoom_level + self._viewport_x
            canvas_y2 = y2 * self._zoom_level + self._viewport_y
            canvas_id = self._canvas.create_line(
                canvas_x,
                canvas_y,
                canvas_x2,
                canvas_y2,
                fill=color,
                width=max(2, int(2 * self._zoom_level))
            )
        # TODO: Add support for more shapes (polygon, text, image/sprite)

        # Add label for the object
        if canvas_id:
            self._canvas_objects[obj_id] = canvas_id

            # Draw name label
            _ = self._canvas.create_text(
                canvas_x + canvas_width / 2,
                canvas_y - 10 * self._zoom_level,
                text=scene_obj.name,
                fill="white",
                font=("Arial", max(8, int(10 * self._zoom_level)))
            )
            # TODO: Associate label with parent object for selection

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

    def clear_scene(self) -> None:
        """Clear all scene objects from the viewer."""
        self._canvas.delete("all")
        self._canvas_objects.clear()
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
        canvas_x = world_x * self._zoom_level + self._viewport_x
        canvas_y = world_y * self._zoom_level + self._viewport_y
        return (canvas_x, canvas_y)

    def canvas_to_world(self, canvas_x: float, canvas_y: float) -> Tuple[float, float]:
        """Convert canvas coordinates to world coordinates.

        Args:
            canvas_x: X coordinate on canvas
            canvas_y: Y coordinate on canvas

        Returns:
            Tuple of (world_x, world_y)
        """
        world_x = (canvas_x - self._viewport_x) / self._zoom_level
        world_y = (canvas_y - self._viewport_y) / self._zoom_level
        return (world_x, world_y)

    # Properties

    @property
    def canvas(self) -> tk.Canvas:
        """Get the main canvas widget."""
        return self._canvas

    @property
    def scene(self) -> Optional[IScene]:
        """Get the current scene."""
        return self._scene

    @property
    def viewport_x(self) -> float:
        """Get the viewport X offset."""
        return self._viewport_x

    @property
    def viewport_y(self) -> float:
        """Get the viewport Y offset."""
        return self._viewport_y

    @property
    def zoom_level(self) -> float:
        """Get the current zoom level."""
        return self._zoom_level


__all__ = ['SceneViewerFrame']

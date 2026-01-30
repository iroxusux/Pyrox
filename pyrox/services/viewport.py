"""Viewport panning service module.
"""
from typing import Callable, Optional
import tkinter as tk
from pyrox.interfaces import IViewport


class ViewportPanningService:
    """Service for handling panning operations in a viewport."""

    def __init__(
        self,
        canvas: Optional[tk.Canvas] = None,
        viewport: Optional[IViewport] = None
    ):
        self._canvas = canvas
        self._viewport = viewport
        self._is_panning = False
        self._start_x = 0
        self._start_y = 0
        self._on_pan_callbacks: list[Callable] = []

    def _bind_to_canvas(self):
        if not self.canvas:
            return

        self.canvas.bind("<ButtonPress-2>", self._start_pan)
        self.canvas.bind("<B2-Motion>", self._do_pan)
        self.canvas.bind("<ButtonRelease-2>", self._end_pan)

    def _start_pan(self, event):
        self._is_panning = True
        self._start_x = event.x
        self._start_y = event.y
        self.canvas.config(cursor="fleur")

    def _do_pan(self, event):
        if self._is_panning:
            dx = event.x - self._start_x
            dy = event.y - self._start_y

            self.viewport.x += dx
            self.viewport.y += dy

            for callback in self._on_pan_callbacks:
                callback()

            self._start_x = event.x
            self._start_y = event.y

    def _end_pan(self, event):
        self._is_panning = False
        self.canvas.config(cursor="")

    def get_canvas(self) -> tk.Canvas:
        """Get the canvas associated with this service."""
        if not self._canvas:
            raise ValueError("Canvas is not set for ViewportPanningService.")
        return self._canvas

    def set_canvas(self, canvas: tk.Canvas) -> None:
        """Set the canvas associated with this service."""
        self._canvas = canvas
        self._bind_to_canvas()

    def get_viewport(self) -> IViewport:
        """Get the viewport associated with this service."""
        if not self._viewport:
            raise ValueError("Viewport is not set for ViewportPanningService.")
        return self._viewport

    def set_viewport(self, viewport: IViewport) -> None:
        """Set the viewport associated with this service."""
        self._viewport = viewport

    def get_on_pan_callbacks(self) -> list[Callable]:
        """Get the list of callbacks to be called on panning events."""
        return self._on_pan_callbacks

    @property
    def canvas(self) -> tk.Canvas:
        """Get the canvas associated with this service."""
        if not self._canvas:
            raise ValueError("Canvas is not set for ViewportPanningService.")
        return self._canvas

    @property
    def viewport(self) -> IViewport:
        """Get the viewport associated with this service."""
        if not self._viewport:
            raise ValueError("Viewport is not set for ViewportPanningService.")
        return self._viewport

    @property
    def on_pan_callbacks(self) -> list[Callable]:
        """Get the list of callbacks to be called on panning events."""
        return self._on_pan_callbacks


class ViewportZoomingService:
    """Service for handling zoom operations in a viewport."""

    def __init__(
        self,
        canvas: Optional[tk.Canvas] = None,
        viewport: Optional[IViewport] = None,
        zoom_factor: float = 1.2,
        min_zoom: float = 0.1,
        max_zoom: float = 10.0
    ):
        """Initialize the zooming service.

        Args:
            canvas: Canvas to bind zoom events to
            viewport: Viewport to modify zoom on
            zoom_factor: Multiplier for zoom in/out operations (default: 1.2)
            min_zoom: Minimum allowed zoom level (default: 0.1)
            max_zoom: Maximum allowed zoom level (default: 10.0)
        """
        self._canvas = canvas
        self._viewport = viewport
        self._zoom_factor = zoom_factor
        self._min_zoom = min_zoom
        self._max_zoom = max_zoom
        self._on_zoom_callbacks: list[Callable] = []

    def _bind_to_canvas(self):
        """Bind mouse wheel event to canvas for zooming."""
        if not self.canvas:
            return

        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)

    def _on_mouse_wheel(self, event):
        """Handle mouse wheel events for zooming.

        Args:
            event: Mouse wheel event with delta property
        """
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
        center_x: Optional[float] = None,
        center_y: Optional[float] = None,
        factor: Optional[float] = None
    ) -> None:
        """Zoom in, optionally centered on a specific point.

        Args:
            center_x: X coordinate to zoom towards (canvas coordinates)
            center_y: Y coordinate to zoom towards (canvas coordinates)
            factor: Custom zoom factor (default: use service zoom_factor)
        """
        if factor is None:
            factor = self._zoom_factor

        old_zoom = self.viewport.zoom
        new_zoom = min(old_zoom * factor, self._max_zoom)

        if new_zoom == old_zoom:
            return  # Already at max zoom

        self._apply_zoom(old_zoom, new_zoom, center_x, center_y)

    def zoom_out(
        self,
        center_x: Optional[float] = None,
        center_y: Optional[float] = None,
        factor: Optional[float] = None
    ) -> None:
        """Zoom out, optionally centered on a specific point.

        Args:
            center_x: X coordinate to zoom from (canvas coordinates)
            center_y: Y coordinate to zoom from (canvas coordinates)
            factor: Custom zoom factor (default: use service zoom_factor)
        """
        if factor is None:
            factor = self._zoom_factor

        old_zoom = self.viewport.zoom
        new_zoom = max(old_zoom / factor, self._min_zoom)

        if new_zoom == old_zoom:
            return  # Already at min zoom

        self._apply_zoom(old_zoom, new_zoom, center_x, center_y)

    def _apply_zoom(
        self,
        old_zoom: float,
        new_zoom: float,
        center_x: Optional[float] = None,
        center_y: Optional[float] = None
    ) -> None:
        """Apply zoom transformation with optional center point.

        When zooming with a center point, adjusts viewport position
        so the point under the mouse stays stationary.

        Args:
            old_zoom: Previous zoom level
            new_zoom: New zoom level to apply
            center_x: X coordinate of zoom center (canvas coordinates)
            center_y: Y coordinate of zoom center (canvas coordinates)
        """
        # If center point provided, adjust viewport to keep that point stationary
        if center_x is not None and center_y is not None:
            # Convert canvas point to scene coordinates before zoom
            scene_x = (center_x - self.viewport.x) / old_zoom
            scene_y = (center_y - self.viewport.y) / old_zoom

            # Update zoom
            self.viewport.zoom = new_zoom

            # Recalculate viewport position to keep scene point under mouse
            self.viewport.x = center_x - (scene_x * new_zoom)
            self.viewport.y = center_y - (scene_y * new_zoom)
        else:
            # Simple zoom without center point
            self.viewport.zoom = new_zoom

        # Notify listeners
        for callback in self._on_zoom_callbacks:
            callback()

    def reset_zoom(self) -> None:
        """Reset zoom to 1.0 (100%)."""
        old_zoom = self.viewport.zoom
        if old_zoom != 1.0:
            self.viewport.zoom = 1.0
            for callback in self._on_zoom_callbacks:
                callback()

    def set_zoom(self, zoom: float) -> None:
        """Set zoom to specific value.

        Args:
            zoom: Zoom level to set (will be clamped to min/max)
        """
        old_zoom = self.viewport.zoom
        new_zoom = max(self._min_zoom, min(zoom, self._max_zoom))

        if new_zoom != old_zoom:
            self.viewport.zoom = new_zoom
            for callback in self._on_zoom_callbacks:
                callback()

    # Getters and Setters

    def get_canvas(self) -> tk.Canvas:
        """Get the canvas associated with this service."""
        if not self._canvas:
            raise ValueError("Canvas is not set for CanvasZoomingService.")
        return self._canvas

    def set_canvas(self, canvas: tk.Canvas) -> None:
        """Set the canvas associated with this service."""
        self._canvas = canvas
        self._bind_to_canvas()

    def get_viewport(self) -> IViewport:
        """Get the viewport associated with this service."""
        if not self._viewport:
            raise ValueError("Viewport is not set for CanvasZoomingService.")
        return self._viewport

    def set_viewport(self, viewport: IViewport) -> None:
        """Set the viewport associated with this service."""
        self._viewport = viewport

    def get_zoom_factor(self) -> float:
        """Get the zoom factor multiplier."""
        return self._zoom_factor

    def set_zoom_factor(self, factor: float) -> None:
        """Set the zoom factor multiplier."""
        if factor <= 1.0:
            raise ValueError("Zoom factor must be greater than 1.0")
        self._zoom_factor = factor

    def get_zoom_limits(self) -> tuple[float, float]:
        """Get the min and max zoom limits.

        Returns:
            Tuple of (min_zoom, max_zoom)
        """
        return (self._min_zoom, self._max_zoom)

    def set_zoom_limits(self, min_zoom: float, max_zoom: float) -> None:
        """Set the min and max zoom limits.

        Args:
            min_zoom: Minimum zoom level
            max_zoom: Maximum zoom level

        Raises:
            ValueError: If min_zoom >= max_zoom or values are invalid
        """
        if min_zoom <= 0:
            raise ValueError("min_zoom must be greater than 0")
        if min_zoom >= max_zoom:
            raise ValueError("min_zoom must be less than max_zoom")

        self._min_zoom = min_zoom
        self._max_zoom = max_zoom

    def get_on_zoom_callbacks(self) -> list[Callable]:
        """Get the list of callbacks to be called on zoom events."""
        return self._on_zoom_callbacks

    # Properties

    @property
    def canvas(self) -> tk.Canvas:
        """Get the canvas associated with this service."""
        if not self._canvas:
            raise ValueError("Canvas is not set for CanvasZoomingService.")
        return self._canvas

    @property
    def viewport(self) -> IViewport:
        """Get the viewport associated with this service."""
        if not self._viewport:
            raise ValueError("Viewport is not set for CanvasZoomingService.")
        return self._viewport

    @property
    def zoom_factor(self) -> float:
        """Get the zoom factor multiplier."""
        return self._zoom_factor

    @property
    def min_zoom(self) -> float:
        """Get the minimum zoom limit."""
        return self._min_zoom

    @property
    def max_zoom(self) -> float:
        """Get the maximum zoom limit."""
        return self._max_zoom

    @property
    def on_zoom_callbacks(self) -> list[Callable]:
        """Get the list of callbacks to be called on zoom events."""
        return self._on_zoom_callbacks


class ViewportGriddingService:
    """Service for rendering grid overlay on a canvas with viewport support."""

    def __init__(
        self,
        canvas: Optional[tk.Canvas] = None,
        viewport: Optional[IViewport] = None,
        grid_size: int = 50,
        grid_color: str = "#505050",
        grid_line_width: int = 1,
        enabled: bool = True,
        min_spacing_pixels: int = 5
    ):
        """Initialize the gridding service.

        Args:
            canvas: Canvas to render grid on
            viewport: Viewport for coordinate transformation
            grid_size: Grid spacing in scene units (default: 50)
            grid_color: Color of grid lines (default: "#505050")
            grid_line_width: Width of grid lines in pixels (default: 1)
            enabled: Whether grid is initially enabled (default: True)
            min_spacing_pixels: Minimum pixel spacing before hiding grid (default: 5)
        """
        self._canvas = canvas
        self._viewport = viewport
        self._grid_size = grid_size
        self._grid_color = grid_color
        self._grid_line_width = grid_line_width
        self._enabled = enabled
        self._min_spacing_pixels = min_spacing_pixels
        self._on_toggle_callbacks: list[Callable] = []

    def render(self) -> None:
        """Render the grid if enabled."""
        if self._enabled:
            self._render_grid()

    def _render_grid(self) -> None:
        """Internal method to render grid overlay on the canvas."""
        if not self._canvas or not self._viewport:
            return

        canvas_width = self._canvas.winfo_width()
        canvas_height = self._canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not yet rendered or minimized
            return

        # Calculate grid spacing in canvas coordinates
        grid_spacing = self._grid_size * self._viewport.zoom

        # Don't render grid if it's too dense
        if grid_spacing < self._min_spacing_pixels:
            return

        # Calculate starting positions based on viewport offset
        # We want the grid to align with scene coordinates (0,0)
        start_x = self._viewport.x % grid_spacing
        start_y = self._viewport.y % grid_spacing

        # Draw vertical lines
        x = start_x
        while x < canvas_width:
            self._canvas.create_line(
                x, 0, x, canvas_height,
                fill=self._grid_color,
                width=self._grid_line_width,
                tags="grid"
            )
            x += grid_spacing

        # Draw horizontal lines
        y = start_y
        while y < canvas_height:
            self._canvas.create_line(
                0, y, canvas_width, y,
                fill=self._grid_color,
                width=self._grid_line_width,
                tags="grid"
            )
            y += grid_spacing

        # Lower grid to background
        self._canvas.tag_lower("grid")

    def clear(self) -> None:
        """Clear all grid lines from the canvas."""
        if self._canvas:
            self._canvas.delete("grid")

    def toggle(self) -> None:
        """Toggle grid visibility."""
        self._enabled = not self._enabled

        # Notify listeners
        for callback in self._on_toggle_callbacks:
            callback(self._enabled)

    def enable(self) -> None:
        """Enable grid rendering."""
        if not self._enabled:
            self._enabled = True
            for callback in self._on_toggle_callbacks:
                callback(True)

    def disable(self) -> None:
        """Disable grid rendering."""
        if self._enabled:
            self._enabled = False
            for callback in self._on_toggle_callbacks:
                callback(False)

    def snap_to_grid(self, x: float, y: float) -> tuple[float, float]:
        """Snap scene coordinates to nearest grid point.

        Args:
            x: X coordinate in scene space
            y: Y coordinate in scene space

        Returns:
            Tuple of (snapped_x, snapped_y) in scene space
        """
        snapped_x = round(x / self._grid_size) * self._grid_size
        snapped_y = round(y / self._grid_size) * self._grid_size
        return (snapped_x, snapped_y)

    # Getters and Setters

    def get_canvas(self) -> tk.Canvas:
        """Get the canvas associated with this service."""
        if not self._canvas:
            raise ValueError("Canvas is not set for ViewportGriddingService.")
        return self._canvas

    def set_canvas(self, canvas: tk.Canvas) -> None:
        """Set the canvas associated with this service."""
        self._canvas = canvas

    def get_viewport(self) -> IViewport:
        """Get the viewport associated with this service."""
        if not self._viewport:
            raise ValueError("Viewport is not set for ViewportGriddingService.")
        return self._viewport

    def set_viewport(self, viewport: IViewport) -> None:
        """Set the viewport associated with this service."""
        self._viewport = viewport

    def get_grid_size(self) -> int:
        """Get the grid spacing in scene units."""
        return self._grid_size

    def set_grid_size(self, size: int) -> None:
        """Set the grid spacing in scene units.

        Args:
            size: Grid spacing in scene units (must be positive)

        Raises:
            ValueError: If size is not positive
        """
        if size <= 0:
            raise ValueError(f"Grid size must be positive, got {size}")
        self._grid_size = size

    def get_grid_color(self) -> str:
        """Get the grid line color."""
        return self._grid_color

    def set_grid_color(self, color: str) -> None:
        """Set the grid line color.

        Args:
            color: Color string (e.g., "#505050" or "gray")
        """
        self._grid_color = color

    def get_grid_line_width(self) -> int:
        """Get the grid line width in pixels."""
        return self._grid_line_width

    def set_grid_line_width(self, width: int) -> None:
        """Set the grid line width in pixels.

        Args:
            width: Line width (must be positive)

        Raises:
            ValueError: If width is not positive
        """
        if width <= 0:
            raise ValueError(f"Grid line width must be positive, got {width}")
        self._grid_line_width = width

    def is_enabled(self) -> bool:
        """Check if grid rendering is enabled."""
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable grid rendering.

        Args:
            enabled: True to enable, False to disable
        """
        if self._enabled != enabled:
            self._enabled = enabled
            for callback in self._on_toggle_callbacks:
                callback(enabled)

    def get_min_spacing_pixels(self) -> int:
        """Get the minimum pixel spacing before hiding grid."""
        return self._min_spacing_pixels

    def set_min_spacing_pixels(self, pixels: int) -> None:
        """Set the minimum pixel spacing before hiding grid.

        Args:
            pixels: Minimum spacing in pixels (must be positive)

        Raises:
            ValueError: If pixels is not positive
        """
        if pixels <= 0:
            raise ValueError(f"Minimum spacing must be positive, got {pixels}")
        self._min_spacing_pixels = pixels

    def get_on_toggle_callbacks(self) -> list[Callable]:
        """Get the list of callbacks to be called on toggle events."""
        return self._on_toggle_callbacks

    # Properties

    @property
    def canvas(self) -> tk.Canvas:
        """Get the canvas associated with this service."""
        if not self._canvas:
            raise ValueError("Canvas is not set for ViewportGriddingService.")
        return self._canvas

    @property
    def viewport(self) -> IViewport:
        """Get the viewport associated with this service."""
        if not self._viewport:
            raise ValueError("Viewport is not set for ViewportGriddingService.")
        return self._viewport

    @property
    def grid_size(self) -> int:
        """Get the grid spacing in scene units."""
        return self._grid_size

    @property
    def grid_color(self) -> str:
        """Get the grid line color."""
        return self._grid_color

    @property
    def grid_line_width(self) -> int:
        """Get the grid line width in pixels."""
        return self._grid_line_width

    @property
    def enabled(self) -> bool:
        """Check if grid rendering is enabled."""
        return self._enabled

    @property
    def min_spacing_pixels(self) -> int:
        """Get the minimum pixel spacing before hiding grid."""
        return self._min_spacing_pixels

    @property
    def on_toggle_callbacks(self) -> list[Callable]:
        """Get the list of callbacks to be called on toggle events."""
        return self._on_toggle_callbacks

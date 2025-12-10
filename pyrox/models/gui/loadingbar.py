"""
Loading Bar Widget for Pyrox applications.

This module provides a flexible and powerful loading bar widget with multiple
display modes, animations, and comprehensive progress tracking capabilities.
The loading bar follows Pyrox GUI patterns and theming system.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import time
import math

from pyrox.models.gui.frame import PyroxFrameContainer
from pyrox.models.gui.theme import DefaultTheme


class LoadingMode(Enum):
    """Loading bar display modes."""
    DETERMINATE = "determinate"      # Shows specific progress percentage
    INDETERMINATE = "indeterminate"  # Shows activity without specific progress
    PULSE = "pulse"                  # Pulsing animation
    WAVE = "wave"                    # Wave-like animation
    SPINNER = "spinner"              # Circular spinner


class LoadingState(Enum):
    """Loading bar states."""
    IDLE = "idle"
    LOADING = "loading"
    COMPLETED = "completed"
    ERROR = "error"
    PAUSED = "paused"


@dataclass
class LoadingConfig:
    """Configuration for loading bar appearance and behavior.

    Attributes:
        mode (LoadingMode): Display mode for the loading bar.
        show_percentage (bool): Whether to show percentage text.
        show_text (bool): Whether to show custom status text.
        show_time (bool): Whether to show elapsed/remaining time.
        animate (bool): Whether to enable animations.
        animation_speed (float): Animation speed multiplier (1.0 = normal).
        color_scheme (str): Color scheme name ('default', 'success', 'warning', 'error').
        height (int): Height of the progress bar in pixels.
        width (Optional[int]): Width of the progress bar (None for auto).
        border_width (int): Width of the border around the bar.
        show_border (bool): Whether to show a border.
        gradient (bool): Whether to use gradient fill.
        striped (bool): Whether to show diagonal stripes.
        pulse_on_complete (bool): Whether to pulse when completed.
    """
    mode: LoadingMode = LoadingMode.DETERMINATE
    show_percentage: bool = True
    show_text: bool = True
    show_time: bool = False
    animate: bool = True
    animation_speed: float = 1.0
    color_scheme: str = 'default'
    height: int = 24
    width: Optional[int] = None
    border_width: int = 1
    show_border: bool = True
    gradient: bool = True
    striped: bool = False
    pulse_on_complete: bool = True


class PyroxLoadingBar(PyroxFrameContainer):
    """
    A flexible and powerful loading bar widget for progress indication.

    The loading bar supports multiple display modes including determinate progress,
    indeterminate activity indicators, and various animation styles. It provides
    comprehensive progress tracking with optional text display, time estimation,
    and event callbacks for progress updates.

    Features:
    - Multiple display modes (progress, indeterminate, pulse, wave, spinner)
    - Animated progress indicators with customizable speed
    - Progress percentage and custom text display
    - Time tracking (elapsed and estimated remaining time)
    - Multiple color schemes and theming support
    - Event callbacks for progress milestones
    - Thread-safe operations for background tasks
    - Gradient and striped visual effects
    - State management (loading, completed, error, paused)
    """

    def __init__(
        self,
        master=None,
        config: Optional[LoadingConfig] = None,
        **kwargs
    ) -> None:
        """
        Initialize the PyroxLoadingBar.

        Args:
            config: LoadingConfig for appearance and behavior
            **kwargs: Additional arguments passed to PyroxFrame
        """
        kwargs['master'] = master
        super().__init__(**kwargs)

        # Configuration
        self.config = config or LoadingConfig()

        # Progress tracking
        self._progress: float = 0.0  # 0.0 to 100.0
        self._max_progress: float = 100.0
        self._state: LoadingState = LoadingState.IDLE
        self._status_text: str = ""
        self._start_time: Optional[float] = None
        self._pause_time: Optional[float] = None
        self._paused_duration: float = 0.0

        # Animation tracking
        self._animation_thread: Optional[threading.Thread] = None
        self._animation_running: bool = False
        self._animation_offset: float = 0.0
        self._pulse_alpha: float = 0.0
        self._pulse_direction: int = 1

        # Color schemes
        self._color_schemes = {
            'default': {
                'bg': DefaultTheme.widget_background,
                'fg': '#4CAF50',  # Green
                'border': DefaultTheme.bordercolor,
                'text': DefaultTheme.foreground,
                'gradient_start': '#4CAF50',
                'gradient_end': '#45a049'
            },
            'success': {
                'bg': DefaultTheme.widget_background,
                'fg': '#4CAF50',
                'border': '#4CAF50',
                'text': '#4CAF50',
                'gradient_start': '#4CAF50',
                'gradient_end': '#45a049'
            },
            'warning': {
                'bg': DefaultTheme.widget_background,
                'fg': '#FF9800',
                'border': '#FF9800',
                'text': '#FF9800',
                'gradient_start': '#FF9800',
                'gradient_end': '#F57C00'
            },
            'error': {
                'bg': DefaultTheme.widget_background,
                'fg': '#f44336',
                'border': '#f44336',
                'text': '#f44336',
                'gradient_start': '#f44336',
                'gradient_end': '#d32f2f'
            },
            'info': {
                'bg': DefaultTheme.widget_background,
                'fg': '#2196F3',
                'border': '#2196F3',
                'text': '#2196F3',
                'gradient_start': '#2196F3',
                'gradient_end': '#1976D2'
            }
        }

        # Event callbacks
        self.on_progress_changed: Optional[Callable[[float, float], None]] = None
        self.on_state_changed: Optional[Callable[[LoadingState, LoadingState], None]] = None
        self.on_completed: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

        # Widget references
        self._canvas: Optional[tk.Canvas] = None
        self._text_var: Optional[tk.StringVar] = None
        self._percentage_var: Optional[tk.StringVar] = None
        self._time_var: Optional[tk.StringVar] = None

        # Create the UI
        self._create_widgets()
        self._update_display()

    def _create_widgets(self) -> None:
        """Create and layout the loading bar widgets."""
        self.frame_root.grid_columnconfigure(0, weight=1)

        # Main container for the loading bar
        bar_frame = ttk.Frame(self.frame_root)
        bar_frame.grid(row=0, column=0, sticky='ew', padx=2, pady=2)
        bar_frame.grid_columnconfigure(0, weight=1)

        # Progress canvas
        canvas_height = self.config.height
        self._canvas = tk.Canvas(
            bar_frame,
            height=canvas_height,
            bg=self._get_color('bg'),
            highlightthickness=0,
            relief='flat'
        )

        if self.config.width:
            self._canvas.config(width=self.config.width)

        self._canvas.grid(row=0, column=0, sticky='ew', pady=1)

        # Text information frame
        info_frame = ttk.Frame(self.frame_root)
        info_frame.grid(row=1, column=0, sticky='ew', padx=2)
        info_frame.grid_columnconfigure(1, weight=1)

        # Status text
        if self.config.show_text:
            self._text_var = tk.StringVar(value="Ready")
            text_label = tk.Label(
                info_frame,
                textvariable=self._text_var,
                bg=DefaultTheme.background,
                fg=self._get_color('text'),
                font=(DefaultTheme.font_family, DefaultTheme.font_size)
            )
            text_label.grid(row=0, column=0, sticky='w')

        # Percentage display
        if self.config.show_percentage:
            self._percentage_var = tk.StringVar(value="0%")
            percentage_label = tk.Label(
                info_frame,
                textvariable=self._percentage_var,
                bg=DefaultTheme.background,
                fg=self._get_color('text'),
                font=(DefaultTheme.font_family, DefaultTheme.font_size)
            )
            percentage_label.grid(row=0, column=2, sticky='e')

        # Time display
        if self.config.show_time:
            self._time_var = tk.StringVar(value="00:00")
            time_label = tk.Label(
                info_frame,
                textvariable=self._time_var,
                bg=DefaultTheme.background,
                fg=self._get_color('text'),
                font=(DefaultTheme.font_family, DefaultTheme.font_size)
            )
            time_label.grid(row=0, column=3, sticky='e', padx=(10, 0))

        # Bind canvas resize for responsive design
        self._canvas.bind('<Configure>', self._on_canvas_resize)

    def _get_color(self, color_key: str) -> str:
        """Get color from the current color scheme."""
        scheme = self._color_schemes.get(self.config.color_scheme, self._color_schemes['default'])
        return scheme.get(color_key, '#FFFFFF')

    def _on_canvas_resize(self, event) -> None:
        """Handle canvas resize events."""
        self._update_display()

    def _update_display(self) -> None:
        """Update the visual display of the loading bar."""
        if not self._canvas:
            return

        # Clear canvas
        self._canvas.delete("all")

        # Get canvas dimensions
        canvas_width = self._canvas.winfo_width()
        canvas_height = self._canvas.winfo_height()

        if canvas_width <= 1:  # Canvas not yet rendered
            self.frame_root.after(10, self._update_display)
            return

        # Draw border
        if self.config.show_border:
            self._canvas.create_rectangle(
                0, 0, canvas_width, canvas_height,
                outline=self._get_color('border'),
                width=self.config.border_width,
                fill=''
            )

        # Draw progress based on mode
        if self.config.mode == LoadingMode.DETERMINATE:
            self._draw_determinate_progress(canvas_width, canvas_height)
        elif self.config.mode == LoadingMode.INDETERMINATE:
            self._draw_indeterminate_progress(canvas_width, canvas_height)
        elif self.config.mode == LoadingMode.PULSE:
            self._draw_pulse_progress(canvas_width, canvas_height)
        elif self.config.mode == LoadingMode.WAVE:
            self._draw_wave_progress(canvas_width, canvas_height)
        elif self.config.mode == LoadingMode.SPINNER:
            self._draw_spinner_progress(canvas_width, canvas_height)

        # Update text displays
        self._update_text_displays()

    def _draw_determinate_progress(self, width: int, height: int) -> None:
        """Draw determinate progress bar."""
        if not self._canvas:
            raise RuntimeError("Canvas not initialized")

        border_offset = self.config.border_width if self.config.show_border else 0
        inner_width = width - (2 * border_offset)
        inner_height = height - (2 * border_offset)

        if inner_width <= 0 or inner_height <= 0:
            return

        # Calculate progress width
        progress_width = (self._progress / self._max_progress) * inner_width

        if progress_width > 0:
            # Draw background
            self._canvas.create_rectangle(
                border_offset, border_offset,
                border_offset + inner_width, border_offset + inner_height,
                fill=self._get_color('bg'),
                outline=''
            )

            # Draw progress fill
            if self.config.gradient and progress_width > 2:
                self._draw_gradient_rectangle(
                    border_offset, border_offset,
                    int(border_offset + progress_width), border_offset + inner_height
                )
            else:
                fill_color = self._get_color('fg')
                self._canvas.create_rectangle(
                    border_offset, border_offset,
                    border_offset + progress_width, border_offset + inner_height,
                    fill=fill_color,
                    outline=''
                )

            # Draw stripes if enabled
            if self.config.striped:
                self._draw_stripes(border_offset, border_offset, progress_width, inner_height)

    def _draw_indeterminate_progress(self, width: int, height: int) -> None:
        """Draw indeterminate progress animation."""
        if not self._canvas:
            raise RuntimeError("Canvas not initialized")

        border_offset = self.config.border_width if self.config.show_border else 0
        inner_width = width - (2 * border_offset)
        inner_height = height - (2 * border_offset)

        if inner_width <= 0 or inner_height <= 0:
            return

        # Draw background
        self._canvas.create_rectangle(
            border_offset, border_offset,
            border_offset + inner_width, border_offset + inner_height,
            fill=self._get_color('bg'),
            outline=''
        )

        # Animated bar
        bar_width = inner_width * 0.3  # 30% of total width
        x_pos = (self._animation_offset % (inner_width + bar_width)) - bar_width

        if x_pos < inner_width:
            start_x = max(border_offset, border_offset + x_pos)
            end_x = min(border_offset + inner_width, border_offset + x_pos + bar_width)

            if end_x > start_x:
                self._canvas.create_rectangle(
                    start_x, border_offset,
                    end_x, border_offset + inner_height,
                    fill=self._get_color('fg'),
                    outline=''
                )

    def _draw_pulse_progress(self, width: int, height: int) -> None:
        """Draw pulsing progress animation."""
        if not self._canvas:
            raise RuntimeError("Canvas not initialized")

        border_offset = self.config.border_width if self.config.show_border else 0
        inner_width = width - (2 * border_offset)
        inner_height = height - (2 * border_offset)

        if inner_width <= 0 or inner_height <= 0:
            return

        # Calculate alpha for pulsing effect
        alpha = (math.sin(self._pulse_alpha) + 1) / 2  # 0.0 to 1.0

        # Draw background
        self._canvas.create_rectangle(
            border_offset, border_offset,
            border_offset + inner_width, border_offset + inner_height,
            fill=self._get_color('bg'),
            outline=''
        )

        # Draw pulsing overlay
        pulse_color = self._blend_colors(self._get_color('bg'), self._get_color('fg'), alpha)
        self._canvas.create_rectangle(
            border_offset, border_offset,
            border_offset + inner_width, border_offset + inner_height,
            fill=pulse_color,
            outline=''
        )

    def _draw_wave_progress(self, width: int, height: int) -> None:
        """Draw wave-like progress animation."""
        if not self._canvas:
            raise RuntimeError("Canvas not initialized")

        border_offset = self.config.border_width if self.config.show_border else 0
        inner_width = width - (2 * border_offset)
        inner_height = height - (2 * border_offset)

        if inner_width <= 0 or inner_height <= 0:
            return

        # Draw background
        self._canvas.create_rectangle(
            border_offset, border_offset,
            border_offset + inner_width, border_offset + inner_height,
            fill=self._get_color('bg'),
            outline=''
        )

        # Draw wave using sine function
        points = []
        wave_amplitude = inner_height * 0.3
        wave_frequency = 2 * math.pi / inner_width

        for x in range(0, inner_width + 2, 2):
            y = (inner_height / 2) + wave_amplitude * math.sin(wave_frequency * x + self._animation_offset / 20)
            points.extend([border_offset + x, border_offset + y])

        # Complete the polygon
        points.extend([border_offset + inner_width, border_offset + inner_height])
        points.extend([border_offset, border_offset + inner_height])

        if len(points) >= 6:  # Minimum points for a polygon
            self._canvas.create_polygon(
                points,
                fill=self._get_color('fg'),
                outline='',
                smooth=True
            )

    def _draw_spinner_progress(self, width: int, height: int) -> None:
        """Draw circular spinner animation."""
        if not self._canvas:
            raise RuntimeError("Canvas not initialized")

        border_offset = self.config.border_width if self.config.show_border else 0
        inner_width = width - (2 * border_offset)
        inner_height = height - (2 * border_offset)

        if inner_width <= 0 or inner_height <= 0:
            return

        # Draw background
        self._canvas.create_rectangle(
            border_offset, border_offset,
            border_offset + inner_width, border_offset + inner_height,
            fill=self._get_color('bg'),
            outline=''
        )

        # Calculate spinner dimensions
        spinner_size = min(inner_width, inner_height) * 0.6
        center_x = border_offset + inner_width / 2
        center_y = border_offset + inner_height / 2
        radius = spinner_size / 2

        # Draw spinning arc
        arc_extent = 90  # Arc length in degrees
        start_angle = self._animation_offset * 2  # Rotation angle

        self._canvas.create_arc(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            start=start_angle,
            extent=arc_extent,
            outline=self._get_color('fg'),
            width=max(2, int(radius / 10)),
            style='arc'
        )

    def _draw_gradient_rectangle(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Draw a rectangle with gradient fill."""
        if not self._canvas:
            raise RuntimeError("Canvas not initialized")

        width = x2 - x1
        height = y2 - y1

        if width <= 0 or height <= 0:
            return

        # Simple gradient simulation using multiple rectangles
        gradient_steps = min(int(width), 50)  # Limit steps for performance
        start_color = self._get_color('gradient_start')
        end_color = self._get_color('gradient_end')

        for i in range(gradient_steps):
            ratio = i / (gradient_steps - 1) if gradient_steps > 1 else 0
            color = self._blend_colors(start_color, end_color, ratio)

            step_width = width / gradient_steps
            step_x1 = x1 + (i * step_width)
            step_x2 = x1 + ((i + 1) * step_width)

            self._canvas.create_rectangle(
                step_x1, y1, step_x2, y2,
                fill=color,
                outline=''
            )

    def _draw_stripes(self, x: int, y: int, width: float, height: int) -> None:
        """Draw diagonal stripes over the progress bar."""
        if not self._canvas:
            raise RuntimeError("Canvas not initialized")

        stripe_width = 8
        stripe_spacing = 16

        # Create diagonal stripes
        for stripe_x in range(int(x - stripe_spacing), int(x + width + stripe_spacing), stripe_spacing):
            stripe_start_x = stripe_x + self._animation_offset % stripe_spacing

            points = [
                stripe_start_x, y,
                stripe_start_x + stripe_width, y,
                stripe_start_x + stripe_width - height, y + height,
                stripe_start_x - height, y + height
            ]

            self._canvas.create_polygon(
                points,
                fill=self._get_color('bg'),
                outline='',
                stipple='gray25'
            )

    def _blend_colors(self, color1: str, color2: str, ratio: float) -> str:
        """Blend two hex colors based on ratio (0.0 = color1, 1.0 = color2)."""
        try:
            # Convert hex to RGB
            c1_rgb = [int(color1[i:i+2], 16) for i in (1, 3, 5)]
            c2_rgb = [int(color2[i:i+2], 16) for i in (1, 3, 5)]

            # Blend colors
            blended_rgb = [
                int(c1_rgb[i] + (c2_rgb[i] - c1_rgb[i]) * ratio)
                for i in range(3)
            ]

            # Convert back to hex
            return f"#{blended_rgb[0]:02x}{blended_rgb[1]:02x}{blended_rgb[2]:02x}"
        except (ValueError, IndexError):
            return color1

    def _update_text_displays(self) -> None:
        """Update all text displays."""
        # Update percentage
        if self._percentage_var:
            if self.config.mode == LoadingMode.DETERMINATE:
                self._percentage_var.set(f"{self._progress:.1f}%")
            else:
                self._percentage_var.set("")

        # Update status text
        if self._text_var:
            if self._status_text:
                self._text_var.set(self._status_text)
            else:
                state_text = {
                    LoadingState.IDLE: "Ready",
                    LoadingState.LOADING: "Loading...",
                    LoadingState.COMPLETED: "Completed",
                    LoadingState.ERROR: "Error",
                    LoadingState.PAUSED: "Paused"
                }
                self._text_var.set(state_text.get(self._state, "Ready"))

        # Update time display
        if self._time_var and self._start_time and self._state == LoadingState.LOADING:
            elapsed = time.time() - self._start_time - self._paused_duration

            if self.config.mode == LoadingMode.DETERMINATE and self._progress > 0:
                # Estimate remaining time
                estimated_total = elapsed * (self._max_progress / self._progress)
                remaining = max(0, estimated_total - elapsed)
                self._time_var.set(f"{int(elapsed//60):02d}:{int(elapsed % 60):02d} / {int(remaining//60):02d}:{int(remaining % 60):02d}")
            else:
                self._time_var.set(f"{int(elapsed//60):02d}:{int(elapsed % 60):02d}")
        elif self._time_var:
            self._time_var.set("00:00")

    def _start_animation(self) -> None:
        """Start the animation thread."""
        if self.config.animate and not self._animation_running:
            self._animation_running = True
            self._animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
            self._animation_thread.start()

    def _stop_animation(self) -> None:
        """Stop the animation thread."""
        self._animation_running = False
        if self._animation_thread and self._animation_thread.is_alive():
            self._animation_thread.join(timeout=1.0)

    def _animation_loop(self) -> None:
        """Animation loop running in separate thread."""
        while self._animation_running:
            try:
                # Update animation variables
                self._animation_offset += 2 * self.config.animation_speed
                self._pulse_alpha += 0.1 * self.config.animation_speed

                # Schedule UI update on main thread
                self.frame_root.after_idle(self._update_display)

                # Control animation speed (60 FPS target)
                time.sleep(1.0 / 60.0 / self.config.animation_speed)
            except Exception:
                break

    def set_progress(self, progress: float, max_progress: Optional[float] = None) -> None:
        """
        Set the current progress value.

        Args:
            progress: Current progress value (0.0 to max_progress)
            max_progress: Optional new maximum progress value
        """
        old_progress = self._progress

        if max_progress is not None:
            self._max_progress = max(max_progress, 0.01)  # Prevent division by zero

        self._progress = max(0.0, min(progress, self._max_progress))

        # Calculate percentage for callback
        percentage = (self._progress / self._max_progress) * 100
        old_percentage = (old_progress / self._max_progress) * 100

        # Trigger callback
        if self.on_progress_changed and abs(percentage - old_percentage) > 0.1:
            self.on_progress_changed(self._progress, percentage)

        # Check for completion
        if self._progress >= self._max_progress and self._state == LoadingState.LOADING:
            self.set_completed()

        self._update_display()

    def increment_progress(self, increment: float = 1.0) -> None:
        """
        Increment the progress by a specified amount.

        Args:
            increment: Amount to increment progress
        """
        self.set_progress(self._progress + increment)

    def set_status_text(self, text: str) -> None:
        """
        Set custom status text.

        Args:
            text: Status text to display
        """
        self._status_text = text
        self._update_display()

    def set_color_scheme(self, scheme: str) -> None:
        """
        Change the color scheme.

        Args:
            scheme: Color scheme name ('default', 'success', 'warning', 'error', 'info')
        """
        if scheme in self._color_schemes:
            self.config.color_scheme = scheme
            self._update_display()

    def set_mode(self, mode: LoadingMode) -> None:
        """
        Change the loading bar mode.

        Args:
            mode: New LoadingMode to use
        """
        old_mode = self.config.mode
        self.config.mode = mode

        # Start/stop animation as needed
        if mode in [LoadingMode.INDETERMINATE, LoadingMode.PULSE, LoadingMode.WAVE, LoadingMode.SPINNER]:
            if self._state == LoadingState.LOADING:
                self._start_animation()
        else:
            if old_mode in [LoadingMode.INDETERMINATE, LoadingMode.PULSE, LoadingMode.WAVE, LoadingMode.SPINNER]:
                self._stop_animation()

        self._update_display()

    def start_loading(self, status_text: str = "") -> None:
        """
        Start the loading process.

        Args:
            status_text: Optional status text to display
        """
        old_state = self._state
        self._state = LoadingState.LOADING
        self._start_time = time.time()
        self._paused_duration = 0.0

        if status_text:
            self._status_text = status_text

        # Trigger state change callback
        if self.on_state_changed:
            self.on_state_changed(old_state, self._state)

        # Start animation if needed
        if self.config.mode in [LoadingMode.INDETERMINATE, LoadingMode.PULSE, LoadingMode.WAVE, LoadingMode.SPINNER]:
            self._start_animation()

        self._update_display()

    def pause_loading(self) -> None:
        """Pause the loading process."""
        if self._state == LoadingState.LOADING:
            old_state = self._state
            self._state = LoadingState.PAUSED
            self._pause_time = time.time()

            # Stop animation
            self._stop_animation()

            # Trigger state change callback
            if self.on_state_changed:
                self.on_state_changed(old_state, self._state)

            self._update_display()

    def resume_loading(self) -> None:
        """Resume the paused loading process."""
        if self._state == LoadingState.PAUSED and self._pause_time:
            old_state = self._state
            self._state = LoadingState.LOADING
            self._paused_duration += time.time() - self._pause_time
            self._pause_time = None

            # Restart animation if needed
            if self.config.mode in [LoadingMode.INDETERMINATE, LoadingMode.PULSE, LoadingMode.WAVE, LoadingMode.SPINNER]:
                self._start_animation()

            # Trigger state change callback
            if self.on_state_changed:
                self.on_state_changed(old_state, self._state)

            self._update_display()

    def set_canceled(self) -> None:
        """Mark the loading as canceled."""
        old_state = self._state
        self._state = LoadingState.IDLE
        self._stop_animation()

        # Trigger state change callback
        if self.on_state_changed:
            self.on_state_changed(old_state, self._state)

        self._update_display()

    def set_completed(self, status_text: str = "") -> None:
        """
        Mark the loading as completed.

        Args:
            status_text: Optional completion status text
        """
        old_state = self._state
        self._state = LoadingState.COMPLETED
        self._stop_animation()

        if status_text:
            self._status_text = status_text

        # Set progress to 100% for determinate mode
        if self.config.mode == LoadingMode.DETERMINATE:
            self._progress = self._max_progress

        # Change to success color scheme
        if self.config.color_scheme == 'default':
            self.set_color_scheme('success')

        # Trigger callbacks
        if self.on_state_changed:
            self.on_state_changed(old_state, self._state)

        if self.on_completed:
            self.on_completed()

        # Pulse effect on completion
        if self.config.pulse_on_complete:
            self.frame_root.after(100, self._completion_pulse)

        self._update_display()

    def set_error(self, error_message: str = "") -> None:
        """
        Mark the loading as failed with error.

        Args:
            error_message: Error message to display
        """
        old_state = self._state
        self._state = LoadingState.ERROR
        self._stop_animation()

        if error_message:
            self._status_text = error_message

        # Change to error color scheme
        self.set_color_scheme('error')

        # Trigger callbacks
        if self.on_state_changed:
            self.on_state_changed(old_state, self._state)

        if self.on_error:
            self.on_error(error_message)

        self._update_display()

    def reset(self) -> None:
        """Reset the loading bar to initial state."""
        old_state = self._state
        self._state = LoadingState.IDLE
        self._progress = 0.0
        self._status_text = ""
        self._start_time = None
        self._pause_time = None
        self._paused_duration = 0.0
        self._animation_offset = 0.0
        self._pulse_alpha = 0.0

        self._stop_animation()

        # Reset to default color scheme
        self.config.color_scheme = 'default'

        # Trigger state change callback
        if self.on_state_changed:
            self.on_state_changed(old_state, self._state)

        self._update_display()

    def _completion_pulse(self, pulse_count: int = 0) -> None:
        """Create a pulsing effect on completion."""
        if pulse_count < 3 and self._state == LoadingState.COMPLETED:
            # Temporarily change to pulse mode
            original_mode = self.config.mode
            self.config.mode = LoadingMode.PULSE
            self._start_animation()

            # Stop pulse after short duration and restore mode
            self.frame_root.after(500, lambda: self._stop_pulse_and_restore(original_mode, pulse_count + 1))

    def _stop_pulse_and_restore(self, original_mode: LoadingMode, pulse_count: int) -> None:
        """Stop pulsing and restore original mode."""
        self._stop_animation()
        self.config.mode = original_mode
        self._update_display()

        # Continue pulsing if needed
        if pulse_count < 3:
            self.frame_root.after(200, lambda: self._completion_pulse(pulse_count))

    def get_progress(self) -> tuple[float, float]:
        """
        Get current progress information.

        Returns:
            Tuple of (current_progress, percentage)
        """
        percentage = (self._progress / self._max_progress) * 100
        return self._progress, percentage

    def get_state(self) -> LoadingState:
        """
        Get current loading state.

        Returns:
            Current LoadingState
        """
        return self._state

    def get_elapsed_time(self) -> float:
        """
        Get elapsed time since loading started.

        Returns:
            Elapsed time in seconds (excluding paused time)
        """
        if not self._start_time:
            return 0.0

        current_time = time.time()
        if self._state == LoadingState.PAUSED and self._pause_time:
            current_time = self._pause_time

        return current_time - self._start_time - self._paused_duration

    def destroy(self) -> None:
        """Clean up resources when widget is destroyed."""
        self._stop_animation()
        self.frame.destroy()


class PyroxTkLoadingBar(tk.Toplevel):
    """
    PyroxLoadingBar that exists as a Tk TopLevel.
    This is useful for standalone loading indicators that pop up in their own window.
    """

    def __init__(
        self,
        master=None,
        config: LoadingConfig | None = None,
        **kwargs
    ) -> None:
        super().__init__(master, **kwargs)
        self.loading_bar = PyroxLoadingBar(self, config=config)
        self.loading_bar.frame.pack(fill=tk.BOTH, expand=True)

        # Disable top bar controls, but keep window viewable
        self.overrideredirect(True)
        self.geometry("400x100")

        # Raise this window on top of all others
        self.lift()
        self.attributes("-topmost", True)

        # Center this window on the screen
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def start(self, status_text: str = "") -> None:
        """Start the loading bar."""
        self.loading_bar.start_loading(status_text)

    def stop(self) -> None:
        """Stop the loading bar."""
        self.loading_bar.set_completed()


# Testing code
if __name__ == '__main__':
    """Test the PyroxLoadingBar when run directly."""
    import random

    # Create the main test window
    root = tk.Tk()
    root.title("PyroxLoadingBar Test")
    root.geometry("900x700")
    root.configure(bg='#2b2b2b')  # Match Pyrox theme

    # Create main container
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
    main_frame.grid_columnconfigure(0, weight=1)

    # Title
    title_label = ttk.Label(
        main_frame,
        text="PyroxLoadingBar Test Suite",
    )
    title_label.grid(row=0, column=0, pady=(0, 15))

    # Create different loading bar examples
    examples_frame = ttk.LabelFrame(
        main_frame,
        text="Loading Bar Examples",
    )
    examples_frame.grid(row=1, column=0, sticky='ew', pady=(0, 10))
    examples_frame.grid_columnconfigure(0, weight=1)

    # Example 1: Determinate progress bar
    ex1_label = ttk.Label(examples_frame, text="Determinate Progress (with gradient & time):")
    ex1_label.grid(row=0, column=0, sticky='w', padx=10, pady=(10, 5))

    config1 = LoadingConfig(
        mode=LoadingMode.DETERMINATE,
        show_percentage=True,
        show_text=True,
        show_time=True,
        gradient=True,
        height=28
    )
    loading_bar1 = PyroxLoadingBar(examples_frame, config=config1)
    loading_bar1.frame_root.grid(row=1, column=0, sticky='ew', padx=10, pady=(0, 10))

    # Example 2: Indeterminate loading bar
    ex2_label = ttk.Label(examples_frame, text="Indeterminate Activity Indicator:")
    ex2_label.grid(row=2, column=0, sticky='w', padx=10, pady=(10, 5))

    config2 = LoadingConfig(
        mode=LoadingMode.INDETERMINATE,
        show_percentage=False,
        show_text=True,
        color_scheme='info',
        height=20
    )
    loading_bar2 = PyroxLoadingBar(examples_frame, config=config2)
    loading_bar2.frame_root.grid(row=3, column=0, sticky='ew', padx=10, pady=(0, 10))

    # Example 3: Pulse loading bar
    ex3_label = ttk.Label(examples_frame, text="Pulse Animation (Warning Style):")
    ex3_label.grid(row=4, column=0, sticky='w', padx=10, pady=(10, 5))

    config3 = LoadingConfig(
        mode=LoadingMode.PULSE,
        show_percentage=False,
        show_text=True,
        color_scheme='warning',
        height=24
    )
    loading_bar3 = PyroxLoadingBar(examples_frame, config=config3)
    loading_bar3.frame_root.grid(row=5, column=0, sticky='ew', padx=10, pady=(0, 10))

    # Example 4: Wave animation
    ex4_label = ttk.Label(examples_frame, text="Wave Animation:")
    ex4_label.grid(row=6, column=0, sticky='w', padx=10, pady=(10, 5))

    config4 = LoadingConfig(
        mode=LoadingMode.WAVE,
        show_percentage=False,
        show_text=True,
        color_scheme='success',
        height=32
    )
    loading_bar4 = PyroxLoadingBar(examples_frame, config=config4)
    loading_bar4.frame_root.grid(row=7, column=0, sticky='ew', padx=10, pady=(0, 10))

    # Example 5: Spinner
    ex5_label = ttk.Label(examples_frame, text="Spinner Animation:")
    ex5_label.grid(row=8, column=0, sticky='w', padx=10, pady=(10, 5))

    config5 = LoadingConfig(
        mode=LoadingMode.SPINNER,
        show_percentage=False,
        show_text=True,
        height=36
    )
    loading_bar5 = PyroxLoadingBar(examples_frame, config=config5)
    loading_bar5.frame_root.grid(row=9, column=0, sticky='ew', padx=10, pady=(0, 15))

    # Example 6: Toplevel loading bar
    ex6_label = ttk.Label(examples_frame, text="Toplevel Loading Bar:")
    ex6_label.grid(row=10, column=0, sticky='w', padx=10, pady=(10, 5))

    toplevel_bar = PyroxTkLoadingBar(root)
    toplevel_bar.loading_bar.config.mode = LoadingMode.DETERMINATE
    toplevel_bar.loading_bar.config.show_percentage = True
    toplevel_bar.loading_bar.config.show_text = True

    # Control panel
    control_frame = ttk.LabelFrame(
        main_frame,
        text="Control Panel",
    )
    control_frame.grid(row=2, column=0, sticky='ew', pady=(0, 10))

    # Control buttons
    buttons_frame = ttk.Frame(control_frame)
    buttons_frame.pack(fill=tk.X, padx=10, pady=10)

    # Progress simulation variables
    progress_thread = None
    simulate_running = False

    def start_simulation():
        """Start progress simulation."""
        global simulate_running, progress_thread

        if simulate_running:
            return

        simulate_running = True

        # Start all loading bars
        loading_bar1.start_loading("Processing files...")
        loading_bar2.start_loading("Connecting to server...")
        loading_bar3.start_loading("Validating data...")
        loading_bar4.start_loading("Synchronizing...")
        loading_bar5.start_loading("Initializing...")
        toplevel_bar.start("Loading resources...")

        # Start progress simulation thread
        progress_thread = threading.Thread(target=simulate_progress, daemon=True)
        progress_thread.start()

        print("Started loading simulation")

    def simulate_progress():
        """Simulate gradual progress updates."""
        global simulate_running

        progress = 0
        while simulate_running and progress < 100:
            progress += random.uniform(0.5, 3.0)
            progress = min(progress, 100)

            # Update determinate progress bar
            root.after_idle(lambda p=progress: loading_bar1.set_progress(p))
            root.after_idle(lambda p=progress: toplevel_bar.loading_bar.set_progress(p))

            # Update status texts randomly
            if random.random() < 0.3:
                statuses = [
                    f"Processing item {int(progress)}...",
                    f"Analyzing data ({progress:.1f}% complete)...",
                    "Optimizing results...",
                    "Finalizing process..."
                ]
                status = statuses[int(progress) % len(statuses)]
                root.after_idle(lambda s=status: loading_bar1.set_status_text(s))
                root.after_idle(lambda s=status: toplevel_bar.loading_bar.set_status_text(s))

            time.sleep(random.uniform(0.1, 0.5))  # Variable update speed

        # Complete all bars
        if simulate_running:
            root.after_idle(complete_simulation)

    def complete_simulation():
        """Complete all loading bars."""
        loading_bar1.set_completed("Processing completed!")
        loading_bar2.set_completed("Connected successfully!")
        loading_bar3.set_completed("Data validated!")
        loading_bar4.set_completed("Sync complete!")
        loading_bar5.set_completed("Ready!")
        toplevel_bar.stop()

        print("Loading simulation completed")

    def pause_simulation():
        """Pause the loading simulation."""
        loading_bar1.pause_loading()
        loading_bar2.pause_loading()
        loading_bar3.pause_loading()
        loading_bar4.pause_loading()
        loading_bar5.pause_loading()
        toplevel_bar.loading_bar.pause_loading()
        print("Loading simulation paused")

    def resume_simulation():
        """Resume the loading simulation."""
        loading_bar1.resume_loading()
        loading_bar2.resume_loading()
        loading_bar3.resume_loading()
        loading_bar4.resume_loading()
        loading_bar5.resume_loading()
        toplevel_bar.loading_bar.resume_loading()
        print("Loading simulation resumed")

    def stop_simulation():
        """Stop the loading simulation."""
        global simulate_running
        simulate_running = False

        loading_bar1.reset()
        loading_bar2.reset()
        loading_bar3.reset()
        loading_bar4.reset()
        loading_bar5.reset()
        toplevel_bar.loading_bar.reset()
        print("Loading simulation stopped and reset")

    def simulate_error():
        """Simulate an error condition."""
        global simulate_running
        simulate_running = False

        loading_bar1.set_error("File processing failed!")
        loading_bar2.set_error("Connection timeout!")
        loading_bar3.set_error("Invalid data format!")
        loading_bar4.set_error("Sync interrupted!")
        loading_bar5.set_error("Initialization failed!")
        toplevel_bar.loading_bar.set_error("Resource loading error!")
        print("Error simulation triggered")

    def change_themes():
        """Cycle through different color schemes."""
        schemes = ['default', 'success', 'warning', 'error', 'info']
        current_scheme = loading_bar1.config.color_scheme
        current_index = schemes.index(current_scheme) if current_scheme in schemes else 0
        next_scheme = schemes[(current_index + 1) % len(schemes)]

        loading_bar1.set_color_scheme(next_scheme)
        toplevel_bar.loading_bar.set_color_scheme(next_scheme)
        print(f"Changed color scheme to: {next_scheme}")

    def toggle_animations():
        """Toggle animation on/off."""
        for bar in [loading_bar1, loading_bar2, loading_bar3, loading_bar4, loading_bar5, toplevel_bar.loading_bar]:
            bar.config.animate = not bar.config.animate

        print(f"Animations {'enabled' if loading_bar1.config.animate else 'disabled'}")

    # Control buttons
    ttk.Button(buttons_frame, text="Start", command=start_simulation, width=8).pack(side=tk.LEFT, padx=2)
    ttk.Button(buttons_frame, text="Pause", command=pause_simulation, width=8).pack(side=tk.LEFT, padx=2)
    ttk.Button(buttons_frame, text="Resume", command=resume_simulation, width=8).pack(side=tk.LEFT, padx=2)
    ttk.Button(buttons_frame, text="Stop", command=stop_simulation, width=8).pack(side=tk.LEFT, padx=2)
    ttk.Button(buttons_frame, text="Error", command=simulate_error, width=8).pack(side=tk.LEFT, padx=2)
    ttk.Button(buttons_frame, text="Themes", command=change_themes, width=8).pack(side=tk.LEFT, padx=2)
    ttk.Button(buttons_frame, text="Animation", command=toggle_animations, width=8).pack(side=tk.LEFT, padx=2)

    # Output log
    output_frame = ttk.LabelFrame(
        main_frame,
        text="Event Log",
    )
    output_frame.grid(row=3, column=0, sticky='ew')

    output_text = tk.Text(
        output_frame,
        height=8,
        bg='#1e1e1e',
        fg='#00ff00',
        font=('Consolas', 9),
        wrap=tk.WORD,
        insertbackground='white'
    )

    scrollbar = ttk.Scrollbar(output_frame, command=output_text.yview)
    output_text.config(yscrollcommand=scrollbar.set)

    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Setup event callbacks for logging
    def log_progress_changed(progress: float, percentage: float):
        """Log progress changes."""
        message = f"Progress: {progress:.1f}/{loading_bar1._max_progress} ({percentage:.1f}%)\n"
        output_text.insert(tk.END, message)
        output_text.see(tk.END)

    def log_state_changed(old_state: LoadingState, new_state: LoadingState):
        """Log state changes."""
        message = f"State changed: {old_state.value} -> {new_state.value}\n"
        output_text.insert(tk.END, message)
        output_text.see(tk.END)

    def log_completed():
        """Log completion."""
        elapsed = loading_bar1.get_elapsed_time()
        message = f"Loading completed! Total time: {elapsed:.2f} seconds\n"
        output_text.insert(tk.END, message)
        output_text.see(tk.END)

    def log_error(error_msg: str):
        """Log errors."""
        message = f"Error occurred: {error_msg}\n"
        output_text.insert(tk.END, message)
        output_text.see(tk.END)

    # Connect callbacks to first loading bar for demonstration
    loading_bar1.on_progress_changed = log_progress_changed
    loading_bar1.on_state_changed = log_state_changed
    loading_bar1.on_completed = log_completed
    loading_bar1.on_error = log_error

    # Initial log message
    output_text.insert(tk.END, "PyroxLoadingBar Test Suite\n")
    output_text.insert(tk.END, "=" * 50 + "\n\n")
    output_text.insert(tk.END, "Features demonstrated:\n")
    output_text.insert(tk.END, "• Determinate progress with percentage and time tracking\n")
    output_text.insert(tk.END, "• Indeterminate activity indicators\n")
    output_text.insert(tk.END, "• Pulse, wave, and spinner animations\n")
    output_text.insert(tk.END, "• Multiple color schemes and themes\n")
    output_text.insert(tk.END, "• State management (loading, paused, completed, error)\n")
    output_text.insert(tk.END, "• Event callbacks and progress tracking\n")
    output_text.insert(tk.END, "• Thread-safe operations\n\n")
    output_text.insert(tk.END, "Use the control panel to test different features!\n\n")

    # Status bar
    status_frame = ttk.Frame(main_frame, relief=tk.SUNKEN)
    status_frame.grid(row=4, column=0, sticky='ew', pady=(10, 0))

    status_label = ttk.Label(
        status_frame,
        text="PyroxLoadingBar Test Ready - Use controls to test functionality",
        anchor=tk.W,
    )
    status_label.pack(fill=tk.X, padx=5, pady=2)

    print("PyroxLoadingBar comprehensive test suite initialized")
    print("Available modes:", [mode.value for mode in LoadingMode])
    print("Available states:", [state.value for state in LoadingState])

    # Cleanup function
    def on_closing():
        """Clean up when window is closed."""
        global simulate_running
        simulate_running = False

        # Stop all loading bars
        for bar in [loading_bar1, loading_bar2, loading_bar3, loading_bar4, loading_bar5]:
            bar.destroy()

        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Start the test
    root.mainloop()

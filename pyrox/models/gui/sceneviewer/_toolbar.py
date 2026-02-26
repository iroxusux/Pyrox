import tkinter as tk
from tkinter import ttk


class _SceneViewerToolbar:
    def __init__(
        self,
        parent
    ):
        self._parent = parent

        # Public callbacks to be set by the SceneViewerFrame
        self.on_toggle_object_palette = lambda: None
        self.on_toggle_properties_panel = lambda: None
        self.on_toggle_bridge_panel = lambda: None
        self.on_toggle_object_explorer = lambda: None
        self.on_toggle_entity_names = lambda: None

    def _call_callback(self, callback):
        if callable(callback):
            callback()

    def build_toolbar(self) -> '_SceneViewerToolbar':
        """Build the toolbar with viewer controls.

        Returns:
            self, for chaining
        """
        if hasattr(self, '_toolbar'):
            self._toolbar.destroy()  # Remove existing toolbar if it exists

        self._toolbar = ttk.Frame(self._parent)
        self._toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Object Palette Toggle Button
        self._object_palette_btn = ttk.Button(
            self._toolbar,
            text="🧰",  # Toolbox emoji
            width=3,
            command=lambda: self._call_callback(self.on_toggle_object_palette)
        )
        self._object_palette_btn.pack(side=tk.LEFT, padx=2)
        self._create_tooltip(self._object_palette_btn, "Toggle Object Palette")

        # Properties Panel Toggle Button
        self._properties_panel_btn = ttk.Button(
            self._toolbar,
            text="📋",  # Clipboard emoji
            width=3,
            command=lambda: self._call_callback(self.on_toggle_properties_panel)
        )
        self._properties_panel_btn.pack(side=tk.LEFT, padx=2)
        self._create_tooltip(self._properties_panel_btn, "Toggle Properties Panel")

        # Scene Bridge Panel Toggle Button
        self._bridge_panel_btn = ttk.Button(
            self._toolbar,
            text="🔗",  # Link emoji
            width=3,
            command=lambda: self._call_callback(self.on_toggle_bridge_panel)
        )
        self._bridge_panel_btn.pack(side=tk.LEFT, padx=2)
        self._create_tooltip(self._bridge_panel_btn, "Toggle Scene Bridge Panel")

        # Object Explorer Toggle Button
        self._object_explorer_btn = ttk.Button(
            self._toolbar,
            text="🗂️",  # File cabinet emoji
            width=3,
            command=lambda: self._call_callback(self.on_toggle_object_explorer)
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
            command=lambda: self._call_callback(self.on_toggle_entity_names)
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

        return self

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

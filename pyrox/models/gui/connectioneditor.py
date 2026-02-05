"""
Connection Editor Widget for Pyrox applications.

This module provides a visual node-based editor for creating and managing
connections between scene objects. Displays objects as nodes with input/output
ports and allows drawing connections between them.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Tuple
from dataclasses import dataclass, field


from pyrox.interfaces import IScene, ISceneObject
from pyrox.models.connection import ConnectionRegistry


@dataclass
class NodePort:
    """Represents an input or output port on a node."""
    name: str
    is_output: bool  # True for output, False for input
    x: float
    y: float
    canvas_id: int


@dataclass
class VisualNode:
    """Represents a visual node on the canvas."""
    obj_id: str
    scene_obj: ISceneObject
    x: float
    y: float
    width: float = 200.0
    height: float = 100.0
    canvas_id: Optional[int] = None
    text_id: Optional[int] = None
    ports: Dict[str, NodePort] = field(default_factory=dict)


class ConnectionEditor(ttk.Frame):
    """
    A visual connection editor for wiring scene objects together.

    Features:
    - Node-based visual representation of scene objects
    - Visual ports for inputs and outputs
    - Drag-and-drop connection creation
    - Connection deletion
    - Pan and zoom canvas
    - Test connections
    - Auto-layout nodes

    Args:
        master: Parent widget
        scene: Scene containing objects to connect
        connection_registry: Registry managing the connections
        **kwargs: Additional arguments passed to ttk.Frame
    """

    def __init__(
        self,
        master=None,
        scene: Optional[IScene] = None,
        connection_registry: Optional[ConnectionRegistry] = None,
        **kwargs
    ) -> None:
        """Initialize the connection editor."""
        super().__init__(master, **kwargs)

        # State
        self._scene: Optional[IScene] = scene
        self._registry: Optional[ConnectionRegistry] = connection_registry
        self._nodes: Dict[str, VisualNode] = {}
        self._connection_lines: Dict[Tuple[str, str, str, str], int] = {}  # (src_id, src_port, tgt_id, tgt_port) -> canvas_id

        # Interaction state
        self._dragging_node: Optional[str] = None
        self._drag_start_x: Optional[float] = None
        self._drag_start_y: Optional[float] = None
        self._connecting: bool = False
        self._connection_start_port: Optional[Tuple[str, str, bool]] = None  # (obj_id, port_name, is_output)
        self._temp_connection_line: Optional[int] = None

        # Viewport state
        self._pan_x: float = 0.0
        self._pan_y: float = 0.0
        self._zoom: float = 1.0
        self._panning: bool = False
        self._pan_start_x: Optional[float] = None
        self._pan_start_y: Optional[float] = None

        # Visual settings
        self._node_color: str = "#4a9eff"
        self._node_border: str = "#2c5aa0"
        self._port_color: str = "#00ff00"
        self._output_port_color: str = "#ff6600"
        self._input_port_color: str = "#6600ff"
        self._connection_color: str = "#ffaa00"
        self._grid_color: str = "#3a3a3a"

        # Build UI
        self._build_ui()
        self._bind_events()

        # Load scene if provided
        if self._scene:
            self.load_scene(self._scene, self._registry)

    def _build_ui(self) -> None:
        """Build the user interface."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Toolbar
        self._build_toolbar()

        # Canvas
        self._canvas = tk.Canvas(
            self,
            bg="#2b2b2b",
            highlightthickness=0
        )
        self._canvas.grid(row=1, column=0, sticky='nsew')

        # Status bar
        self._build_status_bar()

    def _build_toolbar(self) -> None:
        """Build the toolbar with controls."""
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky='ew', padx=5, pady=5)

        # Buttons
        ttk.Button(
            toolbar,
            text="🔄 Reload",
            command=self.reload_scene,
            width=10
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="🎯 Auto Layout",
            command=self.auto_layout,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="🧹 Clear All",
            command=self.clear_all_connections,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Button(
            toolbar,
            text="✓ Test All",
            command=self.test_all_connections,
            width=10
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="💾 Save",
            command=self.save_connections,
            width=10
        ).pack(side=tk.LEFT, padx=2)

        # Zoom controls
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Label(toolbar, text="Zoom:").pack(side=tk.LEFT, padx=(5, 2))

        ttk.Button(
            toolbar,
            text="➕",
            command=self.zoom_in,
            width=3
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="➖",
            command=self.zoom_out,
            width=3
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="Reset",
            command=self.reset_view,
            width=8
        ).pack(side=tk.LEFT, padx=2)

    def _build_status_bar(self) -> None:
        """Build the status bar."""
        self._status_var = tk.StringVar(value="Ready")

        status_bar = ttk.Frame(self)
        status_bar.grid(row=2, column=0, sticky='ew', padx=5, pady=5)

        ttk.Label(
            status_bar,
            textvariable=self._status_var,
            relief=tk.SUNKEN
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _bind_events(self) -> None:
        """Bind mouse and keyboard events."""
        # Left click - select/start connection
        self._canvas.bind("<ButtonPress-1>", self._on_left_click)
        self._canvas.bind("<B1-Motion>", self._on_left_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_left_release)

        # Middle click - pan
        self._canvas.bind("<ButtonPress-2>", self._on_middle_press)
        self._canvas.bind("<B2-Motion>", self._on_middle_drag)
        self._canvas.bind("<ButtonRelease-2>", self._on_middle_release)

        # Right click - context menu
        self._canvas.bind("<ButtonPress-3>", self._on_right_click)

        # Mouse wheel - zoom
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)

        # Delete key
        self._canvas.bind("<Delete>", self._on_delete)

    def load_scene(
        self,
        scene: IScene,
        connection_registry: Optional[ConnectionRegistry] = None
    ) -> None:
        """Load a scene into the editor.

        Args:
            scene: Scene to load
            connection_registry: Optional connection registry to use
        """
        self._scene = scene
        if connection_registry:
            self._registry = connection_registry
        elif not self._registry:
            self._registry = ConnectionRegistry()

        # Clear existing
        self._canvas.delete("all")
        self._nodes.clear()
        self._connection_lines.clear()

        # Create nodes for all scene objects
        x, y = 50, 50
        for obj_id, scene_obj in scene.scene_objects.items():
            self._create_node(obj_id, scene_obj, x, y)

            # Register physics body with connection registry (not the SceneObject wrapper)
            # The physics body has the actual callback lists and methods
            if self._registry and obj_id not in self._registry._objects:
                self._registry.register_object(obj_id, scene_obj.physics_body)

            # Move to next position
            x += 250
            if x > 800:
                x = 50
                y += 150

        # Draw existing connections
        self._draw_existing_connections()

        self._status_var.set(f"Loaded {len(self._nodes)} objects")

    def _create_node(
        self,
        obj_id: str,
        scene_obj: ISceneObject,
        x: float,
        y: float
    ) -> None:
        """Create a visual node for a scene object.

        Args:
            obj_id: Object ID
            scene_obj: Scene object
            x: X position
            y: Y position
        """
        # Get inputs and outputs
        outputs = scene_obj.get_outputs()
        inputs = scene_obj.get_inputs()

        # Calculate node height based on port count
        port_spacing = 25
        max_ports = max(len(outputs), len(inputs))
        height = max(100, 60 + max_ports * port_spacing)

        node = VisualNode(
            obj_id=obj_id,
            scene_obj=scene_obj,
            x=x,
            y=y,
            height=height
        )

        # Draw node rectangle
        canvas_id = self._canvas.create_rectangle(
            x, y, x + node.width, y + node.height,
            fill=self._node_color,
            outline=self._node_border,
            width=2,
            tags=("node", obj_id)
        )
        node.canvas_id = canvas_id

        # Draw node title
        text_id = self._canvas.create_text(
            x + node.width / 2, y + 20,
            text=scene_obj.name,
            fill="white",
            font=("Arial", 10, "bold"),
            tags=("node", obj_id)
        )
        node.text_id = text_id

        # Draw output ports (right side)
        port_y = y + 50
        for output_name in outputs.keys():
            port_x = x + node.width

            # Draw port circle
            port_id = self._canvas.create_oval(
                port_x - 8, port_y - 8, port_x + 8, port_y + 8,
                fill=self._output_port_color,
                outline="white",
                width=2,
                tags=("port", "output", obj_id, output_name)
            )

            # Draw port label
            self._canvas.create_text(
                port_x - 15, port_y,
                text=output_name.replace("_callbacks", "").replace("on_", ""),
                fill="white",
                font=("Arial", 8),
                anchor=tk.E,
                tags=("port_label", obj_id)
            )

            node.ports[output_name] = NodePort(
                name=output_name,
                is_output=True,
                x=port_x,
                y=port_y,
                canvas_id=port_id
            )

            port_y += port_spacing

        # Draw input ports (left side)
        port_y = y + 50
        for input_name in inputs.keys():
            port_x = x

            # Draw port circle
            port_id = self._canvas.create_oval(
                port_x - 8, port_y - 8, port_x + 8, port_y + 8,
                fill=self._input_port_color,
                outline="white",
                width=2,
                tags=("port", "input", obj_id, input_name)
            )

            # Draw port label
            self._canvas.create_text(
                port_x + 15, port_y,
                text=input_name,
                fill="white",
                font=("Arial", 8),
                anchor=tk.W,
                tags=("port_label", obj_id)
            )

            node.ports[input_name] = NodePort(
                name=input_name,
                is_output=False,
                x=port_x,
                y=port_y,
                canvas_id=port_id
            )

            port_y += port_spacing

        self._nodes[obj_id] = node

    def _draw_existing_connections(self) -> None:
        """Draw all existing connections from the registry."""
        if not self._registry:
            return

        for conn in self._registry._connections:
            self._draw_connection(
                conn.source_id,
                conn.source_output,
                conn.target_id,
                conn.target_input
            )

    def _draw_connection(
        self,
        source_id: str,
        source_port: str,
        target_id: str,
        target_port: str
    ) -> bool:
        """Draw a connection line between two ports.

        Args:
            source_id: Source object ID
            source_port: Source port name
            target_id: Target object ID
            target_port: Target port name

        Returns:
            True if connection was drawn successfully, False otherwise
        """
        source_node = self._nodes.get(source_id)
        target_node = self._nodes.get(target_id)

        if not source_node:
            print(f"Warning: Source node {source_id} not found")
            return False
        if not target_node:
            print(f"Warning: Target node {target_id} not found")
            return False

        source_port_obj = source_node.ports.get(source_port)
        target_port_obj = target_node.ports.get(target_port)

        if not source_port_obj:
            print(f"Warning: Source port {source_port} not found on {source_id}")
            print(f"Available ports: {list(source_node.ports.keys())}")
            return False
        if not target_port_obj:
            print(f"Warning: Target port {target_port} not found on {target_id}")
            print(f"Available ports: {list(target_node.ports.keys())}")
            return False

        # Draw bezier curve connection
        x1, y1 = source_port_obj.x, source_port_obj.y
        x2, y2 = target_port_obj.x, target_port_obj.y

        # Control points for bezier curve
        cx1 = x1 + 50
        cy1 = y1
        cx2 = x2 - 50
        cy2 = y2

        # Draw smooth curve
        line_id = self._canvas.create_line(
            x1, y1,
            cx1, cy1,
            cx2, cy2,
            x2, y2,
            fill=self._connection_color,
            width=3,
            smooth=True,
            tags=("connection", f"{source_id}_{source_port}", f"{target_id}_{target_port}")
        )

        self._connection_lines[(source_id, source_port, target_id, target_port)] = line_id

        # Force canvas update to make line visible immediately
        self._canvas.update_idletasks()
        return True

    def _on_left_click(self, event: tk.Event) -> None:
        """Handle left mouse button press.

        Args:
            event: Mouse event
        """
        # Check if clicked on a port
        clicked_items = self._canvas.find_overlapping(
            event.x - 5, event.y - 5,
            event.x + 5, event.y + 5
        )

        for item in clicked_items:
            tags = self._canvas.gettags(item)
            if "port" in tags:
                # Start connection
                obj_id = tags[2]
                port_name = tags[3]
                is_output = "output" in tags

                self._connection_start_port = (obj_id, port_name, is_output)
                self._connecting = True
                self._status_var.set(f"Connecting from {obj_id}.{port_name}...")
                return

        # Check if clicked on a node
        for item in clicked_items:
            tags = self._canvas.gettags(item)
            if "node" in tags and len(tags) >= 2:
                obj_id = tags[1]
                if obj_id in self._nodes:
                    # Start dragging node
                    self._dragging_node = obj_id
                    self._drag_start_x = event.x
                    self._drag_start_y = event.y
                    return

    def _on_left_drag(self, event: tk.Event) -> None:
        """Handle left mouse button drag.

        Args:
            event: Mouse event
        """
        if self._connecting and self._connection_start_port:
            # Update temporary connection line
            if self._temp_connection_line:
                self._canvas.delete(self._temp_connection_line)

            source_node = self._nodes[self._connection_start_port[0]]
            source_port = source_node.ports[self._connection_start_port[1]]

            self._temp_connection_line = self._canvas.create_line(
                source_port.x, source_port.y,
                event.x, event.y,
                fill=self._connection_color,
                width=2,
                dash=(5, 5),
                tags="temp"
            )

        elif self._dragging_node and self._drag_start_x is not None:
            # Move node
            dx = event.x - self._drag_start_x
            dy = event.y - self._drag_start_y

            node = self._nodes[self._dragging_node]

            # Move all items with this node's tag
            for item in self._canvas.find_withtag(self._dragging_node):
                self._canvas.move(item, dx, dy)

            # Update node position
            node.x += dx
            node.y += dy

            # Update port positions
            for port in node.ports.values():
                port.x += dx
                port.y += dy

            # Update drag start position
            self._drag_start_x = event.x
            self._drag_start_y = event.y

            # Redraw connections involving this node
            self._redraw_node_connections(self._dragging_node)

    def _on_left_release(self, event: tk.Event) -> None:
        """Handle left mouse button release.

        Args:
            event: Mouse event
        """
        if self._connecting and self._connection_start_port:
            # Check if released on a port
            clicked_items = self._canvas.find_overlapping(
                event.x - 5, event.y - 5,
                event.x + 5, event.y + 5
            )

            for item in clicked_items:
                tags = self._canvas.gettags(item)
                if "port" in tags:
                    target_obj_id = tags[2]
                    target_port_name = tags[3]
                    is_output = "output" in tags

                    source_obj_id, source_port_name, source_is_output = self._connection_start_port

                    # Valid connection: output to input or input to output
                    if source_is_output != is_output:
                        if source_is_output:
                            # Source is output, target is input
                            self._create_connection(
                                source_obj_id, source_port_name,
                                target_obj_id, target_port_name
                            )
                        else:
                            # Source is input, target is output
                            self._create_connection(
                                target_obj_id, target_port_name,
                                source_obj_id, source_port_name
                            )
                    else:
                        self._status_var.set("❌ Cannot connect ports of same type!")
                    break

            # Clean up temporary line
            if self._temp_connection_line:
                self._canvas.delete(self._temp_connection_line)
                self._temp_connection_line = None

            self._connecting = False
            self._connection_start_port = None
            self._status_var.set("Ready")

        self._dragging_node = None
        self._drag_start_x = None
        self._drag_start_y = None

    def _create_connection(
        self,
        source_id: str,
        source_port: str,
        target_id: str,
        target_port: str
    ) -> None:
        """Create a new connection.

        Args:
            source_id: Source object ID
            source_port: Source output port name
            target_id: Target object ID
            target_port: Target input port name
        """
        # Check if connection already exists
        conn_key = (source_id, source_port, target_id, target_port)
        if conn_key in self._connection_lines:
            self._status_var.set("⚠️ Connection already exists!")
            return

        # Create connection in registry
        if self._registry:
            try:
                self._registry.connect(
                    source_id, source_port,
                    target_id, target_port
                )

                # Draw connection
                success = self._draw_connection(source_id, source_port, target_id, target_port)

                if success:
                    self._status_var.set(f"✓ Connected {source_id}.{source_port} → {target_id}.{target_port}")
                else:
                    self._status_var.set(f"❌ Failed to draw connection - check console for details")
            except Exception as e:
                self._status_var.set(f"❌ Error: {str(e)}")
                print(f"Connection error: {e}")
                import traceback
                traceback.print_exc()

    def _redraw_node_connections(self, obj_id: str) -> None:
        """Redraw all connections involving a node.

        Args:
            obj_id: Object ID
        """
        # Find all connections involving this node
        to_redraw = []
        for conn_key in self._connection_lines.keys():
            source_id, source_port, target_id, target_port = conn_key
            if source_id == obj_id or target_id == obj_id:
                to_redraw.append(conn_key)

        # Redraw them
        for conn_key in to_redraw:
            source_id, source_port, target_id, target_port = conn_key

            # Delete old line
            old_line_id = self._connection_lines.pop(conn_key)
            self._canvas.delete(old_line_id)

            # Draw new line
            self._draw_connection(source_id, source_port, target_id, target_port)

    def _on_middle_press(self, event: tk.Event) -> None:
        """Handle middle mouse button press for panning."""
        self._panning = True
        self._pan_start_x = event.x
        self._pan_start_y = event.y
        self._canvas.config(cursor="fleur")

    def _on_middle_drag(self, event: tk.Event) -> None:
        """Handle middle mouse drag for panning."""
        if self._panning and self._pan_start_x is not None:
            dx = event.x - self._pan_start_x
            dy = event.y - self._pan_start_y

            # Move everything
            self._canvas.move("all", dx, dy)

            # Update all node and port positions
            for node in self._nodes.values():
                node.x += dx
                node.y += dy
                for port in node.ports.values():
                    port.x += dx
                    port.y += dy

            self._pan_start_x = event.x
            self._pan_start_y = event.y

    def _on_middle_release(self, event: tk.Event) -> None:
        """Handle middle mouse button release."""
        self._panning = False
        self._pan_start_x = None
        self._pan_start_y = None
        self._canvas.config(cursor="")

    def _on_right_click(self, event: tk.Event) -> None:
        """Handle right-click for context menu.

        Args:
            event: Mouse event
        """
        # Check if clicked on a connection
        clicked_items = self._canvas.find_overlapping(
            event.x - 5, event.y - 5,
            event.x + 5, event.y + 5
        )

        for item in clicked_items:
            tags = self._canvas.gettags(item)
            if "connection" in tags:
                # Show delete option for connection
                menu = tk.Menu(self._canvas, tearoff=0)
                menu.add_command(
                    label="Delete Connection",
                    command=lambda: self._delete_connection_by_tags(tags)
                )
                menu.add_command(
                    label="Test Connection",
                    command=lambda: self._test_connection_by_tags(tags)
                )
                menu.post(event.x_root, event.y_root)
                return

    def _delete_connection_by_tags(self, tags: Tuple[str, ...]) -> None:
        """Delete a connection by its canvas tags.

        Args:
            tags: Canvas item tags
        """
        # Parse tags to get connection info
        # Format: ("connection", "source_id_source_port", "target_id_target_port")
        if len(tags) < 3:
            return

        # Find matching connection
        for conn_key, line_id in list(self._connection_lines.items()):
            source_id, source_port, target_id, target_port = conn_key
            expected_tag1 = f"{source_id}_{source_port}"
            expected_tag2 = f"{target_id}_{target_port}"

            if expected_tag1 in tags and expected_tag2 in tags:
                # Remove from registry
                if self._registry:
                    # Find and remove from connections list
                    for i, conn in enumerate(self._registry._connections):
                        if (conn.source_id == source_id and
                            conn.source_output == source_port and
                            conn.target_id == target_id and
                                conn.target_input == target_port):

                            # Remove from callback list
                            source_obj = self._registry._objects[source_id]
                            target_obj = self._registry._objects[target_id]
                            callback_list = getattr(source_obj, source_port)
                            target_method = getattr(target_obj, target_port)

                            if target_method in callback_list:
                                callback_list.remove(target_method)

                            # Remove from connections list
                            self._registry._connections.pop(i)
                            break

                # Remove from canvas
                self._canvas.delete(line_id)
                del self._connection_lines[conn_key]

                self._status_var.set(f"✓ Deleted connection {source_id}.{source_port} → {target_id}.{target_port}")
                return

    def _test_connection_by_tags(self, tags: Tuple[str, ...]) -> None:
        """Test a connection by triggering its source.

        Args:
            tags: Canvas item tags
        """
        # Find matching connection
        for conn_key in self._connection_lines.keys():
            source_id, source_port, target_id, target_port = conn_key
            expected_tag1 = f"{source_id}_{source_port}"
            expected_tag2 = f"{target_id}_{target_port}"

            if expected_tag1 in tags and expected_tag2 in tags:
                # Test the connection by calling all callbacks
                if self._registry:
                    source_obj = self._registry._objects[source_id]
                    callback_list = getattr(source_obj, source_port, [])

                    if callback_list:
                        for callback in callback_list:
                            try:
                                callback()
                                self._status_var.set(f"✓ Tested connection - callback executed successfully")
                            except Exception as e:
                                self._status_var.set(f"❌ Test failed: {str(e)}")
                    else:
                        self._status_var.set(f"⚠️ No callbacks found for {source_port}")
                return

    def _on_mousewheel(self, event: tk.Event) -> None:
        """Handle mouse wheel for zooming."""
        # TODO: Implement zoom functionality
        pass

    def _on_delete(self, event: tk.Event) -> None:
        """Handle delete key press."""
        # TODO: Implement deleting selected connections
        pass

    def reload_scene(self) -> None:
        """Reload the current scene."""
        if self._scene:
            self.load_scene(self._scene, self._registry)

    def auto_layout(self) -> None:
        """Automatically layout nodes in a grid."""
        if not self._nodes:
            return

        # Simple grid layout
        x, y = 50, 50
        for node in self._nodes.values():
            # Calculate movement delta
            dx = x - node.x
            dy = y - node.y

            # Move node
            for item in self._canvas.find_withtag(node.obj_id):
                self._canvas.move(item, dx, dy)

            # Update positions
            node.x = x
            node.y = y
            for port in node.ports.values():
                port.x += dx
                port.y += dy

            # Next position
            x += 250
            if x > 800:
                x = 50
                y += 200

        # Redraw all connections
        if self._connection_lines:
            for conn_key in list(self._connection_lines.keys()):
                source_id, source_port, target_id, target_port = conn_key

                # Delete old line
                old_line_id = self._connection_lines.pop(conn_key)
                self._canvas.delete(old_line_id)

                # Draw new line
                self._draw_connection(source_id, source_port, target_id, target_port)

        self._status_var.set("✓ Auto-layout applied")

    def clear_all_connections(self) -> None:
        """Clear all connections."""
        result = messagebox.askyesno(
            "Clear All Connections",
            "Are you sure you want to delete all connections?"
        )

        if result and self._registry:
            # Clear from registry
            for conn in list(self._registry._connections):
                source_obj = self._registry._objects.get(conn.source_id)
                target_obj = self._registry._objects.get(conn.target_id)

                if source_obj and target_obj:
                    callback_list = getattr(source_obj, conn.source_output, [])
                    target_method = getattr(target_obj, conn.target_input, None)

                    if target_method and target_method in callback_list:
                        callback_list.remove(target_method)

            self._registry._connections.clear()

            # Clear from canvas - delete all connection items
            self._canvas.delete("connection")

            # Clear the dictionary
            self._connection_lines.clear()

            # Force canvas update
            self._canvas.update_idletasks()

            self._status_var.set("✓ All connections cleared")

    def test_all_connections(self) -> None:
        """Test all connections by displaying their status."""
        if not self._registry or not self._registry._connections:
            messagebox.showinfo("Test Connections", "No connections to test")
            return

        results = []
        for conn in self._registry._connections:
            source_obj = self._registry._objects.get(conn.source_id)
            target_obj = self._registry._objects.get(conn.target_id)

            if source_obj and target_obj:
                # Check if connection is valid
                callback_list = getattr(source_obj, conn.source_output, None)
                target_method = getattr(target_obj, conn.target_input, None)

                if callback_list is not None and target_method is not None:
                    if target_method in callback_list:
                        results.append(f"✓ {conn.source_id}.{conn.source_output} → {conn.target_id}.{conn.target_input}")
                    else:
                        results.append(f"❌ {conn.source_id}.{conn.source_output} → {conn.target_id}.{conn.target_input} (not wired)")
                else:
                    results.append(f"❌ {conn.source_id}.{conn.source_output} → {conn.target_id}.{conn.target_input} (invalid)")
            else:
                results.append(f"❌ {conn.source_id}.{conn.source_output} → {conn.target_id}.{conn.target_input} (object missing)")

        messagebox.showinfo(
            "Connection Test Results",
            "\n".join(results)
        )

    def save_connections(self) -> None:
        """Save connections to the scene."""
        if self._registry and self._scene:
            # Update scene's connection registry
            self._scene.connection_registry = self._registry
            self._status_var.set("✓ Connections saved to scene")
        else:
            self._status_var.set("❌ No scene or registry to save")

    def zoom_in(self) -> None:
        """Zoom in the canvas."""
        # TODO: Implement zoom
        self._status_var.set("Zoom in (not yet implemented)")

    def zoom_out(self) -> None:
        """Zoom out the canvas."""
        # TODO: Implement zoom
        self._status_var.set("Zoom out (not yet implemented)")

    def reset_view(self) -> None:
        """Reset the view to default position and zoom."""
        self.auto_layout()


def create_demo_window():
    """Create a demo window showing the ConnectionEditor in action."""
    root = tk.Tk()
    root.title("Pyrox Connection Editor Demo")
    root.geometry("1200x800")
    root.configure(bg="#2b2b2b")

    # Create a demo scene
    from pyrox.models.scene import Scene, SceneObject
    from pyrox.models.physics import BasePhysicsBody
    from pyrox.models.physics.sensor import ProximitySensorBody
    from pyrox.models.physics.conveyor import ConveyorBody

    scene = Scene(name="Demo Scene")

    # Create some objects
    sensor1 = SceneObject(
        name="Checkpoint 1",
        scene_object_type="Sensor",
        physics_body=ProximitySensorBody.create_checkpoint_sensor(x=0, y=0, name="Checkpoint 1")
    )

    sensor2 = SceneObject(
        name="Checkpoint 2",
        scene_object_type="Sensor",
        physics_body=ProximitySensorBody.create_checkpoint_sensor(x=100, y=0, name="Checkpoint 2")
    )

    conveyor1 = SceneObject(
        name="Conveyor 1",
        scene_object_type="Conveyor",
        physics_body=ConveyorBody(name="Conveyor 1", x=0, y=50, width=200, height=20, belt_speed=2.0)
    )

    conveyor2 = SceneObject(
        name="Conveyor 2",
        scene_object_type="Conveyor",
        physics_body=ConveyorBody(name="Conveyor 2", x=0, y=100, width=200, height=20, belt_speed=2.0)
    )

    # Add to scene
    scene.add_scene_object(sensor1)
    scene.add_scene_object(sensor2)
    scene.add_scene_object(conveyor1)
    scene.add_scene_object(conveyor2)

    # Create connection registry - register physics bodies (not SceneObjects)
    # The physics bodies have the actual callback lists and methods
    registry = ConnectionRegistry()
    for obj_id, obj in scene.scene_objects.items():
        registry.register_object(obj_id, obj.physics_body)

    # Create connection editor
    editor = ConnectionEditor(
        root,
        scene=scene,
        connection_registry=registry
    )
    editor.pack(fill=tk.BOTH, expand=True)

    root.mainloop()


if __name__ == "__main__":
    create_demo_window()

"""
Connection Editor Widget for Pyrox applications.

This module provides a visual node-based editor for creating and managing
connections between scene objects. Displays objects as nodes with input/output
ports and allows drawing connections between them.

Usage:
    As an embedded widget:
        >>> from pyrox.models.gui.connectioneditor import ConnectionEditor
        >>> editor = ConnectionEditor(parent=parent_widget, scene=my_scene)

    As a standalone demo:
        >>> python pyrox/models/gui/connectioneditor.py
"""
from __future__ import annotations

import sys
from typing import Optional, Dict, Tuple, Any
from dataclasses import dataclass, field

from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QPen, QBrush, QColor, QPainterPath, QFont, QPainter,
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QGraphicsView, QGraphicsScene,
    QGraphicsLineItem, QMessageBox,
    QSizePolicy, QMainWindow,
)

from pyrox.models.gui.contextmenu import PyroxContextMenu, MenuItem

from pyrox.interfaces import IScene, ISceneObject
from pyrox.models.connection import ConnectionRegistry

# Integer keys for QGraphicsItem.setData() / .data()
_ROLE_ITEM_TYPE = int(Qt.ItemDataRole.UserRole)        # str: 'port' | 'node' | 'connection' | 'label'
_ROLE_OBJ_ID = int(Qt.ItemDataRole.UserRole) + 1    # str: obj_id
_ROLE_PORT_NAME = int(Qt.ItemDataRole.UserRole) + 2    # str: port name
_ROLE_IS_OUTPUT = int(Qt.ItemDataRole.UserRole) + 3    # bool
_ROLE_CONN_KEY = int(Qt.ItemDataRole.UserRole) + 4    # Tuple[str, str, str, str]


@dataclass
class NodePort:
    """Represents an input or output port on a node."""

    name: str
    is_output: bool
    x: float  # absolute scene x (centre of port ellipse)
    y: float  # absolute scene y
    item: Any = None  # QGraphicsEllipseItem


@dataclass
class VisualNode:
    """Represents a visual node on the canvas."""

    obj_id: str
    scene_obj: ISceneObject
    x: float
    y: float
    width: float = 200.0
    height: float = 100.0
    rect_item: Any = None   # QGraphicsRectItem
    text_item: Any = None   # QGraphicsTextItem
    all_items: list = field(default_factory=list)  # every scene item owned by this node
    ports: Dict[str, NodePort] = field(default_factory=dict)


class _CanvasView(QGraphicsView):
    """Internal QGraphicsView that delegates all events to the owning ConnectionEditor."""

    def __init__(self, editor: 'ConnectionEditor') -> None:
        super().__init__()
        self._editor = editor
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def mousePressEvent(self, event) -> None:
        self._editor._on_mouse_press(event)

    def mouseMoveEvent(self, event) -> None:
        self._editor._on_mouse_move(event)

    def mouseReleaseEvent(self, event) -> None:
        self._editor._on_mouse_release(event)

    def wheelEvent(self, event) -> None:
        self._editor._on_wheel(event)

    def contextMenuEvent(self, event) -> None:
        self._editor._on_context_menu(event)

    def keyPressEvent(self, event) -> None:
        self._editor._on_key_press(event)


class ConnectionEditor(QWidget):
    """
    A visual connection editor for wiring scene objects together.

    Features:
    - Node-based visual representation of scene objects
    - Visual ports for inputs and outputs
    - Drag-and-drop connection creation
    - Connection deletion via right-click context menu
    - Pan (middle-click drag) and zoom (scroll wheel / toolbar buttons)
    - Test connections
    - Auto-layout nodes

    Args:
        parent: Parent widget
        scene: Scene containing objects to connect
        connection_registry: Registry managing the connections
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        scene: Optional[IScene] = None,
        connection_registry: Optional[ConnectionRegistry] = None,
    ) -> None:
        super().__init__(parent)

        # Domain state
        self._scene: Optional[IScene] = scene
        self._registry: Optional[ConnectionRegistry] = connection_registry
        self._nodes: Dict[str, VisualNode] = {}
        self._connection_lines: Dict[Tuple[str, str, str, str], Any] = {}  # -> QGraphicsPathItem

        # Interaction state
        self._dragging_node: Optional[str] = None
        self._drag_start: Optional[QPointF] = None
        self._connecting: bool = False
        self._connection_start_port: Optional[Tuple[str, str, bool]] = None  # (obj_id, port_name, is_output)
        self._temp_connection_line: Optional[QGraphicsLineItem] = None

        # Panning state
        self._panning: bool = False
        self._pan_start: Optional[QPointF] = None

        # Visual palette
        self._node_color = QColor("#4a9eff")
        self._node_border = QColor("#2c5aa0")
        self._output_port_color = QColor("#ff6600")
        self._input_port_color = QColor("#6600ff")
        self._connection_color = QColor("#ffaa00")

        self._build_ui()

        if self._scene:
            self.load_scene(self._scene, self._registry)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_toolbar())
        layout.addWidget(self._make_hsep())

        self._gscene = QGraphicsScene(self)
        self._gscene.setBackgroundBrush(QBrush(QColor("#2b2b2b")))

        self._view = _CanvasView(self)
        self._view.setScene(self._gscene)
        self._view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._view, stretch=1)

        layout.addWidget(self._make_hsep())

        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("padding: 2px 6px;")
        layout.addWidget(self._status_label)

    def _build_toolbar(self) -> QWidget:
        toolbar = QWidget()
        h = QHBoxLayout(toolbar)
        h.setContentsMargins(5, 5, 5, 5)
        h.setSpacing(2)

        for text, slot in (
            ("🔄 Reload",      self.reload_scene),
            ("🎯 Auto Layout", self.auto_layout),
            ("🧹 Clear All",   self.clear_all_connections),
        ):
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            h.addWidget(btn)

        h.addWidget(self._make_vsep())

        for text, slot in (
            ("✓ Test All", self.test_all_connections),
            ("💾 Save",    self.save_connections),
        ):
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            h.addWidget(btn)

        h.addWidget(self._make_vsep())
        h.addWidget(QLabel("Zoom:"))

        for text, slot, width in (
            ("➕",    self.zoom_in,    40),
            ("➖",    self.zoom_out,   40),
            ("Reset", self.reset_view, 55),
        ):
            btn = QPushButton(text)
            btn.setFixedWidth(width)
            btn.clicked.connect(slot)
            h.addWidget(btn)

        h.addStretch()
        return toolbar

    @staticmethod
    def _make_hsep() -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.Shape.HLine)
        f.setFrameShadow(QFrame.Shadow.Sunken)
        return f

    @staticmethod
    def _make_vsep() -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.Shape.VLine)
        f.setFrameShadow(QFrame.Shadow.Sunken)
        return f

    # ------------------------------------------------------------------
    # Scene loading
    # ------------------------------------------------------------------

    def load_scene(
        self,
        scene: IScene,
        connection_registry: Optional[ConnectionRegistry] = None,
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

        self._gscene.clear()
        self._nodes.clear()
        self._connection_lines.clear()

        x, y = 50.0, 50.0
        for obj_id, scene_obj in scene.scene_objects.items():
            self._create_node(obj_id, scene_obj, x, y)

            if self._registry and obj_id not in self._registry._objects:
                self._registry.register_object(obj_id, scene_obj.physics_body)

            x += 250
            if x > 800:
                x = 50
                y += 150

        self._draw_existing_connections()
        self._set_status(f"Loaded {len(self._nodes)} objects")

    def _create_node(
        self,
        obj_id: str,
        scene_obj: ISceneObject,
        x: float,
        y: float,
    ) -> None:
        """Create a visual node for a scene object.

        Args:
            obj_id: Object ID
            scene_obj: Scene object
            x: X position in scene coordinates
            y: Y position in scene coordinates
        """
        outputs = scene_obj.physics_body.get_outputs()
        inputs = scene_obj.physics_body.get_inputs()

        port_spacing = 25.0
        max_ports = max(len(outputs), len(inputs), 1)
        height = max(100.0, 60.0 + max_ports * port_spacing)

        node = VisualNode(obj_id=obj_id, scene_obj=scene_obj, x=x, y=y, height=height)

        # Background rectangle
        rect_item = self._gscene.addRect(
            QRectF(x, y, node.width, height),
            QPen(self._node_border, 2),
            QBrush(self._node_color),
        )

        if rect_item is None:
            raise RuntimeError("Failed to create node rectangle item")

        rect_item.setData(_ROLE_ITEM_TYPE, 'node')
        rect_item.setData(_ROLE_OBJ_ID, obj_id)
        node.rect_item = rect_item
        node.all_items.append(rect_item)

        # Title label
        font = QFont("Arial", 10, QFont.Weight.Bold)
        text_item = self._gscene.addText(scene_obj.name, font)

        if text_item is None:
            raise RuntimeError("Failed to create node text item")

        text_item.setDefaultTextColor(QColor("white"))
        text_item.setPos(
            x + node.width / 2 - text_item.boundingRect().width() / 2,
            y + 10,
        )
        text_item.setData(_ROLE_ITEM_TYPE, 'label')
        text_item.setData(_ROLE_OBJ_ID, obj_id)
        node.text_item = text_item
        node.all_items.append(text_item)

        small_font = QFont("Arial", 8)

        # Output ports (right side)
        port_y = y + 50.0
        for output_name in outputs.keys():
            self._add_port(node, output_name, True, x + node.width, port_y, small_font)
            port_y += port_spacing

        # Input ports (left side)
        port_y = y + 50.0
        for input_name in inputs.keys():
            self._add_port(node, input_name, False, x, port_y, small_font)
            port_y += port_spacing

        self._nodes[obj_id] = node

    def _add_port(
        self,
        node: VisualNode,
        name: str,
        is_output: bool,
        cx: float,
        cy: float,
        font: QFont,
    ) -> None:
        """Add a port ellipse and its label to a node."""
        r = 8.0
        color = self._output_port_color if is_output else self._input_port_color

        ellipse = self._gscene.addEllipse(
            QRectF(cx - r, cy - r, r * 2, r * 2),
            QPen(QColor("white"), 2),
            QBrush(color),
        )

        if ellipse is None:
            raise RuntimeError("Failed to create port ellipse item")

        ellipse.setData(_ROLE_ITEM_TYPE, 'port')
        ellipse.setData(_ROLE_OBJ_ID, node.obj_id)
        ellipse.setData(_ROLE_PORT_NAME, name)
        ellipse.setData(_ROLE_IS_OUTPUT, is_output)
        node.all_items.append(ellipse)

        label_text = name.replace("_callbacks", "").replace("on_", "") if is_output else name
        label_item = self._gscene.addText(label_text, font)

        if label_item is None:
            raise RuntimeError("Failed to create port label item")

        label_item.setDefaultTextColor(QColor("white"))
        lw = label_item.boundingRect().width()
        lh = label_item.boundingRect().height()
        label_item.setPos(
            (cx - r - lw - 4) if is_output else (cx + r + 4),
            cy - lh / 2,
        )
        label_item.setData(_ROLE_ITEM_TYPE, 'label')
        label_item.setData(_ROLE_OBJ_ID, node.obj_id)
        node.all_items.append(label_item)

        node.ports[name] = NodePort(name=name, is_output=is_output, x=cx, y=cy, item=ellipse)

    # ------------------------------------------------------------------
    # Connection drawing
    # ------------------------------------------------------------------

    def _draw_existing_connections(self) -> None:
        """Draw all existing connections from the registry."""
        if not self._registry:
            return
        for conn in self._registry._connections:
            self._draw_connection(
                conn.source_id, conn.source_output,
                conn.target_id, conn.target_input,
            )

    def _draw_connection(
        self,
        source_id: str,
        source_port: str,
        target_id: str,
        target_port: str,
    ) -> bool:
        """Draw a bezier curve between two ports.

        Args:
            source_id: Source object ID
            source_port: Source output port name
            target_id: Target object ID
            target_port: Target input port name

        Returns:
            True if the connection was drawn successfully, False otherwise
        """
        sn = self._nodes.get(source_id)
        tn = self._nodes.get(target_id)

        if not sn:
            print(f"Warning: Source node {source_id} not found")
            return False
        if not tn:
            print(f"Warning: Target node {target_id} not found")
            return False

        sp = sn.ports.get(source_port)
        tp = tn.ports.get(target_port)

        if not sp:
            print(f"Warning: Source port {source_port} not found on {source_id}")
            print(f"Available ports: {list(sn.ports.keys())}")
            return False
        if not tp:
            print(f"Warning: Target port {target_port} not found on {target_id}")
            print(f"Available ports: {list(tn.ports.keys())}")
            return False

        x1, y1 = sp.x, sp.y
        x2, y2 = tp.x, tp.y
        cx1, cy1 = x1 + 50, y1
        cx2, cy2 = x2 - 50, y2

        path = QPainterPath()
        path.moveTo(x1, y1)
        path.cubicTo(cx1, cy1, cx2, cy2, x2, y2)

        path_item = self._gscene.addPath(path, QPen(self._connection_color, 3))
        if path_item is None:
            raise RuntimeError("Failed to create connection path item")

        path_item.setZValue(-1)  # render behind nodes

        conn_key: Tuple[str, str, str, str] = (source_id, source_port, target_id, target_port)
        path_item.setData(_ROLE_ITEM_TYPE, 'connection')
        path_item.setData(_ROLE_CONN_KEY, conn_key)

        self._connection_lines[conn_key] = path_item
        return True

    # ------------------------------------------------------------------
    # Event handlers (delegated from _CanvasView)
    # ------------------------------------------------------------------

    def _items_at(self, scene_pos: QPointF):
        """Return scene items within ±5 px of scene_pos."""
        return self._gscene.items(
            QRectF(scene_pos.x() - 5, scene_pos.y() - 5, 10, 10)
        )

    def _on_mouse_press(self, event) -> None:
        scene_pos = self._view.mapToScene(event.position().toPoint())
        btn = event.button()

        if btn == Qt.MouseButton.LeftButton:
            # Port click → start wiring
            for item in self._items_at(scene_pos):
                if item.data(_ROLE_ITEM_TYPE) == 'port':
                    self._connection_start_port = (
                        item.data(_ROLE_OBJ_ID),
                        item.data(_ROLE_PORT_NAME),
                        item.data(_ROLE_IS_OUTPUT),
                    )
                    self._connecting = True
                    obj_id, port_nm, _ = self._connection_start_port
                    self._set_status(f"Connecting from {obj_id}.{port_nm}...")
                    return

            # Node click → start dragging
            for item in self._items_at(scene_pos):
                if item.data(_ROLE_ITEM_TYPE) == 'node':
                    obj_id = item.data(_ROLE_OBJ_ID)
                    if obj_id in self._nodes:
                        self._dragging_node = obj_id
                        self._drag_start = scene_pos
                        return

        elif btn == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            self._view.setCursor(Qt.CursorShape.SizeAllCursor)

    def _on_mouse_move(self, event) -> None:
        scene_pos = self._view.mapToScene(event.position().toPoint())

        if self._connecting and self._connection_start_port:
            # Rubber-band line from source port to cursor
            if self._temp_connection_line:
                self._gscene.removeItem(self._temp_connection_line)
                self._temp_connection_line = None

            source_node = self._nodes[self._connection_start_port[0]]
            sp = source_node.ports[self._connection_start_port[1]]
            self._temp_connection_line = self._gscene.addLine(
                sp.x, sp.y, scene_pos.x(), scene_pos.y(),
                QPen(self._connection_color, 2, Qt.PenStyle.DashLine),
            )

        elif self._dragging_node and self._drag_start is not None:
            dx = scene_pos.x() - self._drag_start.x()
            dy = scene_pos.y() - self._drag_start.y()
            node = self._nodes[self._dragging_node]

            for item in node.all_items:
                item.moveBy(dx, dy)

            node.x += dx
            node.y += dy
            for port in node.ports.values():
                port.x += dx
                port.y += dy

            self._drag_start = scene_pos
            self._redraw_node_connections(self._dragging_node)

        elif self._panning and self._pan_start is not None:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            hbar = self._view.horizontalScrollBar()
            vbar = self._view.verticalScrollBar()
            if not hbar or not vbar:
                raise RuntimeError("Scroll bars not found on view")

            hbar.setValue(
                hbar.value() - int(delta.x())
            )
            vbar.setValue(
                vbar.value() - int(delta.y())
            )

    def _on_mouse_release(self, event) -> None:
        scene_pos = self._view.mapToScene(event.position().toPoint())
        btn = event.button()

        if btn == Qt.MouseButton.LeftButton:
            if self._connecting and self._connection_start_port:
                for item in self._items_at(scene_pos):
                    if item.data(_ROLE_ITEM_TYPE) == 'port':
                        target_obj_id = item.data(_ROLE_OBJ_ID)
                        target_port_nm = item.data(_ROLE_PORT_NAME)
                        is_output = item.data(_ROLE_IS_OUTPUT)

                        src_obj, src_port, src_is_out = self._connection_start_port

                        if src_is_out != is_output:
                            if src_is_out:
                                self._create_connection(src_obj, src_port, target_obj_id, target_port_nm)
                            else:
                                self._create_connection(target_obj_id, target_port_nm, src_obj, src_port)
                        else:
                            self._set_status("❌ Cannot connect ports of the same type!")
                        break

                if self._temp_connection_line:
                    self._gscene.removeItem(self._temp_connection_line)
                    self._temp_connection_line = None

                self._connecting = False
                self._connection_start_port = None
                self._set_status("Ready")

            self._dragging_node = None
            self._drag_start = None

        elif btn == Qt.MouseButton.MiddleButton:
            self._panning = False
            self._pan_start = None
            self._view.setCursor(Qt.CursorShape.ArrowCursor)

    def _on_wheel(self, event) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self._view.scale(factor, factor)

    def _on_context_menu(self, event) -> None:
        scene_pos = self._view.mapToScene(event.pos())
        for item in self._items_at(scene_pos):
            if item.data(_ROLE_ITEM_TYPE) == 'connection':
                conn_key = item.data(_ROLE_CONN_KEY)
                menu = PyroxContextMenu(self._view)
                menu.add_item(MenuItem(
                    id='delete',
                    label='Delete Connection',
                    command=lambda k=conn_key: self._delete_connection(k),
                    icon='🗑',
                ))
                menu.add_item(MenuItem(
                    id='test',
                    label='Test Connection',
                    command=lambda k=conn_key: self._test_connection(k),
                    icon='✓',
                ))
                menu.show_at_event(event)
                return

    def _on_key_press(self, event) -> None:
        if event.key() == Qt.Key.Key_Delete:
            # TODO: delete selected connection
            pass

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _create_connection(
        self,
        source_id: str,
        source_port: str,
        target_id: str,
        target_port: str,
    ) -> None:
        """Create a new connection between two ports.

        Args:
            source_id: Source object ID
            source_port: Source output port name
            target_id: Target object ID
            target_port: Target input port name
        """
        conn_key = (source_id, source_port, target_id, target_port)
        if conn_key in self._connection_lines:
            self._set_status("⚠️ Connection already exists!")
            return

        if self._registry:
            try:
                self._registry.connect(source_id, source_port, target_id, target_port)
                success = self._draw_connection(source_id, source_port, target_id, target_port)
                if success:
                    self._set_status(
                        f"✓ Connected {source_id}.{source_port} → {target_id}.{target_port}"
                    )
                else:
                    self._set_status("❌ Failed to draw connection - check console for details")
            except Exception as e:
                self._set_status(f"❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()

    def _redraw_node_connections(self, obj_id: str) -> None:
        """Redraw all connections that involve a given node (called after drag).

        Args:
            obj_id: Object ID of the moved node
        """
        to_redraw = [k for k in self._connection_lines if k[0] == obj_id or k[2] == obj_id]
        for conn_key in to_redraw:
            old_item = self._connection_lines.pop(conn_key)
            self._gscene.removeItem(old_item)
            self._draw_connection(*conn_key)

    def _delete_connection(self, conn_key: Tuple[str, str, str, str]) -> None:
        """Remove a connection from the registry and the canvas.

        Args:
            conn_key: (source_id, source_port, target_id, target_port)
        """
        source_id, source_port, target_id, target_port = conn_key

        if self._registry:
            for _, conn in enumerate(self._registry._connections):
                if (conn.source_id == source_id
                        and conn.source_output == source_port
                        and conn.target_id == target_id
                        and conn.target_input == target_port):
                    self._registry.disconnect(source_id, source_port, target_id, target_port)
                    break

        item = self._connection_lines.pop(conn_key, None)
        if item:
            self._gscene.removeItem(item)

        self._set_status(
            f"✓ Deleted connection {source_id}.{source_port} → {target_id}.{target_port}"
        )

    def _test_connection(self, conn_key: Tuple[str, str, str, str]) -> None:
        """Test a connection by firing all its source callbacks.

        Args:
            conn_key: (source_id, source_port, target_id, target_port)
        """
        source_id, source_port, _, _ = conn_key
        if self._registry:
            src_obj = self._registry._objects.get(source_id)
            if src_obj:
                cb_list = getattr(src_obj, source_port, [])
                if cb_list:
                    for cb in cb_list:
                        try:
                            cb()
                            self._set_status("✓ Tested connection - callback executed successfully")
                        except Exception as e:
                            self._set_status(f"❌ Test failed: {str(e)}")
                else:
                    self._set_status(f"⚠️ No callbacks found for {source_port}")

    # ------------------------------------------------------------------
    # Toolbar actions
    # ------------------------------------------------------------------

    def reload_scene(self) -> None:
        """Reload the current scene."""
        if self._scene:
            self.load_scene(self._scene, self._registry)

    def auto_layout(self) -> None:
        """Automatically arrange nodes in a grid."""
        if not self._nodes:
            return

        x, y = 50.0, 50.0
        for node in self._nodes.values():
            dx = x - node.x
            dy = y - node.y

            for item in node.all_items:
                item.moveBy(dx, dy)

            node.x = x
            node.y = y
            for port in node.ports.values():
                port.x += dx
                port.y += dy

            x += 250
            if x > 800:
                x = 50
                y += 200

        # Redraw all connections at updated positions
        all_keys = list(self._connection_lines.keys())
        for conn_key in all_keys:
            old_item = self._connection_lines.pop(conn_key)
            self._gscene.removeItem(old_item)
            self._draw_connection(*conn_key)

        self._set_status("✓ Auto-layout applied")

    def clear_all_connections(self) -> None:
        """Delete all connections after user confirmation."""
        if QMessageBox.question(
            self,
            "Clear All Connections",
            "Are you sure you want to delete all connections?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return

        if self._registry:
            for conn in list(self._registry._connections):
                src_obj = self._registry._objects.get(conn.source_id)
                tgt_obj = self._registry._objects.get(conn.target_id)
                if src_obj and tgt_obj:
                    cb_list = getattr(src_obj, conn.source_output, [])
                    tgt_method = getattr(tgt_obj, conn.target_input, None)
                    if tgt_method and tgt_method in cb_list:
                        cb_list.remove(tgt_method)
            self._registry._connections.clear()

        for item in self._connection_lines.values():
            self._gscene.removeItem(item)
        self._connection_lines.clear()

        self._set_status("✓ All connections cleared")

    def test_all_connections(self) -> None:
        """Validate all connections and display a results dialog."""
        if not self._registry or not self._registry._connections:
            QMessageBox.information(self, "Test Connections", "No connections to test")
            return

        results = []
        for conn in self._registry._connections:
            src_obj = self._registry._objects.get(conn.source_id)
            tgt_obj = self._registry._objects.get(conn.target_id)
            tag = f"{conn.source_id}.{conn.source_output} → {conn.target_id}.{conn.target_input}"

            if src_obj and tgt_obj:
                cb_list = getattr(src_obj, conn.source_output, None)
                tgt_method = getattr(tgt_obj, conn.target_input,  None)
                if cb_list is not None and tgt_method is not None:
                    results.append(("✓ " if tgt_method in cb_list else "❌ (not wired) ") + tag)
                else:
                    results.append(f"❌ (invalid) {tag}")
            else:
                results.append(f"❌ (object missing) {tag}")

        QMessageBox.information(self, "Connection Test Results", "\n".join(results))

    def save_connections(self) -> None:
        """Save connections back to the scene."""
        if self._registry and self._scene:
            self._scene.set_connection_registry(self._registry)
            self._set_status("✓ Connections saved to scene")
        else:
            self._set_status("❌ No scene or registry to save")

    def zoom_in(self) -> None:
        """Zoom in the canvas."""
        self._view.scale(1.2, 1.2)

    def zoom_out(self) -> None:
        """Zoom out the canvas."""
        self._view.scale(1 / 1.2, 1 / 1.2)

    def reset_view(self) -> None:
        """Reset zoom/pan and re-apply auto-layout."""
        self._view.resetTransform()
        self.auto_layout()

    def _set_status(self, message: str) -> None:
        self._status_label.setText(message)


def create_demo_window() -> QMainWindow:
    """Create a demo QMainWindow containing a ConnectionEditor with sample objects."""
    from pyrox.models.scene import Scene, SceneObject
    from pyrox.models.physics.sensor import ProximitySensorBody
    from pyrox.models.physics.conveyor import ConveyorBody

    scene = Scene(name="Demo Scene")

    for name, obj_type, body in (
        ("Checkpoint 1", "Sensor",
         ProximitySensorBody.create_checkpoint_sensor(x=0,   y=0,   name="Checkpoint 1")),
        ("Checkpoint 2", "Sensor",
         ProximitySensorBody.create_checkpoint_sensor(x=100, y=0,   name="Checkpoint 2")),
        ("Conveyor 1",   "Conveyor",
         ConveyorBody(name="Conveyor 1", x=0, y=50,  width=200, height=20, belt_speed=2.0)),
        ("Conveyor 2",   "Conveyor",
         ConveyorBody(name="Conveyor 2", x=0, y=100, width=200, height=20, belt_speed=2.0)),
    ):
        scene.add_scene_object(SceneObject(name=name, scene_object_type=obj_type, physics_body=body))

    registry = ConnectionRegistry()
    for obj_id, obj in scene.scene_objects.items():
        registry.register_object(obj_id, obj.physics_body)

    window = QMainWindow()
    window.setWindowTitle("Pyrox Connection Editor Demo")
    window.resize(1200, 800)
    window.setCentralWidget(ConnectionEditor(scene=scene, connection_registry=registry))
    return window


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = create_demo_window()
    window.show()
    sys.exit(app.exec())

"""Unit tests for SceneViewerFrame and _SceneCanvasView.

PyQt6 is mocked out entirely at sys.modules level **before** any pyrox/Qt
import, so no display server, Qt application instance, or GUI is needed.

Test strategy
─────────────
* Business-logic methods (coordinate conversion, viewport culling, scene
  management, selection, deletion, render loop, context actions) are tested
  on a ``SceneViewerFrame`` instance whose ``__init__`` is bypassed via
  ``object.__new__``.  All Qt/service internals are replaced with
  ``MagicMock`` or lightweight stubs.

* ``_SceneCanvasView`` event routing is tested by creating an instance with
  ``object.__new__`` and injecting a mocked frame.

Never import PyQt6 directly in this file – the stubs installed below are
all that is needed.
"""

import sys
import time
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Install PyQt6 stubs in sys.modules BEFORE any other import that may
# transitively pull in the real PyQt6.  Classes used as base classes in the
# source tree must be genuine Python *types* (not plain MagicMock instances)
# so that class-body inheritance (`class Foo(QWidget)`) succeeds.
# ---------------------------------------------------------------------------


class _QtBase:
    """Minimal stub ancestor for all Qt widget/item stubs."""

    def __init__(self, *args, **kwargs):  # noqa: D401
        pass

    def __getattr__(self, name: str):
        mock = MagicMock()
        object.__setattr__(self, name, mock)
        return mock


def _stub_type(name: str) -> type:
    """Return a new class that inherits from *_QtBase*, usable as a base class."""
    return type(name, (_QtBase,), {})


# Build the three Qt sub-module stubs
_qt_core_mod = MagicMock(name="PyQt6.QtCore")
_qt_gui_mod = MagicMock(name="PyQt6.QtGui")
_qt_widgets_mod = MagicMock(name="PyQt6.QtWidgets")

# Qt enum/flag constants used by comparisons inside sceneviewer.py.
# Using plain integers lets `|` and `==` work just like the real Qt flags.
_Qt = MagicMock(name="Qt")
_Qt.MouseButton.LeftButton = 0x00000001
_Qt.MouseButton.MiddleButton = 0x00000004
_Qt.MouseButton.RightButton = 0x00000002

_Qt.KeyboardModifier.ControlModifier = 0x04000000
_Qt.KeyboardModifier.ShiftModifier = 0x02000000
_Qt.KeyboardModifier.AltModifier = 0x08000000

_Qt.Key.Key_Delete = 16777223
_Qt.Key.Key_Escape = 16777216
_Qt.Key.Key_L = 76
_Qt.Key.Key_G = 71
_Qt.Key.Key_U = 85
_Qt.Key.Key_BracketRight = 93
_Qt.Key.Key_BracketLeft = 91

_Qt.CursorShape.SizeAllCursor = object()
_Qt.CursorShape.ArrowCursor = object()
_Qt.Orientation.Horizontal = 1
_Qt.BrushStyle.NoBrush = 0
_Qt.PenStyle.NoPen = 0
_Qt.AspectRatioMode.IgnoreAspectRatio = 0
_Qt.TransformationMode.SmoothTransformation = 1
_Qt.ScrollBarPolicy.ScrollBarAlwaysOff = 1
_Qt.FocusPolicy.StrongFocus = 1
_Qt.AlignmentFlag = MagicMock()

_qt_core_mod.Qt = _Qt
_qt_core_mod.QRectF = _stub_type("QRectF")
_qt_core_mod.QLineF = _stub_type("QLineF")
_qt_core_mod.QPointF = _stub_type("QPointF")
_qt_core_mod.QTimer = _stub_type("QTimer")

# Widget/item types – must be real types so subclassing works
for _cls_name in (
    "QWidget", "QGraphicsView", "QSplitter", "QVBoxLayout", "QHBoxLayout",
    "QPushButton", "QLabel", "QFrame", "QAbstractScrollArea",
    "QGraphicsEllipseItem", "QGraphicsLineItem", "QGraphicsPixmapItem",
    "QGraphicsRectItem", "QGraphicsScene", "QGraphicsSimpleTextItem",
    "QScrollBar",
):
    setattr(_qt_widgets_mod, _cls_name, _stub_type(_cls_name))

# GUI types
for _cls_name in (
    "QBrush", "QColor", "QPen", "QFont", "QCursor",
    "QContextMenuEvent", "QKeyEvent", "QMouseEvent",
    "QWheelEvent", "QResizeEvent", "QPainter", "QPixmap",
):
    setattr(_qt_gui_mod, _cls_name, _stub_type(_cls_name))

sys.modules.update({
    "PyQt6":            MagicMock(name="PyQt6"),
    "PyQt6.QtCore":     _qt_core_mod,
    "PyQt6.QtGui":      _qt_gui_mod,
    "PyQt6.QtWidgets":  _qt_widgets_mod,
    "PyQt6.sip":        MagicMock(name="PyQt6.sip"),
})

# ---------------------------------------------------------------------------
# Now it is safe to import from pyrox — Qt symbols resolve to our stubs.
# ---------------------------------------------------------------------------
from pyrox.models.gui.sceneviewer.sceneviewer import (  # noqa: E402
    SceneViewerFrame,
    _SceneCanvasView,
)
from pyrox.models.gui.sceneviewer._user_mode import UserMode  # noqa: E402

# Ensure the Qt object used inside sceneviewer.py's module namespace is the
# same stub so all constant comparisons (`btn == Qt.MouseButton.LeftButton`)
# resolve correctly.
import pyrox.models.gui.sceneviewer.sceneviewer as _sv_module  # noqa: E402
_sv_module.Qt = _Qt

# Remove stub entries from sys.modules so that test files collected/executed
# after this one can import the real PyQt6 without getting our mocks.
# The sceneviewer module is already imported above and holds its own references
# to the stub types, so these tests remain unaffected.
for _k in list(sys.modules.keys()):
    if _k == "PyQt6" or _k.startswith("PyQt6."):
        del sys.modules[_k]
del _k

# Convenience aliases matching the values installed above
_CTRL = _Qt.KeyboardModifier.ControlModifier
_SHIFT = _Qt.KeyboardModifier.ShiftModifier
_ALT = _Qt.KeyboardModifier.AltModifier
_CTRL_SHIFT = _CTRL | _SHIFT
_CTRL_ALT = _CTRL | _ALT

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_viewport(x: float = 0.0, y: float = 0.0, zoom: float = 1.0):
    return SimpleNamespace(x=x, y=y, zoom=zoom)


def _make_frame() -> SceneViewerFrame:
    """Return a ``SceneViewerFrame`` whose Qt ``__init__`` has been bypassed.

    All instance attributes are populated with ``MagicMock`` objects or
    sensible default values so that business-logic methods can be exercised
    in isolation.
    """
    frame: SceneViewerFrame = object.__new__(SceneViewerFrame)

    # Viewport service
    vp = _make_viewport()
    vs = MagicMock(name="viewport_service")
    vs.viewport = vp
    vs.needs_render.return_value = False
    vs.grid.snap_to_grid.side_effect = lambda x, y: (x, y)

    # Core state
    frame._scene = None
    frame._runner = None
    frame._gfx_items = {}
    frame._drag_start_x = None
    frame._drag_start_y = None
    frame._is_dragging = False
    frame._object_counter = 0
    frame._clipboard_data = []
    frame._needs_full_render = False
    frame._render_timer = None
    frame._render_interval_ms = 16
    frame._sprite_cache = {}
    frame._sprite_cache_zoom = -1.0
    frame._last_tick_time = time.monotonic()
    frame._entity_names_visible = True
    frame._mode = UserMode.SELECT

    # Services
    frame._viewport_service = vs
    com = MagicMock(name="com_svc")
    com.selected_objects = []
    com.selected_objects_display = ""
    com._selection_color = "#ff0000"
    com._selection_width = 2
    frame._canvas_object_management_service = com

    # Panels
    frame._properties_panel = MagicMock(name="props_panel")
    frame._properties_panel.visible = False
    frame._object_explorer = MagicMock(name="explorer")
    frame._bridge_panel = MagicMock(name="bridge")
    frame._connection_editor_panel = MagicMock(name="conn_editor")
    frame._object_palette = MagicMock(name="palette")
    frame._toolbar = MagicMock(name="toolbar")

    # Canvas
    cv = MagicMock(name="canvas_view")
    cv.width.return_value = 800
    cv.height.return_value = 600
    frame._canvas_view = cv

    gfx = MagicMock(name="gfx_scene")
    gfx.items.return_value = []
    frame._gfx_scene = gfx

    frame._paned_window = MagicMock(name="paned_window")
    frame._canvas_context_menu = MagicMock(name="canvas_ctx")
    frame._object_context_menu = MagicMock(name="obj_ctx")

    return frame


def _make_scene_object(
    obj_id: str = "obj1",
    x: float = 10.0,
    y: float = 20.0,
    w: float = 50.0,
    h: float = 50.0,
    layer: int = 0,
) -> MagicMock:
    obj = MagicMock(name=f"scene_obj:{obj_id}")
    obj.id = obj_id
    obj.x = x
    obj.y = y
    obj.width = w
    obj.height = h
    obj.get_layer.return_value = layer
    obj.get_group_id.return_value = None
    obj.properties = {}
    obj.is_animating = False
    obj.yaw = 0.0
    return obj


def _make_scene(objects: list | None = None) -> MagicMock:
    scene = MagicMock(name="scene")
    scene.scene_objects = {}
    for obj in (objects or []):
        scene.scene_objects[obj.id] = obj
    scene.get_on_scene_updated.return_value = []
    scene.get_scene_object.side_effect = lambda oid: scene.scene_objects.get(oid)
    return scene


def _make_canvas_view(mode: UserMode = UserMode.SELECT) -> tuple[_SceneCanvasView, SceneViewerFrame]:
    """Return a (*view*, *frame*) pair with Qt initialisation bypassed.

    ``_SceneCanvasView.__init__`` is patched out so no real Qt objects are
    created – the required instance attributes are set manually afterwards.
    """
    frame = _make_frame()
    frame._mode = mode

    with patch.object(_SceneCanvasView, "__init__", return_value=None):
        view = _SceneCanvasView(MagicMock(), frame)

    view._frame = frame
    view._is_panning = False
    view._pan_start_x = 0.0
    view._pan_start_y = 0.0
    # Provide a stub setCursor so panning code doesn't error
    view.setCursor = MagicMock()
    return view, frame


def _mouse_event(
    button,
    x: float = 100.0,
    y: float = 100.0,
    buttons=None,
    modifiers: int = 0,
) -> MagicMock:
    event = MagicMock()
    pos = MagicMock()
    pos.x.return_value = x
    pos.y.return_value = y
    event.button.return_value = button
    event.position.return_value = pos
    event.buttons.return_value = buttons if buttons is not None else button
    event.modifiers.return_value = modifiers
    return event


def _key_event(key: int, mods: int = 0) -> MagicMock:
    event = MagicMock()
    event.key.return_value = key
    event.modifiers.return_value = mods
    return event


# ===========================================================================
# Test classes
# ===========================================================================


class TestCoordinateConversion(unittest.TestCase):
    """world_to_canvas / canvas_to_world arithmetic."""

    def setUp(self):
        self.frame = _make_frame()

    def test_world_to_canvas_identity(self):
        """zoom=1, pan=0 → canvas position equals world position."""
        cx, cy = self.frame.world_to_canvas(100.0, 200.0)
        self.assertAlmostEqual(cx, 100.0)
        self.assertAlmostEqual(cy, 200.0)

    def test_world_to_canvas_with_pan(self):
        self.frame._viewport_service.viewport.x = 50.0
        self.frame._viewport_service.viewport.y = -20.0
        cx, cy = self.frame.world_to_canvas(100.0, 200.0)
        self.assertAlmostEqual(cx, 150.0)
        self.assertAlmostEqual(cy, 180.0)

    def test_world_to_canvas_with_zoom(self):
        self.frame._viewport_service.viewport.zoom = 2.0
        cx, cy = self.frame.world_to_canvas(50.0, 75.0)
        self.assertAlmostEqual(cx, 100.0)
        self.assertAlmostEqual(cy, 150.0)

    def test_world_to_canvas_zoom_and_pan_combined(self):
        self.frame._viewport_service.viewport.zoom = 2.0
        self.frame._viewport_service.viewport.x = 10.0
        self.frame._viewport_service.viewport.y = 5.0
        cx, cy = self.frame.world_to_canvas(30.0, 20.0)
        # canvas = world * zoom + pan = 30*2+10, 20*2+5
        self.assertAlmostEqual(cx, 70.0)
        self.assertAlmostEqual(cy, 45.0)

    def test_canvas_to_world_identity(self):
        wx, wy = self.frame.canvas_to_world(100.0, 200.0)
        self.assertAlmostEqual(wx, 100.0)
        self.assertAlmostEqual(wy, 200.0)

    def test_canvas_to_world_with_pan(self):
        self.frame._viewport_service.viewport.x = 50.0
        self.frame._viewport_service.viewport.y = -20.0
        wx, wy = self.frame.canvas_to_world(150.0, 180.0)
        self.assertAlmostEqual(wx, 100.0)
        self.assertAlmostEqual(wy, 200.0)

    def test_canvas_to_world_with_zoom(self):
        self.frame._viewport_service.viewport.zoom = 2.0
        wx, wy = self.frame.canvas_to_world(100.0, 150.0)
        self.assertAlmostEqual(wx, 50.0)
        self.assertAlmostEqual(wy, 75.0)

    def test_round_trip_various_viewports(self):
        """canvas_to_world(world_to_canvas(x, y)) must equal (x, y)."""
        vp = self.frame._viewport_service.viewport
        vp.zoom = 1.5
        vp.x = 30.0
        vp.y = -10.0
        for wx_in, wy_in in [(0, 0), (100, 200), (-50, 75), (999, 1337)]:
            cx, cy = self.frame.world_to_canvas(float(wx_in), float(wy_in))
            wx, wy = self.frame.canvas_to_world(cx, cy)
            self.assertAlmostEqual(wx, wx_in, places=9,
                                   msg=f"round-trip failed for ({wx_in}, {wy_in})")
            self.assertAlmostEqual(wy, wy_in, places=9)

    def test_world_to_canvas_origin_unchanged_at_unit_zoom_no_pan(self):
        cx, cy = self.frame.world_to_canvas(0.0, 0.0)
        self.assertAlmostEqual(cx, 0.0)
        self.assertAlmostEqual(cy, 0.0)


class TestViewportCulling(unittest.TestCase):
    """_is_in_viewport visibility checks."""

    def setUp(self):
        self.frame = _make_frame()

    # _is_in_viewport ---------------------------------------------------------

    def test_object_fully_inside(self):
        obj = _make_scene_object(x=100, y=100, w=50, h=50)
        self.assertTrue(self.frame._is_in_viewport(obj, 0, 0, 500, 500))

    def test_object_fully_right_of_viewport(self):
        obj = _make_scene_object(x=600, y=100, w=50, h=50)
        self.assertFalse(self.frame._is_in_viewport(obj, 0, 0, 500, 500))

    def test_object_fully_left_of_viewport(self):
        # x + width = -100 + 50 = -50 < min_x 0
        obj = _make_scene_object(x=-100, y=100, w=50, h=50)
        self.assertFalse(self.frame._is_in_viewport(obj, 0, 0, 500, 500))

    def test_object_fully_above_viewport(self):
        # y + height = -100 + 50 = -50 < min_y 0
        obj = _make_scene_object(x=100, y=-100, w=50, h=50)
        self.assertFalse(self.frame._is_in_viewport(obj, 0, 0, 500, 500))

    def test_object_fully_below_viewport(self):
        obj = _make_scene_object(x=100, y=600, w=50, h=50)
        self.assertFalse(self.frame._is_in_viewport(obj, 0, 0, 500, 500))

    def test_object_partially_visible_on_right_edge(self):
        # x=480, width=50 → right edge 530 > max_x 500 but left 480 ≤ max_x
        obj = _make_scene_object(x=480, y=100, w=50, h=50)
        self.assertTrue(self.frame._is_in_viewport(obj, 0, 0, 500, 500))

    def test_object_right_edge_exactly_at_min_x(self):
        # x + width = 0 → at boundary, condition x+w >= min_x is True (0 >= 0)
        obj = _make_scene_object(x=-50, y=100, w=50, h=50)
        self.assertTrue(self.frame._is_in_viewport(obj, 0, 0, 500, 500))

    def test_object_just_outside_left(self):
        # x + width = -1 < min_x 0
        obj = _make_scene_object(x=-51, y=100, w=50, h=50)
        self.assertFalse(self.frame._is_in_viewport(obj, 0, 0, 500, 500))

    def test_object_left_edge_exactly_at_max_x(self):
        # x = max_x → condition x <= max_x is True
        obj = _make_scene_object(x=500, y=100, w=50, h=50)
        self.assertTrue(self.frame._is_in_viewport(obj, 0, 0, 500, 500))

    def test_object_just_outside_right(self):
        obj = _make_scene_object(x=501, y=100, w=50, h=50)
        self.assertFalse(self.frame._is_in_viewport(obj, 0, 0, 500, 500))

    # _compute_viewport_bounds -----------------------------------------------

    def test_compute_bounds_default_viewport(self):
        """zoom=1, pan=0, canvas 800×600 → bounds cover -margin to w+margin."""
        margin = 100.0
        min_x, min_y, max_x, max_y = self.frame._compute_viewport_bounds(margin=margin)
        # (-vx - margin) / z   = -100
        self.assertAlmostEqual(min_x, -margin)
        self.assertAlmostEqual(min_y, -margin)
        # (cw - vx + margin) / z = 900
        self.assertAlmostEqual(max_x, 800 + margin)
        self.assertAlmostEqual(max_y, 600 + margin)

    def test_compute_bounds_with_pan(self):
        vp = self.frame._viewport_service.viewport
        vp.x = 100.0
        vp.y = 50.0
        min_x, min_y, max_x, max_y = self.frame._compute_viewport_bounds(margin=0.0)
        self.assertAlmostEqual(min_x, -100.0)
        self.assertAlmostEqual(min_y,  -50.0)
        self.assertAlmostEqual(max_x,  700.0)  # (800-100)/1
        self.assertAlmostEqual(max_y,  550.0)  # (600-50)/1

    def test_compute_bounds_with_zoom(self):
        self.frame._viewport_service.viewport.zoom = 2.0
        min_x, min_y, max_x, max_y = self.frame._compute_viewport_bounds(margin=0.0)
        # (800-0)/2 = 400; (600-0)/2 = 300
        self.assertAlmostEqual(max_x, 400.0)
        self.assertAlmostEqual(max_y, 300.0)

    def test_compute_bounds_zero_margin(self):
        min_x, min_y, max_x, max_y = self.frame._compute_viewport_bounds(margin=0.0)
        self.assertAlmostEqual(min_x, 0.0)
        self.assertAlmostEqual(min_y, 0.0)
        self.assertAlmostEqual(max_x, 800.0)
        self.assertAlmostEqual(max_y, 600.0)


class TestSceneManagement(unittest.TestCase):
    """set_scene, get_scene, clear_scene."""

    def setUp(self):
        self.frame = _make_frame()

    def test_initial_scene_is_none(self):
        self.assertIsNone(self.frame.get_scene())

    def test_set_scene_stores_scene(self):
        scene = _make_scene()
        with patch.object(self.frame, "render_scene"):
            self.frame.set_scene(scene)
        self.assertIs(self.frame.get_scene(), scene)
        self.assertIs(self.frame._scene, scene)

    def test_set_scene_with_same_scene_is_noop(self):
        """Setting the identical scene object must be a no-op."""
        scene = _make_scene()
        with patch.object(self.frame, "render_scene"):
            self.frame.set_scene(scene)

        # Attach a spy to confirm no further work is done
        self.frame._enable_menu_entries = MagicMock()
        with patch.object(self.frame, "render_scene"):
            self.frame.set_scene(scene)  # same object

        self.frame._enable_menu_entries.assert_not_called()

    def test_set_scene_to_none_clears_scene(self):
        scene = _make_scene()
        with patch.object(self.frame, "render_scene"):
            self.frame.set_scene(scene)
            self.frame.set_scene(None)
        self.assertIsNone(self.frame._scene)

    def test_set_scene_enables_menu_when_scene_provided(self):
        self.frame._enable_menu_entries = MagicMock()
        scene = _make_scene()
        with patch.object(self.frame, "render_scene"):
            self.frame.set_scene(scene)
        self.frame._enable_menu_entries.assert_called_once_with(enable=True)

    def test_set_scene_disables_menu_when_none(self):
        self.frame._enable_menu_entries = MagicMock()
        self.frame._scene = _make_scene()
        self.frame._scene.get_on_scene_updated.return_value = []
        with patch.object(self.frame, "render_scene"):
            self.frame.set_scene(None)
        self.frame._enable_menu_entries.assert_called_once_with(enable=False)

    def test_set_scene_propagates_to_bridge_panel(self):
        scene = _make_scene()
        with patch.object(self.frame, "render_scene"):
            self.frame.set_scene(scene)
        self.frame._bridge_panel.update_scene.assert_called()

    def test_set_scene_propagates_to_connection_editor(self):
        scene = _make_scene()
        with patch.object(self.frame, "render_scene"):
            self.frame.set_scene(scene)
        self.frame._connection_editor_panel.update_scene.assert_called_with(scene)

    def test_set_scene_propagates_to_explorer(self):
        scene = _make_scene()
        with patch.object(self.frame, "render_scene"):
            self.frame.set_scene(scene)
        self.frame._object_explorer.set_scene.assert_called_with(scene)

    def test_set_scene_calls_render(self):
        scene = _make_scene()
        self.frame.render_scene = MagicMock()
        self.frame.set_scene(scene)
        self.frame.render_scene.assert_called_once()

    def test_set_scene_resets_viewport(self):
        scene = _make_scene()
        with patch.object(self.frame, "render_scene"):
            self.frame.set_scene(scene)
        self.frame._viewport_service.reset_view.assert_called()

    def test_clear_scene_calls_clear_canvas(self):
        scene = _make_scene()
        self.frame._scene = scene
        self.frame.clear_canvas = MagicMock()
        self.frame.clear_scene()
        self.frame.clear_canvas.assert_called_once()

    def test_clear_scene_empties_scene_objects(self):
        scene = _make_scene()
        self.frame._scene = scene
        self.frame.clear_canvas = MagicMock()
        self.frame.clear_scene()
        scene.set_scene_objects.assert_called_once_with({})

    def test_clear_scene_with_no_scene_is_safe(self):
        self.frame._scene = None
        self.frame.clear_canvas = MagicMock()
        # Should not raise
        self.frame.clear_scene()
        self.frame.clear_canvas.assert_called_once()


class TestSelectionManagement(unittest.TestCase):
    """select_object, deselect_object, toggle_selection, clear_selection."""

    def setUp(self):
        self.frame = _make_frame()
        self.frame._update_selection_display = MagicMock()
        self.frame._update_object_appearance = MagicMock()

    def test_select_object_delegates_to_service(self):
        self.frame.select_object("obj1", clear_previous=False)
        self.frame._canvas_object_management_service.select_object.assert_called_with("obj1", False)

    def test_select_object_clear_previous(self):
        self.frame.select_object("obj1", clear_previous=True)
        self.frame._canvas_object_management_service.select_object.assert_called_with("obj1", True)

    def test_select_object_updates_display(self):
        self.frame.select_object("obj1")
        self.frame._update_selection_display.assert_called_once()

    def test_select_object_updates_appearance(self):
        self.frame.select_object("obj1")
        self.frame._update_object_appearance.assert_called_with("obj1")

    def test_select_with_clear_updates_previously_selected_appearance(self):
        self.frame._canvas_object_management_service.selected_objects = ["old_obj"]
        self.frame.select_object("new_obj", clear_previous=True)
        # Both old and new should have their appearance updated
        calls = self.frame._update_object_appearance.call_args_list
        obj_ids = [c[0][0] for c in calls]
        self.assertIn("old_obj", obj_ids)
        self.assertIn("new_obj", obj_ids)

    def test_deselect_object_delegates_to_service(self):
        self.frame.deselect_object("obj1")
        self.frame._canvas_object_management_service.deselect_object.assert_called_with("obj1")

    def test_deselect_object_updates_display(self):
        self.frame.deselect_object("obj1")
        self.frame._update_selection_display.assert_called_once()

    def test_deselect_object_updates_appearance(self):
        self.frame.deselect_object("obj1")
        self.frame._update_object_appearance.assert_called_with("obj1")

    def test_toggle_selection_delegates_to_service(self):
        self.frame.toggle_selection("obj1")
        self.frame._canvas_object_management_service.toggle_selection.assert_called_with("obj1")

    def test_toggle_selection_updates_display(self):
        self.frame.toggle_selection("obj1")
        self.frame._update_selection_display.assert_called_once()

    def test_clear_selection_delegates_to_service(self):
        self.frame._canvas_object_management_service.selected_objects = ["a", "b"]
        self.frame.clear_selection()
        self.frame._canvas_object_management_service.clear_selection.assert_called_once()

    def test_clear_selection_updates_appearance_for_each_previously_selected(self):
        self.frame._canvas_object_management_service.selected_objects = ["a", "b", "c"]
        self.frame.clear_selection()
        calls = {c[0][0] for c in self.frame._update_object_appearance.call_args_list}
        self.assertEqual(calls, {"a", "b", "c"})

    def test_clear_empty_selection_is_safe(self):
        self.frame._canvas_object_management_service.selected_objects = []
        self.frame.clear_selection()  # should not raise


class TestObjectDeletion(unittest.TestCase):
    """delete_selected_objects."""

    def setUp(self):
        self.frame = _make_frame()
        self.frame.render_scene = MagicMock()

    def test_delete_without_scene_is_safe(self):
        self.frame._scene = None
        self.frame.delete_selected_objects()
        self.frame.render_scene.assert_not_called()

    def test_delete_without_selection_is_safe(self):
        self.frame._scene = _make_scene()
        self.frame._canvas_object_management_service.selected_objects = []
        self.frame.delete_selected_objects()
        self.frame.render_scene.assert_not_called()

    def test_delete_removes_object_from_scene(self):
        obj = _make_scene_object("obj1")
        scene = _make_scene([obj])
        self.frame._scene = scene
        self.frame._canvas_object_management_service.selected_objects = ["obj1"]
        self.frame.delete_selected_objects()
        scene.remove_scene_object.assert_called_with("obj1")

    def test_delete_clears_selection_afterwards(self):
        obj = _make_scene_object("obj1")
        scene = _make_scene([obj])
        self.frame._scene = scene
        self.frame._canvas_object_management_service.selected_objects = ["obj1"]
        self.frame.delete_selected_objects()
        self.frame._canvas_object_management_service.clear_selection.assert_called_once()

    def test_delete_calls_render_afterwards(self):
        obj = _make_scene_object("obj1")
        scene = _make_scene([obj])
        self.frame._scene = scene
        self.frame._canvas_object_management_service.selected_objects = ["obj1"]
        self.frame.delete_selected_objects()
        self.frame.render_scene.assert_called_once()

    def test_delete_multiple_objects(self):
        obj1 = _make_scene_object("obj1")
        obj2 = _make_scene_object("obj2")
        scene = _make_scene([obj1, obj2])
        self.frame._scene = scene
        self.frame._canvas_object_management_service.selected_objects = ["obj1", "obj2"]
        self.frame.delete_selected_objects()
        scene.remove_scene_object.assert_any_call("obj1")
        scene.remove_scene_object.assert_any_call("obj2")


class TestMarkDirty(unittest.TestCase):
    """_mark_dirty sets the pending-render flag."""

    def setUp(self):
        self.frame = _make_frame()

    def test_mark_dirty_sets_flag(self):
        self.frame._needs_full_render = False
        self.frame._mark_dirty()
        self.assertTrue(self.frame._needs_full_render)

    def test_mark_dirty_with_args_still_sets_flag(self):
        """The method accepts *_ to allow use as a callback."""
        self.frame._needs_full_render = False
        self.frame._mark_dirty("ignored", 42)
        self.assertTrue(self.frame._needs_full_render)

    def test_mark_dirty_idempotent(self):
        self.frame._needs_full_render = True
        self.frame._mark_dirty()
        self.assertTrue(self.frame._needs_full_render)


class TestRenderLoop(unittest.TestCase):
    """_render_loop decision branch coverage."""

    def setUp(self):
        self.frame = _make_frame()

    def test_full_render_when_dirty(self):
        self.frame._needs_full_render = True
        self.frame._scene = None
        self.frame.render_scene = MagicMock()
        self.frame._render_loop()
        self.frame.render_scene.assert_called_once()

    def test_dirty_flag_cleared_after_render(self):
        self.frame._needs_full_render = True
        self.frame.render_scene = MagicMock()
        self.frame._render_loop()
        self.assertFalse(self.frame._needs_full_render)

    def test_full_render_when_viewport_service_requests_it(self):
        self.frame._needs_full_render = False
        self.frame._viewport_service.needs_render.return_value = True
        self.frame._scene = None
        self.frame.render_scene = MagicMock()
        self.frame._render_loop()
        self.frame.render_scene.assert_called_once()

    def test_fast_update_called_when_not_dirty_and_has_scene(self):
        self.frame._needs_full_render = False
        self.frame._scene = _make_scene()
        self.frame.render_scene = MagicMock()
        self.frame._update_scene_objects_fast = MagicMock()
        self.frame._render_loop()
        self.frame.render_scene.assert_not_called()
        self.frame._update_scene_objects_fast.assert_called_once()

    def test_fast_update_skipped_with_no_scene(self):
        self.frame._needs_full_render = False
        self.frame._scene = None
        self.frame._update_scene_objects_fast = MagicMock()
        self.frame._render_loop()
        self.frame._update_scene_objects_fast.assert_not_called()

    def test_objects_ticked_each_frame(self):
        obj1 = _make_scene_object("obj1")
        obj2 = _make_scene_object("obj2")
        self.frame._scene = _make_scene([obj1, obj2])
        self.frame._needs_full_render = False
        self.frame._update_scene_objects_fast = MagicMock()
        self.frame._render_loop()
        obj1.update.assert_called_once()
        obj2.update.assert_called_once()

    def test_properties_panel_refreshed_when_visible_and_selection_exists(self):
        self.frame._needs_full_render = True
        self.frame.render_scene = MagicMock()
        self.frame._properties_panel.visible = True
        self.frame._canvas_object_management_service.selected_objects = ["obj1"]
        self.frame._scene = _make_scene()
        self.frame._render_loop()
        self.frame._properties_panel.refresh.assert_called_once()

    def test_properties_panel_not_refreshed_when_hidden(self):
        self.frame._needs_full_render = True
        self.frame.render_scene = MagicMock()
        self.frame._properties_panel.visible = False
        self.frame._canvas_object_management_service.selected_objects = ["obj1"]
        self.frame._render_loop()
        self.frame._properties_panel.refresh.assert_not_called()


class TestEntityNames(unittest.TestCase):
    """toggle_entity_names flips flag and triggers a render."""

    def setUp(self):
        self.frame = _make_frame()
        self.frame.render_scene = MagicMock()
        self.frame._enable_entry = MagicMock()

    def test_toggle_off(self):
        self.frame._entity_names_visible = True
        self.frame.toggle_entity_names()
        self.assertFalse(self.frame._entity_names_visible)

    def test_toggle_on(self):
        self.frame._entity_names_visible = False
        self.frame.toggle_entity_names()
        self.assertTrue(self.frame._entity_names_visible)

    def test_double_toggle_returns_to_original(self):
        original = self.frame._entity_names_visible
        self.frame.toggle_entity_names()
        self.frame.toggle_entity_names()
        self.assertEqual(self.frame._entity_names_visible, original)

    def test_toggle_triggers_render(self):
        self.frame.toggle_entity_names()
        self.frame.render_scene.assert_called_once()

    def test_toggle_updates_menu_entry(self):
        self.frame.toggle_entity_names()
        self.frame._enable_entry.assert_called_once()


class TestDragState(unittest.TestCase):
    """_on_drag_end_qt resets dragging bookkeeping."""

    def setUp(self):
        self.frame = _make_frame()

    def test_drag_end_clears_dragging_flag(self):
        self.frame._is_dragging = True
        self.frame._on_drag_end_qt(MagicMock())
        self.assertFalse(self.frame._is_dragging)

    def test_drag_end_clears_start_x(self):
        self.frame._drag_start_x = 100.0
        self.frame._on_drag_end_qt(MagicMock())
        self.assertIsNone(self.frame._drag_start_x)

    def test_drag_end_clears_start_y(self):
        self.frame._drag_start_y = 200.0
        self.frame._on_drag_end_qt(MagicMock())
        self.assertIsNone(self.frame._drag_start_y)

    def test_drag_object_skipped_when_no_selection(self):
        """No drag should occur if nothing is selected."""
        self.frame._canvas_object_management_service.selected_objects = []
        self.frame._drag_start_x = 0.0
        self.frame._drag_start_y = 0.0
        event = _mouse_event(_Qt.MouseButton.LeftButton, x=50, y=50)
        self.frame._on_drag_object_qt(event)
        # Nothing in _gfx_items should have been touched
        self.frame._gfx_scene.assert_not_called()

    def test_drag_object_skipped_when_no_start_position(self):
        self.frame._canvas_object_management_service.selected_objects = ["obj1"]
        self.frame._drag_start_x = None
        self.frame._drag_start_y = None
        self.frame._on_drag_object_qt(MagicMock())
        # No exception; nothing moved


class TestContextCopy(unittest.TestCase):
    """_context_copy / _context_cut clipboard behaviour."""

    def setUp(self):
        self.frame = _make_frame()

    def test_copy_with_no_scene_leaves_clipboard_empty(self):
        self.frame._scene = None
        self.frame._context_copy()
        self.assertEqual(self.frame._clipboard_data, [])

    def test_copy_with_no_selection_leaves_clipboard_empty(self):
        self.frame._scene = _make_scene()
        self.frame._canvas_object_management_service.selected_objects = []
        self.frame._context_copy()
        self.assertEqual(self.frame._clipboard_data, [])

    def test_copy_stores_serialised_object(self):
        obj = _make_scene_object("obj1")
        obj.to_dict.return_value = {"id": "obj1", "body": {"x": 10, "y": 20}}
        scene = _make_scene([obj])
        scene.get_scene_object.return_value = obj
        self.frame._scene = scene
        self.frame._canvas_object_management_service.selected_objects = ["obj1"]
        self.frame._context_copy()
        self.assertEqual(len(self.frame._clipboard_data), 1)
        self.assertEqual(self.frame._clipboard_data[0]["id"], "obj1")

    def test_copy_multiple_objects(self):
        obj1 = _make_scene_object("obj1")
        obj2 = _make_scene_object("obj2")
        obj1.to_dict.return_value = {"id": "obj1", "body": {}}
        obj2.to_dict.return_value = {"id": "obj2", "body": {}}
        scene = _make_scene([obj1, obj2])
        scene.get_scene_object.side_effect = lambda oid: {"obj1": obj1, "obj2": obj2}.get(oid)
        self.frame._scene = scene
        self.frame._canvas_object_management_service.selected_objects = ["obj1", "obj2"]
        self.frame._context_copy()
        self.assertEqual(len(self.frame._clipboard_data), 2)

    def test_cut_copies_then_deletes(self):
        self.frame._context_copy = MagicMock()
        self.frame.delete_selected_objects = MagicMock()
        self.frame._context_cut()
        self.frame._context_copy.assert_called_once()
        self.frame.delete_selected_objects.assert_called_once()


class TestUpdateSceneObjectsFast(unittest.TestCase):
    """_update_scene_objects_fast viewport culling/entry logic."""

    def setUp(self):
        self.frame = _make_frame()

    def test_no_scene_returns_safely(self):
        self.frame._scene = None
        self.frame._update_scene_objects_fast()  # must not raise

    def test_object_in_viewport_with_items_calls_fast_update(self):
        obj = _make_scene_object("obj1", x=100, y=100, w=50, h=50)
        self.frame._scene = _make_scene([obj])
        mock_item = MagicMock()
        mock_item.scene.return_value = self.frame._gfx_scene
        self.frame._gfx_items = {"obj1": [mock_item]}
        self.frame._fast_update_item = MagicMock()
        self.frame._update_scene_objects_fast()
        self.frame._fast_update_item.assert_called_once_with("obj1", obj)

    def test_object_in_viewport_without_items_triggers_render(self):
        """Object that enters the viewport must be rendered fresh."""
        obj = _make_scene_object("obj1", x=100, y=100, w=50, h=50)
        self.frame._scene = _make_scene([obj])
        self.frame._gfx_items = {}  # no existing items
        self.frame._render_scene_object = MagicMock()
        self.frame._update_scene_objects_fast()
        self.frame._render_scene_object.assert_called_once_with("obj1", obj)

    def test_object_outside_viewport_is_culled(self):
        """Object that leaves the viewport must have its items removed."""
        obj = _make_scene_object("obj1", x=5000, y=5000, w=50, h=50)
        self.frame._scene = _make_scene([obj])
        mock_item = MagicMock()
        mock_item.scene.return_value = self.frame._gfx_scene
        self.frame._gfx_items = {"obj1": [mock_item]}
        self.frame._update_scene_objects_fast()
        self.assertNotIn("obj1", self.frame._gfx_items)
        self.frame._gfx_scene.removeItem.assert_called_with(mock_item)

    def test_object_outside_viewport_without_items_untouched(self):
        """Culled object with no items should not cause errors."""
        obj = _make_scene_object("obj1", x=5000, y=5000, w=50, h=50)
        self.frame._scene = _make_scene([obj])
        self.frame._gfx_items = {}
        self.frame._update_scene_objects_fast()  # must not raise
        self.frame._gfx_scene.removeItem.assert_not_called()


# ===========================================================================
# _SceneCanvasView tests
# ===========================================================================


class TestCanvasViewMousePress(unittest.TestCase):
    """mousePressEvent routing."""

    def test_none_event_is_safe(self):
        view, _ = _make_canvas_view()
        view.mousePressEvent(None)  # must not raise

    def test_left_button_select_mode_calls_select_click(self):
        view, frame = _make_canvas_view(UserMode.SELECT)
        frame._on_select_click_qt = MagicMock()
        event = _mouse_event(_Qt.MouseButton.LeftButton)
        view.mousePressEvent(event)
        frame._on_select_click_qt.assert_called_once_with(event)

    def test_left_button_insert_mode_calls_place_object(self):
        view, frame = _make_canvas_view(UserMode.INSERT)
        frame._place_object_from_template = MagicMock()
        event = _mouse_event(_Qt.MouseButton.LeftButton, x=200.0, y=300.0)
        view.mousePressEvent(event)
        frame._place_object_from_template.assert_called_once()

    def test_middle_button_starts_panning(self):
        view, _ = _make_canvas_view()
        event = _mouse_event(_Qt.MouseButton.MiddleButton, x=50.0, y=60.0)
        view.mousePressEvent(event)
        self.assertTrue(view._is_panning)
        self.assertEqual(view._pan_start_x, 50.0)
        self.assertEqual(view._pan_start_y, 60.0)


class TestCanvasViewMouseRelease(unittest.TestCase):
    """mouseReleaseEvent routing."""

    def test_none_event_is_safe(self):
        view, _ = _make_canvas_view()
        view.mouseReleaseEvent(None)

    def test_middle_release_stops_panning(self):
        view, _ = _make_canvas_view()
        view._is_panning = True
        event = _mouse_event(_Qt.MouseButton.MiddleButton)
        view.mouseReleaseEvent(event)
        self.assertFalse(view._is_panning)

    def test_left_release_in_select_mode_calls_drag_end(self):
        view, frame = _make_canvas_view(UserMode.SELECT)
        frame._on_drag_end_qt = MagicMock()
        event = _mouse_event(_Qt.MouseButton.LeftButton)
        view.mouseReleaseEvent(event)
        frame._on_drag_end_qt.assert_called_once_with(event)


class TestCanvasViewMouseMove(unittest.TestCase):
    """mouseMoveEvent routing."""

    def test_none_event_is_safe(self):
        view, _ = _make_canvas_view()
        view.mouseMoveEvent(None)

    def test_middle_drag_pans_viewport(self):
        view, frame = _make_canvas_view()
        view._is_panning = True
        view._pan_start_x = 50.0
        view._pan_start_y = 50.0
        event = MagicMock()
        pos = MagicMock()
        pos.x.return_value = 70.0  # dx = +20
        pos.y.return_value = 60.0  # dy = +10
        event.position.return_value = pos
        event.buttons.return_value = _Qt.MouseButton.MiddleButton
        with patch("pyrox.models.gui.sceneviewer.sceneviewer.ViewportEventBus"):
            view.mouseMoveEvent(event)
        self.assertAlmostEqual(frame._viewport_service.viewport.x, 20.0)
        self.assertAlmostEqual(frame._viewport_service.viewport.y, 10.0)

    def test_middle_drag_updates_pan_start(self):
        view, _ = _make_canvas_view()
        view._is_panning = True
        view._pan_start_x = 50.0
        view._pan_start_y = 50.0
        event = MagicMock()
        pos = MagicMock()
        pos.x.return_value = 80.0
        pos.y.return_value = 90.0
        event.position.return_value = pos
        event.buttons.return_value = _Qt.MouseButton.MiddleButton
        with patch("pyrox.models.gui.sceneviewer.sceneviewer.ViewportEventBus"):
            view.mouseMoveEvent(event)
        self.assertEqual(view._pan_start_x, 80.0)
        self.assertEqual(view._pan_start_y, 90.0)

    def test_left_drag_select_mode_calls_drag_object(self):
        view, frame = _make_canvas_view(UserMode.SELECT)
        frame._on_drag_object_qt = MagicMock()
        event = MagicMock()
        event.buttons.return_value = _Qt.MouseButton.LeftButton
        view.mouseMoveEvent(event)
        frame._on_drag_object_qt.assert_called_once_with(event)


class TestCanvasViewWheel(unittest.TestCase):
    """wheelEvent zooms correctly."""

    def test_none_event_is_safe(self):
        view, _ = _make_canvas_view()
        view.wheelEvent(None)

    def test_scroll_up_zooms_in(self):
        view, frame = _make_canvas_view()
        frame._mark_dirty = MagicMock()
        event = MagicMock()
        pos = MagicMock()
        pos.x.return_value = 400.0
        pos.y.return_value = 300.0
        event.position.return_value = pos
        event.angleDelta().y.return_value = 120  # positive = scroll up
        view.wheelEvent(event)
        frame._viewport_service.zoom.zoom_in.assert_called_once()
        frame._mark_dirty.assert_called_once()

    def test_scroll_down_zooms_out(self):
        view, frame = _make_canvas_view()
        frame._mark_dirty = MagicMock()
        event = MagicMock()
        pos = MagicMock()
        pos.x.return_value = 400.0
        pos.y.return_value = 300.0
        event.position.return_value = pos
        event.angleDelta().y.return_value = -120  # negative = scroll down
        view.wheelEvent(event)
        frame._viewport_service.zoom.zoom_out.assert_called_once()
        frame._mark_dirty.assert_called_once()


class TestCanvasViewKeyboard(unittest.TestCase):
    """keyPressEvent routing to frame actions."""

    def test_none_key_event_is_safe(self):
        view, _ = _make_canvas_view()
        view.keyPressEvent(None)

    def test_delete_deletes_selected(self):
        view, frame = _make_canvas_view()
        frame.delete_selected_objects = MagicMock()
        view.keyPressEvent(_key_event(_Qt.Key.Key_Delete))
        frame.delete_selected_objects.assert_called_once()

    def test_escape_clears_selection(self):
        view, frame = _make_canvas_view()
        frame.clear_selection = MagicMock()
        view.keyPressEvent(_key_event(_Qt.Key.Key_Escape))
        frame.clear_selection.assert_called_once()

    def test_ctrl_l_toggles_entity_names(self):
        view, frame = _make_canvas_view()
        frame.toggle_entity_names = MagicMock()
        view.keyPressEvent(_key_event(_Qt.Key.Key_L, mods=_CTRL))
        frame.toggle_entity_names.assert_called_once()

    def test_ctrl_bracket_right_layer_up(self):
        view, frame = _make_canvas_view()
        frame._context_layer_up = MagicMock()
        view.keyPressEvent(_key_event(_Qt.Key.Key_BracketRight, mods=_CTRL))
        frame._context_layer_up.assert_called_once()

    def test_ctrl_bracket_left_layer_down(self):
        view, frame = _make_canvas_view()
        frame._context_layer_down = MagicMock()
        view.keyPressEvent(_key_event(_Qt.Key.Key_BracketLeft, mods=_CTRL))
        frame._context_layer_down.assert_called_once()

    def test_ctrl_shift_bracket_right_bring_to_front(self):
        view, frame = _make_canvas_view()
        frame._context_bring_to_front = MagicMock()
        view.keyPressEvent(_key_event(_Qt.Key.Key_BracketRight, mods=_CTRL_SHIFT))
        frame._context_bring_to_front.assert_called_once()

    def test_ctrl_shift_bracket_left_send_to_back(self):
        view, frame = _make_canvas_view()
        frame._context_send_to_back = MagicMock()
        view.keyPressEvent(_key_event(_Qt.Key.Key_BracketLeft, mods=_CTRL_SHIFT))
        frame._context_send_to_back.assert_called_once()

    def test_ctrl_alt_g_groups(self):
        view, frame = _make_canvas_view()
        frame._context_group_selected = MagicMock()
        view.keyPressEvent(_key_event(_Qt.Key.Key_G, mods=_CTRL_ALT))
        frame._context_group_selected.assert_called_once()

    def test_ctrl_alt_u_ungroups(self):
        view, frame = _make_canvas_view()
        frame._context_ungroup_selected = MagicMock()
        view.keyPressEvent(_key_event(_Qt.Key.Key_U, mods=_CTRL_ALT))
        frame._context_ungroup_selected.assert_called_once()

    def test_unrecognised_key_does_not_raise(self):
        view, _ = _make_canvas_view()
        # Provide a valid super-call stub so the fallback path doesn't blow up
        view.__class__.__bases__[0].keyPressEvent = MagicMock()
        view.keyPressEvent(_key_event(99999))


# ===========================================================================
# Composite object rotation tests
#
# Four test classes work together to cover the full rotation story inside the
# sceneviewer, from the context-menu dispatch through to the canvas
# bounding-box geometry:
#
#   TestCompositeRotationContextMenu  — viewer dispatch / guard rails
#   TestCompositeRotationDirection    — correct CardinalDirection sequence
#   TestCompositeComponentOffsets     — component offset & dimension maths
#   TestCompositeBoundingBoxAlignment — rendered bbox position & size
#
# The last two classes use *real* CompositeSceneObject instances (no PyQt6
# dependency) so the actual rotation formulae are exercised end-to-end.
# ===========================================================================


# ---------------------------------------------------------------------------
# Shared helpers for composite rotation tests
# ---------------------------------------------------------------------------

def _make_real_physics_body(name: str = "body",
                            x: float = 0.0, y: float = 0.0,
                            width: float = 100.0, height: float = 80.0):
    """Returns a real BasePhysicsBody (no Qt deps)."""
    from pyrox.models import BasePhysicsBody
    from pyrox.interfaces import BodyType, ColliderType, CollisionLayer
    return BasePhysicsBody(
        name=name,
        template_name=name,
        x=x, y=y, width=width, height=height,
        mass=1.0,
        body_type=BodyType.DYNAMIC,
        collider_type=ColliderType.RECTANGLE,
        collision_layer=CollisionLayer.DEFAULT,
    )


def _make_real_composite(name: str = "Panel",
                         x: float = 0.0, y: float = 0.0,
                         width: float = 100.0, height: float = 80.0):
    """Returns a real CompositeSceneObject with no components."""
    from pyrox.models.scene.compositesceneobject import CompositeSceneObject
    return CompositeSceneObject(
        name=name,
        physics_body=_make_real_physics_body(name, x, y, width, height),
    )


def _make_real_composite_with_component(comp_w: float = 20.0,
                                        comp_h: float = 10.0,
                                        offset_x: float = 10.0,
                                        offset_y: float = 20.0):
    """100×80 composite NORTH with one component at the given offset / size."""
    from pyrox.models import SceneObject
    composite = _make_real_composite(width=100.0, height=80.0)
    child = SceneObject(
        name="btn",
        physics_body=_make_real_physics_body("btn", width=comp_w, height=comp_h),
        parent=composite,
        parent_offset_x=offset_x,
        parent_offset_y=offset_y,
    )
    composite.add_component("btn", child)
    return composite, child


def _dispatch_rotate(composite, clockwise: bool):
    """Drive composite rotation through the viewer's context-menu path."""
    frame = _make_frame()
    scene = _make_scene()
    scene.scene_objects["c"] = composite
    scene.get_scene_object.return_value = composite
    frame._scene = scene
    frame._canvas_object_management_service.selected_objects = ["c"]
    frame.render_scene = MagicMock()
    if clockwise:
        frame._context_rotate_cw()
    else:
        frame._context_rotate_ccw()


# ===========================================================================

class TestCompositeRotationContextMenu(unittest.TestCase):
    """_context_rotate_cw / _context_rotate_ccw viewer dispatch and guard rails."""

    def setUp(self):
        self.frame = _make_frame()
        self.frame.render_scene = MagicMock()

    # --- guard rails ---------------------------------------------------------

    def test_rotate_cw_no_scene_is_noop(self):
        self.frame._scene = None
        self.frame._context_rotate_cw()
        self.frame.render_scene.assert_not_called()

    def test_rotate_ccw_no_scene_is_noop(self):
        self.frame._scene = None
        self.frame._context_rotate_ccw()
        self.frame.render_scene.assert_not_called()

    def test_rotate_cw_no_selection_is_noop(self):
        self.frame._scene = _make_scene()
        self.frame._canvas_object_management_service.selected_objects = []
        self.frame._context_rotate_cw()
        self.frame.render_scene.assert_not_called()

    def test_rotate_ccw_no_selection_is_noop(self):
        self.frame._scene = _make_scene()
        self.frame._canvas_object_management_service.selected_objects = []
        self.frame._context_rotate_ccw()
        self.frame.render_scene.assert_not_called()

    def test_rotate_cw_skips_object_not_found_in_scene(self):
        """get_scene_object returning None must not raise."""
        scene = _make_scene()
        scene.get_scene_object.return_value = None
        self.frame._scene = scene
        self.frame._canvas_object_management_service.selected_objects = ["ghost"]
        self.frame._context_rotate_cw()  # must not raise
        self.frame.render_scene.assert_called_once()

    # --- dispatch ------------------------------------------------------------

    def test_rotate_cw_calls_rotate_clockwise_on_selected(self):
        obj = _make_scene_object("c1")
        scene = _make_scene([obj])
        scene.get_scene_object.return_value = obj
        self.frame._scene = scene
        self.frame._canvas_object_management_service.selected_objects = ["c1"]
        self.frame._context_rotate_cw()
        obj.rotate_clockwise.assert_called_once()

    def test_rotate_ccw_calls_rotate_counterclockwise_on_selected(self):
        obj = _make_scene_object("c1")
        scene = _make_scene([obj])
        scene.get_scene_object.return_value = obj
        self.frame._scene = scene
        self.frame._canvas_object_management_service.selected_objects = ["c1"]
        self.frame._context_rotate_ccw()
        obj.rotate_counterclockwise.assert_called_once()

    def test_rotate_cw_applies_to_all_selected(self):
        obj1 = _make_scene_object("c1")
        obj2 = _make_scene_object("c2")
        scene = _make_scene([obj1, obj2])
        scene.get_scene_object.side_effect = lambda oid: {"c1": obj1, "c2": obj2}.get(oid)
        self.frame._scene = scene
        self.frame._canvas_object_management_service.selected_objects = ["c1", "c2"]
        self.frame._context_rotate_cw()
        obj1.rotate_clockwise.assert_called_once()
        obj2.rotate_clockwise.assert_called_once()

    def test_rotate_ccw_applies_to_all_selected(self):
        obj1 = _make_scene_object("c1")
        obj2 = _make_scene_object("c2")
        scene = _make_scene([obj1, obj2])
        scene.get_scene_object.side_effect = lambda oid: {"c1": obj1, "c2": obj2}.get(oid)
        self.frame._scene = scene
        self.frame._canvas_object_management_service.selected_objects = ["c1", "c2"]
        self.frame._context_rotate_ccw()
        obj1.rotate_counterclockwise.assert_called_once()
        obj2.rotate_counterclockwise.assert_called_once()

    def test_rotate_cw_triggers_render_scene(self):
        obj = _make_scene_object("c1")
        scene = _make_scene([obj])
        scene.get_scene_object.return_value = obj
        self.frame._scene = scene
        self.frame._canvas_object_management_service.selected_objects = ["c1"]
        self.frame._context_rotate_cw()
        self.frame.render_scene.assert_called_once()

    def test_rotate_ccw_triggers_render_scene(self):
        obj = _make_scene_object("c1")
        scene = _make_scene([obj])
        scene.get_scene_object.return_value = obj
        self.frame._scene = scene
        self.frame._canvas_object_management_service.selected_objects = ["c1"]
        self.frame._context_rotate_ccw()
        self.frame.render_scene.assert_called_once()


class TestCompositeRotationDirection(unittest.TestCase):
    """CardinalDirection sequence is correct when rotation is dispatched via the viewer.

    Rotation formula (90° steps, y-down screen space):
        NORTH → CW  → EAST  → CW  → SOUTH → CW  → WEST  → CW  → NORTH
        NORTH → CCW → WEST  → CCW → SOUTH → CCW → EAST  → CCW → NORTH
    """

    def test_cw_rotation_north_to_east(self):
        from pyrox.interfaces import CardinalDirection
        comp = _make_real_composite()
        _dispatch_rotate(comp, clockwise=True)
        self.assertEqual(comp.direction, CardinalDirection.EAST)

    def test_ccw_rotation_north_to_west(self):
        from pyrox.interfaces import CardinalDirection
        comp = _make_real_composite()
        _dispatch_rotate(comp, clockwise=False)
        self.assertEqual(comp.direction, CardinalDirection.WEST)

    def test_cw_twice_north_to_south(self):
        from pyrox.interfaces import CardinalDirection
        comp = _make_real_composite()
        _dispatch_rotate(comp, clockwise=True)
        _dispatch_rotate(comp, clockwise=True)
        self.assertEqual(comp.direction, CardinalDirection.SOUTH)

    def test_cw_three_times_north_to_west(self):
        from pyrox.interfaces import CardinalDirection
        comp = _make_real_composite()
        for _ in range(3):
            _dispatch_rotate(comp, clockwise=True)
        self.assertEqual(comp.direction, CardinalDirection.WEST)

    def test_four_cw_rotations_restore_direction(self):
        comp = _make_real_composite()
        original_dir = comp.direction
        for _ in range(4):
            _dispatch_rotate(comp, clockwise=True)
        self.assertEqual(comp.direction, original_dir)

    def test_four_ccw_rotations_restore_direction(self):
        comp = _make_real_composite()
        original_dir = comp.direction
        for _ in range(4):
            _dispatch_rotate(comp, clockwise=False)
        self.assertEqual(comp.direction, original_dir)

    def test_cw_then_ccw_restores_direction(self):
        comp = _make_real_composite()
        original_dir = comp.direction
        _dispatch_rotate(comp, clockwise=True)
        _dispatch_rotate(comp, clockwise=False)
        self.assertEqual(comp.direction, original_dir)

    def test_ccw_then_cw_restores_direction(self):
        comp = _make_real_composite()
        original_dir = comp.direction
        _dispatch_rotate(comp, clockwise=False)
        _dispatch_rotate(comp, clockwise=True)
        self.assertEqual(comp.direction, original_dir)

    def test_cw_swaps_composite_width_and_height(self):
        """100×80 composite → CW → 80×100."""
        comp = _make_real_composite(width=100.0, height=80.0)
        _dispatch_rotate(comp, clockwise=True)
        self.assertAlmostEqual(comp.width, 80.0)
        self.assertAlmostEqual(comp.height, 100.0)

    def test_ccw_swaps_composite_width_and_height(self):
        comp = _make_real_composite(width=100.0, height=80.0)
        _dispatch_rotate(comp, clockwise=False)
        self.assertAlmostEqual(comp.width, 80.0)
        self.assertAlmostEqual(comp.height, 100.0)

    def test_four_cw_rotations_restore_dimensions(self):
        comp = _make_real_composite(width=100.0, height=80.0)
        for _ in range(4):
            _dispatch_rotate(comp, clockwise=True)
        self.assertAlmostEqual(comp.width, 100.0)
        self.assertAlmostEqual(comp.height, 80.0)

    def test_cw_rotation_is_not_same_as_ccw(self):
        """A single CW and a single CCW step must produce different directions."""
        cw = _make_real_composite()
        ccw = _make_real_composite()
        _dispatch_rotate(cw, clockwise=True)
        _dispatch_rotate(ccw, clockwise=False)
        self.assertNotEqual(cw.direction, ccw.direction)


class TestCompositeComponentOffsets(unittest.TestCase):
    """Component offset and dimension maths after CW/CCW dispatch from the viewer.

    Reference formulae (screen space, y-down, point = component top-left):

        CW  90°:  new_ox = old_oy
                  new_oy = composite_W − old_ox − comp_w

        CCW 90°:  new_ox = composite_H − old_oy − comp_h
                  new_oy = old_ox

    where composite_W / composite_H are the composite dims *before* the swap.
    """

    def test_cw_component_offset_correct(self):
        """CW: old offset (10, 20), comp 20×10, composite 100×80 → new (20, 70)."""
        comp, btn = _make_real_composite_with_component(
            comp_w=20.0, comp_h=10.0, offset_x=10.0, offset_y=20.0
        )
        _dispatch_rotate(comp, clockwise=True)
        ox, oy = btn.parent_offset
        self.assertAlmostEqual(ox, 20.0)   # old_oy
        self.assertAlmostEqual(oy, 70.0)   # 100 − 10 − 20

    def test_ccw_component_offset_correct(self):
        """CCW: old offset (10, 20), comp 20×10, composite 100×80 → new (50, 10)."""
        comp, btn = _make_real_composite_with_component(
            comp_w=20.0, comp_h=10.0, offset_x=10.0, offset_y=20.0
        )
        _dispatch_rotate(comp, clockwise=False)
        ox, oy = btn.parent_offset
        self.assertAlmostEqual(ox, 50.0)   # 80 − 20 − 10
        self.assertAlmostEqual(oy, 10.0)   # old_ox

    def test_cw_swaps_component_dimensions(self):
        """CW rotation swaps component width ↔ height (20×10 → 10×20)."""
        comp, btn = _make_real_composite_with_component(comp_w=20.0, comp_h=10.0)
        _dispatch_rotate(comp, clockwise=True)
        self.assertAlmostEqual(btn.width, 10.0)
        self.assertAlmostEqual(btn.height, 20.0)

    def test_ccw_swaps_component_dimensions(self):
        """CCW rotation swaps component width ↔ height (20×10 → 10×20)."""
        comp, btn = _make_real_composite_with_component(comp_w=20.0, comp_h=10.0)
        _dispatch_rotate(comp, clockwise=False)
        self.assertAlmostEqual(btn.width, 10.0)
        self.assertAlmostEqual(btn.height, 20.0)

    def test_four_cw_restores_component_offsets(self):
        """4 × CW must return component to its original offset."""
        comp, btn = _make_real_composite_with_component(
            comp_w=20.0, comp_h=10.0, offset_x=10.0, offset_y=20.0
        )
        for _ in range(4):
            _dispatch_rotate(comp, clockwise=True)
        ox, oy = btn.parent_offset
        self.assertAlmostEqual(ox, 10.0)
        self.assertAlmostEqual(oy, 20.0)

    def test_four_cw_restores_component_dimensions(self):
        comp, btn = _make_real_composite_with_component(comp_w=20.0, comp_h=10.0)
        for _ in range(4):
            _dispatch_rotate(comp, clockwise=True)
        self.assertAlmostEqual(btn.width, 20.0)
        self.assertAlmostEqual(btn.height, 10.0)

    def test_cw_applies_to_all_components(self):
        """Every registered component gets its offset and dimensions updated."""
        from pyrox.models.scene.compositesceneobject import CompositeSceneObject
        from pyrox.models import SceneObject
        from pyrox.interfaces import CardinalDirection

        comp = CompositeSceneObject(
            name="Panel",
            physics_body=_make_real_physics_body("body", width=100.0, height=80.0),
            direction=CardinalDirection.NORTH,
        )
        a = SceneObject(name="a",
                        physics_body=_make_real_physics_body("a", width=20.0, height=10.0),
                        parent=comp,
                        parent_offset_x=5.0, parent_offset_y=10.0)
        b = SceneObject(name="b",
                        physics_body=_make_real_physics_body("b", width=30.0, height=15.0),
                        parent=comp,
                        parent_offset_x=5.0, parent_offset_y=40.0)
        comp.add_component("a", a)
        comp.add_component("b", b)

        _dispatch_rotate(comp, clockwise=True)

        # a: new_ox = old_oy=10,  new_oy = 100−5−20 = 75
        ax, ay = a.parent_offset
        self.assertAlmostEqual(ax, 10.0)
        self.assertAlmostEqual(ay, 75.0)

        # b: new_ox = old_oy=40,  new_oy = 100−5−30 = 65
        bx, by = b.parent_offset
        self.assertAlmostEqual(bx, 40.0)
        self.assertAlmostEqual(by, 65.0)

    def test_cw_offset_is_distinct_from_ccw_offset(self):
        """CW and CCW must move the component to *different* positions."""
        comp_cw, btn_cw = _make_real_composite_with_component(
            comp_w=20.0, comp_h=10.0, offset_x=10.0, offset_y=20.0
        )
        comp_ccw, btn_ccw = _make_real_composite_with_component(
            comp_w=20.0, comp_h=10.0, offset_x=10.0, offset_y=20.0
        )
        _dispatch_rotate(comp_cw, clockwise=True)
        _dispatch_rotate(comp_ccw, clockwise=False)
        self.assertNotEqual(btn_cw.parent_offset, btn_ccw.parent_offset)


class TestCompositeBoundingBoxAlignment(unittest.TestCase):
    """Bounding-box canvas geometry produced by _render_composite_scene_object.

    The renderer computes:
        canvas_x = composite.x * zoom + vx
        canvas_y = composite.y * zoom + vy
        canvas_w = composite.width  * zoom
        canvas_h = composite.height * zoom

    and creates:
        bbox_item = QGraphicsRectItem(QRectF(0, 0, canvas_w, canvas_h))
        bbox_item.setPos(canvas_x, canvas_y)

    After a CW/CCW rotation the composite swaps its width and height, so:
        canvas_w uses the *new* (post-rotation) composite.width
        canvas_h uses the *new* (post-rotation) composite.height
    """

    # ---------------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------------

    def _make_frame_with_viewport(self, zoom: float = 1.0,
                                  vx: float = 0.0, vy: float = 0.0):
        frame = _make_frame()
        frame._canvas_object_management_service.selected_objects = []
        frame._viewport_service.viewport = _make_viewport(x=vx, y=vy, zoom=zoom)
        return frame

    def _get_bbox_item(self, frame, composite, obj_id: str = "c"):
        """Render composite and return the *first* QGraphicsRectItem added to the gfx scene.

        The returned item has a MagicMock ``setPos`` so axis-position assertions work.
        ``sv_mod.QGraphicsRectItem`` is temporarily replaced with a lightweight stub
        that records calls to ``setPos``, ``setPen``, ``setBrush``, ``setData``, and
        ``setZValue``.
        """
        import pyrox.models.gui.sceneviewer.sceneviewer as _sv

        class _CapRectItem:
            def __init__(self_, *args, **kwargs):
                self_.setPos = MagicMock()
                self_.setPen = MagicMock()
                self_.setBrush = MagicMock()
                self_.setData = MagicMock()
                self_.setZValue = MagicMock()
                self_.setTransformOriginPoint = MagicMock()
                self_.setRotation = MagicMock()

        orig_item = _sv.QGraphicsRectItem
        _sv.QGraphicsRectItem = _CapRectItem
        try:
            frame._gfx_scene.reset_mock()
            frame._render_composite_scene_object(obj_id, composite)
            calls = frame._gfx_scene.addItem.call_args_list
            self.assertGreater(len(calls), 0, "addItem was never called")
            return calls[0][0][0]
        finally:
            _sv.QGraphicsRectItem = orig_item

    def _capture_qrectf_args(self, frame, composite, obj_id: str = "c"):
        """Render composite and return a list of (x, y, w, h) tuples, one per QRectF call.

        Both ``QRectF`` and ``QGraphicsRectItem`` are patched so the stub rect-item
        constructors accept the captured ``QRectF`` instances without type errors.
        """
        import pyrox.models.gui.sceneviewer.sceneviewer as _sv
        captured: list[tuple] = []

        class _CapQRectF:
            def __init__(self_, *args):
                self_.args = args
                captured.append(args)

        class _CapRectItem:
            def __init__(self_, *args, **kwargs):
                self_.setPos = MagicMock()
                self_.setPen = MagicMock()
                self_.setBrush = MagicMock()
                self_.setData = MagicMock()
                self_.setZValue = MagicMock()
                self_.setTransformOriginPoint = MagicMock()
                self_.setRotation = MagicMock()

        orig_qrectf = _sv.QRectF
        orig_item = _sv.QGraphicsRectItem
        _sv.QRectF = _CapQRectF
        _sv.QGraphicsRectItem = _CapRectItem
        try:
            frame._gfx_scene.reset_mock()
            frame._render_composite_scene_object(obj_id, composite)
        finally:
            _sv.QRectF = orig_qrectf
            _sv.QGraphicsRectItem = orig_item
        return captured

    # ---------------------------------------------------------------------------
    # Position (setPos) tests
    # ---------------------------------------------------------------------------

    def test_bbox_setpos_uses_composite_world_coords(self):
        """setPos must be called with composite.(x,y) projected through zoom+pan."""
        frame = self._make_frame_with_viewport(zoom=1.5, vx=20.0, vy=10.0)
        comp = _make_real_composite(x=50.0, y=40.0)
        bbox = self._get_bbox_item(frame, comp)
        expected_x = 50.0 * 1.5 + 20.0   # 95.0
        expected_y = 40.0 * 1.5 + 10.0   # 70.0
        bbox.setPos.assert_called_once_with(expected_x, expected_y)

    def test_bbox_setpos_at_origin_no_pan_unit_zoom(self):
        frame = self._make_frame_with_viewport(zoom=1.0)
        comp = _make_real_composite(x=0.0, y=0.0)
        bbox = self._get_bbox_item(frame, comp)
        bbox.setPos.assert_called_once_with(0.0, 0.0)

    def test_bbox_setpos_scales_with_zoom(self):
        """Doubling zoom doubles the canvas position offset contribution."""
        comp_x, comp_y = 30.0, 20.0
        frame1 = self._make_frame_with_viewport(zoom=1.0)
        frame2 = self._make_frame_with_viewport(zoom=2.0)
        comp = _make_real_composite(x=comp_x, y=comp_y)

        bbox1 = self._get_bbox_item(frame1, comp)
        bbox2 = self._get_bbox_item(frame2, comp)

        cx1, cy1 = bbox1.setPos.call_args[0]
        cx2, cy2 = bbox2.setPos.call_args[0]
        self.assertAlmostEqual(cx2, cx1 * 2.0)
        self.assertAlmostEqual(cy2, cy1 * 2.0)

    def test_bbox_position_unchanged_after_cw_rotation(self):
        """Rotation changes shape but composite world origin stays the same."""
        frame = self._make_frame_with_viewport(zoom=1.0)
        comp = _make_real_composite(x=50.0, y=40.0)
        comp.rotate_clockwise()
        bbox = self._get_bbox_item(frame, comp)
        # world origin is still (50, 40) after rotation
        bbox.setPos.assert_called_once_with(50.0 * 1.0, 40.0 * 1.0)

    def test_bbox_position_unchanged_after_ccw_rotation(self):
        frame = self._make_frame_with_viewport(zoom=1.0)
        comp = _make_real_composite(x=50.0, y=40.0)
        comp.rotate_counterclockwise()
        bbox = self._get_bbox_item(frame, comp)
        bbox.setPos.assert_called_once_with(50.0 * 1.0, 40.0 * 1.0)

    # ---------------------------------------------------------------------------
    # Size (QRectF args) tests
    # ---------------------------------------------------------------------------

    def test_bbox_qrectf_before_rotation(self):
        """QRectF(0, 0, canvas_w, canvas_h) must match initial composite dims × zoom."""
        frame = self._make_frame_with_viewport(zoom=2.0)
        comp = _make_real_composite(width=100.0, height=80.0)
        rects = self._capture_qrectf_args(frame, comp)
        # rects[0] is the bbox; composite has no components so only one QRectF call
        self.assertEqual(rects[0][0], 0)
        self.assertEqual(rects[0][1], 0)
        self.assertAlmostEqual(rects[0][2], 100.0 * 2.0)
        self.assertAlmostEqual(rects[0][3], 80.0 * 2.0)

    def test_bbox_qrectf_after_cw_rotation_reflects_swapped_dims(self):
        """After CW: 100×80 composite becomes 80×100; bbox size must follow."""
        frame = self._make_frame_with_viewport(zoom=1.0)
        comp = _make_real_composite(width=100.0, height=80.0)
        comp.rotate_clockwise()   # now width=80, height=100
        rects = self._capture_qrectf_args(frame, comp)
        self.assertAlmostEqual(rects[0][2], 80.0)    # new canvas_w
        self.assertAlmostEqual(rects[0][3], 100.0)   # new canvas_h

    def test_bbox_qrectf_after_ccw_rotation_reflects_swapped_dims(self):
        """After CCW: 100×80 composite becomes 80×100; bbox size must follow."""
        frame = self._make_frame_with_viewport(zoom=1.0)
        comp = _make_real_composite(width=100.0, height=80.0)
        comp.rotate_counterclockwise()
        rects = self._capture_qrectf_args(frame, comp)
        self.assertAlmostEqual(rects[0][2], 80.0)
        self.assertAlmostEqual(rects[0][3], 100.0)

    def test_bbox_qrectf_after_four_cw_restores_original(self):
        """4 × CW must return bbox to original dimensions."""
        frame = self._make_frame_with_viewport(zoom=1.0)
        comp = _make_real_composite(width=100.0, height=80.0)
        for _ in range(4):
            comp.rotate_clockwise()
        rects = self._capture_qrectf_args(frame, comp)
        self.assertAlmostEqual(rects[0][2], 100.0)
        self.assertAlmostEqual(rects[0][3], 80.0)

    def test_bbox_canvas_width_scales_with_zoom(self):
        """canvas_w = composite.width × zoom."""
        frame = self._make_frame_with_viewport(zoom=3.0)
        comp = _make_real_composite(width=60.0, height=40.0)
        rects = self._capture_qrectf_args(frame, comp)
        self.assertAlmostEqual(rects[0][2], 60.0 * 3.0)

    def test_bbox_canvas_height_scales_with_zoom(self):
        frame = self._make_frame_with_viewport(zoom=3.0)
        comp = _make_real_composite(width=60.0, height=40.0)
        rects = self._capture_qrectf_args(frame, comp)
        self.assertAlmostEqual(rects[0][3], 40.0 * 3.0)

    def test_bbox_width_after_cw_is_old_height_times_zoom(self):
        """Canonical check: new canvas_w = original composite.height × zoom."""
        zoom = 2.0
        frame = self._make_frame_with_viewport(zoom=zoom)
        comp = _make_real_composite(width=100.0, height=80.0)
        comp.rotate_clockwise()
        rects = self._capture_qrectf_args(frame, comp)
        # old height was 80; after CW it becomes the new width
        self.assertAlmostEqual(rects[0][2], 80.0 * zoom)

    def test_bbox_height_after_cw_is_old_width_times_zoom(self):
        """Canonical check: new canvas_h = original composite.width × zoom."""
        zoom = 2.0
        frame = self._make_frame_with_viewport(zoom=zoom)
        comp = _make_real_composite(width=100.0, height=80.0)
        comp.rotate_clockwise()
        rects = self._capture_qrectf_args(frame, comp)
        self.assertAlmostEqual(rects[0][3], 100.0 * zoom)

    def test_bbox_size_cw_then_ccw_restores_original_dims(self):
        """CW followed immediately by CCW must give the original bbox size."""
        frame = self._make_frame_with_viewport(zoom=1.0)
        comp = _make_real_composite(width=100.0, height=80.0)
        comp.rotate_clockwise()
        comp.rotate_counterclockwise()
        rects = self._capture_qrectf_args(frame, comp)
        self.assertAlmostEqual(rects[0][2], 100.0)
        self.assertAlmostEqual(rects[0][3], 80.0)

    def test_bbox_w_and_h_differ_for_non_square_composite(self):
        """Non-square composite must produce distinct width and height values."""
        frame = self._make_frame_with_viewport(zoom=1.0)
        comp = _make_real_composite(width=120.0, height=60.0)
        rects = self._capture_qrectf_args(frame, comp)
        self.assertNotAlmostEqual(rects[0][2], rects[0][3])

    def test_bbox_w_and_h_match_after_cw_rotation_for_non_square(self):
        """After CW on 120×60: canvas_w=60, canvas_h=120 (swapped)."""
        frame = self._make_frame_with_viewport(zoom=1.0)
        comp = _make_real_composite(width=120.0, height=60.0)
        comp.rotate_clockwise()
        rects = self._capture_qrectf_args(frame, comp)
        self.assertAlmostEqual(rects[0][2], 60.0)
        self.assertAlmostEqual(rects[0][3], 120.0)


# ===========================================================================

if __name__ == "__main__":
    unittest.main()

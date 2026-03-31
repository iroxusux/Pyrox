"""Canvas Services.
"""
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsScene
from pyrox.interfaces import IHasCanvas, IScene
from pyrox.services.scene import (
    HasSceneMixin
)

"""Gui Protocol Models.
"""


class HasCanvasMixin(IHasCanvas[QGraphicsScene]):
    def __init__(
        self,
        canvas: QGraphicsScene | None = None,
    ):
        self._canvas = canvas

    def get_canvas(self) -> QGraphicsScene | None:
        return self._canvas

    def set_canvas(self, canvas: QGraphicsScene) -> None:
        self._canvas = canvas

    @property
    def canvas(self) -> QGraphicsScene | None:
        return self.get_canvas()


class CanvasObjectManagmenentService(
    HasCanvasMixin,
    HasSceneMixin,
):
    def __init__(
        self,
        canvas: QGraphicsScene | None = None,
        scene: IScene | None = None,
        objects: dict[str, int] | None = None
    ):
        HasCanvasMixin.__init__(self, canvas)
        HasSceneMixin.__init__(self, scene)
        self._objects = objects if objects is not None else {}
        self._selected_objects: set[str] = set()

        # Selection state
        self._selection_color: str = "#ffaa00"  # Orange highlight for selection
        self._selection_width: int = 3

    def clear(self):
        """Clear all tracked canvas objects without deleting grid or other items."""
        if not self._canvas:
            return

        for item in list(self._canvas.items()):
            if item.data(0) in ("scene_object", "scene_object_label"):
                self._canvas.removeItem(item)
        self._objects.clear()

    def clear_selection(self):
        self._selected_objects.clear()

    def get_from_canvas_id(
        self,
        canvas_id: int
    ) -> str | None:
        for obj_id, c_id in self._objects.items():
            if c_id == canvas_id:
                return obj_id
        return None

    def get_non_grid_objects(
        self,
        pos: QPointF
    ) -> list[QGraphicsItem]:
        if not self._canvas:
            return []
        rect = QRectF(pos.x() - 2, pos.y() - 2, 4, 4)
        return [item for item in self._canvas.items(rect) if item.data(0) != "grid"]

    def set_object(
        self,
        scene_object_id: str,
        canvas_id: int
    ) -> None:
        self._objects[scene_object_id] = canvas_id

    def get_object(
        self,
        scene_object_id: str
    ) -> int | None:
        return self._objects.get(scene_object_id)

    def get_objects(self) -> dict[str, int]:
        return self._objects

    def remove_object(
        self,
        scene_object_id: str
    ) -> None:
        if scene_object_id in self._objects:
            del self._objects[scene_object_id]

    def deselect_object(
        self,
        obj_id: str
    ) -> None:
        if obj_id in self._selected_objects:
            self._selected_objects.remove(obj_id)

    def select_object(
        self,
        obj_id: str,
        clear_previous: bool = True
    ) -> None:
        if clear_previous:
            self.clear_selection()
        self._selected_objects.add(obj_id)

    def toggle_selection(
        self,
        obj_id: str
    ) -> None:
        if obj_id in self._selected_objects:
            self.deselect_object(obj_id)
        else:
            self.select_object(obj_id, clear_previous=False)

    @property
    def objects(self) -> dict[str, int]:
        return self.get_objects()

    @property
    def selected_objects(self) -> set[str]:
        return self._selected_objects

    @property
    def selected_objects_display(self) -> str:
        count = len(self._selected_objects)
        if count == 0:
            return "No selection"
        elif count == 1:
            return f"Selected: {list(self._selected_objects)[0]}"
        else:
            return f"Selected: {count} objects"

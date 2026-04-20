"""Object palette panel for the scene viewer, allowing users to select templates for placement in the scene.
"""
from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from pyrox.models.scene import SceneObjectFactory


class _SceneViewerObjectPalettePanel:
    """Manages the floating object palette window and template selection state."""

    def __init__(
        self,
        content_frame: QWidget,
        on_template_selected: Callable[[str, bool], None],
    ) -> None:
        self._content_frame = content_frame
        self._frame: QWidget | None = None
        self._visible: bool = False
        self._positioned: bool = False
        self._current_template: str | None = None
        self._current_template_is_scene_object: bool = False
        self._palette_content_widget: QWidget | None = None
        self._palette_content_layout: QVBoxLayout | None = None
        self._templates: dict = {}
        self._scene_object_templates: dict = {}

        # Public callback wired by SceneViewerFrame
        self.on_template_selected = on_template_selected

    # ---- properties ----

    @property
    def visible(self) -> bool:
        return self._visible

    @property
    def templates(self) -> dict:
        return self._templates

    @property
    def scene_object_templates(self) -> dict:
        return self._scene_object_templates

    def get_selected_template(self) -> tuple[str | None, bool]:
        """Return ``(template_name, is_scene_object)`` for the pending placement."""
        return self._current_template, self._current_template_is_scene_object

    def clear_template(self) -> None:
        """Clear the pending template selection after placement."""
        self._current_template = None
        self._current_template_is_scene_object = False

    # ---- lifecycle ----

    def build(self) -> '_SceneViewerObjectPalettePanel':
        """Build the floating palette tool window."""
        self._frame = QWidget(
            None,
            Qt.WindowType.Tool,
        )
        self._frame.setWindowTitle("Object Palette")
        self._frame.setMinimumSize(200, 300)
        self._frame.resize(220, 500)

        palette_layout = QVBoxLayout(self._frame)
        palette_layout.setContentsMargins(4, 4, 4, 4)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        palette_layout.addWidget(scroll_area)

        self._palette_content_widget = QWidget()
        self._palette_content_layout = QVBoxLayout(self._palette_content_widget)
        self._palette_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(self._palette_content_widget)

        self._frame.hide()
        return self

    # ---- visibility ----

    def show(self) -> None:
        if not self._frame:
            return
        if not self._positioned:
            global_top_left = self._content_frame.mapToGlobal(
                self._content_frame.rect().topLeft()
            )
            self._frame.move(global_top_left.x() + 10, global_top_left.y() + 40)
            self._positioned = True
        self._frame.show()
        self._frame.raise_()
        self._visible = True

    def hide(self) -> None:
        if self._frame:
            self._frame.hide()
        self._visible = False

    def toggle(self) -> None:
        self._visible = not self._visible
        if self._visible:
            self.show()
        else:
            self.hide()

    # ---- templates ----

    def initialize_templates(self) -> None:
        """Fetch all registered templates and populate the palette buttons."""
        if self._palette_content_layout is None or self._palette_content_widget is None:
            return

        # self._templates = PhysicsSceneFactory.get_all_templates()
        self._scene_object_templates = SceneObjectFactory.get_all_templates()

        # Clear any previously built buttons
        while self._palette_content_layout.count():
            item = self._palette_content_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()  # type: ignore[union-attr]

        # if self._templates:
        #     physics_label = QLabel("Physics Objects")
        #     physics_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        #     self._palette_content_layout.addWidget(physics_label)

        #     for template_name in self._templates:
        #         btn = QPushButton(text=template_name, parent=self._palette_content_widget)
        #         btn.clicked.connect(
        #             lambda _checked, name=template_name: self._on_template_button_clicked(name, False)
        #         )
        #         self._palette_content_layout.addWidget(btn)

        if self._scene_object_templates:
            scene_label = QLabel("Scene Objects")
            scene_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            self._palette_content_layout.addWidget(scene_label)

            for template_name in self._scene_object_templates:
                btn = QPushButton(text=template_name, parent=self._palette_content_widget)
                btn.clicked.connect(
                    lambda _checked, name=template_name: self._on_template_button_clicked(name, True)
                )
                self._palette_content_layout.addWidget(btn)

    def _on_template_button_clicked(self, template_name: str, is_scene_object: bool) -> None:
        self._current_template = template_name
        self._current_template_is_scene_object = is_scene_object
        if callable(self.on_template_selected):
            self.on_template_selected(template_name, is_scene_object)


__all__ = [
    '_SceneViewerObjectPalettePanel',
]

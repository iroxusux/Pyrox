from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QBoxLayout, QLabel, QWidget

from pyrox.models.gui.toolbar import ToolBar, ToolBarButton


class _SceneViewerToolbar:
    def __init__(
        self,
        parent: QWidget
    ):
        self._parent = parent

        # Public callbacks to be set by the SceneViewerFrame
        self.on_toggle_object_palette = lambda: None
        self.on_toggle_properties_panel = lambda: None
        self.on_toggle_bridge_panel = lambda: None
        self.on_toggle_object_explorer = lambda: None
        self.on_toggle_entity_names = lambda: None

    def build_toolbar(self) -> '_SceneViewerToolbar':
        """Build the toolbar with viewer controls.

        Returns:
            self, for chaining
        """
        if hasattr(self, '_widget') and self._widget is not None:
            self._widget.deleteLater()

        self._widget = ToolBar(
            self._parent,
            orientation=Qt.Orientation.Horizontal,
            height=34,
        )

        self._widget.add_button(ToolBarButton(
            id='object_palette',
            text='Object Palette',
            icon='🧰',
            icon_only=True,
            tooltip='Toggle Object Palette',
            command=lambda: self.on_toggle_object_palette(),
            width=32,
        ))
        self._widget.add_button(ToolBarButton(
            id='properties_panel',
            text='Properties Panel',
            icon='📋',
            icon_only=True,
            tooltip='Toggle Properties Panel',
            command=lambda: self.on_toggle_properties_panel(),
            width=32,
        ))
        self._widget.add_button(ToolBarButton(
            id='bridge_panel',
            text='Scene Bridge Panel',
            icon='🔗',
            icon_only=True,
            tooltip='Toggle Scene Bridge Panel',
            command=lambda: self.on_toggle_bridge_panel(),
            width=32,
        ))
        self._widget.add_button(ToolBarButton(
            id='object_explorer',
            text='Object Explorer',
            icon='🗂️',
            icon_only=True,
            tooltip='Toggle Object Explorer',
            command=lambda: self.on_toggle_object_explorer(),
            width=32,
        ))

        self._widget.add_separator()

        self._widget.add_button(ToolBarButton(
            id='entity_names',
            text='Entity Names',
            icon='🏷️',
            icon_only=True,
            tooltip='Toggle Entity Names',
            command=lambda: self.on_toggle_entity_names(),
            width=32,
        ))

        self._widget.add_separator()

        # Selection info label — inserted before the trailing stretch
        self._selection_label = QLabel('No selection', self._widget)
        toolbar_layout = self._widget.layout()
        if toolbar_layout is not None:
            toolbar_layout.insertWidget(toolbar_layout.count() - 1, self._selection_label)

        # Insert the toolbar widget at the top of the parent's layout
        parent_layout = self._parent.layout()
        if isinstance(parent_layout, QBoxLayout):
            parent_layout.insertWidget(0, self._widget)

        return self

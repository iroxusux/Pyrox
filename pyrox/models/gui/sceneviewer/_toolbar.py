from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QFrame, QBoxLayout


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

    def _call_callback(self, callback):
        if callable(callback):
            callback()

    @staticmethod
    def _make_separator(parent: QWidget) -> QFrame:
        sep = QFrame(parent)
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        return sep

    def build_toolbar(self) -> '_SceneViewerToolbar':
        """Build the toolbar with viewer controls.

        Returns:
            self, for chaining
        """
        if hasattr(self, '_widget') and self._widget is not None:
            self._widget.deleteLater()

        self._widget = QWidget(self._parent)
        layout = QHBoxLayout(self._widget)
        layout.setContentsMargins(5, 3, 5, 3)
        layout.setSpacing(2)

        # Object Palette Toggle Button
        self._object_palette_btn = QPushButton("🧰", self._widget)
        self._object_palette_btn.setFixedWidth(32)
        self._object_palette_btn.setToolTip("Toggle Object Palette")
        self._object_palette_btn.clicked.connect(
            lambda: self._call_callback(self.on_toggle_object_palette)
        )
        layout.addWidget(self._object_palette_btn)

        # Properties Panel Toggle Button
        self._properties_panel_btn = QPushButton("📋", self._widget)
        self._properties_panel_btn.setFixedWidth(32)
        self._properties_panel_btn.setToolTip("Toggle Properties Panel")
        self._properties_panel_btn.clicked.connect(
            lambda: self._call_callback(self.on_toggle_properties_panel)
        )
        layout.addWidget(self._properties_panel_btn)

        # Scene Bridge Panel Toggle Button
        self._bridge_panel_btn = QPushButton("🔗", self._widget)
        self._bridge_panel_btn.setFixedWidth(32)
        self._bridge_panel_btn.setToolTip("Toggle Scene Bridge Panel")
        self._bridge_panel_btn.clicked.connect(
            lambda: self._call_callback(self.on_toggle_bridge_panel)
        )
        layout.addWidget(self._bridge_panel_btn)

        # Object Explorer Toggle Button
        self._object_explorer_btn = QPushButton("🗂️", self._widget)
        self._object_explorer_btn.setFixedWidth(32)
        self._object_explorer_btn.setToolTip("Toggle Object Explorer")
        self._object_explorer_btn.clicked.connect(
            lambda: self._call_callback(self.on_toggle_object_explorer)
        )
        layout.addWidget(self._object_explorer_btn)

        layout.addWidget(self._make_separator(self._widget))

        # Entity Names Toggle Button
        self._entity_names_btn = QPushButton("🏷️", self._widget)
        self._entity_names_btn.setFixedWidth(32)
        self._entity_names_btn.setToolTip("Toggle Entity Names")
        self._entity_names_btn.clicked.connect(
            lambda: self._call_callback(self.on_toggle_entity_names)
        )
        layout.addWidget(self._entity_names_btn)

        layout.addWidget(self._make_separator(self._widget))

        # Selection info label
        self._selection_label = QLabel("No selection", self._widget)
        layout.addWidget(self._selection_label)

        layout.addStretch()

        # Insert the toolbar widget at the top of the parent's layout
        parent_layout = self._parent.layout()
        if isinstance(parent_layout, QBoxLayout):
            parent_layout.insertWidget(0, self._widget)

        return self

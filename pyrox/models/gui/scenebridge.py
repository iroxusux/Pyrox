"""GUI for Scene Bridge Management.

Provides a user interface for creating and managing bindings between
a source object and scene object properties.
"""
from __future__ import annotations

from typing import Any, Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMenu,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSplitter,
    QStatusBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pyrox.interfaces import BindingDirection, IScene, ISceneBinding, ISceneBridge
from pyrox.models.gui.frame import TaskFrame
from pyrox.models.scene.sceneboundlayer import SceneBoundLayer
from pyrox.services.logging import log


class SceneBridgeDialog(TaskFrame):
    """Dialog for managing Scene Bridge bindings.

    Allows users to:
    - View all configured bindings
    - Add new bindings between source keys and scene object properties
    - Remove or edit existing bindings
    - Enable/disable individual bindings
    - Start/stop bridge synchronisation
    """

    def __init__(
        self,
        parent,
        bridge: ISceneBridge,
        scene: Optional[IScene] = None,
    ):
        super().__init__(
            name='scene_bridge_dialog',
            parent=parent,
        )
        self.bridge = bridge
        self.scene = scene

        # content_frame already has a QVBoxLayout from TaskFrame — reuse it
        _existing = self.content_frame.layout()
        main_layout: QVBoxLayout = (
            _existing if isinstance(_existing, QVBoxLayout)
            else QVBoxLayout(self.content_frame)
        )
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._create_toolbar(main_layout)
        self._create_bindings_view(main_layout)
        self._create_status_bar(main_layout)

        self._refresh_bindings()
        self._update_status()
        self._schedule_refresh()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _create_toolbar(self, layout: QVBoxLayout):
        """Create toolbar with control buttons."""
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)

        # Bridge controls
        control_group = QGroupBox("Bridge Control")
        control_layout = QHBoxLayout(control_group)

        self.start_button = QPushButton("\u25b6 Start")
        self.start_button.setStyleSheet("background-color: lightgreen;")
        self.start_button.clicked.connect(self._start_bridge)
        control_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("\u23f9 Stop")
        self.stop_button.setStyleSheet("background-color: lightcoral;")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._stop_bridge)
        control_layout.addWidget(self.stop_button)

        toolbar_layout.addWidget(control_group)

        # Binding management
        binding_group = QGroupBox("Bindings")
        binding_layout = QHBoxLayout(binding_group)

        add_btn = QPushButton("\u2795 Add Binding")
        add_btn.clicked.connect(self._add_binding_dialog)
        binding_layout.addWidget(add_btn)

        edit_btn = QPushButton("\u270f Edit Selected")
        edit_btn.clicked.connect(self._edit_selected_binding)
        binding_layout.addWidget(edit_btn)

        remove_btn = QPushButton("\U0001f5d1 Remove Selected")
        remove_btn.clicked.connect(self._remove_selected_binding)
        binding_layout.addWidget(remove_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_all_bindings)
        binding_layout.addWidget(clear_btn)

        toolbar_layout.addWidget(binding_group)

        # Refresh
        refresh_btn = QPushButton("\U0001f504 Refresh")
        refresh_btn.clicked.connect(self._refresh_bindings)
        toolbar_layout.addWidget(refresh_btn)

        toolbar_layout.addStretch()
        layout.addWidget(toolbar)

    def _create_bindings_view(self, layout: QVBoxLayout):
        """Create tree widget for bindings."""
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            '\u2713', 'Binding Key', 'Direction', 'Scene Object',
            'Property', 'Source Value', 'Scene Value', 'Description',
        ])
        self.tree.setColumnWidth(0, 40)
        self.tree.setColumnWidth(1, 160)
        self.tree.setColumnWidth(2, 80)
        self.tree.setColumnWidth(3, 120)
        self.tree.setColumnWidth(4, 100)
        self.tree.setColumnWidth(5, 100)
        self.tree.setColumnWidth(6, 100)
        self.tree.setColumnWidth(7, 200)
        self.tree.setAlternatingRowColors(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemDoubleClicked.connect(self._toggle_binding_enabled)

        layout.addWidget(self.tree, 1)

    def _create_status_bar(self, layout: QVBoxLayout):
        """Create status bar."""
        self._status_bar = QStatusBar()
        self._status_bar.showMessage("Ready")
        layout.addWidget(self._status_bar)

    # ------------------------------------------------------------------
    # Data refresh / status
    # ------------------------------------------------------------------

    def _refresh_bindings(self):
        """Refresh the bindings display."""
        self.tree.clear()

        direction_icon = {
            BindingDirection.READ: "\u2192",
            BindingDirection.WRITE: "\u2190",
            BindingDirection.BOTH: "\u21c4",
        }

        for binding in self.bridge.get_bindings():
            enabled_icon = "\u2713" if binding.enabled else "\u2717"
            source_value = str(binding.last_source_value) if binding.last_source_value is not None else "N/A"
            scene_value = str(binding.last_scene_value) if binding.last_scene_value is not None else "N/A"

            item = QTreeWidgetItem([
                enabled_icon,
                binding.binding_key,
                direction_icon.get(binding.direction, "?"),
                binding.object_id,
                binding.property_path,
                source_value,
                scene_value,
                binding.description,
            ])
            self.tree.addTopLevelItem(item)

        self._update_status()

    def _update_status(self):
        """Update status bar and button states."""
        bindings = self.bridge.get_bindings()
        enabled_count = sum(1 for b in bindings if b.enabled)
        active_status = "ACTIVE" if self.bridge.is_active() else "STOPPED"

        self._status_bar.showMessage(
            f"{active_status} | {enabled_count}/{len(bindings)} bindings enabled"
        )

        if self.bridge.is_active():
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    # ------------------------------------------------------------------
    # Bridge control
    # ------------------------------------------------------------------

    def _start_bridge(self):
        """Start the bridge."""
        try:
            self.bridge.start()
            self._update_status()
            QMessageBox.information(self.root, "Bridge Started", "Scene bridge is now active")
        except Exception as e:
            QMessageBox.critical(self.root, "Error", f"Failed to start bridge: {e}")
            log(self).error(f"Failed to start bridge: {e}")

    def _stop_bridge(self):
        """Stop the bridge."""
        self.bridge.stop()
        self._update_status()
        QMessageBox.information(self.root, "Bridge Stopped", "Scene bridge has been stopped")

    # ------------------------------------------------------------------
    # Binding management
    # ------------------------------------------------------------------

    def _add_binding_dialog(self):
        """Show dialog to add a new binding."""
        dialog = AddBindingDialog(self.root, self.bridge, self.scene)
        dialog.exec()
        self._refresh_bindings()

    def _edit_selected_binding(self):
        """Edit the selected binding."""
        items = self.tree.selectedItems()
        if not items:
            QMessageBox.information(self.root, "No Selection", "Please select a binding to edit")
            return

        item = items[0]
        binding_key = item.text(1)
        object_id = item.text(3)
        property_path = item.text(4)

        matches = [
            b for b in self.bridge.get_bindings()
            if b.binding_key == binding_key
            and b.object_id == object_id
            and b.property_path == property_path
        ]

        if matches:
            dialog = EditBindingDialog(self.root, self.bridge, matches[0])
            dialog.exec()
            self._refresh_bindings()

    def _remove_selected_binding(self):
        """Remove the selected binding."""
        items = self.tree.selectedItems()
        if not items:
            QMessageBox.information(self.root, "No Selection", "Please select a binding to remove")
            return

        item = items[0]
        binding_key = item.text(1)
        object_id = item.text(3)
        property_path = item.text(4)

        reply = QMessageBox.question(
            self.root,
            "Confirm Remove",
            f"Remove binding '{binding_key}' \u2192 {object_id}.{property_path}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.bridge.remove_binding(binding_key, object_id, property_path)
            self._refresh_bindings()

    def _clear_all_bindings(self):
        """Clear all bindings."""
        reply = QMessageBox.question(
            self.root,
            "Confirm Clear",
            "Remove all bindings?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.bridge.clear_bindings()
            self._refresh_bindings()

    def _toggle_binding_enabled(self, item: QTreeWidgetItem, column: int):
        """Toggle enabled state of double-clicked binding."""
        binding_key = item.text(1)
        object_id = item.text(3)
        property_path = item.text(4)

        for binding in self.bridge.get_bindings():
            if (
                binding.binding_key == binding_key
                and binding.object_id == object_id
                and binding.property_path == property_path
            ):
                binding.enabled = not binding.enabled
                log(self).info(
                    f"Toggled binding '{binding_key}': "
                    f"{'enabled' if binding.enabled else 'disabled'}"
                )
                break

        self._refresh_bindings()

    def _show_context_menu(self, pos):
        """Show context menu on right-click."""
        item = self.tree.itemAt(pos)
        if item:
            self.tree.setCurrentItem(item)
            menu = QMenu(self.root)
            menu.addAction("Edit", self._edit_selected_binding)
            menu.addAction("Remove", self._remove_selected_binding)
            menu.addSeparator()
            menu.addAction("Toggle Enabled", lambda: self._toggle_binding_enabled(item, 0))
            viewport = self.tree.viewport()
            if viewport:
                menu.exec(viewport.mapToGlobal(pos))

    def _schedule_refresh(self):
        """Schedule periodic refresh."""
        self._refresh_timer = QTimer(self.root)
        self._refresh_timer.timeout.connect(self._on_timer)
        self._refresh_timer.start(1000)

    def _on_timer(self):
        """Handle periodic refresh timer."""
        if self.bridge.is_active():
            self._refresh_bindings()


# ---------------------------------------------------------------------------
# Add / Edit dialogs
# ---------------------------------------------------------------------------

class AddBindingDialog(QDialog):
    """Dialog for adding a new scene bridge binding.

    The form is split into two clearly labelled sections:

    * **External Source** — select a ``SceneBoundLayer`` source (e.g. *keyboard*,
      *plc*) and one of its public properties via :class:`ExternalSourceBrowserDialog`.
    * **Scene Destination** — select a :class:`~pyrox.interfaces.scene.ISceneObject`
      (or its ``physics_body``) and one of its properties via
      :class:`SceneObjectPropertyBrowserDialog`.

    Direction and an optional description round out the form.
    """

    def __init__(self, parent, bridge: ISceneBridge, scene: Optional[IScene]):
        super().__init__(parent)
        self.bridge = bridge
        self.scene = scene

        self.setWindowTitle("Add Scene Binding")
        self.setFixedSize(540, 400)
        self.setModal(True)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 8, 10, 8)

        # ── External Source section ───────────────────────────────────────────
        src_group = QGroupBox(" External Source ")
        src_layout = QHBoxLayout(src_group)

        src_form = QWidget()
        src_form_layout = QHBoxLayout(src_form)
        src_form_layout.setContentsMargins(0, 0, 0, 0)
        src_form_layout.addWidget(QLabel("Binding Key:"))
        self.key_entry = QLineEdit()
        src_form_layout.addWidget(self.key_entry, 1)
        browse_ext_btn = QPushButton("Browse\u2026")
        browse_ext_btn.clicked.connect(self._browse_external)
        src_form_layout.addWidget(browse_ext_btn)
        src_layout.addWidget(src_form)
        outer_layout.addWidget(src_group)

        # ── Scene Destination section ─────────────────────────────────────────
        dst_group = QGroupBox(" Scene Destination ")
        dst_layout = QVBoxLayout(dst_group)

        obj_row = QWidget()
        obj_row_layout = QHBoxLayout(obj_row)
        obj_row_layout.setContentsMargins(0, 0, 0, 0)
        obj_row_layout.addWidget(QLabel("Object ID:"))
        self.object_entry = QLineEdit()
        obj_row_layout.addWidget(self.object_entry, 1)
        browse_scene_btn = QPushButton("Browse\u2026")
        browse_scene_btn.clicked.connect(self._browse_scene)
        obj_row_layout.addWidget(browse_scene_btn)
        dst_layout.addWidget(obj_row)

        prop_row = QWidget()
        prop_row_layout = QHBoxLayout(prop_row)
        prop_row_layout.setContentsMargins(0, 0, 0, 0)
        prop_row_layout.addWidget(QLabel("Property:"))
        self.property_entry = QLineEdit()
        self.property_entry.setReadOnly(True)
        prop_row_layout.addWidget(self.property_entry, 1)
        dst_layout.addWidget(prop_row)
        outer_layout.addWidget(dst_group)

        # ── Direction row ─────────────────────────────────────────────────────
        dir_row = QWidget()
        dir_layout = QHBoxLayout(dir_row)
        dir_layout.setContentsMargins(0, 0, 0, 0)
        dir_layout.addWidget(QLabel("Direction:"))
        self._direction_group = QButtonGroup(self)
        for i, (label, value) in enumerate((
            ("External \u2192 Scene", "read"),
            ("Scene \u2192 External", "write"),
            ("Both", "both"),
        )):
            rb = QRadioButton(label)
            rb.setProperty("direction_value", value)
            if i == 0:
                rb.setChecked(True)
            self._direction_group.addButton(rb)
            dir_layout.addWidget(rb)
        dir_layout.addStretch()
        outer_layout.addWidget(dir_row)

        # ── Description row ───────────────────────────────────────────────────
        desc_row = QWidget()
        desc_layout = QHBoxLayout(desc_row)
        desc_layout.setContentsMargins(0, 0, 0, 0)
        desc_layout.addWidget(QLabel("Description:"))
        self.description_entry = QLineEdit()
        desc_layout.addWidget(self.description_entry, 1)
        outer_layout.addWidget(desc_row)

        outer_layout.addStretch()

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        add_btn = QPushButton("Add Binding")
        add_btn.clicked.connect(self._add_binding)
        btn_layout.addWidget(add_btn)
        outer_layout.addWidget(btn_row)

    # ------------------------------------------------------------------
    # Browse helpers
    # ------------------------------------------------------------------

    def _browse_external(self) -> None:
        """Open the external-source browser and fill the *Binding Key* entry."""
        bound_obj = self.bridge.get_bound_object()
        if isinstance(bound_obj, SceneBoundLayer):
            dialog = ExternalSourceBrowserDialog(self, bound_obj)
            dialog.exec()
            if hasattr(dialog, 'selected_item'):
                self.key_entry.setText(dialog.selected_item)
        else:
            existing_keys = sorted({b.binding_key for b in self.bridge.get_bindings()})
            if not existing_keys:
                QMessageBox.information(
                    self,
                    "No Keys",
                    "No binding keys available.\n"
                    "Register a SceneBoundLayer as the bound object to "
                    "browse available source properties.",
                )
                return
            dialog = ItemSelectionDialog(self, "Select Binding Key", existing_keys)
            dialog.exec()
            if hasattr(dialog, 'selected_item'):
                self.key_entry.setText(dialog.selected_item)

    def _browse_scene(self) -> None:
        """Open the scene-object property browser and fill *Object ID* + *Property*."""
        if not self.scene:
            QMessageBox.warning(self, "No Scene", "No scene is loaded.")
            return

        dialog = SceneObjectPropertyBrowserDialog(self, self.scene)
        dialog.exec()

        if hasattr(dialog, 'selected_object_id'):
            self.object_entry.setText(dialog.selected_object_id)
        if hasattr(dialog, 'selected_property'):
            self.property_entry.setReadOnly(False)
            self.property_entry.setText(dialog.selected_property)
            self.property_entry.setReadOnly(True)

    # ------------------------------------------------------------------
    # Commit
    # ------------------------------------------------------------------

    def _add_binding(self) -> None:
        """Validate entries and call add_binding."""
        binding_key = self.key_entry.text().strip()
        object_id = self.object_entry.text().strip()
        property_path = self.property_entry.text().strip()

        if not binding_key or not object_id or not property_path:
            QMessageBox.critical(self, "Missing Fields", "Please fill in all required fields.")
            return

        checked_btn = self._direction_group.checkedButton()
        direction = BindingDirection(checked_btn.property("direction_value") if checked_btn else "read")
        description = self.description_entry.text().strip()

        try:
            self.bridge.add_binding(
                binding_key=binding_key,
                object_id=object_id,
                property_path=property_path,
                direction=direction,
                description=description,
            )
            QMessageBox.information(self, "Success", "Binding added successfully.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add binding: {e}")


class EditBindingDialog(QDialog):
    """Dialog for editing an existing binding."""

    def __init__(self, parent, bridge: ISceneBridge, binding: ISceneBinding):
        super().__init__(parent)
        self.bridge = bridge
        self.binding = binding

        self.setWindowTitle("Edit Binding")
        self.setFixedSize(400, 280)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        layout.addWidget(QLabel(f"Key:      {binding.binding_key}"))
        layout.addWidget(QLabel(f"Object:   {binding.object_id}"))
        layout.addWidget(QLabel(f"Property: {binding.property_path}"))

        layout.addWidget(QLabel("Description:"))
        self.description_entry = QLineEdit(binding.description)
        self.description_entry.setMinimumWidth(300)
        layout.addWidget(self.description_entry)

        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(binding.enabled)
        layout.addWidget(self.enabled_check)

        layout.addStretch()

        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        layout.addWidget(btn_row)

    def _save(self):
        """Persist edits to the binding."""
        self.binding.description = self.description_entry.text()
        self.binding.enabled = self.enabled_check.isChecked()
        QMessageBox.information(self, "Success", "Binding updated")
        self.accept()


# ---------------------------------------------------------------------------
# External source browser (SceneBoundLayer → source → property)
# ---------------------------------------------------------------------------

class ExternalSourceBrowserDialog(QDialog):
    """Two-pane browser for selecting a binding key from a
    :class:`~pyrox.models.scene.sceneboundlayer.SceneBoundLayer`.

    * **Left pane** — listbox of registered source names (e.g. ``"plc"``,
      ``"keyboard"``, ``"sim"``).  Selecting a source populates the right
      pane with that source's inspectable public properties.
    * **Right pane** — treeview showing ``Property`` name and ``Type``
      columns, introspected from the actual source object so the user can
      see at a glance what kind of value each property holds.

    Closing via *Select* stores the composed ``"source.property"`` string in
    ``self.selected_item``.
    """

    def __init__(self, parent, layer: SceneBoundLayer) -> None:
        super().__init__(parent)
        self.layer = layer
        self.setWindowTitle("Browse External Sources")
        self.resize(580, 380)
        self.setModal(True)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(
            "Select a source (left), then a property (right), then click Select."
        ))

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left — source list
        left_group = QGroupBox("Sources")
        left_layout = QVBoxLayout(left_group)
        self._source_list = QListWidget()
        self._source_list.currentRowChanged.connect(self._on_source_selected)
        left_layout.addWidget(self._source_list)
        for name in layer.list_sources():
            self._source_list.addItem(name)
        splitter.addWidget(left_group)
        splitter.setStretchFactor(0, 0)

        # Right — property tree
        right_group = QGroupBox("Properties")
        right_layout = QVBoxLayout(right_group)
        self._prop_tree = QTreeWidget()
        self._prop_tree.setHeaderLabels(["Property", "Type"])
        prop_header = self._prop_tree.header()
        if prop_header:
            prop_header.setStretchLastSection(False)
        self._prop_tree.setColumnWidth(1, 80)
        self._prop_tree.itemDoubleClicked.connect(lambda _i, _c: self._select())
        right_layout.addWidget(self._prop_tree)
        splitter.addWidget(right_group)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

        # Preview
        self._preview_label = QLabel("")
        layout.addWidget(self._preview_label)

        # Buttons
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(self._select)
        btn_layout.addWidget(select_btn)
        layout.addWidget(btn_row)

        # Pre-select first source
        if layer.list_sources():
            self._source_list.setCurrentRow(0)

    def _on_source_selected(self, row: int) -> None:
        """Populate the property pane for the currently selected source."""
        if row < 0:
            return
        list_item = self._source_list.item(row)
        if list_item is None:
            return
        source_name = list_item.text()
        source_obj = self.layer.get_source(source_name)

        self._prop_tree.clear()
        props = self.layer.enumerate_source_properties(source_name)
        for prop in props:
            try:
                val = (
                    source_obj[prop]
                    if isinstance(source_obj, dict)
                    else getattr(source_obj, prop)
                )
                type_name = type(val).__name__
            except Exception:
                type_name = '?'
            QTreeWidgetItem(self._prop_tree, [prop, type_name])

        self._preview_label.setText(
            f"source: {source_name}  \u2014  select a property"
            if props else f"source: {source_name}  \u2014  (no public properties)"
        )

    def _on_prop_selected(self) -> None:
        """Update the preview label."""
        src_item = self._source_list.currentItem()
        prop_items = self._prop_tree.selectedItems()
        if src_item and prop_items:
            src = src_item.text()
            prop = prop_items[0].text(0)
            self._preview_label.setText(f"key: {src}.{prop}")

    def _select(self) -> None:
        """Compose and store the selected binding key, then close."""
        src_item = self._source_list.currentItem()
        prop_items = self._prop_tree.selectedItems()
        if not src_item:
            QMessageBox.warning(self, "No Source", "Please select a source first")
            return
        if not prop_items:
            QMessageBox.warning(self, "No Property", "Please select a property first")
            return
        self.selected_item = f"{src_item.text()}.{prop_items[0].text(0)}"
        self.accept()


# ---------------------------------------------------------------------------
# Scene object + property browser
# ---------------------------------------------------------------------------

class SceneObjectPropertyBrowserDialog(QDialog):
    """Browser for selecting a scene object (or its physics body) and a property.

    * **Left pane** — treeview of scene objects grouped by
      ``scene_object_type``, with a live search bar.  Each object node
      exposes a ``⚙ Physics Body`` child when a physics body is present,
      allowing properties on either the scene object itself *or* its
      associated physics body to be selected.
    * **Right pane** — treeview showing ``Property`` and ``Type`` columns,
      introspected from whichever node (scene object or physics body) is
      currently selected on the left.

    After *Select*:
    * ``self.selected_object_id`` — the scene object's ID string.
    * ``self.selected_property``  — the property path.  For physics body
      properties this is automatically prefixed: ``"physics_body.{name}"``.
    """

    _TAG_GROUP = 'group'
    _TAG_OBJECT = 'object'
    _TAG_PHYSICS = 'physics'

    def __init__(self, parent, scene: IScene) -> None:
        super().__init__(parent)
        self.scene = scene
        self.setWindowTitle("Browse Scene Destination")
        self.resize(660, 440)
        self.setModal(True)

        # iid → (object_id: str, target_obj: Any, is_physics_body: bool)
        self._node_map: dict[int, tuple[str, Any, bool]] = {}

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(
            "Select an object or its \u2699 Physics Body (left), "
            "then a property (right), then click Select."
        ))

        # -- Search bar --------------------------------------------------------
        search_row = QWidget()
        search_layout = QHBoxLayout(search_row)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.addWidget(QLabel("\U0001f50d"))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Filter objects…")
        self._search_edit.textChanged.connect(lambda _: self._populate_objects())
        search_layout.addWidget(self._search_edit, 1)
        layout.addWidget(search_row)

        # -- Two panes ---------------------------------------------------------
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left — scene object tree
        left_group = QGroupBox("Scene Objects")
        left_layout = QVBoxLayout(left_group)
        self._obj_tree = QTreeWidget()
        self._obj_tree.setHeaderHidden(True)
        self._obj_tree.itemSelectionChanged.connect(self._on_node_selected)
        left_layout.addWidget(self._obj_tree)
        splitter.addWidget(left_group)

        # Right — property tree
        right_group = QGroupBox("Properties")
        right_layout = QVBoxLayout(right_group)
        self._prop_tree = QTreeWidget()
        self._prop_tree.setHeaderLabels(["Property", "Type"])
        scene_prop_header = self._prop_tree.header()
        if scene_prop_header:
            scene_prop_header.setStretchLastSection(False)
        self._prop_tree.setColumnWidth(1, 80)
        self._prop_tree.itemSelectionChanged.connect(self._on_prop_selected)
        self._prop_tree.itemDoubleClicked.connect(lambda _i, _c: self._select())
        right_layout.addWidget(self._prop_tree)
        splitter.addWidget(right_group)

        layout.addWidget(splitter, 1)

        # Preview
        self._preview_label = QLabel("")
        layout.addWidget(self._preview_label)

        # Buttons
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(self._select)
        btn_layout.addWidget(select_btn)
        layout.addWidget(btn_row)

        self._populate_objects()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_objects(self) -> list:
        """Return a flat list of scene objects from the scene."""
        if hasattr(self.scene, 'get_scene_objects'):
            result = self.scene.get_scene_objects()
            if isinstance(result, dict):
                return list(result.values())
            return list(result) if result else []
        return list(getattr(self.scene, 'scene_objects', {}).values())

    @staticmethod
    def _label(obj: Any) -> str:
        if hasattr(obj, 'get_name'):
            return obj.get_name()
        return getattr(obj, 'id', str(obj))

    # ------------------------------------------------------------------
    # Left-pane population
    # ------------------------------------------------------------------

    def _populate_objects(self) -> None:
        """Rebuild the object treeview from the current scene."""
        self._obj_tree.clear()
        self._prop_tree.clear()
        self._node_map.clear()
        self._preview_label.setText("")

        objects = self._get_objects()
        if not objects:
            return

        filter_text = self._search_edit.text().lower().strip()

        groups: dict[str, list] = {}
        for obj in objects:
            obj_type = (
                getattr(obj, 'scene_object_type', None)
                or getattr(obj, '_scene_object_type', None)
                or 'Unknown'
            )
            groups.setdefault(obj_type, []).append(obj)

        bold_font = QFont()
        bold_font.setBold(True)
        italic_font = QFont()
        italic_font.setItalic(True)

        for group_name, members in sorted(groups.items()):
            matching = [
                obj for obj in members
                if not filter_text or filter_text in self._label(obj).lower()
            ]
            if not matching:
                continue

            group_item = QTreeWidgetItem(self._obj_tree, [f"{group_name}  ({len(matching)})"])
            group_item.setFont(0, bold_font)
            group_item.setExpanded(True)
            group_item.setFlags(group_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)

            for obj in sorted(matching, key=lambda o: self._label(o).lower()):
                obj_id = getattr(obj, 'get_id', lambda: getattr(obj, 'id', str(obj)))()
                obj_item = QTreeWidgetItem(group_item, [self._label(obj)])
                self._node_map[id(obj_item)] = (obj_id, obj, False)

                # Expose physics body as a selectable child node
                physics_body = getattr(obj, 'physics_body', None)
                if physics_body is not None:
                    pb_item = QTreeWidgetItem(obj_item, ["\u2699 Physics Body"])
                    pb_item.setFont(0, italic_font)
                    pb_item.setForeground(0, pb_item.foreground(0))
                    self._node_map[id(pb_item)] = (obj_id, physics_body, True)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_node_selected(self) -> None:
        """Populate the property pane for the selected object or physics body."""
        selected = self._obj_tree.selectedItems()
        if not selected:
            return
        sel_item = selected[0]
        node_id = id(sel_item)
        if node_id not in self._node_map:
            return  # group header

        obj_id, target_obj, is_physics = self._node_map[node_id]

        self._prop_tree.clear()
        props = SceneBoundLayer._inspect_properties(target_obj)
        for prop in props:
            try:
                val = getattr(target_obj, prop)
                type_name = type(val).__name__
            except Exception:
                type_name = '?'
            QTreeWidgetItem(self._prop_tree, [prop, type_name])

        target_label = "physics_body" if is_physics else "object"
        self._preview_label.setText(
            f"object: {obj_id}  \u2014  target: {target_label}  \u2014  select a property"
            if props
            else f"object: {obj_id}  \u2014  target: {target_label}  \u2014  (no public properties)"
        )

    def _on_prop_selected(self) -> None:
        """Update the preview label."""
        obj_sel = self._obj_tree.selectedItems()
        prop_sel = self._prop_tree.selectedItems()
        if obj_sel and prop_sel:
            node_id = id(obj_sel[0])
            if node_id in self._node_map:
                obj_id, _, is_physics = self._node_map[node_id]
                prop = prop_sel[0].text(0)
                full_prop = f"physics_body.{prop}" if is_physics else prop
                self._preview_label.setText(f"object: {obj_id}  \u2014  property: {full_prop}")

    def _select(self) -> None:
        """Validate selection, compose results, and close."""
        obj_sel = self._obj_tree.selectedItems()
        if not obj_sel or id(obj_sel[0]) not in self._node_map:
            QMessageBox.warning(
                self,
                "No Object",
                "Please select an object or its Physics Body node first.",
            )
            return
        prop_sel = self._prop_tree.selectedItems()
        if not prop_sel:
            QMessageBox.warning(self, "No Property", "Please select a property first")
            return

        obj_id, _, is_physics = self._node_map[id(obj_sel[0])]
        prop = prop_sel[0].text(0)
        self.selected_object_id: str = obj_id
        self.selected_property: str = f"physics_body.{prop}" if is_physics else prop
        self.accept()


class ItemSelectionDialog(QDialog):
    """Generic single-item selection dialog backed by a list widget."""

    def __init__(self, parent, title: str, items: list[str]):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(420, 300)
        self.setModal(True)

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        for item in items:
            self.list_widget.addItem(item)
        self.list_widget.itemDoubleClicked.connect(self._select)
        layout.addWidget(self.list_widget, 1)

        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(self._select)
        btn_layout.addWidget(select_btn)
        layout.addWidget(btn_row)

    def _select(self):
        """Confirm selection and close."""
        items = self.list_widget.selectedItems()
        if items:
            self.selected_item = items[0].text()
            self.accept()


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def create_demo_window():
    """Create a standalone demo window for :class:`SceneBridgeDialog`.

    Builds lightweight mock implementations of :class:`~pyrox.interfaces.ISceneBridge`,
    :class:`~pyrox.interfaces.ISceneBinding`, and :class:`~pyrox.interfaces.IScene`
    so every panel feature (add / edit / remove / toggle / start / stop, periodic
    refresh) can be exercised without a live scene engine.

    The demo also wires up a real :class:`~pyrox.models.scene.SceneBoundLayer`
    with two registered sources (``plc`` and ``keyboard``) so the
    :class:`ExternalSourceBrowserDialog` fully exercises its two-pane source/property
    treeview.  Scene objects carry ``scene_object_type`` attributes and several
    have a mock ``physics_body`` so the :class:`SceneObjectPropertyBrowserDialog`
    physics-body child nodes are exercised as well.

    Returns:
        QWidget: The configured root widget (caller must show and exec the app).
    """
    import sys
    from types import SimpleNamespace
    from PyQt6.QtWidgets import QApplication

    # ------------------------------------------------------------------
    # Mock binding
    # ------------------------------------------------------------------

    class _MockBinding:
        def __init__(
            self,
            key: str,
            object_id: str,
            property_path: str,
            direction: BindingDirection = BindingDirection.READ,
            description: str = "",
            enabled: bool = True,
            source_val: Any = None,
            scene_val: Any = None,
        ) -> None:
            self.binding_key = key
            self.object_id = object_id
            self.property_path = property_path
            self.direction = direction
            self.description = description
            self.enabled = enabled
            self.last_source_value = source_val
            self.last_scene_value = scene_val

    # ------------------------------------------------------------------
    # Mock physics body
    # ------------------------------------------------------------------

    class _MockPhysicsBody:
        def __init__(self) -> None:
            self.mass_kg: float = 10.0
            self.velocity_x: float = 0.0
            self.velocity_y: float = 0.0
            self.is_static: bool = False
            self.collisions_enabled: bool = True

    # ------------------------------------------------------------------
    # Typed mock scene objects
    # ------------------------------------------------------------------

    class _MockConveyor:
        scene_object_type = "Conveyor"

        def __init__(self, obj_id: str) -> None:
            self._id = obj_id
            self.speed_m_s: float = 0.0
            self.enabled: bool = False
            self.belt_tension_n: float = 4.2
            self.physics_body = _MockPhysicsBody()

        def get_id(self) -> str:
            return self._id

        def get_name(self) -> str:
            return self._id

    class _MockSensor:
        scene_object_type = "Sensor"

        def __init__(self, obj_id: str) -> None:
            self._id = obj_id
            self.active: bool = False
            self.signal_strength: float = 0.0
            self.physics_body = None

        def get_id(self) -> str:
            return self._id

        def get_name(self) -> str:
            return self._id

    class _MockRobot:
        scene_object_type = "Robot"

        def __init__(self, obj_id: str) -> None:
            self._id = obj_id
            self.max_speed_mm_s: float = 500.0
            self.current_speed_mm_s: float = 0.0
            self.tool_active: bool = False
            self.physics_body = _MockPhysicsBody()

        def get_id(self) -> str:
            return self._id

        def get_name(self) -> str:
            return self._id

    # ------------------------------------------------------------------
    # Mock scene
    # ------------------------------------------------------------------

    class _MockScene:
        def __init__(self, objects: list) -> None:
            self._objects = objects

        def get_scene_objects(self) -> list:
            return list(self._objects)

    # ------------------------------------------------------------------
    # Mock bridge
    # ------------------------------------------------------------------

    class _MockBridge:
        def __init__(self, bindings: list[_MockBinding], bound_layer: SceneBoundLayer) -> None:
            self._bindings: list[_MockBinding] = list(bindings)
            self._active = False
            self._bound_layer = bound_layer

        def get_bindings(self) -> list[_MockBinding]:
            return list(self._bindings)

        def is_active(self) -> bool:
            return self._active

        def start(self) -> None:
            self._active = True

        def stop(self) -> None:
            self._active = False

        def get_bound_object(self) -> SceneBoundLayer:
            return self._bound_layer

        def add_binding(
            self,
            binding_key: str,
            object_id: str,
            property_path: str,
            direction: BindingDirection = BindingDirection.READ,
            description: str = "",
        ) -> None:
            self._bindings.append(_MockBinding(
                binding_key, object_id, property_path,
                direction, description,
            ))

        def remove_binding(
            self, binding_key: str, object_id: str, property_path: str
        ) -> None:
            self._bindings = [
                b for b in self._bindings
                if not (
                    b.binding_key == binding_key
                    and b.object_id == object_id
                    and b.property_path == property_path
                )
            ]

        def clear_bindings(self) -> None:
            self._bindings.clear()

    # ------------------------------------------------------------------
    # Real SceneBoundLayer with two named sources
    # ------------------------------------------------------------------

    _plc_source = SimpleNamespace(
        conveyor_speed=1.25,
        conveyor_enabled=True,
        sensor_active=False,
        robot_speed=800.0,
        estop_active=False,
    )
    _keyboard_source = SimpleNamespace(
        key_w=False,
        key_s=False,
        key_a=False,
        key_d=False,
        key_space=False,
        speed_multiplier=1.0,
    )

    _bound_layer = SceneBoundLayer()
    _bound_layer.register_source("plc", _plc_source)
    _bound_layer.register_source("keyboard", _keyboard_source)

    # ------------------------------------------------------------------
    # Seed data
    # ------------------------------------------------------------------

    _mock_scene = _MockScene([
        _MockConveyor("conv_001"),
        _MockConveyor("conv_002"),
        _MockSensor("sens_001"),
        _MockRobot("rob_001"),
        _MockRobot("rob_002"),
    ])

    _mock_bridge = _MockBridge(
        bound_layer=_bound_layer,
        bindings=[
            _MockBinding(
                key="plc.conveyor_speed",
                object_id="conv_001",
                property_path="speed_m_s",
                direction=BindingDirection.READ,
                description="Conveyor A belt speed",
                enabled=True,
                source_val=1.25,
                scene_val=1.25,
            ),
            _MockBinding(
                key="plc.conveyor_enabled",
                object_id="conv_001",
                property_path="enabled",
                direction=BindingDirection.BOTH,
                description="Conveyor A run command",
                enabled=True,
                source_val=True,
                scene_val=True,
            ),
            _MockBinding(
                key="plc.sensor_active",
                object_id="sens_001",
                property_path="active",
                direction=BindingDirection.READ,
                description="Entry gate proximity sensor",
                enabled=False,
                source_val=False,
                scene_val=None,
            ),
            _MockBinding(
                key="plc.robot_speed",
                object_id="rob_001",
                property_path="max_speed_mm_s",
                direction=BindingDirection.WRITE,
                description="Robot A maximum speed setpoint",
                enabled=True,
                source_val=None,
                scene_val=800,
            ),
            _MockBinding(
                key="keyboard.key_w",
                object_id="rob_002",
                property_path="physics_body.velocity_y",
                direction=BindingDirection.READ,
                description="Drive robot B forward with W key",
                enabled=True,
                source_val=False,
                scene_val=0.0,
            ),
        ],
    )

    # ------------------------------------------------------------------
    # Root window + dialog
    # ------------------------------------------------------------------

    app = QApplication.instance() or QApplication(sys.argv)
    root = QWidget()
    root.setWindowTitle("SceneBridgeDialog — Demo")
    root.resize(980, 460)

    root_layout = QVBoxLayout(root)
    root_layout.setContentsMargins(8, 8, 8, 8)

    dialog = SceneBridgeDialog(
        parent=root,
        bridge=_mock_bridge,   # type: ignore[arg-type]
        scene=_mock_scene,     # type: ignore[arg-type]
    )
    root_layout.addWidget(dialog.root)

    return root, app


if __name__ == "__main__":
    import sys
    demo_root, app = create_demo_window()
    demo_root.show()
    sys.exit(app.exec())

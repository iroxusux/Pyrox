"""GUI for Scene Bridge Management.

Provides a user interface for creating and managing bindings between
a source object and scene object properties.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Optional

from pyrox.interfaces import BindingDirection, IScene, ISceneBinding, ISceneBridge
from pyrox.models.gui.tk.frame import TkinterTaskFrame
from pyrox.models.scene.sceneboundlayer import SceneBoundLayer
from pyrox.services.logging import log


class SceneBridgeDialog(TkinterTaskFrame):
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

        self._create_toolbar()
        self._create_bindings_view()
        self._create_status_bar()

        self._refresh_bindings()
        self._update_status()
        self._schedule_refresh()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _create_toolbar(self):
        """Create toolbar with control buttons."""
        toolbar = tk.Frame(self.content_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Bridge controls
        control_frame = tk.LabelFrame(toolbar, text="Bridge Control")
        control_frame.pack(side=tk.LEFT, padx=2)

        self.start_button = tk.Button(
            control_frame,
            text="\u25b6 Start",
            command=self._start_bridge,
            bg="lightgreen",
        )
        self.start_button.pack(side=tk.LEFT, padx=2)

        self.stop_button = tk.Button(
            control_frame,
            text="\u23f9 Stop",
            command=self._stop_bridge,
            bg="lightcoral",
            state=tk.DISABLED,
        )
        self.stop_button.pack(side=tk.LEFT, padx=2)

        # Binding management
        binding_frame = tk.LabelFrame(toolbar, text="Bindings")
        binding_frame.pack(side=tk.LEFT, padx=2)

        tk.Button(
            binding_frame,
            text="\u2795 Add Binding",
            command=self._add_binding_dialog,
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            binding_frame,
            text="\u270f Edit Selected",
            command=self._edit_selected_binding,
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            binding_frame,
            text="\U0001f5d1 Remove Selected",
            command=self._remove_selected_binding,
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            binding_frame,
            text="Clear All",
            command=self._clear_all_bindings,
        ).pack(side=tk.LEFT, padx=2)

        # Refresh
        tk.Button(
            toolbar,
            text="\U0001f504 Refresh",
            command=self._refresh_bindings,
        ).pack(side=tk.LEFT, padx=5)

    def _create_bindings_view(self):
        """Create treeview for bindings."""
        view_frame = tk.Frame(self.content_frame)
        view_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        vsb = ttk.Scrollbar(view_frame, orient="vertical")
        hsb = ttk.Scrollbar(view_frame, orient="horizontal")

        self.tree = ttk.Treeview(
            view_frame,
            columns=('Enabled', 'Key', 'Direction', 'Object', 'Property', 'SourceValue', 'SceneValue', 'Description'),
            show='headings',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
        )

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        self.tree.heading('Enabled', text='\u2713')
        self.tree.heading('Key', text='Binding Key')
        self.tree.heading('Direction', text='Direction')
        self.tree.heading('Object', text='Scene Object')
        self.tree.heading('Property', text='Property')
        self.tree.heading('SourceValue', text='Source Value')
        self.tree.heading('SceneValue', text='Scene Value')
        self.tree.heading('Description', text='Description')

        self.tree.column('Enabled', width=40)
        self.tree.column('Key', width=160)
        self.tree.column('Direction', width=80)
        self.tree.column('Object', width=120)
        self.tree.column('Property', width=100)
        self.tree.column('SourceValue', width=100)
        self.tree.column('SceneValue', width=100)
        self.tree.column('Description', width=200)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        view_frame.grid_rowconfigure(0, weight=1)
        view_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind('<Button-3>', self._show_context_menu)
        self.tree.bind('<Double-Button-1>', self._toggle_binding_enabled)

    def _create_status_bar(self):
        """Create status bar."""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(
            self.content_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ------------------------------------------------------------------
    # Data refresh / status
    # ------------------------------------------------------------------

    def _refresh_bindings(self):
        """Refresh the bindings display."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        direction_icon = {
            BindingDirection.READ: "\u2192",
            BindingDirection.WRITE: "\u2190",
            BindingDirection.BOTH: "\u21c4",
        }

        for binding in self.bridge.get_bindings():
            enabled_icon = "\u2713" if binding.enabled else "\u2717"
            source_value = str(binding.last_source_value) if binding.last_source_value is not None else "N/A"
            scene_value = str(binding.last_scene_value) if binding.last_scene_value is not None else "N/A"

            self.tree.insert('', tk.END, values=(
                enabled_icon,
                binding.binding_key,
                direction_icon.get(binding.direction, "?"),
                binding.object_id,
                binding.property_path,
                source_value,
                scene_value,
                binding.description,
            ))

        self._update_status()

    def _update_status(self):
        """Update status bar and button states."""
        bindings = self.bridge.get_bindings()
        enabled_count = sum(1 for b in bindings if b.enabled)
        active_status = "ACTIVE" if self.bridge.is_active() else "STOPPED"

        self.status_var.set(
            f"{active_status} | {enabled_count}/{len(bindings)} bindings enabled"
        )

        if self.bridge.is_active():
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Bridge control
    # ------------------------------------------------------------------

    def _start_bridge(self):
        """Start the bridge."""
        try:
            self.bridge.start()
            self._update_status()
            messagebox.showinfo("Bridge Started", "Scene bridge is now active")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start bridge: {e}")
            log(self).error(f"Failed to start bridge: {e}")

    def _stop_bridge(self):
        """Stop the bridge."""
        self.bridge.stop()
        self._update_status()
        messagebox.showinfo("Bridge Stopped", "Scene bridge has been stopped")

    # ------------------------------------------------------------------
    # Binding management
    # ------------------------------------------------------------------

    def _add_binding_dialog(self):
        """Show dialog to add a new binding."""
        dialog = AddBindingDialog(self.root, self.bridge, self.scene)
        self.root.wait_window(dialog)
        self._refresh_bindings()

    def _edit_selected_binding(self):
        """Edit the selected binding."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a binding to edit")
            return

        item = self.tree.item(selection[0])
        binding_key = item['values'][1]
        object_id = item['values'][3]
        property_path = item['values'][4]

        matches = [
            b for b in self.bridge.get_bindings()
            if b.binding_key == binding_key
            and b.object_id == object_id
            and b.property_path == property_path
        ]

        if matches:
            dialog = EditBindingDialog(self.root, self.bridge, matches[0])
            self.root.wait_window(dialog)
            self._refresh_bindings()

    def _remove_selected_binding(self):
        """Remove the selected binding."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a binding to remove")
            return

        item = self.tree.item(selection[0])
        binding_key = item['values'][1]
        object_id = item['values'][3]
        property_path = item['values'][4]

        if messagebox.askyesno(
            "Confirm Remove",
            f"Remove binding '{binding_key}' \u2192 {object_id}.{property_path}?",
        ):
            self.bridge.remove_binding(binding_key, object_id, property_path)
            self._refresh_bindings()

    def _clear_all_bindings(self):
        """Clear all bindings."""
        if messagebox.askyesno("Confirm Clear", "Remove all bindings?"):
            self.bridge.clear_bindings()
            self._refresh_bindings()

    def _toggle_binding_enabled(self, event):
        """Toggle enabled state of double-clicked binding."""
        if self.tree.identify_region(event.x, event.y) != "cell":
            return

        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        binding_key = item['values'][1]
        object_id = item['values'][3]
        property_path = item['values'][4]

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

    def _show_context_menu(self, event):
        """Show context menu on right-click."""
        # Select item under cursor
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)

            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Edit", command=self._edit_selected_binding)
            menu.add_command(label="Remove", command=self._remove_selected_binding)
            menu.add_separator()
            menu.add_command(label="Toggle Enabled", command=lambda: self._toggle_binding_enabled(event))

            menu.post(event.x_root, event.y_root)

    def _schedule_refresh(self):
        """Schedule periodic refresh."""
        try:
            if not self.root.winfo_exists():
                return
        except Exception:
            return
        if self.bridge.is_active():
            self._refresh_bindings()
        self.root.after(1000, self._schedule_refresh)


# ---------------------------------------------------------------------------
# Add / Edit dialogs
# ---------------------------------------------------------------------------

class AddBindingDialog(tk.Toplevel):
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

        self.title("Add Scene Binding")
        self.geometry("540x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        outer = tk.Frame(self, padx=10, pady=8)
        outer.pack(fill=tk.BOTH, expand=True)

        # ── External Source section ───────────────────────────────────────────
        src_lf = tk.LabelFrame(outer, text=" External Source ", padx=8, pady=6)
        src_lf.pack(fill=tk.X, pady=(0, 6))
        src_lf.columnconfigure(1, weight=1)

        tk.Label(src_lf, text="Binding Key:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.key_entry = tk.Entry(src_lf, width=38)
        self.key_entry.grid(row=0, column=1, sticky=tk.EW, pady=4, padx=(4, 0))
        tk.Button(
            src_lf, text="Browse\u2026", command=self._browse_external
        ).grid(row=0, column=2, padx=(6, 0))

        # ── Scene Destination section ─────────────────────────────────────────
        dst_lf = tk.LabelFrame(outer, text=" Scene Destination ", padx=8, pady=6)
        dst_lf.pack(fill=tk.X, pady=(0, 6))
        dst_lf.columnconfigure(1, weight=1)

        tk.Label(dst_lf, text="Object ID:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.object_entry = tk.Entry(dst_lf, width=38)
        self.object_entry.grid(row=0, column=1, sticky=tk.EW, pady=4, padx=(4, 0))
        tk.Button(
            dst_lf, text="Browse\u2026", command=self._browse_scene
        ).grid(row=0, column=2, padx=(6, 0), rowspan=2, sticky=tk.NS)

        tk.Label(dst_lf, text="Property:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.property_entry = tk.Entry(dst_lf, width=38, state="readonly")
        self.property_entry.grid(row=1, column=1, sticky=tk.EW, pady=4, padx=(4, 0))

        # ── Direction row ─────────────────────────────────────────────────────
        dir_frame = tk.Frame(outer)
        dir_frame.pack(fill=tk.X, pady=(0, 4))

        tk.Label(dir_frame, text="Direction:").pack(side=tk.LEFT)
        self.direction_var = tk.StringVar(value="read")
        for label, value in (
            ("External \u2192 Scene", "read"),
            ("Scene \u2192 External", "write"),
            ("Both", "both"),
        ):
            tk.Radiobutton(
                dir_frame, text=label,
                variable=self.direction_var, value=value,
            ).pack(side=tk.LEFT, padx=(8, 0))

        # ── Description row ───────────────────────────────────────────────────
        desc_frame = tk.Frame(outer)
        desc_frame.pack(fill=tk.X, pady=(0, 4))
        desc_frame.columnconfigure(1, weight=1)

        tk.Label(desc_frame, text="Description:").grid(row=0, column=0, sticky=tk.W)
        self.description_entry = tk.Entry(desc_frame)
        self.description_entry.grid(row=0, column=1, sticky=tk.EW, padx=(6, 0))

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_frame = tk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=8)
        tk.Button(btn_frame, text="Add Binding", command=self._add_binding).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    # ------------------------------------------------------------------
    # Browse helpers
    # ------------------------------------------------------------------

    def _browse_external(self) -> None:
        """Open the external-source browser and fill the *Binding Key* entry.

        When the bridge's bound object is a :class:`~pyrox.models.scene.sceneboundlayer.SceneBoundLayer`
        the dialog shows all registered sources (keyboard, plc, …) with their
        introspected properties in a two-pane treeview.  Otherwise falls back to
        the list of keys currently registered in existing bindings.
        """
        bound_obj = self.bridge.get_bound_object()
        if isinstance(bound_obj, SceneBoundLayer):
            dialog = ExternalSourceBrowserDialog(self, bound_obj)
        else:
            existing_keys = sorted({b.binding_key for b in self.bridge.get_bindings()})
            if not existing_keys:
                messagebox.showinfo(
                    "No Keys",
                    "No binding keys available.\n"
                    "Register a SceneBoundLayer as the bound object to "
                    "browse available source properties.",
                )
                return
            dialog = ItemSelectionDialog(self, "Select Binding Key", existing_keys)

        self.wait_window(dialog)

        if hasattr(dialog, 'selected_item'):
            self.key_entry.delete(0, tk.END)
            self.key_entry.insert(0, dialog.selected_item)

    def _browse_scene(self) -> None:
        """Open the scene-object property browser and fill *Object ID* + *Property*.

        Opens :class:`SceneObjectPropertyBrowserDialog` which shows a grouped
        treeview of scene objects (with optional ``physics_body`` children) on the
        left and introspected properties on the right.  Confirming a selection
        fills both the *Object ID* and *Property* fields simultaneously.
        """
        if not self.scene:
            messagebox.showwarning("No Scene", "No scene is loaded.")
            return

        dialog = SceneObjectPropertyBrowserDialog(self, self.scene)
        self.wait_window(dialog)

        if hasattr(dialog, 'selected_object_id'):
            self.object_entry.delete(0, tk.END)
            self.object_entry.insert(0, dialog.selected_object_id)
        if hasattr(dialog, 'selected_property'):
            self.property_entry.config(state="normal")
            self.property_entry.delete(0, tk.END)
            self.property_entry.insert(0, dialog.selected_property)
            self.property_entry.config(state="readonly")

    # ------------------------------------------------------------------
    # Commit
    # ------------------------------------------------------------------

    def _add_binding(self) -> None:
        """Validate entries and call :py:meth:`~pyrox.interfaces.scene.ISceneBridge.add_binding`."""
        binding_key = self.key_entry.get().strip()
        object_id = self.object_entry.get().strip()
        property_path = self.property_entry.get().strip()

        if not binding_key or not object_id or not property_path:
            messagebox.showerror("Missing Fields", "Please fill in all required fields.")
            return

        direction = BindingDirection(self.direction_var.get())
        description = self.description_entry.get().strip()

        try:
            self.bridge.add_binding(
                binding_key=binding_key,
                object_id=object_id,
                property_path=property_path,
                direction=direction,
                description=description,
            )
            messagebox.showinfo("Success", "Binding added successfully.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add binding: {e}")


class EditBindingDialog(tk.Toplevel):
    """Dialog for editing an existing binding."""

    def __init__(self, parent, bridge: ISceneBridge, binding: ISceneBinding):
        super().__init__(parent)
        self.bridge = bridge
        self.binding = binding

        self.title("Edit Binding")
        self.geometry("400x280")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        form_frame = tk.Frame(self, padx=10, pady=10)
        form_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(form_frame, text=f"Key:      {binding.binding_key}").pack(anchor=tk.W, pady=4)
        tk.Label(form_frame, text=f"Object:   {binding.object_id}").pack(anchor=tk.W, pady=4)
        tk.Label(form_frame, text=f"Property: {binding.property_path}").pack(anchor=tk.W, pady=4)

        tk.Label(form_frame, text="Description:").pack(anchor=tk.W, pady=(10, 0))
        self.description_entry = tk.Entry(form_frame, width=50)
        self.description_entry.insert(0, binding.description)
        self.description_entry.pack(fill=tk.X, pady=5)

        self.enabled_var = tk.BooleanVar(value=binding.enabled)
        tk.Checkbutton(form_frame, text="Enabled", variable=self.enabled_var).pack(anchor=tk.W, pady=5)

        button_frame = tk.Frame(self)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        tk.Button(button_frame, text="Save", command=self._save).pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def _save(self):
        """Persist edits to the binding."""
        self.binding.description = self.description_entry.get()
        self.binding.enabled = self.enabled_var.get()
        messagebox.showinfo("Success", "Binding updated")
        self.destroy()


# ---------------------------------------------------------------------------
# External source browser (SceneBoundLayer → source → property)
# ---------------------------------------------------------------------------

class ExternalSourceBrowserDialog(tk.Toplevel):
    """Two-pane browser for selecting a binding key from a
    :class:`~pyrox.models.scene.sceneboundlayer.SceneBoundLayer`.

    * **Left pane** \u2014 listbox of registered source names (e.g. ``"plc"``,
      ``"keyboard"``, ``"sim"``).  Selecting a source populates the right
      pane with that source\'s inspectable public properties.
    * **Right pane** \u2014 treeview showing ``Property`` name and ``Type``
      columns, introspected from the actual source object so the user can
      see at a glance what kind of value each property holds.

    Closing via *Select* stores the composed ``"source.property"`` string in
    ``self.selected_item``.
    """

    def __init__(self, parent, layer: SceneBoundLayer) -> None:
        super().__init__(parent)
        self.layer = layer
        self.title("Browse External Sources")
        self.geometry("580x380")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        tk.Label(
            self,
            text="Select a source (left), then a property (right), then click Select.",
            anchor=tk.W, padx=8, pady=4,
        ).pack(fill=tk.X)

        panes = tk.Frame(self)
        panes.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Left \u2014 source listbox
        left = tk.LabelFrame(panes, text="Sources")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 4))

        left_scroll = ttk.Scrollbar(left)
        left_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._source_lb = tk.Listbox(
            left, yscrollcommand=left_scroll.set, exportselection=False, width=20,
        )
        self._source_lb.pack(fill=tk.BOTH, expand=True)
        left_scroll.config(command=self._source_lb.yview)

        for name in layer.list_sources():
            self._source_lb.insert(tk.END, name)

        self._source_lb.bind('<<ListboxSelect>>', self._on_source_selected)

        # Right \u2014 property treeview
        right = tk.LabelFrame(panes, text="Properties")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))

        right_scroll = ttk.Scrollbar(right)
        right_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._prop_tree = ttk.Treeview(
            right,
            columns=('type',),
            show='tree headings',
            selectmode='browse',
            yscrollcommand=right_scroll.set,
        )
        self._prop_tree.heading('#0', text='Property')
        self._prop_tree.heading('type', text='Type')
        self._prop_tree.column('#0', stretch=True)
        self._prop_tree.column('type', width=80, stretch=False)
        self._prop_tree.pack(fill=tk.BOTH, expand=True)
        right_scroll.config(command=self._prop_tree.yview)

        self._prop_tree.bind('<<TreeviewSelect>>', self._on_prop_selected)
        self._prop_tree.bind('<Double-Button-1>', lambda _e: self._select())

        # Preview
        self._preview_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self._preview_var, anchor=tk.W,
                 padx=8, fg='#444').pack(fill=tk.X)

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=6)
        tk.Button(btn_frame, text="Select", command=self._select).pack(side=tk.RIGHT, padx=4)
        tk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

        # Pre-select first source so the right pane is immediately populated
        if layer.list_sources():
            self._source_lb.selection_set(0)
            self._on_source_selected(None)

    def _on_source_selected(self, _event: Any) -> None:
        """Populate the property pane for the currently selected source."""
        sel = self._source_lb.curselection()
        if not sel:
            return
        source_name = self._source_lb.get(sel[0])
        source_obj = self.layer.get_source(source_name)

        self._prop_tree.delete(*self._prop_tree.get_children())
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
            self._prop_tree.insert('', tk.END, text=prop, values=(type_name,))

        self._preview_var.set(
            f"source: {source_name}  \u2014  select a property"
            if props else f"source: {source_name}  \u2014  (no public properties)"
        )

    def _on_prop_selected(self, _event: Any) -> None:
        """Update the preview label."""
        src_sel = self._source_lb.curselection()
        prop_sel = self._prop_tree.selection()
        if src_sel and prop_sel:
            src = self._source_lb.get(src_sel[0])
            prop = self._prop_tree.item(prop_sel[0], 'text')
            self._preview_var.set(f"key: {src}.{prop}")

    def _select(self) -> None:
        """Compose and store the selected binding key, then close."""
        src_sel = self._source_lb.curselection()
        prop_sel = self._prop_tree.selection()
        if not src_sel:
            messagebox.showwarning("No Source", "Please select a source first", parent=self)
            return
        if not prop_sel:
            messagebox.showwarning("No Property", "Please select a property first", parent=self)
            return
        src = self._source_lb.get(src_sel[0])
        prop = self._prop_tree.item(prop_sel[0], 'text')
        self.selected_item = f"{src}.{prop}"
        self.destroy()


# ---------------------------------------------------------------------------
# Scene object + property browser
# ---------------------------------------------------------------------------

class SceneObjectPropertyBrowserDialog(tk.Toplevel):
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
        self.title("Browse Scene Destination")
        self.geometry("660x440")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        tk.Label(
            self,
            text="Select an object or its \u2699 Physics Body (left), then a property (right), then click Select.",
            anchor=tk.W, padx=8, pady=4,
        ).pack(fill=tk.X)

        # -- Search bar --------------------------------------------------------
        search_frame = tk.Frame(self)
        search_frame.pack(fill=tk.X, padx=8, pady=(0, 4))
        tk.Label(search_frame, text="\U0001f50d").pack(side=tk.LEFT)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._populate_objects())
        tk.Entry(search_frame, textvariable=self._search_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=4
        )

        # -- Two panes ---------------------------------------------------------
        panes = tk.Frame(self)
        panes.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Left — scene object treeview (with optional physics body children)
        left = tk.LabelFrame(panes, text="Scene Objects")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))

        left_scroll = ttk.Scrollbar(left)
        left_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._obj_tree = ttk.Treeview(
            left,
            columns=('id', 'node_type'),
            show='tree',
            selectmode='browse',
            yscrollcommand=left_scroll.set,
        )
        self._obj_tree.column('#0', stretch=True)
        self._obj_tree.column('id', width=0, stretch=False)
        self._obj_tree.column('node_type', width=0, stretch=False)
        self._obj_tree.tag_configure(self._TAG_GROUP, font=('', 9, 'bold'))
        self._obj_tree.tag_configure(self._TAG_OBJECT, font=('', 9))
        self._obj_tree.tag_configure(
            self._TAG_PHYSICS, font=('', 9, 'italic'), foreground='#445566'
        )
        self._obj_tree.pack(fill=tk.BOTH, expand=True)
        left_scroll.config(command=self._obj_tree.yview)
        self._obj_tree.bind('<<TreeviewSelect>>', self._on_node_selected)

        # Right — property treeview
        right = tk.LabelFrame(panes, text="Properties")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))

        right_scroll = ttk.Scrollbar(right)
        right_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._prop_tree = ttk.Treeview(
            right,
            columns=('type',),
            show='tree headings',
            selectmode='browse',
            yscrollcommand=right_scroll.set,
        )
        self._prop_tree.heading('#0', text='Property')
        self._prop_tree.heading('type', text='Type')
        self._prop_tree.column('#0', stretch=True)
        self._prop_tree.column('type', width=80, stretch=False)
        self._prop_tree.pack(fill=tk.BOTH, expand=True)
        right_scroll.config(command=self._prop_tree.yview)
        self._prop_tree.bind('<<TreeviewSelect>>', self._on_prop_selected)
        self._prop_tree.bind('<Double-Button-1>', lambda _e: self._select())

        # Preview
        self._preview_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self._preview_var, anchor=tk.W,
                 padx=8, fg='#444').pack(fill=tk.X)

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=6)
        tk.Button(btn_frame, text="Select", command=self._select).pack(side=tk.RIGHT, padx=4)
        tk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

        # iid → (object_id: str, target_obj: Any, is_physics_body: bool)
        self._node_map: dict[str, tuple[str, Any, bool]] = {}

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
        self._obj_tree.delete(*self._obj_tree.get_children())
        self._prop_tree.delete(*self._prop_tree.get_children())
        self._node_map.clear()
        self._preview_var.set("")

        objects = self._get_objects()
        if not objects:
            return

        filter_text = self._search_var.get().lower().strip()

        groups: dict[str, list] = {}
        for obj in objects:
            obj_type = (
                getattr(obj, 'scene_object_type', None)
                or getattr(obj, '_scene_object_type', None)
                or 'Unknown'
            )
            groups.setdefault(obj_type, []).append(obj)

        for group_name, members in sorted(groups.items()):
            matching = [
                obj for obj in members
                if not filter_text or filter_text in self._label(obj).lower()
            ]
            if not matching:
                continue

            group_node = self._obj_tree.insert(
                '', tk.END,
                text=f"{group_name}  ({len(matching)})",
                values=('', self._TAG_GROUP),
                open=True,
                tags=(self._TAG_GROUP,),
            )

            for obj in sorted(matching, key=lambda o: self._label(o).lower()):
                obj_id = getattr(obj, 'get_id', lambda: getattr(obj, 'id', str(obj)))()
                obj_iid = self._obj_tree.insert(
                    group_node, tk.END,
                    text=self._label(obj),
                    values=(obj_id, self._TAG_OBJECT),
                    open=False,
                    tags=(self._TAG_OBJECT,),
                )
                self._node_map[obj_iid] = (obj_id, obj, False)

                # Expose physics body as a selectable child node
                physics_body = getattr(obj, 'physics_body', None)
                if physics_body is not None:
                    pb_iid = self._obj_tree.insert(
                        obj_iid, tk.END,
                        text="\u2699 Physics Body",
                        values=(obj_id, self._TAG_PHYSICS),
                        tags=(self._TAG_PHYSICS,),
                    )
                    self._node_map[pb_iid] = (obj_id, physics_body, True)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_node_selected(self, _event: Any) -> None:
        """Populate the property pane for the selected object or physics body."""
        selected = self._obj_tree.selection()
        if not selected:
            return
        iid = selected[0]
        if iid not in self._node_map:
            return  # group header

        obj_id, target_obj, is_physics = self._node_map[iid]

        self._prop_tree.delete(*self._prop_tree.get_children())
        props = SceneBoundLayer._inspect_properties(target_obj)
        for prop in props:
            try:
                val = getattr(target_obj, prop)
                type_name = type(val).__name__
            except Exception:
                type_name = '?'
            self._prop_tree.insert('', tk.END, text=prop, values=(type_name,))

        target_label = "physics_body" if is_physics else "object"
        self._preview_var.set(
            f"object: {obj_id}  \u2014  target: {target_label}  \u2014  select a property"
            if props
            else f"object: {obj_id}  \u2014  target: {target_label}  \u2014  (no public properties)"
        )

    def _on_prop_selected(self, _event: Any) -> None:
        """Update the preview label."""
        obj_sel = self._obj_tree.selection()
        prop_sel = self._prop_tree.selection()
        if obj_sel and prop_sel and obj_sel[0] in self._node_map:
            obj_id, _, is_physics = self._node_map[obj_sel[0]]
            prop = self._prop_tree.item(prop_sel[0], 'text')
            full_prop = f"physics_body.{prop}" if is_physics else prop
            self._preview_var.set(f"object: {obj_id}  \u2014  property: {full_prop}")

    def _select(self) -> None:
        """Validate selection, compose results, and close."""
        obj_sel = self._obj_tree.selection()
        if not obj_sel or obj_sel[0] not in self._node_map:
            messagebox.showwarning(
                "No Object",
                "Please select an object or its Physics Body node first.",
                parent=self,
            )
            return
        prop_sel = self._prop_tree.selection()
        if not prop_sel:
            messagebox.showwarning("No Property", "Please select a property first", parent=self)
            return

        obj_id, _, is_physics = self._node_map[obj_sel[0]]
        prop = self._prop_tree.item(prop_sel[0], 'text')
        self.selected_object_id: str = obj_id
        self.selected_property: str = f"physics_body.{prop}" if is_physics else prop
        self.destroy()


class ItemSelectionDialog(tk.Toplevel):
    """Generic single-item selection dialog backed by a listbox."""

    def __init__(self, parent, title: str, items: list[str]):
        super().__init__(parent)
        self.title(title)
        self.geometry("420x300")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        frame = tk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        for item in items:
            self.listbox.insert(tk.END, item)

        button_frame = tk.Frame(self)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        tk.Button(button_frame, text="Select", command=self._select).pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

        self.listbox.bind('<Double-Button-1>', lambda _e: self._select())

    def _select(self):
        """Confirm selection and close."""
        selection = self.listbox.curselection()
        if selection:
            self.selected_item = self.listbox.get(selection[0])
            self.destroy()


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def create_demo_window() -> tk.Tk:
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
        tk.Tk: The configured root window (caller must call ``mainloop()``).
    """
    from types import SimpleNamespace

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
    # Mock physics body  (inspectable properties shown as children in the
    # left treeview of SceneObjectPropertyBrowserDialog)
    # ------------------------------------------------------------------

    class _MockPhysicsBody:
        def __init__(self) -> None:
            self.mass_kg: float = 10.0
            self.velocity_x: float = 0.0
            self.velocity_y: float = 0.0
            self.is_static: bool = False
            self.collisions_enabled: bool = True

    # ------------------------------------------------------------------
    # Typed mock scene objects — each carries scene_object_type,
    # physics_body (or None), and bindable public properties.
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
            self.physics_body = None  # sensors have no physics body in this demo

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
    # Mock bridge — returns a real SceneBoundLayer so ExternalSourceBrowserDialog
    # can display the two-pane source/property treeview.
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

    root = tk.Tk()
    root.title("SceneBridgeDialog — Demo")
    root.geometry("980x460")

    dialog = SceneBridgeDialog(
        parent=root,
        bridge=_mock_bridge,   # type: ignore[arg-type]
        scene=_mock_scene,     # type: ignore[arg-type]
    )
    dialog.root.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    return root


if __name__ == "__main__":
    demo_window = create_demo_window()
    demo_window.mainloop()

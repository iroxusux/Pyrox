"""GUI for Scene Bridge Management.

Provides a user interface for creating and managing bindings between
a source object and scene object properties.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from pyrox.interfaces import BindingDirection, IScene, ISceneBinding
from pyrox.models.gui.tk.frame import TkinterTaskFrame
from pyrox.models.scene.scenebridge import SceneBridge
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
        bridge: SceneBridge,
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
        active_status = "ACTIVE" if self.bridge._active else "STOPPED"

        self.status_var.set(
            f"{active_status} | {enabled_count}/{len(bindings)} bindings enabled"
        )

        if self.bridge._active:
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
        if self.bridge._active:
            self._refresh_bindings()
        self.root.after(1000, self._schedule_refresh)


# ---------------------------------------------------------------------------
# Add / Edit dialogs
# ---------------------------------------------------------------------------

class AddBindingDialog(tk.Toplevel):
    """Dialog for adding a new scene bridge binding."""

    def __init__(self, parent, bridge: SceneBridge, scene: Optional[IScene]):
        super().__init__(parent)
        self.bridge = bridge
        self.scene = scene

        self.title("Add Scene Binding")
        self.geometry("500x360")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        form_frame = tk.Frame(self, padx=10, pady=10)
        form_frame.pack(fill=tk.BOTH, expand=True)

        row = 0

        # Binding Key
        tk.Label(form_frame, text="Binding Key:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.key_entry = tk.Entry(form_frame, width=40)
        self.key_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        tk.Button(
            form_frame, text="Browse...", command=self._browse_keys
        ).grid(row=row, column=2, padx=5)
        row += 1

        # Scene Object
        tk.Label(form_frame, text="Scene Object ID:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.object_entry = tk.Entry(form_frame, width=40)
        self.object_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        tk.Button(
            form_frame, text="Browse...", command=self._browse_objects
        ).grid(row=row, column=2, padx=5)
        row += 1

        # Property Path
        tk.Label(form_frame, text="Property Path:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.property_entry = tk.Entry(form_frame, width=40)
        self.property_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        tk.Label(form_frame, text="e.g., speed, position.x").grid(row=row, column=2, padx=5)
        row += 1

        # Direction
        tk.Label(form_frame, text="Direction:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.direction_var = tk.StringVar(value="read")
        direction_frame = tk.Frame(form_frame)
        direction_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        tk.Radiobutton(
            direction_frame, text="Source \u2192 Scene",
            variable=self.direction_var, value="read",
        ).pack(side=tk.LEFT)
        tk.Radiobutton(
            direction_frame, text="Scene \u2192 Source",
            variable=self.direction_var, value="write",
        ).pack(side=tk.LEFT)
        tk.Radiobutton(
            direction_frame, text="Both",
            variable=self.direction_var, value="both",
        ).pack(side=tk.LEFT)
        row += 1

        # Description
        tk.Label(form_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.description_entry = tk.Entry(form_frame, width=40)
        self.description_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1

        form_frame.columnconfigure(1, weight=1)

        button_frame = tk.Frame(self)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        tk.Button(button_frame, text="Add Binding", command=self._add_binding).pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def _browse_keys(self):
        """Browse binding keys already registered in the bridge."""
        existing_keys = sorted({b.binding_key for b in self.bridge.get_bindings()})
        if not existing_keys:
            messagebox.showinfo("No Keys", "No binding keys registered yet")
            return

        dialog = ItemSelectionDialog(self, "Select Binding Key", existing_keys)
        self.wait_window(dialog)

        if hasattr(dialog, 'selected_item'):
            self.key_entry.delete(0, tk.END)
            self.key_entry.insert(0, dialog.selected_item)

    def _browse_objects(self):
        """Browse scene objects."""
        if not self.scene:
            messagebox.showwarning("No Scene", "No scene is loaded")
            return

        objects = self.scene.get_scene_objects()
        if not objects:
            messagebox.showinfo("No Objects", "Scene has no objects")
            return

        ids = [
            getattr(obj, 'get_id')() if hasattr(obj, 'get_id') else str(obj)
            for obj in objects
        ]
        dialog = ItemSelectionDialog(self, "Select Scene Object", ids)
        self.wait_window(dialog)

        if hasattr(dialog, 'selected_item'):
            self.object_entry.delete(0, tk.END)
            self.object_entry.insert(0, dialog.selected_item)

    def _add_binding(self):
        """Validate and add the binding."""
        binding_key = self.key_entry.get().strip()
        object_id = self.object_entry.get().strip()
        property_path = self.property_entry.get().strip()

        if not binding_key or not object_id or not property_path:
            messagebox.showerror("Missing Fields", "Please fill in all required fields")
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
            messagebox.showinfo("Success", "Binding added successfully")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add binding: {e}")


class EditBindingDialog(tk.Toplevel):
    """Dialog for editing an existing binding."""

    def __init__(self, parent, bridge: SceneBridge, binding: ISceneBinding):
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
# Generic selection helper
# ---------------------------------------------------------------------------

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

""" preferences task
    """
from __future__ import annotations
from pyrox.models import Application, ApplicationTask
from pyrox.services.logging import log
from pyrox.services.env import EnvManager
from pyrox.services.plc import start_logix_5k

import tkinter as tk
from tkinter import colorchooser, messagebox, ttk
import copy
from pyrox.models.gui.ladder import THEME


class AppearanceEditor:
    """Editor for application appearance themes using THEME dictionary.
    """

    def __init__(self, parent_app: Application):
        self.parent_app = parent_app
        self.dialog = None
        self.theme_vars = {}
        self.original_theme = {}
        self.preview_labels = {}

        # Load saved theme from runtime_info or use defaults
        self._load_theme_from_runtime()

    def _load_theme_from_runtime(self):
        """Load theme values from application runtime_info."""
        saved_theme: dict = EnvManager.get('UI_LADDER_THEME', {}, dict)

        # Merge saved values with default THEME
        self.current_theme = copy.deepcopy(THEME)
        self.current_theme.update(saved_theme)

        # Store original values for cancel functionality
        self.original_theme = copy.deepcopy(self.current_theme)

    def _save_theme_to_runtime(self):
        """Save current theme values to application runtime_info."""
        EnvManager.set('UI_LADDER_THEME', str(self.current_theme))

    def _create_color_row(self, parent, key: str, label_text: str, row: int):
        """Create a row with label, color preview, and change button."""
        # Label
        tk.Label(parent, text=label_text, width=20, anchor='w').grid(
            row=row, column=0, padx=5, pady=2, sticky='w'
        )

        # Color preview
        color_frame = tk.Frame(parent, width=60, height=25, relief='solid', bd=1)
        color_frame.grid(row=row, column=1, padx=5, pady=2)
        color_frame.grid_propagate(False)  # Maintain fixed size

        # Store reference for updating
        self.preview_labels[key] = color_frame

        # Update color
        self._update_color_preview(key)

        # Change button
        tk.Button(
            parent,
            text="Change",
            command=lambda k=key: self._change_color(k),
            width=8
        ).grid(row=row, column=2, padx=5, pady=2)

        # Reset button
        tk.Button(
            parent,
            text="Reset",
            command=lambda k=key: self._reset_color(k),
            width=8
        ).grid(row=row, column=3, padx=5, pady=2)

    def _create_font_row(self, parent, key: str, label_text: str, row: int):
        """Create a row for font selection."""
        # Label
        tk.Label(parent, text=label_text, width=20, anchor='w').grid(
            row=row, column=0, padx=5, pady=2, sticky='w'
        )

        # Font display
        font_var = tk.StringVar(value=self.current_theme[key])
        self.theme_vars[key] = font_var

        font_entry = tk.Entry(parent, textvariable=font_var, width=15, state='readonly')
        font_entry.grid(row=row, column=1, padx=5, pady=2)

        # Change button (placeholder - could implement font chooser)
        tk.Button(
            parent,
            text="Change",
            command=lambda: self._change_font(key),
            width=8
        ).grid(row=row, column=2, padx=5, pady=2)

        # Reset button
        tk.Button(
            parent,
            text="Reset",
            command=lambda k=key: self._reset_font(k),
            width=8
        ).grid(row=row, column=3, padx=5, pady=2)

    def _create_number_row(self, parent, key: str, label_text: str, row: int, min_val=1, max_val=10):
        """Create a row for numeric values."""
        # Label
        tk.Label(parent, text=label_text, width=20, anchor='w').grid(
            row=row, column=0, padx=5, pady=2, sticky='w'
        )

        # Spinbox for numeric input
        spinbox_var = tk.IntVar(value=self.current_theme[key])
        self.theme_vars[key] = spinbox_var

        spinbox = tk.Spinbox(
            parent,
            from_=min_val,
            to=max_val,
            textvariable=spinbox_var,
            width=10,
            command=lambda k=key: self._update_numeric_value(k)
        )
        spinbox.grid(row=row, column=1, padx=5, pady=2)

        # Bind to update on manual entry
        spinbox_var.trace('w', lambda *args, k=key: self._update_numeric_value(k))

        # Reset button
        tk.Button(
            parent,
            text="Reset",
            command=lambda k=key: self._reset_numeric(k),
            width=8
        ).grid(row=row, column=3, padx=5, pady=2)

    def _update_color_preview(self, key: str):
        """Update the color preview for a specific key."""
        if key in self.preview_labels:
            color = self.current_theme[key]
            self.preview_labels[key].configure(bg=color)

    def _change_color(self, key: str):
        """Open color chooser and update theme."""
        current_color = self.current_theme[key]
        new_color = colorchooser.askcolor(
            initialcolor=current_color,
            title=f"Choose color for {key}"
        )[1]  # Get hex value

        if new_color:
            self.current_theme[key] = new_color
            self._update_color_preview(key)
            self._update_preview()

    def _reset_color(self, key: str):
        """Reset color to default THEME value."""
        if key in THEME:
            self.current_theme[key] = THEME[key]
            self._update_color_preview(key)
            self._update_preview()

    def _change_font(self, key: str):
        """Change font (simplified - could be expanded with font chooser)."""
        fonts = ["Consolas", "Arial", "Courier New", "Times New Roman", "Helvetica", "Monaco"]

        # Create simple selection dialog
        font_dialog = tk.Toplevel(self.dialog)
        font_dialog.title("Select Font")
        font_dialog.geometry("300x200")
        font_dialog.transient(self.dialog)
        font_dialog.grab_set()

        tk.Label(font_dialog, text="Select Font:", font=('Arial', 10, 'bold')).pack(pady=10)

        font_var = tk.StringVar(value=self.current_theme[key])

        for font in fonts:
            tk.Radiobutton(
                font_dialog,
                text=font,
                variable=font_var,
                value=font,
                font=(font, 10)
            ).pack(anchor='w', padx=20)

        button_frame = tk.Frame(font_dialog)
        button_frame.pack(pady=20)

        def apply_font():
            self.current_theme[key] = font_var.get()
            self.theme_vars[key].set(font_var.get())
            self._update_preview()
            font_dialog.destroy()

        tk.Button(button_frame, text="Apply", command=apply_font).pack(side='left', padx=5)
        tk.Button(button_frame, text="Cancel", command=font_dialog.destroy).pack(side='left', padx=5)

    def _reset_font(self, key: str):
        """Reset font to default THEME value."""
        if key in THEME:
            self.current_theme[key] = THEME[key]
            if key in self.theme_vars:
                self.theme_vars[key].set(THEME[key])
            self._update_preview()

    def _update_numeric_value(self, key: str):
        """Update numeric value in theme."""
        if key in self.theme_vars:
            self.current_theme[key] = self.theme_vars[key].get()
            self._update_preview()

    def _reset_numeric(self, key: str):
        """Reset numeric value to default THEME value."""
        if key in THEME and key in self.theme_vars:
            self.current_theme[key] = THEME[key]
            self.theme_vars[key].set(THEME[key])
            self._update_preview()

    def _update_preview(self):
        """Update the preview area with current theme."""
        if hasattr(self, 'preview_frame'):
            # Update preview labels and elements
            for widget in self.preview_frame.winfo_children():
                widget.destroy()

            self._create_preview_content()

    def _create_preview_content(self):
        """Create preview content showing current theme."""
        # Background
        self.preview_frame.configure(bg=self.current_theme['background'])

        # Sample ladder elements
        tk.Label(
            self.preview_frame,
            text="Sample Ladder Elements",
            font=(self.current_theme['font'], 12, 'bold'),
            fg=self.current_theme['foreground'],
            bg=self.current_theme['background']
        ).pack(pady=5)

        # Contact preview
        contact_frame = tk.Frame(self.preview_frame, bg=self.current_theme['background'])
        contact_frame.pack(pady=5)

        tk.Label(
            contact_frame,
            text="Contact:",
            font=(self.current_theme['font'], 10),
            fg=self.current_theme['foreground'],
            bg=self.current_theme['background']
        ).pack(side='left')

        contact_canvas = tk.Canvas(
            contact_frame,
            width=50,
            height=30,
            bg=self.current_theme['background'],
            highlightthickness=0
        )
        contact_canvas.pack(side='left', padx=10)

        # Draw mini contact
        contact_canvas.create_rectangle(
            10, 10, 40, 20,
            outline=self.current_theme['ladder_rung_color'],
            fill=self.current_theme['background'],
            width=self.current_theme['ladder_line_width']
        )

        # Comment preview
        comment_frame = tk.Frame(
            self.preview_frame,
            bg=self.current_theme['comment_background'],
            relief='solid',
            bd=1
        )
        comment_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(
            comment_frame,
            text="This is a sample comment",
            font=(self.current_theme['font'], 9),
            fg=self.current_theme['comment_foreground'],
            bg=self.current_theme['comment_background']
        ).pack(pady=2)

        # Highlight example
        highlight_frame = tk.Frame(
            self.preview_frame,
            bg=self.current_theme['highlight_background'],
            relief='solid',
            bd=2
        )
        highlight_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(
            highlight_frame,
            text="Highlighted Element",
            font=(self.current_theme['font'], 9),
            fg=self.current_theme['highlight_color'],
            bg=self.current_theme['highlight_background']
        ).pack(pady=2)

    def _apply_theme(self):
        """Apply the current theme settings."""
        # Save to runtime_info
        self._save_theme_to_runtime()

        # Update the global THEME dictionary
        THEME.update(self.current_theme)

        # Show confirmation
        messagebox.showinfo("Theme Applied", "Theme settings have been applied and saved.")

        # Close dialog
        if self.dialog:
            self.dialog.destroy()

    def _cancel_changes(self):
        """Cancel changes and restore original theme."""
        # Restore original theme
        self.current_theme = copy.deepcopy(self.original_theme)

        # Update THEME dictionary back to original
        THEME.update(self.original_theme)

        # Close dialog
        if self.dialog:
            self.dialog.destroy()

    def _reset_all_to_defaults(self):
        """Reset all theme values to defaults."""
        if messagebox.askyesno("Reset All", "Reset all appearance settings to defaults?"):
            # Reset to original THEME defaults
            default_theme = {
                "font": "Consolas",
                "instruction_alias": "#EF1010",
                "background": "#333333",
                "comment_background": "#444444",
                "comment_foreground": "#09C83F",
                "foreground": "#f00bd5",
                "highlight_color": "#4A90E2",
                "highlight_background": "#344FE9",
                "button_color": "#4A90E2",
                "button_hover_color": "#357ABD",
                "button_text_color": "#ffffff",
                "ladder_rung_color": "#EF1010",
                "ladder_line_width": 2,
                "tooltip_background": "#e6f3ff",
                "tooltip_label_background": "#e6f3ff",
                "tooltip_label_foreground": "#0066cc",
            }

            self.current_theme = copy.deepcopy(default_theme)

            # Update all UI elements
            for key in self.current_theme:
                if key in self.preview_labels:
                    self._update_color_preview(key)
                if key in self.theme_vars:
                    if isinstance(self.theme_vars[key], tk.StringVar):
                        self.theme_vars[key].set(self.current_theme[key])
                    elif isinstance(self.theme_vars[key], tk.IntVar):
                        self.theme_vars[key].set(self.current_theme[key])

            self._update_preview()

    def show(self):
        """Show the appearance editor dialog."""
        self.dialog = tk.Toplevel(self.parent_app.tk_app)
        self.dialog.title("Appearance Editor")
        self.dialog.geometry("800x600")
        self.dialog.transient(self.parent_app.tk_app)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # Create main paned window
        main_paned = ttk.PanedWindow(self.dialog, orient='horizontal')
        main_paned.pack(fill='both', expand=True, padx=5, pady=5)

        # Left panel - Settings
        settings_frame = ttk.Frame(main_paned)
        main_paned.add(settings_frame, weight=1)

        # Right panel - Preview
        preview_label_frame = ttk.LabelFrame(main_paned, text="Preview")
        main_paned.add(preview_label_frame, weight=1)

        self.preview_frame = tk.Frame(preview_label_frame)
        self.preview_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Create settings notebook
        settings_notebook = ttk.Notebook(settings_frame)
        settings_notebook.pack(fill='both', expand=True)

        # Colors tab
        colors_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(colors_frame, text="Colors")

        # Create scrollable frame for colors
        colors_canvas = tk.Canvas(colors_frame)
        colors_scrollbar = ttk.Scrollbar(colors_frame, orient="vertical", command=colors_canvas.yview)
        colors_content = ttk.Frame(colors_canvas)

        colors_content.bind(
            "<Configure>",
            lambda e: colors_canvas.configure(scrollregion=colors_canvas.bbox("all"))
        )

        colors_canvas.create_window((0, 0), window=colors_content, anchor="nw")
        colors_canvas.configure(yscrollcommand=colors_scrollbar.set)

        colors_canvas.pack(side="left", fill="both", expand=True)
        colors_scrollbar.pack(side="right", fill="y")

        # Add color settings
        color_settings = [
            ("instruction_alias", "Instruction Alias"),
            ("background", "Background"),
            ("comment_background", "Comment Background"),
            ("comment_foreground", "Comment Foreground"),
            ("foreground", "Foreground"),
            ("highlight_color", "Highlight Color"),
            ("highlight_background", "Highlight Background"),
            ("button_color", "Button Color"),
            ("button_hover_color", "Button Hover Color"),
            ("button_text_color", "Button Text Color"),
            ("ladder_rung_color", "Ladder Rung Color"),
            ("tooltip_background", "Tooltip Background"),
            ("tooltip_label_background", "Tooltip Label Background"),
            ("tooltip_label_foreground", "Tooltip Label Foreground"),
        ]

        for i, (key, label) in enumerate(color_settings):
            self._create_color_row(colors_content, key, label, i)

        # Fonts tab
        fonts_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(fonts_frame, text="Fonts")

        self._create_font_row(fonts_frame, "font", "Default Font", 0)

        # Numbers tab
        numbers_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(numbers_frame, text="Sizing")

        self._create_number_row(numbers_frame, "ladder_line_width", "Ladder Line Width", 0, 1, 5)

        # Button frame
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=5, pady=5)

        # Left side buttons
        tk.Button(
            button_frame,
            text="Reset All",
            command=self._reset_all_to_defaults,
            bg='orange',
            fg='white'
        ).pack(side='left', padx=5)

        # Right side buttons
        tk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel_changes,
            bg='lightcoral',
            width=10
        ).pack(side='right', padx=5)

        tk.Button(
            button_frame,
            text="Apply",
            command=self._apply_theme,
            bg='lightgreen',
            width=10
        ).pack(side='right', padx=5)

        # Create initial preview
        self._create_preview_content()

        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._cancel_changes)


class LaunchToStudioTask(ApplicationTask):
    """Launch to Studio 5000 Task
    This task launches the Studio 5000 application with the current controller file.
    """

    def launch_studio(self):
        if not self.application.controller:
            log(self).error('No controller loaded, cannot launch Studio 5000.')
            return

        self.application.save_controller()
        if not self.application.controller.file_location:
            log(self).error('Controller file location is not set.')
            return

        start_logix_5k(self.application.controller.file_location)

    def inject(self) -> None:
        if not self.application.menu:
            return

        self.application.menu.edit.add_command(label='Launch to Studio 5000', command=self.launch_studio)


class AppearanceTask(ApplicationTask):
    """Appearance editor task for customizing the application theme."""

    def show_appearance_editor(self):
        """Show the appearance editor dialog."""
        editor = AppearanceEditor(self.application)
        editor.show()

    def inject(self) -> None:
        if not self.application.menu:
            return

        self.application.menu.edit.add_command(
            label='Appearance...',
            command=self.show_appearance_editor
        )


class PreferencesTask(ApplicationTask):
    """built-in preferences task.
    """

    def preferences(self):
        pass  # Placeholder for future preferences dialog

    def inject(self) -> None:
        if not self.application.menu:
            return

        self.application.menu.edit.add_separator()
        self.application.menu.edit.add_command(label='Preferences', command=self.preferences)

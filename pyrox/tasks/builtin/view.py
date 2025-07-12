""" view tasks
    """
from __future__ import annotations

from tkinter import BooleanVar, Menu
from tkinter import ttk
from ttkthemes import ThemedTk
from pyrox.models import ApplicationTask


class ViewTask(ApplicationTask):

    def __init__(self,
                 *args,
                 **kwargs):
        super().__init__(*args,
                         **kwargs)

    def _open_dir(self, dir_location: str):
        """Open a directory in the file explorer."""

        if not dir_location:
            self.logger.warning('No directory selected...')
            return

        self.logger.info('Opening directory -> %s', dir_location)
        try:
            import os
            os.startfile(dir_location)
        except Exception as e:
            self.logger.error(f'Failed to open directory: {e}')

    def inject_theme_menu(self) -> None:
        """Inject a dropdown menu listing all available ttkthemes themes, with checkboxes for selection."""
        if not self.application.menu:
            self.logger.error('Application menu not found, cannot inject theme menu.')
            return

        # Get all ttkthemes themes
        root = self.application.tk_app
        if hasattr(root, 'get_themes'):
            themes = root.get_themes()
        else:
            # fallback: use ThemedTk to get themes
            themes = ThemedTk().get_themes()
        current_theme = root.get_theme() if hasattr(root, 'get_theme') else root.tk.call("ttk::style", "theme", "use")

        theme_menu = Menu(self.application.menu.view, name='theme_menu', tearoff=0)
        self.application.menu.view.add_cascade(menu=theme_menu, label='Themes')

        self._theme_var = {}
        for theme in sorted(themes):
            var = BooleanVar(value=(theme == current_theme))
            self._theme_var[theme] = var

            def set_theme(t=theme):
                if hasattr(root, 'set_theme'):
                    root.set_theme(t)
                else:
                    ttk.Style(root).theme_use(t)
                self.application.runtime_info.set('theme', t)
                self.logger.info(f'Set theme to {t}')
                for th, v in self._theme_var.items():
                    v.set(th == t)

            theme_menu.add_checkbutton(label=theme, variable=var, command=set_theme)

    def inject(self) -> None:
        self.inject_theme_menu()

        if not self.application.menu:
            self.logger.error('Application menu not found, cannot inject view tasks.')
            return

        getattr(self.application, 'all_directories', None)
        if not self.application.directory_service.all_directories:
            self.logger.error('Application does not support directories services, cannot create view tasks.')
            return

        drop_down = Menu(self.application.menu.view, name='application_directories', tearoff=0)
        self.application.menu.view.add_cascade(menu=drop_down, label='Application Directories',)

        for dir_name in self.application.directory_service.all_directories:
            drop_down.add_command(label=dir_name, command=lambda d=dir_name: self._open_dir(
                self.application.directory_service.all_directories[d]))

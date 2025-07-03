""" preferences task
    """
from __future__ import annotations

from pyrox.models import Application, ApplicationTask, ApplicationConfiguration

from tkinter.ttk import Frame, Notebook


class PreferencesTask(ApplicationTask):
    """built-in preferences task.
    """

    def preferences(self):
        self.logger.info('running...')
        config = ApplicationConfiguration.toplevel()
        config.headless = True
        config.title = 'Pyrox Preferences'
        config.inc_log_window = False
        config.inc_organizer = False
        config.inc_workspace = False
        config.size_ = '650x500'
        app = Application(config)
        app.build()
        app.tk_app.resizable(False, False)

        notebook = Notebook(app.frame)
        notebook.pack(fill='both', expand=True)

        frame1 = Frame(notebook)
        frame2 = Frame(notebook)
        frame3 = Frame(notebook)
        frame4 = Frame(notebook)

        notebook.add(frame1, text='General')
        notebook.add(frame2, text='Appearance')
        notebook.add(frame3, text='Shortcuts')
        notebook.add(frame4, text='Advanced')

        app.start()

    def inject(self) -> None:
        if not self.application.menu:
            return

        self.application.menu.edit.add_separator()
        self.application.menu.edit.add_command(label='Preferences', command=self.preferences)

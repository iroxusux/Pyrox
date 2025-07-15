""" preferences task
    """
from __future__ import annotations

from pyrox.models import Application, ApplicationTask, ApplicationConfiguration

from tkinter.ttk import Frame, Notebook


class LaunchToStudioTask(ApplicationTask):
    """Launch to Studio 5000 Task
    This task launches the Studio 5000 application with the current controller file.
    """

    def launch_studio(self):
        if not self.application.controller:
            self.logger.error('No controller loaded, cannot launch Studio 5000.')
            return

        self.application.save_controller()
        controller_file = self.application.controller.file_location
        if not controller_file:
            self.logger.error('Controller file location is not set.')
            return

        self.logger.info('Launching Studio 5000 with file: %s', controller_file)
        try:
            import os
            os.startfile(controller_file)
        except Exception as e:
            self.logger.error(f'Failed to launch Studio 5000: {e}')

    def inject(self) -> None:
        if not self.application.menu:
            return

        self.application.menu.edit.add_command(label='Launch to Studio 5000', command=self.launch_studio)


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

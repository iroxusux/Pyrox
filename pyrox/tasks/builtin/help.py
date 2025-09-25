""" help tasks
    """
from __future__ import annotations

from logging import INFO, DEBUG, WARNING, ERROR, CRITICAL
from tkinter import BooleanVar, Canvas, Menu
from pathlib import Path
from PIL import ImageTk, Image
import importlib.metadata

from pyrox.models import Application, ApplicationTask, ApplicationConfiguration


LOGGING_LEVELS = [(INFO, 'Info'), (DEBUG, 'Debug'), (WARNING, 'Warning'), (ERROR, 'Error'), (CRITICAL, 'Critical')]


class HelpTask(ApplicationTask):
    """built-in help task.
    """

    def __init__(self, application):
        super().__init__(application)
        self._logger_var = {}

        self._app_config = ApplicationConfiguration.toplevel()
        self._app_config.headless = True
        self._app_config.title = 'Pyrox Help'
        self._app_config.size_ = '650x500'
        self._app_config.inc_log_window = False
        self._app_config.inc_organizer = False
        self._app_config.inc_workspace = False

        self._app = None  # coming back to this later, this is causing issues with logging... Application(self._app_config)

    def about(self):
        self.log().info('launching about page...')
        config = ApplicationConfiguration.toplevel()
        config.headless = True
        config.title = 'About Pyrox'
        config.inc_log_window = False
        config.inc_organizer = False
        config.inc_workspace = False
        config.size_ = '650x500'
        app = Application(config)
        app.build()
        app.tk_app.resizable(False, False)
        canvas = Canvas(app.frame)
        canvas.pack(fill='both', expand=True)
        path = str(Path(__file__).parent.parent.parent) + r'\ui\splash\about.png'
        bg_image = ImageTk.PhotoImage(Image.open(path))
        canvas.create_image(0, 0, image=bg_image, anchor='nw')
        title_text = "Pyrox - Indicon LLC."
        sub_text = 'A python-based environment for controls engineering tools.'
        dev_text = 'Developed by Indicon LLC: (https://indicon.com)'
        auth_text = 'Design Leader: Brian LaFond (blafond@indicon.com)'
        ver_text = f'Version: {importlib.metadata.version('pyrox')}'
        canvas.create_text(10, 10, text=title_text, fill="black", font=("Arial", 14, "bold"), anchor='nw')
        canvas.create_text(10, 40, text=sub_text, fill="black", font=("Arial", 12), anchor='nw')
        canvas.create_text(10, 60, text=dev_text, fill="black", font=("Arial", 12), anchor='nw')
        canvas.create_text(10, 80, text=auth_text, fill="black", font=("Arial", 12), anchor='nw')
        canvas.create_text(10, 100, text=ver_text, fill="black", font=("Arial", 12), anchor='nw')
        app.start()

    def guide(self):
        self.log().info('guides...')

    def inject(self) -> None:
        if not self.application.menu:
            return

        self.application.menu.help.add_command(label='About', command=self.about)
        drop_down = Menu(self.application.menu.help, name='logging', tearoff=0)
        self.application.menu.help.insert_cascade(0, label='Set Logging Level', menu=drop_down)

        for level, name in LOGGING_LEVELS:
            var = BooleanVar(value=(self.application.log().level == level))
            self._logger_var[level] = var

            def set_logger_level(x=level):
                """Set the logger level for this task."""
                if self.application:
                    self.application.set_logging_level(x)
                    for lvl, v in self._logger_var.items():
                        v.set(lvl == x)

            drop_down.add_checkbutton(
                label=name,
                variable=var,
                command=set_logger_level
            )
        self.application.menu.help.insert_separator(1)

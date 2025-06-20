"""built-in help task.
    """
from __future__ import annotations
from pyrox.models.application import Application, ApplicationTask, ApplicationConfiguration

from tkinter import Canvas
from pathlib import Path
from PIL import ImageTk, Image
import importlib.metadata


class HelpTask(ApplicationTask):
    """built-in help task.
    """

    def about(self):
        self.logger.info('launching about page...')
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
        self.logger.info('guides...')

    def inject(self) -> None:
        if not self.application.menu:
            return

        # self.application.menu.help.add_separator()
        # self.application.menu.help.add_command(label='Guides', command=self.guide)
        # self.application.menu.help.add_separator()
        self.application.menu.help.add_command(label='About', command=self.about)

""" file tasks
"""
import sys
from pyrox.models import ApplicationTask


class FileTask(ApplicationTask):

    def inject(self) -> None:
        self.file_menu.insert_separator(index=0)
        self.file_menu.add_item(
            index=1,
            label='Exit',
            command=lambda: sys.exit(0),
        )

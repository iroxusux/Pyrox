""" file tasks
"""
import sys
from pyrox.models import ApplicationTask, SceneViewerFrame


class FileTask(ApplicationTask):

    def _open_scene_viewer(self) -> None:
        """Open the Scene Viewer frame."""
        scene_viewer = SceneViewerFrame(parent=self.application.workspace)
        scene_viewer.pack(fill='both', expand=True)
        scene_viewer.focus_set()

    def inject(self) -> None:
        self.file_menu.add_item(
            index=0,
            label='Exit',
            command=lambda: exit(0),
            accelerator='Ctrl+Q',
            underline=0,
            binding_info=('<Control-q>', lambda e: sys.exit(0))
        )
        self.view_menu.add_item(
            index=1,
            label='View Scene',
            command=self._open_scene_viewer,
            accelerator='Ctrl+Shift+S',
            underline=0,
            binding_info=('<Control-Shift-s>', lambda e: self._open_scene_viewer())
        )

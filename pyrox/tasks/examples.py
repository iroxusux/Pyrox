""" file tasks
"""
import sys
from pyrox.services import (
    EnvironmentService,
    SceneRunnerService,
)
from pyrox.models import (
    ApplicationTask
)
from pyrox.models.gui import SceneViewerFrame


class ExampleTask(ApplicationTask):

    def _open_scene_viewer(self) -> None:
        """Open the Scene Viewer frame."""

        # Initialize SceneRunnerService
        SceneRunnerService.initialize(
            app=self.application,
            environment=EnvironmentService(preset='top_down'),
            enable_physics=True
        )

        # Create and register SceneViewerFrame
        scene_viewer = SceneViewerFrame(
            parent=self.application.workspace.workspace_area.root,  # type: ignore
            runner=SceneRunnerService
        )

        self.application.workspace.register_frame(scene_viewer)
        scene_viewer.on_destroy().append(lambda *_, **__: SceneRunnerService.stop())
        SceneRunnerService.new_scene()
        SceneRunnerService.run()

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

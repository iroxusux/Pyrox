""" file tasks
"""
import importlib
import sys
from pyrox import models
from pyrox.services.scene import SceneRunnerService


class FileTask(models.ApplicationTask):

    def _open_scene_viewer(self) -> None:
        """Open the Scene Viewer frame."""
        # Reload modules to ensure the latest changes are reflected
        importlib.reload(models)

        # Create SceneObjectFactory
        scene_object_factory = models.scene.SceneObjectFactory()
        scene_object_factory.register(
            'Cube',
            models.scene.SceneObject
        )

        # Create Scene
        s = models.scene.Scene(
            name="Example Scene",
            description="An example scene with a cube object.",
            scene_object_factory=scene_object_factory
        )

        # Create a concrete SceneObject subclass for demonstration
        class TestSceneObject(models.scene.PhysicsSceneObject):
            def __init__(self):
                super().__init__(
                    id="test_scene_object",
                    name="Test Scene Object",
                    scene_object_type="Cube",
                    description="A test scene object for demonstration purposes.",
                )

        # Add a test scene object
        test_object = TestSceneObject()
        s.add_scene_object(test_object)

        # Create SceneRunnerService
        runner = SceneRunnerService(
            app=self.application,
            scene=s,
            enable_physics=True
        )

        scene_viewer = models.gui.sceneviewer.SceneViewerFrame(
            parent=self.application.workspace.workspace_area.root,  # type: ignore
            scene=s
        )
        self.application.workspace.register_frame(scene_viewer)

        runner.run()

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

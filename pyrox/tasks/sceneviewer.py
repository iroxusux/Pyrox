"""Sceneviewer task injection file.
This file is paired with the Sceneviewer GUI to initialize all command bar buttons.
They intialize as disabled until a sceneviewer is running, but all the buttons will occupy a space in the menu.
"""
from pyrox.interfaces.application import IApplication
from pyrox.models import ApplicationTask
from pyrox.services import (
    SceneRunnerService,
    SceneEventBus,
    SceneEvent,
    SceneEventType,
    MenuRegistry
)


class SceneviewerApplicationTask(ApplicationTask):
    def __init__(
        self,
        application: IApplication
    ) -> None:
        super().__init__(application)
        # ---------- File Menu ----------
        file_menu = self.gui.root_menu().file_menu

        # Scene save / load controls
        self.register_menu_command(
            menu=file_menu,
            registry_id="scene.new",
            registry_path="File/New Scene",
            index=0,
            label="New Scene",
            command=SceneRunnerService.new_scene,
            accelerator="Ctrl+N",
            underline=0,
            category="scene"
        )

        self.register_menu_command(
            menu=file_menu,
            registry_id="scene.save",
            registry_path="File/Save Scene",
            index=1,
            label="Save Scene",
            command=SceneRunnerService.save_scene,
            accelerator="Ctrl+S",
            underline=0,
            category="scene",
            enabled=False
        )

        self.register_menu_command(
            menu=file_menu,
            registry_id="scene.load",
            registry_path="File/Load Scene",
            index=2,
            label="Load Scene",
            command=SceneRunnerService.load_scene,
            accelerator="Ctrl+O",
            underline=0,
            category="scene"
        )

        # ---------- Edit Menu ----------
        scene_edit_dropdown = self.gui.unsafe_get_backend().create_gui_menu(
            master=self.gui.root_menu().edit_menu.menu,
            tearoff=0
        )

        self.register_menu_command(
            menu=scene_edit_dropdown,
            registry_id="scene.edit.delete_selected",
            registry_path="Edit/Scene Viewer/Delete Selected Objects",
            index=0,
            label="Delete Selected Objects",
            command=None,  # To be assigned by SceneViewer
            accelerator="Del",
            underline=7,
            category="scene",
            enabled=False
        )

        self.register_submenu(
            menu=self.gui.root_menu().edit_menu,
            submenu=scene_edit_dropdown,
            registry_id="scene.edit",
            registry_path="Edit/Scene Viewer",
            index=0,
            label="Scene Viewer",
            underline=0,
            category="scene"
        )

        # ---------- View Menu ----------

        scene_view_dropdown = self.gui.unsafe_get_backend().create_gui_menu(
            master=self.gui.root_menu().view_menu.menu,
            tearoff=0
        )

        # Zoom controls
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.zoom_in",
            registry_path="View/Scene Viewer/+Zoom In",
            index=0,
            label="+Zoom In",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl++",
            underline=0,
            category="scene",
            enabled=False
        )
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.zoom_out",
            registry_path="View/Scene Viewer/-Zoom Out",
            index=1,
            label="-Zoom Out",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+-",
            underline=0,
            category="scene",
            enabled=False
        )
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.reset_view",
            registry_path="View/Scene Viewer/Reset View",
            index=2,
            label="Reset View",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+0",
            underline=0,
            category="scene",
            enabled=False
        )

        scene_view_dropdown.insert_separator(3)

        # Grid controls
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.show_grid",
            registry_path="View/Scene Viewer/Show Grid",
            index=4,
            label="Show Grid",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+G",
            underline=0,
            category="scene",
            enabled=False
        )
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.snap_to_grid",
            registry_path="View/Scene Viewer/Snap to Grid",
            index=5,
            label="Snap to Grid",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+Shift+G",
            underline=0,
            category="scene",
            enabled=False
        )

        scene_view_dropdown.insert_separator(6)

        # Design Mode controls
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.design_mode",
            registry_path="View/Scene Viewer/Design Mode",
            index=7,
            label="Design Mode",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+D",
            underline=0,
            category="scene",
            enabled=False
        )
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.object_palette",
            registry_path="View/Scene Viewer/Object Palette",
            index=8,
            label="Object Palette",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+Shift+D",
            underline=0,
            category="scene",
            enabled=False
        )
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.properties_panel",
            registry_path="View/Scene Viewer/Properties Panel",
            index=9,
            label="Properties Panel",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+Alt+D",
            underline=0,
            category="scene",
            enabled=False
        )

        # Connection editor
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.connection_editor",
            registry_path="View/Scene Viewer/Connection Editor",
            index=10,
            label="Connection Editor",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+E",
            underline=0,
            category="scene",
            enabled=False
        )

        self.register_submenu(
            menu=self.gui.root_menu().view_menu,
            submenu=scene_view_dropdown,
            registry_id="scene.view",
            registry_path="View/Scene Viewer",
            index=0,
            label="Scene Viewer",
            underline=0,
            category="scene"
        )

        SceneEventBus.subscribe(
            SceneEventType.SCENE_LOADED,
            lambda event: self._enable_menu_entries(event, True)
        )
        SceneEventBus.subscribe(
            SceneEventType.SCENE_UNLOADED,
            lambda event: self._enable_menu_entries(event, False)
        )

    def _enable_menu_entries(
        self,
        event: SceneEvent,
        enable: bool
    ) -> None:
        """Enable or disable all SceneViewer-related menu entries.
        Args:
            enable: True to enable, False to disable.
        """
        if enable:
            MenuRegistry.enable_items_by_owner("SceneviewerApplicationTask")
        else:
            MenuRegistry.disable_items_by_owner("SceneviewerApplicationTask")

"""Workspace interface module.
Defines the IWorkspace interface for GUI workspaces.
"""
from abc import ABC, abstractmethod
from typing import Callable
from pyrox.interfaces.gui.frame import ITaskFrame


class IWorkspace(ABC):
    """Interface for a GUI Workspace.
    """

    # -------- Geometry management --------

    @abstractmethod
    def save_workspace_geometry(self) -> None: ...

    @abstractmethod
    def restore_workspace_geometry(self) -> None: ...

    # -------- Workspace management --------

    @abstractmethod
    def clear_workspace(self) -> None: ...

    @abstractmethod
    def clear_all(self) -> None: ...

    @abstractmethod
    def get_workspace_info(self) -> dict: ...

    @abstractmethod
    def subscribe_to_sash_movement_events(
        self,
        callback: Callable[[str, float], None]
    ) -> None: ...

    @abstractmethod
    def get_workspace_area(self): ...

    @abstractmethod
    def get_workspace_paned_window(self): ...

    @property
    @abstractmethod
    def workspace_area(self): ...

    @property
    @abstractmethod
    def workspace_paned_window(self): ...

    # -------- Frames management --------

    @abstractmethod
    def register_frame(
        self,
        frame: ITaskFrame,
        raise_frame: bool = True
    ) -> None: ...

    @abstractmethod
    def unregister_frame(
        self,
        frame: ITaskFrame
    ) -> None: ...

    @abstractmethod
    def get_frame(
        self,
        frame_name: str
    ) -> ITaskFrame | None: ...

    @abstractmethod
    def get_frames(self) -> list[ITaskFrame]: ...

    @abstractmethod
    def set_frames(
        self,
        frames: list[ITaskFrame]
    ) -> None: ...

    @abstractmethod
    def raise_frame(
        self,
        frame: ITaskFrame
    ) -> None: ...

    # -------- Sidebar management --------

    @abstractmethod
    def get_sidebar_width(self) -> int | None: ...

    @abstractmethod
    def set_sidebar_width(self, perc_of_window: float) -> None: ...

    @abstractmethod
    def on_main_sash_moved(self, event): ...

    @abstractmethod
    def get_sidebar_organizer(self): ...

    @property
    @abstractmethod
    def sidebar_organizer(self): ...

    # -------- Sidebar tab management --------

    @abstractmethod
    def show_sidebar(self) -> None: ...

    @abstractmethod
    def hide_sidebar(self) -> None: ...

    @abstractmethod
    def toggle_sidebar(self) -> bool: ...

    # -------- Sidebar panel management --------

    @abstractmethod
    def add_panel(
        self,
        panel,
        position: str = 'left'
    ) -> None: ...

    @abstractmethod
    def remove_panel(
        self,
        panel
    ) -> None: ...

    @abstractmethod
    def get_panels(self) -> list: ...

    @abstractmethod
    def clear_panels(self) -> None: ...

    @abstractmethod
    def set_panel_height(
        self,
        panel_id: str,
        height: int
    ) -> None: ...

    @abstractmethod
    def get_panel_height(self, panel_id) -> int: ...

    # -------- Sidebar widget management --------

    @abstractmethod
    def add_sidebar_widget(
        self,
        widget,
        tab_name: str,
        widget_id: str | None = None,
        icon: str | None = None,
        closeable: bool = True
    ) -> str: ...

    @abstractmethod
    def add_workspace_task_frame(
        self,
        task_frame: ITaskFrame,
        raise_frame: bool = True
    ) -> str: ...

    @abstractmethod
    def clear_sidebar(self) -> None: ...

    @abstractmethod
    def remove_widget(self, widget_id: str) -> bool: ...

    @abstractmethod
    def get_widget(self, widget_id: str): ...

    @abstractmethod
    def get_all_widget_ids(self) -> dict[str, list[str]]: ...

    # -------- Log Window management --------

    @abstractmethod
    def get_log_window_height(self) -> int | None: ...

    @abstractmethod
    def set_log_window_height(self, perc_of_window: float) -> None: ...

    @abstractmethod
    def on_log_sash_moved(self, event): ...

    # -------- Status bar management --------

    @abstractmethod
    def set_status(self, status: str) -> None: ...

    @abstractmethod
    def get_status(self) -> str: ...

    # ------- Properties --------

    @property
    @abstractmethod
    def frames(self) -> list[ITaskFrame]: ...

    @property
    @abstractmethod
    def panels(self) -> list: ...

    @property
    @abstractmethod
    def status(self) -> str: ...

    @status.setter
    @abstractmethod
    def status(
        self,
        status: str
    ) -> None: ...

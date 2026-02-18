"""Workspace interface module.
Defines the IWorkspace interface for GUI workspaces.
"""
from abc import abstractmethod
from typing import Callable, Generic, TypeVar
from pyrox.interfaces.protocols.meta import ICoreRunnableMixin
from pyrox.interfaces.gui import ITaskFrame
from .component import IGuiComponent


T = TypeVar('T', bound=IGuiComponent)


class IWorkspace(
    Generic[T],
    IGuiComponent[T],
    ICoreRunnableMixin
):
    """Interface for a GUI Workspace.
    """

    # -------- Geometry management --------

    @abstractmethod
    def save_workspace_geometry(self) -> None:
        """Handle workspace geometry change events.

        Uses debouncing to prevent lag during rapid resize events.
        Cancels any pending save and schedules a new one after a delay.
        """
        raise NotImplementedError("save_workspace_geometry must be implemented by subclass")

    @abstractmethod
    def restore_workspace_geometry(self) -> None:
        """Restore the workspace geometry from the environment."""
        raise NotImplementedError("restore_workspace_geometry must be implemented by subclass")

    # -------- Workspace management --------

    @abstractmethod
    def clear_workspace(self) -> None:
        """Clear all widgets from the workspace area."""
        raise NotImplementedError("clear_workspace must be implemented by subclass")

    @abstractmethod
    def clear_all(self) -> None:
        """Clear all widgets from both areas."""
        raise NotImplementedError("clear_all must be implemented by subclass")

    @abstractmethod
    def get_workspace_info(self) -> dict:
        """Get comprehensive workspace information."""
        raise NotImplementedError("get_workspace_info must be implemented by subclass")

    @abstractmethod
    def subscribe_to_sash_movement_events(
        self,
        callback: Callable[[str, float], None]
    ) -> None:
        """Subscribe to sash movement events.
        This is temporary and may be replaced with a more robust GUI backend event system later.

        Args:
            callback: Function to call on sash movement with parameters (sash_id, position)
        """
        raise NotImplementedError("subscribe_to_sash_movement_events must be implemented by subclass")

    @abstractmethod
    def get_workspace_area(self):
        """Get the workspace area.

        Returns:
            IGuiFrame: The workspace area instance.
        """
        raise NotImplementedError("get_workspace_area must be implemented by subclass")

    @abstractmethod
    def get_workspace_paned_window(self):
        """Get the main workspace paned window.

         Returns:
            ttk.PanedWindow: The main workspace paned window, or None if not initialized.
         """
        raise NotImplementedError("get_workspace_paned_window must be implemented by subclass")

    @property
    def workspace_area(self):
        """Get the workspace area.

        Returns:
            PyroxFrameContainer: The workspace area instance.
        """
        return self.get_workspace_area()

    @property
    def workspace_paned_window(self):
        """Get the main workspace paned window.

        Returns:
            The main workspace paned window, or None if not initialized.
        """
        return self.get_workspace_paned_window()

    # -------- Frames management --------

    @abstractmethod
    def register_frame(
        self,
        frame: ITaskFrame,
        raise_frame: bool = True
    ) -> None:
        """Register a frame with the workspace.

        Args:
            frame (ITaskFrame): The frame to register.
            raise_frame (bool): Whether to bring the frame to the front upon registration.
        """
        raise NotImplementedError("register_frame must be implemented by subclass")

    @abstractmethod
    def unregister_frame(
        self,
        frame: ITaskFrame
    ) -> None:
        """Unregister a frame from the workspace.

        Args:
            frame (ITaskFrame): The frame to unregister.
        """
        raise NotImplementedError("unregister_frame must be implemented by subclass")

    @abstractmethod
    def get_frame(
        self,
        frame_name: str
    ) -> ITaskFrame | None:
        """Get a registered frame by its ID.

        Args:
            frame_name (str): The frame_name of the frame.

        Returns:
            ITaskFrame or None: The registered frame, or None if not found.
        """
        raise NotImplementedError("get_frame must be implemented by subclass")

    @abstractmethod
    def get_frames(self) -> list[ITaskFrame]:
        """Get all registered frames in the workspace.

        Returns:
            list[ITaskFrame]: List of registered frames.
        """
        raise NotImplementedError("get_frames must be implemented by subclass")

    @abstractmethod
    def set_frames(
        self,
        frames: list[ITaskFrame]
    ) -> None:
        """Set the registered frames in the workspace.

        Args:
            frames (List[ITaskFrame]): List of frames to register.
        """
        raise NotImplementedError("set_frames must be implemented by subclass")

    @abstractmethod
    def raise_frame(
        self,
        frame: ITaskFrame
    ) -> None:
        """Raise a registered frame to the front of the workspace.

        Args:
            frame (ITaskFrame): The frame to raise.
        """
        raise NotImplementedError("raise_frame must be implemented by subclass")

    # -------- Sidebar management --------

    @abstractmethod
    def get_sidebar_width(self) -> int | None:
        """Get the current main window sash position as a percentage of the window width."""
        raise NotImplementedError("get_sidebar_width must be implemented by subclass")

    @abstractmethod
    def set_sidebar_width(self, perc_of_window: float) -> None:
        """Set the sidebar width as a percentage of the window width."""
        raise NotImplementedError("set_sidebar_width must be implemented by subclass")

    @abstractmethod
    def on_main_sash_moved(self, event):
        raise NotImplementedError("on_main_sash_moved must be implemented by subclass")

    # -------- Sidebar tab management --------

    @abstractmethod
    def show_sidebar(self) -> None:
        """Show the sidebar organizer."""
        raise NotImplementedError("show_sidebar must be implemented by subclass")

    @abstractmethod
    def hide_sidebar(self) -> None:
        """Hide the sidebar organizer."""
        raise NotImplementedError("hide_sidebar must be implemented by subclass")

    @abstractmethod
    def toggle_sidebar(self) -> bool:
        """
        Toggle sidebar visibility.

        Returns:
            New visibility state
        """
        raise NotImplementedError("toggle_sidebar must be implemented by subclass")

    # -------- Sidebar panel management --------

    @abstractmethod
    def add_panel(
        self,
        panel: T,
        position: str = 'left'
    ) -> None:
        """
        Add a panel to the workspace.

        Args:
            panel: The panel widget to add
            position: Position to add the panel ('left' or 'right')
        """
        raise NotImplementedError("add_panel must be implemented by subclass")

    @abstractmethod
    def remove_panel(
        self,
        panel: T
    ) -> None:
        """
        Remove a panel from the workspace.

        Args:
            panel: The panel widget to remove
        """
        raise NotImplementedError("remove_panel must be implemented by subclass")

    @abstractmethod
    def get_panels(self) -> list[T]:
        """
        Get all panels in the workspace.

        Returns:
            List of panel widgets
        """
        raise NotImplementedError("get_panels must be implemented by subclass")

    @abstractmethod
    def clear_panels(self) -> None:
        """
        Clear all panels from the workspace.
        """
        raise NotImplementedError("clear_panels must be implemented by subclass")

    @abstractmethod
    def set_panel_height(
        self,
        panel_id: str,
        height: int
    ) -> None:
        """
        Set the height of a specific panel.

        Args:
            panel_id: The ID of the panel
            height: The height to set for the panel
        """
        raise NotImplementedError("set_panel_height must be implemented by subclass")

    @abstractmethod
    def get_panel_height(self, panel_id) -> int:
        """
        Get the height of the log window as a fraction of total height.

        Returns:
            Fractional height (0.0 to 1.0)
        """
        raise NotImplementedError("get_panel_height must be implemented by subclass")

    # -------- Sidebar widget management --------

    @abstractmethod
    def add_sidebar_widget(
        self,
        widget: T,
        tab_name: str,
        widget_id: str | None = None,
        icon: str | None = None,
        closeable: bool = True
    ) -> str:
        """
        Add a widget to the sidebar organizer.

        Args:
            widget: The widget to add
            tab_name: Name for the tab
            widget_id: Custom widget ID (auto-generated if None)
            icon: Optional icon for the tab (Unicode character or emoji)
            closeable: Whether the tab can be closed

        Returns:
            The widget ID

        Raises:
            ValueError: If widget_id already exists
        """
        raise NotImplementedError("add_sidebar_widget must be implemented by subclass")

    @abstractmethod
    def add_workspace_task_frame(
        self,
        task_frame: ITaskFrame,
        raise_frame: bool = True
    ) -> str:
        """
        Add a widget to the main workspace area.

        Args:
            task_frame: The TaskFrame to add
            raise_frame: Whether to raise the frame to the top

        Returns:
            The widget ID

        Raises:
            ValueError: If widget_id already exists or task_frame is None
        """
        raise NotImplementedError("add_workspace_task_frame must be implemented by subclass")

    @abstractmethod
    def clear_sidebar(self) -> None:
        """Clear all widgets from the sidebar."""
        raise NotImplementedError("clear_sidebar must be implemented by subclass")

    @abstractmethod
    def remove_widget(self, widget_id: str) -> bool:
        """
        Remove a widget from the workspace.

        Args:
            widget_id: ID of the widget to remove

        Returns:
            True if widget was removed, False if not found
        """
        raise NotImplementedError("remove_widget must be implemented by subclass")

    @abstractmethod
    def get_widget(self, widget_id: str) -> T | ITaskFrame | None:
        """Get a widget by its ID."""
        raise NotImplementedError("get_widget must be implemented by subclass")

    @abstractmethod
    def get_all_widget_ids(self) -> dict[str, list[str]]:
        """Get all widget IDs organized by location."""
        raise NotImplementedError("get_all_widget_ids must be implemented by subclass")

    # -------- Log Window management --------

    @abstractmethod
    def get_log_window_height(self) -> int | None:
        """Get the current log window sash position as a percentage of the window height."""
        raise NotImplementedError("get_log_window_height must be implemented by subclass")

    @abstractmethod
    def set_log_window_height(self, perc_of_window: float) -> None:
        """Set the log window height as a percentage of the window height."""
        raise NotImplementedError("set_log_window_height must be implemented by subclass")

    @abstractmethod
    def on_log_sash_moved(self, event):
        raise NotImplementedError("on_log_sash_moved must be implemented by subclass")

    # -------- Status bar management --------

    @abstractmethod
    def set_status(self, status: str) -> None:
        """Set the status bar message."""
        raise NotImplementedError("set_status must be implemented by subclass")

    @abstractmethod
    def get_status(self) -> str:
        """Get the current status message."""
        raise NotImplementedError("get_status must be implemented by subclass")

    # ------- Properties --------

    @property
    def frames(self) -> list[ITaskFrame]:
        """Get all registered frames in the workspace.

        Returns:
            list[ITaskFrame]: List of registered frames.
        """
        return self.get_frames()

    @property
    def panels(self) -> list[T]:
        """Get all panels in the workspace.

        Returns:
            list[IGUIComponent]: List of panels in the workspace.
        """
        return self.get_panels()

    @property
    def status(self) -> str:
        """Get the current status message of the workspace.

        Returns:
            str: The current status message.
        """
        return self.get_status()

    @status.setter
    def status(
        self,
        status: str
    ) -> None:
        """Set the current status message of the workspace.

        Args:
            status (str): The status message to set.
        """
        self.set_status(status)
